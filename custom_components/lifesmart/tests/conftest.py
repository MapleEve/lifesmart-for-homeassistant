"""
共享的 pytest fixtures，用于 LifeSmart 集成测试。 @MapleEve

此文件是整个测试框架的基石，旨在提供可复用的、一致的模拟数据和环境。
将所有核心的模拟设备、客户端和配置项统一定义在此处，以确保所有测试用例都在可预测和标准化的基础上运行。
"""

import logging
from unittest.mock import AsyncMock, patch, MagicMock

import aiohttp
import pytest
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.lifesmart.const import (
    DOMAIN,
    CONF_EXCLUDE_ITEMS,
    CONF_EXCLUDE_AGTS,
)

_LOGGER = logging.getLogger(__name__)


# 设置兼容性支持
from custom_components.lifesmart.compatibility import setup_logging

setup_logging()


@pytest.fixture(scope="session", autouse=True)
def prevent_socket_access():
    """
    一个全局的、自动执行的 Fixture，用于在整个测试会话期间
    阻止任何意外的网络 socket 连接。

    这是通过 aiohttp 的 `TraceConfig` 实现的，它会在 DNS 解析开始前
    就引发一个运行时错误，从而有效地阻止了 aiodns 定时器的创建，
    这是导致 "Lingering timer" 错误的主要原因。

    注意：这个fixture是GH CI必需的，不能删除。
    """

    async def _on_dns_resolvehost_start(session, trace_config_ctx, params):
        raise RuntimeError(
            f"Socket access is disabled for tests. Tried to resolve {params.host}"
        )

    trace_config = aiohttp.TraceConfig()

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
def expected_lingering_timers() -> bool:
    """
    为旧版本HA提供兼容性：允许定时器残留以避免兼容性问题。

    这是因为旧版本HA (如2024.2.0及以下) 没有提供get_scheduled_timer_handles函数，
    而pytest-homeassistant-custom-component插件的verify_cleanup directly访问loop._scheduled，
    这可能在某些情况下导致测试性能问题。

    通过返回True，我们允许定时器残留，让插件的verify_cleanup只是警告而不是失败。
    """
    try:
        # 检查是否有新版本的定时器处理函数
        from homeassistant.util.async_ import get_scheduled_timer_handles

        # 新版本HA有官方支持，可以进行严格检查
        return False
    except ImportError:
        # 旧版本HA没有官方支持，允许定时器残留以避免兼容性问题
        return True


# --- 统一的模拟配置 ---
@pytest.fixture(name="mock_config_data")
def mock_config_data_fixture():
    """
    提供标准的模拟配置数据。

    这个 Fixture 封装了一套标准的云端模式配置信息，用于在测试中创建
    `MockConfigEntry`。这确保了所有测试都使用一致的凭据，简化了测试的编写。
    """
    from .test_utils import create_mock_config_data

    return create_mock_config_data()


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
    from .test_utils import create_mock_lifesmart_devices

    return create_mock_lifesmart_devices()


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
    一个高级 fixture，它 patch LifeSmartOAPIClient 类并返回这个类的 Mock。

    这允许测试根据需要控制 `LifeSmartOAPIClient()` 的返回值，对于测试重载
    (reload) 行为至关重要。通过 patch 类本身，我们可以确保每次调用
    `hass.config_entries.async_reload` 时，后续的 `LifeSmartOAPIClient()`
    调用都会返回一个我们可以控制的新实例。
    """
    with patch(
        "custom_components.lifesmart.core.openapi_client.LifeSmartOAPIClient",
        autospec=True,
    ) as mock_class:
        # 配置默认的实例行为
        instance = mock_class.return_value
        instance.async_get_all_devices.return_value = mock_lifesmart_devices
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
        instance.async_send_single_command = AsyncMock(return_value=0)
        instance.async_send_multi_command = AsyncMock(return_value=0)

        yield mock_class


@pytest.fixture
def mock_client(mock_client_class):
    """
    提供一个默认的模拟 LifeSmartOAPIClient 实例。

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
def mock_hub_class():
    """
    一个高级 fixture，它 patch LifeSmartHub 类并返回这个类的 Mock。

    这允许我们验证其方法（如 `async_setup`, `async_unload`）是否在集成的生命周期中
    （设置、卸载、重载）被正确调用。
    """
    with patch(
        "custom_components.lifesmart.hub.LifeSmartHub", autospec=True
    ) as mock_class:
        # 获取实例的 mock，以便我们可以配置和断言它的方法
        instance = mock_class.return_value
        instance.async_setup = AsyncMock(return_value=True)
        instance.async_unload = AsyncMock()
        instance.get_devices = MagicMock()
        instance.get_client = MagicMock()
        instance.get_exclude_config = MagicMock(return_value=(set(), set()))
        instance.data_update_handler = AsyncMock()
        yield mock_class


@pytest.fixture(autouse=True)
def auto_prevent_thread_creation(request):
    """
    精准的autouse fixture：只防止线程/定时器创建，不影响业务逻辑。

    设计原则：
    1. 只mock会产生线程残留的基础设施组件
    2. 完全保留业务逻辑，允许测试验证真实的成功/失败场景
    3. 从根源解决线程残留问题，而不是"允许残留"
    4. 对于Hub单元测试，提供更精细的控制

    被mock的组件：
    - async_track_time_interval: Hub中用于令牌刷新的定时任务
    - LifeSmartStateManager: WebSocket连接管理器，会创建异步任务

    不被mock的组件：
    - Hub的所有业务方法 (async_setup, get_devices等)
    - 客户端的所有API调用
    - 配置和数据处理逻辑

    特殊处理：
    - test_hub.py 中的测试需要验证真实的定时器和状态管理器创建
    - 但prevent_socket_access已经阻止了网络访问，所以只需要跳过线程mock
    """
    # 检查是否在test_hub.py中运行
    if "test_hub.py" in request.fspath.basename:
        # test_hub.py需要测试真实的Hub逻辑，包括定时器和状态管理器的创建
        # prevent_socket_access fixture已经处理了网络访问阻止
        # 所以这里只需要让测试正常运行，不添加额外的mock
        yield
    else:
        # 其他测试文件使用完整的线程防护
        with (
            patch(
                # 防止创建真实的定时器任务（线程残留的根源）
                "homeassistant.helpers.event.async_track_time_interval",
                return_value=MagicMock(),
            ),
            patch(
                # 防止创建真实的WebSocket状态管理器（异步任务残留的根源）
                "custom_components.lifesmart.hub.LifeSmartStateManager",
                return_value=MagicMock(),
            ),
        ):
            yield


@pytest.fixture
def mock_hub_for_testing():
    """
    显式fixture：为需要完全控制Hub行为的测试提供mock。

    使用场景：
    - 测试集成的设置/卸载流程
    - 需要验证Hub方法调用的测试
    - 需要模拟特定设备列表的测试

    与auto_prevent_thread_creation的区别：
    - 这个fixture mock业务逻辑，那个只mock基础设施
    - 这个是显式使用，那个是自动应用
    """
    with (
        patch(
            "custom_components.lifesmart.hub.LifeSmartHub.async_setup",
            return_value=True,
        ) as mock_hub_setup,
        patch(
            "custom_components.lifesmart.hub.LifeSmartHub.get_devices",
            return_value=[],
        ) as mock_get_devices,
        patch(
            "custom_components.lifesmart.hub.LifeSmartHub.get_client",
            return_value=MagicMock(),
        ) as mock_get_client,
        patch(
            "custom_components.lifesmart.hub.LifeSmartHub.async_unload",
            return_value=True,
        ) as mock_hub_unload,
    ):
        yield mock_hub_setup, mock_get_devices, mock_get_client, mock_hub_unload


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_hub_class: MagicMock,
    mock_lifesmart_devices: list,
):
    """
    一个统一的 fixture，用于完整地设置和加载 LifeSmart 集成及其所有平台。

    这是绝大多数集成测试的入口点。它执行了以下操作：
    1. 将模拟的 `ConfigEntry` 添加到 Home Assistant。
    2. Patch 掉真实的 Hub 创建过程，注入模拟数据。
    3. 触发 `async_setup` 流程。
    4. 验证集成是否成功加载。
    5. 将控制权交给测试用例。
    6. 在测试结束后，自动执行卸载流程，并验证卸载是否成功。
    """
    mock_config_entry.add_to_hass(hass)

    # 配置 mock hub 实例
    hub_instance = mock_hub_class.return_value
    hub_instance.get_devices.return_value = mock_lifesmart_devices
    hub_instance.get_client.return_value = mock_client
    hub_instance.get_exclude_config.return_value = (
        {"excluded_device"},
        {"excluded_hub"},
    )

    with patch(
        "custom_components.lifesmart.LifeSmartHub",
        new=mock_hub_class,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

    # 验证集成已成功加载
    assert mock_config_entry.state == ConfigEntryState.LOADED

    # 验证 Hub 被正确设置
    mock_hub_class.assert_called_once()
    hub_instance.async_setup.assert_called_once()

    # 将控制权交给测试用例
    yield mock_config_entry

    # --- 测试结束后的清理 ---
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
    from .test_utils import create_mock_device_climate_fancoil

    return create_mock_device_climate_fancoil()


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
    提供一个 SL_NATURE 面板的模拟数据，该面板被配置为控制"风机盘管"。

    SL_NATURE 面板是一个多功能设备，其具体功能由内部数据点决定。
    - `P5` 的 `val` 为 3: 表示此面板工作在"温控器"模式下。
    - `P6` 的 `val` 为 `(4 << 6)`: 这是最关键的配置，定义了其控制的设备类型为
      "风机盘管(双阀)"，这将决定实体支持的 `hvac_modes` 和 `fan_modes`。
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
    提供一个 SL_NATURE 面板的模拟数据，该面板被配置为控制"新风"。

    - `P6` 的 `val` 为 `(0 << 6)`: 定义了其控制的设备类型为"新风"。
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
    提供一个 SL_NATURE 面板的模拟数据，该面板被配置为控制"水地暖"。

    - `P6` 的 `val` 为 `(2 << 6)`: 定义了其控制的设备类型为"水地暖"。
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
    from .test_utils import create_mock_device_spot_rgb_light

    return create_mock_device_spot_rgb_light()


@pytest.fixture
def mock_device_dual_io_rgbw_light() -> dict:
    """
    提供一个双 IO 口 RGBW 灯 (SL_CT_RGBW) 的模拟数据。

    - 初始状态: 开，但颜色和效果均未激活。
      - `RGBW` 口为开 (`type: 129`)，但值为 0。
      - `DYN` 口为关 (`type: 128`)。
    """
    from .test_utils import create_mock_device_dual_io_rgbw_light

    return create_mock_device_dual_io_rgbw_light()


@pytest.fixture
def mock_device_single_io_rgbw_light() -> dict:
    """
    提供一个单 IO 口 RGBW 灯 (SL_SC_RGB) 的模拟数据。

    此 Fixture 用于对该特定设备类型的协议进行精确测试。
    - 初始状态: 开，颜色为 (1, 2, 3)，亮度为 100%。
      - `val` 为 `0x64010203` (亮度100, R=1, G=2, B=3)。
    """
    from .test_utils import create_mock_device_single_io_rgbw_light

    return create_mock_device_single_io_rgbw_light()


# ============================================================================
# === 为隔离测试专用的 Setup Fixtures ===
# ============================================================================


@pytest.fixture
async def setup_integration_spot_rgb_only(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_hub_class: MagicMock,
    mock_device_spot_rgb_light: dict,
):
    """
    一个专用的 setup fixture，只加载 SPOT RGB 灯。

    此 fixture 创建一个只包含单个 SPOT RGB 灯的纯净测试环境，
    用于对该设备的颜色和亮度逻辑进行精确的边缘情况测试。
    """
    mock_config_entry.add_to_hass(hass)

    # 配置 mock hub 实例
    hub_instance = mock_hub_class.return_value
    devices = [mock_device_spot_rgb_light]
    hub_instance.get_devices.return_value = devices
    hub_instance.get_client.return_value = mock_client
    hub_instance.get_exclude_config.return_value = (set(), set())

    with patch(
        "custom_components.lifesmart.LifeSmartHub",
        new=mock_hub_class,
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
    mock_hub_class: MagicMock,
    mock_device_dual_io_rgbw_light: dict,
):
    """
    一个专用的 setup fixture，只加载双 IO 口灯。

    此 fixture 创建一个只包含单个双 IO 口灯的纯净测试环境，
    用于对该设备颜色和效果的互斥逻辑进行精确的联合测试。
    """
    mock_config_entry.add_to_hass(hass)

    # 配置 mock hub 实例
    hub_instance = mock_hub_class.return_value
    devices = [mock_device_dual_io_rgbw_light]
    hub_instance.get_devices.return_value = devices
    hub_instance.get_client.return_value = mock_client
    hub_instance.get_exclude_config.return_value = (set(), set())

    with patch(
        "custom_components.lifesmart.LifeSmartHub",
        new=mock_hub_class,
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
    mock_hub_class: MagicMock,
    mock_device_single_io_rgbw_light: dict,
):
    """
    一个专用的 setup fixture，只加载单 IO 口 RGBW 灯。

    此 fixture 创建一个只包含单个 SL_SC_RGB 灯的纯净测试环境，
    用于对该设备的服务调用与设备协议的精确匹配进行测试。
    """
    mock_config_entry.add_to_hass(hass)

    # 配置 mock hub 实例
    hub_instance = mock_hub_class.return_value
    devices = [mock_device_single_io_rgbw_light]
    hub_instance.get_devices.return_value = devices
    hub_instance.get_client.return_value = mock_client
    hub_instance.get_exclude_config.return_value = (set(), set())

    with patch(
        "custom_components.lifesmart.LifeSmartHub",
        new=mock_hub_class,
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    assert mock_config_entry.state == ConfigEntryState.LOADED
    yield mock_config_entry


# 导入MAPLE HOME风格的pytest横幅
try:
    from .pytest_maple_banner import pytest_sessionstart
except ImportError:
    # 如果导入失败，使用简单的版本显示
    def pytest_sessionstart(session):
        """简单的版本信息显示（备用方案）"""
        try:
            import homeassistant.const as ha_const
            import aiohttp

            ha_version = getattr(ha_const, "__version__", "Unknown")
            aiohttp_version = getattr(aiohttp, "__version__", "Unknown")
            print(f"🏠 Home Assistant: {ha_version} | 🌐 aiohttp: {aiohttp_version}")
        except ImportError:
            print("⚠️  Could not determine Home Assistant version")
        print()
