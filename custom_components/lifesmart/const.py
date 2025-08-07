"""由 @MapleEve 实现的 LifeSmart 集成常量模块。

此文件定义了所有与 LifeSmart 平台交互所需的硬编码常量、设备类型代码、API命令码、
以及用于在 Home Assistant 和 LifeSmart 之间转换数据的映射。

维护此文件的准确性和清晰度对于整个集成的稳定和可扩展性至关重要。
"""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.climate.const import (
    HVACMode,
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
)
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    Platform,
    PERCENTAGE,
    LIGHT_LUX,
    UnitOfTemperature,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfEnergy,
    CONCENTRATION_PARTS_PER_MILLION,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
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

MULTI_PLATFORM_DEVICE_MAPPING = {
    # ================= 动态分类设备 (Dynamic Classification Devices) =================
    # 这些设备根据配置或状态动态决定功能平台
    # 超能面板 - 动态分类：开关版 vs 温控版
    "SL_NATURE": {
        "dynamic": True,
        "switch_mode": {
            "condition": "P5&0xFF==1",
            "io": ["P1", "P2", "P3"],
            "sensor_io": ["P4", "P5"],
        },
        "climate_mode": {
            "condition": "P5&0xFF in [3,6]",
            "io": ["P1", "P4", "P5", "P6", "P7", "P8", "P9", "P10"],
            "sensor_io": ["P4", "P5"],
            "binary_sensor_io": ["P2", "P3"],  # 超能面板和星玉面板的阀门开关检测
        },
    },
    # 通用控制器 - 动态分类：二元传感器/窗帘/开关
    "SL_P": {
        "dynamic": True,
        "binary_sensor_mode": {
            "condition": "(P1>>24)&0xE==0",
            "io": ["P1", "P5", "P6", "P7"],
        },
        "cover_mode": {
            "condition": "(P1>>24)&0xE in [2,4]",
            "io": ["P1", "P2", "P3", "P4"],
        },
        "switch_mode": {
            "condition": "(P1>>24)&0xE in [8,10]",
            "io": ["P1", "P2", "P3", "P4"],
        },
    },
    # 通用控制器HA版 - 在SL_P基础上额外支持P8/P9/P10独立开关
    "SL_JEMA": {
        "dynamic": True,
        "binary_sensor_mode": {
            "condition": "(P1>>24)&0xE==0",
            "io": ["P1", "P5", "P6", "P7"],
        },
        "cover_mode": {
            "condition": "(P1>>24)&0xE in [2,4]",
            "io": ["P1", "P2", "P3", "P4"],
        },
        "switch_mode": {
            "condition": "(P1>>24)&0xE in [8,10]",
            "io": ["P1", "P2", "P3", "P4"],
        },
        "always_switch": {
            "io": ["P8", "P9", "P10"],
            "description": "HA独立开关端口，不受P1工作模式影响",
        },
    },
    # ================= 开关设备 (Switch Devices) =================
    # 单一开关功能或主要开关功能的设备
    # ================= 基础插座系列 (Basic Outlet Series) =================
    "SL_OL": {
        "switch": {
            "O": {
                "description": "插座开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
    },
    "SL_OL_3C": {
        "switch": {
            "O": {
                "description": "3C版插座开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
    },
    "SL_OL_UK": {
        "switch": {
            "O": {
                "description": "英标插座开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
    },
    "SL_OL_UL": {
        "switch": {
            "O": {
                "description": "美标插座开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
    },
    "SL_OL_DE": {
        "switch": {
            "O": {
                "description": "德标插座开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
    },
    "OD_WE_OT1": {
        "switch": {
            "P1": {
                "description": "Wi-Fi插座开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
    },
    # 开关控制器系列
    "SL_S": {
        "switch": {
            "P2": {
                "description": "通用开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
    },
    "SL_P_SW": {
        "switch": {
            "P1": {
                "description": "九路开关控制第1路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "auto_off": {"type": CMD_TYPE_PRESS, "val": "duration_100ms"},
                },
                "special": "支持自动关闭功能，val参数为持续时长(100ms为单位)",
            },
            "P2": {
                "description": "九路开关控制第2路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "auto_off": {"type": CMD_TYPE_PRESS, "val": "duration_100ms"},
                },
            },
            "P3": {
                "description": "九路开关控制第3路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "auto_off": {"type": CMD_TYPE_PRESS, "val": "duration_100ms"},
                },
            },
            "P4": {
                "description": "九路开关控制第4路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "auto_off": {"type": CMD_TYPE_PRESS, "val": "duration_100ms"},
                },
            },
            "P5": {
                "description": "九路开关控制第5路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "auto_off": {"type": CMD_TYPE_PRESS, "val": "duration_100ms"},
                },
            },
            "P6": {
                "description": "九路开关控制第6路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "auto_off": {"type": CMD_TYPE_PRESS, "val": "duration_100ms"},
                },
            },
            "P7": {
                "description": "九路开关控制第7路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "auto_off": {"type": CMD_TYPE_PRESS, "val": "duration_100ms"},
                },
            },
            "P8": {
                "description": "九路开关控制第8路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "auto_off": {"type": CMD_TYPE_PRESS, "val": "duration_100ms"},
                },
            },
            "P9": {
                "description": "九路开关控制第9路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "auto_off": {"type": CMD_TYPE_PRESS, "val": "duration_100ms"},
                },
            },
        },
    },
    # 奇点开关模块系列
    "SL_SW_MJ1": {
        "switch": {
            "P1": {
                "description": "单路开关模块",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
    },
    "SL_SW_MJ2": {
        "switch": {
            "P1": {
                "description": "双路开关模块第1路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P2": {
                "description": "双路开关模块第2路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
    },
    "SL_SW_MJ3": {
        "switch": {
            "P1": {
                "description": "三路开关模块第1路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P2": {
                "description": "三路开关模块第2路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P3": {
                "description": "三路开关模块第3路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
    },
    # 极星开关120V零火版系列
    "SL_SW_BS1": {
        "switch": {
            "P1": {
                "description": "单路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
    },
    "SL_SW_BS2": {
        "switch": {
            "P1": {
                "description": "双路开关控制第1路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P2": {
                "description": "双路开关控制第2路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
    },
    "SL_SW_BS3": {
        "switch": {
            "P1": {
                "description": "三路开关控制第1路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P2": {
                "description": "三路开关控制第2路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P3": {
                "description": "三路开关控制第3路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
    },
    # 虚拟开关
    "V_IND_S": {
        "switch": {
            "P1": {
                "description": "虚拟开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
    },
    "V_HG_L": {
        "switch": {
            "P1": {
                "description": "极速开关组",
                "rw": "R",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
    },
    # ================= 开关+传感器设备 (Switch + Sensor Devices) =================
    # 同时具有开关和传感器功能的设备
    # 恒星/辰星/极星系列 - 开关 + 电量传感器
    "SL_SW_ND1": {
        "switch": {
            "P1": {
                "description": "单键开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "sensor": {
            "P2": {
                "description": "电池电量",
                "rw": "R",
                "data_type": "battery",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
                "conversion": "voltage_to_battery",
            },
        },
    },
    "SL_MC_ND1": {
        "switch": {
            "P1": {
                "description": "单键开关伴侣控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "sensor": {
            "P2": {
                "description": "电池电量",
                "rw": "R",
                "data_type": "battery",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
                "conversion": "voltage_to_battery",
            },
        },
    },
    "SL_SW_ND2": {
        "switch": {
            "P1": {
                "description": "双键开关控制第1路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P2": {
                "description": "双键开关控制第2路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "sensor": {
            "P3": {
                "description": "电池电量",
                "rw": "R",
                "data_type": "battery",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
                "conversion": "voltage_to_battery",
            },
        },
    },
    "SL_MC_ND2": {
        "switch": {
            "P1": {
                "description": "双键开关伴侣控制第1路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P2": {
                "description": "双键开关伴侣控制第2路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "sensor": {
            "P3": {
                "description": "电池电量",
                "rw": "R",
                "data_type": "battery",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
                "conversion": "voltage_to_battery",
            },
        },
    },
    "SL_SW_ND3": {
        "switch": {
            "P1": {
                "description": "三键开关控制第1路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P2": {
                "description": "三键开关控制第2路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P3": {
                "description": "三键开关控制第3路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "sensor": {
            "P4": {
                "description": "电池电量",
                "rw": "R",
                "data_type": "battery",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
                "conversion": "voltage_to_battery",
            },
        },
    },
    "SL_MC_ND3": {
        "switch": {
            "P1": {
                "description": "三键开关伴侣控制第1路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P2": {
                "description": "三键开关伴侣控制第2路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P3": {
                "description": "三键开关伴侣控制第3路",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "sensor": {
            "P4": {
                "description": "电池电量",
                "rw": "R",
                "data_type": "battery",
                "device_class": "battery",
                "unit_of_measurement": "%",
                "state_class": "measurement",
                "conversion": "voltage_to_battery",
            },
        },
    },
    # 星玉情景面板 - 多开关
    "SL_SW_NS6": {
        "switch": {
            "P1": {
                "description": "情景开关P1",
                "rw": "RW",
                "data_type": "scene_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P2": {
                "description": "情景开关P2",
                "rw": "RW", 
                "data_type": "scene_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P3": {
                "description": "情景开关P3",
                "rw": "RW",
                "data_type": "scene_switch", 
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P4": {
                "description": "情景开关P4",
                "rw": "RW",
                "data_type": "scene_switch",
                "conversion": "type_bit_0", 
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
    },
    # ================= 开关+灯光设备 (Switch + Light Devices) =================
    # 同时具有开关控制和指示灯功能的设备
    # 入墙插座 - 开关 + 指示灯
    "SL_OL_W": {
        "switch": {
            "L1": {
                "description": "插座开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯颜色控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright": {
                "description": "开状态时指示灯颜色控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
        },
    },
    # ================= 流光开关系列 (Flow Light Switch Series) =================
    "SL_SW_IF1": {
        "switch": {
            "L1": {
                "description": "第一路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",  # type&1==1表示打开; type&1==0表示关闭
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",  # bit0-7:Blue, bit8-15:Green, bit16-23:Red, bit24-31:White
                "dynamic_support": True,  # White>0时支持动态模式
            },
            "bright": {
                "description": "开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
        },
    },
    "SL_SW_IF2": {
        "switch": {
            "L1": {
                "description": "第一路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "L2": {
                "description": "第二路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
        },
    },
    "SL_SW_IF3": {
        "switch": {
            "L1": {
                "description": "第一路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "L2": {
                "description": "第二路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "L3": {
                "description": "第三路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "dark3": {
                "description": "第三路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright3": {
                "description": "第三路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
        },
    },
    # ================= 塞纳/格致开关系列 (Senna/Gezhi Switch Series) =================
    "SL_SW_FE1": {
        "switch": {
            "L1": {
                "description": "第一路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright": {
                "description": "开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
        },
    },
    "SL_SW_FE2": {
        "switch": {
            "L1": {
                "description": "第一路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "L2": {
                "description": "第二路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
        },
    },
    # ================= 橙朴流光开关系列 (Orange Piapo Flow Light Switch Series) =================
    "SL_SW_CP1": {
        "switch": {
            "L1": {
                "description": "第一路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright": {
                "description": "开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
        },
    },
    "SL_SW_CP2": {
        "switch": {
            "L1": {
                "description": "第一路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "L2": {
                "description": "第二路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
        },
    },
    "SL_SW_CP3": {
        "switch": {
            "L1": {
                "description": "第一路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "L2": {
                "description": "第二路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "L3": {
                "description": "第三路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "dark3": {
                "description": "第三路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright3": {
                "description": "第三路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
        },
    },
    # ================= 单火流光开关系列 (Single-Wire Flow Light Switch Series) =================
    "SL_SF_IF1": {
        "switch": {
            "L1": {
                "description": "第一路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright": {
                "description": "开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
        },
    },
    "SL_SF_IF2": {
        "switch": {
            "L1": {
                "description": "第一路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "L2": {
                "description": "第二路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
        },
    },
    "SL_SF_IF3": {
        "switch": {
            "L1": {
                "description": "第一路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "L2": {
                "description": "第二路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "L3": {
                "description": "第三路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "dark3": {
                "description": "第三路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright3": {
                "description": "第三路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
        },
    },
    "SL_SF_RC": {
        "switch": {
            "L1": {
                "description": "第一路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "L2": {
                "description": "第二路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "L3": {
                "description": "第三路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright": {
                "description": "开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
        },
    },
    # 触摸开关/极星开关零火版系列 - 开关 + 指示灯
    "SL_SW_RC": {
        "switch": {
            "L1": {
                "description": "第一路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "L2": {
                "description": "第二路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "L3": {
                "description": "第三路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright": {
                "description": "开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
        },
    },
    # 白玉/墨玉流光开关系列 - 开关 + 指示灯
    "SL_SW_RC1": {
        "switch": {
            "L1": {
                "description": "单路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright": {
                "description": "开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
        },
    },
    "SL_SW_RC2": {
        "switch": {
            "L1": {
                "description": "第一路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "L2": {
                "description": "第二路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
        },
    },
    "SL_SW_RC3": {
        "switch": {
            "L1": {
                "description": "第一路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "L2": {
                "description": "第二路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "L3": {
                "description": "第三路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "dark3": {
                "description": "第三路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright3": {
                "description": "第三路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
        },
    },
    # 星玉开关系列 - 开关 + 指示灯
    "SL_SW_NS1": {
        "switch": {
            "L1": {
                "description": "单路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright": {
                "description": "开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
        },
    },
    "SL_SW_NS2": {
        "switch": {
            "L1": {
                "description": "第一路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "L2": {
                "description": "第二路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
        },
    },
    "SL_SW_NS3": {
        "switch": {
            "L1": {
                "description": "第一路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "L2": {
                "description": "第二路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "L3": {
                "description": "第三路开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "light": {
            "dark1": {
                "description": "第一路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "dark2": {
                "description": "第二路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "dark3": {
                "description": "第三路关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright1": {
                "description": "第一路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright2": {
                "description": "第二路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
            "bright3": {
                "description": "第三路开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "dynamic_support": True,
            },
        },
    },
    # ================= 灯光设备 (Light Devices) =================
    # 纯灯光控制设备，主要或仅具有灯光功能
    # 白光调光灯
    "SL_SPWM": {
        "light": {
            "P1": {
                "description": "白光亮度控制",
                "rw": "RW",
                "data_type": "brightness",
                "conversion": "val_to_brightness",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                        "val": "brightness_value",
                    },
                },
                "brightness_range": [0, 100],
                "support_brightness": True,
            },
        },
    },
    "SL_SW_WW": {
        "light": {
            "P1": {
                "description": "星玉调光开关亮度控制",
                "rw": "RW",
                "data_type": "brightness",
                "conversion": "val_to_brightness",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                        "val": "brightness_value",
                    },
                },
                "brightness_range": [0, 100],
                "support_brightness": True,
            },
            "P2": {
                "description": "色温控制",
                "rw": "RW",
                "data_type": "color_temp",
                "conversion": "val_to_color_temp",
                "commands": {
                    "set_color_temp": {
                        "type": CMD_TYPE_SET_VAL,
                        "val": "color_temp_value",
                    },
                },
                "color_temp_range": [2700, 6500],  # 暖白到冷白
                "support_color_temp": True,
            },
        },
        "sensor": {
            "P1": {
                "description": "当前亮度状态",
                "device_class": "illuminance",
                "unit_of_measurement": "%",
                "state_class": "measurement",
                "rw": "R",
                "data_type": "brightness_status",
                "conversion": "v_or_val",
                "commands": {},
            },
        },
    },
    "SL_LI_IR": {
        "light": {
            "P1": {
                "description": "红外吸顶灯暖白光控制",
                "rw": "RW",
                "data_type": "brightness",
                "conversion": "val_to_brightness",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                        "val": "brightness_value",
                    },
                },
                "brightness_range": [0, 100],
                "support_brightness": True,
                "light_type": "warm_white",
            },
            "P2": {
                "description": "红外吸顶灯冷白光控制",
                "rw": "RW",
                "data_type": "brightness",
                "conversion": "val_to_brightness",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                        "val": "brightness_value",
                    },
                },
                "brightness_range": [0, 100],
                "support_brightness": True,
                "light_type": "cool_white",
            },
            "P3": {
                "description": "红外吸顶灯夜灯模式",
                "rw": "RW",
                "data_type": "night_light",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
                "light_type": "night_light",
            },
        },
    },
    # RGB/RGBW灯光设备
    "SL_SC_RGB": {
        "light": {
            "RGB": {
                "description": "RGB三色灯颜色控制",
                "rw": "RW",
                "data_type": "rgb_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_rgb": {"type": CMD_TYPE_SET_RAW_ON, "val": "rgb_color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "rgb_color_value",
                    },
                },
                "color_format": "RGB",  # bit0-7:Blue, bit8-15:Green, bit16-23:Red
                "support_color": True,
            },
        },
    },
    "SL_CT_RGBW": {
        "light": {
            "RGBW": {
                "description": "RGBW四色灯颜色控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_rgbw": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "val": "rgbw_color_value",
                    },
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "rgbw_color_value",
                    },
                },
                "color_format": "RGBW",  # bit0-7:Blue, bit8-15:Green, bit16-23:Red, bit24-31:White
                "support_color": True,
            },
            "DYN": {
                "description": "动态灯效控制",
                "rw": "RW",
                "data_type": "dynamic_effect",
                "conversion": "raw_value",
                "commands": {
                    "set_effect": {"type": CMD_TYPE_SET_RAW_ON, "val": "effect_value"},
                    "stop_effect": {"type": CMD_TYPE_SET_RAW_OFF, "val": 0},
                },
                "support_effects": True,
                "available_effects": "DYN_EFFECT_LIST",
            },
        },
    },
    "SL_LI_RGBW": {
        "light": {
            "RGBW": {
                "description": "RGBW智能灯泡颜色控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_rgbw": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "val": "rgbw_color_value",
                    },
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "rgbw_color_value",
                    },
                },
                "color_format": "RGBW",
                "support_color": True,
            },
            "DYN": {
                "description": "智能灯泡动态灯效控制",
                "rw": "RW",
                "data_type": "dynamic_effect",
                "conversion": "raw_value",
                "commands": {
                    "set_effect": {"type": CMD_TYPE_SET_RAW_ON, "val": "effect_value"},
                    "stop_effect": {"type": CMD_TYPE_SET_RAW_OFF, "val": 0},
                },
                "support_effects": True,
                "available_effects": "DYN_EFFECT_LIST",
            },
        },
    },
    # Spot类型设备
    "SL_SPOT": {
        "light": {
            "RGB": {
                "description": "超级碗RGB灯光控制",
                "rw": "RW",
                "data_type": "rgb_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_rgb": {"type": CMD_TYPE_SET_RAW_ON, "val": "rgb_color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "rgb_color_value",
                    },
                },
                "color_format": "RGB",
                "support_color": True,
            },
        },
    },
    "MSL_IRCTL": {
        "light": {
            "RGBW": {
                "description": "超级碗RGBW颜色控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_rgbw": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "val": "rgbw_color_value",
                    },
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "rgbw_color_value",
                    },
                },
                "color_format": "RGBW",
                "support_color": True,
            },
            "DYN": {
                "description": "超级碗动态灯效控制",
                "rw": "RW",
                "data_type": "dynamic_effect",
                "conversion": "raw_value",
                "commands": {
                    "set_effect": {"type": CMD_TYPE_SET_RAW_ON, "val": "effect_value"},
                    "stop_effect": {"type": CMD_TYPE_SET_RAW_OFF, "val": 0},
                },
                "support_effects": True,
                "available_effects": "DYN_EFFECT_LIST",
            },
        },
    },
    "OD_WE_IRCTL": {
        "light": {
            "RGB": {
                "description": "海外版超级碗RGB灯光控制",
                "rw": "RW",
                "data_type": "rgb_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_rgb": {"type": CMD_TYPE_SET_RAW_ON, "val": "rgb_color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "rgb_color_value",
                    },
                },
                "color_format": "RGB",
                "support_color": True,
            },
        },
    },
    # 量子灯
    "OD_WE_QUAN": {
        "light": {
            "P1": {
                "description": "量子灯亮度控制",
                "rw": "RW",
                "data_type": "brightness",
                "conversion": "val_to_brightness",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                        "val": "brightness_value",
                    },
                },
                "brightness_range": [0, 100],
                "support_brightness": True,
            },
            "P2": {
                "description": "量子灯颜色和特效控制",
                "rw": "RW",
                "data_type": "quantum_effect",
                "conversion": "raw_value",
                "commands": {
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "set_effect": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "val": "quantum_effect_value",
                    },
                    "stop_effect": {"type": CMD_TYPE_SET_RAW_OFF, "val": 0},
                },
                "support_color": True,
                "support_effects": True,
                "available_effects": "ALL_EFFECT_LIST",
                "special_features": ["audio_sync", "second_generation_effects"],
            },
        },
    },
    # ================= 灯光+传感器设备 (Light + Sensor Devices) =================
    # 具有灯光控制和环境传感器功能的设备
    # 调光壁灯 - 灯光 + PIR + 光照传感器
    "SL_LI_GD1": {
        "light": {
            "P1": {
                "description": "调光壁灯亮度控制",
                "rw": "RW",
                "data_type": "brightness",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_brightness": {"type": CMD_TYPE_SET_VAL, "val": "brightness"},
                },
                "range": [0, 255],
            },
        },
        "binary_sensor": {
            "P2": {
                "description": "PIR移动检测",
                "rw": "R",
                "data_type": "motion_detection",
                "conversion": "type_bit_0",
                "commands": {},
                "device_class": BinarySensorDeviceClass.MOTION,
            },
        },
        "sensor": {
            "P3": {
                "description": "环境光照监测",
                "rw": "R",
                "data_type": "illuminance",
                "conversion": "raw_value",
                "commands": {},
                "device_class": SensorDeviceClass.ILLUMINANCE,
                "unit": LIGHT_LUX,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    # 花园地灯 - 灯光 + 充电指示 + 传感器
    "SL_LI_UG1": {
        "light": {
            "P1": {
                "description": "花园地灯RGBW颜色控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {"type": CMD_TYPE_SET_RAW_OFF, "val": "color_value"},
                },
                "color_format": "RGBW",
            },
        },
        "sensor": {
            "P2": {
                "description": "环境光照监测",
                "rw": "R",
                "data_type": "illuminance", 
                "conversion": "raw_value",
                "commands": {},
                "device_class": SensorDeviceClass.ILLUMINANCE,
                "unit": LIGHT_LUX,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "P4": {
                "description": "电量监测",
                "rw": "R",
                "data_type": "battery_level",
                "conversion": "v_or_val",
                "commands": {},
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "range": [0, 100],
            },
        },
        "binary_sensor": {
            "P3": {
                "description": "太阳能充电状态",
                "rw": "R",
                "data_type": "charging_status",
                "conversion": "type_bit_0",
                "commands": {},
                "device_class": BinarySensorDeviceClass.BATTERY_CHARGING,
            },
        },
    },
    # ================= 覆盖物设备 (Cover Devices) =================
    # 纯覆盖物控制设备，主要或仅具有窗帘/门控制功能
    # 窗帘电机控制器
    "SL_DOOYA": {
        "cover": {
            "P1": {
                "description": "杜亚窗帘位置状态",
                "rw": "R",
                "data_type": "position_percentage",
                "conversion": "v_or_val",
                "commands": {},
                "range": [0, 100],
            },
            "P2": {
                "description": "杜亚窗帘控制命令",
                "rw": "RW",
                "data_type": "cover_control",
                "conversion": "raw_value",
                "commands": {
                    "open": {"type": CMD_TYPE_SET_VAL, "val": 100},
                    "close": {"type": CMD_TYPE_SET_VAL, "val": 0},
                    "set_position": {"type": CMD_TYPE_SET_VAL, "val": "position_value"},
                },
                "range": [0, 100],
            },
        },
    },
    "SL_P_V2": {
        "cover": {
            "P2": {
                "description": "智界窗帘打开控制",
                "rw": "RW",
                "data_type": "cover_open",
                "conversion": "type_bit_0",
                "commands": {
                    "open": {"type": CMD_TYPE_ON, "val": 1},
                },
            },
            "P3": {
                "description": "智界窗帘关闭控制",
                "rw": "RW",
                "data_type": "cover_close",
                "conversion": "type_bit_0",
                "commands": {
                    "close": {"type": CMD_TYPE_ON, "val": 1},
                },
            },
            "P4": {
                "description": "智界窗帘停止控制",
                "rw": "RW",
                "data_type": "cover_stop",
                "conversion": "type_bit_0",
                "commands": {
                    "stop": {"type": CMD_TYPE_ON, "val": 1},
                },
            },
        },
        "sensor": {
            "P8": {
                "description": "智界窗帘电压监测",
                "device_class": "voltage",
                "unit_of_measurement": "V",
                "state_class": "measurement",
                "rw": "R",
                "data_type": "voltage",
                "conversion": "v_or_val",
                "commands": {},
            },
        },
    },
    "SL_CN_FE": {
        "cover": {
            "P1": {
                "description": "三键窗帘打开控制",
                "rw": "RW",
                "data_type": "cover_open",
                "conversion": "type_bit_0",
                "commands": {
                    "open": {"type": CMD_TYPE_ON, "val": 1},
                },
            },
            "P2": {
                "description": "三键窗帘关闭控制",
                "rw": "RW",
                "data_type": "cover_close",
                "conversion": "type_bit_0",
                "commands": {
                    "close": {"type": CMD_TYPE_ON, "val": 1},
                },
            },
            "P3": {
                "description": "三键窗帘停止控制",
                "rw": "RW",
                "data_type": "cover_stop",
                "conversion": "type_bit_0",
                "commands": {
                    "stop": {"type": CMD_TYPE_ON, "val": 1},
                },
            },
        },
    },
    # ================= 基础环境传感器 (Basic Environmental Sensors) =================
    "SL_SC_THL": {
        "sensor": {
            "T": {
                "description": "当前环境温度",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",  # 只读
                "data_type": "temperature_10x",  # val值是温度值*10
                "conversion": "val_divide_10",  # 转换类型
                "precision": 1,  # 小数位数
            },
            "H": {
                "description": "当前环境湿度",
                "device_class": SensorDeviceClass.HUMIDITY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "humidity_10x",
                "conversion": "val_divide_10",
                "precision": 1,
            },
            "Z": {
                "description": "当前环境光照",
                "device_class": SensorDeviceClass.ILLUMINANCE,
                "unit": LIGHT_LUX,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "raw_lux",
                "conversion": "v_or_val",  # 优先使用v，不存在则使用val
            },
            "V": {
                "description": "电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "voltage_to_percentage",
                "conversion": "voltage_to_battery",
                "range": [0, 100],
            },
        },
    },
    "SL_SC_BE": {
        "sensor": {
            "T": {
                "description": "当前环境温度",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "temperature_10x",
                "conversion": "val_divide_10",
                "precision": 1,
            },
            "H": {
                "description": "当前环境湿度",
                "device_class": SensorDeviceClass.HUMIDITY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "humidity_10x",
                "conversion": "val_divide_10",
                "precision": 1,
            },
            "Z": {
                "description": "当前环境光照",
                "device_class": SensorDeviceClass.ILLUMINANCE,
                "unit": LIGHT_LUX,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "raw_lux",
                "conversion": "v_or_val",
            },
            "V": {
                "description": "电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "voltage_to_percentage",
                "conversion": "voltage_to_battery",
                "range": [0, 100],
            },
        },
    },
    "SL_SC_B1": {
        "sensor": {
            "T": {
                "description": "当前环境温度",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "temperature_10x",
                "conversion": "val_divide_10",
                "precision": 1,
            },
            "H": {
                "description": "当前环境湿度",
                "device_class": SensorDeviceClass.HUMIDITY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "humidity_10x",
                "conversion": "val_divide_10",
                "precision": 1,
            },
            "Z": {
                "description": "当前环境光照",
                "device_class": SensorDeviceClass.ILLUMINANCE,
                "unit": LIGHT_LUX,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "raw_lux",
                "conversion": "v_or_val",
            },
            "V": {
                "description": "电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "voltage_to_percentage",
                "conversion": "voltage_to_battery",
                "range": [0, 100],
            },
        },
    },
    # ================= 空气质量传感器 (Air Quality Sensors) =================
    "SL_SC_CA": {
        "sensor": {
            "P1": {
                "description": "当前环境温度",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "temperature_10x",
                "conversion": "val_divide_10",
                "precision": 1,
            },
            "P2": {
                "description": "当前环境湿度",
                "device_class": SensorDeviceClass.HUMIDITY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "humidity_10x",
                "conversion": "val_divide_10",
                "precision": 1,
            },
            "P3": {
                "description": "CO2浓度",
                "device_class": SensorDeviceClass.CO2,
                "unit": CONCENTRATION_PARTS_PER_MILLION,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "co2_ppm",
                "conversion": "v_or_val",
                "thresholds": {
                    "excellent": {"max": 500, "label": "优"},
                    "good": {"max": 700, "label": "良"},
                    "moderate": {"max": 1000, "label": "中"},
                    "poor": {"min": 1000, "label": "差"},
                },
            },
            "P4": {
                "description": "电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "voltage_to_percentage",
                "conversion": "voltage_to_battery",
                "range": [0, 100],
            },
            "P5": {
                "description": "USB供电状态",
                "device_class": SensorDeviceClass.VOLTAGE,
                "unit": UnitOfElectricPotential.VOLT,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "usb_power_voltage",
                "conversion": "raw_value",
                "threshold": 430,  # >430表示USB供电工作
            },
        },
    },
    "SL_SC_CQ": {
        "sensor": {
            "P1": {
                "description": "当前环境温度",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "temperature_10x",
                "conversion": "val_divide_10",
                "precision": 1,
            },
            "P2": {
                "description": "当前环境湿度",
                "device_class": SensorDeviceClass.HUMIDITY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "humidity_10x",
                "conversion": "val_divide_10",
                "precision": 1,
            },
            "P3": {
                "description": "CO2浓度",
                "device_class": SensorDeviceClass.CO2,
                "unit": CONCENTRATION_PARTS_PER_MILLION,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "co2_ppm",
                "conversion": "v_or_val",
                "thresholds": {
                    "excellent": {"max": 500, "label": "优"},
                    "good": {"max": 700, "label": "良"},
                    "moderate": {"max": 1000, "label": "中"},
                    "poor": {"min": 1000, "label": "差"},
                },
            },
            "P4": {
                "description": "TVOC浓度",
                "device_class": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
                "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "tvoc_1000x",  # val值是实际值*1000
                "conversion": "val_divide_1000",
                "precision": 3,
                "thresholds": {
                    "excellent": {"max": 0.34, "label": "优"},
                    "good": {"max": 0.68, "label": "良"},
                    "moderate": {"max": 1.02, "label": "中"},
                    "poor": {"min": 1.02, "label": "差"},
                },
            },
            "P5": {
                "description": "电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "voltage_to_percentage",
                "conversion": "voltage_to_battery",
                "range": [0, 100],
            },
            "P6": {
                "description": "USB供电状态",
                "device_class": SensorDeviceClass.VOLTAGE,
                "unit": UnitOfElectricPotential.VOLT,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "usb_power_voltage",
                "conversion": "raw_value",
                "threshold": 430,  # >430表示USB供电工作
            },
        },
    },
    "SL_SC_CH": {
        "sensor": {
            "P1": {
                "description": "甲醛浓度",
                "device_class": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
                "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "formaldehyde_1000x",  # val值是实际值*1000
                "conversion": "val_divide_1000",
                "precision": 3,
                "safe_range": [0, 86],  # 安全区间 0-86 ug/m³
                "alarm_thresholds": {
                    "no_alarm": 5000,
                    "medium_sensitivity": 100,
                    "high_sensitivity": 80,
                },
            },
        },
        "binary_sensor": {
            "P1": {
                "description": "甲醛浓度告警状态",
                "rw": "R",
                "data_type": "formaldehyde_alarm",
                "conversion": "type_bit_0",  # type&1==1表示超过告警门限
            },
        },
        "switch": {
            "P2": {
                "description": "甲醛告警门限设置",
                "rw": "RW",
                "data_type": "threshold_setting",
                "conversion": "raw_value",
                "commands": {
                    "set_threshold": {
                        "type": CMD_TYPE_SET_VAL,
                        "val": "threshold_value",
                    },
                },
                "presets": {
                    "no_alarm": 5000,
                    "medium": 100,
                    "high": 80,
                },
            },
            "P3": {
                "description": "警报音控制",
                "rw": "RW",
                "data_type": "alarm_sound",
                "conversion": "type_bit_0",  # type&1==1表示报警音正在响
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
    },
    # ================= 计量插座系列 (Power Meter Outlets) =================
    "SL_OE_3C": {
        "switch": {
            "P1": {
                "description": "插座开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P4": {
                "description": "功率门限控制",
                "rw": "RW",
                "data_type": "power_threshold",
                "commands": {
                    "enable": {"type": CMD_TYPE_ON, "val": 1},
                    "disable": {"type": CMD_TYPE_OFF, "val": 0},
                    "enable_with_threshold": {
                        "type": CMD_TYPE_SET_VAL,
                        "val": "threshold_watts",
                    },
                    "disable_with_threshold": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "val": "threshold_watts",
                    },
                },
                "range": [0, 3000],  # 0-3000W
                "unit": UnitOfPower.WATT,
            },
        },
        "sensor": {
            "P2": {
                "description": "累计用电量",
                "device_class": SensorDeviceClass.ENERGY,
                "unit": UnitOfEnergy.KILO_WATT_HOUR,
                "state_class": SensorStateClass.TOTAL_INCREASING,
                "rw": "R",
                "data_type": "ieee754_float",
                "conversion": "ieee754_float",
                "precision": 5,
            },
            "P3": {
                "description": "当前功率",
                "device_class": SensorDeviceClass.POWER,
                "unit": UnitOfPower.WATT,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "ieee754_float",
                "conversion": "ieee754_float",
                "precision": 2,
            },
            "P4": {
                "description": "功率门限值",
                "device_class": SensorDeviceClass.POWER,
                "unit": UnitOfPower.WATT,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "integer",
                "conversion": "raw_value",
            },
        },
    },
    "SL_OE_DE": {
        "switch": {
            "P1": {
                "description": "插座开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P4": {
                "description": "功率门限控制",
                "rw": "RW",
                "data_type": "power_threshold",
                "commands": {
                    "enable": {"type": CMD_TYPE_ON, "val": 1},
                    "disable": {"type": CMD_TYPE_OFF, "val": 0},
                    "enable_with_threshold": {
                        "type": CMD_TYPE_SET_VAL,
                        "val": "threshold_watts",
                    },
                    "disable_with_threshold": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "val": "threshold_watts",
                    },
                },
                "range": [0, 3000],
                "unit": UnitOfPower.WATT,
            },
        },
        "sensor": {
            "P2": {
                "description": "累计用电量",
                "device_class": SensorDeviceClass.ENERGY,
                "unit": UnitOfEnergy.KILO_WATT_HOUR,
                "state_class": SensorStateClass.TOTAL_INCREASING,
                "rw": "R",
                "data_type": "ieee754_float",
                "conversion": "ieee754_float",
                "precision": 5,
            },
            "P3": {
                "description": "当前功率",
                "device_class": SensorDeviceClass.POWER,
                "unit": UnitOfPower.WATT,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "ieee754_float",
                "conversion": "ieee754_float",
                "precision": 2,
            },
            "P4": {
                "description": "功率门限值",
                "device_class": SensorDeviceClass.POWER,
                "unit": UnitOfPower.WATT,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "integer",
                "conversion": "raw_value",
            },
        },
    },
    "SL_OE_W": {
        "switch": {
            "P1": {
                "description": "插座开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P4": {
                "description": "功率门限控制",
                "rw": "RW",
                "data_type": "power_threshold",
                "commands": {
                    "enable": {"type": CMD_TYPE_ON, "val": 1},
                    "disable": {"type": CMD_TYPE_OFF, "val": 0},
                    "enable_with_threshold": {
                        "type": CMD_TYPE_SET_VAL,
                        "val": "threshold_watts",
                    },
                    "disable_with_threshold": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "val": "threshold_watts",
                    },
                },
                "range": [0, 3000],
                "unit": UnitOfPower.WATT,
            },
        },
        "sensor": {
            "P2": {
                "description": "累计用电量",
                "device_class": SensorDeviceClass.ENERGY,
                "unit": UnitOfEnergy.KILO_WATT_HOUR,
                "state_class": SensorStateClass.TOTAL_INCREASING,
                "rw": "R",
                "data_type": "ieee754_float",
                "conversion": "ieee754_float",
                "precision": 5,
            },
            "P3": {
                "description": "当前功率",
                "device_class": SensorDeviceClass.POWER,
                "unit": UnitOfPower.WATT,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "ieee754_float",
                "conversion": "ieee754_float",
                "precision": 2,
            },
            "P4": {
                "description": "功率门限值",
                "device_class": SensorDeviceClass.POWER,
                "unit": UnitOfPower.WATT,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "integer",
                "conversion": "raw_value",
            },
        },
    },
    # 第三方传感器和计量器
    "ELIQ_EM": {
        "sensor": {
            "EPA": {
                "description": "ELIQ电量监测",
                "rw": "R",
                "data_type": "ieee754_float",
                "conversion": "ieee754_float",
                "commands": {},
                "device_class": SensorDeviceClass.ENERGY,
                "unit": UnitOfEnergy.KILO_WATT_HOUR,
                "state_class": SensorStateClass.TOTAL_INCREASING,
                "precision": 5,
            },
        },
    },
    "V_DLT645_P": {
        "sensor": {
            "EE": {
                "description": "DLT累计电量监测",
                "rw": "R",
                "data_type": "energy_total",
                "conversion": "raw_value",
                "commands": {},
                "device_class": SensorDeviceClass.ENERGY,
                "unit": UnitOfEnergy.KILO_WATT_HOUR,
                "state_class": SensorStateClass.TOTAL_INCREASING,
            },
            "EP": {
                "description": "DLT当前功率监测",
                "rw": "R",
                "data_type": "power_current",
                "conversion": "raw_value",
                "commands": {},
                "device_class": SensorDeviceClass.POWER,
                "unit": UnitOfPower.WATT,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    "V_485_P": {
        "sensor": {
            "io": [
                "P1",
                "T",
                "H",
                "PM",
                "PMx",
                "CO2PPM",
                "TVOC",
                "COPPM",
                "CH20PPM",
                "O2VOL",
                "NH3PPM",
                "H2SPPM",
                "PHM",
                "SMOKE",
                "EP",
                "EPF*",  # 支持EPF和EPFx格式
                "EF*",  # 支持EF和EFx格式
                "EI*",  # 支持EI和EIx格式
                "EV*",  # 支持EV和EVx格式
                "EE*",  # 支持EE和EEx格式
            ],
            "description": "485多功能传感器",
        },
        "switch": {"io": ["L*", "O"], "description": "485开关控制，支持Lx格式"},
    },
    "V_HG_XX": {
        "sensor": {
            "P1": {
                "description": "极速虚拟设备传感器",
                "rw": "R",
                "data_type": "raw_value",
                "conversion": "raw_value",
                "commands": {},
            },
        },
    },
    # ================= 二元传感器设备 (Binary Sensor Devices) =================
    # 纯二元传感器或二元传感器为主要功能的设备
    # 门磁传感器
    "SL_SC_G": {
        "binary_sensor": {
            "G": {
                "description": "门窗开关状态",
                "device_class": "door",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
        "sensor": {
            "V": {
                "description": "电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "voltage_to_percentage",
                "conversion": "voltage_to_battery",
                "range": [0, 100],
                "commands": {},
            },
        },
    },
    "SL_SC_GS": {
        "binary_sensor": {
            "P1": {
                "description": "门窗磁感应检测",
                "device_class": "door",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
            "AXS": {
                "description": "震动检测",
                "device_class": "vibration",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
        "sensor": {
            "V": {
                "description": "电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "voltage_to_percentage",
                "conversion": "voltage_to_battery",
                "range": [0, 100],
                "commands": {},
            },
        },
    },
    "SL_SC_BG": {
        "binary_sensor": {
            "G": {
                "description": "门窗状态检测",
                "device_class": "door",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
            "AXS": {
                "description": "震动检测",
                "device_class": "vibration",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
        "button": {
            "B": {
                "description": "按键",
                "rw": "R",
                "data_type": "button_press",
                "conversion": "button_event",
                "commands": {},
            },
        },
        "sensor": {
            "V": {
                "description": "电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "voltage_to_percentage",
                "conversion": "voltage_to_battery",
                "range": [0, 100],
                "commands": {},
            },
        },
    },
    # 运动传感器
    "SL_SC_MHW": {
        "binary_sensor": {
            "M": {
                "description": "人体红外检测",
                "device_class": "motion",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
        "sensor": {
            "V": {
                "description": "电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "voltage_to_percentage",
                "conversion": "voltage_to_battery",
                "range": [0, 100],
                "commands": {},
            },
        },
    },
    "SL_SC_BM": {
        "binary_sensor": {
            "M": {
                "description": "CUBE动态感应器移动检测",
                "device_class": "motion",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
        "sensor": {
            "V": {
                "description": "电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "voltage_to_percentage",
                "conversion": "voltage_to_battery",
                "range": [0, 100],
                "commands": {},
            },
        },
    },
    "SL_SC_CM": {
        "binary_sensor": {
            "P1": {
                "description": "PIR人体红外检测",
                "device_class": "motion",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
        "sensor": {
            "P3": {
                "description": "主电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "voltage_to_percentage",
                "conversion": "voltage_to_battery",
                "range": [0, 100],
                "commands": {},
            },
            "P4": {
                "description": "USB供电检测",
                "device_class": SensorDeviceClass.POWER,
                "unit": UnitOfPower.WATT,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "power_supply_state",
                "conversion": "v_or_val",
                "commands": {},
            },
        },
    },
    "SL_BP_MZ": {
        "binary_sensor": {
            "P1": {
                "description": "PIR人体红外移动检测",
                "device_class": "motion",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
        "sensor": {
            "P2": {
                "description": "环境光照监测",
                "device_class": SensorDeviceClass.ILLUMINANCE,
                "unit": LIGHT_LUX,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "raw_lux",
                "conversion": "v_or_val",
                "commands": {},
            },
            "P3": {
                "description": "电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "voltage_to_percentage",
                "conversion": "voltage_to_battery",
                "range": [0, 100],
                "commands": {},
            },
        },
    },
    # 水浸传感器
    "SL_SC_WA": {
        "binary_sensor": {
            "WA": {
                "description": "水浸状态检测",
                "device_class": "moisture",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
        "sensor": {
            "V": {
                "description": "电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "voltage_to_percentage",
                "conversion": "voltage_to_battery",
                "range": [0, 100],
                "commands": {},
            },
        },
    },
    # 烟雾传感器
    "SL_P_A": {
        "binary_sensor": {
            "P1": {
                "description": "烟雾检测",
                "device_class": "smoke",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
        "sensor": {
            "P2": {
                "description": "电压监测",
                "device_class": SensorDeviceClass.VOLTAGE,
                "unit": UnitOfElectricPotential.VOLT,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "voltage_measurement",
                "conversion": "v_or_val",
                "commands": {},
            },
        },
    },
    # 雷达传感器
    "SL_P_RM": {
        "binary_sensor": {
            "P1": {
                "description": "雷达人体检测",
                "device_class": "motion",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
        "sensor": {
            "P2": {
                "description": "雷达参数配置监测",
                "rw": "R",
                "data_type": "radar_config_params",
                "conversion": "v_or_val",
                "commands": {},
            },
        },
    },
    # 云防系列传感器
    "SL_DF_GG": {
        "binary_sensor": {
            "A": {
                "description": "云防门窗检测",
                "device_class": "door",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
            "A2": {
                "description": "云防门窗检测2",
                "device_class": "door",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
            "TR": {
                "description": "防拆检测",
                "device_class": "tamper",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
        "sensor": {
            "T": {
                "description": "云防环境温度",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "temperature_10x",
                "conversion": "val_divide_10",
                "precision": 1,
                "commands": {},
            },
            "V": {
                "description": "电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "voltage_to_percentage",
                "conversion": "voltage_to_battery",
                "range": [0, 100],
                "commands": {},
            },
        },
    },
    "SL_DF_MM": {
        "binary_sensor": {
            "M": {
                "description": "移动检测",
                "device_class": "motion",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
            "TR": {
                "description": "防拆状态",
                "device_class": "tamper",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
        "sensor": {
            "T": {
                "description": "环境温度",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "temperature_10x",
                "conversion": "val_divide_10",
                "precision": 1,
                "commands": {},
            },
            "V": {
                "description": "电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "voltage_to_percentage",
                "conversion": "voltage_to_battery",
                "range": [0, 100],
                "commands": {},
            },
        },
    },
    "SL_DF_BB": {
        "button": {
            "eB1": {
                "description": "遥控器按键1",
                "rw": "R",
                "data_type": "button_press",
                "conversion": "button_event",
                "commands": {},
            },
            "eB2": {
                "description": "遥控器按键2",
                "rw": "R",
                "data_type": "button_press",
                "conversion": "button_event",
                "commands": {},
            },
            "eB3": {
                "description": "遥控器按键3",
                "rw": "R",
                "data_type": "button_press",
                "conversion": "button_event",
                "commands": {},
            },
            "eB4": {
                "description": "遥控器按键4",
                "rw": "R",
                "data_type": "button_press",
                "conversion": "button_event",
                "commands": {},
            },
        },
        "sensor": {
            "V": {
                "description": "电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "voltage_to_percentage",
                "conversion": "voltage_to_battery",
                "range": [0, 100],
                "commands": {},
            },
        },
    },
    # 摄像头设备（仅传感器功能）
    "cam": {
        "binary_sensor": {
            "M": {
                "description": "摄像头移动检测",
                "device_class": "motion",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
    },
    "LSCAM:LSCAMV1": {
        "binary_sensor": {
            "M": {
                "description": "摄像头移动检测",
                "device_class": "motion",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
        "sensor": {
            "V": {
                "description": "电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "voltage_to_percentage",
                "conversion": "voltage_to_battery",
                "range": [0, 100],
                "commands": {},
            },
            "CFST": {
                "description": "摄像头状态监测",
                "rw": "R",
                "data_type": "camera_status",
                "conversion": "v_or_val",
                "commands": {},
            },
        },
    },
    "LSCAM:LSICAMEZ1": {
        "binary_sensor": {
            "M": {
                "description": "户外摄像头移动检测",
                "device_class": "motion",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
    },
    "LSCAM:LSICAMEZ2": {
        "binary_sensor": {
            "M": {
                "description": "户外摄像头移动检测",
                "device_class": "motion",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
    },
    "LSCAM:LSICAMGOS1": {
        "binary_sensor": {
            "M": {
                "description": "高清摄像头移动检测",
                "device_class": "motion",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
    },
    "LSCAM:LSLKCAMV1": {
        "binary_sensor": {
            "M": {
                "description": "视频门锁摄像头移动检测",
                "device_class": "motion",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
    },
    # 第三方设备
    "V_DUNJIA_P": {
        "binary_sensor": {
            "P1": {
                "description": "人脸识别门锁状态",
                "device_class": "lock",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
    },
    # ================= 多功能传感器设备 (Multi-sensor Devices) =================
    # 具有多种传感器类型的复合设备
    # 燃气传感器 - 传感器 + 二元传感器 + 开关
    "SL_SC_CP": {
        "binary_sensor": {
            "P1": {
                "description": "燃气浓度告警检测",
                "device_class": "gas",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
        "sensor": {
            "P1": {
                "description": "燃气浓度数值",
                "device_class": "gas",
                "unit": "ppm",
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "gas_concentration",
                "conversion": "v_or_val",
                "commands": {},
            },
            "P2": {
                "description": "告警门限监测",
                "unit": "ppm",
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "alarm_threshold",
                "conversion": "v_or_val",
                "commands": {},
            },
        },
        "switch": {
            "P3": {
                "description": "燃气报警音控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
    },
    # 噪音传感器 - 传感器 + 二元传感器 + 开关
    "SL_SC_CN": {
        "binary_sensor": {
            "P1": {
                "description": "噪音告警检测",
                "device_class": "sound",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
        "sensor": {
            "P1": {
                "description": "噪音分贝数值",
                "unit": "dB",
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "noise_level",
                "conversion": "v_or_val",
                "commands": {},
            },
            "P2": {
                "description": "噪音告警门限",
                "unit": "dB",
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "alarm_threshold",
                "conversion": "v_or_val",
                "commands": {},
            },
            "P4": {
                "description": "噪音校正值",
                "unit": "dB",
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "calibration_value",
                "conversion": "v_or_val",
                "commands": {},
            },
        },
        "switch": {
            "P3": {
                "description": "噪音报警设置控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
    },
    # 语音小Q
    "SL_SC_CV": {
        "sensor": {
            "T": {
                "description": "语音设备环境温度",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "temperature_10x",
                "conversion": "val_divide_10",
                "precision": 1,
                "commands": {},
            },
            "H": {
                "description": "语音设备环境湿度",
                "device_class": SensorDeviceClass.HUMIDITY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "humidity_10x",
                "conversion": "val_divide_10",
                "precision": 1,
                "commands": {},
            },
        },
    },
    # ================= 智能锁设备 (Lock Devices) =================
    # 智能门锁设备，具有二元传感器和传感器功能
    "SL_LK_LS": {
        "binary_sensor": {
            "ALM": {
                "description": "门锁告警状态",
                "rw": "R",
                "data_type": "lock_alarm",
                "conversion": "lock_alarm_bits",
                "commands": {},
                "device_class": BinarySensorDeviceClass.SAFETY,
            },
        },
        "sensor": {
            "BAT": {
                "description": "门锁电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "battery_percentage",
                "conversion": "v_or_val",
                "commands": {},
                "range": [0, 100],
            },
            "EVTLO": {
                "description": "实时开锁状态和解锁日志",
                "rw": "R",
                "data_type": "unlock_realtime_status",
                "conversion": "unlock_status_with_log",
                "commands": {},
                "state_mapping": {
                    "type&1==1": "opened",
                    "type&1==0": "closed"
                },
                "val_format": {
                    "bit0_11": "用户编号",
                    "bit12_15": "开锁方式",
                    "bit16_27": "用户编号2(双开)",
                    "bit28_31": "开锁方式2(双开)",
                },
                "unlock_methods": UNLOCK_METHOD
            },
            "EVTOP": {
                "description": "操作记录历史数据",
                "rw": "R",
                "data_type": "operation_history",
                "conversion": "operation_history_decoder",
                "commands": {},
                "data_format": "[1Byte记录类型][2Byte用户ID][1Byte用户标志]",
            },
            "HISLK": {
                "description": "最近一次开锁记录",
                "rw": "R", 
                "data_type": "last_unlock_record",
                "conversion": "raw_value",
                "commands": {},
            },
        },
    },
    "SL_LK_GTM": {
        "binary_sensor": {
            "ALM": {
                "description": "门锁告警状态",
                "rw": "R",
                "data_type": "lock_alarm",
                "conversion": "lock_alarm_bits",
                "commands": {},
                "device_class": BinarySensorDeviceClass.SAFETY,
                "alarm_bits": {
                    "bit0": "错误报警(密码/指纹/卡片超过10次)",
                    "bit1": "劫持报警(防劫持密码/指纹)",
                    "bit2": "防撬报警(锁被撬开)",
                    "bit3": "机械钥匙报警",
                    "bit4": "低电压报警(电池电量不足)",
                    "bit5": "异动告警",
                    "bit6": "门铃",
                    "bit7": "火警",
                    "bit8": "入侵告警",
                    "bit11": "恢复出厂告警"
                }
            },
        },
        "sensor": {
            "BAT": {
                "description": "门锁电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "battery_level",
                "conversion": "raw_value",
                "commands": {},
                "range": [0, 100],
            },
            "EVTLO": {
                "description": "实时开锁状态和日志",
                "rw": "R",
                "data_type": "unlock_realtime_log",
                "conversion": "unlock_log_decoder",
                "commands": {},
                "state_mapping": {
                    "type&1==1": "opened",
                    "type&1==0": "closed"
                },
                "val_format": {
                    "bit0_11": "用户编号",
                    "bit12_15": "开锁方式",
                    "bit16_27": "用户编号2(双开)",
                    "bit28_31": "开锁方式2(双开)",
                },
                "unlock_methods": UNLOCK_METHOD
            },
            "EVTOP": {
                "description": "操作记录历史",
                "rw": "R", 
                "data_type": "operation_history",
                "conversion": "operation_history_decoder",
                "commands": {},
                "data_format": "[1Byte记录类型][2Byte用户ID][1Byte用户标志]",
                "user_flags": {
                    "bit01=11": "管理员",
                    "bit01=01": "普通用户",
                    "bit01=00": "已删除用户"
                }
            },
            "HISLK": {
                "description": "最近一次开锁信息",
                "rw": "R",
                "data_type": "last_unlock_info", 
                "conversion": "last_unlock_decoder",
                "commands": {},
                "state_mapping": {
                    "type&1==1": "opened",
                    "type&1==0": "closed"
                },
                "val_format": {
                    "bit0_11": "用户编号",
                    "bit12_15": "开锁方式",
                    "bit16_27": "用户编号2",
                    "bit28_31": "开锁方式2",
                }
            },
        },
    },
    "SL_LK_AG": {
        "binary_sensor": {
            "ALM": {
                "description": "门锁告警状态",
                "rw": "R",
                "data_type": "lock_alarm",
                "conversion": "lock_alarm_bits",
                "commands": {},
                "device_class": BinarySensorDeviceClass.SAFETY,
                "alarm_bits": {
                    "bit0": "错误报警(密码/指纹/卡片超过10次)",
                    "bit1": "劫持报警(防劫持密码/指纹)",
                    "bit2": "防撬报警(锁被撬开)",
                    "bit3": "机械钥匙报警",
                    "bit4": "低电压报警(电池电量不足)",
                    "bit5": "异动告警",
                    "bit6": "门铃",
                    "bit7": "火警",
                    "bit8": "入侵告警",
                    "bit11": "恢复出厂告警"
                }
            },
        },
        "sensor": {
            "BAT": {
                "description": "门锁电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "battery_level",
                "conversion": "raw_value",
                "commands": {},
                "range": [0, 100],
            },
            "EVTLO": {
                "description": "实时开锁状态和日志",
                "rw": "R",
                "data_type": "unlock_realtime_log",
                "conversion": "unlock_log_decoder",
                "commands": {},
                "state_mapping": {
                    "type&1==1": "opened",
                    "type&1==0": "closed"
                },
                "val_format": {
                    "bit0_11": "用户编号",
                    "bit12_15": "开锁方式",
                    "bit16_27": "用户编号2(双开)",
                    "bit28_31": "开锁方式2(双开)",
                },
                "unlock_methods": UNLOCK_METHOD
            },
            "EVTOP": {
                "description": "操作记录历史",
                "rw": "R", 
                "data_type": "operation_history",
                "conversion": "operation_history_decoder",
                "commands": {},
                "data_format": "[1Byte记录类型][2Byte用户ID][1Byte用户标志]",
                "user_flags": {
                    "bit01=11": "管理员",
                    "bit01=01": "普通用户",
                    "bit01=00": "已删除用户"
                }
            },
            "HISLK": {
                "description": "最近一次开锁信息",
                "rw": "R",
                "data_type": "last_unlock_info", 
                "conversion": "last_unlock_decoder",
                "commands": {},
                "state_mapping": {
                    "type&1==1": "opened",
                    "type&1==0": "closed"
                },
                "val_format": {
                    "bit0_11": "用户编号",
                    "bit12_15": "开锁方式",
                    "bit16_27": "用户编号2",
                    "bit28_31": "开锁方式2",
                }
            },
        },
    },
    "SL_LK_SG": {
        "binary_sensor": {
            "ALM": {
                "description": "门锁告警状态",
                "rw": "R",
                "data_type": "lock_alarm",
                "conversion": "lock_alarm_bits",
                "commands": {},
                "device_class": BinarySensorDeviceClass.SAFETY,
                "alarm_bits": {
                    "bit0": "错误报警(密码/指纹/卡片超过10次)",
                    "bit1": "劫持报警(防劫持密码/指纹)",
                    "bit2": "防撬报警(锁被撬开)",
                    "bit3": "机械钥匙报警",
                    "bit4": "低电压报警(电池电量不足)",
                    "bit5": "异动告警",
                    "bit6": "门铃",
                    "bit7": "火警",
                    "bit8": "入侵告警",
                    "bit11": "恢复出厂告警"
                }
            },
        },
        "sensor": {
            "BAT": {
                "description": "门锁电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "battery_level",
                "conversion": "raw_value",
                "commands": {},
                "range": [0, 100],
            },
            "EVTLO": {
                "description": "实时开锁状态和日志",
                "rw": "R",
                "data_type": "unlock_realtime_log",
                "conversion": "unlock_log_decoder",
                "commands": {},
                "state_mapping": {
                    "type&1==1": "opened",
                    "type&1==0": "closed"
                },
                "val_format": {
                    "bit0_11": "用户编号",
                    "bit12_15": "开锁方式",
                    "bit16_27": "用户编号2(双开)",
                    "bit28_31": "开锁方式2(双开)",
                },
                "unlock_methods": UNLOCK_METHOD
            },
            "EVTOP": {
                "description": "操作记录历史",
                "rw": "R", 
                "data_type": "operation_history",
                "conversion": "operation_history_decoder",
                "commands": {},
                "data_format": "[1Byte记录类型][2Byte用户ID][1Byte用户标志]",
                "user_flags": {
                    "bit01=11": "管理员",
                    "bit01=01": "普通用户",
                    "bit01=00": "已删除用户"
                }
            },
            "HISLK": {
                "description": "最近一次开锁信息",
                "rw": "R",
                "data_type": "last_unlock_info", 
                "conversion": "last_unlock_decoder",
                "commands": {},
                "state_mapping": {
                    "type&1==1": "opened",
                    "type&1==0": "closed"
                },
                "val_format": {
                    "bit0_11": "用户编号",
                    "bit12_15": "开锁方式",
                    "bit16_27": "用户编号2",
                    "bit28_31": "开锁方式2",
                }
            },
        },
    },
    "SL_LK_YL": {
        "binary_sensor": {
            "ALM": {
                "description": "门锁告警状态",
                "rw": "R",
                "data_type": "lock_alarm",
                "conversion": "lock_alarm_bits",
                "commands": {},
                "device_class": BinarySensorDeviceClass.SAFETY,
                "alarm_bits": {
                    "bit0": "错误报警(密码/指纹/卡片超过10次)",
                    "bit1": "劫持报警(防劫持密码/指纹)",
                    "bit2": "防撬报警(锁被撬开)",
                    "bit3": "机械钥匙报警",
                    "bit4": "低电压报警(电池电量不足)",
                    "bit5": "异动告警",
                    "bit6": "门铃",
                    "bit7": "火警",
                    "bit8": "入侵告警",
                    "bit11": "恢复出厂告警"
                }
            },
        },
        "sensor": {
            "BAT": {
                "description": "门锁电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "battery_level",
                "conversion": "raw_value",
                "commands": {},
                "range": [0, 100],
            },
            "EVTLO": {
                "description": "实时开锁状态和日志",
                "rw": "R",
                "data_type": "unlock_realtime_log",
                "conversion": "unlock_log_decoder",
                "commands": {},
                "state_mapping": {
                    "type&1==1": "opened",
                    "type&1==0": "closed"
                },
                "val_format": {
                    "bit0_11": "用户编号",
                    "bit12_15": "开锁方式",
                    "bit16_27": "用户编号2(双开)",
                    "bit28_31": "开锁方式2(双开)",
                },
                "unlock_methods": UNLOCK_METHOD
            },
            "EVTOP": {
                "description": "操作记录历史",
                "rw": "R", 
                "data_type": "operation_history",
                "conversion": "operation_history_decoder",
                "commands": {},
                "data_format": "[1Byte记录类型][2Byte用户ID][1Byte用户标志]",
                "user_flags": {
                    "bit01=11": "管理员",
                    "bit01=01": "普通用户",
                    "bit01=00": "已删除用户"
                }
            },
            "HISLK": {
                "description": "最近一次开锁信息",
                "rw": "R",
                "data_type": "last_unlock_info", 
                "conversion": "last_unlock_decoder",
                "commands": {},
                "state_mapping": {
                    "type&1==1": "opened",
                    "type&1==0": "closed"
                },
                "val_format": {
                    "bit0_11": "用户编号",
                    "bit12_15": "开锁方式",
                    "bit16_27": "用户编号2",
                    "bit28_31": "开锁方式2",
                }
            },
        },
    },
    "SL_P_BDLK": {
        "binary_sensor": {
            "ALM": {
                "description": "门锁报警状态检测",
                "rw": "R",
                "data_type": "alarm_status",
                "conversion": "type_bit_0",
                "commands": {},
                "device_class": BinarySensorDeviceClass.SAFETY,
            },
        },
        "sensor": {
            "EVTLO": {
                "description": "实时开锁状态和日志",
                "rw": "R",
                "data_type": "unlock_realtime_log",
                "conversion": "unlock_log_decoder",
                "commands": {},
                "state_mapping": {
                    "type&1==1": "opened",
                    "type&1==0": "closed"
                },
                "val_format": {
                    "bit0_11": "用户编号",
                    "bit12_15": "开锁方式",
                    "bit16_27": "用户编号2",
                    "bit28_31": "开锁方式2",
                },
                "unlock_methods": UNLOCK_METHOD
            },
            "BAT": {
                "description": "门锁电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "battery_percentage",
                "conversion": "v_or_val",
                "commands": {},
                "range": [0, 100],
            },
            "EVTOP": {
                "description": "开锁操作记录",
                "rw": "R",
                "data_type": "unlock_method",
                "conversion": "unlock_method_mapping",
                "commands": {},
                "states": "UNLOCK_METHOD",
            },
            "HISLK": {
                "description": "历史开锁记录",
                "rw": "R",
                "data_type": "unlock_history",
                "conversion": "raw_value",
                "commands": {},
            },
        },
    },
    "OD_JIUWANLI_LOCK1": {
        "binary_sensor": {
            "ALM": {
                "description": "门锁报警状态检测",
                "rw": "R",
                "data_type": "alarm_status",
                "conversion": "type_bit_0",
                "commands": {},
                "device_class": BinarySensorDeviceClass.SAFETY,
            },
        },
        "sensor": {
            "EVTLO": {
                "description": "实时开锁状态和日志",
                "rw": "R",
                "data_type": "unlock_realtime_log",
                "conversion": "unlock_log_decoder",
                "commands": {},
                "state_mapping": {
                    "type&1==1": "opened",
                    "type&1==0": "closed"
                },
                "val_format": {
                    "bit0_11": "用户编号",
                    "bit12_15": "开锁方式",
                    "bit16_27": "用户编号2",
                    "bit28_31": "开锁方式2",
                },
                "unlock_methods": UNLOCK_METHOD
            },
            "BAT": {
                "description": "门锁电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "battery_percentage",
                "conversion": "v_or_val",
                "commands": {},
                "range": [0, 100],
            },
            "EVTOP": {
                "description": "开锁操作记录",
                "rw": "R",
                "data_type": "unlock_method",
                "conversion": "unlock_method_mapping",
                "commands": {},
                "states": "UNLOCK_METHOD",
            },
            "HISLK": {
                "description": "历史开锁记录",
                "rw": "R",
                "data_type": "unlock_history",
                "conversion": "raw_value",
                "commands": {},
            },
        },
    },
    "SL_LK_SWIFTE": {
        "binary_sensor": {
            "ALM": {
                "description": "门锁报警状态检测",
                "rw": "R",
                "data_type": "alarm_status",
                "conversion": "type_bit_0",
                "commands": {},
                "device_class": BinarySensorDeviceClass.SAFETY,
            },
        },
        "sensor": {
            "EVTLO": {
                "description": "实时开锁状态和日志",
                "rw": "R",
                "data_type": "unlock_realtime_log",
                "conversion": "unlock_log_decoder",
                "commands": {},
                "state_mapping": {
                    "type&1==1": "opened",
                    "type&1==0": "closed"
                },
                "val_format": {
                    "bit0_11": "用户编号",
                    "bit12_15": "开锁方式",
                    "bit16_27": "用户编号2",
                    "bit28_31": "开锁方式2",
                },
                "unlock_methods": UNLOCK_METHOD
            },
            "BAT": {
                "description": "门锁电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "battery_percentage",
                "conversion": "v_or_val",
                "commands": {},
                "range": [0, 100],
            },
            "EVTOP": {
                "description": "开锁操作记录",
                "rw": "R",
                "data_type": "unlock_method",
                "conversion": "unlock_method_mapping",
                "commands": {},
                "states": "UNLOCK_METHOD",
            },
            "HISLK": {
                "description": "历史开锁记录",
                "rw": "R",
                "data_type": "unlock_history",
                "conversion": "raw_value",
                "commands": {},
            },
        },
    },
    "SL_LK_TY": {
        "binary_sensor": {
            "ALM": {
                "description": "C100门锁报警状态检测",
                "rw": "R",
                "data_type": "alarm_status",
                "conversion": "type_bit_0",
                "commands": {},
                "device_class": BinarySensorDeviceClass.SAFETY,
            },
        },
        "sensor": {
            "BAT": {
                "description": "C100门锁电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "battery_percentage",
                "conversion": "v_or_val",
                "commands": {},
                "range": [0, 100],
            },
            "EVTLO": {
                "description": "C100实时开锁状态",
                "rw": "R",
                "data_type": "unlock_realtime_status",
                "conversion": "unlock_status_with_log",
                "commands": {},
                "state_mapping": {
                    "type&1==1": "opened",
                    "type&1==0": "closed"
                },
            },
            "EVTBEL": {
                "description": "门铃消息状态",
                "rw": "R",
                "data_type": "doorbell_message_status",
                "conversion": "doorbell_message_decoder",
                "commands": {},
                "state_mapping": {
                    "type&1=1": "有门铃消息"
                }
            },
            "HISLK": {
                "description": "C100门锁历史开锁记录",
                "rw": "R",
                "data_type": "unlock_history",
                "conversion": "raw_value",
                "commands": {},
            },
        },
    },
    # ================= 温控设备 (Climate Devices) =================
    # 纯温控设备或温控为主要功能的设备
    # 空调控制面板
    "SL_UACCB": {
        "climate": {
            "P1": {
                "description": "空调开关控制",
                "rw": "RW",
                "data_type": "hvac_mode",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P2": {
                "description": "空调模式设置",
                "rw": "RW",
                "data_type": "hvac_mode",
                "conversion": "raw_value",
                "commands": {
                    "set_mode": {"type": 0xCE, "val": "mode_value"},
                },
            },
            "P3": {
                "description": "风速设置",
                "rw": "RW",
                "data_type": "fan_speed",
                "conversion": "raw_value",
                "commands": {
                    "set_fan_mode": {"type": 0xCF, "val": "fan_speed_value"},
                },
            },
            "P4": {
                "description": "目标温度设置",
                "rw": "RW",
                "data_type": "temperature_10x",
                "conversion": "temperature_to_10x",
                "commands": {
                    "set_temperature": {"type": 0x88, "val": "temperature*10"},
                },
            },
        },
        "sensor": {
            "P6": {
                "description": "当前温度监测",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "temperature_10x",
                "conversion": "val_divide_10",
                "precision": 1,
                "commands": {},
            },
        },
    },
    "V_AIR_P": {
        "climate": {
            "O": {
                "description": "空调开关控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "MODE": {
                "description": "空调模式设置",
                "rw": "RW",
                "data_type": "hvac_mode",
                "conversion": "raw_value",
                "commands": {
                    "set_mode": {"type": 0xCE, "val": "mode_value"},
                },
            },
            "F": {
                "description": "风速设置",
                "rw": "RW",
                "data_type": "fan_speed",
                "conversion": "raw_value",
                "commands": {
                    "set_fan_mode": {"type": 0xCF, "val": "fan_speed_value"},
                },
            },
            "tT": {
                "description": "目标温度设置",
                "rw": "RW",
                "data_type": "temperature_10x",
                "conversion": "temperature_to_10x",
                "commands": {
                    "set_temperature": {"type": 0x88, "val": "temperature*10"},
                },
            },
        },
        "sensor": {
            "T": {
                "description": "环境温度传感器",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "temperature_10x",
                "conversion": "val_divide_10",
                "precision": 1,
                "commands": {},
            },
        },
    },
    # ================= 温控设备 (Climate Devices) =================
    "SL_CP_DN": {
        "climate": {
            "P1": {
                "description": "地暖系统配置",
                "rw": "RW",
                "data_type": "complex_config",
                "control_type": "system_config",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_config": {"type": "current", "val": "config_value"},
                },
                "config_bits": {
                    "system_state": {"bit": 0, "description": "系统开关状态"},
                    "mode": {"bits": [31], "description": "模式: 0手动/1自动"},
                    "temp_limit": {"bits": [24, 19], "description": "限温值=val+40"},
                    "control_mode": {"bits": [18, 17], "description": "控温模式"},
                    "time_mode": {"bits": [16, 15], "description": "时段模式"},
                    "external_sensor_diff": {
                        "bits": [14, 11],
                        "description": "外置探头差=(val-10)/2",
                    },
                    "internal_sensor_diff": {
                        "bits": [10, 8],
                        "description": "内置探头差=(val-10)/2",
                    },
                    "temp_correction": {
                        "bits": [7, 3],
                        "description": "温度修正=val/2+5",
                    },
                    "power_restore": {"bit": 1, "description": "停电后来电状态"},
                    "backlight": {"bit": 0, "description": "背光设置"},
                },
            },
            "P3": {
                "description": "目标温度设置",
                "rw": "RW",
                "data_type": "temperature_10x",
                "conversion": "val_divide_10",
                "control_type": "target_temperature",
                "commands": {
                    "set_temperature": {"type": "current", "val": "temperature*10"},
                },
                "precision": 1,
                "range": [5, 35],  # 5°C - 35°C
                "unit": UnitOfTemperature.CELSIUS,
            },
        },
        "switch": {
            "P2": {
                "description": "继电器开关控制",
                "rw": "RW",
                "data_type": "relay_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
        "sensor": {
            "P4": {
                "description": "室内温度",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "temperature_10x",
                "conversion": "val_divide_10",
                "precision": 1,
            },
            "P5": {
                "description": "底版温度",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "temperature_10x",
                "conversion": "val_divide_10",
                "precision": 1,
            },
        },
    },
    "SL_DN": {
        "climate": {
            "P1": {
                "description": "地暖系统开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P2": {
                "description": "地暖模式设置",
                "rw": "RW",
                "data_type": "hvac_mode",
                "conversion": "raw_value",
                "commands": {
                    "set_mode": {"type": 0xCE, "val": "mode_value"},
                },
            },
            "P8": {
                "description": "目标温度设置",
                "rw": "RW",
                "data_type": "temperature_10x",
                "conversion": "temperature_to_10x",
                "commands": {
                    "set_temperature": {"type": 0x88, "val": "temperature*10"},
                },
            },
        },
        "binary_sensor": {
            "P3": {
                "description": "地暖阀门状态",
                "device_class": "opening",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
        "sensor": {
            "P4": {
                "description": "室内温度",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "temperature_10x",
                "conversion": "val_divide_10",
                "precision": 1,
                "commands": {},
            },
            "P9": {
                "description": "底版温度监测",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "temperature_10x",
                "conversion": "val_divide_10",
                "precision": 1,
                "commands": {},
            },
        },
    },
    # 风机盘管和新风系统
    "SL_CP_AIR": {
        "climate": {
            "P1": {
                "description": "风机盘管开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P2": {
                "description": "阀门控制",
                "rw": "RW",
                "data_type": "valve_control",
                "conversion": "raw_value",
                "commands": {
                    "set_valve": {"type": 0x89, "val": "valve_position"},
                },
            },
            "P3": {
                "description": "风速设置",
                "rw": "RW",
                "data_type": "fan_speed",
                "conversion": "raw_value",
                "commands": {
                    "set_fan_mode": {"type": 0xCF, "val": "fan_speed_value"},
                },
            },
            "P4": {
                "description": "目标温度设置",
                "rw": "RW",
                "data_type": "temperature_10x",
                "conversion": "temperature_to_10x",
                "commands": {
                    "set_temperature": {"type": 0x88, "val": "temperature*10"},
                },
            },
        },
        "sensor": {
            "P5": {
                "description": "室内温度监测",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "temperature_10x",
                "conversion": "val_divide_10",
                "precision": 1,
                "commands": {},
            },
        },
        "binary_sensor": {
            "P2": {
                "description": "阀门状态检测",
                "device_class": "opening",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
    },
    "SL_CP_VL": {
        "climate": {
            "P1": {
                "description": "温控阀门开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P3": {
                "description": "目标温度设置",
                "rw": "RW",
                "data_type": "temperature_10x",
                "conversion": "temperature_to_10x",
                "commands": {
                    "set_temperature": {"type": 0x88, "val": "temperature*10"},
                },
            },
        },
        "binary_sensor": {
            "P5": {
                "description": "告警状态检测",
                "device_class": "problem",
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
        "sensor": {
            "P4": {
                "description": "当前温度",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "temperature_10x",
                "conversion": "val_divide_10",
                "precision": 1,
                "commands": {},
            },
            "P6": {
                "description": "电池电量监测",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "voltage_to_percentage",
                "conversion": "voltage_to_battery",
                "range": [0, 100],
                "commands": {},
            },
        },
    },
    "SL_FCU": {
        "climate": {
            "io": ["P1", "P6", "P7", "P8", "P9", "P10"],
            "description": "风机盘管控制",
        },
        "binary_sensor": {"io": ["P2", "P3"], "description": "阀门开关检测"},
        "sensor": {"io": ["P4"], "description": "温度监测"},
    },
    "SL_TR_ACIPM": {
        "climate": {
            "io": ["P1", "P2", "P3"],
            "description": "新风系统配置、风速控制和VOC阈值设置",
        },
        "sensor": {
            "io": ["P4", "P5", "P6"],
            "description": "VOC浓度、PM2.5浓度和温度传感器",
        },
    },
    # 第三方新风系统
    "V_FRESH_P": {
        "climate": {"io": ["O", "MODE", "F1", "F2"], "description": "新风系统控制"},
        "sensor": {"io": "T", "description": "环境温度监测"},
    },
    "V_SZJSXR_P": {
        "climate": {"io": ["O", "MODE"], "description": "新风系统控制"},
        "sensor": {"io": "T", "description": "环境温度监测"},
    },
    "V_T8600_P": {
        "climate": {"io": ["O", "MODE"], "description": "温控器控制"},
        "sensor": {"io": "T", "description": "环境温度监测"},
    },
    # ================= 报警设备 (Alarm Devices) =================
    # 报警器和警报设备
    # 智能报警器
    "SL_ALM": {
        "switch": {
            "P1": {
                "description": "报警器播放控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
            "P2": {
                "description": "报警器音量控制",
                "rw": "RW",
                "data_type": "volume_level",
                "conversion": "raw_value",
                "commands": {
                    "set_volume": {"type": CMD_TYPE_SET_VAL, "val": "volume_level"},
                },
                "range": [0, 100],
            },
        },
    },
    "LSSSMINIV1": {
        "switch": {
            "P1": {
                "description": "多功能报警器控制",
                "rw": "RW",
                "data_type": "binary_switch", 
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
            },
        },
    },
    # 云防室内警铃
    "SL_DF_SR": {
        "siren": {
            "SR": {
                "description": "云防室内警铃声音播放",
                "rw": "RW",
                "data_type": "siren_control",
                "conversion": "raw_value",
                "commands": {
                    "turn_on": {"type": CMD_TYPE_ON, "val": 1},
                    "turn_off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_volume": {"type": CMD_TYPE_SET_VAL, "val": "volume_level"},
                },
                "volume_range": [0, 10],
                "tone_options": ["alarm", "warning", "emergency", "doorbell"],
            },
        },
        "binary_sensor": {
            "TR": {
                "description": "防拆状态检测",
                "device_class": BinarySensorDeviceClass.TAMPER,
                "rw": "R",
                "data_type": "binary_state",
                "conversion": "type_bit_0",
                "commands": {},
            },
        },
        "sensor": {
            "T": {
                "description": "环境温度监测",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "temperature_10x",
                "conversion": "val_divide_10",
                "precision": 1,
                "commands": {},
            },
            "V": {
                "description": "电池电量",
                "device_class": SensorDeviceClass.BATTERY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "rw": "R",
                "data_type": "voltage_to_percentage",
                "conversion": "voltage_to_battery",
                "range": [0, 100],
                "commands": {},
            },
        },
        "switch": {
            "P1": {
                "description": "报警设置控制",
                "rw": "RW",
                "data_type": "alarm_config",
                "conversion": "raw_value",
                "commands": {
                    "enable": {"type": CMD_TYPE_ON, "val": 1},
                    "disable": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_alarm_mode": {"type": CMD_TYPE_SET_CONFIG, "val": "alarm_mode"},
                },
                "alarm_modes": ["silent", "low", "medium", "high"],
            },
        },
    },
    # 空气净化器 - 开关 + 传感器
    "OD_MFRESH_M8088": {
        "switch": {
            "O": {
                "description": "空气净化器开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                },
                "states": {
                    "type&1==1": "on",
                    "type&1==0": "off"
                }
            },
            "RM": {
                "description": "运行模式控制",
                "rw": "RW", 
                "data_type": "fan_mode",
                "conversion": "raw_value",
                "commands": {
                    "set_mode": {"type": CMD_TYPE_SET_VAL, "val": "mode_value"},
                },
                "states": {
                    0: "auto",
                    1: "fan_1", 
                    2: "fan_2",
                    3: "fan_3",
                    4: "fan_max",
                    5: "sleep"
                }
            },
        },
        "sensor": {
            "T": {
                "description": "当前环境温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_or_val",
                "commands": {},
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
                "precision": 1,
            },
            "H": {
                "description": "当前环境湿度", 
                "rw": "R",
                "data_type": "humidity",
                "conversion": "v_or_val", 
                "commands": {},
                "device_class": SensorDeviceClass.HUMIDITY,
                "unit": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "precision": 1,
            },
            "PM": {
                "description": "PM2.5浓度",
                "rw": "R",
                "data_type": "pm25_concentration",
                "conversion": "v_or_val",
                "commands": {},
                "device_class": SensorDeviceClass.PM25,
                "unit": CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "FL": {
                "description": "滤芯寿命", 
                "rw": "R",
                "data_type": "filter_life_hours",
                "conversion": "raw_value",
                "commands": {},
                "unit": "h",
                "state_class": SensorStateClass.MEASUREMENT,
                "range": [0, 4800],
            },
            "UV": {
                "description": "紫外线指数",
                "rw": "R",
                "data_type": "uv_index", 
                "conversion": "raw_value",
                "commands": {},
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    # ================= 红外设备 (Remote/IR Devices) =================
    # 红外控制设备
    "SL_P_IR": {
        "remote": {
            "P1": {
                "description": "红外控制功能",
                "rw": "W",
                "data_type": "ir_command",
                "conversion": "raw_value",
                "commands": {
                    "send_command": {"type": CMD_TYPE_SET_RAW_ON, "val": "ir_code"},
                    "learn_command": {"type": CMD_TYPE_SET_CONFIG, "val": "learn_mode"},
                },
                "supported_devices": ["tv", "ac", "fan", "light", "projector"],
                "protocol": "infrared",
            },
        },
    },
    # ================= 第三方设备 (Third-party Devices) =================
    # 通过控制器接入的第三方设备
    "SL_DF_KP": {
        "binary_sensor": {"io": "P1", "description": "云防Keypad按键检测"},
    },
    # ================= 版本设备 (Versioned Devices) =================
    # 这些设备在VERSIONED_DEVICE_TYPES中定义，需要独立的IO口映射
    "SL_SW_DM1": {
        "versioned": True,
        "V1": {  # 动态调光开关版本 - 具有传感器和智能控制功能
            "light": {
                "P1": {
                    "description": "调光开关主光源亮度控制",
                    "rw": "RW",
                    "data_type": "brightness",
                    "conversion": "val_to_brightness",
                    "commands": {
                        "on": {"type": CMD_TYPE_ON, "val": 1},
                        "off": {"type": CMD_TYPE_OFF, "val": 0},
                        "set_brightness": {
                            "type": CMD_TYPE_SET_VAL,
                            "val": "brightness_value",
                        },
                    },
                    "brightness_range": [0, 100],
                    "support_brightness": True,
                },
                "P2": {
                    "description": "指示灯亮度控制",
                    "rw": "RW",
                    "data_type": "brightness",
                    "conversion": "val_to_brightness",
                    "commands": {
                        "on": {"type": CMD_TYPE_ON, "val": 1},
                        "off": {"type": CMD_TYPE_OFF, "val": 0},
                        "set_brightness": {
                            "type": CMD_TYPE_SET_VAL,
                            "val": "brightness_value",
                        },
                    },
                    "brightness_range": [0, 100],
                    "support_brightness": True,
                },
            },
            "binary_sensor": {
                "P3": {
                    "description": "PIR移动检测",
                    "rw": "R",
                    "data_type": "motion_sensor",
                    "conversion": "type_bit_0",
                    "device_class": "motion",
                    "commands": {},
                },
            },
            "sensor": {
                "P4": {
                    "description": "环境光照强度",
                    "device_class": "illuminance",
                    "unit_of_measurement": "lux",
                    "state_class": "measurement",
                    "rw": "R",
                    "data_type": "illuminance",
                    "conversion": "v_or_val",
                    "commands": {},
                },
                "P5": {
                    "description": "调光参数设置",
                    "rw": "RW",
                    "data_type": "config_value",
                    "conversion": "raw_value",
                    "commands": {
                        "set_config": {
                            "type": CMD_TYPE_SET_CONFIG,
                            "val": "config_value",
                        },
                    },
                },
                "P6": {
                    "description": "动态控制设置",
                    "rw": "RW",
                    "data_type": "dynamic_config",
                    "conversion": "raw_value",
                    "commands": {
                        "set_dynamic": {
                            "type": CMD_TYPE_SET_CONFIG,
                            "val": "dynamic_value",
                        },
                    },
                },
            },
        },
        "V2": {  # 星玉调光开关(可控硅)版本 - 基础调光功能
            "light": {
                "P1": {
                    "description": "星玉调光开关主光源亮度控制",
                    "rw": "RW",
                    "data_type": "brightness",
                    "conversion": "val_to_brightness",
                    "commands": {
                        "on": {"type": CMD_TYPE_ON, "val": 1},
                        "off": {"type": CMD_TYPE_OFF, "val": 0},
                        "set_brightness": {
                            "type": CMD_TYPE_SET_VAL,
                            "val": "brightness_value",
                        },
                    },
                    "brightness_range": [0, 100],
                    "support_brightness": True,
                    "dimmer_type": "triac",  # 可控硅调光
                },
                "P2": {
                    "description": "指示灯亮度控制",
                    "rw": "RW",
                    "data_type": "brightness",
                    "conversion": "val_to_brightness",
                    "commands": {
                        "on": {"type": CMD_TYPE_ON, "val": 1},
                        "off": {"type": CMD_TYPE_OFF, "val": 0},
                        "set_brightness": {
                            "type": CMD_TYPE_SET_VAL,
                            "val": "brightness_value",
                        },
                    },
                    "brightness_range": [0, 100],
                    "support_brightness": True,
                },
            },
            # V2版本不包含传感器功能
        },
    },
    "SL_SC_BB": {
        "versioned": True,
        "V1": {  # 基础随心按键版本 - 简单按键检测
            "binary_sensor": {
                "B": {
                    "description": "按键状态检测",
                    "rw": "R",
                    "data_type": "simple_button",
                    "conversion": "binary_state",
                    "commands": {},
                    "states": {
                        0: "未按下",
                        1: "按下",
                    },
                },
            },
            "sensor": {
                "V": {
                    "description": "电池电量",
                    "device_class": SensorDeviceClass.BATTERY,
                    "unit": PERCENTAGE,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "rw": "R",
                    "data_type": "voltage_to_percentage",
                    "conversion": "voltage_to_battery",
                    "commands": {},
                    "range": [0, 100],
                    "voltage_range": [2000, 4200],  # 2V-4.2V
                },
            },
        },
        "V2": {  # 高级随心按键版本 - 支持复杂手势识别
            "binary_sensor": {
                "B": {
                    "description": "按键事件检测",
                    "rw": "R",
                    "data_type": "advanced_button_event",
                    "conversion": "raw_value",
                    "commands": {},
                    "events": {
                        1: "单击事件",
                        2: "双击事件",
                        255: "长按事件",
                        0: "无事件",
                    },
                    "attributes": {
                        "event_type": "get_button_event_type",
                        "last_event": "get_last_event_time",
                    },
                },
            },
            "sensor": {
                "V": {
                    "description": "电池电量",
                    "device_class": SensorDeviceClass.BATTERY,
                    "unit": PERCENTAGE,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "rw": "R",
                    "data_type": "voltage_to_percentage",
                    "conversion": "voltage_to_battery",
                    "commands": {},
                    "range": [0, 100],
                    "voltage_range": [2000, 4200],
                },
            },
        },
    },
    "SL_LK_DJ": {
        "versioned": True,
        "V1": {  # 智能门锁C210版本
            "binary_sensor": {
                "EVTLO": {
                    "description": "门锁锁定状态检测",
                    "rw": "R",
                    "data_type": "lock_status",
                    "conversion": "type_bit_0",
                    "commands": {},
                    "device_class": "lock",
                },
                "ALM": {
                    "description": "门锁报警状态检测",
                    "rw": "R",
                    "data_type": "alarm_status",
                    "conversion": "type_bit_0",
                    "commands": {},
                    "device_class": BinarySensorDeviceClass.SAFETY,
                },
            },
            "sensor": {
                "BAT": {
                    "description": "门锁电池电量",
                    "device_class": SensorDeviceClass.BATTERY,
                    "unit": PERCENTAGE,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "rw": "R",
                    "data_type": "battery_percentage",
                    "conversion": "v_or_val",
                    "commands": {},
                    "range": [0, 100],
                },
                "EVTOP": {
                    "description": "开锁操作记录",
                    "rw": "R",
                    "data_type": "unlock_method",
                    "conversion": "unlock_method_mapping",
                    "commands": {},
                    "states": "UNLOCK_METHOD",
                },
                "HISLK": {
                    "description": "历史开锁记录",
                    "rw": "R",
                    "data_type": "unlock_history",
                    "conversion": "raw_value",
                    "commands": {},
                },
            },
        },
        "V2": {  # 智能门锁C200版本 - 包含门铃功能
            "binary_sensor": {
                "EVTLO": {
                    "description": "门锁锁定状态检测",
                    "rw": "R",
                    "data_type": "lock_status",
                    "conversion": "type_bit_0",
                    "commands": {},
                    "device_class": "lock",
                },
                "ALM": {
                    "description": "门锁报警状态检测",
                    "rw": "R",
                    "data_type": "alarm_status",
                    "conversion": "type_bit_0",
                    "commands": {},
                    "device_class": BinarySensorDeviceClass.SAFETY,
                },
                "EVTBEL": {
                    "description": "门铃按键检测",
                    "rw": "R",
                    "data_type": "doorbell_press",
                    "conversion": "type_bit_0",
                    "commands": {},
                    "device_class": "sound",
                },
            },
            "sensor": {
                "BAT": {
                    "description": "门锁电池电量",
                    "device_class": SensorDeviceClass.BATTERY,
                    "unit": PERCENTAGE,
                    "state_class": SensorStateClass.MEASUREMENT,
                    "rw": "R",
                    "data_type": "battery_percentage",
                    "conversion": "v_or_val",
                    "commands": {},
                    "range": [0, 100],
                },
                "EVTOP": {
                    "description": "开锁操作记录",
                    "rw": "R",
                    "data_type": "unlock_method",
                    "conversion": "unlock_method_mapping",
                    "commands": {},
                    "states": "UNLOCK_METHOD",
                },
                "HISLK": {
                    "description": "历史开锁记录",
                    "rw": "R",
                    "data_type": "unlock_history",
                    "conversion": "raw_value",
                    "commands": {},
                },
            },
        },
    },
    "SL_LI_WW": {
        "versioned": True,
        "V1": {  # 智能灯泡(冷暖白)版本
            "light": {
                "P1": {
                    "description": "智能灯泡亮度控制",
                    "rw": "RW",
                    "data_type": "brightness",
                    "conversion": "val_to_brightness",
                    "commands": {
                        "on": {"type": CMD_TYPE_ON, "val": 1},
                        "off": {"type": CMD_TYPE_OFF, "val": 0},
                        "set_brightness": {
                            "type": CMD_TYPE_SET_VAL,
                            "val": "brightness_value",
                        },
                    },
                    "brightness_range": [0, 100],
                    "support_brightness": True,
                },
                "P2": {
                    "description": "冷暖白色温控制",
                    "rw": "RW",
                    "data_type": "color_temp",
                    "conversion": "val_to_color_temp",
                    "commands": {
                        "set_color_temp": {
                            "type": CMD_TYPE_SET_VAL,
                            "val": "color_temp_value",
                        },
                    },
                    "color_temp_range": [2700, 6500],
                    "support_color_temp": True,
                },
            },
        },
        "V2": {  # 调光调色智控器(0-10V)版本
            "light": {
                "P1": {
                    "description": "0-10V调光器亮度控制",
                    "rw": "RW",
                    "data_type": "brightness",
                    "conversion": "val_to_brightness",
                    "commands": {
                        "on": {"type": CMD_TYPE_ON, "val": 1},
                        "off": {"type": CMD_TYPE_OFF, "val": 0},
                        "set_brightness": {
                            "type": CMD_TYPE_SET_VAL,
                            "val": "brightness_value",
                        },
                    },
                    "brightness_range": [0, 100],
                    "support_brightness": True,
                    "dimmer_type": "0_10v",  # 0-10V调光协议
                },
                "P2": {
                    "description": "0-10V调光器色温控制",
                    "rw": "RW",
                    "data_type": "color_temp",
                    "conversion": "val_to_color_temp",
                    "commands": {
                        "set_color_temp": {
                            "type": CMD_TYPE_SET_VAL,
                            "val": "color_temp_value",
                        },
                    },
                    "color_temp_range": [2700, 6500],
                    "support_color_temp": True,
                },
            },
        },
    },
    # ================= 窗帘设备 (Cover Devices) =================
    # 缺失映射的窗帘控制设备
    "SL_SW_WIN": {
        "cover": {
            "OP": {
                "description": "窗帘打开控制",
                "rw": "RW",
                "data_type": "cover_open",
                "conversion": "type_bit_0",
                "commands": {
                    "open": {"type": CMD_TYPE_ON, "val": 1},
                },
            },
            "CL": {
                "description": "窗帘关闭控制",
                "rw": "RW",
                "data_type": "cover_close",
                "conversion": "type_bit_0",
                "commands": {
                    "close": {"type": CMD_TYPE_ON, "val": 1},
                },
            },
            "ST": {
                "description": "窗帘停止控制",
                "rw": "RW",
                "data_type": "cover_stop",
                "conversion": "type_bit_0",
                "commands": {
                    "stop": {"type": CMD_TYPE_ON, "val": 1},
                },
            },
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "brightness",
                "conversion": "val_to_brightness",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                        "val": "brightness_value",
                    },
                },
                "brightness_range": [0, 100],
                "support_brightness": True,
            },
            "bright": {
                "description": "开状态时指示灯亮度控制",
                "rw": "RW",
                "data_type": "brightness",
                "conversion": "val_to_brightness",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                        "val": "brightness_value",
                    },
                },
                "brightness_range": [0, 100],
                "support_brightness": True,
            },
        },
    },
    "SL_CN_IF": {
        "cover": {
            "P1": {
                "description": "流光窗帘打开控制",
                "rw": "RW",
                "data_type": "cover_open",
                "conversion": "type_bit_0",
                "commands": {
                    "open": {"type": CMD_TYPE_ON, "val": 1},
                },
            },
            "P2": {
                "description": "流光窗帘关闭控制",
                "rw": "RW",
                "data_type": "cover_close",
                "conversion": "type_bit_0",
                "commands": {
                    "close": {"type": CMD_TYPE_ON, "val": 1},
                },
            },
            "P3": {
                "description": "流光窗帘停止控制",
                "rw": "RW",
                "data_type": "cover_stop",
                "conversion": "type_bit_0",
                "commands": {
                    "stop": {"type": CMD_TYPE_ON, "val": 1},
                },
            },
        },
        "light": {
            "P4": {
                "description": "流光窗帘指示灯P4颜色控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "support_color": True,
            },
            "P5": {
                "description": "流光窗帘指示灯P5颜色控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "support_color": True,
            },
            "P6": {
                "description": "流光窗帘指示灯P6颜色控制",
                "rw": "RW",
                "data_type": "rgbw_color",
                "conversion": "raw_value",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
                    "set_color": {"type": CMD_TYPE_SET_RAW_ON, "val": "color_value"},
                    "turn_off_with_color": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "val": "color_value",
                    },
                },
                "color_format": "RGBW",
                "support_color": True,
            },
        },
    },
    "SL_ETDOOR": {
        "cover": {
            "P2": {
                "description": "车库门状态",
                "rw": "R",
                "data_type": "door_status",
                "conversion": "type_bit_0",
                "commands": {},
                "states": {
                    0: "closed",
                    1: "open",
                },
            },
            "P3": {
                "description": "车库门控制",
                "rw": "RW",
                "data_type": "door_control",
                "conversion": "type_bit_0",
                "commands": {
                    "toggle": {"type": CMD_TYPE_ON, "val": 1},
                },
            },
        },
        "light": {
            "P1": {
                "description": "车库门灯光控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1},
                    "off": {"type": CMD_TYPE_OFF, "val": 0},
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
    # 按钮开关版本区分 - 基于不同的按键检测能力
    "SL_SC_BB": {
        # SL_SC_BB_V1基础随心按键 - 简单按键检测
        # IO口: V(电量 R) B(按键状态 R: 0=未按下 1=按下)
        "V1": "cube_clicker_basic",
        # SL_SC_BB_V2高级随心按键 - 支持复杂手势识别
        # IO口: P1(按键状态 R: 1=单击 2=双击 255=长按) P2(电量 R)
        "V2": "cube_clicker_advanced",
    },
    # 智能门锁版本区分 - 不同型号不同功能
    "SL_LK_DJ": {
        # 智能门锁C210
        "V1": "smart_lock_c210",
        # 智能门锁C200
        "V2": "smart_lock_c200",
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
    Platform.REMOTE,
    # Platform.CAMERA, # 摄像头平台当前未实现
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
