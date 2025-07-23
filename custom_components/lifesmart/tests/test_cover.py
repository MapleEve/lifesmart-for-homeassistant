"""Unit and integration tests for the LifeSmart cover platform."""

from unittest.mock import MagicMock

import pytest
from homeassistant.components.cover import (
    ATTR_POSITION,
    DOMAIN as COVER_DOMAIN,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_SET_COVER_POSITION,
    SERVICE_STOP_COVER,
    CoverDeviceClass,
    CoverEntityFeature,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

# Import all constants and classes from the component
from custom_components.lifesmart.const import *

pytestmark = pytest.mark.asyncio


# --- Helper to find a device in the shared fixture ---
def find_device(devices: list, me: str):
    """Helper to find a specific device from the mock list by its 'me' id."""
    return next((d for d in devices if d.get(DEVICE_ID_KEY) == me), None)


async def setup_platform(
    hass: HomeAssistant, mock_client: MagicMock, devices: list, config_entry: MagicMock
) -> None:
    """Helper function to set up the cover platform."""
    hass.data.setdefault(DOMAIN, {})[config_entry.entry_id] = {
        "client": mock_client,
        "devices": devices,
        "exclude_devices": [],
        "exclude_hubs": [],
    }
    await hass.config_entries.async_forward_entry_setup(config_entry, COVER_DOMAIN)
    await hass.async_block_till_done()


# --- TEST SUITE ---


@pytest.mark.asyncio
class TestCoverSetup:
    """Tests for the platform setup."""

    async def test_setup_entry_creates_entities(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry: MagicMock,
        mock_lifesmart_devices: list,
    ):
        """Test that cover entities are created for all supported device types."""
        await setup_platform(
            hass, mock_client, mock_lifesmart_devices, mock_config_entry
        )

        # Expected covers from conftest.py: cover_garage, cover_dooya, cover_nonpos = 3
        assert len(hass.states.async_entity_ids(COVER_DOMAIN)) == 3
        assert hass.states.get("cover.garage_door") is not None
        assert hass.states.get("cover.living_room_curtain") is not None
        assert hass.states.get("cover.bedroom_curtain") is not None

    async def test_setup_entry_with_exclusions(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry: MagicMock,
        mock_lifesmart_devices: list,
    ):
        """Test that excluded devices are not added."""
        hass.data[DOMAIN][mock_config_entry.entry_id] = {
            "client": mock_client,
            "devices": mock_lifesmart_devices,
            "exclude_devices": ["cover_dooya"],  # Exclude by 'me' from conftest.py
            "exclude_hubs": [],
        }
        await hass.config_entries.async_forward_entry_setup(
            mock_config_entry, COVER_DOMAIN
        )
        await hass.async_block_till_done()

        assert hass.states.get("cover.garage_door") is not None
        assert (
            hass.states.get("cover.living_room_curtain") is None
        )  # Should be excluded
        assert hass.states.get("cover.bedroom_curtain") is not None


@pytest.mark.asyncio
class TestCoverEntity:
    """Tests for the LifeSmartCover entity class."""

    @pytest.mark.parametrize(
        "device_me, expected_class, expected_features",
        [
            (
                "cover_garage",
                CoverDeviceClass.GARAGE,
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
                | CoverEntityFeature.STOP
                | CoverEntityFeature.SET_POSITION,
            ),
            (
                "cover_dooya",
                CoverDeviceClass.CURTAIN,
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
                | CoverEntityFeature.STOP
                | CoverEntityFeature.SET_POSITION,
            ),
            (
                "cover_nonpos",
                CoverDeviceClass.CURTAIN,
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
                | CoverEntityFeature.STOP,
            ),
        ],
        ids=["Garage", "PositionalCurtain", "NonPositionalCurtain"],
    )
    async def test_entity_initialization(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry: MagicMock,
        mock_lifesmart_devices: list,
        device_me,
        expected_class,
        expected_features,
    ):
        """Test entity features and device class based on device type."""
        device = find_device(mock_lifesmart_devices, device_me)
        await setup_platform(hass, mock_client, [device], mock_config_entry)
        entity_id = f"cover.{device[DEVICE_NAME_KEY].lower().replace(' ', '_')}"
        state = hass.states.get(entity_id)

        assert state is not None
        assert state.attributes.get("device_class") == expected_class
        assert state.attributes.get("supported_features") == expected_features

    @pytest.mark.parametrize(
        "device_me, io_key, data, expected_pos, exp_opening, exp_closing, exp_is_closed",
        [
            ("cover_garage", "P2", {"val": 0, "type": 128}, 0, False, False, True),
            ("cover_dooya", "P1", {"val": 100, "type": 128}, 100, False, False, False),
            ("cover_garage", "P2", {"val": 50, "type": 128}, 50, False, False, False),
            (
                "cover_dooya",
                "P1",
                {"val": 178, "type": 129},
                50,
                True,
                False,
                False,
            ),  # Opening (val=0x80|50)
            (
                "cover_garage",
                "P2",
                {"val": 50, "type": 129},
                50,
                False,
                True,
                False,
            ),  # Closing (val=50)
        ],
        ids=["Closed", "Open", "Stopped", "Opening", "Closing"],
    )
    async def test_positional_cover_state_update(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry: MagicMock,
        mock_lifesmart_devices: list,
        device_me,
        io_key,
        data,
        expected_pos,
        exp_opening,
        exp_closing,
        exp_is_closed,
    ):
        """Test state parsing for covers that support set_position."""
        device = find_device(mock_lifesmart_devices, device_me)
        # Create a copy to modify its data for the test
        device_copy = {**device, DEVICE_DATA_KEY: {io_key: data}}

        await setup_platform(hass, mock_client, [device_copy], mock_config_entry)

        entity_id = f"cover.{device[DEVICE_NAME_KEY].lower().replace(' ', '_')}"
        state = hass.states.get(entity_id)

        # CORRECTED: Use state.attributes.get("current_position") instead of the old constant
        assert state.attributes.get("current_position") == expected_pos
        assert state.attributes.get("is_opening") == exp_opening
        assert state.attributes.get("is_closing") == exp_closing
        assert state.attributes.get("is_closed") == exp_is_closed

    async def test_service_calls(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry: MagicMock,
        mock_lifesmart_devices: list,
    ):
        """Test that cover services call the correct client methods."""
        device = find_device(mock_lifesmart_devices, "cover_dooya")
        await setup_platform(hass, mock_client, [device], mock_config_entry)
        entity_id = "cover.living_room_curtain"

        await hass.services.async_call(
            COVER_DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )
        mock_client.open_cover_async.assert_awaited_once_with(
            "hub_cover", "cover_dooya", device[DEVICE_TYPE_KEY]
        )

        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_client.close_cover_async.assert_awaited_once_with(
            "hub_cover", "cover_dooya", device[DEVICE_TYPE_KEY]
        )

        await hass.services.async_call(
            COVER_DOMAIN, SERVICE_STOP_COVER, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )
        mock_client.stop_cover_async.assert_awaited_once_with(
            "hub_cover", "cover_dooya", device[DEVICE_TYPE_KEY]
        )

        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_SET_COVER_POSITION,
            {ATTR_ENTITY_ID: entity_id, ATTR_POSITION: 60},
            blocking=True,
        )
        mock_client.set_cover_position_async.assert_awaited_once_with(
            "hub_cover", "cover_dooya", 60, device[DEVICE_TYPE_KEY]
        )

    async def test_data_dispatcher(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry: MagicMock,
        mock_lifesmart_devices: list,
    ):
        """Test that entity updates via both specific and global dispatchers."""
        device = find_device(mock_lifesmart_devices, "cover_dooya")
        await setup_platform(hass, mock_client, [device], mock_config_entry)
        entity_id = "cover.living_room_curtain"
        entity_registry = async_get_entity_registry(hass)
        entry = entity_registry.async_get(entity_id)

        # CORRECTED: Use state.attributes.get("current_position")
        assert hass.states.get(entity_id).attributes.get("current_position") == 100

        # Test entity-specific update
        new_data_specific = {"P1": {"val": 30, "type": 128}}
        async_dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entry.unique_id}",
            new_data_specific,
        )
        await hass.async_block_till_done()
        assert hass.states.get(entity_id).attributes.get("current_position") == 30

        # Test global refresh update
        device_in_hass = find_device(
            hass.data[DOMAIN][mock_config_entry.entry_id]["devices"], "cover_dooya"
        )
        device_in_hass[DEVICE_DATA_KEY] = {"P1": {"val": 45, "type": 128}}

        async_dispatcher_send(hass, LIFESMART_SIGNAL_UPDATE_ENTITY)
        await hass.async_block_till_done()
        assert hass.states.get(entity_id).attributes.get("current_position") == 45
