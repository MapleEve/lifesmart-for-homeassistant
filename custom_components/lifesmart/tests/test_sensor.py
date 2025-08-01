"""
针对 LifeSmart 传感器 (Sensor) 平台的单元测试。

此测试套件提供全面的覆盖，包括：
- 验证实体创建和排除逻辑
- 广泛的传感器类型属性测试
- 边界条件测试（零值、空值、无效数据）
- 实体可用性逻辑验证
- 不同实时更新格式覆盖（'v' vs 'val'）
- 状态更新和dispatcher处理验证

注意：辅助函数测试已移至 test_helpers.py 以避免重复。
"""

import pytest
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    LIGHT_LUX,
    PERCENTAGE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.lifesmart.const import *
from custom_components.lifesmart.helpers import (
    generate_unique_id,
)
from .test_utils import find_test_device


class TestSensorSetup:
    """测试传感器平台的设置逻辑。"""

    @pytest.mark.asyncio
    async def test_setup_creates_correct_entities(
        self,
        hass: HomeAssistant,
        setup_integration: ConfigEntry,
        mock_lifesmart_devices: list,
    ):
        """测试传感器设置是否创建了正确的实体。"""
        entity_registry = er.async_get(hass)

        expected_entities = {
            "sensor.living_room_env_t",
            "sensor.living_room_env_h",
            "sensor.living_room_env_z",
            "sensor.living_room_env_v",
            "sensor.study_co2_p3",
            "sensor.washing_machine_plug_p2",
            "sensor.washing_machine_plug_p3",
            "sensor.main_door_lock_bat",
            "sensor.nature_panel_thermo_p4",
            "sensor.boundary_test_sensor_t",
            "sensor.boundary_test_sensor_h",
            "sensor.boundary_test_sensor_z",
        }

        created_entities = {
            entry.entity_id
            for entry in entity_registry.entities.values()
            if entry.platform == DOMAIN and entry.domain == "sensor"
        }

        assert expected_entities.issubset(
            created_entities
        ), "所有预期的传感器实体都应该被创建"

    @pytest.mark.asyncio
    async def test_setup_respects_exclusions(
        self,
        hass: HomeAssistant,
        setup_integration: ConfigEntry,
        mock_lifesmart_devices: list,
    ):
        """测试设置是否正确排除了配置中指定的设备。"""
        entity_registry = er.async_get(hass)

        excluded_device_on_hub = find_test_device(
            mock_lifesmart_devices, "device_on_excluded_hub"
        )
        unique_id_excluded_hub = generate_unique_id(
            excluded_device_on_hub[DEVICE_TYPE_KEY],
            excluded_device_on_hub[HUB_ID_KEY],
            excluded_device_on_hub[DEVICE_ID_KEY],
            "T",
        )
        assert (
            entity_registry.async_get_entity_id(
                "sensor", DOMAIN, unique_id_excluded_hub
            )
            is None
        ), "被排除的设备不应该创建传感器实体"


class TestSensorEntity:
    """测试 LifeSmart 传感器实体的核心行为。"""

    @pytest.mark.parametrize(
        "device_me, sub_key, expected_name_suffix, expected_class, expected_unit, expected_state_class, expected_value",
        [
            (
                "sensor_env",
                "T",
                "T",
                SensorDeviceClass.TEMPERATURE,
                UnitOfTemperature.CELSIUS,
                SensorStateClass.MEASUREMENT,
                25.5,
            ),
            (
                "sensor_env",
                "H",
                "H",
                SensorDeviceClass.HUMIDITY,
                PERCENTAGE,
                SensorStateClass.MEASUREMENT,
                60.1,
            ),
            (
                "sensor_env",
                "Z",
                "Z",
                SensorDeviceClass.ILLUMINANCE,
                LIGHT_LUX,
                SensorStateClass.MEASUREMENT,
                1000,
            ),
            (
                "sensor_env",
                "V",
                "V",
                SensorDeviceClass.VOLTAGE,
                UnitOfElectricPotential.VOLT,
                SensorStateClass.MEASUREMENT,
                95,
            ),
            (
                "sensor_lock_battery",
                "BAT",
                "BAT",
                SensorDeviceClass.BATTERY,
                PERCENTAGE,
                SensorStateClass.MEASUREMENT,
                88,
            ),
            (
                "sensor_power_plug",
                "P2",
                "P2",
                SensorDeviceClass.ENERGY,
                UnitOfEnergy.KILO_WATT_HOUR,
                SensorStateClass.TOTAL_INCREASING,
                1.5,
            ),
            (
                "sensor_power_plug",
                "P3",
                "P3",
                SensorDeviceClass.POWER,
                UnitOfPower.WATT,
                SensorStateClass.MEASUREMENT,
                1200,
            ),
            (
                "sensor_co2",
                "P3",
                "P3",
                SensorDeviceClass.CO2,
                CONCENTRATION_PARTS_PER_MILLION,
                SensorStateClass.MEASUREMENT,
                800,
            ),
        ],
        ids=[
            "TemperatureSensorProperties",
            "HumiditySensorProperties",
            "IlluminanceSensorProperties",
            "VoltageSensorProperties",
            "BatterySensorProperties",
            "EnergySensorProperties",
            "PowerSensorProperties",
            "Co2SensorProperties",
        ],
    )
    @pytest.mark.asyncio
    async def test_sensor_properties_and_initial_state(
        self,
        hass: HomeAssistant,
        setup_integration: ConfigEntry,
        mock_lifesmart_devices: list,
        device_me,
        sub_key,
        expected_name_suffix,
        expected_class,
        expected_unit,
        expected_state_class,
        expected_value,
    ):
        """测试传感器实体的属性和初始状态是否正确。"""
        raw_device = find_test_device(mock_lifesmart_devices, device_me)
        entity_id = (
            f"sensor.{raw_device['name'].lower().replace(' ', '_')}_{sub_key.lower()}"
        )
        state = hass.states.get(entity_id)
        assert state is not None, f"实体 {entity_id} 未找到"
        assert (
            state.name == f"{raw_device['name']} {expected_name_suffix}"
        ), f"实体名称应为 {raw_device['name']} {expected_name_suffix}"
        assert state.attributes.get("device_class") == (
            expected_class.value if expected_class else None
        ), f"设备类别应为 {expected_class}"
        assert state.attributes.get("state_class") == (
            expected_state_class.value if expected_state_class else None
        ), f"状态类别应为 {expected_state_class}"
        assert (
            state.attributes.get("unit_of_measurement") == expected_unit
        ), f"测量单位应为 {expected_unit}"
        assert float(state.state) == expected_value, f"初始值应为 {expected_value}"

    @pytest.mark.asyncio
    async def test_sensor_boundary_and_invalid_data(
        self, hass: HomeAssistant, setup_integration: ConfigEntry
    ):
        """测试传感器在边界条件和无效数据时的处理。"""
        # 零值应被正确处理
        state_zero = hass.states.get("sensor.boundary_test_sensor_t")
        assert (
            state_zero is not None and float(state_zero.state) == 0.0
        ), "零值应被正确处理为 0.0"

        # 空数据应使实体状态变为 'unknown'
        state_empty = hass.states.get("sensor.boundary_test_sensor_h")
        assert (
            state_empty is not None and state_empty.state == STATE_UNKNOWN
        ), "空数据应使实体状态变为 unknown"

        # 无效数据类型应使实体状态变为 'unknown' 而不崩溃
        state_invalid = hass.states.get("sensor.boundary_test_sensor_z")
        assert (
            state_invalid is not None and state_invalid.state == STATE_UNKNOWN
        ), "无效数据类型应使实体状态变为 unknown"

        # 完全缺失的子键不应创建实体
        assert (
            hass.states.get("sensor.boundary_test_sensor_v") is None
        ), "完全缺失的子键不应创建实体"

    @pytest.mark.asyncio
    async def test_sensor_becomes_unavailable(
        self, hass: HomeAssistant, setup_integration: ConfigEntry
    ):
        """测试传感器实体在设备消失时变为不可用状态。"""
        entity_id = "sensor.living_room_env_t"

        # 确认实体初始状态不是不可用
        assert (
            hass.states.get(entity_id).state != STATE_UNAVAILABLE
        ), "实体初始状态不应为不可用"

        # 模拟设备从API响应中消失
        device_list = hass.data[DOMAIN][setup_integration.entry_id]["devices"]
        hass.data[DOMAIN][setup_integration.entry_id]["devices"] = [
            d for d in device_list if d.get(DEVICE_ID_KEY) != "sensor_env"
        ]

        # 触发全局刷新
        async_dispatcher_send(hass, LIFESMART_SIGNAL_UPDATE_ENTITY)
        await hass.async_block_till_done()

        # 验证实体状态变为不可用
        assert (
            hass.states.get(entity_id).state == STATE_UNAVAILABLE
        ), "设备消失后实体状态应变为不可用"

    @pytest.mark.parametrize(
        "entity_id, unique_id_suffix, initial_value, update_payload, expected_value",
        [
            ("sensor.living_room_env_t", "sensor_env_T", 25.5, {"val": 288}, 28.8),
            (
                "sensor.washing_machine_plug_p3",
                "sensor_power_plug_P3",
                1200,
                {"v": 1500.5},
                1500.5,
            ),
            (
                "sensor.main_door_lock_bat",
                "sensor_lock_battery_BAT",
                88,
                {"val": 50},
                50,
            ),
        ],
        ids=["TemperatureValueUpdate", "PowerVoltageUpdate", "BatteryValueUpdate"],
    )
    @pytest.mark.asyncio
    async def test_sensor_update_from_dispatcher(
        self,
        hass: HomeAssistant,
        setup_integration: ConfigEntry,
        mock_lifesmart_devices: list,
        entity_id,
        unique_id_suffix,
        initial_value,
        update_payload,
        expected_value,
    ):
        """测试传感器实体在收到dispatcher更新信号后的状态变化。"""
        state = hass.states.get(entity_id)
        assert (
            state is not None and float(state.state) == initial_value
        ), f"实体 {entity_id} 初始值应为 {initial_value}"

        device_me, sub_key = unique_id_suffix.rsplit("_", 1)
        raw_device = find_test_device(mock_lifesmart_devices, device_me)
        unique_id = generate_unique_id(
            raw_device[DEVICE_TYPE_KEY],
            raw_device[HUB_ID_KEY],
            raw_device[DEVICE_ID_KEY],
            sub_key,
        )

        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", update_payload
        )
        await hass.async_block_till_done()

        assert (
            float(hass.states.get(entity_id).state) == expected_value
        ), f"更新后状态值应为 {expected_value}"


class TestComplexSensorScenarios:
    """测试传感器的复杂场景和边界情况。"""

    @pytest.mark.asyncio
    async def test_update_with_ambiguous_val_key(
        self,
        hass: HomeAssistant,
        setup_integration: ConfigEntry,
        mock_lifesmart_devices: list,
    ):
        """验证对模糊'val'键的智能处理。"""
        entity_id = "sensor.living_room_env_t"
        device_me = "sensor_env"
        sub_key = "T"

        # 获取dispatcher所需的unique_id
        raw_device = find_test_device(mock_lifesmart_devices, device_me)
        unique_id = generate_unique_id(
            raw_device[DEVICE_TYPE_KEY],
            raw_device[HUB_ID_KEY],
            raw_device[DEVICE_ID_KEY],
            sub_key,
        )

        # 模拟推送一个小的'val'值（模糊情况）
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", {"val": 26}
        )
        await hass.async_block_till_done()
        assert (
            float(hass.states.get(entity_id).state) == 26.0
        ), "应将小的'val'值视为最终值"

        # 模拟推送一个大的'val'值（明确的原始值）
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", {"val": 275}
        )
        await hass.async_block_till_done()
        assert (
            float(hass.states.get(entity_id).state) == 27.5
        ), "应将大的'val'值视为原始值并转换"
