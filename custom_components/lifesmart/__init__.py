"""HACS implementation of LifeSmart by @MapleEve"""

import asyncio
import json
import logging
import traceback
from importlib import reload
from typing import Any, Optional, Tuple

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
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.entity import Entity
from homeassistant.util.ssl import get_default_context

from . import lifesmart_protocol
from .const import (
    BINARY_SENSOR_TYPES,
    CLIMATE_TYPES,
    CONF_AI_INCLUDE_AGTS,
    CONF_AI_INCLUDE_ITEMS,
    CONF_EXCLUDE_AGTS,
    CONF_EXCLUDE_ITEMS,
    CONF_LIFESMART_APPKEY,
    CONF_LIFESMART_APPTOKEN,
    CONF_LIFESMART_USERID,
    CONF_LIFESMART_USERTOKEN,
    COVER_TYPES,
    DEVICE_ID_KEY,
    DEVICE_NAME_KEY,
    DEVICE_TYPE_KEY,
    DOMAIN,
    EV_SENSOR_TYPES,
    GAS_SENSOR_TYPES,
    HUB_ID_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    LIFESMART_STATE_MANAGER,
    LIGHT_DIMMER_TYPES,
    LIGHT_SWITCH_TYPES,
    LOCK_TYPES,
    OT_SENSOR_TYPES,
    SMART_PLUG_TYPES,
    SPOT_TYPES,
    SUBDEVICE_INDEX_KEY,
    SUPPORTED_PLATFORMS,
    SUPPORTED_SUB_BINARY_SENSORS,
    SUPPORTED_SUB_SWITCH_TYPES,
    SUPPORTED_SWTICH_TYPES,
    MANUFACTURER,
    UPDATE_LISTENER,
)
from .lifesmart_client import LifeSmartClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up LifeSmart integration from config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Initialize client
    client = None
    if config_entry.data.get(CONF_TYPE, CONN_CLASS_CLOUD_PUSH) == CONN_CLASS_CLOUD_PUSH:
        app_key = config_entry.data.get(CONF_LIFESMART_APPKEY)
        app_token = config_entry.data.get(CONF_LIFESMART_APPTOKEN)
        user_token = config_entry.data.get(CONF_LIFESMART_USERTOKEN)
        user_id = config_entry.data.get(CONF_LIFESMART_USERID)
        region = config_entry.data.get(CONF_REGION)
        client = LifeSmartClient(
            hass,
            region,
            app_key,
            app_token,
            user_token,
            user_id,
        )
    else:
        reload(lifesmart_protocol)
        client = lifesmart_protocol.LifeSmartLocalClient(
            config_entry.data[CONF_HOST],
            config_entry.data[CONF_PORT],
            config_entry.data[CONF_USERNAME],
            config_entry.data[CONF_PASSWORD],
            config_entry.entry_id,
        )

    if not client:
        _LOGGER.error("Failed to initialize client")
        return False

    # 获取设备数据
    try:
        devices = await client.get_all_device_async()
    except Exception as e:
        _LOGGER.error("Failed to fetch devices: %s", e)
        return False

    # 中枢设备注册
    registry = dr.async_get(hass)
    hubs = {d[HUB_ID_KEY] for d in devices if HUB_ID_KEY in d}
    for hub_id in hubs:
        registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            identifiers={(DOMAIN, hub_id)},
            manufacturer=MANUFACTURER,
            name=f"LifeSmart Hub ({hub_id[-6:]})",
            model="LifeSmart Gateway",
            sw_version="1.0",
        )

    # 存储配置数据
    hass.data[DOMAIN][config_entry.entry_id] = {
        "client": client,
        "devices": devices,
        "exclude_devices": config_entry.data.get(CONF_EXCLUDE_ITEMS, []),
        "exclude_hubs": config_entry.data.get(CONF_EXCLUDE_AGTS, []),
        "ai_include_hubs": config_entry.data.get(CONF_AI_INCLUDE_AGTS, []),
        "ai_include_items": config_entry.data.get(CONF_AI_INCLUDE_ITEMS, []),
        UPDATE_LISTENER: config_entry.add_update_listener(_async_update_listener),
    }

    # 加载平台组件
    await hass.config_entries.async_forward_entry_setups(
        config_entry, SUPPORTED_PLATFORMS
    )

    # Register services
    async def send_ir_keys(call):
        """处理红外指令发送"""
        await client.send_ir_key_async(
            call.data[HUB_ID_KEY],
            call.data["ai"],
            call.data[DEVICE_ID_KEY],
            call.data["category"],
            call.data["brand"],
            call.data["keys"],
        )

    async def trigger_scene(call):
        """触发场景"""
        await client.set_scene_async(
            call.data[HUB_ID_KEY],
            call.data["id"],
        )

    hass.services.async_register(DOMAIN, "send_ir_keys", send_ir_keys)
    hass.services.async_register(DOMAIN, "trigger_scene", trigger_scene)

    # 云端实时状态监听
    if isinstance(client, LifeSmartClient):
        state_manager = LifeSmartStateManager(
            hass=hass, config_entry=config_entry, ws_url=client.get_wss_url()
        )
        state_manager.start()
        hass.data[DOMAIN][LIFESMART_STATE_MANAGER] = state_manager

    # 本地模式断开连接处理
    if not isinstance(client, LifeSmartClient):
        config_entry.async_on_unload(
            hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STOP, client.async_disconnect
            )
        )

    return True


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
        device_value = data.get("val", None)

        # 获取配置参数
        # exclude_devices = config_entry.data.get(CONF_EXCLUDE_ITEMS, [])
        # exclude_hubs = config_entry.data.get(CONF_EXCLUDE_AGTS, [])
        ai_include_hubs = config_entry.data.get(CONF_AI_INCLUDE_AGTS, [])
        ai_include_items = config_entry.data.get(CONF_AI_INCLUDE_ITEMS, [])

        # ---------- 过滤器处理 ---------- #
        # 中枢级过滤
        # if hub_id in exclude_hubs:
        #     _LOGGER.debug("中枢 %s 在排除列表中，忽略更新", hub_id)
        #     return

        # 设备级过滤
        # if device_id in exclude_devices:
        #     _LOGGER.debug("设备 %s 在排除列表中，忽略更新", device_id)
        #     return

        # ---------- 特殊子设备处理 ---------- #
        # AI事件过滤 (sub_device_key == 's' 表示AI事件)
        if sub_device_key == "s":
            if device_id in ai_include_items and hub_id in ai_include_hubs:
                _LOGGER.info("触发AI事件: %s", data)
                # TODO: 这里可以扩展具体AI处理逻辑
            return

        # 门锁报警状态处理
        if device_type in LOCK_TYPES and sub_device_key == "ALM":
            entity_id = generate_entity_id(
                device_type, hub_id, device_id, sub_device_key
            )
            dispatcher_send(
                hass,
                f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}",
                {"state": device_value},
            )
            return

        # 门锁电池状态处理
        if device_type in LOCK_TYPES and sub_device_key == "BAT":
            entity_id = generate_entity_id(
                device_type, hub_id, device_id, sub_device_key
            )
            dispatcher_send(
                hass,
                f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}",
                {"battery": device_value},
            )
            return

        # ---------- 普通设备更新处理 ---------- #
        # 生成实体ID (自动处理特殊字符)
        entity_id = generate_entity_id(device_type, hub_id, device_id, sub_device_key)

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
    """V2.1 完全修复的 WebSocket 管理器"""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        ws_url: str,
        retry_interval: int = 10,
        max_retries: int = 60,
    ) -> None:
        self.hass = hass
        self.config_entry = config_entry
        self.ws_url = ws_url
        self.retry_interval = retry_interval
        self.max_retries = max_retries
        self._ws = None
        self._connection_lock = asyncio.Lock()
        self._retry_count = 0
        self._task = None
        self._should_stop = False

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
            _LOGGER.debug("原始消息内容:\n%s", json.dumps(data, indent=2))

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
                desc, advice, category = _get_error_advice(error_code)

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
                    await data_update_handler(
                        self.hass, self.config_entry, {"msg": data}
                    )
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


# ======================== 辅助工具函数 ======================== #
# 错误码到友好描述的映射（可根据文档扩展）
ERROR_CODE_MAPPING = {
    10001: ("请求格式错误", "请校验JSON数据结构及字段类型"),
    10002: ("AppKey不存在", "检查集成配置中的APPKey是否正确"),
    10003: ("不⽀持HTTP GET请求", "该接口要求使用POST方法"),
    10004: ("签名⾮法", "检查时间戳和签名算法是否正确"),
    10005: ("⽤户没有授权", "请到管理平台授予访问权限", "用户授权"),
    10007: ("⾮法访问", "检查请求来源IP白名单设置", "安全策略"),
    10010: ("Method⾮法", "检查API请求方法是否被支持", "方法调用"),
    10015: ("权限不够", "联系管理员提升账户权限等级", "权限管理"),
    10017: ("数据⾮法", "校验提交的字段取值范围及格式", "数据校验"),
    10019: ("对象不存在", "检查请求中的设备/用户ID是否正确", "资源定位"),
}

# 错误分类建议模板
RECOMMENDATION_GROUP = {
    "用户授权": "请重新登录或刷新令牌",
    "安全策略": "检查网络安全配置或联系运维",
    "方法调用": "参考最新版API文档确认调用方式",
    "权限管理": "联系账户管理员调整权限设置",
    "数据校验": "使用调试工具验证数据格式",
    "资源定位": "检查请求参数的资源ID有效性",
    "default": "查看官方文档或联系技术支持",
}


def _get_error_advice(error_code: int) -> Tuple[str, str]:
    """获取错误描述和解决方案"""
    # 优先使用预定义的错误映射
    if error_code in ERROR_CODE_MAPPING:
        desc, *advice = ERROR_CODE_MAPPING[error_code]
        category = advice[1] if len(advice) > 1 else None
        advice_text = advice[0] if len(advice) > 0 else ""
        return desc, advice_text, category

    # 动态生成未知错误描述（示例）
    error_ranges = {
        (10000, 10100): "API请求错误",
        (10100, 10200): "设备操作错误",
        (20000, 20100): "服务端内部错误",
    }
    desc = next(
        (v for k, v in error_ranges.items() if k[0] <= error_code < k[1]),
        "未知业务错误",
    )
    return desc, "", None


def get_platform_by_device(device_type, sub_device=None):
    if device_type in SUPPORTED_SWTICH_TYPES:
        return Platform.SWITCH
    elif device_type in BINARY_SENSOR_TYPES:
        return Platform.BINARY_SENSOR
    elif device_type in COVER_TYPES:
        return Platform.COVER
    elif device_type in EV_SENSOR_TYPES + GAS_SENSOR_TYPES + OT_SENSOR_TYPES:
        return Platform.SENSOR
    elif device_type in SPOT_TYPES + LIGHT_SWITCH_TYPES + LIGHT_DIMMER_TYPES:
        return Platform.LIGHT
    elif device_type in CLIMATE_TYPES:
        return Platform.CLIMATE
    elif device_type in LOCK_TYPES and sub_device == "BAT":
        return Platform.SENSOR
    elif device_type in LOCK_TYPES and sub_device in ["EVTLO", "ALM"]:
        return Platform.BINARY_SENSOR
    elif device_type in SMART_PLUG_TYPES and sub_device == "P1":
        return Platform.SWITCH
    elif device_type in SMART_PLUG_TYPES and sub_device in ["P2", "P3"]:
        return Platform.SENSOR
    return ""


def generate_entity_id(
    device_type: str,  # 主设备类型（例如："SmartPlug", "DoorLock"）
    hub_id: str,  # 中枢/网关ID（例如："AG-ABCD12345"）
    device_id: str,  # 设备唯一标识（例如："DEV_001"）
    sub_device: Optional[str] = None,  # 子设备标识（例如："P1"）
) -> str:
    """生成符合Home Assistant规范的实体ID

    格式: [platform].[清理后的设备类型]_[清理后的中枢ID]_[清理后的设备ID]_[清理后的子设备] (小写)
    """
    import re

    # ------ 1. 定义参数清理函数 ------ #
    def sanitize(input_str: str) -> str:
        """清理非法字符，保留字母、数字和下划线，转为小写"""
        return re.sub(r"[^a-zA-Z0-9_]", "", input_str).lower()

    # ------ 2. 标准化各参数格式 ------ #
    safe_type = sanitize(device_type)  # 清理类型：例如 "SmartPlug/V2" → "smartsmugv2"
    safe_hub = sanitize(hub_id)  # 清理中枢ID：例如 "AG-1122" → "ag1122"
    safe_dev = sanitize(device_id)  # 清理设备ID：例如 "Bedroom_Light" → "bedroomlight"
    safe_sub = sanitize(sub_device) if sub_device else None

    # ------ 3. 确定目标平台 ------ #
    platform = get_platform_by_device(device_type, sub_device).value

    # ------ 4. 构建基础名称 ------ #
    # 主设备前缀 = 类型_中枢ID_设备ID
    base_parts = [safe_type, safe_hub, safe_dev]

    # ------ 5. 处理子设备片段 ------ #
    # 如果存在子设备，添加清理后的标识符（但需处理特殊情况）
    if safe_sub:
        # 特殊处理：调光器可能需要保留原样（例如P1P2）
        if device_type in LIGHT_DIMMER_TYPES and safe_sub in {"p1", "p2"}:
            base_parts.append(safe_sub.upper())  # 例如: ..._P1P2
        else:
            base_parts.append(safe_sub)  # 例如: ..._p1

    # ------ 6. 最终组装 ------ #
    clean_entity = "_".join(base_parts)

    # 确保长度不超过 Home Assistant 的 255 字符限制
    max_length = 255 - (len(platform) + 1)  # 平台名称和点的开销
    clean_entity = clean_entity[:max_length]

    # 格式化为完整 entity_id (例如: switch.smartplug_ag1122_dev001_p1)
    return f"{platform}.{clean_entity}"
