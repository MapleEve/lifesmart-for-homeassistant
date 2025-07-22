"""
Unit tests for the LifeSmart binary sensor platform.
This version strictly adheres to using constants defined in const.py
for all mock device creation, ensuring full alignment with the component's code.
"""

from unittest.mock import patch, AsyncMock

import pytest
from freezegun import freeze_time
from homeassistant.components.binary_sensor import (
    DOMAIN as BINARY_SENSOR_DOMAIN,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send

# --- Strictly import constants from the component's code ---
from custom_components.lifesmart.const import *


# --- Helper to safely access devtypes from constant lists ---
def get_first_devtype(const_list, fallback="FALLBACK_TYPE"):
    """Safely get the first device type from a constant tuple/list."""
    return const_list[0] if const_list else fallback


# --- MOCK DEVICE DATA: STRICTLY USING CONSTANTS ---
# Each mock device now programmatically uses the first element from the
# corresponding constant list imported from const.py.
MOCK_DEVICES = {
    # GUARD_SENSOR_TYPES -> Using GUARD_SENSOR_TYPES[0]
    "door_sensor_open": {
        "agt": "hub1",
        "me": "d1",
        "devtype": get_first_devtype(GUARD_SENSOR_TYPES),
        "name": "Front Door",
        "data": {"G": {"val": 0, "type": 0}},
    },
    # MOTION_SENSOR_TYPES -> Using MOTION_SENSOR_TYPES[0]
    "motion_sensor_detected": {
        "agt": "hub1",
        "me": "d2",
        "devtype": get_first_devtype(MOTION_SENSOR_TYPES),
        "name": "Living Room Motion",
        "data": {"M": {"val": 1, "type": 0}},
    },
    # WATER_SENSOR_TYPES -> Using WATER_SENSOR_TYPES[0]
    "water_sensor_wet": {
        "agt": "hub1",
        "me": "d3",
        "devtype": get_first_devtype(WATER_SENSOR_TYPES),
        "name": "Kitchen Sink",
        "data": {"WA": {"val": 50, "type": 0}},
    },
    # DEFED_SENSOR_TYPES -> Using DEFED_SENSOR_TYPES[1] for motion
    "defed_sensor_triggered": {
        "agt": "hub1",
        "me": "d4",
        "devtype": "SL_DF_MM",  # Example from list
        "name": "Garage DEFED",
        "data": {"M": {"val": 1, "type": 129}},
    },
    # LOCK_TYPES -> Using LOCK_TYPES[0]
    "lock_device": {
        "agt": "hub1",
        "me": "d5",
        "devtype": get_first_devtype(LOCK_TYPES),
        "name": "Main Lock",
        "data": {
            "EVTLO": {"val": 4121, "type": 1, "valts": 1672531200000},
            "ALM": {"val": 2, "type": 0},
        },
    },
    # SMOKE_SENSOR_TYPES -> Using SMOKE_SENSOR_TYPES[0]
    "smoke_sensor_triggered": {
        "agt": "hub1",
        "me": "d6",
        "devtype": get_first_devtype(SMOKE_SENSOR_TYPES),
        "name": "Hallway Smoke",
        "data": {"P1": {"val": 1, "type": 0}},
    },
    # RADAR_SENSOR_TYPES -> Using RADAR_SENSOR_TYPES[0]
    "radar_sensor_occupied": {
        "agt": "hub1",
        "me": "d7",
        "devtype": get_first_devtype(RADAR_SENSOR_TYPES),
        "name": "Study Occupancy",
        "data": {"P1": {"val": 1, "type": 0}},
    },
    # Momentary Button -> Hardcoded 'SL_SC_BB_V2' as it's a specific handled case
    "button_v2": {
        "agt": "hub1",
        "me": "d8",
        "devtype": "SL_SC_BB_V2",
        "name": "Panic Button",
        "data": {"P1": {"val": 0, "type": 0}},
    },
    # CLIMATE_TYPES -> Using a type from the list
    "climate_valve_alarm": {
        "agt": "hub1",
        "me": "d9",
        "devtype": "SL_CP_VL",  # Example from list
        "name": "Valve Controller",
        "data": {"P5": {"val": 5, "type": 0}},
    },
    # GENERIC_CONTROLLER_TYPES -> Using GENERIC_CONTROLLER_TYPES[0]
    "generic_controller_on": {
        "agt": "hub1",
        "me": "d10",
        "devtype": get_first_devtype(GENERIC_CONTROLLER_TYPES),
        "name": "Generic Relay",
        "data": {"P2": {"val": 0, "type": 0}},
    },
}

pytestmark = pytest.mark.asyncio


async def setup_platform(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    devices: list,
    exclude_devices: list | None = None,
    exclude_hubs: list | None = None,
) -> None:
    """Helper to set up the binary sensor platform."""
    hass.data[DOMAIN] = {
        config_entry.entry_id: {
            "client": AsyncMock(),
            "devices": devices,
            "exclude_devices": exclude_devices or [],
            "exclude_hubs": exclude_hubs or [],
        }
    }
    with patch("custom_components.lifesmart.LifeSmartDevice"):
        await hass.config_entries.async_forward_entry_setup(
            config_entry, BINARY_SENSOR_DOMAIN
        )
    await hass.async_block_till_done()


async def test_async_setup_entry(hass: HomeAssistant, mock_config_entry: ConfigEntry):
    """Test platform setup creates the correct number of entities."""
    # This test ensures that setup logic correctly handles multiple sub-entities from a single device
    await setup_platform(hass, mock_config_entry, [MOCK_DEVICES["lock_device"]])
    entity_registry = er.async_get(hass)
    assert (
        len(entity_registry.entities) == 2
    ), "A lock should create 2 binary sensors (ALM and EVTLO)"


@pytest.mark.parametrize(
    "device_fixture, entity_id_suffix, expected_name, expected_class, expected_state",
    [
        (
            "door_sensor_open",
            "d1_g",
            "Front Door G",
            BinarySensorDeviceClass.DOOR,
            STATE_ON,
        ),
        (
            "motion_sensor_detected",
            "d2_m",
            "Living Room Motion M",
            BinarySensorDeviceClass.MOTION,
            STATE_ON,
        ),
        (
            "water_sensor_wet",
            "d3_wa",
            "Kitchen Sink WA",
            BinarySensorDeviceClass.MOISTURE,
            STATE_ON,
        ),
        (
            "defed_sensor_triggered",
            "d4_m",
            "Garage DEFED M",
            BinarySensorDeviceClass.MOTION,
            STATE_ON,
        ),
        (
            "smoke_sensor_triggered",
            "d6_p1",
            "Hallway Smoke P1",
            BinarySensorDeviceClass.SMOKE,
            STATE_ON,
        ),
        (
            "radar_sensor_occupied",
            "d7_p1",
            "Study Occupancy P1",
            BinarySensorDeviceClass.OCCUPANCY,
            STATE_ON,
        ),
        ("button_v2", "d8_p1", "Panic Button P1", None, STATE_OFF),
        (
            "climate_valve_alarm",
            "d9_p5",
            "Valve Controller P5",
            BinarySensorDeviceClass.PROBLEM,
            STATE_ON,
        ),
        (
            "generic_controller_on",
            "d10_p2",
            "Generic Relay P2",
            BinarySensorDeviceClass.OPENING,
            STATE_ON,
        ),
    ],
)
async def test_entity_initialization(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    device_fixture: str,
    entity_id_suffix: str,
    expected_name: str,
    expected_class: BinarySensorDeviceClass,
    expected_state: str,
):
    """Test the initialization of various binary sensor entities."""
    device = MOCK_DEVICES[device_fixture]
    await setup_platform(hass, mock_config_entry, [device])

    entity_id = f"binary_sensor.{expected_name.lower().replace(' ', '_')}"
    state = hass.states.get(entity_id)
    assert state is not None, f"Entity {entity_id} not found"

    assert state.name == expected_name
    assert state.attributes.get("device_class") == expected_class
    assert state.state == expected_state

    entity_registry = er.async_get(hass)
    unique_id = f"lifesmart_hub1_{entity_id_suffix}"
    entry = entity_registry.async_get(entity_id)
    assert entry and entry.unique_id.endswith(unique_id)


async def test_special_attributes_initialization(
    hass: HomeAssistant, mock_config_entry: ConfigEntry
):
    """Test extra state attributes for specialized binary sensors."""
    await setup_platform(hass, mock_config_entry, [MOCK_DEVICES["lock_device"]])

    lock_evt_state = hass.states.get("binary_sensor.main_lock_evtlo")
    assert lock_evt_state is not None
    assert lock_evt_state.attributes.get("unlocking_method") == "Password"
    assert lock_evt_state.attributes.get("unlocking_user") == 25


async def test_momentary_button_update(
    hass: HomeAssistant, mock_config_entry: ConfigEntry
):
    """Test the transient state change of a momentary button."""
    await setup_platform(hass, mock_config_entry, [MOCK_DEVICES["button_v2"]])
    entity_id = "binary_sensor.panic_button_p1"
    unique_id = f"lifesmart_hub1_{MOCK_DEVICES['button_v2']['me']}_{'p1'}"

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep, freeze_time(
        "2023-01-01T12:00:00Z"
    ) as frozen_time:

        async_dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}",
            {"val": 1, "type": 129},
        )
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        assert state.state == STATE_ON
        assert state.attributes.get("last_event") == "single_click"
        assert state.attributes.get("last_event_time") == frozen_time().isoformat()

        mock_sleep.assert_awaited_once_with(0.5)


async def test_global_refresh_update(
    hass: HomeAssistant, mock_config_entry: ConfigEntry
):
    """Test entity state update via a global data refresh."""
    await setup_platform(hass, mock_config_entry, [MOCK_DEVICES["door_sensor_open"]])
    entity_id = "binary_sensor.front_door_g"
    assert hass.states.get(entity_id).state == STATE_ON

    updated_device = MOCK_DEVICES["door_sensor_closed"].copy()
    hass.data[DOMAIN][mock_config_entry.entry_id]["devices"] = [updated_device]

    async_dispatcher_send(hass, LIFESMART_SIGNAL_UPDATE_ENTITY)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_OFF
