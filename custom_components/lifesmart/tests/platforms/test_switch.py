"""
LifeSmart 开关平台测试套件。

此测试套件专门测试 switch.py 中的开关平台功能，包括：
- 开关实体的设置和初始化
- 各种开关类型的支持（三路开关、智能插座、通用控制器、九路控制器）
- 开关状态控制（开启、关闭）
- 设备排除配置的处理
- 状态更新和回调处理
- 不同开关模式和设备类别的验证

测试使用结构化的类组织，每个类专注于特定的开关类型，
并包含详细的中文注释以确保可维护性。
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN, SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_OFF, STATE_ON, STATE_OFF
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.lifesmart.core.const import *
from custom_components.lifesmart.switch import async_setup_entry
from ..utils.constants import (
    FRIENDLY_DEVICE_NAMES,
)
from ..utils.factories import create_devices_by_category
from ..utils.factories import (
    create_traditional_switch_devices,
    create_advanced_switch_devices,
    create_smart_plug_devices,
    create_power_meter_plug_devices,
)
from ..utils.helpers import (
    get_entity_unique_id,
    create_mock_hub,
    assert_platform_entity_count_matches_devices,
    verify_platform_entity_count,
    find_device_by_friendly_name,
    validate_device_data,
)


# ==================== 开关平台设置测试类 ====================


class TestSwitchSetup:
    """测试开关平台的设置和初始化功能。"""

    @pytest.mark.asyncio
    async def test_setup_all_switches(
        self, hass: HomeAssistant, setup_integration_switch_only: ConfigEntry
    ):
        """测试从conftest中成功设置所有开关实体。

        验证所有类型的开关设备都能正确创建和注册：
        - 3个三路开关 (sw_if3)
        - 1个智能插座 (sw_ol)
        - 3个自然风开关 (sw_nature)
        - 3个通用控制器开关模式 (generic_p_switch_mode)
        - 9个九路控制器 (sw_p9)
        总计19个开关实体。
        """
        # 使用专用开关工厂函数创建设备
        traditional_switches = create_traditional_switch_devices()
        advanced_switches = create_advanced_switch_devices()
        smart_plugs = create_smart_plug_devices()
        power_meter_plugs = create_power_meter_plug_devices()

        # 合并所有开关设备
        devices_list = (
            traditional_switches + advanced_switches + smart_plugs + power_meter_plugs
        )

        # 验证设备数据完整性
        for device in devices_list:
            validate_device_data(device)

        # 使用FRIENDLY_DEVICE_NAMES验证关键设备
        switch_friendly_names = [
            name
            for name, device_type in FRIENDLY_DEVICE_NAMES.items()
            if "switch" in device_type.lower() or "plug" in device_type.lower()
        ]

        for friendly_name in switch_friendly_names[:3]:  # 验证前3个
            device = find_device_by_friendly_name(devices_list, friendly_name)
            if device:
                assert device is not None, f"{friendly_name}设备应该存在"

        # 验证平台实体数量
        verify_platform_entity_count(hass, SWITCH_DOMAIN, devices_list)
        assert_platform_entity_count_matches_devices(hass, SWITCH_DOMAIN, devices_list)

        assert hass.states.get("switch.9_way_controller_p4") is not None

    @pytest.mark.asyncio
    async def test_setup_with_exclusions(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        mock_config_data: dict,
    ):
        """测试设备和Hub可以从设置中排除。

        验证排除配置功能：
        - 通过CONF_EXCLUDE_ITEMS排除特定设备
        - 通过CONF_EXCLUDE_AGTS排除特定Hub
        - 确保排除的设备不会创建实体
        - 验证剩余设备正确创建
        """
        # 1. 创建一个带有自定义排除选项的 ConfigEntry
        custom_options = {
            CONF_EXCLUDE_ITEMS: "sw_ol, sw_p9",  # Exclude Outlet and 9-way
            CONF_EXCLUDE_AGTS: "excluded_hub",  # Exclude Power Plug
        }
        entry_with_exclusions = MockConfigEntry(
            domain=DOMAIN,
            data=mock_config_data,
            options=custom_options,
            entry_id="exclusion_test_entry",
        )

        # 2. 准备 hass.data，因为 async_setup_entry 会从中读取数据
        # 使用工厂函数创建设备和mock hub
        mock_lifesmart_devices = create_devices_by_category(
            ["traditional_switch", "advanced_switch", "smart_plug"]
        )
        mock_hub = create_mock_hub(mock_lifesmart_devices, mock_client)
        mock_hub.get_exclude_config.return_value = (
            {"sw_ol", "sw_p9"},  # exclude_devices
            {"excluded_hub"},  # exclude_hubs
        )

        hass.data[DOMAIN] = {
            entry_with_exclusions.entry_id: {
                "hub": mock_hub,
                "devices": mock_lifesmart_devices,
            }
        }

        # 3. 调用被测试的函数
        # async_add_entities is a synchronous function, not a coroutine.
        async_add_entities = MagicMock()
        await async_setup_entry(hass, entry_with_exclusions, async_add_entities)

        # 4. 断言
        # 预期: 3 (sw_if3) + 3 (sw_nature) + 3 (generic_p_switch_mode) = 9
        created_entities = async_add_entities.call_args[0][0]
        assert len(created_entities) == 9

        entity_ids = {entity.unique_id for entity in created_entities}
        assert not any("sw_ol" in eid for eid in entity_ids)
        assert not any("sw_p9" in eid for eid in entity_ids)
        assert not any("excluded_hub" in eid for eid in entity_ids)


# ==================== 标准三路开关测试类 ====================


class TestStandardSwitch:
    """测试标准三路开关 (SL_SW_IF3) 的功能。"""

    @pytest.mark.asyncio
    async def test_initial_properties_and_control(
        self, hass: HomeAssistant, setup_integration_switch_only, mock_client: AsyncMock
    ):
        """测试开关实体的初始属性和控制功能。

        验证：
        - 实体存在性和初始状态
        - 设备类型正确设置
        - 控制命令正确传递
        - 状态更新机制正常
        """
        # 使用工厂函数查找三路开关设备
        devices = create_devices_by_category(["traditional_switch"])
        switch_device = None
        for device in devices:
            if device.get("devtype") == "SL_SW_IF3":
                switch_device = device
                break

        assert switch_device is not None, "应该找到三路开关测试设备"

        # 构建实体ID（基于设备实际数据）
        entity_id = f"switch.{switch_device['name'].lower().replace(' ', '_')}_l1"

        # 测试初始属性
        state = hass.states.get(entity_id)
        assert state is not None, "开关实体应存在"
        assert state.state == STATE_ON, "初始状态应为开启"
        assert (
            state.attributes.get("device_class") == SwitchDeviceClass.SWITCH
        ), "设备类别应为开关"

        # 测试控制功能
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        assert (
            hass.states.get(entity_id).state == STATE_OFF
        ), "关闭服务调用后状态应为关闭"

        # 验证客户端调用
        mock_client.turn_off_light_switch_async.assert_called_with(
            "L1", switch_device["agt"], switch_device["me"]
        )

        # 测试状态更新
        unique_id = get_entity_unique_id(hass, entity_id)
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", {"type": CMD_TYPE_ON}
        )
        await hass.async_block_till_done()
        assert (
            hass.states.get(entity_id).state == STATE_ON
        ), "接收dispatcher更新后状态应为开启"


# ==================== 智能插座测试类 ====================


class TestSmartOutlet:
    """测试智能插座 (SL_OL) 的功能。"""

    @pytest.mark.asyncio
    async def test_initial_properties_and_control(
        self, hass: HomeAssistant, setup_integration_switch_only, mock_client: AsyncMock
    ):
        """测试智能插座的初始属性和控制功能。

        验证：
        - 实体存在性和初始状态
        - 设备类型为插座
        - 控制命令正确传递
        """
        # 使用工厂函数查找智能插座设备
        devices = create_devices_by_category(["smart_plug"])
        outlet_device = None
        for device in devices:
            if device.get("devtype") == "SL_OL":
                outlet_device = device
                break

        assert outlet_device is not None, "应该找到智能插座测试设备"

        # 构建实体ID（基于设备实际数据）
        entity_id = f"switch.{outlet_device['name'].lower().replace(' ', '_')}_o"

        # 测试初始属性
        state = hass.states.get(entity_id)
        assert state is not None, "插座实体应存在"
        assert state.state == STATE_ON, "初始状态应为开启"
        assert (
            state.attributes.get("device_class") == SwitchDeviceClass.OUTLET
        ), "设备类别应为插座"

        # 测试控制功能
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

        # 验证客户端调用
        mock_client.turn_off_light_switch_async.assert_called_with(
            "O", outlet_device["agt"], outlet_device["me"]
        )


# ==================== 通用控制器开关模式测试类 ====================


class TestGenericControllerAsSwitch:
    """测试通用控制器 (SL_P) 在三路开关模式下的功能。"""

    @pytest.mark.parametrize(
        ("sub_key", "expected_initial_state"),
        [
            ("P2", STATE_ON),
            ("P3", STATE_OFF),
            ("P4", STATE_ON),
        ],
        ids=[
            "GenControllerChannelP2On",
            "GenControllerChannelP3Off",
            "GenControllerChannelP4On",
        ],
    )
    @pytest.mark.asyncio
    async def test_channel_behavior(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        setup_integration_switch_only,
        sub_key: str,
        expected_initial_state: str,
    ):
        """测试通用控制器各通道的行为。

        验证不同通道：
        - P2通道初始状态为开启
        - P3通道初始状态为关闭
        - P4通道初始状态为开启
        - 关闭服务调用正确传递参数
        """
        # 使用工厂函数查找通用控制器设备
        devices = create_devices_by_category(["generic_p_switch_mode"])
        controller_device = None
        for device in devices:
            if device.get("devtype") == "SL_P":
                controller_device = device
                break

        assert controller_device is not None, "应该找到通用控制器测试设备"

        # 构建实体ID（基于设备实际数据）
        entity_id_suffix = sub_key.lower()
        entity_id = f"switch.{controller_device['name'].lower().replace(' ', '_')}_{entity_id_suffix}"

        # 测试初始状态
        state = hass.states.get(entity_id)
        assert state is not None, f"Entity {entity_id} not found"
        assert (
            state.state == expected_initial_state
        ), f"初始状态应为 {expected_initial_state}"

        # 测试控制功能
        await hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        # 验证客户端调用
        mock_client.turn_off_light_switch_async.assert_called_with(
            sub_key, controller_device["agt"], controller_device["me"]
        )


# ==================== 九路控制器测试类 ====================


class TestNineWayController:
    """测试九路开关控制器 (SL_P_SW) 的功能。"""

    @pytest.mark.parametrize(
        ("sub_key", "expected_initial_state"),
        [
            ("P1", STATE_ON),
            ("P8", STATE_OFF),
            ("P9", STATE_ON),
        ],
        ids=["NineWayChannelP1On", "NineWayChannelP8Off", "NineWayChannelP9On"],
    )
    @pytest.mark.asyncio
    async def test_channel_behavior(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        setup_integration_switch_only,
        sub_key: str,
        expected_initial_state: str,
    ):
        """测试九路控制器各通道的行为。

        验证不同通道：
        - P1通道初始状态为开启
        - P8通道初始状态为关闭
        - P9通道初始状态为开启
        - 关闭服务调用正确传递到对应通道
        """
        # 使用工厂函数查找九路控制器设备
        devices = create_devices_by_category(["sw_p9"])
        controller_device = None
        for device in devices:
            if device.get("devtype") == "SL_P_SW":
                controller_device = device
                break

        assert controller_device is not None, "应该找到九路控制器测试设备"

        # 构建实体ID（基于设备实际数据）
        entity_id_suffix = sub_key.lower()
        entity_id = f"switch.{controller_device['name'].lower().replace(' ', '_')}_{entity_id_suffix}"

        # 测试初始状态
        state = hass.states.get(entity_id)
        assert state is not None, f"Entity {entity_id} not found"
        assert (
            state.state == expected_initial_state
        ), f"初始状态应为 {expected_initial_state}"

        # 测试控制功能
        await hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        # 验证客户端调用
        mock_client.turn_off_light_switch_async.assert_called_with(
            sub_key, controller_device["agt"], controller_device["me"]
        )
