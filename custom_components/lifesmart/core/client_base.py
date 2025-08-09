"""
此模块定义了 LifeSmart 客户端的抽象基类 (Abstract Base Class)。

由 @MapleEve 设计和实现。

核心设计思想:
- 将与协议无关的设备控制业务逻辑（例如，“打开窗帘”意味着向特定IO口发送特定值）
  集中到这个基类中，以遵循 DRY (Don't Repeat Yourself) 原则。
- 定义一组底层的、必须由具体客户端（如云端、本地）实现的抽象方法
  （如 `_async_send_single_command`），从而将“做什么”与“怎么做”分离。
- 为所有客户端提供一个统一、稳定的接口，便于上层平台（light, cover, climate等）调用。
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from homeassistant.components.climate import HVACMode

from .config.cover_mappings import NON_POSITIONAL_COVER_CONFIG
from .config.device_specs import _RAW_DEVICE_DATA
from .config.hvac_mappings import (
    REVERSE_F_HVAC_MODE_MAP,
    LIFESMART_F_FAN_MAP,
    LIFESMART_TF_FAN_MAP,
    LIFESMART_ACIPM_FAN_MAP,
    LIFESMART_CP_AIR_FAN_MAP,
    REVERSE_LIFESMART_HVAC_MODE_MAP,
    REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP,
)
from .const import (
    # --- 命令类型常量 ---
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_PRESS,
    CMD_TYPE_SET_VAL,
    CMD_TYPE_SET_CONFIG,
    CMD_TYPE_SET_TEMP_DECIMAL,
    CMD_TYPE_SET_RAW_ON,
    CMD_TYPE_SET_TEMP_FCU,
)
from .platform.platform_detection import safe_get

_LOGGER = logging.getLogger(__name__)


def _get_device_climate_config(device_type: str, action: str) -> dict | None:
    """从映射中获取设备的climate配置。"""
    device_config = _RAW_DEVICE_DATA.get(device_type, {})
    climate_config = device_config.get("climate", {})
    if not climate_config:
        return None

    # 查找相关的IO口配置
    for io_port, io_config in climate_config.items():
        if action in io_config.get("climate_actions", []):
            return {"io_port": io_port, "config": io_config}
    return None


def _get_device_hvac_config(device_type: str) -> dict | None:
    """获取设备的HVAC模式配置。"""
    # 基于设备类型的硬编码映射 - 待从raw_data获取
    hvac_configs = {
        "V_AIR_P": {"mode_io": "MODE", "mode_map": REVERSE_F_HVAC_MODE_MAP},
        "SL_NATURE": {"mode_io": "P7", "mode_map": REVERSE_LIFESMART_HVAC_MODE_MAP},
        "SL_FCU": {"mode_io": "P7", "mode_map": REVERSE_LIFESMART_HVAC_MODE_MAP},
        "SL_UACCB": {"mode_io": "P2", "mode_map": REVERSE_LIFESMART_HVAC_MODE_MAP},
        "SL_CP_AIR": {
            "mode_io": "P1",
            "mode_map": REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP,
            "use_raw": True,
        },
        "SL_CP_DN": {"mode_io": "P1", "use_raw": True, "auto_bit": 31},
        "SL_CP_VL": {
            "mode_io": "P1",
            "use_raw": True,
            "mode_map": {HVACMode.HEAT: 0, HVACMode.AUTO: 2},
        },
    }
    return hvac_configs.get(device_type)


def _get_device_temp_config(device_type: str) -> dict | None:
    """获取设备的温度设置配置。"""
    temp_configs = {
        "V_AIR_P": {"temp_io": "tT", "cmd_type": CMD_TYPE_SET_TEMP_DECIMAL},
        "SL_UACCB": {"temp_io": "P3", "cmd_type": CMD_TYPE_SET_TEMP_DECIMAL},
        "SL_CP_DN": {"temp_io": "P3", "cmd_type": CMD_TYPE_SET_RAW_ON},
        "SL_CP_AIR": {"temp_io": "P4", "cmd_type": CMD_TYPE_SET_RAW_ON},
        "SL_NATURE": {"temp_io": "P8", "cmd_type": CMD_TYPE_SET_TEMP_DECIMAL},
        "SL_FCU": {"temp_io": "P8", "cmd_type": CMD_TYPE_SET_TEMP_FCU},
        "SL_CP_VL": {"temp_io": "P3", "cmd_type": CMD_TYPE_SET_RAW_ON},
    }
    return temp_configs.get(device_type)


def _get_device_fan_config(device_type: str) -> dict | None:
    """获取设备的风扇配置。"""
    fan_configs = {
        "V_AIR_P": {
            "fan_io": "F",
            "fan_map": LIFESMART_F_FAN_MAP,
            "cmd_type": CMD_TYPE_SET_CONFIG,
        },
        "SL_TR_ACIPM": {
            "fan_io": "P2",
            "fan_map": LIFESMART_ACIPM_FAN_MAP,
            "cmd_type": CMD_TYPE_SET_RAW_ON,
        },
        "SL_NATURE": {
            "fan_io": "P9",
            "fan_map": LIFESMART_TF_FAN_MAP,
            "cmd_type": CMD_TYPE_SET_CONFIG,
        },
        "SL_FCU": {
            "fan_io": "P9",
            "fan_map": LIFESMART_TF_FAN_MAP,
            "cmd_type": CMD_TYPE_SET_CONFIG,
        },
        "SL_CP_AIR": {
            "fan_io": "P1",
            "fan_map": LIFESMART_CP_AIR_FAN_MAP,
            "use_raw": True,
        },
    }
    return fan_configs.get(device_type)


def _is_device_type(device_type: str, target_type: str) -> bool:
    """检查设备是否为特定类型。

    Args:
        device_type: 要检查的设备类型
        target_type: 目标设备类型（如'SL_DOOYA'）

    Returns:
        如果设备类型匹配则返回True
    """
    return device_type == target_type


def _is_dooya_device(device_type: str) -> bool:
    """检查设备是否为DOOYA类型窗帘。"""
    return device_type == "SL_DOOYA"


def _is_garage_door_device(device_type: str) -> bool:
    """检查设备是否为车库门类型。"""
    # 根据DEVICE_MAPPING检查车库门设备类型
    # 如果有其他车库门类型，可以在这里添加
    garage_door_types = {"SL_GARAGE"}  # 示例，需要根据实际mapping调整
    return device_type in garage_door_types


class LifeSmartClientBase(ABC):
    """
    LifeSmart 客户端的抽象基类，定义了通用的设备控制接口和共享的业务逻辑。
    """

    # --- 公共接口 (Public API) ---
    async def async_get_all_devices(self, timeout=10) -> list[dict[str, Any]]:
        """
        获取所有设备信息的公共接口。

        此方法为上层代码（如 hub.py）提供一个稳定的调用入口。
        它会调用内部的、由具体子类实现的 _async_get_all_devices 方法。
        """
        return await self._async_get_all_devices()

    async def async_send_single_command(
        self, agt: str, me: str, idx: str, command_type: int, val: Any
    ) -> int:
        """
        发送单个IO口命令的公共接口。

        由具体客户端子类实现的 _async_send_single_command 方法完成实际操作。
        """
        return await self._async_send_single_command(agt, me, idx, command_type, val)

    async def async_send_multi_command(
        self, agt: str, me: str, io_list: list[dict]
    ) -> int:
        """
        同时发送多个IO口命令的公共接口。

        由具体客户端子类实现的 _async_send_multi_command 方法完成实际操作。
        """
        return await self._async_send_multi_command(agt, me, io_list)

    async def async_set_scene(self, agt: str, scene_name: str) -> int:
        """
        激活一个场景的公共接口。

        由具体客户端子类实现的 _async_set_scene 方法完成实际操作。
        """
        return await self._async_set_scene(agt, scene_name)

    async def async_send_ir_key(
        self,
        agt: str,
        me: str,
        category: str,
        brand: str,
        keys: str,
        ai: str = "",
        idx: str = "",
    ) -> int:
        """
        发送红外按键命令的公共接口。

        Args:
            agt: 智慧中心ID
            me: 设备ID
            category: 设备类别
            brand: 品牌
            keys: 按键列表(JSON字符串)
            ai: 虚拟遥控器ID (与idx二选一)
            idx: 通用码库索引 (与ai二选一)

        Returns:
            操作结果码，0表示成功

        由具体客户端子类实现的 _async_send_ir_key 方法完成实际操作。
        """
        return await self._async_send_ir_key(agt, me, category, brand, keys, ai, idx)

    async def async_add_scene(self, agt: str, scene_name: str, actions: str) -> int:
        """
        创建新场景的公共接口。

        由具体客户端子类实现的 _async_add_scene 方法完成实际操作。
        """
        return await self._async_add_scene(agt, scene_name, actions)

    async def async_delete_scene(self, agt: str, scene_name: str) -> int:
        """
        删除场景的公共接口。

        由具体客户端子类实现的 _async_delete_scene 方法完成实际操作。
        """
        return await self._async_delete_scene(agt, scene_name)

    async def async_get_scene_list(self, agt: str) -> list[dict[str, Any]]:
        """
        获取场景列表的公共接口。

        由具体客户端子类实现的 _async_get_scene_list 方法完成实际操作。
        """
        return await self._async_get_scene_list(agt)

    async def async_get_room_list(self, agt: str) -> list[dict[str, Any]]:
        """
        获取房间列表的公共接口。

        由具体客户端子类实现的 _async_get_room_list 方法完成实际操作。
        """
        return await self._async_get_room_list(agt)

    async def async_get_hub_list(self) -> list[dict[str, Any]]:
        """
        获取中枢列表的公共接口。

        由具体客户端子类实现的 _async_get_hub_list 方法完成实际操作。
        """
        return await self._async_get_hub_list()

    async def async_change_device_icon(self, device_id: str, icon: str) -> int:
        """
        修改设备图标的公共接口。

        由具体客户端子类实现的 _async_change_device_icon 方法完成实际操作。
        """
        return await self._async_change_device_icon(device_id, icon)

    async def async_set_device_eeprom(
        self, device_id: str, key: str, value: Any
    ) -> int:
        """
        设置设备EEPROM的公共接口。

        由具体客户端子类实现的 _async_set_device_eeprom 方法完成实际操作。
        """
        return await self._async_set_device_eeprom(device_id, key, value)

    async def async_add_device_timer(
        self, device_id: str, cron_info: str, key: str
    ) -> int:
        """
        为设备添加定时器的公共接口。

        由具体客户端子类实现的 _async_add_device_timer 方法完成实际操作。
        """
        return await self._async_add_device_timer(device_id, cron_info, key)

    async def async_ir_control(self, device_id: str, options: dict) -> int:
        """
        通过场景控制红外设备的公共接口。

        由具体客户端子类实现的 _async_ir_control 方法完成实际操作。
        """
        return await self._async_ir_control(device_id, options)

    async def async_send_ir_code(self, device_id: str, ir_data: list | bytes) -> int:
        """
        发送原始红外码的公共接口。

        由具体客户端子类实现的 _async_send_ir_code 方法完成实际操作。
        """
        return await self._async_send_ir_code(device_id, ir_data)

    async def async_ir_raw_control(self, device_id: str, raw_data: str) -> int:
        """
        发送原始红外控制数据的公共接口。

        由具体客户端子类实现的 _async_ir_raw_control 方法完成实际操作。
        """
        return await self._async_ir_raw_control(device_id, raw_data)

    async def async_get_ir_remote_list(self, agt: str) -> dict[str, Any]:
        """
        获取红外遥控器列表的公共接口。

        由具体客户端子类实现的 _async_get_ir_remote_list 方法完成实际操作。
        """
        return await self._async_get_ir_remote_list(agt)

    # --- 受保护的抽象方法 (Protected Abstract Methods) ---
    @abstractmethod
    async def _async_get_all_devices(self, timeout=10) -> list[dict[str, Any]]:
        """
        [抽象方法] 获取所有设备信息，带超时控制

        每个具体的客户端（云端、本地TCP等）都必须实现此方法。
        它应该返回一个包含所有设备信息的列表。
        如果获取失败，应返回一个空列表或引发适当的异常。
        """
        pass

    @abstractmethod
    async def _async_send_single_command(
        self, agt: str, me: str, idx: str, command_type: int, val: Any
    ) -> int:
        """
        [抽象方法] 发送单个IO口命令。
        必须由具体的客户端子类（云端/本地）实现。
        """
        pass

    @abstractmethod
    async def _async_send_multi_command(
        self, agt: str, me: str, io_list: list[dict]
    ) -> int:
        """
        [抽象方法] 同时发送多个IO口的命令。
        必须由具体的客户端子类（云端/本地）实现。
        """
        pass

    @abstractmethod
    async def _async_set_scene(self, agt: str, scene_name: str) -> int:
        """[抽象方法] 激活一个场景。"""
        pass

    @abstractmethod
    async def _async_send_ir_key(
        self,
        agt: str,
        me: str,
        category: str,
        brand: str,
        keys: str,
        ai: str = "",
        idx: str = "",
    ) -> int:
        """
        [抽象方法] 发送红外按键命令。

        Args:
            agt: 智慧中心ID
            me: 设备ID
            category: 设备类别
            brand: 品牌
            keys: 按键列表(JSON字符串)
            ai: 虚拟遥控器ID (与idx二选一)
            idx: 通用码库索引 (与ai二选一)

        Returns:
            操作结果码，0表示成功
        """
        pass

    @abstractmethod
    async def _async_add_scene(self, agt: str, scene_name: str, actions: str) -> int:
        """[抽象方法] 创建新场景。"""
        pass

    @abstractmethod
    async def _async_delete_scene(self, agt: str, scene_name: str) -> int:
        """[抽象方法] 删除场景。"""
        pass

    @abstractmethod
    async def _async_get_scene_list(self, agt: str) -> list[dict[str, Any]]:
        """[抽象方法] 获取场景列表。"""
        pass

    @abstractmethod
    async def _async_get_room_list(self, agt: str) -> list[dict[str, Any]]:
        """[抽象方法] 获取房间列表。"""
        pass

    @abstractmethod
    async def _async_get_hub_list(self) -> list[dict[str, Any]]:
        """[抽象方法] 获取中枢列表。"""
        pass

    @abstractmethod
    async def _async_change_device_icon(self, device_id: str, icon: str) -> int:
        """[抽象方法] 修改设备图标。"""
        pass

    @abstractmethod
    async def _async_set_device_eeprom(
        self, device_id: str, key: str, value: Any
    ) -> int:
        """[抽象方法] 设置设备EEPROM。"""
        pass

    @abstractmethod
    async def _async_add_device_timer(
        self, device_id: str, cron_info: str, key: str
    ) -> int:
        """[抽象方法] 为设备添加定时器。"""
        pass

    @abstractmethod
    async def _async_ir_control(self, device_id: str, options: dict) -> int:
        """[抽象方法] 通过场景控制红外设备。"""
        pass

    @abstractmethod
    async def _async_send_ir_code(self, device_id: str, ir_data: list | bytes) -> int:
        """[抽象方法] 发送原始红外码。"""
        pass

    @abstractmethod
    async def _async_ir_raw_control(self, device_id: str, raw_data: str) -> int:
        """[抽象方法] 发送原始红外控制数据。"""
        pass

    @abstractmethod
    async def _async_get_ir_remote_list(self, agt: str) -> dict[str, Any]:
        """[抽象方法] 获取红外遥控器列表。"""
        pass

    # --- 通用开关/灯光控制 ---

    async def turn_on_light_switch_async(self, idx: str, agt: str, me: str) -> int:
        """开启一个灯或开关。"""
        return await self._async_send_single_command(agt, me, idx, CMD_TYPE_ON, 1)

    async def turn_off_light_switch_async(self, idx: str, agt: str, me: str) -> int:
        """关闭一个灯或开关。"""
        return await self._async_send_single_command(agt, me, idx, CMD_TYPE_OFF, 0)

    async def press_switch_async(
        self, idx: str, agt: str, me: str, duration_ms: int
    ) -> int:
        """执行点动操作（按下后在指定时间后自动弹起）。"""
        val = max(1, round(duration_ms / 100))
        return await self._async_send_single_command(agt, me, idx, CMD_TYPE_PRESS, val)

    # --- 窗帘/覆盖物控制 ---

    async def open_cover_async(self, agt: str, me: str, device_type: str) -> int:
        """开启窗帘或车库门。"""
        if _is_garage_door_device(device_type):
            return await self._async_send_single_command(
                agt, me, "P3", CMD_TYPE_SET_VAL, 100
            )
        if _is_dooya_device(device_type):
            return await self._async_send_single_command(
                agt, me, "P2", CMD_TYPE_SET_VAL, 100
            )
        if device_type in NON_POSITIONAL_COVER_CONFIG:
            cmd_idx = safe_get(NON_POSITIONAL_COVER_CONFIG, device_type, "open")
            if cmd_idx is None:
                _LOGGER.warning("设备类型 %s 缺少 'open' 配置", device_type)
                return -1
            return await self._async_send_single_command(
                agt, me, cmd_idx, CMD_TYPE_ON, 1
            )
        _LOGGER.warning("设备类型 %s 的 'open_cover' 操作未被支持。", device_type)
        return -1

    async def close_cover_async(self, agt: str, me: str, device_type: str) -> int:
        """关闭窗帘或车库门。"""
        if _is_garage_door_device(device_type):
            return await self._async_send_single_command(
                agt, me, "P3", CMD_TYPE_SET_VAL, 0
            )
        if _is_dooya_device(device_type):
            return await self._async_send_single_command(
                agt, me, "P2", CMD_TYPE_SET_VAL, 0
            )
        if device_type in NON_POSITIONAL_COVER_CONFIG:
            cmd_idx = safe_get(NON_POSITIONAL_COVER_CONFIG, device_type, "close")
            if cmd_idx is None:
                _LOGGER.warning("设备类型 %s 缺少 'close' 配置", device_type)
                return -1
            return await self._async_send_single_command(
                agt, me, cmd_idx, CMD_TYPE_ON, 1
            )
        _LOGGER.warning("设备类型 %s 的 'close_cover' 操作未被支持。", device_type)
        return -1

    async def stop_cover_async(self, agt: str, me: str, device_type: str) -> int:
        """停止窗帘或车库门。"""
        if _is_garage_door_device(device_type):
            return await self._async_send_single_command(
                agt, me, "P3", CMD_TYPE_SET_CONFIG, CMD_TYPE_OFF
            )
        if _is_dooya_device(device_type):
            return await self._async_send_single_command(
                agt, me, "P2", CMD_TYPE_SET_CONFIG, CMD_TYPE_OFF
            )
        if device_type in NON_POSITIONAL_COVER_CONFIG:
            cmd_idx = safe_get(NON_POSITIONAL_COVER_CONFIG, device_type, "stop")
            if cmd_idx is None:
                _LOGGER.warning("设备类型 %s 缺少 'stop' 配置", device_type)
                return -1
            return await self._async_send_single_command(
                agt, me, cmd_idx, CMD_TYPE_ON, 1
            )
        _LOGGER.warning("设备类型 %s 的 'stop_cover' 操作未被支持。", device_type)
        return -1

    async def set_cover_position_async(
        self, agt: str, me: str, position: int, device_type: str
    ) -> int:
        """设置窗帘或车库门到指定位置。"""
        if _is_garage_door_device(device_type):
            return await self._async_send_single_command(
                agt, me, "P3", CMD_TYPE_SET_VAL, position
            )
        if _is_dooya_device(device_type):
            return await self._async_send_single_command(
                agt, me, "P2", CMD_TYPE_SET_VAL, position
            )
        _LOGGER.warning("设备类型 %s 不支持设置位置。", device_type)
        return -1

    # --- 温控设备控制 ---

    async def async_set_climate_hvac_mode(
        self,
        agt: str,
        me: str,
        device_type: str,
        hvac_mode: HVACMode,
        current_val: int = 0,
    ) -> int:
        """设置温控设备的HVAC模式。"""
        if hvac_mode == HVACMode.OFF:
            return await self._async_send_single_command(agt, me, "P1", CMD_TYPE_OFF, 0)

        await self._async_send_single_command(agt, me, "P1", CMD_TYPE_ON, 1)

        # 使用配置化方法替代硬编码
        hvac_config = _get_device_hvac_config(device_type)
        if not hvac_config:
            _LOGGER.warning("设备类型 %s 不支持HVAC模式设置", device_type)
            return -1

        mode_io = hvac_config["mode_io"]

        # SL_CP_DN特殊处理 - 只有AUTO位
        if device_type == "SL_CP_DN":
            is_auto = 1 if hvac_mode == HVACMode.AUTO else 0
            auto_bit = hvac_config["auto_bit"]
            new_val = (current_val & ~(1 << auto_bit)) | (is_auto << auto_bit)
            return await self._async_send_single_command(
                agt, me, mode_io, CMD_TYPE_SET_RAW_ON, new_val
            )

        # 获取模式映射
        mode_map = hvac_config.get("mode_map", {})
        mode_val = mode_map.get(hvac_mode)
        if mode_val is None:
            _LOGGER.warning("设备类型 %s 不支持HVAC模式: %s", device_type, hvac_mode)
            return -1

        # 根据配置选择命令类型
        if hvac_config.get("use_raw"):
            if device_type == "SL_CP_AIR":
                new_val = (current_val & ~(0b11 << 13)) | (mode_val << 13)
            elif device_type == "SL_CP_VL":
                new_val = (current_val & ~(0b11 << 1)) | (mode_val << 1)
            else:
                new_val = mode_val
            return await self._async_send_single_command(
                agt, me, mode_io, CMD_TYPE_SET_RAW_ON, new_val
            )
        else:
            return await self._async_send_single_command(
                agt, me, mode_io, CMD_TYPE_SET_CONFIG, mode_val
            )

    async def async_set_climate_temperature(
        self, agt: str, me: str, device_type: str, temp: float
    ) -> int:
        """设置温控设备的目标温度。"""
        temp_val = int(temp * 10)

        # 使用配置化方法替代硬编码
        temp_config = _get_device_temp_config(device_type)
        if not temp_config:
            _LOGGER.warning("设备类型 %s 不支持温度设置", device_type)
            return -1

        temp_io = temp_config["temp_io"]
        cmd_type = temp_config["cmd_type"]

        return await self._async_send_single_command(
            agt, me, temp_io, cmd_type, temp_val
        )

    async def async_set_climate_fan_mode(
        self, agt: str, me: str, device_type: str, fan_mode: str, current_val: int = 0
    ) -> int:
        """设置温控设备的风扇模式。"""
        # 使用配置化方法替代硬编码
        fan_config = _get_device_fan_config(device_type)
        if not fan_config:
            _LOGGER.warning("设备类型 %s 不支持风扇模式设置", device_type)
            return -1

        fan_map = fan_config["fan_map"]
        fan_val = fan_map.get(fan_mode)
        if fan_val is None:
            _LOGGER.warning("设备类型 %s 不支持风扇模式: %s", device_type, fan_mode)
            return -1

        fan_io = fan_config["fan_io"]

        # SL_CP_AIR特殊处理 - 需要位操作
        if fan_config.get("use_raw") and device_type == "SL_CP_AIR":
            new_val = (current_val & ~(0b11 << 15)) | (fan_val << 15)
            return await self._async_send_single_command(
                agt, me, fan_io, CMD_TYPE_SET_RAW_ON, new_val
            )
        else:
            cmd_type = fan_config["cmd_type"]
            return await self._async_send_single_command(
                agt, me, fan_io, cmd_type, fan_val
            )
