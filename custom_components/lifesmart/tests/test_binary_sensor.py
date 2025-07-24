"""
Unit tests for the LifeSmart binary sensor platform.
"""

from datetime import datetime, timezone
from unittest.mock import patch, AsyncMock

import pytest
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.lifesmart import generate_unique_id
from custom_components.lifesmart.const import *

pytestmark = pytest.mark.asyncio


def find_device(devices: list, me: str):
    """Helper to find a specific device from the mock list by its 'me' id."""
    return next((d for d in devices if d.get(DEVICE_ID_KEY) == me), None)


async def test_lock_creates_multiple_sensors(
    hass: HomeAssistant,
    setup_integration: ConfigEntry,
):
    """Test that a lock device creates the correct number of binary sensors."""
    assert hass.states.get("binary_sensor.main_lock_alm") is not None
    assert hass.states.get("binary_sensor.main_lock_evtlo") is not None


@pytest.mark.parametrize(
    "device_me, entity_id_suffix, expected_name, expected_class, expected_state",
    [
        ("bs_door", "g", "Front Door G", BinarySensorDeviceClass.DOOR, STATE_ON),
        ("bs_motion", "m", "Living Motion M", BinarySensorDeviceClass.MOTION, STATE_ON),
        (
            "bs_water",
            "wa",
            "Kitchen Water WA",
            BinarySensorDeviceClass.MOISTURE,
            STATE_ON,
        ),
        ("bs_defed", "m", "Garage DEFED M", BinarySensorDeviceClass.MOTION, STATE_ON),
        ("bs_smoke", "p1", "Hallway Smoke P1", BinarySensorDeviceClass.SMOKE, STATE_ON),
        (
            "bs_radar",
            "p1",
            "Study Occupancy P1",
            BinarySensorDeviceClass.OCCUPANCY,
            STATE_ON,
        ),
        ("bs_button", "p1", "Panic Button P1", None, STATE_OFF),
    ],
)
async def test_entity_initialization(
    hass: HomeAssistant,
    setup_integration: ConfigEntry,
    mock_lifesmart_devices: list,
    device_me: str,
    entity_id_suffix: str,
    expected_name: str,
    expected_class: BinarySensorDeviceClass,
    expected_state: str,
):
    """Test the initialization of various binary sensor entities."""
    device = find_device(mock_lifesmart_devices, device_me)
    assert device, f"Device '{device_me}' not found in mock_lifesmart_devices"

    entity_id = f"binary_sensor.{expected_name.lower().replace(' ', '_')}"
    state = hass.states.get(entity_id)
    assert state is not None, f"Entity {entity_id} not found"

    assert state.name == expected_name
    assert state.attributes.get("device_class") == (
        expected_class.value if expected_class else None
    )
    assert state.state == expected_state

    entity_registry = er.async_get(hass)
    unique_id = generate_unique_id(
        device[DEVICE_TYPE_KEY],
        device[HUB_ID_KEY],
        device[DEVICE_ID_KEY],
        entity_id_suffix,
    )
    entry = entity_registry.async_get(entity_id)
    assert entry and entry.unique_id == unique_id


async def test_special_attributes_initialization(
    hass: HomeAssistant,
    setup_integration: ConfigEntry,
):
    """Test extra state attributes for specialized binary sensors like locks."""
    lock_evt_state = hass.states.get("binary_sensor.main_lock_evtlo")
    assert lock_evt_state is not None
    assert lock_evt_state.attributes.get("unlocking_method") == "Password"
    assert lock_evt_state.attributes.get("unlocking_user") == 25


async def test_momentary_button_update(
    hass: HomeAssistant,
    setup_integration: ConfigEntry,
    mock_lifesmart_devices: list,
    freezer,
):
    """Test the transient state change of a momentary button."""
    button_device = find_device(mock_lifesmart_devices, "bs_button")
    entity_id = "binary_sensor.panic_button_p1"
    unique_id = (
        f"lifesmart_{button_device[HUB_ID_KEY]}_{button_device[DEVICE_ID_KEY]}_p1"
    )

    freezer.move_to("2023-01-01T12:00:00+00:00")

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        async_dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}",
            {"val": 1, "type": 129},
        )
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        assert state.state == STATE_ON
        assert state.attributes.get("last_event") == "single_click"

        # Get the frozen time in the correct format for comparison
        expected_time = datetime.now(timezone.utc).isoformat()
        assert state.attributes.get("last_event_time") == expected_time

        mock_sleep.assert_awaited_once_with(0.5)


async def test_global_refresh_update(
    hass: HomeAssistant,
    setup_integration: ConfigEntry,
):
    """Test entity state update via a global data refresh."""
    entity_id = "binary_sensor.front_door_g"
    assert hass.states.get(entity_id).state == STATE_ON

    # Find the door device in the live hass data and update it
    door_device = find_device(
        hass.data[DOMAIN][setup_integration.entry_id]["devices"], "bs_door"
    )
    door_device[DEVICE_DATA_KEY] = {"G": {"val": 1, "type": 0}}

    async_dispatcher_send(hass, LIFESMART_SIGNAL_UPDATE_ENTITY)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_OFF
