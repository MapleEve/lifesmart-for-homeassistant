"""
Unit and integration tests for the LifeSmart Climate platform.
This version uses shared fixtures from conftest.py and correct mocking strategies.
"""

from unittest.mock import AsyncMock, ANY

import pytest
from homeassistant.components.climate import (
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_FAN_MODE,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_TEMPERATURE,
    ClimateEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

# --- Strictly import constants from the component's code ---
from custom_components.lifesmart.const import *

pytestmark = pytest.mark.asyncio

# --- Helper Functions ---


def find_device(devices: list, me: str):
    """Helper to find a specific device from the mock list by its 'me' id."""
    return next((d for d in devices if d.get(DEVICE_ID_KEY) == me), None)


async def setup_platform(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    mock_client: AsyncMock,
    devices: list,
) -> None:
    """Set up the climate platform using provided fixtures and devices."""
    hass.data[DOMAIN] = {
        config_entry.entry_id: {
            "client": mock_client,
            "devices": devices,
            "exclude_devices": [],
            "exclude_hubs": [],
        }
    }
    await hass.config_entries.async_forward_entry_setup(config_entry, CLIMATE_DOMAIN)
    await hass.async_block_till_done()


# --- TEST SUITE ---


class TestClimateSetup:
    """Tests for the setup logic of the climate platform."""

    async def test_setup_entry_creates_correct_entities(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        mock_config_entry: ConfigEntry,
        mock_lifesmart_devices: list,
    ):
        """Test that async_setup_entry correctly identifies and creates climate entities."""
        await setup_platform(
            hass, mock_config_entry, mock_client, mock_lifesmart_devices
        )

        # Expected climate devices from conftest.py = 5
        assert len(hass.states.async_entity_ids(CLIMATE_DOMAIN)) == 5
        assert hass.states.get("climate.nature_panel_climate") is not None
        assert hass.states.get("climate.floor_heating") is not None
        assert hass.states.get("climate.fan_coil_unit") is not None
        assert hass.states.get("climate.air_panel") is not None
        assert hass.states.get("climate.air_system") is not None


class TestClimateEntity:
    """Tests for the LifeSmartClimate entity's attributes, state, and services."""

    @pytest.mark.parametrize(
        "device_me, expected_attrs, expected_features",
        [
            (
                "climate_floor_heat",
                {
                    "hvac_mode": HVACMode.AUTO,
                    "current_temperature": 22.5,
                    "target_temperature": 25.0,
                },
                ClimateEntityFeature.TARGET_TEMPERATURE,
            ),
            (
                "climate_fancoil",
                {"hvac_mode": HVACMode.COOL, "fan_mode": FAN_MEDIUM},
                ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE,
            ),
            (
                "climate_airpanel",
                {"hvac_mode": HVACMode.OFF},
                ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE,
            ),
            (
                "climate_airsystem",
                {"hvac_mode": HVACMode.FAN_ONLY, "fan_mode": FAN_LOW},
                ClimateEntityFeature.FAN_MODE,
            ),
            (
                "climate_nature",
                {
                    "hvac_modes": [
                        HVACMode.OFF,
                        HVACMode.AUTO,
                        HVACMode.FAN_ONLY,
                        HVACMode.COOL,
                        HVACMode.HEAT,
                        HVACMode.HEAT_COOL,
                    ]
                },
                ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE,
            ),
        ],
        ids=["FloorHeating", "FanCoil", "AirPanel", "AirSystem", "NaturePanel"],
    )
    async def test_entity_state_and_attributes(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        mock_config_entry: ConfigEntry,
        mock_lifesmart_devices: list,
        device_me: str,
        expected_attrs: dict,
        expected_features: ClimateEntityFeature,
    ):
        """Test initialization of entity attributes and features for various device types."""
        device = find_device(mock_lifesmart_devices, device_me)
        await setup_platform(hass, mock_config_entry, mock_client, [device])

        entity_id = f"climate.{device[DEVICE_NAME_KEY].lower().replace(' ', '_')}"
        state = hass.states.get(entity_id)

        assert state is not None, f"Entity {entity_id} not found"
        assert state.attributes.get("supported_features") == expected_features
        for attr, val in expected_attrs.items():
            assert (
                state.attributes.get(attr) == val
            ), f"Attribute '{attr}' mismatch for {entity_id}"

    async def test_service_calls(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        mock_config_entry: ConfigEntry,
        mock_lifesmart_devices: list,
    ):
        """Test service calls for setting temperature, hvac_mode, and fan_mode."""
        device = find_device(mock_lifesmart_devices, "climate_fancoil")
        await setup_platform(hass, mock_config_entry, mock_client, [device])
        entity_id = "climate.fan_coil_unit"

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: entity_id, ATTR_TEMPERATURE: 22.0},
            blocking=True,
        )
        mock_client.async_set_climate_temperature.assert_awaited_once_with(
            "hub_climate", "climate_fancoil", "SL_CP_AIR", 22.0
        )

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: entity_id, "hvac_mode": HVACMode.HEAT},
            blocking=True,
        )
        mock_client.async_set_climate_hvac_mode.assert_awaited_once_with(
            "hub_climate", "climate_fancoil", "SL_CP_AIR", HVACMode.HEAT, ANY
        )

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_FAN_MODE,
            {ATTR_ENTITY_ID: entity_id, "fan_mode": FAN_HIGH},
            blocking=True,
        )
        mock_client.async_set_climate_fan_mode.assert_awaited_once_with(
            "hub_climate", "climate_fancoil", "SL_CP_AIR", FAN_HIGH, ANY
        )

    async def test_entity_update_from_dispatcher(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        mock_config_entry: ConfigEntry,
        mock_lifesmart_devices: list,
    ):
        """Test that entity state updates correctly when a dispatcher signal is received."""
        device = find_device(mock_lifesmart_devices, "climate_airpanel")
        await setup_platform(hass, mock_config_entry, mock_client, [device])
        entity_id = "climate.air_panel"

        assert hass.states.get(entity_id).state == HVACMode.OFF

        new_data = {"O": {"type": 1}, "MODE": {"val": 2}, "T": {"v": 21.0}}
        entity_registry = async_get_entity_registry(hass)
        entry = entity_registry.async_get(entity_id)
        assert entry is not None

        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entry.unique_id}", new_data
        )
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        assert state.state == HVACMode.HEAT
        assert state.attributes.get("current_temperature") == 21.0
