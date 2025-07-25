"""
Unit tests for the LifeSmart sensor platform.
This version uses shared fixtures from conftest.py and correct mocking strategies.
"""

from unittest.mock import AsyncMock, MagicMock

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

from custom_components.lifesmart.const import *
from custom_components.lifesmart.sensor import (
    LifeSmartSensor,
    async_setup_entry,
    _is_sensor_subdevice,
)

pytestmark = pytest.mark.asyncio


# --- Helper to find a device in the shared fixture ---
def find_device(devices: list, me: str):
    """Helper to find a specific device from the mock list by its 'me' id."""
    return next((d for d in devices if d.get(DEVICE_ID_KEY) == me), None)


# --- TESTS for async_setup_entry ---


async def test_async_setup_entry_creates_sensors(
    hass: HomeAssistant,
    mock_client: AsyncMock,
    mock_config_entry: ConfigEntry,
    mock_lifesmart_devices: list,
):
    """Test successful creation of sensor entities based on shared fixtures."""
    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            "devices": mock_lifesmart_devices,
            "client": mock_client,
            "exclude_devices": ["excluded_device"],
            "exclude_hubs": ["excluded_hub"],
        }
    }
    async_add_entities = AsyncMock()

    await async_setup_entry(hass, mock_config_entry, async_add_entities)

    # Expected sensors from conftest.py's mock_lifesmart_devices:
    # sensor_env: 4 (T, H, Z, V)
    # sensor_co2: 1 (P3)
    # sensor_power_plug: 2 (P2, P3)
    # sensor_lock_battery: 1 (BAT)
    # sensor_switch_battery: 1 (P4)
    # sensor_nature_thermo: 1 (P4)
    # Total = 4 + 1 + 2 + 1 + 1 + 1 = 10 sensors
    assert async_add_entities.call_count == 1
    assert (
        len(async_add_entities.call_args[0][0]) == 10
    ), "Incorrect number of sensor entities created"


async def test_async_setup_entry_handles_no_devices(
    hass: HomeAssistant, mock_client: AsyncMock, mock_config_entry: ConfigEntry
):
    """Test setup with no devices."""
    hass.data[DOMAIN] = {
        mock_config_entry.entry_id: {
            "devices": [],
            "client": mock_client,
            "exclude_devices": [],
            "exclude_hubs": [],
        }
    }
    async_add_entities = AsyncMock()
    await async_setup_entry(hass, mock_config_entry, async_add_entities)
    async_add_entities.assert_called_once_with([])


# --- TESTS for _is_sensor_subdevice ---


@pytest.mark.parametrize(
    ("device_type", "sub_key", "expected"),
    [
        # Positive cases from each block (using static strings instead of indexing sets)
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
        # Negative cases
        ("SL_CP_DN", "P1", False),
        ("SL_LK_LS", "P1", False),
        ("SL_ETDOOR", "P1", False),
        ("UNKNOWN_TYPE", "P1", False),
    ],
)
def test_is_sensor_subdevice(device_type, sub_key, expected):
    """Test the sub-device validation logic for all branches."""
    assert _is_sensor_subdevice(device_type, sub_key) == expected


# --- TESTS for LifeSmartSensor Entity ---


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
        # Temperature from sensor_env
        (
            "sensor_env",
            "T",
            "T",
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            SensorStateClass.MEASUREMENT,
            25.5,
        ),
        # Humidity from sensor_env
        (
            "sensor_env",
            "H",
            "H",
            SensorDeviceClass.HUMIDITY,
            PERCENTAGE,
            SensorStateClass.MEASUREMENT,
            60.1,
        ),
        # Illuminance from sensor_env
        (
            "sensor_env",
            "Z",
            "Z",
            SensorDeviceClass.ILLUMINANCE,
            LIGHT_LUX,
            SensorStateClass.MEASUREMENT,
            1000,
        ),
        # Voltage from sensor_env
        (
            "sensor_env",
            "V",
            "V",
            SensorDeviceClass.VOLTAGE,
            UnitOfElectricPotential.VOLT,
            SensorStateClass.MEASUREMENT,
            95,
        ),
        # Battery from lock
        (
            "sensor_lock_battery",
            "BAT",
            "BAT",
            SensorDeviceClass.BATTERY,
            PERCENTAGE,
            SensorStateClass.MEASUREMENT,
            88,
        ),
        # Battery from switch
        (
            "sensor_switch_battery",
            "P4",
            "P4",
            SensorDeviceClass.BATTERY,
            PERCENTAGE,
            SensorStateClass.MEASUREMENT,
            92,
        ),
        # Energy from power plug
        (
            "sensor_power_plug",
            "P2",
            "P2",
            SensorDeviceClass.ENERGY,
            UnitOfEnergy.KILO_WATT_HOUR,
            SensorStateClass.TOTAL_INCREASING,
            1.5,
        ),
        # Power from power plug
        (
            "sensor_power_plug",
            "P3",
            "P3",
            SensorDeviceClass.POWER,
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            1200,
        ),
        # CO2 from CO2 sensor
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
def test_lifesmart_sensor_properties(
    hass: HomeAssistant,
    mock_client: AsyncMock,
    mock_config_entry: ConfigEntry,
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

    sub_data = raw_device[DEVICE_DATA_KEY][sub_key]
    expected_name = f"{raw_device[DEVICE_NAME_KEY]} {expected_name_suffix}"

    # Calculate expected object_id based on the new logic
    device_name_slug = raw_device[DEVICE_NAME_KEY].lower().replace(" ", "_")
    sub_key_slug = sub_key.lower()
    expected_object_id = f"{device_name_slug}_{sub_key_slug}"

    sensor = LifeSmartSensor(
        raw_device=raw_device,
        sub_device_key=sub_key,
        sub_device_data=sub_data,
        client=mock_client,
        entry_id=mock_config_entry.entry_id,
    )
    sensor.hass = hass

    assert sensor.name == expected_name
    assert sensor.object_id == expected_object_id
    assert sensor.device_class == expected_class
    assert sensor.native_unit_of_measurement == expected_unit
    assert sensor.state_class == expected_state_class
    assert sensor.native_value == expected_value
    from custom_components.lifesmart import generate_unique_id

    assert sensor.unique_id == generate_unique_id(
        raw_device[DEVICE_TYPE_KEY], raw_device[HUB_ID_KEY], device_me, sub_key
    )


async def test_lifesmart_sensor_updates(
    hass: HomeAssistant,
    mock_client: AsyncMock,
    mock_config_entry: ConfigEntry,
    mock_lifesmart_devices: list,
):
    """Test real-time and global refresh updates."""
    # Setup initial device and sensor
    raw_device = find_device(mock_lifesmart_devices, "sensor_env")
    sub_key = "T"
    sub_data = raw_device[DEVICE_DATA_KEY][sub_key]

    sensor = LifeSmartSensor(
        raw_device=raw_device,
        sub_device_key=sub_key,
        sub_device_data=sub_data,
        client=mock_client,
        entry_id=mock_config_entry.entry_id,
    )
    sensor.hass = hass
    sensor.async_write_ha_state = MagicMock()

    # 1. Test real-time update (WebSocket push with 'v' for direct value)
    update_data_ws = {"msg": {sub_key: {"v": 26.0}}}
    await sensor._handle_update(update_data_ws)
    assert sensor.native_value == 26.0
    sensor.async_write_ha_state.assert_called_once()

    # 2. Test real-time update (raw 'val', requires conversion)
    sensor.async_write_ha_state.reset_mock()
    update_data_raw = {sub_key: {"val": 265}}  # 26.5 for temp
    await sensor._handle_update(update_data_raw)
    assert sensor.native_value == 26.5
    sensor.async_write_ha_state.assert_called_once()

    # 3. Test global refresh
    sensor.async_write_ha_state.reset_mock()
    updated_device = raw_device.copy()
    updated_device[DEVICE_DATA_KEY] = {sub_key: {"val": 270}}  # 27.0 for temp

    hass.data[DOMAIN] = {mock_config_entry.entry_id: {"devices": [updated_device]}}
    await sensor._handle_global_refresh()
    assert sensor.native_value == 27.0
    sensor.async_write_ha_state.assert_called_once()
