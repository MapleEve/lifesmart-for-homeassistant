"""
Unit and integration tests for the LifeSmart Climate platform.
This version strictly adheres to using constants from const.py, fixtures from conftest.py,
and correct Python execution order.
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


# --- HELPER FUNCTIONS (DEFINED BEFORE USE) ---


def get_first_devtype(const_list, fallback="FALLBACK_TYPE"):
    """Safely get the first device type from a constant tuple/list."""
    return const_list[0] if const_list else fallback


def create_mock_device(devtype, device_id, hub_id, data, name="Test Climate"):
    """Helper to create a base mock device dictionary."""
    return {
        DEVICE_TYPE_KEY: devtype,
        DEVICE_ID_KEY: device_id,
        HUB_ID_KEY: hub_id,
        DEVICE_NAME_KEY: name,
        DEVICE_DATA_KEY: data,
    }


# --- MOCK DEVICE DATA: STRICTLY USING CONSTANTS AND HELPERS ---
MOCK_DEVICES = {
    "SL_NATURE_CLIMATE": create_mock_device(
        "SL_NATURE",
        "nature_climate_1",
        "sl-hub-1",
        name="Nature Panel",
        data={
            "P5": {"val": 3},
            "P6": {"val": (4 << 6)},
        },  # Mode 4: AUTO, FAN, COOL, HEAT, HEAT_COOL
    ),
    "SL_NATURE_NON_CLIMATE": create_mock_device(
        "SL_NATURE", "nature_non_climate_1", "sl-hub-1", data={"P5": {"val": 2}}
    ),
    "SL_CP_DN_HEAT_AUTO": create_mock_device(
        "SL_CP_DN",
        "cp_dn_1",
        "sl-hub-1",
        name="Floor Heating",
        data={
            "P1": {"type": 1, "val": 2147483648},  # bit 31 is 1 -> AUTO
            "P3": {"v": 25.0},
            "P4": {"v": 22.5},
        },
    ),
    "SL_CP_AIR_COOL_MED": create_mock_device(
        "SL_CP_AIR",
        "cp_air_1",
        "sl-hub-1",
        name="Fan Coil Unit",
        data={
            "P1": {
                "type": 1,
                "val": (1 << 15) | (1 << 13),
            },  # Fan: 1 (Med), Mode: 1 (Cool)
            "P4": {"v": 24.0},
            "P5": {"v": 26.0},
        },
    ),
    "V_AIR_P_OFF": create_mock_device(
        "V_AIR_P",
        "v_air_p_1",
        "sl-hub-1",
        name="Air Panel",
        data={
            "O": {"type": 0},
            "MODE": {"val": 1},
            "F": {"val": 2},
            "T": {"v": 23.0},
            "tT": {"v": 25.0},
        },
    ),
    "SL_TR_ACIPM_FAN": create_mock_device(
        "SL_TR_ACIPM",
        "tr_acipm_1",
        "sl-hub-1",
        name="Air System",
        data={"P1": {"type": 1, "val": 1}},
    ),
}

pytestmark = pytest.mark.asyncio


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
    ):
        """Test that async_setup_entry correctly identifies and creates climate entities."""
        devices_to_load = [
            MOCK_DEVICES["SL_NATURE_CLIMATE"],
            MOCK_DEVICES["SL_NATURE_NON_CLIMATE"],  # Should be ignored
            MOCK_DEVICES["SL_CP_DN_HEAT_AUTO"],
            create_mock_device("SL_SW_IF1", "sw1", "sl-hub-1", {}),  # Should be ignored
        ]

        await setup_platform(hass, mock_config_entry, mock_client, devices_to_load)

        assert len(hass.states.async_entity_ids(CLIMATE_DOMAIN)) == 2
        assert hass.states.get("climate.nature_panel") is not None
        assert hass.states.get("climate.floor_heating") is not None
        assert (
            hass.states.get("climate.test_climate_sl_nature_nature_non_climate_1")
            is None
        )


class TestClimateEntity:
    """Tests for the LifeSmartClimate entity's attributes, state, and services."""

    @pytest.mark.parametrize(
        "device_key, expected_attrs, expected_features",
        [
            (
                "SL_CP_DN_HEAT_AUTO",
                {
                    "hvac_mode": HVACMode.AUTO,
                    "current_temperature": 22.5,
                    "target_temperature": 25.0,
                },
                ClimateEntityFeature.TARGET_TEMPERATURE,
            ),
            (
                "SL_CP_AIR_COOL_MED",
                {"hvac_mode": HVACMode.COOL, "fan_mode": FAN_MEDIUM},
                ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE,
            ),
            (
                "V_AIR_P_OFF",
                {"hvac_mode": HVACMode.OFF},
                ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE,
            ),
            (
                "SL_TR_ACIPM_FAN",
                {"hvac_mode": HVACMode.FAN_ONLY, "fan_mode": FAN_LOW},
                ClimateEntityFeature.FAN_MODE,
            ),
            (
                "SL_NATURE_CLIMATE",
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
        device_key: str,
        expected_attrs: dict,
        expected_features: ClimateEntityFeature,
    ):
        """Test initialization of entity attributes and features for various device types."""
        device = MOCK_DEVICES[device_key]
        await setup_platform(hass, mock_config_entry, mock_client, [device])

        entity_id = f"climate.{device[DEVICE_NAME_KEY].lower().replace(' ', '_')}"
        state = hass.states.get(entity_id)

        assert state is not None, f"Entity {entity_id} not found"
        assert state.attributes.get("supported_features") == expected_features
        for attr, val in expected_attrs.items():
            assert state.attributes.get(attr) == val

    async def test_service_calls(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        mock_config_entry: ConfigEntry,
    ):
        """Test service calls for setting temperature, hvac_mode, and fan_mode."""
        device = MOCK_DEVICES["SL_CP_AIR_COOL_MED"]
        await setup_platform(hass, mock_config_entry, mock_client, [device])
        entity_id = "climate.fan_coil_unit"

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: entity_id, ATTR_TEMPERATURE: 22.0},
            blocking=True,
        )
        mock_client.async_set_climate_temperature.assert_awaited_once_with(
            ANY, "cp_air_1", "SL_CP_AIR", 22.0
        )

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: entity_id, "hvac_mode": HVACMode.HEAT},
            blocking=True,
        )
        mock_client.async_set_climate_hvac_mode.assert_awaited_once_with(
            ANY, "cp_air_1", "SL_CP_AIR", HVACMode.HEAT, ANY
        )

        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_FAN_MODE,
            {ATTR_ENTITY_ID: entity_id, "fan_mode": FAN_HIGH},
            blocking=True,
        )
        mock_client.async_set_climate_fan_mode.assert_awaited_once_with(
            ANY, "cp_air_1", "SL_CP_AIR", FAN_HIGH, ANY
        )

    async def test_entity_update_from_dispatcher(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        mock_config_entry: ConfigEntry,
    ):
        """Test that entity state updates correctly when a dispatcher signal is received."""
        device = MOCK_DEVICES["V_AIR_P_OFF"]
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
