"""Tests for the LifeSmart integration's core setup and data handling."""

from unittest.mock import MagicMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

# 从组件的根 __init__.py 文件中导入所有需要的对象
from custom_components.lifesmart import (
    LifeSmartStateManager,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.lifesmart.const import (
    DOMAIN,
    LIFESMART_STATE_MANAGER,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    DEVICE_ID_KEY,
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
    mock_lifesmart_devices: list,
):
    """测试成功设置，并验证 StateManager 被正确创建、存储并启动。"""
    # The mock_client fixture from conftest already has get_all_device_async mocked
    # to return mock_lifesmart_devices.

    with patch("homeassistant.config_entries.ConfigEntries.async_forward_entry_setups"):
        assert await async_setup_entry(hass, mock_config_entry) is True
        await hass.async_block_till_done()

    entry_data = hass.data[DOMAIN][mock_config_entry.entry_id]
    assert LIFESMART_STATE_MANAGER in entry_data
    state_manager = entry_data[LIFESMART_STATE_MANAGER]
    assert isinstance(state_manager, LifeSmartStateManager)
    # 验证 state_manager.start() 已被调用, 这间接证明了 ws_connect 被调用
    mock_client.ws_connect.assert_called_once()


async def test_unload_entry_cleans_up_resources(
    hass: HomeAssistant, mock_client: MagicMock, mock_config_entry: ConfigEntry
):
    """测试成功卸载集成，并清理所有资源。"""
    await async_setup_entry(hass, mock_config_entry)
    await hass.async_block_till_done()

    # 从 hass.data 中获取真实的 state_manager 实例
    state_manager = hass.data[DOMAIN][mock_config_entry.entry_id][
        LIFESMART_STATE_MANAGER
    ]
    # 为其 stop 方法创建一个 mock 以便验证调用
    state_manager.stop = MagicMock()

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_forward_entry_unload",
        return_value=True,
    ) as mock_unload:
        assert await async_unload_entry(hass, mock_config_entry) is True

    mock_unload.assert_called_once()
    state_manager.stop.assert_called_once()
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
    # 1. 初始化 StateManager
    entry_id = "test_entry_id_123"
    manager = LifeSmartStateManager(
        hass, entry_id, mock_client, mock_lifesmart_devices, None
    )

    # 模拟平台已设置并填充了 unique_id 映射
    manager._unique_ids = {
        ("hub_sw", "sw_if3", "L1"): "switch.3_gang_switch_l1_unique_id"
    }
    manager._exclude_devices = ["excluded_device"]
    manager._exclude_hubs = ["excluded_hub"]

    # 2. 启动 StateManager 并捕获 WebSocket 回调
    await manager.start()
    mock_client.ws_connect.assert_called_once()
    # 捕获传递给 ws_connect 的第一个参数，即消息处理回调
    message_callback = mock_client.ws_connect.call_args[0][0]

    # 3. 使用捕获的回调函数来测试各种消息场景
    with patch(
        "homeassistant.helpers.dispatcher.async_dispatcher_send"
    ) as mock_dispatcher, patch(
        "homeassistant.helpers.device_registry.async_get"
    ) as mock_get_dr, patch.object(
        hass.config_entries, "async_reload"
    ) as mock_reload:

        mock_device_registry = MagicMock()
        mock_get_dr.return_value = mock_device_registry

        # --- 场景: 'io' 消息 -> 触发实体更新 ---
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
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_switch.3_gang_switch_l1_unique_id",
            {"val": 0},
        )
        mock_dispatcher.reset_mock()

        # --- 场景: 'epname' 消息 -> 更新设备注册表 ---
        name_change_msg = {
            "type": "epname",
            "msg": {"agt": "hub_sw", "me": "sw_if3", "name": "New Name"},
        }
        mock_device = MagicMock(id="device_id_1")
        mock_device_registry.async_get_device.return_value = mock_device
        await message_callback(name_change_msg)
        mock_device_registry.async_get_device.assert_called_with(
            identifiers={(DOMAIN, "hub_sw", "sw_if3")}
        )
        mock_device_registry.async_update_device.assert_called_with(
            device_id="device_id_1", name="New Name"
        )

        # --- 场景: 'devadd' 和 'devdel' 消息 -> 触发集成重载 ---
        for msg_type in ["devadd", "devdel"]:
            dev_change_msg = {
                "type": msg_type,
                "msg": {"agt": "any", "me": "any", "devtype": "any"},
            }
            await message_callback(dev_change_msg)
            # 验证是针对正确的 entry_id 调用的 reload
            mock_reload.assert_called_with(entry_id)
            mock_reload.reset_mock()

        # --- 场景: 测试忽略逻辑 ---
        # 忽略被排除的设备
        await message_callback(
            {"type": "io", "msg": {"agt": "hub_bs", "me": "excluded_device"}}
        )
        # 忽略被排除的网关
        await message_callback(
            {
                "type": "io",
                "msg": {"agt": "excluded_hub", "me": "device_on_excluded_hub"},
            }
        )
        # 忽略格式错误的消息
        await message_callback({"type": "io", "msg": {}})

        mock_dispatcher.assert_not_called()
        mock_reload.assert_not_called()
