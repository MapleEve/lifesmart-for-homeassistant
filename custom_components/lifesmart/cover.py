"""
此模块为 LifeSmart 平台提供窗帘、车库门等覆盖物 (Cover) 设备支持。

由 @MapleEve 初始创建和维护。

主要功能:
- 定义 LifeSmartBaseCover、LifeSmartPositionalCover 和 LifeSmartNonPositionalCover
  三个类，分别代表覆盖物设备的基类、支持位置控制的设备和不支持位置控制的设备。
- 在 `async_setup_entry` 中，根据设备类型和IO口配置，智能地创建正确的实体。
- 对通用控制器 (Generic Controller) 进行特殊处理，仅当其工作在窗帘模式时才创建实体。
- 实现乐观更新 (Optimistic Update)，在用户发出指令后立即更新UI状态，提升响应体验。
- 精确处理非定位窗帘在“移动中停止”后的最终状态判断。
"""

import logging
from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DEVICE_DATA_KEY,
    DEVICE_ID_KEY,
    DEVICE_NAME_KEY,
    DEVICE_TYPE_KEY,
    DEVICE_VERSION_KEY,
    DOMAIN,
    DOOYA_TYPES,
    GARAGE_DOOR_TYPES,
    GENERIC_CONTROLLER_TYPES,
    HUB_ID_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    MANUFACTURER,
    NON_POSITIONAL_COVER_CONFIG,
)
from .entity import LifeSmartEntity
from .helpers import generate_unique_id, get_cover_subdevices, safe_get

# 初始化模块级日志记录器
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    从配置条目异步设置 LifeSmart 覆盖物设备。

    此函数负责筛选出所有覆盖物设备，并为每个设备的有效控制点创建实体。
    它包含对通用控制器的特殊处理逻辑。
    """
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    covers = []
    for device in hub.get_devices():
        # 如果设备或其所属网关在排除列表中，则跳过
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        # 使用helpers中的统一逻辑获取所有有效的窗帘子设备
        subdevice_keys = get_cover_subdevices(device)
        for sub_key in subdevice_keys:
            device_type = device.get(DEVICE_TYPE_KEY)

            # 根据设备是否支持位置，创建不同类型的实体
            if device_type in GARAGE_DOOR_TYPES or device_type in DOOYA_TYPES:
                covers.append(
                    LifeSmartPositionalCover(
                        raw_device=device,
                        client=hub.get_client(),
                        entry_id=config_entry.entry_id,
                        sub_device_key=sub_key,
                    )
                )
            elif (
                device_type in NON_POSITIONAL_COVER_CONFIG
                or device_type in GENERIC_CONTROLLER_TYPES
            ):
                covers.append(
                    LifeSmartNonPositionalCover(
                        raw_device=device,
                        client=hub.get_client(),
                        entry_id=config_entry.entry_id,
                        sub_device_key=sub_key,
                    )
                )

    async_add_entities(covers)


class LifeSmartBaseCover(LifeSmartEntity, CoverEntity):
    """
    LifeSmart 覆盖物设备的基类。

    实现了所有覆盖物设备共有的逻辑，如设备信息、实体唯一ID、
    更新处理机制和基础的开/关/停服务调用。
    """

    def __init__(
        self,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
        sub_device_key: str,
    ) -> None:
        """初始化覆盖物基类。"""
        super().__init__(raw_device, client)
        self._entry_id = entry_id
        self._sub_key = sub_device_key

        # --- 实体命名逻辑 ---
        base_name = self._name
        # 尝试从IO口数据中获取更具体的名称
        sub_name_from_data = safe_get(
            raw_device, DEVICE_DATA_KEY, self._sub_key, DEVICE_NAME_KEY
        )
        # 如果没有具体名称，则使用IO口键名作为后缀
        suffix = (
            sub_name_from_data
            if sub_name_from_data and sub_name_from_data != self._sub_key
            else self._sub_key.upper()
        )
        self._attr_name = f"{base_name} {suffix}"

        # --- 实体ID生成逻辑 ---
        device_name_slug = self._name.lower().replace(" ", "_")
        sub_key_slug = self._sub_key.lower()
        self._attr_object_id = f"{device_name_slug}_{sub_key_slug}"

        self._attr_unique_id = generate_unique_id(
            self.devtype, self.agt, self.me, self._sub_key
        )

        # 初始化状态
        self._initialize_state()

    @callback
    def _initialize_state(self) -> None:
        """初始化状态的抽象方法，由子类实现。"""
        raise NotImplementedError

    @property
    def device_info(self) -> DeviceInfo:
        """返回设备信息，用于在 Home Assistant UI 中将实体链接到物理设备。"""
        return DeviceInfo(
            identifiers={(DOMAIN, self.agt, self.me)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=self.devtype,
            sw_version=self._raw_device.get(DEVICE_VERSION_KEY, "unknown"),
            via_device=(DOMAIN, self.agt),
        )

    async def async_added_to_hass(self) -> None:
        """当实体被添加到 Home Assistant 时，注册更新监听器。"""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{self._attr_unique_id}",
                self._handle_update,
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, LIFESMART_SIGNAL_UPDATE_ENTITY, self._handle_global_refresh
            )
        )

    @callback
    def _handle_update(self, new_data: dict) -> None:
        """处理来自 WebSocket 的实时状态更新。"""
        if new_data:
            self._raw_device[DEVICE_DATA_KEY] = new_data
            self._initialize_state()
            self.async_write_ha_state()

    @callback
    def _handle_global_refresh(self) -> None:
        """处理来自 API 轮询的全局设备列表刷新。"""
        try:
            devices = self.hass.data[DOMAIN][self._entry_id]["devices"]
            current_device = next(
                (d for d in devices if d[DEVICE_ID_KEY] == self.me), None
            )
            if current_device:
                self._raw_device = current_device
                self._initialize_state()
                self.async_write_ha_state()
        except (KeyError, StopIteration):
            _LOGGER.warning("在全局刷新期间未能找到设备 %s。", self._attr_unique_id)

    async def async_open_cover(self, **kwargs: Any) -> None:
        """
        打开覆盖物，并进行乐观更新。

        在向设备发送命令的同时，立即将实体状态更新为 'opening'，
        为用户提供即时反馈。
        """
        self._attr_is_opening = True
        self._attr_is_closing = False
        self.async_write_ha_state()
        await self._client.open_cover_async(self.agt, self.me, self.devtype)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """
        关闭覆盖物，并进行乐观更新。

        立即将实体状态更新为 'closing'。
        """
        self._attr_is_closing = True
        self._attr_is_opening = False
        self.async_write_ha_state()
        await self._client.close_cover_async(self.agt, self.me, self.devtype)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """
        停止覆盖物移动，并进行乐观更新。

        立即将实体的 'is_opening' 和 'is_closing' 标志位设为 False。
        最终状态（open/closed）将由下一次设备状态更新来确定。
        """
        self._attr_is_opening = False
        self._attr_is_closing = False
        self.async_write_ha_state()
        await self._client.stop_cover_async(self.agt, self.me, self.devtype)


class LifeSmartPositionalCover(LifeSmartBaseCover):
    """代表支持位置控制的 LifeSmart 覆盖物设备。"""

    def __init__(
        self,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
        sub_device_key: str,
    ) -> None:
        """初始化定位覆盖物。"""
        super().__init__(raw_device, client, entry_id, sub_device_key)
        self._attr_supported_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )
        self._attr_device_class = (
            CoverDeviceClass.GARAGE
            if self.devtype in GARAGE_DOOR_TYPES
            else CoverDeviceClass.CURTAIN
        )

    @callback
    def _initialize_state(self) -> None:
        """
        从设备数据中解析并更新实体的状态。

        此方法解析包含位置和移动方向的 'val' 值。
        - val 的低7位 (val & 0x7F) 代表当前位置 (0-100)。
        - val 的最高位 (val & 0x80) 代表移动方向 (0=开, 1=关)。
        - 'type' 值的奇偶性代表是否正在移动。
        """
        status_data = safe_get(
            self._raw_device, DEVICE_DATA_KEY, self._sub_key, default={}
        )
        if not status_data:
            return  # 如果没有状态数据，则不进行更新

        val = status_data.get("val", 0)
        self._attr_current_cover_position = val & 0x7F
        is_moving = status_data.get("type", 0) & 1 == 1
        is_opening_direction = (val & 0x80) == 0

        self._attr_is_opening = is_moving and is_opening_direction
        self._attr_is_closing = is_moving and not is_opening_direction
        self._attr_is_closed = (
            self.current_cover_position is not None and self.current_cover_position <= 0
        )

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """设置覆盖物到指定位置。"""
        position = kwargs[ATTR_POSITION]
        # 乐观更新：假设窗帘会朝目标位置移动
        if self.current_cover_position is not None:
            if position > self.current_cover_position:
                self._attr_is_opening = True
                self._attr_is_closing = False
            else:
                self._attr_is_closing = True
                self._attr_is_opening = False
            self.async_write_ha_state()

        await self._client.set_cover_position_async(
            self.agt, self.me, position, self.devtype
        )


class LifeSmartNonPositionalCover(LifeSmartBaseCover):
    """代表仅支持开/关/停的 LifeSmart 覆盖物设备。"""

    def __init__(
        self,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
        sub_device_key: str,
    ) -> None:
        """初始化非定位覆盖物。"""
        # 用于在停止时判断最终状态
        self._last_known_is_opening = False

        super().__init__(raw_device, client, entry_id, sub_device_key)
        self._attr_supported_features = (
            CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
        )
        self._attr_device_class = CoverDeviceClass.CURTAIN

    @callback
    def _initialize_state(self) -> None:
        """
        从设备数据中解析并更新实体的状态。

        此方法通过检查开（OP）、关（CL）IO口的 'type' 值的奇偶性来判断
        窗帘是否正在移动。
        """
        self._attr_current_cover_position = None
        config_key = (
            "SL_P" if self.devtype in GENERIC_CONTROLLER_TYPES else self.devtype
        )
        config = NON_POSITIONAL_COVER_CONFIG.get(config_key, {})
        data = safe_get(self._raw_device, DEVICE_DATA_KEY, default={})

        # 如果没有配置或数据，则不更新
        if not config or not data:
            return

        is_opening = data.get(config["open"], {}).get("type", 0) & 1 == 1
        is_closing = data.get(config["close"], {}).get("type", 0) & 1 == 1

        # 记录最后一次的移动方向
        if is_opening:
            self._last_known_is_opening = True
        elif is_closing:
            self._last_known_is_opening = False

        self._attr_is_opening = is_opening
        self._attr_is_closing = is_closing

        # 判断是否关闭
        if not is_opening and not is_closing:
            # 如果停止移动，根据最后一次的移动方向来判断最终状态
            # 如果最后是打开方向，则认为最终是打开状态 (is_closed = False)
            # 如果最后是关闭方向，则认为最终是关闭状态 (is_closed = True)
            self._attr_is_closed = not self._last_known_is_opening
        else:
            # 如果正在移动，则肯定不是关闭状态
            self._attr_is_closed = False
