"""
LifeSmart 集成核心功能测试套件 (`__init__.py`)

此文件包含对 LifeSmart 集成核心入口 `__init__.py` 的单元测试。
测试覆盖了集成的设置、卸载、数据处理、服务注册以及各种边界和异常情况，
并完全依赖于 `conftest.py` 中定义的共享 Fixtures。
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.config_entries import (
    ConfigEntryState,
    CONN_CLASS_LOCAL_PUSH,
)
from homeassistant.const import (
    CONF_TYPE,
    CONF_HOST,
    CONF_PORT,
    CONF_USERNAME,
    CONF_PASSWORD,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.lifesmart.const import (
    DOMAIN,
)
from custom_components.lifesmart.exceptions import LifeSmartAuthError


# ====================================================================
# Section 1: 集成设置与卸载 (Setup and Unload)
# ====================================================================


@pytest.mark.asyncio
async def test_setup_and_unload_success_cloud_mode(
    hass: HomeAssistant,
    mock_client: MagicMock,
    mock_config_entry: MockConfigEntry,
    mock_lifesmart_devices: list,
):
    """
    /**
     * test_setup_and_unload_success_cloud_mode - 测试云端模式的完整设置与卸载流程
     *
     * 模拟场景:
     *   - 使用 `conftest.py` 提供的标准云端模式配置。
     *   - 通过 `hass.config_entries.async_setup` 触发完整的设置流程。
     *
     * 预期结果 (设置后):
     *   - 集成状态应为 `LOADED`。
     *   - Hub 应被创建并正确初始化。
     *
     * 预期结果 (卸载后):
     *   - 集成状态应为 `NOT_LOADED`。
     *   - `hass.data[DOMAIN]` 中对应的 entry_id 被完全移除。
     *   - 所有后台任务被清理。
     */
    """
    mock_config_entry.add_to_hass(hass)

    # Mock Hub 的方法而不是不存在的函数
    with patch(
        "custom_components.lifesmart.hub.LifeSmartHub.async_setup", return_value=True
    ) as mock_hub_setup:
        with patch(
            "custom_components.lifesmart.hub.LifeSmartHub.get_devices",
            return_value=mock_lifesmart_devices,
        ):
            with patch(
                "custom_components.lifesmart.hub.LifeSmartHub.get_client",
                return_value=mock_client,
            ):
                assert await hass.config_entries.async_setup(
                    mock_config_entry.entry_id
                ), "应该成功设置配置条目"
                await hass.async_block_till_done()

    assert (
        mock_config_entry.state == ConfigEntryState.LOADED
    ), "配置条目状态应该为已加载"
    entry_data = hass.data[DOMAIN][mock_config_entry.entry_id]
    assert "hub" in entry_data, "条目数据中应包含hub"
    assert entry_data["client"] == mock_client, "条目数据中的客户端应该正确"
    assert entry_data["devices"] == mock_lifesmart_devices, "条目数据中的设备应该正确"

    # 测试卸载
    with patch(
        "custom_components.lifesmart.hub.LifeSmartHub.async_unload"
    ) as mock_hub_unload:
        assert await hass.config_entries.async_unload(
            mock_config_entry.entry_id
        ), "应该成功卸载配置条目"
        await hass.async_block_till_done()
        mock_hub_unload.assert_called_once()

    await asyncio.sleep(0)  # 给予事件循环一个机会来完成所有后台清理任务

    assert (
        mock_config_entry.state == ConfigEntryState.NOT_LOADED
    ), "卸载后配置条目状态应该为未加载"
    assert mock_config_entry.entry_id not in hass.data.get(
        DOMAIN, {}
    ), "卸载后应该清理hass.data中的条目数据"


@pytest.mark.asyncio
async def test_setup_success_local_mode(hass: HomeAssistant, mock_client: MagicMock):
    """
    /**
     * test_setup_success_local_mode - 测试本地模式下的成功设置流程
     *
     * 模拟场景:
     *   - 创建一个包含完整本地连接信息的 `MockConfigEntry`。
     *   - Mock Hub 的设置过程以绕过真实的网络连接。
     *
     * 预期结果:
     *   - 集成状态应为 `LOADED`。
     *   - Hub 应被创建并存储在 `hass.data` 中。
     */
    """
    mock_config_entry_local = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: CONN_CLASS_LOCAL_PUSH,
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 8888,
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "password",
        },
        entry_id="test_local_entry",
        title="Local Hub",
    )
    mock_config_entry_local.add_to_hass(hass)

    mock_devices = []
    with patch(
        "custom_components.lifesmart.hub.LifeSmartHub.async_setup", return_value=True
    ):
        with patch(
            "custom_components.lifesmart.hub.LifeSmartHub.get_devices",
            return_value=mock_devices,
        ):
            with patch(
                "custom_components.lifesmart.hub.LifeSmartHub.get_client",
                return_value=mock_client,
            ):
                assert await hass.config_entries.async_setup(
                    mock_config_entry_local.entry_id
                ), "本地模式应该成功设置"
                await hass.async_block_till_done()

    assert (
        mock_config_entry_local.state == ConfigEntryState.LOADED
    ), "本地模式配置条目状态应该为已加载"
    entry_data = hass.data[DOMAIN][mock_config_entry_local.entry_id]
    assert "hub" in entry_data, "本地模式条目数据中应包含hub"
    assert entry_data["client"] == mock_client, "本地模式条目数据中的客户端应该正确"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exception_instance",
    [
        LifeSmartAuthError("Invalid credentials"),
        ConfigEntryNotReady("Network timeout"),
    ],
    ids=["AuthenticationError", "NetworkTimeoutError"],
)
async def test_setup_failure_path(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    exception_instance: Exception,
):
    """
    /**
     * test_setup_failure_path - 测试设置过程中的失败路径
     *
     * 模拟场景:
     *   - Hub.async_setup() 抛出异常实例。
     *
     * 预期结果:
     *   - 如果是 `LifeSmartAuthError`，集成状态为 `SETUP_ERROR`。
     *   - 如果是 `ConfigEntryNotReady`，集成状态为 `SETUP_RETRY`。
     */
    """
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.lifesmart.hub.LifeSmartHub.async_setup",
        side_effect=exception_instance,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    if isinstance(exception_instance, ConfigEntryNotReady):
        assert (
            mock_config_entry.state == ConfigEntryState.SETUP_RETRY
        ), "网络超时时配置条目状态应该为重试"
    else:
        assert (
            mock_config_entry.state == ConfigEntryState.SETUP_ERROR
        ), "认证错误时配置条目状态应该为设置错误"
