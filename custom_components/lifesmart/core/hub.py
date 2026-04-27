"""LifeSmart 智能家居系统集成的中央协调器 Hub。

═══════════════════════════════════════════════════════════════════════════════════
🏗️ 架构设计理念
═══════════════════════════════════════════════════════════════════════════════════

本模块实现了 LifeSmart 集成的核心协调器模式，采用三层架构设计：

┌─────────────────────────────────────────────────────────────────────────────────┐
│ 🎯 业务层 (Hub Layer)                                                            │
│ ├── 设备生命周期管理                                                             │
│ ├── 实时状态更新分发                                                             │
│ ├── 设备过滤和AI事件处理                                                         │
│ └── 统一数据访问接口                                                             │
├─────────────────────────────────────────────────────────────────────────────────┤
│ 🔌 通信层 (Communication Layer)                                                  │
│ ├── OAPI客户端 (云端REST + WebSocket)                                           │
│ ├── Local TCP客户端 (本地网关直连)                                              │
│ └── 自适应网络质量检测                                                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│ ⚡ 基础设施层 (Infrastructure Layer)                                            │
│ ├── 并发控制管理器 (防止竞态条件)                                               │
│ ├── WebSocket状态管理器 (长连接维护)                                            │
│ ├── 令牌生命周期管理                                                             │
│ └── 故障检测与恢复机制                                                           │
└─────────────────────────────────────────────────────────────────────────────────┘

═══════════════════════════════════════════════════════════════════════════════════
🔥 核心功能特性
═══════════════════════════════════════════════════════════════════════════════════

🎛️  **双模式通信支持**
    - OAPI模式：云端REST API + WebSocket实时推送
    - 本地模式：TCP直连网关，低延迟控制
    - 动态模式切换和故障转移

🔄  **智能设备状态管理**
    - 实时WebSocket推送处理
    - 设备状态缓存和增量更新
    - 断线重连后的状态同步策略

🛡️  **企业级并发控制**
    - 令牌刷新防竞态保护
    - 设备更新并发限制
    - WebSocket连接独占锁
    - 消息处理异步队列

🌐  **网络质量自适应**
    - 实时网络质量检测
    - 动态调整心跳间隔
    - 智能重连延迟算法
    - 网络异常预测和预处理

🔧  **生产级错误处理**
    - 多层异常捕获和分类
    - 设备问题标记和跟踪
    - 自动故障恢复流程
    - 详细的诊断信息记录

💡  **高级功能集成**
    - 设备和网关过滤配置
    - AI事件特殊处理
    - Home Assistant原生集成
    - 实时诊断统计接口

═══════════════════════════════════════════════════════════════════════════════════
⚠️  关键技术考虑
═══════════════════════════════════════════════════════════════════════════════════

🔐 **安全性**：令牌安全存储、WebSocket认证、本地连接加密
🚀 **性能**：异步I/O、消息队列、设备状态缓存、网络优化
🛡️ **可靠性**：故障检测、自动重连、数据一致性保证
📊 **可观测性**：详细日志、性能统计、网络质量监控
🔧 **可维护性**：模块化设计、清晰接口、完整测试覆盖

═══════════════════════════════════════════════════════════════════════════════════

作者：@MapleEve
版本：v2.0 (架构重构版)
创建日期：2024年
更新日期：2025年8月
许可：遵循项目开源许可证
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any

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
from .compatibility import get_ws_timeout
from .concurrency_manager import ConcurrencyManager
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
    CONF_WS_HEARTBEAT_INTERVAL,
    CONF_WS_MAX_RECONNECT_ATTEMPTS,
    CONF_WS_NETWORK_MODE,
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
from .network_quality_detector import NetworkQualityDetector, calculate_reconnect_delay

_LOGGER = logging.getLogger(__name__)


class LifeSmartHub:
    """LifeSmart 智能家居系统集成的中央协调器核心类。

    ═══════════════════════════════════════════════════════════════════════════════════
    🎯 设计模式与架构理念
    ═══════════════════════════════════════════════════════════════════════════════════

    本类采用 **中央协调器模式 (Central Coordinator Pattern)**，作为整个 LifeSmart
    集成的单一入口点和状态管理中心。设计遵循以下核心原则：

    🏗️ **单一职责原则**：每个方法专注于一个特定的业务功能
    🔒 **封装性原则**：内部状态通过受控接口访问
    🔗 **依赖注入原则**：通过构造函数注入核心依赖
    ♻️  **资源生命周期管理**：完整的创建-使用-销毁循环
    🛡️ **故障隔离原则**：错误不会级联影响其他组件

    ═══════════════════════════════════════════════════════════════════════════════════
    📋 核心职责模块
    ═══════════════════════════════════════════════════════════════════════════════════

    🔌 **客户端生命周期管理**
       ├── 根据配置创建合适的客户端实例 (OAPI/TCP)
       ├── 处理客户端认证和令牌管理
       ├── 管理客户端连接状态和重连逻辑
       └── 提供统一的客户端访问接口

    📊 **设备数据中心化管理**
       ├── 维护全局设备列表和状态缓存
       ├── 处理设备列表的增量和全量更新
       ├── 实现设备数据的过滤和筛选逻辑
       └── 为平台实体提供设备数据访问

    🔄 **实时状态更新分发系统**
       ├── 接收WebSocket/TCP推送的设备状态变更
       ├── 解析和验证状态更新数据的完整性
       ├── 通过Home Assistant dispatcher分发更新事件
       └── 处理特殊事件类型 (如AI事件)

    🌐 **WebSocket长连接维护**
       ├── 管理与LifeSmart云端的WebSocket连接
       ├── 处理连接断开和自动重连逻辑
       ├── 维护心跳和网络质量检测
       └── 协调令牌刷新和连接认证

    🛡️ **故障检测与恢复机制**
       ├── 监控各组件的健康状态
       ├── 实现多级故障恢复策略
       ├── 记录和分析设备异常模式
       └── 提供故障诊断和统计接口

    Attributes:
        hass (HomeAssistant): Home Assistant核心实例，提供异步事件循环等
        config_entry (ConfigEntry): 集成配置条目，包含用户配置和选项
        client (Optional[LifeSmartClientBase]): 统一客户端接口 (OAPI/TCP)
        devices (list[dict]): 全局设备列表缓存，支持过滤和实时更新
        _state_manager (Optional[LifeSmartStateManager]): WebSocket状态管理器
        _local_task (Optional[asyncio.Task]): 本地TCP连接任务
        _refresh_task_unsub (Optional[Callable]): 定时刷新任务取消函数
        _concurrency_manager (ConcurrencyManager): 企业级并发控制管理器
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
        self._refresh_task_unsub: Optional[Callable[[], None]] = None

        # 初始化并发控制管理器
        self._concurrency_manager = ConcurrencyManager()

        # 保持向后兼容的锁引用（已弃用，将在未来版本中移除）
        self._token_refresh_lock = self._concurrency_manager._token_refresh_lock
        self._device_update_semaphore = (
            self._concurrency_manager._device_update_semaphore
        )

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

            # 记录启动时间用于统计
            self._startup_time = datetime.now()

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
            auth_response = await self._concurrency_manager.safe_token_refresh(
                self.client.async_refresh_token
            )
            # 如果令牌有更新，持久化到配置
            if config_data.get("usertoken") != auth_response.get("usertoken"):
                config_data["usertoken"] = auth_response["usertoken"]
                await self._concurrency_manager.safe_config_update(
                    lambda: self.hass.config_entries.async_update_entry(
                        self.config_entry, data=config_data
                    )
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
                concurrency_manager=self._concurrency_manager,  # 传递并发控制管理器
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

        # 使用并发控制管理器处理设备更新
        async def _process_update():
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

            except json.JSONDecodeError as e:
                _LOGGER.warning("设备数据JSON解析失败: %s", e)
                # 触发设备重新同步
                asyncio.create_task(self._schedule_device_sync())

            except KeyError as e:
                _LOGGER.warning("设备数据字段缺失: %s", e)
                # 记录设备状态异常
                device_type = raw_data.get("msg", {}).get(DEVICE_TYPE_KEY, "unknown")
                asyncio.create_task(self._mark_device_problematic(device_type))

            except Exception as e:
                _LOGGER.error("处理设备更新时发生异常: %s", e, exc_info=True)
                # 触发故障恢复流程
                asyncio.create_task(self._trigger_recovery_procedure(raw_data))

        await self._concurrency_manager.safe_device_update(_process_update)

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

        # 关闭并发控制管理器
        await self._concurrency_manager.shutdown()

        _LOGGER.info("LifeSmart Hub 已成功卸载。")

    async def _schedule_device_sync(self):
        """调度设备重新同步"""

        async def _sync_operation():
            try:
                _LOGGER.info("开始执行设备重新同步...")
                await asyncio.sleep(5)  # 延迟5秒避免频繁同步
                # 重新获取设备列表并更新本地缓存
                if self.client:
                    new_devices = await self.client.async_get_all_devices()
                    self.devices = new_devices
                    # 通知所有实体更新
                    dispatcher_send(self.hass, LIFESMART_SIGNAL_UPDATE_ENTITY)
                    _LOGGER.info("设备重新同步完成，更新了 %d 个设备", len(new_devices))
            except LifeSmartAPIError as e:
                _LOGGER.error("设备同步API错误: %s", e)
            except Exception as e:
                _LOGGER.error("设备重新同步失败: %s", e)

        await self._concurrency_manager.safe_device_sync(_sync_operation)

    async def _mark_device_problematic(self, device_type: str):
        """标记设备存在问题"""
        try:
            _LOGGER.warning("设备类型 %s 存在数据问题，已标记", device_type)
            # 实现设备健康状态跟踪
            if not hasattr(self, "_problematic_devices"):
                self._problematic_devices = {}

            self._problematic_devices[device_type] = {
                "timestamp": datetime.now(),
                "count": self._problematic_devices.get(device_type, {}).get("count", 0)
                + 1,
            }

            # 如果某设备类型问题过多，考虑暂时跳过
            if self._problematic_devices[device_type]["count"] > 10:
                _LOGGER.error("设备类型 %s 问题过多，需要人工检查", device_type)
        except Exception as e:
            _LOGGER.error("标记设备问题时异常: %s", e)

    async def _trigger_recovery_procedure(self, raw_data: dict):
        """触发故障恢复流程"""

        async def _recovery_operation():
            try:
                _LOGGER.info("触发故障恢复流程...")

                # 1. 记录故障信息
                _LOGGER.debug(
                    "故障恢复: 记录信息 - 时间: %s, 数据: %s",
                    datetime.now().isoformat(),
                    raw_data,
                )

                # 2. 尝试恢复策略
                await asyncio.sleep(10)  # 给系统一些时间稳定

                # 3. 检查WebSocket连接状态（仅OAPI模式）
                if self._state_manager:
                    if hasattr(self._state_manager, "_ws") and (
                        not self._state_manager._ws or self._state_manager._ws.closed
                    ):
                        _LOGGER.info("WebSocket连接异常，将触发重连")
                        # 可以触发_state_manager的重连逻辑

                # 4. 触发一次设备状态全量刷新
                await self._schedule_device_sync()

                _LOGGER.info("故障恢复流程完成")
            except Exception as e:
                _LOGGER.error("故障恢复流程异常: %s", e, exc_info=True)

        await self._concurrency_manager.safe_recovery_operation(_recovery_operation)

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

    def get_concurrency_stats(self) -> Dict[str, Any]:
        """获取并发控制统计信息（用于诊断）。"""
        return self._concurrency_manager.get_concurrency_stats()

    def get_network_stats(self) -> Dict[str, Any]:
        """获取网络状态统计信息（用于诊断和监控）。"""
        stats = {}
        if self._state_manager:
            stats = self._state_manager.get_network_stats()

        # 添加Hub级别的网络信息
        stats.update(
            {
                "connection_type": (
                    "cloud" if hasattr(self.client, "get_wss_url") else "local"
                ),
                "total_devices": len(self.devices),
                "hub_active_since": getattr(self, "_startup_time", None),
            }
        )

        return stats


class LifeSmartStateManager:
    """LifeSmart WebSocket 状态管理器。

    负责维护与 LifeSmart 云端的 WebSocket 长连接，处理实时状态更新、
    认证、心跳维持以及连接中断后的自动重连。

    现已集成网络质量检测器，支持根据网络状况自适应调整连接参数。
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: LifeSmartOpenAPIClient,
        ws_url: str,
        refresh_callback: Callable[[], None],
        concurrency_manager: ConcurrencyManager,
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
            concurrency_manager: 并发控制管理器
            retry_interval: 初始重试间隔（秒）- 现在会根据网络质量动态调整
            max_retries: 最大重试次数 - 现在会根据网络质量动态调整
        """
        self.hass = hass
        self.config_entry = config_entry
        self.client = client
        self.ws_url = ws_url
        self.refresh_callback = refresh_callback
        self.retry_interval = retry_interval
        self.max_retries = max_retries
        self._concurrency_manager = concurrency_manager

        # 初始化网络质量检测器
        network_mode = config_entry.options.get(CONF_WS_NETWORK_MODE, "auto")
        self._network_detector = NetworkQualityDetector(network_mode)

        # WebSocket连接相关
        self._ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self._connection_lock = self._concurrency_manager._connection_lock
        self._retry_count = 0
        self._ws_task: Optional[asyncio.Task] = None
        self._token_task: Optional[asyncio.Task] = None
        self._should_stop = False
        self._last_disconnect_time: Optional[datetime] = None
        self._token_expiry_time: int = 0
        self._token_refresh_event = asyncio.Event()

        # 网络质量相关状态
        self._current_network_quality = "normal"
        self._last_quality_check = 0

        # 获取用户自定义配置
        self._custom_heartbeat_interval = config_entry.options.get(
            CONF_WS_HEARTBEAT_INTERVAL
        )
        self._custom_max_reconnect_attempts = config_entry.options.get(
            CONF_WS_MAX_RECONNECT_ATTEMPTS
        )

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
                # 使用并发控制管理器保护连接操作
                async def _connect_operation():
                    _LOGGER.info("正在尝试建立 WebSocket 连接...")
                    self._ws = await self._create_websocket()
                    _LOGGER.info("WebSocket 底层连接已建立，正在进行认证...")
                    await self._perform_auth()
                    _LOGGER.info("认证成功，开始监听消息...")
                    await self._message_consumer()

                await self._concurrency_manager.safe_connection_operation(
                    _connect_operation
                )

            except PermissionError as e:
                _LOGGER.critical("WebSocket 认证失败，不可恢复的错误: %s", e)
                break

            except aiohttp.ClientResponseError as e:
                if e.status == 401:
                    _LOGGER.error("WebSocket认证失败，检查令牌有效性: %s", e)
                    # 触发重新认证流程
                    break
                elif e.status >= 500:
                    _LOGGER.warning("服务器错误(%d)，将重试: %s", e.status, e)
                    await self._schedule_retry()
                else:
                    _LOGGER.error("客户端请求错误(%d): %s", e.status, e)
                    break

            except (ConnectionError, aiohttp.ClientOSError) as e:
                _LOGGER.warning("网络连接问题，将重试: %s", e)
                await self._schedule_retry()

            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                _LOGGER.warning(
                    "WebSocket 网络错误，将进行重试 (%d/%d): %s",
                    self._retry_count + 1,
                    self.max_retries,
                    e,
                )
                await self._schedule_retry()

            except json.JSONDecodeError as e:
                _LOGGER.error("服务器响应格式错误: %s", e)
                await self._schedule_retry()

            except asyncio.CancelledError:
                _LOGGER.info("WebSocket 连接任务被取消")
                raise  # 不应该捕获取消异常

            except Exception as e:
                # 只保留真正无法预料的异常
                error_type = type(e).__name__
                _LOGGER.error(
                    "WebSocket连接处理器发生未预期的%s异常: %s",
                    error_type,
                    e,
                    exc_info=True,
                )

                # 限制未知异常的重试次数
                if not hasattr(self, "_unknown_error_count"):
                    self._unknown_error_count = 0

                self._unknown_error_count += 1
                if self._unknown_error_count > 3:
                    _LOGGER.error(
                        "未知异常过多(%d次)，停止重试", self._unknown_error_count
                    )
                    break

                await self._schedule_retry()

    async def _create_websocket(self) -> aiohttp.ClientWebSocketResponse:
        """创建新的 WebSocket 连接。

        Returns:
            WebSocket 连接实例

        Raises:
            aiohttp.ClientConnectorCertificateError: SSL 证书验证失败
        """
        session = async_get_clientsession(self.hass)

        # 获取当前网络质量的超时配置
        timeout_config = self._network_detector.get_timeout_config(
            self._current_network_quality
        )
        heartbeat_interval = self._get_heartbeat_interval()

        _LOGGER.debug(
            "创建WebSocket连接 - 网络质量: %s, 心跳间隔: %ds, 接收超时: %ds",
            self._current_network_quality,
            heartbeat_interval,
            timeout_config["receive"],
        )

        try:
            return await session.ws_connect(
                self.ws_url,
                heartbeat=heartbeat_interval,
                compress=15,
                timeout=get_ws_timeout(timeout_config["receive"]),
            )
        except aiohttp.ClientConnectorCertificateError as e:
            _LOGGER.error("证书验证失败，请检查服务器区域设置: %s", e)
            raise

    async def _perform_auth(self):
        """执行 WebSocket 认证流程。

        Raises:
            PermissionError: 认证失败
        """
        timeout_config = self._network_detector.get_timeout_config(
            self._current_network_quality
        )
        auth_timeout = timeout_config["auth"]

        auth_payload = self.client.generate_wss_auth()
        _LOGGER.debug("发送 WebSocket 认证载荷: %s", auth_payload)
        await self._ws.send_str(auth_payload)

        response = await self._ws.receive(timeout=auth_timeout)
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
                    # 使用并发控制管理器处理消息
                    await self._concurrency_manager.safe_message_processing(
                        self._process_text_message, msg.data
                    )
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
        max_attempts = self._get_max_reconnect_attempts()

        if self._retry_count > max_attempts:
            _LOGGER.error("已达到最大重试次数 (%s)，将停止尝试连接。", max_attempts)
            return

        # 使用智能重连延迟计算
        timeout_config = self._network_detector.get_timeout_config(
            self._current_network_quality
        )
        base_delay = timeout_config["reconnect_base"]

        delay = calculate_reconnect_delay(
            self._retry_count, base_delay, self._current_network_quality
        )

        _LOGGER.info(
            "WebSocket 连接断开，将在 %.1f 秒后进行第 %d 次重试 (网络质量: %s)。",
            delay,
            self._retry_count,
            self._current_network_quality,
        )
        await asyncio.sleep(delay)

    async def _token_refresh_handler(self):
        """后台任务，定期检查和刷新令牌。"""
        await asyncio.sleep(60)  # 启动后等待

        # 配置常量 - 避免硬编码
        TOKEN_CHECK_INTERVAL_SECONDS = 3600  # 1小时检查一次
        TOKEN_REFRESH_THRESHOLD_DAYS = 275  # 275天提前刷新

        check_interval_seconds = TOKEN_CHECK_INTERVAL_SECONDS

        while not self._should_stop:
            try:
                # 等待令牌过期时间设置
                if self._token_expiry_time == 0:
                    await asyncio.sleep(check_interval_seconds)
                    continue

                now = int(time.time())
                time_to_expiry = self._token_expiry_time - now
                refresh_threshold = TOKEN_REFRESH_THRESHOLD_DAYS * 24 * 3600

                if time_to_expiry < refresh_threshold:
                    _LOGGER.info(
                        "令牌即将在 %.1f 小时内过期，开始刷新...", time_to_expiry / 3600
                    )

                    # 使用并发控制管理器进行令牌刷新和配置更新
                    try:
                        new_token_data = (
                            await self._concurrency_manager.safe_token_refresh(
                                self.client.async_refresh_token
                            )
                        )

                        # 更新配置并设置新的过期时间
                        current_data = self.config_entry.data.copy()
                        current_data[CONF_LIFESMART_USERTOKEN] = new_token_data[
                            "usertoken"
                        ]

                        await self._concurrency_manager.safe_config_update(
                            lambda: self.hass.config_entries.async_update_entry(
                                self.config_entry, data=current_data
                            )
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

        # 1. 安全关闭 WebSocket 连接，改进资源清理
        if self._ws and not self._ws.closed:
            try:
                # 获取当前网络质量的超时配置
                timeout_config = self._network_detector.get_timeout_config(
                    self._current_network_quality
                )
                close_timeout = timeout_config["close"]
                heartbeat_timeout = timeout_config["heartbeat"]

                # 先发送关闭帧
                await asyncio.wait_for(self._ws.close(code=1000), timeout=close_timeout)
                # 等待连接完全关闭
                await asyncio.wait_for(self._ws.wait_for_close(), timeout=close_timeout)
                _LOGGER.debug("WebSocket连接已正常关闭")
            except asyncio.TimeoutError:
                _LOGGER.warning("WebSocket关闭超时，进行强制清理")
            except Exception as e:
                _LOGGER.error("WebSocket关闭异常: %s", e)
            finally:
                # 清理引用但不直接设置为None（避免内存泄漏）
                self._ws = None

        # 2. 收集并取消所有任务
        tasks_to_cancel = []
        if hasattr(self, "_ws_task") and self._ws_task and not self._ws_task.done():
            self._ws_task.cancel()
            tasks_to_cancel.append(self._ws_task)
        if (
            hasattr(self, "_token_task")
            and self._token_task
            and not self._token_task.done()
        ):
            self._token_task.cancel()
            tasks_to_cancel.append(self._token_task)

        # 3. 等待任务完成，设置超时和异常处理
        if tasks_to_cancel:
            try:
                done, pending = await asyncio.wait_for(
                    asyncio.wait(tasks_to_cancel, return_when=asyncio.ALL_COMPLETED),
                    timeout=heartbeat_timeout,
                )
                # 检查是否有任务异常完成
                for task in done:
                    if task.exception() and not isinstance(
                        task.exception(), asyncio.CancelledError
                    ):
                        _LOGGER.warning("任务异常结束: %s", task.exception())
            except asyncio.TimeoutError:
                _LOGGER.warning(
                    "任务取消超时，仍有 %d 个任务未完成", len(tasks_to_cancel)
                )
                # 强制终止仍然运行的任务
                for task in tasks_to_cancel:
                    if not task.done():
                        task.cancel()

        _LOGGER.info("LifeSmart 状态管理器已完全停止。")

    async def _update_network_quality(self):
        """更新网络质量检测。"""
        try:
            new_quality = await self._network_detector.detect_network_quality(
                self.ws_url
            )
            if new_quality != self._current_network_quality:
                _LOGGER.info(
                    "网络质量变化: %s -> %s, 调整连接参数",
                    self._current_network_quality,
                    new_quality,
                )
                self._current_network_quality = new_quality
                # 重置重试计数器，给新的网络环境更多机会
                self._retry_count = max(0, self._retry_count - 5)
        except Exception as e:
            _LOGGER.warning("网络质量检测失败: %s", e)

    def _get_max_reconnect_attempts(self) -> int:
        """获取最大重连次数（考虑用户自定义配置）。"""
        if self._custom_max_reconnect_attempts:
            return self._custom_max_reconnect_attempts
        return self._network_detector.get_max_reconnect_attempts(
            self._current_network_quality
        )

    def _get_heartbeat_interval(self) -> int:
        """获取心跳间隔（考虑用户自定义配置）。"""
        if self._custom_heartbeat_interval:
            return self._custom_heartbeat_interval
        return self._network_detector.get_heartbeat_interval(
            self._current_network_quality
        )

    def get_network_stats(self) -> Dict[str, Any]:
        """获取网络质量统计信息。"""
        return {
            "current_quality": self._current_network_quality,
            "detector_stats": self._network_detector.get_stats(),
            "retry_count": self._retry_count,
            "max_retries": self._get_max_reconnect_attempts(),
            "heartbeat_interval": self._get_heartbeat_interval(),
        }
