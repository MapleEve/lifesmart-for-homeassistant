"""由 @MapleEve 实现的 LifeSmart 集成常量模块。

此文件定义了所有与 LifeSmart 平台交互所需的硬编码常量、设备类型代码、API命令码、
以及用于在 Home Assistant 和 LifeSmart 之间转换数据的映射。

维护此文件的准确性和清晰度对于整个集成的稳定和可扩展性至关重要。
"""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
)
from homeassistant.components.button import (
    ButtonDeviceClass,
)
from homeassistant.components.climate.const import (
    HVACMode,
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfEnergy,
    UnitOfPower,
)

# ================= 重要技术说明 (Critical Technical Documentation) =================

"""
⚠️ 重要：LifeSmart设备动态分类和IO口处理技术说明 ⚠️

本集成支持LifeSmart平台的全系列智能设备，包含复杂的动态设备分类逻辑和精确的IO口控制协议。
以下是关键技术要点，修改时务必理解这些规则：

1. 【动态设备分类规则】
   某些设备(如SL_P通用控制器、SL_NATURE超能面板)根据配置参数动态决定功能：
   - SL_P通用控制器：根据P1口的工作模式(P1>>24)&0xE决定是开关、窗帘还是传感器
   - SL_NATURE超能面板：根据P5口值(P5&0xFF)决定是开关版(1)还是温控版(3/6)
   - 动态分类必须在helpers.py中实现，不能仅依赖设备类型判断

2. 【IO口数据格式和位运算规则】
   LifeSmart使用type和val两个字段表示IO口状态：
   - type字段：奇偶性(type&1)表示开关状态，1开启/0关闭
   - val字段：具体数值，含义因设备而异
   - 32位复合值：高位可能包含配置、低位包含状态(如P1工作模式)
   - 浮点数编码：部分设备使用IEEE754格式存储浮点数到32位整数

3. 【设备版本处理(VERSIONED_DEVICE_TYPES)】
   某些设备需要根据fullCls字段区分版本：
   - SL_SW_DM1: V1是动态调光开关，V2是星玉调光开关(可控硅)
   - SL_SC_BB: V1是基础按键，V2是高级按键(支持双击长按)
   - SL_LK_DJ: V1是C210门锁，V2是C200门锁
   - 版本区分逻辑在helpers.py中的get_device_version()实现

4. 【特殊IO口命名和控制逻辑】
   不同设备系列使用不同的IO口命名规则：
   - 开关面板：L1/L2/L3 + dark/bright指示灯控制
   - 通用控制器：P1-P10，功能因工作模式而异
   - 温控设备：tT目标温度、T当前温度、MODE/F风速等
   - 灯光设备：RGBW颜色、DYN动态效果、P1/P2亮度色温等

5. 【多平台设备处理】
   单个物理设备可能创建多个Home Assistant实体：
   - SL_NATURE温控版：同时创建climate实体(温控)和sensor实体(温度)
   - SL_JEMA通用控制器：根据工作模式创建对应实体+P8/P9/P10独立开关
   - 灯光设备：可能同时支持switch和light平台

6. 【命令下发协议(CMD_TYPE_*)】
   不同的控制命令使用不同的type值：
   - CMD_TYPE_ON(0x81)/CMD_TYPE_OFF(0x80)：基础开关控制
   - CMD_TYPE_SET_VAL(0xCF)：设置数值(亮度、位置等)
   - CMD_TYPE_SET_RAW(0xFF)：设置原始值(颜色、配置等)
   - CMD_TYPE_SET_CONFIG(0xCE)：设置配置参数
   - 温度设置有专用命令码，避免精度丢失

7. 【网络协议和数据同步】
   - WebSocket实时推送：_schg消息格式为 agt/ep/device_id/m/io_key
   - API轮询：定期获取全量设备列表，处理设备增删
   - 数据归一化：normalize_device_names()处理{$EPN}等占位符
   - 乐观更新：UI立即响应用户操作，失败时回滚状态

8. 【设备平台映射系统】
   基于IO特征的动态平台判断，取代传统的设备类型聚合列表：
   - get_device_platform_mapping()：根据设备IO特征获取支持的平台
   - MULTI_PLATFORM_DEVICE_MAPPING：多平台设备IO口映射
   - STAR_SERIES_IO_MAPPING：恒星系列不同键数的IO口映射
   - 支持单设备多平台，避免设备重复定义问题

9. 【兼容性处理】
   - 向后兼容：保留已废弃的设备类型定义，避免现有配置失效
   - 设备别名：某些设备有多个型号名称，统一映射到标准类型
   - 缺失数据防护：使用safe_get()防止KeyError，提供默认值

10. 【测试和验证】
    - Mock架构：测试时精准Mock网络和线程组件，保留业务逻辑验证
    - 设备工厂：test_utils.py提供统一的测试设备数据生成
    - 全环境测试：支持Python 3.10-3.13和HA 2022.10-2024.12版本

修改设备类型定义或IO口逻辑时，务必：
✓ 理解设备的完整工作流程和数据格式
✓ 考虑动态分类和版本兼容性
✓ 更新对应的helpers.py逻辑
✓ 运行完整测试确保无回归
✓ 参考官方文档`docs/LifeSmart 智慧设备规格属性说明.md`

❌ 切勿仅凭设备名称判断功能
❌ 切勿破坏现有的位运算逻辑
❌ 切勿删除看似"冗余"的设备类型定义
❌ 切勿忽略浮点数和复合值的特殊处理
"""

# ================= 核心常量 (Core Constants) =================
DOMAIN = "lifesmart"
MANUFACTURER = "LifeSmart"

# --- JSON 数据键名 ---
# 这些常量用于从LifeSmart API响应的JSON数据中安全地提取值。
HUB_ID_KEY = "agt"  # 智慧中心 (网关) 的唯一标识符
DEVICE_ID_KEY = "me"  # 设备的唯一标识符
DEVICE_TYPE_KEY = "devtype"  # 设备的类型代码，用于区分不同种类的设备
DEVICE_FULLCLS_KEY = "fullCls"  # 包含版本号的完整设备类型，用于区分设备版本
DEVICE_NAME_KEY = "name"  # 设备的用户自定义名称
DEVICE_DATA_KEY = "data"  # 包含设备所有IO口状态的字典
DEVICE_VERSION_KEY = "ver"  # 设备的固件或软件版本
SUBDEVICE_INDEX_KEY = "idx"  # 子设备或IO口的索引键，如 'L1', 'P1'


# ================= WebSocket 及更新机制常量 =================
# --- Home Assistant 信号 (Dispatcher Signals) ---
UPDATE_LISTENER = "update_listener"  # 用于在 hass.data 中存储配置更新监听器的键
LIFESMART_STATE_MANAGER = (
    "lifesmart_wss"  # 用于在 hass.data 中存储 WebSocket 管理器实例的键
)
LIFESMART_SIGNAL_UPDATE_ENTITY = "lifesmart_updated"  # 用于在集成内部进行事件通知的信号

# ================= 配置常量 (Configuration Constants) =================
# 这些常量用于在 config_flow 和 __init__.py 中处理用户的配置数据。
CONF_LIFESMART_APPKEY = "appkey"
CONF_LIFESMART_APPTOKEN = "apptoken"
CONF_LIFESMART_USERTOKEN = "usertoken"
CONF_LIFESMART_AUTH_METHOD = "auth_method"
CONF_LIFESMART_USERPASSWORD = "userpassword"
CONF_LIFESMART_USERID = "userid"
CONF_EXCLUDE_ITEMS = "exclude"
CONF_EXCLUDE_AGTS = "exclude_agt"
CONF_AI_INCLUDE_AGTS = "ai_include_agt"
CONF_AI_INCLUDE_ITEMS = "ai_include_me"

# --- AI 类型常量 ---
CON_AI_TYPE_SCENE = "scene"
CON_AI_TYPE_AIB = "aib"
CON_AI_TYPE_GROUP = "grouphw"
CON_AI_TYPES = {
    CON_AI_TYPE_SCENE,
    CON_AI_TYPE_AIB,
    CON_AI_TYPE_GROUP,
}
AI_TYPES = "ai"
# ================= IO 命令类型常量 (IO Command Type Constants) =================

# IO值类型定义 - 参考官方文档附录3.5
# TYPE定义中的重要常量，用于正确解析IO数据
IO_TYPE_FLOAT_MASK = 0x7E  # 用于判断是否为浮点类型
IO_TYPE_FLOAT_VALUE = 0x02  # 浮点类型标识
IO_TYPE_EXCEPTION = 0x1E  # 异常数据类型

# 精度相关的位掩码
IO_TYPE_PRECISION_MASK = 0x78
IO_TYPE_PRECISION_BASE = 0x08
IO_TYPE_PRECISION_BITS = 0x06

# IO数据流向定义 - 参考官方文档3.5.1 TYPE定义
IO_DIRECTION_INPUT = 0x00  # bit7=0表示输入
IO_DIRECTION_OUTPUT = 0x80  # bit7=1表示输出

# IO命令类型定义 - 参考官方文档附录3.1
# 这些命令类型用于设备的 type 控制
CMD_TYPE_ON = 0x81  # 通用开启命令
CMD_TYPE_OFF = 0x80  # 通用关闭命令
CMD_TYPE_PRESS = 0x89  # 点动命令
CMD_TYPE_SET_VAL = 0xCF  # 设置数值/启用功能 (如亮度、窗帘位置、功率门限启用)
CMD_TYPE_SET_CONFIG = 0xCE  # 设置配置/禁用功能 (如空调模式、风速、功率门限禁用)
CMD_TYPE_SET_TEMP_DECIMAL = 0x88  # 设置温度 (值为实际温度*10)
CMD_TYPE_SET_RAW_ON = 0xFF  # 开灯亮度/配置设置开始(颜色、动态、配置值等)
CMD_TYPE_SET_RAW_OFF = 0xFE  # 关灯亮度设置/配置设置停止（颜色、动态、配置值等）
CMD_TYPE_SET_TEMP_FCU = 0x89  # FCU温控器设置温度的特殊命令码


# ================= 温控器映射 (Climate Mappings) =================
# 用于在 Home Assistant 的标准 HVAC 模式与 LifeSmart 的私有模式值之间进行转换。

# --- V_AIR_P (智控器空调面板) 模式映射 ---
LIFESMART_F_HVAC_MODE_MAP = {
    1: HVACMode.AUTO,
    2: HVACMode.FAN_ONLY,
    3: HVACMode.COOL,
    4: HVACMode.HEAT,
}
REVERSE_F_HVAC_MODE_MAP = {v: k for k, v in LIFESMART_F_HVAC_MODE_MAP.items()}

# --- SL_UACCB, SL_NATURE, SL_FCU 等设备的模式映射 ---
# 这个映射包含了地暖等特殊模式
LIFESMART_HVAC_MODE_MAP = {
    1: HVACMode.AUTO,
    2: HVACMode.FAN_ONLY,
    3: HVACMode.COOL,
    4: HVACMode.HEAT,
    5: HVACMode.DRY,
    7: HVACMode.HEAT,  # SL_NATURE/FCU 地暖模式
    8: HVACMode.HEAT_COOL,  # SL_NATURE/FCU 地暖+空调模式
}
# 注意：由于一个HA模式可能对应多个设备模式，反向映射只用于那些没有歧义的设备
REVERSE_LIFESMART_HVAC_MODE_MAP = {
    HVACMode.AUTO: 1,
    HVACMode.FAN_ONLY: 2,
    HVACMode.COOL: 3,
    HVACMode.HEAT: 4,  # 默认将制热映射回 4
    HVACMode.DRY: 5,
    HVACMode.HEAT_COOL: 8,
}


# --- SL_CP_AIR (风机盘管) 模式与风速映射 (来自P1 bitmask) ---
LIFESMART_CP_AIR_HVAC_MODE_MAP = {
    0: HVACMode.COOL,
    1: HVACMode.HEAT,
    2: HVACMode.FAN_ONLY,
}
REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP = {
    v: k for k, v in LIFESMART_CP_AIR_HVAC_MODE_MAP.items()
}

# --- SL_TR_ACIPM (新风) 风速映射 ---
LIFESMART_ACIPM_FAN_MAP = {
    FAN_LOW: 1,
    FAN_MEDIUM: 2,
    FAN_HIGH: 3,
}
REVERSE_LIFESMART_ACIPM_FAN_MAP = {v: k for k, v in LIFESMART_ACIPM_FAN_MAP.items()}

# --- SL_CP_AIR (风机盘管) 风速映射 (P1 bitmask) ---
LIFESMART_CP_AIR_FAN_MAP = {
    FAN_AUTO: 0,
    FAN_LOW: 1,
    FAN_MEDIUM: 2,
    FAN_HIGH: 3,
}
REVERSE_LIFESMART_CP_AIR_FAN_MAP = {v: k for k, v in LIFESMART_CP_AIR_FAN_MAP.items()}

# --- SL_NATURE / SL_FCU (超能面板) 风速映射 (tF) ---
LIFESMART_TF_FAN_MAP = {
    FAN_AUTO: 101,
    FAN_LOW: 15,
    FAN_MEDIUM: 45,
    FAN_HIGH: 75,
}
REVERSE_LIFESMART_TF_FAN_MODE_MAP = {v: k for k, v in LIFESMART_TF_FAN_MAP.items()}

# --- V_AIR_P 风速映射 (F) ---
LIFESMART_F_FAN_MAP = {
    FAN_LOW: 15,
    FAN_MEDIUM: 45,
    FAN_HIGH: 75,
}
REVERSE_LIFESMART_F_FAN_MODE_MAP = {v: k for k, v in LIFESMART_F_FAN_MAP.items()}


# 门锁解锁方式映射
UNLOCK_METHOD = {
    0: "None",
    1: "Password",
    2: "Fingerprint",
    3: "NFC",
    4: "Keys",
    5: "Remote",
    6: "12V Signal",
    7: "App",
    8: "Bluetooth",
    9: "Manual",
    15: "Error",
}


# ================= 平台聚合已废弃 (Platform Aggregation Deprecated) =================
# 注意：ALL_*_TYPES聚合列表已被完全废弃并移除。
#
# 🔄 **新的设备平台映射架构**：
# - 使用 helpers.py 中的 get_device_platform_mapping() 函数获取设备支持的平台
# - 基于 MULTI_PLATFORM_DEVICE_MAPPING精确映射
# - 支持单设备多平台，避免了设备重复定义问题
# - 动态分类设备（如SL_NATURE、SL_P）根据IO状态自动判断平台归属
#
# 📋 **迁移指南**：
# - 旧代码: `if device_type in ALL_SWITCH_TYPES`
# - 新代码: `platforms = get_device_platform_mapping(device);`
#           `if Platform.SWITCH in platforms`
#
# 🔍 **技术优势**：
# - ✅ 消除设备重复定义
# - ✅ 支持多平台设备（如SL_OL_W：开关+灯光）
# - ✅ 动态分类（如超能面板根据配置变化功能）
# - ✅ IO口级别的精确控制
# - ✅ 更好的可维护性和扩展性

# ================= 设备IO特征映射 (Device IO Feature Mapping) =================
# 基于设备实际IO口功能的平台支持映射，解决多平台设备问题
# 每个设备只在一个主要集合中定义，但可支持多个平台

DEVICE_MAPPING = {
    # ================= 设备映射按官方文档顺序排列 (Device Mapping in Official Documentation Order) =================
    # 🚨 严格按照官方文档 "LifeSmart 智慧设备规格属性说明.md" 的章节顺序排列
    # 🚨 2.1 插座系列 → 2.2 开关系列 → 2.3 窗帘控制 → 2.4 灯光系列 → ... → 2.14 超能面板
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "sensor": {
            "P2": {
                "description": "用电量",
                "rw": "R",
                "data_type": "energy",
                "conversion": "ieee754_float",
                "detailed_description": "为累计用电量，`val` 值为 `IEEE754` 浮点数的32位整数表示，`v` 值为浮点数，单位为度(kwh)",
                "device_class": SensorDeviceClass.ENERGY,
                "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
                "state_class": SensorStateClass.TOTAL_INCREASING,
            },
            "P3": {
                "description": "功率",
                "rw": "R",
                "data_type": "power",
                "conversion": "ieee754_float",
                "detailed_description": "为当前负载功率，`v` 值为浮点数，单位为w",
                "device_class": SensorDeviceClass.POWER,
                "unit_of_measurement": UnitOfPower.WATT,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
        "switch_extra": {
            "P4": {
                "description": "功率门限",
                "rw": "RW",
                "data_type": "power_threshold",
                "conversion": "val_direct",
                "detailed_description": "功率门限，用电保护，值为整数，超出门限则会断电，单位为w",
                "commands": {
                    "enable": {"type": CMD_TYPE_ON, "val": 1, "description": "使能"},
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
                        "type": CMD_TYPE_SET_CONFIG,
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "sensor": {
            "P2": {
                "description": "用电量",
                "rw": "R",
                "data_type": "energy",
                "conversion": "ieee754_float",
                "detailed_description": "为累计用电量，`val` 值为 `IEEE754` 浮点数的32位整数表示，`v` 值为浮点数，单位为度(kwh)",
                "device_class": SensorDeviceClass.ENERGY,
                "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
                "state_class": SensorStateClass.TOTAL_INCREASING,
            },
            "P3": {
                "description": "功率",
                "rw": "R",
                "data_type": "power",
                "conversion": "ieee754_float",
                "detailed_description": "为当前负载功率，`v` 值为浮点数，单位为w",
                "device_class": SensorDeviceClass.POWER,
                "unit_of_measurement": UnitOfPower.WATT,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
        "switch_extra": {
            "P4": {
                "description": "功率门限",
                "rw": "RW",
                "data_type": "power_threshold",
                "conversion": "val_direct",
                "detailed_description": "功率门限，用电保护，值为整数，超出门限则会断电，单位为w",
                "commands": {
                    "enable": {"type": CMD_TYPE_ON, "val": 1, "description": "使能"},
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
                        "type": CMD_TYPE_SET_CONFIG,
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "sensor": {
            "P2": {
                "description": "用电量",
                "rw": "R",
                "data_type": "energy",
                "conversion": "ieee754_float",
                "detailed_description": "为累计用电量，`val` 值为 `IEEE754` 浮点数的32位整数表示，`v` 值为浮点数，单位为度(kwh)",
                "device_class": SensorDeviceClass.ENERGY,
                "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
                "state_class": SensorStateClass.TOTAL_INCREASING,
            },
            "P3": {
                "description": "功率",
                "rw": "R",
                "data_type": "power",
                "conversion": "ieee754_float",
                "detailed_description": "为当前负载功率，`v` 值为浮点数，单位为w",
                "device_class": SensorDeviceClass.POWER,
                "unit_of_measurement": UnitOfPower.WATT,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
        "switch_extra": {
            "P4": {
                "description": "功率门限",
                "rw": "RW",
                "data_type": "power_threshold",
                "conversion": "val_direct",
                "detailed_description": "功率门限，用电保护，值为整数，超出门限则会断电，单位为w",
                "commands": {
                    "enable": {"type": CMD_TYPE_ON, "val": 1, "description": "使能"},
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
                        "type": CMD_TYPE_SET_CONFIG,
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "indicator_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，取值范围：0~1023",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_brightness_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置亮度值，val=亮度值",
                    },
                    "set_brightness_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置亮度值，val=亮度值",
                    },
                },
            },
            "bright": {
                "description": "开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "indicator_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，取值范围：0~1023",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_brightness_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置亮度值，val=亮度值",
                    },
                    "set_brightness_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置亮度值，val=亮度值",
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "L3": {
                "description": "第三路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark3": {
                "description": "第三路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright3": {
                "description": "第三路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    # 2.2.1 传统开关系列补充 (Traditional Switch Series Supplement)
    "SL_SW_IF3": {
        "name": "流光开关三键",
        "switch": {
            "L1": {
                "description": "第一路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "L3": {
                "description": "第三路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark3": {
                "description": "第三路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright3": {
                "description": "第三路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "L3": {
                "description": "第三路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark3": {
                "description": "第三路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright3": {
                "description": "第三路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "L3": {
                "description": "第三路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark3": {
                "description": "第三路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright3": {
                "description": "第三路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "L2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright": {
                "description": "开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright": {
                "description": "开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright": {
                "description": "开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright": {
                "description": "开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
            "bright": {
                "description": "开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
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
                "detailed_description": "type&1==1,表示打开(忽略`val` 值)；type&1==0,表示关闭(忽略`val` 值)；",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "sensor": {
            "P2": {
                "description": "温度采集",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始温度值，它是温度值*10，`v` 值表示实际值(单位：℃)",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
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
                "detailed_description": "type&1==1,表示打开(忽略`val` 值)；type&1==0,表示关闭(忽略`val` 值)；",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "P2": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "type&1==1,表示打开(忽略`val` 值)；type&1==0,表示关闭(忽略`val` 值)；",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "sensor": {
            "P3": {
                "description": "温度采集",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始温度值，它是温度值*10，`v` 值表示实际值(单位：℃)",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
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
                "detailed_description": "type&1==1,表示打开(忽略`val` 值)；type&1==0,表示关闭(忽略`val` 值)；",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "P2": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "type&1==1,表示打开(忽略`val` 值)；type&1==0,表示关闭(忽略`val` 值)；",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "P3": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "type&1==1,表示打开(忽略`val` 值)；type&1==0,表示关闭(忽略`val` 值)；",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "sensor": {
            "P4": {
                "description": "温度采集",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始温度值，它是温度值*10，`v` 值表示实际值(单位：℃)",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "sensor": {
            "P2": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery_level",
                "conversion": "voltage_to_percentage",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据 `val` 电压值换算的",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "P2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "sensor": {
            "P3": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery_level",
                "conversion": "voltage_to_percentage",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据 `val` 电压值换算的",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
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
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "P2": {
                "description": "第二路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "P3": {
                "description": "第三路开关控制口",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "sensor": {
            "P4": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery_level",
                "conversion": "voltage_to_percentage",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据 `val` 电压值换算的",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
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
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
    },
    "SL_SPWM": {
        "name": "PWM调光开关控制器",
        "switch": {
            "P1": {
                "description": "开关",
                "rw": "RW",
                "data_type": "dimmer_switch",
                "conversion": "type_bit_0",
                "detailed_description": "type&1==1 表示处于打开状态；type&1==0 表示处于关闭状态；val 值为亮度值，可调范围：[0,255]，值越大表示光越亮，0处于最暗，光完全熄灭，255处于最亮",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_brightness_on": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "打开并且设置亮度，val=亮度值[0,255]",
                    },
                    "set_brightness_off": {
                        "type": CMD_TYPE_SET_CONFIG,
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
                "detailed_description": "type&1==1 表示处于打开状态；type&1==0 表示处于关闭状态",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "P2": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "type&1==1 表示处于打开状态；type&1==0 表示处于关闭状态",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "P3": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "type&1==1 表示处于打开状态；type&1==0 表示处于关闭状态",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "P4": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "type&1==1 表示处于打开状态；type&1==0 表示处于关闭状态",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "P5": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "type&1==1 表示处于打开状态；type&1==0 表示处于关闭状态",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "P6": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "type&1==1 表示处于打开状态；type&1==0 表示处于关闭状态",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "P7": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "type&1==1 表示处于打开状态；type&1==0 表示处于关闭状态",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "P8": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "type&1==1 表示处于打开状态；type&1==0 表示处于关闭状态",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "P9": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "type&1==1 表示处于打开状态；type&1==0 表示处于关闭状态",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
    },
    # 2.2.4 随心开关 (CUBE Clicker)
    "SL_SC_BB": {
        "name": "随心开关",
        "button": {
            "B": {
                "description": "按键状态",
                "rw": "R",
                "data_type": "button_state",
                "conversion": "val_direct",
                "detailed_description": "`val` 的值定义如下：- 0：未按下按键 - 1：按下按键",
                "device_class": ButtonDeviceClass.IDENTIFY,
            },
        },
        "sensor": {
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始电压值 `v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据 `val` 电压值换算的",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    "SL_SC_BB_V2": {
        "name": "随心按键",
        "button": {
            "P1": {
                "description": "按键状态",
                "rw": "R",
                "data_type": "button_events",
                "conversion": "val_direct",
                "detailed_description": "`type` 的值定义如下: `type&1==1`，表示有按键事件产生；`type&1==0`,表示按键事件消失；`val` 值指明按键事件类型，只有在 `type&1==1` 才有效，`val` 的值定义如下：1：单击事件 2：双击事件 255：长按事件",
                "device_class": ButtonDeviceClass.IDENTIFY,
            },
        },
        "sensor": {
            "P2": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery_level",
                "conversion": "voltage_to_percentage",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0，100]，它是根据 `val` 电压值换算的。",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    # 2.2.5 奇点开关模块系列 (Singularity Switch Module Series)
    "SL_SW_MJ1": {
        "name": "奇点开关模块一键",
        "switch": {
            "P1": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "type&1==1,表示打开(忽略`val` 值)；type&1==0,表示关闭(忽略`val` 值)；",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
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
                "detailed_description": "type&1==1,表示打开(忽略`val` 值)；type&1==0,表示关闭(忽略`val` 值)；",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "P2": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "type&1==1,表示打开(忽略`val` 值)；type&1==0,表示关闭(忽略`val` 值)；",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
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
                "detailed_description": "type&1==1,表示打开(忽略`val` 值)；type&1==0,表示关闭(忽略`val` 值)；",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "P2": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "type&1==1,表示打开(忽略`val` 值)；type&1==0,表示关闭(忽略`val` 值)；",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
            "P3": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "type&1==1,表示打开(忽略`val` 值)；type&1==0,表示关闭(忽略`val` 值)；",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
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
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "执行打开窗帘"},
                },
            },
            "ST": {
                "description": "停止 (stop)",
                "rw": "RW", 
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示停止当前动作",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "执行停止窗帘"},
                },
            },
            "CL": {
                "description": "关闭窗帘 (close)",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0", 
                "detailed_description": "`type&1==1`表示关闭窗帘",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "执行关闭窗帘"},
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
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭；`val`表示指示灯亮度值，取值范围：0~1023",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_brightness_on": {"type": CMD_TYPE_SET_RAW_ON, "description": "开灯并设置亮度值，val=亮度值"},
                    "set_brightness_off": {"type": CMD_TYPE_SET_RAW_OFF, "description": "关灯并设置亮度值，val=亮度值"},
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
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_brightness_on": {"type": CMD_TYPE_SET_RAW_ON, "description": "开灯并设置亮度值，val=亮度值"},
                    "set_brightness_off": {"type": CMD_TYPE_SET_RAW_OFF, "description": "关灯并设置亮度值，val=亮度值"},
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
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "执行打开窗帘"},
                },
            },
            "P2": {
                "description": "停止 (stop)",
                "rw": "RW",
                "data_type": "binary_switch", 
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示停止当前动作",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "执行停止窗帘"},
                },
            },
            "P3": {
                "description": "关闭窗帘 (close)",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示关闭窗帘",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "执行关闭窗帘"},
                },
            },
        },
        "light": {
            "P4": {
                "description": "打开面板指示灯的颜色值",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct", 
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭；`val`表示指示灯亮度值，定义如下：（当`White>0`时，表示动态模式）具体动态值请参考：附录3.1动态颜色(`DYN`)定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {"type": CMD_TYPE_SET_RAW_ON, "description": "开灯并设置颜色或动态值，val=颜色或动态值"},
                    "set_color_off": {"type": CMD_TYPE_SET_RAW_OFF, "description": "关灯并设置颜色值或动态值，val=颜色或动态值"},
                },
            },
            "P5": {
                "description": "停止(stop)时指示灯的颜色值",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭;`val`表示指示灯亮度值，定义如下：`bit0~bit7`:Blue, `bit8~bit15`:Green, `bit16~bit23`:Red, `bit24~bit31`:White, （当`White>0`时，表示动态模式）具体动态值请参考：附录3.1动态颜色(`DYN`)定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {"type": CMD_TYPE_SET_RAW_ON, "description": "开灯并设置颜色或动态值，val=颜色或动态值"},
                    "set_color_off": {"type": CMD_TYPE_SET_RAW_OFF, "description": "关灯并设置颜色值或动态值，val=颜色或动态值"},
                },
            },
            "P6": {
                "description": "关闭面板指示灯的颜色值",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭；`val`表示指示灯亮度值，定义如下：`bit24~bit31`:White, （当`White>0`时，表示动态模式）具体动态值请参考：附录3.1动态颜色(`DYN`)定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {"type": CMD_TYPE_SET_RAW_ON, "description": "开灯并设置颜色或动态值，val=颜色或动态值"},
                    "set_color_off": {"type": CMD_TYPE_SET_RAW_OFF, "description": "关灯并设置颜色值或动态值，val=颜色或动态值"},
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
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "执行打开窗帘"},
                },
            },
            "P2": {
                "description": "停止 (stop)",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0", 
                "detailed_description": "`type&1==1`表示停止当前动作",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "执行停止窗帘"},
                },
            },
            "P3": {
                "description": "关闭窗帘",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示关闭窗帘",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "执行关闭窗帘"},
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
                "detailed_description": "`type&1==1`表示控制正在运行；`type&1==0`表示没有运行；当正在运行的时候即(`type&1==1`):,`val%0x80==0x80`表示正在开，否则表示正在关；`val%0x7F`的值表示窗帘打开的百分比([0,100]);若`val%0x7F`大于100则表示获取不到位置信息，只有执行全开或全关之后才能重新获取位置信息。",
            },
            "P2": {
                "description": "窗帘控制",
                "rw": "W",
                "data_type": "position_control",
                "conversion": "val_direct",
                "commands": {
                    "open": {"type": 0xCF, "val": 100, "description": "完全打开"},
                    "close": {"type": 0xCF, "val": 0, "description": "完全关闭"},
                    "stop": {"type": 0xCE, "val": 0x80, "description": "停止窗帘"},
                    "set_position": {"type": 0xCF, "description": "开到百分比，val=percent，percent取值:[0,100]"},
                },
            },
        },
    },
    # 2.3.3 智界窗帘电机智控器
    "SL_P_V2": {
        "name": "智界窗帘电机智控器",
        "cover": {
            "P2": {
                "description": "打开窗帘 (open)",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示打开窗帘",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "执行打开窗帘"},
                },
            },
            "P3": {
                "description": "关闭窗帘 (close)",
                "rw": "RW", 
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示关闭窗帘",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "执行关闭窗帘"},
                },
            },
            "P4": {
                "description": "停止 (stop)",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示停止当前动作",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "执行停止窗帘"},
                },
            },
        },
        "sensor": {
            "P8": {
                "description": "电压(V)",
                "rw": "R",
                "data_type": "voltage",
                "conversion": "friendly_val",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0，100]，它是根据val电压值换算的。",
                "device_class": SensorDeviceClass.VOLTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
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
                "range": "0x00000000-0xFFFFFFFF",
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭；`val` 值为颜色值，大小4个字节，定义如下：`bit0`~`bit7`:Blue, `bit8`~`bit15`:Green, `bit16`~`bit23`:Red, `bit24`~`bit31`:White，例如：红色：0x00FF0000, 白色：0xFF000000",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色值，val=颜色值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值，val=颜色值",
                    },
                },
            },
            "DYN": {
                "description": "动态颜色值",
                "rw": "RW",
                "data_type": "dynamic_effect",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1`表示打开动态；`type&1==0`表示关闭动态；`val`表示动态颜色值，具体动态值请参考：附录3.2 动态颜色（DYN）定义",
                "commands": {
                    "enable": {"type": CMD_TYPE_ON, "val": 1, "description": "使能"},
                    "disable": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_effect_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "使能并设置动态值，val=动态值",
                    },
                    "set_effect_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
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
                "range": "0x00000000-0xFFFFFFFF",
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭；`val` 值为颜色值，大小4个字节，定义如下：`bit0`~`bit7`:Blue, `bit8`~`bit15`:Green, `bit16`~`bit23`:Red, `bit24`~`bit31`:White，例如：红色：0x00FF0000, 白色：0xFF000000",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色值，val=颜色值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值，val=颜色值",
                    },
                },
            },
            "DYN": {
                "description": "动态颜色值",
                "rw": "RW",
                "data_type": "dynamic_effect",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1`表示打开动态；`type&1==0`表示关闭动态；`val`表示动态颜色值，具体动态值请参考：附录3.2 动态颜色（DYN）定义",
                "commands": {
                    "enable": {"type": CMD_TYPE_ON, "val": 1, "description": "使能"},
                    "disable": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_effect_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "使能并设置动态值，val=动态值",
                    },
                    "set_effect_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
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
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭；`val` 值为颜色值，大小4个字节，定义如下：`bit0`~`bit7`:Blue, `bit8`~`bit15`:Green, `bit16`~`bit23`:Red, `bit24`~`bit31`:White, （当White>=128时，表示动态模式）具体动态值请参考：附录3.2动态颜色（DYN）定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
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
                "detailed_description": "`type&1==1`表示打开(忽略`val` 值)；`type&1==0`表示关闭(忽略`val` 值)；`val`指示灯光的亮度值范围[0,100]，100亮度最大",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯(打开)"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯(关闭)"},
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置亮度，val=亮度值[0，100]",
                    },
                },
            },
            "P2": {
                "description": "颜色控制",
                "rw": "RW",
                "data_type": "quantum_light",
                "conversion": "val_direct",
                "range": "0x00000000-0xFFFFFFFF",
                "detailed_description": "`val` 值为颜色值，大小4个字节，定义如下：`bit0`~`bit7`:Blue, `bit8`~`bit15`:Green, `bit16`~`bit23`:Red, `bit24`~`bit31`:White, （当White>0时，表示动态模式）具体动态值请参考：附录3.2动态颜色(DYN)定义, 附录3.3量子灯特殊(DYN)定义",
                "commands": {
                    "set_color": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "设置颜色或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    },
    # 2.4.3 调光调色控制器/白光智能灯泡 (Smart Bulb)
    "SL_LI_WW": {
        "name": "调光调色控制器",
        "light": {
            "P1": {
                "description": "亮度控制",
                "rw": "RW",
                "data_type": "brightness_light",
                "conversion": "val_direct",
                "range": "0-255",
                "detailed_description": "`type&1==1`,表示打开(忽略`val` 值);`type&1==0`,表示关闭(忽略`val` 值)；val指示灯光的亮度值范围[0，255]，255亮度最大",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置亮度，val=亮度值[0，255]",
                    },
                },
            },
            "P2": {
                "description": "色温控制",
                "rw": "RW",
                "data_type": "color_temperature",
                "conversion": "val_direct",
                "range": "0-255",
                "detailed_description": "`val` 值为色温值，取值范围[0，255]，0表示暖光，255表示冷光",
                "commands": {
                    "set_color_temp": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置色温，val=色温值[0，255]",
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
                "detailed_description": "`type&1==1`表示处于打开状态；`type&1==0`表示处于关闭状态；`val` 值为亮度值，可调范围：[0，255], 值越大表示光越亮，0处于最暗，光完全熄灭，255处于最亮",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_brightness_on": {
                        "type": 207,
                        "description": "打开并且设置亮度，val=亮度值[0,255]",
                    },
                    "set_brightness_off": {
                        "type": 206,
                        "description": "关闭并设置亮度，val=亮度值[0,255]",
                    },
                },
            },
        },
        "binary_sensor": {
            "P2": {
                "description": "移动检测",
                "rw": "R",
                "data_type": "motion",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下: 0：没有检测到移动, 1:有检测到移动",
                "device_class": BinarySensorDeviceClass.MOTION,
            },
        },
        "sensor": {
            "P3": {
                "description": "环境光照",
                "rw": "R",
                "data_type": "illuminance",
                "conversion": "val_direct",
                "detailed_description": "`val` 值表示原始光照值(单位：lux)",
                "device_class": SensorDeviceClass.ILLUMINANCE,
                "unit_of_measurement": "lux",
                "state_class": SensorStateClass.MEASUREMENT,
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
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭；`val` 值为颜色值，大小4个字节，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White/DYN。例如：红色：`0x00FF0000`, 白色：`0xFF000000`。`bit24~bit31`即可以设置白光又可以设置动态。当其值在[0~100]表示设置的是白光，0表示不显示白光，100表示白光最亮；当其值大于等于128表示设置为动态模式，具体动态值请参考：附录3.2 动态颜色(DYN)定义",
                "commands": {
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值或动态值，val=颜色或动态值",
                    },
                },
            },
        },
        "sensor": {
            "P2": {
                "description": "环境光照",
                "rw": "R",
                "data_type": "illuminance",
                "conversion": "val_direct",
                "detailed_description": "`val` 值表示光照值(单位: lux)",
                "device_class": SensorDeviceClass.ILLUMINANCE,
                "unit_of_measurement": "lux",
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "P3": {
                "description": "充电指示",
                "rw": "R",
                "data_type": "charging_status",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0：没有充电, 1：正在充电，`val`表示原始电压值",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": "V",
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "P4": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery_level",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始电压值,`v` 值将表示当前剩余电量百分比，值范围[0，100]，它是根据val电压值换算的",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    # 2.5 超级碗 (SPOT Series)
    "MSL_IRCTL": {
        "name": "超级碗RGB灯",
        "light": {
            "RGBW": {
                "description": "RGB颜色值",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "range": "0x00000000-0xFFFFFFFF",
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭；`val` 值为颜色值，大小4个字节，定义如下：`bit0`~`bit7`:Blue, `bit8`~`bit15`:Green, `bit16`~`bit23`:Red, `bit24`~`bit31`:white，例如：红色：0x00FF0000, 白色：0xFF000000",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色值，val=颜色值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置颜色值，val=颜色值",
                    },
                },
            },
            "DYN": {
                "description": "动态颜色值",
                "rw": "RW",
                "data_type": "dynamic_effect",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1`表示打开动态；`type&1==0`表示关闭动态；`val`表示动态颜色值，具体动态值请参考：附录3.2 动态颜色（DYN）定义",
                "commands": {
                    "enable": {"type": CMD_TYPE_ON, "val": 1, "description": "使能"},
                    "disable": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_effect_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "使能并设置动态值，val=动态值",
                    },
                    "set_effect_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
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
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭；`val` 值为颜色值，大小4个字节，定义如下：`bit0`~`bit7`:Blue, `bit8`~`bit15`:Green, `bit16`~`bit23`:Red, `bit24`~`bit31`:white，例如：红色：0x00FF0000, 白色：0x00FFFFFF, （当White>0时，表示动态模式）具体动态值请参考：附录3.2动态颜色(DYN)定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
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
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭；`val` 值为颜色值，大小4个字节，定义如下：`bit0`~`bit7`:Blue, `bit8`~`bit15`:Green, `bit16`~`bit23`:Red, `bit24`~`bit31`:white, （当White>0时，表示动态模式）具体动态值请参考：附录3.2动态颜色(DYN)定义",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_color_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置颜色或动态值，val=颜色或动态值",
                    },
                    "set_color_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
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
                "detailed_description": "`type&1==1`，表示打开(忽略`val` 值)；`type&1==0`，表示关闭(忽略`val` 值)；`val` 值为亮度值，值范围[0，255]，255亮度最大",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置亮度，val=亮度值[0，255]",
                    },
                },
            },
            "P2": {
                "description": "色温控制",
                "rw": "RW",
                "data_type": "color_temperature",
                "conversion": "val_direct",
                "range": "0-255",
                "detailed_description": "`val` 值为色温值，取值范围[0，255]，0表示暖光，255表示冷光",
                "commands": {
                    "set_color_temp": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置色温，val=色温值[0,255]",
                    },
                },
            },
            "P3": {
                "description": "夜灯亮度控制",
                "rw": "RW",
                "data_type": "nightlight_brightness",
                "conversion": "val_direct",
                "range": "0,63,127,195,255",
                "detailed_description": "`val` 值为夜灯亮度，共有5档，亮度从低到高分别如下：0、63、127、195、255。0表示夜灯处于关闭状态，255表示夜灯处于最亮状态。注意：若亮度值为其它值则根据如下规则判断亮度档位：0：关闭档，>=196：最亮档，>=128并且<=195：次亮档，>=64并且<=127：第三亮档，>0并且<=63：第四亮档",
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
                "detailed_description": "`type&1==1`，表示打开(忽略`val` 值)；`type&1==0`，表示关闭(忽略`val` 值)；`val` 值为亮度值，值范围[0，255]，255亮度最大",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置亮度，val=亮度值[0，255]",
                    },
                },
            },
            "P2": {
                "description": "色温控制",
                "rw": "RW",
                "data_type": "color_temperature",
                "conversion": "val_direct",
                "range": "0-255",
                "detailed_description": "`val` 值为色温值，取值范围[0，255]，0表示暖光，255表示冷光",
                "commands": {
                    "set_color_temp": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置色温，val=色温值[0,255]",
                    },
                },
            },
            "P3": {
                "description": "夜灯亮度控制",
                "rw": "RW",
                "data_type": "nightlight_brightness",
                "conversion": "val_direct",
                "range": "0,63,127,195,255",
                "detailed_description": "`val` 值为夜灯亮度，共有5档，亮度从低到高分别如下：0、63、127、195、255。0表示夜灯处于关闭状态，255表示夜灯处于最亮状态。注意：若亮度值为其它值则根据如下规则判断亮度档位：0：关闭档，>=196：最亮档，>=128并且<=195：次亮档，>=64并且<=127：第三亮档，>0并且<=63：第四亮档",
                "commands": {
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置亮度，val=亮度值[0、63、127、195、255]",
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
                    "detailed_description": "type&1==1,表示打开(忽略`val` 值)；type&1==0,表示关闭(忽略`val` 值)；",
                    "commands": {
                        "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                        "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    },
                },
                "P4": {
                    "description": "T当前温度",
                    "rw": "R",
                    "data_type": "temperature",
                    "conversion": "v_field",
                    "detailed_description": "`v` 值表示温度值 `val` 值表示原始温度值，它是温度值*10",
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "unit_of_measurement": UnitOfTemperature.CELSIUS,
                    "state_class": SensorStateClass.MEASUREMENT,
                },
                "P5": {
                    "description": "设备种类",
                    "rw": "R",
                    "data_type": "device_type",
                    "conversion": "val_direct",
                    "detailed_description": "val&0xFF指示设备种类。1：开关面板 2：POE面板 3：温控面板 6：温控面板 注意：值必须是3或者6才是温控面板，否则是其它类型的设备。",
                },
                "P6": {
                    "description": "CFG配置",
                    "rw": "RW",
                    "data_type": "config_bitmask",
                    "conversion": "val_direct",
                    "detailed_description": "(val>>6)&0x7 指示设备类型 0：新风模式 1：风机盘管（单阀）模式 2：水地暖模式 3：风机盘管+水地暖模式 4: 风机盘管（双阀）模式 5：水地暖+新风模式",
                    "commands": {
                        "set_config": {
                            "type": CMD_TYPE_SET_RAW_ON,
                            "description": "设置配置，需要保留其它位",
                        },
                    },
                },
                "P7": {
                    "description": "MODE模式",
                    "rw": "RW",
                    "data_type": "hvac_mode",
                    "conversion": "val_direct",
                    "detailed_description": "3：Cool制冷 4：Heat 制热 7：DN地暖 8：DN_Heat 地暖+空调 注意：P6 CFG配置不同，支持的MODE也会不同",
                    "commands": {
                        "set_mode": {
                            "type": CMD_TYPE_SET_CONFIG,
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
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "unit_of_measurement": UnitOfTemperature.CELSIUS,
                    "commands": {
                        "set_temperature": {
                            "type": CMD_TYPE_SET_TEMP_DECIMAL,
                            "description": "设置目标温度，val=温度*10",
                        },
                    },
                },
                "P9": {
                    "description": "tF目标风速",
                    "rw": "RW",
                    "data_type": "fan_speed",
                    "conversion": "val_direct",
                    "detailed_description": "`val` 值表示风速，定义如下：0：Stop停止 0<val<30：Low低档 30<=val<65：Medium中档 65<=val<100：High高档 101：Auto自动 注意：P6 CFG配置不同，支持的tF也会不同",
                    "commands": {
                        "set_fan_speed": {
                            "type": CMD_TYPE_SET_CONFIG,
                            "description": "设置风速",
                        },
                    },
                },
                "P10": {
                    "description": "F当前风速",
                    "rw": "R",
                    "data_type": "fan_speed",
                    "conversion": "val_direct",
                    "detailed_description": "`val` 值表示风速，定义如下：0：stop停止 0<val<30：Low低档 30<=val<65：Medium中档 65<=val<100：High高档 101：Auto自动",
                },
            },
            "binary_sensor": {
                "P2": {
                    "description": "阀门状态",
                    "rw": "R",
                    "data_type": "valve_status",
                    "conversion": "val_direct",
                    "detailed_description": "阀门1状态(盘管的冷阀或者盘管的冷热阀)",
                    "device_class": BinarySensorDeviceClass.OPENING,
                },
                "P3": {
                    "description": "阀门状态",
                    "rw": "R",
                    "data_type": "valve_status",
                    "conversion": "val_direct",
                    "detailed_description": "阀门2状态（盘管的热阀或者地暖阀)",
                    "device_class": BinarySensorDeviceClass.OPENING,
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
                "device_class": BinarySensorDeviceClass.DOOR,
            },
        },
        "sensor": {
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据`val`电压值换算的",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
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
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0：打开，1：关闭",
                "device_class": BinarySensorDeviceClass.DOOR,
            },
            "B": {
                "description": "按键状态",
                "rw": "R",
                "data_type": "button_status",
                "conversion": "val_direct", 
                "detailed_description": "`val` 值定义如下：0：未按下按键，1：按下按键",
                "device_class": BinarySensorDeviceClass.MOVING,
            },
            "AXS": {
                "description": "震动状态",
                "rw": "R",
                "data_type": "vibration_status",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0：无震动，非0：震动",
                "device_class": BinarySensorDeviceClass.VIBRATION,
            },
        },
        "sensor": {
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据`val`电压值换算的",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    "SL_SC_GS": {
        "name": "门禁感应器（增强版）",
        "binary_sensor": {
            "P1": {
                "description": "门禁状态",
                "rw": "R",
                "data_type": "door_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示处于打开状态(忽略`val` 值)；`type&1==0`表示处于吸合状态(忽略`val` 值)",
                "device_class": BinarySensorDeviceClass.DOOR,
            },
            "AXS": {
                "description": "震动状态",
                "rw": "R",
                "data_type": "vibration_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示处于震动状态；`type&1==0`表示无震动状态；`val` 值表示震动强度",
                "device_class": BinarySensorDeviceClass.VIBRATION,
            },
        },
        "sensor": {
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据`val`电压值换算的",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    
    # 2.6.2 动态感应器（Motion Sensor)
    "SL_SC_MHW": {
        "name": "动态感应器",
        "binary_sensor": {
            "M": {
                "description": "移动检测",
                "rw": "R",
                "data_type": "motion_status",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0：没有检测到移动，1：有检测到移动",
                "device_class": BinarySensorDeviceClass.MOTION,
            },
        },
        "sensor": {
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val`表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据`val`电压值换算的",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
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
                "device_class": BinarySensorDeviceClass.MOTION,
            },
        },
        "sensor": {
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val`表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据`val`电压值换算的",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
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
                "device_class": BinarySensorDeviceClass.MOTION,
            },
        },
        "sensor": {
            "P3": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val`表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据`val`电压值换算的",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "P4": {
                "description": "USB供电电压",
                "rw": "R",
                "data_type": "voltage",
                "conversion": "val_direct",
                "detailed_description": "`val`表示原始电压值，若`val` 值大于430则表明电已经充满。若设备连接USB，供电在工作，则应该忽略`P3`电量属性",
                "device_class": SensorDeviceClass.VOLTAGE,
                "unit_of_measurement": "V",
                "state_class": SensorStateClass.MEASUREMENT,
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
                "device_class": BinarySensorDeviceClass.MOTION,
            },
        },
        "sensor": {
            "P2": {
                "description": "当前环境光照",
                "rw": "R",
                "data_type": "illuminance",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始光照值，`v` 值表示实际值(单位：lux)",
                "device_class": SensorDeviceClass.ILLUMINANCE,
                "unit_of_measurement": "lx",
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "P3": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val`表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据`val`电压值换算的",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    
    # 2.6.3 环境感应器（Env Sensor)
    "SL_SC_THL": {
        "name": "环境感应器（温湿度光照）",
        "sensor": {
            "T": {
                "description": "当前环境温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "detailed_description": "`val` 值表示原始温度值，它是温度值*10值(单位：℃)",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "H": {
                "description": "当前环境湿度",
                "rw": "R",
                "data_type": "humidity",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始湿度值，它是湿度值*10，`v` 值表示实际值(单位：%)",
                "device_class": SensorDeviceClass.HUMIDITY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "Z": {
                "description": "当前环境光照",
                "rw": "R",
                "data_type": "illuminance",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始光照值，`v` 值表示实际值(单位：lux)",
                "device_class": SensorDeviceClass.ILLUMINANCE,
                "unit_of_measurement": "lx",
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据`val`电压值换算的",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
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
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "H": {
                "description": "当前环境湿度",
                "rw": "R",
                "data_type": "humidity",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始湿度值，它是湿度值*10，`v` 值表示实际值(单位：%)",
                "device_class": SensorDeviceClass.HUMIDITY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "Z": {
                "description": "当前环境光照",
                "rw": "R",
                "data_type": "illuminance",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始光照值，`v` 值表示实际值(单位：lux)",
                "device_class": SensorDeviceClass.ILLUMINANCE,
                "unit_of_measurement": "lx",
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据`val`电压值换算的",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
        },
    },
    
    # 2.6.4 水浸传感器（Water Flooding Sensor)
    "SL_SC_WA": {
        "name": "水浸传感器",
        "sensor": {
            "WA": {
                "description": "导电率",
                "rw": "R",
                "data_type": "conductivity",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0：未检测到水；值越大表示水越多，导电率越高",
                "device_class": SensorDeviceClass.MOISTURE,
                "unit_of_measurement": "µS/cm",
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据`val`电压值换算的",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    
    # 2.6.5 气体感应器(甲醛)(CH2O Sensor)
    "SL_SC_CH": {
        "name": "甲醛感应器",
        "sensor": {
            "P1": {
                "description": "甲醛浓度",
                "rw": "R",
                "data_type": "formaldehyde",
                "conversion": "v_field",
                "detailed_description": "`type&1==1`表示甲醛浓度值超过告警门限；`val` 值表示甲醛浓度原始值，实际值等于原始值/1000（单位：ug/m³）；`v` 值表示实际值；甲醛浓度安全区间为：[0,0.086]mg/m³ 也即：[0,86]ug/m³",
                "device_class": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
                "unit_of_measurement": "µg/m³",
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
        "switch": {
            "P2": {
                "description": "甲醛浓度告警门限",
                "rw": "RW",
                "data_type": "threshold_setting",
                "conversion": "val_direct",
                "detailed_description": "`val` 值越大则灵敏度越低，门限越高（单位：ug/m³）：不告警：`val=5000`；中灵敏：`val=100`；高灵敏：`val=80`",
                "commands": {
                    "set_sensitivity": {
                        "type": CMD_TYPE_SET_CONFIG,
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
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "手工触发报警音"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "手动消除报警音"},
                },
            },
        },
    },
    
    # 2.6.6 气体感应器(燃气）(Gas Sensor)
    "SL_SC_CP": {
        "name": "燃气感应器",
        "sensor": {
            "P1": {
                "description": "燃气浓度",
                "rw": "R",
                "data_type": "gas_concentration",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1`表示燃气浓度值超过告警门限，有告警；`val`为当前燃气浓度值",
                "device_class": SensorDeviceClass.GAS,
                "unit_of_measurement": "ppm",
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
        "switch": {
            "P2": {
                "description": "燃气浓度告警门限",
                "rw": "RW",
                "data_type": "threshold_setting",
                "conversion": "val_direct",
                "detailed_description": "`val` 值越大则灵敏度越低，门限越高：低灵敏度：`val=150`；中灵敏度：`val=120`；高灵敏度：`val=90`",
                "commands": {
                    "set_sensitivity": {
                        "type": CMD_TYPE_SET_CONFIG,
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
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "手工触发报警音"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "手动消除报警音"},
                },
            },
        },
    },
    
    # 2.6.7 环境感应器 (TVOC+CO2) (TVOC+CO2 Sensor)
    "SL_SC_CQ": {
        "name": "TVOC+CO2环境感应器",
        "sensor": {
            "P1": {
                "description": "当前环境温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始温度值，它是温度值*10，`v` 值表示实际值(单位：℃)",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "P2": {
                "description": "当前环境湿度",
                "rw": "R",
                "data_type": "humidity",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始湿度值，它是湿度值*10，`v` 值表示实际值(单位：%)",
                "device_class": SensorDeviceClass.HUMIDITY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "P3": {
                "description": "当前CO2浓度值",
                "rw": "R",
                "data_type": "co2_concentration",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示co2浓度值，`v` 值表示实际值(单位：ppm)，参考：`val`<=500：优，`val`<=700：良，`val`<=1000：中，`val`>1000：差",
                "device_class": SensorDeviceClass.CO2,
                "unit_of_measurement": "ppm",
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "P4": {
                "description": "当前TVOC浓度值",
                "rw": "R",
                "data_type": "tvoc_concentration",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示tvoc原始浓度值，它是TVOC浓度值*1000，实际浓度值=原始浓度值/1000，`v` 值表示实际值(单位：mg/m3)，参考：`val`<0.34：优，`val`<0.68：良，`val`<=1.02：中，`val`>1.02：差",
                "device_class": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
                "unit_of_measurement": "mg/m³",
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "P5": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据`val`电压值换算的",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "P6": {
                "description": "USB供电电压",
                "rw": "R",
                "data_type": "voltage",
                "conversion": "val_direct",
                "detailed_description": "`val`表示原始电压值，若`val` 值大于430则表明电已经充满。若设备连接USB，供电在工作，则应该忽略`P5`电量属性",
                "device_class": SensorDeviceClass.VOLTAGE,
                "unit_of_measurement": "V",
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    
    # 2.6.8 ELIQ电量计量器(ELIQ)
    "ELIQ_EM": {
        "name": "ELIQ电量计量器",
        "sensor": {
            "EPA": {
                "description": "平均功率",
                "rw": "R",
                "data_type": "power",
                "conversion": "val_direct",
                "detailed_description": "`val` 值表示平均功率",
                "device_class": SensorDeviceClass.POWER,
                "unit_of_measurement": UnitOfPower.WATT,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    
    # 2.6.9 烟雾感应器(Smoke Sensor)
    "SL_P_A": {
        "name": "烟雾感应器",
        "binary_sensor": {
            "P1": {
                "description": "当前是否有烟雾告警",
                "rw": "R",
                "data_type": "smoke_alarm",
                "conversion": "val_direct",
                "detailed_description": "`val`等于0表示没有烟雾告警，等于1表示有烟雾告警",
                "device_class": BinarySensorDeviceClass.SMOKE,
            },
        },
        "sensor": {
            "P2": {
                "description": "电压",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "如果使用9V的电池，则实际电压值=(`val`/100)*3，注意：其值可能会超过9V，例如9.58V；如果外接12V供电，则该值无效。`v` 值将表示当前剩余电量百分比，值范围[0,100]",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    
    # 2.6.10 环境感应器(CO2）(CO2 Sensor)
    "SL_SC_CA": {
        "name": "CO2环境感应器",
        "sensor": {
            "P1": {
                "description": "当前环境温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始温度值，它是温度值*10，`v` 值表示实际值(单位：℃)",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "P2": {
                "description": "当前环境湿度",
                "rw": "R",
                "data_type": "humidity",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始湿度值，它是湿度值*10，`v` 值表示实际值(单位：%)",
                "device_class": SensorDeviceClass.HUMIDITY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "P3": {
                "description": "当前CO2浓度值",
                "rw": "R",
                "data_type": "co2_concentration",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示co2浓度值，`v` 值表示实际值(单位：ppm)，参考：`val`<=500：优，`val`<=700：良，`val`<=1000：中，`val`>1000：差",
                "device_class": SensorDeviceClass.CO2,
                "unit_of_measurement": "ppm",
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "P4": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据`val`电压值换算的",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "P5": {
                "description": "USB供电电压",
                "rw": "R",
                "data_type": "voltage",
                "conversion": "val_direct",
                "detailed_description": "`val`表示原始电压值，若`val` 值大于430则表明供电在工作，否则表明未供电工作",
                "device_class": SensorDeviceClass.VOLTAGE,
                "unit_of_measurement": "V",
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    
    # 2.6.11 人体存在感应器（Radar Motion Sensor)
    "SL_P_RM": {
        "name": "雷达人体存在感应器",
        "binary_sensor": {
            "P1": {
                "description": "移动检测(Motion)",
                "rw": "R",
                "data_type": "motion_status",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0：没有检测到移动，非0：有检测到移动",
                "device_class": BinarySensorDeviceClass.MOTION,
            },
        },
        "switch": {
            "P2": {
                "description": "移动检测参数设置",
                "rw": "RW",
                "data_type": "radar_config",
                "conversion": "val_direct",
                "detailed_description": "包含动态锁定时间与灵敏度设置。其中：`bit0-bit7`：动态锁定时间，取值范围为：1-255，具体锁定时间为：配置值*4，单位为秒，例如`bit0-bit7`配置值为16，则表示动态锁定时间为64秒。`bit8-bit25`：灵敏度，灵敏度默认值为4，范围1-255，值越小则越灵敏",
                "commands": {
                    "set_config": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "description": "设置感应器动态锁定时间与灵敏度",
                    },
                },
            },
        },
    },
    
    # 2.6.12 云防门窗感应器（DEFED Window/Door)
    "SL_DF_GG": {
        "name": "云防门窗感应器",
        "binary_sensor": {
            "A": {
                "description": "当前状态",
                "rw": "R",
                "data_type": "door_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示处于打开状态(忽略`val` 值)；`type&1==0`表示处于吸合状态(忽略`val` 值)",
                "device_class": BinarySensorDeviceClass.DOOR,
            },
            "A2": {
                "description": "外部感应器状态",
                "rw": "R",
                "data_type": "door_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示处于打开状态(忽略`val` 值)；`type&1==0`表示处于吸合状态(忽略`val` 值)；需要接外部感应器，如果没有接则type值为1",
                "device_class": BinarySensorDeviceClass.DOOR,
            },
            "TR": {
                "description": "防拆状态",
                "rw": "R",
                "data_type": "tamper_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`则表示触发防拆警报；`type&1==0`则表示状态正常",
                "device_class": BinarySensorDeviceClass.TAMPER,
            },
        },
        "sensor": {
            "T": {
                "description": "温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始温度值，它是实际温度值*10，`v` 值表示实际值(单位：℃)",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据`val`电压值换算的。注意：`type&1==1`表示低电报警状态",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    
    # 2.6.13 云防动态感应器（DEFED Motion)
    "SL_DF_MM": {
        "name": "云防动态感应器",
        "binary_sensor": {
            "M": {
                "description": "当前状态",
                "rw": "R",
                "data_type": "motion_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示侦测到人体移动(忽略`val` 值)；`type&1==0`表示没有侦测到人体移动(忽略`val` 值)",
                "device_class": BinarySensorDeviceClass.MOTION,
            },
            "TR": {
                "description": "防拆状态",
                "rw": "R",
                "data_type": "tamper_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`则表示触发防拆警报；`type&1==0`则表示状态正常",
                "device_class": BinarySensorDeviceClass.TAMPER,
            },
        },
        "sensor": {
            "T": {
                "description": "温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始温度值，它是实际温度值*10，`v` 值表示实际值(单位：℃)",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据`val`电压值换算的。注意：`type&1==1`表示低电报警状态",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    
    # 2.6.14 云防室内警铃(DEFED Indoor Siren)
    "SL_DF_SR": {
        "name": "云防室内警铃",
        "binary_sensor": {
            "SR": {
                "description": "当前状态",
                "rw": "R",
                "data_type": "siren_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示警铃播放(忽略`val` 值)；`type&1==0`表示正常(忽略`val` 值)",
                "device_class": BinarySensorDeviceClass.SOUND,
            },
            "TR": {
                "description": "防拆状态",
                "rw": "R",
                "data_type": "tamper_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`则表示触发防拆警报；`type&1==0`则表示状态正常",
                "device_class": BinarySensorDeviceClass.TAMPER,
            },
        },
        "sensor": {
            "T": {
                "description": "温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始温度值，它是实际温度值*10，`v` 值表示实际值(单位：℃)",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据val电压值换算的。注意：`type&1==1`表示低电报警状态",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
        "switch": {
            "P1": {
                "description": "报警设置",
                "rw": "RW",
                "data_type": "alarm_config",
                "conversion": "val_direct",
                "detailed_description": "`val`为32bit值，描述如下(16进制)：`0xAABBCCDD`：`AABB`表示警报持续时长，单位为0.1秒；`CC`是声音强度(136-255)，255最强，136最弱；`DD`表示音频序号：0：无，1：信息，2：告警",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "播放"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "停止"},
                    "set_config_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "设置值并播放",
                    },
                    "set_config_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "设置值并停止",
                    },
                },
            },
        },
    },
    
    # 2.6.15 云防遥控器（DEFED Key Fob)
    "SL_DF_BB": {
        "name": "云防遥控器",
        "binary_sensor": {
            "eB1": {
                "description": "按键1状态(为布防图标)",
                "rw": "R",
                "data_type": "button_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示按键处于按下状态(忽略`val` 值)；`type&1==0`表示按键处于松开状态(忽略`val` 值)",
                "device_class": BinarySensorDeviceClass.MOVING,
            },
            "eB2": {
                "description": "按键2状态(为撤防图标)",
                "rw": "R",
                "data_type": "button_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示按键处于按下状态(忽略`val` 值)；`type&1==0`表示按键处于松开状态(忽略`val` 值)",
                "device_class": BinarySensorDeviceClass.MOVING,
            },
            "eB3": {
                "description": "按键3状态(为警告图标)",
                "rw": "R",
                "data_type": "button_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示按键处于按下状态(忽略`val` 值)；`type&1==0`表示按键处于松开状态(忽略`val` 值)",
                "device_class": BinarySensorDeviceClass.MOVING,
            },
            "eB4": {
                "description": "按键4状态(为在家图标)",
                "rw": "R",
                "data_type": "button_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示按键处于按下状态(忽略`val` 值)；`type&1==0`表示按键处于松开状态(忽略`val` 值)",
                "device_class": BinarySensorDeviceClass.MOVING,
            },
        },
        "sensor": {
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据`val`电压值换算的。注意：`type&1==1`表示低电报警状态",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    
    # 2.6.16 噪音感应器（Noise Sensor)
    "SL_SC_CN": {
        "name": "噪音感应器",
        "sensor": {
            "P1": {
                "description": "噪音值",
                "rw": "R",
                "data_type": "noise_level",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1`表示噪音值大于告警门限；`type&1==0`表示噪音值没有超过告警门限；`val`表示当前噪音值，单位为分贝",
                "device_class": SensorDeviceClass.SOUND_PRESSURE,
                "unit_of_measurement": "dB",
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "P4": {
                "description": "噪音校正值",
                "rw": "RW",
                "data_type": "noise_calibration",
                "conversion": "val_direct",
                "detailed_description": "取值范围为[-128~127]，如果噪音采样有误差，可以配置噪音校正值校正",
                "device_class": SensorDeviceClass.SOUND_PRESSURE,
                "unit_of_measurement": "dB",
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
        "switch": {
            "P2": {
                "description": "告警门限设置",
                "rw": "RW",
                "data_type": "threshold_config",
                "conversion": "val_direct",
                "detailed_description": "`val`为32bit值(十六进制)：`0xAABBCCDD`：`DD`表示告警门限值，数值单位为分贝，取值范围[0,255]；`CC`表示采样值1，取值范围[0,255]；`BB`表示采样值2，取值范围[0,255]；`CCBB`共同作用形成越限率",
                "commands": {
                    "set_threshold": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "修改门限值",
                    },
                },
            },
            "P3": {
                "description": "报警设置",
                "rw": "RW",
                "data_type": "alarm_config",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1`表示处于报警状态；`type&1==0`表示处于正常状态；`val`为32bit值，描述如下(16进制)：`0xAABBCCDD`：`AABB`表示警报持续时长，单位为0.1秒，等于65535则表示一直持续；`CC`是声音强度，0表示没有声音，其它值表示有声音；`DD`表示音频模式：0：无声音，1：指示音，2：告警音，0x7F：测试音，0x80-0xFF：自定义模式",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "播放"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "停止"},
                    "set_config_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "设置值并播放",
                    },
                    "set_config_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "设置值并停止",
                    },
                },
            },
        },
    },
}

# --- 动态分类设备列表 (Dynamic Classification Devices) ---
# 这些设备的平台归属由 helpers.py 中的逻辑决定
DYNAMIC_CLASSIFICATION_DEVICES = {
    "SL_NATURE",  # 根据P5值决定是开关版还是温控版
    "SL_P",  # 根据P1工作模式决定功能
    "SL_JEMA",  # 同SL_P，但额外支持P8/P9/P10独立开关
}

# --- 需要根据fullCls区分版本的设备类型 ---
# 注意：只有在IO口和功能上真正有差异的设备才需要版本区分
VERSIONED_DEVICE_TYPES = {
    # 调光开关系列 - 根据fullCls区分不同版本功能
    "SL_SW_DM1": {
        # SL_SW_DM1_V1为动态调光开关 - 具有传感器和智能控制功能
        # IO口: P1(开关+亮度 RW) P2(指示灯 RW) P3(移动检测 R) P4(环境光照 R) P5(调光设置 RW) P6(动态设置 RW)
        "V1": "motion_dimmer",
        # SL_SW_DM1_V2为星玉调光开关(可控硅) - 基础调光功能
        # IO口: P1(开关+亮度 RW) P2(指示灯亮度 RW)
        "V2": "triac_dimmer",
    },
    # 白光调光灯版本区分 - 基于相同的IO口功能
    "SL_LI_WW": {
        # SL_LI_WW_V1智能灯泡(冷暖白) - 同SL_LI_WW规范
        # IO口: P1(亮度控制 RW) P2(色温控制 RW)
        "V1": "dimmable_light_v1",
        # SL_LI_WW_V2调光调色智控器(0-10V) - 同SL_LI_WW规范
        # IO口: P1(亮度控制 RW) P2(色温控制 RW)
        "V2": "dimmable_light_v2",
    },
}

# --- Home Assistant 支持的平台列表 ---
SUPPORTED_PLATFORMS = {
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.COVER,
    Platform.LIGHT,
    Platform.CLIMATE,
    Platform.LOCK,
    Platform.BUTTON,
    Platform.FAN,
    Platform.EVENT,
    Platform.NUMBER,
    Platform.SIREN,
    Platform.VALVE,
    Platform.AIR_QUALITY,
    Platform.REMOTE,
    Platform.CAMERA,
}

# ================= 技术定义 (Technical Constants) =================

# 第三方设备版本映射 - 参考官方文档附录3.6
# 当设备通过通用控制器接入第三方设备时，可根据ver值判别具体设备型号
THIRD_PARTY_DEVICES = {
    "V_AIR_P": {
        "0.0.0.1": {
            "code": "000001",
            "model": "DTA116A621",
            "name": "大金空调DTA116A621",
        },
        "0.0.0.2": {"code": "000002", "model": "KRAVEN_VRV", "name": "空调VRV控制器"},
        "0.0.0.7": {"code": "000007", "model": "TM8X", "name": "特灵"},
        "0.0.0.10": {"code": "00000A", "model": "KL420", "name": "开利420C"},
        "0.0.0.15": {
            "code": "00000F",
            "model": "MEDIA-CCM18",
            "name": "美的多联机MODBUS网关-CCM18",
        },
        "0.0.0.17": {
            "code": "000011",
            "model": "PHNIX-ST800",
            "name": "芬尼ST800二合一温控面板",
        },
        "0.0.0.18": {
            "code": "000012",
            "model": "SHINEFAN-G9",
            "name": "祥帆新风G9面板",
        },
        "0.0.0.19": {
            "code": "000013",
            "model": "TCB-IFMB646TLE",
            "name": "东芝空调网关TCB-IFMB646TLE",
        },
        "0.0.0.21": {
            "code": "000015",
            "model": "THT420B",
            "name": "开利空调面板THT420B",
        },
        "0.0.0.24": {
            "code": "000018",
            "model": "NetproDual",
            "name": "NetPro Dual DAIKIN",
        },
        "0.0.0.31": {"code": "00001F", "model": "CLP5DO", "name": "三恒系统"},
    },
    "V_FRESH_P": {
        "0.0.0.3": {"code": "000003", "model": "KV11_RTU", "name": "艾弗纳KV11"},
        "0.0.0.8": {"code": "000008", "model": "CA-S2", "name": "森德"},
        "0.0.0.22": {
            "code": "000016",
            "model": "NAVIEN-TAC550",
            "name": "NAVIEN新风主机NAVIEN-TAC550",
        },
        "0.0.0.23": {
            "code": "000017",
            "model": "KD-1-E",
            "name": "兰舍新风控制器KD-1-E",
        },
        "0.0.0.31": {"code": "00001F", "model": "CLP5DO", "name": "三恒系统"},
    },
    "V_485_P": {
        "0.0.0.12": {
            "code": "00000C",
            "model": "RY-A101",
            "name": "气体压力传感器RY_A101",
        },
        "0.0.0.13": {"code": "00000D", "model": "KL-19XR", "name": "KL-19XR"},
        "0.0.0.25": {"code": "000019", "model": "GD-H2S", "name": "GD-H2S"},
        "0.0.0.26": {
            "code": "00001A",
            "model": "HQ100-S12",
            "name": "智能照明控制模块HQ100-S12",
        },
        "0.0.0.27": {"code": "00001B", "model": "DTSR958", "name": "导轨电能表"},
        "0.0.0.28": {
            "code": "00001C",
            "model": "ZXB1L-125",
            "name": "智能断路器ZXB1L-125",
        },
        "0.0.0.29": {
            "code": "00001D",
            "model": "ZXB1L-3-125",
            "name": "智能断路器3相ZXB1L-3-125",
        },
        "0.0.0.30": {
            "code": "00001E",
            "model": "HD120A16GK",
            "name": "HDHK智能电流采集器HD120A16GK",
        },
        "0.0.0.32": {
            "code": "000020",
            "model": "BF-12LI",
            "name": "BF-12LI智能采集模块",
        },
    },
    "V_DLT645_P": {
        "0.0.0.6": {"code": "000006", "model": "DLT645", "name": "DLT645"},
    },
}


# ================= 动态效果映射 (Dynamic Effects Mappings) =================
# --- 通用动态效果 ---
# 动态颜色（DYN）定义 - 参考官方文档附录3.2
# 这些值用于设备的动态颜色效果，如彩灯、开关指示灯等
DYN_EFFECT_MAP = {
    "青草": 0x8218CC80,
    "海浪": 0x8318CC80,
    "深蓝山脈": 0x8418CC80,
    "紫色妖姬": 0x8518CC80,
    "树莓": 0x8618CC80,
    "橙光": 0x8718CC80,
    "秋实": 0x8818CC80,
    "冰淇淋": 0x8918CC80,
    "高原": 0x8020CC80,
    "披萨": 0x8120CC80,
    "果汁": 0x8A20CC80,
    "温暖小屋": 0x8B30CC80,
    "魔力红": 0x9318CC80,
    "光斑": 0x9518CC80,
    "蓝粉知己": 0x9718CC80,
    "晨曦": 0x9618CC80,
    "木槿": 0x9818CC80,
    "缤纷时代": 0x9918CC80,
    "天上人间": 0xA318CC80,
    "魅蓝": 0xA718CC80,
    "炫红": 0xA918CC80,
}
# 量子灯特殊（DYN）定义 - 参考官方文档附录3.3
# 量子灯专用的特殊动态效果
# --- 量子灯特殊动态效果 ---
QUANTUM_EFFECT_MAP = {
    "马戏团": 0x04810130,
    "北极光": 0x04C40600,
    "黑凤梨": 0x03BC0190,
    "十里桃花": 0x04940800,
    "彩虹糖": 0x05BD0690,
    "云起": 0x04970400,
    "日出印象": 0x01C10A00,
    "马卡龙": 0x049A0E00,
    "光盘时代": 0x049A0000,
    "动感光波": 0x0213A400,
    "圣诞节": 0x068B0900,
    "听音变色": 0x07BD0990,  # 第二代量子灯才支持
}

# 将动态效果和量子灯光效果映射合并
DYN_EFFECT_LIST = list(DYN_EFFECT_MAP.keys())
ALL_EFFECT_MAP = {**DYN_EFFECT_MAP, **QUANTUM_EFFECT_MAP}
ALL_EFFECT_LIST = list(ALL_EFFECT_MAP.keys())


# ================= 其他配置映射 =================

# 无位置窗帘配置映射 (用于将开/关/停动作映射到正确的IO口)
NON_POSITIONAL_COVER_CONFIG = {
    "SL_SW_WIN": {"open": "OP", "close": "CL", "stop": "ST"},
    "SL_P_V2": {
        "open": "P2",
        "close": "P3",
        "stop": "P4",
    },  # 不是版本设备，真实设备名称
    "SL_CN_IF": {"open": "P1", "close": "P2", "stop": "P3"},
    "SL_CN_FE": {"open": "P1", "close": "P2", "stop": "P3"},
    # 通用控制器
    "SL_P": {"open": "P2", "close": "P3", "stop": "P4"},
    "SL_JEMA": {"open": "P2", "close": "P3", "stop": "P4"},
}

# 服务器区域选项 (用于配置流程)
LIFESMART_REGION_OPTIONS = [
    "cn0",
    "cn1",
    "cn2",
    "us",
    "eur",
    "jp",
    "apz",
    "AUTO",
]
