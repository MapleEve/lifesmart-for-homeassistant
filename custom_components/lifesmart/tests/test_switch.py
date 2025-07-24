"""Unit tests for the LifeSmart switch platform."""

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.switch import SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from custom_components.lifesmart.const import *
from custom_components.lifesmart.switch import (
    DOMAIN as SWITCH_DOMAIN,
    LifeSmartSwitch,
    _is_switch_subdevice,
    async_setup_entry,
)

pytestmark = pytest.mark.asyncio


# --- Helper to find a device in the shared fixture ---
def find_device(devices: list, me: str):
    """Helper to find a specific device from the mock list by its 'me' id."""
    return next((d for d in devices if d.get(DEVICE_ID_KEY) == me), None)


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
    setup_integration: ConfigEntry,
) -> None:
    """Test successful setup of switch entities using shared fixtures."""
    # Assert
    # Expected switches from conftest.py:
    # 3 (from sw_if3) + 1 (from sw_ol) + 2 (from sw_oe3c) + 3 (from sw_nature) = 9
    assert len(hass.states.async_entity_ids("switch")) == 9


async def test_async_setup_entry_with_exclusions(
    hass: HomeAssistant,
    mock_client: AsyncMock,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test that devices and hubs can be excluded from setup."""
    mock_config_entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        mock_config_entry,
        options={
            CONF_EXCLUDE_ITEMS: "sw_ol",
            CONF_EXCLUDE_AGTS: "hub_sw_excluded",
        },
    )
    await hass.async_block_till_done()

    with patch("custom_components.lifesmart.LifeSmartClient", return_value=mock_client):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert len(hass.states.async_entity_ids(SWITCH_DOMAIN)) == 6
    assert hass.states.get("switch.3_gang_switch_l1") is not None
    assert hass.states.get("switch.smart_outlet_o") is None
    assert hass.states.get("switch.power_plug_p1") is None

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()


async def test_async_setup_entry_no_switches(
    hass: HomeAssistant,
    mock_client: AsyncMock,
    mock_config_entry: ConfigEntry,
) -> None:
    """Test setup with no switch devices."""
    # Arrange
    hass.data[DOMAIN][mock_config_entry.entry_id] = {
        "client": mock_client,
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
    await async_setup_entry(hass, mock_config_entry, async_add_entities)

    # Assert
    async_add_entities.assert_called_once_with([])


# --- Test `LifeSmartSwitch` Entity Class ---


@pytest.fixture
def switch_entity(
    hass: HomeAssistant,
    mock_client: AsyncMock,
    mock_config_entry: ConfigEntry,
    mock_lifesmart_devices: list[dict[str, Any]],
) -> LifeSmartSwitch:
    """Provides a standard LifeSmartSwitch entity for testing."""
    device_data = next(
        (d for d in mock_lifesmart_devices if d.get(DEVICE_ID_KEY) == "sw_if3"), None
    )
    assert device_data, "Device 'sw_if3' not found"

    # This setup is for isolated unit tests, not using the full integration setup
    ha_device = LifeSmartSwitch(
        raw_device=device_data,
        sub_device_key="L1",
        sub_device_data=device_data[DEVICE_DATA_KEY]["L1"],
        client=mock_client,
        entry_id=mock_config_entry.entry_id,
    )
    ha_device.hass = hass
    hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = {
        "devices": mock_lifesmart_devices
    }
    return ha_device


def test_switch_init_and_properties(switch_entity: LifeSmartSwitch) -> None:
    """Test the initialization and basic properties of the switch entity."""
    assert switch_entity.unique_id == "SL_SW_IF3_hub_sw_sw_if3_L1"
    assert switch_entity.name == "3-Gang Switch L1"
    assert switch_entity.device_class == SwitchDeviceClass.SWITCH
    assert switch_entity.is_on is True  # Initial state from L1 is 'on' (type 129)
    assert switch_entity.extra_state_attributes == {
        "hub_id": "hub_sw",
        "device_id": "sw_if3",
        "subdevice_index": "L1",
    }


def test_switch_name_generation(
    mock_client: AsyncMock, mock_config_entry: ConfigEntry
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
        raw_device=base_device,
        sub_device_key="P1",
        sub_device_data=base_device[DEVICE_DATA_KEY]["P1"],
        client=mock_client,
        entry_id=mock_config_entry.entry_id,
    )
    assert entity_with_subname.name == "Device Base Name Button Name"

    # Without sub-name
    entity_without_subname = LifeSmartSwitch(
        raw_device=base_device,
        sub_device_key="P2",
        sub_device_data=base_device[DEVICE_DATA_KEY]["P2"],
        client=mock_client,
        entry_id=mock_config_entry.entry_id,
    )
    assert entity_without_subname.name == "Device Base Name P2"


def test_determine_device_class(
    mock_client: AsyncMock, mock_config_entry: ConfigEntry
) -> None:
    """Test device class determination for outlets and switches."""
    # Test for OUTLET
    for dev_type in SMART_PLUG_TYPES | POWER_METER_PLUG_TYPES:
        device_data = {DEVICE_TYPE_KEY: dev_type, DEVICE_DATA_KEY: {}}
        entity = LifeSmartSwitch(
            device_data, "P1", {}, mock_client, mock_config_entry.entry_id
        )
        assert entity.device_class == SwitchDeviceClass.OUTLET

    # Test for SWITCH
    device_data = {DEVICE_TYPE_KEY: "SL_SW_IF3", DEVICE_DATA_KEY: {}}
    entity = LifeSmartSwitch(
        device_data, "P1", {}, mock_client, mock_config_entry.entry_id
    )
    assert entity.device_class == SwitchDeviceClass.SWITCH


def test_parse_state() -> None:
    """Test the _parse_state method."""
    dummy_switch = LifeSmartSwitch(
        raw_device={
            HUB_ID_KEY: "a",
            DEVICE_ID_KEY: "b",
            DEVICE_TYPE_KEY: "c",
            DEVICE_DATA_KEY: {},
        },
        sub_device_key="k",
        sub_device_data={},
        client=AsyncMock(),
        entry_id="e",
    )
    assert dummy_switch._parse_state({"type": 129}) is True
    assert dummy_switch._parse_state({"type": 1}) is True
    assert dummy_switch._parse_state({"type": 128}) is False
    assert dummy_switch._parse_state({"type": 0}) is False
    assert dummy_switch._parse_state({}) is False


async def test_turn_on_off(
    switch_entity: LifeSmartSwitch,
) -> None:
    """Test turning the switch on and off."""
    client = switch_entity._client
    switch_entity.async_write_ha_state = AsyncMock()

    # Turn on
    await switch_entity.async_turn_on()
    client.turn_on_light_switch_async.assert_awaited_once_with("L1", "hub_sw", "sw_if3")
    assert switch_entity.is_on is True
    switch_entity.async_write_ha_state.assert_called_once()

    # Turn off
    await switch_entity.async_turn_off()
    client.turn_off_light_switch_async.assert_awaited_once_with(
        "L1", "hub_sw", "sw_if3"
    )
    assert switch_entity.is_on is False
    assert switch_entity.async_write_ha_state.call_count == 2


async def test_data_update_handlers(
    hass: HomeAssistant, switch_entity: LifeSmartSwitch
) -> None:
    """Test that the switch state updates via dispatcher signals."""
    switch_entity.async_write_ha_state = AsyncMock()

    # 1. Test `_handle_update` (specific entity update)
    update_callback = switch_entity._handle_update
    await update_callback({"type": 128})  # Turn off
    assert switch_entity.is_on is False
    switch_entity.async_write_ha_state.assert_called_once()

    # 2. Test `_handle_global_refresh`
    device_in_hass = next(
        (
            d
            for d in hass.data[DOMAIN][switch_entity._entry_id]["devices"]
            if d.get(DEVICE_ID_KEY) == "sw_if3"
        ),
        None,
    )
    device_in_hass[DEVICE_DATA_KEY]["L1"]["type"] = 129  # Turn on

    refresh_callback = switch_entity._handle_global_refresh
    await refresh_callback()

    assert switch_entity.is_on is True
    assert switch_entity.async_write_ha_state.call_count == 2
