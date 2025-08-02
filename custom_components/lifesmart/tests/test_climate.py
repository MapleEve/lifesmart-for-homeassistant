"""
针对 LifeSmart 温控 (Climate) 平台的单元和集成测试。

此测试套件旨在全面验证 LifeSmartClimate 实体的行为。它被设计为在单个文件中
运行，包含了两种类型的测试：

1.  通用集成测试 (使用全局 `setup_integration` Fixture):
    这些测试在一个加载了所有模拟设备（温控器、开关等）的"完整"环境中运行。
    它们旨在验证平台的基本功能，如正确的实体创建、多设备环境下的服务调用
    和状态更新。

2.  隔离场景测试 (使用本文件中定义的专用 `setup_*_only` Fixtures):
    这些测试是为特定设备或特定复杂场景设计的。它们在一个"纯净"的环境中运行，
    该环境只加载当前测试所必需的一个设备。这通过为每个场景定义一个独立的
    setup fixture 来实现，确保了测试的精确性和稳定性，避免了其他设备状态的干扰。
    这种方法对于测试复杂的状态机（如风机盘管的模式切换）至关重要。
"""

from unittest.mock import AsyncMock, MagicMock, patch

# 兼容性模块导入 - 获取兼容的气候实体功能常量
from custom_components.lifesmart.compatibility import get_climate_entity_features

CLIMATE_FEATURES = get_climate_entity_features()

import pytest
from homeassistant.components.climate import (
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_FAN_MODE,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_TEMPERATURE,
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

from custom_components.lifesmart.const import *
from custom_components.lifesmart.helpers import (
    generate_unique_id,
)
from .test_utils import find_test_device


def get_entity_unique_id(device: dict) -> str:
    """一个辅助函数，用于根据设备信息生成实体在 Home Assistant 中的唯一ID。"""
    return generate_unique_id(
        device[DEVICE_TYPE_KEY], device[HUB_ID_KEY], device[DEVICE_ID_KEY], None
    )


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
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_device_climate_fancoil: dict,  # 直接从 conftest.py 注入单个设备
):
    """一个专用的 setup fixture，只加载风机盘管这一个设备。"""
    mock_config_entry.add_to_hass(hass)
    # 只使用注入的单个设备来创建测试环境了
    devices = [mock_device_climate_fancoil]

    # 创建一个模拟的 hub 对象
    from unittest.mock import AsyncMock

    mock_hub = MagicMock()
    mock_hub.async_setup = AsyncMock(return_value=True)
    mock_hub.get_devices.return_value = devices
    mock_hub.get_client.return_value = mock_client
    mock_hub.get_exclude_config.return_value = (set(), set())
    mock_hub.async_unload = AsyncMock(return_value=None)

    with patch("custom_components.lifesmart.LifeSmartHub", return_value=mock_hub):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    assert mock_config_entry.state == ConfigEntryState.LOADED
    yield mock_config_entry


@pytest.fixture
async def setup_integration_floorheat_only(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_device_climate_floor_heat: dict,
):
    """一个专用的 setup fixture，只加载地暖这一个设备。"""
    mock_config_entry.add_to_hass(hass)
    devices = [mock_device_climate_floor_heat]

    # 创建一个模拟的 hub 对象
    from unittest.mock import AsyncMock

    mock_hub = MagicMock()
    mock_hub.async_setup = AsyncMock(return_value=True)
    mock_hub.get_devices.return_value = devices
    mock_hub.get_client.return_value = mock_client
    mock_hub.get_exclude_config.return_value = (set(), set())
    mock_hub.async_unload = AsyncMock(return_value=None)

    with patch("custom_components.lifesmart.LifeSmartHub", return_value=mock_hub):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    assert mock_config_entry.state == ConfigEntryState.LOADED
    yield mock_config_entry


@pytest.fixture
async def setup_integration_nature_fancoil_mode(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_device_climate_nature_fancoil: dict,
):
    """一个专用的 setup fixture，只加载配置为"风机盘管模式"的 Nature Panel。"""
    mock_config_entry.add_to_hass(hass)
    devices = [mock_device_climate_nature_fancoil]

    # 创建一个模拟的 hub 对象
    from unittest.mock import AsyncMock

    mock_hub = MagicMock()
    mock_hub.async_setup = AsyncMock(return_value=True)
    mock_hub.get_devices.return_value = devices
    mock_hub.get_client.return_value = mock_client
    mock_hub.get_exclude_config.return_value = (set(), set())
    mock_hub.async_unload = AsyncMock(return_value=None)

    with patch("custom_components.lifesmart.LifeSmartHub", return_value=mock_hub):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    assert mock_config_entry.state == ConfigEntryState.LOADED
    yield mock_config_entry


# ==================== 通用集成测试 (在完整环境中运行) ====================


class TestClimateSetup:
    """
    测试温控平台的设置逻辑。

    此类别的测试专注于验证 `async_setup_entry` 函数和相关的设备识别逻辑
    是否按预期工作。它们使用全局的 `setup_integration` Fixture，该 Fixture
    会加载 `conftest.py` 中定义的所有设备。
    """

    @pytest.mark.asyncio
    async def test_setup_entry_creates_correct_entities(
        self,
        hass: HomeAssistant,
        setup_integration: ConfigEntry,  # 使用全局 setup，加载所有设备
    ):
        """
        测试 async_setup_entry 是否能正确识别并创建所有预期的温控实体。

        这是一个“快乐路径”测试，确保在标准配置下，所有在模拟设备列表中
        定义的温控设备都被成功加载为 Home Assistant 中的 climate 实体。
        """
        assert (
            len(hass.states.async_entity_ids(CLIMATE_DOMAIN)) == 5
        ), "应该创建5个温控实体"
        assert (
            hass.states.get("climate.nature_panel_thermo") is not None
        ), "超能面板温控实体应存在"
        assert hass.states.get("climate.floor_heating") is not None, "地暖实体应存在"
        assert (
            hass.states.get("climate.fan_coil_unit") is not None
        ), "风机盘管实体应存在"
        assert hass.states.get("climate.air_panel") is not None, "空调面板实体应存在"
        assert hass.states.get("climate.air_system") is not None, "新风系统实体应存在"

    @pytest.mark.asyncio
    async def test_nature_panel_is_not_climate_after_reload(
        self,
        hass: HomeAssistant,
        mock_lifesmart_devices: list,
        mock_client: AsyncMock,
        setup_integration: ConfigEntry,  # 使用全局 setup
    ):
        """
        边界测试：验证在重载后，非温控版的 SL_NATURE 面板不再作为 climate 实体活动。
        """
        assert (
            hass.states.get("climate.nature_panel_thermo") is not None
        ), "超能面板温控实体初始应存在"
        assert (
            len(hass.states.async_entity_ids(CLIMATE_DOMAIN)) == 5
        ), "应该有5个温控实体"

        # 模拟将 Nature Panel 的模式从温控(P5=3)改为开关(P5=1)
        nature_switch = find_test_device(
            mock_lifesmart_devices, "climate_nature_thermo"
        )
        nature_switch["data"]["P5"]["val"] = 1

        # 模拟重载过程 - 使用新的 Hub 架构
        with patch("custom_components.lifesmart.LifeSmartHub") as MockHubClass:
            mock_hub_instance = MockHubClass.return_value
            # async_setup 需要返回 AsyncMock
            from unittest.mock import AsyncMock

            mock_hub_instance.async_setup = AsyncMock(return_value=True)
            mock_hub_instance.get_devices.return_value = mock_lifesmart_devices
            mock_hub_instance.get_client.return_value = mock_client
            mock_hub_instance.get_exclude_config.return_value = (set(), set())
            mock_hub_instance.async_unload = AsyncMock(return_value=None)

            assert await hass.config_entries.async_reload(setup_integration.entry_id)
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
                "climate_nature_thermo",
                "SL_NATURE",
                HVACMode.AUTO,
                {"current_temperature": 28.0, "temperature": 26.0, "fan_mode": FAN_LOW},
                CLIMATE_FEATURES["TARGET_TEMPERATURE"]
                | CLIMATE_FEATURES["FAN_MODE"]
                | CLIMATE_FEATURES["TURN_ON"]
                | CLIMATE_FEATURES["TURN_OFF"],
            ),
            (
                "climate.floor_heating",
                "Floor Heating",
                "climate_floor_heat",
                "SL_CP_DN",
                HVACMode.AUTO,
                {"current_temperature": 22.5, "temperature": 25.0},
                CLIMATE_FEATURES["TARGET_TEMPERATURE"]
                | CLIMATE_FEATURES["TURN_ON"]
                | CLIMATE_FEATURES["TURN_OFF"],
            ),
            (
                "climate.fan_coil_unit",
                "Fan Coil Unit",
                "climate_fancoil",
                "SL_CP_AIR",
                HVACMode.HEAT,
                {"fan_mode": FAN_LOW, "temperature": 24.0, "current_temperature": 26.0},
                CLIMATE_FEATURES["TARGET_TEMPERATURE"]
                | CLIMATE_FEATURES["FAN_MODE"]
                | CLIMATE_FEATURES["TURN_ON"]
                | CLIMATE_FEATURES["TURN_OFF"],
            ),
            (
                "climate.air_panel",
                "Air Panel",
                "climate_airpanel",
                "V_AIR_P",
                HVACMode.OFF,
                {"current_temperature": 23.0, "temperature": 25.0, "fan_mode": FAN_LOW},
                CLIMATE_FEATURES["TARGET_TEMPERATURE"]
                | CLIMATE_FEATURES["FAN_MODE"]
                | CLIMATE_FEATURES["TURN_ON"]
                | CLIMATE_FEATURES["TURN_OFF"],
            ),
            (
                "climate.air_system",
                "Air System",
                "climate_airsystem",
                "SL_TR_ACIPM",
                HVACMode.FAN_ONLY,
                {"fan_mode": FAN_LOW},
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
        setup_integration: ConfigEntry,
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
                ("hub_climate", "climate_nature_thermo", "SL_NATURE", 22.0),
            ),
            (
                "climate.nature_panel_thermo",
                SERVICE_SET_HVAC_MODE,
                {ATTR_HVAC_MODE: HVACMode.COOL},
                "async_set_climate_hvac_mode",
                ("hub_climate", "climate_nature_thermo", "SL_NATURE", HVACMode.COOL, 0),
            ),
            (
                "climate.floor_heating",
                SERVICE_SET_HVAC_MODE,
                {ATTR_HVAC_MODE: HVACMode.HEAT},
                "async_set_climate_hvac_mode",
                (
                    "hub_climate",
                    "climate_floor_heat",
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
                    "hub_climate",
                    "climate_fancoil",
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
        setup_integration: ConfigEntry,
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
                "climate_fancoil",
                {"P1": {"type": 1, "val": (2 << 15) | (0 << 13)}},
                HVACMode.COOL,
                {"fan_mode": FAN_MEDIUM},
            ),
            ("climate_floor_heat", {"P1": {"type": 1, "val": 0}}, HVACMode.HEAT, {}),
            (
                "climate_airpanel",
                {"O": {"type": 1}, "MODE": {"val": 3}, "T": {"v": 21.0}},
                HVACMode.COOL,
                {"current_temperature": 21.0},
            ),
            (
                "climate_airpanel",
                {"O": {"type": 1}, "MODE": {"val": 3}},
                HVACMode.COOL,
                {"current_temperature": 23.0},
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
        setup_integration: ConfigEntry,
        mock_lifesmart_devices: list,
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
        mock_device_climate_fancoil: dict,
        setup_integration_fancoil_only: ConfigEntry,
    ):
        """
        隔离联合测试：模拟风机盘管 (SL_CP_AIR) 从 '制热/低风' -> '制冷/高风' -> '关机' 的完整状态迁移。

        此测试在一个只加载了单个风机盘管设备的环境中运行，以确保：
        1. 状态计算的精确性：对 `current_val` (位掩码) 的计算不会受到其他设备的影响。
        2. API 调用的准确性：验证每次服务调用都向底层 client 发送了正确的参数。
        3. 状态更新的响应：模拟设备状态更新后，HA 实体能正确反映变化。
        """
        entity_id = "climate.fan_coil_unit"
        device = mock_device_climate_fancoil
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
        mock_device_climate_floor_heat: dict,
        setup_integration_floorheat_only: ConfigEntry,
    ):
        """
        隔离边界测试：验证地暖 (SL_CP_DN) 从关机状态开机时，默认进入制热模式。
        """
        entity_id = "climate.floor_heating"
        device = mock_device_climate_floor_heat
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
