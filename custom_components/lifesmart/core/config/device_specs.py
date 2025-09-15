"""
LifeSmart 设备规格纯数据层 - (125 个设备)
由 @MapleEve 初始创建和维护

此文件包含所有设备的规格数据，已转换为纯Python数据结构。
所有HA常量已清理为纯字符串格式，实现数据层的完全独立。

设备按照官方文档 "LifeSmart 智慧设备规格属性说明.md" 的章节顺序排列：
2.1 插座系列 → 2.2 开关系列 → 2.3 窗帘控制 → 2.4 灯光系列 → ... → 2.14 超能面板
"""

from typing import Dict, Any

from custom_components.lifesmart.core.const import (
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_SET_VAL,
    CMD_TYPE_SET_TEMP_DECIMAL,
    CMD_TYPE_SET_CONFIG,
    CMD_TYPE_SET_INDICATOR_BRIGHTNESS,
    CMD_TYPE_SET_RAW_OFF,
    CMD_TYPE_SET_RAW_ON,
)

# 总设备数量
TOTAL_DEVICES = 125

# ================= 设备映射按官方文档顺序排列 =================
# (Device Mapping in Official Documentation Order)
# 🚨 严格按照官方文档 "LifeSmart 智慧设备规格属性说明.md" 的章节顺序排列
# 🚨 2.1 插座系列 → 2.2 开关系列 → 2.3 窗帘控制 → 2.4 灯光系列 → ... → 2.14 超能面板

_RAW_DEVICE_DATA = {
    # ================= 2.1 插座系列 (Outlet Series) =================
    # 2.1.1 传统插座系列 (Traditional Outlet Series)
    "SL_OL": {
        "name": "智慧插座",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_OL",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "O": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_OL_3C": {
        "name": "智慧插座",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_OL_3C",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "O": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_OL_DE": {
        "name": "德标插座",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_OL_DE",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "O": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_OL_UK": {
        "name": "英标插座",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_OL_UK",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "O": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_OL_UL": {
        "name": "美标插座",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_OL_UL",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "O": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
        },
    },
    "OD_WE_OT1": {
        "name": "Wi-Fi插座",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "OD_WE_OT1",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "P1": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
        },
    },
    # 2.1.2 计量插座系列 (Energy Monitoring Outlet Series)
    "SL_OE_3C": {
        "name": "计量插座",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_OE_3C",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "P1": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "sensor": {
                "io_configs": {
                    "P2": {
                        "description": "energy",
                        "data_type": "energy",
                        "conversion": "ieee754_float",
                        "device_class": "energy",
                        "unit_of_measurement": "kWh",
                        "state_class": "total_increasing",
                    },
                    "P3": {
                        "description": "power",
                        "data_type": "power",
                        "conversion": "ieee754_float",
                        "device_class": "power",
                        "unit_of_measurement": "W",
                        "state_class": "measurement",
                    },
                },
            },
            "number": {
                "io_configs": {
                    "P4": {
                        "description": "power_threshold",
                        "data_type": "power",
                        "conversion": "val_direct",
                        "device_class": "power",
                        "unit_of_measurement": "W",
                        "min": 0,
                        "max": 3500,
                        "commands": {
                            "enable": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "disable": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "enable_and_set": {
                                "type": CMD_TYPE_SET_VAL,
                            },
                            "disable_and_set": {
                                "type": CMD_TYPE_SET_CONFIG,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_OE_DE": {
        "name": "计量插座德标",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_OE_DE",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "P1": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "sensor": {
                "io_configs": {
                    "P2": {
                        "description": "energy",
                        "data_type": "energy",
                        "conversion": "ieee754_float",
                        "device_class": "energy",
                        "unit_of_measurement": "kWh",
                        "state_class": "total_increasing",
                    },
                    "P3": {
                        "description": "power",
                        "data_type": "power",
                        "conversion": "ieee754_float",
                        "device_class": "power",
                        "unit_of_measurement": "W",
                        "state_class": "measurement",
                    },
                },
            },
            "number": {
                "io_configs": {
                    "P4": {
                        "description": "power_threshold",
                        "data_type": "power_threshold",
                        "conversion": "val_direct",
                        "commands": {
                            "enable": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "disable": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "enable_and_set": {
                                "type": CMD_TYPE_SET_VAL,
                            },
                            "disable_and_set": {
                                "type": CMD_TYPE_SET_CONFIG,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_OE_W": {
        "name": "计量插座",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_OE_W",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "P1": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "sensor": {
                "io_configs": {
                    "P2": {
                        "description": "energy",
                        "data_type": "energy",
                        "conversion": "ieee754_float",
                        "device_class": "energy",
                        "unit_of_measurement": "kWh",
                        "state_class": "total_increasing",
                    },
                    "P3": {
                        "description": "power",
                        "data_type": "power",
                        "conversion": "ieee754_float",
                        "device_class": "power",
                        "unit_of_measurement": "W",
                        "state_class": "measurement",
                    },
                },
            },
            "number": {
                "io_configs": {
                    "P4": {
                        "description": "power_threshold",
                        "data_type": "power_threshold",
                        "conversion": "val_direct",
                        "commands": {
                            "enable": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "disable": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "enable_and_set": {
                                "type": CMD_TYPE_SET_VAL,
                            },
                            "disable_and_set": {
                                "type": CMD_TYPE_SET_CONFIG,
                            },
                        },
                    },
                },
            },
        },
    },
    # ================= 2.2 开关系列 (Switch Series) =================
    # 2.2.1 随心开关系列 (Freestyle Switch Series)
    "SL_SW_RC1": {
        "name": "白玉/墨玉流光开关一键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SW_RC1",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "L1": {
                        "description": "switch_1",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "light": {
                "io_configs": {
                    "dark": {
                        "description": "indicator_brightness_off",
                        "data_type": "brightness_light",
                        "conversion": "val_direct",
                        "range": [0, 1023],
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright": {
                        "description": "indicator_brightness_on",
                        "data_type": "brightness_light",
                        "conversion": "val_direct",
                        "range": [0, 1023],
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_SW_RC2": {
        "name": "白玉/墨玉流光开关二键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SW_RC2",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "L1": {
                        "description": "switch_1",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "L2": {
                        "description": "switch_2",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "light": {
                "io_configs": {
                    "dark1": {
                        "description": "indicator_brightness_1_off",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "dark2": {
                        "description": "indicator_brightness_2_off",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright1": {
                        "description": "indicator_brightness_1_on",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright2": {
                        "description": "indicator_brightness_2_on",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_SW_RC3": {
        "name": "白玉/墨玉流光开关三键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SW_RC3",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "L1": {
                        "description": "switch_1",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "L2": {
                        "description": "switch_2",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "L3": {
                        "description": "switch_3",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "light": {
                "io_configs": {
                    "dark1": {
                        "description": "indicator_brightness_1_off",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "dark2": {
                        "description": "indicator_brightness_2_off",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "dark3": {
                        "description": "indicator_brightness_3_off",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright1": {
                        "description": "indicator_brightness_1_on",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright2": {
                        "description": "indicator_brightness_2_on",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright3": {
                        "description": "indicator_brightness_3_on",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                },
            },
        },
    },
    # 2.2.1 传统开关系列补充 (Traditional Switch Series Supplement)
    "SL_SF_RC": {
        "name": "单火触摸开关/入墙开关",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SF_RC",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "L1": {
                        "description": "switch_1",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "L2": {
                        "description": "switch_2",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "L3": {
                        "description": "switch_3",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "light": {
                "io_configs": {
                    "dark": {
                        "description": "indicator_brightness_off",
                        "data_type": "brightness_light",
                        "conversion": "val_direct",
                        "range": [0, 1023],
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright": {
                        "description": "indicator_brightness_on",
                        "data_type": "brightness_light",
                        "conversion": "val_direct",
                        "range": [0, 1023],
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_SW_RC": {
        "name": "触摸开关，极星开关(零火版)",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SW_RC",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "L1": {
                        "description": "switch_1",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "L2": {
                        "description": "switch_2",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "L3": {
                        "description": "switch_3",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "light": {
                "io_configs": {
                    "dark": {
                        "description": "indicator_brightness_off",
                        "data_type": "brightness_light",
                        "conversion": "val_direct",
                        "range": [0, 1023],
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright": {
                        "description": "indicator_brightness_on",
                        "data_type": "brightness_light",
                        "conversion": "val_direct",
                        "range": [0, 1023],
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_SW_IF3": {
        "name": "流光开关三键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SW_IF3",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "L1": {
                        "description": "switch_1",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "L2": {
                        "description": "switch_2",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "L3": {
                        "description": "switch_3",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "light": {
                "io_configs": {
                    "dark1": {
                        "description": "indicator_brightness_1_off",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "dark2": {
                        "description": "indicator_brightness_2_off",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "dark3": {
                        "description": "indicator_brightness_3_off",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright1": {
                        "description": "indicator_brightness_1_on",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright2": {
                        "description": "indicator_brightness_2_on",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright3": {
                        "description": "indicator_brightness_3_on",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_SF_IF3": {
        "name": "单火流光开关三键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SF_IF3",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "L1": {
                        "description": "switch_1",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "L2": {
                        "description": "switch_2",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "L3": {
                        "description": "switch_3",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "light": {
                "io_configs": {
                    "dark1": {
                        "description": "indicator_brightness_1_off",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "dark2": {
                        "description": "indicator_brightness_2_off",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "dark3": {
                        "description": "indicator_brightness_3_off",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright1": {
                        "description": "indicator_brightness_1_on",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright2": {
                        "description": "indicator_brightness_2_on",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright3": {
                        "description": "indicator_brightness_3_on",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_SW_CP3": {
        "name": "橙朴流光开关三键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SW_CP3",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "L1": {
                        "description": "switch_1",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "L2": {
                        "description": "switch_2",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "L3": {
                        "description": "switch_3",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "light": {
                "io_configs": {
                    "dark1": {
                        "description": "indicator_brightness_1_off",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "dark2": {
                        "description": "indicator_brightness_2_off",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "dark3": {
                        "description": "indicator_brightness_3_off",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright1": {
                        "description": "indicator_brightness_1_on",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright2": {
                        "description": "indicator_brightness_2_on",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright3": {
                        "description": "indicator_brightness_3_on",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_SW_IF2": {
        "name": "流光开关二键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SW_IF2",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "L1": {
                        "description": "switch_1",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "L2": {
                        "description": "switch_2",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "light": {
                "io_configs": {
                    "dark1": {
                        "description": "indicator_brightness_1_off",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "dark2": {
                        "description": "indicator_brightness_2_off",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright1": {
                        "description": "indicator_brightness_1_on",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright2": {
                        "description": "indicator_brightness_2_on",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_SF_IF2": {
        "name": "单火流光开关二键",
        "switch": {
            "L1": {
                "description": "switch_1",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
            "L2": {
                "description": "switch_2",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
        },
        "light": {
            "dark1": {
                "description": "indicator_brightness_1_off",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "dark2": {
                "description": "indicator_brightness_2_off",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "bright1": {
                "description": "indicator_brightness_1_on",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "bright2": {
                "description": "indicator_brightness_2_on",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
        },
    },
    "SL_SW_CP2": {
        "name": "橙朴开关二键",
        "switch": {
            "L1": {
                "description": "switch_1",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
            "L2": {
                "description": "switch_2",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
        },
        "light": {
            "dark1": {
                "description": "indicator_brightness_1_off",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "dark2": {
                "description": "indicator_brightness_2_off",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "bright1": {
                "description": "indicator_brightness_1_on",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "bright2": {
                "description": "indicator_brightness_2_on",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
        },
    },
    "SL_SW_FE2": {
        "name": "塞纳开关二键",
        "switch": {
            "L1": {
                "description": "switch_1",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
            "L2": {
                "description": "switch_2",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
        },
        "light": {
            "dark1": {
                "description": "indicator_brightness_1_off",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "dark2": {
                "description": "indicator_brightness_2_off",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "bright1": {
                "description": "indicator_brightness_1_on",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "bright2": {
                "description": "indicator_brightness_2_on",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
        },
    },
    "SL_SW_IF1": {
        "name": "零火流光开关单键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SW_IF1",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "L1": {
                        "description": "switch_1",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "light": {
                "io_configs": {
                    "dark": {
                        "description": "indicator_brightness_off",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright": {
                        "description": "indicator_brightness_on",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_SF_IF1": {
        "name": "单火流光开关单键",
        "switch": {
            "L1": {
                "description": "switch_1",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
        },
        "light": {
            "dark": {
                "description": "indicator_brightness_off",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "bright": {
                "description": "indicator_brightness_on",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
        },
    },
    "SL_SW_CP1": {
        "name": "橙朴开关单键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SW_CP1",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "L1": {
                        "description": "switch_1",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "light": {
                "io_configs": {
                    "dark": {
                        "description": "indicator_brightness_off",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright": {
                        "description": "indicator_brightness_on",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_SW_FE1": {
        "name": "塞纳开关单键",
        "switch": {
            "L1": {
                "description": "switch_1",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
        },
        "light": {
            "dark": {
                "description": "indicator_brightness_off",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "bright": {
                "description": "indicator_brightness_on",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
        },
    },
    "SL_OL_W": {
        "name": "智慧插座开关版",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_OL_W",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "L1": {
                        "description": "switch_1",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "light": {
                "io_configs": {
                    "dark": {
                        "description": "indicator_brightness_off",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright": {
                        "description": "indicator_brightness_on",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                },
            },
        },
    },
    # 2.2.2 恒星/辰星/极星开关系列 (Star Series Switch)
    "SL_SW_ND1": {
        "name": "恒星开关一键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SW_ND1",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "P1": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "sensor": {
                "io_configs": {
                    "P2": {
                        "description": "battery",
                        "data_type": "battery",
                        "conversion": "v_field",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                },
            },
        },
    },
    "SL_SW_ND2": {
        "name": "恒星开关二键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SW_ND2",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "P1": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P2": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "sensor": {
                "io_configs": {
                    "P3": {
                        "description": "battery",
                        "data_type": "battery",
                        "conversion": "v_field",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                },
            },
        },
    },
    "SL_SW_ND3": {
        "name": "恒星开关三键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SW_ND3",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "P1": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P2": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P3": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "sensor": {
                "io_configs": {
                    "P4": {
                        "description": "battery",
                        "data_type": "battery",
                        "conversion": "v_field",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                },
            },
        },
    },
    "SL_MC_ND1": {
        "name": "恒星/辰星开关伴侣一键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_MC_ND1",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "P1": {
                        "description": "switch_1",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "sensor": {
                "io_configs": {
                    "P2": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "v_field",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                },
            },
        },
    },
    "SL_MC_ND2": {
        "name": "恒星/辰星开关伴侣二键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_MC_ND2",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "P1": {
                        "description": "switch_1",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P2": {
                        "description": "switch_2",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "sensor": {
                "io_configs": {
                    "P3": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "v_field",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                },
            },
        },
    },
    "SL_MC_ND3": {
        "name": "恒星/辰星开关伴侣三键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_MC_ND3",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "P1": {
                        "description": "switch_1",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P2": {
                        "description": "switch_2",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P3": {
                        "description": "switch_3",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "sensor": {
                "io_configs": {
                    "P4": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "v_field",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                },
            },
        },
    },
    # 2.2.3 开关控制器系列 (Switch Controller Series)
    "SL_S": {
        "name": "单路开关控制器",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_S",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "P2": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_SPWM": {
        "name": "PWM调光开关控制器",
        "category": "light",
        "manufacturer": "lifesmart",
        "model": "SL_SPWM",
        "_generation": 2,
        "platforms": {
            "light": {
                "io_configs": {
                    "P1": {
                        "description": "dimmable_light",
                        "data_type": "brightness_light",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_brightness_on": {
                                "type": CMD_TYPE_SET_VAL,
                            },
                            "set_brightness_off": {
                                "type": CMD_TYPE_SET_CONFIG,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_P_SW": {
        "name": "九路开关控制器",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_P_SW",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "P1": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P2": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P3": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P4": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P5": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P6": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P7": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P8": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P9": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
        },
    },
    # 2.2.3.5 环境传感器 B1 系列 (Environmental Sensor B1 Series)
    "SL_SC_B1": {
        "name": "高级环境传感器",
        "category": "sensor",
        "manufacturer": "lifesmart",
        "model": "SL_SC_B1",
        "_generation": 2,
        "platforms": {
            "sensor": {
                "io_configs": {
                    "T": {
                        "description": "temperature",
                        "data_type": "temperature",
                        "conversion": "val_div_10",
                        "device_class": "temperature",
                        "unit_of_measurement": "°C",
                        "state_class": "measurement",
                    },
                    "H": {
                        "description": "humidity",
                        "data_type": "humidity",
                        "conversion": "v_field",
                        "device_class": "humidity",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                    "CO2": {
                        "description": "co2_concentration",
                        "data_type": "aqi",
                        "conversion": "v_field",
                        "device_class": "aqi",
                        "unit_of_measurement": "ppm",
                        "state_class": "measurement",
                    },
                    "TVOC": {
                        "description": "tvoc_concentration",
                        "data_type": "aqi",
                        "conversion": "val_div_100",
                        "unit_of_measurement": "mg/m³",
                        "state_class": "measurement",
                    },
                    "V": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "v_field",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                },
            },
        },
    },
    # 2.2.4 随心开关按钮系列 (Button Switch Series)
    "SL_SC_BB": {
        "name": "随心开关",
        "category": "button",
        "manufacturer": "lifesmart",
        "model": "SL_SC_BB",
        "_generation": 2,
        "platforms": {
            "button": {
                "io_configs": {
                    "B": {
                        "description": "button",
                        "data_type": "button_state",
                        "conversion": "val_direct",
                        "device_class": "identify",
                    },
                },
            },
            "sensor": {
                "io_configs": {
                    "V": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "v_field",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                },
            },
        },
    },
    # 2.2.5 调光开关系列 (Dimmer Switch Series)
    "SL_SW_DM1": {
        "versioned": True,
        "version_modes": {
            "V1": {
                "name": "动态调光开关",
                "light": {
                    "P1": {
                        "description": "switch",
                        "data_type": "brightness_light",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_brightness_on": {
                                "type": CMD_TYPE_SET_VAL,
                            },
                            "set_brightness_off": {
                                "type": CMD_TYPE_SET_CONFIG,
                            },
                        },
                    },
                    "P2": {
                        "description": "indicator",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_brightness": {
                                "type": CMD_TYPE_SET_INDICATOR_BRIGHTNESS,
                            },
                        },
                    },
                },
                "binary_sensor": {
                    "P3": {
                        "description": "motion",
                        "data_type": "motion_status",
                        "conversion": "val_direct",
                        "device_class": "motion",
                    },
                },
                "sensor": {
                    "P4": {
                        "description": "illuminance",
                        "data_type": "illuminance",
                        "conversion": "val_direct",
                        "device_class": "illuminance",
                        "unit_of_measurement": "lx",
                        "state_class": "measurement",
                    },
                    "P5": {
                        "description": "dimming_control",
                        "data_type": "dimming_config",
                        "conversion": "val_direct",
                        "commands": {
                            "set_config": {
                                "type": CMD_TYPE_SET_CONFIG,
                            },
                        },
                    },
                    "P6": {
                        "description": "dynamic_control",
                        "data_type": "dynamic_config",
                        "conversion": "val_direct",
                        "commands": {
                            "set_config": {
                                "type": CMD_TYPE_SET_CONFIG,
                            },
                        },
                    },
                },
            },
            "V2": {
                "name": "星玉调光开关(可控硅)",
                "light": {
                    "P1": {
                        "description": "switch",
                        "data_type": "brightness_light",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_brightness_on": {
                                "type": CMD_TYPE_SET_VAL,
                            },
                            "set_brightness_off": {
                                "type": CMD_TYPE_SET_CONFIG,
                            },
                        },
                    },
                    "P2": {
                        "description": "indicator_brightness",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_brightness": {
                                "type": CMD_TYPE_SET_VAL,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_LI_WW": {
        "versioned": True,
        "version_modes": {
            "V1": {
                "name": "智能灯泡(冷暖白)",
                "light": {
                    "P1": {
                        "description": "brightness",
                        "data_type": "brightness_light",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_brightness": {
                                "type": CMD_TYPE_SET_VAL,
                            },
                        },
                    },
                    "P2": {
                        "description": "color_temp",
                        "data_type": "color_temperature",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "commands": {
                            "set_color_temp": {
                                "type": CMD_TYPE_SET_VAL,
                            },
                        },
                    },
                },
            },
            "V2": {
                "name": "调光调色智控器(0-10V)",
                "light": {
                    "P1": {
                        "description": "brightness",
                        "data_type": "brightness_light",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_brightness": {
                                "type": CMD_TYPE_SET_VAL,
                            },
                        },
                    },
                    "P2": {
                        "description": "color_temp",
                        "data_type": "color_temperature",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "commands": {
                            "set_color_temp": {
                                "type": CMD_TYPE_SET_VAL,
                            },
                        },
                    },
                },
            },
        },
    },
    # 2.2.6 奇点开关模块系列 (Singularity Switch Module Series)
    "SL_SW_MJ1": {
        "name": "奇点开关模块一键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SW_MJ1",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "P1": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_SW_MJ2": {
        "name": "奇点开关模块二键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SW_MJ2",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "P1": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P2": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_SW_MJ3": {
        "name": "奇点开关模块三键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SW_MJ3",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "P1": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P2": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P3": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
        },
    },
    # 2.2.7 随心按键 (CUBE Clicker2)
    "SL_SC_BB_V2": {
        "name": "随心按键",
        "category": "button",
        "manufacturer": "lifesmart",
        "model": "SL_SC_BB_V2",
        "_generation": 2,
        "platforms": {
            "button": {
                "io_configs": {
                    "P1": {
                        "description": "button",
                        "data_type": "button_events",
                        "conversion": "val_direct",
                        "device_class": "identify",
                    },
                },
            },
            "sensor": {
                "io_configs": {
                    "P2": {
                        "description": "energy",
                        "data_type": "battery_level",
                        "conversion": "voltage_to_percentage",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                },
            },
        },
    },
    # 2.2.8 星玉开关系列 (Nature Switch Series)
    "SL_SW_NS1": {
        "name": "星玉开关一键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SW_NS1",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "L1": {
                        "description": "switch_1",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
            "light": {
                "io_configs": {
                    "dark": {
                        "description": "indicator_brightness_off",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "bright": {
                        "description": "indicator_brightness_on",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_SW_NS2": {
        "name": "星玉开关二键",
        "switch": {
            "L1": {
                "description": "switch_1",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
            "L2": {
                "description": "switch_2",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
        },
        "light": {
            "dark1": {
                "description": "indicator_brightness_1_off",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "dark2": {
                "description": "indicator_brightness_2_off",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "bright1": {
                "description": "indicator_brightness_1_on",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "bright2": {
                "description": "indicator_brightness_2_on",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
        },
    },
    "SL_SW_NS3": {
        "name": "星玉开关三键",
        "switch": {
            "L1": {
                "description": "switch_1",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
            "L2": {
                "description": "switch_2",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
            "L3": {
                "description": "switch_3",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
        },
        "light": {
            "dark1": {
                "description": "indicator_brightness_1_off",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "dark2": {
                "description": "indicator_brightness_2_off",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "dark3": {
                "description": "indicator_brightness_3_off",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "bright1": {
                "description": "indicator_brightness_1_on",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "bright2": {
                "description": "indicator_brightness_2_on",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "bright3": {
                "description": "indicator_brightness_3_on",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
        },
    },
    # 2.2.11 极星开关(120零火版) (BS Series)
    "SL_SW_BS1": {
        "name": "极星开关(120零火版)一键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SW_BS1",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "P1": {
                        "description": "switch_1",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_SW_BS2": {
        "name": "极星开关(120零火版)二键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SW_BS2",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "P1": {
                        "description": "switch_1",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P2": {
                        "description": "switch_2",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
        },
    },
    "SL_SW_BS3": {
        "name": "极星开关(120零火版)三键",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SW_BS3",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "P1": {
                        "description": "switch_1",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P2": {
                        "description": "switch_2",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P3": {
                        "description": "switch_3",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
        },
    },
    # 2.2.12 星玉调光开关（可控硅）Dimming Light Switch
    "SL_SW_WW": {
        "name": "星玉调光开关",
        "category": "light",
        "manufacturer": "lifesmart",
        "model": "SL_SW_WW",
        "_generation": 2,
        "platforms": {
            "light": {
                "io_configs": {
                    "P1": {
                        "description": "brightness",
                        "data_type": "brightness",
                        "conversion": "val_to_brightness",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_brightness": {
                                "type": CMD_TYPE_SET_VAL,
                            },
                        },
                    },
                    "P2": {
                        "description": "color_temp",
                        "data_type": "color_temp",
                        "conversion": "val_to_color_temp",
                        "commands": {
                            "set_color_temp": {
                                "type": CMD_TYPE_SET_VAL,
                            },
                        },
                    },
                },
            },
        },
    },
    # 2.2.14 星玉情景面板（Nature Switch Scene Panel)
    "SL_SW_NS6": {
        "name": "星玉情景面板",
        "switch": {
            "P1": {
                "description": "scene_switch_1",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
            "P2": {
                "description": "scene_switch_2",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
            "P3": {
                "description": "scene_switch_3",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
            "P4": {
                "description": "scene_switch_4",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
            "P5": {
                "description": "scene_switch_5",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
            "P6": {
                "description": "scene_switch_6",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
        },
        "sensor": {
            "P7": {
                "description": "turn_on_controller_config",
                "data_type": "scene_config",
                "conversion": "val_direct",
                "commands": {
                    "config": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                },
            },
        },
    },
    # ================= 2.3 窗帘控制系列 (Curtain Controller) =================
    # 2.3.1 窗帘控制开关
    "SL_SW_WIN": {
        "name": "窗帘控制开关",
        "category": "cover",
        "manufacturer": "lifesmart",
        "model": "SL_SW_WIN",
        "_generation": 2,  # DEVICE_CENTRIC_CONFIG格式标识
        # 基础平台配置
        "platforms": {
            "cover": {
                "io_configs": {
                    "OP": {
                        "description": "open_curtain",
                        "data_type": "cover_control",
                        "conversion": "type_bit_0",
                        "commands": {
                            "open": {
                                "type": "CMD_TYPE_ON",
                                "val": 1,
                            }
                        },
                    },
                    "CL": {
                        "description": "close_curtain",
                        "data_type": "cover_control",
                        "conversion": "type_bit_0",
                        "commands": {
                            "close": {
                                "type": "CMD_TYPE_ON",
                                "val": 1,
                            }
                        },
                    },
                    "ST": {
                        "description": "stop",
                        "data_type": "cover_control",
                        "conversion": "type_bit_0",
                        "commands": {
                            "stop": {
                                "type": "CMD_TYPE_ON",
                                "val": 1,
                            }
                        },
                    },
                }
            },
            "light": {
                "io_configs": {
                    "dark": {
                        "description": "turn_off_indicator_brightness",
                        "data_type": "brightness_light",
                        "conversion": "val_direct",
                        "range": "0~1023",
                        "commands": {
                            "on": {
                                "type": "CMD_TYPE_ON",
                                "val": 1,
                            },
                            "off": {
                                "type": "CMD_TYPE_OFF",
                                "val": 0,
                            },
                            "set_brightness_on": {
                                "type": "CMD_TYPE_SET_RAW_ON",
                            },
                            "set_brightness_off": {
                                "type": "CMD_TYPE_SET_RAW_OFF",
                            },
                        },
                    },
                    "bright": {
                        "description": "turn_on_indicator_brightness",
                        "data_type": "brightness_light",
                        "conversion": "val_direct",
                        "range": "0~1023",
                        "commands": {
                            "on": {
                                "type": "CMD_TYPE_ON",
                                "val": 1,
                            },
                            "off": {
                                "type": "CMD_TYPE_OFF",
                                "val": 0,
                            },
                            "set_brightness_on": {
                                "type": "CMD_TYPE_SET_RAW_ON",
                            },
                            "set_brightness_off": {
                                "type": "CMD_TYPE_SET_RAW_OFF",
                            },
                        },
                    },
                }
            },
        },
        # 核心：cover_config嵌入配置 - 明确位置反馈能力
        "cover_config": {
            "device_class": "curtain",
            "position_feedback": False,  # 明确表达：无位置反馈能力
            "control_type": "optimistic",  # 乐观控制模式
            "capabilities": ["open", "close", "stop"],
            # 控制行为配置
            "travel_time": 30,  # 预估运行时间（秒）
            "assume_closed_on_start": False,  # 启动时不假设状态
            # IO端口映射
            "io_mapping": {
                "open_io": "OP",  # 打开命令IO端口
                "close_io": "CL",  # 关闭命令IO端口
                "stop_io": "ST",  # 停止命令IO端口
            },
            # 命令配置
            "commands": {
                "open": {
                    "io_port": "OP",
                    "command_type": "CMD_TYPE_ON",
                    "value": 1,
                },
                "close": {
                    "io_port": "CL",
                    "command_type": "CMD_TYPE_ON",
                    "value": 1,
                },
                "stop": {
                    "io_port": "ST",
                    "command_type": "CMD_TYPE_ON",
                    "value": 1,
                },
            },
        },
        # 设备能力标识
        "capabilities": [
            "cover_control",  # 窗帘控制能力
            "basic_positioning",  # 基础定位（开/关/停）
            "no_position_feedback",  # 明确标识：无位置反馈
        ],
        # Home Assistant实体配置
        "entity_config": {
            "unique_id_template": "lifesmart_{device_id}_cover",
            "name_template": "{device_name} 窗帘",
            "icon": "mdi:curtains",
            "device_class": "curtain",
        },
        # 翻译键支持
        "translation_keys": {
            "cover_open": "打开窗帘",
            "cover_close": "关闭窗帘",
            "cover_stop": "停止窗帘",
            "cover_state_opening": "正在打开",
            "cover_state_closing": "正在关闭",
            "cover_state_stopped": "已停止",
        },
        # 设备特定行为配置
        "behavior_config": {
            "state_tracking": "optimistic",  # 乐观状态跟踪
            "command_delay": 0.5,  # 命令间延迟（秒）
            "state_timeout": 30,  # 状态超时（秒）
            "auto_assume_state": False,  # 不自动假设状态
        },
    },
    "SL_CN_IF": {
        "name": "流光窗帘控制器",
        "category": "cover",
        "manufacturer": "lifesmart",
        "model": "SL_CN_IF",
        "_generation": 2,  # DEVICE_CENTRIC_CONFIG格式标识
        # 集成的窗帘控制配置（原NON_POSITIONAL_COVER_CONFIG）
        "cover_features": {
            "position_feedback": False,  # 无位置反馈
            "optimistic_mode": True,  # 乐观判断状态
            "control_mapping": {"open": "P1", "close": "P2", "stop": "P3"},
        },
        # 基础平台配置
        "platforms": {
            "cover": {
                "io_configs": {
                    "P1": {
                        "description": "open_curtain",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                        },
                    },
                    "P2": {
                        "description": "close_curtain",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                        },
                    },
                    "P3": {
                        "description": "stop",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                        },
                    },
                }
            },
            "light": {
                "io_configs": {
                    "P4": {
                        "description": "open_panel_indicator_color",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "P5": {
                        "description": "stop_indicator_color",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                    "P6": {
                        "description": "close_panel_indicator_color",
                        "data_type": "single_io_rgbw_light",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_color_on": {
                                "type": CMD_TYPE_SET_RAW_ON,
                            },
                            "set_color_off": {
                                "type": CMD_TYPE_SET_RAW_OFF,
                            },
                        },
                    },
                }
            },
        },
    },
    "SL_CN_FE": {
        "name": "塞纳三键窗帘",
        "category": "cover",
        "manufacturer": "lifesmart",
        "model": "SL_CN_FE",
        "_generation": 2,  # DEVICE_CENTRIC_CONFIG格式标识
        # 集成的窗帘控制配置（原NON_POSITIONAL_COVER_CONFIG）
        "cover_features": {
            "position_feedback": False,  # 无位置反馈
            "optimistic_mode": True,  # 乐观判断状态
            "control_mapping": {"open": "P1", "close": "P3", "stop": "P2"},
        },
        # 基础平台配置
        "platforms": {
            "cover": {
                "io_configs": {
                    "P1": {
                        "description": "open_curtain",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                        },
                    },
                    "P2": {
                        "description": "stop",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                        },
                    },
                    "P3": {
                        "description": "close_curtain",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                        },
                    },
                }
            },
        },
    },
    # 2.3.2 DOOYA窗帘电机
    "SL_DOOYA": {
        "name": "DOOYA窗帘电机",
        "cover": {
            "P1": {
                "description": "curtain",
                "data_type": "position_status",
                "conversion": "val_direct",
            },
            "P2": {
                "description": "curtain",
                "data_type": "position_control",
                "conversion": "val_direct",
                "commands": {
                    "open": {
                        "type": CMD_TYPE_SET_VAL,
                        "val": 100,
                    },
                    "close": {
                        "type": CMD_TYPE_SET_VAL,
                        "val": 0,
                    },
                    "stop": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "val": 128,
                    },
                    "set_position": {
                        "type": CMD_TYPE_SET_VAL,
                    },
                },
            },
        },
    },
    "SL_P_V2": {
        "name": "智界窗帘电机智控器",
        "category": "cover",
        "manufacturer": "lifesmart",
        "model": "SL_P_V2",
        "_generation": 2,  # DEVICE_CENTRIC_CONFIG格式标识
        # 集成的窗帘控制配置（原NON_POSITIONAL_COVER_CONFIG）
        "cover_features": {
            "position_feedback": False,  # 无位置反馈
            "optimistic_mode": True,  # 乐观判断状态
            "control_mapping": {"open": "P2", "close": "P3", "stop": "P4"},
        },
        # 基础平台配置
        "platforms": {
            "cover": {
                "io_configs": {
                    "P2": {
                        "description": "open_curtain",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                        },
                    },
                    "P3": {
                        "description": "close_curtain",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                        },
                    },
                    "P4": {
                        "description": "stop",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                        },
                    },
                }
            },
            "sensor": {
                "io_configs": {
                    "P8": {
                        "description": "electric",
                        "data_type": "voltage",
                        "conversion": "friendly_val",
                        "device_class": "voltage",
                        "state_class": "measurement",
                    },
                }
            },
        },
    },
    # ================= 2.4 灯光系列 (Light Series) =================
    # 2.4.1 灯光系列 (RGBW/RGB Light Series)
    "SL_CT_RGBW": {
        "name": "RGBW灯带",
        "light": {
            "RGBW": {
                "description": "color",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "DYN": {
                "description": "color",
                "data_type": "dynamic_effect",
                "conversion": "val_direct",
                "commands": {
                    "enable": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "disable": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_effect_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_effect_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
        },
    },
    "SL_LI_RGBW": {
        "name": "RGBW灯泡",
        "light": {
            "RGBW": {
                "description": "color",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "DYN": {
                "description": "color",
                "data_type": "dynamic_effect",
                "conversion": "val_direct",
                "commands": {
                    "enable": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "disable": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_effect_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_effect_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
        },
    },
    "SL_SC_RGB": {
        "name": "RGB灯带无白光",
        "light": {
            "RGB": {
                "description": "color",
                "data_type": "rgb_light",
                "conversion": "val_direct",
                "range": "0x00000000-0xFFFFFFFF",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
        },
    },
    # 2.4.2 量子灯 (Quantum Light)
    "OD_WE_QUAN": {
        "name": "量子灯",
        "light": {
            "P1": {
                "description": "brightness",
                "data_type": "brightness_light",
                "conversion": "val_direct",
                "range": "0-100",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                    },
                },
            },
            "P2": {
                "description": "color",
                "data_type": "quantum_light",
                "conversion": "val_direct",
                "range": "0x00000000-0xFFFFFFFF",
                "commands": {
                    "set_color": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                },
            },
        },
    },
    # 2.4.4 门廊壁灯 (Porch Wall Lamp)
    "SL_LI_GD1": {
        "name": "门廊壁灯",
        "light": {
            "P1": {
                "description": "switch",
                "data_type": "brightness_light",
                "conversion": "val_direct",
                "range": "0-255",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                    },
                },
            },
        },
        "binary_sensor": {
            "P2": {
                "description": "motion",
                "data_type": "motion_status",
                "conversion": "val_direct",
                "device_class": "motion",
            },
        },
        "sensor": {
            "P3": {
                "description": "illuminance",
                "data_type": "illuminance",
                "conversion": "v_field",
                "device_class": "illuminance",
                "unit_of_measurement": "lux",
                "state_class": "measurement",
            },
        },
    },
    # 2.4.5 花园地灯 (Garden Landscape Light)
    "SL_LI_UG1": {
        "name": "花园地灯",
        "light": {
            "P1": {
                "description": "turn_on_switch",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "range": "0x00000000-0xFFFFFFFF",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
        },
        "sensor": {
            "P2": {
                "description": "illuminance",
                "data_type": "illuminance",
                "conversion": "v_field",
                "device_class": "illuminance",
                "unit_of_measurement": "lux",
                "state_class": "measurement",
            },
            "P3": {
                "description": "electric",
                "data_type": "charging_status",
                "conversion": "val_direct",
                "device_class": "battery",
                "unit_of_measurement": "V",
                "state_class": "measurement",
            },
            "P4": {
                "description": "energy",
                "data_type": "battery",
                "conversion": "v_field",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    # 2.5 超级碗 (SPOT Series)
    "MSL_IRCTL": {
        "name": "超级碗RGB灯",
        "light": {
            "RGBW": {
                "description": "color",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "DYN": {
                "description": "color",
                "data_type": "dynamic_effect",
                "conversion": "val_direct",
                "commands": {
                    "enable": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "disable": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_effect_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_effect_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
        },
    },
    "OD_WE_IRCTL": {
        "name": "超级碗RGB灯(OD)",
        "light": {
            "RGB": {
                "description": "color",
                "data_type": "rgb_light",
                "conversion": "val_direct",
                "range": "0x00000000-0xFFFFFFFF",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
        },
    },
    "SL_SPOT": {
        "name": "超级碗RGB灯",
        "light": {
            "RGB": {
                "description": "color",
                "data_type": "rgb_light",
                "conversion": "val_direct",
                "range": "0x00000000-0xFFFFFFFF",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
        },
    },
    "SL_LI_IR": {
        "name": "红外吸顶灯",
        "light": {
            "P1": {
                "description": "brightness",
                "data_type": "brightness_light",
                "conversion": "val_direct",
                "range": "0-255",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                    },
                },
            },
            "P2": {
                "description": "color_temp",
                "data_type": "color_temperature",
                "conversion": "val_direct",
                "range": "0-255",
                "commands": {
                    "set_color_temp": {
                        "type": CMD_TYPE_SET_VAL,
                    },
                },
            },
            "P3": {
                "description": "brightness",
                "data_type": "nightlight_brightness",
                "conversion": "val_direct",
                "range": "0,63,127,195,255",
                "commands": {
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                    },
                },
            },
        },
    },
    "SL_P_IR": {
        "name": "红外模块",
        "light": {
            "P1": {
                "description": "brightness",
                "data_type": "brightness_light",
                "conversion": "val_direct",
                "range": "0-255",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                    },
                },
            },
            "P2": {
                "description": "color_temp",
                "data_type": "color_temperature",
                "conversion": "val_direct",
                "range": "0-255",
                "commands": {
                    "set_color_temp": {
                        "type": CMD_TYPE_SET_VAL,
                    },
                },
            },
            "P3": {
                "description": "brightness",
                "data_type": "nightlight_brightness",
                "conversion": "val_direct",
                "range": "0,63,127,195,255",
                "commands": {
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                    },
                },
            },
        },
    },
    "SL_SC_CV": {
        "name": "语音小Q",
        "category": "switch",
        "manufacturer": "lifesmart",
        "model": "SL_SC_CV",
        "_generation": 2,
        "platforms": {
            "switch": {
                "io_configs": {
                    "P1": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                },
            },
        },
    },
    # ================= 2.6 感应器系列 (Sensor Series) =================
    # 2.6.1 门禁感应器（Guard Sensor)
    "SL_SC_G": {
        "name": "门禁感应器",
        "category": "sensor",
        "manufacturer": "lifesmart",
        "model": "SL_SC_G",
        "_generation": 2,
        "platforms": {
            "binary_sensor": {
                "io_configs": {
                    "G": {
                        "description": "current_state",
                        "data_type": "door_status",
                        "conversion": "val_direct",
                        "device_class": "door",
                    },
                },
            },
            "sensor": {
                "io_configs": {
                    "V": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "v_field",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                },
            },
        },
    },
    "SL_SC_BG": {
        "name": "门禁感应器（带按键震动）",
        "category": "sensor",
        "manufacturer": "lifesmart",
        "model": "SL_SC_BG",
        "_generation": 2,
        "platforms": {
            "binary_sensor": {
                "io_configs": {
                    "G": {
                        "description": "current_state",
                        "data_type": "door_status",
                        "conversion": "type_bit_0",
                        "device_class": "door",
                    },
                    "B": {
                        "description": "button",
                        "data_type": "button_status",
                        "conversion": "val_direct",
                        "device_class": "moving",
                    },
                    "AXS": {
                        "description": "vibration_status",
                        "data_type": "vibration_status",
                        "conversion": "val_direct",
                        "device_class": "vibration",
                    },
                },
            },
            "sensor": {
                "io_configs": {
                    "V": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "v_field",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                },
            },
        },
    },
    "SL_SC_GS": {
        "name": "门禁感应器（增强版）",
        "binary_sensor": {
            "P1": {
                "description": "current_state",
                "data_type": "door_status",
                "conversion": "type_bit_0",
                "device_class": "door",
            },
            "AXS": {
                "description": "vibration_status",
                "data_type": "vibration_status",
                "conversion": "type_bit_0",
                "device_class": "vibration",
            },
        },
        "sensor": {
            "V": {
                "description": "energy",
                "data_type": "battery",
                "conversion": "v_field",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    "SL_SC_MHW": {
        "name": "动态感应器",
        "category": "sensor",
        "manufacturer": "lifesmart",
        "model": "SL_SC_MHW",
        "_generation": 2,
        "platforms": {
            "binary_sensor": {
                "io_configs": {
                    "M": {
                        "description": "motion",
                        "data_type": "motion_status",
                        "conversion": "val_direct",
                        "device_class": "motion",
                    },
                },
            },
            "sensor": {
                "io_configs": {
                    "V": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "v_field",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                },
            },
        },
    },
    "SL_SC_BM": {
        "name": "动态感应器",
        "category": "sensor",
        "manufacturer": "lifesmart",
        "model": "SL_SC_BM",
        "_generation": 2,
        "platforms": {
            "binary_sensor": {
                "io_configs": {
                    "M": {
                        "description": "motion",
                        "data_type": "motion_status",
                        "conversion": "val_direct",
                        "device_class": "motion",
                    },
                },
            },
            "sensor": {
                "io_configs": {
                    "V": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "v_field",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                },
            },
        },
    },
    "SL_SC_CM": {
        "name": "动态感应器（带USB供电）",
        "category": "sensor",
        "manufacturer": "lifesmart",
        "model": "SL_SC_CM",
        "_generation": 2,
        "platforms": {
            "binary_sensor": {
                "io_configs": {
                    "P1": {
                        "description": "motion",
                        "data_type": "motion_status",
                        "conversion": "val_direct",
                        "device_class": "motion",
                    },
                },
            },
            "sensor": {
                "io_configs": {
                    "P3": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "v_field",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                    "P4": {
                        "description": "electric",
                        "data_type": "voltage",
                        "conversion": "val_direct",
                        "device_class": "voltage",
                        "unit_of_measurement": "V",
                        "state_class": "measurement",
                    },
                },
            },
        },
    },
    "SL_BP_MZ": {
        "name": "动态感应器PRO",
        "binary_sensor": {
            "P1": {
                "description": "motion",
                "data_type": "motion_status",
                "conversion": "val_direct",
                "device_class": "motion",
            },
        },
        "sensor": {
            "P2": {
                "description": "illuminance",
                "data_type": "illuminance",
                "conversion": "v_field",
                "device_class": "illuminance",
                "unit_of_measurement": "lx",
                "state_class": "measurement",
            },
            "P3": {
                "description": "energy",
                "data_type": "battery",
                "conversion": "v_field",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    "SL_SC_THL": {
        "name": "环境感应器（温湿度光照）",
        "category": "sensor",
        "manufacturer": "lifesmart",
        "model": "SL_SC_THL",
        "_generation": 2,
        "platforms": {
            "sensor": {
                "io_configs": {
                    "T": {
                        "description": "temperature",
                        "data_type": "temperature",
                        "conversion": "val_div_10",
                        "device_class": "temperature",
                        "unit_of_measurement": "°C",
                        "state_class": "measurement",
                    },
                    "H": {
                        "description": "humidity",
                        "data_type": "humidity",
                        "conversion": "v_field",
                        "device_class": "humidity",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                    "Z": {
                        "description": "illuminance",
                        "data_type": "illuminance",
                        "conversion": "v_field",
                        "device_class": "illuminance",
                        "unit_of_measurement": "lx",
                        "state_class": "measurement",
                    },
                    "V": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "v_field",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                },
            },
        },
    },
    "SL_SC_BE": {
        "name": "环境感应器（温湿度光照）",
        "category": "sensor",
        "manufacturer": "lifesmart",
        "model": "SL_SC_BE",
        "_generation": 2,
        "platforms": {
            "sensor": {
                "io_configs": {
                    "T": {
                        "description": "temperature",
                        "data_type": "temperature",
                        "conversion": "val_div_10",
                        "device_class": "temperature",
                        "unit_of_measurement": "°C",
                        "state_class": "measurement",
                    },
                    "H": {
                        "description": "humidity",
                        "data_type": "humidity",
                        "conversion": "v_field",
                        "device_class": "humidity",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                    "Z": {
                        "description": "illuminance",
                        "data_type": "illuminance",
                        "conversion": "v_field",
                        "device_class": "illuminance",
                        "unit_of_measurement": "lx",
                        "state_class": "measurement",
                    },
                    "V": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "v_field",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                },
            },
        },
    },
    "SL_SC_WA": {
        "name": "水浸传感器",
        "category": "sensor",
        "manufacturer": "lifesmart",
        "model": "SL_SC_WA",
        "_generation": 2,
        "platforms": {
            "binary_sensor": {
                "io_configs": {
                    "WA": {
                        "description": "water_leak_detection",
                        "data_type": "water_leak",
                        "conversion": "val_greater_than_zero",
                        "device_class": "moisture",
                    },
                },
            },
            "sensor": {
                "io_configs": {
                    "WA": {
                        "description": "electric",
                        "data_type": "conductivity",
                        "conversion": "val_direct",
                        "device_class": "moisture",
                        "unit_of_measurement": "µS/cm",
                        "state_class": "measurement",
                    },
                    "V": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "v_field",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                },
            },
        },
    },
    "SL_SC_CH": {
        "name": "甲醛感应器",
        "sensor": {
            "P1": {
                "description": "formaldehyde_concentration",
                "data_type": "甲醛_concentration",
                "conversion": "v_field",
                "device_class": "volatile_organic_compounds",
                "unit_of_measurement": "µg/m³",
                "state_class": "measurement",
            },
        },
        "switch": {
            "P2": {
                "description": "concentration",
                "data_type": "threshold_setting",
                "conversion": "val_direct",
                "commands": {
                    "set_sensitivity": {
                        "type": CMD_TYPE_SET_CONFIG,
                    },
                },
            },
            "P3": {
                "description": "alarm_sound",
                "data_type": "alarm_status",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
        },
    },
    "SL_SC_CP": {
        "name": "燃气感应器",
        "sensor": {
            "P1": {
                "description": "concentration",
                "data_type": "燃气_concentration",
                "conversion": "val_direct",
                "device_class": "gas",
                "unit_of_measurement": "ppm",
                "state_class": "measurement",
            },
        },
        "switch": {
            "P2": {
                "description": "concentration",
                "data_type": "threshold_setting",
                "conversion": "val_direct",
                "commands": {
                    "set_sensitivity": {
                        "type": CMD_TYPE_SET_CONFIG,
                    },
                },
            },
            "P3": {
                "description": "alarm_sound",
                "data_type": "alarm_status",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
        },
    },
    "SL_SC_CQ": {
        "name": "TVOC+CO2环境感应器",
        "sensor": {
            "P1": {
                "description": "temperature",
                "data_type": "temperature",
                "conversion": "v_field",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
            "P2": {
                "description": "humidity",
                "data_type": "humidity",
                "conversion": "v_field",
                "device_class": "humidity",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "P3": {
                "description": "concentration",
                "data_type": "co2_concentration",
                "conversion": "v_field",
                "device_class": "carbon_dioxide",
                "unit_of_measurement": "ppm",
                "state_class": "measurement",
            },
            "P4": {
                "description": "concentration",
                "data_type": "tvoc_concentration",
                "conversion": "v_field",
                "device_class": "volatile_organic_compounds",
                "unit_of_measurement": "mg/m³",
                "state_class": "measurement",
            },
            "P5": {
                "description": "energy",
                "data_type": "battery",
                "conversion": "v_field",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "P6": {
                "description": "electric",
                "data_type": "voltage",
                "conversion": "val_direct",
                "device_class": "voltage",
                "unit_of_measurement": "V",
                "state_class": "measurement",
            },
        },
    },
    "ELIQ_EM": {
        "name": "ELIQ电量计量器",
        "sensor": {
            "EPA": {
                "description": "power",
                "data_type": "power",
                "conversion": "val_direct",
                "device_class": "power",
                "unit_of_measurement": "W",
                "state_class": "measurement",
            },
        },
    },
    "SL_P_A": {
        "name": "烟雾感应器",
        "binary_sensor": {
            "P1": {
                "description": "sl_p_a",
                "data_type": "smoke_alarm",
                "conversion": "val_direct",
                "device_class": "smoke",
            },
        },
        "sensor": {
            "P2": {
                "description": "voltage",
                "data_type": "battery",
                "conversion": "v_field",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    "SL_SC_CA": {
        "name": "CO2环境感应器",
        "sensor": {
            "P1": {
                "description": "temperature",
                "data_type": "temperature",
                "conversion": "v_field",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
            "P2": {
                "description": "humidity",
                "data_type": "humidity",
                "conversion": "v_field",
                "device_class": "humidity",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "P3": {
                "description": "concentration",
                "data_type": "co2_concentration",
                "conversion": "v_field",
                "device_class": "carbon_dioxide",
                "unit_of_measurement": "ppm",
                "state_class": "measurement",
            },
            "P4": {
                "description": "energy",
                "data_type": "battery",
                "conversion": "v_field",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "P5": {
                "description": "electric",
                "data_type": "voltage",
                "conversion": "val_direct",
                "device_class": "voltage",
                "unit_of_measurement": "V",
                "state_class": "measurement",
            },
        },
    },
    "SL_P_RM": {
        "name": "雷达人体存在感应器",
        "binary_sensor": {
            "P1": {
                "description": "detection",
                "data_type": "motion_status",
                "conversion": "val_direct",
                "device_class": "motion",
            },
        },
        "switch": {
            "P2": {
                "description": "detection",
                "data_type": "radar_config",
                "conversion": "val_direct",
                "commands": {
                    "set_config": {
                        "type": CMD_TYPE_SET_CONFIG,
                    },
                },
            },
        },
    },
    "SL_DF_GG": {
        "name": "云防门窗感应器",
        "binary_sensor": {
            "A": {
                "description": "current_state",
                "data_type": "door_status",
                "conversion": "type_bit_0",
                "device_class": "door",
            },
            "TR": {
                "description": "tamper",
                "data_type": "tamper_status",
                "conversion": "type_bit_0",
                "device_class": "tamper",
            },
            "A2": {
                "description": "sensor",
                "data_type": "door_status",
                "conversion": "type_bit_0",
                "device_class": "door",
            },
        },
        "sensor": {
            "T": {
                "description": "temperature",
                "data_type": "temperature",
                "conversion": "v_field",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
            "V": {
                "description": "energy",
                "data_type": "battery",
                "conversion": "v_field",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    "SL_DF_MM": {
        "name": "云防动态感应器",
        "binary_sensor": {
            "M": {
                "description": "current_state",
                "data_type": "motion_status",
                "conversion": "type_bit_0",
                "device_class": "motion",
            },
            "TR": {
                "description": "tamper",
                "data_type": "tamper_status",
                "conversion": "type_bit_0",
                "device_class": "tamper",
            },
        },
        "sensor": {
            "T": {
                "description": "temperature",
                "data_type": "temperature",
                "conversion": "v_field",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
            "V": {
                "description": "energy",
                "data_type": "battery",
                "conversion": "v_field",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    "SL_DF_SR": {
        "name": "云防室内警铃",
        "binary_sensor": {
            "SR": {
                "description": "current_state",
                "data_type": "siren_status",
                "conversion": "type_bit_0",
                "device_class": "sound",
            },
            "TR": {
                "description": "tamper",
                "data_type": "tamper_status",
                "conversion": "type_bit_0",
                "device_class": "tamper",
            },
        },
        "sensor": {
            "T": {
                "description": "temperature",
                "data_type": "temperature",
                "conversion": "v_field",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
            "V": {
                "description": "energy",
                "data_type": "battery",
                "conversion": "v_field",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
        "switch": {
            "P1": {
                "description": "setting",
                "data_type": "alarm_config",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_config_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_config_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
        },
    },
    "SL_DF_BB": {
        "name": "云防遥控器",
        "binary_sensor": {
            "eB1": {
                "description": "status",
                "data_type": "button_status",
                "conversion": "type_bit_0",
                "device_class": "moving",
            },
            "eB2": {
                "description": "status",
                "data_type": "button_status",
                "conversion": "type_bit_0",
                "device_class": "moving",
            },
            "eB3": {
                "description": "status",
                "data_type": "button_status",
                "conversion": "type_bit_0",
                "device_class": "moving",
            },
            "eB4": {
                "description": "status",
                "data_type": "button_status",
                "conversion": "type_bit_0",
                "device_class": "moving",
            },
        },
        "sensor": {
            "V": {
                "description": "energy",
                "data_type": "battery",
                "conversion": "v_field",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    "SL_SC_CN": {
        "name": "噪音感应器",
        "sensor": {
            "P1": {
                "description": "sl_sc_cn",
                "data_type": "noise_level",
                "conversion": "val_direct",
                "device_class": "sound_pressure",
                "unit_of_measurement": "dB",
                "state_class": "measurement",
            },
            "P4": {
                "description": "sl_sc_cn",
                "data_type": "noise_calibration",
                "conversion": "val_direct",
                "device_class": "sound_pressure",
                "unit_of_measurement": "dB",
                "state_class": "measurement",
            },
        },
        "switch": {
            "P2": {
                "description": "setting",
                "data_type": "threshold_config",
                "conversion": "val_direct",
                "commands": {
                    "set_threshold": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                },
            },
            "P3": {
                "description": "setting",
                "data_type": "alarm_config",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_config_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_config_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
        },
    },
    # ================= 2.7 空气净化器 (Air Purifier) =================
    "OD_MFRESH_M8088": {
        "name": "空气净化器",
        "switch": {
            "O": {
                "description": "switch",
                "data_type": "binary_switch",
                "conversion": "type_bit0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
            "RM": {
                "description": "mode",
                "data_type": "run_mode",
                "conversion": "val_direct",
                "commands": {
                    "set_mode": {
                        "type": CMD_TYPE_SET_VAL,
                    },
                },
            },
        },
        "sensor": {
            "T": {
                "description": "temperature",
                "data_type": "temperature",
                "conversion": "friendly_value",
                "unit_of_measurement": "°C",
                "device_class": "temperature",
                "state_class": "measurement",
            },
            "H": {
                "description": "humidity",
                "data_type": "humidity",
                "conversion": "friendly_value",
                "unit_of_measurement": "%",
                "device_class": "humidity",
                "state_class": "measurement",
            },
            "PM": {
                "description": "PM2.5",
                "data_type": "pm25",
                "conversion": "friendly_value",
                "unit_of_measurement": "µg/m³",
                "device_class": "pm25",
                "state_class": "measurement",
            },
            "FL": {
                "description": "fl",
                "data_type": "filter_life",
                "conversion": "val_direct",
                "unit_of_measurement": "h",
            },
            "UV": {
                "description": "fl",
                "data_type": "uv_index",
                "conversion": "val_direct",
            },
        },
    },
    # ================= 2.8 智能门锁 (Smart Door Lock) =================
    # 2.8.1 智能门锁系列 (Smart Door Lock Series)
    "SL_LK_LS": {
        "name": "思锁智能门锁",
        "category": "lock",
        "manufacturer": "lifesmart",
        "model": "SL_LK_LS",
        "_generation": 2,
        "lock_features": {
            "virtual_entities": {
                "alm_bitmask": {
                    "bit_definitions": {
                        0: {
                            "name": "error_alarm",
                            "description": "error_alarm",
                            "device_class": "problem",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "错误报警",
                        },
                        1: {
                            "name": "hijack_alarm",
                            "description": "hijack_alarm",
                            "device_class": "safety",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "劫持报警",
                        },
                        2: {
                            "name": "tamper_alarm",
                            "description": "tamper_alarm",
                            "device_class": "tamper",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "防撬报警",
                        },
                        3: {
                            "name": "key_alarm",
                            "description": "mechanical_key_alarm",
                            "device_class": "lock",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "机械钥匙报警",
                        },
                        4: {
                            "name": "low_battery",
                            "description": "low_voltage_alarm",
                            "device_class": "battery",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "低电量报警",
                        },
                        5: {
                            "name": "motion_alarm",
                            "description": "motion_alarm",
                            "device_class": "motion",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "异动告警",
                        },
                        6: {
                            "name": "doorbell",
                            "description": "doorbell",
                            "device_class": "sound",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "门铃",
                        },
                        7: {
                            "name": "fire_alarm",
                            "description": "fire_alarm",
                            "device_class": "smoke",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "火警",
                        },
                        8: {
                            "name": "intrusion_alarm",
                            "description": "intrusion_alarm",
                            "device_class": "safety",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "入侵告警",
                        },
                        11: {
                            "name": "factory_reset",
                            "description": "factory_reset_alarm",
                            "device_class": "problem",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "恢复出厂告警",
                        },
                    },
                },
                "evtlo_data": {
                    "data_definitions": {
                        "lock_status": {
                            "name": "门锁状态",
                            "description": "door_lock_switch_status",
                            "platform": "lock",
                            "extraction_logic": "type_bit_0",
                            "extraction_params": {},
                            "friendly_name": "门锁",
                        },
                        "user_id": {
                            "name": "用户编号",
                            "description": "unlock_user_id",
                            "platform": "sensor",
                            "extraction_logic": "bit_range",
                            "extraction_params": {"start_bit": 0, "end_bit": 11},
                            "friendly_name": "用户编号",
                        },
                        "unlock_method": {
                            "name": "开锁方式",
                            "description": "unlock_method",
                            "platform": "sensor",
                            "extraction_logic": "bit_range_mapped",
                            "extraction_params": {
                                "start_bit": 12,
                                "end_bit": 15,
                                "mapping": {
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
                            "description": "double_open_mode",
                            "platform": "binary_sensor",
                            "device_class": "lock",
                            "extraction_logic": "dual_unlock_detection",
                            "extraction_params": {},
                            "friendly_name": "双开模式",
                        },
                    },
                },
            },
        },
        "platforms": {
            "lock": {
                "io_configs": {
                    "EVTLO": {
                        "description": "door_lock_status",
                        "data_type": "door_lock",
                        "conversion": "type_bit_0",
                        "device_class": "lock",
                    },
                },
            },
            "binary_sensor": {
                "io_configs": {
                    "ALM": {
                        "description": "status",
                        "data_type": "alarm_status",
                        "conversion": "val_greater_than_zero",
                        "device_class": "problem",
                    },
                },
            },
            "sensor": {
                "io_configs": {
                    "BAT": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "val_direct",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                    "ALM": {
                        "description": "alarm",
                        "data_type": "alarm_status",
                        "conversion": "val_direct",
                    },
                    "EVTLO": {
                        "description": "real_time_unlock",
                        "data_type": "lock_event",
                        "conversion": "val_direct",
                    },
                    "HISLK": {
                        "description": "last_unlock_info",
                        "data_type": "recent_unlock",
                        "conversion": "val_direct",
                    },
                    "EVTOP": {
                        "description": "operation_record",
                        "data_type": "operation_record",
                        "conversion": "val_direct",
                    },
                },
            },
        },
    },
    "SL_LK_GTM": {
        "name": "盖特曼智能门锁",
        "category": "lock",
        "manufacturer": "lifesmart",
        "model": "SL_LK_GTM",
        "_generation": 2,
        "lock_features": {
            "virtual_entities": {
                "alm_bitmask": {
                    "bit_definitions": {
                        0: {
                            "name": "error_alarm",
                            "description": "error_alarm",
                            "device_class": "problem",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "错误报警",
                        },
                        1: {
                            "name": "hijack_alarm",
                            "description": "hijack_alarm",
                            "device_class": "safety",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "劫持报警",
                        },
                        2: {
                            "name": "tamper_alarm",
                            "description": "tamper_alarm",
                            "device_class": "tamper",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "防撬报警",
                        },
                        3: {
                            "name": "key_alarm",
                            "description": "mechanical_key_alarm",
                            "device_class": "lock",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "机械钥匙报警",
                        },
                        4: {
                            "name": "low_battery",
                            "description": "low_voltage_alarm",
                            "device_class": "battery",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "低电量报警",
                        },
                        5: {
                            "name": "motion_alarm",
                            "description": "motion_alarm",
                            "device_class": "motion",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "异动告警",
                        },
                        6: {
                            "name": "doorbell",
                            "description": "doorbell",
                            "device_class": "sound",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "门铃",
                        },
                        7: {
                            "name": "fire_alarm",
                            "description": "fire_alarm",
                            "device_class": "smoke",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "火警",
                        },
                        8: {
                            "name": "intrusion_alarm",
                            "description": "intrusion_alarm",
                            "device_class": "safety",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "入侵告警",
                        },
                        11: {
                            "name": "factory_reset",
                            "description": "factory_reset_alarm",
                            "device_class": "problem",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "恢复出厂告警",
                        },
                    },
                },
                "evtlo_data": {
                    "data_definitions": {
                        "lock_status": {
                            "name": "门锁状态",
                            "description": "door_lock_switch_status",
                            "platform": "lock",
                            "extraction_logic": "type_bit_0",
                            "extraction_params": {},
                            "friendly_name": "门锁",
                        },
                        "user_id": {
                            "name": "用户编号",
                            "description": "unlock_user_id",
                            "platform": "sensor",
                            "extraction_logic": "bit_range",
                            "extraction_params": {"start_bit": 0, "end_bit": 11},
                            "friendly_name": "用户编号",
                        },
                        "unlock_method": {
                            "name": "开锁方式",
                            "description": "unlock_method",
                            "platform": "sensor",
                            "extraction_logic": "bit_range_mapped",
                            "extraction_params": {
                                "start_bit": 12,
                                "end_bit": 15,
                                "mapping": {
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
                            "description": "double_open_mode",
                            "platform": "binary_sensor",
                            "device_class": "lock",
                            "extraction_logic": "dual_unlock_detection",
                            "extraction_params": {},
                            "friendly_name": "双开模式",
                        },
                    },
                },
            },
        },
        "platforms": {
            "sensor": {
                "io_configs": {
                    "BAT": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "val_direct",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                    "ALM": {
                        "description": "alarm",
                        "data_type": "alarm_status",
                        "conversion": "val_direct",
                    },
                    "EVTLO": {
                        "description": "real_time_unlock",
                        "data_type": "lock_event",
                        "conversion": "val_direct",
                    },
                    "HISLK": {
                        "description": "last_unlock_info",
                        "data_type": "recent_unlock",
                        "conversion": "val_direct",
                    },
                    "EVTOP": {
                        "description": "operation_record",
                        "data_type": "operation_record",
                        "conversion": "val_direct",
                    },
                },
            },
        },
    },
    "SL_LK_AG": {
        "name": "Aqara智能门锁",
        "category": "lock",
        "manufacturer": "lifesmart",
        "model": "SL_LK_AG",
        "_generation": 2,
        "lock_features": {
            "virtual_entities": {
                "alm_bitmask": {
                    "bit_definitions": {
                        0: {
                            "name": "error_alarm",
                            "description": "error_alarm",
                            "device_class": "problem",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "错误报警",
                        },
                        1: {
                            "name": "hijack_alarm",
                            "description": "hijack_alarm",
                            "device_class": "safety",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "劫持报警",
                        },
                        2: {
                            "name": "tamper_alarm",
                            "description": "tamper_alarm",
                            "device_class": "tamper",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "防撬报警",
                        },
                        3: {
                            "name": "key_alarm",
                            "description": "mechanical_key_alarm",
                            "device_class": "lock",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "机械钥匙报警",
                        },
                        4: {
                            "name": "low_battery",
                            "description": "low_voltage_alarm",
                            "device_class": "battery",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "低电量报警",
                        },
                        5: {
                            "name": "motion_alarm",
                            "description": "motion_alarm",
                            "device_class": "motion",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "异动告警",
                        },
                        6: {
                            "name": "doorbell",
                            "description": "doorbell",
                            "device_class": "sound",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "门铃",
                        },
                        7: {
                            "name": "fire_alarm",
                            "description": "fire_alarm",
                            "device_class": "smoke",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "火警",
                        },
                        8: {
                            "name": "intrusion_alarm",
                            "description": "intrusion_alarm",
                            "device_class": "safety",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "入侵告警",
                        },
                        11: {
                            "name": "factory_reset",
                            "description": "factory_reset_alarm",
                            "device_class": "problem",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "恢复出厂告警",
                        },
                    },
                },
                "evtlo_data": {
                    "data_definitions": {
                        "lock_status": {
                            "name": "门锁状态",
                            "description": "door_lock_switch_status",
                            "platform": "lock",
                            "extraction_logic": "type_bit_0",
                            "extraction_params": {},
                            "friendly_name": "门锁",
                        },
                        "user_id": {
                            "name": "用户编号",
                            "description": "unlock_user_id",
                            "platform": "sensor",
                            "extraction_logic": "bit_range",
                            "extraction_params": {"start_bit": 0, "end_bit": 11},
                            "friendly_name": "用户编号",
                        },
                        "unlock_method": {
                            "name": "开锁方式",
                            "description": "unlock_method",
                            "platform": "sensor",
                            "extraction_logic": "bit_range_mapped",
                            "extraction_params": {
                                "start_bit": 12,
                                "end_bit": 15,
                                "mapping": {
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
                            "description": "double_open_mode",
                            "platform": "binary_sensor",
                            "device_class": "lock",
                            "extraction_logic": "dual_unlock_detection",
                            "extraction_params": {},
                            "friendly_name": "双开模式",
                        },
                    },
                },
            },
        },
        "platforms": {
            "sensor": {
                "io_configs": {
                    "BAT": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "val_direct",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                    "ALM": {
                        "description": "alarm",
                        "data_type": "alarm_status",
                        "conversion": "val_direct",
                    },
                    "EVTLO": {
                        "description": "real_time_unlock",
                        "data_type": "lock_event",
                        "conversion": "val_direct",
                    },
                    "HISLK": {
                        "description": "last_unlock_info",
                        "data_type": "recent_unlock",
                        "conversion": "val_direct",
                    },
                    "EVTOP": {
                        "description": "operation_record",
                        "data_type": "operation_record",
                        "conversion": "val_direct",
                    },
                },
            },
        },
    },
    "SL_LK_SG": {
        "name": "思哥智能门锁",
        "category": "lock",
        "manufacturer": "lifesmart",
        "model": "SL_LK_SG",
        "_generation": 2,
        "lock_features": {
            "virtual_entities": {
                "alm_bitmask": {
                    "bit_definitions": {
                        0: {
                            "name": "error_alarm",
                            "description": "error_alarm",
                            "device_class": "problem",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "错误报警",
                        },
                        1: {
                            "name": "hijack_alarm",
                            "description": "hijack_alarm",
                            "device_class": "safety",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "劫持报警",
                        },
                        2: {
                            "name": "tamper_alarm",
                            "description": "tamper_alarm",
                            "device_class": "tamper",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "防撬报警",
                        },
                        3: {
                            "name": "key_alarm",
                            "description": "mechanical_key_alarm",
                            "device_class": "lock",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "机械钥匙报警",
                        },
                        4: {
                            "name": "low_battery",
                            "description": "low_voltage_alarm",
                            "device_class": "battery",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "低电量报警",
                        },
                        5: {
                            "name": "motion_alarm",
                            "description": "motion_alarm",
                            "device_class": "motion",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "异动告警",
                        },
                        6: {
                            "name": "doorbell",
                            "description": "doorbell",
                            "device_class": "sound",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "门铃",
                        },
                        7: {
                            "name": "fire_alarm",
                            "description": "fire_alarm",
                            "device_class": "smoke",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "火警",
                        },
                        8: {
                            "name": "intrusion_alarm",
                            "description": "intrusion_alarm",
                            "device_class": "safety",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "入侵告警",
                        },
                        11: {
                            "name": "factory_reset",
                            "description": "factory_reset_alarm",
                            "device_class": "problem",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "恢复出厂告警",
                        },
                    },
                },
                "evtlo_data": {
                    "data_definitions": {
                        "lock_status": {
                            "name": "门锁状态",
                            "description": "door_lock_switch_status",
                            "platform": "lock",
                            "extraction_logic": "type_bit_0",
                            "extraction_params": {},
                            "friendly_name": "门锁",
                        },
                        "user_id": {
                            "name": "用户编号",
                            "description": "unlock_user_id",
                            "platform": "sensor",
                            "extraction_logic": "bit_range",
                            "extraction_params": {"start_bit": 0, "end_bit": 11},
                            "friendly_name": "用户编号",
                        },
                        "unlock_method": {
                            "name": "开锁方式",
                            "description": "unlock_method",
                            "platform": "sensor",
                            "extraction_logic": "bit_range_mapped",
                            "extraction_params": {
                                "start_bit": 12,
                                "end_bit": 15,
                                "mapping": {
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
                            "description": "double_open_mode",
                            "platform": "binary_sensor",
                            "device_class": "lock",
                            "extraction_logic": "dual_unlock_detection",
                            "extraction_params": {},
                            "friendly_name": "双开模式",
                        },
                    },
                },
            },
        },
        "platforms": {
            "sensor": {
                "io_configs": {
                    "BAT": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "val_direct",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                    "ALM": {
                        "description": "alarm",
                        "data_type": "alarm_status",
                        "conversion": "val_direct",
                    },
                    "EVTLO": {
                        "description": "real_time_unlock",
                        "data_type": "lock_event",
                        "conversion": "val_direct",
                    },
                    "HISLK": {
                        "description": "last_unlock_info",
                        "data_type": "recent_unlock",
                        "conversion": "val_direct",
                    },
                    "EVTOP": {
                        "description": "operation_record",
                        "data_type": "operation_record",
                        "conversion": "val_direct",
                    },
                },
            },
        },
    },
    "SL_LK_YL": {
        "name": "Yale智能门锁",
        "category": "lock",
        "manufacturer": "lifesmart",
        "model": "SL_LK_YL",
        "_generation": 2,
        "lock_features": {
            "virtual_entities": {
                "alm_bitmask": {
                    "bit_definitions": {
                        0: {
                            "name": "error_alarm",
                            "description": "error_alarm",
                            "device_class": "problem",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "错误报警",
                        },
                        1: {
                            "name": "hijack_alarm",
                            "description": "hijack_alarm",
                            "device_class": "safety",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "劫持报警",
                        },
                        2: {
                            "name": "tamper_alarm",
                            "description": "tamper_alarm",
                            "device_class": "tamper",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "防撬报警",
                        },
                        3: {
                            "name": "key_alarm",
                            "description": "mechanical_key_alarm",
                            "device_class": "lock",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "机械钥匙报警",
                        },
                        4: {
                            "name": "low_battery",
                            "description": "low_voltage_alarm",
                            "device_class": "battery",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "低电量报警",
                        },
                        5: {
                            "name": "motion_alarm",
                            "description": "motion_alarm",
                            "device_class": "motion",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "异动告警",
                        },
                        6: {
                            "name": "doorbell",
                            "description": "doorbell",
                            "device_class": "sound",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "门铃",
                        },
                        7: {
                            "name": "fire_alarm",
                            "description": "fire_alarm",
                            "device_class": "smoke",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "火警",
                        },
                        8: {
                            "name": "intrusion_alarm",
                            "description": "intrusion_alarm",
                            "device_class": "safety",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "入侵告警",
                        },
                        11: {
                            "name": "factory_reset",
                            "description": "factory_reset_alarm",
                            "device_class": "problem",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "恢复出厂告警",
                        },
                    },
                },
                "evtlo_data": {
                    "data_definitions": {
                        "lock_status": {
                            "name": "门锁状态",
                            "description": "door_lock_switch_status",
                            "platform": "lock",
                            "extraction_logic": "type_bit_0",
                            "extraction_params": {},
                            "friendly_name": "门锁",
                        },
                        "user_id": {
                            "name": "用户编号",
                            "description": "unlock_user_id",
                            "platform": "sensor",
                            "extraction_logic": "bit_range",
                            "extraction_params": {"start_bit": 0, "end_bit": 11},
                            "friendly_name": "用户编号",
                        },
                        "unlock_method": {
                            "name": "开锁方式",
                            "description": "unlock_method",
                            "platform": "sensor",
                            "extraction_logic": "bit_range_mapped",
                            "extraction_params": {
                                "start_bit": 12,
                                "end_bit": 15,
                                "mapping": {
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
                            "description": "double_open_mode",
                            "platform": "binary_sensor",
                            "device_class": "lock",
                            "extraction_logic": "dual_unlock_detection",
                            "extraction_params": {},
                            "friendly_name": "双开模式",
                        },
                    },
                },
            },
        },
        "platforms": {
            "sensor": {
                "io_configs": {
                    "BAT": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "val_direct",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                    "ALM": {
                        "description": "alarm",
                        "data_type": "alarm_status",
                        "conversion": "val_direct",
                    },
                    "EVTLO": {
                        "description": "real_time_unlock",
                        "data_type": "lock_event",
                        "conversion": "val_direct",
                    },
                    "HISLK": {
                        "description": "last_unlock_info",
                        "data_type": "recent_unlock",
                        "conversion": "val_direct",
                    },
                    "EVTOP": {
                        "description": "operation_record",
                        "data_type": "operation_record",
                        "conversion": "val_direct",
                    },
                },
            },
        },
    },
    "SL_LK_SWIFTE": {
        "name": "SWIFTE智能门锁",
        "category": "lock",
        "manufacturer": "lifesmart",
        "model": "SL_LK_SWIFTE",
        "_generation": 2,
        "lock_features": {
            "virtual_entities": {
                "alm_bitmask": {
                    "bit_definitions": {
                        0: {
                            "name": "error_alarm",
                            "description": "error_alarm",
                            "device_class": "problem",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "错误报警",
                        },
                        1: {
                            "name": "hijack_alarm",
                            "description": "hijack_alarm",
                            "device_class": "safety",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "劫持报警",
                        },
                        2: {
                            "name": "tamper_alarm",
                            "description": "tamper_alarm",
                            "device_class": "tamper",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "防撬报警",
                        },
                        3: {
                            "name": "key_alarm",
                            "description": "mechanical_key_alarm",
                            "device_class": "lock",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "机械钥匙报警",
                        },
                        4: {
                            "name": "low_battery",
                            "description": "low_voltage_alarm",
                            "device_class": "battery",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "低电量报警",
                        },
                        5: {
                            "name": "motion_alarm",
                            "description": "motion_alarm",
                            "device_class": "motion",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "异动告警",
                        },
                        6: {
                            "name": "doorbell",
                            "description": "doorbell",
                            "device_class": "sound",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "门铃",
                        },
                        7: {
                            "name": "fire_alarm",
                            "description": "fire_alarm",
                            "device_class": "smoke",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "火警",
                        },
                        8: {
                            "name": "intrusion_alarm",
                            "description": "intrusion_alarm",
                            "device_class": "safety",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "入侵告警",
                        },
                        11: {
                            "name": "factory_reset",
                            "description": "factory_reset_alarm",
                            "device_class": "problem",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "恢复出厂告警",
                        },
                    },
                },
                "evtlo_data": {
                    "data_definitions": {
                        "lock_status": {
                            "name": "门锁状态",
                            "description": "door_lock_switch_status",
                            "platform": "lock",
                            "extraction_logic": "type_bit_0",
                            "extraction_params": {},
                            "friendly_name": "门锁",
                        },
                        "user_id": {
                            "name": "用户编号",
                            "description": "unlock_user_id",
                            "platform": "sensor",
                            "extraction_logic": "bit_range",
                            "extraction_params": {"start_bit": 0, "end_bit": 11},
                            "friendly_name": "用户编号",
                        },
                        "unlock_method": {
                            "name": "开锁方式",
                            "description": "unlock_method",
                            "platform": "sensor",
                            "extraction_logic": "bit_range_mapped",
                            "extraction_params": {
                                "start_bit": 12,
                                "end_bit": 15,
                                "mapping": {
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
                            "description": "double_open_mode",
                            "platform": "binary_sensor",
                            "device_class": "lock",
                            "extraction_logic": "dual_unlock_detection",
                            "extraction_params": {},
                            "friendly_name": "双开模式",
                        },
                    },
                },
            },
        },
        "platforms": {
            "sensor": {
                "io_configs": {
                    "BAT": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "val_direct",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                    "ALM": {
                        "description": "alarm",
                        "data_type": "alarm_status",
                        "conversion": "val_direct",
                    },
                    "EVTLO": {
                        "description": "real_time_unlock",
                        "data_type": "lock_event",
                        "conversion": "val_direct",
                    },
                    "HISLK": {
                        "description": "last_unlock_info",
                        "data_type": "recent_unlock",
                        "conversion": "val_direct",
                    },
                    "EVTOP": {
                        "description": "operation_record",
                        "data_type": "operation_record",
                        "conversion": "val_direct",
                    },
                },
            },
        },
    },
    "OD_JIUWANLI_LOCK1": {
        "name": "久万里智能门锁",
        "category": "lock",
        "manufacturer": "lifesmart",
        "model": "OD_JIUWANLI_LOCK1",
        "_generation": 2,
        "lock_features": {
            "virtual_entities": {
                "alm_bitmask": {
                    "bit_definitions": {
                        0: {
                            "name": "error_alarm",
                            "description": "error_alarm",
                            "device_class": "problem",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "错误报警",
                        },
                        1: {
                            "name": "hijack_alarm",
                            "description": "hijack_alarm",
                            "device_class": "safety",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "劫持报警",
                        },
                        2: {
                            "name": "tamper_alarm",
                            "description": "tamper_alarm",
                            "device_class": "tamper",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "防撬报警",
                        },
                        3: {
                            "name": "key_alarm",
                            "description": "mechanical_key_alarm",
                            "device_class": "lock",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "机械钥匙报警",
                        },
                        4: {
                            "name": "low_battery",
                            "description": "low_voltage_alarm",
                            "device_class": "battery",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "低电量报警",
                        },
                        5: {
                            "name": "motion_alarm",
                            "description": "motion_alarm",
                            "device_class": "motion",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "异动告警",
                        },
                        6: {
                            "name": "doorbell",
                            "description": "doorbell",
                            "device_class": "sound",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "门铃",
                        },
                        7: {
                            "name": "fire_alarm",
                            "description": "fire_alarm",
                            "device_class": "smoke",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "火警",
                        },
                        8: {
                            "name": "intrusion_alarm",
                            "description": "intrusion_alarm",
                            "device_class": "safety",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "入侵告警",
                        },
                        11: {
                            "name": "factory_reset",
                            "description": "factory_reset_alarm",
                            "device_class": "problem",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "恢复出厂告警",
                        },
                    },
                },
                "evtlo_data": {
                    "data_definitions": {
                        "lock_status": {
                            "name": "门锁状态",
                            "description": "door_lock_switch_status",
                            "platform": "lock",
                            "extraction_logic": "type_bit_0",
                            "extraction_params": {},
                            "friendly_name": "门锁",
                        },
                        "user_id": {
                            "name": "用户编号",
                            "description": "unlock_user_id",
                            "platform": "sensor",
                            "extraction_logic": "bit_range",
                            "extraction_params": {"start_bit": 0, "end_bit": 11},
                            "friendly_name": "用户编号",
                        },
                        "unlock_method": {
                            "name": "开锁方式",
                            "description": "unlock_method",
                            "platform": "sensor",
                            "extraction_logic": "bit_range_mapped",
                            "extraction_params": {
                                "start_bit": 12,
                                "end_bit": 15,
                                "mapping": {
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
                            "description": "double_open_mode",
                            "platform": "binary_sensor",
                            "device_class": "lock",
                            "extraction_logic": "dual_unlock_detection",
                            "extraction_params": {},
                            "friendly_name": "双开模式",
                        },
                    },
                },
            },
        },
        "platforms": {
            "sensor": {
                "io_configs": {
                    "BAT": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "val_direct",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                    "ALM": {
                        "description": "alarm",
                        "data_type": "alarm_status",
                        "conversion": "val_direct",
                    },
                    "EVTLO": {
                        "description": "real_time_unlock",
                        "data_type": "lock_event",
                        "conversion": "val_direct",
                    },
                    "HISLK": {
                        "description": "last_unlock_info",
                        "data_type": "recent_unlock",
                        "conversion": "val_direct",
                    },
                    "EVTOP": {
                        "description": "operation_record",
                        "data_type": "operation_record",
                        "conversion": "val_direct",
                    },
                },
            },
        },
    },
    "SL_P_BDLK": {
        "name": "百度智能门锁",
        "category": "lock",
        "manufacturer": "lifesmart",
        "model": "SL_P_BDLK",
        "_generation": 2,
        "lock_features": {
            "virtual_entities": {
                "alm_bitmask": {
                    "bit_definitions": {
                        0: {
                            "name": "error_alarm",
                            "description": "error_alarm",
                            "device_class": "problem",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "错误报警",
                        },
                        1: {
                            "name": "hijack_alarm",
                            "description": "hijack_alarm",
                            "device_class": "safety",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "劫持报警",
                        },
                        2: {
                            "name": "tamper_alarm",
                            "description": "tamper_alarm",
                            "device_class": "tamper",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "防撬报警",
                        },
                        3: {
                            "name": "key_alarm",
                            "description": "mechanical_key_alarm",
                            "device_class": "lock",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "机械钥匙报警",
                        },
                        4: {
                            "name": "low_battery",
                            "description": "low_voltage_alarm",
                            "device_class": "battery",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "低电量报警",
                        },
                        5: {
                            "name": "motion_alarm",
                            "description": "motion_alarm",
                            "device_class": "motion",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "异动告警",
                        },
                        6: {
                            "name": "doorbell",
                            "description": "doorbell",
                            "device_class": "sound",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "门铃",
                        },
                        7: {
                            "name": "fire_alarm",
                            "description": "fire_alarm",
                            "device_class": "smoke",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "火警",
                        },
                        8: {
                            "name": "intrusion_alarm",
                            "description": "intrusion_alarm",
                            "device_class": "safety",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "入侵告警",
                        },
                        11: {
                            "name": "factory_reset",
                            "description": "factory_reset_alarm",
                            "device_class": "problem",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "恢复出厂告警",
                        },
                    },
                },
                "evtlo_data": {
                    "data_definitions": {
                        "lock_status": {
                            "name": "门锁状态",
                            "description": "door_lock_switch_status",
                            "platform": "lock",
                            "extraction_logic": "type_bit_0",
                            "extraction_params": {},
                            "friendly_name": "门锁",
                        },
                        "user_id": {
                            "name": "用户编号",
                            "description": "unlock_user_id",
                            "platform": "sensor",
                            "extraction_logic": "bit_range",
                            "extraction_params": {"start_bit": 0, "end_bit": 11},
                            "friendly_name": "用户编号",
                        },
                        "unlock_method": {
                            "name": "开锁方式",
                            "description": "unlock_method",
                            "platform": "sensor",
                            "extraction_logic": "bit_range_mapped",
                            "extraction_params": {
                                "start_bit": 12,
                                "end_bit": 15,
                                "mapping": {
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
                            "description": "double_open_mode",
                            "platform": "binary_sensor",
                            "device_class": "lock",
                            "extraction_logic": "dual_unlock_detection",
                            "extraction_params": {},
                            "friendly_name": "双开模式",
                        },
                    },
                },
            },
        },
        "platforms": {
            "sensor": {
                "io_configs": {
                    "BAT": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "val_direct",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                    "ALM": {
                        "description": "alarm",
                        "data_type": "alarm_status",
                        "conversion": "val_direct",
                    },
                    "EVTLO": {
                        "description": "real_time_unlock",
                        "data_type": "lock_event",
                        "conversion": "val_direct",
                    },
                    "HISLK": {
                        "description": "last_unlock_info",
                        "data_type": "recent_unlock",
                        "conversion": "val_direct",
                    },
                    "EVTOP": {
                        "description": "operation_record",
                        "data_type": "operation_record",
                        "conversion": "val_direct",
                    },
                },
            },
        },
    },
    # 2.8.2 C100/C200门锁系列 (C100/C200 Door Lock Series)
    "SL_LK_TY": {
        "name": "C200门锁",
        "category": "lock",
        "manufacturer": "lifesmart",
        "model": "SL_LK_TY",
        "_generation": 2,
        "lock_features": {
            "virtual_entities": {
                "alm_bitmask": {
                    "bit_definitions": {
                        0: {
                            "name": "error_alarm",
                            "description": "error_alarm",
                            "device_class": "problem",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "错误报警",
                        },
                        1: {
                            "name": "hijack_alarm",
                            "description": "hijack_alarm",
                            "device_class": "safety",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "劫持报警",
                        },
                        2: {
                            "name": "tamper_alarm",
                            "description": "tamper_alarm",
                            "device_class": "tamper",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "防撬报警",
                        },
                        3: {
                            "name": "key_alarm",
                            "description": "mechanical_key_alarm",
                            "device_class": "lock",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "机械钥匙报警",
                        },
                        4: {
                            "name": "low_battery",
                            "description": "low_voltage_alarm",
                            "device_class": "battery",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "低电量报警",
                        },
                        5: {
                            "name": "motion_alarm",
                            "description": "motion_alarm",
                            "device_class": "motion",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "异动告警",
                        },
                        6: {
                            "name": "doorbell",
                            "description": "doorbell",
                            "device_class": "sound",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "门铃",
                        },
                        7: {
                            "name": "fire_alarm",
                            "description": "fire_alarm",
                            "device_class": "smoke",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "火警",
                        },
                        8: {
                            "name": "intrusion_alarm",
                            "description": "intrusion_alarm",
                            "device_class": "safety",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "入侵告警",
                        },
                        11: {
                            "name": "factory_reset",
                            "description": "factory_reset_alarm",
                            "device_class": "problem",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "恢复出厂告警",
                        },
                    },
                },
                "evtlo_data": {
                    "data_definitions": {
                        "lock_status": {
                            "name": "门锁状态",
                            "description": "door_lock_switch_status",
                            "platform": "lock",
                            "extraction_logic": "type_bit_0",
                            "extraction_params": {},
                            "friendly_name": "门锁",
                        },
                        "user_id": {
                            "name": "用户编号",
                            "description": "unlock_user_id",
                            "platform": "sensor",
                            "extraction_logic": "bit_range",
                            "extraction_params": {"start_bit": 0, "end_bit": 11},
                            "friendly_name": "用户编号",
                        },
                        "unlock_method": {
                            "name": "开锁方式",
                            "description": "unlock_method",
                            "platform": "sensor",
                            "extraction_logic": "bit_range_mapped",
                            "extraction_params": {
                                "start_bit": 12,
                                "end_bit": 15,
                                "mapping": {
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
                            "description": "double_open_mode",
                            "platform": "binary_sensor",
                            "device_class": "lock",
                            "extraction_logic": "dual_unlock_detection",
                            "extraction_params": {},
                            "friendly_name": "双开模式",
                        },
                    },
                },
            },
        },
        "platforms": {
            "sensor": {
                "io_configs": {
                    "BAT": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "val_direct",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                    "ALM": {
                        "description": "alarm",
                        "data_type": "alarm_status",
                        "conversion": "val_direct",
                    },
                    "EVTLO": {
                        "description": "real_time_unlock",
                        "data_type": "lock_event",
                        "conversion": "val_direct",
                    },
                    "HISLK": {
                        "description": "last_unlock_info",
                        "data_type": "recent_unlock",
                        "conversion": "val_direct",
                    },
                    "EVTBEL": {
                        "description": "evtbel",
                        "data_type": "doorbell_message",
                        "conversion": "val_direct",
                    },
                },
            },
        },
    },
    "SL_LK_DJ": {
        "name": "C100门锁",
        "category": "lock",
        "manufacturer": "lifesmart",
        "model": "SL_LK_DJ",
        "_generation": 2,
        "lock_features": {
            "virtual_entities": {
                "alm_bitmask": {
                    "bit_definitions": {
                        0: {
                            "name": "error_alarm",
                            "description": "error_alarm",
                            "device_class": "problem",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "错误报警",
                        },
                        1: {
                            "name": "hijack_alarm",
                            "description": "hijack_alarm",
                            "device_class": "safety",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "劫持报警",
                        },
                        2: {
                            "name": "tamper_alarm",
                            "description": "tamper_alarm",
                            "device_class": "tamper",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "防撬报警",
                        },
                        3: {
                            "name": "key_alarm",
                            "description": "mechanical_key_alarm",
                            "device_class": "lock",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "机械钥匙报警",
                        },
                        4: {
                            "name": "low_battery",
                            "description": "low_voltage_alarm",
                            "device_class": "battery",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "低电量报警",
                        },
                        5: {
                            "name": "motion_alarm",
                            "description": "motion_alarm",
                            "device_class": "motion",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "异动告警",
                        },
                        6: {
                            "name": "doorbell",
                            "description": "doorbell",
                            "device_class": "sound",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "门铃",
                        },
                        7: {
                            "name": "fire_alarm",
                            "description": "fire_alarm",
                            "device_class": "smoke",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "火警",
                        },
                        8: {
                            "name": "intrusion_alarm",
                            "description": "intrusion_alarm",
                            "device_class": "safety",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "入侵告警",
                        },
                        11: {
                            "name": "factory_reset",
                            "description": "factory_reset_alarm",
                            "device_class": "problem",
                            "platform": "binary_sensor",
                            "extraction_logic": "bit_extract",
                            "friendly_name": "恢复出厂告警",
                        },
                    },
                },
                "evtlo_data": {
                    "data_definitions": {
                        "lock_status": {
                            "name": "门锁状态",
                            "description": "door_lock_switch_status",
                            "platform": "lock",
                            "extraction_logic": "type_bit_0",
                            "extraction_params": {},
                            "friendly_name": "门锁",
                        },
                        "user_id": {
                            "name": "用户编号",
                            "description": "unlock_user_id",
                            "platform": "sensor",
                            "extraction_logic": "bit_range",
                            "extraction_params": {"start_bit": 0, "end_bit": 11},
                            "friendly_name": "用户编号",
                        },
                        "unlock_method": {
                            "name": "开锁方式",
                            "description": "unlock_method",
                            "platform": "sensor",
                            "extraction_logic": "bit_range_mapped",
                            "extraction_params": {
                                "start_bit": 12,
                                "end_bit": 15,
                                "mapping": {
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
                            "description": "double_open_mode",
                            "platform": "binary_sensor",
                            "device_class": "lock",
                            "extraction_logic": "dual_unlock_detection",
                            "extraction_params": {},
                            "friendly_name": "双开模式",
                        },
                    },
                },
            },
        },
        "platforms": {
            "sensor": {
                "io_configs": {
                    "BAT": {
                        "description": "energy",
                        "data_type": "battery",
                        "conversion": "val_direct",
                        "device_class": "battery",
                        "unit_of_measurement": "%",
                        "state_class": "measurement",
                    },
                    "ALM": {
                        "description": "alarm",
                        "data_type": "alarm_status",
                        "conversion": "val_direct",
                    },
                    "EVTLO": {
                        "description": "real_time_unlock",
                        "data_type": "lock_event",
                        "conversion": "val_direct",
                    },
                    "HISLK": {
                        "description": "last_unlock_info",
                        "data_type": "recent_unlock",
                        "conversion": "val_direct",
                    },
                    "EVTBEL": {
                        "description": "evtbel",
                        "data_type": "doorbell_message",
                        "conversion": "val_direct",
                    },
                },
            },
        },
    },
    # ================= 2.9 温控器 (Climate Controller) =================
    # 2.9.1 智控器空调面板 (Central AIR Board)
    "V_AIR_P": {
        "name": "智控器空调面板",
        "category": "climate",
        "manufacturer": "lifesmart",
        "model": "V_AIR_P",
        "_generation": 2,  # DEVICE_CENTRIC_CONFIG格式标识
        # 基础平台配置
        "platforms": {
            "climate": {
                "io_configs": {
                    "O": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": "CMD_TYPE_ON",
                                "val": 1,
                            },
                            "off": {
                                "type": "CMD_TYPE_OFF",
                                "val": 0,
                            },
                        },
                    },
                    "MODE": {
                        "description": "mode",
                        "data_type": "hvac_mode",
                        "conversion": "val_direct",
                        "commands": {
                            "set_mode": {
                                "type": "CMD_TYPE_SET_CONFIG",
                            }
                        },
                    },
                    "F": {
                        "description": "fan_speed",
                        "data_type": "fan_speed",
                        "conversion": "val_direct",
                        "commands": {
                            "set_fan_speed": {
                                "type": "CMD_TYPE_SET_CONFIG",
                                "fan_modes": {"low": 15, "medium": 45, "high": 75},
                            }
                        },
                    },
                    "tT": {
                        "description": "target_temperature",
                        "data_type": "temperature",
                        "conversion": "v_field",
                        "device_class": "temperature",
                        "unit_of_measurement": "°C",
                        "commands": {
                            "set_temperature": {
                                "type": "CMD_TYPE_SET_TEMP_DECIMAL",
                            }
                        },
                    },
                    "T": {
                        "description": "temperature",
                        "data_type": "temperature",
                        "conversion": "v_field",
                        "device_class": "temperature",
                        "unit_of_measurement": "°C",
                        "state_class": "measurement",
                    },
                }
            }
        },
        # 核心：climate_config嵌入配置 - 解决HVAC映射冲突
        "climate_config": {
            "template": "standard_hvac",
            "hvac_modes": {
                "io_field": "MODE",
                "modes": {
                    1: "auto",  # Auto自动
                    2: "fan_only",  # Fan 吹风
                    3: "cool",  # Cool 制冷
                    4: "heat",  # Heat 制热
                    5: "dry",  # Dry除湿
                },
            },
            "temperature": {
                "target_io": "tT",
                "current_io": "T",
                "range": [16, 30],
                "precision": 0.1,
                "conversion": {"source": "v"},
            },
            "fan_modes": {
                "io_field": "F",
                "modes": {15: "low", 45: "medium", 75: "high"},  # 低档  # 中档  # 高档
            },
            "power_control": {
                "io_field": "O",
                "on_command": {"type": "CMD_TYPE_ON"},
                "off_command": {"type": "CMD_TYPE_OFF"},
            },
            "capabilities": [
                "heating",
                "cooling",
                "fan_control",
                "dehumidifying",
                "target_temperature",
                "auto_mode",
            ],
        },
        # 设备能力标识
        "capabilities": [
            "climate_control",
            "temperature_monitoring",
            "hvac_mode_control",
            "fan_speed_control",
        ],
        # HA翻译支持
        "translation_keys": {
            "hvac_mode_auto": "自动",
            "hvac_mode_fan_only": "吹风",
            "hvac_mode_cool": "制冷",
            "hvac_mode_heat": "制热",
            "hvac_mode_dry": "除湿",
            "fan_mode_low": "低档",
            "fan_mode_medium": "中档",
            "fan_mode_high": "高档",
        },
    },
    "SL_TR_ACIPM": {
        "name": "新风系统",
        "category": "climate",
        "manufacturer": "lifesmart",
        "model": "SL_TR_ACIPM",
        "_generation": 2,
        "climate_features": {
            "hvac_modes": {
                1: "auto",  # 自动模式
                2: "fan_only",  # 仅送风模式
                3: "cool",  # 制冷模式
                4: "heat",  # 制热模式
            },
            "fan_speeds": {
                1: "low",  # 低速档
                2: "medium",  # 中速档
                3: "high",  # 高速档
            },
        },
        "platforms": {
            "climate": {
                "io_configs": {
                    "P1": {
                        "description": "sl_tr_acipm",
                        "data_type": "hvac_mode",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_mode": {
                                "type": CMD_TYPE_SET_CONFIG,
                            },
                        },
                    },
                    "P2": {
                        "description": "fan_speed",
                        "data_type": "fan_speed",
                        "conversion": "val_direct",
                        "commands": {
                            "set_config": {
                                "type": CMD_TYPE_SET_CONFIG,
                                "fan_modes": {
                                    "low": 1,
                                    "medium": 2,
                                    "high": 3,
                                },
                            },
                        },
                    },
                    "P3": {
                        "description": "set_VOC",
                        "data_type": "voc_concentration",
                        "conversion": "val_div_10",
                        "device_class": "volatile_organic_compounds",
                        "unit_of_measurement": "ppm",
                        "commands": {
                            "set_voc": {
                                "type": CMD_TYPE_SET_CONFIG,
                            },
                        },
                    },
                }
            },
            "sensor": {
                "io_configs": {
                    "P4": {
                        "description": "VOC",
                        "data_type": "voc_concentration",
                        "conversion": "val_div_10",
                        "device_class": "volatile_organic_compounds",
                        "unit_of_measurement": "ppm",
                        "state_class": "measurement",
                    },
                    "P5": {
                        "description": "PM2.5",
                        "data_type": "pm25",
                        "conversion": "v_field",
                        "device_class": "pm25",
                        "unit_of_measurement": "μg/m³",
                        "state_class": "measurement",
                    },
                    "P6": {
                        "description": "temperature",
                        "data_type": "temperature",
                        "conversion": "val_div_10",
                        "device_class": "temperature",
                        "unit_of_measurement": "°C",
                        "state_class": "measurement",
                    },
                }
            },
        },
    },
    "SL_CP_DN": {
        "name": "地暖温控器",
        "climate": {
            "P1": {
                "description": "sl_cp_dn",
                "data_type": "hvac_mode",
                "conversion": "val_direct",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_config": {
                        "type": CMD_TYPE_SET_CONFIG,
                    },
                },
            },
            "P3": {
                "description": "target_temperature",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_SET_CONFIG,
                    },
                },
            },
        },
        "binary_sensor": {
            "P2": {
                "description": "switch",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "device_class": "opening",
            },
        },
        "sensor": {
            "P4": {
                "description": "temperature",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
            "P5": {
                "description": "temperature",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
        },
    },
    "SL_CP_AIR": {
        "name": "风机盘管",
        "category": "climate",
        "manufacturer": "lifesmart",
        "model": "SL_CP_AIR",
        "_generation": 2,
        "climate_features": {
            "hvac_modes": {
                0: "cool",  # 制冷模式
                1: "heat",  # 制热模式
                2: "fan_only",  # 仅送风模式
            },
            "fan_speeds": {
                0: "auto",  # 自动风速
                1: "low",  # 低速档
                2: "medium",  # 中速档
                3: "high",  # 高速档
            },
        },
        "platforms": {
            "climate": {
                "io_configs": {
                    "P1": {
                        "description": "sl_cp_air",
                        "data_type": "hvac_mode",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                            "set_config": {
                                "type": CMD_TYPE_SET_CONFIG,
                            },
                        },
                    },
                    "P4": {
                        "description": "target_temperature",
                        "data_type": "temperature",
                        "conversion": "val_div_10",
                        "device_class": "temperature",
                        "unit_of_measurement": "°C",
                        "commands": {
                            "set_temperature": {
                                "type": CMD_TYPE_SET_CONFIG,
                            },
                        },
                    },
                }
            },
            "binary_sensor": {
                "io_configs": {
                    "P2": {
                        "description": "valve",
                        "data_type": "valve_status",
                        "conversion": "type_bit_0",
                        "device_class": "opening",
                    },
                }
            },
            "sensor": {
                "io_configs": {
                    "P3": {
                        "description": "fan_speed",
                        "data_type": "fan_speed",
                        "conversion": "val_direct",
                    },
                    "P5": {
                        "description": "temperature",
                        "data_type": "temperature",
                        "conversion": "val_div_10",
                        "device_class": "temperature",
                        "unit_of_measurement": "°C",
                        "state_class": "measurement",
                    },
                }
            },
        },
    },
    "SL_UACCB": {
        "name": "空调控制面板",
        "climate": {
            "P1": {
                "description": "switch",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
            "P2": {
                "description": "mode",
                "data_type": "hvac_mode",
                "conversion": "val_direct",
                "commands": {
                    "set_config": {
                        "type": CMD_TYPE_SET_CONFIG,
                    },
                },
            },
            "P3": {
                "description": "target_temperature",
                "data_type": "temperature",
                "conversion": "v_field",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_SET_TEMP_DECIMAL,
                    },
                },
            },
            "P4": {
                "description": "fan_speed",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "commands": {
                    "set_fan_speed": {
                        "type": CMD_TYPE_SET_CONFIG,
                    },
                },
            },
        },
        "sensor": {
            "P6": {
                "description": "temperature",
                "data_type": "temperature",
                "conversion": "v_field",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
        },
    },
    "SL_CP_VL": {
        "name": "温控阀门",
        "climate": {
            "P1": {
                "description": "turn_on_switch",
                "data_type": "hvac_mode",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_config": {
                        "type": CMD_TYPE_SET_CONFIG,
                    },
                },
            },
            "P3": {
                "description": "target_temperature",
                "data_type": "temperature",
                "conversion": "v_field",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_SET_TEMP_DECIMAL,
                    },
                },
            },
        },
        "sensor": {
            "P4": {
                "description": "temperature",
                "data_type": "temperature",
                "conversion": "v_field",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
            "P5": {
                "description": "alarm",
                "data_type": "alarm_status",
                "conversion": "val_direct",
            },
            "P6": {
                "description": "energy",
                "data_type": "battery",
                "conversion": "v_field",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
        "binary_sensor": {
            "P5": {
                "description": "status",
                "data_type": "alarm_status",
                "conversion": "val_direct",
                "device_class": "problem",
            },
        },
    },
    "SL_DN": {
        "name": "星玉地暖",
        "climate": {
            "P1": {
                "description": "switch",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
            "P2": {
                "description": "mode",
                "data_type": "config_bitmask",
                "conversion": "val_direct",
                "commands": {
                    "set_config": {
                        "type": CMD_TYPE_SET_CONFIG,
                    },
                },
            },
            "P8": {
                "description": "target_temperature",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_SET_CONFIG,
                    },
                },
            },
        },
        "binary_sensor": {
            "P3": {
                "description": "valve",
                "data_type": "valve_status",
                "conversion": "type_bit_0",
                "device_class": "opening",
            },
        },
        "sensor": {
            "P4": {
                "description": "temperature",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
            "P9": {
                "description": "temperature",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
        },
    },
    # ================= 2.10 通用控制器系列 (General Controller Series) =================
    # 2.10.1 通用控制器 (General Controller)
    "SL_P": {
        "name": "通用控制器",
        "category": "cover",
        "manufacturer": "lifesmart",
        "model": "SL_P",
        "_generation": 2,
        "dynamic": True,
        "cover_features": {
            "position_feedback": False,
            "optimistic_mode": True,
            # 集成的窗帘控制配置（原NON_POSITIONAL_COVER_CONFIG）
            "control_mapping": {"open": "P2", "close": "P3", "stop": "P4"},
            "control_modes": {
                "free_mode": {
                    "condition": "(P1>>24)&0xe == 0",
                    "binary_sensor": {
                        "P5": {
                            "description": "status",
                            "data_type": "status_input",
                            "conversion": "type_bit_0",
                            "device_class": "moving",
                        },
                        "P6": {
                            "description": "status",
                            "data_type": "status_input",
                            "conversion": "type_bit_0",
                            "device_class": "moving",
                        },
                        "P7": {
                            "description": "status",
                            "data_type": "status_input",
                            "conversion": "type_bit_0",
                            "device_class": "moving",
                        },
                    },
                },
                "cover_mode": {
                    "condition": "(P1>>24)&0xe in [2,4]",
                    "cover": {
                        "P2": {
                            "description": "open_curtain",
                            "data_type": "binary_switch",
                            "conversion": "type_bit_0",
                            "commands": {
                                "open": {
                                    "type": CMD_TYPE_ON,
                                    "val": 1,
                                },
                            },
                        },
                        "P3": {
                            "description": "close_curtain",
                            "data_type": "binary_switch",
                            "conversion": "type_bit_0",
                            "commands": {
                                "close": {
                                    "type": CMD_TYPE_ON,
                                    "val": 1,
                                },
                            },
                        },
                        "P4": {
                            "description": "curtain",
                            "data_type": "binary_switch",
                            "conversion": "type_bit_0",
                            "commands": {
                                "stop": {
                                    "type": CMD_TYPE_ON,
                                    "val": 1,
                                },
                            },
                        },
                    },
                },
                "switch_mode": {
                    "condition": "(P1>>24)&0xe in [8,10]",
                    "switch": {
                        "P2": {
                            "description": "switch",
                            "data_type": "binary_switch",
                            "conversion": "type_bit_0",
                            "commands": {
                                "on": {
                                    "type": CMD_TYPE_ON,
                                    "val": 1,
                                },
                                "off": {
                                    "type": CMD_TYPE_OFF,
                                    "val": 0,
                                },
                            },
                        },
                        "P3": {
                            "description": "switch",
                            "data_type": "binary_switch",
                            "conversion": "type_bit_0",
                            "commands": {
                                "on": {
                                    "type": CMD_TYPE_ON,
                                    "val": 1,
                                },
                                "off": {
                                    "type": CMD_TYPE_OFF,
                                    "val": 0,
                                },
                            },
                        },
                        "P4": {
                            "description": "switch",
                            "data_type": "binary_switch",
                            "conversion": "type_bit_0",
                            "commands": {
                                "on": {
                                    "type": CMD_TYPE_ON,
                                    "val": 1,
                                },
                                "off": {
                                    "type": CMD_TYPE_OFF,
                                    "val": 0,
                                },
                            },
                        },
                    },
                },
            },
        },
        "platforms": {
            "cover": {
                "io_configs": {
                    "P2": {
                        "description": "open_curtain",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "open": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                        },
                    },
                    "P3": {
                        "description": "close_curtain",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "close": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                        },
                    },
                    "P4": {
                        "description": "curtain",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "stop": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                        },
                    },
                }
            },
            "switch": {
                "io_configs": {
                    "P2": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P3": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P4": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                }
            },
            "binary_sensor": {
                "io_configs": {
                    "P5": {
                        "description": "status",
                        "data_type": "status_input",
                        "conversion": "type_bit_0",
                        "device_class": "moving",
                    },
                    "P6": {
                        "description": "status",
                        "data_type": "status_input",
                        "conversion": "type_bit_0",
                        "device_class": "moving",
                    },
                    "P7": {
                        "description": "status",
                        "data_type": "status_input",
                        "conversion": "type_bit_0",
                        "device_class": "moving",
                    },
                }
            },
            "sensor": {
                "io_configs": {
                    "P1": {
                        "description": "control",
                        "data_type": "control_config",
                        "conversion": "val_direct",
                        "commands": {
                            "set_config": {
                                "type": CMD_TYPE_SET_CONFIG,
                            },
                        },
                    },
                }
            },
        },
    },
    # 2.10.2 通用控制器HA (HA Interface Adapter)
    "SL_JEMA": {
        "name": "通用控制器HA",
        "category": "cover",
        "manufacturer": "lifesmart",
        "model": "SL_JEMA",
        "_generation": 2,
        "dynamic": True,
        "cover_features": {
            "position_feedback": False,
            "optimistic_mode": True,
            # 集成的窗帘控制配置（原NON_POSITIONAL_COVER_CONFIG）
            "control_mapping": {"open": "P2", "close": "P3", "stop": "P4"},
            "control_modes": {
                "free_mode": {
                    "condition": "(P1>>24)&0xe == 0",
                    "binary_sensor": {
                        "P5": {
                            "description": "status",
                            "data_type": "status_input",
                            "conversion": "type_bit_0",
                            "device_class": "moving",
                        },
                        "P6": {
                            "description": "status",
                            "data_type": "status_input",
                            "conversion": "type_bit_0",
                            "device_class": "moving",
                        },
                        "P7": {
                            "description": "status",
                            "data_type": "status_input",
                            "conversion": "type_bit_0",
                            "device_class": "moving",
                        },
                    },
                },
                "cover_mode": {
                    "condition": "(P1>>24)&0xe in [2,4]",
                    "cover": {
                        "P2": {
                            "description": "curtain",
                            "data_type": "binary_switch",
                            "conversion": "type_bit_0",
                            "commands": {
                                "open": {
                                    "type": CMD_TYPE_ON,
                                    "val": 1,
                                },
                            },
                        },
                        "P3": {
                            "description": "curtain",
                            "data_type": "binary_switch",
                            "conversion": "type_bit_0",
                            "commands": {
                                "close": {
                                    "type": CMD_TYPE_ON,
                                    "val": 1,
                                },
                            },
                        },
                        "P4": {
                            "description": "curtain",
                            "data_type": "binary_switch",
                            "conversion": "type_bit_0",
                            "commands": {
                                "stop": {
                                    "type": CMD_TYPE_ON,
                                    "val": 1,
                                },
                            },
                        },
                    },
                },
                "switch_mode": {
                    "condition": "(P1>>24)&0xe in [8,10]",
                    "switch": {
                        "P2": {
                            "description": "switch",
                            "data_type": "binary_switch",
                            "conversion": "type_bit_0",
                            "commands": {
                                "on": {
                                    "type": CMD_TYPE_ON,
                                    "val": 1,
                                },
                                "off": {
                                    "type": CMD_TYPE_OFF,
                                    "val": 0,
                                },
                            },
                        },
                        "P3": {
                            "description": "switch",
                            "data_type": "binary_switch",
                            "conversion": "type_bit_0",
                            "commands": {
                                "on": {
                                    "type": CMD_TYPE_ON,
                                    "val": 1,
                                },
                                "off": {
                                    "type": CMD_TYPE_OFF,
                                    "val": 0,
                                },
                            },
                        },
                        "P4": {
                            "description": "switch",
                            "data_type": "binary_switch",
                            "conversion": "type_bit_0",
                            "commands": {
                                "on": {
                                    "type": CMD_TYPE_ON,
                                    "val": 1,
                                },
                                "off": {
                                    "type": CMD_TYPE_OFF,
                                    "val": 0,
                                },
                            },
                        },
                    },
                },
            },
        },
        "platforms": {
            "cover": {
                "io_configs": {
                    "P2": {
                        "description": "curtain",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "open": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                        },
                    },
                    "P3": {
                        "description": "curtain",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "close": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                        },
                    },
                    "P4": {
                        "description": "curtain",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "stop": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                        },
                    },
                }
            },
            "switch": {
                "io_configs": {
                    "P2": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P3": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P4": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P8": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P9": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                    "P10": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                            },
                        },
                    },
                }
            },
            "binary_sensor": {
                "io_configs": {
                    "P5": {
                        "description": "status",
                        "data_type": "status_input",
                        "conversion": "type_bit_0",
                        "device_class": "moving",
                    },
                    "P6": {
                        "description": "status",
                        "data_type": "status_input",
                        "conversion": "type_bit_0",
                        "device_class": "moving",
                    },
                    "P7": {
                        "description": "status",
                        "data_type": "status_input",
                        "conversion": "type_bit_0",
                        "device_class": "moving",
                    },
                }
            },
            "sensor": {
                "io_configs": {
                    "P1": {
                        "description": "control",
                        "data_type": "control_config",
                        "conversion": "val_direct",
                        "commands": {
                            "set_config": {
                                "type": CMD_TYPE_SET_CONFIG,
                            },
                        },
                    },
                }
            },
        },
    },
    # ================= 第三方设备 (Third-party Devices) =================
    "V_DLT645_P": {
        "name": "DLT电量计量器",
        "sensor": {
            "EE": {
                "description": "energy",
                "data_type": "energy_consumption",
                "conversion": "ieee754_or_friendly",
                "unit_of_measurement": "kWh",
                "device_class": "energy",
                "state_class": "total_increasing",
            },
            "EP": {
                "description": "power",
                "data_type": "power",
                "conversion": "ieee754_or_friendly",
                "unit_of_measurement": "W",
                "device_class": "power",
                "state_class": "measurement",
            },
        },
    },
    "V_DUNJIA_P": {
        "name": "X100人脸识别可视门锁",
        "sensor": {
            "BAT": {
                "description": "energy",
                "data_type": "battery",
                "conversion": "val_direct",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "ALM": {
                "description": "alarm",
                "data_type": "alarm_status",
                "conversion": "val_direct",
            },
            "EVTLO": {
                "description": "real_time_unlock",
                "data_type": "lock_event",
                "conversion": "val_direct",
            },
            "HISLK": {
                "description": "last_unlock_info",
                "data_type": "recent_unlock",
                "conversion": "val_direct",
            },
        },
    },
    "V_HG_L": {
        "name": "极速开关组",
        "switch": {
            "L1": {
                "description": "switch_1",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
            "L2": {
                "description": "switch_2",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
            "L3": {
                "description": "switch_3",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
        },
    },
    "V_HG_XX": {
        "name": "极速虚拟设备",
        "switch": {
            "P1": {
                "description": "switch",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
        },
    },
    "V_SZJSXR_P": {
        "name": "新风控制器(深圳建设新风)",
        "climate": {
            "O": {
                "description": "switch",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
            "MODE": {
                "description": "mode",
                "data_type": "hvac_mode",
                "conversion": "val_direct",
                "commands": {
                    "set_mode": {
                        "type": CMD_TYPE_SET_CONFIG,
                    },
                },
            },
            "F": {
                "description": "fan_speed",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "commands": {
                    "set_fan_speed": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "fan_modes": {
                            "low": 15,
                            "medium": 45,
                            "high": 75,
                        },
                    },
                },
            },
            "tT": {
                "description": "target_temperature",
                "data_type": "temperature",
                "conversion": "v_field",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_SET_TEMP_DECIMAL,
                    },
                },
            },
            "T": {
                "description": "temperature",
                "data_type": "temperature",
                "conversion": "v_field",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
        },
    },
    "V_T8600_P": {
        "name": "YORK温控器T8600",
        "climate": {
            "O": {
                "description": "switch",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
            "MODE": {
                "description": "mode",
                "data_type": "hvac_mode",
                "conversion": "val_direct",
                "commands": {
                    "set_mode": {
                        "type": CMD_TYPE_SET_CONFIG,
                    },
                },
            },
            "F": {
                "description": "fan_speed",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "commands": {
                    "set_fan_speed": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "fan_modes": {
                            "low": 15,
                            "medium": 45,
                            "high": 75,
                        },
                    },
                },
            },
            "tT": {
                "description": "target_temperature",
                "data_type": "temperature",
                "conversion": "v_field",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_SET_TEMP_DECIMAL,
                    },
                },
            },
            "T": {
                "description": "temperature",
                "data_type": "temperature",
                "conversion": "v_field",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
        },
    },
    "V_FRESH_P": {
        "name": "艾弗纳KV11新风控制器",
        "switch": {
            "O": {
                "description": "switch",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
            "MODE": {
                "description": "mode",
                "data_type": "mode_config",
                "conversion": "val_direct",
                "commands": {
                    "set_mode": {
                        "type": CMD_TYPE_SET_VAL,
                    },
                },
            },
        },
        "sensor": {
            "F1": {
                "description": "fan_speed",
                "data_type": "fan_speed",
                "conversion": "val_direct",
            },
            "F2": {
                "description": "fan_speed",
                "data_type": "fan_speed",
                "conversion": "val_direct",
            },
            "T": {
                "description": "ambient_temperature",
                "data_type": "temperature",
                "conversion": "v_field",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
        },
    },
    "V_IND_S": {
        "name": "工业传感器",
        "sensor": {
            "P1": {
                "description": "v_ind_s",
                "data_type": "generic_value",
                "conversion": "ieee754_or_friendly",
            },
        },
    },
    "V_485_P": {
        "name": "485控制器",
        "wildcard_support": True,
        "switch": {
            "O": {
                "description": "switch",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
            "L*": {
                "description": "switch",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
        },
        "sensor": {
            "P1": {
                "description": "v_ind_s",
                "data_type": "generic_value",
                "conversion": "ieee754_or_friendly",
            },
            "EE": {
                "description": "energy",
                "data_type": "energy_consumption",
                "conversion": "ieee754_or_friendly",
                "unit_of_measurement": "kWh",
                "device_class": "energy",
                "state_class": "total_increasing",
            },
            "EE*": {
                "description": "electric",
                "data_type": "energy_consumption",
                "conversion": "ieee754_or_friendly",
                "unit_of_measurement": "kWh",
                "device_class": "energy",
                "state_class": "total_increasing",
            },
            "EP": {
                "description": "power",
                "data_type": "power",
                "conversion": "ieee754_or_friendly",
                "unit_of_measurement": "W",
                "device_class": "power",
                "state_class": "measurement",
            },
            "EPF": {
                "description": "power_factor",
                "data_type": "power_factor",
                "conversion": "friendly_value",
                "device_class": "power_factor",
                "state_class": "measurement",
            },
            "EPF*": {
                "description": "power",
                "data_type": "power_factor",
                "conversion": "friendly_value",
                "device_class": "power_factor",
                "state_class": "measurement",
            },
            "EF": {
                "description": "electric",
                "data_type": "frequency",
                "conversion": "friendly_value",
                "unit_of_measurement": "Hz",
                "device_class": "frequency",
                "state_class": "measurement",
            },
            "EF*": {
                "description": "electric",
                "data_type": "frequency",
                "conversion": "friendly_value",
                "unit_of_measurement": "Hz",
                "device_class": "frequency",
                "state_class": "measurement",
            },
            "EI": {
                "description": "current",
                "data_type": "current",
                "conversion": "friendly_value",
                "unit_of_measurement": "A",
                "device_class": "current",
                "state_class": "measurement",
            },
            "EI*": {
                "description": "electric",
                "data_type": "current",
                "conversion": "friendly_value",
                "unit_of_measurement": "A",
                "device_class": "current",
                "state_class": "measurement",
            },
            "EV": {
                "description": "voltage",
                "data_type": "voltage",
                "conversion": "friendly_value",
                "unit_of_measurement": "V",
                "device_class": "voltage",
                "state_class": "measurement",
            },
            "EV*": {
                "description": "electric",
                "data_type": "voltage",
                "conversion": "friendly_value",
                "unit_of_measurement": "V",
                "device_class": "voltage",
                "state_class": "measurement",
            },
            "T": {
                "description": "temperature",
                "data_type": "temperature",
                "conversion": "friendly_value",
                "unit_of_measurement": "°C",
                "device_class": "temperature",
                "state_class": "measurement",
            },
            "H": {
                "description": "humidity",
                "data_type": "humidity",
                "conversion": "friendly_value",
                "unit_of_measurement": "%",
                "device_class": "humidity",
                "state_class": "measurement",
            },
            "PM": {
                "description": "PM2.5",
                "data_type": "pm25",
                "conversion": "friendly_value",
                "unit_of_measurement": "µg/m³",
                "device_class": "pm25",
                "state_class": "measurement",
            },
            "PMx": {
                "description": "PM10",
                "data_type": "pm10",
                "conversion": "friendly_value",
                "unit_of_measurement": "µg/m³",
                "device_class": "pm10",
                "state_class": "measurement",
            },
            "COPPM": {
                "description": "coppm",
                "data_type": "co_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "ppm",
                "device_class": "carbon_monoxide",
                "state_class": "measurement",
            },
            "CO2PPM": {
                "description": "coppm",
                "data_type": "co2_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "ppm",
                "device_class": "carbon_dioxide",
                "state_class": "measurement",
            },
            "CH20PPM": {
                "description": "coppm",
                "data_type": "formaldehyde_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "ppm",
                "device_class": "volatile_organic_compounds",
                "state_class": "measurement",
            },
            "O2VOL": {
                "description": "coppm",
                "data_type": "oxygen_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "vol%",
                "state_class": "measurement",
            },
            "NH3PPM": {
                "description": "coppm",
                "data_type": "ammonia_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "ppm",
                "state_class": "measurement",
            },
            "H2SPPM": {
                "description": "coppm",
                "data_type": "h2s_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "ppm",
                "state_class": "measurement",
            },
            "TVOC": {
                "description": "TVOC",
                "data_type": "tvoc_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "mg/m³",
                "device_class": "volatile_organic_compounds",
                "state_class": "measurement",
            },
            "PHM": {
                "description": "co2ppm",
                "data_type": "noise_level",
                "conversion": "friendly_value",
                "unit_of_measurement": "dB",
                "device_class": "sound_pressure",
                "state_class": "measurement",
            },
            "SMOKE": {
                "description": "ch20ppm",
                "data_type": "smoke_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "ppm",
                "state_class": "measurement",
            },
        },
    },
    # ================= 2.11 摄像头系列 (Camera Series) =================
    # 基于官方文档2.13摄像头系列规格
    # 基础设备类型: cam，通过dev_rt属性区分具体型号
    "LSSSMINIV1": {
        "name": "红外夜灯",
        "light": {
            "P1": {
                "description": "control",
                "data_type": "infrared_light",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
        },
        "binary_sensor": {
            "P2": {
                "description": "motion",
                "data_type": "motion_status",
                "conversion": "val_direct",
                "device_class": "motion",
            },
        },
        "sensor": {
            "P3": {
                "description": "illuminance",
                "data_type": "illuminance",
                "conversion": "v_field",
                "device_class": "illuminance",
                "unit_of_measurement": "lx",
                "state_class": "measurement",
            },
            "P4": {
                "description": "energy",
                "data_type": "battery",
                "conversion": "v_field",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    "SL_DF_KP": {
        "name": "云防键盘",
        "binary_sensor": {
            "KY": {
                "description": "button",
                "data_type": "keypad_status",
                "conversion": "val_direct",
                "device_class": "moving",
            },
            "TR": {
                "description": "tamper",
                "data_type": "tamper_status",
                "conversion": "type_bit_0",
                "device_class": "tamper",
            },
        },
        "sensor": {
            "T": {
                "description": "temperature",
                "data_type": "temperature",
                "conversion": "v_field",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
            "V": {
                "description": "energy",
                "data_type": "battery",
                "conversion": "v_field",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    "cam": {
        "name": "摄像头",
        "camera": {
            "stream": {
                "description": "camera_stream",
                "data_type": "camera_stream",
                "conversion": "camera_url",
            }
        },
        "dev_rt_variants": {
            "LSCAM:LSCAMV1": {
                "name": "FRAME摄像头",
                "supported_ios": ["M", "V", "CFST"],
            },
            "LSCAM:LSICAMEZ1": {
                "name": "户外摄像头",
                "supported_ios": ["M"],
            },
            "LSCAM:LSICAMEZ2": {
                "name": "户外摄像头",
                "supported_ios": ["M"],
            },
            "LSCAM:LSLKCAMV1": {
                "name": "视频门锁摄像头",
                "supported_ios": ["M"],
            },
            "LSCAM:LSICAMGOS1": {
                "name": "高清摄像头",
                "supported_ios": ["M"],
                "model_key_support": {
                    "0xd2": "高清摄像头",
                    "0xda": "云视户外摄像头",
                    "0xdb": "云瞳室内摄像头",
                    "0xdc": "云瞳室外摄像头",
                },
            },
        },
        "binary_sensor": {
            "M": {
                "description": "motion",
                "data_type": "motion_detection",
                "conversion": "val_direct",
                "device_class": "motion",
            },
        },
        "sensor": {
            "V": {
                "description": "voltage",
                "data_type": "battery",
                "conversion": "v_field",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
                "availability_condition": "dev_rt == 'LSCAM:LSCAMV1'",
            },
            "CFST": {
                "description": "status",
                "data_type": "camera_status",
                "conversion": "val_direct",
                "availability_condition": "dev_rt == 'LSCAM:LSCAMV1'",
            },
        },
    },
    # ================= 2.12 车库门控制 (Garage Door Control) =================
    "SL_ETDOOR": {
        "name": "车库门控制器",
        "light": {
            "P1": {
                "description": "control",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                },
            },
        },
        "cover": {
            "P2": {
                "description": "status",
                "data_type": "garage_door_status",
                "conversion": "val_direct",
            },
            "P3": {
                "description": "control",
                "data_type": "garage_door_control",
                "conversion": "val_direct",
                "commands": {
                    "open": {
                        "type": CMD_TYPE_SET_VAL,
                        "val": 100,
                    },
                    "close": {
                        "type": CMD_TYPE_SET_VAL,
                        "val": 0,
                    },
                    "stop": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "val": 128,
                    },
                    "set_position": {
                        "type": CMD_TYPE_SET_VAL,
                    },
                },
            },
        },
    },
    # ================= 2.13 智能报警器(CoSS版) (Smart Alarm CoSS) =================
    # 基于官方文档2.12 智能报警器（CoSS版）规格
    "SL_ALM": {
        "name": "智能报警器(CoSS版)",
        "switch": {
            "P1": {
                "description": "control",
                "data_type": "alarm_playback",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_config_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                    },
                    "set_config_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                    },
                },
            },
            "P2": {
                "description": "control",
                "data_type": "volume_control",
                "conversion": "type_bit_0",
                "commands": {
                    "unmute": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                    },
                    "mute": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                    },
                    "set_volume": {
                        "type": CMD_TYPE_SET_CONFIG,
                    },
                },
            },
        },
    },
    # ================= 超能面板设备 (NATURE Series Devices) =================
    # 基于官方文档2.14 超能面板系列（NATURE Series)
    # 注意：这是动态分类设备，根据P5值决定是开关版还是温控版
    "SL_NATURE": {
        "dynamic": True,
        "switch_mode": {
            "condition": "P5&0xFF==1",
            "io": ["P1", "P2", "P3"],
            "sensor_io": ["P4", "P5"],
        },
        "climate_mode": {
            "condition": "P5&0xFF in [3,6]",
            "climate": {
                "P1": {
                    "description": "switch",
                    "data_type": "binary_switch",
                    "conversion": "type_bit_0",
                    "commands": {
                        "on": {
                            "type": CMD_TYPE_ON,
                            "val": 1,
                        },
                        "off": {
                            "type": CMD_TYPE_OFF,
                            "val": 0,
                        },
                    },
                },
                "P4": {
                    "description": "temperature",
                    "data_type": "temperature",
                    "conversion": "v_field",
                    "device_class": "temperature",
                    "unit_of_measurement": "°C",
                    "state_class": "measurement",
                },
                "P5": {
                    "description": "switch",
                    "data_type": "device_type",
                    "conversion": "val_direct",
                },
                "P6": {
                    "description": "switch",
                    "data_type": "config_bitmask",
                    "conversion": "val_direct",
                    "commands": {
                        "set_config": {
                            "type": CMD_TYPE_SET_RAW_ON,
                        },
                    },
                },
                "P7": {
                    "description": "mode",
                    "data_type": "hvac_mode",
                    "conversion": "val_direct",
                    "commands": {
                        "set_config": {
                            "type": CMD_TYPE_SET_CONFIG,
                        },
                    },
                },
                "P8": {
                    "description": "target_temperature",
                    "data_type": "temperature",
                    "conversion": "v_field",
                    "device_class": "temperature",
                    "unit_of_measurement": "°C",
                    "commands": {
                        "set_temperature": {
                            "type": CMD_TYPE_SET_TEMP_DECIMAL,
                        },
                    },
                },
                "P9": {
                    "description": "target_fan_speed",
                    "data_type": "fan_speed",
                    "conversion": "val_direct",
                    "commands": {
                        "set_config": {
                            "type": CMD_TYPE_SET_CONFIG,
                            "fan_modes": {
                                "low": 25,
                                "medium": 50,
                                "high": 75,
                                "auto": 101,
                            },
                        },
                    },
                },
                "P10": {
                    "description": "fan_speed",
                    "data_type": "fan_speed",
                    "conversion": "val_direct",
                },
            },
            "binary_sensor": {
                "P2": {
                    "description": "valve",
                    "data_type": "valve_status",
                    "conversion": "val_direct",
                    "device_class": "opening",
                },
                "P3": {
                    "description": "valve",
                    "data_type": "valve_status",
                    "conversion": "val_direct",
                    "device_class": "opening",
                },
            },
        },
    },
    # ================= 2.14 智能面板系列 (Smart Panel Series) =================
    # 2.14.4 星玉温控面板 (Nature Thermostat)
    "SL_FCU": {
        "name": "星玉温控面板",
        "category": "climate",
        "manufacturer": "lifesmart",
        "model": "SL_FCU",
        "_generation": 2,  # DEVICE_CENTRIC_CONFIG格式标识
        # 基础平台配置
        "platforms": {
            "climate": {
                "io_configs": {
                    "P1": {
                        "description": "switch",
                        "data_type": "binary_switch",
                        "conversion": "val_direct",
                        "commands": {
                            "on": {
                                "type": "CMD_TYPE_ON",
                                "val": 1,
                            },
                            "off": {
                                "type": "CMD_TYPE_OFF",
                                "val": 0,
                            },
                        },
                    },
                    "P7": {
                        "description": "mode",
                        "data_type": "hvac_mode",
                        "conversion": "val_direct",
                        "commands": {
                            "set_config": {
                                "type": "CMD_TYPE_SET_VAL",
                            }
                        },
                    },
                    "P8": {
                        "description": "target_temperature",
                        "data_type": "temperature",
                        "conversion": "v_field",
                        "unit_of_measurement": "°C",
                        "commands": {
                            "set_temperature": {
                                "type": "CMD_TYPE_SET_TEMP_FCU",
                            }
                        },
                    },
                    "P9": {
                        "description": "target_fan_speed",
                        "data_type": "fan_speed",
                        "conversion": "val_direct",
                        "commands": {
                            "set_config": {
                                "type": "CMD_TYPE_SET_CONFIG",
                                "fan_modes": {
                                    "low": 15,
                                    "medium": 45,
                                    "high": 75,
                                    "auto": 101,
                                },
                            }
                        },
                    },
                }
            },
            "sensor": {
                "io_configs": {
                    "P4": {
                        "description": "temperature",
                        "data_type": "temperature",
                        "conversion": "v_field",
                        "device_class": "temperature",
                        "unit_of_measurement": "°C",
                    },
                    "P10": {
                        "description": "fan_speed",
                        "data_type": "fan_speed",
                        "conversion": "val_direct",
                    },
                }
            },
            "binary_sensor": {
                "io_configs": {
                    "P2": {
                        "description": "valve",
                        "data_type": "valve_status",
                        "conversion": "val_direct",
                        "device_class": "opening",
                    },
                    "P3": {
                        "description": "valve",
                        "data_type": "valve_status",
                        "conversion": "val_direct",
                        "device_class": "opening",
                    },
                }
            },
        },
        # 核心：P6 bitmask_config嵌入配置 - 解决功能缺失
        "bitmask_config": {
            "P6": {
                "type": "multi_bit_switch",
                "virtual_device_template": "SL_FCU_P6_{name}",
                "bit_definitions": {
                    0: {
                        "name": "hot_water",
                        "platform": "switch",
                        "description": "hot_water_switch",
                        "translation_key": "hot_water_switch",
                        "commands": {
                            "on": {
                                "type": "CMD_TYPE_SET_CFG_FCU",
                                "bit_position": 0,
                                "bit_value": 1,
                            },
                            "off": {
                                "type": "CMD_TYPE_SET_CFG_FCU",
                                "bit_position": 0,
                                "bit_value": 0,
                            },
                        },
                    },
                    1: {
                        "name": "floor_heating",
                        "platform": "switch",
                        "description": "floor_heating_switch",
                        "translation_key": "floor_heating_switch",
                        "commands": {
                            "on": {
                                "type": "CMD_TYPE_SET_CFG_FCU",
                                "bit_position": 1,
                                "bit_value": 1,
                            },
                            "off": {
                                "type": "CMD_TYPE_SET_CFG_FCU",
                                "bit_position": 1,
                                "bit_value": 0,
                            },
                        },
                    },
                    2: {
                        "name": "heating",
                        "platform": "switch",
                        "description": "heating_switch",
                        "translation_key": "heating_switch",
                        "commands": {
                            "on": {
                                "type": "CMD_TYPE_SET_CFG_FCU",
                                "bit_position": 2,
                                "bit_value": 1,
                            },
                            "off": {
                                "type": "CMD_TYPE_SET_CFG_FCU",
                                "bit_position": 2,
                                "bit_value": 0,
                            },
                        },
                    },
                    3: {
                        "name": "cooling",
                        "platform": "switch",
                        "description": "cooling_switch",
                        "translation_key": "cooling_switch",
                        "commands": {
                            "on": {
                                "type": "CMD_TYPE_SET_CFG_FCU",
                                "bit_position": 3,
                                "bit_value": 1,
                            },
                            "off": {
                                "type": "CMD_TYPE_SET_CFG_FCU",
                                "bit_position": 3,
                                "bit_value": 0,
                            },
                        },
                    },
                    4: {
                        "name": "ventilation",
                        "platform": "switch",
                        "description": "switch",
                        "translation_key": "ventilation_switch",
                        "commands": {
                            "on": {
                                "type": "CMD_TYPE_SET_CFG_FCU",
                                "bit_position": 4,
                                "bit_value": 1,
                            },
                            "off": {
                                "type": "CMD_TYPE_SET_CFG_FCU",
                                "bit_position": 4,
                                "bit_value": 0,
                            },
                        },
                    },
                    5: {
                        "name": "dehumidify",
                        "platform": "switch",
                        "description": "switch",
                        "translation_key": "dehumidify_switch",
                        "commands": {
                            "on": {
                                "type": "CMD_TYPE_SET_CFG_FCU",
                                "bit_position": 5,
                                "bit_value": 1,
                            },
                            "off": {
                                "type": "CMD_TYPE_SET_CFG_FCU",
                                "bit_position": 5,
                                "bit_value": 0,
                            },
                        },
                    },
                    6: {
                        "name": "humidify",
                        "platform": "switch",
                        "description": "switch",
                        "translation_key": "humidify_switch",
                        "commands": {
                            "on": {
                                "type": "CMD_TYPE_SET_CFG_FCU",
                                "bit_position": 6,
                                "bit_value": 1,
                            },
                            "off": {
                                "type": "CMD_TYPE_SET_CFG_FCU",
                                "bit_position": 6,
                                "bit_value": 0,
                            },
                        },
                    },
                    7: {
                        "name": "emergency_ventilation",
                        "platform": "switch",
                        "description": "switch",
                        "translation_key": "emergency_ventilation_switch",
                        "commands": {
                            "on": {
                                "type": "CMD_TYPE_SET_CFG_FCU",
                                "bit_position": 7,
                                "bit_value": 1,
                            },
                            "off": {
                                "type": "CMD_TYPE_SET_CFG_FCU",
                                "bit_position": 7,
                                "bit_value": 0,
                            },
                        },
                    },
                    8: {
                        "name": "emergency_heating",
                        "platform": "switch",
                        "description": "switch",
                        "translation_key": "emergency_heating_switch",
                        "commands": {
                            "on": {
                                "type": "CMD_TYPE_SET_CFG_FCU",
                                "bit_position": 8,
                                "bit_value": 1,
                            },
                            "off": {
                                "type": "CMD_TYPE_SET_CFG_FCU",
                                "bit_position": 8,
                                "bit_value": 0,
                            },
                        },
                    },
                    9: {
                        "name": "emergency_cooling",
                        "platform": "switch",
                        "description": "switch",
                        "translation_key": "emergency_cooling_switch",
                        "commands": {
                            "on": {
                                "type": "CMD_TYPE_SET_CFG_FCU",
                                "bit_position": 9,
                                "bit_value": 1,
                            },
                            "off": {
                                "type": "CMD_TYPE_SET_CFG_FCU",
                                "bit_position": 9,
                                "bit_value": 0,
                            },
                        },
                    },
                },
            }
        },
        # 核心：climate_config嵌入配置 - 解决HVAC映射冲突
        "climate_config": {
            "template": "advanced_hvac",
            "hvac_modes": {
                "io_field": "P7",
                "modes": {
                    1: "heat",  # 制热
                    2: "cool",  # 制冷
                    3: "fan_only",  # 通风
                    4: "dry",  # 除湿
                    5: "dry",  # 加湿 (HA中合并到dry模式)
                    6: "fan_only",  # 应急通风 (合并到fan_only)
                    7: "heat",  # 应急加热 (合并到heat)
                    8: "cool",  # 应急制冷 (合并到cool)
                    16: "auto",  # 自动
                },
            },
            "temperature": {
                "target_io": "P8",
                "current_io": "P4",
                "range": [5, 35],
                "precision": 0.1,
                "conversion": {"source": "v"},
            },
            "fan_modes": {
                "io_field": "P9",
                "modes": {
                    15: "low",  # 低档
                    45: "medium",  # 中档
                    75: "high",  # 高档
                    101: "auto",  # 自动
                },
            },
            "capabilities": [
                "heating",
                "cooling",
                "fan_control",
                "dehumidifying",
                "target_temperature",
            ],
        },
        # 设备能力标识
        "capabilities": [
            "climate_control",
            "bitmask_switch_control",
            "temperature_monitoring",
            "valve_monitoring",
        ],
        # HA翻译支持
        "translation_keys": {
            "hot_water_switch": "热回水开关",
            "floor_heating_switch": "地暖开关",
            "heating_switch": "制热开关",
            "cooling_switch": "制冷开关",
            "ventilation_switch": "通风开关",
            "dehumidify_switch": "除湿开关",
            "humidify_switch": "加湿开关",
            "emergency_ventilation_switch": "应急通风开关",
            "emergency_heating_switch": "应急加热开关",
            "emergency_cooling_switch": "应急制冷开关",
        },
    },
}


# 导出设备数据供外部使用
def get_device_data(device_id: str) -> Dict[str, Any]:
    """获取指定设备的数据"""
    return _RAW_DEVICE_DATA.get(device_id, {})


def get_all_device_ids() -> list:
    """获取所有设备ID列表"""
    return list(_RAW_DEVICE_DATA.keys())


# ================= 测试设备配置 =================
# 仅用于测试环境的虚拟设备配置
_RAW_DEVICE_DATA["VIRTUAL_TEST"] = {
    "name": "虚拟测试设备",
    "sensor": {
        "TEST": {
            "description": "hs",
            "data_type": "generic",
            "conversion": "val_field",
            "state_class": "measurement",
        },
    },
}


def get_device_count() -> int:
    """获取设备总数"""
    return len(_RAW_DEVICE_DATA)


# [MIGRATION COMPLETED 2025-08-17]
# All external mappings have been integrated directly into device configurations
# following DEVICE_CENTRIC_CONFIG architecture. External mappings removed to
# eliminate redundancy and achieve "全部集成进入最大的设备字典，而不在外面"
#
# Integrated mappings:
# - NON_POSITIONAL_COVER_CONFIG → 5 cover devices (SL_P_V2, SL_CN_IF, SL_CN_FE, SL_P, SL_JEMA)
# - HVAC mode mappings → 2 climate devices (SL_TR_ACIPM, SL_CP_AIR)
# - Fan speed mappings → 2 devices (SL_TR_ACIPM, SL_CP_AIR)
# - Bitmask configurations → 10 lock devices (all ALM and EVTLO configs)

# 导出设备数据和配置供外部使用
DEVICE_SPECS_DATA = _RAW_DEVICE_DATA
