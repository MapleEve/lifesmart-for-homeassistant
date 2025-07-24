"""Unit tests for the LifeSmart light platform, using shared fixtures."""

from unittest.mock import AsyncMock, call

import pytest
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_COLOR_TEMP_KELVIN,
    DOMAIN as LIGHT_DOMAIN,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.lifesmart.const import *
from custom_components.lifesmart.light import (
    _is_light_subdevice,
    _parse_color_value,
)

pytestmark = pytest.mark.asyncio

# --- Helper Functions ---


def test_parse_color_value():
    """Test the _parse_color_value helper function."""
    assert _parse_color_value(0x00AABBCC, has_white=False) == (0xAA, 0xBB, 0xCC)
    assert _parse_color_value(0xDDEEFF00, has_white=True) == (0xEE, 0xFF, 0x00, 0xDD)


@pytest.mark.parametrize(
    ("device_type", "sub_key", "expected"),
    [
        ("ANY", "P1", True),
        ("SL_SW_IF3", "L1", True),
        ("ANY", "OTHER", False),
        ("ANY", "P5", False),  # Test exclusion
    ],
)
def test_is_light_subdevice(device_type: str, sub_key: str, expected: bool) -> None:
    """Test the _is_light_subdevice helper function."""
    assert _is_light_subdevice(device_type, sub_key) is expected


# --- Test `async_setup_entry` ---


async def test_async_setup_entry_creates_entities(
    hass: HomeAssistant,
    setup_integration: ConfigEntry,
) -> None:
    """Test successful setup of all light entity types from shared fixtures."""
    # Expected lights from conftest.py:
    # Brightness(1) + Dimmer(1) + Quantum(1) + SingleIORGB(1) + DualIORGBW(1)
    # + SPOTRGB(1) + SPOTRGBW(1) + CoverLight(1) + GenericHS(1) = 9
    assert len(hass.states.async_entity_ids(LIGHT_DOMAIN)) == 9
    assert hass.states.get("light.brightness_light") is not None
    assert hass.states.get("light.dimmer_light") is not None
    assert hass.states.get("light.quantum_light") is not None
    assert hass.states.get("light.single_io_rgb_light") is not None
    assert hass.states.get("light.dual_io_rgbw_light") is not None
    assert hass.states.get("light.spot_rgb_light") is not None
    assert hass.states.get("light.spot_rgbw_light") is not None
    assert hass.states.get("light.cover_light_p1") is not None
    assert hass.states.get("light.generic_hs_light_hs") is not None


# --- Test Service Calls for Each Light Type ---


class TestLifeSmartBrightnessLight:
    async def test_services(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        setup_integration: ConfigEntry,
    ):
        entity_id = "light.brightness_light"
        await hass.services.async_call(
            LIGHT_DOMAIN,
            "turn_on",
            {ATTR_ENTITY_ID: entity_id, ATTR_BRIGHTNESS: 150},
            blocking=True,
        )
        mock_client.set_single_ep_async.assert_called_with(
            "hub_light", "light_bright", "P1", CMD_TYPE_SET_VAL, 150
        )


class TestLifeSmartDimmerLight:
    async def test_services(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        setup_integration: ConfigEntry,
    ):
        entity_id = "light.dimmer_light"
        # A kelvin value of 3726 produces a `val` of 73 in a standard 2700-6500K range.
        await hass.services.async_call(
            LIGHT_DOMAIN,
            "turn_on",
            {
                ATTR_ENTITY_ID: entity_id,
                ATTR_BRIGHTNESS: 200,
                ATTR_COLOR_TEMP_KELVIN: 3726,
            },
            blocking=True,
        )
        mock_client.set_single_ep_async.assert_has_calls(
            [
                call("hub_light", "light_dimmer", "P1", CMD_TYPE_SET_VAL, 200),
                call("hub_light", "light_dimmer", "P2", CMD_TYPE_SET_VAL, 73),
            ],
            any_order=True,
        )
        # Also ensure the final turn_on call is made
        mock_client.turn_on_light_switch_async.assert_called_with(
            "P1", "hub_light", "light_dimmer"
        )


class TestLifeSmartQuantumLight:
    async def test_services(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        setup_integration: ConfigEntry,
    ):
        entity_id = "light.quantum_light"
        await hass.services.async_call(
            LIGHT_DOMAIN,
            "turn_on",
            {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "魔力红"},
            blocking=True,
        )
        mock_client.set_multi_eps_async.assert_called_with(
            "hub_light",
            "light_quantum",
            [
                {"idx": "P1", "type": CMD_TYPE_ON, "val": 1},
                {
                    "idx": "P2",
                    "type": CMD_TYPE_SET_RAW,
                    "val": ALL_EFFECT_MAP["魔力红"],
                },
            ],
        )


class TestLifeSmartSingleIORGBWLight:
    async def test_services(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        setup_integration: ConfigEntry,
    ):
        entity_id = "light.single_io_rgb_light"
        # white w=255 -> 100%. val = (100<<24) | (1<<16) | (2<<8) | 3
        await hass.services.async_call(
            LIGHT_DOMAIN,
            "turn_on",
            {ATTR_ENTITY_ID: entity_id, ATTR_RGBW_COLOR: (1, 2, 3, 255)},
            blocking=True,
        )
        mock_client.set_single_ep_async.assert_called_with(
            "hub_light", "light_singlergb", "RGB", CMD_TYPE_SET_RAW, 0x64010203
        )


class TestLifeSmartDualIORGBWLight:
    async def test_services(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        setup_integration: ConfigEntry,
    ):
        entity_id = "light.dual_io_rgbw_light"
        await hass.services.async_call(
            LIGHT_DOMAIN,
            "turn_on",
            {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "魔力红"},
            blocking=True,
        )
        mock_client.set_multi_eps_async.assert_called_with(
            "hub_light",
            "light_dualrgbw",
            [
                {"idx": "RGBW", "type": CMD_TYPE_ON, "val": 1},
                {
                    "idx": "DYN",
                    "type": CMD_TYPE_SET_RAW,
                    "val": DYN_EFFECT_MAP["魔力红"],
                },
            ],
        )


class TestLifeSmartSPOTRGBLight:
    async def test_services(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        setup_integration: ConfigEntry,
    ):
        entity_id = "light.spot_rgb_light"
        await hass.services.async_call(
            LIGHT_DOMAIN,
            "turn_on",
            {ATTR_ENTITY_ID: entity_id, ATTR_RGB_COLOR: (255, 128, 64)},
            blocking=True,
        )
        mock_client.set_single_ep_async.assert_called_with(
            "hub_light", "light_spotrgb", "RGB", CMD_TYPE_SET_RAW, 0xFF8040
        )


class TestLifeSmartSPOTRGBWLight:
    async def test_services(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        setup_integration: ConfigEntry,
    ):
        entity_id = "light.spot_rgbw_light"
        await hass.services.async_call(
            LIGHT_DOMAIN,
            "turn_on",
            {ATTR_ENTITY_ID: entity_id, ATTR_RGBW_COLOR: (0x22, 0x33, 0x44, 0x11)},
            blocking=True,
        )
        mock_client.set_multi_eps_async.assert_called_with(
            "hub_light",
            "light_spotrgbw",
            [
                {"idx": "RGBW", "type": CMD_TYPE_SET_RAW, "val": 0x11223344},
                {"idx": "DYN", "type": CMD_TYPE_OFF, "val": 0},
            ],
        )


class TestLifeSmartCoverLight:
    async def test_services_and_update(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        setup_integration: ConfigEntry,
    ):
        entity_id = "light.cover_light_p1"

        # Test turn on
        await hass.services.async_call(
            LIGHT_DOMAIN, "turn_on", {ATTR_ENTITY_ID: entity_id}, blocking=True
        )
        mock_client.turn_on_light_switch_async.assert_called_with(
            "P1", "hub_light", "light_cover"
        )
        assert hass.states.get(entity_id).state == "on"

        # Test dispatcher update to turn off
        from homeassistant.helpers.entity_registry import (
            async_get as async_get_entity_registry,
        )

        entity_registry = async_get_entity_registry(hass)
        entry = entity_registry.async_get(entity_id)
        assert entry is not None

        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entry.unique_id}", {"type": 128}
        )
        await hass.async_block_till_done()
        assert hass.states.get(entity_id).state == "off"


class TestLifeSmartLight:
    async def test_hs_service(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        setup_integration: ConfigEntry,
    ):
        entity_id = "light.generic_hs_light_hs"

        # HS (240, 100) -> Blue -> RGB(0,0,255) -> AI val = 255
        await hass.services.async_call(
            LIGHT_DOMAIN,
            "turn_on",
            {ATTR_ENTITY_ID: entity_id, "hs_color": (240, 100)},
            blocking=True,
        )
        mock_client.set_single_ep_async.assert_called_with(
            "hub_light", "light_generic_hs", "HS", CMD_TYPE_SET_RAW, 255
        )
