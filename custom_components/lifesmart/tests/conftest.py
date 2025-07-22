"""共享的 pytest fixtures，用于 LifeSmart 集成测试。"""

from collections.abc import Generator
from unittest.mock import patch, MagicMock, AsyncMock

import pytest
from homeassistant.const import CONF_REGION
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.lifesmart import async_setup_entry
from custom_components.lifesmart.const import (
    DOMAIN,
    CONF_LIFESMART_APPKEY,
    CONF_LIFESMART_APPTOKEN,
    CONF_LIFESMART_USERID,
    CONF_LIFESMART_USERTOKEN,
)

# 自动为所有测试加载 Home Assistant 的 pytest 插件
pytest_plugins = "pytest_homeassistant_custom_component"

# 定义标准的模拟配置数据
MOCK_CONFIG = {
    CONF_LIFESMART_APPKEY: "mock_appkey",
    CONF_LIFESMART_APPTOKEN: "mock_apptoken",
    CONF_LIFESMART_USERID: "mock_userid",
    CONF_LIFESMART_USERTOKEN: "mock_usertoken",
    CONF_REGION: "cn2",
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """自动为所有测试启用自定义组件集成。"""
    yield


@pytest.fixture
def lifesmart_client_factory():
    """
    提供一个 LifeSmartClient 的工厂 fixture。
    允许测试用例按需创建具有特定返回值的模拟客户端。
    """

    def _create_client(devices=None, side_effect=None):
        """创建并返回一个模拟的 LifeSmartClient 实例。"""
        if devices is None:
            devices = []

        client = MagicMock(name="mock_lifesmart_client")

        # 如果需要模拟异常（如认证失败、连接超时）
        if side_effect:
            client.get_all_device_async.side_effect = side_effect
            client.login_async.side_effect = side_effect
            return client

        # 默认模拟成功调用的返回值
        client.get_all_device_async = AsyncMock(return_value=devices)
        client.login_async = AsyncMock(
            return_value={
                "usertoken": "mock_new_usertoken",
                "userid": MOCK_CONFIG[CONF_LIFESMART_USERID],
                "region": MOCK_CONFIG[CONF_REGION],
            }
        )
        client.async_refresh_token = AsyncMock(
            return_value={
                "usertoken": "mock_refreshed_usertoken",
                "expiredtime": 9999999999,
            }
        )
        client.send_epset_async = AsyncMock(return_value=0)
        client.turn_on_light_switch_async = AsyncMock(return_value=0)
        client.turn_off_light_switch_async = AsyncMock(return_value=0)
        client.async_set_multi_ep_async = AsyncMock(return_value=0)

        return client

    return _create_client


@pytest.fixture
def lifesmart_client(lifesmart_client_factory):
    """提供一个默认的、无设备的模拟 LifeSmartClient。"""
    return lifesmart_client_factory()


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """提供一个模拟的 ConfigEntry 实例。"""
    return MockConfigEntry(
        domain=DOMAIN,
        data=MOCK_CONFIG,
        entry_id="mock_entry_id_12345",
        title="LifeSmart Mock",
    )


@pytest.fixture
async def setup_integration(
    hass, mock_config_entry, lifesmart_client_factory
) -> Generator[MockConfigEntry, None, None]:
    """
    一个高级 fixture，用于设置完整的 LifeSmart 集成。

    它会自动处理：
    1. 创建并添加模拟的 ConfigEntry。
    2. Patch LifeSmartClient 以使用模拟客户端。
    3. 调用 async_setup_entry。
    4. 验证集成加载成功。

    对于大多数实体测试，这是唯一需要的 setup fixture。
    """
    # 允许测试通过 `pytest.mark.parametrize` 传递设备数据
    mock_devices = []
    if hasattr(pytest, "current_test") and hasattr(pytest.current_test, "callspec"):
        mock_devices = pytest.current_test.callspec.params.get("mock_devices", [])

    # 使用工厂创建带有特定设备的客户端
    mock_client = lifesmart_client_factory(devices=mock_devices)

    # 将配置条目添加到 HASS
    mock_config_entry.add_to_hass(hass)

    # Patch 客户端的创建过程，使其返回我们的 mock_client
    with patch("custom_components.lifesmart.LifeSmartClient", return_value=mock_client):
        # 设置集成
        result = await async_setup_entry(hass, mock_config_entry)
        await hass.async_block_till_done()

        # 验证集成已成功加载
        assert result is True

        yield mock_config_entry
