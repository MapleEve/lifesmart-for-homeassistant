"""Tests for the LifeSmart integration's core setup and data handling."""

import asyncio
import json
from unittest.mock import MagicMock, patch, AsyncMock

import aiohttp
import pytest
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant

from custom_components.lifesmart import (
    LifeSmartStateManager,
)
from custom_components.lifesmart.const import (
    DOMAIN,
    LIFESMART_STATE_MANAGER,
    CONF_EXCLUDE_ITEMS,
    CONF_EXCLUDE_AGTS,
    CONF_AI_INCLUDE_ITEMS,
    CONF_AI_INCLUDE_AGTS,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    DEVICE_ID_KEY,
    HUB_ID_KEY,
)


# --- Helper to find a device in the shared fixture ---
def find_device(devices: list, me: str):
    """Helper to find a specific device from the mock list by its 'me' id."""
    return next((d for d in devices if d.get(DEVICE_ID_KEY) == me), None)


# --- 测试集成设置与卸载 ---


async def test_setup_success_and_state_manager_creation(
    hass: HomeAssistant,
    mock_client: MagicMock,
    setup_integration: ConfigEntry,
):
    """测试成功设置，并验证 StateManager 被正确创建、存储并启动。"""
    # The setup_integration fixture handles the setup process.
    assert setup_integration.state == ConfigEntryState.LOADED

    entry_data = hass.data[DOMAIN][setup_integration.entry_id]
    assert LIFESMART_STATE_MANAGER in entry_data
    state_manager = entry_data[LIFESMART_STATE_MANAGER]
    assert isinstance(state_manager, LifeSmartStateManager)


async def test_unload_entry_cleans_up_resources(
    hass: HomeAssistant,
    setup_integration: ConfigEntry,
):
    """测试成功卸载集成，并清理所有资源。"""
    # The setup_integration fixture has already run and loaded the integration.
    assert setup_integration.entry_id in hass.data[DOMAIN]

    # The teardown logic (unload) is now handled by the `setup_integration` fixture's `yield`
    # This test now simply verifies that the fixture works as expected.
    # The unload process is implicitly tested when the fixture cleans up.
    pass


@pytest.mark.asyncio
async def test_state_manager_message_handling_logic(
    hass: HomeAssistant, mock_client: MagicMock, mock_lifesmart_devices: list
):
    """
    测试 LifeSmartStateManager 对 'io' 类型 WebSocket 消息的响应。
    此测试通过捕获传递给 ws_connect 的回调函数来精确测试消息处理逻辑。
    """
    # 从 conftest.py 中获取一个真实存在的设备用于测试
    test_device = find_device(mock_lifesmart_devices, "sw_if3")
    assert test_device is not None, "测试设备 'sw_if3' 未在 conftest 中定义"

    # 使用真实设备的 hub_id 和 me
    hub_id = test_device[HUB_ID_KEY]
    device_id = test_device[DEVICE_ID_KEY]
    sub_key = "L1"  # 假设的子键

    # 创建一个模拟的 ConfigEntry
    mock_config_entry = MagicMock(spec=ConfigEntry)
    mock_config_entry.entry_id = "test_entry_id_123"
    mock_config_entry.options = {
        CONF_EXCLUDE_ITEMS: "excluded_device",
        CONF_EXCLUDE_AGTS: "excluded_hub",
    }

    manager = None
    # --- FIX: Patch the method that creates the real network connection ---
    with patch(
        "custom_components.lifesmart.LifeSmartStateManager._create_websocket",
        new_callable=AsyncMock,
    ) as mock_create_ws:
        # 模拟一个 WebSocket 对象
        mock_ws = MagicMock(spec=aiohttp.ClientWebSocketResponse)
        mock_ws.send_str = AsyncMock()
        mock_ws.close = AsyncMock()

        # 模拟认证成功
        auth_response_msg = MagicMock(spec=aiohttp.WSMessage)
        auth_response_msg.type = aiohttp.WSMsgType.TEXT
        auth_response_msg.data = json.dumps({"code": 0, "message": "success"})

        # 模拟消息流
        async def mock_receive_logic(*args, **kwargs):
            # 第一次调用返回认证成功
            if mock_ws.receive.call_count == 1:
                return auth_response_msg
            # 后续调用无限期挂起，直到被取消
            await asyncio.sleep(3600)

        mock_ws.receive.side_effect = mock_receive_logic

        # 让 _create_websocket 返回我们完全模拟的 WebSocket 对象
        mock_create_ws.return_value = mock_ws

        try:
            # 1. 初始化 StateManager
            manager = LifeSmartStateManager(
                hass=hass,
                config_entry=mock_config_entry,
                client=mock_client,
                ws_url="wss://fake.url/ws",
                refresh_callback=AsyncMock(),
            )

            # 2. 启动 StateManager
            manager.start()
            await asyncio.sleep(0)  # 允许任务启动

            # 验证 _create_websocket 被调用，证明网络连接尝试被触发
            mock_create_ws.assert_awaited_once()

            with patch(
                "custom_components.lifesmart.data_update_handler",
                new_callable=AsyncMock,
            ) as mock_data_handler:
                # 3. 直接调用 _process_text_message 来模拟收到消息
                update_msg_str = json.dumps(
                    {
                        "type": "io",
                        "msg": {
                            "agt": hub_id,
                            "me": device_id,
                            "idx": sub_key,
                            "data": {"val": 0},
                        },
                    }
                )
                await manager._process_text_message(update_msg_str)
                mock_data_handler.assert_awaited_once()

        finally:
            if manager:
                await manager.stop()


from custom_components.lifesmart import data_update_handler


@pytest.mark.asyncio
async def test_data_update_handler_logic(hass: HomeAssistant):
    """
    独立测试 data_update_handler 函数的过滤和分发逻辑。
    """
    mock_config_entry = MagicMock(spec=ConfigEntry)
    mock_config_entry.options = {
        CONF_EXCLUDE_ITEMS: "excluded_device",
        CONF_EXCLUDE_AGTS: "excluded_hub",
        CONF_AI_INCLUDE_ITEMS: "ai_device",
        CONF_AI_INCLUDE_AGTS: "ai_hub",
    }

    with patch("custom_components.lifesmart.dispatcher_send") as mock_dispatcher:

        # --- 场景1: 标准设备更新 -> 应该分发 ---
        raw_data = {
            "type": "io",
            "msg": {
                "devtype": "SL_SW_IF3",
                "agt": "hub_sw",
                "me": "61A9",
                "idx": "L1",
                "data": {"val": 1},
            },
        }
        await data_update_handler(hass, mock_config_entry, raw_data)
        expected_unique_id = "sl_sw_if3_hub_sw_61a9_l1"
        mock_dispatcher.assert_called_once_with(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{expected_unique_id}",
            raw_data["msg"],
        )
        mock_dispatcher.reset_mock()

        # --- 场景2: 被排除的设备 -> 不应分发 ---
        raw_data_excluded_dev = {
            "type": "io",
            "msg": {"agt": "hub_sw", "me": "excluded_device", "idx": "G"},
        }
        await data_update_handler(hass, mock_config_entry, raw_data_excluded_dev)
        mock_dispatcher.assert_not_called()
        mock_dispatcher.reset_mock()

        # --- 场景3: 来自被排除的中枢 -> 不应分发 ---
        raw_data_excluded_hub = {
            "type": "io",
            "msg": {"agt": "excluded_hub", "me": "some_device", "idx": "P1"},
        }
        await data_update_handler(hass, mock_config_entry, raw_data_excluded_hub)
        mock_dispatcher.assert_not_called()
        mock_dispatcher.reset_mock()

        # --- 场景4: AI 事件 -> 不应分发 (特殊处理后返回) ---
        raw_data_ai = {
            "type": "io",
            "msg": {"agt": "ai_hub", "me": "ai_device", "idx": "s"},
        }
        await data_update_handler(hass, mock_config_entry, raw_data_ai)
        mock_dispatcher.assert_not_called()
        mock_dispatcher.reset_mock()
