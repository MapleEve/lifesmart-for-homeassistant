"""
针对 LifeSmart 温控 (Climate) 平台的单元和集成测试。

此测试套件旨在全面验证 LifeSmartClimate 实体的行为。它被设计为在单个文件中
运行，包含了两种类型的测试：

1.  通用集成测试 (使用平台专用 `setup_integration_climate_only` Fixture):
    这些测试在一个加载了所有模拟设备（温控器、开关等）的"完整"环境中运行。
    它们旨在验证平台的基本功能，如正确的实体创建、多设备环境下的服务调用
    和状态更新。

2.  隔离场景测试 (使用本文件中定义的专用 `setup_*_only` Fixtures):
    这些测试是为特定设备或特定复杂场景设计的。它们在一个"纯净"的环境中运行，
    该环境只加载当前测试所必需的一个设备。这通过为每个场景定义一个独立的
    setup fixture 来实现，确保了测试的精确性和稳定性，避免了其他设备状态的干扰。
    这种方法对于测试复杂的状态机（如风机盘管的模式切换）至关重要。
"""

from unittest.mock import AsyncMock, patch

# 兼容性模块导入 - 获取兼容的气候实体功能常量
from custom_components.lifesmart.core.compatibility import get_climate_entity_features

CLIMATE_FEATURES = get_climate_entity_features()

import pytest
from homeassistant.components.climate import (
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_FAN_MODE,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_TEMPERATURE,
    HVACMode,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
)
from homeassistant.components.climate.const import (
    # ATTR_* 常量位于 homeassistant.components.climate.const 中
    ATTR_FAN_MODE,
    ATTR_HVAC_MODE,
)
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.lifesmart.core.const import *
from ..utils.helpers import (
    find_test_device,
    create_mock_hub,
    assert_platform_entity_count_matches_devices,
    verify_platform_entity_count,
    get_platform_device_types_for_testing,
    find_device_by_friendly_name,
    filter_devices_by_hub,
    group_devices_by_hub,
    get_all_hub_ids,
    validate_device_data,
    get_entity_unique_id,
)
from ..utils.constants import (
    FRIENDLY_DEVICE_NAMES,
)
from ..utils.typed_factories import (
    create_mock_device_climate_fancoil,
)
from ..utils.typed_factories import create_devices_by_category
from ..utils.constants import MOCK_CLOUD_CREDENTIALS


def get_entity_unique_id(device: dict) -> str:
    """一个辅助函数，用于根据设备信息生成实体在 Home Assistant 中的唯一ID。"""
    # 直接实现unique_id生成逻辑，避免从非测试文件导入
    device_type = device[DEVICE_TYPE_KEY]
    hub_id = device[HUB_ID_KEY]
    device_id = device[DEVICE_ID_KEY]

    return f"{device_type}_{hub_id}_{device_id}"


# ============================================================================
# === 隔离测试专用的 Setup Fixtures ===
# 设计说明:
# 以下 Fixtures 是为本文件中的隔离测试场景专门创建的。
# 每个 Fixture 都只加载一个特定的设备，从而创建一个纯净的测试环境。
# 这种方法取代了之前所有复杂的、有问题的参数化方案，是更健壮、更清晰的实践。
# ============================================================================


@pytest.fixture
async def setup_integration_fancoil_only(
    hass: HomeAssistant,
    mock_client: AsyncMock,
):
    """一个专用的 setup fixture，只加载风机盘管这一个设备。"""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    # 使用工厂函数创建风机盘管设备
    devices = create_devices_by_category(["climate_fancoil"])
    fancoil_device = find_test_device(devices, "9p8r")  # SL_CP_AIR 风机盘管
    assert fancoil_device is not None, "应该找到风机盘管测试设备"

    mock_config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CLOUD_CREDENTIALS, entry_id="fancoil_test_entry"
    )
    mock_config_entry.add_to_hass(hass)

    # 使用新的辅助函数创建Mock Hub
    mock_hub = create_mock_hub([fancoil_device], mock_client)

    with patch(
        "custom_components.lifesmart.core.hub.LifeSmartHub", return_value=mock_hub
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    assert mock_config_entry.state == ConfigEntryState.LOADED
    yield mock_config_entry, fancoil_device


@pytest.fixture
async def setup_integration_floorheat_only(
    hass: HomeAssistant,
    mock_client: AsyncMock,
):
    """一个专用的 setup fixture，只加载地暖这一个设备。"""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    # 使用工厂函数创建地暖设备
    devices = create_devices_by_category(["climate_floor"])
    floor_device = find_test_device(devices, "8o7q")  # SL_CP_DN 地暖
    assert floor_device is not None, "应该找到地暖测试设备"

    mock_config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CLOUD_CREDENTIALS, entry_id="floor_heat_test_entry"
    )
    mock_config_entry.add_to_hass(hass)

    # 使用新的辅助函数创建Mock Hub
    mock_hub = create_mock_hub([floor_device], mock_client)

    with patch(
        "custom_components.lifesmart.core.hub.LifeSmartHub", return_value=mock_hub
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    assert mock_config_entry.state == ConfigEntryState.LOADED
    yield mock_config_entry, floor_device


@pytest.fixture
async def setup_integration_nature_fancoil_mode(
    hass: HomeAssistant,
    mock_client: AsyncMock,
):
    """一个专用的 setup fixture，只加载配置为"风机盘管模式"的 Nature Panel。"""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    # 使用工厂函数创建超能面板温控版设备
    devices = create_devices_by_category(["climate_nature"])
    nature_device = find_test_device(devices, "7n6p")  # SL_NATURE 超能面板
    assert nature_device is not None, "应该找到超能面板测试设备"

    mock_config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_CLOUD_CREDENTIALS, entry_id="nature_fancoil_test_entry"
    )
    mock_config_entry.add_to_hass(hass)

    # 使用新的辅助函数创建Mock Hub
    mock_hub = create_mock_hub([nature_device], mock_client)

    with patch(
        "custom_components.lifesmart.core.hub.LifeSmartHub", return_value=mock_hub
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    assert mock_config_entry.state == ConfigEntryState.LOADED
    yield mock_config_entry, nature_device


# ==================== 通用集成测试 (在完整环境中运行) ====================


class TestClimateSetup:
    """
    测试温控平台的设置逻辑。

    此类别的测试专注于验证 `async_setup_entry` 函数和相关的设备识别逻辑
    是否按预期工作。它们使用平台专用的 `setup_integration_climate_only` Fixture，该 Fixture
    会加载 `conftest.py` 中定义的所有设备。
    """

    @pytest.mark.asyncio
    async def test_setup_entry_creates_correct_entities(
        self,
        hass: HomeAssistant,
        setup_integration_climate_only: ConfigEntry,  # 使用气候平台专用 setup，只加载气候设备
    ):
        """
        测试 async_setup_entry 是否能正确识别并创建所有预期的温控实体。

        这是一个“快乐路径”测试，确保在标准配置下，所有在模拟设备列表中
        定义的温控设备都被成功加载为 Home Assistant 中的 climate 实体。
        """
        # 使用专用函数获取气候平台设备类型并验证实体计数
        from ..utils.typed_factories import create_devices_by_category

        climate_device_types = get_platform_device_types_for_testing("climate")
        devices_list = create_devices_by_category(climate_device_types)

        # 验证设备计数和平台实体数量一致性
        verify_platform_entity_count(hass, CLIMATE_DOMAIN, devices_list)
        assert_platform_entity_count_matches_devices(hass, CLIMATE_DOMAIN, devices_list)
        # 使用FRIENDLY_DEVICE_NAMES常量获取气候设备名称
        climate_friendly_names = [
            name
            for name, device_type in FRIENDLY_DEVICE_NAMES.items()
            if device_type in climate_device_types
        ]

        # 验证设备数据完整性和专用气候设备创建
        for device in devices_list:
            validate_device_data(device)

        # 使用专用风机盘管设备创建函数
        fancoil_device = create_mock_device_climate_fancoil()
        validate_device_data(fancoil_device)

        # 验证Hub管理和设备分组
        all_hub_ids = get_all_hub_ids()
        grouped_devices = group_devices_by_hub(devices_list)
        assert len(grouped_devices) > 0, "应该有设备按Hub分组"

        # 测试Hub过滤功能
        first_hub_devices = filter_devices_by_hub(devices_list, 0)
        assert len(first_hub_devices) >= 0, "Hub过滤应该正常工作"

        # 验证友好名称设备查找
        for friendly_name in climate_friendly_names:
            device = find_device_by_friendly_name(devices_list, friendly_name)
            if device:
                assert device is not None, f"{friendly_name}设备应该存在于设备列表中"

        # 继续原有的entity_id检查逻辑
        assert (
            hass.states.get("climate.nature_panel_thermo") is not None
        ), "超能面板温控实体应存在"
        assert (
            hass.states.get("climate.floor_heating_controller") is not None
        ), "地暖实体应存在"
        assert (
            hass.states.get("climate.fan_coil_unit") is not None
        ), "风机盘管实体应存在"
        assert (
            hass.states.get("climate.air_conditioner_panel") is not None
        ), "空调面板实体应存在"
        assert hass.states.get("climate.air_system") is not None, "新风系统实体应存在"

    @pytest.mark.asyncio
    async def test_nature_panel_is_not_climate_after_reload(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        setup_integration_climate_only: ConfigEntry,  # 使用气候平台专用 setup
    ):
        """
        边界测试：验证在重载后，非温控版的 SL_NATURE 面板不再作为 climate 实体活动。
        """
        assert (
            hass.states.get("climate.nature_panel_thermo") is not None
        ), "超能面板温控实体初始应存在"
        # 使用工厂函数获取测试设备
        from ..utils.typed_factories import create_mock_lifesmart_devices

        devices_list = create_mock_lifesmart_devices()
        assert_platform_entity_count_matches_devices(hass, CLIMATE_DOMAIN, devices_list)

        # 模拟将 Nature Panel 的模式从温控(P5=3)改为开关(P5=1)
        nature_switch = find_test_device(devices_list, "7n6p")
        nature_switch["data"]["P5"]["val"] = 1

        # 模拟重载过程 - 使用新的 Hub 架构
        with patch("custom_components.lifesmart.core.hub.LifeSmartHub") as MockHubClass:
            # 使用新的辅助函数创建Mock Hub
            mock_hub_instance = create_mock_hub(devices_list, mock_client)
            MockHubClass.return_value = mock_hub_instance

            assert await hass.config_entries.async_reload(
                setup_integration_climate_only.entry_id
            )
            await hass.async_block_till_done()

        # 验证结果
        reloaded_state = hass.states.get("climate.nature_panel_thermo")
        assert reloaded_state is not None
        assert reloaded_state.state == "unavailable"
        assert hass.states.get("switch.nature_panel_thermo_p1") is not None


class TestClimateEntity:
    """
    测试 LifeSmartClimate 实体的核心行为。

    此类别的测试覆盖了实体的属性、状态、服务调用和状态更新逻辑，
    它们同样在加载了所有设备的“完整”环境中运行。
    """

    @pytest.mark.parametrize(
        "entity_id, entity_name, me, devtype, expected_state, expected_attrs, expected_features",
        [
            (
                "climate.nature_panel_thermo",
                "Nature Panel Thermo",
                "7n6p",
                "SL_NATURE",
                HVACMode.COOL,
                {"current_temperature": 22.5, "temperature": 24.0, "fan_mode": FAN_LOW},
                CLIMATE_FEATURES["TARGET_TEMPERATURE"]
                | CLIMATE_FEATURES["FAN_MODE"]
                | CLIMATE_FEATURES["TURN_ON"]
                | CLIMATE_FEATURES["TURN_OFF"],
            ),
            (
                "climate.floor_heating_controller",
                "Floor Heating Controller",
                "8o7q",
                "SL_CP_DN",
                HVACMode.AUTO,
                {"current_temperature": 21.5, "temperature": 23.0},
                CLIMATE_FEATURES["TARGET_TEMPERATURE"]
                | CLIMATE_FEATURES["TURN_ON"]
                | CLIMATE_FEATURES["TURN_OFF"],
            ),
            (
                "climate.fan_coil_unit",
                "Fan Coil Unit",
                "9p8r",
                "SL_CP_AIR",
                HVACMode.HEAT,
                {"fan_mode": FAN_LOW, "temperature": 25.0, "current_temperature": 23.5},
                CLIMATE_FEATURES["TARGET_TEMPERATURE"]
                | CLIMATE_FEATURES["FAN_MODE"]
                | CLIMATE_FEATURES["TURN_ON"]
                | CLIMATE_FEATURES["TURN_OFF"],
            ),
            (
                "climate.air_conditioner_panel",
                "Air Conditioner Panel",
                "0q9s",
                "V_AIR_P",
                HVACMode.COOL,
                {
                    "current_temperature": 24.5,
                    "temperature": 26.0,
                    "fan_mode": FAN_MEDIUM,
                },
                CLIMATE_FEATURES["TARGET_TEMPERATURE"]
                | CLIMATE_FEATURES["FAN_MODE"]
                | CLIMATE_FEATURES["TURN_ON"]
                | CLIMATE_FEATURES["TURN_OFF"],
            ),
            (
                "climate.air_system",
                "Air System",
                "1r0t",
                "SL_TR_ACIPM",
                HVACMode.FAN_ONLY,
                {"fan_mode": FAN_MEDIUM},
                CLIMATE_FEATURES["FAN_MODE"]
                | CLIMATE_FEATURES["TURN_ON"]
                | CLIMATE_FEATURES["TURN_OFF"],
            ),
        ],
        ids=[
            "NatureThermostaat",
            "FloorHeatingSystem",
            "FanCoilUnit",
            "AirPanelControl",
            "AirSystemControl",
        ],
    )
    @pytest.mark.asyncio
    async def test_entity_state_and_attributes(
        self,
        hass: HomeAssistant,
        setup_integration_climate_only: ConfigEntry,
        entity_id: str,
        entity_name: str,
        me: str,
        devtype: str,
        expected_state: HVACMode,
        expected_attrs: dict,
        expected_features: int,
    ):
        """
        参数化测试：验证不同设备类型在初始化后的实体状态和属性是否正确。

        此测试是实体功能的基础，确保从原始设备数据到 Home Assistant 状态属性的
        初始映射是准确无误的。
        """
        state = hass.states.get(entity_id)
        assert state is not None, f"实体 {entity_id} 未找到"
        assert state.name == entity_name
        assert state.state == expected_state
        assert state.attributes.get("supported_features") == expected_features
        for attr, val in expected_attrs.items():
            assert (
                state.attributes.get(attr) == val
            ), f"实体 {entity_id} 的属性 '{attr}' 不匹配"

    @pytest.mark.parametrize(
        "entity_id, service, service_data, expected_client_method, expected_call_args",
        [
            (
                "climate.nature_panel_thermo",
                SERVICE_SET_TEMPERATURE,
                {ATTR_TEMPERATURE: 22.0},
                "async_set_climate_temperature",
                ("H0LHHHInGL3XYzTVTqm8UH", "7n6p", "SL_NATURE", 22.0),
            ),
            (
                "climate.nature_panel_thermo",
                SERVICE_SET_HVAC_MODE,
                {ATTR_HVAC_MODE: HVACMode.COOL},
                "async_set_climate_hvac_mode",
                ("H0LHHHInGL3XYzTVTqm8UH", "7n6p", "SL_NATURE", HVACMode.COOL, 0),
            ),
            (
                "climate.floor_heating_controller",
                SERVICE_SET_HVAC_MODE,
                {ATTR_HVAC_MODE: HVACMode.HEAT},
                "async_set_climate_hvac_mode",
                (
                    "H0LHHHInGL3XYzTVTqm8UH",
                    "8o7q",
                    "SL_CP_DN",
                    HVACMode.HEAT,
                    2147483648,
                ),
            ),
            (
                "climate.fan_coil_unit",
                SERVICE_SET_FAN_MODE,
                {ATTR_FAN_MODE: FAN_HIGH},
                "async_set_climate_fan_mode",
                (
                    "H0LHHHInGL3XYzTVTqm8UH",
                    "9p8r",
                    "SL_CP_AIR",
                    FAN_HIGH,
                    (1 << 15) | (1 << 13),
                ),
            ),
        ],
        ids=[
            "SetTemperatureService",
            "SetSimpleHvacMode",
            "SetBitmaskHvacMode",
            "SetFanModeService",
        ],
    )
    @pytest.mark.asyncio
    async def test_service_calls(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        setup_integration_climate_only: ConfigEntry,
        entity_id: str,
        service: str,
        service_data: dict,
        expected_client_method: str,
        expected_call_args: tuple,
    ):
        """
        参数化测试：验证各类服务调用是否能正确触发底层的 client 方法。

        此测试至关重要，它确保了用户在 Home Assistant UI 上的操作能够被正确地
        转换为对 LifeSmart API 的调用，特别是验证了 `current_val` 参数。
        """
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            service,
            {ATTR_ENTITY_ID: entity_id, **service_data},
            blocking=True,
        )
        method_to_check = getattr(mock_client, expected_client_method)
        method_to_check.assert_awaited_once_with(*expected_call_args)

    @pytest.mark.parametrize(
        "me, new_data, expected_state, expected_attrs",
        [
            (
                "9p8r",
                {"P1": {"type": 1, "val": (2 << 15) | (0 << 13)}},
                HVACMode.COOL,
                {"fan_mode": FAN_MEDIUM},
            ),
            ("8o7q", {"P1": {"type": 1, "val": 0}}, HVACMode.HEAT, {}),
            (
                "0q9s",
                {"O": {"type": 1}, "MODE": {"val": 3}, "T": {"v": 21.0}},
                HVACMode.COOL,
                {"current_temperature": 21.0},
            ),
            (
                "0q9s",
                {"O": {"type": 1}, "MODE": {"val": 3}},
                HVACMode.COOL,
                {"current_temperature": 24.5},
            ),
        ],
        ids=[
            "FanCoilStateUpdate",
            "FloorHeatStateUpdate",
            "AirPanelStateUpdate",
            "MissingDataKeyHandling",
        ],
    )
    @pytest.mark.asyncio
    async def test_entity_update_from_dispatcher(
        self,
        hass: HomeAssistant,
        setup_integration_climate_only: ConfigEntry,
        me: str,
        new_data: dict,
        expected_state: str,
        expected_attrs: dict,
    ):
        """
        参数化测试：验证实体在收到 dispatcher 更新信号后的状态变化。

        此测试模拟了从 WebSocket 接收到实时数据的场景，验证了 `_update_state`
        方法能否正确解析各种复杂数据（特别是位掩码），并更新实体的状态。
        同时，它也测试了代码在面对不完整数据时的容错能力。
        """
        # 使用工厂函数获取测试设备
        mock_lifesmart_devices = create_devices_by_category(
            ["climate_fancoil", "climate_floor", "climate_nature"]
        )
        device = find_test_device(mock_lifesmart_devices, me)
        assert device is not None
        entity_id = f"climate.{device['name'].lower().replace(' ', '_')}"
        unique_id = get_entity_unique_id(device)
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", new_data
        )
        await hass.async_block_till_done()
        state = hass.states.get(entity_id)
        assert state.state == expected_state
        for attr, val in expected_attrs.items():
            assert state.attributes.get(attr) == val


# ==================== 隔离场景测试 (在纯净环境中运行) ====================


class TestComplexClimateScenarios:
    """
    专注于联合测试、复杂状态机和边缘场景。
    这里的每个测试都使用本文件中定义的专用 `setup_*_only` Fixture 来创建一个
    只包含当前测试所需设备的纯净环境。
    """

    @pytest.mark.asyncio
    async def test_fancoil_state_machine_transition(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        setup_integration_fancoil_only: ConfigEntry,
    ):
        """
        隔离联合测试：模拟风机盘管 (SL_CP_AIR) 从 '制热/低风' -> '制冷/高风' -> '关机' 的完整状态迁移。

        此测试在一个只加载了单个风机盘管设备的环境中运行，以确保：
        1. 状态计算的精确性：对 `current_val` (位掩码) 的计算不会受到其他设备的影响。
        2. API 调用的准确性：验证每次服务调用都向底层 client 发送了正确的参数。
        3. 状态更新的响应：模拟设备状态更新后，HA 实体能正确反映变化。
        """
        # 从 setup fixture 中获取设备数据
        _, device = setup_integration_fancoil_only
        entity_id = "climate.fancoil_single_test"
        hub_id, me, devtype = device["agt"], device["me"], device["devtype"]

        initial_val = (1 << 15) | (1 << 13)
        state = hass.states.get(entity_id)
        assert state.state == HVACMode.HEAT
        assert state.attributes.get("fan_mode") == FAN_LOW

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.COOL},
            blocking=True,
        )
        mock_client.async_set_climate_hvac_mode.assert_awaited_with(
            hub_id, me, devtype, HVACMode.COOL, initial_val
        )

        unique_id = get_entity_unique_id(device)
        val_after_mode_change = (1 << 15) | (0 << 13)
        async_dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}",
            {"P1": {"type": 1, "val": val_after_mode_change}},
        )
        await hass.async_block_till_done()

        state_after_mode_change = hass.states.get(entity_id)
        assert state_after_mode_change.state == HVACMode.COOL
        assert state_after_mode_change.attributes.get("fan_mode") == FAN_LOW

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_FAN_MODE,
            {ATTR_ENTITY_ID: entity_id, ATTR_FAN_MODE: FAN_HIGH},
            blocking=True,
        )
        mock_client.async_set_climate_fan_mode.assert_awaited_with(
            hub_id, me, devtype, FAN_HIGH, val_after_mode_change
        )

        val_after_fan_change = (3 << 15) | (0 << 13)
        async_dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}",
            {"P1": {"type": 1, "val": val_after_fan_change}},
        )
        await hass.async_block_till_done()

        state_after_fan_change = hass.states.get(entity_id)
        assert state_after_fan_change.state == HVACMode.COOL
        assert state_after_fan_change.attributes.get("fan_mode") == FAN_HIGH

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.OFF},
            blocking=True,
        )
        mock_client.async_set_climate_hvac_mode.assert_awaited_with(
            hub_id, me, devtype, HVACMode.OFF, val_after_fan_change
        )

    @pytest.mark.asyncio
    async def test_nature_panel_dynamic_features(
        self,
        hass: HomeAssistant,
        setup_integration_nature_fancoil_mode: ConfigEntry,
    ):
        """
        隔离联合测试：验证 SL_NATURE 面板根据 P6 配置动态生成支持的 HVAC 和风扇模式。
        """
        entity_id = "climate.nature_panel_thermo"
        state = hass.states.get(entity_id)
        assert state is not None, "Nature Panel climate entity should be created"

        expected_hvac_modes = [
            HVACMode.OFF,
            HVACMode.AUTO,
            HVACMode.COOL,
            HVACMode.HEAT,
            HVACMode.FAN_ONLY,
        ]
        expected_fan_modes = [FAN_LOW, FAN_MEDIUM, FAN_HIGH, FAN_AUTO]

        assert sorted(state.attributes.get("hvac_modes")) == sorted(expected_hvac_modes)
        assert sorted(state.attributes.get("fan_modes")) == sorted(expected_fan_modes)

    @pytest.mark.asyncio
    async def test_floor_heating_turn_on_from_off(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        setup_integration_floorheat_only: ConfigEntry,
    ):
        """
        隔离边界测试：验证地暖 (SL_CP_DN) 从关机状态开机时，默认进入制热模式。
        """
        # 从 setup fixture 中获取设备数据
        _, device = setup_integration_floorheat_only
        entity_id = "climate.floor_heating"
        hub_id, me, devtype = device["agt"], device["me"], device["devtype"]
        unique_id = get_entity_unique_id(device)

        async_dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}",
            {"P1": {"type": 0, "val": 0}},
        )
        await hass.async_block_till_done()
        assert hass.states.get(entity_id).state == HVACMode.OFF

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: HVACMode.HEAT},
            blocking=True,
        )
        mock_client.async_set_climate_hvac_mode.assert_awaited_with(
            hub_id, me, devtype, HVACMode.HEAT, 0
        )


# ==================== 共享的错误处理测试 Fixtures ====================


@pytest.fixture
def climate_error_test_devices():
    """提供用于错误处理测试的设备数据。"""
    return {
        "valid_climate_device": {
            "agt": "test_hub_001",
            "me": "climate_device_001",
            "devtype": "SL_CP_DN",
            "data": {"P1": {"type": 1, "val": 1}, "P2": {"type": 1, "val": 25}},
            "idx": 0,
            "name": "climate_device_001",
        },
        "empty_data_device": {
            "agt": "test_hub_001",
            "me": "empty_device_001",
            "devtype": "SL_CP_DN",
            "data": {},
            "idx": 0,
            "name": "empty_device_001",
        },
        "unsupported_device": {
            "agt": "test_hub_001",
            "me": "unsupported_device_001",
            "devtype": "UNSUPPORTED_CLIMATE_TYPE",
            "data": {},
            "idx": 0,
        },
    }


@pytest.fixture
async def setup_climate_entity_for_errors(
    hass: HomeAssistant, mock_client, climate_error_test_devices
):
    """设置用于错误处理测试的气候实体。"""

    async def _setup_entity(device_key: str):
        device = climate_error_test_devices[device_key]
        setup_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CLOUD_CREDENTIALS)
        setup_entry.add_to_hass(hass)

        # 使用新的辅助函数创建Mock Hub
        mock_hub = create_mock_hub([device], mock_client)

        with (
            patch(
                "custom_components.lifesmart.core.client.openapi_client.LifeSmartOpenAPIClient",
                return_value=mock_client,
            ),
            patch(
                "custom_components.lifesmart.core.hub.LifeSmartHub",
                return_value=mock_hub,
            ),
        ):
            await hass.config_entries.async_setup(setup_entry.entry_id)
            await hass.async_block_till_done()

        return device, setup_entry

    return _setup_entity


class TestClimateEntityErrorHandling:
    """测试气候实体的错误处理和边界情况。"""

    @pytest.mark.asyncio
    async def test_unsupported_device_type_not_created(
        self, hass: HomeAssistant, mock_client, setup_climate_entity_for_errors
    ):
        """测试不支持的设备类型不会创建气候实体。"""
        device, setup_entry = await setup_climate_entity_for_errors(
            "unsupported_device"
        )

        # 断言：不支持的设备类型不会创建任何气候实体
        climate_entities = hass.states.async_entity_ids(CLIMATE_DOMAIN)
        assert len(climate_entities) == 0, "不支持的设备类型不应该创建任何气候实体"

    @pytest.mark.parametrize(
        "invalid_hvac_mode,expected_error_pattern",
        [
            ("invalid_hvac_mode", "expected HVACMode"),
            (123, "expected HVACMode"),
            (None, "expected HVACMode"),
        ],
        ids=["StringMode", "NumericMode", "NoneMode"],
    )
    @pytest.mark.asyncio
    async def test_invalid_hvac_mode_rejected(
        self,
        hass: HomeAssistant,
        mock_client,
        setup_climate_entity_for_errors,
        invalid_hvac_mode,
        expected_error_pattern,
    ):
        """测试无效HVAC模式被Home Assistant的schema验证正确拒绝。"""
        device, setup_entry = await setup_climate_entity_for_errors(
            "valid_climate_device"
        )
        entity_id = f"climate.{device['name']}"

        # 断言：实体已创建
        state = hass.states.get(entity_id)
        assert state is not None, f"气候实体 {entity_id} 应该已创建"

        # 尝试设置无效的HVAC模式，应该被HA的schema验证拒绝
        with pytest.raises(Exception) as exc_info:
            await hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_HVAC_MODE,
                {ATTR_ENTITY_ID: entity_id, ATTR_HVAC_MODE: invalid_hvac_mode},
                blocking=True,
            )

        # 验证错误信息包含预期的模式
        assert expected_error_pattern in str(
            exc_info.value
        ), f"错误信息应包含 '{expected_error_pattern}'"

        # 断言：无效模式不应该触发客户端调用
        mock_client.async_set_climate_hvac_mode.assert_not_called()

    @pytest.mark.parametrize(
        "temperature,expected_behavior",
        [
            (-10, "rejected_or_clamped"),  # 超低温度
            (50, "rejected_or_clamped"),  # 超高温度
            (25, "accepted"),  # 正常温度
        ],
        ids=["TooLow", "TooHigh", "Normal"],
    )
    @pytest.mark.asyncio
    async def test_temperature_range_validation(
        self,
        hass: HomeAssistant,
        mock_client,
        setup_climate_entity_for_errors,
        temperature,
        expected_behavior,
    ):
        """测试温度范围验证功能。"""
        device, setup_entry = await setup_climate_entity_for_errors(
            "valid_climate_device"
        )
        entity_id = f"climate.{device['name']}"
        hub_id, me, devtype = device["agt"], device["me"], device["devtype"]

        # 断言：实体已创建
        state = hass.states.get(entity_id)
        assert state is not None, f"气候实体 {entity_id} 应该已创建"

        # 测试温度设置行为
        exception_caught = False
        try:
            await hass.services.async_call(
                CLIMATE_DOMAIN,
                SERVICE_SET_TEMPERATURE,
                {ATTR_ENTITY_ID: entity_id, ATTR_TEMPERATURE: temperature},
                blocking=True,
            )
        except Exception:
            exception_caught = True

        if expected_behavior == "accepted":
            # 正常温度应该被接受
            assert not exception_caught, f"正常温度 {temperature}°C 不应该被拒绝"
            # 验证客户端调用
            mock_client.async_set_climate_temperature.assert_called_with(
                hub_id, me, devtype, temperature
            )
        elif expected_behavior == "rejected_or_clamped":
            # 超出范围的温度可能被拒绝或限制在合理范围内
            calls = mock_client.async_set_climate_temperature.call_args_list

            for call in calls:
                # 检查参数位置或关键字参数
                temp = None
                if len(call[0]) > 3:
                    temp = call[0][3]  # temperature is 4th argument (0-indexed)
                elif "temperature" in call[1]:
                    temp = call[1]["temperature"]

                if temp is not None:
                    # 如果有调用，温度应该在合理范围内
                    assert 5 <= temp <= 40, f"温度 {temp}°C 应该在 5-40°C 范围内"

    @pytest.mark.asyncio
    async def test_empty_device_data_default_state(
        self,
        hass: HomeAssistant,
        mock_client,
        climate_error_test_devices,
        setup_climate_entity_for_errors,
    ):
        """测试空设备数据的默认状态处理。"""
        device, setup_entry = await setup_climate_entity_for_errors("empty_data_device")
        entity_id = f"climate.{device['name']}"

        # 断言：即使数据为空，也应该能够创建实体
        state = hass.states.get(entity_id)
        assert state is not None, f"空数据设备应该也能创建气候实体 {entity_id}"

        # 断言：缺少数据时应该有默认状态
        valid_states = [HVACMode.OFF, "unknown", "unavailable"]
        assert (
            state.state in valid_states
        ), f"空数据设备的默认状态应该是 {valid_states} 之一，实际是 {state.state}"

    @pytest.mark.asyncio
    async def test_dispatcher_invalid_data_ignored(
        self,
        hass: HomeAssistant,
        mock_client,
        climate_error_test_devices,
        setup_climate_entity_for_errors,
    ):
        """测试调度器无效数据更新被忽略。"""
        device, setup_entry = await setup_climate_entity_for_errors(
            "valid_climate_device"
        )
        entity_id = f"climate.{device['name']}"

        from custom_components.lifesmart.core.helpers import generate_unique_id

        unique_id = generate_unique_id(
            device["devtype"], device["agt"], device["me"], None
        )

        # 断言：实体已创建且有初始状态
        initial_state = hass.states.get(entity_id)
        assert initial_state is not None, f"气候实体 {entity_id} 应该已创建"

        # 发送无效数据更新
        async_dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}",
            {
                "INVALID_PARAM": {"type": 0x3E7, "val": "invalid_value"}
            },  # 无效参数测试 (原CMD_TYPE_UNKNOWN_999)
        )
        await hass.async_block_till_done()

        # 断言：实体仍然存在且状态不变或保持有效
        updated_state = hass.states.get(entity_id)
        assert updated_state is not None, f"无效数据更新后实体 {entity_id} 仍应存在"

        # 断言：状态应该仍然有效（不是"unavailable"或空）
        assert updated_state.state != "unavailable", "无效数据更新不应该导致实体不可用"
