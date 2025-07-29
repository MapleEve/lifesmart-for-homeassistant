"""
共享的 pytest fixtures，用于 LifeSmart 集成测试。
"""

import asyncio
import json
import logging
import sys
import threading
from typing import Generator
from unittest.mock import AsyncMock, patch, MagicMock

import aiohttp
import pytest
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_REGION
from homeassistant.core import HomeAssistant, HassJob
from homeassistant.util.async_ import get_scheduled_timer_handles
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.lifesmart.const import *

_LOGGER = logging.getLogger(__name__)

sys.modules["aiodns"] = None

# 自动为所有测试加载 Home Assistant 的 pytest 插件
pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def verify_cleanup(
    event_loop: asyncio.AbstractEventLoop,
    expected_lingering_tasks: bool,
    expected_lingering_timers: bool,
) -> Generator[None, None, None]:
    """
    一个被覆盖的清理验证 fixture。

    1. 移除了对内部变量 'INSTANCES' 的脆弱依赖。
    2. 移除了导致导入错误的 'long_repr_strings' 上下文管理器。
    3. 在线程检查中断言中，明确允许名为 '_run_safe_shutdown_loop' 的线程存在，
       以解决顽固的线程泄露断言失败问题。
    """
    threads_before = frozenset(threading.enumerate())
    tasks_before = asyncio.all_tasks(event_loop)
    yield

    event_loop.run_until_complete(event_loop.shutdown_default_executor())

    # Warn and clean-up lingering tasks and timers
    # before moving on to the next test.
    tasks = asyncio.all_tasks(event_loop) - tasks_before
    for task in tasks:
        if expected_lingering_tasks:
            _LOGGER.warning("Lingering task after test %r", task)
        else:
            pytest.fail(f"Lingering task after test {task!r}")
        task.cancel()
    if tasks:
        event_loop.run_until_complete(asyncio.wait(tasks))

    for handle in get_scheduled_timer_handles(event_loop):
        if not handle.cancelled():
            if expected_lingering_timers:
                _LOGGER.warning("Lingering timer after test %r", handle)
            elif handle._args and isinstance(job := handle._args[-1], HassJob):
                if job.cancel_on_shutdown:
                    continue
                pytest.fail(f"Lingering timer after job {job!r}")
            else:
                pytest.fail(f"Lingering timer after test {handle!r}")
            handle.cancel()

    # Verify no threads where left behind.
    threads = frozenset(threading.enumerate()) - threads_before
    for thread in threads:
        assert (
            isinstance(thread, threading._DummyThread)
            or thread.name.startswith("waitpid-")
            or "_run_safe_shutdown_loop" in thread.name
        ), f"Leaked thread: {thread.name}"


# --- 统一的模拟配置 ---
@pytest.fixture(name="mock_config_data")
def mock_config_data_fixture():
    """提供标准的模拟配置数据。"""
    return {
        CONF_LIFESMART_APPKEY: "mock_appkey",
        CONF_LIFESMART_APPTOKEN: "mock_apptoken",
        CONF_LIFESMART_USERID: "mock_userid",
        CONF_LIFESMART_USERTOKEN: "mock_usertoken",
        CONF_REGION: "cn2",
    }


# --- 统一的模拟设备列表 ---
@pytest.fixture(name="mock_lifesmart_devices")
def mock_lifesmart_devices_fixture():
    """一个全面的模拟设备列表，覆盖所有平台的测试需求。"""
    return [
        # --- Switch Devices ---
        # 1. 标准三路开关 (SUPPORTED_SWITCH_TYPES)
        {
            "agt": "hub_sw",
            "me": "sw_if3",
            "devtype": "SL_SW_IF3",
            "name": "3-Gang Switch",
            "data": {"L1": {"type": 129}, "L2": {"type": 128}, "L3": {"type": 129}},
        },
        # 2. 普通插座 (SMART_PLUG_TYPES)
        {
            "agt": "hub_sw",
            "me": "sw_ol",
            "devtype": "SL_OL",
            "name": "Smart Outlet",
            "data": {"O": {"type": 129}},
        },
        # 3. 计量插座 (POWER_METER_PLUG_TYPES) - 位于被排除的 hub
        {
            "agt": "excluded_hub",
            "me": "sw_oe3c",
            "devtype": "SL_OE_3C",
            "name": "Power Plug",
            "data": {"P1": {"type": 129}, "P4": {"type": 128}},
        },
        # 4. 超能面板开关版 (SL_NATURE)
        {
            "agt": "hub_sw",
            "me": "sw_nature",
            "devtype": "SL_NATURE",
            "name": "Nature Panel Switch",
            "data": {
                "P1": {"type": 129},
                "P2": {"type": 128},
                "P3": {"type": 129},
                "P5": {"val": 1},
            },
        },
        # 5 通用控制器（三路开关模式）
        {
            "agt": "hub_sw",
            "me": "generic_p_switch_mode",
            "devtype": "SL_P",
            "name": "Generic Controller Switch",
            "data": {
                "P1": {"val": (8 << 24)},  # Mode 8: 3-way switch
                "P2": {"type": 129},
                "P3": {"type": 128},
                "P4": {"type": 129},
            },
        },
        # 6. 九路开关控制器 (SL_P_SW)
        {
            "agt": "hub_sw",
            "me": "sw_p9",
            "devtype": "SL_P_SW",
            "name": "9-Way Controller",
            "data": {
                "P1": {"type": 129},
                "P2": {"type": 128},
                "P3": {"type": 129},
                "P4": {"type": 128},
                "P5": {"type": 129},
                "P6": {"type": 128},
                "P7": {"type": 129},
                "P8": {"type": 128},
                "P9": {"type": 129},
                "P10": {"type": 128},
            },
        },
        # --- Light Devices ---
        # 1. BRIGHTNESS_LIGHT_TYPES -> SL_SPWM
        {
            "agt": "hub_light",
            "me": "light_bright",
            "devtype": "SL_SPWM",
            "name": "Brightness Light",
            "data": {"P1": {"type": 129, "val": 100}},
        },
        # 2. LIGHT_DIMMER_TYPES -> SL_LI_WW_V2
        {
            "agt": "hub_light",
            "me": "light_dimmer",
            "devtype": "SL_LI_WW_V2",
            "name": "Dimmer Light",
            "data": {"P1": {"type": 129, "val": 100}, "P2": {"val": 27}},
        },
        # 3. QUANTUM_TYPES -> OD_WE_QUAN
        {
            "agt": "hub_light",
            "me": "light_quantum",
            "devtype": "OD_WE_QUAN",
            "name": "Quantum Light",
            "data": {"P1": {"type": 129, "val": 100}, "P2": {"val": 0x01010203}},
        },
        # 4. RGB_LIGHT_TYPES -> SL_SC_RGB
        {
            "agt": "hub_light",
            "me": "light_singlergb",
            "devtype": "SL_SC_RGB",
            "name": "Single IO RGB Light",
            "data": {"RGB": {"type": 129, "val": 0x64010203}},
        },
        # 5. RGBW_LIGHT_TYPES -> SL_CT_RGBW
        {
            "agt": "hub_light",
            "me": "light_dualrgbw",
            "devtype": "SL_CT_RGBW",
            "name": "Dual IO RGBW Light",
            "data": {"RGBW": {"type": 129, "val": 0}, "DYN": {"type": 128}},
        },
        # 6. SPOT_TYPES -> SL_SPOT (RGB)
        {
            "agt": "hub_light",
            "me": "light_spotrgb",
            "devtype": "SL_SPOT",
            "name": "SPOT RGB Light",
            "data": {"RGB": {"type": 129, "val": 0xFF8040}},
        },
        # 7. SPOT_TYPES -> MSL_IRCTL (RGBW)
        {
            "agt": "hub_light",
            "me": "light_spotrgbw",
            "devtype": "MSL_IRCTL",
            "name": "SPOT RGBW Light",
            "data": {
                "RGBW": {"type": 129, "val": 0x11223344},
                "DYN": {"type": 129, "val": DYN_EFFECT_MAP["海浪"]},
            },
        },
        # 8. GARAGE_DOOR_TYPES -> SL_ETDOOR
        {
            "agt": "hub_light",
            "me": "light_cover",
            "devtype": "SL_ETDOOR",
            "name": "Cover Light",
            "data": {"P1": {"type": 129}},
        },
        # 9. LIGHT_SWITCH_TYPES -> SL_OL_W
        {
            "agt": "hub_light",
            "me": "light_switch",
            "devtype": "SL_OL_W",
            "name": "Wall Outlet Light",
            "data": {"P1": {"type": 129}},
        },
        # 10. LIGHT_BULB_TYPES -> SL_LI_BL
        {
            "agt": "hub_light",
            "me": "light_bulb",
            "devtype": "SL_LI_BL",
            "name": "Simple Bulb",
            "data": {"P1": {"type": 128}},
        },
        # 11. OUTDOOR_LIGHT_TYPES -> SL_LI_UG1
        {
            "agt": "hub_light",
            "me": "light_outdoor",
            "devtype": "SL_LI_UG1",
            "name": "Outdoor Light",
            "data": {"P1": {"type": 129, "val": 0x64010203}},
        },
        # --- Binary Sensor Devices ---
        {
            "agt": "hub_bs",
            "me": "bs_door",
            "devtype": "SL_SC_G",
            "name": "Front Door",
            "data": {"G": {"val": 0, "type": 0}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_motion",
            "devtype": "SL_SC_MHW",
            "name": "Living Motion",
            "data": {"M": {"val": 1, "type": 0}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_water",
            "devtype": "SL_SC_WA",
            "name": "Kitchen Water",
            "data": {"WA": {"val": 50, "type": 0}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_defed",
            "devtype": "SL_DF_MM",
            "name": "Garage DEFED",
            "data": {"M": {"val": 1, "type": 129}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_lock",
            "devtype": "SL_LK_LS",
            "name": "Main Lock",
            "data": {"EVTLO": {"val": 4121, "type": 1}, "ALM": {"val": 2}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_smoke",
            "devtype": "SL_P_A",
            "name": "Hallway Smoke",
            "data": {"P1": {"val": 1, "type": 0}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_radar",
            "devtype": "SL_P_RM",
            "name": "Study Occupancy",
            "data": {"P1": {"val": 1, "type": 0}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_button",
            "devtype": "SL_SC_BB_V2",
            "name": "Panic Button",
            "data": {"P1": {"val": 0, "type": 0}},
        },
        # --- Sensor Devices ---
        {
            "agt": "hub_sensor",
            "me": "sensor_env",
            "devtype": "SL_SC_THL",
            "name": "Living Room Env",
            "data": {
                "T": {"v": 25.5},
                "H": {"v": 60.1},
                "Z": {"v": 1000},
                "V": {"val": 95},
            },
        },
        {
            "agt": "hub_sensor",
            "me": "sensor_co2",
            "devtype": "SL_SC_CA",
            "name": "Study CO2",
            "data": {"P3": {"val": 800}},
        },
        {
            "agt": "hub_sensor",
            "me": "sensor_power_plug",
            "devtype": "SL_OE_3C",
            "name": "Washing Machine Plug",
            "data": {"P2": {"v": 1.5}, "P3": {"v": 1200}},
        },
        {
            "agt": "hub_sensor",
            "me": "sensor_lock_battery",
            "devtype": "SL_LK_LS",
            "name": "Main Door Lock",
            "data": {"BAT": {"val": 88}},
        },
        {
            "agt": "hub_sensor",
            "me": "sensor_boundary",
            "devtype": "SL_SC_THL",
            "name": "Boundary Test Sensor",
            "data": {
                "T": {"val": 0},  # Zero value
                "H": {},  # Empty data
                "Z": {"val": "invalid_string"},  # Invalid data type
                # 'V' key is completely missing
            },
        },
        # --- Cover Devices ---
        {
            "agt": "hub_cover",
            "me": "cover_garage",
            "devtype": "SL_ETDOOR",
            "name": "Garage Door",
            "data": {"P2": {"val": 0, "type": 128}},
        },
        {
            "agt": "hub_cover",
            "me": "cover_dooya",
            "devtype": "SL_DOOYA",
            "name": "Living Room Curtain",
            "data": {"P1": {"val": 100, "type": 128}},
        },
        {
            "agt": "hub_cover",
            "me": "cover_nonpos",
            "devtype": "SL_SW_WIN",
            "name": "Bedroom Curtain",
            "data": {"OP": {"type": 128}, "CL": {"type": 128}, "ST": {"type": 128}},
        },
        {
            "agt": "hub_cover",
            "me": "cover_generic",
            "devtype": "SL_P",
            "name": "Generic Controller Curtain",
            "data": {
                "P1": {"val": (2 << 24)},
                "P2": {"type": 128},
                "P3": {"type": 128},
                "P4": {"type": 128},
            },
        },
        # --- Climate Devices ---
        {
            "agt": "hub_climate",
            "me": "climate_nature_thermo",
            "devtype": "SL_NATURE",
            "name": "Nature Panel Thermo",
            "data": {
                "P1": {"type": 129, "val": 1},  # On
                "P4": {"v": 28.0},  # Current Temp
                "P5": {"val": 3},  # 关键：标识为温控面板
                "P6": {"val": (4 << 6)},  # CFG, 4 -> ⻛机盘管（双阀）模式
                "P7": {"val": 1},  # Mode, 1 -> Auto
                "P8": {"v": 26.0},  # Target Temp
                "P10": {"val": 15},  # Fan Speed, 15 -> Low
            },
        },
        {
            "agt": "hub_climate",
            "me": "climate_floor_heat",
            "devtype": "SL_CP_DN",
            "name": "Floor Heating",
            "data": {
                "P1": {"type": 1, "val": 2147483648},
                "P3": {"v": 25.0},
                "P4": {"v": 22.5},
            },
        },
        {
            "agt": "hub_climate",
            "me": "climate_fancoil",
            "devtype": "SL_CP_AIR",
            "name": "Fan Coil Unit",
            "data": {
                "P1": {"type": 1, "val": (1 << 15) | (1 << 13)},
                "P4": {"v": 24.0},
                "P5": {"v": 26.0},
            },
        },
        {
            "agt": "hub_climate",
            "me": "climate_airpanel",
            "devtype": "V_AIR_P",
            "name": "Air Panel",
            "data": {
                "O": {"type": 0},
                "MODE": {"val": 1},
                "F": {"val": 2},
                "T": {"v": 23.0},
                "tT": {"v": 25.0},
            },
        },
        {
            "agt": "hub_climate",
            "me": "climate_airsystem",
            "devtype": "SL_TR_ACIPM",
            "name": "Air System",
            "data": {"P1": {"type": 1, "val": 1}},
        },
        # --- Devices for Exclusion/Special Tests ---
        {
            "agt": "hub_bs",
            "me": "excluded_device",
            "devtype": "SL_SC_G",
            "name": "Excluded Sensor",
            "data": {"G": {"v": 20}},
        },
        {
            "agt": "excluded_hub",
            "me": "device_on_excluded_hub",
            "devtype": "SL_SC_THL",
            "name": "Sensor on Excluded Hub",
            "data": {"T": {"v": 21}},
        },
    ]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """自动为所有测试启用自定义组件集成。"""
    yield


@pytest.fixture
def mock_client(mock_lifesmart_devices):
    """
    提供一个默认的、配置了模拟设备的模拟 LifeSmartClient。
    """
    with patch(
        "custom_components.lifesmart.LifeSmartClient", autospec=True
    ) as mock_client_class:
        client_instance = mock_client_class.return_value
        client_instance.get_all_device_async.return_value = mock_lifesmart_devices
        client_instance.login_async = AsyncMock(
            return_value={
                "usertoken": "mock_new_usertoken",
                "userid": "mock_userid",
                "region": "cn2",
            }
        )
        client_instance.async_refresh_token = AsyncMock(
            return_value={
                "usertoken": "mock_refreshed_usertoken",
                "expiredtime": 9999999999,
            }
        )

        # 模拟所有控制方法
        client_instance.turn_on_light_switch_async = AsyncMock(return_value=0)
        client_instance.turn_off_light_switch_async = AsyncMock(return_value=0)
        client_instance.set_single_ep_async = AsyncMock(return_value=0)
        client_instance.set_multi_eps_async = AsyncMock(return_value=0)
        client_instance.open_cover_async = AsyncMock(return_value=0)
        client_instance.close_cover_async = AsyncMock(return_value=0)
        client_instance.stop_cover_async = AsyncMock(return_value=0)
        client_instance.set_cover_position_async = AsyncMock(return_value=0)
        client_instance.async_set_climate_hvac_mode = AsyncMock(return_value=0)
        client_instance.async_set_climate_fan_mode = AsyncMock(return_value=0)
        client_instance.async_set_climate_temperature = AsyncMock(return_value=0)
        client_instance.get_wss_url.return_value = "wss://example.com/ws"

        # 模拟后台任务启动/停止
        client_instance.ws_connect = AsyncMock()
        client_instance.ws_disconnect = AsyncMock()

    yield client_instance


@pytest.fixture
def mock_config_entry(mock_config_data) -> MockConfigEntry:
    """提供一个模拟的 ConfigEntry 实例。"""
    return MockConfigEntry(
        domain=DOMAIN,
        data=mock_config_data,
        entry_id="mock_entry_id_12345",
        title="LifeSmart Mock",
        options={
            CONF_EXCLUDE_ITEMS: "excluded_device",
            CONF_EXCLUDE_AGTS: "excluded_hub",
        },
    )


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_lifesmart_devices: list,
):
    """
    一个统一的 fixture，用于完整地设置和加载 LifeSmart 集成及其所有平台。
    """
    mock_config_entry.add_to_hass(hass)
    mock_client.get_all_device_async.return_value = mock_lifesmart_devices

    with patch(
        "custom_components.lifesmart.LifeSmartClient",
        return_value=mock_client,
    ), patch(
        "aiohttp.ClientSession.ws_connect", new_callable=AsyncMock
    ) as mock_ws_connect:
        mock_ws = mock_ws_connect.return_value

        # 模拟一个稳定、认证后无限期挂起的 WebSocket 连接
        auth_response_msg = MagicMock(spec=aiohttp.WSMessage)
        auth_response_msg.type = aiohttp.WSMsgType.TEXT
        auth_response_msg.data = json.dumps({"code": 0, "message": "success"})

        async def mock_receive_logic(*args, **kwargs):
            # 第一次调用返回认证成功
            if mock_ws.receive.call_count == 1:
                return auth_response_msg
            # 后续调用无限期挂起，直到被取消
            await asyncio.sleep(3600)

        mock_ws.receive.side_effect = mock_receive_logic
        mock_ws.send_str = AsyncMock()
        mock_ws.close = AsyncMock()

        # 设置并加载集成
        assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # 验证集成已成功加载
    assert mock_config_entry.state == ConfigEntryState.LOADED

    # 将控制权交给测试用例
    yield mock_config_entry

    # 在卸载之前，手动检查并取消任何可能由本地连接测试遗留的后台任务
    entry_id = mock_config_entry.entry_id
    if (
        DOMAIN in hass.data
        and entry_id in hass.data[DOMAIN]
        and (local_task := hass.data[DOMAIN][entry_id].get("local_task"))
    ):
        if not local_task.done():
            local_task.cancel()
            # 等待任务实际被取消
            await asyncio.sleep(0)

    # 卸载集成
    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # 验证集成已成功卸载
    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED
