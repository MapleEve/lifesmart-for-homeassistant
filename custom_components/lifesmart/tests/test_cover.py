"""Unit and integration tests for the LifeSmart cover platform."""

from unittest.mock import AsyncMock, MagicMock

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

from custom_components.lifesmart.const import *
from custom_components.lifesmart.cover import async_setup_entry

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
        assert hass.states.get("cover.garage_door_p2") is not None
        assert hass.states.get("cover.living_room_curtain_p1") is not None
        assert hass.states.get("cover.bedroom_curtain_p1") is not None

    async def test_setup_entry_with_exclusions(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry: ConfigEntry,
        mock_lifesmart_devices: list,
    ):
        """Test that excluded devices are not added using a manual setup."""
        mock_config_entry.add_to_hass(hass)

        try:
            hass.config_entries.async_update_entry(
                mock_config_entry,
                options={
                    CONF_EXCLUDE_ITEMS: "cover_dooya",
                    CONF_EXCLUDE_AGTS: "",
                },
            )
            await hass.async_block_till_done()

            async_add_entities_mock = AsyncMock()
            hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = {
                "client": mock_client,
                "devices": mock_lifesmart_devices,
            }

            await async_setup_entry(hass, mock_config_entry, async_add_entities_mock)
            await hass.async_block_till_done()

            created_entities = async_add_entities_mock.call_args[0][0]
            created_names = {entity.name for entity in created_entities}

            assert "Garage Door P2" in created_names
            assert "Living Room Curtain P1" not in created_names
            assert "Bedroom Curtain P1" in created_names
            assert len(created_names) == 2

        finally:
            if hass.data.get(DOMAIN, {}).get(mock_config_entry.entry_id):
                hass.data[DOMAIN].pop(mock_config_entry.entry_id)


@pytest.mark.asyncio
class TestCoverEntity:
    """Tests for the LifeSmartCover entity class."""

    @pytest.mark.parametrize(
        "device_me, sub_key, expected_class, expected_features",
        [
            (
                "cover_garage",
                "P2",
                CoverDeviceClass.GARAGE,
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
                | CoverEntityFeature.STOP
                | CoverEntityFeature.SET_POSITION,
            ),
            (
                "cover_dooya",
                "P1",
                CoverDeviceClass.CURTAIN,
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
                | CoverEntityFeature.STOP
                | CoverEntityFeature.SET_POSITION,
            ),
            (
                "cover_nonpos",
                "P1",
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
        sub_key,
        expected_class,
        expected_features,
    ):
        """Test entity features and device class based on device type."""
        device = find_device(mock_lifesmart_devices, device_me)
        entity_id = f"cover.{device[DEVICE_NAME_KEY].lower().replace(' ', '_')}_{sub_key.lower()}"
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
        entity_id = f"cover.{device[DEVICE_NAME_KEY].lower().replace(' ', '_')}_{io_key.lower()}"
        entity_registry = async_get_entity_registry(hass)
        entry = entity_registry.async_get(entity_id)

        # The new _handle_update expects the full device data, not just the sub-key
        full_update_data = device[DEVICE_DATA_KEY].copy()
        full_update_data[io_key] = data

        async_dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entry.unique_id}",
            full_update_data,
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
        entity_id = "cover.living_room_curtain_p1"

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
        entity_id = "cover.living_room_curtain_p1"
        entity_registry = async_get_entity_registry(hass)
        entry = entity_registry.async_get(entity_id)

        assert hass.states.get(entity_id).attributes.get(ATTR_CURRENT_POSITION) == 100

        # Test specific update
        device_in_hass = find_device(
            hass.data[DOMAIN][setup_integration.entry_id]["devices"], "cover_dooya"
        )
        new_data_specific = device_in_hass[DEVICE_DATA_KEY].copy()
        new_data_specific["P1"] = {"val": 30, "type": 128}

        async_dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entry.unique_id}",
            new_data_specific,
        )
        await hass.async_block_till_done()
        assert hass.states.get(entity_id).attributes.get(ATTR_CURRENT_POSITION) == 30

        # Test global update
        device_in_hass[DEVICE_DATA_KEY]["P1"] = {"val": 45, "type": 128}

        async_dispatcher_send(hass, LIFESMART_SIGNAL_UPDATE_ENTITY)
        await hass.async_block_till_done()
        assert hass.states.get(entity_id).attributes.get(ATTR_CURRENT_POSITION) == 45
