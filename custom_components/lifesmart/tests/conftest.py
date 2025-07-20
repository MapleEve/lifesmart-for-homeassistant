"""初始化pytest测试环境的配置和模拟对象。"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import CONF_REGION

from custom_components.lifesmart.const import (
    DOMAIN,
    CONF_LIFESMART_APPKEY,
    CONF_LIFESMART_APPTOKEN,
    CONF_LIFESMART_USERID,
    CONF_LIFESMART_USERTOKEN,
)

# 自动为所有测试应用这个fixture
pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture
def mock_lifesmart_client():
    """提供一个模拟的LifeSmartClient实例。"""
    client = AsyncMock()
    client.get_all_device_async.return_value = []  # 默认返回空设备列表
    client.login_async.return_value = {
        "usertoken": "mock_new_usertoken",
        "userid": "mock_userid",
        "region": "cn2",
    }
    client.async_refresh_token.return_value = {
        "usertoken": "mock_refreshed_usertoken",
        "expiredtime": 9999999999,
    }
    client.send_epset_async.return_value = 0  # 模拟成功
    client.turn_on_light_switch_async.return_value = 0
    client.turn_off_light_switch_async.return_value = 0
    return client


@pytest.fixture
def mock_config_entry():
    """提供一个模拟的ConfigEntry实例。"""
    return MagicMock(
        data={
            CONF_LIFESMART_APPKEY: "mock_appkey",
            CONF_LIFESMART_APPTOKEN: "mock_apptoken",
            CONF_LIFESMART_USERID: "mock_userid",
            CONF_LIFESMART_USERTOKEN: "mock_usertoken",
            CONF_REGION: "cn2",
        },
        options={},
        entry_id="mock_entry_id",
    )


@pytest.fixture
def mock_setup_entry(hass, mock_lifesmart_client):
    """模拟集成设置，将模拟客户端注入hass.data。"""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["mock_entry_id"] = {
        "client": mock_lifesmart_client,
        "devices": [],
        "exclude_devices": "",
        "exclude_hubs": "",
    }
    return True
