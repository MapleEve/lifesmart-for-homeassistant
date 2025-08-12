"""
LifeSmart 设备规格纯数据层 - (125 个设备)
由 @MapleEve 初始创建和维护

此文件包含所有设备的规格数据，已转换为纯Python数据结构。
所有HA常量已清理为纯字符串格式，实现数据层的完全独立。

设备按照官方文档 "LifeSmart 智慧设备规格属性说明.md" 的章节顺序排列：
2.1 插座系列 → 2.2 开关系列 → 2.3 窗帘控制 → 2.4 灯光系列 → ... → 2.14 超能面板
"""

from typing import Dict, Any

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
        "switch": {
            "O": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
    },
    "SL_OL_3C": {
        "name": "智慧插座",
        "switch": {
            "O": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
    },
    "SL_OL_DE": {
        "name": "德标插座",
        "switch": {
            "O": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
    },
    "SL_OL_UK": {
        "name": "英标插座",
        "switch": {
            "O": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
    },
    "SL_OL_UL": {
        "name": "美标插座",
        "switch": {
            "O": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
    },
    "OD_WE_OT1": {
        "name": "Wi-Fi插座",
        "switch": {
            "P1": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
    },
    # 2.1.2 计量插座系列 (Energy Monitoring Outlet Series)
    "SL_OE_3C": {
        "name": "计量插座",
        "switch": {
            "P1": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "sensor": {
            "P2": {
                "description": "用电量",
                "rw": "R",
                "data_type": "energy",
                "conversion": "ieee754_float",
                "detailed_description": (
                    "为累计用电量，`val` 值为 `IEEE754` 浮点数的32位整数表示，"
                    "`v` 值为浮点数，单位为度(kwh)"
                ),
                "device_class": "energy",
                "unit_of_measurement": "kWh",
                "state_class": "total_increasing",
            },
            "P3": {
                "description": "功率",
                "rw": "R",
                "data_type": "power",
                "conversion": "ieee754_float",
                "detailed_description": "为当前负载功率，`v` 值为浮点数，单位为w",
                "device_class": "power",
                "unit_of_measurement": "W",
                "state_class": "measurement",
            },
        },
        "switch_extra": {
            "P4": {
                "description": "功率门限",
                "rw": "RW",
                "data_type": "power_threshold",
                "conversion": "val_direct",
                "detailed_description": (
                    "功率门限，用电保护，值为整数，超出门限则会断电，单位为w"
                ),
                "commands": {
                    "enable": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "使能",
                    },
                    "disable": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "不使能",
                    },
                    "set_threshold_enable": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "使能并且设置门限",
                    },
                    "set_threshold_disable": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "不使能并且设置门限",
                    },
                },
            },
        },
    },
    "SL_OE_DE": {
        "name": "计量插座德标",
        "switch": {
            "P1": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "sensor": {
            "P2": {
                "description": "用电量",
                "rw": "R",
                "data_type": "energy",
                "conversion": "ieee754_float",
                "detailed_description": (
                    "为累计用电量，`val` 值为 `IEEE754` 浮点数的32位整数表示，"
                    "`v` 值为浮点数，单位为度(kwh)"
                ),
                "device_class": "energy",
                "unit_of_measurement": "kWh",
                "state_class": "total_increasing",
            },
            "P3": {
                "description": "功率",
                "rw": "R",
                "data_type": "power",
                "conversion": "ieee754_float",
                "detailed_description": "为当前负载功率，`v` 值为浮点数，单位为w",
                "device_class": "power",
                "unit_of_measurement": "W",
                "state_class": "measurement",
            },
        },
        "switch_extra": {
            "P4": {
                "description": "功率门限",
                "rw": "RW",
                "data_type": "power_threshold",
                "conversion": "val_direct",
                "detailed_description": (
                    "功率门限，用电保护，值为整数，超出门限则会断电，单位为w"
                ),
                "commands": {
                    "enable": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "使能",
                    },
                    "disable": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "不使能",
                    },
                    "set_threshold_enable": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "使能并且设置门限",
                    },
                    "set_threshold_disable": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "不使能并且设置门限",
                    },
                },
            },
        },
    },
    "SL_OE_W": {
        "name": "入墙插座",
        "switch": {
            "P1": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "sensor": {
            "P2": {
                "description": "用电量",
                "rw": "R",
                "data_type": "energy",
                "conversion": "ieee754_float",
                "detailed_description": (
                    "为累计用电量，`val` 值为 `IEEE754` 浮点数的32位整数表示，"
                    "`v` 值为浮点数，单位为度(kwh)"
                ),
                "device_class": "energy",
                "unit_of_measurement": "kWh",
                "state_class": "total_increasing",
            },
            "P3": {
                "description": "功率",
                "rw": "R",
                "data_type": "power",
                "conversion": "ieee754_float",
                "detailed_description": "为当前负载功率，`v` 值为浮点数，单位为w",
                "device_class": "power",
                "unit_of_measurement": "W",
                "state_class": "measurement",
            },
        },
        "switch_extra": {
            "P4": {
                "description": "功率门限",
                "rw": "RW",
                "data_type": "power_threshold",
                "conversion": "val_direct",
                "detailed_description": (
                    "功率门限，用电保护，值为整数，超出门限则会断电，单位为w"
                ),
                "commands": {
                    "enable": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "使能",
                    },
                    "disable": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "不使能",
                    },
                    "set_threshold_enable": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "使能并且设置门限",
                    },
                    "set_threshold_disable": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "不使能并且设置门限",
                    },
                },
            },
        },
    },
    # ================= 2.2 开关系列 (Switch Series) =================
    # 2.2.1 随心开关系列 (Freestyle Switch Series)
    "SL_SW_RC1": {
        "name": "随心开关一位",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "indicator_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，取值范围：0~1023"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_brightness_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯设置亮度",
                    },
                    "set_brightness_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯设置亮度",
                    },
                },
            },
            "bright": {
                "description": "开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "indicator_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，取值范围：0~1023"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_brightness_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯设置亮度",
                    },
                    "set_brightness_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯设置亮度",
                    },
                },
            },
        },
    },
    "SL_SW_RC2": {
        "name": "流光开关二键",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    "SL_SW_RC3": {
        "name": "流光开关三键",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L3": {
                "description": "第三路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark3": {
                "description": "第三路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright3": {
                "description": "第三路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    # 2.2.1 传统开关系列补充 (Traditional Switch Series Supplement)
    "SL_SF_RC": {
        "name": "单火触摸开关",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L3": {
                "description": "第三路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "indicator_light",
                "conversion": "val_direct",
                "range": "0-1023",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，取值范围：0~1023"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_brightness_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置亮度值",
                    },
                    "set_brightness_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置亮度值",
                    },
                },
            },
            "bright": {
                "description": "开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "indicator_light",
                "conversion": "val_direct",
                "range": "0-1023",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，取值范围：0~1023"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_brightness_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置亮度值",
                    },
                    "set_brightness_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置亮度值",
                    },
                },
            },
        },
    },
    "SL_SW_RC": {
        "name": "触摸开关/极星开关(零火版)",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L3": {
                "description": "第三路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "indicator_light",
                "conversion": "val_direct",
                "range": "0-1023",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，取值范围：0~1023"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_brightness_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置亮度值",
                    },
                    "set_brightness_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置亮度值",
                    },
                },
            },
            "bright": {
                "description": "开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "indicator_light",
                "conversion": "val_direct",
                "range": "0-1023",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，取值范围：0~1023"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_brightness_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置亮度值",
                    },
                    "set_brightness_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置亮度值",
                    },
                },
            },
        },
    },
    "SL_SW_IF3": {
        "name": "流光开关三键",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L3": {
                "description": "第三路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark3": {
                "description": "第三路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright3": {
                "description": "第三路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    "SL_SF_IF3": {
        "name": "单火流光开关三键",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L3": {
                "description": "第三路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark3": {
                "description": "第三路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright3": {
                "description": "第三路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    "SL_SW_CP3": {
        "name": "橙朴开关三键",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L3": {
                "description": "第三路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark3": {
                "description": "第三路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright3": {
                "description": "第三路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    "SL_SW_IF2": {
        "name": "零火流光开关二键",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    "SL_SF_IF2": {
        "name": "单火流光开关二键",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    "SL_SW_CP2": {
        "name": "橙朴开关二键",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    "SL_SW_FE2": {
        "name": "塞纳开关二键",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    "SL_SW_IF1": {
        "name": "零火流光开关单键",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright": {
                "description": "开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    "SL_SF_IF1": {
        "name": "单火流光开关单键",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright": {
                "description": "开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    "SL_SW_CP1": {
        "name": "橙朴开关单键",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright": {
                "description": "开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    "SL_SW_FE1": {
        "name": "塞纳开关单键",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright": {
                "description": "开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    "SL_OL_W": {
        "name": "智慧插座开关版",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright": {
                "description": "开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    # 2.2.2 恒星/辰星/极星开关系列 (Star Series Switch)
    "SL_SW_ND1": {
        "name": "恒星开关一键",
        "switch": {
            "P1": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "sensor": {
            "P2": {
                "description": "当前环境温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始温度值，它是温度值*10，`v` 值表示实际值(单位：℃)",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
        },
    },
    "SL_SW_ND2": {
        "name": "恒星开关二键",
        "switch": {
            "P1": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P2": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "sensor": {
            "P3": {
                "description": "当前环境温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始温度值，它是温度值*10，`v` 值表示实际值(单位：℃)",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
        },
    },
    "SL_SW_ND3": {
        "name": "恒星开关三键",
        "switch": {
            "P1": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P2": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P3": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "sensor": {
            "P4": {
                "description": "当前环境温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始温度值，它是温度值*10，`v` 值表示实际值(单位：℃)",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
        },
    },
    "SL_MC_ND1": {
        "name": "恒星/辰星开关伴侣一键",
        "switch": {
            "P1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "sensor": {
            "P2": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据 `val` 电压值换算的"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    "SL_MC_ND2": {
        "name": "恒星/辰星开关伴侣二键",
        "switch": {
            "P1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "sensor": {
            "P3": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据 `val` 电压值换算的"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    "SL_MC_ND3": {
        "name": "恒星/辰星开关伴侣三键",
        "switch": {
            "P1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P3": {
                "description": "第三路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "sensor": {
            "P4": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据 `val` 电压值换算的"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    # 2.2.3 开关控制器系列 (Switch Controller Series)
    "SL_S": {
        "name": "单路开关控制器",
        "switch": {
            "P2": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "-",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
    },
    "SL_SPWM": {
        "name": "PWM调光开关控制器",
        "light": {
            "P1": {
                "description": "可调亮度灯光",
                "rw": "RW",
                "data_type": "brightness_light",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "type&1==1 表示处于打开状态；"
                    "type&1==0 表示处于关闭状态；"
                    "val 值为亮度值，可调范围：[0-255]，值越大表示光越亮，0处于最暗，光完全熄灭，255处于最亮"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                    "set_brightness_on": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "打开并且设置亮度，val=亮度值[0,255]",
                    },
                    "set_brightness_off": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "关闭并设置亮度，val=亮度值[0,255]",
                    },
                },
            },
        },
    },
    "SL_P_SW": {
        "name": "九路开关控制器",
        "switch": {
            "P1": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P2": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P3": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P4": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P5": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P6": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P7": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P8": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P9": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
    },
    # 2.2.4 随心开关按钮系列 (Button Switch Series)
    "SL_SC_BB": {
        "name": "随心开关",
        "button": {
            "B": {
                "description": "按键状态",
                "rw": "R",
                "data_type": "button_state",
                "conversion": "val_direct",
                "detailed_description": "`val` 的值定义如下：- 0：未按下按键 - 1：按下按键",
                "device_class": "identify",
            },
        },
        "sensor": {
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值 `v` 值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据 `val` 电压值换算的"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
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
                        "description": "开关",
                        "rw": "RW",
                        "data_type": "brightness_light",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "detailed_description": (
                            "`type&1==1`表示处于打开状态；"
                            "`type&1==0`表示处于关闭状态；"
                            "`val` 值为亮度值，可调范围：[0,255], 值越大表示光越亮，0处于最暗，光完全熄灭，255处于最亮"
                        ),
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                            "set_brightness_on": {
                                "type": CMD_TYPE_SET_VAL,
                                "description": "打开并且设置亮度，val=亮度值[0,255]",
                            },
                            "set_brightness_off": {
                                "type": CMD_TYPE_UNKNOWN_206,
                                "description": "关闭并设置亮度，val=亮度值[0,255]",
                            },
                        },
                    },
                    "P2": {
                        "description": "指示灯",
                        "rw": "RW",
                        "data_type": "indicator_light",
                        "conversion": "val_direct",
                        "detailed_description": (
                            "`type&1==1`表示处于打开状态；"
                            "`type&1==0`表示处于关闭状态；"
                            "`val` 值为亮度值，它有灯光处于打开状态下的指示灯亮度和"
                            "灯光处于关闭状态下的指示灯亮度。`bit8-bit15`：用于指示"
                            "灯光处于打开状态下的指示灯亮度 `bit0-bit7`：用于指示"
                            "灯光处于关闭状态下的指示灯亮度 每8个bit可调范围：[0,255], "
                            "值越大表示光越亮，0处于最暗，光完全熄灭，255处于最亮。"
                        ),
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                            "set_brightness": {
                                "type": CMD_TYPE_UNKNOWN_223,
                                "description": "设置亮度，val=亮度值[0,65535]",
                            },
                        },
                    },
                },
                "binary_sensor": {
                    "P3": {
                        "description": "移动检测",
                        "rw": "R",
                        "data_type": "motion_status",
                        "conversion": "val_direct",
                        "detailed_description": "`val` 值定义如下：0：没有检测到移动 1：有检测到移动",
                        "device_class": "motion",
                    },
                },
                "sensor": {
                    "P4": {
                        "description": "环境光照",
                        "rw": "R",
                        "data_type": "illuminance",
                        "conversion": "val_direct",
                        "detailed_description": "`val` 值表示原始光照值(单位：lux)",
                        "device_class": "illuminance",
                        "unit_of_measurement": "lx",
                        "state_class": "measurement",
                    },
                    "P5": {
                        "description": "调光设置",
                        "rw": "RW",
                        "data_type": "dimming_config",
                        "conversion": "val_direct",
                        "detailed_description": "当前调光设置值",
                        "commands": {
                            "set_config": {
                                "type": CMD_TYPE_UNKNOWN_206,
                                "description": "设置调光参数配置",
                            },
                        },
                    },
                    "P6": {
                        "description": "动态设置",
                        "rw": "RW",
                        "data_type": "dynamic_config",
                        "conversion": "val_direct",
                        "detailed_description": "当前动态设置值",
                        "commands": {
                            "set_config": {
                                "type": CMD_TYPE_UNKNOWN_206,
                                "description": "设置动态参数配置",
                            },
                        },
                    },
                },
            },
            "V2": {
                "name": "星玉调光开关(可控硅)",
                "light": {
                    "P1": {
                        "description": "开关",
                        "rw": "RW",
                        "data_type": "brightness_light",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "detailed_description": (
                            "`type&1==1`表示处于打开状态；"
                            "`type&1==0`表示处于关闭状态；"
                            "`val` 值为亮度值，可调范围：[0,255], 值越大表示光越亮，0处于最暗，光完全熄灭，255处于最亮"
                        ),
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                            "set_brightness_on": {
                                "type": CMD_TYPE_SET_VAL,
                                "description": "打开并且设置亮度，val=亮度值[0,255]",
                            },
                            "set_brightness_off": {
                                "type": CMD_TYPE_UNKNOWN_206,
                                "description": "关闭并设置亮度，val=亮度值[0,255]",
                            },
                        },
                    },
                    "P2": {
                        "description": "指示灯亮度",
                        "rw": "RW",
                        "data_type": "indicator_light",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "detailed_description": (
                            "`type&1==1`表示处于打开状态；"
                            "`type&1==0`表示处于关闭状态；"
                            "`val` 值为亮度值，可调范围：[0,255], 值越大表示光越亮，0处于最暗，光完全熄灭，255处于最亮"
                        ),
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                            "set_brightness": {
                                "type": CMD_TYPE_SET_VAL,
                                "description": "设置亮度，val=亮度值[0,255]",
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
                        "description": "亮度控制",
                        "rw": "RW",
                        "data_type": "brightness_light",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "detailed_description": (
                            "`type&1==1`表示处于打开状态；"
                            "`type&1==0`表示处于关闭状态；"
                            "`val` 值为亮度值，可调范围：[0-255], 值越大表示光越亮，0处于最暗，光完全熄灭，255处于最亮"
                        ),
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                            "set_brightness": {
                                "type": CMD_TYPE_SET_VAL,
                                "description": "设置亮度，val=亮度值[0-255]",
                            },
                        },
                    },
                    "P2": {
                        "description": "色温控制",
                        "rw": "RW",
                        "data_type": "color_temperature",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "detailed_description": "`val` 值为色温值，取值范围[0-255]，0表示暖光，255表示冷光",
                        "commands": {
                            "set_color_temp": {
                                "type": CMD_TYPE_SET_VAL,
                                "description": "设置色温，val=色温值[0-255]",
                            },
                        },
                    },
                },
            },
            "V2": {
                "name": "调光调色智控器(0-10V)",
                "light": {
                    "P1": {
                        "description": "亮度控制",
                        "rw": "RW",
                        "data_type": "brightness_light",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "detailed_description": (
                            "`type&1==1`表示处于打开状态；"
                            "`type&1==0`表示处于关闭状态；"
                            "`val` 值为亮度值，可调范围：[0-255], 值越大表示光越亮，0处于最暗，光完全熄灭，255处于最亮"
                        ),
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                            "set_brightness": {
                                "type": CMD_TYPE_SET_VAL,
                                "description": "设置亮度，val=亮度值[0-255]",
                            },
                        },
                    },
                    "P2": {
                        "description": "色温控制",
                        "rw": "RW",
                        "data_type": "color_temperature",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "detailed_description": "`val` 值为色温值，取值范围[0-255]，0表示暖光，255表示冷光",
                        "commands": {
                            "set_color_temp": {
                                "type": CMD_TYPE_SET_VAL,
                                "description": "设置色温，val=色温值[0-255]",
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
        "switch": {
            "P1": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "type&1==1,表示打开(忽略`val` 值)；"
                    "type&1==0,表示关闭(忽略`val` 值)；"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
    },
    "SL_SW_MJ2": {
        "name": "奇点开关模块二键",
        "switch": {
            "P1": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "type&1==1,表示打开(忽略`val` 值)；"
                    "type&1==0,表示关闭(忽略`val` 值)；"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P2": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "type&1==1,表示打开(忽略`val` 值)；"
                    "type&1==0,表示关闭(忽略`val` 值)；"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
    },
    "SL_SW_MJ3": {
        "name": "奇点开关模块三键",
        "switch": {
            "P1": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "type&1==1,表示打开(忽略`val` 值)；"
                    "type&1==0,表示关闭(忽略`val` 值)；"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P2": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "type&1==1,表示打开(忽略`val` 值)；"
                    "type&1==0,表示关闭(忽略`val` 值)；"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P3": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "type&1==1,表示打开(忽略`val` 值)；"
                    "type&1==0,表示关闭(忽略`val` 值)；"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
    },
    # 2.2.7 随心按键 (CUBE Clicker2)
    "SL_SC_BB_V2": {
        "name": "随心按键",
        "button": {
            "P1": {
                "description": "按键状态",
                "rw": "R",
                "data_type": "button_events",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type` 的值定义如下: `type&1==1`，表示有按键事件产生；"
                    "`type&1==0`,表示按键事件消失；"
                    "`val` 值指明按键事件类型，只有在 `type&1==1` 才有效，"
                    "`val` 的值定义如下：1：单击事件 2：双击事件 255：长按事件"
                ),
                "device_class": "identify",
            },
        },
        "sensor": {
            "P2": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery_level",
                "conversion": "voltage_to_percentage",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，"
                    "值范围[0，100]，它是根据 `val` 电压值换算的。"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    # 2.2.8 星玉开关系列 (Nature Switch Series)
    "SL_SW_NS1": {
        "name": "星玉开关一键",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright": {
                "description": "开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    "SL_SW_NS2": {
        "name": "星玉开关二键",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    "SL_SW_NS3": {
        "name": "星玉开关三键",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L3": {
                "description": "第三路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark3": {
                "description": "第三路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright3": {
                "description": "第三路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    # 2.2.11 极星开关(120零火版) (BS Series)
    "SL_SW_BS1": {
        "name": "极星开关(120零火版)一键",
        "switch": {
            "P1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
    },
    "SL_SW_BS2": {
        "name": "极星开关(120零火版)二键",
        "switch": {
            "P1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
    },
    "SL_SW_BS3": {
        "name": "极星开关(120零火版)三键",
        "switch": {
            "P1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P3": {
                "description": "第三路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
    },
    # 2.2.12 星玉调光开关（可控硅）Dimming Light Switch
    "SL_SW_WW": {
        "name": "星玉调光开关",
        "light": {
            "P1": {
                "description": "亮度控制",
                "rw": "RW",
                "data_type": "brightness",
                "conversion": "val_to_brightness",
                "detailed_description": (
                    "`type&1==1`表示打开(忽略`val` 值);"
                    "`type&1==0`表示关闭(忽略`val` 值);"
                    "val指示灯光的亮度值范围[0，255]，255亮度最大。"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置亮度，val=亮度值[0,255]",
                    },
                },
            },
            "P2": {
                "description": "色温控制",
                "rw": "RW",
                "data_type": "color_temp",
                "conversion": "val_to_color_temp",
                "detailed_description": "`val` 值为色温值，取值范围[0，255]，0表示暖光，255表示冷光",
                "commands": {
                    "set_color_temp": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置色温，val=色温值[0,255]",
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
                "description": "情景开关1",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P2": {
                "description": "情景开关2",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P3": {
                "description": "情景开关3",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P4": {
                "description": "情景开关4",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P5": {
                "description": "情景开关5",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P6": {
                "description": "情景开关6",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "sensor": {
            "P7": {
                "description": "开关控制器配置",
                "rw": "RW",
                "data_type": "scene_config",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val` 值为面板上六个按键的功能配置参数。"
                    "`bit0-bit3`:设置P1;`bit4-bit7`:设置P2;`bit8-bit11`：设置P3;"
                    "`bit12-bit15`: 设置P4;`bit16-bit19`:设置P5;`bit20-bit23`：设置P6;"
                    "如上划分每4个bit分别代表对应面板上的按钮设置，"
                    "我们按照每4个bit的值来看功能的定义设置，以P1的设置为例："
                    "值为0时：表示自复位开关，默认5s自动关;"
                    "值为1、2、3时：分别对应面板物理设备上的继电器L1，"
                    "那么该P1的开关操作就是操作的继电器L1的开关；"
                    "值为4~14时：表示自复位开关自定义延迟关的时间，"
                    "若x表示满足当前区间的值，那么延迟关时间的计算公式为："
                    "(5+(X-3)*15) 单位为秒S。值为15时：表示通用开关，不会自动关。"
                    "当P1~P6设置为绑定继电器时，当前为普通开关控制器。"
                ),
                "commands": {
                    "config": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "下发配置，val=bit0~bit23按对应Px配置值后合并的一个数值",
                    },
                },
            },
        },
    },
    # ================= 2.3 窗帘控制系列 (Curtain Controller) =================
    # 2.3.1 窗帘控制开关
    "SL_SW_WIN": {
        "name": "窗帘控制开关",
        "cover": {
            "OP": {
                "description": "打开窗帘",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示打开窗帘",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "执行打开窗帘",
                    },
                },
            },
            "ST": {
                "description": "停止 (stop)",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示停止当前动作",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "执行停止窗帘",
                    },
                },
            },
            "CL": {
                "description": "关闭窗帘 (close)",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示关闭窗帘",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "执行关闭窗帘",
                    },
                },
            },
        },
        "light": {
            "dark": {
                "description": "关闭状态时指示灯亮度",
                "rw": "RW",
                "data_type": "brightness_light",
                "conversion": "val_direct",
                "range": "0~1023",
                "detailed_description": (
                    "`type&1==1`表示打开；`type&1==0`表示关闭；"
                    "`val`表示指示灯亮度值，取值范围：0~1023"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_brightness_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯设置亮度",
                    },
                    "set_brightness_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯设置亮度",
                    },
                },
            },
            "bright": {
                "description": "开启状态时指示灯亮度",
                "rw": "RW",
                "data_type": "brightness_light",
                "conversion": "val_direct",
                "range": "0~1023",
                "detailed_description": "`val`表示指示灯亮度值，取值范围：0~1023",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_brightness_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯设置亮度",
                    },
                    "set_brightness_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯设置亮度",
                    },
                },
            },
        },
    },
    "SL_CN_IF": {
        "name": "流光窗帘控制器",
        "cover": {
            "P1": {
                "description": "打开窗帘",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示打开窗帘",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "执行打开窗帘",
                    },
                },
            },
            "P2": {
                "description": "停止 (stop)",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示停止当前动作",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "执行停止窗帘",
                    },
                },
            },
            "P3": {
                "description": "关闭窗帘 (close)",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示关闭窗帘",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "执行关闭窗帘",
                    },
                },
            },
        },
        "light": {
            "P4": {
                "description": "打开面板指示灯的颜色值",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "P5": {
                "description": "停止(stop)时指示灯的颜色值",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "P6": {
                "description": "关闭面板指示灯的颜色值",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    "SL_CN_FE": {
        "name": "塞纳三键窗帘",
        "cover": {
            "P1": {
                "description": "打开窗帘",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示打开窗帘",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "执行打开窗帘",
                    },
                },
            },
            "P2": {
                "description": "停止 (stop)",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示停止当前动作",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "执行停止窗帘",
                    },
                },
            },
            "P3": {
                "description": "关闭窗帘 (close)",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示关闭窗帘",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "执行关闭窗帘",
                    },
                },
            },
        },
    },
    # 2.3.2 DOOYA窗帘电机
    "SL_DOOYA": {
        "name": "DOOYA窗帘电机",
        "cover": {
            "P1": {
                "description": "窗帘状态",
                "rw": "R",
                "data_type": "position_status",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示控制正在运行；"
                    "`type&1==0`表示没有运行；"
                    "当正在运行的时候即(`type&1==1`):,`val%0x80==0x80`表示正在开，否则表示正在关；"
                    "`val%0x7F`的值表示窗帘打开的百分比([0,100]);"
                    "若`val%0x7F`大于100则表示获取不到位置信息，"
                    "只有执行全开或全关之后才能重新获取位置信息。"
                ),
            },
            "P2": {
                "description": "窗帘控制",
                "rw": "W",
                "data_type": "position_control",
                "conversion": "val_direct",
                "commands": {
                    "open": {
                        "type": CMD_TYPE_SET_VAL,
                        "val": 100,
                        "description": "完全打开",
                    },
                    "close": {
                        "type": CMD_TYPE_SET_VAL,
                        "val": 0,
                        "description": "完全关闭",
                    },
                    "stop": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "val": 128,
                        "description": "停止窗帘",
                    },
                    "set_position": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "开到百分比，val=percent，percent取值:[0,100]",
                    },
                },
            },
        },
    },
    "SL_P_V2": {
        "name": "智界窗帘电机智控器",
        "cover": {
            "P2": {
                "description": "打开窗帘",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示打开窗帘",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "执行打开窗帘",
                    },
                },
            },
            "P4": {
                "description": "停止 (stop)",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示停止当前动作",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "执行停止窗帘",
                    },
                },
            },
            "P3": {
                "description": "关闭窗帘 (close)",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示关闭窗帘",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "执行关闭窗帘",
                    },
                },
            },
        },
        "sensor": {
            "P8": {
                "description": "电压(V)",
                "rw": "R",
                "data_type": "voltage",
                "conversion": "friendly_val",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，"
                    "值范围[0，100]，它是根据val电压值换算的。"
                ),
                "device_class": "voltage",
                "state_class": "measurement",
            },
        },
    },
    # ================= 2.4 灯光系列 (Light Series) =================
    # 2.4.1 灯光系列 (RGBW/RGB Light Series)
    "SL_CT_RGBW": {
        "name": "RGBW灯带",
        "light": {
            "RGBW": {
                "description": "RGBW颜色值",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "DYN": {
                "description": "动态颜色值",
                "rw": "RW",
                "data_type": "dynamic_effect",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开动态；"
                    "`type&1==0`表示关闭动态；"
                    "`val`表示动态颜色值，具体动态值请参考：附录3.2 动态颜色（DYN）定义"
                ),
                "commands": {
                    "enable": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "使能",
                    },
                    "disable": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                    "set_effect_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "使能并设置动态值，val=动态值",
                    },
                    "set_effect_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关闭并设置动态值，val=动态值",
                    },
                },
            },
        },
    },
    "SL_LI_RGBW": {
        "name": "RGBW灯泡",
        "light": {
            "RGBW": {
                "description": "RGBW颜色值",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "DYN": {
                "description": "动态颜色值",
                "rw": "RW",
                "data_type": "dynamic_effect",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开动态；"
                    "`type&1==0`表示关闭动态；"
                    "`val`表示动态颜色值，具体动态值请参考：附录3.2 动态颜色（DYN）定义"
                ),
                "commands": {
                    "enable": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "使能",
                    },
                    "disable": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                    "set_effect_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "使能并设置动态值，val=动态值",
                    },
                    "set_effect_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关闭并设置动态值，val=动态值",
                    },
                },
            },
        },
    },
    "SL_SC_RGB": {
        "name": "RGB灯带无白光",
        "light": {
            "RGB": {
                "description": "RGB颜色值",
                "rw": "RW",
                "data_type": "rgb_light",
                "conversion": "val_direct",
                "range": "0x00000000-0xFFFFFFFF",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    "`type&1==0`表示关闭；"
                    "`val` 值为颜色值，大小4个字节，定义如下："
                    "`bit0`~`bit7`:Blue, `bit8`~`bit15`:Green, "
                    "`bit16`~`bit23`:Red, `bit24`~`bit31`:White, "
                    "(当White>0时，表示动态模式)"
                    "具体动态值请参考：附录3.2动态颜色(DYN)定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
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
                "description": "亮度控制",
                "rw": "RW",
                "data_type": "brightness_light",
                "conversion": "val_direct",
                "range": "0-100",
                "detailed_description": (
                    "`type&1==1`表示打开(忽略`val` 值)；"
                    "`type&1==0`表示关闭(忽略`val` 值)；"
                    "`val`指示灯光的亮度值范围[0,100]，100亮度最大"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置亮度，val=亮度值[0-100]",
                    },
                },
            },
            "P2": {
                "description": "颜色控制",
                "rw": "RW",
                "data_type": "quantum_light",
                "conversion": "val_direct",
                "range": "0x00000000-0xFFFFFFFF",
                "detailed_description": (
                    "`val` 值为颜色值，大小4个字节，定义如下："
                    "`bit0`~`bit7`:Blue, `bit8`~`bit15`:Green, "
                    "`bit16`~`bit23`:Red, `bit24~bit31`:White, "
                    "(当White>0时，表示动态模式)"
                    "具体动态值请参考：附录3.2动态颜色(DYN)定义, "
                    "附录3.3量子灯特殊(DYN)定义"
                ),
                "commands": {
                    "set_color": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "设置颜色或动态值，val=颜色或动态值",
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
                "description": "开关",
                "rw": "RW",
                "data_type": "brightness_light",
                "conversion": "val_direct",
                "range": "0-255",
                "detailed_description": (
                    "`type&1==1`表示处于打开状态；"
                    "`type&1==0`表示处于关闭状态；"
                    "`val` 值为亮度值，可调范围：[0-255], 值越大表示光越亮，0处于最暗，光完全熄灭，255处于最亮"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置亮度，val=亮度值[0-255]",
                    },
                },
            },
        },
        "binary_sensor": {
            "P2": {
                "description": "移动检测",
                "rw": "R",
                "data_type": "motion_status",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0：没有检测到移动，1：有检测到移动",
                "device_class": "motion",
            },
        },
        "sensor": {
            "P3": {
                "description": "当前环境光照",
                "rw": "R",
                "data_type": "illuminance",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始光照值，`v` 值表示实际值(单位：lux)",
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
                "description": "开关/颜色设置",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "range": "0x00000000-0xFFFFFFFF",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    "`type&1==0`表示关闭；"
                    "`val` 值为颜色值，大小4个字节，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green "
                    "- `bit16~bit23`: Red - `bit24~bit31`: White/DYN。"
                    "例如：红色：`0x00FF0000`, 白色：`0xFF000000`。"
                    "`bit24~bit31`即可以设置白光又可以设置动态。"
                    "当其值在[0~100]表示设置的是白光，0表示不显示白光，"
                    "100表示白光最亮；"
                    "当其值大于等于128表示设置为动态模式，具体动态值请参考：附录3.2 动态颜色(DYN)定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
        "sensor": {
            "P2": {
                "description": "当前环境光照",
                "rw": "R",
                "data_type": "illuminance",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始光照值，`v` 值表示实际值(单位：lux)",
                "device_class": "illuminance",
                "unit_of_measurement": "lux",
                "state_class": "measurement",
            },
            "P3": {
                "description": "充电指示",
                "rw": "R",
                "data_type": "charging_status",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0：没有充电, 1：正在充电，`val`表示原始电压值",
                "device_class": "battery",
                "unit_of_measurement": "V",
                "state_class": "measurement",
            },
            "P4": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据 `val` 电压值换算的"
                ),
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
                "description": "RGBW颜色值",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1` 表示打开；`type&1==0` 表示关闭；"
                    "`val` 表示指示灯亮度值，定义如下："
                    "- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - "
                    "`bit24~bit31`: White（当 White>0 时，表示动态模式）"
                    "具体动态值请参考：附录3.1动态颜色（`DYN`）定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "DYN": {
                "description": "动态颜色值",
                "rw": "RW",
                "data_type": "dynamic_effect",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开动态；"
                    "`type&1==0`表示关闭动态；"
                    "`val`表示动态颜色值，具体动态值请参考：附录3.2 动态颜色（DYN）定义"
                ),
                "commands": {
                    "enable": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "使能",
                    },
                    "disable": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                    "set_effect_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "使能并设置动态值，val=动态值",
                    },
                    "set_effect_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关闭并设置动态值，val=动态值",
                    },
                },
            },
        },
    },
    "OD_WE_IRCTL": {
        "name": "超级碗RGB灯(OD)",
        "light": {
            "RGB": {
                "description": "RGB颜色值",
                "rw": "RW",
                "data_type": "rgb_light",
                "conversion": "val_direct",
                "range": "0x00000000-0xFFFFFFFF",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    "`type&1==0`表示关闭；"
                    "`val` 值为颜色值，大小4个字节，定义如下："
                    "`bit0`~`bit7`:Blue, `bit8`~`bit15`:Green, "
                    "`bit16`~`bit23`:Red, `bit24`~`bit31`:White, "
                    "(当White>0时，表示动态模式)"
                    "具体动态值请参考：附录3.2动态颜色(DYN)定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    "SL_SPOT": {
        "name": "超级碗RGB灯",
        "light": {
            "RGB": {
                "description": "RGB颜色值",
                "rw": "RW",
                "data_type": "rgb_light",
                "conversion": "val_direct",
                "range": "0x00000000-0xFFFFFFFF",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    "`type&1==0`表示关闭；"
                    "`val` 值为颜色值，大小4个字节，定义如下："
                    "`bit0`~`bit7`:Blue, `bit8`~`bit15`:Green, "
                    "`bit16`~`bit23`:Red, `bit24`~`bit31`:White, "
                    "(当White>0时，表示动态模式)"
                    "具体动态值请参考：附录3.2动态颜色(DYN)定义"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                    "set_color_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    "SL_LI_IR": {
        "name": "红外吸顶灯",
        "light": {
            "P1": {
                "description": "亮度控制",
                "rw": "RW",
                "data_type": "brightness_light",
                "conversion": "val_direct",
                "range": "0-255",
                "detailed_description": (
                    "`type&1==1`表示处于打开状态；"
                    "`type&1==0`表示处于关闭状态；"
                    "`val` 值为亮度值，可调范围：[0-255], 值越大表示光越亮，0处于最暗，光完全熄灭，255处于最亮"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置亮度，val=亮度值[0-255]",
                    },
                },
            },
            "P2": {
                "description": "色温控制",
                "rw": "RW",
                "data_type": "color_temperature",
                "conversion": "val_direct",
                "range": "0-255",
                "detailed_description": "`val` 值为色温值，取值范围[0-255]，0表示暖光，255表示冷光",
                "commands": {
                    "set_color_temp": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置色温，val=色温值[0-255]",
                    },
                },
            },
            "P3": {
                "description": "夜灯亮度控制",
                "rw": "RW",
                "data_type": "nightlight_brightness",
                "conversion": "val_direct",
                "range": "0,63,127,195,255",
                "detailed_description": (
                    "`val` 值为夜灯亮度，共有5档，亮度从低到高分别如下："
                    "0、63、127、195、255。0表示夜灯处于关闭状态，"
                    "255表示夜灯处于最亮状态。注意：若亮度值为其它值则根据如下规则判断亮度档位："
                    "0：关闭档，>=196：最亮档，>=128并且<=195：次亮档，"
                    ">=64并且<=127：第三亮档，>0并且<=63：第四亮档"
                ),
                "commands": {
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置亮度，val=亮度值[0、63、127、195、255]",
                    },
                },
            },
        },
    },
    "SL_P_IR": {
        "name": "红外模块",
        "light": {
            "P1": {
                "description": "亮度控制",
                "rw": "RW",
                "data_type": "brightness_light",
                "conversion": "val_direct",
                "range": "0-255",
                "detailed_description": (
                    "`type&1==1`表示处于打开状态；"
                    "`type&1==0`表示处于关闭状态；"
                    "`val` 值为亮度值，可调范围：[0-255], 值越大表示光越亮，0处于最暗，光完全熄灭，255处于最亮"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置亮度，val=亮度值[0-255]",
                    },
                },
            },
            "P2": {
                "description": "色温控制",
                "rw": "RW",
                "data_type": "color_temperature",
                "conversion": "val_direct",
                "range": "0-255",
                "detailed_description": "`val` 值为色温值，取值范围[0-255]，0表示暖光，255表示冷光",
                "commands": {
                    "set_color_temp": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置色温，val=色温值[0-255]",
                    },
                },
            },
            "P3": {
                "description": "夜灯亮度控制",
                "rw": "RW",
                "data_type": "nightlight_brightness",
                "conversion": "val_direct",
                "range": "0,63,127,195,255",
                "detailed_description": (
                    "`val` 值为夜灯亮度，共有5档，亮度从低到高分别如下："
                    "0、63、127、195、255。0表示夜灯处于关闭状态，"
                    "255表示夜灯处于最亮状态。注意：若亮度值为其它值则根据如下规则判断亮度档位："
                    "0：关闭档，>=196：最亮档，>=128并且<=195：次亮档，"
                    ">=64并且<=127：第三亮档，>0并且<=63：第四亮档"
                ),
                "commands": {
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置亮度，val=亮度值[0、63、127、195、255]",
                    },
                },
            },
        },
    },
    "SL_SC_CV": {
        "name": "语音小Q",
        "switch": {
            "P1": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
    },
    # ================= 2.6 感应器系列 (Sensor Series) =================
    # 2.6.1 门禁感应器（Guard Sensor)
    "SL_SC_G": {
        "name": "门禁感应器",
        "binary_sensor": {
            "G": {
                "description": "当前状态",
                "rw": "R",
                "data_type": "door_status",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0：打开，1：关闭",
                "device_class": "door",
            },
        },
        "sensor": {
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据 `val` 电压值换算的"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    "SL_SC_BG": {
        "name": "门禁感应器（带按键震动）",
        "binary_sensor": {
            "G": {
                "description": "当前状态",
                "rw": "R",
                "data_type": "door_status",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1`表示处于打开状态(忽略`val` 值)；"
                    "`type&1==0`表示处于吸合状态(忽略`val` 值)"
                ),
                "device_class": "door",
            },
            "B": {
                "description": "按键状态",
                "rw": "R",
                "data_type": "button_status",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示按键处于按下状态(忽略`val` 值)；"
                    "`type&1==0`表示按键处于松开状态(忽略`val` 值)"
                ),
                "device_class": "moving",
            },
            "AXS": {
                "description": "震动状态",
                "rw": "R",
                "data_type": "vibration_status",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0：无震动，非0：震动",
                "device_class": "vibration",
            },
        },
        "sensor": {
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据 `val` 电压值换算的"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    "SL_SC_GS": {
        "name": "门禁感应器（增强版）",
        "binary_sensor": {
            "P1": {
                "description": "当前状态",
                "rw": "R",
                "data_type": "door_status",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1`表示处于打开状态(忽略`val` 值)；"
                    "`type&1==0`表示处于吸合状态(忽略`val` 值)"
                ),
                "device_class": "door",
            },
            "AXS": {
                "description": "震动状态",
                "rw": "R",
                "data_type": "vibration_status",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1`表示处于震动状态；`type&1==0`表示无震动状态；"
                    "`val` 值表示震动强度"
                ),
                "device_class": "vibration",
            },
        },
        "sensor": {
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据 `val` 电压值换算的"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    "SL_SC_MHW": {
        "name": "动态感应器",
        "binary_sensor": {
            "M": {
                "description": "移动检测",
                "rw": "R",
                "data_type": "motion_status",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0：没有检测到移动，1：有检测到移动",
                "device_class": "motion",
            },
        },
        "sensor": {
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据 `val` 电压值换算的"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    "SL_SC_BM": {
        "name": "动态感应器",
        "binary_sensor": {
            "M": {
                "description": "移动检测",
                "rw": "R",
                "data_type": "motion_status",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0：没有检测到移动，1：有检测到移动",
                "device_class": "motion",
            },
        },
        "sensor": {
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据 `val` 电压值换算的"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    "SL_SC_CM": {
        "name": "动态感应器（带USB供电）",
        "binary_sensor": {
            "P1": {
                "description": "移动检测",
                "rw": "R",
                "data_type": "motion_status",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0：没有检测到移动，1：有检测到移动",
                "device_class": "motion",
            },
        },
        "sensor": {
            "P3": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据 `val` 电压值换算的"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "P4": {
                "description": "USB供电电压",
                "rw": "R",
                "data_type": "voltage",
                "conversion": "val_direct",
                "detailed_description": "`val`表示原始电压值，若`val` 值大于430则表明供电在工作，否则表明未供电工作",
                "device_class": "voltage",
                "unit_of_measurement": "V",
                "state_class": "measurement",
            },
        },
    },
    "SL_BP_MZ": {
        "name": "动态感应器PRO",
        "binary_sensor": {
            "P1": {
                "description": "移动检测",
                "rw": "R",
                "data_type": "motion_status",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0：没有检测到移动，1：有检测到移动",
                "device_class": "motion",
            },
        },
        "sensor": {
            "P2": {
                "description": "当前环境光照",
                "rw": "R",
                "data_type": "illuminance",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始光照值，`v` 值表示实际值(单位：lux)",
                "device_class": "illuminance",
                "unit_of_measurement": "lx",
                "state_class": "measurement",
            },
            "P3": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据 `val` 电压值换算的"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    "SL_SC_THL": {
        "name": "环境感应器（温湿度光照）",
        "sensor": {
            "T": {
                "description": "当前环境温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "detailed_description": "`val` 值表示原始温度值，它是温度值*10值(单位：℃)",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
            "H": {
                "description": "当前环境湿度",
                "rw": "R",
                "data_type": "humidity",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始湿度值，它是湿度值*10，`v` 值表示实际值(单位：%)",
                "device_class": "humidity",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "Z": {
                "description": "当前环境光照",
                "rw": "R",
                "data_type": "illuminance",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始光照值，`v` 值表示实际值(单位：lux)",
                "device_class": "illuminance",
                "unit_of_measurement": "lx",
                "state_class": "measurement",
            },
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据 `val` 电压值换算的"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    "SL_SC_BE": {
        "name": "环境感应器（温湿度光照）",
        "sensor": {
            "T": {
                "description": "当前环境温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "detailed_description": "`val` 值表示原始温度值，它是温度值*10值(单位：℃)",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
            "H": {
                "description": "当前环境湿度",
                "rw": "R",
                "data_type": "humidity",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始湿度值，它是湿度值*10，`v` 值表示实际值(单位：%)",
                "device_class": "humidity",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "Z": {
                "description": "当前环境光照",
                "rw": "R",
                "data_type": "illuminance",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始光照值，`v` 值表示实际值(单位：lux)",
                "device_class": "illuminance",
                "unit_of_measurement": "lx",
                "state_class": "measurement",
            },
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据 `val` 电压值换算的"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    "SL_SC_WA": {
        "name": "水浸传感器",
        "binary_sensor": {
            "WA": {
                "description": "水浸检测",
                "rw": "R",
                "data_type": "water_leak",
                "conversion": "val_greater_than_zero",
                "detailed_description": "`val` 值大于0表示检测到水；val=0表示未检测到水",
                "device_class": "moisture",
            },
        },
        "sensor": {
            "WA": {
                "description": "导电率",
                "rw": "R",
                "data_type": "conductivity",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0：未检测到水；值越大表示水越多，导电率越高",
                "device_class": "moisture",
                "unit_of_measurement": "µS/cm",
                "state_class": "measurement",
            },
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据`val`电压值换算的"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    "SL_SC_CH": {
        "name": "甲醛感应器",
        "sensor": {
            "P1": {
                "description": "甲醛浓度",
                "rw": "R",
                "data_type": "甲醛_concentration",
                "conversion": "v_field",
                "detailed_description": "`type&1==1`表示甲醛浓度值超过告警门限；`val` 值表示甲醛浓度值",
                "device_class": "volatile_organic_compounds",
                "unit_of_measurement": "µg/m³",
                "state_class": "measurement",
            },
        },
        "switch": {
            "P2": {
                "description": "甲醛浓度告警门限",
                "rw": "RW",
                "data_type": "threshold_setting",
                "conversion": "val_direct",
                "detailed_description": "`val` 值越大则灵敏度越低，门限越高",
                "commands": {
                    "set_sensitivity": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置报警器灵敏度",
                    },
                },
            },
            "P3": {
                "description": "警报音",
                "rw": "RW",
                "data_type": "alarm_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`指示报警音正在响，反之则没有报警音",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "手工触发报警音",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "手动消除报警音",
                    },
                },
            },
        },
    },
    "SL_SC_CP": {
        "name": "燃气感应器",
        "sensor": {
            "P1": {
                "description": "燃气浓度",
                "rw": "R",
                "data_type": "燃气_concentration",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1`表示燃气浓度值超过告警门限；`val` 值表示燃气浓度值",
                "device_class": "gas",
                "unit_of_measurement": "ppm",
                "state_class": "measurement",
            },
        },
        "switch": {
            "P2": {
                "description": "燃气浓度告警门限",
                "rw": "RW",
                "data_type": "threshold_setting",
                "conversion": "val_direct",
                "detailed_description": "`val` 值越大则灵敏度越低，门限越高",
                "commands": {
                    "set_sensitivity": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置报警器灵敏度",
                    },
                },
            },
            "P3": {
                "description": "警报音",
                "rw": "RW",
                "data_type": "alarm_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`指示报警音正在响，反之则没有报警音",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "手工触发报警音",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "手动消除报警音",
                    },
                },
            },
        },
    },
    "SL_SC_CQ": {
        "name": "TVOC+CO2环境感应器",
        "sensor": {
            "P1": {
                "description": "当前环境温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始温度值，它是温度值*10，`v` 值表示实际值(单位：℃)",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
            "P2": {
                "description": "当前环境湿度",
                "rw": "R",
                "data_type": "humidity",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始湿度值，它是湿度值*10，`v` 值表示实际值(单位：%)",
                "device_class": "humidity",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "P3": {
                "description": "当前CO2浓度值",
                "rw": "R",
                "data_type": "co2_concentration",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示co2浓度值，`v` 值表示实际值(单位：ppm)，参考："
                    "`val`<=500：优，`val`<=700：良，`val`<=1000：中，`val`>1000：差"
                ),
                "device_class": "carbon_dioxide",
                "unit_of_measurement": "ppm",
                "state_class": "measurement",
            },
            "P4": {
                "description": "当前TVOC浓度值",
                "rw": "R",
                "data_type": "tvoc_concentration",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示tvoc原始浓度值，它是TVOC浓度值*1000，实际浓度值=原始浓度值/1000，"
                    "`v` 值表示实际值(单位：mg/m3)，参考：`val`<0.34：优，`val`<0.68：良，"
                    "`val`<=1.02：中，`val`>1.02：差"
                ),
                "device_class": "volatile_organic_compounds",
                "unit_of_measurement": "mg/m³",
                "state_class": "measurement",
            },
            "P5": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据 `val` 电压值换算的"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "P6": {
                "description": "USB供电电压",
                "rw": "R",
                "data_type": "voltage",
                "conversion": "val_direct",
                "detailed_description": "`val`表示原始电压值，若`val` 值大于430则表明供电在工作，否则表明未供电工作",
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
                "description": "平均功率",
                "rw": "R",
                "data_type": "power",
                "conversion": "val_direct",
                "detailed_description": "`val` 值表示平均功率",
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
                "description": "当前是否有烟雾告警",
                "rw": "R",
                "data_type": "smoke_alarm",
                "conversion": "val_direct",
                "detailed_description": "`val`等于0表示没有烟雾告警，等于1表示有烟雾告警",
                "device_class": "smoke",
            },
        },
        "sensor": {
            "P2": {
                "description": "电压",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "如果使用9V的电池，则实际电压值=(`val`/100)*3，注意：其值可能会超过9V，"
                    "例如9.58V；如果外接12V供电，则该值无效。`v` 值将表示当前剩余电量百分比，"
                    "值范围[0,100]"
                ),
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
                "description": "当前环境温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始温度值，它是温度值*10，`v` 值表示实际值(单位：℃)",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
            "P2": {
                "description": "当前环境湿度",
                "rw": "R",
                "data_type": "humidity",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始湿度值，它是湿度值*10，`v` 值表示实际值(单位：%)",
                "device_class": "humidity",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "P3": {
                "description": "当前CO2浓度值",
                "rw": "R",
                "data_type": "co2_concentration",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示co2浓度值，`v` 值表示实际值(单位：ppm)，参考："
                    "`val`<=500：优，`val`<=700：良，`val`<=1000：中，`val`>1000：差"
                ),
                "device_class": "carbon_dioxide",
                "unit_of_measurement": "ppm",
                "state_class": "measurement",
            },
            "P4": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据 `val` 电压值换算的"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "P5": {
                "description": "USB供电电压",
                "rw": "R",
                "data_type": "voltage",
                "conversion": "val_direct",
                "detailed_description": "`val`表示原始电压值，若`val` 值大于430则表明供电在工作，否则表明未供电工作",
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
                "description": "移动检测(Motion)",
                "rw": "R",
                "data_type": "motion_status",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0：没有检测到移动，非0：有检测到移动",
                "device_class": "motion",
            },
        },
        "switch": {
            "P2": {
                "description": "移动检测参数设置",
                "rw": "RW",
                "data_type": "radar_config",
                "conversion": "val_direct",
                "detailed_description": (
                    "包含动态锁定时间与灵敏度设置。其中：`bit0-bit7`：动态锁定时间，取值范围为：1-255，"
                    "具体锁定时间为：配置值*4，单位为秒，例如`bit0-bit7`配置值为16，则表示动态锁定时间为64秒。"
                    "`bit8-bit25`：灵敏度，灵敏度默认值为4，范围1-255，值越小则越灵敏"
                ),
                "commands": {
                    "set_config": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置感应器动态锁定时间与灵敏度",
                    },
                },
            },
        },
    },
    "SL_DF_GG": {
        "name": "云防门窗感应器",
        "binary_sensor": {
            "A": {
                "description": "当前状态",
                "rw": "R",
                "data_type": "door_status",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1`表示处于打开状态(忽略`val` 值)；"
                    "`type&1==0`表示处于吸合状态(忽略`val` 值)"
                ),
                "device_class": "door",
            },
            "TR": {
                "description": "防拆状态",
                "rw": "R",
                "data_type": "tamper_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`则表示触发防拆警报；`type&1==0`则表示状态正常",
                "device_class": "tamper",
            },
            "A2": {
                "description": "外部感应器状态",
                "rw": "R",
                "data_type": "door_status",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1`表示处于打开状态(忽略`val` 值)；"
                    "`type&1==0`表示处于吸合状态(忽略`val` 值)；"
                    "需要接外部感应器，如果没有接则type值为1"
                ),
                "device_class": "door",
            },
        },
        "sensor": {
            "T": {
                "description": "当前环境温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始温度值，它是实际温度值*10，`v` 值表示实际值(单位：℃)",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，"
                    "它是根据`val`电压值换算的。注意：`type&1==1`表示低电报警状态"
                ),
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
                "description": "当前状态",
                "rw": "R",
                "data_type": "motion_status",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1`表示侦测到人体移动(忽略`val` 值)；"
                    "`type&1==0`表示没有侦测到人体移动(忽略`val` 值)"
                ),
                "device_class": "motion",
            },
            "TR": {
                "description": "防拆状态",
                "rw": "R",
                "data_type": "tamper_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`则表示触发防拆警报；`type&1==0`则表示状态正常",
                "device_class": "tamper",
            },
        },
        "sensor": {
            "T": {
                "description": "温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始温度值，它是实际温度值*10，`v` 值表示实际值(单位：℃)",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，"
                    "它是根据`val`电压值换算的。注意：`type&1==1`表示低电报警状态"
                ),
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
                "description": "当前状态",
                "rw": "R",
                "data_type": "siren_status",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1`表示警铃播放(忽略`val` 值)；"
                    "`type&1==0`表示正常(忽略`val` 值)"
                ),
                "device_class": "sound",
            },
            "TR": {
                "description": "防拆状态",
                "rw": "R",
                "data_type": "tamper_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`则表示触发防拆警报；`type&1==0`则表示状态正常",
                "device_class": "tamper",
            },
        },
        "sensor": {
            "T": {
                "description": "温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始温度值，它是实际温度值*10，`v` 值表示实际值(单位：℃)",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，"
                    "它是根据val电压值换算的。注意：`type&1==1`表示低电报警状态"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
        "switch": {
            "P1": {
                "description": "报警设置",
                "rw": "RW",
                "data_type": "alarm_config",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val`为32bit值，描述如下(16进制)：`0xAABBCCDD`：`AABB`表示警报持续时长，单位为0.1秒；"
                    "`CC`是声音强度(136-255)，255最强，136最弱；`DD`表示音频序号：0：无，1：信息，2：告警"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "播放",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "停止",
                    },
                    "set_config_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "设置值并播放",
                    },
                    "set_config_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "设置值并停止",
                    },
                },
            },
        },
    },
    "SL_DF_BB": {
        "name": "云防遥控器",
        "binary_sensor": {
            "eB1": {
                "description": "按键1状态(为布防图标)",
                "rw": "R",
                "data_type": "button_status",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1`表示按键处于按下状态(忽略`val` 值)；"
                    "`type&1==0`表示按键处于松开状态(忽略`val` 值)"
                ),
                "device_class": "moving",
            },
            "eB2": {
                "description": "按键2状态(为撤防图标)",
                "rw": "R",
                "data_type": "button_status",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1`表示按键处于按下状态(忽略`val` 值)；"
                    "`type&1==0`表示按键处于松开状态(忽略`val` 值)"
                ),
                "device_class": "moving",
            },
            "eB3": {
                "description": "按键3状态(为警告图标)",
                "rw": "R",
                "data_type": "button_status",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1`表示按键处于按下状态(忽略`val` 值)；"
                    "`type&1==0`表示按键处于松开状态(忽略`val` 值)"
                ),
                "device_class": "moving",
            },
            "eB4": {
                "description": "按键4状态(为在家图标)",
                "rw": "R",
                "data_type": "button_status",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1`表示按键处于按下状态(忽略`val` 值)；"
                    "`type&1==0`表示按键处于松开状态(忽略`val` 值)"
                ),
                "device_class": "moving",
            },
        },
        "sensor": {
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，"
                    "它是根据`val`电压值换算的。注意：`type&1==1`表示低电报警状态"
                ),
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
                "description": "噪音值",
                "rw": "R",
                "data_type": "noise_level",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示噪音值大于告警门限；"
                    "`type&1==0`表示噪音值没有超过告警门限；"
                    "`val`表示当前噪音值，单位为分贝"
                ),
                "device_class": "sound_pressure",
                "unit_of_measurement": "dB",
                "state_class": "measurement",
            },
            "P4": {
                "description": "噪音校正值",
                "rw": "RW",
                "data_type": "noise_calibration",
                "conversion": "val_direct",
                "detailed_description": "取值范围为[-128~127]，如果噪音采样有误差，可以配置噪音校正值校正",
                "device_class": "sound_pressure",
                "unit_of_measurement": "dB",
                "state_class": "measurement",
            },
        },
        "switch": {
            "P2": {
                "description": "告警门限设置",
                "rw": "RW",
                "data_type": "threshold_config",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val`为32bit值(十六进制)：`0xAABBCCDD`：`DD`表示告警门限值，数值单位为分贝，取值范围[0,255]；"
                    "`CC`表示采样值1，取值范围[0,255]；`BB`表示采样值2，取值范围[0,255]；"
                    "`CCBB`共同作用形成越限率"
                ),
                "commands": {
                    "set_threshold": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "修改门限值",
                    },
                },
            },
            "P3": {
                "description": "报警设置",
                "rw": "RW",
                "data_type": "alarm_config",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示处于报警状态；"
                    "`type&1==0`表示处于正常状态；"
                    "`val`为32bit值，描述如下(16进制)：`0xAABBCCDD`：`AABB`表示警报持续时长，"
                    "单位为0.1秒，等于65535则表示一直持续；"
                    "`CC`是声音强度，0表示没有声音，其它值表示有声音；"
                    "`DD`表示音频模式：0：无声音，1：指示音，2：告警音，0x7F：测试音，0x80-0xFF：自定义模式"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "播放",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "停止",
                    },
                    "set_config_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "设置值并播放",
                    },
                    "set_config_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "设置值并停止",
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
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit0",
                "detailed_description": "`type&1==1`表示打开,`val` 值忽略；`type&1==0`表示关闭；",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "RM": {
                "description": "运行模式",
                "rw": "RW",
                "data_type": "run_mode",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0:auto 1~3:风量1~3 4：风量最大 5:睡眠模式",
                "commands": {
                    "set_mode": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置运行模式",
                    },
                },
            },
        },
        "sensor": {
            "T": {
                "description": "温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "friendly_value",
                "unit_of_measurement": "°C",
                "device_class": "temperature",
                "state_class": "measurement",
                "detailed_description": "`val` 值表示原始温度值，它是温度值*10，`v` 值表示实际值(单位：℃)",
            },
            "H": {
                "description": "湿度",
                "rw": "R",
                "data_type": "humidity",
                "conversion": "friendly_value",
                "unit_of_measurement": "%",
                "device_class": "humidity",
                "state_class": "measurement",
                "detailed_description": "`val` 值表示原始湿度值，它是湿度值*10，`v` 值表示实际值(单位：%)",
            },
            "PM": {
                "description": "PM2.5",
                "rw": "R",
                "data_type": "pm25",
                "conversion": "friendly_value",
                "unit_of_measurement": "µg/m³",
                "device_class": "pm25",
                "state_class": "measurement",
                "detailed_description": "`val` 值表示PM2.5值，`v` 值表示实际值(单位：ug/m³)",
            },
            "FL": {
                "description": "滤芯寿命",
                "rw": "R",
                "data_type": "filter_life",
                "conversion": "val_direct",
                "unit_of_measurement": "h",
                "detailed_description": "`val` 值表示滤芯寿命，范围：0~4800(单位：h)",
            },
            "UV": {
                "description": "紫外线指数",
                "rw": "R",
                "data_type": "uv_index",
                "conversion": "val_direct",
                "detailed_description": "`val` 值表示紫外线指数",
            },
        },
    },
    # ================= 2.8 智能门锁 (Smart Door Lock) =================
    # 2.8.1 智能门锁系列 (Smart Door Lock Series)
    "SL_LK_LS": {
        "name": "思锁智能门锁",
        "binary_sensor": {
            "EVTLO": {
                "description": "门锁状态",
                "rw": "R",
                "data_type": "door_lock",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示打开；`type&1==0` 表示关闭",
                "device_class": "lock",
            },
            "ALM": {
                "description": "告警状态",
                "rw": "R",
                "data_type": "alarm_status",
                "conversion": "val_greater_than_zero",
                "detailed_description": "任何告警位为1时表示有告警",
                "device_class": "problem",
            },
        },
        "sensor": {
            "BAT": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "val_direct",
                "detailed_description": "`Val`表示电量值",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "ALM": {
                "description": "告警信息",
                "rw": "R",
                "data_type": "alarm_status",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val` 值定义如下: `bit0`：1为错误报警（输入错误密码或指纹或卡片超过10次就报警) "
                    "`bit1`：1为劫持报警（输入防劫持密码或防劫持指纹开锁就报警) "
                    "`bit2`：1为防撬报警 (锁被撬开) `bit3`：1为机械钥匙报警（使用机械钥匙开 "
                    "`bit4`：1为低电压报警（电池电量不足) `bit5`：1为异动告警 "
                    "`bit6`：1为门铃 `bit7`：1为火警 `bit8`：1为入侵告警 `bit11`：1为恢复出厂告警"
                ),
            },
            "EVTLO": {
                "description": "实时开锁",
                "rw": "R",
                "data_type": "lock_event",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0` 表示关闭；"
                    " `val` 值定义如下: `bit0~11`表示用户编号; 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁(12v开锁信号开锁)；"
                    " 7：APP开启；"
                    " 8：蓝牙开锁；"
                    " 9：手动开锁；"
                    " 15：出错) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式：(同上定义) (注：因有可能存在两种方式同时开启门锁"
                    " 的情况，单开时`bit0~15`为开锁信息，其 他位为0；"
                    "双开时`bit0~15`和`bit16~31` 分别为相应的开锁信息) "
                    "`val`的长度有8/24/32bit三种类型"
                ),
            },
            "HISLK": {
                "description": "最近一次开锁信息",
                "rw": "R",
                "data_type": "recent_unlock",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0`表示关闭；"
                    " `val` 值定义如下： `bit0~11`表示用户编号；"
                    " `bit12~15`表示开锁方式：( 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁；"
                    " 7：APP开启) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式: （同上定义）"
                ),
            },
            "EVTOP": {
                "description": "操作记录",
                "rw": "R",
                "data_type": "operation_record",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type`可以获知长度，方法是： (`type=0x40+(8-1)*2` or "
                    "`type=0x40+(16-1)*2` or `type=0x40+(32-1)*2`) "
                    "`val`的通用的编码次序是：[1Byte的记录类型][2Byte的用户id]"
                    "[1Byte的用户flag] 用户标志flag：`bit01=11`表示管理员，"
                    "01表示普通用户，00表示已经删除了"
                ),
            },
        },
    },
    "SL_LK_GTM": {
        "name": "盖特曼智能门锁",
        "sensor": {
            "BAT": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "val_direct",
                "detailed_description": "`Val`表示电量值",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "ALM": {
                "description": "告警信息",
                "rw": "R",
                "data_type": "alarm_status",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val` 值定义如下: `bit0`：1为错误报警（输入错误密码或指纹或卡片超过10次就报警) "
                    "`bit1`：1为劫持报警（输入防劫持密码或防劫持指纹开锁就报警) "
                    "`bit2`：1为防撬报警 (锁被撬开) `bit3`：1为机械钥匙报警（使用机械钥匙开 "
                    "`bit4`：1为低电压报警（电池电量不足) `bit5`：1为异动告警 "
                    "`bit6`：1为门铃 `bit7`：1为火警 `bit8`：1为入侵告警 `bit11`：1为恢复出厂告警"
                ),
            },
            "EVTLO": {
                "description": "实时开锁",
                "rw": "R",
                "data_type": "lock_event",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0` 表示关闭；"
                    " `val` 值定义如下: `bit0~11`表示用户编号; 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁(12v开锁信号开锁)；"
                    " 7：APP开启；"
                    " 8：蓝牙开锁；"
                    " 9：手动开锁；"
                    " 15：出错) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式：(同上定义) (注：因有可能存在两种方式同时开启门锁"
                    " 的情况，单开时`bit0~15`为开锁信息，其 他位为0；"
                    "双开时`bit0~15`和`bit16~31` 分别为相应的开锁信息) "
                    "`val`的长度有8/24/32bit三种类型"
                ),
            },
            "HISLK": {
                "description": "最近一次开锁信息",
                "rw": "R",
                "data_type": "recent_unlock",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0`表示关闭；"
                    " `val` 值定义如下： `bit0~11`表示用户编号；"
                    " `bit12~15`表示开锁方式：( 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁；"
                    " 7：APP开启) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式: （同上定义）"
                ),
            },
            "EVTOP": {
                "description": "操作记录",
                "rw": "R",
                "data_type": "operation_record",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type`可以获知长度，方法是： (`type=0x40+(8-1)*2` or "
                    "`type=0x40+(16-1)*2` or `type=0x40+(32-1)*2`) "
                    "`val`的通用的编码次序是：[1Byte的记录类型][2Byte的用户id]"
                    "[1Byte的用户flag] 用户标志flag：`bit01=11`表示管理员，"
                    "01表示普通用户，00表示已经删除了"
                ),
            },
        },
    },
    "SL_LK_AG": {
        "name": "Aqara智能门锁",
        "sensor": {
            "BAT": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "val_direct",
                "detailed_description": "`Val`表示电量值",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "ALM": {
                "description": "告警信息",
                "rw": "R",
                "data_type": "alarm_status",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val` 值定义如下: `bit0`：1为错误报警（输入错误密码或指纹或卡片超过10次就报警) "
                    "`bit1`：1为劫持报警（输入防劫持密码或防劫持指纹开锁就报警) "
                    "`bit2`：1为防撬报警 (锁被撬开) `bit3`：1为机械钥匙报警（使用机械钥匙开 "
                    "`bit4`：1为低电压报警（电池电量不足) `bit5`：1为异动告警 "
                    "`bit6`：1为门铃 `bit7`：1为火警 `bit8`：1为入侵告警 `bit11`：1为恢复出厂告警"
                ),
            },
            "EVTLO": {
                "description": "实时开锁",
                "rw": "R",
                "data_type": "lock_event",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0` 表示关闭；"
                    " `val` 值定义如下: `bit0~11`表示用户编号; 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁(12v开锁信号开锁)；"
                    " 7：APP开启；"
                    " 8：蓝牙开锁；"
                    " 9：手动开锁；"
                    " 15：出错) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式：(同上定义) (注：因有可能存在两种方式同时开启门锁"
                    " 的情况，单开时`bit0~15`为开锁信息，其 他位为0；"
                    "双开时`bit0~15`和`bit16~31` 分别为相应的开锁信息) "
                    "`val`的长度有8/24/32bit三种类型"
                ),
            },
            "HISLK": {
                "description": "最近一次开锁信息",
                "rw": "R",
                "data_type": "recent_unlock",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0`表示关闭；"
                    " `val` 值定义如下： `bit0~11`表示用户编号；"
                    " `bit12~15`表示开锁方式：( 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁；"
                    " 7：APP开启) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式: （同上定义）"
                ),
            },
            "EVTOP": {
                "description": "操作记录",
                "rw": "R",
                "data_type": "operation_record",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type`可以获知长度，方法是： (`type=0x40+(8-1)*2` or "
                    "`type=0x40+(16-1)*2` or `type=0x40+(32-1)*2`) "
                    "`val`的通用的编码次序是：[1Byte的记录类型][2Byte的用户id]"
                    "[1Byte的用户flag] 用户标志flag：`bit01=11`表示管理员，"
                    "01表示普通用户，00表示已经删除了"
                ),
            },
        },
    },
    "SL_LK_SG": {
        "name": "思哥智能门锁",
        "sensor": {
            "BAT": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "val_direct",
                "detailed_description": "`Val`表示电量值",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "ALM": {
                "description": "告警信息",
                "rw": "R",
                "data_type": "alarm_status",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val` 值定义如下: `bit0`：1为错误报警（输入错误密码或指纹或卡片超过10次就报警) "
                    "`bit1`：1为劫持报警（输入防劫持密码或防劫持指纹开锁就报警) "
                    "`bit2`：1为防撬报警 (锁被撬开) `bit3`：1为机械钥匙报警（使用机械钥匙开 "
                    "`bit4`：1为低电压报警（电池电量不足) `bit5`：1为异动告警 "
                    "`bit6`：1为门铃 `bit7`：1为火警 `bit8`：1为入侵告警 `bit11`：1为恢复出厂告警"
                ),
            },
            "EVTLO": {
                "description": "实时开锁",
                "rw": "R",
                "data_type": "lock_event",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0` 表示关闭；"
                    " `val` 值定义如下: `bit0~11`表示用户编号; 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁(12v开锁信号开锁)；"
                    " 7：APP开启；"
                    " 8：蓝牙开锁；"
                    " 9：手动开锁；"
                    " 15：出错) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式：(同上定义) (注：因有可能存在两种方式同时开启门锁"
                    " 的情况，单开时`bit0~15`为开锁信息，其 他位为0；"
                    "双开时`bit0~15`和`bit16~31` 分别为相应的开锁信息) "
                    "`val`的长度有8/24/32bit三种类型"
                ),
            },
            "HISLK": {
                "description": "最近一次开锁信息",
                "rw": "R",
                "data_type": "recent_unlock",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0`表示关闭；"
                    " `val` 值定义如下： `bit0~11`表示用户编号；"
                    " `bit12~15`表示开锁方式：( 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁；"
                    " 7：APP开启) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式: （同上定义）"
                ),
            },
            "EVTOP": {
                "description": "操作记录",
                "rw": "R",
                "data_type": "operation_record",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type`可以获知长度，方法是： (`type=0x40+(8-1)*2` or "
                    "`type=0x40+(16-1)*2` or `type=0x40+(32-1)*2`) "
                    "`val`的通用的编码次序是：[1Byte的记录类型][2Byte的用户id]"
                    "[1Byte的用户flag] 用户标志flag：`bit01=11`表示管理员，"
                    "01表示普通用户，00表示已经删除了"
                ),
            },
        },
    },
    "SL_LK_YL": {
        "name": "Yale智能门锁",
        "sensor": {
            "BAT": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "val_direct",
                "detailed_description": "`Val`表示电量值",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "ALM": {
                "description": "告警信息",
                "rw": "R",
                "data_type": "alarm_status",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val` 值定义如下: `bit0`：1为错误报警（输入错误密码或指纹或卡片超过10次就报警) "
                    "`bit1`：1为劫持报警（输入防劫持密码或防劫持指纹开锁就报警) "
                    "`bit2`：1为防撬报警 (锁被撬开) `bit3`：1为机械钥匙报警（使用机械钥匙开 "
                    "`bit4`：1为低电压报警（电池电量不足) `bit5`：1为异动告警 "
                    "`bit6`：1为门铃 `bit7`：1为火警 `bit8`：1为入侵告警 `bit11`：1为恢复出厂告警"
                ),
            },
            "EVTLO": {
                "description": "实时开锁",
                "rw": "R",
                "data_type": "lock_event",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0` 表示关闭；"
                    " `val` 值定义如下: `bit0~11`表示用户编号; 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁(12v开锁信号开锁)；"
                    " 7：APP开启；"
                    " 8：蓝牙开锁；"
                    " 9：手动开锁；"
                    " 15：出错) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式：(同上定义) (注：因有可能存在两种方式同时开启门锁"
                    " 的情况，单开时`bit0~15`为开锁信息，其 他位为0；"
                    "双开时`bit0~15`和`bit16~31` 分别为相应的开锁信息) "
                    "`val`的长度有8/24/32bit三种类型"
                ),
            },
            "HISLK": {
                "description": "最近一次开锁信息",
                "rw": "R",
                "data_type": "recent_unlock",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0`表示关闭；"
                    " `val` 值定义如下： `bit0~11`表示用户编号；"
                    " `bit12~15`表示开锁方式：( 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁；"
                    " 7：APP开启) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式: （同上定义）"
                ),
            },
            "EVTOP": {
                "description": "操作记录",
                "rw": "R",
                "data_type": "operation_record",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type`可以获知长度，方法是： (`type=0x40+(8-1)*2` or "
                    "`type=0x40+(16-1)*2` or `type=0x40+(32-1)*2`) "
                    "`val`的通用的编码次序是：[1Byte的记录类型][2Byte的用户id]"
                    "[1Byte的用户flag] 用户标志flag：`bit01=11`表示管理员，"
                    "01表示普通用户，00表示已经删除了"
                ),
            },
        },
    },
    "SL_LK_SWIFTE": {
        "name": "SWIFTE智能门锁",
        "sensor": {
            "BAT": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "val_direct",
                "detailed_description": "`Val`表示电量值",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "ALM": {
                "description": "告警信息",
                "rw": "R",
                "data_type": "alarm_status",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val` 值定义如下: `bit0`：1为错误报警（输入错误密码或指纹或卡片超过10次就报警) "
                    "`bit1`：1为劫持报警（输入防劫持密码或防劫持指纹开锁就报警) "
                    "`bit2`：1为防撬报警 (锁被撬开) `bit3`：1为机械钥匙报警（使用机械钥匙开 "
                    "`bit4`：1为低电压报警（电池电量不足) `bit5`：1为异动告警 "
                    "`bit6`：1为门铃 `bit7`：1为火警 `bit8`：1为入侵告警 `bit11`：1为恢复出厂告警"
                ),
            },
            "EVTLO": {
                "description": "实时开锁",
                "rw": "R",
                "data_type": "lock_event",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0` 表示关闭；"
                    " `val` 值定义如下: `bit0~11`表示用户编号; 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁(12v开锁信号开锁)；"
                    " 7：APP开启；"
                    " 8：蓝牙开锁；"
                    " 9：手动开锁；"
                    " 15：出错) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式：(同上定义) (注：因有可能存在两种方式同时开启门锁"
                    " 的情况，单开时`bit0~15`为开锁信息，其 他位为0；"
                    "双开时`bit0~15`和`bit16~31` 分别为相应的开锁信息) "
                    "`val`的长度有8/24/32bit三种类型"
                ),
            },
            "HISLK": {
                "description": "最近一次开锁信息",
                "rw": "R",
                "data_type": "recent_unlock",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0`表示关闭；"
                    " `val` 值定义如下： `bit0~11`表示用户编号；"
                    " `bit12~15`表示开锁方式：( 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁；"
                    " 7：APP开启) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式: （同上定义）"
                ),
            },
            "EVTOP": {
                "description": "操作记录",
                "rw": "R",
                "data_type": "operation_record",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type`可以获知长度，方法是： (`type=0x40+(8-1)*2` or "
                    "`type=0x40+(16-1)*2` or `type=0x40+(32-1)*2`) "
                    "`val`的通用的编码次序是：[1Byte的记录类型][2Byte的用户id]"
                    "[1Byte的用户flag] 用户标志flag：`bit01=11`表示管理员，"
                    "01表示普通用户，00表示已经删除了"
                ),
            },
        },
    },
    "OD_JIUWANLI_LOCK1": {
        "name": "久万里智能门锁",
        "sensor": {
            "BAT": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "val_direct",
                "detailed_description": "`Val`表示电量值",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "ALM": {
                "description": "告警信息",
                "rw": "R",
                "data_type": "alarm_status",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val` 值定义如下: `bit0`：1为错误报警（输入错误密码或指纹或卡片超过10次就报警) "
                    "`bit1`：1为劫持报警（输入防劫持密码或防劫持指纹开锁就报警) "
                    "`bit2`：1为防撬报警 (锁被撬开) `bit3`：1为机械钥匙报警（使用机械钥匙开 "
                    "`bit4`：1为低电压报警（电池电量不足) `bit5`：1为异动告警 "
                    "`bit6`：1为门铃 `bit7`：1为火警 `bit8`：1为入侵告警 `bit11`：1为恢复出厂告警"
                ),
            },
            "EVTLO": {
                "description": "实时开锁",
                "rw": "R",
                "data_type": "lock_event",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0` 表示关闭；"
                    " `val` 值定义如下: `bit0~11`表示用户编号; 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁(12v开锁信号开锁)；"
                    " 7：APP开启；"
                    " 8：蓝牙开锁；"
                    " 9：手动开锁；"
                    " 15：出错) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式：(同上定义) (注：因有可能存在两种方式同时开启门锁"
                    " 的情况，单开时`bit0~15`为开锁信息，其 他位为0；"
                    "双开时`bit0~15`和`bit16~31` 分别为相应的开锁信息) "
                    "`val`的长度有8/24/32bit三种类型"
                ),
            },
            "HISLK": {
                "description": "最近一次开锁信息",
                "rw": "R",
                "data_type": "recent_unlock",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0`表示关闭；"
                    " `val` 值定义如下： `bit0~11`表示用户编号；"
                    " `bit12~15`表示开锁方式：( 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁；"
                    " 7：APP开启) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式: （同上定义）"
                ),
            },
            "EVTOP": {
                "description": "操作记录",
                "rw": "R",
                "data_type": "operation_record",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type`可以获知长度，方法是： (`type=0x40+(8-1)*2` or "
                    "`type=0x40+(16-1)*2` or `type=0x40+(32-1)*2`) "
                    "`val`的通用的编码次序是：[1Byte的记录类型][2Byte的用户id]"
                    "[1Byte的用户flag] 用户标志flag：`bit01=11`表示管理员，"
                    "01表示普通用户，00表示已经删除了"
                ),
            },
        },
    },
    "SL_P_BDLK": {
        "name": "百度智能门锁",
        "sensor": {
            "BAT": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "val_direct",
                "detailed_description": "`Val`表示电量值",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "ALM": {
                "description": "告警信息",
                "rw": "R",
                "data_type": "alarm_status",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val` 值定义如下: `bit0`：1为错误报警（输入错误密码或指纹或卡片超过10次就报警) "
                    "`bit1`：1为劫持报警（输入防劫持密码或防劫持指纹开锁就报警) "
                    "`bit2`：1为防撬报警 (锁被撬开) `bit3`：1为机械钥匙报警（使用机械钥匙开 "
                    "`bit4`：1为低电压报警（电池电量不足) `bit5`：1为异动告警 "
                    "`bit6`：1为门铃 `bit7`：1为火警 `bit8`：1为入侵告警 `bit11`：1为恢复出厂告警"
                ),
            },
            "EVTLO": {
                "description": "实时开锁",
                "rw": "R",
                "data_type": "lock_event",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0` 表示关闭；"
                    " `val` 值定义如下: `bit0~11`表示用户编号; 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁(12v开锁信号开锁)；"
                    " 7：APP开启；"
                    " 8：蓝牙开锁；"
                    " 9：手动开锁；"
                    " 15：出错) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式：(同上定义) (注：因有可能存在两种方式同时开启门锁"
                    " 的情况，单开时`bit0~15`为开锁信息，其 他位为0；"
                    "双开时`bit0~15`和`bit16~31` 分别为相应的开锁信息) "
                    "`val`的长度有8/24/32bit三种类型"
                ),
            },
            "HISLK": {
                "description": "最近一次开锁信息",
                "rw": "R",
                "data_type": "recent_unlock",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0`表示关闭；"
                    " `val` 值定义如下： `bit0~11`表示用户编号；"
                    " `bit12~15`表示开锁方式：( 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁；"
                    " 7：APP开启) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式: （同上定义）"
                ),
            },
            "EVTOP": {
                "description": "操作记录",
                "rw": "R",
                "data_type": "operation_record",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type`可以获知长度，方法是： (`type=0x40+(8-1)*2` or "
                    "`type=0x40+(16-1)*2` or `type=0x40+(32-1)*2`) "
                    "`val`的通用的编码次序是：[1Byte的记录类型][2Byte的用户id]"
                    "[1Byte的用户flag] 用户标志flag：`bit01=11`表示管理员，"
                    "01表示普通用户，00表示已经删除了"
                ),
            },
        },
    },
    # 2.8.2 C100/C200门锁系列 (C100/C200 Door Lock Series)
    "SL_LK_TY": {
        "name": "C200门锁",
        "sensor": {
            "BAT": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "val_direct",
                "detailed_description": "`Val`表示电量值",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "ALM": {
                "description": "告警信息",
                "rw": "R",
                "data_type": "alarm_status",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val` 值定义如下: `bit0`：1为错误报警（输入错误密码或指纹或卡片超过10次就报警) "
                    "`bit1`：1为劫持报警（输入防劫持密码或防劫持指纹开锁就报警) "
                    "`bit2`：1为防撬报警 (锁被撬开) `bit3`：1为机械钥匙报警（使用机械钥匙开 "
                    "`bit4`：1为低电压报警（电池电量不足) `bit5`：1为异动告警 "
                    "`bit6`：1为门铃 `bit7`：1为火警 `bit8`：1为入侵告警 `bit11`：1为恢复出厂告警"
                ),
            },
            "EVTLO": {
                "description": "实时开锁",
                "rw": "R",
                "data_type": "lock_event",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0` 表示关闭；"
                    " `val` 值定义如下: `bit0~11`表示用户编号; 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁(12v开锁信号开锁)；"
                    " 7：APP开启；"
                    " 8：蓝牙开锁；"
                    " 9：手动开锁；"
                    " 15：出错) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式：(同上定义) (注：因有可能存在两种方式同时开启门锁"
                    " 的情况，单开时`bit0~15`为开锁信息，其 他位为0；"
                    "双开时`bit0~15`和`bit16~31` 分别为相应的开锁信息) "
                    "`val`的长度有8/24/32bit三种类型"
                ),
            },
            "HISLK": {
                "description": "最近一次开锁信息",
                "rw": "R",
                "data_type": "recent_unlock",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0`表示关闭；"
                    " `val` 值定义如下： `bit0~11`表示用户编号；"
                    " `bit12~15`表示开锁方式：( 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁；"
                    " 7：APP开启) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式: （同上定义）"
                ),
            },
            "EVTBEL": {
                "description": "门铃消息",
                "rw": "R",
                "data_type": "doorbell_message",
                "conversion": "val_direct",
                "detailed_description": "门铃消息状态，与EVTLO共享，`type&1=1`表示有门铃消息",
            },
        },
    },
    "SL_LK_DJ": {
        "name": "C100门锁",
        "sensor": {
            "BAT": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "val_direct",
                "detailed_description": "`Val`表示电量值",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "ALM": {
                "description": "告警信息",
                "rw": "R",
                "data_type": "alarm_status",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val` 值定义如下: `bit0`：1为错误报警（输入错误密码或指纹或卡片超过10次就报警) "
                    "`bit1`：1为劫持报警（输入防劫持密码或防劫持指纹开锁就报警) "
                    "`bit2`：1为防撬报警 (锁被撬开) `bit3`：1为机械钥匙报警（使用机械钥匙开 "
                    "`bit4`：1为低电压报警（电池电量不足) `bit5`：1为异动告警 "
                    "`bit6`：1为门铃 `bit7`：1为火警 `bit8`：1为入侵告警 `bit11`：1为恢复出厂告警"
                ),
            },
            "EVTLO": {
                "description": "实时开锁",
                "rw": "R",
                "data_type": "lock_event",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0` 表示关闭；"
                    " `val` 值定义如下: `bit0~11`表示用户编号; 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁(12v开锁信号开锁)；"
                    " 7：APP开启；"
                    " 8：蓝牙开锁；"
                    " 9：手动开锁；"
                    " 15：出错) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式：(同上定义) (注：因有可能存在两种方式同时开启门锁"
                    " 的情况，单开时`bit0~15`为开锁信息，其 他位为0；"
                    "双开时`bit0~15`和`bit16~31` 分别为相应的开锁信息) "
                    "`val`的长度有8/24/32bit三种类型"
                ),
            },
            "HISLK": {
                "description": "最近一次开锁信息",
                "rw": "R",
                "data_type": "recent_unlock",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0`表示关闭；"
                    " `val` 值定义如下： `bit0~11`表示用户编号；"
                    " `bit12~15`表示开锁方式：( 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁；"
                    " 7：APP开启) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式: （同上定义）"
                ),
            },
            "EVTBEL": {
                "description": "门铃消息",
                "rw": "R",
                "data_type": "doorbell_message",
                "conversion": "val_direct",
                "detailed_description": "门铃消息状态，与EVTLO共享，`type&1=1`表示有门铃消息",
            },
        },
    },
    # ================= 2.9 温控器 (Climate Controller) =================
    # 2.9.1 智控器空调面板 (Central AIR Board)
    "V_AIR_P": {
        "name": "智控器空调面板",
        "climate": {
            "O": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1`,`val` 值忽略表示打开；"
                    "`type&1==0`,`val` 值忽略表示关闭；"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开空调",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭空调",
                    },
                },
            },
            "MODE": {
                "description": "模式",
                "rw": "RW",
                "data_type": "hvac_mode",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type==0xCE`,`val` 值表示模式，定义如下：1:Auto自动; 2:Fan 吹风; "
                    "3:Cool 制冷; 4:Heat 制热; 5:Dry除湿"
                ),
                "commands": {
                    "set_mode": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置模式，val=模式值",
                    },
                },
            },
            "F": {
                "description": "风速",
                "rw": "RW",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type==0xCE`,`val` 值表示风速，定义如下：`val<30`:低档; `val<65`:中档; "
                    "`val>=65`:高档"
                ),
                "commands": {
                    "set_fan_speed": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置风速，低档val=15; 中档val=45; 高档val=75",
                        "fan_modes": {
                            "low": 15,
                            "medium": 45,
                            "high": 75,
                        },
                    },
                },
            },
            "tT": {
                "description": "目标温度",
                "rw": "RW",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": (
                    "`type==0x88`,`v` 值表示实际温度值，`val` 值表示原始温度值，它是温度值*10"
                ),
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_UNKNOWN_136,
                        "description": "设置目标温度，val=目标温度值*10",
                    },
                },
            },
            "T": {
                "description": "当前温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": (
                    "`type==0x08`,`v` 值表示实际温度值，"
                    "`val` 值表示原始温度值，它是温度值*10"
                ),
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
        },
    },
    "SL_TR_ACIPM": {
        "name": "新风系统",
        "climate": {
            "P1": {
                "description": "系统配置",
                "rw": "RW",
                "data_type": "hvac_mode",
                "conversion": "val_direct",
                "detailed_description": "1:自动; 2:手动; 3:定时",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                    "set_mode": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置模式，val=模式值",
                    },
                },
            },
            "P2": {
                "description": "风速",
                "rw": "RW",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val`值定义如下: 0:关闭; 1:1档; 2:2档; 3:3档 注意：只有在模式处于手动模式下"
                    "该参数设置才有效"
                ),
                "commands": {
                    "set_config": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置风速",
                        "fan_modes": {
                            "low": 1,
                            "medium": 2,
                            "high": 3,
                        },
                    },
                },
            },
            "P3": {
                "description": "设置VOC",
                "rw": "RW",
                "data_type": "voc_concentration",
                "conversion": "val_div_10",
                "detailed_description": "`val`值减小10倍为真实值，`v`值表示实际值(单位：ppm)",
                "device_class": "volatile_organic_compounds",
                "unit_of_measurement": "ppm",
                "commands": {
                    "set_voc": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置VOC值，需要将真实值扩大10倍",
                    },
                },
            },
        },
        "sensor": {
            "P4": {
                "description": "VOC",
                "rw": "R",
                "data_type": "voc_concentration",
                "conversion": "val_div_10",
                "detailed_description": (
                    "`val`值表示原始VOC值，且`val`值减小10倍为真实值，"
                    "`v`值表示实际值(单位：ppm)"
                ),
                "device_class": "volatile_organic_compounds",
                "unit_of_measurement": "ppm",
                "state_class": "measurement",
            },
            "P5": {
                "description": "PM2.5",
                "rw": "R",
                "data_type": "pm25",
                "conversion": "v_field",
                "detailed_description": "`val`值表示原始PM2.5值，`v`为实际值(单位：μg/m³)",
                "device_class": "pm25",
                "unit_of_measurement": "μg/m³",
                "state_class": "measurement",
            },
            "P6": {
                "description": "当前温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "detailed_description": "`val`值除以10为真实温度值，`v`值表示实际值(单位：℃)",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
        },
    },
    "SL_CP_DN": {
        "name": "地暖温控器",
        "climate": {
            "P1": {
                "description": "系统配置",
                "rw": "RW",
                "data_type": "hvac_mode",
                "conversion": "val_direct",
                "detailed_description": "该IO的type和val字段说明，详见文档表2-17-1",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                    "set_config": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置配置，需要保留其他位",
                    },
                },
            },
            "P3": {
                "description": "目标温度",
                "rw": "RW",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "detailed_description": "`val`值表示原始温度值，真实温度值为原始值除以10倍，`v`值表示实际值",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置目标温度",
                    },
                },
            },
        },
        "binary_sensor": {
            "P2": {
                "description": "继电器开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                "device_class": "opening",
            },
        },
        "sensor": {
            "P4": {
                "description": "室内温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "detailed_description": "`val`值表示原始温度值，真实温度值为原始值除以10倍，精度为0.1，`v`值表示实际值",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
            "P5": {
                "description": "底版温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "detailed_description": "`val`值表示原始温度值，真实温度值为原始值除以10，精度为0.1，`v`值表示实际值",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
        },
    },
    "SL_CP_AIR": {
        "name": "风机盘管",
        "climate": {
            "P1": {
                "description": "系统配置",
                "rw": "RW",
                "data_type": "hvac_mode",
                "conversion": "val_direct",
                "detailed_description": "该IO的type和val字段说明，详见文档表2-18-1",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                    "set_config": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置配置，需要保留其他位",
                    },
                },
            },
            "P4": {
                "description": "目标温度",
                "rw": "RW",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "detailed_description": "`val`值表示原始温度值，真实温度值为原始值除以10倍，精度为0.5，`v`值表示实际值",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置目标温度",
                    },
                },
            },
        },
        "binary_sensor": {
            "P2": {
                "description": "阀门状态",
                "rw": "R",
                "data_type": "valve_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type`值定义如下: 0x80:阀门关; 0x81:阀门开",
                "device_class": "opening",
            },
        },
        "sensor": {
            "P3": {
                "description": "风速状态",
                "rw": "R",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "detailed_description": "`val`值定义如下: 0:自动; 1:低速; 2:中速; 3:高速",
            },
            "P5": {
                "description": "室内温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "detailed_description": "`val`值表示原始温度值，真实温度值为原始值除以10，精度为0.1，`v`值表示实际值",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
        },
    },
    "SL_UACCB": {
        "name": "空调控制面板",
        "climate": {
            "P1": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1`,`val`值忽略表示打开；"
                    "`type&1==0`，`val`值忽略表示关闭"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开空调",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭空调",
                    },
                },
            },
            "P2": {
                "description": "模式",
                "rw": "RW",
                "data_type": "hvac_mode",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type==0xCE`，`val`值表示模式，定义如下：1:Auto自动；2:Fan吹风；"
                    "3:Cool制冷；4:Heat制热；5:Dry除湿"
                ),
                "commands": {
                    "set_config": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置模式",
                    },
                },
            },
            "P3": {
                "description": "目标温度",
                "rw": "RW",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": (
                    "`type==0x88`,`v`值表示实际温度值，"
                    "`val`值表示原始温度值，它是温度值*10"
                ),
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_UNKNOWN_136,
                        "description": "设置目标温度，val=目标温度值*10",
                    },
                },
            },
            "P4": {
                "description": "风速",
                "rw": "RW",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "detailed_description": "`val<30`:低档；`val<65`:中档；`val>=65`:高档",
                "commands": {
                    "set_fan_speed": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置风速，低档val=15；中档val=45；高档val=75",
                    },
                },
            },
        },
        "sensor": {
            "P6": {
                "description": "当前温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": (
                    "`type==0x08`,`v`值表示实际温度值，"
                    "`val`值表示原始温度值，它是温度值*10"
                ),
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
                "description": "开关及系统配置",
                "rw": "RW",
                "data_type": "hvac_mode",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1`,`val`值忽略表示打开；"
                    "该IO的type和val字段说明，详见文档表2-19-1"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                    "set_config": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置配置，需要保留其他位",
                    },
                },
            },
            "P3": {
                "description": "目标温度",
                "rw": "RW",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`v`值表示实际温度值，`val`值表示原始温度值，它是温度值*10",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_UNKNOWN_136,
                        "description": "设置目标温度，val=目标温度值*10",
                    },
                },
            },
        },
        "sensor": {
            "P4": {
                "description": "当前温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`v`值表示实际温度值，`val`值表示原始温度值，它是温度值*10",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
            "P5": {
                "description": "告警",
                "rw": "R",
                "data_type": "alarm_status",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val`表示告警信息，可参考：bit0:高温保护；bit1:低温保护；bit2:int_sensor；"
                    "bit3:ext_sensor；bit4:低电量；bit5:设备掉线"
                ),
            },
            "P6": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据 `val` 电压值换算的"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
        "binary_sensor": {
            "P5": {
                "description": "告警状态",
                "rw": "R",
                "data_type": "alarm_status",
                "conversion": "val_direct",
                "detailed_description": "基于P5传感器值的二进制告警状态，有告警时为True",
                "device_class": "problem",
            },
        },
    },
    "SL_DN": {
        "name": "星玉地暖",
        "climate": {
            "P1": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1`，`val`值忽略表示打开；"
                    "`type&1==0`，`val`值忽略表示关闭"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开地暖",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭地暖",
                    },
                },
            },
            "P2": {
                "description": "模式",
                "rw": "RW",
                "data_type": "config_bitmask",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val`值定义如下：温度限制0-5位：17+val(17~80)；回差6-9位：使用温度(v+1)*0.5作为回差参数；"
                    "控温模式10-11位：0/1:in；2:out；3:all"
                ),
                "commands": {
                    "set_config": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置模式配置",
                    },
                },
            },
            "P8": {
                "description": "目标温度",
                "rw": "RW",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "detailed_description": "`val`值表示原始温度值，真实温度值为原始值除以10倍，精度为0.5，`v`值表示实际值",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置目标温度",
                    },
                },
            },
        },
        "binary_sensor": {
            "P3": {
                "description": "阀门状态",
                "rw": "R",
                "data_type": "valve_status",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "type值定义如下：0x80:阀门关；0x81:阀门开；"
                    "`val`值类型为浮点数值，表示的是电量统计"
                ),
                "device_class": "opening",
            },
        },
        "sensor": {
            "P4": {
                "description": "室内温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "detailed_description": "`val`值表示原始温度值，真实温度值为原始值除以10倍，精度为0.1，`v`值表示实际值",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
            "P9": {
                "description": "底版温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "detailed_description": "`val`值表示原始温度值，真实温度值为原始值除以10，精度为0.1，`v`值表示实际值",
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
        "dynamic": True,
        "control_modes": {
            "free_mode": {
                "condition": "(P1>>24)&0xe == 0",
                "binary_sensor": {
                    "P5": {
                        "description": "Status1状态输入",
                        "rw": "R",
                        "data_type": "status_input",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示有状态触发，仅自由模式有效",
                        "device_class": "moving",
                    },
                    "P6": {
                        "description": "Status2状态输入",
                        "rw": "R",
                        "data_type": "status_input",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示有状态触发，仅自由模式有效",
                        "device_class": "moving",
                    },
                    "P7": {
                        "description": "Status3状态输入",
                        "rw": "R",
                        "data_type": "status_input",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示有状态触发，仅自由模式有效",
                        "device_class": "moving",
                    },
                },
            },
            "cover_mode": {
                "condition": "(P1>>24)&0xe in [2,4]",
                "cover": {
                    "P2": {
                        "description": "打开窗帘",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示打开窗帘",
                        "commands": {
                            "open": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开窗帘",
                            },
                        },
                    },
                    "P3": {
                        "description": "关闭窗帘",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示关闭窗帘",
                        "commands": {
                            "close": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "关闭窗帘",
                            },
                        },
                    },
                    "P4": {
                        "description": "停止窗帘",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示停止窗帘",
                        "commands": {
                            "stop": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "停止窗帘",
                            },
                        },
                    },
                },
            },
            "switch_mode": {
                "condition": "(P1>>24)&0xe in [8,10]",
                "switch": {
                    "P2": {
                        "description": "Ctrl1第一路开关",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                        },
                    },
                    "P3": {
                        "description": "Ctrl2第二路开关",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                        },
                    },
                    "P4": {
                        "description": "Ctrl3第三路开关",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示打开",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                        },
                    },
                },
            },
        },
        "sensor": {
            "P1": {
                "description": "控制参数",
                "rw": "RW",
                "data_type": "control_config",
                "conversion": "val_direct",
                "detailed_description": (
                    "32位控制参数：31bit软件配置标志，24-27bit工作模式，"
                    "16-18bit延时使能，0-15bit延时秒数"
                ),
                "commands": {
                    "set_config": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置控制参数，需要保留未修改的bit位",
                    },
                },
            },
        },
    },
    # 2.10.2 通用控制器HA (HA Interface Adapter)
    "SL_JEMA": {
        "name": "通用控制器HA",
        "dynamic": True,
        "control_modes": {
            "free_mode": {
                "condition": "(P1>>24)&0xe == 0",
                "binary_sensor": {
                    "P5": {
                        "description": "Status1状态输入",
                        "rw": "R",
                        "data_type": "status_input",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示有状态触发，仅自由模式有效",
                        "device_class": "moving",
                    },
                    "P6": {
                        "description": "Status2状态输入",
                        "rw": "R",
                        "data_type": "status_input",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示有状态触发，仅自由模式有效",
                        "device_class": "moving",
                    },
                    "P7": {
                        "description": "Status3状态输入",
                        "rw": "R",
                        "data_type": "status_input",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示有状态触发，仅自由模式有效",
                        "device_class": "moving",
                    },
                },
            },
            "cover_mode": {
                "condition": "(P1>>24)&0xe in [2,4]",
                "cover": {
                    "P2": {
                        "description": "Ctrl1打开窗帘",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                        "commands": {
                            "open": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开窗帘",
                            },
                        },
                    },
                    "P3": {
                        "description": "Ctrl2关闭窗帘",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                        "commands": {
                            "close": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "关闭窗帘",
                            },
                        },
                    },
                    "P4": {
                        "description": "Ctrl3停止窗帘",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                        "commands": {
                            "stop": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "停止窗帘",
                            },
                        },
                    },
                },
            },
            "switch_mode": {
                "condition": "(P1>>24)&0xe in [8,10]",
                "switch": {
                    "P2": {
                        "description": "Ctrl1第一路开关",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                        },
                    },
                    "P3": {
                        "description": "Ctrl2第二路开关",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                        },
                    },
                    "P4": {
                        "description": "Ctrl3第三路开关",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                        },
                    },
                },
            },
        },
        "switch": {
            "P8": {
                "description": "HA1独立开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P9": {
                "description": "HA2独立开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P10": {
                "description": "HA3独立开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "sensor": {
            "P1": {
                "description": "控制参数",
                "rw": "RW",
                "data_type": "control_config",
                "conversion": "val_direct",
                "detailed_description": (
                    "32位控制参数：31bit恒为1(软件可配置)，24-27bit工作模式，"
                    "16-18bit延时使能，0-15bit延时秒数"
                ),
                "commands": {
                    "set_config": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置控制参数，需要保留未修改的bit位",
                    },
                },
            },
        },
    },
    # ================= 第三方设备 (Third-party Devices) =================
    "V_DLT645_P": {
        "name": "DLT电量计量器",
        "sensor": {
            "EE": {
                "description": "用电量",
                "rw": "R",
                "data_type": "energy_consumption",
                "conversion": "ieee754_or_friendly",
                "unit_of_measurement": "kWh",
                "device_class": "energy",
                "state_class": "total_increasing",
                "detailed_description": (
                    "为累计用电量，`val` 值为为IEEE754浮点数的32位整数表示，"
                    "`v` 值为浮点数，单位为度(kwh)。注意：`v` 值可以直接使用，"
                    "若不存在`v` 值，则需要手动转换。其值类型为IEEE 754浮点数的32位整数布局。"
                ),
            },
            "EP": {
                "description": "功率",
                "rw": "R",
                "data_type": "power",
                "conversion": "ieee754_or_friendly",
                "unit_of_measurement": "W",
                "device_class": "power",
                "state_class": "measurement",
                "detailed_description": (
                    "为当前负载功率，`v` 值为浮点数，单位为w。注意：`v` 值可以直接使用，若不存在`v` 值，"
                    "则需要手动转换。其值类型为IEEE 754浮点数的32位整数布局。"
                ),
            },
        },
    },
    "V_DUNJIA_P": {
        "name": "X100人脸识别可视门锁",
        "sensor": {
            "BAT": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "val_direct",
                "detailed_description": "`Val`表示电量值",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
            "ALM": {
                "description": "告警信息",
                "rw": "R",
                "data_type": "alarm_status",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val` 值定义如下: `bit0`：1为错误报警（输入错误密码或指纹或卡片超过10次就报警) "
                    "`bit1`：1为劫持报警（输入防劫持密码或防劫持指纹开锁就报警) "
                    "`bit2`：1为防撬报警 (锁被撬开) `bit3`：1为机械钥匙报警（使用机械钥匙开 "
                    "`bit4`：1为低电压报警（电池电量不足) `bit5`：1为异动告警 "
                    "`bit6`：1为门铃 `bit7`：1为火警 `bit8`：1为入侵告警 `bit11`：1为恢复出厂告警"
                ),
            },
            "EVTLO": {
                "description": "实时开锁",
                "rw": "R",
                "data_type": "lock_event",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0` 表示关闭；"
                    " `val` 值定义如下: `bit0~11`表示用户编号; 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁(12v开锁信号开锁)；"
                    " 7：APP开启；"
                    " 8：蓝牙开锁；"
                    " 9：手动开锁；"
                    " 15：出错) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式：(同上定义) (注：因有可能存在两种方式同时开启门锁"
                    " 的情况，单开时`bit0~15`为开锁信息，其 他位为0；"
                    "双开时`bit0~15`和`bit16~31` 分别为相应的开锁信息) "
                    "`val`的长度有8/24/32bit三种类型"
                ),
            },
            "HISLK": {
                "description": "最近一次开锁信息",
                "rw": "R",
                "data_type": "recent_unlock",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示打开；"
                    " `type&1==0`表示关闭；"
                    " `val` 值定义如下： `bit0~11`表示用户编号；"
                    " `bit12~15`表示开锁方式：( 0：未定义；"
                    " 1：密码；"
                    " 2：指纹；"
                    " 3:`NFC`; 4：机械钥匙；"
                    " 5：远程开锁；"
                    " 7：APP开启) `bit16~27`表示用户编号；"
                    " `bit28~31`表示开锁方式: （同上定义）"
                ),
            },
        },
    },
    "V_HG_L": {
        "name": "极速开关组",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L3": {
                "description": "第三路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
    },
    "V_HG_XX": {
        "name": "极速虚拟设备",
        "switch": {
            "P1": {
                "description": "虚拟开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
    },
    "V_SZJSXR_P": {
        "name": "新风控制器(深圳建设新风)",
        "climate": {
            "O": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1`,`val` 值忽略表示打开；"
                    "`type&1==0`,`val` 值忽略表示关闭；"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开空调",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭空调",
                    },
                },
            },
            "MODE": {
                "description": "模式",
                "rw": "RW",
                "data_type": "hvac_mode",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type==0xCE`,`val` 值表示模式，定义如下：1:Auto自动; 2:Fan 吹风; "
                    "3:Cool 制冷; 4:Heat 制热; 5:Dry除湿"
                ),
                "commands": {
                    "set_mode": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置模式，val=模式值",
                    },
                },
            },
            "F": {
                "description": "风速",
                "rw": "RW",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type==0xCE`,`val` 值表示风速，定义如下：`val<30`:低档; `val<65`:中档; "
                    "`val>=65`:高档"
                ),
                "commands": {
                    "set_fan_speed": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置风速，低档val=15; 中档val=45; 高档val=75",
                        "fan_modes": {
                            "low": 15,
                            "medium": 45,
                            "high": 75,
                        },
                    },
                },
            },
            "tT": {
                "description": "目标温度",
                "rw": "RW",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": (
                    "`type==0x88`,`v` 值表示实际温度值，`val` 值表示原始温度值，它是温度值*10"
                ),
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_UNKNOWN_136,
                        "description": "设置目标温度，val=目标温度值*10",
                    },
                },
            },
            "T": {
                "description": "当前温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": (
                    "`type==0x08`,`v` 值表示实际温度值，"
                    "`val` 值表示原始温度值，它是温度值*10"
                ),
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
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1`,`val` 值忽略表示打开；"
                    "`type&1==0`,`val` 值忽略表示关闭；"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开空调",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭空调",
                    },
                },
            },
            "MODE": {
                "description": "模式",
                "rw": "RW",
                "data_type": "hvac_mode",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type==0xCE`,`val` 值表示模式，定义如下：1:Auto自动; 2:Fan 吹风; "
                    "3:Cool 制冷; 4:Heat 制热; 5:Dry除湿"
                ),
                "commands": {
                    "set_mode": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置模式，val=模式值",
                    },
                },
            },
            "F": {
                "description": "风速",
                "rw": "RW",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type==0xCE`,`val` 值表示风速，定义如下：`val<30`:低档; `val<65`:中档; "
                    "`val>=65`:高档"
                ),
                "commands": {
                    "set_fan_speed": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置风速，低档val=15; 中档val=45; 高档val=75",
                        "fan_modes": {
                            "low": 15,
                            "medium": 45,
                            "high": 75,
                        },
                    },
                },
            },
            "tT": {
                "description": "目标温度",
                "rw": "RW",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": (
                    "`type==0x88`,`v` 值表示实际温度值，`val` 值表示原始温度值，它是温度值*10"
                ),
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_UNKNOWN_136,
                        "description": "设置目标温度，val=目标温度值*10",
                    },
                },
            },
            "T": {
                "description": "当前温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": (
                    "`type==0x08`,`v` 值表示实际温度值，"
                    "`val` 值表示原始温度值，它是温度值*10"
                ),
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
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1` 表示打开(忽略 `val` 值)；"
                    "`type&1==0` 表示关闭(忽略 `val` 值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "MODE": {
                "description": "工作模式",
                "rw": "RW",
                "data_type": "mode_config",
                "conversion": "val_direct",
                "detailed_description": "`val` 值为模式位掩码，0-1位和2-3位分别控制不同功能",
                "commands": {
                    "set_mode": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置工作模式",
                    },
                },
            },
        },
        "sensor": {
            "F1": {
                "description": "送风风速",
                "rw": "R",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val` 值表示风速，0:停止, val<30:低档, "
                    "val<65:中档, val>=65:高档"
                ),
            },
            "F2": {
                "description": "排风风速",
                "rw": "R",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val` 值表示风速，0:停止, val<30:低档, "
                    "val<65:中档, val>=65:高档"
                ),
            },
            "T": {
                "description": "环境温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val` 值除以10为真实温度值，`v` 值表示实际值(单位：℃)",
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
                "description": "传感器数值",
                "rw": "R",
                "data_type": "generic_value",
                "conversion": "ieee754_or_friendly",
                "detailed_description": (
                    "为当前接入设备的值，`val` 值为IEEE754浮点数的32位整数表示，"
                    "`v` 值为浮点数，单位为具体接入设备当前的单位"
                ),
            },
        },
    },
    "V_485_P": {
        "name": "485控制器",
        "wildcard_support": True,
        "switch": {
            "O": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "type&1=1，`val` 值忽略表示打开；"
                    "type&1=0，`val` 值忽略表示关闭；"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "L*": {
                "description": "多路开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "type&1=1,`val` 值忽略表示打开；type&1=0，`val` 值忽略表示关闭；"
                    "(Lx，x为1时，即L1表示第一位开关的IO控制口，"
                    "多位开关时x可取值为3，L3则表示第三位开关的IO控制口）"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "sensor": {
            "P1": {
                "description": "当前接入设备的值",
                "rw": "R",
                "data_type": "generic_value",
                "conversion": "ieee754_or_friendly",
                "detailed_description": (
                    "为当前接入设备的值，`val` 值为为IEEE754浮点数的32位整数表示，"
                    "`v` 值为浮点数，单位为具体接入设备当前的单位。如：接入设备为压力传感器，"
                    "那么val为当前接入设备的压力值，单位以接入设备的单位设定为准。"
                ),
            },
            "EE": {
                "description": "用电量",
                "rw": "R",
                "data_type": "energy_consumption",
                "conversion": "ieee754_or_friendly",
                "unit_of_measurement": "kWh",
                "device_class": "energy",
                "state_class": "total_increasing",
                "detailed_description": (
                    "为累计用电量，`val` 值为为IEEE754浮点数的32位整数表示，"
                    "`v` 值为浮点数，单位为度(kwh)。"
                ),
            },
            "EE*": {
                "description": "多路用电量",
                "rw": "R",
                "data_type": "energy_consumption",
                "conversion": "ieee754_or_friendly",
                "unit_of_measurement": "kWh",
                "device_class": "energy",
                "state_class": "total_increasing",
                "detailed_description": (
                    "为累计用电量，`val` 值为为IEEE754浮点数的32位整数表示，"
                    "`v` 值为浮点数，单位为度(kwh)。(EEx，x取值为数字)"
                ),
            },
            "EP": {
                "description": "功率",
                "rw": "R",
                "data_type": "power",
                "conversion": "ieee754_or_friendly",
                "unit_of_measurement": "W",
                "device_class": "power",
                "state_class": "measurement",
                "detailed_description": "为当前负载功率，`v` 值为浮点数，单位为w。",
            },
            "EPF": {
                "description": "功率因数",
                "rw": "R",
                "data_type": "power_factor",
                "conversion": "friendly_value",
                "device_class": "power_factor",
                "state_class": "measurement",
                "detailed_description": "功率因数，单位无。",
            },
            "EPF*": {
                "description": "多路功率因数",
                "rw": "R",
                "data_type": "power_factor",
                "conversion": "friendly_value",
                "device_class": "power_factor",
                "state_class": "measurement",
                "detailed_description": "功率因数，单位无。(EPFx，x取值为数字)",
            },
            "EF": {
                "description": "交流电频率",
                "rw": "R",
                "data_type": "frequency",
                "conversion": "friendly_value",
                "unit_of_measurement": "Hz",
                "device_class": "frequency",
                "state_class": "measurement",
                "detailed_description": "交流电频率，单位为HZ。",
            },
            "EF*": {
                "description": "多路交流电频率",
                "rw": "R",
                "data_type": "frequency",
                "conversion": "friendly_value",
                "unit_of_measurement": "Hz",
                "device_class": "frequency",
                "state_class": "measurement",
                "detailed_description": "交流电频率，单位为HZ。(EFx，x取值为数字)",
            },
            "EI": {
                "description": "电流",
                "rw": "R",
                "data_type": "current",
                "conversion": "friendly_value",
                "unit_of_measurement": "A",
                "device_class": "current",
                "state_class": "measurement",
                "detailed_description": "电流，单位为A。",
            },
            "EI*": {
                "description": "多路电流",
                "rw": "R",
                "data_type": "current",
                "conversion": "friendly_value",
                "unit_of_measurement": "A",
                "device_class": "current",
                "state_class": "measurement",
                "detailed_description": "电流，单位为A。(EIx，x取值为数字)",
            },
            "EV": {
                "description": "电压",
                "rw": "R",
                "data_type": "voltage",
                "conversion": "friendly_value",
                "unit_of_measurement": "V",
                "device_class": "voltage",
                "state_class": "measurement",
                "detailed_description": "电压，单位为V。",
            },
            "EV*": {
                "description": "多路电压",
                "rw": "R",
                "data_type": "voltage",
                "conversion": "friendly_value",
                "unit_of_measurement": "V",
                "device_class": "voltage",
                "state_class": "measurement",
                "detailed_description": "电压，单位为V。(EVx，x取值为数字)",
            },
            "T": {
                "description": "温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "friendly_value",
                "unit_of_measurement": "°C",
                "device_class": "temperature",
                "state_class": "measurement",
                "detailed_description": "`val` 值表示原始温度值，`v` 值为实际值(单位：℃)。",
            },
            "H": {
                "description": "湿度",
                "rw": "R",
                "data_type": "humidity",
                "conversion": "friendly_value",
                "unit_of_measurement": "%",
                "device_class": "humidity",
                "state_class": "measurement",
                "detailed_description": "`val` 值表示原始湿度值，`v` 值为实际值(单位：%)。",
            },
            "PM": {
                "description": "PM2.5",
                "rw": "R",
                "data_type": "pm25",
                "conversion": "friendly_value",
                "unit_of_measurement": "µg/m³",
                "device_class": "pm25",
                "state_class": "measurement",
                "detailed_description": "`val` 值表示PM2.5值，`v` 值为实际值(单位：ug/m³)。",
            },
            "PMx": {
                "description": "PM10",
                "rw": "R",
                "data_type": "pm10",
                "conversion": "friendly_value",
                "unit_of_measurement": "µg/m³",
                "device_class": "pm10",
                "state_class": "measurement",
                "detailed_description": "`val` 值表示PM10值，`v` 值为实际值(单位：ug/m³)。",
            },
            "COPPM": {
                "description": "一氧化碳",
                "rw": "R",
                "data_type": "co_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "ppm",
                "device_class": "carbon_monoxide",
                "state_class": "measurement",
                "detailed_description": "`val` 值表示co浓度值，`v` 值为实际值(单位：ppm)。",
            },
            "CO2PPM": {
                "description": "二氧化碳",
                "rw": "R",
                "data_type": "co2_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "ppm",
                "device_class": "carbon_dioxide",
                "state_class": "measurement",
                "detailed_description": "`val` 值表示co2浓度值，`v` 值为实际值(单位：ppm)。",
            },
            "CH20PPM": {
                "description": "甲醛",
                "rw": "R",
                "data_type": "formaldehyde_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "ppm",
                "device_class": "volatile_organic_compounds",
                "state_class": "measurement",
                "detailed_description": "`val` 值表示甲醛原始浓度值，`v` 值为实际值(单位：ppm)。",
            },
            "O2VOL": {
                "description": "氧气",
                "rw": "R",
                "data_type": "oxygen_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "vol%",
                "state_class": "measurement",
                "detailed_description": "`val` 值表示氧气原始浓度值，`v` 值为实际值(单位：vol%)。",
            },
            "NH3PPM": {
                "description": "氨气",
                "rw": "R",
                "data_type": "ammonia_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "ppm",
                "state_class": "measurement",
                "detailed_description": "`val` 值表示氨气原始浓度值，`v` 值为实际值(单位：ppm)。",
            },
            "H2SPPM": {
                "description": "硫化氢",
                "rw": "R",
                "data_type": "h2s_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "ppm",
                "state_class": "measurement",
                "detailed_description": "`val` 值表示硫化氢原始浓度值，`v` 值为实际值(单位：ppm)。",
            },
            "TVOC": {
                "description": "TVOC",
                "rw": "R",
                "data_type": "tvoc_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "mg/m³",
                "device_class": "volatile_organic_compounds",
                "state_class": "measurement",
                "detailed_description": "`val` 值表示TVOC原始浓度值，`v` 值为实际值(单位：mg/m³)。",
            },
            "PHM": {
                "description": "噪音",
                "rw": "R",
                "data_type": "noise_level",
                "conversion": "friendly_value",
                "unit_of_measurement": "dB",
                "device_class": "sound_pressure",
                "state_class": "measurement",
                "detailed_description": "`val` 值表示噪音原始值，`v` 值为实际值(单位：dB)。",
            },
            "SMOKE": {
                "description": "烟雾",
                "rw": "R",
                "data_type": "smoke_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "ppm",
                "state_class": "measurement",
                "detailed_description": "`val` 值表示烟雾原始浓度值，`v` 值为实际值(单位：ppm)。",
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
                "description": "夜灯控制",
                "rw": "RW",
                "data_type": "infrared_light",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示开启红外夜灯；`type&1==0`表示关闭红外夜灯",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开启夜灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭夜灯",
                    },
                },
            },
        },
        "binary_sensor": {
            "P2": {
                "description": "人体感应",
                "rw": "R",
                "data_type": "motion_status",
                "conversion": "val_direct",
                "detailed_description": "`val`值定义如下：0：没有检测到移动，1：有检测到移动",
                "device_class": "motion",
            },
        },
        "sensor": {
            "P3": {
                "description": "环境光照",
                "rw": "R",
                "data_type": "illuminance",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始光照值，`v` 值表示实际值(单位：lux)",
                "device_class": "illuminance",
                "unit_of_measurement": "lx",
                "state_class": "measurement",
            },
            "P4": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据 `val` 电压值换算的"
                ),
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
                "description": "按键状态",
                "rw": "R",
                "data_type": "keypad_status",
                "conversion": "val_direct",
                "detailed_description": "`val`值表示按键编号，0表示无按键按下，其他值表示对应按键编号",
                "device_class": "moving",
            },
            "TR": {
                "description": "防拆状态",
                "rw": "R",
                "data_type": "tamper_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`则表示触发防拆警报；`type&1==0`则表示状态正常",
                "device_class": "tamper",
            },
        },
        "sensor": {
            "T": {
                "description": "温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val`值表示原始温度值，它是实际温度值*10，`v`值表示实际值(单位：℃)",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
                "state_class": "measurement",
            },
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val`值表示原始电压值，`v`值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据`val`电压值换算的。注意：`type&1==1`表示低电报警状态"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
            },
        },
    },
    "cam": {
        "camera": True,
        "name": "摄像头",
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
                "description": "移动检测",
                "rw": "R",
                "data_type": "motion_detection",
                "conversion": "val_direct",
                "detailed_description": "`val`值定义如下：0：没有检测到移动，1：有检测到移动",
                "device_class": "motion",
            },
        },
        "sensor": {
            "V": {
                "description": "电压",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": (
                    "`val`表示原始电压值，`v`值将表示当前剩余电量百分比，"
                    "值范围[0,100]，它是根据val电压值换算的。注意：当前只有FRAME设备有该属性"
                ),
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
                "availability_condition": "dev_rt == 'LSCAM:LSCAMV1'",
            },
            "CFST": {
                "description": "摄像头状态",
                "rw": "R",
                "data_type": "camera_status",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val`值定义如下（按位表示值）：第0位：表示是否有外接电源，1表示有外接电源，0表示没有；"
                    "第1位：是否为旋转云台，1表示摄像头在旋转云台上，0表示没有；"
                    "第2位：表示是否正在旋转，1表示正在旋转。注意：当前只有FRAME设备有该属性"
                ),
                "availability_condition": "dev_rt == 'LSCAM:LSCAMV1'",
            },
        },
    },
    # ================= 2.12 车库门控制 (Garage Door Control) =================
    "SL_ETDOOR": {
        "name": "车库门控制器",
        "light": {
            "P1": {
                "description": "灯光控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "`type&1==1`表示打开(忽略`val`值)；"
                    "`type&1==0`表示关闭(忽略`val`值)"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
        },
        "cover": {
            "P2": {
                "description": "车库门状态",
                "rw": "R",
                "data_type": "garage_door_status",
                "conversion": "val_direct",
                "detailed_description": (
                    "`type&1==1`表示控制正在运行；"
                    "`type&1==0`表示没有运行；"
                    "当正在运行的时候即(`type&1==1`):`val&0x80==0x80`表示正在开，否则表示正在关；"
                    "`val&0x7F`的值表示车库门打开的百分比"
                ),
            },
            "P3": {
                "description": "车库门控制",
                "rw": "W",
                "data_type": "garage_door_control",
                "conversion": "val_direct",
                "detailed_description": "百分比取值范围：[0,100]",
                "commands": {
                    "open": {
                        "type": CMD_TYPE_SET_VAL,
                        "val": 100,
                        "description": "完全打开",
                    },
                    "close": {
                        "type": CMD_TYPE_SET_VAL,
                        "val": 0,
                        "description": "完全关闭",
                    },
                    "stop": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "val": 128,
                        "description": "停止车库门开合",
                    },
                    "set_position": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "开到百分比，val=percent，percent取值:[0,100]",
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
                "description": "播放控制",
                "rw": "RW",
                "data_type": "alarm_playback",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "type&1==1,表示正在播放(忽略`val` 值)；"
                    "type&1==0,表示没有播放(忽略`val` 值)；"
                    "val为32bit值，描述如下(16进制)：0xAABBCCDD "
                    "AABB表示时间或者循环次数(最高位1表示次数，否则为时间，时间单位为秒)；"
                    "CC是音量(只有16级，使用高4位，若CC值等于0将采用P2 IO定义的音量值，否则将使用CC值做为音量值)；"
                    "DD表示音频序号；"
                ),
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "播放",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "停止",
                    },
                    "set_config_on": {
                        "type": CMD_TYPE_UNKNOWN_255,
                        "description": "设置值并播放，val=需要设置的值",
                    },
                    "set_config_off": {
                        "type": CMD_TYPE_UNKNOWN_254,
                        "description": "设置值并停止，val=需要设置的值",
                    },
                },
            },
            "P2": {
                "description": "音量控制",
                "rw": "RW",
                "data_type": "volume_control",
                "conversion": "type_bit_0",
                "detailed_description": (
                    "type&1==1表示处于正常模式；"
                    "type&1==0表示处于静音模式；"
                    "`val` 值表示音量值，只有16级，使用高4位。即有效位为：0x000000F0"
                ),
                "commands": {
                    "unmute": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "取消静音",
                    },
                    "mute": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "设置静音",
                    },
                    "set_volume": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置音量，val=音量值",
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
                    "description": "开关",
                    "rw": "RW",
                    "data_type": "binary_switch",
                    "conversion": "type_bit_0",
                    "detailed_description": (
                        "type&1==1,表示打开(忽略`val` 值)；"
                        "type&1==0,表示关闭(忽略`val` 值)；"
                    ),
                    "commands": {
                        "on": {
                            "type": CMD_TYPE_ON,
                            "val": 1,
                            "description": "打开",
                        },
                        "off": {
                            "type": CMD_TYPE_OFF,
                            "val": 0,
                            "description": "关闭",
                        },
                    },
                },
                "P4": {
                    "description": "T当前温度",
                    "rw": "R",
                    "data_type": "temperature",
                    "conversion": "v_field",
                    "detailed_description": "`v` 值表示温度值 `val` 值表示原始温度值，它是温度值*10",
                    "device_class": "temperature",
                    "unit_of_measurement": "°C",
                    "state_class": "measurement",
                },
                "P5": {
                    "description": "设备种类",
                    "rw": "R",
                    "data_type": "device_type",
                    "conversion": "val_direct",
                    "detailed_description": (
                        "val&0xFF指示设备种类。1：开关面板 2：POE面板 3：温控面板 6：温控面板 "
                        "注意：值必须是3或者6才是温控面板，否则是其它类型的设备。"
                    ),
                },
                "P6": {
                    "description": "CFG配置",
                    "rw": "RW",
                    "data_type": "config_bitmask",
                    "conversion": "val_direct",
                    "detailed_description": (
                        "(val>>6)&0x7 指示设备类型 0：新风模式 1：风机盘管（单阀）模式 "
                        "2：水地暖模式 3：风机盘管+水地暖模式 4: 风机盘管（双阀）模式 5：水地暖+新风模式"
                    ),
                    "commands": {
                        "set_config": {
                            "type": CMD_TYPE_UNKNOWN_255,
                            "description": "设置配置，需要保留其它位",
                        },
                    },
                },
                "P7": {
                    "description": "MODE模式",
                    "rw": "RW",
                    "data_type": "hvac_mode",
                    "conversion": "val_direct",
                    "detailed_description": (
                        "3：Cool制冷 4：Heat 制热 7：DN地暖 8：DN_Heat 地暖+空调 "
                        "注意：P6 CFG配置不同，支持的MODE也会不同"
                    ),
                    "commands": {
                        "set_config": {
                            "type": CMD_TYPE_UNKNOWN_206,
                            "description": "设置模式",
                        },
                    },
                },
                "P8": {
                    "description": "tT目标温度",
                    "rw": "RW",
                    "data_type": "temperature",
                    "conversion": "v_field",
                    "detailed_description": "`v` 值表示温度值 `val` 值表示原始温度值，它是温度值*10",
                    "device_class": "temperature",
                    "unit_of_measurement": "°C",
                    "commands": {
                        "set_temperature": {
                            "type": CMD_TYPE_UNKNOWN_136,
                            "description": "设置目标温度，val=温度*10",
                        },
                    },
                },
                "P9": {
                    "description": "tF目标风速",
                    "rw": "RW",
                    "data_type": "fan_speed",
                    "conversion": "val_direct",
                    "detailed_description": (
                        "`val` 值表示风速，定义如下：0：Stop停止 0<val<30：Low低档 "
                        "30<=val<65：Medium中档 65<=val<100：High高档 101：Auto自动 "
                        "注意：P6 CFG配置不同，支持的tF也会不同"
                    ),
                    "commands": {
                        "set_config": {
                            "type": CMD_TYPE_UNKNOWN_206,
                            "description": "设置风速",
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
                    "description": "F当前风速",
                    "rw": "R",
                    "data_type": "fan_speed",
                    "conversion": "val_direct",
                    "detailed_description": (
                        "`val` 值表示风速，定义如下：0：stop停止 0<val<30：Low低档 "
                        "30<=val<65：Medium中档 65<=val<100：High高档 101：Auto自动"
                    ),
                },
            },
            "binary_sensor": {
                "P2": {
                    "description": "阀门状态",
                    "rw": "R",
                    "data_type": "valve_status",
                    "conversion": "val_direct",
                    "detailed_description": "阀门1状态(盘管的冷阀或者盘管的冷热阀)",
                    "device_class": "opening",
                },
                "P3": {
                    "description": "阀门状态",
                    "rw": "R",
                    "data_type": "valve_status",
                    "conversion": "val_direct",
                    "detailed_description": "阀门2状态（盘管的热阀或者地暖阀)",
                    "device_class": "opening",
                },
            },
        },
    },
    # ================= 2.14 智能面板系列 (Smart Panel Series) =================
    # 2.14.4 星玉温控面板 (Nature Thermostat)
    "SL_FCU": {
        "name": "星玉温控面板",
        "climate": {
            "P1": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "val_direct",
                "detailed_description": "开关状态：0关 1开",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭",
                    },
                },
            },
            "P6": {
                "description": "CFG配置",
                "rw": "RW",
                "data_type": "config_bitmask",
                "conversion": "val_direct",
                "detailed_description": (
                    "配置功能：bit0：热回水开关，bit1：地暖开关，bit2：制热开关，"
                    "bit3：制冷开关，bit4：通风开关，bit5：除湿开关，bit6：加湿开关，"
                    "bit7：应急通风开关，bit8：应急加热开关，bit9：应急制冷开关"
                ),
            },
            "P7": {
                "description": "MODE模式",
                "rw": "RW",
                "data_type": "hvac_mode",
                "conversion": "val_direct",
                "detailed_description": (
                    "运行模式：1制热、2制冷、3通风、4除湿、5加湿、"
                    "6应急通风、7应急加热、8应急制冷、16自动"
                ),
                "commands": {
                    "set_config": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置模式",
                    },
                },
            },
            "P8": {
                "description": "tT目标温度",
                "rw": "RW",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`v` 值表示温度值 `val` 值表示原始温度值，它是温度值*10",
                "unit_of_measurement": "°C",
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_UNKNOWN_136,
                        "description": "设置目标温度，val=温度*10",
                    },
                },
            },
            "P9": {
                "description": "tF目标风速",
                "rw": "RW",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val` 值表示风速，定义如下：0：Stop停止 0<val<30：Low低档 30<=val<65：Medium中档 "
                    "65<=val<100：High高档 101：Auto自动 注意：P6 CFG配置不同，支持的tF也会不同"
                ),
                "commands": {
                    "set_config": {
                        "type": CMD_TYPE_UNKNOWN_206,
                        "description": "设置风速",
                        "fan_modes": {
                            "low": 15,
                            "medium": 45,
                            "high": 75,
                            "auto": 101,
                        },
                    },
                },
            },
        },
        "sensor": {
            "P4": {
                "description": "T当前温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`v` 值表示温度值 `val` 值表示原始温度值，它是温度值*10",
                "device_class": "temperature",
                "unit_of_measurement": "°C",
            },
            "P10": {
                "description": "F当前风速",
                "rw": "R",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "detailed_description": (
                    "`val` 值表示风速，定义如下：0：stop停止 0<val<30：Low低档 "
                    "30<=val<65：Medium中档 65<=val<100：High高档 101：Auto自动"
                ),
            },
        },
        "binary_sensor": {
            "P2": {
                "description": "阀门状态",
                "rw": "R",
                "data_type": "valve_status",
                "conversion": "val_direct",
                "detailed_description": "阀门1状态(盘管的冷阀或者盘管的冷热阀)",
                "device_class": "opening",
            },
            "P3": {
                "description": "阀门状态",
                "rw": "R",
                "data_type": "valve_status",
                "conversion": "val_direct",
                "detailed_description": "阀门2状态（盘管的热阀或者地暖阀)",
                "device_class": "opening",
            },
        },
    },
    # ================= 缺失设备补充 (Missing Devices) =================
    "SL_SC_GD": {
        "name": "车库门控制器",
        "cover": {
            "P1": {
                "description": "车库门控制",
                "rw": "RW",
                "data_type": "cover_control",
                "conversion": "val_direct",
                "detailed_description": "车库门开关控制",
                "device_class": "garage",
                "commands": {
                    "open": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "打开车库门",
                    },
                    "close": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关闭车库门",
                    },
                },
            },
        },
        "light": {
            "HS": {
                "description": "车库门灯光",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "车库门照明灯控制",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "开灯",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "关灯",
                    },
                },
            },
        },
        "binary_sensor": {
            "G": {
                "description": "车库门状态传感器",
                "rw": "R",
                "data_type": "binary_sensor",
                "conversion": "type_bit_0",
                "detailed_description": "车库门开关状态检测",
                "device_class": "garage_door",
            },
        },
    },
}


# ================= HVAC和风扇映射配置 (从hvac_mappings.py整合) =================
# 导入HA常量以确保映射正确
try:
    from homeassistant.components.climate.const import (
from custom_components.lifesmart.core.const import CMD_TYPE_OFF, CMD_TYPE_ON, CMD_TYPE_SET_VAL
        HVACMode,
        FAN_AUTO,
        FAN_HIGH,
        FAN_LOW,
        FAN_MEDIUM,
    )

    # ================= 核心温控器HVAC模式映射 =================
    # 核心温控器HVAC模式映射 - 对应基础的F系列设备
    # 数值含义：1=自动模式，2=仅送风，3=制冷，4=制热
    _LIFESMART_F_HVAC_MODE_MAP = {
        1: HVACMode.AUTO,  # 自动模式 - 系统自动选择制冷或制热
        2: HVACMode.FAN_ONLY,  # 仅送风模式 - 只有风扇工作，不制冷制热
        3: HVACMode.COOL,  # 制冷模式 - 空调制冷运行
        4: HVACMode.HEAT,  # 制热模式 - 空调制热运行
    }
    # 反向映射：从Home Assistant模式到LifeSmart数值
    _REVERSE_F_HVAC_MODE_MAP = {v: k for k, v in _LIFESMART_F_HVAC_MODE_MAP.items()}

    # ================= 扩展HVAC模式映射 =================
    # 扩展HVAC模式映射 - 支持更多设备类型和特殊模式
    # 包含地暖、除湿等高级功能，适用于SL_NATURE、FCU等设备
    _LIFESMART_HVAC_MODE_MAP = {
        1: HVACMode.AUTO,  # 自动模式 - 智能调节温度
        2: HVACMode.FAN_ONLY,  # 仅送风模式 - 循环空气但不调温
        3: HVACMode.COOL,  # 制冷模式 - 降低室内温度
        4: HVACMode.HEAT,  # 制热模式 - 提高室内温度
        5: HVACMode.DRY,  # 除湿模式 - 降低室内湿度
        7: HVACMode.HEAT,  # SL_NATURE/FCU地暖模式 - 地板辐射采暖
        8: HVACMode.HEAT_COOL,  # SL_NATURE/FCU地暖+空调复合模式 - 同时支持制热制冷
    }
    # 反向映射：Home Assistant到LifeSmart模式转换
    # 注意：制热模式默认映射到标准制热(4)而非地暖(7)
    _REVERSE_LIFESMART_HVAC_MODE_MAP = {
        HVACMode.AUTO: 1,  # 自动模式
        HVACMode.FAN_ONLY: 2,  # 仅送风
        HVACMode.COOL: 3,  # 制冷
        HVACMode.HEAT: 4,  # 制热(标准模式)
        HVACMode.DRY: 5,  # 除湿
        HVACMode.HEAT_COOL: 8,  # 制热制冷复合模式
    }

    # ================= 风机盘管模式映射 =================
    # 风机盘管(Fan Coil Unit)模式映射 - CP_AIR系列设备专用
    # 数值含义：0=制冷，1=制热，2=仅送风
    _LIFESMART_CP_AIR_HVAC_MODE_MAP = {
        0: HVACMode.COOL,  # 制冷模式 - 冷水循环制冷
        1: HVACMode.HEAT,  # 制热模式 - 热水循环制热
        2: HVACMode.FAN_ONLY,  # 仅送风模式 - 风机运行但不调温
    }
    # 反向映射：Home Assistant到风机盘管模式
    _REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP = {
        v: k for k, v in _LIFESMART_CP_AIR_HVAC_MODE_MAP.items()
    }

    # ================= 风速映射配置 =================

    # 新风设备风速映射 - ACIPM系列新风机专用
    # 数值含义：1=低速，2=中速，3=高速
    _LIFESMART_ACIPM_FAN_MAP = {
        FAN_LOW: 1,  # 低速档 - 静音运行，适合夜间
        FAN_MEDIUM: 2,  # 中速档 - 日常通风，平衡噪音和效果
        FAN_HIGH: 3,  # 高速档 - 快速换气，适合人员密集时
    }
    # 反向映射：LifeSmart风速值到Home Assistant风扇模式
    _REVERSE_LIFESMART_ACIPM_FAN_MAP = {
        v: k for k, v in _LIFESMART_ACIPM_FAN_MAP.items()
    }

    # 风机盘管风速映射 - CP_AIR系列设备专用
    # 数值含义：0=自动，1=低速，2=中速，3=高速
    _LIFESMART_CP_AIR_FAN_MAP = {
        FAN_AUTO: 0,  # 自动风速 - 系统根据温差自动调节
        FAN_LOW: 1,  # 低速档 - 节能静音模式
        FAN_MEDIUM: 2,  # 中速档 - 标准舒适模式
        FAN_HIGH: 3,  # 高速档 - 快速调温模式
    }
    # 反向映射：LifeSmart风速值到Home Assistant风扇模式
    _REVERSE_LIFESMART_CP_AIR_FAN_MAP = {
        v: k for k, v in _LIFESMART_CP_AIR_FAN_MAP.items()
    }

    # 超能面板风速映射 - SL_NATURE系列超能面板专用
    # 数值含义：101=自动，15=低速，45=中速，75=高速
    # 注意：使用百分比数值表示风速级别
    _LIFESMART_TF_FAN_MAP = {
        FAN_AUTO: 101,  # 自动模式 - 智能风速调节(数值101为特殊标识)
        FAN_LOW: 15,  # 低速档 - 15%风速，静音节能
        FAN_MEDIUM: 45,  # 中速档 - 45%风速，日常使用
        FAN_HIGH: 75,  # 高速档 - 75%风速，快速换气
    }
    # 反向映射：LifeSmart风速百分比到Home Assistant风扇模式
    _REVERSE_LIFESMART_TF_FAN_MODE_MAP = {
        v: k for k, v in _LIFESMART_TF_FAN_MAP.items()
    }

    # V_AIR_P风速映射 - V_AIR_P系列空气处理设备专用
    # 数值含义：15=低速，45=中速，75=高速(百分比风速)
    # 注意：该系列不支持自动模式，仅支持手动三档调节
    _LIFESMART_F_FAN_MAP = {
        FAN_LOW: 15,  # 低速档 - 15%风速，夜间模式
        FAN_MEDIUM: 45,  # 中速档 - 45%风速，标准模式
        FAN_HIGH: 75,  # 高速档 - 75%风速，强力模式
    }
    # 反向映射：LifeSmart风速百分比到Home Assistant风扇模式
    _REVERSE_LIFESMART_F_FAN_MODE_MAP = {v: k for k, v in _LIFESMART_F_FAN_MAP.items()}

    # 导出所有HVAC和风扇映射（保持向后兼容）
    LIFESMART_F_HVAC_MODE_MAP = _LIFESMART_F_HVAC_MODE_MAP
    REVERSE_F_HVAC_MODE_MAP = _REVERSE_F_HVAC_MODE_MAP
    LIFESMART_HVAC_MODE_MAP = _LIFESMART_HVAC_MODE_MAP
    REVERSE_LIFESMART_HVAC_MODE_MAP = _REVERSE_LIFESMART_HVAC_MODE_MAP
    LIFESMART_CP_AIR_HVAC_MODE_MAP = _LIFESMART_CP_AIR_HVAC_MODE_MAP
    REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP = _REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP
    LIFESMART_ACIPM_FAN_MAP = _LIFESMART_ACIPM_FAN_MAP
    REVERSE_LIFESMART_ACIPM_FAN_MAP = _REVERSE_LIFESMART_ACIPM_FAN_MAP
    LIFESMART_CP_AIR_FAN_MAP = _LIFESMART_CP_AIR_FAN_MAP
    REVERSE_LIFESMART_CP_AIR_FAN_MAP = _REVERSE_LIFESMART_CP_AIR_FAN_MAP
    LIFESMART_TF_FAN_MAP = _LIFESMART_TF_FAN_MAP
    REVERSE_LIFESMART_TF_FAN_MODE_MAP = _REVERSE_LIFESMART_TF_FAN_MODE_MAP
    LIFESMART_F_FAN_MAP = _LIFESMART_F_FAN_MAP
    REVERSE_LIFESMART_F_FAN_MODE_MAP = _REVERSE_LIFESMART_F_FAN_MODE_MAP

except ImportError:
    # Home Assistant不可用时的降级方案 - 使用空映射
    LIFESMART_F_HVAC_MODE_MAP = {}
    REVERSE_F_HVAC_MODE_MAP = {}
    LIFESMART_HVAC_MODE_MAP = {}
    REVERSE_LIFESMART_HVAC_MODE_MAP = {}
    LIFESMART_CP_AIR_HVAC_MODE_MAP = {}
    REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP = {}
    LIFESMART_ACIPM_FAN_MAP = {}
    REVERSE_LIFESMART_ACIPM_FAN_MAP = {}
    LIFESMART_CP_AIR_FAN_MAP = {}
    REVERSE_LIFESMART_CP_AIR_FAN_MAP = {}
    LIFESMART_TF_FAN_MAP = {}
    REVERSE_LIFESMART_TF_FAN_MODE_MAP = {}
    LIFESMART_F_FAN_MAP = {}
    REVERSE_LIFESMART_F_FAN_MODE_MAP = {}

# ================= 窗帘设备配置 (从cover_mappings.py整合) =================

# 非位置型窗帘设备配置映射 - 仅支持开启/关闭/停止命令
# 此类设备不支持位置反馈，无法获取精确的开启百分比
_NON_POSITIONAL_COVER_CONFIG = {
    # SL_SW_WIN - 窗帘开关面板：专用窗帘控制器
    # IO口功能：OP=开启窗帘，CL=关闭窗帘，ST=紧急停止
    "SL_SW_WIN": {"open": "OP", "close": "CL", "stop": "ST"},
    # SL_P_V2 - 通用控制器V2：多功能控制器的窗帘模式
    # 注意：这不是版本设备，而是真实的设备型号
    # IO口功能：P2=开启操作，P3=关闭操作，P4=停止操作
    "SL_P_V2": {
        "open": "P2",  # P2口用于向上/开启方向驱动窗帘
        "close": "P3",  # P3口用于向下/关闭方向驱动窗帘
        "stop": "P4",  # P4口提供紧急停止功能
    },
    # SL_CN_IF - 红外窗帘控制器：通过红外信号控制传统窗帘
    # IO口功能：P1=开启红外信号，P2=关闭红外信号，P3=停止红外信号
    "SL_CN_IF": {"open": "P1", "close": "P2", "stop": "P3"},
    # SL_CN_FE - 新型窗帘控制器：增强型窗帘驱动器
    # IO口功能：P1=开启驱动，P2=关闭驱动，P3=停止驱动
    "SL_CN_FE": {"open": "P1", "close": "P2", "stop": "P3"},
    # SL_P - 通用控制器：多功能智能控制器的窗帘模式
    # 通过动态检测确定为窗帘模式时使用此配置
    # IO口功能：P2=开启继电器，P3=关闭继电器，P4=停止继电器
    "SL_P": {"open": "P2", "close": "P3", "stop": "P4"},
    # SL_JEMA - JEMA协议控制器：支持JEMA标准的窗帘控制设备
    # IO口功能：P2=JEMA开启命令，P3=JEMA关闭命令，P4=JEMA停止命令
    "SL_JEMA": {"open": "P2", "close": "P3", "stop": "P4"},
}

# 导出窗帘配置（保持向后兼容）
NON_POSITIONAL_COVER_CONFIG = _NON_POSITIONAL_COVER_CONFIG


def get_device_data(device_id: str) -> Dict[str, Any]:
    """获取指定设备的数据"""
    return _RAW_DEVICE_DATA.get(device_id, {})


def get_all_device_ids() -> list:
    """获取所有设备ID列表"""
    return list(_RAW_DEVICE_DATA.keys())


def get_device_count() -> int:
    """获取设备总数"""
    return len(_RAW_DEVICE_DATA)


# 导出设备数据和配置供外部使用
DEVICE_SPECS_DATA = _RAW_DEVICE_DATA
DEVICE_DATA = _RAW_DEVICE_DATA  # 保持向后兼容

# 导出所有配置映射
__all__ = [
    # 设备规格数据
    "DEVICE_SPECS_DATA",
    "DEVICE_DATA",
    "get_device_data",
    "get_all_device_ids",
    "get_device_count",
    # HVAC和风扇映射（从hvac_mappings.py迁移）
    "LIFESMART_F_HVAC_MODE_MAP",
    "REVERSE_F_HVAC_MODE_MAP",
    "LIFESMART_HVAC_MODE_MAP",
    "REVERSE_LIFESMART_HVAC_MODE_MAP",
    "LIFESMART_CP_AIR_HVAC_MODE_MAP",
    "REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP",
    "LIFESMART_ACIPM_FAN_MAP",
    "REVERSE_LIFESMART_ACIPM_FAN_MAP",
    "LIFESMART_CP_AIR_FAN_MAP",
    "REVERSE_LIFESMART_CP_AIR_FAN_MAP",
    "LIFESMART_TF_FAN_MAP",
    "REVERSE_LIFESMART_TF_FAN_MODE_MAP",
    "LIFESMART_F_FAN_MAP",
    "REVERSE_LIFESMART_F_FAN_MODE_MAP",
    # 窗帘配置（从cover_mappings.py迁移）
    "NON_POSITIONAL_COVER_CONFIG",
]
