"""Tests for the LifeSmart integration's core setup and data handling."""

from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from custom_components.lifesmart import (
    LifeSmartStateManager,
    async_unload_entry,
)
from custom_components.lifesmart.const import (
    DOMAIN,
    LIFESMART_STATE_MANAGER,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    DEVICE_ID_KEY,
    HUB_ID_KEY,
)

pytestmark = pytest.mark.asyncio


# --- Helper to find a device in the shared fixture ---
def find_device(devices: list, me: str):
    """Helper to find a specific device from the mock list by its 'me' id."""
    return next((d for d in devices if d.get(DEVICE_ID_KEY) == me), None)


# --- 测试集成设置与卸载 ---


async def test_setup_success_and_state_manager_creation(
    hass: HomeAssistant,
    mock_client: MagicMock,
    mock_config_entry: ConfigEntry,
    setup_integration: ConfigEntry,
):
    """测试成功设置，并验证 StateManager 被正确创建、存储并启动。"""
    # The setup_integration fixture handles the setup process.
    assert mock_config_entry.state == ConfigEntryState.LOADED

    entry_data = hass.data[DOMAIN][mock_config_entry.entry_id]
    assert LIFESMART_STATE_MANAGER in entry_data
    state_manager = entry_data[LIFESMART_STATE_MANAGER]
    assert isinstance(state_manager, LifeSmartStateManager)
    # Verify state_manager.start() was called, which indirectly means ws_connect was called
    mock_client.ws_connect.assert_called_once()


async def test_unload_entry_cleans_up_resources(
    hass: HomeAssistant,
    mock_client: MagicMock,
    mock_config_entry: ConfigEntry,
    setup_integration: ConfigEntry,
):
    """测试成功卸载集成，并清理所有资源。"""
    # setup_integration fixture has already run.
    assert mock_config_entry.entry_id in hass.data[DOMAIN]

    # Get the real state_manager instance from hass.data
    state_manager = hass.data[DOMAIN][mock_config_entry.entry_id][
        LIFESMART_STATE_MANAGER
    ]
    # Create a mock for its stop method to verify the call
    state_manager.stop = AsyncMock()

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_unload",
        return_value=True,
    ) as mock_forward_unload:
        assert await async_unload_entry(hass, mock_config_entry) is True

    mock_forward_unload.assert_called_once()
    state_manager.stop.assert_awaited_once()
    assert mock_config_entry.entry_id not in hass.data[DOMAIN]


# --- **核心修正：隔离测试 LifeSmartStateManager 的 WebSocket 消息处理逻辑** ---


@pytest.mark.asyncio
async def test_state_manager_message_handling_logic(
    hass: HomeAssistant, mock_client: MagicMock, mock_lifesmart_devices: list
):
    """
    全面测试 LifeSmartStateManager 对所有类型 WebSocket 消息的响应。
    此测试通过捕获传递给 ws_connect 的回调函数来精确测试消息处理逻辑。
    """
    # 1. Initialize StateManager
    entry_id = "test_entry_id_123"
    manager = LifeSmartStateManager(
        hass, entry_id, mock_client, mock_lifesmart_devices, None
    )

    # Mock platform setup and populate unique_id mapping
    unique_id = f"lifesmart_{mock_lifesmart_devices[0][HUB_ID_KEY]}_{mock_lifesmart_devices[0][DEVICE_ID_KEY]}_L1"
    manager._unique_ids = {("hub_sw", "sw_if3", "L1"): unique_id}
    manager._exclude_devices = ["excluded_device"]
    manager._exclude_hubs = ["excluded_hub"]

    # 2. Start StateManager and capture the WebSocket callback
    await manager.start()
    mock_client.ws_connect.assert_called_once()
    # Capture the first argument passed to ws_connect, which is the message handling callback
    message_callback = mock_client.ws_connect.call_args.args[0]
    assert callable(message_callback)

    # 3. Use the captured callback to test various message scenarios
    with patch(
        "homeassistant.helpers.dispatcher.async_dispatcher_send"
    ) as mock_dispatcher, patch(
        "homeassistant.helpers.device_registry.async_get"
    ) as mock_get_dr, patch.object(
        hass.config_entries, "async_reload"
    ) as mock_reload:

        mock_device_registry = MagicMock()
        mock_get_dr.return_value = mock_device_registry

        # --- Scenario: 'io' message -> triggers entity update ---
        update_msg = {
            "type": "io",
            "msg": {
                "agt": "hub_sw",
                "me": "sw_if3",
                "idx": "L1",
                "data": {"val": 0},
            },
        }
        await message_callback(update_msg)
        mock_dispatcher.assert_called_once_with(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}",
            {"val": 0},
        )
        mock_dispatcher.reset_mock()

        # --- Scenario: 'epname' message -> updates device registry ---
        name_change_msg = {
            "type": "epname",
            "msg": {"agt": "hub_sw", "me": "sw_if3", "name": "New Name"},
        }
        mock_device = MagicMock(spec=DeviceEntry, id="device_id_1")
        mock_device_registry.async_get_device.return_value = mock_device
        await message_callback(name_change_msg)
        mock_device_registry.async_get_device.assert_called_with(
            identifiers={(DOMAIN, "hub_sw", "sw_if3")}
        )
        mock_device_registry.async_update_device.assert_called_with(
            device_id="device_id_1", name="New Name"
        )

        # --- Scenario: 'devadd' and 'devdel' messages -> trigger integration reload ---
        for msg_type in ["devadd", "devdel"]:
            dev_change_msg = {
                "type": msg_type,
                "msg": {"agt": "any", "me": "any", "devtype": "any"},
            }
            await message_callback(dev_change_msg)
            # Verify reload is called for the correct entry_id
            mock_reload.assert_called_with(entry_id)
            mock_reload.reset_mock()

        # --- Scenario: Test ignore logic ---
        # Ignore excluded device
        await message_callback(
            {"type": "io", "msg": {"agt": "hub_bs", "me": "excluded_device"}}
        )
        # Ignore excluded hub
        await message_callback(
            {
                "type": "io",
                "msg": {"agt": "excluded_hub", "me": "device_on_excluded_hub"},
            }
        )
        # Ignore malformed message
        await message_callback({"type": "io", "msg": {}})

        mock_dispatcher.assert_not_called()
        mock_reload.assert_not_called()
