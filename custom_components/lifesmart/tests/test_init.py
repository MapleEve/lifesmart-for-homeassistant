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
    ConfigEntry,
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

from custom_components.lifesmart import (
    data_update_handler,
    generate_unique_id,
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
)
from custom_components.lifesmart.exceptions import LifeSmartAuthError


# ====================================================================
# Section 1: 集成设置与卸载 (Setup and Unload)
# ====================================================================


@pytest.mark.asyncio
async def test_setup_and_unload_success_cloud_mode(
    hass: HomeAssistant, mock_client: MagicMock, mock_config_entry: MockConfigEntry
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
     *   - `LifeSmartStateManager` 应被创建并启动。
     *
     * 预期结果 (卸载后):
     *   - 集成状态应为 `NOT_LOADED`。
     *   - `hass.data[DOMAIN]` 中对应的 entry_id 被完全移除。
     *   - 所有后台任务被清理。
     */
    """
    mock_config_entry.add_to_hass(hass)

    with patch("custom_components.lifesmart.LifeSmartClient", return_value=mock_client):
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED
    entry_data = hass.data[DOMAIN][mock_config_entry.entry_id]
    assert entry_data["client"] == mock_client
    assert LIFESMART_STATE_MANAGER in entry_data
    assert isinstance(entry_data[LIFESMART_STATE_MANAGER], LifeSmartStateManager)

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED
    assert mock_config_entry.entry_id not in hass.data.get(DOMAIN, {})


@pytest.mark.asyncio
async def test_setup_success_local_mode(hass: HomeAssistant, mock_client: MagicMock):
    """
    /**
     * test_setup_success_local_mode - 测试本地模式下的成功设置流程
     *
     * 模拟场景:
     *   - 创建一个包含完整本地连接信息的 `MockConfigEntry`。
     *   - Patch `_async_create_client_and_get_devices` 以绕过真实的网络连接。
     *
     * 预期结果:
     *   - 集成状态应为 `LOADED`。
     *   - `local_task` 应被创建并存储在 `hass.data` 中。
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

    mock_task = asyncio.create_task(asyncio.sleep(0))
    with patch(
        "custom_components.lifesmart._async_create_client_and_get_devices",
        return_value=(mock_client, [], None, mock_task),
    ):
        assert await hass.config_entries.async_setup(mock_config_entry_local.entry_id)
        await hass.async_block_till_done()

    assert mock_config_entry_local.state == ConfigEntryState.LOADED
    entry_data = hass.data[DOMAIN][mock_config_entry_local.entry_id]
    assert entry_data["client"] == mock_client
    assert "local_task" in entry_data
    mock_task.cancel()  # 清理任务


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "exception_instance",
    [
        LifeSmartAuthError("Invalid credentials"),
        ConfigEntryNotReady("Network timeout"),
    ],
    ids=["auth_error", "not_ready"],
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
     *   - `_async_create_client_and_get_devices` 抛出异常实例。
     *
     * 预期结果:
     *   - 如果是 `LifeSmartAuthError`，集成状态为 `SETUP_ERROR`。
     *   - 如果是 `ConfigEntryNotReady`，集成状态为 `SETUP_RETRY`。
     */
    """
    mock_config_entry.add_to_hass(hass)

    with patch(
        "custom_components.lifesmart._async_create_client_and_get_devices",
        side_effect=exception_instance,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    if isinstance(exception_instance, ConfigEntryNotReady):
        assert mock_config_entry.state == ConfigEntryState.SETUP_RETRY
    else:
        assert mock_config_entry.state == ConfigEntryState.SETUP_ERROR


# ====================================================================
# Section 2: 数据更新处理器 (Data Update Handler)
# ====================================================================


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "raw_data, options, should_dispatch, expected_unique_id_suffix",
    [
        (
            {
                "type": "io",
                "msg": {"devtype": "SL_SW", "agt": "hub1", "me": "dev1", "idx": "L1"},
            },
            {},
            True,
            "sl_sw_hub1_dev1_l1",
        ),
        (
            {
                "type": "io",
                "msg": {"devtype": "SL_SW", "agt": "hub1", "me": "dev_ex", "idx": "L1"},
            },
            {CONF_EXCLUDE_ITEMS: "dev_ex,dev2"},
            False,
            None,
        ),
        (
            {
                "type": "io",
                "msg": {"devtype": "SL_SW", "agt": "hub_ex", "me": "dev1", "idx": "L1"},
            },
            {CONF_EXCLUDE_AGTS: "hub_ex"},
            False,
            None,
        ),
        (
            {
                "type": "io",
                "msg": {
                    "devtype": "SL_SCENE",
                    "agt": "hub_ai",
                    "me": "dev_ai",
                    "idx": "s",
                },
            },
            {CONF_AI_INCLUDE_AGTS: "hub_ai", CONF_AI_INCLUDE_ITEMS: "dev_ai"},
            False,
            None,
        ),
        (
            {
                "type": "io",
                "msg": {
                    "devtype": "SL_SCENE",
                    "agt": "hub_other",
                    "me": "dev_ai",
                    "idx": "s",
                },
            },
            {CONF_AI_INCLUDE_AGTS: "hub_ai", CONF_AI_INCLUDE_ITEMS: "dev_ai"},
            False,
            None,
        ),
        ({}, {}, False, None),
        ({"type": "io", "msg": {}}, {}, False, None),
    ],
    ids=[
        "standard",
        "excluded_dev",
        "excluded_hub",
        "ai_included",
        "ai_not_included",
        "empty_data",
        "empty_msg",
    ],
)
async def test_data_update_handler(
    hass: HomeAssistant,
    raw_data: dict,
    options: dict,
    should_dispatch: bool,
    expected_unique_id_suffix: str,
):
    """
    /**
     * test_data_update_handler - 全面测试数据更新处理器的过滤和分发逻辑
     */
    """
    mock_config_entry = MagicMock(spec=ConfigEntry)
    mock_config_entry.options = options

    with patch("custom_components.lifesmart.dispatcher_send") as mock_dispatcher:
        await data_update_handler(hass, mock_config_entry, raw_data)

        if should_dispatch:
            expected_signal = (
                f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{expected_unique_id_suffix}"
            )
            mock_dispatcher.assert_called_once_with(
                hass, expected_signal, raw_data["msg"]
            )
        else:
            mock_dispatcher.assert_not_called()


# ====================================================================
# Section 3: 唯一 ID 生成器 (Unique ID Generator)
# ====================================================================


@pytest.mark.parametrize(
    "devtype, agt, me, sub_key, expected_id",
    [
        ("SL_SW_IF1", "agt123", "dev456", "L1", "sl_sw_if1_agt123_dev456_l1"),
        ("SL_P_IR", "agt123", "dev789", None, "sl_p_ir_agt123_dev789"),
        (
            "SL_SW-WIN",
            "AzcAANOlBwADWFAEdTMyMQ/me",
            "MyDevice-01",
            "OP",
            "sl_swwin_azcaanolbwadwfaedtmymqme_mydevice01_op",
        ),
        ("", "agt1", "dev1", "L1", "_agt1_dev1_l1"),
    ],
    ids=["standard", "no_subkey", "special_chars", "empty_devtype"],
)
def test_generate_unique_id(
    devtype: str, agt: str, me: str, sub_key: str, expected_id: str
):
    """
    /**
     * test_generate_unique_id - 测试唯一 ID 生成函数的健壮性
     *
     * 模拟场景:
     *   - 输入各种合法的、包含特殊字符的、或为空的设备参数。
     *
     * 预期结果:
     *   - 函数应始终返回一个稳定、合法、小写的 unique_id。
     *   - 特殊字符（如 - 和 /）应被移除，符合 re.sub(r"\\W", "", ...) 的行为。
     */
    """
    assert generate_unique_id(devtype, agt, me, sub_key) == expected_id
