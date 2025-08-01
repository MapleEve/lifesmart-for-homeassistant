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
    CONF_EXCLUDE_ITEMS,
    CONF_EXCLUDE_AGTS,
    CONF_AI_INCLUDE_ITEMS,
    CONF_AI_INCLUDE_AGTS,
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
    async def test_state_manager_start_stop(
        self, hass: HomeAssistant, mock_config_entry, mock_oapi_client
    ):
        """测试状态管理器的启动和停止。"""
        from custom_components.lifesmart.hub import LifeSmartStateManager

        manager = LifeSmartStateManager(
            hass=hass,
            config_entry=mock_config_entry,
            client=mock_oapi_client,
            ws_url="wss://test.com/ws",
            refresh_callback=AsyncMock(),
        )

        # 测试启动
        manager.start()
        assert manager._ws_task is not None
        assert manager._token_task is not None
        assert not manager._should_stop

        # 测试停止
        await manager.stop()
        assert manager._should_stop

    @pytest.mark.asyncio
    async def test_state_manager_create_websocket_ssl_error(
        self, hass: HomeAssistant, mock_config_entry, mock_oapi_client
    ):
        """测试WebSocket创建时的错误处理。"""
        from custom_components.lifesmart.hub import LifeSmartStateManager

        manager = LifeSmartStateManager(
            hass=hass,
            config_entry=mock_config_entry,
            client=mock_oapi_client,
            ws_url="ws://localhost/test",  # 使用本地地址避免DNS解析
            refresh_callback=AsyncMock(),
        )

        with patch(
            "homeassistant.helpers.aiohttp_client.async_get_clientsession"
        ) as mock_session_get:
            mock_session = mock_session_get.return_value
            # 直接模拟WebSocket连接失败
            mock_session.ws_connect.side_effect = Exception("Connection failed")

            with pytest.raises(Exception):
                await manager._create_websocket()

    @pytest.mark.asyncio
    async def test_state_manager_perform_auth_failure(
        self, hass: HomeAssistant, mock_config_entry, mock_oapi_client
    ):
        """测试WebSocket认证失败的处理。"""
        from custom_components.lifesmart.hub import LifeSmartStateManager
        import aiohttp
        import json

        manager = LifeSmartStateManager(
            hass=hass,
            config_entry=mock_config_entry,
            client=mock_oapi_client,
            ws_url="wss://test.com/ws",
            refresh_callback=AsyncMock(),
        )

        # 模拟WebSocket连接
        mock_ws = AsyncMock()
        manager._ws = mock_ws

        # 模拟认证失败响应
        auth_response = AsyncMock()
        auth_response.type = aiohttp.WSMsgType.TEXT
        auth_response.data = json.dumps({"code": -1, "message": "Auth failed"})
        mock_ws.receive.return_value = auth_response

        with pytest.raises(PermissionError, match="认证被服务器拒绝"):
            await manager._perform_auth()

    @pytest.mark.asyncio
    async def test_state_manager_message_consumer_error(
        self, hass: HomeAssistant, mock_config_entry, mock_oapi_client
    ):
        """测试消息消费循环中的错误处理。"""
        from custom_components.lifesmart.hub import LifeSmartStateManager
        import aiohttp

        manager = LifeSmartStateManager(
            hass=hass,
            config_entry=mock_config_entry,
            client=mock_oapi_client,
            ws_url="wss://test.com/ws",
            refresh_callback=AsyncMock(),
        )

        # 模拟WebSocket连接和错误消息
        mock_ws = AsyncMock()
        error_msg = AsyncMock()
        error_msg.type = aiohttp.WSMsgType.ERROR
        mock_ws.__aiter__.return_value = [error_msg]
        manager._ws = mock_ws

        # 设置hub数据以供消息处理使用
        hass.data[DOMAIN] = {mock_config_entry.entry_id: {"hub": AsyncMock()}}

        # 消费循环应该在遇到错误消息时中断，不应该抛出异常
        await manager._message_consumer()

    @pytest.mark.asyncio
    async def test_state_manager_process_text_message(
        self, hass: HomeAssistant, mock_config_entry, mock_oapi_client
    ):
        """测试文本消息处理。"""
        from custom_components.lifesmart.hub import LifeSmartStateManager

        manager = LifeSmartStateManager(
            hass=hass,
            config_entry=mock_config_entry,
            client=mock_oapi_client,
            ws_url="wss://test.com/ws",
            refresh_callback=AsyncMock(),
        )

        # 设置模拟hub
        mock_hub = AsyncMock()
        hass.data[DOMAIN] = {mock_config_entry.entry_id: {"hub": mock_hub}}

        # 测试有效的io消息
        valid_message = '{"type": "io", "msg": {"test": "data"}}'
        await manager._process_text_message(valid_message)
        mock_hub.data_update_handler.assert_called_once()

        # 重置mock
        mock_hub.reset_mock()

        # 测试无效JSON
        invalid_json = "invalid json"
        await manager._process_text_message(invalid_json)  # 不应该抛出异常

        # 测试非io类型消息
        non_io_message = '{"type": "other", "data": "test"}'
        await manager._process_text_message(non_io_message)
        mock_hub.data_update_handler.assert_not_called()

    @pytest.mark.asyncio
    async def test_state_manager_schedule_retry(
        self, hass: HomeAssistant, mock_config_entry, mock_oapi_client
    ):
        """测试重试调度逻辑。"""
        from custom_components.lifesmart.hub import LifeSmartStateManager

        manager = LifeSmartStateManager(
            hass=hass,
            config_entry=mock_config_entry,
            client=mock_oapi_client,
            ws_url="wss://test.com/ws",
            refresh_callback=AsyncMock(),
            max_retries=2,
        )

        # 第一次重试
        with patch("asyncio.sleep") as mock_sleep:
            await manager._schedule_retry()
            assert manager._retry_count == 1
            assert manager._last_disconnect_time is not None
            mock_sleep.assert_called_once()

        # 超过最大重试次数
        manager._retry_count = 3
        await manager._schedule_retry()
        # 重试计数应该继续增加，但不应该再调用sleep

    @pytest.mark.asyncio
    async def test_state_manager_token_refresh_handler(
        self, hass: HomeAssistant, mock_config_entry, mock_oapi_client
    ):
        """测试令牌刷新处理器。"""
        from custom_components.lifesmart.hub import LifeSmartStateManager

        manager = LifeSmartStateManager(
            hass=hass,
            config_entry=mock_config_entry,
            client=mock_oapi_client,
            ws_url="wss://test.com/ws",
            refresh_callback=AsyncMock(),
        )

        # 设置令牌即将过期
        import time

        current_time = int(time.time())
        manager._token_expiry_time = current_time + 1000  # 很快过期

        with patch("asyncio.sleep") as mock_sleep, patch(
            "time.time", return_value=current_time
        ):
            # 模拟令牌刷新成功
            mock_oapi_client.async_refresh_token.return_value = {
                "usertoken": "new_token",
                "expiredtime": current_time + 10000,
            }

            # 启动刷新任务并快速停止
            manager._should_stop = False
            task = asyncio.create_task(manager._token_refresh_handler())
            await asyncio.sleep(0.1)  # 让任务运行一点
            manager._should_stop = True

            try:
                await asyncio.wait_for(task, timeout=1.0)
            except asyncio.TimeoutError:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    @pytest.mark.asyncio
    async def test_state_manager_auth_with_disconnect_recovery(
        self, hass: HomeAssistant, mock_config_entry, mock_oapi_client
    ):
        """测试认证成功后的断线恢复逻辑。"""
        from custom_components.lifesmart.hub import LifeSmartStateManager
        from datetime import datetime, timedelta
        import aiohttp
        import json

        manager = LifeSmartStateManager(
            hass=hass,
            config_entry=mock_config_entry,
            client=mock_oapi_client,
            ws_url="wss://test.com/ws",
            refresh_callback=AsyncMock(),
        )

        # 设置长时间断线
        manager._last_disconnect_time = datetime.now() - timedelta(minutes=35)

        # 模拟WebSocket连接和认证成功
        mock_ws = AsyncMock()
        manager._ws = mock_ws

        auth_response = AsyncMock()
        auth_response.type = aiohttp.WSMsgType.TEXT
        auth_response.data = json.dumps({"code": 0, "message": "success"})
        mock_ws.receive.return_value = auth_response

        await manager._perform_auth()

        # 验证全量刷新被触发
        manager.refresh_callback.assert_called_once()
        assert manager._last_disconnect_time is None
        assert manager._retry_count == 0

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

    @pytest.mark.asyncio
    async def test_hub_setup_local_connection_failure(
        self, hass: HomeAssistant, mock_config_entry_local
    ):
        """测试本地模式连接失败的处理。"""
        hub = LifeSmartHub(hass, mock_config_entry_local)

        with patch(
            "custom_components.lifesmart.hub.LifeSmartLocalTCPClient"
        ) as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.async_get_all_devices.return_value = []  # 空设备列表

            with pytest.raises(ConfigEntryNotReady):
                await hub.async_setup()

    @pytest.mark.asyncio
    async def test_hub_setup_local_exception(
        self, hass: HomeAssistant, mock_config_entry_local
    ):
        """测试本地模式设置时的异常处理。"""
        hub = LifeSmartHub(hass, mock_config_entry_local)

        with patch(
            "custom_components.lifesmart.hub.LifeSmartLocalTCPClient"
        ) as mock_client_class:
            mock_client_class.side_effect = Exception("Connection error")

            with pytest.raises(ConfigEntryNotReady):
                await hub.async_setup()

    @pytest.mark.asyncio
    async def test_hub_setup_oapi_auth_error_password_login(
        self, hass: HomeAssistant, mock_config_entry_oapi
    ):
        """测试密码登录时的认证错误处理。"""
        # 将配置条目添加到hass并修改配置为密码登录
        mock_config_entry_oapi.add_to_hass(hass)
        hass.config_entries.async_update_entry(
            mock_config_entry_oapi,
            data={
                **mock_config_entry_oapi.data,
                CONF_LIFESMART_AUTH_METHOD: "password",
            },
        )

        hub = LifeSmartHub(hass, mock_config_entry_oapi)

        with patch(
            "custom_components.lifesmart.hub.LifeSmartOAPIClient"
        ) as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.login_async.side_effect = LifeSmartAuthError("Login failed")

            with pytest.raises(ConfigEntryNotReady):
                await hub.async_setup()

    @pytest.mark.asyncio
    async def test_hub_setup_api_error(
        self, hass: HomeAssistant, mock_config_entry_oapi
    ):
        """测试 API 错误的处理。"""
        hub = LifeSmartHub(hass, mock_config_entry_oapi)

        with patch(
            "custom_components.lifesmart.hub.LifeSmartOAPIClient"
        ) as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.async_refresh_token.side_effect = LifeSmartAPIError("API Error")

            with pytest.raises(ConfigEntryNotReady):
                await hub.async_setup()

    @pytest.mark.asyncio
    async def test_data_update_handler_filtered_device(
        self, hass: HomeAssistant, mock_config_entry_oapi
    ):
        """测试被过滤设备的数据更新处理。"""
        mock_config_entry_oapi.add_to_hass(hass)
        hub = LifeSmartHub(hass, mock_config_entry_oapi)

        # 设置过滤配置
        hass.config_entries.async_update_entry(
            mock_config_entry_oapi,
            options={
                CONF_EXCLUDE_ITEMS: "filtered_device",
                CONF_EXCLUDE_AGTS: "filtered_hub",
            },
        )

        # 测试被过滤的设备数据
        filtered_data = {
            "msg": {
                DEVICE_TYPE_KEY: "SL_SW",
                HUB_ID_KEY: "filtered_hub",
                DEVICE_ID_KEY: "dev1",
                SUBDEVICE_INDEX_KEY: "L1",
            }
        }

        with patch(
            "custom_components.lifesmart.hub.dispatcher_send"
        ) as mock_dispatcher:
            await hub.data_update_handler(filtered_data)
            mock_dispatcher.assert_not_called()

    @pytest.mark.asyncio
    async def test_data_update_handler_error_handling(
        self, hass: HomeAssistant, mock_config_entry_oapi
    ):
        """测试数据更新处理中的错误处理。"""
        mock_config_entry_oapi.add_to_hass(hass)
        hub = LifeSmartHub(hass, mock_config_entry_oapi)

        # 测试无效数据
        invalid_data = {"invalid": "data"}
        await hub.data_update_handler(invalid_data)  # 不应该抛出异常

        # 测试包含异常的数据处理
        exception_data = {
            "msg": {
                DEVICE_TYPE_KEY: "SL_SW",
                HUB_ID_KEY: "hub1",
                DEVICE_ID_KEY: "dev1",
                SUBDEVICE_INDEX_KEY: "L1",
            }
        }

        with patch(
            "custom_components.lifesmart.hub.generate_unique_id",
            side_effect=Exception("Test error"),
        ):
            await hub.data_update_handler(exception_data)  # 不应该抛出异常

    @pytest.mark.asyncio
    async def test_handle_ai_event(self, hass: HomeAssistant, mock_config_entry_oapi):
        """测试 AI 事件处理。"""
        mock_config_entry_oapi.add_to_hass(hass)
        hub = LifeSmartHub(hass, mock_config_entry_oapi)

        # 设置 AI 包含配置
        hass.config_entries.async_update_entry(
            mock_config_entry_oapi,
            options={
                CONF_AI_INCLUDE_ITEMS: "ai_device",
                CONF_AI_INCLUDE_AGTS: "ai_hub",
            },
        )

        # 模拟 AI 事件数据
        ai_event_data = {
            DEVICE_TYPE_KEY: "SL_SCENE",
            HUB_ID_KEY: "ai_hub",
            DEVICE_ID_KEY: "ai_device",
        }

        hub._handle_ai_event(ai_event_data, "ai_device", "ai_hub")

    @pytest.mark.asyncio
    async def test_async_register_hubs(
        self, hass: HomeAssistant, mock_config_entry_oapi
    ):
        """测试中枢设备注册功能。"""
        mock_config_entry_oapi.add_to_hass(hass)
        hub = LifeSmartHub(hass, mock_config_entry_oapi)

        # 设置测试设备数据
        hub.devices = [
            {HUB_ID_KEY: "hub1", DEVICE_ID_KEY: "dev1"},
            {HUB_ID_KEY: "hub2", DEVICE_ID_KEY: "dev2"},
            {"invalid": "device"},  # 没有hub_id的设备
        ]

        await hub._async_register_hubs()

        # 验证设备注册表中的设备
        import homeassistant.helpers.device_registry as dr

        registry = dr.async_get(hass)
        hub1_device = registry.async_get_device(identifiers={(DOMAIN, "hub1")})
        hub2_device = registry.async_get_device(identifiers={(DOMAIN, "hub2")})

        assert hub1_device is not None, "Hub1 应该被注册"
        assert hub2_device is not None, "Hub2 应该被注册"
        assert "LifeSmart Hub" in hub1_device.name, "Hub名称应该正确"

    @pytest.mark.asyncio
    async def test_cleanup_local_task(
        self, hass: HomeAssistant, mock_config_entry_local
    ):
        """测试本地任务清理功能。"""
        hub = LifeSmartHub(hass, mock_config_entry_local)

        # 创建一个模拟任务
        async def dummy_task():
            await asyncio.sleep(1)

        task = asyncio.create_task(dummy_task())
        hub._local_task = task

        # 测试清理
        await hub._cleanup_local_task()
        assert task.cancelled(), "任务应该被取消"

        # 测试已完成任务的清理
        completed_task = asyncio.create_task(asyncio.sleep(0))
        await completed_task
        hub._local_task = completed_task
        await hub._cleanup_local_task()  # 不应该抛出异常

    @pytest.mark.asyncio
    async def test_hub_setup_token_update(
        self, hass: HomeAssistant, mock_config_entry_oapi
    ):
        """测试设置过程中的令牌更新。"""
        mock_config_entry_oapi.add_to_hass(hass)
        hub = LifeSmartHub(hass, mock_config_entry_oapi)

        with patch(
            "custom_components.lifesmart.hub.LifeSmartOAPIClient"
        ) as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.async_get_all_devices = AsyncMock(return_value=[])
            # 模拟令牌刷新返回新令牌
            mock_client.async_refresh_token = AsyncMock(
                return_value={
                    "usertoken": "updated_token",
                    "expiredtime": 9999999999,
                }
            )
            mock_client.get_wss_url.return_value = "wss://test.com/ws"

            with patch(
                "custom_components.lifesmart.hub.LifeSmartStateManager"
            ) as mock_state_manager_class:
                mock_state_manager_instance = MagicMock()
                mock_state_manager_instance.set_token_expiry = MagicMock()
                mock_state_manager_instance.start = MagicMock()
                mock_state_manager_instance.stop = AsyncMock()
                mock_state_manager_class.return_value = mock_state_manager_instance

                result = await hub.async_setup()

                assert result is True
                # 验证配置条目是否被更新
                assert (
                    hub.config_entry.data.get("usertoken") == "updated_token"
                ), "配置条目应该被更新为新令牌"

                await hub.async_unload()

    @pytest.mark.asyncio
    async def test_local_update_callback(
        self, hass: HomeAssistant, mock_config_entry_local
    ):
        """测试本地更新回调。"""
        hub = LifeSmartHub(hass, mock_config_entry_local)

        # 模拟数据更新处理器
        hub.data_update_handler = AsyncMock()

        test_data = {"test": "data"}
        await hub._local_update_callback(test_data)

        hub.data_update_handler.assert_called_once_with(test_data)
