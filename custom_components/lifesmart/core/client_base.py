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
from .const import HTTP_TIMEOUT
from typing import Any

from homeassistant.components.climate import HVACMode

from .config.cover_mappings import NON_POSITIONAL_COVER_CONFIG
from .config.mapping_engine import mapping_engine
from .const import (
    # --- 命令类型常量 ---
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_PRESS,
    CMD_TYPE_SET_VAL,
    CMD_TYPE_SET_CONFIG,
    CMD_TYPE_SET_TEMP_DECIMAL,
    CMD_TYPE_SET_RAW_ON,
)
from .platform.platform_detection import (
    safe_get,
    is_cover,
    get_device_effective_type,
)

_LOGGER = logging.getLogger(__name__)

# 常量定义
COVER_PLATFORM_NOT_SUPPORTED = "设备不支持cover平台操作"


class LifeSmartClientBase(ABC):
    """
    LifeSmart 客户端的抽象基类，定义了通用的设备控制接口和共享的业务逻辑。
    """

    # --- 公共接口 (Public API) ---
    async def async_get_all_devices(self, timeout=HTTP_TIMEOUT) -> list[dict[str, Any]]:
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
    async def _async_get_all_devices(
        self, timeout=HTTP_TIMEOUT
    ) -> list[dict[str, Any]]:
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

    async def open_cover_async(self, agt: str, me: str, device: dict) -> int:
        """开启窗帘或车库门。"""
        if not is_cover(device):
            _LOGGER.warning(COVER_PLATFORM_NOT_SUPPORTED)
            return -1

        device_type = get_device_effective_type(device)

        # 获取设备映射配置
        device_mapping = mapping_engine.resolve_device_mapping_from_data(device)
        cover_config = device_mapping.get("cover", {})

        # 查找合适的IO口进行操作
        for io_port, io_config in cover_config.items():
            if isinstance(io_config, dict):
                # 检查是否有commands配置
                commands = io_config.get("commands", {})
                if "open" in commands:
                    open_cmd = commands["open"]
                    return await self._async_send_single_command(
                        agt,
                        me,
                        io_port,
                        open_cmd.get("type", CMD_TYPE_SET_VAL),
                        open_cmd.get("val", 100),
                    )

                # 旧的逻辑:通过描述判断
                description = io_config.get("description", "").lower()
                if "position" in description:
                    return await self._async_send_single_command(
                        agt, me, io_port, CMD_TYPE_SET_VAL, 100
                    )
                elif "open" in description:
                    return await self._async_send_single_command(
                        agt, me, io_port, CMD_TYPE_ON, 1
                    )

        # 回退到NON_POSITIONAL_COVER_CONFIG
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

    async def close_cover_async(self, agt: str, me: str, device: dict) -> int:
        """关闭窗帘或车库门。"""
        if not is_cover(device):
            _LOGGER.warning(COVER_PLATFORM_NOT_SUPPORTED)
            return -1

        device_type = get_device_effective_type(device)

        # 获取设备映射配置
        device_mapping = mapping_engine.resolve_device_mapping_from_data(device)
        cover_config = device_mapping.get("cover", {})

        # 查找合适的IO口进行操作
        for io_port, io_config in cover_config.items():
            if isinstance(io_config, dict):
                # 检查是否有commands配置
                commands = io_config.get("commands", {})
                if "close" in commands:
                    close_cmd = commands["close"]
                    return await self._async_send_single_command(
                        agt,
                        me,
                        io_port,
                        close_cmd.get("type", CMD_TYPE_SET_VAL),
                        close_cmd.get("val", 0),
                    )

                # 旧的逻辑:通过描述判断
                description = io_config.get("description", "").lower()
                if "position" in description:
                    return await self._async_send_single_command(
                        agt, me, io_port, CMD_TYPE_SET_VAL, 0
                    )
                elif "close" in description:
                    return await self._async_send_single_command(
                        agt, me, io_port, CMD_TYPE_ON, 1
                    )

        # 回退到NON_POSITIONAL_COVER_CONFIG
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

    async def stop_cover_async(self, agt: str, me: str, device: dict) -> int:
        """停止窗帘或车库门。"""
        if not is_cover(device):
            _LOGGER.warning(COVER_PLATFORM_NOT_SUPPORTED)
            return -1

        device_type = get_device_effective_type(device)

        # 获取设备映射配置
        device_mapping = mapping_engine.resolve_device_mapping_from_data(device)
        cover_config = device_mapping.get("cover", {})

        # 查找合适的IO口进行操作
        for io_port, io_config in cover_config.items():
            if isinstance(io_config, dict):
                # 检查是否有commands配置
                commands = io_config.get("commands", {})
                if "stop" in commands:
                    stop_cmd = commands["stop"]
                    return await self._async_send_single_command(
                        agt,
                        me,
                        io_port,
                        stop_cmd.get("type", CMD_TYPE_SET_CONFIG),
                        stop_cmd.get("val", CMD_TYPE_OFF),
                    )

                # 旧的逻辑:通过描述判断
                description = io_config.get("description", "").lower()
                if "position" in description:
                    return await self._async_send_single_command(
                        agt, me, io_port, CMD_TYPE_SET_CONFIG, CMD_TYPE_OFF
                    )
                elif "stop" in description:
                    return await self._async_send_single_command(
                        agt, me, io_port, CMD_TYPE_ON, 1
                    )

        # 回退到NON_POSITIONAL_COVER_CONFIG
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
        self, agt: str, me: str, position: int, device: dict
    ) -> int:
        """设置窗帘或车库门到指定位置。"""
        if not is_cover(device):
            _LOGGER.warning(COVER_PLATFORM_NOT_SUPPORTED)
            return -1

        device_type = get_device_effective_type(device)

        # 获取设备映射配置
        device_mapping = mapping_engine.resolve_device_mapping_from_data(device)
        cover_config = device_mapping.get("cover", {})

        # 查找位置控制IO口
        for io_port, io_config in cover_config.items():
            if isinstance(io_config, dict):
                # 检查是否有commands配置
                commands = io_config.get("commands", {})
                if "set_position" in commands:
                    set_pos_cmd = commands["set_position"]
                    return await self._async_send_single_command(
                        agt,
                        me,
                        io_port,
                        set_pos_cmd.get("type", CMD_TYPE_SET_VAL),
                        position,
                    )

                # 旧的逻辑:通过描述判断
                description = io_config.get("description", "").lower()
                if "position" in description:
                    return await self._async_send_single_command(
                        agt, me, io_port, CMD_TYPE_SET_VAL, position
                    )

        _LOGGER.warning("设备类型 %s 不支持设置位置。", device_type)
        return -1

    # --- 温控设备控制 ---

    async def async_set_climate_hvac_mode(
        self,
        agt: str,
        me: str,
        device: dict,
        hvac_mode: HVACMode,
        current_val: int = 0,
    ) -> int:
        """设置温控设备的HVAC模式。"""
        device_type = get_device_effective_type(device)

        # 获取设备映射配置
        device_mapping = mapping_engine.resolve_device_mapping_from_data(device)
        climate_config = device_mapping.get("climate", {})

        if hvac_mode == HVACMode.OFF:
            # 查找开关IO口
            for io_port, io_config in climate_config.items():
                if isinstance(io_config, dict):
                    commands = io_config.get("commands", {})
                    if "off" in commands:
                        off_cmd = commands["off"]
                        return await self._async_send_single_command(
                            agt,
                            me,
                            io_port,
                            off_cmd.get("type", CMD_TYPE_OFF),
                            off_cmd.get("val", 0),
                        )
            # 默认使用P1口关闭
            return await self._async_send_single_command(agt, me, "P1", CMD_TYPE_OFF, 0)

        # 先打开设备
        for io_port, io_config in climate_config.items():
            if isinstance(io_config, dict):
                commands = io_config.get("commands", {})
                if "on" in commands:
                    on_cmd = commands["on"]
                    await self._async_send_single_command(
                        agt,
                        me,
                        io_port,
                        on_cmd.get("type", CMD_TYPE_ON),
                        on_cmd.get("val", 1),
                    )
                    break
        else:
            # 默认使用P1口打开
            await self._async_send_single_command(agt, me, "P1", CMD_TYPE_ON, 1)

        # 查找HVAC模式控制IO口
        for io_port, io_config in climate_config.items():
            if isinstance(io_config, dict):
                description = io_config.get("description", "").lower()
                commands = io_config.get("commands", {})

                # 优先使用commands配置
                if "set_mode" in commands:
                    mode_cmd = commands["set_mode"]
                    # 将HVACMode转换为值
                    mode_val = {
                        HVACMode.AUTO: 1,
                        HVACMode.FAN_ONLY: 2,
                        HVACMode.COOL: 3,
                        HVACMode.HEAT: 4,
                        HVACMode.DRY: 5,
                    }.get(hvac_mode, 1)

                    return await self._async_send_single_command(
                        agt,
                        me,
                        io_port,
                        mode_cmd.get("type", CMD_TYPE_SET_CONFIG),
                        mode_val,
                    )

                # 旧的逻辑:通过描述判断
                elif (
                    "hvac" in description
                    or "mode" in description
                    or "模式" in description
                ):
                    return await self._async_send_single_command(
                        agt, me, io_port, CMD_TYPE_SET_CONFIG, hvac_mode.value
                    )

        _LOGGER.warning("设备类型 %s 不支持HVAC模式设置", device_type)
        return -1

    async def async_set_climate_temperature(
        self, agt: str, me: str, device: dict, temp: float
    ) -> int:
        """设置温控设备的目标温度。"""
        temp_val = int(temp * 10)
        device_type = get_device_effective_type(device)

        # 获取设备映射配置
        device_mapping = mapping_engine.resolve_device_mapping_from_data(device)
        climate_config = device_mapping.get("climate", {})

        # 查找温度设置IO口
        for io_port, io_config in climate_config.items():
            if isinstance(io_config, dict):
                description = io_config.get("description", "").lower()
                commands = io_config.get("commands", {})

                # 优先使用commands配置
                if "set_temperature" in commands:
                    temp_cmd = commands["set_temperature"]
                    return await self._async_send_single_command(
                        agt,
                        me,
                        io_port,
                        temp_cmd.get("type", CMD_TYPE_SET_VAL),
                        temp_val,
                    )

                # 旧的逻辑:通过描述判断
                elif "temp" in description or "温度" in description:
                    # 根据IO配置选择合适的命令类型
                    conversion = io_config.get("conversion", "")
                    if "decimal" in conversion:
                        cmd_type = CMD_TYPE_SET_TEMP_DECIMAL
                    elif "raw" in conversion:
                        cmd_type = CMD_TYPE_SET_RAW_ON
                    else:
                        cmd_type = CMD_TYPE_SET_VAL

                    return await self._async_send_single_command(
                        agt, me, io_port, cmd_type, temp_val
                    )

        _LOGGER.warning("设备类型 %s 不支持温度设置", device_type)
        return -1

    async def async_set_climate_fan_mode(
        self, agt: str, me: str, device: dict, fan_mode: str, current_val: int = 0
    ) -> int:
        """设置温控设备的风扇模式。"""
        device_type = get_device_effective_type(device)

        # 获取设备映射配置
        device_mapping = mapping_engine.resolve_device_mapping_from_data(device)
        climate_config = device_mapping.get("climate", {})

        # 查找风扇模式控制IO口
        for io_port, io_config in climate_config.items():
            # 检查IO口是否在实际设备数据中存在
            if io_port not in device.get("data", {}):
                continue

            if isinstance(io_config, dict):
                description = io_config.get("description", "").lower()
                commands = io_config.get("commands", {})

                # 优先使用commands配置
                if "set_fan_speed" in commands:
                    fan_cmd = commands["set_fan_speed"]
                    # 将fan_mode转换为值（根据V_AIR_P设备的配置）
                    fan_val = {"low": 15, "medium": 45, "high": 75}.get(fan_mode, 15)

                    return await self._async_send_single_command(
                        agt,
                        me,
                        io_port,
                        fan_cmd.get("type", CMD_TYPE_SET_CONFIG),
                        fan_val,
                    )

                # 旧的逻辑:通过描述判断
                elif "fan" in description or "风" in description:
                    # 根据配置选择合适的命令类型
                    conversion = io_config.get("conversion", "")
                    if "raw" in conversion:
                        cmd_type = CMD_TYPE_SET_RAW_ON
                    elif "config" in conversion:
                        cmd_type = CMD_TYPE_SET_CONFIG
                    else:
                        cmd_type = CMD_TYPE_SET_VAL

                    return await self._async_send_single_command(
                        agt, me, io_port, cmd_type, fan_mode
                    )

        _LOGGER.warning("设备类型 %s 不支持风扇模式设置", device_type)
        return -1
