"""LifeSmart 集成的实体基类。

此模块提供所有平台实体共享的基类，包括通用属性、方法和状态管理逻辑。

由 @MapleEve 创建，作为集成架构重构的一部分。
"""

from typing import Any

from homeassistant.helpers.entity import Entity

from .const import DEVICE_ID_KEY, DEVICE_NAME_KEY, DEVICE_TYPE_KEY, HUB_ID_KEY
from .core.client_base import LifeSmartClientBase


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
