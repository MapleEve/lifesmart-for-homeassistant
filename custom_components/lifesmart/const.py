from homeassistant.components import climate
from homeassistant.const import Platform

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
SUPPORTED_SWTICH_TYPES = [
    "OD_WE_OT1",
    "SL_MC_ND1",
    "SL_MC_ND2",
    "SL_MC_ND3",
    "SL_NATURE",
    "SL_OL",
    "SL_OL_3C",
    "SL_OL_DE",
    "SL_OL_UK",
    "SL_OL_UL",
    "SL_OL_W",
    "SL_P_SW",
    "SL_S",
    "SL_SF_IF1",
    "SL_SF_IF2",
    "SL_SF_IF3",
    "SL_SF_RC",
    "SL_SPWM",
    "SL_SW_CP1",
    "SL_SW_CP2",
    "SL_SW_CP3",
    "SL_SW_DM1",
    "SL_SW_FE1",
    "SL_SW_FE2",
    "SL_SW_IF1",
    "SL_SW_IF2",
    "SL_SW_IF3",
    "SL_SW_MJ1",
    "SL_SW_MJ2",
    "SL_SW_MJ3",
    "SL_SW_ND1",
    "SL_SW_ND2",
    "SL_SW_ND3",
    "SL_SW_NS3",
    "SL_SW_RC",
    "SL_SW_RC1",
    "SL_SW_RC2",
    "SL_SW_RC3",
    "SL_SW_NS1",
    "SL_SW_NS2",
    "SL_SW_NS3",
    "V_IND_S",
]

SUPPORTED_SUB_SWITCH_TYPES = [
    "L1",
    "L2",
    "L3",
    "P1",
    "P2",
    "P3",
]

SUPPORTED_SUB_BINARY_SENSORS = [
    "M",
    "G",
    "B",
    "AXS",
    "P1",
    "P5",
    "P6",
    "P7",
]

LIGHT_SWITCH_TYPES = [
    "SL_OL_W",
    "SL_SW_IF1",
    "SL_SW_IF2",
    "SL_SW_IF3",
    "SL_CT_RGBW",
]
LIGHT_DIMMER_TYPES = [
    "SL_LI_WW",
]

QUANTUM_TYPES = [
    "OD_WE_QUAN",
]
MOTION_SENSOR_TYPES = ["SL_SC_MHW", "SL_SC_BM", "SL_SC_CM"]
SMOKE_SENSOR_TYPES = ["SL_P_A"]
SPOT_TYPES = ["MSL_IRCTL", "OD_WE_IRCTL", "SL_SPOT"]
BINARY_SENSOR_TYPES = [
    "SL_SC_G",
    "SL_SC_BG",
    "SL_SC_MHW ",
    "SL_SC_BM",
    "SL_SC_CM",
    "SL_P_A",
    "SL_P",
]
COVER_TYPES = ["SL_DOOYA", "SL_P_V2", "SL_SW_WIN", "SL_CN_IF", "SL_CN_FE"]
GAS_SENSOR_TYPES = ["SL_SC_WA ", "SL_SC_CH", "SL_SC_CP", "ELIQ_EM"]
EV_SENSOR_TYPES = ["SL_SC_THL", "SL_SC_BE", "SL_SC_CQ", "SL_SC_B1_V1"]
OT_SENSOR_TYPES = ["SL_SC_MHW", "SL_SC_BM", "SL_SC_G", "SL_SC_BG"]
LOCK_TYPES = [
    "SL_LK_LS",
    "SL_LK_GTM",
    "SL_LK_AG",
    "SL_LK_SG",
    "SL_LK_YL",
    "SL_P_BDLK",
    "OD_JIUWANLI_LOCK1",
]
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
GUARD_SENSOR_TYPES = ["SL_SC_G", "SL_SC_BG"]
DEVICE_WITHOUT_IDXNAME = [
    "SL_NATURE",
    "SL_SW_ND1",
    "SL_SW_ND2",
    "SL_SW_ND3",
    "SL_SW_MJ1",
    "SL_SW_MJ2",
    "SL_SW_MJ3",
]
GENERIC_CONTROLLER_TYPES = ["SL_P", "SL_P_IR"]
SMART_PLUG_TYPES = ["SL_OE_DE", "SL_OE_3C", "SL_OE_W", "OD_WE_OT1"]

LIFESMART_HVAC_STATE_LIST = [
    climate.const.HVACMode.OFF,
    climate.const.HVACMode.AUTO,
    climate.const.HVACMode.FAN_ONLY,
    climate.const.HVACMode.COOL,
    climate.const.HVACMode.HEAT,
    climate.const.HVACMode.DRY,
]

SUPPORTED_PLATFORMS = [
    Platform.SWITCH,
    Platform.BINARY_SENSOR,
    Platform.SENSOR,
    Platform.COVER,
    Platform.LIGHT,
    Platform.CLIMATE,
]
CLIMATE_TYPES = ["V_AIR_P", "SL_CP_DN"]

ENTITYID = "entity_id"
DOMAIN = "lifesmart"

MANUFACTURER = "LifeSmart"

DEVICE_ID_KEY = "me"
SUBDEVICE_INDEX_KEY = "idx"
DEVICE_TYPE_KEY = "devtype"
HUB_ID_KEY = "agt"
DEVICE_NAME_KEY = "name"
DEVICE_DATA_KEY = "data"
DEVICE_VERSION_KEY = "ver"

LIFESMART_STATE_MANAGER = "lifesmart_wss"
UPDATE_LISTENER = "update_listener"

LIFESMART_SIGNAL_UPDATE_ENTITY = "lifesmart_updated"

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
