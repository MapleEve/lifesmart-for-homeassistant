"""
LifeSmart O(1)配置驱动IO处理器 - 零硬编码纯新架构
由 @MapleEve 初始创建和维护

此模块实现完全基于配置驱动的IO处理架构：
- 零硬编码的设备类型判断
- 配置驱动的属性生成器系统
- O(1)复杂度的统一处理接口
- 基于processor_type的直接映射

核心架构原则：
- 所有逻辑通过配置驱动，不依赖硬编码判断
- 属性生成器注册表实现O(1)分配
- 统一的处理接口，零特殊case处理
"""

import datetime
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from .logic_processors import process_io_data, get_processor_registry
from ...const import (
    UNLOCK_METHOD,
)

_LOGGER = logging.getLogger(__name__)


# ================= 配置驱动属性生成器 =================


class AttributeGenerator(ABC):
    """属性生成器基类 - 配置驱动架构"""

    @abstractmethod
    def generate_attributes(
        self, io_config: dict[str, Any], raw_data: dict[str, Any], current_state: Any
    ) -> dict[str, Any]:
        """生成IO口属性"""
        pass

    @abstractmethod
    def get_generator_type(self) -> str:
        """获取生成器类型标识"""
        pass


class DefaultAttributeGenerator(AttributeGenerator):
    """默认属性生成器 - 返回原始数据"""

    def generate_attributes(
        self, io_config: dict[str, Any], raw_data: dict[str, Any], current_state: Any
    ) -> dict[str, Any]:
        """生成默认属性"""
        return dict(raw_data)

    def get_generator_type(self) -> str:
        return "default"


class DoorLockAttributeGenerator(AttributeGenerator):
    """门锁属性生成器 - 配置驱动"""

    def generate_attributes(
        self, io_config: dict[str, Any], raw_data: dict[str, Any], current_state: Any
    ) -> dict[str, Any]:
        """生成门锁事件属性"""
        val = raw_data.get("val", 0)

        # 从配置获取属性字段映射
        attr_config = io_config.get("attribute_config", {})

        return {
            attr_config.get(
                "unlocking_method_field", "unlocking_method"
            ): UNLOCK_METHOD.get(val >> 12, "Unknown"),
            attr_config.get("unlocking_user_field", "unlocking_user"): val & 0xFFF,
            attr_config.get("device_type_field", "device_type"): io_config.get(
                "device_type", "unknown"
            ),
            attr_config.get(
                "unlocking_success_field", "unlocking_success"
            ): current_state,
            attr_config.get(
                "last_updated_field", "last_updated"
            ): datetime.datetime.fromtimestamp(
                raw_data.get("valts", 0) / 1000
            ).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        }

    def get_generator_type(self) -> str:
        return "door_lock_attributes"


class DoorLockAlarmAttributeGenerator(AttributeGenerator):
    """门锁报警属性生成器"""

    def generate_attributes(
        self, io_config: dict[str, Any], raw_data: dict[str, Any], current_state: Any
    ) -> dict[str, Any]:
        """生成门锁报警属性"""
        val = raw_data.get("val", 0)
        attr_config = io_config.get("attribute_config", {})

        return {attr_config.get("alarm_type_field", "alarm_type"): val}

    def get_generator_type(self) -> str:
        return "door_lock_alarm_attributes"


class WaterSensorAttributeGenerator(AttributeGenerator):
    """水浸传感器属性生成器"""

    def generate_attributes(
        self, io_config: dict[str, Any], raw_data: dict[str, Any], current_state: Any
    ) -> dict[str, Any]:
        """生成水浸传感器属性"""
        val = raw_data.get("val", 0)
        attr_config = io_config.get("attribute_config", {})

        return {
            attr_config.get("conductivity_level_field", "conductivity_level"): val,
            attr_config.get("water_detected_field", "water_detected"): val != 0,
        }

    def get_generator_type(self) -> str:
        return "water_sensor_attributes"


class BitmaskAlarmAttributeGenerator(AttributeGenerator):
    """位运算告警属性生成器"""

    def generate_attributes(
        self, io_config: dict[str, Any], raw_data: dict[str, Any], current_state: Any
    ) -> dict[str, Any]:
        """生成位运算告警属性"""
        val = raw_data.get("val", 0)
        attr_config = io_config.get("attribute_config", {})

        # 可配置的位字段映射
        bit_mapping = attr_config.get(
            "bit_mapping",
            {
                "high_temp_protection": 0b1,
                "low_temp_protection": 0b10,
                "internal_sensor_fault": 0b100,
                "external_sensor_fault": 0b1000,
                "low_battery": 0b10000,
                "device_offline": 0b100000,
            },
        )

        attributes = {}
        for attr_name, bit_mask in bit_mapping.items():
            attributes[attr_name] = bool(val & bit_mask)

        return attributes

    def get_generator_type(self) -> str:
        return "bitmask_alarm_attributes"


# ================= 属性生成器注册表 =================


class AttributeGeneratorRegistry:
    """O(1)属性生成器注册表"""

    def __init__(self):
        self._generators: dict[str, AttributeGenerator] = {}
        self._register_all_generators()

    def _register_all_generators(self):
        """预注册所有属性生成器"""
        generators = [
            DefaultAttributeGenerator(),
            DoorLockAttributeGenerator(),
            DoorLockAlarmAttributeGenerator(),
            WaterSensorAttributeGenerator(),
            BitmaskAlarmAttributeGenerator(),
        ]

        for generator in generators:
            generator_type = generator.get_generator_type()
            self._generators[generator_type] = generator
            _LOGGER.debug(f"Registered O(1) attribute generator: {generator_type}")

    def get_generator(self, generator_type: str) -> Optional[AttributeGenerator]:
        """O(1)属性生成器获取"""
        return self._generators.get(generator_type)

    def list_generators(self) -> dict[str, AttributeGenerator]:
        """获取所有已注册的生成器"""
        return dict(self._generators)


# ================= O(1)统一处理接口 =================

# 全局注册表实例
_attribute_registry = AttributeGeneratorRegistry()


def process_io_value(io_config: dict[str, Any], raw_data: dict[str, Any]) -> Any:
    """
    O(1)IO数值处理统一接口

    Args:
        io_config: IO口配置，包含processor_type字段
        raw_data: 原始数据

    Returns:
        处理后的值
    """
    return process_io_data(io_config, raw_data)


def process_io_attributes(
    io_config: dict[str, Any], raw_data: dict[str, Any], current_state: Any
) -> dict[str, Any]:
    """
    O(1)IO属性处理统一接口 - 完全配置驱动，零硬编码

    Args:
        io_config: IO口配置，包含attribute_generator字段
        raw_data: 原始数据
        current_state: 当前状态值

    Returns:
        生成的属性字典
    """
    # 操作1: 获取属性生成器类型
    generator_type = io_config.get("attribute_generator", "default")

    # 操作2: O(1)获取属性生成器
    generator = _attribute_registry.get_generator(generator_type)
    if not generator:
        _LOGGER.warning(f"Unknown attribute generator: {generator_type}, using default")
        generator = _attribute_registry.get_generator("default")

    # 操作3: 生成属性
    try:
        attributes = generator.generate_attributes(io_config, raw_data, current_state)
        _LOGGER.debug(f"O(1) generated attributes with {generator_type}")
        return attributes

    except Exception as e:
        _LOGGER.error(f"Error in O(1) attribute generator {generator_type}: {e}")
        return dict(raw_data)


def process_light_state(
    io_config: dict[str, Any], raw_data: dict[str, Any]
) -> dict[str, Any]:
    """
    O(1)灯光状态处理统一接口 - 配置驱动实现

    Args:
        io_config: IO口配置
        raw_data: 原始数据

    Returns:
        包含灯光所有状态信息的字典
    """
    # 开关状态处理
    switch_config = io_config.copy()
    switch_config["processor_type"] = io_config.get(
        "switch_processor", "type_bit_0_switch"
    )
    is_on = process_io_data(switch_config, raw_data)

    result = {
        "is_on": is_on,
        "brightness": None,
        "rgb_color": None,
        "rgbw_color": None,
        "color_temp": None,
        "effect": None,
    }

    # 亮度处理 - 配置驱动
    if io_config.get("has_brightness", True):
        brightness_config = io_config.copy()
        brightness_config["processor_type"] = io_config.get(
            "brightness_processor", "direct_value"
        )
        brightness = process_io_data(brightness_config, raw_data)
        result["brightness"] = brightness if is_on else 0

    # 颜色处理 - 配置驱动
    if io_config.get("has_color", False):
        color_config = io_config.copy()
        color_config["processor_type"] = io_config.get("color_processor", "rgbw_color")
        color_result = process_io_data(color_config, raw_data)

        if isinstance(color_result, dict):
            result["rgb_color"] = color_result.get("rgb")
            result["rgbw_color"] = color_result.get("rgbw")
            if color_result.get("is_dynamic"):
                result["effect"] = io_config.get("dynamic_effect_name", "dynamic")

    # 色温处理 - 配置驱动
    if io_config.get("has_color_temp", False):
        temp_config = io_config.copy()
        temp_config["processor_type"] = io_config.get("temp_processor", "direct_value")
        result["color_temp"] = process_io_data(temp_config, raw_data)

    return result


def get_friendly_value(io_config: dict[str, Any], raw_data: dict[str, Any]) -> Any:
    """
    O(1)获取友好值统一接口 - 与process_io_value等效
    """
    return process_io_value(io_config, raw_data)


def classify_device_mode(
    device_config: dict[str, Any], device_data: dict[str, Any]
) -> str:
    """
    O(1)设备模式分类接口 - 配置驱动实现

    Args:
        device_config: 设备配置，包含分类规则
        device_data: 设备数据

    Returns:
        设备模式字符串
    """
    if not device_config.get("dynamic", False):
        return "static"

    # 配置驱动的分类逻辑
    classification_config = device_config.get("classification", {})
    classification_type = classification_config.get("type", "unknown")

    if classification_type == "conditional":
        return _classify_conditional_device(classification_config, device_data)
    elif classification_type == "bitwise":
        return _classify_bitwise_device(classification_config, device_data)

    return "unknown"


def _classify_conditional_device(
    config: dict[str, Any], device_data: dict[str, Any]
) -> str:
    """条件分类设备 - 配置驱动"""
    condition_field = config.get("condition_field")
    conditions = config.get("conditions", {})

    if not condition_field or condition_field not in device_data:
        return "unknown"

    field_data = device_data[condition_field]
    val = field_data.get("val", 0)

    # 遍历条件配置
    for mode, condition_config in conditions.items():
        condition_type = condition_config.get("type")
        condition_value = condition_config.get("value")

        if condition_type == "equal" and val == condition_value:
            return mode
        elif (
            condition_type == "in_range"
            and isinstance(condition_value, list)
            and val in condition_value
        ):
            return mode
        elif (
            condition_type == "bitwise_and"
            and (val & condition_value) == condition_value
        ):
            return mode

    return config.get("default_mode", "unknown")


def _classify_bitwise_device(
    config: dict[str, Any], device_data: dict[str, Any]
) -> str:
    """位操作分类设备 - 配置驱动"""
    source_field = config.get("source_field")
    bit_patterns = config.get("bit_patterns", {})

    if not source_field or source_field not in device_data:
        return "unknown"

    field_data = device_data[source_field]
    bit_value = field_data.get("val", 0)

    # 遍历位模式
    for mode, pattern_config in bit_patterns.items():
        bit_mask = pattern_config.get("mask", 0)
        expected_value = pattern_config.get("value", 0)

        if (bit_value & bit_mask) == expected_value:
            return mode

    return config.get("default_mode", "unknown")


class EnhancedIOProcessor:
    """增强的IO状态处理器 - O(1)纯新架构实现"""

    def __init__(self):
        """初始化处理器 - 使用全局注册表"""
        self._processor_registry = get_processor_registry()
        self._attribute_registry = _attribute_registry

    def process_io_value(
        self, io_config: dict[str, Any], raw_data: dict[str, Any]
    ) -> Any:
        """处理IO口数据值 - O(1)实现"""
        return process_io_value(io_config, raw_data)

    def get_enhanced_value(
        self, io_config: dict[str, Any], raw_data: dict[str, Any]
    ) -> Any:
        """获取增强转换值 - O(1)实现"""
        return process_io_value(io_config, raw_data)


def get_attribute_generator_registry() -> AttributeGeneratorRegistry:
    """获取属性生成器注册表实例"""
    return _attribute_registry


# 创建全局实例
enhanced_io_processor = EnhancedIOProcessor()


# ================= 导出接口 =================

__all__ = [
    # O(1)统一接口
    "process_io_value",
    "process_io_attributes",
    "process_light_state",
    "get_friendly_value",
    "classify_device_mode",
    # 增强处理器类
    "EnhancedIOProcessor",
    "enhanced_io_processor",
    # 属性生成器系统
    "get_attribute_generator_registry",
    "AttributeGenerator",
    "AttributeGeneratorRegistry",
]
