"""
Unit and integration tests for the LifeSmart Climate platform.
"""

from unittest.mock import AsyncMock

import pytest
from homeassistant.components.climate import (
    DOMAIN as CLIMATE_DOMAIN,
    SERVICE_SET_TEMPERATURE,
    ClimateEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, ATTR_TEMPERATURE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.lifesmart import generate_unique_id
from custom_components.lifesmart.const import *

pytestmark = pytest.mark.asyncio


def find_device(devices: list, me: str):
    """Helper to find a specific device from the mock list by its 'me' id."""
    return next((d for d in devices if d.get(DEVICE_ID_KEY) == me), None)


# --- TEST SUITE ---


class TestClimateSetup:
    """Tests for the setup logic of the climate platform."""

    async def test_setup_entry_creates_correct_entities(
        self,
        hass: HomeAssistant,
        setup_integration: ConfigEntry,
    ):
        """Test that async_setup_entry correctly identifies and creates climate entities."""
        assert len(hass.states.async_entity_ids(CLIMATE_DOMAIN)) == 5
        assert hass.states.get("climate.nature_panel_thermo") is not None
        assert hass.states.get("climate.floor_heating") is not None
        assert hass.states.get("climate.fan_coil_unit") is not None
        assert hass.states.get("climate.air_panel") is not None
        assert hass.states.get("climate.air_system") is not None


class TestClimateEntity:
    """Tests for the LifeSmartClimate entity's attributes, state, and services."""

    @pytest.mark.parametrize(
        "entity_id, entity_name, me, devtype, expected_state, expected_attrs, expected_features",
        [
            (
                "climate.nature_panel_thermo",
                "Nature Panel Thermo",
                "climate_nature_thermo",
                "SL_NATURE",
                HVACMode.AUTO,
                {
                    "current_temperature": 28.0,
                    "temperature": 26.0,
                    "fan_mode": "low",
                },
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.FAN_MODE
                | ClimateEntityFeature.TURN_ON
                | ClimateEntityFeature.TURN_OFF,
            ),
            (
                "climate.floor_heating",
                "Floor Heating",
                "climate_floor_heat",
                "SL_CP_DN",
                HVACMode.AUTO,
                {"current_temperature": 22.5, "temperature": 25.0},
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.TURN_ON
                | ClimateEntityFeature.TURN_OFF,
            ),
            (
                "climate.fan_coil_unit",
                "Fan Coil Unit",
                "climate_fancoil",
                "SL_CP_AIR",
                HVACMode.HEAT,
                {"fan_mode": FAN_LOW, "temperature": 24.0, "current_temperature": 26.0},
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.FAN_MODE
                | ClimateEntityFeature.TURN_ON
                | ClimateEntityFeature.TURN_OFF,
            ),
            (
                "climate.air_panel",
                "Air Panel",
                "climate_airpanel",
                "V_AIR_P",
                HVACMode.OFF,
                {"current_temperature": 23.0, "temperature": 25.0},
                ClimateEntityFeature.TARGET_TEMPERATURE
                | ClimateEntityFeature.FAN_MODE
                | ClimateEntityFeature.TURN_ON
                | ClimateEntityFeature.TURN_OFF,
            ),
            (
                "climate.air_system",
                "Air System",
                "climate_airsystem",
                "SL_TR_ACIPM",
                HVACMode.FAN_ONLY,
                {"fan_mode": FAN_LOW},
                ClimateEntityFeature.FAN_MODE
                | ClimateEntityFeature.TURN_ON
                | ClimateEntityFeature.TURN_OFF,
            ),
        ],
        ids=["NatureThermo", "FloorHeating", "FanCoil", "AirPanel", "AirSystem"],
    )
    async def test_entity_state_and_attributes(
        self,
        hass: HomeAssistant,
        setup_integration: ConfigEntry,
        entity_id: str,
        entity_name: str,
        me: str,
        devtype: str,
        expected_state: HVACMode,
        expected_attrs: dict,
        expected_features: ClimateEntityFeature,
    ):
        """Test initialization of entity attributes and features for various device types."""
        state = hass.states.get(entity_id)

        assert state is not None, f"Entity {entity_id} not found"
        assert state.name == entity_name
        assert state.state == expected_state
        assert state.attributes.get("supported_features") == expected_features
        for attr, val in expected_attrs.items():
            assert (
                state.attributes.get(attr) == val
            ), f"Attribute '{attr}' mismatch for {entity_id}"

    async def test_service_calls(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        setup_integration: ConfigEntry,
    ):
        """Test service calls for setting temperature, hvac_mode, and fan_mode."""
        entity_id = "climate.nature_panel_thermo"

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: entity_id, ATTR_TEMPERATURE: 22.0},
            blocking=True,
        )
        mock_client.async_set_climate_temperature.assert_awaited_once_with(
            "hub_climate", "climate_nature_thermo", "SL_NATURE", 22.0
        )

    async def test_entity_update_from_dispatcher(
        self,
        hass: HomeAssistant,
        setup_integration: ConfigEntry,
        mock_lifesmart_devices: list,
    ):
        """Test that entity state updates correctly when a dispatcher signal is received."""
        entity_id = "climate.air_panel"
        device = find_device(mock_lifesmart_devices, "climate_airpanel")
        assert device is not None

        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == HVACMode.OFF

        unique_id = generate_unique_id(
            device[DEVICE_TYPE_KEY], device[HUB_ID_KEY], device[DEVICE_ID_KEY], None
        )

        new_data = {"O": {"type": 1}, "MODE": {"val": 2}, "T": {"v": 21.0}}

        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", new_data
        )
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        assert state.state == HVACMode.FAN_ONLY
        assert state.attributes.get("current_temperature") == 21.0
