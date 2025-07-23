"""
Unit tests for the LifeSmart binary sensor platform.
This version uses shared fixtures from conftest.py and correct mocking strategies.
"""

import datetime
from datetime import timezone
from unittest.mock import patch, AsyncMock

import pytest
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

pytestmark = pytest.mark.asyncio


async def setup_platform(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    mock_client: AsyncMock,
    devices: list,
) -> None:
    """
    Helper to set up the binary sensor platform.
    This is now a standard setup helper that uses fixtures correctly.
    """
    hass.data[DOMAIN] = {
        config_entry.entry_id: {
            "client": mock_client,
            "devices": devices,
            "exclude_devices": [],
            "exclude_hubs": [],
        }
    }
    # We no longer patch LifeSmartDevice. We let the platform setup run as intended.
    await hass.config_entries.async_forward_entry_setup(
        config_entry, BINARY_SENSOR_DOMAIN
    )
    await hass.async_block_till_done()


def find_device(devices: list, me: str):
    """Helper to find a specific device from the mock list by its 'me' id."""
    return next((d for d in devices if d.get(DEVICE_ID_KEY) == me), None)


async def test_async_setup_entry(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_lifesmart_devices: list,
):
    """Test platform setup creates the correct number of entities from a single device."""
    # Find the specific lock device from the shared fixture
    lock_device = find_device(mock_lifesmart_devices, "bs_lock")
    assert lock_device, "Lock device 'bs_lock' not found in mock_lifesmart_devices"

    await setup_platform(hass, mock_config_entry, mock_client, [lock_device])

    entity_registry = er.async_get(hass)
    # A lock device should create 2 binary sensors (ALM for alarm and EVTLO for unlock events)
    assert (
        len(entity_registry.entities) == 2
    ), "A lock should create 2 binary sensors (ALM and EVTLO)"


@pytest.mark.parametrize(
    "device_me, entity_id_suffix, expected_name, expected_class, expected_state",
    [
        # The device_me corresponds to the 'me' key in the mock_lifesmart_devices fixture
        (
            "bs_door",
            "bs_door_g",
            "Front Door G",
            BinarySensorDeviceClass.DOOR,
            STATE_ON,  # val is 0, which means open/on for door sensors
        ),
        (
            "bs_motion",
            "bs_motion_m",
            "Living Motion M",
            BinarySensorDeviceClass.MOTION,
            STATE_ON,
        ),
        (
            "bs_water",
            "bs_water_wa",
            "Kitchen Water WA",
            BinarySensorDeviceClass.MOISTURE,
            STATE_ON,
        ),
        (
            "bs_defed",
            "bs_defed_m",
            "Garage DEFED M",
            BinarySensorDeviceClass.MOTION,
            STATE_ON,
        ),
        (
            "bs_smoke",
            "bs_smoke_p1",
            "Hallway Smoke P1",
            BinarySensorDeviceClass.SMOKE,
            STATE_ON,
        ),
        (
            "bs_radar",
            "bs_radar_p1",
            "Study Occupancy P1",
            BinarySensorDeviceClass.OCCUPANCY,
            STATE_ON,
        ),
        ("bs_button", "bs_button_p1", "Panic Button P1", None, STATE_OFF),
    ],
)
async def test_entity_initialization(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
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

    await setup_platform(hass, mock_config_entry, mock_client, [device])

    entity_id = f"binary_sensor.{expected_name.lower().replace(' ', '_')}"
    state = hass.states.get(entity_id)
    assert state is not None, f"Entity {entity_id} not found"

    assert state.name == expected_name
    assert state.attributes.get("device_class") == expected_class
    assert state.state == expected_state

    entity_registry = er.async_get(hass)
    # Construct unique_id based on the device data from the fixture
    unique_id = f"lifesmart_{device[HUB_ID_KEY]}_{entity_id_suffix}"
    entry = entity_registry.async_get(entity_id)
    assert entry and entry.unique_id.endswith(unique_id)


async def test_special_attributes_initialization(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_lifesmart_devices: list,
):
    """Test extra state attributes for specialized binary sensors like locks."""
    lock_device = find_device(mock_lifesmart_devices, "bs_lock")
    assert lock_device, "Lock device 'bs_lock' not found in mock_lifesmart_devices"

    await setup_platform(hass, mock_config_entry, mock_client, [lock_device])

    lock_evt_state = hass.states.get("binary_sensor.main_lock_evtlo")
    assert lock_evt_state is not None
    # Based on EVT_MAP in const.py, val 4121 -> "Password", user 25
    assert lock_evt_state.attributes.get("unlocking_method") == "Password"
    assert lock_evt_state.attributes.get("unlocking_user") == 25


async def test_momentary_button_update(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_lifesmart_devices: list,
    freezer,
):
    """Test the transient state change of a momentary button."""
    button_device = find_device(mock_lifesmart_devices, "bs_button")
    assert (
        button_device
    ), "Button device 'bs_button' not found in mock_lifesmart_devices"

    await setup_platform(hass, mock_config_entry, mock_client, [button_device])
    entity_id = "binary_sensor.panic_button_p1"
    unique_id = (
        f"lifesmart_{button_device[HUB_ID_KEY]}_{button_device[DEVICE_ID_KEY]}_p1"
    )

    freezer.move_to("2023-01-01T12:00:00Z")
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        # Simulate a WebSocket push for this entity
        async_dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}",
            {"val": 1, "type": 129},
        )
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        assert state.state == STATE_ON
        assert state.attributes.get("last_event") == "single_click"
        # 3. 使用标准库获取被冻结的时间
        assert (
            state.attributes.get("last_event_time")
            == datetime.datetime.now(timezone.utc).isoformat()
        )

        # The momentary button is designed to turn off after a short delay
        mock_sleep.assert_awaited_once_with(0.5)


async def test_global_refresh_update(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_lifesmart_devices: list,
):
    """Test entity state update via a global data refresh."""
    door_device = find_device(mock_lifesmart_devices, "bs_door")
    assert door_device, "Door sensor 'bs_door' not found in mock_lifesmart_devices"

    # Initial state is open (val: 0 -> ON)
    await setup_platform(hass, mock_config_entry, mock_client, [door_device])
    entity_id = "binary_sensor.front_door_g"
    assert hass.states.get(entity_id).state == STATE_ON

    # Create an updated version of the device where the door is closed
    updated_device = door_device.copy()
    updated_device[DEVICE_DATA_KEY] = {"G": {"val": 1, "type": 0}}  # val: 1 -> OFF
    hass.data[DOMAIN][mock_config_entry.entry_id]["devices"] = [updated_device]

    # Simulate a global refresh signal
    async_dispatcher_send(hass, LIFESMART_SIGNAL_UPDATE_ENTITY)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_OFF
