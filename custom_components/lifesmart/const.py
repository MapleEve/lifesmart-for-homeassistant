"""由 @MapleEve 实现的 LifeSmart 集成常量模块。

此文件定义了所有与 LifeSmart 平台交互所需的硬编码常量、设备类型代码、API命令码、以及用于在 Home Assistant 和 LifeSmart 之间转换数据的映射。

维护此文件的准确性和清晰度对于整个集成的稳定和可扩展性至关重要。
"""

from homeassistant.components.climate.const import (
    HVACMode,
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
)
from homeassistant.const import Platform

# ================= 核心常量 (Core Constants) =================
DOMAIN = "lifesmart"
MANUFACTURER = "LifeSmart"

# --- JSON 数据键名 ---
# 这些常量用于从LifeSmart API响应的JSON数据中安全地提取值。
HUB_ID_KEY = "agt"  # 智慧中心 (网关) 的唯一标识符
DEVICE_ID_KEY = "me"  # 设备的唯一标识符
DEVICE_TYPE_KEY = "devtype"  # 设备的类型代码，用于区分不同种类的设备
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

# ================= 其他设备类型 =================
# --- 超级碗 (SPOT) ---
SPOT_TYPES = {
    "MSL_IRCTL",  # 超级碗（基础版,蓝牙版）
    "OD_WE_IRCTL",  # 超级碗（闪联版）
    "SL_SPOT",  # 超级碗（CoSS版）
    "SL_P_IR",  # 红外模块 / 超级碗（Mini版）
    "SL_P_IR_V2",  # 红外模块 / 超级碗（Mini版 V2）
}

# --- 通用控制器 ---
GENERIC_CONTROLLER_TYPES = {
    "SL_P",  # 通用控制器
    "SL_JEMA",  # 通用控制器
}
# --- 摄像头 ---
CAMERA_TYPES = {
    "LSCAM:LSICAMGOS1",  # 摄像头
    "LSCAM:LSICAMEZ2",  # 摄像头
}

# ================= 开关系列 (Switch Series) =================
# 涵盖所有单火、零火、调光、场景、窗帘等开关面板
# --- 带电压的开关系列 ---
VOLTAGE_SWITCH_TYPES = {
    # --- 恒星/⾠星/极星系列 (Nature/Star) ---
    "SL_SW_ND1",  # 恒星/辰星/极星开关 (单键)
    "SL_MC_ND1",  # 恒星/辰星/极星开关伴侣 (单键)
    "SL_SW_ND2",  # 恒星/辰星/极星开关 (双键)
    "SL_MC_ND2",  # 恒星/辰星/极星开关伴侣 (双键)
    "SL_SW_ND3",  # 恒星/辰星/极星开关 (三键)
    "SL_MC_ND3",  # 恒星/辰星/极星开关伴侣 (三键)
}
SUPPORTED_SWITCH_TYPES = {
    # --- 传统/通用开关控制器 ---
    "SL_S",  # 开关智控器
    "SL_P_SW",  # 九路开关控制器
    # --- 流光开关 ---
    "SL_SW_IF1",  # 流光开关 (单键) / 辰星开关
    "SL_SW_IF2",  # 流光开关 (双键) / 辰星开关
    "SL_SW_IF3",  # 流光开关 (三键) / 辰星开关
    "SL_SW_FE1",  # 塞纳/格致开关 (单键)
    "SL_SW_FE2",  # 塞纳/格致开关 (双键)
    "SL_SW_RC",  # 触摸开关 / 极星开关(零火版)
    "SL_SF_IF1",  # 单火流光开关 (单键)
    "SL_SF_IF2",  # 单火流光开关 (双键)
    "SL_SF_IF3",  # 单火流光开关 (三键)
    "SL_SF_RC",  # 单火触摸开关
    # --- ⽩⽟/墨⽟流光开关 ---
    "SL_SW_RC1",  # 白玉/墨玉流光开关 (单键)
    "SL_SW_RC2",  # 白玉/墨玉流光开关 (双键)
    "SL_SW_RC3",  # 白玉/墨玉流光开关 (三键)
    # --- 视界触摸开关 ---
    "SL_SW_NS1",  # 星玉开关 (单键)
    "SL_SW_NS2",  # 星玉开关 (双键)
    "SL_SW_NS3",  # 星玉开关 (三键)
    # --- 橙朴流光开关 ---
    "SL_SW_CP1",  # 橙朴流光开关 (单键)
    "SL_SW_CP2",  # 橙朴流光开关 (双键)
    "SL_SW_CP3",  # 橙朴流光开关 (三键)
    # --- 极星开关 ---
    "SL_SW_BS1",  # 极星开关 (120零火版, 单键)
    "SL_SW_BS2",  # 极星开关 (120零火版, 双键)
    "SL_SW_BS3",  # 极星开关 (120零火版, 三键)
    # --- 超能面板系列 ---
    "SL_NATURE",  # 超能面板 (根据P5口区分开关版或温控版)
    # --- 奇点开关模块 ---
    "SL_SW_MJ1",  # 奇点开关模块 (单路)
    "SL_SW_MJ2",  # 奇点开关模块 (双路)
    "SL_SW_MJ3",  # 奇点开关模块 (三路)
    "SL_SW_DM1",  # 动态调光开关
    # --- 其他开关 ---
    "V_IND_S",  # 虚拟开关
}

BUTTON_SWITCH_TYPES = {
    "SL_SC_BB",  # 随心开关 (CUBE Clicker)
    "SL_SC_BB_V2",  # 随心按键 (CUBE Clicker2)
}

# ================= 插座系列 (Outlet/Plug Series) =================
SMART_PLUG_TYPES = {
    "SL_OL",  # 智慧插座
    "SL_OL_3C",  # 智慧插座 (国标3C)
    "SL_OL_DE",  # 智慧插座 (德标)
    "SL_OL_UK",  # 智慧插座 (英标)
    "SL_OL_UL",  # 智慧插座 (美标)
    "OD_WE_OT1",  # Wi-Fi插座
}

# --- 计量插座 ---
POWER_METER_PLUG_TYPES = {
    "SL_OE_DE",  # 计量插座 (德标)
    "SL_OE_3C",  # 计量插座 (国标3C)
    "SL_OE_W",  # 入墙计量插座
}

# ================= 灯光系列 (Light Series) =================
# --- 灯光开关 (在HA中作为light实体) ---
LIGHT_SWITCH_TYPES = {
    "SL_OL_W",  # 入墙插座 (其开关行为被视为灯)
}
# --- 调光调色灯/控制器 ---
LIGHT_DIMMER_TYPES = {
    "SL_LI_WW",  # 白光智能灯泡
    "SL_LI_WW_V1",  # 智能灯泡(冷暖白)
    "SL_LI_WW_V2",  # 调光调色智控器(0-10V)
}
# --- 亮度调节控制器 ---
BRIGHTNESS_LIGHT_TYPES = {
    "SL_SPWM",  # 可调亮度开关智控器
}
# --- 量子灯 ---
QUANTUM_TYPES = {
    "OD_WE_QUAN",  # 量子灯
}
# --- RGB灯带/灯泡 ---
RGB_LIGHT_TYPES = {
    "SL_SC_RGB",  # 幻彩灯带（不带白光）
}
RGBW_LIGHT_TYPES = {
    "SL_CT_RGBW",  # 幻彩灯带 (带白光)
    "SL_LI_RGBW",  # RGBW灯泡
}
# --- 户外灯 ---
OUTDOOR_LIGHT_TYPES = {
    "SL_LI_GD1",  # 调光壁灯 (门廊壁灯)
    "SL_LI_UG1",  # 花园地灯
}
# --- 智能灯泡 ---
LIGHT_BULB_TYPES = {
    "SL_LI_BL",  # 智能灯泡
}

# ================= 窗帘系列 (Cover Series) =================
DOOYA_TYPES = {
    "SL_DOOYA",  # DOOYA窗帘电机
    "SL_DOOYA_V2",  # DOOYA窗帘电机 V2
    "SL_DOOYA_V3",  # 卷帘电机
    "SL_DOOYA_V4",  # 卷帘电机电池版
}

COVER_TYPES = {
    "SL_P_V2",  # 智界窗帘电机智控器
    "SL_SW_WIN",  # 窗帘控制开关
    "SL_CN_IF",  # 窗帘开关
    "SL_CN_FE",  # 窗帘开关
}

# 车库门
GARAGE_DOOR_TYPES = {
    "SL_ETDOOR",  # 车库门控制器
}

# ================= 感应器 - 二元状态 (Binary Sensor Series) =================
# --- 门窗感应器 ---
GUARD_SENSOR_TYPES = {"SL_SC_G", "SL_SC_BG"}  # 门禁感应器, 多功能(CUBE)门禁感应器
# --- 移动动态(PIR)感应器 ---
MOTION_SENSOR_TYPES = {
    "SL_SC_MHW",  # 动态感应器
    "SL_SC_BM",  # 多功能(CUBE)动态感应器
    "SL_SC_CM",  # 动态感应器（7号电池版）
}
# --- 水浸感应器 ---
WATER_SENSOR_TYPES = {"SL_SC_WA"}  # 水浸感应器
# --- 烟雾感应器 ---
SMOKE_SENSOR_TYPES = {"SL_P_A"}  # 烟雾感应器
# --- 人体存在(雷达)感应器 ---
RADAR_SENSOR_TYPES = {"SL_P_RM"}  # 人体存在感应器
# --- 云防系列 ---
DEFED_SENSOR_TYPES = {
    "SL_DF_GG",  # 云防门窗感应器
    "SL_DF_MM",  # 云防动态感应器
    "SL_DF_SR",  # 云防室内警铃
    "SL_DF_BB",  # 云防遥控器
}
# --- 基础二元传感器 (通常是其他设备附带的) ---
BINARY_SENSOR_TYPES = GUARD_SENSOR_TYPES | MOTION_SENSOR_TYPES

# ================= 感应器 - 数值状态 (Sensor Series) =================
# --- 环境感应器 ---
EV_SENSOR_TYPES = {
    "SL_SC_THL",  # 环境感应器 (温湿度光照)
    "SL_SC_BE",  # 多功能(CUBE)环境感应器
    "SL_SC_CQ",  # 环境感应器(CO2+TVOC)
    "SL_SC_B1",  # 环境感应器
    "SL_SC_CA",  # 环境感应器(CO2)
}
# TVOC/CO2/甲醛等
ENVIRONMENT_SENSOR_TYPES = {
    "SL_SC_CQ",  # 环境感应器(CO2+TVOC)
    "SL_SC_CA",  # 环境感应器(CO2)
    "SL_SC_B1",  # 环境感应器
    "SL_SC_CH",  # 气体感应器(甲醛)
}
# --- 燃气感应器 ---
GAS_SENSOR_TYPES = {"SL_SC_CP"}  # 气体感应器(燃气)
# --- 噪音感应器 ---
NOISE_SENSOR_TYPES = {"SL_SC_CN"}  # 噪音感应器
# --- 电量计量器 ---
POWER_METER_TYPES = {"ELIQ_EM", "V_DLT645_P"}  # ELIQ电量计量器, DLT电量计量器
# --- 语音小Q ---
VOICE_SENSOR_TYPES = {"SL_SC_CV"}  # 语音小Q

# ================= 温控系列 (Climate Series) =================
CLIMATE_TYPES = {
    "V_AIR_P",  # 智控器空调⾯板
    "SL_CP_DN",  # 地暖温控面板
    "SL_UACCB",  # 空调控制面板
    "SL_CP_VL",  # 温控阀门
    "SL_TR_ACIPM",  # 新风系统
    "SL_CP_AIR",  # ⻛机盘管
    "V_FRESH_P",  # 艾弗纳 KV11 (新风)
    "SL_NATURE",  # 超能面板PRO(温控) / 星玉温控面板
    "SL_FCU",  # ⻛机盘管 (星玉温控面板)
}

# ================= 温控器映射 (Climate Mappings) =================
# 用于在 Home Assistant 的标准 HVAC 模式与 LifeSmart 的私有模式值之间进行转换。

# SL_UACCB, SL_NATURE, SL_FCU 等设备的模式映射
LIFESMART_HVAC_MODE_MAP = {
    1: HVACMode.AUTO,
    2: HVACMode.FAN_ONLY,
    3: HVACMode.COOL,
    4: HVACMode.HEAT,
    5: HVACMode.DRY,
    7: HVACMode.HEAT,  # SL_NATURE/FCU 地暖模式
    8: HVACMode.HEAT_COOL,  # SL_NATURE/FCU 地暖+空调模式
}
REVERSE_LIFESMART_HVAC_MODE_MAP = {v: k for k, v in LIFESMART_HVAC_MODE_MAP.items()}

# --- V_AIR_P / SL_UACCB 风速映射 ---
LIFESMART_F_FAN_MODE_MAP = {
    FAN_LOW: 15,
    FAN_MEDIUM: 45,
    FAN_HIGH: 75,
}


def get_f_fan_mode(val: int) -> str:
    """根据 F 口的 val 值获取风扇模式。"""
    if val < 30:
        return FAN_LOW
    if val < 65:
        return FAN_MEDIUM
    return FAN_HIGH


# --- SL_TR_ACIPM (新风) 风速映射 ---
LIFESMART_ACIPM_FAN_MAP = {
    FAN_LOW: 1,
    FAN_MEDIUM: 2,
    FAN_HIGH: 3,
}
REVERSE_LIFESMART_ACIPM_FAN_MAP = {v: k for k, v in LIFESMART_ACIPM_FAN_MAP.items()}

# --- SL_CP_AIR (风机盘管) 模式与风速映射 (来自P1 bitmask) ---
LIFESMART_CP_AIR_MODE_MAP = {
    0: HVACMode.COOL,
    1: HVACMode.HEAT,
    2: HVACMode.FAN_ONLY,
}
REVERSE_LIFESMART_CP_AIR_MODE_MAP = {v: k for k, v in LIFESMART_CP_AIR_MODE_MAP.items()}

LIFESMART_CP_AIR_FAN_MAP = {
    0: FAN_AUTO,
    1: FAN_LOW,
    2: FAN_MEDIUM,
    3: FAN_HIGH,
}
REVERSE_LIFESMART_CP_AIR_FAN_MAP = {v: k for k, v in LIFESMART_CP_AIR_FAN_MAP.items()}

# --- SL_NATURE / SL_FCU (超能面板) 风速映射 (tF) ---
LIFESMART_TF_FAN_MODE_MAP = {
    FAN_AUTO: 101,
    FAN_LOW: 15,
    FAN_MEDIUM: 45,
    FAN_HIGH: 75,
}
REVERSE_LIFESMART_TF_FAN_MODE_MAP = {v: k for k, v in LIFESMART_TF_FAN_MODE_MAP.items()}


def get_tf_fan_mode(val: int) -> str | None:
    """根据 tF/F 口的 val 值获取风扇模式。"""
    if 30 >= val > 0:
        return FAN_LOW
    if val <= 65:
        return FAN_MEDIUM
    if val <= 100:
        return FAN_HIGH
    if val == 101:
        return FAN_AUTO
    return None  # 风扇停止时返回 None


# ================= 门锁系列 (Lock Series) =================
LOCK_TYPES = {
    "SL_LK_LS",  # 智能门锁 LS
    "SL_LK_GTM",  # 智能门锁 盖特曼
    "SL_LK_AG",  # 智能门锁 西勒奇
    "SL_LK_SG",  # 智能门锁 思哥
    "SL_LK_YL",  # 智能门锁 耶鲁
    "SL_P_BDLK",  # 智能门锁 必达
    "OD_JIUWANLI_LOCK1",  # 智能门锁 九万里
}
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

# ================= 平台聚合 (Platform Aggregation) =================
# 这些列表用于在 __init__.py 的 get_platform_by_device 函数中快速确定设备所属的平台。

# --- 总开关列表 ---
ALL_SWITCH_TYPES = (
    SUPPORTED_SWITCH_TYPES
    | SMART_PLUG_TYPES
    | POWER_METER_PLUG_TYPES
    | GENERIC_CONTROLLER_TYPES  # 通用控制器是动态的，他可能包含开关、插座等多种类型
    | VOLTAGE_SWITCH_TYPES  # 带电压的开关
)

# --- 总灯光列表 ---
ALL_LIGHT_TYPES = (
    LIGHT_SWITCH_TYPES
    | LIGHT_DIMMER_TYPES
    | RGB_LIGHT_TYPES
    | RGBW_LIGHT_TYPES
    | QUANTUM_TYPES
    | OUTDOOR_LIGHT_TYPES
    | LIGHT_BULB_TYPES
    | BRIGHTNESS_LIGHT_TYPES
    | SPOT_TYPES  # 超级碗的流光灯
    | GARAGE_DOOR_TYPES  # 车库门灯
)

# --- 总二元传感器列表 ---
ALL_BINARY_SENSOR_TYPES = (
    BINARY_SENSOR_TYPES
    | WATER_SENSOR_TYPES
    | SMOKE_SENSOR_TYPES
    | RADAR_SENSOR_TYPES
    | DEFED_SENSOR_TYPES
    | LOCK_TYPES
    | GENERIC_CONTROLLER_TYPES  # 通用控制器有时也作为二元传感器
    | BUTTON_SWITCH_TYPES  # 按钮开关也可以作为二元传感器
)

# --- 总数值传感器列表 ---
ALL_SENSOR_TYPES = (
    EV_SENSOR_TYPES
    | ENVIRONMENT_SENSOR_TYPES
    | GAS_SENSOR_TYPES
    | NOISE_SENSOR_TYPES
    | POWER_METER_TYPES
    | VOICE_SENSOR_TYPES
    | ALL_BINARY_SENSOR_TYPES  # 二元传感器也可能提供电量等数值
    | COVER_TYPES  # 窗帘电机电量
    | BUTTON_SWITCH_TYPES  # 按钮开关也可能提供电量等数值
    | SMOKE_SENSOR_TYPES
    | POWER_METER_PLUG_TYPES  # 计量插座也可能提供电量等数值
)

# --- 总窗帘/覆盖物列表 ---
ALL_COVER_TYPES = (
    COVER_TYPES
    | DOOYA_TYPES
    | GARAGE_DOOR_TYPES
    | GENERIC_CONTROLLER_TYPES  # 通用控制器是动态的，他可能包含开关、插座等多种类型
)

# --- Home Assistant 支持的平台列表 ---
SUPPORTED_PLATFORMS = {
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.COVER,
    Platform.LIGHT,
    Platform.CLIMATE,
    # Platform.CAMERA, # 摄像头平台当前未实现
}

# ================= 命令类型常量 (Command Type Constants) =================
# 用于 EpSet API 调用的命令类型代码，以提高代码可读性和可维护性。
CMD_TYPE_ON = "0x81"  # 通用开启命令
CMD_TYPE_OFF = "0x80"  # 通用关闭命令
CMD_TYPE_PRESS = "0x89"  # 点动命令
CMD_TYPE_SET_VAL = "0xCF"  # 设置数值 (如亮度、窗帘位置)
CMD_TYPE_SET_CONFIG = "0xCE"  # 设置配置/模式 (如空调模式、风速)
CMD_TYPE_SET_TEMP_DECIMAL = "0x88"  # 设置温度 (值为实际温度*10)
CMD_TYPE_SET_RAW = "0xFF"  # 设置原始值 (常用于位掩码配置)
CMD_TYPE_SET_TEMP_FCU = "0x89"  # FCU温控器设置温度的特殊命令码

# ================= 动态效果映射 (Dynamic Effects Mappings) =================
# --- 通用动态效果 ---
DYN_EFFECT_MAP = {
    "青草": 0x8218CC80,
    "海浪": 0x8318CC80,
    "深蓝山脉": 0x8418CC80,
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
    "听音变色(二代专属)": 0x07BD0990,
}

# 将动态效果和量子灯光效果映射合并
DYN_EFFECT_LIST = list(DYN_EFFECT_MAP.keys())
ALL_EFFECT_MAP = {**DYN_EFFECT_MAP, **QUANTUM_EFFECT_MAP}
ALL_EFFECT_LIST = list(ALL_EFFECT_MAP.keys())


# ================= 其他配置映射 =================

# 无位置窗帘配置映射 (用于将开/关/停动作映射到正确的IO口)
NON_POSITIONAL_COVER_CONFIG = {
    "SL_SW_WIN": {"open": "OP", "close": "CL", "stop": "ST"},
    "SL_P_V2": {"open": "P2", "close": "P3", "stop": "P4"},
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
