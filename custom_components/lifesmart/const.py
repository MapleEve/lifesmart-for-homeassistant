"""
LifeSmart Integration by @MapleEve
Provides constants and configurations for the LifeSmart home automation platform.
"""

from homeassistant.components import climate
from homeassistant.components.climate.const import (
    HVACMode,
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
)
from homeassistant.const import Platform

# ================= 常量定义 (Constants Definition) =================
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

CON_AI_TYPE_SCENE = "scene"
CON_AI_TYPE_AIB = "aib"
CON_AI_TYPE_GROUP = "grouphw"
CON_AI_TYPES = [
    CON_AI_TYPE_SCENE,
    CON_AI_TYPE_AIB,
    CON_AI_TYPE_GROUP,
]
AI_TYPES = ["ai"]

# ================= 开关系列 (Switch Series) =================
# 涵盖所有单火、零火、调光、场景、窗帘等开关面板
SUPPORTED_SWITCH_TYPES = [
    # --- 传统/通用开关控制器 ---
    "SL_S",
    "SL_P_SW",
    # --- 流光开关 ---
    "SL_SW_IF1",
    "SL_SW_IF2",
    "SL_SW_IF3",
    "SL_SW_FE1",
    "SL_SW_FE2",
    "SL_SW_RC",
    "SL_SF_IF1",
    "SL_SF_IF2",
    "SL_SF_IF3",
    "SL_SF_RC",
    # --- ⽩⽟/墨⽟流光开关 ---
    "SL_SW_RC1",
    "SL_SW_RC2",
    "SL_SW_RC3",
    # --- 恒星/⾠星/极星系列 (Nature/Star) ---
    "SL_SW_ND1",
    "SL_MC_ND1",
    "SL_SW_ND2",
    "SL_MC_ND2",
    "SL_SW_ND3",
    "SL_MC_ND3",
    # --- 视界触摸开关 ---
    "SL_SW_NS1",
    "SL_SW_NS2",
    "SL_SW_NS3",
    # --- 橙补流光开关 ---
    "SL_SW_CP1",
    "SL_SW_CP2",
    "SL_SW_CP3",
    # --- 极星开关 ---
    "SL_SW_BS1",
    "SL_SW_BS2",
    "SL_SW_BS3",
    "SL_SC_BB",  # 随心开关
    "SL_SC_BB_V2",  # 随心开关 V2
    # --- 超能面板系列 ---
    "SL_NATURE",  # 超能面板开关
    # --- 奇点开关模块 ---
    "SL_SW_MJ1",
    "SL_SW_MJ2",
    "SL_SW_MJ3",
    "SL_SW_DM1",
]

# ================= 插座系列 (Outlet/Plug Series) =================
SMART_PLUG_TYPES = [
    "SL_OL",
    "SL_OL_3C",  # 3C插座
    "SL_OL_DE",  # 德标
    "SL_OL_UK",  # 英标
    "SL_OL_UL",  # 美标
    "OD_WE_OT1",  # 智能插座（Wifi）
]

# --- 计量插座 ---
POWER_METER_PLUG_TYPES = [
    "SL_OE_DE",  # 德标插座
    "SL_OE_3C",  # 3C插座
    "SL_OE_W",  # 入墙插座
]

# ================= 灯光系列 (Light Series) =================
# --- 灯光开关 (作为light实体) ---
LIGHT_SWITCH_TYPES = [
    "SL_OL_W",
]
# --- 调光调色灯/控制器 ---
LIGHT_DIMMER_TYPES = [
    "SL_LI_WW",
    "SL_LI_WW_V1",
    "SL_LI_WW_V2",
]
# --- 亮度调节控制器 ---
BRIGHTNESS_LIGHT_TYPES = [
    "SL_SPWM",
]
# --- 量子灯 ---
QUANTUM_TYPES = [
    "OD_WE_QUAN",
]
# --- RGB灯带/灯泡 ---
RGB_LIGHT_TYPES = [
    "SL_SC_RGB",
]
RGBW_LIGHT_TYPES = [
    "SL_CT_RGBW",
    "SL_LI_RGBW",
]
# --- 户外灯 ---
OUTDOOR_LIGHT_TYPES = [
    "SL_LI_GD1",  # 调光壁灯（门廊壁灯）
    "SL_LI_UG1",  # 花园地灯
]
# --- 智能灯泡 ---
LIGHT_BULB_TYPES = [
    "SL_LI_BL",
]

# ================= 窗帘系列 (Cover Series) =================
DOOYA_TYPES = [
    "SL_DOOYA",
    "SL_DOOYA_V2",
    "SL_DOOYA_V3",  # 卷帘电机
    "SL_DOOYA_V4",  # 卷帘电机电池
]

COVER_TYPES = [
    "SL_P_V2",
    "SL_SW_WIN",
    "SL_CN_IF",
    "SL_CN_FE",
]

# 车库门
GARAGE_DOOR_TYPES = [
    "SL_ETDOOR",
]

# ================= 感应器 - 二元状态 (Binary Sensor Series) =================
# --- 门窗感应器 ---
GUARD_SENSOR_TYPES = ["SL_SC_G", "SL_SC_BG"]
# --- 移动动态(PIR)感应器 ---
MOTION_SENSOR_TYPES = ["SL_SC_MHW", "SL_SC_BM", "SL_SC_CM"]
# --- 水浸感应器 ---
WATER_SENSOR_TYPES = ["SL_SC_WA"]
# --- 烟雾感应器 ---
SMOKE_SENSOR_TYPES = ["SL_P_A"]
# --- 人体存在(雷达)感应器 ---
RADAR_SENSOR_TYPES = ["SL_P_RM"]
# --- 云防系列 ---
DEFED_SENSOR_TYPES = [
    "SL_DF_GG",  # 云防门窗
    "SL_DF_MM",  # 云防动态
    "SL_DF_SR",  # 云防警铃
    "SL_DF_BB",  # 云防遥控器
]
# --- 基础二元传感器 (通常是其他设备附带的) ---
BINARY_SENSOR_TYPES = (
    [
        "SL_P",  # SPOT Pro
    ]
    + GUARD_SENSOR_TYPES
    + MOTION_SENSOR_TYPES
)

# ================= 感应器 - 数值状态 (Sensor Series) =================
# --- 环境感应器 ---
EV_SENSOR_TYPES = ["SL_SC_THL", "SL_SC_BE", "SL_SC_CQ", "SL_SC_B1", "SL_SC_CA"]
# TVOC/CO2/甲醛等
ENVIRONMENT_SENSOR_TYPES = [
    "SL_SC_CQ",
    "SL_SC_CA",
    "SL_SC_B1",
    "SL_SC_CH",
]
# --- 燃气感应器 ---
GAS_SENSOR_TYPES = ["SL_SC_CP"]  # 燃气
# --- 噪音感应器 ---
NOISE_SENSOR_TYPES = ["SL_SC_CN"]
# --- 电量计量器 ---
POWER_METER_TYPES = ["ELIQ_EM", "V_DLT645_P"]
# --- 语音小Q ---
VOICE_SENSOR_TYPES = ["SL_SC_CV"]

# ================= 温控系列 (Climate Series) =================
CLIMATE_TYPES = [
    "V_AIR_P",  # 智控器空调⾯板
    "SL_CP_DN",  # 地暖温控器
    "SL_UACCB",  # 空调控制器
    "SL_CP_VL",  # 温控阀门
    "SL_TR_ACIPM",  # 新风系统
    "SL_CP_AIR",  # 风机盘管
    "V_FRESH_P",  # 艾弗纳 KV11
    "SL_NATURE",  # 超能面板 Pro
    "SL_FCU",  # 超能面板 星⽟
]
# ================= 温控器映射 (Climate Mappings) =================
# SL_UACCB, SL_NATURE, SL_FCU 等设备的模式映射
LIFESMART_HVAC_MODE_MAP = {
    1: HVACMode.AUTO,
    2: HVACMode.FAN_ONLY,
    3: HVACMode.COOL,
    4: HVACMode.HEAT,
    5: HVACMode.DRY,
    7: HVACMode.HEAT,  # SL_NATURE/FCU 地暖
    8: HVACMode.HEAT_COOL,  # SL_NATURE/FCU 地暖+空调
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
LOCK_TYPES = [
    "SL_LK_LS",
    "SL_LK_GTM",
    "SL_LK_AG",
    "SL_LK_SG",
    "SL_LK_YL",
    "SL_P_BDLK",
    "OD_JIUWANLI_LOCK1",
]
# 门锁解锁方式
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

# ================= 其他设备类型 =================
# --- 超级碗 (SPOT) ---
SPOT_TYPES = ["MSL_IRCTL", "OD_WE_IRCTL", "SL_SPOT", "SL_P_IR", "SL_P_IR_V2"]
# --- 通用控制器 ---
GENERIC_CONTROLLER_TYPES = ["SL_P", "SL_JEMA"]
# --- 摄像头 ---
CAMERA_TYPES = ["LSCAM:LSICAMGOS1", "LSCAM:LSICAMEZ2"]

# ================= 平台聚合 (Platform Aggregation) =================
# --- 总开关列表 ---
ALL_SWITCH_TYPES = SUPPORTED_SWITCH_TYPES + SMART_PLUG_TYPES + POWER_METER_PLUG_TYPES

# --- 总灯光列表 ---
ALL_LIGHT_TYPES = (
    LIGHT_SWITCH_TYPES
    + LIGHT_DIMMER_TYPES
    + RGB_LIGHT_TYPES
    + RGBW_LIGHT_TYPES
    + QUANTUM_TYPES
    + OUTDOOR_LIGHT_TYPES
    + LIGHT_BULB_TYPES
)
# --- 总二元传感器列表 ---
ALL_BINARY_SENSOR_TYPES = (
    BINARY_SENSOR_TYPES
    + WATER_SENSOR_TYPES
    + SMOKE_SENSOR_TYPES
    + RADAR_SENSOR_TYPES
    + DEFED_SENSOR_TYPES
    + LOCK_TYPES
)

# --- 总数值传感器列表 ---
ALL_SENSOR_TYPES = (
    EV_SENSOR_TYPES
    + ENVIRONMENT_SENSOR_TYPES
    + GAS_SENSOR_TYPES
    + NOISE_SENSOR_TYPES
    + POWER_METER_TYPES
    + VOICE_SENSOR_TYPES
    +
    # 部分二元传感器也提供数值读数 (如电量、温度)
    ALL_BINARY_SENSOR_TYPES
    + COVER_TYPES
)


# --- 总窗帘/覆盖物列表 ---
ALL_COVER_TYPES = COVER_TYPES + DOOYA_TYPES + GARAGE_DOOR_TYPES

# --- 支持的平台列表 ---
SUPPORTED_PLATFORMS = [
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.COVER,
    Platform.LIGHT,
    Platform.CLIMATE,
    # Platform.CAMERA,
]

# ================= 其他常量 =================
# 空调状态列表
LIFESMART_HVAC_STATE_LIST = [
    climate.const.HVACMode.OFF,
    climate.const.HVACMode.AUTO,
    climate.const.HVACMode.FAN_ONLY,
    climate.const.HVACMode.COOL,
    climate.const.HVACMode.HEAT,
    climate.const.HVACMode.DRY,
]

# 无位置窗帘配置映射
NON_POSITIONAL_COVER_CONFIG = {
    "SL_SW_WIN": {"open": "OP", "close": "CL", "stop": "ST"},
    "SL_P_V2": {"open": "P2", "close": "P3", "stop": "P4"},
    "SL_CN_IF": {"open": "P1", "close": "P2", "stop": "P3"},
    "SL_CN_FE": {"open": "P1", "close": "P2", "stop": "P3"},
}

# 组件相关常量
DOMAIN = "lifesmart"
MANUFACTURER = "LifeSmart"

# 设备相关常量
DEVICE_ID_KEY = "me"
SUBDEVICE_INDEX_KEY = "idx"
DEVICE_TYPE_KEY = "devtype"
HUB_ID_KEY = "agt"
DEVICE_NAME_KEY = "name"
DEVICE_DATA_KEY = "data"
DEVICE_VERSION_KEY = "ver"

# WebSocket 相关常量
LIFESMART_STATE_MANAGER = "lifesmart_wss"
UPDATE_LISTENER = "update_listener"
LIFESMART_SIGNAL_UPDATE_ENTITY = "lifesmart_updated"

# 服务器区域
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
