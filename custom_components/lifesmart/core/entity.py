"""LifeSmart 集成的实体基类。

此模块提供所有平台实体共享的基类，包括通用属性、方法和状态管理逻辑。

由 @MapleEve 创建，作为集成架构重构的一部分。
"""

import logging
from typing import Any

from homeassistant.exceptions import PlatformNotReady, HomeAssistantError
from homeassistant.helpers.entity import Entity

from .client_base import LifeSmartClientBase
from .const import DEVICE_ID_KEY, DEVICE_NAME_KEY, DEVICE_TYPE_KEY, HUB_ID_KEY

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
