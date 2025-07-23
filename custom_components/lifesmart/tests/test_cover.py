"""Unit and integration tests for the LifeSmart cover platform."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_POSITION,
    DOMAIN as COVER_DOMAIN,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_SET_COVER_POSITION,
    SERVICE_STOP_COVER,
    CoverDeviceClass,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, STATE_CLOSED, STATE_OPEN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from custom_components.lifesmart import async_setup_entry
from custom_components.lifesmart.const import *

pytestmark = pytest.mark.asyncio


# --- Helper to find a device in the shared fixture ---
def find_device(devices: list, me: str):
    """Helper to find a specific device from the mock list by its 'me' id."""
    return next((d for d in devices if d.get(DEVICE_ID_KEY) == me), None)


# --- TEST SUITE ---


@pytest.mark.asyncio
class TestCoverSetup:
    """Tests for the platform setup."""

    async def test_setup_entry_creates_entities(
        self, hass: HomeAssistant, setup_integration: ConfigEntry
    ):
        """Test that cover entities are created for all supported device types."""
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
        """Test that excluded devices are not added using a manual setup."""
        mock_config_entry.add_to_hass(hass)
        hass.config_entries.async_update_entry(
            mock_config_entry,
            options={
                CONF_EXCLUDE_ITEMS: "cover_dooya",
                CONF_EXCLUDE_AGTS: "",
            },
        )
        await hass.async_block_till_done()

        with patch(
            "custom_components.lifesmart.LifeSmartClient", return_value=mock_client
        ):
            await async_setup_entry(hass, mock_config_entry)
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
        setup_integration: ConfigEntry,
        mock_lifesmart_devices: list,
        device_me,
        expected_class,
        expected_features,
    ):
        """Test entity features and device class based on device type."""
        device = find_device(mock_lifesmart_devices, device_me)
        entity_id = f"cover.{device[DEVICE_NAME_KEY].lower().replace(' ', '_')}"
        state = hass.states.get(entity_id)

        assert state is not None
        assert state.attributes.get("device_class") == expected_class
        assert state.attributes.get("supported_features") == expected_features

    @pytest.mark.parametrize(
        "device_me, io_key, data, expected_pos, exp_state",
        [
            ("cover_garage", "P2", {"val": 0, "type": 128}, 0, STATE_CLOSED),
            ("cover_dooya", "P1", {"val": 100, "type": 128}, 100, STATE_OPEN),
            ("cover_garage", "P2", {"val": 50, "type": 128}, 50, STATE_OPEN),
            ("cover_dooya", "P1", {"val": 50, "type": 129}, 50, STATE_OPEN),
        ],
        ids=["Closed", "Open", "Stopped", "Moving"],
    )
    async def test_positional_cover_state_update(
        self,
        hass: HomeAssistant,
        setup_integration: ConfigEntry,
        mock_lifesmart_devices: list,
        device_me,
        io_key,
        data,
        expected_pos,
        exp_state,
    ):
        """Test state parsing for covers that support set_position."""
        device = find_device(mock_lifesmart_devices, device_me)
        entity_id = f"cover.{device[DEVICE_NAME_KEY].lower().replace(' ', '_')}"
        entity_registry = async_get_entity_registry(hass)
        entry = entity_registry.async_get(entity_id)

        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entry.unique_id}", {io_key: data}
        )
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        assert state.attributes.get(ATTR_CURRENT_POSITION) == expected_pos
        assert state.state == exp_state

    async def test_service_calls(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        setup_integration: ConfigEntry,
        mock_lifesmart_devices: list,
    ):
        """Test that cover services call the correct client methods."""
        device = find_device(mock_lifesmart_devices, "cover_dooya")
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
        setup_integration: ConfigEntry,
        mock_lifesmart_devices: list,
    ):
        """Test that entity updates via both specific and global dispatchers."""
        entity_id = "cover.living_room_curtain"
        entity_registry = async_get_entity_registry(hass)
        entry = entity_registry.async_get(entity_id)

        assert hass.states.get(entity_id).attributes.get(ATTR_CURRENT_POSITION) == 100

        new_data_specific = {"P1": {"val": 30, "type": 128}}
        async_dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entry.unique_id}",
            new_data_specific,
        )
        await hass.async_block_till_done()
        assert hass.states.get(entity_id).attributes.get(ATTR_CURRENT_POSITION) == 30

        device_in_hass = find_device(
            hass.data[DOMAIN][setup_integration.entry_id]["devices"], "cover_dooya"
        )
        device_in_hass[DEVICE_DATA_KEY] = {"P1": {"val": 45, "type": 128}}

        async_dispatcher_send(hass, LIFESMART_SIGNAL_UPDATE_ENTITY)
        await hass.async_block_till_done()
        assert hass.states.get(entity_id).attributes.get(ATTR_CURRENT_POSITION) == 45
