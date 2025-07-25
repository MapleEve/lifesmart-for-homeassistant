"""
Unit tests for the LifeSmart sensor platform.
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
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.lifesmart import generate_unique_id
from custom_components.lifesmart.const import *
from custom_components.lifesmart.sensor import _is_sensor_subdevice

pytestmark = pytest.mark.asyncio


def find_device(devices: list, me: str):
    """Helper to find a specific device from the mock list by its 'me' id."""
    return next((d for d in devices if d.get(DEVICE_ID_KEY) == me), None)


async def test_async_setup_entry_creates_sensors(
    hass: HomeAssistant,
    setup_integration: ConfigEntry,
):
    """Test successful creation of sensor entities based on shared fixtures."""
    entity_registry = er.async_get(hass)

    # 筛选出所有的 lifesmart sensor 实体
    lifesmart_sensors = [
        entry
        for entry in entity_registry.entities.values()
        if entry.platform == DOMAIN and entry.domain == "sensor"
    ]

    # Expected sensors from conftest.py's mock_lifesmart_devices:
    # sensor_env: 4 (T, H, Z, V)
    # sensor_co2: 1 (P3)
    # sensor_power_plug: 2 (P2, P3)
    # sensor_lock_battery: 1 (BAT)
    # sensor_switch_battery: 1 (P4)
    # climate_nature_thermo: 1 (P4)
    # Total = 10 sensors
    # 注意：conftest.py 中有一个被排除的设备 sw_oe3c，它也有 sensor，但不应被创建
    # 还有一个在被排除的 hub 上的设备，也不应被创建
    assert len(lifesmart_sensors) == 10, "Incorrect number of sensor entities created"


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
            "sensor_switch_battery",
            "P4",
            "P4",
            SensorDeviceClass.BATTERY,
            PERCENTAGE,
            SensorStateClass.MEASUREMENT,
            92,
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
    """Test all derived properties of the LifeSmartSensor entity using shared fixtures."""
    raw_device = find_device(mock_lifesmart_devices, device_me)
    assert raw_device, f"Device '{device_me}' not found in mock_lifesmart_devices"

    device_name_slug = raw_device["name"].lower().replace(" ", "_")
    sub_key_slug = sub_key.lower()
    entity_id = f"sensor.{device_name_slug}_{sub_key_slug}"

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
    # Home Assistant state is always a string, so we need to convert for comparison
    assert float(state.state) == expected_value

    entity_registry = er.async_get(hass)
    entry = entity_registry.async_get(entity_id)
    assert entry is not None
    expected_unique_id = generate_unique_id(
        raw_device[DEVICE_TYPE_KEY], raw_device[HUB_ID_KEY], device_me, sub_key
    )
    assert entry.unique_id == expected_unique_id


async def test_lifesmart_sensor_updates(
    hass: HomeAssistant,
    setup_integration: ConfigEntry,
    mock_lifesmart_devices: list,
):
    """Test real-time and global refresh updates."""
    raw_device = find_device(mock_lifesmart_devices, "sensor_env")
    sub_key = "T"
    device_name_slug = raw_device["name"].lower().replace(" ", "_")
    sub_key_slug = sub_key.lower()
    entity_id = f"sensor.{device_name_slug}_{sub_key_slug}"

    unique_id = generate_unique_id(
        raw_device[DEVICE_TYPE_KEY],
        raw_device[HUB_ID_KEY],
        raw_device[DEVICE_ID_KEY],
        sub_key,
    )

    # 1. Test real-time update (WebSocket push with 'v' for direct value)
    async_dispatcher_send(
        hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", {"v": 26.0}
    )
    await hass.async_block_till_done()
    assert float(hass.states.get(entity_id).state) == 26.0

    # 2. Test real-time update (raw 'val', requires conversion)
    async_dispatcher_send(
        hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", {"val": 265}
    )
    await hass.async_block_till_done()
    assert float(hass.states.get(entity_id).state) == 26.5

    # 3. Test global refresh
    # Modify the device data in hass.data
    device_list = hass.data[DOMAIN][setup_integration.entry_id]["devices"]
    for i, device in enumerate(device_list):
        if device["me"] == "sensor_env":
            # Create a copy to avoid modifying the original fixture data
            updated_device = device.copy()
            updated_device[DEVICE_DATA_KEY] = updated_device[DEVICE_DATA_KEY].copy()
            updated_device[DEVICE_DATA_KEY][sub_key] = {"val": 270}
            device_list[i] = updated_device
            break

    async_dispatcher_send(hass, LIFESMART_SIGNAL_UPDATE_ENTITY)
    await hass.async_block_till_done()
    assert float(hass.states.get(entity_id).state) == 27.0


# --- This test remains unchanged as it's a pure function test ---
@pytest.mark.parametrize(
    ("device_type", "sub_key", "expected"),
    [
        ("SL_CP_DN", "P5", True),
        ("SL_CP_VL", "P6", True),
        ("SL_TR_ACIPM", "P4", True),
        ("SL_SC_THL", "T", True),
        ("SL_SC_THL", "P5", True),
        ("SL_SC_CH", "P1", True),
        ("SL_SC_GAS", "P2", True),
        ("SL_LK_LS", "BAT", True),
        ("SL_CT_C", "P8", True),
        ("SL_OE_3C", "P2", True),
        ("SL_OL", "EV", True),
        ("SL_SC_CN", "P1", True),
        ("ELIQ_EM", "EPA", True),
        ("SL_P_A", "T", True),
        ("SL_S_WFS", "V", True),
        ("SL_SW_IF1", "P4", True),
        ("SL_SC_BB_V2", "P2", True),
        ("SL_CP_DN", "P1", False),
        ("SL_LK_LS", "P1", False),
        ("SL_ETDOOR", "P1", False),
        ("UNKNOWN_TYPE", "P1", False),
    ],
)
def test_is_sensor_subdevice(device_type, sub_key, expected):
    """Test the sub-device validation logic for all branches."""
    assert _is_sensor_subdevice(device_type, sub_key) == expected
