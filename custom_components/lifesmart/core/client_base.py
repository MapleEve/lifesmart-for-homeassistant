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

from custom_components.lifesmart.const import (
    # --- 命令类型常量 ---
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_PRESS,
    CMD_TYPE_SET_VAL,
    CMD_TYPE_SET_CONFIG,
    CMD_TYPE_SET_TEMP_DECIMAL,
    CMD_TYPE_SET_RAW,
    CMD_TYPE_SET_TEMP_FCU,
    # --- 设备类型和映射 ---
    DOOYA_TYPES,
    GARAGE_DOOR_TYPES,
    NON_POSITIONAL_COVER_CONFIG,
    REVERSE_F_HVAC_MODE_MAP,
    LIFESMART_F_FAN_MAP,
    LIFESMART_TF_FAN_MAP,
    LIFESMART_ACIPM_FAN_MAP,
    LIFESMART_CP_AIR_FAN_MAP,
    REVERSE_LIFESMART_HVAC_MODE_MAP,
    REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP,
)

_LOGGER = logging.getLogger(__name__)


class LifeSmartClientBase(ABC):
    """
    LifeSmart 客户端的抽象基类，定义了通用的设备控制接口和共享的业务逻辑。
    """

    @abstractmethod
    async def _async_send_single_command(
        self, agt: str, me: str, idx: str, command_type: str, val: Any
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
        if device_type in GARAGE_DOOR_TYPES:
            return await self._async_send_single_command(
                agt, me, "P3", CMD_TYPE_SET_VAL, 100
            )
        if device_type in DOOYA_TYPES:
            return await self._async_send_single_command(
                agt, me, "P2", CMD_TYPE_SET_VAL, 100
            )
        if device_type in NON_POSITIONAL_COVER_CONFIG:
            cmd_idx = NON_POSITIONAL_COVER_CONFIG[device_type]["open"]
            return await self._async_send_single_command(
                agt, me, cmd_idx, CMD_TYPE_ON, 1
            )
        _LOGGER.warning("设备类型 %s 的 'open_cover' 操作未被支持。", device_type)
        return -1

    async def close_cover_async(self, agt: str, me: str, device_type: str) -> int:
        """关闭窗帘或车库门。"""
        if device_type in GARAGE_DOOR_TYPES:
            return await self._async_send_single_command(
                agt, me, "P3", CMD_TYPE_SET_VAL, 0
            )
        if device_type in DOOYA_TYPES:
            return await self._async_send_single_command(
                agt, me, "P2", CMD_TYPE_SET_VAL, 0
            )
        if device_type in NON_POSITIONAL_COVER_CONFIG:
            cmd_idx = NON_POSITIONAL_COVER_CONFIG[device_type]["close"]
            return await self._async_send_single_command(
                agt, me, cmd_idx, CMD_TYPE_ON, 1
            )
        _LOGGER.warning("设备类型 %s 的 'close_cover' 操作未被支持。", device_type)
        return -1

    async def stop_cover_async(self, agt: str, me: str, device_type: str) -> int:
        """停止窗帘或车库门。"""
        if device_type in GARAGE_DOOR_TYPES:
            return await self._async_send_single_command(
                agt, me, "P3", CMD_TYPE_SET_CONFIG, CMD_TYPE_OFF
            )
        if device_type in DOOYA_TYPES:
            return await self._async_send_single_command(
                agt, me, "P2", CMD_TYPE_SET_CONFIG, CMD_TYPE_OFF
            )
        if device_type in NON_POSITIONAL_COVER_CONFIG:
            cmd_idx = NON_POSITIONAL_COVER_CONFIG[device_type]["stop"]
            return await self._async_send_single_command(
                agt, me, cmd_idx, CMD_TYPE_ON, 1
            )
        _LOGGER.warning("设备类型 %s 的 'stop_cover' 操作未被支持。", device_type)
        return -1

    async def set_cover_position_async(
        self, agt: str, me: str, position: int, device_type: str
    ) -> int:
        """设置窗帘或车库门到指定位置。"""
        if device_type in GARAGE_DOOR_TYPES:
            return await self._async_send_single_command(
                agt, me, "P3", CMD_TYPE_SET_VAL, position
            )
        if device_type in DOOYA_TYPES:
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

        mode_val = None
        idx = None

        if device_type == "V_AIR_P":
            mode_val = REVERSE_F_HVAC_MODE_MAP.get(hvac_mode)
            idx = "MODE"
        elif device_type in {"SL_NATURE", "SL_FCU"}:
            mode_val = REVERSE_LIFESMART_HVAC_MODE_MAP.get(hvac_mode)
            idx = "P7"
        elif device_type == "SL_UACCB":
            mode_val = REVERSE_LIFESMART_HVAC_MODE_MAP.get(hvac_mode)
            idx = "P2"

        if mode_val is not None and idx is not None:
            return await self._async_send_single_command(
                agt, me, idx, CMD_TYPE_SET_CONFIG, mode_val
            )

        if device_type == "SL_CP_AIR":
            mode_val = REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP.get(hvac_mode)
            if mode_val is not None:
                new_val = (current_val & ~(0b11 << 13)) | (mode_val << 13)
                return await self._async_send_single_command(
                    agt, me, "P1", CMD_TYPE_SET_RAW, new_val
                )

        if device_type == "SL_CP_DN":
            is_auto = 1 if hvac_mode == HVACMode.AUTO else 0
            new_val = (current_val & ~(1 << 31)) | (is_auto << 31)
            return await self._async_send_single_command(
                agt, me, "P1", CMD_TYPE_SET_RAW, new_val
            )

        if device_type == "SL_CP_VL":
            mode_map = {HVACMode.HEAT: 0, HVACMode.AUTO: 2}
            mode_val = mode_map.get(hvac_mode, 0)
            new_val = (current_val & ~(0b11 << 1)) | (mode_val << 1)
            return await self._async_send_single_command(
                agt, me, "P1", CMD_TYPE_SET_RAW, new_val
            )

        return 0

    async def async_set_climate_temperature(
        self, agt: str, me: str, device_type: str, temp: float
    ) -> int:
        """设置温控设备的目标温度。"""
        temp_val = int(temp * 10)
        idx_map = {
            "V_AIR_P": ("tT", CMD_TYPE_SET_TEMP_DECIMAL),
            "SL_UACCB": ("P3", CMD_TYPE_SET_TEMP_DECIMAL),
            "SL_CP_DN": ("P3", CMD_TYPE_SET_RAW),
            "SL_CP_AIR": ("P4", CMD_TYPE_SET_RAW),
            "SL_NATURE": ("P8", CMD_TYPE_SET_TEMP_DECIMAL),
            "SL_FCU": ("P8", CMD_TYPE_SET_TEMP_FCU),
            "SL_CP_VL": ("P3", CMD_TYPE_SET_RAW),
        }
        if device_type in idx_map:
            idx, cmd_type = idx_map[device_type]
            return await self._async_send_single_command(
                agt, me, idx, cmd_type, temp_val
            )
        return -1

    async def async_set_climate_fan_mode(
        self, agt: str, me: str, device_type: str, fan_mode: str, current_val: int = 0
    ) -> int:
        """设置温控设备的风扇模式。"""
        if device_type == "V_AIR_P":
            if (fan_val := LIFESMART_F_FAN_MAP.get(fan_mode)) is not None:
                return await self._async_send_single_command(
                    agt, me, "F", CMD_TYPE_SET_CONFIG, fan_val
                )
        elif device_type == "SL_TR_ACIPM":
            if (fan_val := LIFESMART_ACIPM_FAN_MAP.get(fan_mode)) is not None:
                return await self._async_send_single_command(
                    agt, me, "P2", CMD_TYPE_SET_RAW, fan_val
                )
        elif device_type in {"SL_NATURE", "SL_FCU"}:
            if (fan_val := LIFESMART_TF_FAN_MAP.get(fan_mode)) is not None:
                return await self._async_send_single_command(
                    agt, me, "P9", CMD_TYPE_SET_CONFIG, fan_val
                )
        elif device_type == "SL_CP_AIR":
            if (fan_val := LIFESMART_CP_AIR_FAN_MAP.get(fan_mode)) is not None:
                new_val = (current_val & ~(0b11 << 15)) | (fan_val << 15)
                return await self._async_send_single_command(
                    agt, me, "P1", CMD_TYPE_SET_RAW, new_val
                )

        _LOGGER.warning("设备类型 %s 不支持风扇模式: %s", device_type, fan_mode)
        return -1
