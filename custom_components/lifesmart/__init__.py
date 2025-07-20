"""由 @MapleEve 实现的 LifeSmart 集成。

此模块是 LifeSmart 集成的核心入口点，负责初始化客户端、
管理设备、设置平台以及处理与 Home Assistant 的生命周期事件。
"""

import asyncio
import json
import logging
import time
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


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """从配置条目设置 LifeSmart 集成。

    此函数是 Home Assistant 加载集成时的主要入口点。它负责协调
    客户端的创建、设备数据的获取、平台的设置以及后台任务的启动。

    Args:
        hass: Home Assistant 的核心实例。
        config_entry: 当前集成的配置条目实例。

    Returns:
        如果集成设置成功，则返回 True；否则返回 False。

    Raises:
        ConfigEntryNotReady: 如果在设置过程中发生可重试的错误（如网络问题），
                             Home Assistant 将捕获此异常并稍后重试。
    """
    hass.data.setdefault(DOMAIN, {})

    # 1. 创建客户端并获取设备，处理连接和认证错误
    try:
        client, devices, auth_response = await _async_create_client_and_get_devices(
            hass, config_entry
        )
    except LifeSmartAuthError:
        # 认证失败是不可恢复的，直接设置失败且不重试。
        return False
    # ConfigEntryNotReady 会被 Home Assistant 捕获并触发重试。

    # 2. 在设备注册表中注册中枢设备
    await _async_register_hubs(hass, config_entry, devices)

    # 3. 将核心数据（客户端、设备列表、配置等）存入 hass.data
    hass.data[DOMAIN][config_entry.entry_id] = {
        "client": client,
        "devices": devices,
        "exclude_devices": config_entry.options.get(CONF_EXCLUDE_ITEMS, ""),
        "exclude_hubs": config_entry.options.get(CONF_EXCLUDE_AGTS, ""),
        "ai_include_hubs": config_entry.options.get(CONF_AI_INCLUDE_AGTS, ""),
        "ai_include_items": config_entry.options.get(CONF_AI_INCLUDE_ITEMS, ""),
        UPDATE_LISTENER: config_entry.add_update_listener(_async_update_listener),
    }

    # 4. 将配置条目转发到各个平台（如 switch, sensor, light 等）进行设置
    await hass.config_entries.async_forward_entry_setups(
        config_entry, SUPPORTED_PLATFORMS
    )

    # 5. 注册集成提供的服务（如场景触发、红外控制等）
    _async_register_services(hass, client)

    # 6. 设置后台任务，如 WebSocket 连接和定时数据刷新、Usertoken 的定时更新
    _async_setup_background_tasks(hass, config_entry, client, auth_response)

    return True


async def _async_create_client_and_get_devices(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> tuple[Any, list, dict | None]:
    """创建 LifeSmart 客户端并获取初始设备列表。

    根据配置类型（云端或本地）初始化对应的客户端，并尝试连接和获取设备数据。
    此函数封装了连接和认证过程中的错误处理。

    Args:
        hass: Home Assistant 的核心实例。
        config_entry: 当前集成的配置条目。

    Returns:
        一个元组，包含已初始化的客户端实例和设备列表。

    Raises:
        LifeSmartAuthError: 当认证凭据无效时引发。
        ConfigEntryNotReady: 当发生网络错误或其他可重试的连接问题时引发。
    """
    config_data = config_entry.data.copy()  # 创建副本
    conn_type = config_data.get(CONF_TYPE, CONN_CLASS_CLOUD_PUSH)
    auth_response = None

    if conn_type == CONN_CLASS_CLOUD_PUSH:
        # --- 云端模式 ---
        try:
            client = LifeSmartClient(
                hass,
                config_data.get(CONF_REGION),
                config_data.get(CONF_LIFESMART_APPKEY),
                config_data.get(CONF_LIFESMART_APPTOKEN),
                config_data.get(CONF_LIFESMART_USERTOKEN),
                config_data.get(CONF_LIFESMART_USERID),
                config_data.get(CONF_LIFESMART_USERPASSWORD),
            )

            # 1. 如果使用密码，先登录获取初始令牌
            if config_data.get(CONF_LIFESMART_AUTH_METHOD) == "password":
                _LOGGER.info("通过密码登录获取初始令牌...")
                auth_response = await client.login_async()

            # 2. 无论如何，都尝试刷新一次令牌
            # 这会验证现有令牌，或使用刚登录获取的令牌来获取最新的过期时间
            _LOGGER.info("正在刷新令牌以确保状态同步...")
            try:
                auth_response = await client.async_refresh_token()
                # 刷新成功，持久化最新的令牌
                if config_data.get("usertoken") != auth_response.get("usertoken"):
                    config_data["usertoken"] = auth_response["usertoken"]
                    hass.config_entries.async_update_entry(
                        config_entry, data=config_data
                    )
            except LifeSmartAuthError as e:
                # 如果刷新失败，且我们不是通过密码登录的，说明旧令牌已失效，需要重新认证
                if config_data.get(CONF_LIFESMART_AUTH_METHOD) != "password":
                    _LOGGER.error("令牌已失效，需要重新认证: %s", e)
                    # 在HA中触发重新认证流程
                    config_entry.async_start_reauth(hass)
                    raise ConfigEntryNotReady("令牌已失效，请重新认证。", e.code) from e

            # 3. 获取设备列表
            devices = await client.get_all_device_async()
            return client, devices, auth_response

        except LifeSmartAuthError as e:
            # 这个块现在只会在初始登录（如果需要）时触发，详细日志已在 client 中记录
            _LOGGER.error("在集成启动期间发生认证错误，无法继续。")
            raise ConfigEntryNotReady(f"认证失败: {e}") from e
        except LifeSmartAPIError as e:
            _LOGGER.error("在集成启动期间发生API错误，无法获取设备。")
            raise ConfigEntryNotReady(f"API错误: {e}") from e
        except Exception as e:
            _LOGGER.error("在集成启动期间发生未知错误: %s", e, exc_info=True)
            raise ConfigEntryNotReady(f"未知错误: {e}") from e

    else:
        # --- 本地模式 ---
        try:
            reload(lifesmart_protocol)  # 重新加载协议模块以支持热更新
            client = lifesmart_protocol.LifeSmartLocalClient(
                config_entry.data[CONF_HOST],
                config_entry.data[CONF_PORT],
                config_entry.data[CONF_USERNAME],
                config_entry.data[CONF_PASSWORD],
                config_entry.entry_id,
            )
            devices = await client.get_all_device_async()
            if not devices:
                raise ConfigEntryNotReady("从本地网关获取设备列表失败。")

            # 注册 Home Assistant 停止时的回调，以优雅地断开本地连接
            config_entry.async_on_unload(
                hass.bus.async_listen_once(
                    EVENT_HOMEASSISTANT_STOP, client.async_disconnect
                )
            )
            return client, devices, None
        except Exception as e:
            _LOGGER.error("设置与 LifeSmart 中枢的本地连接失败: %s", e)
            raise ConfigEntryNotReady from e


async def _async_register_hubs(
    hass: HomeAssistant, config_entry: ConfigEntry, devices: list
):
    """在 Home Assistant 设备注册表中注册 LifeSmart 中枢。

    Args:
        hass: Home Assistant 的核心实例。
        config_entry: 当前集成的配置条目。
        devices: 从 API 获取的设备列表。
    """
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


def _async_register_services(hass: HomeAssistant, client: Any):
    """注册 LifeSmart 集成提供的服务。

    这些服务允许用户通过 Home Assistant 的服务调用功能与 LifeSmart 设备进行交互，
    例如发送红外命令或触发场景。

    Args:
        hass: Home Assistant 的核心实例。
        client: 已初始化的 LifeSmart 客户端。
    """

    async def send_ir_keys(call):
        """处理发送红外按键的服务调用。"""
        await client.send_ir_key_async(
            call.data[HUB_ID_KEY],
            call.data["ai"],
            call.data[DEVICE_ID_KEY],
            call.data["category"],
            call.data["brand"],
            call.data["keys"],
        )

    async def trigger_scene(call):
        """处理触发场景的服务调用。"""
        agt = call.data.get(HUB_ID_KEY)
        scene_id = call.data.get("id")

        if not agt or not scene_id:
            _LOGGER.error("触发场景失败：'agt' 和 'id' 参数不能为空。")
            return

        _LOGGER.info("正在通过服务调用触发场景: Hub=%s, SceneID=%s", agt, scene_id)
        await client.set_scene_async(agt, scene_id)

    async def press_switch(call):
        """处理点动开关的服务调用。"""
        entity_id = call.data.get("entity_id")
        duration = call.data.get("duration", 1000)  # 默认点动1秒

        entity = hass.states.get(entity_id)
        if not entity:
            _LOGGER.error("未找到实体: %s", entity_id)
            return

        # 从实体属性中获取设备信息
        agt = entity.attributes.get(HUB_ID_KEY)
        me = entity.attributes.get(DEVICE_ID_KEY)
        idx = entity.attributes.get(SUBDEVICE_INDEX_KEY)

        if not all([agt, me, idx]):
            _LOGGER.error("实体 %s 缺少必要的属性 (agt, me, idx)。", entity_id)
            return

        await client.press_switch_async(idx, agt, me, duration)

    hass.services.async_register(DOMAIN, "press_switch", press_switch)
    hass.services.async_register(DOMAIN, "send_ir_keys", send_ir_keys)
    hass.services.async_register(DOMAIN, "trigger_scene", trigger_scene)


def _async_setup_background_tasks(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    client: Any,
    auth_response: dict | None = None,
):
    """设置后台任务，包括 WebSocket 管理器和定时刷新。

    Args:
        hass: Home Assistant 的核心实例。
        config_entry: 当前集成的配置条目。
        client: 已初始化的 LifeSmart 客户端。
        auth_response: 登录成功后返回的认证数据，包含令牌过期时间。
    """

    async def _async_periodic_refresh(now=None):
        """全局设备数据定时刷新任务。"""
        try:
            _LOGGER.debug("开始定时刷新设备数据。")
            new_devices = await client.get_all_device_async()
            hass.data[DOMAIN][config_entry.entry_id]["devices"] = new_devices
            dispatcher_send(hass, LIFESMART_SIGNAL_UPDATE_ENTITY)
            _LOGGER.debug("全局设备数据刷新完成。")
        except (LifeSmartAPIError, LifeSmartAuthError) as e:
            _LOGGER.warning("因 API/认证 错误，定时刷新失败: %s", e)
        except Exception as e:
            _LOGGER.warning("定时刷新时发生意外错误，这可能是临时问题。错误: %s", e)

    # 仅在云端模式下启动 WebSocket 状态管理器和令牌刷新任务
    if isinstance(client, LifeSmartClient):
        state_manager = LifeSmartStateManager(
            hass=hass,
            config_entry=config_entry,
            client=client,
            ws_url=client.get_wss_url(),
            refresh_callback=_async_periodic_refresh,
        )
        # 如果有认证响应，设置初始的令牌过期时间
        if auth_response and "expiredtime" in auth_response:
            state_manager.set_token_expiry(auth_response["expiredtime"])

        state_manager.start()
        hass.data[DOMAIN][LIFESMART_STATE_MANAGER] = state_manager

    # 设置定时刷新任务（每10分钟），作为 WebSocket 的备用和补充
    cancel_refresh = async_track_time_interval(
        hass, _async_periodic_refresh, timedelta(minutes=10)
    )
    config_entry.async_on_unload(cancel_refresh)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """处理集成的卸载流程。

    此函数确保在卸载集成时，所有相关的连接、任务和数据都被正确清理。

    Args:
        hass: Home Assistant 的核心实例。
        entry: 正在被卸载的配置条目。

    Returns:
        如果卸载成功，则返回 True。
    """
    entry_id = entry.entry_id

    # 停止 WebSocket 状态管理器
    if state_manager := hass.data[DOMAIN].get(LIFESMART_STATE_MANAGER):
        await state_manager.stop()

    # 断开本地客户端连接
    client = hass.data[DOMAIN].get(entry_id, {}).get("client")
    if isinstance(client, lifesmart_protocol.LifeSmartLocalClient):
        await client.async_disconnect(None)

    # 卸载所有相关的平台组件
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, SUPPORTED_PLATFORMS
    )

    # 清理 hass.data 中存储的数据
    if unload_ok and DOMAIN in hass.data and entry_id in hass.data[DOMAIN]:
        # 移除此配置条目的更新监听器
        hass.data[DOMAIN][entry_id][UPDATE_LISTENER]()
        # 弹出此配置条目的数据
        hass.data[DOMAIN].pop(entry_id)
        # 如果这是最后一个配置条目，清理整个域
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

    return unload_ok


async def data_update_handler(
    hass: HomeAssistant, config_entry: ConfigEntry, raw_data: dict
) -> None:
    """处理来自云端或本地的设备状态更新。

    这是所有实时数据更新的中央处理器，负责解析数据、应用过滤器，
    并通过 dispatcher 将更新分派给对应的实体。

    Args:
        hass: Home Assistant 的核心实例。
        config_entry: 当前集成的配置条目。
        raw_data: 从 WebSocket 或本地连接收到的原始数据包。
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

        # 从 config_entry.options 获取过滤器配置
        exclude_devices_str = config_entry.options.get(CONF_EXCLUDE_ITEMS, "")
        exclude_hubs_str = config_entry.options.get(CONF_EXCLUDE_AGTS, "")
        ai_include_hubs_str = config_entry.options.get(CONF_AI_INCLUDE_AGTS, "")
        ai_include_items_str = config_entry.options.get(CONF_AI_INCLUDE_ITEMS, "")

        # 将字符串配置转换为列表进行处理
        exclude_devices = [
            dev.strip() for dev in exclude_devices_str.split(",") if dev.strip()
        ]
        exclude_hubs = [
            hub.strip() for hub in exclude_hubs_str.split(",") if hub.strip()
        ]
        ai_include_hubs = [
            hub.strip() for hub in ai_include_hubs_str.split(",") if hub.strip()
        ]
        ai_include_items = [
            item.strip() for item in ai_include_items_str.split(",") if item.strip()
        ]

        # --- 过滤器处理 ---
        if device_id in exclude_devices:
            _LOGGER.debug(
                "忽略设备更新 [%s | %s]（在排除列表中）", device_id, device_type
            )
            return
        if hub_id in exclude_hubs:
            _LOGGER.debug("忽略中枢 [%s] 下所有设备的更新（在排除列表中）", hub_id)
            return

        # --- 特殊子设备处理（AI事件） ---
        if sub_device_key == "s":
            if device_id in ai_include_items and hub_id in ai_include_hubs:
                _LOGGER.info("触发AI事件: %s", data)
                # 未来可在此处扩展AI事件的具体处理逻辑
            return

        # --- 普通设备更新处理 ---
        entity_id = generate_entity_id(device_type, hub_id, device_id, sub_device_key)

        # 通过 dispatcher 将更新信号发送给对应的实体
        dispatcher_send(hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data)

        _LOGGER.debug(
            "状态更新已派发 -> %s: %s", entity_id, json.dumps(data, ensure_ascii=False)
        )

    except Exception as e:
        _LOGGER.error("处理设备更新时发生异常: %s\n原始数据: %s", str(e), raw_data)


async def _async_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """当配置选项更新时，处理重载逻辑。

    此函数作为监听器，在用户通过“选项”流程修改配置后被调用，
    触发集成的重新加载以应用新设置。

    Args:
        hass: Home Assistant 的核心实例。
        config_entry: 已更新的配置条目。
    """
    _LOGGER.info("检测到配置更新，正在重新加载 LifeSmart 集成...")
    await hass.config_entries.async_reload(config_entry.entry_id)


class LifeSmartDevice(Entity):
    """LifeSmart 基础设备类。

    此类不直接作为 Home Assistant 实体使用，而是作为其他平台实体（如 Switch, Light）
    的基类，提供通用的属性和方法。

    Attributes:
        _name (str): 设备名称。
        _agt (str): 所属中枢的 ID。
        _me (str): 设备的唯一 ID。
        _devtype (str): 设备的类型代码。
        _client: LifeSmart 客户端实例。
        _attributes (dict): 存储通用设备属性的字典。
    """

    def __init__(self, dev: dict, lifesmart_client: LifeSmartClient) -> None:
        """初始化基础设备。

        Args:
            dev: 从 API 获取的设备信息字典。
            lifesmart_client: LifeSmart 客户端实例。
        """
        self._name = (
            dev.get(DEVICE_NAME_KEY) or f"Unnamed {dev.get(DEVICE_TYPE_KEY, 'Device')}"
        )
        self._device_name = self._name
        self._agt = dev.get(HUB_ID_KEY)
        self._me = dev.get(DEVICE_ID_KEY)
        self._devtype = dev.get(DEVICE_TYPE_KEY)
        self._client = lifesmart_client
        self._attributes = {
            HUB_ID_KEY: self._agt,
            DEVICE_ID_KEY: self._me,
            DEVICE_TYPE_KEY: self._devtype,
        }

    @property
    def object_id(self) -> str:
        """返回 LifeSmart 设备的 ID。"""
        return self.entity_id

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """返回设备的状态属性。"""
        return self._attributes

    @property
    def name(self) -> str:
        """返回 LifeSmart 设备的名称。"""
        return self._name

    @property
    def assumed_state(self) -> bool:
        """返回是否采用乐观更新模式。"""
        return False

    @property
    def should_poll(self) -> bool:
        """返回实体是否需要轮询更新状态。"""
        return False

    async def async_lifesmart_epset(self, type: str, val: Any, idx: str) -> Any:
        """向 LifeSmart 设备发送 EpSet 命令。"""
        return await self._client.send_epset_async(self._agt, self._me, idx, type, val)

    async def async_lifesmart_epget(self) -> Any:
        """获取 LifeSmart 设备的详细信息。"""
        return await self._client.get_epget_async(self._agt, self._me)

    async def async_lifesmart_sceneset(self, id: str) -> Any:
        """设置场景。"""
        response = await self._client.set_scene_async(self._agt, id)
        return response["code"]


class LifeSmartStateManager:
    """LifeSmart WebSocket 状态管理器。

    此类负责维护与 LifeSmart 云端的 WebSocket 长连接，处理实时状态更新、
    认证、心跳维持以及连接中断后的自动重连。

    Attributes:
        hass: Home Assistant 核心实例。
        config_entry: 集成配置条目。
        ws_url (str): WebSocket 连接地址。
        refresh_callback (callable): 全量刷新回调函数。
        _ws: 当前的 aiohttp WebSocket 连接实例。
        _ws_task: 运行连接循环的 asyncio 任务。
        _token_task: 运行令牌刷新管理的 asyncio 任务。
        _should_stop (bool): 标记是否应停止连接循环。
        _last_disconnect_time (Optional[datetime]): 上次断开连接的时间。
        _token_expiry_time (int): 令牌的过期时间戳。
        _token_refresh_event (asyncio.Event): 用于令牌刷新任务的事件。
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: LifeSmartClient,
        ws_url: str,
        refresh_callback: callable,
        retry_interval: int = 10,
        max_retries: int = 60,
    ) -> None:
        """初始化 WebSocket 状态管理器。

        Args:
            hass: Home Assistant 核心实例。
            config_entry: 集成配置条目。
            ws_url: WebSocket 连接地址。
            refresh_callback: 用于在长时间断连后触发全量刷新的回调函数。
            retry_interval (int): 初始重试间隔（秒）。
            max_retries (int): 最大重试次数。
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
        """设置令牌的过期时间戳。"""
        self._token_expiry_time = expiry_timestamp
        self._token_refresh_event.set()  # 通知刷新任务可以开始工作了
        _LOGGER.info(
            "令牌过期时间已设置为: %s", datetime.fromtimestamp(expiry_timestamp)
        )

    async def _connection_handler(self):
        """主连接处理循环，包含状态机和错误处理。"""
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
                break  # 认证失败，停止重试

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
        """创建新的 WebSocket 连接，并处理 SSL 验证。"""
        ssl_context = get_default_context()
        session = async_get_clientsession(self.hass)
        try:
            return await session.ws_connect(
                self.ws_url,
                heartbeat=25,
                compress=15,
                ssl=ssl_context,
                timeout=aiohttp.ClientTimeout(total=30),
            )
        except aiohttp.ClientConnectorCertificateError as e:
            _LOGGER.error("SSL 证书验证失败，请检查服务器区域设置是否正确。错误: %s", e)
            raise

    async def _perform_auth(self):
        """执行 WebSocket 认证流程。"""
        client = self.hass.data[DOMAIN][self.config_entry.entry_id]["client"]
        auth_payload = client.generate_wss_auth()
        _LOGGER.debug("发送 WebSocket 认证载荷: %s", auth_payload)
        await self._ws.send_str(auth_payload)

        response = await self._ws.receive(timeout=30)
        if response.type != aiohttp.WSMsgType.TEXT:
            raise PermissionError(f"服务器返回了非预期的响应类型: {response.type}")

        data = json.loads(response.data)
        _LOGGER.debug("收到 WebSocket 认证响应: %s", data)

        # 检查多种可能的成功响应格式
        if not (data.get("code") == 0 and data.get("message") == "success"):
            error_msg = data.get("message", "未知认证错误")
            raise PermissionError(f"认证被服务器拒绝: {error_msg}")

        _LOGGER.info("✅ WebSocket 认证成功。")
        # 如果是断线重连，检查断开时长
        if self._last_disconnect_time:
            disconnect_duration = datetime.now() - self._last_disconnect_time
            if disconnect_duration > timedelta(minutes=30):
                _LOGGER.warning(
                    "WebSocket 断开已超过 %d 分钟，将触发一次全量设备刷新以确保状态同步。",
                    int(disconnect_duration.total_seconds() / 60),
                )
                self.hass.loop.create_task(self.refresh_callback())

        # 连接成功后，重置所有状态计时器
        self._last_disconnect_time = None
        self._retry_count = 0

    async def _message_consumer(self):
        """持续消费来自 WebSocket 的消息。"""
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
        """处理单条文本消息。"""
        try:
            _LOGGER.debug("收到 WebSocket 消息: %s", raw_data)
            data = json.loads(raw_data)
            if data.get("type") == "io":
                await data_update_handler(self.hass, self.config_entry, data)
        except json.JSONDecodeError:
            _LOGGER.warning("无法解析收到的 WebSocket 消息: %s", raw_data[:200])
        except Exception as e:
            _LOGGER.error("处理 WebSocket 消息时发生错误: %s", e)

    async def _schedule_retry(self):
        """调度下一次重连尝试，采用指数退避策略。"""
        if self._last_disconnect_time is None:
            self._last_disconnect_time = datetime.now()

        self._retry_count += 1
        if self._retry_count > self.max_retries:
            _LOGGER.error("已达到最大重试次数 (%s)，将停止尝试连接。", self.max_retries)
            return

        # 指数退避算法，最大间隔5分钟
        delay = min(self.retry_interval * (2 ** (self._retry_count - 1)), 300)
        _LOGGER.info(
            "WebSocket 连接断开，将在 %.1f 秒后进行第 %d 次重试。",
            delay,
            self._retry_count,
        )
        await asyncio.sleep(delay)

    async def _token_refresh_handler(self):
        """后台任务，采用周期性检查的方式，在 usertoken 过期前自动刷新。"""
        # 启动后稍作等待，避免在HA启动高峰期执行
        await asyncio.sleep(60)

        # 定义检查周期为1小时
        check_interval_seconds = 1 * 3600

        while not self._should_stop:
            try:
                # 如果初始令牌时间还未设置，则等待
                if self._token_expiry_time == 0:
                    await asyncio.sleep(check_interval_seconds)
                    continue

                now = int(time.time())
                time_to_expiry = self._token_expiry_time - now

                # 定义刷新阈值，还有 275 天就要尝试了（90 天刷新一次）
                refresh_threshold = 275 * 24 * 3600

                if time_to_expiry < refresh_threshold:
                    _LOGGER.info(
                        "令牌即将在 %.1f 小时内过期，开始刷新...", time_to_expiry / 3600
                    )
                    try:
                        new_token_data = await self.client.async_refresh_token()

                        # 更新成功，持久化新令牌并更新内部状态
                        current_data = self.config_entry.data.copy()
                        current_data[CONF_LIFESMART_USERTOKEN] = new_token_data[
                            "usertoken"
                        ]
                        self.hass.config_entries.async_update_entry(
                            self.config_entry, data=current_data
                        )

                        self.set_token_expiry(new_token_data["expiredtime"])
                        _LOGGER.info("令牌刷新成功，下一次检查在1小时后。")

                    except LifeSmartAuthError as e:
                        # 刷新失败，记录错误。循环将在1小时后自动重试。
                        _LOGGER.error("自动刷新令牌失败: %s。将在1小时后重试。", e)
                else:
                    _LOGGER.debug(
                        "令牌有效期充足 (剩余 %.1f 小时)，下一次检查在1小时后。",
                        time_to_expiry / 3600,
                    )

                # 等待下一个检查周期
                await asyncio.sleep(check_interval_seconds)

            except asyncio.CancelledError:
                _LOGGER.info("令牌刷新任务已被取消。")
                break
            except Exception as e:
                _LOGGER.error(
                    "令牌刷新处理器发生未捕获的异常: %s。将在1小时后重试。", e
                )
                # 即使发生未知异常，也等待一个周期再试，避免快速失败循环
                await asyncio.sleep(check_interval_seconds)

    async def stop(self):
        """优雅地停止 WebSocket 连接和管理任务。"""
        _LOGGER.info("正在停止 LifeSmart WebSocket 状态管理器...")
        self._should_stop = True
        if self._ws and not self._ws.closed:
            await self._ws.close(code=1000)

        # 取消所有任务，_connection_handler 和 _token_refresh_handler
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


def get_platform_by_device(device_type: str, sub_device: Optional[str] = None) -> str:
    """根据设备类型和子索引，决定其所属的 Home Assistant 平台。

    Args:
        device_type: 设备的类型代码。
        sub_device: 子设备的索引键（如果适用）。

    Returns:
        对应的平台字符串（如 'switch', 'light'），或空字符串。
    """
    if device_type in ALL_SWITCH_TYPES:
        return Platform.SWITCH
    if device_type in ALL_LIGHT_TYPES:
        return Platform.LIGHT
    if device_type in ALL_COVER_TYPES:
        return Platform.COVER
    if device_type in CLIMATE_TYPES:
        return Platform.CLIMATE

    # 对复合设备进行子设备判断
    if device_type in LOCK_TYPES:
        if sub_device == "BAT":
            return Platform.SENSOR
        if sub_device in ["EVTLO", "ALM"]:
            return Platform.BINARY_SENSOR

    if device_type in SMART_PLUG_TYPES:
        if sub_device == "P1":
            return Platform.SWITCH
        if sub_device in ["P2", "P3"]:
            return Platform.SENSOR

    # 将剩余的各类传感器归类,这个判断应该在复合设备之后，避免错误分类
    if device_type in ALL_BINARY_SENSOR_TYPES:
        return Platform.BINARY_SENSOR
    if device_type in ALL_SENSOR_TYPES:
        return Platform.SENSOR

    return ""


def generate_entity_id(
    device_type: str,
    hub_id: str,
    device_id: str,
    sub_device: Optional[str] = None,
) -> str:
    """为 LifeSmart 设备生成符合 Home Assistant 规范的唯一实体 ID。

    此函数确保生成的 ID 是唯一的、可读的，并符合 HA 的命名规则。

    Args:
        device_type: 设备的类型代码。
        hub_id: 所属中枢的 ID。
        device_id: 设备的 ID。
        sub_device: 子设备的索引键（如果适用）。

    Returns:
        格式化的实体 ID 字符串，例如 'switch.sl_sw_nd1_agt123_dev456_p1'。
    """
    import re

    def sanitize(input_str: str) -> str:
        """移除字符串中的非字母数字字符并转为小写。"""
        return re.sub(r"\W", "", str(input_str)).lower()

    platform_str = get_platform_by_device(device_type, sub_device)
    if not platform_str:
        return ""  # 如果无法确定平台，则不生成ID

    # 构建实体ID的基础部分
    base_parts = [
        sanitize(device_type),
        sanitize(hub_id),
        sanitize(device_id),
    ]
    if sub_device:
        base_parts.append(sanitize(sub_device))

    clean_entity = "_".join(base_parts)
    # 确保实体ID不超过最大长度限制
    max_length = 255 - (len(platform_str) + 1)
    clean_entity = clean_entity[:max_length]

    return f"{platform_str}.{clean_entity}"
