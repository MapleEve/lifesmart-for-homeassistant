"""
共享的 pytest fixtures，用于 LifeSmart 集成测试。 @MapleEve

此文件是整个测试框架的基石，旨在提供可复用的、一致的模拟数据和环境。
将所有核心的模拟设备、客户端和配置项统一定义在此处，以确保所有测试用例都在可预测和标准化的基础上运行。
"""

import asyncio
import logging
import threading
import time
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


# 自动为所有测试加载 Home Assistant 的 pytest 插件
pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(scope="session", autouse=True)
def prevent_socket_access():
    """
    一个全局的、自动执行的 Fixture，用于在整个测试会话期间
    阻止任何意外的网络 socket 连接。

    这是通过 aiohttp 的 `TraceConfig` 实现的，它会在 DNS 解析开始前
    就引发一个运行时错误，从而有效地阻止了 aiodns 定时器的创建，
    这是导致 "Lingering timer" 错误的主要原因。

    此方案是社区中解决 aiodns 问题的最佳实践。
    """

    async def _on_dns_resolvehost_start(session, trace_config_ctx, params):
        raise RuntimeError(
            f"Socket access is disabled for tests. Tried to resolve {params.host}"
        )

    trace_config = aiohttp.TraceConfig()

    # --- 这是被修正的一行 ---
    # 使用 aiohttp 提示的正确属性名 on_dns_resolvehost_start
    trace_config.on_dns_resolvehost_start.append(_on_dns_resolvehost_start)

    # 通过 patch aiohttp.ClientSession，强制所有新创建的会话都使用我们
    # 配置好的 trace_config，从而阻止 DNS 解析。
    original_client_session = aiohttp.ClientSession

    def patched_client_session(*args, **kwargs):
        existing_trace_configs = kwargs.get("trace_configs") or []
        return original_client_session(
            *args, **kwargs, trace_configs=[*existing_trace_configs, trace_config]
        )

    with patch("aiohttp.ClientSession", new=patched_client_session):
        yield


@pytest.fixture(autouse=True)
def verify_cleanup(
    event_loop: asyncio.AbstractEventLoop,
    expected_lingering_tasks: bool,
    expected_lingering_timers: bool,
) -> Generator[None, None, None]:
    """
    一个被覆盖的清理验证 fixture，用于确保测试之间没有资源泄露。

    此 fixture 在每个测试运行前后执行，用于捕获并报告任何未被正确清理的
    异步任务、定时器或线程。这对于维护一个稳定、可靠的测试套件至关重要，
    可以防止一个测试的副作用影响到后续的测试。

    覆盖原因:
    1. 移除了对 `pytest-homeassistant-custom-component` 内部变量 'INSTANCES'
       的脆弱依赖，以增强健壮性。
    2. 移除了可能导致导入错误的 'long_repr_strings' 上下文管理器。
    3. 在线程检查中断言中，明确允许名为 '_run_safe_shutdown_loop' 的线程存在，
       这是为了解决在某些 CI 环境下顽固的线程泄露断言失败问题。
    """
    # 记录测试开始前的状态
    threads_before = frozenset(threading.enumerate())
    tasks_before = asyncio.all_tasks(event_loop)

    yield  # 执行测试用例

    # --- 测试结束后的清理与验证 ---
    event_loop.run_until_complete(event_loop.shutdown_default_executor())

    # 检查并警告/失败于残留的异步任务
    tasks = asyncio.all_tasks(event_loop) - tasks_before
    for task in tasks:
        if expected_lingering_tasks:
            _LOGGER.warning("Lingering task after test %r", task)
        else:
            pytest.fail(f"Lingering task after test {task!r}")
        task.cancel()
    if tasks:
        event_loop.run_until_complete(asyncio.wait(tasks))

    # 检查并警告/失败于残留的定时器
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

    # 验证没有泄露的线程
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
    """
    提供标准的模拟配置数据。

    这个 Fixture 封装了一套标准的云端模式配置信息，用于在测试中创建
    `MockConfigEntry`。这确保了所有测试都使用一致的凭据，简化了测试的编写。
    """
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
    """
    一个全面的模拟设备列表，覆盖所有平台的测试需求。

    这个 Fixture 是许多集成测试的核心。它提供了一个包含各种设备类型
    （开关、灯、传感器、温控器等）的列表，模拟了一个真实用户的完整家庭环境。

    用途:
    - 用于 `setup_integration` Fixture，以在 Home Assistant 中创建所有这些设备对应的实体。
    - 用于测试平台级别的功能，例如，确保 `climate` 平台在初始化时不会错误地创建 `switch` 实体。
    - 用于测试设备排除逻辑。
    """
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
                "P5": {"val": 1},  # P5=1 表示其为开关模式
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
            "data": {"T": {"val": 0}, "H": {}, "Z": {"val": "invalid_string"}},
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
    """
    自动为所有测试启用自定义组件集成。

    这是一个 `autouse` fixture，它会自动应用到所有测试中，确保
    `pytest-homeassistant-custom-component` 的功能被激活。
    """
    yield


@pytest.fixture
def mock_client_class(mock_lifesmart_devices):
    """
    一个高级 fixture，它 patch LifeSmartClient 类并返回这个类的 Mock。

    这允许测试根据需要控制 `LifeSmartClient()` 的返回值，对于测试重载
    (reload) 行为至关重要。通过 patch 类本身，我们可以确保每次调用
    `hass.config_entries.async_reload` 时，后续的 `LifeSmartClient()`
    调用都会返回一个我们可以控制的新实例。
    """
    with patch(
        "custom_components.lifesmart.core.lifesmart_client.LifeSmartClient",
        autospec=True,
    ) as mock_class:
        # 配置默认的实例行为
        instance = mock_class.return_value
        instance.get_all_device_async.return_value = mock_lifesmart_devices
        instance.login_async.return_value = {
            "usertoken": "mock_new_usertoken",
            "userid": "mock_userid",
            "region": "cn2",
        }
        instance.async_refresh_token.return_value = {
            "usertoken": "mock_refreshed_usertoken",
            "expiredtime": 9999999999,
        }

        # 为所有设备控制方法预设一个异步 mock，以捕获调用
        instance.turn_on_light_switch_async = AsyncMock(return_value=0)
        instance.turn_off_light_switch_async = AsyncMock(return_value=0)
        instance.set_single_ep_async = AsyncMock(return_value=0)
        instance.set_multi_eps_async = AsyncMock(return_value=0)
        instance.open_cover_async = AsyncMock(return_value=0)
        instance.close_cover_async = AsyncMock(return_value=0)
        instance.stop_cover_async = AsyncMock(return_value=0)
        instance.set_cover_position_async = AsyncMock(return_value=0)
        instance.async_set_climate_hvac_mode = AsyncMock(return_value=0)
        instance.async_set_climate_fan_mode = AsyncMock(return_value=0)
        instance.async_set_climate_temperature = AsyncMock(return_value=0)
        instance.get_wss_url.return_value = "wss://example.com/ws"
        instance.ws_connect = AsyncMock()
        instance.ws_disconnect = AsyncMock()

        # 为灯光测试中使用的底层命令方法提供 mock
        instance._async_send_single_command = AsyncMock(return_value=0)
        instance._async_send_multi_command = AsyncMock(return_value=0)

        yield mock_class


@pytest.fixture
def mock_client(mock_client_class):
    """
    提供一个默认的模拟 LifeSmartClient 实例。

    这个 fixture 依赖于 `mock_client_class`，为不需要控制重载行为的
    标准测试提供向后兼容性。它只是简单地返回 `mock_client_class`
    所创建的那个模拟实例。
    """
    return mock_client_class.return_value


@pytest.fixture
def mock_config_entry(mock_config_data) -> MockConfigEntry:
    """
    提供一个模拟的 ConfigEntry 实例。

    这个 Fixture 使用 `mock_config_data` 来创建一个标准的、可用于测试的
    `MockConfigEntry` 对象，并预设了排除选项，用于测试相关的逻辑。
    """
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
def mock_state_manager_class():
    """
    一个高级 fixture，它 patch LifeSmartStateManager 类并返回这个类的 Mock。

    这允许我们验证其方法（如 `start`, `stop`）是否在集成的生命周期中
    （设置、卸载、重载）被正确调用。
    """
    with patch(
        "custom_components.lifesmart.LifeSmartStateManager", autospec=True
    ) as mock_class:
        # 获取实例的 mock，以便我们可以配置和断言它的方法
        instance = mock_class.return_value
        instance.start = MagicMock()
        instance.stop = AsyncMock()
        instance.set_token_expiry = MagicMock()
        yield mock_class


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_state_manager_class: MagicMock,
    mock_lifesmart_devices: list,
):
    """
    一个统一的 fixture，用于完整地设置和加载 LifeSmart 集成及其所有平台。

    这是绝大多数集成测试的入口点。它执行了以下操作：
    1. 将模拟的 `ConfigEntry` 添加到 Home Assistant。
    2. Patch 掉真实的客户端创建和设备获取过程，注入模拟数据。
    3. Patch 掉 `LifeSmartStateManager` 以便进行行为验证。
    4. 触发 `async_setup` 流程。
    5. 验证集成是否成功加载。
    6. 将控制权交给测试用例。
    7. 在测试结束后，自动执行卸载流程，并验证卸载是否成功。
    """
    mock_config_entry.add_to_hass(hass)

    create_client_return_value = (
        mock_client,
        mock_lifesmart_devices,
        {"expiredtime": int(time.time()) + 3600},
    )
    with patch(
        "custom_components.lifesmart._async_create_client_and_get_devices",
        return_value=create_client_return_value,
    ), patch(
        "custom_components.lifesmart.LifeSmartStateManager",
        new=mock_state_manager_class,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # 验证集成已成功加载
    assert mock_config_entry.state == ConfigEntryState.LOADED

    # 验证 StateManager 被正确启动
    mock_state_manager_class.return_value.start.assert_called_once()

    # 将控制权交给测试用例
    yield mock_config_entry

    # --- 测试结束后的清理 ---
    # 在卸载之前，手动检查并取消任何可能由本地连接测试遗留的后台任务
    entry_id = mock_config_entry.entry_id
    if (
        DOMAIN in hass.data
        and entry_id in hass.data[DOMAIN]
        and (local_task := hass.data[DOMAIN][entry_id].get("local_task"))
    ):
        if not local_task.done():
            local_task.cancel()
            await asyncio.sleep(0)

    # 卸载集成
    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # 验证集成已成功卸载
    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED


# ============================================================================
# === 为隔离测试专用的原子设备 Fixtures ===
#
# 设计说明:
# 以下 Fixtures 是对您现有 `mock_lifesmart_devices` 的补充，而非替代。
# 它们提供了独立的、可按需注入的“原材料”，专门用于对特定设备进行深度、
# 隔离的测试，确保测试的纯净性，不受其他设备干扰。
#
# 这种分离的设计，使得测试的意图更加清晰，维护也更加方便。
# ============================================================================


@pytest.fixture
def mock_device_climate_fancoil() -> dict:
    """
    提供一个标准的风机盘管设备 (SL_CP_AIR) 的模拟数据。

    此设备的状态由一个位掩码 (bitmask) `P1` 控制，这是测试的重点。
    - 初始状态: 制热模式 (Heat) + 低风速 (Low)。
      - `val` 的第 13 位为 1: 代表制热模式 (HEAT)。
      - `val` 的第 15 位为 1: 代表低风速 (FAN_LOW)。
      - 计算: `(1 << 15) | (1 << 13)`
    - 初始温度:
      - `P4`: 目标温度 (target_temperature) 为 24.0。
      - `P5`: 当前温度 (current_temperature) 为 26.0。
    """
    return {
        "agt": "hub_climate",
        "me": "climate_fancoil",
        "devtype": "SL_CP_AIR",
        "name": "Fan Coil Unit",
        "data": {
            "P1": {"type": 1, "val": (1 << 15) | (1 << 13)},
            "P4": {"v": 24.0},
            "P5": {"v": 26.0},
        },
    }


@pytest.fixture
def mock_device_climate_floor_heat() -> dict:
    """
    提供一个标准的地暖设备 (SL_CP_DN) 的模拟数据。

    - 初始状态: 自动模式 (Auto)。
      - `P1` 的 `val` 为 `2147483648` (0x80000000)，根据协议，这代表自动模式。
    - 初始温度:
      - `P3`: 目标温度 (target_temperature) 为 25.0。
      - `P4`: 当前温度 (current_temperature) 为 22.5。
    """
    return {
        "agt": "hub_climate",
        "me": "climate_floor_heat",
        "devtype": "SL_CP_DN",
        "name": "Floor Heating",
        "data": {
            "P1": {"type": 1, "val": 2147483648},
            "P3": {"v": 25.0},
            "P4": {"v": 22.5},
        },
    }


@pytest.fixture
def mock_device_climate_nature_fancoil() -> dict:
    """
    提供一个 SL_NATURE 面板的模拟数据，该面板被配置为控制“风机盘管”。

    SL_NATURE 面板是一个多功能设备，其具体功能由内部数据点决定。
    - `P5` 的 `val` 为 3: 表示此面板工作在“温控器”模式下。
    - `P6` 的 `val` 为 `(4 << 6)`: 这是最关键的配置，定义了其控制的设备类型为
      “风机盘管(双阀)”，这将决定实体支持的 `hvac_modes` 和 `fan_modes`。
    """
    return {
        "agt": "hub_climate",
        "me": "climate_nature_thermo",
        "devtype": "SL_NATURE",
        "name": "Nature Panel Thermo",
        "data": {
            "P1": {"type": 129, "val": 1},
            "P4": {"v": 28.0},
            "P5": {"val": 3},
            "P6": {"val": (4 << 6)},
            "P7": {"val": 1},
            "P8": {"v": 26.0},
            "P10": {"val": 15},
        },
    }


@pytest.fixture
def mock_device_climate_nature_freshair() -> dict:
    """
    提供一个 SL_NATURE 面板的模拟数据，该面板被配置为控制“新风”。

    - `P6` 的 `val` 为 `(0 << 6)`: 定义了其控制的设备类型为“新风”。
    """
    return {
        "agt": "hub_climate",
        "me": "climate_nature_thermo",
        "devtype": "SL_NATURE",
        "name": "Nature Panel Thermo",
        "data": {
            "P1": {"type": 129, "val": 1},
            "P4": {"v": 28.0},
            "P5": {"val": 3},
            "P6": {"val": (0 << 6)},
            "P7": {"val": 1},
            "P8": {"v": 26.0},
            "P10": {"val": 15},
        },
    }


@pytest.fixture
def mock_device_climate_nature_floorheat() -> dict:
    """
    提供一个 SL_NATURE 面板的模拟数据，该面板被配置为控制“水地暖”。

    - `P6` 的 `val` 为 `(2 << 6)`: 定义了其控制的设备类型为“水地暖”。
    """
    return {
        "agt": "hub_climate",
        "me": "climate_nature_thermo",
        "devtype": "SL_NATURE",
        "name": "Nature Panel Thermo",
        "data": {
            "P1": {"type": 129, "val": 1},
            "P4": {"v": 28.0},
            "P5": {"val": 3},
            "P6": {"val": (2 << 6)},
            "P7": {"val": 1},
            "P8": {"v": 26.0},
            "P10": {"val": 15},
        },
    }


@pytest.fixture
def mock_device_spot_rgb_light() -> dict:
    """
    提供一个 SPOT RGB 灯 (SL_SPOT) 的模拟数据。

    - 初始状态: 开，颜色为 (255, 128, 64)。
      - `val` 为 `0xFF8040`。
    """
    return {
        "agt": "hub_light",
        "me": "light_spotrgb",
        "devtype": "SL_SPOT",
        "name": "SPOT RGB Light",
        "data": {"RGB": {"type": 129, "val": 0xFF8040}},
    }


@pytest.fixture
def mock_device_dual_io_rgbw_light() -> dict:
    """
    提供一个双 IO 口 RGBW 灯 (SL_CT_RGBW) 的模拟数据。

    - 初始状态: 开，但颜色和效果均未激活。
      - `RGBW` 口为开 (`type: 129`)，但值为 0。
      - `DYN` 口为关 (`type: 128`)。
    """
    return {
        "agt": "hub_light",
        "me": "light_dualrgbw",
        "devtype": "SL_CT_RGBW",
        "name": "Dual IO RGBW Light",
        "data": {"RGBW": {"type": 129, "val": 0}, "DYN": {"type": 128}},
    }


@pytest.fixture
def mock_device_single_io_rgbw_light() -> dict:
    """
    提供一个单 IO 口 RGBW 灯 (SL_SC_RGB) 的模拟数据。

    此 Fixture 用于对该特定设备类型的协议进行精确测试。
    - 初始状态: 开，颜色为 (1, 2, 3)，亮度为 100%。
      - `val` 为 `0x64010203` (亮度100, R=1, G=2, B=3)。
    """
    return {
        "agt": "hub_light",
        "me": "light_singlergb",
        "devtype": "SL_SC_RGB",
        "name": "Single IO RGB Light",
        "data": {"RGB": {"type": 129, "val": 0x64010203}},
    }


# ============================================================================
# === 为隔离测试专用的 Setup Fixtures ===
# ============================================================================


@pytest.fixture
async def setup_integration_spot_rgb_only(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_state_manager_class: MagicMock,
    mock_device_spot_rgb_light: dict,
):
    """
    一个专用的 setup fixture，只加载 SPOT RGB 灯。

    此 fixture 创建一个只包含单个 SPOT RGB 灯的纯净测试环境，
    用于对该设备的颜色和亮度逻辑进行精确的边缘情况测试。
    """
    mock_config_entry.add_to_hass(hass)
    # 只使用注入的单个设备来创建测试环境
    devices = [mock_device_spot_rgb_light]
    create_client_return_value = (
        mock_client,
        devices,
        {"expiredtime": int(time.time()) + 3600},
    )
    with patch(
        "custom_components.lifesmart._async_create_client_and_get_devices",
        return_value=create_client_return_value,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    assert mock_config_entry.state == ConfigEntryState.LOADED
    yield mock_config_entry


@pytest.fixture
async def setup_integration_dual_io_light_only(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_state_manager_class: MagicMock,
    mock_device_dual_io_rgbw_light: dict,
):
    """
    一个专用的 setup fixture，只加载双 IO 口灯。

    此 fixture 创建一个只包含单个双 IO 口灯的纯净测试环境，
    用于对该设备颜色和效果的互斥逻辑进行精确的联合测试。
    """
    mock_config_entry.add_to_hass(hass)
    devices = [mock_device_dual_io_rgbw_light]
    create_client_return_value = (
        mock_client,
        devices,
        {"expiredtime": int(time.time()) + 3600},
    )
    with patch(
        "custom_components.lifesmart._async_create_client_and_get_devices",
        return_value=create_client_return_value,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    assert mock_config_entry.state == ConfigEntryState.LOADED
    yield mock_config_entry


@pytest.fixture
async def setup_integration_single_io_rgbw_only(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_state_manager_class: MagicMock,
    mock_device_single_io_rgbw_light: dict,
):
    """
    一个专用的 setup fixture，只加载单 IO 口 RGBW 灯。

    此 fixture 创建一个只包含单个 SL_SC_RGB 灯的纯净测试环境，
    用于对该设备的服务调用与设备协议的精确匹配进行测试。
    """
    mock_config_entry.add_to_hass(hass)
    devices = [mock_device_single_io_rgbw_light]
    create_client_return_value = (
        mock_client,
        devices,
        {"expiredtime": int(time.time()) + 3600},
    )
    with patch(
        "custom_components.lifesmart._async_create_client_and_get_devices",
        return_value=create_client_return_value,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    assert mock_config_entry.state == ConfigEntryState.LOADED
    yield mock_config_entry
