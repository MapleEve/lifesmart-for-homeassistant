"""
测试 Hub 模块的核心功能。

此测试文件专门测试 hub.py 中的 LifeSmartHub 类，包括：
- Hub 的创建和初始化
- 客户端管理（OAPI 和本地 TCP）
- 设备数据管理
- 实时状态更新处理
- WebSocket 状态管理器
- 生命周期管理（设置和卸载）
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.config_entries import CONN_CLASS_CLOUD_PUSH
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_TYPE,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.lifesmart.const import (
    CONF_LIFESMART_APPKEY,
    CONF_LIFESMART_APPTOKEN,
    CONF_LIFESMART_AUTH_METHOD,
    CONF_LIFESMART_USERID,
    CONF_LIFESMART_USERTOKEN,
    DEVICE_ID_KEY,
    DEVICE_TYPE_KEY,
    DOMAIN,
    HUB_ID_KEY,
    SUBDEVICE_INDEX_KEY,
)
from custom_components.lifesmart.exceptions import LifeSmartAPIError, LifeSmartAuthError
from custom_components.lifesmart.hub import LifeSmartHub


@pytest.fixture
def mock_config_entry_oapi():
    """提供 OAPI 模式的配置条目。"""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: CONN_CLASS_CLOUD_PUSH,
            CONF_LIFESMART_APPKEY: "test_appkey",
            CONF_LIFESMART_APPTOKEN: "test_apptoken",
            CONF_LIFESMART_USERID: "test_userid",
            CONF_LIFESMART_USERTOKEN: "test_usertoken",
            CONF_LIFESMART_AUTH_METHOD: "token",
        },
        entry_id="test_entry_oapi",
    )


@pytest.fixture
def mock_config_entry_local():
    """提供本地模式的配置条目。"""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_TYPE: "local_push",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 8080,
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "test_pass",
        },
        entry_id="test_entry_local",
    )


class TestLifeSmartHub:
    """测试 LifeSmartHub 类的核心功能。"""

    @pytest.mark.asyncio
    async def test_hub_initialization(
        self, hass: HomeAssistant, mock_config_entry_oapi
    ):
        """测试 Hub 的基本初始化。"""
        hub = LifeSmartHub(hass, mock_config_entry_oapi)

        assert hub.hass == hass, "Hub的hass实例应该正确"
        assert hub.config_entry == mock_config_entry_oapi, "Hub的配置条目应该正确"
        assert hub.client is None, "初始化时客户端应该为None"
        assert hub.devices == [], "初始化时设备列表应该为空"
        assert hub._state_manager is None, "初始化时状态管理器应该为None"
        assert hub._local_task is None, "初始化时本地任务应该为None"
        assert hub._refresh_task_unsub is None, "初始化时刷新任务取消器应该为None"

    @pytest.mark.asyncio
    async def test_hub_setup_oapi_success(
        self, hass: HomeAssistant, mock_config_entry_oapi
    ):
        """测试 OAPI 模式下 Hub 的成功设置。"""
        # 将配置条目添加到 hass
        mock_config_entry_oapi.add_to_hass(hass)

        hub = LifeSmartHub(hass, mock_config_entry_oapi)
        mock_devices = [{"agt": "hub1", "me": "dev1", "devtype": "SL_SW"}]

        with patch(
            "custom_components.lifesmart.hub.LifeSmartOAPIClient"
        ) as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.async_get_all_devices = AsyncMock(return_value=mock_devices)
            mock_client.async_refresh_token = AsyncMock(
                return_value={
                    "usertoken": "new_token",
                    "expiredtime": 9999999999,
                }
            )
            mock_client.get_wss_url.return_value = "wss://test.com/ws"

            with patch(
                "custom_components.lifesmart.hub.LifeSmartStateManager"
            ) as mock_state_manager_class:
                # 创建正确的mock实例，区分同步和异步方法
                mock_state_manager_instance = MagicMock()
                mock_state_manager_instance.set_token_expiry = MagicMock()  # 同步方法
                mock_state_manager_instance.start = MagicMock()  # 同步方法
                mock_state_manager_instance.stop = AsyncMock()  # 异步方法
                mock_state_manager_class.return_value = mock_state_manager_instance

                result = await hub.async_setup()

                assert result is True, "云端模式设置应该成功"
                assert hub.client == mock_client, "Hub的客户端应该被正确设置"
                assert hub.devices == mock_devices, "Hub的设备列表应该被正确设置"
                assert hub._state_manager is not None, "状态管理器应该被创建"
                mock_state_manager_instance.start.assert_called_once()

                # 清理资源
                await hub.async_unload()

    @pytest.mark.asyncio
    async def test_hub_setup_local_success(
        self, hass: HomeAssistant, mock_config_entry_local
    ):
        """测试本地模式下 Hub 的成功设置。"""
        # 将配置条目添加到 hass
        mock_config_entry_local.add_to_hass(hass)

        hub = LifeSmartHub(hass, mock_config_entry_local)
        mock_devices = [{"agt": "hub1", "me": "dev1", "devtype": "SL_SW"}]

        with patch(
            "custom_components.lifesmart.hub.LifeSmartLocalTCPClient"
        ) as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.async_get_all_devices = AsyncMock(return_value=mock_devices)

            # 模拟异步连接任务 - 创建一个真正的 asyncio Task
            async def dummy_task():
                await asyncio.sleep(100)  # 永不结束的任务

            real_task = asyncio.create_task(dummy_task())
            with patch.object(hass, "async_create_task", return_value=real_task):
                result = await hub.async_setup()

                assert result is True, "本地模式设置应该成功"
                assert hub.client == mock_client, "Hub的客户端应该被正确设置"
                assert hub.devices == mock_devices, "Hub的设备列表应该被正确设置"
                assert hub._local_task == real_task, "本地任务应该被正确设置"

                # 清理资源
                await hub.async_unload()

    @pytest.mark.asyncio
    async def test_hub_setup_auth_error(
        self, hass: HomeAssistant, mock_config_entry_oapi
    ):
        """测试 Hub 设置时的认证错误。"""
        # 确保配置条目被添加到 hass 中，这样重新认证流程才能找到它
        mock_config_entry_oapi.add_to_hass(hass)

        hub = LifeSmartHub(hass, mock_config_entry_oapi)

        with patch(
            "custom_components.lifesmart.hub.LifeSmartOAPIClient"
        ) as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.async_refresh_token.side_effect = LifeSmartAuthError(
                "Auth failed"
            )

            with pytest.raises(ConfigEntryNotReady):
                await hub.async_setup()

    @pytest.mark.asyncio
    async def test_hub_get_methods(self, hass: HomeAssistant, mock_config_entry_oapi):
        """测试 Hub 的便利方法。"""
        # 添加配置条目到 hass
        mock_config_entry_oapi.add_to_hass(hass)

        hub = LifeSmartHub(hass, mock_config_entry_oapi)
        mock_client = MagicMock()
        mock_devices = [{"agt": "hub1", "me": "dev1"}]

        hub.client = mock_client
        hub.devices = mock_devices

        # 使用 async_update_entry 来正确设置选项
        hass.config_entries.async_update_entry(
            mock_config_entry_oapi,
            options={"exclude": "dev1,dev2", "exclude_agt": "hub2"},
        )

        # 测试 get_client
        assert hub.get_client() == mock_client, "get_client应该返回正确的客户端"

        # 测试 get_devices
        assert hub.get_devices() == mock_devices, "get_devices应该返回正确的设备列表"

        # 测试 get_exclude_config
        exclude_devices, exclude_hubs = hub.get_exclude_config()
        assert exclude_devices == {"dev1", "dev2"}, "排除设备列表应该正确解析"
        assert exclude_hubs == {"hub2"}, "排除Hub列表应该正确解析"

    @pytest.mark.asyncio
    async def test_data_update_handler(
        self, hass: HomeAssistant, mock_config_entry_oapi
    ):
        """测试数据更新处理器。"""
        # 添加配置条目到 hass
        mock_config_entry_oapi.add_to_hass(hass)

        hub = LifeSmartHub(hass, mock_config_entry_oapi)

        # 使用 async_update_entry 设置选项
        hass.config_entries.async_update_entry(mock_config_entry_oapi, options={})

        # 测试正常的数据更新
        raw_data = {
            "msg": {
                DEVICE_TYPE_KEY: "SL_SW",
                HUB_ID_KEY: "hub1",
                DEVICE_ID_KEY: "dev1",
                SUBDEVICE_INDEX_KEY: "L1",
            }
        }

        with patch(
            "custom_components.lifesmart.hub.dispatcher_send"
        ) as mock_dispatcher:
            await hub.data_update_handler(raw_data)
            mock_dispatcher.assert_called_once()

        # 测试空数据包
        await hub.data_update_handler({"msg": {}})

        # 测试 AI 事件
        ai_data = {
            "msg": {
                DEVICE_TYPE_KEY: "SL_SCENE",
                HUB_ID_KEY: "hub1",
                DEVICE_ID_KEY: "dev1",
                SUBDEVICE_INDEX_KEY: "s",
            }
        }

        with patch.object(hub, "_handle_ai_event") as mock_ai_handler:
            await hub.data_update_handler(ai_data)
            mock_ai_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_hub_unload(self, hass: HomeAssistant, mock_config_entry_oapi):
        """测试 Hub 的卸载功能。"""
        import asyncio

        hub = LifeSmartHub(hass, mock_config_entry_oapi)

        # 模拟已设置的状态
        mock_refresh_unsub = MagicMock()
        mock_state_manager = AsyncMock()
        mock_client = MagicMock()

        # 创建一个真正的任务用于测试
        async def dummy_task():
            await asyncio.sleep(100)  # 永不结束的任务

        real_task = asyncio.create_task(dummy_task())

        hub._refresh_task_unsub = mock_refresh_unsub
        hub._state_manager = mock_state_manager
        hub.client = mock_client
        hub._local_task = real_task

        with patch(
            "custom_components.lifesmart.hub.LifeSmartLocalTCPClient"
        ) as mock_local_client:
            # 设置 client 为本地客户端类型
            hub.client = mock_local_client.return_value

            await hub.async_unload()

            # 验证清理调用
            mock_refresh_unsub.assert_called_once()
            mock_state_manager.stop.assert_called_once()
            mock_local_client.return_value.disconnect.assert_called_once()

            # 验证任务被取消
            assert real_task.cancelled(), "任务应该被取消"


class TestLifeSmartStateManager:
    """测试 LifeSmartStateManager 的功能。"""

    @pytest.fixture
    def mock_oapi_client(self):
        """提供模拟的 OAPI 客户端。"""
        client = MagicMock()
        client.generate_wss_auth.return_value = '{"auth": "test"}'
        return client

    @pytest.fixture
    def mock_config_entry(self):
        """提供模拟的配置条目。"""
        return MockConfigEntry(
            domain=DOMAIN,
            data={CONF_LIFESMART_USERTOKEN: "test_token"},
            entry_id="test_entry",
        )

    @pytest.mark.asyncio
    async def test_state_manager_initialization(
        self, hass: HomeAssistant, mock_config_entry, mock_oapi_client
    ):
        """测试状态管理器的初始化。"""
        from custom_components.lifesmart.hub import LifeSmartStateManager

        refresh_callback = AsyncMock()

        manager = LifeSmartStateManager(
            hass=hass,
            config_entry=mock_config_entry,
            client=mock_oapi_client,
            ws_url="wss://test.com/ws",
            refresh_callback=refresh_callback,
        )

        assert manager.hass == hass
        assert manager.config_entry == mock_config_entry
        assert manager.client == mock_oapi_client
        assert manager.ws_url == "wss://test.com/ws"
        assert manager.refresh_callback == refresh_callback
        assert manager._should_stop is False

    @pytest.mark.asyncio
    async def test_state_manager_token_expiry(
        self, hass: HomeAssistant, mock_config_entry, mock_oapi_client
    ):
        """测试状态管理器的令牌过期时间设置。"""
        from custom_components.lifesmart.hub import LifeSmartStateManager

        manager = LifeSmartStateManager(
            hass=hass,
            config_entry=mock_config_entry,
            client=mock_oapi_client,
            ws_url="wss://test.com/ws",
            refresh_callback=AsyncMock(),
        )

        expiry_time = 9999999999
        manager.set_token_expiry(expiry_time)

        assert manager._token_expiry_time == expiry_time
        assert manager._token_refresh_event.is_set()

    @pytest.mark.asyncio
    async def test_periodic_refresh(self, hass: HomeAssistant, mock_config_entry_oapi):
        """测试定时刷新功能。"""
        hub = LifeSmartHub(hass, mock_config_entry_oapi)
        mock_client = AsyncMock()
        mock_devices = [{"agt": "hub1", "me": "dev1"}]

        hub.client = mock_client
        mock_client.async_get_all_devices.return_value = mock_devices

        with patch(
            "custom_components.lifesmart.hub.dispatcher_send"
        ) as mock_dispatcher:
            await hub._async_periodic_refresh()

            assert hub.devices == mock_devices
            mock_dispatcher.assert_called_once()

    @pytest.mark.asyncio
    async def test_periodic_refresh_with_error(
        self, hass: HomeAssistant, mock_config_entry_oapi
    ):
        """测试定时刷新遇到错误的情况。"""
        hub = LifeSmartHub(hass, mock_config_entry_oapi)
        mock_client = AsyncMock()

        hub.client = mock_client
        mock_client.async_get_all_devices.side_effect = LifeSmartAPIError("API Error")

        # 不应该抛出异常，而是记录警告
        await hub._async_periodic_refresh()
