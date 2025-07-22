# tests/test_sensor.py

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    LIGHT_LUX,
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfSoundPressure,
    UnitOfElectricCurrent,
)
from homeassistant.core import HomeAssistant

from custom_components.lifesmart.const import (
    DOMAIN,
    CLIMATE_TYPES,
    EV_SENSOR_TYPES,
    POWER_METER_PLUG_TYPES,
    SMART_PLUG_TYPES,
    LOCK_TYPES,
    SUPPORTED_SWITCH_TYPES,
)
from custom_components.lifesmart.sensor import (
    LifeSmartSensor,
    async_setup_entry,
    _is_sensor_subdevice,
)


# --- MOCK DATA FIXTURES ---


@pytest.fixture
def mock_lifesmart_client():
    """Mock the LifeSmart API client."""
    return MagicMock()


@pytest.fixture
def mock_config_entry():
    """Mock the config entry."""
    entry = MagicMock()
    entry.entry_id = "test_entry_id"
    return entry


# A diverse list of mock devices to test various scenarios
MOCK_DEVICES = [
    # 1. Standard Env Sensor (Temp, Humidity, Illuminance, Voltage)
    {
        "agt": "hub1",
        "me": "device1",
        "devtype": "SL_SC_THL",
        "name": "Living Room Env",
        "data": {
            "T": {"v": 25.5, "val": 255},
            "H": {"v": 60.1, "val": 601},
            "Z": {"v": 1000},
            "V": {"val": 95},
        },
    },
    # 2. CO2 Sensor
    {
        "agt": "hub1",
        "me": "device2",
        "devtype": "SL_SC_CA",
        "name": "Study CO2",
        "data": {
            "P1": {"val": 220},  # Temp
            "P2": {"val": 550},  # Humidity
            "P3": {"val": 800},  # CO2
            "P4": {"val": 100},  # Battery
        },
    },
    # 3. Power Meter Plug
    {
        "agt": "hub1",
        "me": "device3",
        "devtype": "SL_OE_3C",
        "name": "Washing Machine Plug",
        "data": {
            "P2": {"v": 1.5},  # Energy
            "P3": {"v": 1200},  # Power
            "P4": {
                "v": 220.5
            },  # Voltage - this is not a standard sensor subkey for this devtype
        },
    },
    # 4. A lock with a battery sensor
    {
        "agt": "hub1",
        "me": "device4",
        "devtype": "SL_LKS_S",
        "name": "Main Door Lock",
        "data": {"BAT": {"val": 88}},
    },
    # 5. A switch with a battery sensor
    {
        "agt": "hub1",
        "me": "device5",
        "devtype": "SL_SW_IF1",
        "name": "Bedroom Switch",
        "data": {"P4": {"val": 92}},
    },
    # 6. A device to be excluded by 'me'
    {
        "agt": "hub1",
        "me": "excluded_device",
        "devtype": "SL_SC_THL",
        "name": "Excluded Sensor",
        "data": {"T": {"v": 20}},
    },
    # 7. A device to be excluded by 'agt'
    {
        "agt": "excluded_hub",
        "me": "device7",
        "devtype": "SL_SC_THL",
        "name": "Sensor on Excluded Hub",
        "data": {"T": {"v": 21}},
    },
    # 8. An unsupported device type
    {
        "agt": "hub1",
        "me": "device8",
        "devtype": "UNSUPPORTED_TYPE",
        "name": "Unsupported Device",
        "data": {"T": {"v": 22}},
    },
    # 9. SL_NATURE panel (Thermostat type)
    {
        "agt": "hub1",
        "me": "nature1",
        "devtype": "SL_NATURE",
        "name": "Nature Panel Thermo",
        "data": {
            "P4": {"val": 235},  # Current Temperature
            "P5": {"val": 3},  # Mode ID for Thermostat
        },
    },
    # 10. SL_NATURE panel (Non-thermostat type)
    {
        "agt": "hub1",
        "me": "nature2",
        "devtype": "SL_NATURE",
        "name": "Nature Panel Switch",
        "data": {"P5": {"val": 1}},
    },
]

# --- TESTS for async_setup_entry ---


async def test_async_setup_entry_creates_sensors(
    hass: HomeAssistant, mock_lifesmart_client, mock_config_entry
):
    """Test successful creation of sensor entities."""
    hass.data[DOMAIN] = {
        "test_entry_id": {
            "devices": MOCK_DEVICES,
            "client": mock_lifesmart_client,
            "exclude_devices": ["excluded_device"],
            "exclude_hubs": ["excluded_hub"],
        }
    }
    async_add_entities = AsyncMock()

    await async_setup_entry(hass, mock_config_entry, async_add_entities)

    # Expected sensors:
    # device1: 4 sensors (T, H, Z, V)
    # device2: 4 sensors (P1, P2, P3, P4)
    # device3: 2 sensors (P2, P3) -> P4 is not a valid sensor for this type
    # device4: 1 sensor (BAT)
    # device5: 1 sensor (P4)
    # nature1: 1 sensor (P4)
    # Total = 4 + 4 + 2 + 1 + 1 + 1 = 13 sensors
    assert async_add_entities.call_count == 1
    assert len(async_add_entities.call_args[0][0]) == 13


async def test_async_setup_entry_handles_no_devices(
    hass: HomeAssistant, mock_lifesmart_client, mock_config_entry
):
    """Test setup with no devices."""
    hass.data[DOMAIN] = {
        "test_entry_id": {
            "devices": [],
            "client": mock_lifesmart_client,
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
        # Positive cases from each block
        ("SL_CP_DN", "P5", True),
        ("SL_CP_VL", "P6", True),
        ("SL_TR_ACIPM", "P4", True),
        (EV_SENSOR_TYPES[0], "T", True),
        (EV_SENSOR_TYPES[0], "P5", True),
        ("SL_SC_CH", "P1", True),
        ("SL_SC_GAS", "P2", True),
        (LOCK_TYPES[0], "BAT", True),
        ("SL_CT_C", "P8", True),
        (POWER_METER_PLUG_TYPES[0], "P2", True),
        (SMART_PLUG_TYPES[0], "EV", True),
        ("SL_SC_NS", "P1", True),
        ("ELIQ_EM", "EPA", True),
        ("SL_P_A", "T", True),
        ("SL_S_WFS", "V", True),
        (SUPPORTED_SWITCH_TYPES[0], "P4", True),
        ("SL_SC_BB_V2", "P2", True),
        # Negative cases
        (CLIMATE_TYPES[0], "P1", False),
        ("SL_LKS_S", "P1", False),
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
        "devtype",
        "me",
        "name",
        "sub_key",
        "sub_data",
        "expected_name",
        "expected_class",
        "expected_unit",
        "expected_state_class",
        "expected_value",
        "expected_attrs",
    ),
    [
        # Temperature
        (
            "SL_SC_THL",
            "d1",
            "Env Sensor",
            "T",
            {"val": 255},
            "Env Sensor T",
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            SensorStateClass.MEASUREMENT,
            25.5,
            None,
        ),
        # Humidity with 'v' present
        (
            "SL_SC_THL",
            "d1",
            "Env Sensor",
            "H",
            {"v": 65.5, "val": 655},
            "Env Sensor H",
            SensorDeviceClass.HUMIDITY,
            PERCENTAGE,
            SensorStateClass.MEASUREMENT,
            65.5,
            None,
        ),
        # Illuminance
        (
            "SL_SC_THL",
            "d1",
            "Env Sensor",
            "Z",
            {"v": 800},
            "Env Sensor Z",
            SensorDeviceClass.ILLUMINANCE,
            LIGHT_LUX,
            SensorStateClass.MEASUREMENT,
            800,
            None,
        ),
        # Voltage
        (
            "SL_SC_THL",
            "d1",
            "Env Sensor",
            "V",
            {"val": 298},
            "Env Sensor V",
            SensorDeviceClass.VOLTAGE,
            UnitOfElectricPotential.VOLT,
            SensorStateClass.MEASUREMENT,
            298,
            None,
        ),
        # Battery from Lock
        (
            "SL_LKS_S",
            "d2",
            "Door Lock",
            "BAT",
            {"val": 88},
            "Door Lock BAT",
            SensorDeviceClass.BATTERY,
            PERCENTAGE,
            SensorStateClass.MEASUREMENT,
            88,
            None,
        ),
        # Battery from Switch with sub-device name
        (
            "SL_SW_IF2",
            "d3",
            "Kitchen Switch",
            "P4",
            {"val": 95, "name": "Battery"},
            "Kitchen Switch Battery",
            SensorDeviceClass.BATTERY,
            PERCENTAGE,
            SensorStateClass.MEASUREMENT,
            95,
            None,
        ),
        # Energy (Total Increasing)
        (
            "SL_OE_3C",
            "d4",
            "Plug",
            "P2",
            {"v": 10.55},
            "Plug P2",
            SensorDeviceClass.ENERGY,
            UnitOfEnergy.KILO_WATT_HOUR,
            SensorStateClass.TOTAL_INCREASING,
            10.55,
            None,
        ),
        # Power
        (
            SMART_PLUG_TYPES[0],
            "d5",
            "Smart Plug",
            "EP",
            {"v": 1500},
            "Smart Plug EP",
            SensorDeviceClass.POWER,
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            1500,
            None,
        ),
        # Current
        (
            SMART_PLUG_TYPES[0],
            "d5",
            "Smart Plug",
            "EI",
            {"v": 1.2},
            "Smart Plug EI",
            SensorDeviceClass.CURRENT,
            UnitOfElectricCurrent.AMPERE,
            None,
            1.2,
            None,
        ),  # Assuming no state class for Current
        # CO2
        (
            "SL_SC_CA",
            "d6",
            "CO2 Sensor",
            "P3",
            {"val": 950},
            "CO2 Sensor P3",
            SensorDeviceClass.CO2,
            CONCENTRATION_PARTS_PER_MILLION,
            SensorStateClass.MEASUREMENT,
            950,
            {"air_quality": 950},
        ),
        # VOC
        (
            "SL_TR_ACIPM",
            "d7",
            "Air Panel",
            "P4",
            {"val": 15},
            "Air Panel P4",
            SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
            CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
            SensorStateClass.MEASUREMENT,
            1.5,
            None,
        ),
        # Gas
        (
            "SL_SC_CP",
            "d8",
            "Gas Sensor",
            "P1",
            {"val": 10},
            "Gas Sensor P1",
            SensorDeviceClass.GAS,
            CONCENTRATION_PARTS_PER_MILLION,
            None,
            10,
            None,
        ),
        # Sound Pressure
        (
            "SL_SC_NS",
            "d9",
            "Noise Sensor",
            "P1",
            {"val": 65},
            "Noise Sensor P1",
            SensorDeviceClass.SOUND_PRESSURE,
            UnitOfSoundPressure.DECIBEL,
            SensorStateClass.MEASUREMENT,
            65,
            None,
        ),
        # Default/None case
        (
            "SL_SC_G",
            "d10",
            "Door Sensor",
            "G",
            {"val": 1},
            "Door Sensor G",
            None,
            None,
            None,
            1,
            None,
        ),
    ],
)
def test_lifesmart_sensor_properties(
    hass: HomeAssistant,
    mock_lifesmart_client,
    mock_config_entry,
    devtype,
    me,
    name,
    sub_key,
    sub_data,
    expected_name,
    expected_class,
    expected_unit,
    expected_state_class,
    expected_value,
    expected_attrs,
):
    """Test all derived properties of the LifeSmartSensor entity."""
    raw_device = {
        "agt": "hub1",
        "me": me,
        "devtype": devtype,
        "name": name,
        "data": {sub_key: sub_data},
    }

    # LifeSmartDevice is a simple dataclass, can be instantiated directly
    from custom_components.lifesmart import LifeSmartDevice

    ha_device = LifeSmartDevice(raw_device, mock_lifesmart_client)

    sensor = LifeSmartSensor(
        device=ha_device,
        raw_device=raw_device,
        sub_device_key=sub_key,
        sub_device_data=sub_data,
        client=mock_lifesmart_client,
        entry_id=mock_config_entry.entry_id,
    )
    sensor.hass = hass

    assert sensor.name == expected_name
    assert sensor.device_class == expected_class
    assert sensor.native_unit_of_measurement == expected_unit
    assert sensor.state_class == expected_state_class
    assert sensor.native_value == expected_value
    assert sensor.extra_state_attributes == expected_attrs
    assert sensor.unique_id == f"{devtype}-hub1-{me}-{sub_key}"
    assert sensor.device_info["identifiers"] == {(DOMAIN, "hub1", me)}
    assert sensor.device_info["name"] == name
    assert sensor.device_info["model"] == devtype
    assert sensor.device_info["manufacturer"] == "LifeSmart"


async def test_lifesmart_sensor_updates(
    hass: HomeAssistant, mock_lifesmart_client, mock_config_entry
):
    """Test real-time and global refresh updates."""
    # Setup initial device and sensor
    raw_device = {
        "agt": "hub1",
        "me": "device1",
        "devtype": "SL_SC_THL",
        "name": "Living Room Env",
        "data": {"T": {"v": 25.5}},
    }
    from custom_components.lifesmart import LifeSmartDevice

    ha_device = LifeSmartDevice(raw_device, mock_lifesmart_client)
    sensor = LifeSmartSensor(
        device=ha_device,
        raw_device=raw_device,
        sub_device_key="T",
        sub_device_data=raw_device["data"]["T"],
        client=mock_lifesmart_client,
        entry_id=mock_config_entry.entry_id,
    )
    sensor.hass = hass
    sensor.async_write_ha_state = MagicMock()

    # 1. Test real-time update (WebSocket push with 'msg' wrapper)
    update_data_ws = {"msg": {"T": {"v": 26.0}}}
    await sensor._handle_update(update_data_ws)
    assert sensor.native_value == 26.0
    sensor.async_write_ha_state.assert_called_once()

    # 2. Test real-time update (raw value, requires conversion)
    sensor.async_write_ha_state.reset_mock()
    update_data_raw = {"T": {"val": 265}}
    await sensor._handle_update(update_data_raw)
    assert sensor.native_value == 26.5
    sensor.async_write_ha_state.assert_called_once()

    # 3. Test global refresh
    sensor.async_write_ha_state.reset_mock()
    updated_device_list = [
        {
            "agt": "hub1",
            "me": "device1",
            "devtype": "SL_SC_THL",
            "name": "Living Room Env",
            "data": {"T": {"val": 270}},  # New value for global refresh
        }
    ]
    hass.data[DOMAIN] = {"test_entry_id": {"devices": updated_device_list}}
    await sensor._handle_global_refresh()
    assert sensor.native_value == 27.0
    sensor.async_write_ha_state.assert_called_once()

    # 4. Test global refresh when device is missing
    sensor.async_write_ha_state.reset_mock()
    hass.data[DOMAIN]["test_entry_id"]["devices"] = []  # Device removed
    with patch("custom_components.lifesmart.sensor._LOGGER.warning") as mock_log:
        await sensor._handle_global_refresh()
        mock_log.assert_called_once()
        # Value should not change, and it should not crash
        assert sensor.native_value == 27.0
        sensor.async_write_ha_state.assert_not_called()
