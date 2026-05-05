"""Regression tests for recent main/current LifeSmart user feedback batch."""

from unittest.mock import AsyncMock, MagicMock, call

import pytest
from homeassistant.components.climate import HVACMode
from homeassistant.components.cover import CoverEntityFeature
from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_COLOR_TEMP_KELVIN

from custom_components.lifesmart.const import CMD_TYPE_SET_VAL
from custom_components.lifesmart.cover import LifeSmartPositionalCover
from custom_components.lifesmart.climate import LifeSmartClimate
from custom_components.lifesmart.helpers import (
    get_binary_sensor_subdevices,
    get_cover_subdevices,
    get_light_subdevices,
    is_binary_sensor,
    is_climate,
    is_cover,
)
from custom_components.lifesmart.light import LifeSmartSingleIORGBWLight, LifeSmartSPOTRGBLight


def _noop_write_state(entity):
    entity.async_write_ha_state = MagicMock()
    return entity


def test_issue_93_alias_device_mapping_for_bg_v1_and_generic_controller_v1():
    """SL_SC_BG_V1 and SL_P_V1 runtime aliases should create expected entities."""
    bg_v1 = {
        "agt": "hub1",
        "me": "door1",
        "devtype": "SL_SC_BG_V1",
        "name": "Door V1",
        "data": {"G": {"val": 0}, "AXS": {"val": 0}, "V": {"v": 95}},
    }
    generic_v1_free = {
        "agt": "hub1",
        "me": "ctl_free",
        "devtype": "SL_P_V1",
        "name": "Generic V1 Free",
        "data": {"P1": {"val": 0}, "P5": {"type": 129}, "P6": {"type": 128}},
    }
    generic_v1_cover = {
        "agt": "hub1",
        "me": "ctl_cover",
        "devtype": "SL_P_V1",
        "name": "Generic V1 Cover",
        "data": {"P1": {"val": 2 << 24}, "P2": {"type": 128}, "P3": {"type": 128}},
    }

    assert is_binary_sensor(bg_v1) is True
    assert set(get_binary_sensor_subdevices(bg_v1)) == {"G", "AXS"}
    assert is_binary_sensor(generic_v1_free) is True
    assert get_binary_sensor_subdevices(generic_v1_free) == ["P5", "P6"]
    assert is_cover(generic_v1_cover) is True
    assert get_cover_subdevices(generic_v1_cover) == ["P2"]


def test_issue_98_single_io_rgbw_light_is_created_without_dyn_endpoint():
    """SL_LI_RGBW/SL_CT_RGBW devices that only expose RGBW should not be dropped."""
    device = {
        "agt": "hub_light",
        "me": "rgbw_without_dyn",
        "devtype": "SL_LI_RGBW",
        "name": "RGBW Bulb",
        "data": {"RGBW": {"type": 129, "val": 0x10203040}},
    }

    assert get_light_subdevices(device) == ["RGBW"]


@pytest.mark.asyncio
async def test_issue_98_single_io_rgbw_turn_off_uses_rgbw_endpoint():
    """Single-IO RGBW entities should send off to RGBW, not a nonexistent P1."""
    client = MagicMock()
    client.async_send_single_command = AsyncMock(return_value=0)
    entity = _noop_write_state(
        LifeSmartSingleIORGBWLight(
            {
                "agt": "hub_light",
                "me": "rgbw_without_dyn",
                "devtype": "SL_LI_RGBW",
                "name": "RGBW Bulb",
                "data": {"RGBW": {"type": 129, "val": 0x10203040}},
            },
            client,
            "entry1",
            "RGBW",
        )
    )

    await entity.async_turn_off()

    client.async_send_single_command.assert_awaited_once_with(
        "hub_light", "rgbw_without_dyn", "RGBW", 0x80, 0
    )


@pytest.mark.asyncio
async def test_issue_98_spot_brightness_and_color_temp_use_p1_p2_endpoints():
    """SL_SPOT exposes RGB plus P1 brightness and P2 color temperature controls."""
    client = MagicMock()
    client.async_send_single_command = AsyncMock(return_value=0)
    entity = _noop_write_state(
        LifeSmartSPOTRGBLight(
            {
                "agt": "hub_light",
                "me": "spot1",
                "devtype": "SL_SPOT",
                "name": "Spot",
                "data": {
                    "RGB": {"type": 129, "val": 0x00112233},
                    "P1": {"type": 129, "val": 100},
                    "P2": {"val": 128},
                },
            },
            client,
            "entry1",
        )
    )

    await entity.async_turn_on(
        **{ATTR_BRIGHTNESS: 180, ATTR_COLOR_TEMP_KELVIN: 4000}
    )

    awaited_calls = client.async_send_single_command.await_args_list
    assert call("hub_light", "spot1", "P1", CMD_TYPE_SET_VAL, 180) in awaited_calls
    assert any(c.args[:4] == ("hub_light", "spot1", "P2", CMD_TYPE_SET_VAL) for c in awaited_calls)


def test_issue_94_dooya_direction_bit_and_partial_update_merge():
    """DOOYA position update should preserve device data and treat 0x80 as opening."""
    client = MagicMock()
    entity = _noop_write_state(
        LifeSmartPositionalCover(
            {
                "agt": "hub_cover",
                "me": "cover_dooya",
                "devtype": "SL_DOOYA",
                "name": "Curtain",
                "data": {"P1": {"type": 128, "val": 100}},
            },
            client,
            "entry1",
            "P1",
        )
    )

    entity._handle_update({"type": 129, "val": 0x80 | 55})

    assert entity.current_cover_position == 55
    assert entity.is_opening is True
    assert entity.is_closing is False
    assert entity.supported_features & CoverEntityFeature.SET_POSITION


def test_issue_91_90_nature_p5_6_raw_temperature_and_floor_heat_mode():
    """SL_NATURE P5 low-byte 6 is thermostat; raw temp vals should parse as val/10."""
    device = {
        "agt": "hub_climate",
        "me": "nature6",
        "devtype": "SL_NATURE",
        "name": "Nature 6",
        "data": {
            "P1": {"type": 129},
            "P4": {"val": 231},
            "P5": {"val": 6},
            "P6": {"val": 2 << 6},
            "P7": {"val": 7},
            "P8": {"val": 245},
            "P9": {"val": 45},
        },
    }

    assert is_climate(device) is True
    entity = _noop_write_state(LifeSmartClimate(device, MagicMock(), "entry1"))

    assert HVACMode.HEAT in entity.hvac_modes
    assert entity.hvac_mode == HVACMode.HEAT
    assert entity.current_temperature == 23.1
    assert entity.target_temperature == 24.5


def test_issue_87_99_climate_partial_update_does_not_null_existing_state():
    """Partial websocket updates should merge instead of replacing full climate state."""
    device = {
        "agt": "hub_climate",
        "me": "nature3",
        "devtype": "SL_NATURE",
        "name": "Nature 3",
        "data": {
            "P1": {"type": 129},
            "P4": {"v": 22.0},
            "P5": {"val": 3},
            "P6": {"val": 1 << 6},
            "P7": {"val": 3},
            "P8": {"v": 24.0},
            "P10": {"val": 75},
        },
    }
    entity = _noop_write_state(LifeSmartClimate(device, MagicMock(), "entry1"))

    entity._handle_update({"P4": {"val": 235, "v": 23.5}})

    assert entity.current_temperature == 23.5
    assert entity.target_temperature == 24.0
    assert entity.hvac_mode == HVACMode.COOL
