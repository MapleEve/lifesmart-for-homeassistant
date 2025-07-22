"""Unit tests for the LifeSmart switch platform."""

import logging
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.lifesmart.const import (
    DEVICE_DATA_KEY,
    DEVICE_ID_KEY,
    DEVICE_NAME_KEY,
    DEVICE_TYPE_KEY,
    DOMAIN,
    HUB_ID_KEY,
    POWER_METER_PLUG_TYPES,
    SMART_PLUG_TYPES,
)
from custom_components.lifesmart.switch import (
    LifeSmartSwitch,
    _is_switch_subdevice,
    async_setup_entry,
)


# --- Test `_is_switch_subdevice` Helper Function ---


@pytest.mark.parametrize(
    ("device_type", "sub_key", "expected"),
    [
        # SL_P_SW (九路开关控制器)
        ("SL_P_SW", "P1", True),
        ("SL_P_SW", "p5", True),
        ("SL_P_SW", "P9", True),
        ("SL_P_SW", "P10", False),
        ("SL_P_SW", "L1", False),
        # SUPPORTED_SWITCH_TYPES (e.g., SL_SW_IF3) - P4 is excluded
        ("SL_SW_IF3", "P4", False),
        ("SL_SW_IF3", "P1", True),
        ("SL_SW_IF3", "L1", True),
        # SL_SC_BB_V2 (随心按键) - P1 is excluded
        ("SL_SC_BB_V2", "P1", False),
        # SL_OL* (智慧插座)
        ("SL_OL", "O", True),
        ("SL_OL_3C", "o", True),
        ("SL_OL", "P1", False),
        # POWER_METER_PLUG_TYPES (e.g., SL_OE_3C)
        ("SL_OE_3C", "P1", True),
        ("SL_OE_3C", "P4", True),
        ("SL_OE_3C", "p2", False),
        # GARAGE_DOOR_TYPES
        ("SL_ETDOOR", "P1", False),
        # General fallbacks
        ("UNKNOWN_TYPE", "L1", True),
        ("UNKNOWN_TYPE", "l2", True),
        ("UNKNOWN_TYPE", "P1", True),
        ("UNKNOWN_TYPE", "p3", True),
        # General invalid keys
        ("ANY_TYPE", "L4", False),
        ("ANY_TYPE", "P5", False),
        ("ANY_TYPE", "INVALID", False),
    ],
)
def test_is_switch_subdevice(device_type: str, sub_key: str, expected: bool) -> None:
    """Test the _is_switch_subdevice helper function with various device types and keys."""
    assert _is_switch_subdevice(device_type, sub_key) == expected


# --- Test `async_setup_entry` ---


async def test_async_setup_entry_success(
    hass: HomeAssistant,
    lifesmart_client: AsyncMock,
    config_entry: ConfigEntry,
    mock_lifesmart_devices: list[dict[str, Any]],
) -> None:
    """Test successful setup of switch entities."""
    # Arrange
    hass.data[DOMAIN][config_entry.entry_id] = {
        "client": lifesmart_client,
        "devices": mock_lifesmart_devices,
        "exclude_devices": [],
        "exclude_hubs": [],
    }
    async_add_entities = AsyncMock()

    # Act
    await async_setup_entry(hass, config_entry, async_add_entities)

    # Assert
    # Total switch sub-devices in mock_lifesmart_devices:
    # 3 (from SL_SW_IF3) + 1 (from SL_OL) + 2 (from SL_OE_3C) + 3 (from SL_NATURE)
    assert async_add_entities.call_count == 1
    assert len(async_add_entities.call_args[0][0]) == 9


async def test_async_setup_entry_with_exclusions(
    hass: HomeAssistant,
    lifesmart_client: AsyncMock,
    config_entry: ConfigEntry,
    mock_lifesmart_devices: list[dict[str, Any]],
) -> None:
    """Test that devices and hubs can be excluded from setup."""
    # Arrange
    hass.data[DOMAIN][config_entry.entry_id] = {
        "client": lifesmart_client,
        "devices": mock_lifesmart_devices,
        # Exclude the SL_OL device (me: "mexp01")
        "exclude_devices": ["mexp01"],
        # Exclude all devices from the second hub (agt: "agtexhub2")
        "exclude_hubs": ["agtexhub2"],
    }
    # Expected devices after exclusion: 3 from SL_SW_IF3, 3 from SL_NATURE
    async_add_entities = AsyncMock()

    # Act
    await async_setup_entry(hass, config_entry, async_add_entities)

    # Assert
    assert async_add_entities.call_count == 1
    assert len(async_add_entities.call_args[0][0]) == 6


async def test_async_setup_entry_no_switches(
    hass: HomeAssistant,
    lifesmart_client: AsyncMock,
    config_entry: ConfigEntry,
) -> None:
    """Test setup with no switch devices."""
    # Arrange
    hass.data[DOMAIN][config_entry.entry_id] = {
        "client": lifesmart_client,
        "devices": [
            {
                HUB_ID_KEY: "agt1",
                DEVICE_ID_KEY: "me1",
                DEVICE_TYPE_KEY: "SL_SC_THL",  # A sensor, not a switch
                DEVICE_DATA_KEY: {},
            }
        ],
        "exclude_devices": [],
        "exclude_hubs": [],
    }
    async_add_entities = AsyncMock()

    # Act
    await async_setup_entry(hass, config_entry, async_add_entities)

    # Assert
    async_add_entities.assert_called_once_with([])


async def test_async_setup_entry_nature_special_handling(
    hass: HomeAssistant,
    lifesmart_client: AsyncMock,
    config_entry: ConfigEntry,
    mock_lifesmart_devices: list[dict[str, Any]],
) -> None:
    """Test the special handling for SL_NATURE device type."""
    # Add a non-switch version of SL_NATURE to the device list
    non_switch_nature = {
        HUB_ID_KEY: "agt1",
        DEVICE_ID_KEY: "meslnature_noswitch",
        DEVICE_TYPE_KEY: "SL_NATURE",
        DEVICE_DATA_KEY: {"P1": {}, "P2": {}, "P5": {"val": 2}},  # Not a switch panel
    }
    devices = mock_lifesmart_devices + [non_switch_nature]

    hass.data[DOMAIN][config_entry.entry_id] = {
        "client": lifesmart_client,
        "devices": devices,
        "exclude_devices": [],
        "exclude_hubs": [],
    }
    async_add_entities = AsyncMock()

    await async_setup_entry(hass, config_entry, async_add_entities)

    # Assert that the non-switch SL_NATURE was skipped
    assert len(async_add_entities.call_args[0][0]) == 9


# --- Test `LifeSmartSwitch` Entity Class ---


@pytest.fixture
def switch_entity(
    hass: HomeAssistant,
    lifesmart_client: AsyncMock,
    config_entry: ConfigEntry,
    mock_lifesmart_devices: list[dict[str, Any]],
) -> LifeSmartSwitch:
    """Provides a standard LifeSmartSwitch entity for testing."""
    device_data = mock_lifesmart_devices[0]  # The SL_SW_IF3
    ha_device = LifeSmartSwitch(
        device=AsyncMock(),
        raw_device=device_data,
        sub_device_key="L1",
        sub_device_data=device_data[DEVICE_DATA_KEY]["L1"],
        client=lifesmart_client,
        entry_id=config_entry.entry_id,
    )
    ha_device.hass = hass
    # Manually set hass.data for the global refresh handler test
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
        "devices": mock_lifesmart_devices
    }
    return ha_device


def test_switch_init_and_properties(switch_entity: LifeSmartSwitch) -> None:
    """Test the initialization and basic properties of the switch entity."""
    assert switch_entity.unique_id == "SL_SW_IF3_agt1_me1_L1"
    assert switch_entity.name == "Switch3 L1"
    assert switch_entity.device_class == SwitchDeviceClass.SWITCH
    assert switch_entity.is_on is True  # Initial state from L1 is 'on'
    assert switch_entity.extra_state_attributes == {
        "hub_id": "agt1",
        "device_id": "me1",
        "subdevice_index": "L1",
    }


def test_switch_name_generation(
    lifesmart_client: AsyncMock, config_entry: ConfigEntry
) -> None:
    """Test various scenarios for switch name generation."""
    base_device = {
        HUB_ID_KEY: "a",
        DEVICE_ID_KEY: "b",
        DEVICE_TYPE_KEY: "SL_SW_IF1",
        DEVICE_NAME_KEY: "Device Base Name",
        DEVICE_DATA_KEY: {
            "P1": {DEVICE_NAME_KEY: "Button Name"},
            "P2": {},
        },
    }
    # With sub-name
    entity_with_subname = LifeSmartSwitch(
        AsyncMock(),
        base_device,
        "P1",
        base_device[DEVICE_DATA_KEY]["P1"],
        lifesmart_client,
        config_entry.entry_id,
    )
    assert entity_with_subname.name == "Device Base Name Button Name"

    # Without sub-name
    entity_without_subname = LifeSmartSwitch(
        AsyncMock(),
        base_device,
        "P2",
        base_device[DEVICE_DATA_KEY]["P2"],
        lifesmart_client,
        config_entry.entry_id,
    )
    assert entity_without_subname.name == "Device Base Name P2"

    # Without base name
    base_device_no_name = base_device.copy()
    del base_device_no_name[DEVICE_NAME_KEY]
    entity_without_base = LifeSmartSwitch(
        AsyncMock(),
        base_device_no_name,
        "P2",
        base_device_no_name[DEVICE_DATA_KEY]["P2"],
        lifesmart_client,
        config_entry.entry_id,
    )
    assert entity_without_base.name == "Unknown Switch P2"


def test_determine_device_class(
    lifesmart_client: AsyncMock, config_entry: ConfigEntry
) -> None:
    """Test device class determination for outlets and switches."""
    # Test for OUTLET
    for dev_type in SMART_PLUG_TYPES | POWER_METER_PLUG_TYPES:
        device_data = {DEVICE_TYPE_KEY: dev_type, DEVICE_DATA_KEY: {}}
        entity = LifeSmartSwitch(
            AsyncMock(), device_data, "P1", {}, lifesmart_client, config_entry.entry_id
        )
        assert entity.device_class == SwitchDeviceClass.OUTLET

    # Test for SWITCH
    device_data = {DEVICE_TYPE_KEY: "SL_SW_IF3", DEVICE_DATA_KEY: {}}
    entity = LifeSmartSwitch(
        AsyncMock(), device_data, "P1", {}, lifesmart_client, config_entry.entry_id
    )
    assert entity.device_class == SwitchDeviceClass.SWITCH


def test_parse_state() -> None:
    """Test the _parse_state method."""
    entity_class = LifeSmartSwitch
    assert entity_class._parse_state(None, {"type": 129}) is True
    assert entity_class._parse_state(None, {"type": 1}) is True
    assert entity_class._parse_state(None, {"type": 128}) is False
    assert entity_class._parse_state(None, {"type": 0}) is False
    assert entity_class._parse_state(None, {}) is False


async def test_turn_on_off(
    switch_entity: LifeSmartSwitch, caplog: pytest.LogCaptureFixture
) -> None:
    """Test turning the switch on and off."""
    client = switch_entity._client
    client.turn_on_light_switch_async.return_value = 0
    client.turn_off_light_switch_async.return_value = 0

    switch_entity.async_write_ha_state = AsyncMock()

    # Turn on
    await switch_entity.async_turn_on()
    client.turn_on_light_switch_async.assert_awaited_once_with("L1", "agt1", "me1")
    assert switch_entity.is_on is True
    assert switch_entity.async_write_ha_state.call_count == 1

    # Turn off
    await switch_entity.async_turn_off()
    client.turn_off_light_switch_async.assert_awaited_once_with("L1", "agt1", "me1")
    assert switch_entity.is_on is False
    assert switch_entity.async_write_ha_state.call_count == 2

    # Test failure case
    client.turn_on_light_switch_async.return_value = -1
    with caplog.at_level(logging.WARNING):
        await switch_entity.async_turn_on()
        assert "Failed to turn on switch" in caplog.text
    assert switch_entity.is_on is False  # State should not change on failure


async def test_data_update_handlers(
    hass: HomeAssistant, switch_entity: LifeSmartSwitch
) -> None:
    """Test that the switch state updates via dispatcher signals."""
    switch_entity.async_write_ha_state = AsyncMock()

    # 1. Test `_handle_update` (specific entity update)
    # Simulate a dispatcher signal for this specific entity
    update_callback = switch_entity._handle_update
    update_callback({"type": 128})  # Turn off

    assert switch_entity.is_on is False
    assert switch_entity.async_write_ha_state.call_count == 1

    # 2. Test `_handle_global_refresh`
    # Simulate a global refresh signal
    refresh_callback = switch_entity._handle_global_refresh
    # Modify the "source of truth" in hass.data
    hass.data[DOMAIN][switch_entity._entry_id]["devices"][0][DEVICE_DATA_KEY]["L1"][
        "type"
    ] = 129
    refresh_callback()

    assert switch_entity.is_on is True
    assert switch_entity.async_write_ha_state.call_count == 2

    # 3. Test global refresh when device is missing
    hass.data[DOMAIN][switch_entity._entry_id]["devices"] = []  # Remove all devices
    with patch.object(switch_entity, "_LOGGER") as mock_logger:
        refresh_callback()
        mock_logger.warning.assert_called_once()
        assert "Could not find device" in mock_logger.warning.call_args[0][0]
