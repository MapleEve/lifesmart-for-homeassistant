"""
LifeSmart O(1)直接映射处理器 - 零硬编码纯新架构

此模块实现真正的O(1)复杂度IO处理架构：
- 零字符串匹配的直接处理器映射
- 预注册的处理器注册表实现O(1)查找
- 纯计算逻辑，移除所有can_handle判断逻辑
- 配置驱动的处理器分配机制

核心性能目标：
- 每次IO处理 ≤ 4次操作
- O(1)复杂度处理器分配
- 零硬编码设备逻辑
"""

import logging
import struct
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

_LOGGER = logging.getLogger(__name__)


class DirectProcessor(ABC):
    """直接处理器基类 - 零字符串匹配架构"""

    @abstractmethod
    def process_value(self, raw_value: Any, type_value: int = 0) -> Any:
        """处理原始值并返回处理后的值 - 纯计算逻辑"""
        pass

    @abstractmethod
    def get_processor_type(self) -> str:
        """获取处理器类型标识"""
        pass


# ================= 基础数据处理器 =================


class TypeBit0Processor(DirectProcessor):
    """type&1开关逻辑处理器 - O(1)实现"""

    def process_value(self, raw_value: Any, type_value: int = 0) -> bool:
        """解析开关状态: type&1==1 表示开启"""
        return bool(type_value & 1)

    def get_processor_type(self) -> str:
        return "type_bit_0_switch"


class RGBWProcessor(DirectProcessor):
    """RGBW颜色处理器 - O(1)实现"""

    def process_value(self, raw_value: Any, type_value: int = 0) -> Dict[str, Any]:
        """解析RGBW位值"""
        val = int(raw_value) if raw_value else 0
        return {
            "blue": val & 0xFF,  # bit0-7
            "green": (val >> 8) & 0xFF,  # bit8-15
            "red": (val >> 16) & 0xFF,  # bit16-23
            "white": (val >> 24) & 0xFF,  # bit24-31
            "is_dynamic": (val >> 24) & 0xFF > 0,
            "brightness": (
                max(val & 0xFF, (val >> 8) & 0xFF, (val >> 16) & 0xFF)
                if (val >> 24) & 0xFF == 0
                else 255
            ),
            "state": bool(type_value & 1),
        }

    def get_processor_type(self) -> str:
        return "rgbw_color"


class HVACModeProcessor(DirectProcessor):
    """HVAC模式处理器 - O(1)实现"""

    # 静态模式映射表
    _MODE_MAPPING = {
        1: "auto",
        2: "fan_only",
        3: "cool",
        4: "heat",
        5: "dry",
        6: "heat",
        7: "heat",
        8: "heat_cool",
    }

    def process_value(self, raw_value: Any, type_value: int = 0) -> str:
        """解析HVAC模式值"""
        val = int(raw_value) if raw_value else 1
        return self._MODE_MAPPING.get(val, "auto")

    def get_processor_type(self) -> str:
        return "hvac_mode"


class TemperatureProcessor(DirectProcessor):
    """温度值处理器 - O(1)实现"""

    def process_value(self, raw_value: Any, type_value: int = 0) -> float:
        """处理温度值 - 支持结构化和直接值"""
        if raw_value is None:
            return 0.0

        # 处理结构化温度数据
        if isinstance(raw_value, dict):
            temp_raw = raw_value.get("v", raw_value.get("val", 0))
        else:
            temp_raw = raw_value

        temp_raw = int(temp_raw) if temp_raw else 0
        return float(temp_raw) / 10.0  # 默认除以10处理

    def get_processor_type(self) -> str:
        return "temperature"


class DirectValueProcessor(DirectProcessor):
    """直接值处理器 - O(1)实现"""

    def process_value(self, raw_value: Any, type_value: int = 0) -> Any:
        """直接返回val或v字段的值"""
        if isinstance(raw_value, dict):
            return (
                raw_value.get("v")
                if raw_value.get("v") is not None
                else raw_value.get("val", 0)
            )
        return raw_value

    def get_processor_type(self) -> str:
        return "direct_value"


class IEEE754FloatProcessor(DirectProcessor):
    """IEEE754浮点数处理器 - O(1)实现"""

    def process_value(self, raw_value: Any, type_value: int = 0) -> float:
        """处理IEEE754浮点数转换"""
        try:
            return struct.unpack("!f", struct.pack("!i", int(raw_value)))[0]
        except (ValueError, struct.error):
            return 0.0

    def get_processor_type(self) -> str:
        return "ieee754_float"


# ================= 专用业务逻辑处理器 =================


class LockEventProcessor(DirectProcessor):
    """门锁事件处理器 - O(1)实现"""

    def process_value(self, raw_value: Any, type_value: int = 0) -> bool:
        """处理门锁事件逻辑"""
        val = int(raw_value) if raw_value else 0
        unlock_user = val & 0xFFF
        return (
            val != 0 and type_value & 0x01 == 1 and unlock_user != 0 and val >> 12 != 15
        )

    def get_processor_type(self) -> str:
        return "lock_event"


class DoorWindowSensorProcessor(DirectProcessor):
    """门窗感应器处理器 - O(1)实现"""

    def process_value(self, raw_value: Any, type_value: int = 0) -> bool:
        """处理门窗感应器逻辑"""
        val = int(raw_value) if raw_value else 0
        return val == 0  # 门窗传感器的G口逻辑

    def get_processor_type(self) -> str:
        return "door_window_sensor"


class MotionSensorProcessor(DirectProcessor):
    """动态感应器处理器 - O(1)实现"""

    def process_value(self, raw_value: Any, type_value: int = 0) -> bool:
        """处理动态感应器逻辑"""
        val = int(raw_value) if raw_value else 0
        return val != 0

    def get_processor_type(self) -> str:
        return "motion_sensor"


class SecurityAlarmProcessor(DirectProcessor):
    """安防报警处理器 - O(1)实现"""

    def process_value(self, raw_value: Any, type_value: int = 0) -> bool:
        """处理安防报警逻辑"""
        val = int(raw_value) if raw_value else 0
        return val > 0

    def get_processor_type(self) -> str:
        return "security_alarm"


class WaterLeakSensorProcessor(DirectProcessor):
    """水浸传感器处理器 - O(1)实现"""

    def process_value(self, raw_value: Any, type_value: int = 0) -> bool:
        """处理水浸传感器逻辑"""
        val = int(raw_value) if raw_value else 0
        return val != 0

    def get_processor_type(self) -> str:
        return "water_leak_sensor"


class BitmaskAlarmProcessor(DirectProcessor):
    """位运算告警处理器 - O(1)实现"""

    def process_value(self, raw_value: Any, type_value: int = 0) -> Dict[str, bool]:
        """处理位运算告警"""
        val = int(raw_value) if raw_value else 0
        return {
            "high_temp_protection": bool(val & 0b1),
            "low_temp_protection": bool(val & 0b10),
            "internal_sensor_fault": bool(val & 0b100),
            "external_sensor_fault": bool(val & 0b1000),
            "low_battery": bool(val & 0b10000),
            "device_offline": bool(val & 0b100000),
            "alarm_active": val > 0,
        }

    def get_processor_type(self) -> str:
        return "bitmask_alarm"


class BitmaskConfigProcessor(DirectProcessor):
    """位掩码配置处理器 - O(1)实现"""

    def process_value(self, raw_value: Any, type_value: int = 0) -> Dict[str, Any]:
        """解析位掩码配置"""
        val = int(raw_value) if raw_value else 0
        config = {}

        # 解析每4位对应一个按键的配置（P1-P6）
        for i in range(6):
            bit_value = (val >> (i * 4)) & 0xF
            port_name = f"P{i + 1}"

            if bit_value == 0:
                config[port_name] = {"mode": "auto_reset", "delay": 5}
            elif 1 <= bit_value <= 3:
                config[port_name] = {"mode": "relay", "relay_id": f"L{bit_value}"}
            elif 4 <= bit_value <= 14:
                delay = 5 + (bit_value - 3) * 15
                config[port_name] = {"mode": "auto_reset", "delay": delay}
            elif bit_value == 15:
                config[port_name] = {"mode": "general_switch", "delay": 0}

        return config

    def get_processor_type(self) -> str:
        return "bitmask_config"


class CoverPositionProcessor(DirectProcessor):
    """窗帘位置处理器 - O(1)实现"""

    def process_value(self, raw_value: Any, type_value: int = 0) -> Dict[str, Any]:
        """处理窗帘位置和移动状态"""
        val = int(raw_value) if raw_value else 0

        # 解析val值的位信息
        position = val & 0x7F  # 低7位为位置（0-100）
        is_opening_direction = (val & 0x80) == 0  # 最高位为方向（0=开，1=关）
        is_moving = bool(type_value & 1)  # type最低位表示是否移动

        return {
            "position": position,
            "is_moving": is_moving,
            "is_opening": is_moving and is_opening_direction,
            "is_closing": is_moving and not is_opening_direction,
        }

    def get_processor_type(self) -> str:
        return "cover_position"


class CoverDirectionProcessor(DirectProcessor):
    """窗帘方向处理器 - O(1)实现"""

    def process_value(self, raw_value: Any, type_value: int = 0) -> bool:
        """处理窗帘移动方向"""
        val = int(raw_value) if raw_value else 0
        # val的最高位表示方向：0=开启方向，1=关闭方向
        return (val & 0x80) == 0

    def get_processor_type(self) -> str:
        return "cover_direction"


# ================= O(1)处理器注册表 =================


class ProcessorRegistry:
    """O(1)处理器注册表 - 零查找延迟"""

    def __init__(self):
        self._processors: Dict[str, DirectProcessor] = {}
        self._register_all_processors()

    def _register_all_processors(self):
        """预注册所有处理器 - 初始化时完成"""
        processors = [
            # 基础处理器
            TypeBit0Processor(),
            RGBWProcessor(),
            HVACModeProcessor(),
            TemperatureProcessor(),
            DirectValueProcessor(),
            IEEE754FloatProcessor(),
            # 专用业务逻辑处理器
            LockEventProcessor(),
            DoorWindowSensorProcessor(),
            MotionSensorProcessor(),
            SecurityAlarmProcessor(),
            WaterLeakSensorProcessor(),
            BitmaskAlarmProcessor(),
            BitmaskConfigProcessor(),
            # 窗帘/覆盖物处理器
            CoverPositionProcessor(),
            CoverDirectionProcessor(),
        ]

        for processor in processors:
            processor_type = processor.get_processor_type()
            self._processors[processor_type] = processor
            _LOGGER.debug(f"Registered O(1) processor: {processor_type}")

    def get_processor(self, processor_type: str) -> Optional[DirectProcessor]:
        """O(1)处理器获取 - 单次字典查找"""
        return self._processors.get(processor_type)

    def list_processors(self) -> Dict[str, DirectProcessor]:
        """获取所有已注册的处理器"""
        return dict(self._processors)


# ================= O(1)统一处理接口 =================

# 全局处理器注册表实例
_processor_registry = ProcessorRegistry()


def process_io_data(io_config: Dict[str, Any], raw_data: Dict[str, Any]) -> Any:
    """
    O(1)IO数据处理统一接口

    性能保证：≤ 4次操作完成处理
    - 1次: 获取processor_type
    - 1次: 字典查找获取processor
    - 1次: 调用process_value
    - 1次: 获取raw_value

    Args:
        io_config: IO口配置，必须包含processor_type字段
        raw_data: 原始数据，包含val和type字段

    Returns:
        处理后的值
    """
    # 操作1: 获取处理器类型
    processor_type = io_config.get("processor_type")
    if not processor_type:
        # 降级到直接值处理
        return raw_data.get("val")

    # 操作2: O(1)获取处理器
    processor = _processor_registry.get_processor(processor_type)
    if not processor:
        _LOGGER.warning(f"Unknown processor type: {processor_type}")
        return raw_data.get("val")

    # 操作3&4: 获取数据并处理
    try:
        raw_value = raw_data.get("val")
        type_value = raw_data.get("type", 0)
        result = processor.process_value(raw_value, type_value)

        _LOGGER.debug(f"O(1) processed with {processor_type}: {raw_value} -> {result}")
        return result

    except Exception as e:
        _LOGGER.error(f"Error in O(1) processor {processor_type}: {e}")
        return raw_data.get("val")


def get_processor_registry() -> ProcessorRegistry:
    """获取处理器注册表实例"""
    return _processor_registry


# ================= 导出接口 =================

__all__ = [
    # 核心处理接口
    "process_io_data",
    "get_processor_registry",
    # 处理器基类
    "DirectProcessor",
    # 处理器注册表
    "ProcessorRegistry",
]
