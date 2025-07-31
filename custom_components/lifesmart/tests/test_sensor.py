"""
Unit tests for the LifeSmart sensor platform (Restored and Enhanced).

This test suite provides comprehensive coverage, including:
- Verification of entity creation and exclusion logic.
- Broad "happy path" property tests for all major sensor types.
- Specific tests for boundary conditions (zero, null, invalid data).
- Validation of entity availability logic.
- Coverage of different real-time update formats ('v' vs 'val').
- **NEW**: Coverage for ambiguous 'val' key in WebSocket updates.

Note: Helper function tests have been moved to test_helpers.py to avoid duplication.
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


@pytest.mark.asyncio
async def test_sensor_creation_and_exclusion(
    hass: HomeAssistant,
    setup_integration: ConfigEntry,
    mock_lifesmart_devices: list,
):
    """
    /**
     * test_sensor_creation_and_exclusion() - 测试传感器的创建和排除逻辑。
     * @hass: Home Assistant 的核心实例。
     * @setup_integration: 已设置的集成 ConfigEntry。
     * @mock_lifesmart_devices: 模拟的设备列表。
     *
     * 此测试验证了所有预期的传感器实体是否被正确创建，同时确保
     * 在配置中被排除的设备（通过 me 或 agt）确实没有被创建为实体。
     */
    """
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

    assert expected_entities.issubset(created_entities)

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
        entity_registry.async_get_entity_id("sensor", DOMAIN, unique_id_excluded_hub)
        is None
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    (
        "device_me",
        "sub_key",
        "expected_name_suffix",
        "expected_class",
        "expected_unit",
        "expected_state_class",
        "expected_value",
    ),
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
)
async def test_lifesmart_sensor_properties(
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
    """
    /**
     * test_lifesmart_sensor_properties() - 测试传感器的核心属性。
     *
     * 此参数化测试恢复了对多种传感器的广泛覆盖，验证每个实体在初始化后
     * 是否具有正确的名称、设备类别、单位、状态类别和初始值。
     */
    """
    raw_device = find_test_device(mock_lifesmart_devices, device_me)
    entity_id = (
        f"sensor.{raw_device['name'].lower().replace(' ', '_')}_{sub_key.lower()}"
    )
    state = hass.states.get(entity_id)
    assert state is not None, f"Entity {entity_id} not found"
    assert state.name == f"{raw_device['name']} {expected_name_suffix}"
    assert state.attributes.get("device_class") == (
        expected_class.value if expected_class else None
    )
    assert state.attributes.get("state_class") == (
        expected_state_class.value if expected_state_class else None
    )
    assert state.attributes.get("unit_of_measurement") == expected_unit
    assert float(state.state) == expected_value


@pytest.mark.asyncio
async def test_sensor_boundary_and_invalid_data(
    hass: HomeAssistant, setup_integration: ConfigEntry
):
    """
    /**
     * test_sensor_boundary_and_invalid_data() - 测试边界条件和无效数据。
     *
     * 此测试验证了传感器在接收到异常数据时的行为是否健壮：
     * 1. 零值 (`val: 0`) 应被正确处理。
     * 2. 空数据 (`{}`) 应使实体状态变为 'unknown'。
     * 3. 无效数据类型 (string) 应使实体状态变为 'unknown' 而不崩溃。
     * 4. 完全缺失的子键不应创建实体。
     */
    """
    state_zero = hass.states.get("sensor.boundary_test_sensor_t")
    assert state_zero is not None and float(state_zero.state) == 0.0

    state_empty = hass.states.get("sensor.boundary_test_sensor_h")
    assert state_empty is not None and state_empty.state == STATE_UNKNOWN

    state_invalid = hass.states.get("sensor.boundary_test_sensor_z")
    assert state_invalid is not None and state_invalid.state == STATE_UNKNOWN

    assert hass.states.get("sensor.boundary_test_sensor_v") is None


@pytest.mark.asyncio
async def test_sensor_becomes_unavailable(
    hass: HomeAssistant, setup_integration: ConfigEntry
):
    """
    /**
     * test_sensor_becomes_unavailable() - 测试实体的可用性逻辑。
     *
     * 模拟场景：一个设备在初始设置时存在，但在后续的全局刷新中从
     * API 响应中消失。
     * 预期结果：对应的 Home Assistant 实体状态应变为 'unavailable'。
     */
    """
    entity_id = "sensor.living_room_env_t"

    assert hass.states.get(entity_id).state != STATE_UNAVAILABLE

    device_list = hass.data[DOMAIN][setup_integration.entry_id]["devices"]
    hass.data[DOMAIN][setup_integration.entry_id]["devices"] = [
        d for d in device_list if d.get(DEVICE_ID_KEY) != "sensor_env"
    ]

    async_dispatcher_send(hass, LIFESMART_SIGNAL_UPDATE_ENTITY)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_UNAVAILABLE


@pytest.mark.asyncio
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
        ("sensor.main_door_lock_bat", "sensor_lock_battery_BAT", 88, {"val": 50}, 50),
    ],
    ids=["temp_update_with_val", "power_update_with_v", "battery_update_with_val"],
)
async def test_sensor_update_logic_coverage(
    hass: HomeAssistant,
    setup_integration: ConfigEntry,
    mock_lifesmart_devices: list,
    entity_id,
    unique_id_suffix,
    initial_value,
    update_payload,
    expected_value,
):
    """
    /**
     * test_sensor_update_logic_coverage() - 覆盖不同的实时更新逻辑。
     *
     * 此测试验证了 `_handle_update` 方法能正确处理两种主要的数据格式：
     * - 包含 'val' 键的原始数据，需要转换。
     * - 包含 'v' 键的最终数据，无需转换。
     */
    """
    state = hass.states.get(entity_id)
    assert state is not None and float(state.state) == initial_value

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

    assert float(hass.states.get(entity_id).state) == expected_value


@pytest.mark.asyncio
async def test_update_with_ambiguous_val_key(
    hass: HomeAssistant, setup_integration: ConfigEntry, mock_lifesmart_devices: list
):
    """
    /**
     * test_update_with_ambiguous_val_key() - 验证对模糊 'val' 键的处理。
     *
     * 此测试专门用于验证 issue 中描述的场景：WebSocket 推送一个使用 'val'
     * 键的最终值（如 26），而不是原始值（如 260）。代码应能正确识别
     * 这种情况，避免将其错误地处理为 2.6。
     */
    """
    entity_id = "sensor.living_room_env_t"
    device_me = "sensor_env"
    sub_key = "T"

    # 1. 获取 dispatcher 所需的 unique_id
    raw_device = find_test_device(mock_lifesmart_devices, device_me)
    unique_id = generate_unique_id(
        raw_device[DEVICE_TYPE_KEY],
        raw_device[HUB_ID_KEY],
        raw_device[DEVICE_ID_KEY],
        sub_key,
    )

    # 2. 模拟推送一个小的 'val' 值 (模糊情况)
    async_dispatcher_send(
        hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", {"val": 26}
    )
    await hass.async_block_till_done()
    assert (
        float(hass.states.get(entity_id).state) == 26.0
    ), "Should handle small 'val' as final value"

    # 3. 模拟推送一个大的 'val' 值 (清晰的原始值)
    async_dispatcher_send(
        hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", {"val": 275}
    )
    await hass.async_block_till_done()
    assert (
        float(hass.states.get(entity_id).state) == 27.5
    ), "Should handle large 'val' as raw value"
