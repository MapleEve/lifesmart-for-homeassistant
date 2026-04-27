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

from custom_components.lifesmart.core.const import (
    DOMAIN,
    CONF_EXCLUDE_ITEMS,
    CONF_EXCLUDE_AGTS,
)
from .utils.constants import (
    REGION_IDENTIFIERS,
    TEST_CONFIG_ENTRY,
    TEST_EXCLUSION_CONFIG,
)
from .utils.helpers import create_mock_hub

_LOGGER = logging.getLogger(__name__)


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
    from .utils.typed_factories import create_mock_config_data

    return create_mock_config_data()


# --- Mock Hub 和客户端配置 ---
@pytest.fixture
def mock_light_devices_only():
    """
    创建仅包含灯光设备的模拟数据列表。
    使用create_gen2_devices来测试分类功能。
    """
    from .utils.typed_factories import create_gen2_devices

    devices = create_gen2_devices(
        [
            "SL_LI_WW",
            "SL_LI_WW",
            "SL_CT_RGBW",
            "SL_SC_RGB",
            "SL_SPOT_RGB",
            "MSL_IRCTL",
            "OD_WE_QUAN",
            "SL_LI_GD1",
            "SL_LI_UG1",
            "SL_LI_RGBW",
        ]
    )
    # Keep current Gen2 devtypes/IO shapes while preserving stable fixture names
    # used by the light focused tests.
    devices[0]["name"] = "White Light Bulb"
    devices[1]["name"] = "Smart Bulb Cool Warm"
    return devices


@pytest.fixture
def mock_sensor_devices_only():
    """
    创建仅包含数值传感器设备的模拟数据列表。
    使用create_gen2_devices来测试传感器分类功能。
    """
    from .utils.typed_factories import create_gen2_devices

    return create_gen2_devices(
        ["SL_SC_THL", "SL_SC_THL", "SL_SC_THL"]
    )


@pytest.fixture
def mock_binary_sensor_devices_only():
    """
    创建仅包含二元传感器设备的模拟数据列表。
    使用create_gen2_devices来专门测试binary_sensor平台功能。
    """
    from .utils.typed_factories import create_gen2_devices

    return create_gen2_devices(["SL_SC_G"])


@pytest.fixture
def mock_climate_devices_only():
    """
    创建仅包含气候控制设备的模拟数据列表。
    使用create_gen2_devices来优化气候平台测试的数据加载。
    """
    from .utils.typed_factories import create_gen2_devices

    return create_gen2_devices(["SL_NATURE", "SL_CP_DN", "SL_CP_AIR"])


@pytest.fixture
def mock_switch_devices_only():
    """
    创建仅包含开关设备的模拟数据列表。
    使用create_gen2_devices来优化开关平台测试的数据加载。
    包含传统开关、高级开关和插座设备（插座在switch平台中）。
    """
    from .utils.typed_factories import create_gen2_devices, create_nature_switch_panel

    return create_gen2_devices(
        [
            "SL_SW_IF3",
            "SL_SW_IF3",
            "SL_OL",
            "SL_OE_3C",
            "SL_P",
            "SL_P_SW",
        ]
    ) + [create_nature_switch_panel()]


@pytest.fixture
def mock_cover_devices_only():
    """
    创建仅包含窗帘/遮盖设备的模拟数据列表。
    使用create_gen2_devices来优化窗帘平台测试的数据加载。
    """
    from .utils.typed_factories import create_gen2_devices

    return create_gen2_devices(["SL_DOOYA"])


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """
    自动为所有测试启用自定义组件集成。

    这是一个 `autouse` fixture，它会自动应用到所有测试中，确保
    `pytest-homeassistant-custom-component` 的功能被激活。
    """
    yield


@pytest.fixture
def mock_client_class(mock_sensor_devices_only):
    """
    一个高级 fixture，它 patch LifeSmartOAPIClient 类并返回这个类的 Mock。

    这允许测试根据需要控制 `LifeSmartOAPIClient()` 的返回值，对于测试重载
    (reload) 行为至关重要。通过 patch 类本身，我们可以确保每次调用
    `hass.config_entries.async_reload` 时，后续的 `LifeSmartOAPIClient()`
    调用都会返回一个我们可以控制的新实例。
    """
    with patch(
        "custom_components.lifesmart.core.hub.LifeSmartOpenAPIClient",
        autospec=True,
    ) as mock_class:
        # 配置默认的实例行为
        instance = mock_class.return_value
        instance.async_get_all_devices.return_value = mock_sensor_devices_only
        instance.login_async.return_value = {
            "usertoken": "mock_new_usertoken",
            "userid": "mock_userid",
            "region": REGION_IDENTIFIERS["china_region"],
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
def mock_failed_client():
    """
    提供模拟失败场景的OAPI客户端mock。

    用于测试连接失败、认证失败等错误处理场景。
    使用create_mock_failed_oapi_client工厂函数。
    """
    from .utils.typed_factories import create_mock_failed_oapi_client

    return create_mock_failed_oapi_client()


@pytest.fixture
def mock_client_with_devices(mock_sensor_devices_only):
    """
    提供带有预配置设备列表的OAPI客户端mock。

    用于需要特定设备数据的测试场景。
    使用create_mock_oapi_client_with_devices工厂函数。
    """
    from .utils.typed_factories import create_mock_oapi_client_with_devices

    return create_mock_oapi_client_with_devices(mock_sensor_devices_only)


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
        entry_id=TEST_CONFIG_ENTRY["mock_entry_id"],
        title=TEST_CONFIG_ENTRY["mock_title"],
        options={
            CONF_EXCLUDE_ITEMS: TEST_EXCLUSION_CONFIG["excluded_device"],
            CONF_EXCLUDE_AGTS: TEST_EXCLUSION_CONFIG["excluded_hub"],
        },
    )


@pytest.fixture
def mock_hub_class():
    """
    一个高级 fixture，它 patch LifeSmartHub 类并返回这个类的 Mock。

    这允许我们验证其方法（如 `async_setup`, `async_unload`）是否在集成的生命周期中
    （设置、卸载、重载）被正确调用。
    """
    with patch("custom_components.lifesmart.LifeSmartHub", autospec=True) as mock_class:
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
                "custom_components.lifesmart.core.hub.LifeSmartStateManager",
                return_value=AsyncMock(),
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
            "custom_components.lifesmart.core.hub.LifeSmartHub.async_setup",
            return_value=True,
        ) as mock_hub_setup,
        patch(
            "custom_components.lifesmart.core.hub.LifeSmartHub.get_devices",
            return_value=[],
        ) as mock_get_devices,
        patch(
            "custom_components.lifesmart.core.hub.LifeSmartHub.get_client",
            return_value=MagicMock(),
        ) as mock_get_client,
        patch(
            "custom_components.lifesmart.core.hub.LifeSmartHub.async_unload",
            return_value=True,
        ) as mock_hub_unload,
    ):
        yield mock_hub_setup, mock_get_devices, mock_get_client, mock_hub_unload


# ============================================================================
# === 平台专用优化设置 Fixtures ===
#
# 设计说明:
# 这些 Fixtures 是对原有通用 `setup_integration` 的补充优化，专门用于
# 平台级别的测试。通过只加载特定平台需要的设备类型，减少了测试的
# 加载开销，提高了测试执行效率。
#
# 每个 fixture 使用 `create_gen2_devices` 函数来精确控制
# 加载的设备类型，从而实现精细化的测试数据管理。
#
# 重构说明 (Phase 1):
# 通过通用函数 _setup_integration_platform_generic 消除95%代码重复，
# 从226行重复代码减少到约30行，大幅提高维护效率。
# ============================================================================


async def _setup_integration_platform_generic(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_hub_class: MagicMock,
    devices_list: list,
    platform_name: str,
):
    """
    通用的平台专用集成设置函数。

    这个函数封装了所有setup_integration_*_only fixtures的共同逻辑，
    消除95%的代码重复，提高维护效率。

    Args:
        hass: HomeAssistant实例
        mock_config_entry: 模拟配置条目
        mock_client: 模拟客户端
        mock_hub_class: 模拟Hub类
        devices_list: 平台特定的设备列表
        platform_name: 平台名称(用于调试)

    Yields:
        ConfigEntry: 配置好的集成条目
    """
    mock_config_entry.add_to_hass(hass)

    # 使用工厂函数创建mock hub实例
    hub_instance = create_mock_hub(devices_list, mock_client)
    hub_instance.get_exclude_config.return_value = (set(), set())

    # Configure mock_hub_class to return our hub_instance
    mock_hub_class.return_value = hub_instance

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED
    mock_hub_class.assert_called_once()
    hub_instance.async_setup.assert_called_once()

    yield mock_config_entry

    # 清理
    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED


@pytest.fixture
async def setup_integration_light_only(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_hub_class: MagicMock,
    mock_light_devices_only: list,
):
    """
    专用的 setup fixture，仅加载灯光设备进行灯光平台测试。

    这个优化版本只加载灯光相关设备，减少测试加载开销，
    提高灯光平台测试的执行效率。
    """
    async for result in _setup_integration_platform_generic(
        hass,
        mock_config_entry,
        mock_client,
        mock_hub_class,
        mock_light_devices_only,
        "light",
    ):
        yield result


@pytest.fixture
async def setup_integration(setup_integration_light_only):
    """Backward-compatible light platform setup fixture alias."""
    yield setup_integration_light_only


@pytest.fixture
async def setup_integration_climate_only(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_hub_class: MagicMock,
    mock_climate_devices_only: list,
):
    """
    专用的 setup fixture，仅加载气候控制设备进行气候平台测试。

    这个优化版本只加载气候控制相关设备，减少测试加载开销，
    提高气候平台测试的执行效率。
    """
    async for result in _setup_integration_platform_generic(
        hass,
        mock_config_entry,
        mock_client,
        mock_hub_class,
        mock_climate_devices_only,
        "SL_NATURE",
    ):
        yield result


@pytest.fixture
async def setup_integration_sensor_only(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_hub_class: MagicMock,
    mock_sensor_devices_only: list,
):
    """
    专用的 setup fixture，仅加载传感器设备进行传感器平台测试。

    这个优化版本只加载传感器相关设备，减少测试加载开销，
    提高传感器平台测试的执行效率。
    """
    async for result in _setup_integration_platform_generic(
        hass,
        mock_config_entry,
        mock_client,
        mock_hub_class,
        mock_sensor_devices_only,
        "sensor",
    ):
        yield result


@pytest.fixture
async def setup_integration_binary_sensor_only(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_hub_class: MagicMock,
    mock_binary_sensor_devices_only: list,
):
    """
    专用的 setup fixture，仅加载二元传感器设备进行binary_sensor平台测试。

    这个优化版本只加载二元传感器相关设备，减少测试加载开销，
    提高binary_sensor平台测试的执行效率。
    """
    async for result in _setup_integration_platform_generic(
        hass,
        mock_config_entry,
        mock_client,
        mock_hub_class,
        mock_binary_sensor_devices_only,
        "SL_SC_G",
    ):
        yield result


@pytest.fixture
async def setup_integration_switch_only(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_hub_class: MagicMock,
    mock_switch_devices_only: list,
):
    """
    专用的 setup fixture，仅加载开关设备进行开关平台测试。

    这个优化版本只加载开关相关设备，减少测试加载开销，
    提高开关平台测试的执行效率。
    """
    async for result in _setup_integration_platform_generic(
        hass,
        mock_config_entry,
        mock_client,
        mock_hub_class,
        mock_switch_devices_only,
        "switch",
    ):
        yield result


@pytest.fixture
async def setup_integration_cover_only(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_hub_class: MagicMock,
    mock_cover_devices_only: list,
):
    """
    专用的 setup fixture，仅加载窗帘设备进行窗帘平台测试。

    这个优化版本只加载窗帘相关设备，减少测试加载开销，
    提高窗帘平台测试的执行效率。
    """
    async for result in _setup_integration_platform_generic(
        hass,
        mock_config_entry,
        mock_client,
        mock_hub_class,
        mock_cover_devices_only,
        "SL_DOOYA",
    ):
        yield result


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

    # 使用工厂函数创建mock hub实例
    devices = [mock_device_spot_rgb_light]
    hub_instance = create_mock_hub(devices, mock_client)

    # Configure mock_hub_class to return our hub_instance
    mock_hub_class.return_value = hub_instance

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED
    yield mock_config_entry

    # 清理
    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED


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

    # 使用工厂函数创建mock hub实例
    devices = [mock_device_dual_io_rgbw_light]
    hub_instance = create_mock_hub(devices, mock_client)

    # Configure mock_hub_class to return our hub_instance
    mock_hub_class.return_value = hub_instance

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED
    yield mock_config_entry

    # 清理
    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED


@pytest.fixture
async def setup_integration_single_io_rgbw_only(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_hub_class: MagicMock,
):
    """
    一个专用的 setup fixture，只加载单 IO 口 RGB 灯。

    此 fixture 创建一个只包含单个 SL_SC_RGB 灯的纯净测试环境，
    用于对该设备的服务调用与设备协议的精确匹配进行测试。
    """
    from .utils.typed_factories import create_mock_device_single_io_rgb_light

    mock_config_entry.add_to_hass(hass)

    # 使用专用的单IO RGB灯工厂函数创建设备
    devices = [create_mock_device_single_io_rgb_light()]
    hub_instance = create_mock_hub(devices, mock_client)

    # Configure mock_hub_class to return our hub_instance
    mock_hub_class.return_value = hub_instance

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED
    yield mock_config_entry

    # 清理
    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED


@pytest.fixture
def mock_device_spot_rgb_light():
    """创建SPOT RGB灯测试设备。"""
    from .utils.typed_factories import create_mock_device_spot_rgb_light

    return create_mock_device_spot_rgb_light()


@pytest.fixture
def mock_device_dual_io_rgbw_light():
    """创建双IO RGBW灯测试设备。"""
    from .utils.typed_factories import create_mock_device_dual_io_rgbw_light

    return create_mock_device_dual_io_rgbw_light()


# ============================================================================
# === Gen2 device dictionary test fixtures ===
# ============================================================================


@pytest.fixture
def typed_core_devices():
    """
    提供所有10个核心设备类型的设备实例列表。

    简化版本，直接返回字典格式设备。
    """
    from .utils.typed_factories import create_core_devices

    return create_core_devices()


@pytest.fixture
def typed_smart_plug():
    """提供 Gen2 智慧插座设备字典 (SL_OL)。"""
    from .utils.typed_factories import create_smart_plug

    return create_smart_plug()


@pytest.fixture
def typed_power_meter_plug():
    """提供 Gen2 计量插座设备字典 (SL_OE_3C)。"""
    from .utils.typed_factories import create_power_meter_plug

    return create_power_meter_plug()


@pytest.fixture
def typed_switch_if3():
    """提供 Gen2 三联开关设备字典 (SL_SW_IF3)。"""
    from .utils.typed_factories import create_switch_if3

    return create_switch_if3()


@pytest.fixture
def typed_dimmer_light():
    """提供 Gen2 调光灯泡设备字典 (SL_LI_WW)。"""
    from .utils.typed_factories import create_dimmer_light

    return create_dimmer_light()


@pytest.fixture
def typed_rgbw_light():
    """提供 Gen2 RGBW灯带设备字典 (SL_CT_RGBW)。"""
    from .utils.typed_factories import create_rgbw_light

    return create_rgbw_light()


@pytest.fixture
def typed_environment_sensor():
    """提供 Gen2 环境传感器设备字典 (SL_SC_THL)。"""
    from .utils.typed_factories import create_environment_sensor

    return create_environment_sensor()


@pytest.fixture
def typed_door_sensor():
    """提供 Gen2 门窗传感器设备字典 (SL_SC_G)。"""
    from .utils.typed_factories import create_door_sensor

    return create_door_sensor()


@pytest.fixture
def typed_curtain_motor():
    """提供 Gen2 窗帘电机设备字典 (SL_DOOYA)。"""
    from .utils.typed_factories import create_curtain_motor

    return create_curtain_motor()


@pytest.fixture
def typed_thermostat_panel():
    """提供 Gen2 温控面板设备字典 (SL_NATURE)。"""
    from .utils.typed_factories import create_thermostat_panel

    return create_thermostat_panel()


@pytest.fixture
def typed_smart_lock():
    """提供 Gen2 智能门锁设备字典 (SL_LK_LS)。"""
    from .utils.typed_factories import create_smart_lock

    return create_smart_lock()


@pytest.fixture
def typed_switch_devices():
    """提供所有 Gen2 开关设备字典列表。"""
    from .utils.typed_factories import create_gen2_devices

    return create_gen2_devices(["SL_OL", "SL_SW_IF3"])


@pytest.fixture
def typed_sensor_devices():
    """提供所有 Gen2 传感器设备字典列表。"""
    from .utils.typed_factories import create_gen2_devices

    return create_gen2_devices(["SL_OE_3C", "SL_SC_THL"])


@pytest.fixture
def typed_light_devices():
    """提供所有 Gen2 灯光设备字典列表。"""
    from .utils.typed_factories import create_gen2_devices

    return create_gen2_devices(["SL_LI_WW", "SL_CT_RGBW"])


@pytest.fixture
def typed_binary_sensor_devices():
    """提供所有 Gen2 二进制传感器设备字典列表。"""
    from .utils.typed_factories import create_gen2_devices

    return create_gen2_devices(["SL_SC_G"])


@pytest.fixture
def typed_cover_devices():
    """提供所有 Gen2 窗帘设备字典列表。"""
    from .utils.typed_factories import create_gen2_devices

    return create_gen2_devices(["SL_DOOYA"])


@pytest.fixture
def typed_climate_devices():
    """提供所有 Gen2 气候控制设备字典列表。"""
    from .utils.typed_factories import create_gen2_devices

    return create_gen2_devices(["SL_NATURE", "SL_CP_DN", "SL_CP_AIR"])


@pytest.fixture
def typed_lock_devices():
    """提供所有 Gen2 门锁设备字典列表。"""
    from .utils.typed_factories import create_gen2_devices

    return create_gen2_devices(["SL_LK_LS"])


# === Gen2 dictionary validation fixtures ===


@pytest.fixture
def typed_devices_as_dicts():
    """
    创建核心设备的字典格式列表。

    简化版本，直接返回字典格式设备，无需类型转换。
    """
    from .utils.typed_factories import create_core_devices

    return create_core_devices()


@pytest.fixture
async def setup_integration_typed_devices_only(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_hub_class: MagicMock,
    typed_devices_as_dicts: list,
):
    """
    专用的setup fixture，使用 Gen2 设备字典数据。
    """
    mock_config_entry.add_to_hass(hass)

    # 使用 Gen2 设备字典数据
    hub_instance = create_mock_hub(typed_devices_as_dicts, mock_client)
    hub_instance.get_exclude_config.return_value = (set(), set())

    # Configure mock_hub_class to return our hub_instance
    mock_hub_class.return_value = hub_instance

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED
    yield mock_config_entry

    # 清理
    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED


# 全局标志，确保banner只显示一次
_BANNER_SHOWN = False


def _show_banner_once():
    """确保banner只显示一次的内部函数"""
    global _BANNER_SHOWN
    if _BANNER_SHOWN:
        return

    _BANNER_SHOWN = True

    try:
        from .pytest_maple_banner import pytest_sessionstart as banner_sessionstart

        banner_sessionstart(None)
    except Exception as e:
        # 如果banner导入失败，使用简单的版本显示
        try:
            import homeassistant.const as ha_const
            import aiohttp

            ha_version = getattr(ha_const, "__version__", "Unknown")
            aiohttp_version = getattr(aiohttp, "__version__", "Unknown")
            print(f"🏠 Home Assistant: {ha_version} | 🌐 aiohttp: {aiohttp_version}")
        except ImportError as import_err:
            print(f"⚠️  Could not determine Home Assistant version: {import_err}")
        print()


def pytest_sessionstart(session):
    """pytest会话开始时显示banner"""
    _show_banner_once()


# Alternative hook registration for older pytest-homeassistant-custom-component versions
def pytest_configure(config):
    """Alternative hook that might work better with older versions"""
    # This hook is called after command line options have been parsed
    # and all plugins and initial conftest files been loaded
    _show_banner_once()


# Phase 2: DeviceResolver 核心测试支持
@pytest.fixture(autouse=True)
def reset_global_singletons():
    """
    在每次测试后自动重置核心组件的全局单例。

    这是确保 Phase 2 DeviceResolver 测试隔离性的关键步骤，
    防止状态从一个测试泄漏到另一个测试中。
    """
    yield  # 运行测试

    # 在测试结束后执行清理
    try:
        from custom_components.lifesmart.core.resolver import device_resolver

        device_resolver._global_resolver = None
    except ImportError:
        # 如果模块还未导入，跳过清理
        pass

    try:
        from custom_components.lifesmart.core.strategies import strategy_factory

        strategy_factory._global_factory = None
    except ImportError:
        # 如果模块还未导入，跳过清理
        pass
