"""Unit and integration tests for the LifeSmart cover platform."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.cover import (
    ATTR_CURRENT_COVER_POSITION,
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


# --- MOCK DEVICE DATA USING CONSTANTS ONLY ---


# Helper to get the first device type from a constant tuple/list
def get_first_devtype(const_list):
    return const_list[0] if const_list else "FALLBACK_TYPE"


# Positional Garage Door, using the first type from GARAGE_DOOR_TYPES
MOCK_GARAGE_DOOR = {
    HUB_ID_KEY: "mock_hub_id",
    DEVICE_ID_KEY: "mock_garage_id",
    DEVICE_TYPE_KEY: get_first_devtype(GARAGE_DOOR_TYPES),
    DEVICE_NAME_KEY: "Garage Door",
    DEVICE_DATA_KEY: {"P2": {"val": 0, "type": 128}},  # Closed, stopped
}

# Positional Dooya Curtain, using the first type from DOOYA_TYPES
MOCK_DOOYA_CURTAIN = {
    HUB_ID_KEY: "mock_hub_id",
    DEVICE_ID_KEY: "mock_dooya_id",
    DEVICE_TYPE_KEY: get_first_devtype(DOOYA_TYPES),
    DEVICE_NAME_KEY: "Living Room Curtain",
    DEVICE_DATA_KEY: {"P1": {"val": 100, "type": 128}},  # Open, stopped
}

# Non-Positional Curtain, using a type from NON_POSITIONAL_COVER_CONFIG
NON_POSITIONAL_TYPE = next(iter(NON_POSITIONAL_COVER_CONFIG))
MOCK_NON_POSITIONAL_CURTAIN = {
    HUB_ID_KEY: "mock_hub_id",
    DEVICE_ID_KEY: "mock_non_pos_id",
    DEVICE_TYPE_KEY: NON_POSITIONAL_TYPE,
    DEVICE_NAME_KEY: "Bedroom Curtain",
    DEVICE_DATA_KEY: {
        "O": {"type": 128},
        "C": {"type": 128},
    },  # Stopped
}

# --- PYTEST FIXTURES AND HELPERS ---


@pytest.fixture(name="mock_client")
def mock_lifesmart_client():
    """Fixture for a mocked LifeSmart client."""
    client = MagicMock()
    client.open_cover_async = AsyncMock(return_value=0)
    client.close_cover_async = AsyncMock(return_value=0)
    client.stop_cover_async = AsyncMock(return_value=0)
    client.set_cover_position_async = AsyncMock(return_value=0)
    return client


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
        self, hass: HomeAssistant, mock_client: MagicMock, mock_config_entry: MagicMock
    ):
        """Test that cover entities are created for all supported device types."""
        non_cover_device = {DEVICE_TYPE_KEY: "SL_SW_IF1"}  # Should be ignored
        devices = [
            MOCK_GARAGE_DOOR,
            MOCK_DOOYA_CURTAIN,
            MOCK_NON_POSITIONAL_CURTAIN,
            non_cover_device,
        ]
        await setup_platform(hass, mock_client, devices, mock_config_entry)

        assert len(hass.states.async_entity_ids(COVER_DOMAIN)) == 3
        assert hass.states.get("cover.garage_door") is not None
        assert hass.states.get("cover.living_room_curtain") is not None
        assert hass.states.get("cover.bedroom_curtain") is not None

    async def test_setup_entry_with_exclusions(
        self, hass: HomeAssistant, mock_client: MagicMock, mock_config_entry: MagicMock
    ):
        """Test that excluded devices are not added."""
        hass.data[DOMAIN][mock_config_entry.entry_id] = {
            "client": mock_client,
            "devices": [MOCK_GARAGE_DOOR, MOCK_DOOYA_CURTAIN],
            "exclude_devices": ["mock_dooya_id"],
            "exclude_hubs": [],
        }
        await hass.config_entries.async_forward_entry_setup(
            mock_config_entry, COVER_DOMAIN
        )
        await hass.async_block_till_done()

        assert hass.states.get("cover.garage_door") is not None
        assert hass.states.get("cover.living_room_curtain") is None


@pytest.mark.asyncio
class TestCoverEntity:
    """Tests for the LifeSmartCover entity class."""

    @pytest.mark.parametrize(
        "device, expected_class, expected_features",
        [
            (
                MOCK_GARAGE_DOOR,
                CoverDeviceClass.GARAGE,
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
                | CoverEntityFeature.STOP
                | CoverEntityFeature.SET_POSITION,
            ),
            (
                MOCK_DOOYA_CURTAIN,
                CoverDeviceClass.CURTAIN,
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
                | CoverEntityFeature.STOP
                | CoverEntityFeature.SET_POSITION,
            ),
            (
                MOCK_NON_POSITIONAL_CURTAIN,
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
        device,
        expected_class,
        expected_features,
    ):
        """Test entity features and device class based on device type."""
        await setup_platform(hass, mock_client, [device], mock_config_entry)
        entity_id = f"cover.{device[DEVICE_NAME_KEY].lower().replace(' ', '_')}"
        state = hass.states.get(entity_id)

        assert state is not None
        assert state.attributes.get("device_class") == expected_class
        assert state.attributes.get("supported_features") == expected_features

    @pytest.mark.parametrize(
        "io_key, data, expected_pos, exp_opening, exp_closing, exp_is_closed",
        [
            ("P2", {"val": 0, "type": 128}, 0, False, False, True),  # Garage closed
            ("P1", {"val": 100, "type": 128}, 100, False, False, False),  # Dooya open
            ("P2", {"val": 50, "type": 128}, 50, False, False, False),  # Stopped
            (
                "P1",
                {"val": 178, "type": 129},
                50,
                True,
                False,
                False,
            ),  # Opening (val=0x80|50)
            (
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
        io_key,
        data,
        expected_pos,
        exp_opening,
        exp_closing,
        exp_is_closed,
    ):
        """Test state parsing for covers that support set_position."""
        devtype = get_first_devtype(
            GARAGE_DOOR_TYPES if io_key == "P2" else DOOYA_TYPES
        )
        device = {
            **MOCK_GARAGE_DOOR,
            DEVICE_TYPE_KEY: devtype,
            DEVICE_DATA_KEY: {io_key: data},
        }
        await setup_platform(hass, mock_client, [device], mock_config_entry)

        state = hass.states.get("cover.garage_door")
        assert state.attributes.get(ATTR_CURRENT_COVER_POSITION) == expected_pos
        assert state.attributes.get("is_opening") == exp_opening
        assert state.attributes.get("is_closing") == exp_closing
        assert state.attributes.get("is_closed") == exp_is_closed

    async def test_service_calls(
        self, hass: HomeAssistant, mock_client: MagicMock, mock_config_entry: MagicMock
    ):
        """Test that cover services call the correct client methods."""
        device = MOCK_DOOYA_CURTAIN
        await setup_platform(hass, mock_client, [device], mock_config_entry)
        entity_id = "cover.living_room_curtain"

        await hass.services.async_call(
            COVER_DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )
        mock_client.open_cover_async.assert_awaited_once_with(
            "mock_hub_id", "mock_dooya_id", device[DEVICE_TYPE_KEY]
        )

        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_client.close_cover_async.assert_awaited_once_with(
            "mock_hub_id", "mock_dooya_id", device[DEVICE_TYPE_KEY]
        )

        await hass.services.async_call(
            COVER_DOMAIN, SERVICE_STOP_COVER, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )
        mock_client.stop_cover_async.assert_awaited_once_with(
            "mock_hub_id", "mock_dooya_id", device[DEVICE_TYPE_KEY]
        )

        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_SET_COVER_POSITION,
            {ATTR_ENTITY_ID: entity_id, ATTR_POSITION: 60},
            blocking=True,
        )
        mock_client.set_cover_position_async.assert_awaited_once_with(
            "mock_hub_id", "mock_dooya_id", 60, device[DEVICE_TYPE_KEY]
        )

    async def test_data_dispatcher(
        self, hass: HomeAssistant, mock_client: MagicMock, mock_config_entry: MagicMock
    ):
        """Test that entity updates via both specific and global dispatchers."""
        await setup_platform(hass, mock_client, [MOCK_DOOYA_CURTAIN], mock_config_entry)
        entity_id = "cover.living_room_curtain"
        entity_registry = async_get_entity_registry(hass)
        entry = entity_registry.async_get(entity_id)

        assert (
            hass.states.get(entity_id).attributes.get(ATTR_CURRENT_COVER_POSITION)
            == 100
        )

        # Test entity-specific update
        new_data_specific = {"P1": {"val": 30, "type": 128}}
        async_dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entry.unique_id}",
            new_data_specific,
        )
        await hass.async_block_till_done()
        assert (
            hass.states.get(entity_id).attributes.get(ATTR_CURRENT_COVER_POSITION) == 30
        )

        # Test global refresh update
        hass.data[DOMAIN][mock_config_entry.entry_id]["devices"][0][DEVICE_DATA_KEY] = {
            "P1": {"val": 45, "type": 128}
        }
        async_dispatcher_send(hass, LIFESMART_SIGNAL_UPDATE_ENTITY)
        await hass.async_block_till_done()
        assert (
            hass.states.get(entity_id).attributes.get(ATTR_CURRENT_COVER_POSITION) == 45
        )
