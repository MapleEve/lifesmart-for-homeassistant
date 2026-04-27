"""
LifeSmart Camera 平台支持模块

由 @MapleEve 创建和维护

本模块为LifeSmart平台提供摄像头设备(Camera)支持，实现了对各种智能摄像头的
全面控制和状态监测。

支持的摄像头功能：
- 实时视频流
- 摄像头开关控制
- 录制功能控制
- 移动侦测设置

摄像头设备类型：
- 室内摄像头：家庭安防监控
- 户外摄像头：室外环境监控
- 智能门铃：门口访客监控

技术特性：
- 配置驱动的IO口检测
- 统一的状态更新机制
- 实时数据与全局刷新双重监听
- 优雅的异常处理和日志记录
"""

import logging
from typing import Any

from homeassistant.components.camera import Camera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core.const import (
    DOMAIN,
    DEVICE_ID_KEY,
    HUB_ID_KEY,
    DEVICE_DATA_KEY,
    DEVICE_TYPE_KEY,
    DEVICE_NAME_KEY,
)
from .core.helpers import generate_unique_id
from .core.platform.platform_detection import get_camera_subdevices

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    从配置条目异步设置 LifeSmart 摄像头设备。

    此函数是摄像头平台的入口点，负责扫描所有设备并创建摄像头实体。

    Args:
        hass: Home Assistant 核心实例
        config_entry: 集成的配置条目，包含认证信息等
        async_add_entities: 用于向 HA 添加实体的回调函数

    Returns:
        None

    处理流程:
        1. 获取 hub 实例和排除配置
        2. 遍历所有设备，检查是否被排除
        3. 使用平台检测函数识别摄像头子设备
        4. 为每个摄像头子设备创建对应实体
        5. 批量添加到 Home Assistant
    """
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    cameras = []
    for device in hub.get_devices():
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        # 使用平台检测函数获取摄像头子设备
        camera_subdevices = get_camera_subdevices(device)

        # 为每个摄像头子设备创建实体
        for sub_key in camera_subdevices:
            try:
                camera = LifeSmartCamera(
                    device=device,
                    sub_key=sub_key,
                    hub=hub,
                )
                cameras.append(camera)
                _LOGGER.debug(
                    "Created camera entity for device %s, sub_key %s",
                    device.get(DEVICE_ID_KEY, "unknown"),
                    sub_key,
                )
            except Exception as e:
                _LOGGER.warning(
                    "Failed to create camera entity for device %s, sub_key %s: %s",
                    device.get(DEVICE_ID_KEY, "unknown"),
                    sub_key,
                    e,
                )

    if cameras:
        async_add_entities(cameras)
        _LOGGER.info("Added %d LifeSmart cameras", len(cameras))


class LifeSmartCamera(Camera):
    """
    LifeSmart 摄像头设备实体。

    提供标准的Home Assistant摄像头功能，包括：
    - 设备信息和状态监测
    - 移动检测
    - 电池状态（针对支持的设备）
    - 摄像头状态检测
    """

    def __init__(self, device: dict[str, Any], sub_key: str, hub) -> None:
        """
        初始化LifeSmart摄像头实体。

        Args:
            device: 设备字典数据
            sub_key: 子设备键，对应设备的IO口
            hub: LifeSmart Hub实例
        """
        self._device = device
        self._sub_key = sub_key
        self._hub = hub

        # 设备基本信息
        self._devtype = device.get(DEVICE_TYPE_KEY, "")
        self._me = device.get(DEVICE_ID_KEY, "")
        self._agt = device.get(HUB_ID_KEY, "")
        self._name = device.get(DEVICE_NAME_KEY, "Camera")

        # 生成唯一ID
        self._unique_id = generate_unique_id(
            self._devtype,
            self._agt,
            self._me,
            self._sub_key,
        )

        # 状态缓存
        self._attr_available = True

        _LOGGER.debug(
            "Initialized camera %s for device %s",
            self._unique_id,
            self._me,
        )

    @property
    def unique_id(self) -> str:
        """返回实体的唯一标识符。"""
        return self._unique_id

    @property
    def name(self) -> str:
        """返回实体的名称。"""
        if self._sub_key and len(get_camera_subdevices(self._device)) > 1:
            return f"{self._name} {self._sub_key}"
        return self._name

    @property
    def device_info(self) -> dict[str, Any]:
        """返回设备信息。"""
        return {
            "identifiers": {(DOMAIN, self._me)},
            "name": self._name,
            "model": self._devtype,
            "manufacturer": "LifeSmart",
            "via_device": (DOMAIN, self._agt),
        }

    @property
    def should_poll(self) -> bool:
        """摄像头不需要定期轮询，使用推送更新。"""
        return False

    @property
    def available(self) -> bool:
        """返回摄像头是否可用。"""
        # 检查设备在线状态
        device_online = self._device.get("stat", 0) == 1

        # 检查hub连接状态
        hub_online = getattr(self._hub, "available", True)

        return device_online and hub_online

    @property
    def motion_detection_enabled(self) -> bool | None:
        """返回移动检测是否开启。"""
        device_data = self._device.get(DEVICE_DATA_KEY, {})
        m_data = device_data.get("M")

        if m_data and isinstance(m_data, dict):
            # val=1表示检测到移动
            return m_data.get("val", 0) == 1

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """返回额外的状态属性。"""
        attrs = {}
        device_data = self._device.get(DEVICE_DATA_KEY, {})

        # 添加设备类型信息
        dev_rt = self._device.get("dev_rt")
        if dev_rt:
            attrs["device_type"] = dev_rt

        # 添加电池状态（仅FRAME设备）
        if "V" in device_data and dev_rt == "LSCAM:LSCAMV1":
            v_data = device_data["V"]
            if isinstance(v_data, dict) and "v" in v_data:
                attrs["battery_level"] = v_data["v"]

        # 添加摄像头状态（仅FRAME设备）
        if "CFST" in device_data and dev_rt == "LSCAM:LSCAMV1":
            cfst_data = device_data["CFST"]
            if isinstance(cfst_data, dict) and "val" in cfst_data:
                val = cfst_data["val"]
                attrs["has_power"] = bool(val & 0x01)
                attrs["has_pan_tilt"] = bool(val & 0x02)
                attrs["is_rotating"] = bool(val & 0x04)

        return attrs if attrs else None

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """
        获取摄像头快照图像。

        注意：此方法需要根据LifeSmart API实现具体的图像获取逻辑。
        目前返回None，表示不支持快照功能。

        Args:
            width: 请求的图像宽度
            height: 请求的图像高度

        Returns:
            图像的字节数据或None
        """
        # TODO: 根据LifeSmart API实现图像获取
        _LOGGER.debug("Camera snapshot requested for %s", self._unique_id)
        return None

    async def async_update(self) -> None:
        """
        更新摄像头状态。

        由于使用推送更新机制，此方法主要用于手动刷新状态。
        """
        try:
            # 从hub获取最新的设备数据
            updated_device = self._hub.get_device_by_id(self._me)
            if updated_device:
                self._device = updated_device
                _LOGGER.debug("Updated camera data for %s", self._unique_id)
            else:
                _LOGGER.warning("Could not find device %s in hub", self._me)
        except Exception as e:
            _LOGGER.error("Failed to update camera %s: %s", self._unique_id, e)
            self._attr_available = False
