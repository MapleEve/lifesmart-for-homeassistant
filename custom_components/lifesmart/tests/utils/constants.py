"""
测试常量定义文件。

此模块包含：
1. 固定的测试用Hub ID列表
2. 测试设备ID常量
3. 其他测试相关的常量定义
4. 友好设备名称映射
"""

# ============================================================================
# === 测试Hub ID常量 ===
# ============================================================================

# 固定的测试用hub ID列表 - 保证测试数据一致性
TEST_HUB_IDS = [
    "A3EAAABgAEwQRzMONjg1NA",  # 文档中的真实hub ID
    "A3EAAABtAEwQRzMONjg5NA",  # 文档中的另一个真实hub ID
    "B4FBBBChBFxRSzNPNkg2OB",  # 固定测试hub ID 1
    "C5GCCCDiBGySTzOQOlh3PC",  # 固定测试hub ID 2
    "D6HDDDEjCHzTUzPRPmi4QD",  # 固定测试hub ID 3
    "E7IEEEFkDI0UVzQSQnj5RE",  # 固定测试hub ID 4
    "F8JFFFGlEJ1VWzRTRok6SF",  # 固定测试hub ID 5
    "G9KGGGHmFK2WXzSUSpl7TG",  # 固定测试hub ID 6
    "H0LHHHInGL3XYzTVTqm8UH",  # 固定测试hub ID 7
    "I1MIIIJoHM4YZzUWUrn9VI",  # 固定测试hub ID 8
]


# ============================================================================
# === 专用设备测试常量 ===
# ============================================================================

# 专用测试设备的Hub和设备ID
SPECIALIZED_TEST_DEVICE_IDS = {
    "climate_fancoil": {
        "agt": "hub_climate",
        "me": "fancoil_single",
    },
    "spot_rgb_light": {
        "agt": "hub_light",
        "me": "spot_rgb_single",
    },
    "dual_io_rgbw_light": {
        "agt": "hub_light",
        "me": "dual_io_rgbw_single",
    },
    "single_io_rgb_light": {
        "agt": "hub_light",
        "me": "single_io_rgb_single",
    },
}


# ============================================================================
# === 友好设备名称映射表 ===
# ============================================================================

# test_helpers.py中使用的友好设备名称到实际设备类型的映射
FRIENDLY_DEVICE_NAMES = {
    # 开关设备
    "sw_ol": "SL_OL",
    "sw_if3": "SL_SW_IF3",
    "sw_p9": "SL_P_SW",
    "sw_nature": "SL_NATURE",
    "generic_p_switch_mode": "SL_P",
    "if3b2": "SL_SW_IF3",  # 特殊测试设备
    # 灯光设备
    "light_bright": "SL_LI_WW",
    "light_dimmer": "SL_LI_WW_V1",
    "light_quantum": "OD_WE_QUAN",
    "light_spotrgb": "SL_SPOT",
    "light_spotrgbw": "MSL_IRCTL",
    "light_singlergb": "SL_CT_RGBW",
    "light_dualrgbw": "SL_LI_RGBW",
    "light_outdoor": "SL_LI_GD1",
    "light_cover": "SL_LI_UG1",
    # 二进制传感器
    "bs_door": "SL_SC_G",
    "bs_motion": "SL_SC_MHW",
    "bs_water": "SL_SC_WA",
    "bs_lock": "SL_LK_LS",
    "bs_smoke": "SL_P_A",
    # 传感器
    "sensor_env": "SL_SC_THL",
    "sensor_co2": "SL_SC_CA",
    "sensor_power_plug": "SL_OE_3C",
    "sensor_lock_battery": "SL_LK_LS",
    # 窗帘设备
    "cover_garage": "SL_ETDOOR",
    "cover_dooya": "SL_DOOYA",
    "cover_generic": "SL_SW_WIN",
    "cover_nonpos": "SL_P",
    # 气候设备
    "climate_nature_thermo": "SL_NATURE",
    "climate_floor_heat": "SL_CP_DN",
    "climate_fancoil": "SL_CP_AIR",
    "climate_airpanel": "V_AIR_P",
    "climate_airsystem": "SL_TR_ACIPM",
}

# 测试用的虚拟设备名称（用于错误处理测试）
VIRTUAL_TEST_DEVICES = [
    "any_device",  # 通用测试设备
    "nonexistent_device",  # 不存在的设备
]


# ============================================================================
# === 其他测试常量 ===
# ============================================================================

# 标准测试配置数据的字段名
STANDARD_CONFIG_FIELDS = [
    "CONF_TYPE",
    "CONF_LIFESMART_APPKEY",
    "CONF_LIFESMART_APPTOKEN",
    "CONF_LIFESMART_USERID",
    "CONF_LIFESMART_USERTOKEN",
    "CONF_REGION",
]

# 默认测试值
DEFAULT_TEST_VALUES = {
    "appkey": "mock_appkey",
    "apptoken": "mock_apptoken",
    "userid": "mock_userid",
    "usertoken": "mock_usertoken",
    "region": "cn2",
    "wss_url": "wss://test.com/ws",
    "wss_auth": '{"auth": "test"}',
}

# 测试用的错误消息常量
TEST_ERROR_MESSAGES = {
    "device_not_found": "Device with me '{}' not found in device list",
    "invalid_hub_id": "Invalid hub ID format: {}",
    "missing_data_field": "Required data field '{}' is missing",
}

# 测试覆盖率相关常量
TEST_COVERAGE_TARGETS = {
    "factories": 95,  # 工厂函数覆盖率目标
    "helpers": 90,  # helper函数覆盖率目标
    "integration": 85,  # 集成测试覆盖率目标
}
