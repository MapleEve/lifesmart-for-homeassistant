"""Test cases for the LifeSmart integration setup and functionality."""

import asyncio
import unittest
from unittest.mock import patch, AsyncMock, MagicMock

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.util import dt as dt_util

from custom_components.lifesmart import (
    async_setup_entry,
    async_unload_entry,
    data_update_handler,
    generate_unique_id,
    LifeSmartStateManager,
)
from custom_components.lifesmart.const import (
    DOMAIN,
    LIFESMART_STATE_MANAGER,
    SUPPORTED_PLATFORMS,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
)
from custom_components.lifesmart.exceptions import LifeSmartAuthError

# --- MOCK DATA ---

MOCK_DEVICES = [
    {
        "agt": "mock_hub_1",
        "me": "mock_switch_1",
        "devtype": "SL_SW_IF1",  # A switch
        "name": "Test Switch",
        "data": {"L1": {"type": 129, "val": 1}},
    },
    {
        "agt": "mock_hub_1",
        "me": "mock_light_1",
        "devtype": "SL_LI_RGBW",  # A light
        "name": "Test Light",
        "data": {
            "RGBW": {"type": 129, "val": 0xFFFFFF},
            "DYN": {"type": 128, "val": 0},
        },
    },
]

MOCK_AUTH_RESPONSE = {
    "usertoken": "new_refreshed_token",
    "expiredtime": int(dt_util.utcnow().timestamp() + 3600),
}

# --- TESTS ---


@pytest.mark.asyncio
async def test_async_setup_entry_success(hass: HomeAssistant, mock_config_entry):
    """Test successful setup of the integration."""
    with patch(
        "custom_components.lifesmart._async_create_client_and_get_devices",
        return_value=(AsyncMock(), MOCK_DEVICES, MOCK_AUTH_RESPONSE),
    ) as mock_create_client, patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups"
    ) as mock_forward_setups, patch(
        "custom_components.lifesmart._async_register_services"
    ) as mock_register_services, patch(
        "custom_components.lifesmart._async_setup_background_tasks"
    ) as mock_setup_tasks:

        # Run setup
        assert await async_setup_entry(hass, mock_config_entry) is True
        await hass.async_block_till_done()

        # 1. Verify client creation and data fetching
        mock_create_client.assert_called_once_with(hass, mock_config_entry)

        # 2. Verify hub registration
        device_registry = dr.async_get(hass)
        hub_device = device_registry.async_get_device(
            identifiers={(DOMAIN, "mock_hub_1")}
        )
        assert hub_device is not None
        assert (
            hub_device.name == "LifeSmart Hub (ck_hub_)"
        )  # Note: name generation depends on hub_id slicing

        # 3. Verify hass.data is populated
        entry_data = hass.data[DOMAIN][mock_config_entry.entry_id]
        assert entry_data["client"] is not None
        assert entry_data["devices"] == MOCK_DEVICES

        # 4. Verify platforms are forwarded
        mock_forward_setups.assert_called_once_with(
            mock_config_entry, SUPPORTED_PLATFORMS
        )

        # 5. Verify services and background tasks are set up
        mock_register_services.assert_called_once()
        mock_setup_tasks.assert_called_once()


@pytest.mark.asyncio
async def test_async_setup_entry_auth_failure(hass: HomeAssistant, mock_config_entry):
    """Test setup failure due to authentication error."""
    with patch(
        "custom_components.lifesmart._async_create_client_and_get_devices",
        side_effect=LifeSmartAuthError("Invalid credentials"),
    ):
        # Setup should fail and return False, not raise ConfigEntryNotReady for auth errors
        assert await async_setup_entry(hass, mock_config_entry) is False
        assert mock_config_entry.state == ConfigEntryState.SETUP_ERROR


@pytest.mark.asyncio
async def test_async_setup_entry_connection_failure(
    hass: HomeAssistant, mock_config_entry
):
    """Test setup being deferred due to a connection error."""
    with patch(
        "custom_components.lifesmart._async_create_client_and_get_devices",
        side_effect=ConfigEntryNotReady("Cannot connect to server"),
    ):
        # ConfigEntryNotReady should be raised to HA core for retry
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, mock_config_entry)
        assert mock_config_entry.state == ConfigEntryState.SETUP_RETRY


@pytest.mark.asyncio
async def test_async_unload_entry(
    hass: HomeAssistant, mock_config_entry, mock_setup_entry
):
    """Test successful unloading of the integration."""
    # Setup a mock state manager
    mock_state_manager = AsyncMock()
    hass.data[DOMAIN][LIFESMART_STATE_MANAGER] = mock_state_manager

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        return_value=True,
    ) as mock_unload:
        assert await async_unload_entry(hass, mock_config_entry) is True

        # Verify state manager was stopped
        mock_state_manager.stop.assert_called_once()

        # Verify platforms were unloaded
        mock_unload.assert_called_once_with(mock_config_entry, SUPPORTED_PLATFORMS)

        # Verify hass.data is cleaned up
        assert mock_config_entry.entry_id not in hass.data[DOMAIN]


@pytest.mark.asyncio
async def test_data_update_handler(hass: HomeAssistant, mock_config_entry):
    """Test the central data update handler logic."""
    # Setup options for exclusion
    mock_config_entry.options = {
        "exclude": "excluded_device_id",
        "exclude_agt": "excluded_hub_id",
    }

    with patch(
        "homeassistant.helpers.dispatcher.dispatcher_send"
    ) as mock_dispatcher_send:
        # 1. Test a valid update
        valid_data = {
            "msg": {
                "agt": "hub1",
                "me": "dev1",
                "devtype": "SL_SW_IF1",
                "idx": "L1",
                "type": 129,
            }
        }
        await data_update_handler(hass, mock_config_entry, valid_data)
        expected_signal = (
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_switch.sl_sw_if1_hub1_dev1_l1"
        )
        mock_dispatcher_send.assert_called_with(
            hass, expected_signal, valid_data["msg"]
        )

        mock_dispatcher_send.reset_mock()

        # 2. Test an update for an excluded device
        excluded_device_data = {
            "msg": {
                "agt": "hub1",
                "me": "excluded_device_id",
                "devtype": "SL_SW_IF1",
                "idx": "L1",
            }
        }
        await data_update_handler(hass, mock_config_entry, excluded_device_data)
        mock_dispatcher_send.assert_not_called()

        # 3. Test an update for an excluded hub
        excluded_hub_data = {
            "msg": {
                "agt": "excluded_hub_id",
                "me": "dev2",
                "devtype": "SL_SW_IF1",
                "idx": "L1",
            }
        }
        await data_update_handler(hass, mock_config_entry, excluded_hub_data)
        mock_dispatcher_send.assert_not_called()


def test_generate_entity_id():
    """Test the entity ID generation utility."""
    # Test a simple switch
    assert (
        generate_unique_id("SL_SW_IF1", "hub123", "dev456", "L1")
        == "switch.sl_sw_if1_hub123_dev456_l1"
    )
    # Test a light
    assert (
        generate_unique_id("SL_LI_RGBW", "hub123", "dev789", "RGBW")
        == "light.sl_li_rgbw_hub123_dev789_rgbw"
    )
    # Test a sensor from a composite device (lock battery)
    assert (
        generate_unique_id("SL_LK_LS", "hub123", "lock01", "BAT")
        == "sensor.sl_lk_ls_hub123_lock01_bat"
    )
    # Test a climate entity (no sub-device needed for platform)
    assert (
        generate_unique_id("SL_CP_AIR", "hub123", "climate01", "climate")
        == "climate.sl_cp_air_hub123_climate01_climate"
    )
    # Test unknown device
    assert generate_unique_id("UNKNOWN_DEV", "hub123", "dev000", "P1") == ""


@pytest.mark.asyncio
async def test_lifesmart_state_manager(hass: HomeAssistant, mock_config_entry):
    """Test the LifeSmartStateManager class."""
    mock_client = AsyncMock()
    mock_client.generate_wss_auth.return_value = "{'auth': 'ok'}"

    mock_ws = AsyncMock()
    mock_ws.receive.side_effect = [
        MagicMock(type="text", data='{"code":0, "message":"success"}'),
        # Keep the loop running then simulate a close
        asyncio.CancelledError,
    ]

    with patch(
        "homeassistant.helpers.aiohttp_client.async_get_clientsession"
    ) as mock_session:
        mock_session.return_value.ws_connect.return_value = mock_ws

        manager = LifeSmartStateManager(
            hass=hass,
            config_entry=mock_config_entry,
            client=mock_client,
            ws_url="wss://fake.url",
            refresh_callback=AsyncMock(),
        )

        # Start and let it run through one cycle
        manager.start()
        await asyncio.sleep(0.1)  # allow the task to start

        # Verify connection and auth were attempted
        mock_session.return_value.ws_connect.assert_called_with(
            "wss://fake.url",
            heartbeat=25,
            compress=15,
            ssl=unittest.mock.ANY,
            timeout=unittest.mock.ANY,
        )
        mock_client.generate_wss_auth.assert_called_once()
        mock_ws.send_str.assert_called_with("{'auth': 'ok'}")

        # Stop the manager
        await manager.stop()
        assert manager._should_stop is True
        assert manager._ws_task.cancelled()
