"""HACS implementation of LifeSmart by @MapleEve"""

import asyncio
import json
import logging
import traceback
from datetime import timedelta, datetime
from importlib import reload
from typing import Optional, Any

import aiohttp
from homeassistant.config_entries import ConfigEntry, CONN_CLASS_CLOUD_PUSH
from homeassistant.const import (
    CONF_REGION,
    CONF_TYPE,
    CONF_HOST,
    CONF_PORT,
    CONF_USERNAME,
    CONF_PASSWORD,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util.ssl import get_default_context

from . import lifesmart_protocol
from .const import (
    # --- 核心常量 ---
    DOMAIN,
    MANUFACTURER,
    UPDATE_LISTENER,
    DEVICE_ID_KEY,
    DEVICE_NAME_KEY,
    DEVICE_TYPE_KEY,
    HUB_ID_KEY,
    SUBDEVICE_INDEX_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    LIFESMART_STATE_MANAGER,
    # --- 配置相关 ---
    CONF_LIFESMART_APPKEY,
    CONF_LIFESMART_APPTOKEN,
    CONF_LIFESMART_USERID,
    CONF_LIFESMART_USERTOKEN,
    CONF_LIFESMART_USERPASSWORD,
    CONF_LIFESMART_AUTH_METHOD,
    CONF_AI_INCLUDE_AGTS,
    CONF_AI_INCLUDE_ITEMS,
    CONF_EXCLUDE_AGTS,
    CONF_EXCLUDE_ITEMS,
    # --- 设备类型聚合列表 (大列表) ---
    ALL_SWITCH_TYPES,
    ALL_LIGHT_TYPES,
    ALL_COVER_TYPES,
    ALL_BINARY_SENSOR_TYPES,
    ALL_SENSOR_TYPES,
    LIGHT_DIMMER_TYPES,
    CLIMATE_TYPES,
    LOCK_TYPES,
    CAMERA_TYPES,
    SMART_PLUG_TYPES,
    SPOT_TYPES,
    # --- 所有支持的平台列表 ---
    SUPPORTED_PLATFORMS,
)
from .diagnostics import get_error_advice, RECOMMENDATION_GROUP
from .exceptions import LifeSmartAPIError, LifeSmartAuthError
from .lifesmart_client import LifeSmartClient

_LOGGER = logging.getLogger(__name__)


# --- 主函数 ---
async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up LifeSmart integration from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # 1. 创建客户端并获取设备，处理连接和认证错误
    try:
        client, devices = await _async_create_client_and_get_devices(hass, config_entry)
    except LifeSmartAuthError:
        return False  # 认证失败，设置失败
    # ConfigEntryNotReady 会被 Home Assistant 捕获并触发重试

    # 2. 注册中枢设备
    await _async_register_hubs(hass, config_entry, devices)

    # 3. 将核心数据存入 hass.data
    hass.data[DOMAIN][config_entry.entry_id] = {
        "client": client,
        "devices": devices,
        "exclude_devices": config_entry.data.get(CONF_EXCLUDE_ITEMS, []),
        "exclude_hubs": config_entry.data.get(CONF_EXCLUDE_AGTS, []),
        "ai_include_hubs": config_entry.data.get(CONF_AI_INCLUDE_AGTS, []),
        "ai_include_items": config_entry.data.get(CONF_AI_INCLUDE_ITEMS, []),
        UPDATE_LISTENER: config_entry.add_update_listener(_async_update_listener),
    }

    # 4. 转发设置到各个平台 (switch, sensor, etc.)
    await hass.config_entries.async_forward_entry_setups(
        config_entry, SUPPORTED_PLATFORMS
    )

    # 5. 注册集成服务
    _async_register_services(hass, client)

    # 6. 设置 WebSocket 和定时刷新等后台任务
    _async_setup_background_tasks(hass, config_entry, client)

    return True


async def _async_create_client_and_get_devices(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> tuple[any, list]:
    """Create the LifeSmart client and get the initial list of devices."""
    config_data = config_entry.data
    conn_type = config_data.get(CONF_TYPE, CONN_CLASS_CLOUD_PUSH)

    if conn_type == CONN_CLASS_CLOUD_PUSH:
        # --- 云端模式 ---
        try:
            if config_data.get(CONF_LIFESMART_AUTH_METHOD) == "password":
                _LOGGER.info(
                    "Password auth method detected, logging in for a fresh token."
                )
                temp_client = LifeSmartClient(
                    hass,
                    config_data.get(CONF_REGION),
                    config_data.get(CONF_LIFESMART_APPKEY),
                    config_data.get(CONF_LIFESMART_APPTOKEN),
                    None,
                    config_data.get(CONF_LIFESMART_USERID),
                    config_data.get(CONF_LIFESMART_USERPASSWORD),
                )
                if await temp_client.login_async():
                    _LOGGER.info("Login successful, updating the user token.")
                    new_token = temp_client._usertoken
                    config_data = {**config_data, CONF_LIFESMART_USERTOKEN: new_token}
                    hass.config_entries.async_update_entry(
                        config_entry, data=config_data
                    )

            client = LifeSmartClient(
                hass,
                config_data.get(CONF_REGION),
                config_data.get(CONF_LIFESMART_APPKEY),
                config_data.get(CONF_LIFESMART_APPTOKEN),
                config_data.get(CONF_LIFESMART_USERTOKEN),
                config_data.get(CONF_LIFESMART_USERID),
            )
            devices = await client.get_all_device_async()
            return client, devices

        except LifeSmartAuthError as e:
            _LOGGER.critical(
                "Authentication failed. Please check your configuration. Error: %s", e
            )
            # 对于认证失败，我们不希望重试，直接返回失败
            raise
        except (
            LifeSmartAPIError,
            aiohttp.ClientError,
            asyncio.TimeoutError,
            Exception,
        ) as e:
            _LOGGER.error(
                "Failed to connect to the LifeSmart cloud. The integration will retry. Error: %s",
                e,
            )
            raise ConfigEntryNotReady from e

    else:
        # --- 本地模式 ---
        try:
            reload(lifesmart_protocol)
            client = lifesmart_protocol.LifeSmartLocalClient(
                config_entry.data[CONF_HOST],
                config_entry.data[CONF_PORT],
                config_entry.data[CONF_USERNAME],
                config_entry.data[CONF_PASSWORD],
                config_entry.entry_id,
            )
            devices = await client.get_all_device_async()
            if not devices:
                raise ConfigEntryNotReady("Failed to get devices from local gateway.")

            # 注册停止时的断连回调
            config_entry.async_on_unload(
                hass.bus.async_listen_once(
                    EVENT_HOMEASSISTANT_STOP, client.async_disconnect
                )
            )
            return client, devices
        except Exception as e:
            _LOGGER.error("Failed to set up local connection to LifeSmart hub: %s", e)
            raise ConfigEntryNotReady from e


async def _async_register_hubs(
    hass: HomeAssistant, config_entry: ConfigEntry, devices: list
):
    """Register LifeSmart hubs in the device registry."""
    registry = dr.async_get(hass)
    hubs = {d[HUB_ID_KEY] for d in devices if HUB_ID_KEY in d}
    for hub_id in hubs:
        registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            identifiers={(DOMAIN, hub_id)},
            manufacturer=MANUFACTURER,
            name=f"LifeSmart Hub ({hub_id[-6:]})",
            model="LifeSmart Gateway",
        )


def _async_register_services(hass: HomeAssistant, client: any):
    """Register the services for the LifeSmart integration."""

    async def send_ir_keys(call):
        """Handle sending IR keys."""
        await client.send_ir_key_async(
            call.data[HUB_ID_KEY],
            call.data["ai"],
            call.data[DEVICE_ID_KEY],
            call.data["category"],
            call.data["brand"],
            call.data["keys"],
        )

    # services.yaml 中 scene_set 的后端实现
    async def trigger_scene(call):
        """处理场景触发的服务调用."""
        # 从服务调用中获取前端传入的参数
        # call.data['agt'] 对应 services.yaml 中的 'agt' 字段
        # call.data['id'] 对应 services.yaml 中的 'id' 字段
        agt = call.data.get(HUB_ID_KEY)  # 使用常量 HUB_ID_KEY 更佳
        scene_id = call.data.get("id")

        if not agt or not scene_id:
            _LOGGER.error("触发场景失败：'agt' 和 'id' 参数不能为空。")
            return

        _LOGGER.info("正在通过服务调用触发场景: Hub=%s, SceneID=%s", agt, scene_id)

        # 调用 client 方法，与 LifeSmart API 通信
        await client.set_scene_async(agt, scene_id)

    # 注册点动开关服务
    async def press_switch(call):
        """Handle the press_switch service call."""
        entity_id = call.data.get("entity_id")
        duration = call.data.get("duration", 1000)  # 默认1秒

        entity = hass.states.get(entity_id)
        if not entity:
            _LOGGER.error("Entity not found: %s", entity_id)
            return

        # 从实体属性中获取设备信息
        agt = entity.attributes.get(HUB_ID_KEY)
        me = entity.attributes.get(DEVICE_ID_KEY)

        # 从 unique_id 中解析出 idx
        # 假设 unique_id 格式为 'switch.sl_p_sw_..._p1'
        try:
            idx = entity.unique_id.split("_")[-1]
        except (IndexError, AttributeError):
            _LOGGER.error("Could not determine idx for entity: %s", entity_id)
            return

        if not all([agt, me, idx]):
            _LOGGER.error(
                "Missing required attributes (agt, me, idx) for entity: %s", entity_id
            )
            return

        await client.press_switch_async(idx, agt, me, duration)

    hass.services.async_register(DOMAIN, "press_switch", press_switch)
    hass.services.async_register(DOMAIN, "send_ir_keys", send_ir_keys)
    hass.services.async_register(DOMAIN, "trigger_scene", trigger_scene)


def _async_setup_background_tasks(
    hass: HomeAssistant, config_entry: ConfigEntry, client: any
):
    """Set up the WebSocket manager and periodic refresh task."""

    async def _async_periodic_refresh(now=None):
        """Global device data refresh task."""
        try:
            _LOGGER.debug("Starting periodic device refresh.")
            new_devices = await client.get_all_device_async()
            hass.data[DOMAIN][config_entry.entry_id]["devices"] = new_devices
            dispatcher_send(hass, LIFESMART_SIGNAL_UPDATE_ENTITY)
            _LOGGER.debug("Global device data refresh completed.")
        except (LifeSmartAPIError, LifeSmartAuthError) as e:
            _LOGGER.warning("Periodic refresh failed due to API/Auth error: %s", e)
        except Exception as e:
            _LOGGER.warning(
                "Periodic refresh failed with an unexpected error. This may be a temporary issue. Error: %s",
                e,
            )

    # 启动 WebSocket 状态管理器（仅限云端模式）
    if isinstance(client, LifeSmartClient):
        state_manager = LifeSmartStateManager(
            hass=hass,
            config_entry=config_entry,
            ws_url=client.get_wss_url(),
            refresh_callback=_async_periodic_refresh,
        )
        state_manager.start()
        hass.data[DOMAIN][LIFESMART_STATE_MANAGER] = state_manager

    # 设置定时刷新任务（每10分钟）
    cancel_refresh = async_track_time_interval(
        hass, _async_periodic_refresh, timedelta(minutes=10)
    )
    config_entry.async_on_unload(cancel_refresh)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """正确处理集成的卸载流程"""

    entry_id = entry.entry_id

    # 停止 WebSocket 状态管理器
    if state_manager := hass.data[DOMAIN].get(LIFESMART_STATE_MANAGER):
        await state_manager.stop()

    # 解构客户端连接
    client = None
    if DOMAIN in hass.data and entry_id in hass.data[DOMAIN]:
        client = hass.data[DOMAIN][entry_id].get("client")
        if isinstance(client, lifesmart_protocol.LifeSmartLocalClient):
            await client.async_disconnect(None)

    # 卸载平台组件（必须获取返回值）
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, SUPPORTED_PLATFORMS
    )

    # 清理数据存储
    if unload_ok:
        if hass.data.get(DOMAIN):
            if entry_id in hass.data[DOMAIN]:
                hass.data[DOMAIN].pop(entry_id)
            if not hass.data[DOMAIN]:  # 最后一个实体卸载后清理根条目
                hass.data.pop(DOMAIN)

    return unload_ok


async def data_update_handler(
    hass: HomeAssistant, config_entry: ConfigEntry, raw_data
) -> None:
    """处理来自云端或本地的设备状态更新"""
    try:
        data = raw_data.get("msg", {})
        if not data:
            _LOGGER.debug("收到空数据包: %s", raw_data)
            return

        # 解析关键字段
        device_type = data.get(DEVICE_TYPE_KEY, "unknown")
        hub_id = data.get(HUB_ID_KEY, "").strip()
        device_id = data.get(DEVICE_ID_KEY, "").strip()
        sub_device_key = str(data.get(SUBDEVICE_INDEX_KEY, "")).strip()

        # 获取配置参数
        exclude_devices = config_entry.data.get(CONF_EXCLUDE_ITEMS, [])
        exclude_hubs = config_entry.data.get(CONF_EXCLUDE_AGTS, [])
        ai_include_hubs = config_entry.data.get(CONF_AI_INCLUDE_AGTS, [])
        ai_include_items = config_entry.data.get(CONF_AI_INCLUDE_ITEMS, [])

        # ---------- 过滤器处理 ---------- #
        # 转换为列表（处理空值和前后空格）
        exclude_devices = [
            dev.strip() for dev in exclude_devices.split(",") if dev.strip()
        ]
        exclude_hubs = [hub.strip() for hub in exclude_hubs.split(",") if hub.strip()]

        # ------ 过滤逻辑加强 ------ #
        # 触发排除的详细日志
        if device_id in exclude_devices:
            _LOGGER.info("忽略设备 [%s | %s]（在排除列表中）", device_id, device_type)
            return

        if hub_id in exclude_hubs:
            _LOGGER.info("忽略中枢 [%s] 下所有设备（在排除列表中）", hub_id)
            return

        # ---------- 特殊子设备处理 ---------- #
        # AI事件过滤 (sub_device_key == 's' 表示AI事件)
        if sub_device_key == "s":
            if device_id in ai_include_items and hub_id in ai_include_hubs:
                _LOGGER.info("触发AI事件: %s", data)
                # TODO: 这里可以扩展具体AI处理逻辑
            return

        # ---------- 普通设备更新处理 ---------- #
        # 生成实体ID (自动处理特殊字符)
        entity_id = generate_entity_id(device_type, hub_id, device_id, sub_device_key)
        _LOGGER.debug(
            "生成实体ID -> device_type %s, hub: %s, dev: %s, sub: %s",
            device_type,
            hub_id,
            device_id,
            sub_device_key,
        )

        # 通过dispatcher发送更新到具体实体
        dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}",
            data,  # 传递原始数据供实体解析
        )

        _LOGGER.debug(
            "状态更新已派发 -> %s: %s", entity_id, json.dumps(data, ensure_ascii=False)
        )

    except Exception as e:
        _LOGGER.error(
            "处理设备更新时发生异常: %s\n原始数据: %s",
            str(e),
            json.dumps({"raw_data": raw_data}, ensure_ascii=False),
        )


async def _async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    _LOGGER.info("更新配置，重新加载...")
    await hass.config_entries.async_reload(config_entry.entry_id)


class LifeSmartDevice(Entity):
    """LifeSmart base device."""

    def __init__(self, dev: dict, lifesmart_client: LifeSmartClient) -> None:
        """Initialize the switch."""
        self._name = dev[DEVICE_NAME_KEY]
        self._device_name = dev[DEVICE_NAME_KEY]
        self._agt = dev[HUB_ID_KEY]
        self._me = dev[DEVICE_ID_KEY]
        self._devtype = dev["devtype"]
        self._client = lifesmart_client
        self._attributes = {
            HUB_ID_KEY: self._agt,
            DEVICE_ID_KEY: self._me,
            "devtype": self._devtype,
        }

    @property
    def object_id(self) -> str:
        """Return LifeSmart device id."""
        return self.entity_id

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return self._attributes

    @property
    def name(self) -> str:
        """Return LifeSmart device name."""
        return self._name

    @property
    def assumed_state(self) -> bool:
        """Return true if we do optimistic updates."""
        return False

    @property
    def should_poll(self) -> bool:
        """Check with the entity.py for an updated state."""
        return False

    async def async_lifesmart_epset(self, type: str, val: Any, idx: str) -> Any:
        """Send command to LifeSmart device."""
        agt = self._agt
        me = self._me
        return await self._client.send_epset_async(type, val, idx, agt, me)

    async def async_lifesmart_epget(self) -> Any:
        """Get LifeSmart device info."""
        agt = self._agt
        me = self._me
        return await self._client.get_epget_async(agt, me)

    async def async_lifesmart_sceneset(self, id: str) -> Any:
        """Set the scene."""
        agt = self._agt
        response = await self._client.set_scene_async(agt, id)
        return response["code"]


class LifeSmartStateManager:
    """WebSocket 管理器"""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        ws_url: str,
        refresh_callback: callable,
        retry_interval: int = 10,
        max_retries: int = 60,
    ) -> None:
        self.hass = hass
        self.config_entry = config_entry
        self.ws_url = ws_url
        self.refresh_callback = refresh_callback
        self.retry_interval = retry_interval
        self.max_retries = max_retries
        self._ws = None
        self._connection_lock = asyncio.Lock()
        self._retry_count = 0
        self._task = None
        self._should_stop = False
        self._last_disconnect_time: Optional[datetime] = None  # WS 上次断开连接时间

    def start(self) -> None:
        """启动 WebSocket 连接管理循环"""
        if not self._task or self._task.done():
            self._close_requested = False  # 重置关闭标记
            self._task = self.hass.loop.create_task(self._connection_handler())
            _LOGGER.info("LifeSmart 状态管理器已启动")

    async def _connection_handler(self):
        """包含增强错误处理的主连接循环"""
        while not self._should_stop and self._retry_count <= self.max_retries:
            try:
                async with self._connection_lock:
                    # 🟢 第一阶段：建立底层连接
                    self._ws = await self._create_websocket()

                    # 🟢 第二阶段：V2版认证流程
                    await self._perform_v2_auth()

                    # 🟢 第三阶段：消息处理循环
                    await self._message_consumer()

            except PermissionError as e:
                # 不可恢复的认证错误
                _LOGGER.critical(
                    "认证方法被拒绝，请检查以下配置:\n"
                    "- APPKey: %s\n"
                    "- AppToken: %s\n"
                    "- 区域设置: %s\n"
                    "完整错误: %s",
                    self.config_entry.data.get(CONF_LIFESMART_APPKEY, "未配置"),
                    self.config_entry.data.get(CONF_LIFESMART_APPTOKEN, "未配置"),
                    self.config_entry.data.get(CONF_REGION, "未配置"),
                    str(e),
                )
                break

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                # 网络层错误自动重试
                _LOGGER.warning(
                    "网络错误 %s (重试 %d/%d)",
                    str(e),
                    self._retry_count + 1,
                    self.max_retries,
                )
                await self._schedule_retry()

            except Exception as e:
                # 未知错误处理
                _LOGGER.error(
                    "未捕获异常: %s\n堆栈跟踪:\n%s",
                    str(e),
                    traceback.format_exc(),
                    exc_info=True,
                )
                await self._schedule_retry()

    async def _create_websocket(self) -> aiohttp.ClientWebSocketResponse:
        """创建新的 WebSocket 连接（包含证书验证）"""
        ssl_context = get_default_context()
        session = async_get_clientsession(self.hass)

        # 重要：使用设备级加密(禁用嘈杂的日志)
        ssl_context.logging_level = logging.ERROR

        try:
            return await session.ws_connect(
                self.ws_url,
                heartbeat=25,
                compress=15,
                ssl=ssl_context,
                timeout=aiohttp.ClientTimeout(total=30),
            )
        except aiohttp.ClientConnectorCertificateError as e:
            _LOGGER.error(
                "SSL证书验证失败！可能原因：\n"
                "1. 选择的区域有误（如国际区使用中国证书）\n"
                "2. 系统根证书过期\n"
                "详细信息：%s",
                e,
            )
            raise

    async def _perform_v2_auth(self):
        """增强版认证流程（支持多种成功状态码和错误处理）"""
        client = self.hass.data[DOMAIN][self.config_entry.entry_id]["client"]
        auth_payload = client.generate_wss_auth()

        # 调试输出认证载荷
        _LOGGER.debug("认证载荷 >>> %s", json.dumps(auth_payload, indent=2))

        # Step 1: 发送认证请求
        await self._ws.send_str(auth_payload)

        # Step 2: 处理认证响应（带有超时机制）
        response = await self._ws.receive(timeout=30)

        # --- 接收消息类型验证 ---
        if response.type != aiohttp.WSMsgType.TEXT:
            raise PermissionError(f"服务器返回非文本响应类型: {response.type}")

        # --- 响应数据解析 ---
        try:
            data = json.loads(response.data)
        except json.JSONDecodeError:
            raise PermissionError(f"无效的JSON响应: {response.data[:100]}...")

        _LOGGER.debug("认证响应 <<< %s", json.dumps(data, indent=2))

        # --- 成功条件判断 ---
        success = any(
            [
                data.get("code") == 0 and data.get("message") == "success",  # 新协议
                data.get("ret") == 0 and "OK" in data.get("msg", ""),  # 旧协议兼容
                data.get("result") == "SUCCESS",  # 其他版本
                "wb hello" in data.get("msg", ""),  # 特殊握手协议
            ]
        )

        # --- 捕获特定错误 ---
        if "method not support" in str(data).lower():
            raise PermissionError(data.get("message", "unknown"))

        if not success:
            error_code = data.get("code") or data.get("ret") or "unknown"
            error_msg = data.get("message") or data.get("msg") or "无详细错误"
            _LOGGER.error("认证失败[代码 %s]: %s", error_code, error_msg)
            raise PermissionError(f"认证被拒: {error_msg} (代码 {error_code})")

        # --- 认证后处理 ---
        _LOGGER.info("✅ 认证成功 | 服务端返回: %s", data.get("msg", "无附加消息"))

        if self._last_disconnect_time:
            disconnect_duration = datetime.now() - self._last_disconnect_time
            if disconnect_duration > timedelta(minutes=30):
                _LOGGER.warning(
                    "WebSocket 断开已超过 %d 分钟，将主动触发一次全量设备刷新以确保状态同步。",
                    int(disconnect_duration.total_seconds() / 60),
                )
                # 使用 create_task 异步执行，不阻塞当前流程
                self.hass.loop.create_task(self.refresh_callback())

        # 连接成功后，重置所有状态计时器
        self._last_disconnect_time = None
        self._retry_count = 0

    async def _message_consumer(self):
        """增强消息处理（包含服务端心跳检测）"""
        _LOGGER.info("进入实时消息监听状态")

        try:
            async for msg in self._ws:

                # ===== 消息类型分发 =====
                if msg.type == aiohttp.WSMsgType.TEXT:
                    await self._process_text_message(msg.data)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    exc = self._ws.exception()
                    error_detail = {
                        "exception_type": type(exc).__name__ if exc else "Unknown",
                        "error_message": str(exc),
                        "connection_state": self._ws.closed,
                    }
                    _LOGGER.error(
                        "协议层致命错误，连接将被重置\n错误详情: %s",
                        json.dumps(error_detail, indent=2),
                    )
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    _LOGGER.warning(
                        "连接被服务端主动关闭 (状态码: %s)", self._ws.close_code
                    )
                    return
                elif msg.type == aiohttp.WSMsgType.CLOSING:
                    _LOGGER.debug("连接关闭进行中...")
                else:
                    _LOGGER.warning("收到未处理的WS消息类型: %s", msg.type)

        except asyncio.CancelledError:
            _LOGGER.info("消息监听任务已被正常终止")
        except ConnectionResetError as e:
            _LOGGER.warning("连接被重置: %s", e)
            await self._schedule_retry()
        except Exception as e:
            _LOGGER.error(
                "消息循环异常: %s\n堆栈跟踪:\n%s",
                e,
                traceback.format_exc(),
                exc_info=True,
            )
            raise

    async def _process_text_message(self, raw_data: str):
        """处理文本消息（含异常隔离）"""
        try:
            data = json.loads(raw_data)

            # ➡️ 记录原始消息（调试用）
            try:
                data_for_log = json.loads(raw_data)
                _LOGGER.debug(
                    "原始消息内容:\n%s",
                    json.dumps(data_for_log, indent=2, ensure_ascii=False),
                )
            except json.JSONDecodeError:
                _LOGGER.debug("收到非JSON格式的原始消息: %s", raw_data)

            # 🛡️ 处理平台要求的安全关闭指令
            if data.get("action") == "wb_close":
                _LOGGER.warning("收到服务端下发的强制关闭指令")
                await self._schedule_retry()

            # ✅ 认证成功回执处理
            if data.get("code") == 0 and data.get("message") == "success":
                _LOGGER.info("WebSocket连接已通过服务端验证")
                return

            # 🚨 处理错误消息
            if data.get("code") not in (None, 0):
                error_code = data.get("code")
                desc, advice, category = get_error_advice(error_code)

                # 优先显示服务器返回的message（更精准）
                error_msg = data.get("message")

                # 生成智能建议
                recommendation = []
                if advice:
                    recommendation.append(f"立即操作：{advice}")
                if category in RECOMMENDATION_GROUP:
                    recommendation.append(f"长期建议：{RECOMMENDATION_GROUP[category]}")
                else:
                    recommendation.append(f"建议：{RECOMMENDATION_GROUP['default']}")

                # 结构化日志输出
                _LOGGER.error(
                    "业务异常 | 代码: %s | 类型: %s\n"
                    "► 错误描述: %s\n"
                    "► 解决方案: %s\n"
                    "► 相关文档: https://error.info/%s",
                    error_code,
                    "严重" if error_code >= 10000 else "警告",
                    f"{desc}（{error_msg}）",
                    "\n    ".join(recommendation),
                    error_code,  # 错误码可链接到知识库
                )
                return

            # 📨 转发设备状态更新
            if data.get("type") == "io":
                try:
                    await data_update_handler(self.hass, self.config_entry, data)
                except Exception as e:
                    _LOGGER.error(
                        "状态更新分发失败: %s\n原始数据:\n%s",
                        e,
                        json.dumps(data, indent=2),
                    )

        except json.JSONDecodeError:
            _LOGGER.error("无法解析的消息内容:\n%s", raw_data[:200])
        except KeyError as e:
            _LOGGER.error("消息字段缺失: %s\n完整消息:\n%s", e, raw_data[:200])

    async def _schedule_retry(self):
        """智能重试调度器"""
        if self._last_disconnect_time is None:
            self._last_disconnect_time = datetime.now()

        self._retry_count += 1

        if self._retry_count > self.max_retries:
            _LOGGER.error(
                "⚠️ 已达到最大重试次数 %s，停止尝试连接\n",
                self.max_retries,
            )
            return

        # 指数退避算法（最大间隔5分钟）
        delay = min(self.retry_interval * 2 ** (self._retry_count - 1), 300)

        _LOGGER.warning("♻️ 将在 %.1f 秒后进行第 %d 次重试", delay, self._retry_count)

        await asyncio.sleep(delay)
        self.hass.loop.create_task(self._connection_handler())

    async def stop(self):
        """优雅停止连接"""
        self._should_stop = True
        if self._ws and not self._ws.closed:
            await self._ws.close(code=1000)
        if self._task:
            self._task.cancel()


def get_platform_by_device(device_type, sub_device=None):
    """根据设备类型和子索引，决定其所属的Home Assistant平台。"""
    if device_type in ALL_SWITCH_TYPES:
        return Platform.SWITCH
    elif device_type in ALL_LIGHT_TYPES:
        return Platform.LIGHT
    elif device_type in ALL_COVER_TYPES:
        return Platform.COVER
    elif device_type in CLIMATE_TYPES:
        return Platform.CLIMATE
    # elif device_type in CAMERA_TYPES:  # TODO:摄像头平台
    #     return Platform.CAMERA

    # --- 对复合设备进行子设备判断 ---
    # 门锁设备
    if device_type in LOCK_TYPES:
        if sub_device == "BAT":  # 门锁的电量是一个 sensor
            return Platform.SENSOR
        elif sub_device in ["EVTLO", "ALM"]:  # 门锁的事件/警报是 binary_sensor
            return Platform.BINARY_SENSOR

    # 智能插座 (某些型号的子索引是传感器)
    if device_type in SMART_PLUG_TYPES:
        if sub_device == "P1":
            return Platform.SWITCH
        elif sub_device in ["P2", "P3"]:
            return Platform.SENSOR

    # --- 将剩余的各类传感器归类 ---
    # 注意：这个判断应该在复合设备之后，避免错误分类
    if device_type in ALL_BINARY_SENSOR_TYPES:
        return Platform.BINARY_SENSOR
    if device_type in ALL_SENSOR_TYPES:
        return Platform.SENSOR

    # 如果所有条件都不满足，返回空
    return ""


def generate_entity_id(
    device_type: str,
    hub_id: str,
    device_id: str,
    sub_device: Optional[str] = None,
) -> str:
    import re

    # 清理非法字符的函数
    def sanitize(input_str: str) -> str:
        return re.sub(r"\W", "", input_str).lower()

    # 标准化参数
    safe_type = sanitize(device_type)
    safe_hub = sanitize(hub_id)
    safe_dev = sanitize(device_id)
    safe_sub = sanitize(sub_device) if sub_device else None

    # 获取平台枚举并正确处理
    platform_enum = get_platform_by_device(device_type, sub_device)
    platform_str = (
        platform_enum.value if isinstance(platform_enum, Platform) else platform_enum
    )

    # 构建实体ID基础部分
    base_parts = [safe_type, safe_hub, safe_dev]
    if safe_sub:
        if device_type in LIGHT_DIMMER_TYPES and safe_sub in {"p1", "p2"}:
            base_parts.append(safe_sub.upper())
        else:
            base_parts.append(safe_sub)

    clean_entity = "_".join(base_parts)
    max_length = 255 - (len(platform_str) + 1)
    clean_entity = clean_entity[:max_length]

    # 返回修正后的实体ID格式
    return f"{platform_str}.{clean_entity}"
