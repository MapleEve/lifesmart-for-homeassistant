"""
统一的Bitmask→Platform映射配置
由 @MapleEve 创建，用于VirtualDeviceStrategy

提供所有bitmask类型的配置驱动映射定义，支持：
- ALM (Alarm bitmask): 门锁报警位掩码
- EVTLO (Event Lock): 门锁事件数据
- config_bitmask: 通用配置位掩码

核心原则：
- O(1)性能设计：预构建查找表
- 配置驱动：消除硬编码逻辑
- 可扩展性：新bitmask类型只需添加配置
"""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.components.lock import LockDeviceClass

# ALM bitmask配置
# 基于原有ALM_BIT_CONFIG，提供完整的10个bit定义
ALM_BITMASK_CONFIG = {
    "io_port_pattern": r"^ALM$",
    "platform_priority": ["binary_sensor"],
    "detection_logic": "pattern_match",
    "virtual_device_template": "{io_port}_bit{bit_position}",
    "bit_definitions": {
        0: {
            "name": "error_alarm",
            "description": "错误报警",
            "device_class": BinarySensorDeviceClass.PROBLEM,
            "platform": "binary_sensor",
            "extraction_logic": "bit_extract",
            "friendly_name": "错误报警",
        },
        1: {
            "name": "hijack_alarm",
            "description": "劫持报警",
            "device_class": BinarySensorDeviceClass.SAFETY,
            "platform": "binary_sensor",
            "extraction_logic": "bit_extract",
            "friendly_name": "劫持报警",
        },
        2: {
            "name": "tamper_alarm",
            "description": "防撬报警",
            "device_class": BinarySensorDeviceClass.TAMPER,
            "platform": "binary_sensor",
            "extraction_logic": "bit_extract",
            "friendly_name": "防撬报警",
        },
        3: {
            "name": "key_alarm",
            "description": "机械钥匙报警",
            "device_class": BinarySensorDeviceClass.LOCK,
            "platform": "binary_sensor",
            "extraction_logic": "bit_extract",
            "friendly_name": "机械钥匙报警",
        },
        4: {
            "name": "low_battery",
            "description": "低电压报警",
            "device_class": BinarySensorDeviceClass.BATTERY,
            "platform": "binary_sensor",
            "extraction_logic": "bit_extract",
            "friendly_name": "低电量报警",
        },
        5: {
            "name": "motion_alarm",
            "description": "异动告警",
            "device_class": BinarySensorDeviceClass.MOTION,
            "platform": "binary_sensor",
            "extraction_logic": "bit_extract",
            "friendly_name": "异动告警",
        },
        6: {
            "name": "doorbell",
            "description": "门铃",
            "device_class": BinarySensorDeviceClass.SOUND,
            "platform": "binary_sensor",
            "extraction_logic": "bit_extract",
            "friendly_name": "门铃",
        },
        7: {
            "name": "fire_alarm",
            "description": "火警",
            "device_class": BinarySensorDeviceClass.SMOKE,
            "platform": "binary_sensor",
            "extraction_logic": "bit_extract",
            "friendly_name": "火警",
        },
        8: {
            "name": "intrusion_alarm",
            "description": "入侵告警",
            "device_class": BinarySensorDeviceClass.SAFETY,
            "platform": "binary_sensor",
            "extraction_logic": "bit_extract",
            "friendly_name": "入侵告警",
        },
        11: {
            "name": "factory_reset",
            "description": "恢复出厂告警",
            "device_class": BinarySensorDeviceClass.PROBLEM,
            "platform": "binary_sensor",
            "extraction_logic": "bit_extract",
            "friendly_name": "恢复出厂告警",
        },
    },
}

# EVTLO bitmask配置
# 基于原有EVTLO_DATA_CONFIG，支持多平台虚拟设备
EVTLO_BITMASK_CONFIG = {
    "io_port_pattern": r"^EVTLO$",
    "platform_priority": ["lock", "sensor", "binary_sensor"],
    "detection_logic": "pattern_match",
    "virtual_device_template": "{io_port}_{data_key}",
    "data_definitions": {
        "lock_status": {
            "name": "门锁状态",
            "description": "门锁开关状态",
            "platform": "lock",
            "extraction_logic": "type_bit_0",
            "extraction_params": {},
            "friendly_name": "门锁",
        },
        "user_id": {
            "name": "用户编号",
            "description": "开锁用户编号",
            "platform": "sensor",
            "extraction_logic": "bit_range",
            "extraction_params": {"start_bit": 0, "end_bit": 11},
            "friendly_name": "用户编号",
        },
        "unlock_method": {
            "name": "开锁方式",
            "description": "开锁方式",
            "platform": "sensor",
            "extraction_logic": "bit_range_mapped",
            "extraction_params": {
                "start_bit": 12,
                "end_bit": 15,
                "mapping": {
                    # 从原有UNLOCK_METHOD导入
                    1: "密码",
                    2: "指纹",
                    3: "卡片",
                    4: "钥匙",
                    5: "手机",
                    6: "组合开锁",
                    7: "其他",
                },
            },
            "friendly_name": "开锁方式",
        },
        "dual_unlock": {
            "name": "双开模式",
            "description": "是否为双开模式",
            "platform": "binary_sensor",
            "device_class": BinarySensorDeviceClass.LOCK,
            "extraction_logic": "dual_unlock_detection",
            "extraction_params": {},
            "friendly_name": "双开模式",
        },
    },
}

# config_bitmask配置
# 用于处理通用的配置位掩码，主要映射到sensor平台
CONFIG_BITMASK_CONFIG = {
    "io_port_pattern": r".*",  # 通用模式，需要进一步检测data_type
    "platform_priority": ["sensor"],
    "detection_logic": "data_type_check",
    "virtual_device_template": "{io_port}_config",
    "data_definitions": {
        "config_value": {
            "name": "配置值",
            "description": "设备配置信息",
            "platform": "sensor",
            "extraction_logic": "val_direct",
            "extraction_params": {},
            "friendly_name": "配置",
        }
    },
}

# 统一的device_class→platform映射表 (O(1)查找)
# 提供HA设备类别到平台的直接映射，消除文字匹配
DEVICE_CLASS_PLATFORM_MAPPING = {
    # binary_sensor类型映射
    BinarySensorDeviceClass.PROBLEM: "binary_sensor",
    BinarySensorDeviceClass.SAFETY: "binary_sensor",
    BinarySensorDeviceClass.TAMPER: "binary_sensor",
    BinarySensorDeviceClass.LOCK: "binary_sensor",
    BinarySensorDeviceClass.BATTERY: "binary_sensor",
    BinarySensorDeviceClass.MOTION: "binary_sensor",
    BinarySensorDeviceClass.SOUND: "binary_sensor",
    BinarySensorDeviceClass.SMOKE: "binary_sensor",
    BinarySensorDeviceClass.DOOR: "binary_sensor",
    BinarySensorDeviceClass.WINDOW: "binary_sensor",
    BinarySensorDeviceClass.OPENING: "binary_sensor",
    BinarySensorDeviceClass.MOVING: "binary_sensor",
    BinarySensorDeviceClass.VIBRATION: "binary_sensor",
    # sensor类型映射
    SensorDeviceClass.TEMPERATURE: "sensor",
    SensorDeviceClass.HUMIDITY: "sensor",
    SensorDeviceClass.BATTERY: "sensor",
    SensorDeviceClass.POWER: "sensor",
    SensorDeviceClass.ENERGY: "sensor",
    SensorDeviceClass.VOLTAGE: "sensor",
    SensorDeviceClass.CURRENT: "sensor",
    SensorDeviceClass.PM25: "sensor",
    SensorDeviceClass.PM10: "sensor",
    SensorDeviceClass.CO2: "sensor",
    SensorDeviceClass.CO: "sensor",
    SensorDeviceClass.ILLUMINANCE: "sensor",
    SensorDeviceClass.MOISTURE: "sensor",
    SensorDeviceClass.GAS: "sensor",
    SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS: "sensor",
    SensorDeviceClass.SOUND_PRESSURE: "sensor",
    SensorDeviceClass.POWER_FACTOR: "sensor",
    SensorDeviceClass.FREQUENCY: "sensor",
    # 其他特殊类型
    None: "sensor",  # 默认映射到sensor
}

# 所有bitmask配置的统一注册表
# 用于BitmaskPlatformMappingRegistry初始化
BITMASK_CONFIGS = {
    "ALM": ALM_BITMASK_CONFIG,
    "EVTLO": EVTLO_BITMASK_CONFIG,
    "config_bitmask": CONFIG_BITMASK_CONFIG,
}

# 支持的所有bitmask类型列表
ALL_BITMASK_TYPES = list(BITMASK_CONFIGS.keys())

# 性能统计常量
PERFORMANCE_TARGETS = {
    "device_class_lookup_time_us": 1.0,  # <1微秒
    "io_port_detection_time_us": 5.0,  # <5微秒
    "virtual_device_cache_hit_time_ms": 0.1,  # <0.1毫秒
}
