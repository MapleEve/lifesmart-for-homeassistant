"""LifeSmart 集成的实体基类。

此模块提供所有平台实体共享的基类，包括通用属性、方法和状态管理逻辑。

由 @MapleEve 创建，作为集成架构重构的一部分。
"""

import asyncio
import logging
from typing import Any, Dict

from homeassistant.exceptions import PlatformNotReady, HomeAssistantError
from homeassistant.helpers.entity import Entity, DeviceInfo
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util.dt import utcnow

from .client_base import LifeSmartClientBase
from .const import (
    DEVICE_ID_KEY,
    DEVICE_NAME_KEY,
    DEVICE_TYPE_KEY,
    HUB_ID_KEY,
    DEVICE_VERSION_KEY,
    DOMAIN,
    MANUFACTURER,
)

_LOGGER = logging.getLogger(__name__)


class LifeSmartEntity(Entity):
    """LifeSmart 实体基类。

    提供所有 LifeSmart 实体共享的通用功能，包括：
    - 设备信息管理
    - 通用属性访问
    - 客户端引用

    Attributes:
        _raw_device: 原始设备数据字典
        _device_name: 设备显示名称
        _agt: 所属中枢 ID
        _me: 设备唯一 ID
        _devtype: 设备类型代码
        _client: LifeSmart 客户端实例
        _attributes: 通用状态属性字典
    """

    def __init__(self, raw_device: dict[str, Any], client: LifeSmartClientBase) -> None:
        """初始化 LifeSmart 实体基类。

        Args:
            raw_device: 从 API 获取的设备信息字典
            client: LifeSmart 客户端实例
        """
        super().__init__()
        self._raw_device = raw_device
        self._device_name = (
            raw_device.get(DEVICE_NAME_KEY)
            or f"Unnamed {raw_device.get(DEVICE_TYPE_KEY, 'Device')}"
        )
        self._agt = raw_device.get(HUB_ID_KEY)
        self._me = raw_device.get(DEVICE_ID_KEY)
        self._devtype = raw_device.get(DEVICE_TYPE_KEY)
        self._client = client
        self._attributes = {
            HUB_ID_KEY: self._agt,
            DEVICE_ID_KEY: self._me,
            DEVICE_TYPE_KEY: self._devtype,
        }

        # 可用性管理
        self._attr_available = True
        self._unavailable_functions = set()  # 记录不可用的功能
        self._platform_errors = {}  # 记录平台错误

        # 资源清理管理
        self._cleanup_tasks = []  # 存储需要清理的异步任务
        self._registered_listeners = []  # 存储注册的监听器
        self._cleanup_callbacks = []  # 存储自定义清理回调

    @property
    def _name(self) -> str:
        """返回设备名称（向后兼容性）。

        为了与现有平台实体代码兼容，提供 _name 属性。

        Returns:
            设备显示名称
        """
        return self._device_name

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """返回实体的额外状态属性。

        Returns:
            包含设备信息的属性字典
        """
        return self._attributes

    @property
    def agt(self) -> str:
        """返回设备所属中枢的 ID。

        Returns:
            中枢 ID
        """
        return self._agt

    @property
    def me(self) -> str:
        """返回设备的唯一 ID。

        Returns:
            设备 ID
        """
        return self._me

    @property
    def devtype(self) -> str:
        """返回设备的类型代码。

        Returns:
            设备类型代码
        """
        return self._devtype

    @property
    def assumed_state(self) -> bool:
        """返回是否采用假定状态模式。

        在 LifeSmart 集成中，我们通过实时推送获得准确状态，
        因此不使用假定状态模式。

        Returns:
            False，不使用假定状态
        """
        return False

    @property
    def should_poll(self) -> bool:
        """返回实体是否需要轮询更新状态。

        LifeSmart 集成通过 WebSocket 和本地连接接收实时更新，
        因此不需要轮询。

        Returns:
            False，不需要轮询
        """
        return False

    @property
    def available(self) -> bool:
        """返回实体是否可用。

        如果客户端协议不支持实体的核心功能，则实体不可用。

        Returns:
            bool: 实体是否可用
        """
        return self._attr_available

    def mark_function_unavailable(
        self, function_name: str, error_msg: str = None
    ) -> None:
        """标记特定功能为不可用。

        Args:
            function_name: 功能名称
            error_msg: 错误消息
        """
        self._unavailable_functions.add(function_name)
        if error_msg:
            self._platform_errors[function_name] = error_msg

        _LOGGER.debug(
            "标记实体 %s 的功能 '%s' 为不可用: %s",
            self.entity_id,
            function_name,
            error_msg or "未指定原因",
        )

    def mark_function_available(self, function_name: str) -> None:
        """标记特定功能为可用。

        Args:
            function_name: 功能名称
        """
        self._unavailable_functions.discard(function_name)
        self._platform_errors.pop(function_name, None)

        _LOGGER.debug("标记实体 %s 的功能 '%s' 为可用", self.entity_id, function_name)

    def is_function_available(self, function_name: str) -> bool:
        """检查特定功能是否可用。

        Args:
            function_name: 功能名称

        Returns:
            bool: 功能是否可用
        """
        return function_name not in self._unavailable_functions

    def set_entity_availability(self, available: bool, reason: str = None) -> None:
        """设置整个实体的可用性。

        Args:
            available: 是否可用
            reason: 不可用的原因
        """
        if self._attr_available != available:
            self._attr_available = available
            if not available and reason:
                _LOGGER.warning("实体 %s 被标记为不可用: %s", self.entity_id, reason)
            elif available:
                _LOGGER.info("实体 %s 恢复可用", self.entity_id)

            # 触发状态更新
            self.schedule_update_ha_state()

    async def safe_call_client_method(self, method_name: str, *args, **kwargs):
        """安全调用客户端方法，处理平台不支持的异常。

        Args:
            method_name: 客户端方法名称
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            方法调用结果，如果不支持则返回 None
        """
        try:
            method = getattr(self._client, method_name)
            return await method(*args, **kwargs)
        except PlatformNotReady as e:
            # 平台不就绪，标记功能为不可用
            self.mark_function_unavailable(method_name, str(e))
            _LOGGER.warning(
                "实体 %s 的功能 '%s' 暂时不可用: %s",
                self.entity_id,
                method_name,
                str(e),
            )
            return None
        except HomeAssistantError as e:
            # Home Assistant 错误，记录但不影响可用性
            _LOGGER.error(
                "实体 %s 调用 '%s' 时发生错误: %s", self.entity_id, method_name, str(e)
            )
            raise
        except Exception as e:
            # 其他异常，记录错误
            _LOGGER.error(
                "实体 %s 调用 '%s' 时发生未知错误: %s",
                self.entity_id,
                method_name,
                str(e),
                exc_info=True,
            )
            raise

    def add_cleanup_task(self, task) -> None:
        """添加需要在实体移除时清理的异步任务。

        Args:
            task: 需要清理的异步任务
        """
        if task and not task.done():
            self._cleanup_tasks.append(task)
            _LOGGER.debug("为实体 %s 添加清理任务: %s", self.entity_id, task)

    def add_cleanup_callback(self, callback) -> None:
        """添加自定义清理回调函数。

        Args:
            callback: 在实体移除时调用的清理回调
        """
        if callable(callback):
            self._cleanup_callbacks.append(callback)
            _LOGGER.debug("为实体 %s 添加清理回调: %s", self.entity_id, callback)

    def register_listener(self, remove_listener) -> None:
        """注册监听器的移除函数。

        Args:
            remove_listener: 用于移除监听器的函数
        """
        if callable(remove_listener):
            self._registered_listeners.append(remove_listener)
            _LOGGER.debug("为实体 %s 注册监听器移除函数", self.entity_id)

    async def async_will_remove_from_hass(self) -> None:
        """在实体从 Home Assistant 中移除时进行资源清理。

        此方法实现了标准的资源清理模式，确保所有异步资源得到正确释放。
        包括：
        - 取消所有注册的监听器
        - 清理未完成的异步任务
        - 执行自定义清理回调
        - 释放客户端资源
        """
        _LOGGER.debug("开始实体 %s 的资源清理", self.entity_id)

        cleanup_errors = []

        # 1. 清理注册的监听器
        if self._registered_listeners:
            _LOGGER.debug("清理 %d 个监听器", len(self._registered_listeners))
            for remove_listener in self._registered_listeners:
                try:
                    if callable(remove_listener):
                        remove_listener()
                        _LOGGER.debug("成功移除监听器")
                except Exception as e:
                    error_msg = f"移除监听器时发生错误: {e}"
                    cleanup_errors.append(error_msg)
                    _LOGGER.warning("%s - 实体: %s", error_msg, self.entity_id)

        # 2. 清理异步任务
        if self._cleanup_tasks:
            _LOGGER.debug("清理 %d 个异步任务", len(self._cleanup_tasks))
            for task in self._cleanup_tasks:
                try:
                    if not task.done():
                        task.cancel()
                        try:
                            await task
                        except Exception:
                            pass  # 忽略取消任务的异常
                        _LOGGER.debug("成功取消异步任务")
                except Exception as e:
                    error_msg = f"取消异步任务时发生错误: {e}"
                    cleanup_errors.append(error_msg)
                    _LOGGER.warning("%s - 实体: %s", error_msg, self.entity_id)

        # 3. 执行自定义清理回调
        if self._cleanup_callbacks:
            _LOGGER.debug("执行 %d 个清理回调", len(self._cleanup_callbacks))
            for callback in self._cleanup_callbacks:
                try:
                    if callable(callback):
                        if asyncio.iscoroutinefunction(callback):
                            await callback()
                        else:
                            callback()
                        _LOGGER.debug("成功执行清理回调")
                except Exception as e:
                    error_msg = f"执行清理回调时发生错误: {e}"
                    cleanup_errors.append(error_msg)
                    _LOGGER.warning("%s - 实体: %s", error_msg, self.entity_id)

        # 4. 释放客户端资源（如果需要）
        try:
            if hasattr(self._client, "cleanup") and callable(self._client.cleanup):
                if asyncio.iscoroutinefunction(self._client.cleanup):
                    await self._client.cleanup()
                else:
                    self._client.cleanup()
                _LOGGER.debug("成功清理客户端资源")
        except Exception as e:
            error_msg = f"清理客户端资源时发生错误: {e}"
            cleanup_errors.append(error_msg)
            _LOGGER.warning("%s - 实体: %s", error_msg, self.entity_id)

        # 5. 清空内部列表
        self._cleanup_tasks.clear()
        self._registered_listeners.clear()
        self._cleanup_callbacks.clear()

        # 6. 记录清理结果
        if cleanup_errors:
            _LOGGER.error(
                "实体 %s 资源清理完成，但有 %d 个错误: %s",
                self.entity_id,
                len(cleanup_errors),
                "; ".join(cleanup_errors),
            )
        else:
            _LOGGER.debug("实体 %s 资源清理成功完成", self.entity_id)

    @property
    def device_info(self) -> DeviceInfo:
        """
        返回设备信息 - 合并自device_info.py的get_generation2_device_info功能

        使用Generation Gates系统进行智能fallback，而非硬性错误。
        对Generation 2设备使用enhanced info，对Legacy设备使用基础info。

        Returns:
            DeviceInfo: Home Assistant标准设备信息对象
        """
        # 检查是否支持enhanced device info
        try:
            from .compatibility import check_feature_gate

            if check_feature_gate(self._raw_device, "enhanced_device_info"):
                # Generation 2设备：使用DeviceResolver获取增强信息
                from .resolver import get_device_resolver

                resolver = get_device_resolver()
                result = resolver.resolve_device_config(self._raw_device)

                if result.success and result.device_config:
                    device_config = result.device_config

                    # 验证Generation 2必需字段
                    if device_config.manufacturer and device_config.model:
                        return DeviceInfo(
                            identifiers={(DOMAIN, self._agt, self._me)},
                            name=self._device_name,
                            manufacturer=device_config.manufacturer,  # ✅ 来自Generation 2规格
                            model=device_config.model,  # ✅ 来自Generation 2规格
                            sw_version=self._raw_device.get(
                                DEVICE_VERSION_KEY, "unknown"
                            ),
                            via_device=(DOMAIN, self._agt),
                        )
                    else:
                        _LOGGER.warning(
                            f"Device {self._me} missing manufacturer/model in Generation 2 specs, "
                            f"falling back to legacy mode"
                        )
        except ImportError:
            _LOGGER.debug("Generation gates not available, using legacy device info")
        except Exception as e:
            _LOGGER.debug(f"Failed to get enhanced device info for {self._me}: {e}")

        # Legacy设备或Generation 2字段不完整时的fallback
        _LOGGER.debug(f"Using legacy device info for device {self._me}")
        return DeviceInfo(
            identifiers={(DOMAIN, self._agt, self._me)},
            name=self._device_name,
            manufacturer=MANUFACTURER,  # ✅ Legacy常量fallback
            model=self._raw_device.get(
                DEVICE_TYPE_KEY, "Unknown Device"
            ),  # ✅ devtype fallback
            sw_version=self._raw_device.get(DEVICE_VERSION_KEY, "unknown"),
            via_device=(DOMAIN, self._agt),
        )
