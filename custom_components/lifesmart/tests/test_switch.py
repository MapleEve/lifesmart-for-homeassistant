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

from custom_components.lifesmart.const import *
from custom_components.lifesmart.switch import async_setup_entry
from .test_utils import get_entity_unique_id


# ==================== 开关平台设置测试类 ====================


class TestSwitchSetup:
    """测试开关平台的设置和初始化功能。"""

    @pytest.mark.asyncio
    async def test_setup_all_switches(
        self, hass: HomeAssistant, setup_integration: ConfigEntry
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
        # 3 (sw_if3) + 1 (sw_ol) + 3 (sw_nature) + 3 (generic_p_switch_mode) + 9 (sw_p9) = 19
        assert len(hass.states.async_entity_ids(SWITCH_DOMAIN)) == 19

        assert hass.states.get("switch.9_way_controller_p4") is not None

    @pytest.mark.asyncio
    async def test_setup_with_exclusions(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        mock_config_data: dict,
        mock_lifesmart_devices: list,
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
        # 创建一个模拟的 hub 对象
        mock_hub = MagicMock()
        mock_hub.get_exclude_config.return_value = (
            {"sw_ol", "sw_p9"},  # exclude_devices
            {"excluded_hub"},  # exclude_hubs
        )
        mock_hub.get_devices.return_value = mock_lifesmart_devices
        mock_hub.get_client.return_value = mock_client

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

    ENTITY_ID = "switch.3_gang_switch_l1"
    DEVICE_ME = "sw_if3"
    HUB_ID = "hub_sw"
    SUB_KEY = "L1"

    @pytest.mark.asyncio
    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        """测试开关实体的初始属性。
        
        验证：
        - 实体存在性
        - 初始状态正确
        - 设备类型正确设置
        """
        state = hass.states.get(self.ENTITY_ID)
        assert state is not None, "开关实体应存在"
        assert state.state == STATE_ON, "初始状态应为开启"
        assert (
            state.attributes.get("device_class") == SwitchDeviceClass.SWITCH
        ), "设备类别应为开关"

    @pytest.mark.asyncio
    async def test_turn_on_off_and_update(
        self, hass: HomeAssistant, mock_client: AsyncMock, setup_integration
    ):
        """测试开关的开启/关闭控制和状态更新。
        
        验证：
        - 关闭服务调用正确传递到客户端
        - 状态正确更新
        - 通过dispatcher接收更新后状态变化
        """
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )
        assert (
            hass.states.get(self.ENTITY_ID).state == STATE_OFF
        ), "关闭服务调用后状态应为关闭"
        mock_client.turn_off_light_switch_async.assert_called_with(
            self.SUB_KEY, self.HUB_ID, self.DEVICE_ME
        )

        unique_id = get_entity_unique_id(hass, self.ENTITY_ID)
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", {"type": 129}
        )
        await hass.async_block_till_done()
        assert (
            hass.states.get(self.ENTITY_ID).state == STATE_ON
        ), "接收dispatcher更新后状态应为开启"


# ==================== 智能插座测试类 ====================


class TestSmartOutlet:
    """测试智能插座 (SL_OL) 的功能。"""

    ENTITY_ID = "switch.smart_outlet_o"
    DEVICE_ME = "sw_ol"
    HUB_ID = "hub_sw"
    SUB_KEY = "O"

    @pytest.mark.asyncio
    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        """测试智能插座的初始属性。
        
        验证：
        - 实体存在性
        - 初始状态为开启
        - 设备类型为插座
        """
        state = hass.states.get(self.ENTITY_ID)
        assert state is not None
        assert state.state == STATE_ON
        assert state.attributes.get("device_class") == SwitchDeviceClass.OUTLET

    @pytest.mark.asyncio
    async def test_turn_on_off(
        self, hass: HomeAssistant, mock_client: AsyncMock, setup_integration
    ):
        """测试智能插座的开关控制。
        
        验证关闭服务调用能正确传递到客户端。
        """
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )
        mock_client.turn_off_light_switch_async.assert_called_with(
            self.SUB_KEY, self.HUB_ID, self.DEVICE_ME
        )


# ==================== 通用控制器开关模式测试类 ====================


class TestGenericControllerAsSwitch:
    """测试通用控制器 (SL_P) 在三路开关模式下的功能。"""

    DEVICE_ME = "generic_p_switch_mode"
    HUB_ID = "hub_sw"

    @pytest.mark.parametrize(
        ("entity_id_suffix", "sub_key", "initial_state"),
        [
            ("p2", "P2", STATE_ON),
            ("p3", "P3", STATE_OFF),
            ("p4", "P4", STATE_ON),
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
        setup_integration,
        entity_id_suffix: str,
        sub_key: str,
        initial_state: str,
    ):
        """测试通用控制器各通道的行为。
        
        验证不同通道：
        - P2通道初始状态为开启
        - P3通道初始状态为关闭  
        - P4通道初始状态为开启
        - 关闭服务调用正确传递参数
        """
        entity_id = f"switch.generic_controller_switch_{entity_id_suffix}"

        state = hass.states.get(entity_id)
        assert state is not None, f"Entity {entity_id} not found"
        assert state.state == initial_state

        await hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )
        mock_client.turn_off_light_switch_async.assert_called_with(
            sub_key, self.HUB_ID, self.DEVICE_ME
        )


# ==================== 九路控制器测试类 ====================


class TestNineWayController:
    """测试九路开关控制器 (SL_P_SW) 的功能。"""

    DEVICE_ME = "sw_p9"
    HUB_ID = "hub_sw"

    @pytest.mark.parametrize(
        ("entity_id_suffix", "sub_key", "initial_state"),
        [
            ("p1", "P1", STATE_ON),
            ("p8", "P8", STATE_OFF),
            ("p9", "P9", STATE_ON),
        ],
        ids=["NineWayChannelP1On", "NineWayChannelP8Off", "NineWayChannelP9On"],
    )
    @pytest.mark.asyncio
    async def test_channel_behavior(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        setup_integration,
        entity_id_suffix: str,
        sub_key: str,
        initial_state: str,
    ):
        """测试九路控制器各通道的行为。
        
        验证不同通道：
        - P1通道初始状态为开启
        - P8通道初始状态为关闭
        - P9通道初始状态为开启
        - 关闭服务调用正确传递到对应通道
        """
        entity_id = f"switch.9_way_controller_{entity_id_suffix}"

        state = hass.states.get(entity_id)
        assert state is not None, f"Entity {entity_id} not found"
        assert state.state == initial_state

        await hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )
        mock_client.turn_off_light_switch_async.assert_called_with(
            sub_key, self.HUB_ID, self.DEVICE_ME
        )
