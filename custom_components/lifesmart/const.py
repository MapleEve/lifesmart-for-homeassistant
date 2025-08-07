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
    Platform,
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
        "name": "随心开关二位",
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
    "SL_SW_RC3": {
        "name": "随心开关三位",
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
    # 2.2.2 恒星/辰星/极星开关系列 (Star Series Switch)
    "SL_SW_ND1": {
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
    # 2.2.3 开关控制器系列 (Switch Controller Series)
    "SL_S": {
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
    # 2.2.5 奇点开关模块系列 (Singularity Switch Module Series)
    "SL_SW_MJ1": {
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
