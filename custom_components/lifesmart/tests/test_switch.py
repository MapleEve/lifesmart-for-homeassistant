"""Unit tests for the LifeSmart switch platform."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN, SwitchDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_OFF, STATE_ON, STATE_OFF
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.lifesmart.const import *
from custom_components.lifesmart.switch import async_setup_entry
from .test_utils import get_entity_unique_id


# --- Test `async_setup_entry` and Entity Behavior ---


@pytest.mark.asyncio
class TestSwitchSetup:
    """Test the platform setup."""

    async def test_setup_all_switches(
        self, hass: HomeAssistant, setup_integration: ConfigEntry
    ):
        """Test successful setup of all switch entities from conftest."""
        # 3 (sw_if3) + 1 (sw_ol) + 3 (sw_nature) + 3 (generic_p_switch_mode) + 9 (sw_p9) = 19
        assert len(hass.states.async_entity_ids(SWITCH_DOMAIN)) == 19

        assert hass.states.get("switch.9_way_controller_p4") is not None

    async def test_setup_with_exclusions(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        mock_config_data: dict,
        mock_lifesmart_devices: list,
    ):
        """Test that devices and hubs can be excluded from setup."""
        # 1. 创建一个带有自定义排除选项的 ConfigEntry
        custom_options = {
            CONF_EXCLUDE_ITEMS: "sw_ol, sw_p9",  # Exclude Outlet and 9-way
            CONF_EXCLUDE_AGTS: "excluded_hub",  # Exclude Power Plug
        }
        entry_with_exclusions = MockConfigEntry(
            domain=DOMAIN,
            data=mock_config_data,
            options=custom_options,
            entry_id="exclusion_test_entry",
        )

        # 2. 准备 hass.data，因为 async_setup_entry 会从中读取数据
        hass.data[DOMAIN] = {
            entry_with_exclusions.entry_id: {
                "client": mock_client,
                "devices": mock_lifesmart_devices,
            }
        }

        # 3. 调用被测试的函数
        # async_add_entities is a synchronous function, not a coroutine.
        async_add_entities = MagicMock()
        await async_setup_entry(hass, entry_with_exclusions, async_add_entities)

        # 4. 断言
        # 预期: 3 (sw_if3) + 3 (sw_nature) + 3 (generic_p_switch_mode) = 9
        created_entities = async_add_entities.call_args[0][0]
        assert len(created_entities) == 9

        entity_ids = {entity.unique_id for entity in created_entities}
        assert not any("sw_ol" in eid for eid in entity_ids)
        assert not any("sw_p9" in eid for eid in entity_ids)
        assert not any("excluded_hub" in eid for eid in entity_ids)


class TestStandardSwitch:
    """Test a standard 3-gang switch (SL_SW_IF3)."""

    ENTITY_ID = "switch.3_gang_switch_l1"
    DEVICE_ME = "sw_if3"
    HUB_ID = "hub_sw"
    SUB_KEY = "L1"

    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        state = hass.states.get(self.ENTITY_ID)
        assert state is not None
        assert state.state == STATE_ON
        assert state.attributes.get("device_class") == SwitchDeviceClass.SWITCH

    async def test_turn_on_off_and_update(
        self, hass: HomeAssistant, mock_client: AsyncMock, setup_integration
    ):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )
        assert hass.states.get(self.ENTITY_ID).state == STATE_OFF
        mock_client.turn_off_light_switch_async.assert_called_with(
            self.SUB_KEY, self.HUB_ID, self.DEVICE_ME
        )

        unique_id = get_entity_unique_id(hass, self.ENTITY_ID)
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", {"type": 129}
        )
        await hass.async_block_till_done()
        assert hass.states.get(self.ENTITY_ID).state == STATE_ON


class TestSmartOutlet:
    """Test a smart outlet (SL_OL)."""

    ENTITY_ID = "switch.smart_outlet_o"
    DEVICE_ME = "sw_ol"
    HUB_ID = "hub_sw"
    SUB_KEY = "O"

    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        state = hass.states.get(self.ENTITY_ID)
        assert state is not None
        assert state.state == STATE_ON
        assert state.attributes.get("device_class") == SwitchDeviceClass.OUTLET

    async def test_turn_on_off(
        self, hass: HomeAssistant, mock_client: AsyncMock, setup_integration
    ):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )
        mock_client.turn_off_light_switch_async.assert_called_with(
            self.SUB_KEY, self.HUB_ID, self.DEVICE_ME
        )


class TestGenericControllerAsSwitch:
    """Test a generic controller (SL_P) in 3-way switch mode."""

    DEVICE_ME = "generic_p_switch_mode"
    HUB_ID = "hub_sw"

    @pytest.mark.parametrize(
        ("entity_id_suffix", "sub_key", "initial_state"),
        [
            ("p2", "P2", STATE_ON),
            ("p3", "P3", STATE_OFF),
            ("p4", "P4", STATE_ON),
        ],
    )
    async def test_channel_behavior(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        setup_integration,
        entity_id_suffix: str,
        sub_key: str,
        initial_state: str,
    ):
        entity_id = f"switch.generic_controller_switch_{entity_id_suffix}"

        state = hass.states.get(entity_id)
        assert state is not None, f"Entity {entity_id} not found"
        assert state.state == initial_state

        await hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )
        mock_client.turn_off_light_switch_async.assert_called_with(
            sub_key, self.HUB_ID, self.DEVICE_ME
        )


class TestNineWayController:
    """Test the 9-way switch controller (SL_P_SW)."""

    DEVICE_ME = "sw_p9"
    HUB_ID = "hub_sw"

    @pytest.mark.parametrize(
        ("entity_id_suffix", "sub_key", "initial_state"),
        [
            ("p1", "P1", STATE_ON),
            ("p8", "P8", STATE_OFF),
            ("p9", "P9", STATE_ON),
        ],
    )
    async def test_channel_behavior(
        self,
        hass: HomeAssistant,
        mock_client: AsyncMock,
        setup_integration,
        entity_id_suffix: str,
        sub_key: str,
        initial_state: str,
    ):
        entity_id = f"switch.9_way_controller_{entity_id_suffix}"

        state = hass.states.get(entity_id)
        assert state is not None, f"Entity {entity_id} not found"
        assert state.state == initial_state

        await hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )
        mock_client.turn_off_light_switch_async.assert_called_with(
            sub_key, self.HUB_ID, self.DEVICE_ME
        )
