"""Test LifeSmart light entities."""

from unittest.mock import AsyncMock, call

import pytest
from homeassistant.components.light import (
    DOMAIN as LIGHT_DOMAIN,
    ColorMode,
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_RGBW_COLOR,
    ATTR_EFFECT,
)
from homeassistant.const import STATE_ON, STATE_OFF
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.lifesmart.const import (
    DOMAIN,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    DYN_EFFECT_MAP,
)
from custom_components.lifesmart.light import async_setup_entry

# --- Mock Device Data ---

# 1. 亮度灯 (e.g., SL_SPWM)
MOCK_BRIGHTNESS_LIGHT = {
    "agt": "hub1",
    "me": "bright_light_me",
    "devtype": "SL_SPWM",
    "name": "Brightness Light",
    "data": {"P1": {"type": 129, "val": 128, "v": 128}},  # On, 50% brightness
}

# 2. 色温灯 (e.g., SL_LI_WW)
MOCK_DIMMER_LIGHT = {
    "agt": "hub1",
    "me": "dimmer_light_me",
    "devtype": "SL_LI_WW",
    "name": "Dimmer Light",
    "data": {
        "P1": {"type": 129, "val": 204},  # On, 80% brightness
        "P2": {"type": 1, "val": 128},  # Middle color temp
    },
}

# 3. 单IO RGBW灯 (e.g., SL_LI_UG1)
MOCK_SINGLE_IO_RGBW_LIGHT = {
    "agt": "hub1",
    "me": "single_rgbw_me",
    "devtype": "SL_LI_UG1",
    "name": "Garden Light",
    "data": {"P1": {"type": 129, "val": 0x00FF8040}},  # On, RGB color (255, 128, 64)
}

# 4. 双IO RGBW灯 (e.g., SL_CT_RGBW)
MOCK_DUAL_IO_RGBW_LIGHT = {
    "agt": "hub1",
    "me": "dual_rgbw_me",
    "devtype": "SL_CT_RGBW",
    "name": "LED Strip",
    "data": {
        "RGBW": {"type": 129, "val": 0x32FF00FF},  # On, White=50, Red=255, Blue=255
        "DYN": {"type": 128, "val": 0},  # Effect off
    },
}

# 5. 量子灯 (OD_WE_QUAN)
MOCK_QUANTUM_LIGHT = {
    "agt": "hub1",
    "me": "quantum_me",
    "devtype": "OD_WE_QUAN",
    "name": "Quantum Light",
    "data": {
        "P1": {"type": 129, "val": 255},  # On, Full brightness
        "P2": {"type": 1, "val": DYN_EFFECT_MAP["海浪"]},  # Effect "海浪"
    },
}

# 6. 超级碗(SPOT) RGB灯
MOCK_SPOT_RGB_LIGHT = {
    "agt": "hub1",
    "me": "spot_rgb_me",
    "devtype": "SL_SPOT",
    "name": "Spot RGB",
    "data": {"RGB": {"type": 129, "val": 0x00FF0000}},  # On, Red
}

# 7. 超级碗(SPOT) RGBW灯
MOCK_SPOT_RGBW_LIGHT = {
    "agt": "hub1",
    "me": "spot_rgbw_me",
    "devtype": "MSL_IRCTL",
    "name": "Spot RGBW",
    "data": {
        "RGBW": {"type": 129, "val": 0x6400FF00},  # On, White=100, Green=255
        "DYN": {"type": 128, "val": 0},
    },
}

# 8. 车库门附带灯
MOCK_COVER_LIGHT = {
    "agt": "hub1",
    "me": "garage_me",
    "devtype": "SL_ETDOOR",
    "name": "Garage Door",
    "data": {"P1": {"type": 128, "val": 0}},  # Off
}

ALL_MOCK_LIGHTS = [
    MOCK_BRIGHTNESS_LIGHT,
    MOCK_DIMMER_LIGHT,
    MOCK_SINGLE_IO_RGBW_LIGHT,
    MOCK_DUAL_IO_RGBW_LIGHT,
    MOCK_QUANTUM_LIGHT,
    MOCK_SPOT_RGB_LIGHT,
    MOCK_SPOT_RGBW_LIGHT,
    MOCK_COVER_LIGHT,
]


@pytest.fixture
def mock_light_platform(hass, mock_lifesmart_client, mock_config_entry):
    """Fixture to set up the light platform with mock devices."""
    hass.data[DOMAIN][mock_config_entry.entry_id] = {
        "client": mock_lifesmart_client,
        "devices": ALL_MOCK_LIGHTS,
        "exclude_devices": "",
        "exclude_hubs": "",
    }
    return True


@pytest.mark.asyncio
async def test_setup_lights(hass: HomeAssistant, mock_light_platform):
    """Test the setup of all light entities."""
    async_add_entities = AsyncMock()
    await async_setup_entry(hass, AsyncMock(), async_add_entities)

    assert async_add_entities.call_count == 1
    entities = async_add_entities.call_args[0][0]
    # Should create one entity for each mock device
    assert len(entities) == len(ALL_MOCK_LIGHTS)

    # Verify entity types and unique IDs
    unique_ids = {entity.unique_id for entity in entities}
    expected_ids = {
        f"{LIGHT_DOMAIN}.sl_spwm_hub1_bright_light_me_p1",
        f"{LIGHT_DOMAIN}.sl_li_ww_hub1_dimmer_light_me_dimmer",
        f"{LIGHT_DOMAIN}.sl_li_ug1_hub1_single_rgbw_me_p1",
        f"{LIGHT_DOMAIN}.sl_ct_rgbw_hub1_dual_rgbw_me_rgbw_dual",
        f"{LIGHT_DOMAIN}.od_we_quan_hub1_quantum_me_quantum",
        f"{LIGHT_DOMAIN}.sl_spot_hub1_spot_rgb_me_rgb",
        f"{LIGHT_DOMAIN}.msl_irctl_hub1_spot_rgbw_me_rgbw",
        f"{LIGHT_DOMAIN}.sl_etdoor_hub1_garage_me_p1",
    }
    assert unique_ids == expected_ids


@pytest.mark.asyncio
async def test_brightness_light(
    hass: HomeAssistant, mock_light_platform, mock_lifesmart_client
):
    """Test LifeSmartBrightnessLight entity."""
    await async_setup_entry(hass, AsyncMock(), AsyncMock())
    entity_id = f"{LIGHT_DOMAIN}.sl_spwm_hub1_bright_light_me_p1"
    state = hass.states.get(entity_id)

    # Test initial state
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_BRIGHTNESS) == 128
    assert state.attributes.get("color_mode") == ColorMode.BRIGHTNESS

    # Test turn_on with brightness
    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {"entity_id": entity_id, ATTR_BRIGHTNESS: 255},
        blocking=True,
    )
    mock_lifesmart_client.send_epset_async.assert_called_with(
        "hub1", "bright_light_me", "P1", "0xcf", 255
    )

    # Test turn_off
    await hass.services.async_call(
        LIGHT_DOMAIN, "turn_off", {"entity_id": entity_id}, blocking=True
    )
    mock_lifesmart_client.turn_off_light_switch_async.assert_called_with(
        "P1", "hub1", "bright_light_me"
    )


@pytest.mark.asyncio
async def test_dimmer_light(
    hass: HomeAssistant, mock_light_platform, mock_lifesmart_client
):
    """Test LifeSmartDimmerLight entity."""
    await async_setup_entry(hass, AsyncMock(), AsyncMock())
    entity_id = f"{LIGHT_DOMAIN}.sl_li_ww_hub1_dimmer_light_me_dimmer"
    state = hass.states.get(entity_id)

    # Test initial state
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_BRIGHTNESS) == 204
    assert state.attributes.get("color_mode") == ColorMode.COLOR_TEMP
    assert state.attributes.get(ATTR_COLOR_TEMP_KELVIN) is not None

    # Test turn_on with brightness and color temp
    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {"entity_id": entity_id, ATTR_BRIGHTNESS: 100, ATTR_COLOR_TEMP_KELVIN: 4000},
        blocking=True,
    )

    # It should call set brightness, set temp, and then turn on
    # Note: the implementation in light.py sends commands sequentially, not via multi_ep
    # We check for the individual calls
    mock_lifesmart_client.send_epset_async.assert_has_calls(
        [
            call("hub1", "dimmer_light_me", "P1", "0xcf", 100),
            call(
                "hub1", "dimmer_light_me", "P2", "0xcf", pytest.approx(147, abs=1)
            ),  # Calculated value for 4000K
        ],
        any_order=True,
    )
    mock_lifesmart_client.turn_on_light_switch_async.assert_called_with(
        "P1", "hub1", "dimmer_light_me"
    )


@pytest.mark.asyncio
async def test_quantum_light_and_effects(
    hass: HomeAssistant, mock_light_platform, mock_lifesmart_client
):
    """Test LifeSmartQuantumLight entity and its effect handling."""
    await async_setup_entry(hass, AsyncMock(), AsyncMock())
    entity_id = f"{LIGHT_DOMAIN}.od_we_quan_hub1_quantum_me_quantum"
    state = hass.states.get(entity_id)

    # Test initial state (in effect mode)
    assert state.state == STATE_ON
    assert state.attributes.get("color_mode") == ColorMode.RGBW
    assert state.attributes.get(ATTR_EFFECT) == "海浪"
    assert state.attributes.get(ATTR_BRIGHTNESS) == 255

    # Test switching to a different effect
    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {"entity_id": entity_id, ATTR_EFFECT: "青草"},
        blocking=True,
    )
    mock_lifesmart_client.async_set_multi_ep_async.assert_called_with(
        "hub1",
        "quantum_me",
        [
            {"idx": "P1", "type": "0x81", "val": 1},
            {"idx": "P2", "type": "0xff", "val": DYN_EFFECT_MAP["青草"]},
        ],
    )

    # Test switching to a static color (should turn off effect)
    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {"entity_id": entity_id, ATTR_RGBW_COLOR: [255, 0, 0, 50]},
        blocking=True,
    )
    expected_color_val = (50 << 24) | (255 << 16) | (0 << 8) | 0
    mock_lifesmart_client.async_set_multi_ep_async.assert_called_with(
        "hub1",
        "quantum_me",
        [
            {"idx": "P1", "type": "0x81", "val": 1},
            {"idx": "P2", "type": "0xff", "val": expected_color_val},
        ],
    )


@pytest.mark.asyncio
async def test_dual_io_rgbw_light(
    hass: HomeAssistant, mock_light_platform, mock_lifesmart_client
):
    """Test LifeSmartDualIORGBWLight entity."""
    await async_setup_entry(hass, AsyncMock(), AsyncMock())
    entity_id = f"{LIGHT_DOMAIN}.sl_ct_rgbw_hub1_dual_rgbw_me_rgbw_dual"
    state = hass.states.get(entity_id)

    # Test initial state
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_RGBW_COLOR) == (255, 0, 255, 50)
    assert state.attributes.get(ATTR_EFFECT) is None

    # Test turning on with an effect
    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {"entity_id": entity_id, ATTR_EFFECT: "缤纷时代"},
        blocking=True,
    )
    mock_lifesmart_client.async_set_multi_ep_async.assert_called_with(
        "hub1",
        "dual_rgbw_me",
        [
            {"idx": "RGBW", "type": "0x81", "val": 1},
            {"idx": "DYN", "type": "0xff", "val": DYN_EFFECT_MAP["缤纷时代"]},
        ],
    )

    # Test turning on with a color (should turn off effect)
    await hass.services.async_call(
        LIGHT_DOMAIN,
        "turn_on",
        {"entity_id": entity_id, ATTR_RGBW_COLOR: [10, 20, 30, 40]},
        blocking=True,
    )
    color_val = (40 << 24) | (10 << 16) | (20 << 8) | 30
    mock_lifesmart_client.async_set_multi_ep_async.assert_called_with(
        "hub1",
        "dual_rgbw_me",
        [
            {"idx": "RGBW", "type": "0xff", "val": color_val},
            {"idx": "DYN", "type": "0x80", "val": 0},
        ],
    )


@pytest.mark.asyncio
async def test_single_io_rgbw_light_update(hass: HomeAssistant, mock_light_platform):
    """Test state update for a single IO RGBW light."""
    await async_setup_entry(hass, AsyncMock(), AsyncMock())
    entity_id = f"{LIGHT_DOMAIN}.sl_li_ug1_hub1_single_rgbw_me_p1"

    # Initial state
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_RGBW_COLOR) == (
        255,
        128,
        64,
        0,
    )  # W is 0 in RGB mode
    assert state.attributes.get(ATTR_EFFECT) is None

    # Simulate an update to white light mode
    update_data = {"type": 129, "val": 0x50000000}  # White light at 80 (0x50)
    async_dispatcher_send(
        hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", update_data
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_EFFECT) is None
    # Brightness is calculated from the white channel (80/100 * 255)
    assert state.attributes.get(ATTR_BRIGHTNESS) == pytest.approx(204, abs=1)

    # Simulate an update to effect mode
    update_data = {"type": 129, "val": DYN_EFFECT_MAP["魔力红"]}
    async_dispatcher_send(
        hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", update_data
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes.get(ATTR_EFFECT) == "魔力红"
    assert (
        state.attributes.get(ATTR_BRIGHTNESS) == 255
    )  # Full brightness in effect mode


@pytest.mark.asyncio
async def test_cover_light(
    hass: HomeAssistant, mock_light_platform, mock_lifesmart_client
):
    """Test the light entity associated with a cover."""
    await async_setup_entry(hass, AsyncMock(), AsyncMock())
    entity_id = f"{LIGHT_DOMAIN}.sl_etdoor_hub1_garage_me_p1"
    state = hass.states.get(entity_id)

    # Test initial state
    assert state.state == STATE_OFF
    assert state.attributes.get("color_mode") == ColorMode.ONOFF

    # Test turn_on
    await hass.services.async_call(
        LIGHT_DOMAIN, "turn_on", {"entity_id": entity_id}, blocking=True
    )
    mock_lifesmart_client.turn_on_light_switch_async.assert_called_with(
        "P1", "hub1", "garage_me"
    )

    # Test turn_off
    await hass.services.async_call(
        LIGHT_DOMAIN, "turn_off", {"entity_id": entity_id}, blocking=True
    )
    mock_lifesmart_client.turn_off_light_switch_async.assert_called_with(
        "P1", "hub1", "garage_me"
    )
