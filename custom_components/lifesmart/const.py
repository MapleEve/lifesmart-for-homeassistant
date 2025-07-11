from homeassistant.components import climate
from homeassistant.const import Platform

# ================= 常量定义 (Constants Definition) =================
CONF_LIFESMART_APPKEY = "appkey"
CONF_LIFESMART_APPTOKEN = "apptoken"
CONF_LIFESMART_USERTOKEN = "usertoken"
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
    # --- 传统/通用开关 ---
    "SL_S",
    "SL_P_SW",
    "SL_SW_IF1",
    "SL_SW_IF2",
    "SL_SW_IF3",
    "SL_SW_FE1",
    "SL_SW_FE2",
    "SL_SW_RC",
    "SL_SW_RC1",
    "SL_SW_RC2",
    "SL_SW_RC3",
    "V_IND_S",
    # --- 极星/辰星系列 (Nature/Star) ---
    "SL_SW_ND1",
    "SL_SW_ND2",
    "SL_SW_ND3",
    "SL_SW_NS1",
    "SL_SW_NS2",
    "SL_SW_NS3",
    "SL_SW_NS1_L",
    "SL_SW_NS2_L",
    "SL_SW_NS3_L",  # 极星开关(零火)
    # --- 奇点/CUBE系列 ---
    "SL_SW_CP1",
    "SL_SW_CP2",
    "SL_SW_CP3",
    "SL_SW_CUBE_B1",
    "SL_SW_CUBE_B2",
    "SL_SW_CUBE_B3",  # 奇点开关模块
    "SL_SW_CUBE_S1",  # 随心开关
    # --- 星玉/超能面板系列 (Nature/Mini) ---
    "SL_NATURE",
    "SL_SW_MINI_1",
    "SL_SW_MINI_2",  # 超能面板
    # --- 其他控制器 ---
    "SL_SF_IF1",
    "SL_SF_IF2",
    "SL_SF_IF3",
    "SL_SF_RC",
    "SL_SPWM",
    # --- 废弃或区域性 ---
    "SL_SW_MJ1",
    "SL_SW_MJ2",
    "SL_SW_MJ3",
    "SL_SW_DM1",
]

# ================= 插座系列 (Outlet/Plug Series) =================
SMART_PLUG_TYPES = [
    "SL_OL",
    "SL_OL_3C",
    "SL_OL_DE",
    "SL_OL_UK",
    "SL_OL_UL",
    "OD_WE_OT1",
    "SL_OE_DE",
    "SL_OE_3C",
    "SL_OE_W",  # 兼容旧版
]

# --- 计量插座 ---
POWER_METER_PLUG_TYPES = [
    "SL_OL_ME",
]

# ================= 灯光系列 (Light Series) =================
# --- 灯光开关 (作为light实体) ---
LIGHT_SWITCH_TYPES = [
    "SL_OL_W",
    "SL_LI_S",
]
# --- 调光调色灯/控制器 ---
LIGHT_DIMMER_TYPES = [
    "SL_LI_WW",
    "SL_LI_WW_V2",
    "SL_LI_DIM",
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
COVER_TYPES = [
    "SL_DOOYA",
    "SL_P_V2",
    "SL_SW_WIN",
    "SL_CN_IF",
    "SL_CN_FE",
    "SL_CU_SMART",  # 智界窗帘电机
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
    "SL_DF_Siren",  # 云防警铃
    "SL_DF_Fob",  # 云防遥控器
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
    "SL_SC_TVOC",
    "SL_SC_CO2",
    "SL_SC_CH",
]
# --- 气体感应器 ---
GAS_SENSOR_TYPES = ["SL_SC_CP"]  # 燃气
# --- 噪音感应器 ---
NOISE_SENSOR_TYPES = ["SL_SC_CN"]
# --- 电量计量器 ---
POWER_METER_TYPES = ["ELIQ_EM", "SL_DLT_M"]  # DLT 电量计量
# --- 语音小Q ---
VOICE_SENSOR_TYPES = ["SL_SC_CV"]

# ================= 温控系列 (Climate Series) =================
CLIMATE_TYPES = [
    "V_AIR_P",
    "SL_CP_DN",
    "SL_TH_P1",
    "SL_TH_P2",  # 地暖温控器
    "SL_TH_S1",
    "SL_TH_S2",  # 温控阀门
    "SL_FA_P1",  # 新风系统
    "SL_FCU_P1",  # 风机盘管
]

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
# --- 红外伴侣 (SPOT) ---
SPOT_TYPES = ["MSL_IRCTL", "OD_WE_IRCTL", "SL_SPOT", "SL_P_IR"]
# --- 通用控制器 ---
GENERIC_CONTROLLER_TYPES = ["SL_P", "SL_P_IR", "SL_GC_HA", "SL_GC_485"]  # 新增
# --- 摄像头 ---
CAMERA_TYPES = ["SL_CAM_OD1", "SL_CAM_PT1"]  # 新增
# --- 报警器 ---
ALARM_TYPES = ["SL_P_ALARM"]  # 新增

# --- 辅助常量 ---
DEVICE_WITHOUT_IDXNAME = [
    "SL_NATURE",
    "SL_SW_ND1",
    "SL_SW_ND2",
    "SL_SW_ND3",
    "SL_SW_MJ1",
    "SL_SW_MJ2",
    "SL_SW_MJ3",
]
SUPPORTED_SUB_SWITCH_TYPES = ["L1", "L2", "L3", "P1", "P2", "P3"]
SUPPORTED_SUB_BINARY_SENSORS = ["M", "G", "B", "AXS", "P1", "P5", "P6", "P7"]

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
    DEFED_SENSOR_TYPES
    + WATER_SENSOR_TYPES
    + SMOKE_SENSOR_TYPES
    + RADAR_SENSOR_TYPES
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

# --- 总窗帘/覆盖物列表 ---
ALL_COVER_TYPES = COVER_TYPES + GARAGE_DOOR_TYPES

# --- 支持的平台列表 ---
SUPPORTED_PLATFORMS = [
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.COVER,
    Platform.LIGHT,
    Platform.CLIMATE,
    Platform.LOCK,
    Platform.CAMERA,
    Platform.ALARM_CONTROL_PANEL,
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

# 组件相关常量
ENTITYID = "entity_id"
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
    {"label": "中国 1 (cn0)", "value": "cn0"},
    {"label": "中国备用(cn1)", "value": "cn1"},
    {"label": "中国 2 (cn2)", "value": "cn2"},
    {"label": "北美服务器 (US/NA)", "value": "us"},
    {"label": "欧洲服务器 (EUROPE)", "value": "eur"},
    {"label": "日本服务器 (JAPAN)", "value": "jp"},
    {"label": "亚太其他区 (APAC)", "value": "apz"},
    {"label": "自动选择 Global", "value": "AUTO"},
]
