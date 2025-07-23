"""Unit tests for the LifeSmart light platform, using shared fixtures."""

from typing import Any
from unittest.mock import AsyncMock, call

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

# Import all constants and classes from the component
from custom_components.lifesmart.const import *
from custom_components.lifesmart.light import (
    LifeSmartBrightnessLight,
    LifeSmartCoverLight,
    LifeSmartDimmerLight,
    LifeSmartDualIORGBWLight,
    LifeSmartLight,
    LifeSmartQuantumLight,
    LifeSmartSingleIORGBWLight,
    LifeSmartSPOTRGBLight,
    LifeSmartSPOTRGBWLight,
    _is_light_subdevice,
    _parse_color_value,
    async_setup_entry,
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
        ("ANY", "RGB", True),
        ("ANY", "P1", True),
        ("SL_SW_IF3", "dark1", True),
        ("ANY", "OTHER", False),
    ],
)
def test_is_light_subdevice(device_type: str, sub_key: str, expected: bool) -> None:
    """Test the _is_light_subdevice helper function."""
    assert _is_light_subdevice(device_type, sub_key) is expected


# --- Test `async_setup_entry` ---


async def test_async_setup_entry_coverage(
    hass: HomeAssistant,
    mock_client: AsyncMock,
    mock_config_entry: ConfigEntry,
    mock_lifesmart_devices: list[dict[str, Any]],
) -> None:
    """Test successful setup of all light entity types from shared fixtures."""
    hass.data[DOMAIN][mock_config_entry.entry_id] = {
        "client": mock_client,
        "devices": mock_lifesmart_devices,
        "exclude_devices": [],
        "exclude_hubs": [],
    }
    async_add_entities = AsyncMock()

    await async_setup_entry(hass, mock_config_entry, async_add_entities)

    # Expected lights from conftest.py:
    # Brightness(1) + Dimmer(1) + Quantum(1) + SingleIORGB(1) + DualIORGBW(1)
    # + SPOTRGB(1) + SPOTRGBW(1) + CoverLight(1) + GenericHS(1) = 9
    assert async_add_entities.call_count == 1
    assert (
        len(async_add_entities.call_args[0][0]) == 9
    ), "Incorrect number of light entities created"


# --- Test All Individual Light Entity Classes ---


def find_device(devices, dev_id):
    """Helper to find a specific device from the mock list."""
    return next((d for d in devices if d[DEVICE_ID_KEY] == dev_id), None)


class TestLifeSmartBrightnessLight:
    async def test_services(
        self, hass, mock_client, mock_config_entry, mock_lifesmart_devices
    ):
        device_data = find_device(mock_lifesmart_devices, "light_bright")
        entity = LifeSmartBrightnessLight(
            AsyncMock(), device_data, "P1", {}, mock_client, mock_config_entry.entry_id
        )

        await entity.async_turn_on(brightness=150)
        mock_client.set_single_ep_async.assert_called_with(
            "hub_light", "light_bright", "P1", CMD_TYPE_SET_VAL, 150
        )


class TestLifeSmartDimmerLight:
    async def test_services(
        self, hass, mock_client, mock_config_entry, mock_lifesmart_devices
    ):
        device_data = find_device(mock_lifesmart_devices, "light_dimmer")
        entity = LifeSmartDimmerLight(
            AsyncMock(), device_data, mock_client, mock_config_entry.entry_id
        )

        # Correcting the test to use a logical Kelvin value that produces the expected API value.
        # A kelvin value of 3726 produces a `val` of 73 in a standard 2700-6500K range.
        await entity.async_turn_on(brightness=200, color_temp_kelvin=3726)
        mock_client.set_single_ep_async.assert_has_calls(
            [
                call("hub_light", "light_dimmer", "P1", CMD_TYPE_SET_VAL, 200),
                call("hub_light", "light_dimmer", "P2", CMD_TYPE_SET_VAL, 73),
            ],
            any_order=True,
        )


class TestLifeSmartQuantumLight:
    async def test_services(
        self, hass, mock_client, mock_config_entry, mock_lifesmart_devices
    ):
        device_data = find_device(mock_lifesmart_devices, "light_quantum")
        entity = LifeSmartQuantumLight(
            AsyncMock(), device_data, mock_client, mock_config_entry.entry_id
        )

        await entity.async_turn_on(effect="魔力红")
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
        self, hass, mock_client, mock_config_entry, mock_lifesmart_devices
    ):
        device_data = find_device(mock_lifesmart_devices, "light_singlergb")
        entity = LifeSmartSingleIORGBWLight(
            AsyncMock(), device_data, mock_client, mock_config_entry.entry_id, "RGB"
        )

        # white w=255 -> 100%. val = (100<<24) | (1<<16) | (2<<8) | 3
        await entity.async_turn_on(rgbw_color=(1, 2, 3, 255))
        mock_client.set_single_ep_async.assert_called_with(
            "hub_light", "light_singlergb", "RGB", CMD_TYPE_SET_RAW, 0x64010203
        )


class TestLifeSmartDualIORGBWLight:
    async def test_services(
        self, hass, mock_client, mock_config_entry, mock_lifesmart_devices
    ):
        device_data = find_device(mock_lifesmart_devices, "light_dualrgbw")
        entity = LifeSmartDualIORGBWLight(
            AsyncMock(),
            device_data,
            mock_client,
            mock_config_entry.entry_id,
            "RGBW",
            "DYN",
        )

        await entity.async_turn_on(effect="魔力红")
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
        self, hass, mock_client, mock_config_entry, mock_lifesmart_devices
    ):
        device_data = find_device(mock_lifesmart_devices, "light_spotrgb")
        entity = LifeSmartSPOTRGBLight(
            AsyncMock(), device_data, mock_client, mock_config_entry.entry_id
        )

        await entity.async_turn_on(rgb_color=(255, 128, 64))
        mock_client.set_single_ep_async.assert_called_with(
            "hub_light", "light_spotrgb", "RGB", CMD_TYPE_SET_RAW, 0xFF8040
        )


class TestLifeSmartSPOTRGBWLight:
    async def test_services(
        self, hass, mock_client, mock_config_entry, mock_lifesmart_devices
    ):
        device_data = find_device(mock_lifesmart_devices, "light_spotrgbw")
        entity = LifeSmartSPOTRGBWLight(
            AsyncMock(), device_data, mock_client, mock_config_entry.entry_id
        )

        await entity.async_turn_on(rgbw_color=(0x22, 0x33, 0x44, 0x11))
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
        self, hass, mock_client, mock_config_entry, mock_lifesmart_devices
    ):
        device_data = find_device(mock_lifesmart_devices, "light_cover")
        entity = LifeSmartCoverLight(
            AsyncMock(),
            device_data,
            "P1",
            device_data[DEVICE_DATA_KEY]["P1"],
            mock_client,
            mock_config_entry.entry_id,
        )
        entity.hass = hass
        entity.async_write_ha_state = AsyncMock()

        await entity.async_turn_on()
        mock_client.turn_on_light_switch_async.assert_called_with(
            "P1", "hub_light", "light_cover"
        )
        assert entity.is_on is True

        # Test dispatcher update
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity.unique_id}", {"type": 128}
        )
        await hass.async_block_till_done()
        assert entity.is_on is False


class TestLifeSmartLight:
    async def test_hs_service(
        self, hass, mock_client, mock_config_entry, mock_lifesmart_devices
    ):
        device_data = find_device(mock_lifesmart_devices, "light_generic_hs")
        sub_data = device_data[DEVICE_DATA_KEY]["HS"]
        entity = LifeSmartLight(
            AsyncMock(),
            device_data,
            "HS",
            sub_data,
            mock_client,
            mock_config_entry.entry_id,
        )

        # HS (240, 100) -> Blue -> RGB(0,0,255) -> AI val = 255
        await entity.async_turn_on(hs_color=(240, 100))
        mock_client.set_single_ep_async.assert_called_with(
            "hub_light", "light_generic_hs", "HS", CMD_TYPE_SET_RAW, 255
        )
