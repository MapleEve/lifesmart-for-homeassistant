"""LifeSmart 集成的中央协调器 Hub。

此模块包含 LifeSmartHub 类，负责：
- 管理客户端实例（OAPI 或 Local TCP）
- 维护设备列表
- 处理实时状态更新分发
- 管理 WebSocket 连接和令牌刷新
- 提供统一的数据访问接口

由 @MapleEve 创建，作为集成架构重构的一部分。
"""

import asyncio
import json
import logging
import time
import traceback
from datetime import datetime, timedelta
from typing import Optional

import aiohttp
from homeassistant.config_entries import CONN_CLASS_CLOUD_PUSH, ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_REGION,
    CONF_TYPE,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.event import async_track_time_interval

from .client import LifeSmartTCPClient, LifeSmartOpenAPIClient
from .client_base import LifeSmartClientBase
# aiohttp 版本兼容性处理
from .compatibility import get_ws_timeout
from .const import (
    CONF_AI_INCLUDE_AGTS,
    CONF_AI_INCLUDE_ITEMS,
    CONF_EXCLUDE_AGTS,
    CONF_EXCLUDE_ITEMS,
    CONF_LIFESMART_APPKEY,
    CONF_LIFESMART_APPTOKEN,
    CONF_LIFESMART_AUTH_METHOD,
    CONF_LIFESMART_USERID,
    CONF_LIFESMART_USERPASSWORD,
    CONF_LIFESMART_USERTOKEN,
    DEVICE_ID_KEY,
    DEVICE_TYPE_KEY,
    DOMAIN,
    HUB_ID_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    MANUFACTURER,
    SUBDEVICE_INDEX_KEY,
)
from .exceptions import LifeSmartAPIError, LifeSmartAuthError
from .helpers import generate_unique_id

_LOGGER = logging.getLogger(__name__)


class LifeSmartHub:
    """LifeSmart 集成的中央协调器。

    此类统一管理客户端、设备数据、状态更新分发等核心功能，
    为各个平台实体提供统一的数据访问接口。

    Attributes:
        hass: Home Assistant 核心实例
        config_entry: 配置条目
        client: LifeSmart 客户端实例（OAPI 或 Local TCP）
        devices: 设备列表
        _state_manager: WebSocket 状态管理器（仅 OAPI 模式）
        _local_task: 本地连接任务（仅本地模式）
        _refresh_task_unsub: 定时刷新任务取消函数
    """

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """初始化 LifeSmart Hub。

        Args:
            hass: Home Assistant 核心实例
            config_entry: 配置条目实例
        """
        self.hass = hass
        self.config_entry = config_entry
        self.client: Optional[LifeSmartClientBase] = None
        self.devices: list[dict] = []
        self._state_manager: Optional[LifeSmartStateManager] = None
        self._local_task: Optional[asyncio.Task] = None
        self._refresh_task_unsub: Optional[callable] = None

    async def async_setup(self) -> bool:
        """异步设置 Hub，包括客户端创建、设备获取和后台任务启动。

        Returns:
            如果设置成功返回 True，否则返回 False

        Raises:
            ConfigEntryNotReady: 如果设置过程中发生可重试的错误
        """
        try:
            # 1. 创建客户端并获取设备
            auth_response = await self._async_create_client_and_get_devices()

            # 2. 注册中枢设备
            await self._async_register_hubs()

            # 3. 设置后台任务
            await self._async_setup_background_tasks(auth_response)

            return True

        except (LifeSmartAuthError, ConfigEntryNotReady):
            raise
        except Exception as e:
            _LOGGER.error("设置 LifeSmart Hub 时发生未知错误: %s", e, exc_info=True)
            raise ConfigEntryNotReady(f"Hub 设置失败: {e}") from e

    async def _async_create_client_and_get_devices(self) -> Optional[dict]:
        """创建客户端并获取设备列表。

        Returns:
            认证响应数据（OAPI 模式）或 None（本地模式）

        Raises:
            LifeSmartAuthError: 认证失败
            ConfigEntryNotReady: 网络或其他可重试错误
        """
        config_data = self.config_entry.data.copy()
        conn_type = config_data.get(CONF_TYPE, CONN_CLASS_CLOUD_PUSH)
        auth_response = None

        if conn_type == CONN_CLASS_CLOUD_PUSH:
            # OAPI 模式
            auth_response = await self._setup_oapi_client(config_data)
        else:
            # 本地模式
            await self._setup_local_client()

        return auth_response

    async def _setup_oapi_client(self, config_data: dict) -> dict:
        """设置 OAPI 客户端。

        Args:
            config_data: 配置数据

        Returns:
            认证响应数据

        Raises:
            LifeSmartAuthError: 认证失败
            ConfigEntryNotReady: 网络错误
        """
        try:
            self.client = LifeSmartOpenAPIClient(
                self.hass,
                config_data.get(CONF_REGION),
                config_data.get(CONF_LIFESMART_APPKEY),
                config_data.get(CONF_LIFESMART_APPTOKEN),
                config_data.get(CONF_LIFESMART_USERTOKEN),
                config_data.get(CONF_LIFESMART_USERID),
                config_data.get(CONF_LIFESMART_USERPASSWORD),
            )

            # 处理认证和令牌刷新
            auth_response = await self._handle_oapi_authentication(config_data)

            # 获取设备列表
            self.devices = await self.client.async_get_all_devices()
            return auth_response

        except LifeSmartAuthError as e:
            _LOGGER.error("OAPI 客户端认证失败")
            raise ConfigEntryNotReady(f"认证失败: {e}") from e
        except LifeSmartAPIError as e:
            _LOGGER.error("OAPI 客户端 API 错误")
            raise ConfigEntryNotReady(f"API错误: {e}") from e

    async def _handle_oapi_authentication(self, config_data: dict) -> dict:
        """处理 OAPI 认证流程。

        Args:
            config_data: 配置数据

        Returns:
            认证响应数据
        """
        auth_response = None

        # 如果使用密码登录，先获取初始令牌
        if config_data.get(CONF_LIFESMART_AUTH_METHOD) == "password":
            _LOGGER.info("通过密码登录获取初始令牌...")
            auth_response = await self.client.login_async()

        # 刷新令牌以确保状态同步
        _LOGGER.info("正在刷新令牌以确保状态同步...")
        try:
            auth_response = await self.client.async_refresh_token()
            # 如果令牌有更新，持久化到配置
            if config_data.get("usertoken") != auth_response.get("usertoken"):
                config_data["usertoken"] = auth_response["usertoken"]
                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=config_data
                )
        except LifeSmartAuthError as e:
            # 如果刷新失败且不是密码登录，触发重新认证
            if config_data.get(CONF_LIFESMART_AUTH_METHOD) != "password":
                _LOGGER.error("令牌已失效，需要重新认证: %s", e)
                self.config_entry.async_start_reauth(self.hass)
                raise ConfigEntryNotReady("令牌已失效，请重新认证。") from e

        return auth_response

    async def _setup_local_client(self) -> None:
        """设置本地 TCP 客户端。

        Raises:
            ConfigEntryNotReady: 连接失败
        """
        try:
            self.client = LifeSmartTCPClient(
                self.config_entry.data[CONF_HOST],
                self.config_entry.data[CONF_PORT],
                self.config_entry.data[CONF_USERNAME],
                self.config_entry.data[CONF_PASSWORD],
                self.config_entry.entry_id,
            )

            # 创建连接任务
            self._local_task = self.hass.async_create_task(
                self.client.async_connect(self._local_update_callback)
            )

            # 获取设备列表
            self.devices = await self.client.async_get_all_devices()
            if not self.devices:
                await self._cleanup_local_task()
                raise ConfigEntryNotReady("从本地网关获取设备列表失败。")

        except Exception as e:
            _LOGGER.error("设置本地连接失败: %s", e, exc_info=True)
            await self._cleanup_local_task()
            raise ConfigEntryNotReady from e

    async def _local_update_callback(self, data: dict) -> None:
        """本地连接的数据更新回调函数。

        Args:
            data: 接收到的数据
        """
        await self.data_update_handler(data)

    async def _cleanup_local_task(self) -> None:
        """清理本地连接任务。"""
        if self._local_task and not self._local_task.done():
            self._local_task.cancel()
            try:
                await self._local_task
            except asyncio.CancelledError:
                pass

    async def _async_register_hubs(self) -> None:
        """在设备注册表中注册中枢设备。"""
        registry = dr.async_get(self.hass)
        hubs = {d[HUB_ID_KEY] for d in self.devices if HUB_ID_KEY in d}
        for hub_id in hubs:
            registry.async_get_or_create(
                config_entry_id=self.config_entry.entry_id,
                identifiers={(DOMAIN, hub_id)},
                manufacturer=MANUFACTURER,
                name=f"LifeSmart Hub ({hub_id[-6:]})",
                model="LifeSmart Gateway",
            )

    async def _async_setup_background_tasks(
        self, auth_response: Optional[dict]
    ) -> None:
        """设置后台任务。

        Args:
            auth_response: OAPI 认证响应数据
        """
        # 设置定时刷新任务
        self._refresh_task_unsub = async_track_time_interval(
            self.hass, self._async_periodic_refresh, timedelta(minutes=10)
        )

        # OAPI 模式下设置 WebSocket 状态管理器
        if self.client and hasattr(self.client, "get_wss_url"):
            self._state_manager = LifeSmartStateManager(
                hass=self.hass,
                config_entry=self.config_entry,
                client=self.client,
                ws_url=self.client.get_wss_url(),
                refresh_callback=self._async_periodic_refresh,
            )

            # 设置令牌过期时间
            if auth_response and "expiredtime" in auth_response:
                self._state_manager.set_token_expiry(auth_response["expiredtime"])

            self._state_manager.start()

    async def _async_periodic_refresh(self, now=None) -> None:
        """定时刷新设备数据。

        Args:
            now: 当前时间（由定时器传入）
        """
        try:
            _LOGGER.debug("开始定时刷新设备数据。")
            new_devices = await self.client.async_get_all_devices()
            self.devices = new_devices
            dispatcher_send(self.hass, LIFESMART_SIGNAL_UPDATE_ENTITY)
            _LOGGER.debug("全局设备数据刷新完成。")
        except (LifeSmartAPIError, LifeSmartAuthError) as e:
            _LOGGER.warning("因 API/认证 错误，定时刷新失败: %s", e)
        except Exception as e:
            _LOGGER.warning("定时刷新时发生意外错误: %s", e)

    async def data_update_handler(self, raw_data: dict) -> None:
        """处理实时设备状态更新。

        Args:
            raw_data: 从 WebSocket 或本地连接收到的原始数据
        """
        try:
            data = raw_data.get("msg", {})
            if not data:
                _LOGGER.debug("收到空数据包，已忽略: %s", raw_data)
                return

            # 解析关键字段
            device_type = data.get(DEVICE_TYPE_KEY, "unknown")
            hub_id = data.get(HUB_ID_KEY, "").strip()
            device_id = data.get(DEVICE_ID_KEY, "").strip()
            sub_device_key = str(data.get(SUBDEVICE_INDEX_KEY, "")).strip()

            # 应用过滤器
            if self._should_filter_device(device_id, hub_id):
                return

            # 处理特殊子设备（AI事件）
            if sub_device_key == "s":
                self._handle_ai_event(data, device_id, hub_id)
                return

            # 分发普通设备更新
            unique_id = generate_unique_id(
                device_type, hub_id, device_id, sub_device_key
            )
            dispatcher_send(
                self.hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", data
            )

            _LOGGER.debug(
                "状态更新已派发 -> %s: %s",
                unique_id,
                json.dumps(data, ensure_ascii=False),
            )

        except Exception as e:
            _LOGGER.error("处理设备更新时发生异常: %s\n原始数据: %s", str(e), raw_data)

    def _should_filter_device(self, device_id: str, hub_id: str) -> bool:
        """检查设备是否应被过滤。

        Args:
            device_id: 设备 ID
            hub_id: 中枢 ID

        Returns:
            如果应该过滤返回 True
        """
        options = self.config_entry.options
        exclude_devices = {
            dev.strip()
            for dev in options.get(CONF_EXCLUDE_ITEMS, "").split(",")
            if dev.strip()
        }
        exclude_hubs = {
            hub.strip()
            for hub in options.get(CONF_EXCLUDE_AGTS, "").split(",")
            if hub.strip()
        }
        return device_id in exclude_devices or hub_id in exclude_hubs

    def _handle_ai_event(self, data: dict, device_id: str, hub_id: str) -> None:
        """处理 AI 事件。

        Args:
            data: 事件数据
            device_id: 设备 ID
            hub_id: 中枢 ID
        """
        options = self.config_entry.options
        ai_include_hubs = {
            hub.strip()
            for hub in options.get(CONF_AI_INCLUDE_AGTS, "").split(",")
            if hub.strip()
        }
        ai_include_items = {
            item.strip()
            for item in options.get(CONF_AI_INCLUDE_ITEMS, "").split(",")
            if item.strip()
        }
        if device_id in ai_include_items and hub_id in ai_include_hubs:
            _LOGGER.info("触发AI事件: %s", data)

    async def async_unload(self) -> None:
        """卸载 Hub，清理所有资源。"""
        _LOGGER.info("正在卸载 LifeSmart Hub...")

        # 停止定时刷新任务
        if self._refresh_task_unsub:
            self._refresh_task_unsub()

        # 停止 WebSocket 状态管理器
        if self._state_manager:
            await self._state_manager.stop()

        # 清理本地连接
        if self.client and hasattr(self.client, "disconnect"):
            # 检查 disconnect 方法是否是协程，如果是则等待
            disconnect_result = self.client.disconnect()
            if asyncio.iscoroutine(disconnect_result):
                await disconnect_result
            if self._local_task:
                self._local_task.cancel()
                try:
                    await self._local_task
                except asyncio.CancelledError:
                    pass

        _LOGGER.info("LifeSmart Hub 已成功卸载。")

    # 便利方法，供平台实体使用
    def get_devices(self) -> list[dict]:
        """获取设备列表。

        Returns:
            设备列表
        """
        return self.devices

    def get_client(self) -> LifeSmartClientBase:
        """获取客户端实例。

        Returns:
            客户端实例
        """
        return self.client

    def get_exclude_config(self) -> tuple[set[str], set[str]]:
        """获取排除配置。

        Returns:
            (排除设备集合, 排除中枢集合)
        """
        options = self.config_entry.options
        exclude_devices = {
            dev.strip()
            for dev in options.get(CONF_EXCLUDE_ITEMS, "").split(",")
            if dev.strip()
        }
        exclude_hubs = {
            hub.strip()
            for hub in options.get(CONF_EXCLUDE_AGTS, "").split(",")
            if hub.strip()
        }
        return exclude_devices, exclude_hubs


class LifeSmartStateManager:
    """LifeSmart WebSocket 状态管理器。

    负责维护与 LifeSmart 云端的 WebSocket 长连接，处理实时状态更新、
    认证、心跳维持以及连接中断后的自动重连。
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: LifeSmartOpenAPIClient,
        ws_url: str,
        refresh_callback: callable,
        retry_interval: int = 10,
        max_retries: int = 60,
    ) -> None:
        """初始化 WebSocket 状态管理器。

        Args:
            hass: Home Assistant 核心实例
            config_entry: 集成配置条目
            client: OAPI 客户端实例
            ws_url: WebSocket 连接地址
            refresh_callback: 全量刷新回调函数
            retry_interval: 初始重试间隔（秒）
            max_retries: 最大重试次数
        """
        self.hass = hass
        self.config_entry = config_entry
        self.client = client
        self.ws_url = ws_url
        self.refresh_callback = refresh_callback
        self.retry_interval = retry_interval
        self.max_retries = max_retries
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._connection_lock = asyncio.Lock()
        self._retry_count = 0
        self._ws_task: Optional[asyncio.Task] = None
        self._token_task: Optional[asyncio.Task] = None
        self._should_stop = False
        self._last_disconnect_time: Optional[datetime] = None
        self._token_expiry_time: int = 0
        self._token_refresh_event = asyncio.Event()

    def start(self) -> None:
        """启动 WebSocket 连接和令牌刷新管理循环。"""
        if not self._ws_task or self._ws_task.done():
            self._should_stop = False
            self._ws_task = self.hass.loop.create_task(self._connection_handler())
            _LOGGER.info("LifeSmart WebSocket 状态管理器已启动。")
        if not self._token_task or self._token_task.done():
            self._token_task = self.hass.loop.create_task(self._token_refresh_handler())
            _LOGGER.info("LifeSmart 令牌刷新管理器已启动。")

    def set_token_expiry(self, expiry_timestamp: int):
        """设置令牌的过期时间戳。

        Args:
            expiry_timestamp: 过期时间戳
        """
        self._token_expiry_time = expiry_timestamp
        self._token_refresh_event.set()
        _LOGGER.info(
            "令牌过期时间已设置为: %s", datetime.fromtimestamp(expiry_timestamp)
        )

    async def _connection_handler(self):
        """主连接处理循环。"""
        while not self._should_stop and self._retry_count <= self.max_retries:
            try:
                async with self._connection_lock:
                    _LOGGER.info("正在尝试建立 WebSocket 连接...")
                    self._ws = await self._create_websocket()
                    _LOGGER.info("WebSocket 底层连接已建立，正在进行认证...")
                    await self._perform_auth()
                    _LOGGER.info("认证成功，开始监听消息...")
                    await self._message_consumer()

            except PermissionError as e:
                _LOGGER.critical("WebSocket 认证失败，不可恢复的错误: %s", e)
                break

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                _LOGGER.warning(
                    "WebSocket 网络错误，将进行重试 (%d/%d): %s",
                    self._retry_count + 1,
                    self.max_retries,
                    e,
                )
                await self._schedule_retry()

            except Exception as e:
                _LOGGER.error(
                    "WebSocket 连接处理器发生未捕获的异常: %s\n%s",
                    e,
                    traceback.format_exc(),
                )
                await self._schedule_retry()

    async def _create_websocket(self) -> aiohttp.ClientWebSocketResponse:
        """创建新的 WebSocket 连接。

        Returns:
            WebSocket 连接实例

        Raises:
            aiohttp.ClientConnectorCertificateError: SSL 证书验证失败
        """
        session = async_get_clientsession(self.hass)
        try:
            return await session.ws_connect(
                self.ws_url,
                heartbeat=25,
                compress=15,
                timeout=get_ws_timeout(30),
            )
        except aiohttp.ClientConnectorCertificateError as e:
            _LOGGER.error("SSL 证书验证失败，请检查服务器区域设置: %s", e)
            raise

    async def _perform_auth(self):
        """执行 WebSocket 认证流程。

        Raises:
            PermissionError: 认证失败
        """
        auth_payload = self.client.generate_wss_auth()
        _LOGGER.debug("发送 WebSocket 认证载荷: %s", auth_payload)
        await self._ws.send_str(auth_payload)

        response = await self._ws.receive(timeout=30)
        if response.type != aiohttp.WSMsgType.TEXT:
            raise PermissionError(f"服务器返回了非预期的响应类型: {response.type}")

        data = json.loads(response.data)
        _LOGGER.debug("收到 WebSocket 认证响应: %s", data)

        if not (data.get("code") == 0 and data.get("message") == "success"):
            error_msg = data.get("message", "未知认证错误")
            raise PermissionError(f"认证被服务器拒绝: {error_msg}")

        _LOGGER.info("✅ WebSocket 认证成功。")

        # 处理断线重连后的全量刷新
        if self._last_disconnect_time:
            disconnect_duration = datetime.now() - self._last_disconnect_time
            if disconnect_duration > timedelta(minutes=30):
                _LOGGER.warning(
                    "WebSocket 断开已超过 %d 分钟，将触发一次全量设备刷新。",
                    int(disconnect_duration.total_seconds() / 60),
                )
                self.hass.loop.create_task(self.refresh_callback())

        # 连接成功后重置状态
        self._last_disconnect_time = None
        self._retry_count = 0

    async def _message_consumer(self):
        """持续消费来自 WebSocket 的消息。

        Raises:
            asyncio.CancelledError: 任务被取消
        """
        try:
            async for msg in self._ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._process_text_message(msg.data)
                elif msg.type in (aiohttp.WSMsgType.ERROR, aiohttp.WSMsgType.CLOSED):
                    _LOGGER.warning("WebSocket 连接已关闭或出错，将重新连接。")
                    break
        except asyncio.CancelledError:
            _LOGGER.info("WebSocket 消息监听任务已被取消。")
            raise
        except Exception:
            _LOGGER.error("在消息消费循环中发生异常，将重新连接。")
            raise

    async def _process_text_message(self, raw_data: str):
        """处理单条文本消息。

        Args:
            raw_data: 原始消息数据
        """
        try:
            _LOGGER.debug("收到 WebSocket 消息: %s", raw_data)
            data = json.loads(raw_data)
            if data.get("type") == "io":
                # 通过 hass.data 获取 hub 实例
                hub = self.hass.data[DOMAIN][self.config_entry.entry_id]["hub"]
                await hub.data_update_handler(data)
        except json.JSONDecodeError:
            _LOGGER.warning("无法解析收到的 WebSocket 消息: %s", raw_data[:200])
        except Exception as e:
            _LOGGER.error("处理 WebSocket 消息时发生错误: %s", e)

    async def _schedule_retry(self):
        """调度下一次重连尝试。"""
        if self._last_disconnect_time is None:
            self._last_disconnect_time = datetime.now()

        self._retry_count += 1
        if self._retry_count > self.max_retries:
            _LOGGER.error("已达到最大重试次数 (%s)，将停止尝试连接。", self.max_retries)
            return

        delay = min(self.retry_interval * (2 ** (self._retry_count - 1)), 300)
        _LOGGER.info(
            "WebSocket 连接断开，将在 %.1f 秒后进行第 %d 次重试。",
            delay,
            self._retry_count,
        )
        await asyncio.sleep(delay)

    async def _token_refresh_handler(self):
        """后台任务，定期检查和刷新令牌。"""
        await asyncio.sleep(60)  # 启动后等待
        check_interval_seconds = 3600  # 1小时检查一次

        while not self._should_stop:
            try:
                # 等待令牌过期时间设置
                if self._token_expiry_time == 0:
                    await asyncio.sleep(check_interval_seconds)
                    continue

                now = int(time.time())
                time_to_expiry = self._token_expiry_time - now
                refresh_threshold = 275 * 24 * 3600  # 275天

                if time_to_expiry < refresh_threshold:
                    _LOGGER.info(
                        "令牌即将在 %.1f 小时内过期，开始刷新...", time_to_expiry / 3600
                    )
                    try:
                        new_token_data = await self.client.async_refresh_token()

                        # 更新配置并设置新的过期时间
                        current_data = self.config_entry.data.copy()
                        current_data[CONF_LIFESMART_USERTOKEN] = new_token_data[
                            "usertoken"
                        ]
                        self.hass.config_entries.async_update_entry(
                            self.config_entry, data=current_data
                        )
                        self.set_token_expiry(new_token_data["expiredtime"])
                        _LOGGER.info("令牌刷新成功。")

                    except LifeSmartAuthError as e:
                        _LOGGER.error("自动刷新令牌失败: %s。将在1小时后重试。", e)
                else:
                    _LOGGER.debug(
                        "令牌有效期充足 (剩余 %.1f 小时)。",
                        time_to_expiry / 3600,
                    )

                await asyncio.sleep(check_interval_seconds)

            except asyncio.CancelledError:
                _LOGGER.info("令牌刷新任务已被取消。")
                break
            except Exception as e:
                _LOGGER.error("令牌刷新处理器发生异常: %s。", e)
                await asyncio.sleep(check_interval_seconds)

    async def stop(self):
        """停止 WebSocket 连接和管理任务。"""
        _LOGGER.info("正在停止 LifeSmart WebSocket 状态管理器...")
        self._should_stop = True

        # 关闭 WebSocket 连接
        if self._ws and not self._ws.closed:
            await self._ws.close(code=1000)

        # 取消任务
        if self._ws_task:
            self._ws_task.cancel()
        if self._token_task:
            self._token_task.cancel()

        # 等待任务完成
        await asyncio.gather(
            self._ws_task if self._ws_task else asyncio.sleep(0),
            self._token_task if self._token_task else asyncio.sleep(0),
            return_exceptions=True,
        )
        _LOGGER.info("LifeSmart 状态管理器已完全停止。")
