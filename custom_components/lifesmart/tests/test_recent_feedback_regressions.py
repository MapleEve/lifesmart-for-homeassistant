"""Regression tests for recent main/current LifeSmart user feedback batch."""

from unittest.mock import AsyncMock, MagicMock, call

import pytest
from homeassistant.components.climate import HVACMode
from homeassistant.components.cover import CoverEntityFeature
from homeassistant.components.light import ATTR_BRIGHTNESS

from custom_components.lifesmart.compatibility import ATTR_COLOR_TEMP_KELVIN
from custom_components.lifesmart.const import (
    CMD_TYPE_SET_VAL,
    LIFESMART_TF_FAN_MAP,
    REVERSE_LIFESMART_HVAC_MODE_MAP,
)
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

    await entity.async_turn_on(**{ATTR_BRIGHTNESS: 180, ATTR_COLOR_TEMP_KELVIN: 4000})

    awaited_calls = client.async_send_single_command.await_args_list
    assert call("hub_light", "spot1", "P1", CMD_TYPE_SET_VAL, 180) in awaited_calls
    assert any(
        c.args[:4] == ("hub_light", "spot1", "P2", CMD_TYPE_SET_VAL)
        for c in awaited_calls
    )


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


def _nature_climate(client=None):
    """An SL_NATURE panel: cooling, target 24.0, current 22.0, fan HIGH."""
    device = {
        "agt": "hub_climate",
        "me": "nature_opt",
        "devtype": "SL_NATURE",
        "name": "Nature Optimistic",
        "data": {
            "P1": {"type": 129},  # odd type == on
            "P4": {"v": 22.0},  # current temperature
            "P7": {"val": 3},  # mode == COOL
            "P8": {"v": 24.0},  # target temperature
            "P9": {"val": 75},  # fan == HIGH
            "P10": {"val": 75},  # fan (read takes precedence over P9)
        },
    }
    return _noop_write_state(
        LifeSmartClimate(
            device, client if client is not None else MagicMock(), "entry1"
        )
    )


def test_optimistic_temperature_survives_unrelated_io_push():
    """A set target temp must persist when an unrelated IO (current temp) pushes.

    Regression: write handlers updated _attr_* but not the cached IO, so the next
    _update_state (re-derived from the full cache) read the stale P8 and reverted
    the value the user had just set.
    """
    entity = _nature_climate()
    assert entity.target_temperature == 24.0

    entity._optimistic_update("temperature", 20.0, 0)
    assert entity.target_temperature == 20.0
    # The cache (not just _attr_*) must carry the new value.
    assert entity._raw_device["data"]["P8"]["v"] == 20.0

    # An unrelated current-temperature push re-derives the whole entity.
    entity._handle_update({"P4": {"val": 230, "v": 23.0}})

    assert entity.current_temperature == 23.0
    assert entity.target_temperature == 20.0  # not clobbered back to 24.0


def test_optimistic_hvac_mode_survives_unrelated_io_push():
    """A set HVAC mode must persist across an unrelated IO push."""
    entity = _nature_climate()
    assert entity.hvac_mode == HVACMode.COOL

    entity._optimistic_update("hvac_mode", HVACMode.HEAT, 0)
    assert entity.hvac_mode == HVACMode.HEAT
    assert entity._raw_device["data"]["P1"]["type"] % 2 == 1  # still "on"
    assert (
        entity._raw_device["data"]["P7"]["val"]
        == REVERSE_LIFESMART_HVAC_MODE_MAP[HVACMode.HEAT]
    )

    entity._handle_update({"P4": {"val": 230, "v": 23.0}})
    assert entity.hvac_mode == HVACMode.HEAT


def test_optimistic_hvac_off_survives_unrelated_io_push():
    """Turning the panel off must persist across an unrelated IO push."""
    entity = _nature_climate()

    entity._optimistic_update("hvac_mode", HVACMode.OFF, 0)
    assert entity.hvac_mode == HVACMode.OFF
    assert entity._raw_device["data"]["P1"]["type"] % 2 == 0  # "off"

    entity._handle_update({"P4": {"val": 230, "v": 23.0}})
    assert entity.hvac_mode == HVACMode.OFF


def test_optimistic_fan_mode_survives_unrelated_io_push():
    """A set fan mode must persist across an unrelated IO push (P9 and P10)."""
    entity = _nature_climate()

    entity._optimistic_update("fan_mode", "low", 0)
    assert entity.fan_mode == "low"
    assert entity._raw_device["data"]["P9"]["val"] == LIFESMART_TF_FAN_MAP["low"]
    # P10 is read in preference to P9, so it must be updated too.
    assert entity._raw_device["data"]["P10"]["val"] == LIFESMART_TF_FAN_MAP["low"]

    entity._handle_update({"P4": {"val": 230, "v": 23.0}})
    assert entity.fan_mode == "low"


def test_optimistic_update_skipped_when_write_fails():
    """A non-zero client result must leave state and cache untouched."""
    entity = _nature_climate()
    entity.async_write_ha_state.reset_mock()

    entity._optimistic_update("temperature", 20.0, -1)

    assert entity.target_temperature == 24.0  # unchanged
    assert entity._raw_device["data"]["P8"]["v"] == 24.0  # cache untouched
    entity.async_write_ha_state.assert_not_called()


async def test_async_set_temperature_optimistic_end_to_end():
    """The async service path sends the command and optimistically commits on success."""
    client = MagicMock()
    client.async_set_climate_temperature = AsyncMock(return_value=0)
    entity = _nature_climate(client)

    await entity.async_set_temperature(temperature=20.0)

    client.async_set_climate_temperature.assert_awaited_once()
    assert entity.target_temperature == 20.0
    assert entity._raw_device["data"]["P8"]["v"] == 20.0


async def test_async_set_temperature_no_optimistic_on_failed_write():
    """A failed client write must not optimistically move the entity state."""
    client = MagicMock()
    client.async_set_climate_temperature = AsyncMock(return_value=-1)
    entity = _nature_climate(client)

    await entity.async_set_temperature(temperature=20.0)

    assert entity.target_temperature == 24.0  # unchanged
