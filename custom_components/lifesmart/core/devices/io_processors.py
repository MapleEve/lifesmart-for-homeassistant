"""
LifeSmart 复杂IO状态处理器

此模块专门处理需要复杂业务逻辑的IO状态转换，包括：
- 位运算状态判断 (type&1)
- 多字段组合状态
- 动态分类设备
- 复杂状态转换处理

主要功能:
- 复杂状态转换函数
- 压缩版内联函数
- 动态分类处理器
- 业务逻辑处理器
"""

from typing import Any, Dict, Optional, Union

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfEnergy, UnitOfPower

# 导入常量
from ..const import (
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_SET_VAL,
    CMD_TYPE_SET_CONFIG,
    CMD_TYPE_SET_RAW_ON,
    CMD_TYPE_SET_RAW_OFF,
)


# ================= 复杂IO状态转换器 (Complex IO State Converters) =================


def bit_state_converter(bit_position: int = 0) -> Dict[str, Any]:
    """位状态转换器 - 处理 type&1 等位运算"""
    return {
        "conversion_type": "bit_operation",
        "bit_position": bit_position,
        "operation": f"type & {1 << bit_position}",
        "state_logic": f"type_bit_{bit_position}",
        "description": f"基于type字段第{bit_position}位判断状态",
    }


def val_threshold_converter(
    threshold: Union[int, float] = 0, operator: str = "gt"
) -> Dict[str, Any]:
    """值阈值转换器 - 处理 val != 0 或自定义阈值"""
    operators = {
        "gt": "greater_than",
        "lt": "less_than",
        "eq": "equals",
        "ne": "not_equals",
        "gte": "greater_than_or_equals",
        "lte": "less_than_or_equals",
    }

    return {
        "conversion_type": "value_threshold",
        "threshold": threshold,
        "operator": operator,
        "state_logic": f"val_{operators.get(operator, 'greater_than')}_{threshold}",
        "description": f"基于val值{operators.get(operator, 'greater_than')} {threshold}判断状态",
    }


def complex_lock_event_converter() -> Dict[str, Any]:
    """复杂门锁事件转换器"""
    return {
        "conversion_type": "lock_event",
        "state_logic": "lock_event_analysis",
        "description": "解析门锁开锁事件，包含用户ID和开锁方式",
        "parse_fields": ["unlock_type", "user_id", "unlock_method"],
        "business_logic": "parse_lock_event",
    }


def bitwise_alarm_converter(alarm_bits: Dict[int, str] = None) -> Dict[str, Any]:
    """位运算告警转换器 - 处理多位告警状态"""
    if alarm_bits is None:
        alarm_bits = {
            0: "错误报警",
            1: "劫持报警",
            2: "防撬报警",
            3: "机械钥匙报警",
            4: "低电压报警",
            5: "异动告警",
            6: "门铃",
            7: "火警",
            8: "入侵告警",
            11: "恢复出厂告警",
        }

    return {
        "conversion_type": "bitwise_alarm",
        "state_logic": "alarm_bit_analysis",
        "alarm_bits": alarm_bits,
        "description": "解析多位告警状态",
    }


def ieee754_float_converter() -> Dict[str, Any]:
    """IEEE754浮点数转换器"""
    return {
        "conversion_type": "ieee754_float",
        "state_logic": "float_conversion",
        "description": "IEEE754浮点数转换",
    }


# ================= 压缩版内联函数 (Optimized Inline Functions) =================


def io_config_compact(
    desc: str,
    rw: str,
    data_type: str,
    conversion: str,
    detail_desc: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """通用IO配置生成器 - 最小化重复代码"""
    config = {
        "description": desc,
        "rw": rw,
        "data_type": data_type,
        "conversion": conversion,
    }

    if detail_desc:
        config["detailed_description"] = detail_desc

    # 添加额外配置
    config.update(kwargs)
    return config


def switch_io_compact(
    port: str,
    desc: str = "开关",
    conversion: str = "type_bit_0",
    detail_desc: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """压缩版开关IO生成器"""
    if detail_desc is None:
        detail_desc = (
            "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)"
        )

    return {
        port: io_config_compact(
            desc,
            "RW",
            "binary_switch",
            conversion,
            detail_desc,
            commands={
                "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
            },
            **bit_state_converter(0),
        )
    }


def light_io_compact(
    port: str, desc: str = "灯光", conversion: str = "val_direct"
) -> Dict[str, Dict[str, Any]]:
    """压缩版灯光IO生成器"""
    return {
        port: io_config_compact(
            desc,
            "RW",
            "rgbw_light",
            conversion,
            "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示颜色值",
            commands={
                "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                "set_color_on": {
                    "type": CMD_TYPE_SET_RAW_ON,
                    "description": "开灯并设置颜色",
                },
                "set_color_off": {
                    "type": CMD_TYPE_SET_RAW_OFF,
                    "description": "关灯并设置颜色",
                },
            },
            **bit_state_converter(0),
        )
    }


def sensor_io_compact(
    port: str,
    desc: str,
    data_type: str,
    conversion: str = "friendly_val",
    unit: Optional[str] = None,
    device_class: Optional[SensorDeviceClass] = None,
    state_class: Optional[SensorStateClass] = None,
) -> Dict[str, Dict[str, Any]]:
    """压缩版传感器IO生成器"""
    config = io_config_compact(desc, "R", data_type, conversion)

    if unit:
        config["unit_of_measurement"] = unit
    if device_class:
        config["device_class"] = device_class
    if state_class:
        config["state_class"] = state_class

    return {port: config}


def binary_sensor_io_compact(
    port: str,
    desc: str,
    conversion_type: str = "type_bit_0",
    detail_desc: Optional[str] = None,
    device_class: Optional[BinarySensorDeviceClass] = None,
) -> Dict[str, Dict[str, Any]]:
    """压缩版二进制传感器IO生成器"""
    config = io_config_compact(desc, "R", "binary_sensor", conversion_type, detail_desc)

    if device_class:
        config["device_class"] = device_class

    # 根据转换类型添加对应的转换器
    if conversion_type == "type_bit_0":
        config.update(bit_state_converter(0))
    elif conversion_type.startswith("val_"):
        # 解析val类型转换参数
        if "not_equals_0" in conversion_type:
            config.update(val_threshold_converter(0, "ne"))
        elif "equals_0" in conversion_type:
            config.update(val_threshold_converter(0, "eq"))
        else:
            config.update(val_threshold_converter(0))

    return {port: config}


# ================= 复杂IO状态处理器 (Complex IO State Handlers) =================


def lock_event_ios_complex() -> Dict[str, Dict[str, Any]]:
    """门锁事件复杂IO处理器"""
    return {
        "EVTLO": io_config_compact(
            "实时开锁",
            "R",
            "lock_event",
            "lock_event",
            "解析门锁实时开锁事件，包含用户ID和开锁方式",
            **complex_lock_event_converter(),
        ),
        "HISLK": io_config_compact(
            "最近开锁",
            "R",
            "lock_event",
            "lock_event",
            "最近一次开锁信息",
            **complex_lock_event_converter(),
        ),
        "EVTOP": io_config_compact(
            "操作记录",
            "R",
            "lock_operation",
            "lock_operation",
            "门锁操作记录，包含记录类型和用户信息",
        ),
    }


def alarm_state_ios_complex() -> Dict[str, Dict[str, Any]]:
    """告警状态复杂IO处理器"""
    return {
        "ALM": io_config_compact(
            "告警信息",
            "R",
            "alarm_state",
            "bitwise_alarm",
            "多位告警状态：bit0错误报警，bit1劫持报警，bit2防撬报警等",
            **bitwise_alarm_converter(),
        )
    }


def door_sensor_ios_dynamic(device_type: str) -> Dict[str, Dict[str, Any]]:
    """门窗感应器动态IO处理器 - 根据设备类型动态生成"""
    if device_type in ["SL_SC_G", "SL_SC_BG"]:
        return binary_sensor_io_compact(
            "G",
            "门窗状态",
            "val_equals_0",
            "val=0表示打开，val=1表示关闭",
            BinarySensorDeviceClass.DOOR,
        )
    elif device_type == "SL_DF_GG":
        return binary_sensor_io_compact(
            "A",
            "门窗状态",
            "val_equals_0",
            "云防门窗：val=0表示打开，val=1表示关闭",
            BinarySensorDeviceClass.DOOR,
        )
    else:
        return binary_sensor_io_compact(
            "P1",
            "门窗状态",
            "type_bit_0",
            "type&1==1表示打开，type&1==0表示关闭",
            BinarySensorDeviceClass.DOOR,
        )


def motion_sensor_ios_dynamic(device_type: str) -> Dict[str, Dict[str, Any]]:
    """动态感应器动态IO处理器"""
    if device_type in ["SL_SC_MHW", "SL_SC_BM", "SL_SC_CM", "SL_BP_MZ"]:
        return binary_sensor_io_compact(
            "M",
            "动态检测",
            "val_not_equals_0",
            "val!=0表示检测到移动",
            BinarySensorDeviceClass.MOTION,
        )
    elif device_type == "SL_DF_MM":
        return binary_sensor_io_compact(
            "M",
            "动态检测",
            "type_bit_0",
            "type&1==1表示检测到移动",
            BinarySensorDeviceClass.MOTION,
        )
    else:
        return binary_sensor_io_compact(
            "P1",
            "动态检测",
            "val_not_equals_0",
            "val!=0表示检测到移动",
            BinarySensorDeviceClass.MOTION,
        )


def gas_sensor_ios_complex() -> Dict[str, Dict[str, Any]]:
    """气体感应器复杂IO处理器"""
    return {
        "P1": io_config_compact(
            "气体浓度",
            "R",
            "gas_concentration",
            "friendly_val",
            "type&1==1表示超过告警门限，val为浓度值",
            alarm_state="type_bit_0",
            device_class=SensorDeviceClass.GAS,
            **bit_state_converter(0),
        ),
        "P2": io_config_compact(
            "告警门限",
            "RW",
            "gas_threshold",
            "val_direct",
            "设置气体浓度告警门限",
            commands={
                "set_threshold": {"type": CMD_TYPE_SET_VAL, "description": "设置门限值"}
            },
        ),
        "P3": io_config_compact(
            "警报音",
            "RW",
            "alarm_sound",
            "type_bit_0",
            "type&1==1表示报警音响起",
            commands={
                "on": {"type": CMD_TYPE_ON, "val": 1, "description": "触发报警音"},
                "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "消除报警音"},
            },
            **bit_state_converter(0),
        ),
    }


def energy_monitoring_ios_complex() -> Dict[str, Dict[str, Any]]:
    """能耗监测复杂IO处理器"""
    return {
        "P2": io_config_compact(
            "用电量",
            "R",
            "energy",
            "ieee754_float",
            "累计用电量，IEEE754浮点数格式",
            device_class=SensorDeviceClass.ENERGY,
            unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
            state_class=SensorStateClass.TOTAL_INCREASING,
            **ieee754_float_converter(),
        ),
        "P3": io_config_compact(
            "功率",
            "R",
            "power",
            "ieee754_float",
            "当前负载功率，IEEE754浮点数格式",
            device_class=SensorDeviceClass.POWER,
            unit_of_measurement=UnitOfPower.WATT,
            state_class=SensorStateClass.MEASUREMENT,
            **ieee754_float_converter(),
        ),
        "P4": io_config_compact(
            "功率门限",
            "RW",
            "power_threshold",
            "val_direct",
            "功率门限设置，超出门限断电保护",
            commands={
                "enable": {"type": CMD_TYPE_ON, "val": 1, "description": "使能"},
                "disable": {"type": CMD_TYPE_OFF, "val": 0, "description": "不使能"},
                "set_threshold_enable": {
                    "type": CMD_TYPE_SET_VAL,
                    "description": "使能并设置门限",
                },
                "set_threshold_disable": {
                    "type": CMD_TYPE_SET_CONFIG,
                    "description": "不使能并设置门限",
                },
            },
        ),
    }


# ================= 业务逻辑处理器 (Business Logic Processors) =================


def parse_lock_event_state(sub_data: Dict[str, Any]) -> bool:
    """解析门锁事件 - 业务逻辑"""
    val = sub_data.get("val", 0)
    unlock_type = sub_data.get("type", 0)
    unlock_user = val & 0xFFF

    return val != 0 and unlock_type & 0x01 == 1 and unlock_user != 0 and val >> 12 != 15


def parse_door_sensor_state(
    device_type: str, sub_key: str, sub_data: Dict[str, Any]
) -> bool:
    """解析门窗感应器 - 业务逻辑"""
    val = sub_data.get("val", 0)
    type_val = sub_data.get("type", 0)

    if device_type in {"SL_SC_G", "SL_SC_BG", "SL_SC_GS"}:
        if device_type == "SL_SC_GS" and sub_key in {"P1", "P2"}:
            return type_val & 1 == 1
        if device_type == "SL_SC_BG" and sub_key == "AXS":
            return val != 0
        return val == 0 if sub_key == "G" else val != 0

    if device_type == "SL_DF_GG" and sub_key == "A":
        return val == 0  # 云防门窗：0=开，1=关

    return type_val & 1 == 1


def parse_motion_sensor_state(device_type: str, sub_data: Dict[str, Any]) -> bool:
    """解析动态感应器 - 业务逻辑"""
    val = sub_data.get("val", 0)

    if device_type in {"SL_SC_MHW", "SL_SC_BM", "SL_SC_CM", "SL_BP_MZ"}:
        return val != 0

    if device_type == "SL_DF_MM":
        type_val = sub_data.get("type", 0)
        return type_val & 1 == 1

    return False


def parse_gas_alarm_state(sub_data: Dict[str, Any]) -> bool:
    """解析气体告警状态 - 业务逻辑"""
    type_val = sub_data.get("type", 0)
    return type_val & 1 == 1


def parse_alarm_bits_state(
    val: int, alarm_mapping: Dict[int, str] = None
) -> Dict[str, bool]:
    """解析多位告警状态 - 业务逻辑"""
    if alarm_mapping is None:
        alarm_mapping = {
            0: "error_alarm",
            1: "hijack_alarm",
            2: "tamper_alarm",
            3: "mechanical_key_alarm",
            4: "low_battery_alarm",
            5: "motion_alarm",
            6: "doorbell",
            7: "fire_alarm",
            8: "intrusion_alarm",
            11: "factory_reset_alarm",
        }

    result = {}
    for bit, alarm_name in alarm_mapping.items():
        result[alarm_name] = bool(val & (1 << bit))

    return result


# ================= 动态分类设备处理器 (Dynamic Classification Handlers) =================


def nature_panel_classification() -> Dict[str, Any]:
    """超能面板动态分类处理器"""
    return {
        "dynamic_classification": {
            "type": "conditional",
            "condition_field": "P5",
            "condition_expression": "val & 0xFF",
            "modes": {
                "1": {"platforms": {"switch": {"ios": ["P1", "P2", "P3"]}}},  # 开关面板
                "3|6": {  # 温控面板
                    "platforms": {"climate": {"ios": ["P1"]}, "sensor": {"ios": ["P4"]}}
                },
            },
        }
    }


def general_controller_classification() -> Dict[str, Any]:
    """通用控制器动态分类处理器"""
    return {
        "dynamic_classification": {
            "type": "bitwise",
            "condition_field": "P1",
            "condition_expression": "(val >> 24) & 0xe",
            "modes": {
                "0": {  # 自由模式
                    "platforms": {
                        "switch": {"ios": ["P2", "P3", "P4"]},
                        "binary_sensor": {"ios": ["P5", "P6", "P7"]},
                    }
                },
                "2|4|6": {  # 窗帘模式
                    "platforms": {"cover": {"ios": ["P2", "P3", "P4"]}}
                },
                "8|10": {  # 开关模式
                    "platforms": {"switch": {"ios": ["P2", "P3", "P4"]}}
                },
            },
        }
    }


# ================= 版本化设备处理器 (Versioned Device Handlers) =================


def versioned_device_config(
    base_config: Dict[str, Any], version_configs: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """版本化设备配置生成器"""
    return {
        "versioned": {
            **{ver: config for ver, config in version_configs.items()},
            "default": base_config,
        }
    }


# ================= 高级IO配置生成器 (Advanced IO Config Generators) =================


def multi_sensor_device_compact(
    name: str, sensor_configs: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """压缩版多传感器设备配置生成器"""
    return {"name": name, "sensor": sensor_configs}


def multi_platform_device_compact(
    name: str, platform_configs: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """压缩版多平台设备配置生成器"""
    config = {"name": name}
    config.update(platform_configs)
    return config


def conditional_io_config(
    condition: str, true_config: Dict[str, Any], false_config: Dict[str, Any] = None
) -> Dict[str, Any]:
    """条件IO配置生成器"""
    return {
        "conditional": {
            "condition": condition,
            "true_config": true_config,
            "false_config": false_config or {},
        }
    }
