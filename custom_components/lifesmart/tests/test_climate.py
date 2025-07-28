"""
针对 LifeSmart 温控 (Climate) 平台的单元和集成测试。

此测试套件旨在全面验证 LifeSmartClimate 实体的行为，包括：
- 正确的实体创建和平台设置逻辑。
- 在不同设备类型下，实体属性和支持特性的初始化是否正确。
- 对 Home Assistant 服务调用（如设置温度、模式、风速）的响应是否正确。
- 通过 dispatcher 接收到状态更新后，实体状态是否能被正确解析和更新，
  特别是对于依赖复杂位掩码的设备。
- 对边界条件（如设备类型判断、数据缺失）的处理是否健壮。
"""

from unittest.mock import AsyncMock, patch

import pytest
# 导入 Home Assistant 温控组件所需的核心常量和服务名称
from homeassistant.components.climate import (
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_FAN_MODE,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_TEMPERATURE,
    ClimateEntityFeature,
)
# ATTR_* 常量位于 homeassistant.components.climate.const 中，而不是 homeassistant.const
from homeassistant.components.climate.const import (
    ATTR_FAN_MODE,
    ATTR_HVAC_MODE,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

# 导入项目内部的工具函数和常量
from custom_components.lifesmart import generate_unique_id
from custom_components.lifesmart.const import *

# 自动为所有测试应用 asyncio 标记
pytestmark = pytest.mark.asyncio


def find_device(devices: list, me: str):
    """一个辅助函数，用于根据设备的 'me' ID 从模拟设备列表中查找特定设备。"""
    return next((d for d in devices if d.get(DEVICE_ID_KEY) == me), None)


def get_entity_unique_id(device: dict) -> str:
    """一个辅助函数，用于根据设备信息生成实体在 Home Assistant 中的唯一ID。"""
    return generate_unique_id(
        device[DEVICE_TYPE_KEY], device[HUB_ID_KEY], device[DEVICE_ID_KEY], None
    )


# ==================== 测试套件 ====================


class TestClimateSetup:
    """
    测试温控平台的设置逻辑。

    此类别的测试专注于验证 `async_setup_entry` 函数和相关的设备识别逻辑
    是否按预期工作。
    """

    async def test_setup_entry_creates_correct_entities(
        self,
        hass: HomeAssistant,
        setup_integration: ConfigEntry,
    ):
        """
        测试 async_setup_entry 是否能正确识别并创建所有预期的温控实体。

        这是一个“快乐路径”测试，确保在标准配置下，所有在模拟设备列表中
        定义的温控设备都被成功加载为 Home Assistant 中的 climate 实体。
        """
        assert len(hass.states.async_entity_ids(CLIMATE_DOMAIN)) == 5
        assert hass.states.get("climate.nature_panel_thermo") is not None
        assert hass.states.get("climate.floor_heating") is not None
        assert hass.states.get("climate.fan_coil_unit") is not None
        assert hass.states.get("climate.air_panel") is not None
        assert hass.states.get("climate.air_system") is not None

    async def test_nature_panel_is_not_climate_after_reload(
        self,
        hass: HomeAssistant,
        mock_lifesmart_devices: list,
        mock_client: AsyncMock,
        setup_integration: ConfigEntry,
    ):
        """
        边界测试：验证在重载后，非温控版的 SL_NATURE 面板不再作为 climate 实体活动。

        此测试验证了 `_is_climate_device` 函数中的特殊逻辑。
        测试流程：
        1. 首先通过 `setup_integration` fixture 完整加载一次集成。
        2. 确认初始状态下，温控版的 Nature Panel climate 实体存在。
        3. 修改模拟设备数据，将 Nature Panel 变为开关版。
        4. 调用 `async_reload` 重新加载配置条目。
        5. 确认重载后，Nature Panel 的 climate 实体状态变为 'unavailable'，
           并且其对应的 switch 实体被正确创建。
        """
        # 步骤 1 & 2: 确认初始状态
        # `setup_integration` 已经完成了初始加载
        assert (
            hass.states.get("climate.nature_panel_thermo") is not None
        ), "初始加载后，温控面板实体应存在"
        assert len(hass.states.async_entity_ids(CLIMATE_DOMAIN)) == 5

        # 步骤 3: 修改模拟数据
        nature_switch = find_device(mock_lifesmart_devices, "climate_nature_thermo")
        # 将 P5 的值修改为 1，这表示它现在应该被识别为开关面板
        nature_switch["data"]["P5"]["val"] = 1

        # 步骤 4: 使用修改后的设备列表重新加载集成
        with patch(
            "custom_components.lifesmart.LifeSmartClient", return_value=mock_client
        ):
            mock_client.get_all_device_async.return_value = mock_lifesmart_devices
            assert await hass.config_entries.async_reload(setup_integration.entry_id)
            await hass.async_block_till_done()

        # 步骤 5: 断言最终状态
        # --- 核心修复：修正断言逻辑 ---
        # 旧的 climate 实体不会完全消失，而是会变为 'unavailable' 状态。
        # 这是 Home Assistant 在实体被移除时的标准行为。
        reloaded_state = hass.states.get("climate.nature_panel_thermo")
        assert reloaded_state is not None, "实体对象在重载后依然存在于状态机中"
        assert (
            reloaded_state.state == "unavailable"
        ), "重载后，旧的 climate 实体状态应变为 'unavailable'"

        # --- 增强测试：验证新的 switch 实体是否被创建 ---
        # 由于 P5 的值变了，现在应该为这个设备创建 switch 实体。
        # 注意：实体ID可能与原始名称不同，取决于 switch 平台的命名规则。
        # 我们在这里检查一个预期的开关实体是否存在。
        assert (
            hass.states.get("switch.nature_panel_thermo_p1") is not None
        ), "重载后，应创建对应的 switch 实体"


class TestClimateEntity:
    """
    测试 LifeSmartClimate 实体的核心行为。

    此类别的测试覆盖了实体的属性、状态、服务调用和状态更新逻辑。
    """

    @pytest.mark.parametrize(
        "entity_id, entity_name, me, devtype, expected_state, expected_attrs, expected_features",
        [
            # 测试用例 1: SL_NATURE (超能面板)，一个功能复杂的设备
            (
                "climate.nature_panel_thermo",
                "Nature Panel Thermo",
                "climate_nature_thermo",
                "SL_NATURE",
                HVACMode.AUTO,
                {
                    "current_temperature": 28.0,
                    "temperature": 26.0,
                    "fan_mode": FAN_LOW,
                },
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.FAN_MODE
                | ClimateEntityFeature.TURN_ON
                | ClimateEntityFeature.TURN_OFF,
            ),
            # 测试用例 2: SL_CP_DN (地暖)，使用位掩码确定模式
            (
                "climate.floor_heating",
                "Floor Heating",
                "climate_floor_heat",
                "SL_CP_DN",
                HVACMode.AUTO,
                {"current_temperature": 22.5, "temperature": 25.0},
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.TURN_ON
                | ClimateEntityFeature.TURN_OFF,
            ),
            # 测试用例 3: SL_CP_AIR (风机盘管)，使用位掩码确定模式和风速
            (
                "climate.fan_coil_unit",
                "Fan Coil Unit",
                "climate_fancoil",
                "SL_CP_AIR",
                HVACMode.HEAT,
                {
                    "fan_mode": FAN_LOW,
                    "temperature": 24.0,
                    "current_temperature": 26.0,
                },
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.FAN_MODE
                | ClimateEntityFeature.TURN_ON
                | ClimateEntityFeature.TURN_OFF,
            ),
            # 测试用例 4: V_AIR_P (空调面板)，一个状态解析相对简单的设备
            (
                "climate.air_panel",
                "Air Panel",
                "climate_airpanel",
                "V_AIR_P",
                HVACMode.OFF,
                {"current_temperature": 23.0, "temperature": 25.0, "fan_mode": FAN_LOW},
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.FAN_MODE
                | ClimateEntityFeature.TURN_ON
                | ClimateEntityFeature.TURN_OFF,
            ),
            # 测试用例 5: SL_TR_ACIPM (新风系统)，仅支持风扇模式
            (
                "climate.air_system",
                "Air System",
                "climate_airsystem",
                "SL_TR_ACIPM",
                HVACMode.FAN_ONLY,
                {"fan_mode": FAN_LOW},
                ClimateEntityFeature.FAN_MODE
                | ClimateEntityFeature.TURN_ON
                | ClimateEntityFeature.TURN_OFF,
            ),
        ],
        ids=["NatureThermo", "FloorHeating", "FanCoil", "AirPanel", "AirSystem"],
    )
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
        expected_features: ClimateEntityFeature,
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
            # 测试用例 1: 设置温度
            (
                "climate.nature_panel_thermo",
                SERVICE_SET_TEMPERATURE,
                {ATTR_TEMPERATURE: 22.0},
                "async_set_climate_temperature",
                ("hub_climate", "climate_nature_thermo", "SL_NATURE", 22.0),
            ),
            # 测试用例 2: 设置HVAC模式 (简单设备)
            (
                "climate.nature_panel_thermo",
                SERVICE_SET_HVAC_MODE,
                {ATTR_HVAC_MODE: HVACMode.COOL},
                "async_set_climate_hvac_mode",
                # 验证 current_val 被正确传递 (对于此设备，初始为0)
                ("hub_climate", "climate_nature_thermo", "SL_NATURE", HVACMode.COOL, 0),
            ),
            # 测试用例 3: 设置HVAC模式 (依赖位掩码的设备)
            (
                "climate.floor_heating",
                SERVICE_SET_HVAC_MODE,
                {ATTR_HVAC_MODE: HVACMode.HEAT},
                "async_set_climate_hvac_mode",
                # 验证从 _p1_val 获取的 current_val 被正确传递
                (
                    "hub_climate",
                    "climate_floor_heat",
                    "SL_CP_DN",
                    HVACMode.HEAT,
                    2147483648,
                ),
            ),
            # 测试用例 4: 设置风扇模式 (依赖位掩码的设备)
            (
                "climate.fan_coil_unit",
                SERVICE_SET_FAN_MODE,
                {ATTR_FAN_MODE: FAN_HIGH},
                "async_set_climate_fan_mode",
                # 验证从 _p1_val 获取的 current_val 被正确传递
                (
                    "hub_climate",
                    "climate_fancoil",
                    "SL_CP_AIR",
                    FAN_HIGH,
                    (1 << 15) | (1 << 13),
                ),
            ),
        ],
        ids=["SetTemp", "SetHvacSimple", "SetHvacBitmask", "SetFanMode"],
    )
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
        转换为对 LifeSmart API 的调用，特别是验证了 `current_val` 参数
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
            # 测试用例 1: SL_CP_AIR, 通过位掩码更新模式和风速
            (
                "climate_fancoil",
                {
                    "P1": {"type": 1, "val": (2 << 15) | (0 << 13)}
                },  # 风速中(2), 模式冷(0)
                HVACMode.COOL,
                {"fan_mode": FAN_MEDIUM},
            ),
            # 测试用例 2: SL_CP_DN, 通过位掩码更新模式
            (
                "climate_floor_heat",
                {"P1": {"type": 1, "val": 0}},  # 模式热 (bit 31 为 0)
                HVACMode.HEAT,
                {},
            ),
            # 测试用例 3: V_AIR_P, 简单的值更新
            (
                "climate_airpanel",
                {
                    "O": {"type": 1},
                    "MODE": {"val": 3},
                    "T": {"v": 21.0},
                },  # 开，模式冷，温度21
                HVACMode.COOL,
                {"current_temperature": 21.0},
            ),
            # 测试用例 4: 边界测试 - 数据键缺失
            (
                "climate_airpanel",
                {"O": {"type": 1}, "MODE": {"val": 3}},  # 缺失 "T" (当前温度) 键
                HVACMode.COOL,
                {"current_temperature": 23.0},  # 属性应保持旧值，不应报错
            ),
        ],
        ids=["FanCoilUpdate", "FloorHeatUpdate", "AirPanelUpdate", "MissingDataKey"],
    )
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
        device = find_device(mock_lifesmart_devices, me)
        assert device is not None
        entity_id = f"climate.{device['name'].lower().replace(' ', '_')}"

        # 发送 dispatcher 更新信号
        unique_id = get_entity_unique_id(device)
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", new_data
        )
        await hass.async_block_till_done()

        # 验证状态和属性是否已按预期更新
        state = hass.states.get(entity_id)
        assert state.state == expected_state
        for attr, val in expected_attrs.items():
            assert state.attributes.get(attr) == val
