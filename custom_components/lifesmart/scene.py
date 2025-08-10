"""
LifeSmart 场景平台支持模块

由 @MapleEve 创建和维护

本模块为LifeSmart平台提供智能场景设备支持，实现了对各种
智能场景的激活和管理。

支持的场景类型：
- 预设场景：回家、离家、睡眠模式
- 自定义场景：用户配置的个性化场景
- 情景模式：日间、夜间、聚会模式
- 系统场景：安全、应急等特殊场景

技术特性：
- 一键激活多设备协同控制
- 场景状态跟踪和记录
- 智能场景名称识别
- 实时激活事件监测
"""

import logging
from typing import Any

from homeassistant.components.scene import Scene
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core.const import (
    # 核心常量
    DOMAIN,
    MANUFACTURER,
    HUB_ID_KEY,
    DEVICE_ID_KEY,
    DEVICE_TYPE_KEY,
    DEVICE_NAME_KEY,
    DEVICE_DATA_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    # 场景平台相关
    # 命令常量
    CMD_TYPE_PRESS,
)
from .core.entity import LifeSmartEntity
from .core.helpers import generate_unique_id
from .core.platform.platform_detection import get_scene_subdevices
from .core.platform.platform_detection import safe_get

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    从配置条目设置 LifeSmart 场景设备。
    """
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    scenes = []
    for device in hub.get_devices():
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device.get(DEVICE_TYPE_KEY)
        if not device_type:
            continue

        # 使用平台检测函数获取scene子设备
        scene_subdevices = get_scene_subdevices(device)

        # 为每个支持的scene子设备创建实体
        for sub_key in scene_subdevices:
            sub_device_data = safe_get(device, DEVICE_DATA_KEY, sub_key, default={})
            if sub_device_data:  # 只有当存在实际数据时才创建实体
                scene = LifeSmartScene(
                    raw_device=device,
                    client=hub.get_client(),
                    entry_id=config_entry.entry_id,
                    sub_device_key=sub_key,
                    sub_device_data=sub_device_data,
                )
                scenes.append(scene)
                _LOGGER.debug(
                    "Added scene %s for device %s",
                    sub_key,
                    device.get(DEVICE_NAME_KEY),
                )

    if scenes:
        async_add_entities(scenes)
        _LOGGER.info("Added %d LifeSmart scenes", len(scenes))


class LifeSmartScene(LifeSmartEntity, Scene):
    """
    LifeSmart 场景设备实现类。
    """

    def __init__(
        self,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
        sub_device_key: str,
        sub_device_data: dict[str, Any],
    ) -> None:
        """
        初始化场景设备。
        """
        super().__init__(raw_device, client)
        self._sub_key = sub_device_key
        self._sub_data = sub_device_data
        self._entry_id = entry_id

        # 生成场景名称和ID
        self._attr_name = self._generate_scene_name()
        self._attr_unique_id = generate_unique_id(
            self.devtype,
            self.agt,
            self.me,
            sub_device_key,
        )

        # 场景相关属性
        self._scene_id = self._extract_scene_id()
        self._scene_name = self._extract_scene_name()
        self._last_activated = None

    @callback
    def _generate_scene_name(self) -> str | None:
        """
        生成用户友好的场景名称。
        """
        base_name = self._name
        # 如果子设备有自己的名字，则使用它
        sub_name = self._sub_data.get(DEVICE_NAME_KEY)
        if sub_name and sub_name != self._sub_key:
            return f"{base_name} {sub_name}"

        # 尝试从scene配置中获取场景名称
        scene_name = self._extract_scene_name()
        if scene_name:
            return f"{base_name} {scene_name}"

        # 否则，使用基础名 + IO口索引
        return f"{base_name} Scene {self._sub_key.upper()}"

    @callback
    def _extract_scene_id(self) -> int | None:
        """
        从设备数据中提取场景ID。
        """
        # 从val字段获取场景ID
        scene_id = self._sub_data.get("val")
        if scene_id is not None:
            return int(scene_id)
        return None

    @callback
    def _extract_scene_name(self) -> str | None:
        """
        从设备数据中提取场景名称。
        """
        # 尝试从不同的字段获取场景名称
        scene_name = self._sub_data.get("scene_name") or self._sub_data.get("name")
        if scene_name:
            return str(scene_name)

        # 如果没有场景名称，使用默认命名
        scene_id = self._scene_id
        if scene_id is not None:
            return f"Scene {scene_id}"

        return None

    async def async_activate(self, **kwargs) -> None:
        """
        激活场景。
        """
        try:
            # 发送场景激活命令
            await self._client.async_send_command(
                self.agt,
                self.me,
                self._sub_key,
                CMD_TYPE_PRESS,
                1,  # 激活场景
            )

            # 记录激活时间
            import datetime

            self._last_activated = datetime.datetime.now()

            _LOGGER.debug(
                "Activated scene %s (%s) on device %s",
                self._scene_name or self._sub_key,
                self._scene_id,
                self._name,
            )

            # 更新状态
            self.async_write_ha_state()

        except Exception as err:
            _LOGGER.error(
                "Failed to activate scene %s on device %s: %s",
                self._sub_key,
                self._name,
                err,
            )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """
        为该场景返回额外的状态属性。
        """
        # Get base attributes from parent class
        base_attrs = super().extra_state_attributes or {}

        # Add scene-specific attributes
        scene_attrs = {}

        if self._scene_id is not None:
            scene_attrs["scene_id"] = self._scene_id

        if self._scene_name:
            scene_attrs["scene_name"] = self._scene_name

        if self._last_activated:
            scene_attrs["last_activated"] = self._last_activated.isoformat()

        # Merge attributes
        if scene_attrs:
            return {**base_attrs, **scene_attrs}

        return base_attrs

    @property
    def device_info(self) -> DeviceInfo:
        """
        返回设备信息。
        """
        return DeviceInfo(
            identifiers={(DOMAIN, self.agt, self.me)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=self.devtype,
            via_device=(DOMAIN, self.agt),
        )

    async def async_added_to_hass(self) -> None:
        """
        订阅状态更新。
        """
        await super().async_added_to_hass()

        # 实体特定更新
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{self._attr_unique_id}",
                self._handle_update,
            )
        )

        # 全局更新
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                LIFESMART_SIGNAL_UPDATE_ENTITY,
                self._handle_global_refresh,
            )
        )

    async def _handle_update(self, new_data: dict) -> None:
        """
        处理实时状态更新。
        """
        try:
            if not new_data:
                return

            # 提取IO数据
            io_data = {}
            if "msg" in new_data and isinstance(new_data["msg"], dict):
                io_data = new_data["msg"].get(self._sub_key, {})
            elif self._sub_key in new_data:
                io_data = new_data[self._sub_key]
            else:
                io_data = new_data

            if not io_data:
                return

            # 检查是否是场景激活事件
            if "type" in io_data and (io_data["type"] & 1):
                # 场景被激活
                import datetime

                self._last_activated = datetime.datetime.now()

                _LOGGER.debug(
                    "Scene %s activated via real-time update",
                    self._scene_name or self._sub_key,
                )

                self.async_write_ha_state()

            # 更新场景信息
            state_changed = False
            if "val" in io_data:
                new_scene_id = int(io_data["val"])
                if self._scene_id != new_scene_id:
                    self._scene_id = new_scene_id
                    state_changed = True

            if "scene_name" in io_data or "name" in io_data:
                new_scene_name = io_data.get("scene_name") or io_data.get("name")
                if self._scene_name != new_scene_name:
                    self._scene_name = str(new_scene_name) if new_scene_name else None
                    state_changed = True

            if state_changed:
                self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(
                "Error handling scene update for %s: %s", self._attr_unique_id, e
            )

    async def _handle_global_refresh(self) -> None:
        """
        处理周期性的全数据刷新。
        """
        try:
            devices = self.hass.data[DOMAIN][self._entry_id]["devices"]
            current_device = next(
                (
                    d
                    for d in devices
                    if d[HUB_ID_KEY] == self.agt and d[DEVICE_ID_KEY] == self.me
                ),
                None,
            )

            if current_device is None:
                if self.available:
                    _LOGGER.warning(
                        "Scene device %s not found during global refresh, "
                        "marking as unavailable.",
                        self.unique_id,
                    )
                    self._attr_available = False
                    self.async_write_ha_state()
                return

            new_sub_data = safe_get(current_device, DEVICE_DATA_KEY, self._sub_key)
            if new_sub_data is None:
                if self.available:
                    _LOGGER.warning(
                        "Scene sub-device %s for %s not found, marking as unavailable.",
                        self._sub_key,
                        self.unique_id,
                    )
                    self._attr_available = False
                    self.async_write_ha_state()
                return

            if not self.available:
                self._attr_available = True

            # 保存旧值用于比较
            old_scene_id = self._scene_id
            old_scene_name = self._scene_name

            # 更新数据并重新提取场景信息
            self._sub_data = new_sub_data
            self._scene_id = self._extract_scene_id()
            self._scene_name = self._extract_scene_name()

            # 如果场景信息有变化，更新HA状态
            if old_scene_id != self._scene_id or old_scene_name != self._scene_name:
                self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(
                "Error during scene global refresh for %s: %s", self.unique_id, e
            )
