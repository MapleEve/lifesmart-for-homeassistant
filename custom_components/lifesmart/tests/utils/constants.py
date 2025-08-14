"""
测试常量定义文件。

此模块包含：
1. 固定的测试用Hub ID列表
2. 测试设备ID常量
3. 其他测试相关的常量定义
4. 友好设备名称映射
"""

from homeassistant.const import CONF_REGION

from custom_components.lifesmart.core.const import (
    CONF_LIFESMART_APPKEY,
    CONF_LIFESMART_APPTOKEN,
    CONF_LIFESMART_USERID,
)

# ============================================================================
# === 基础测试值 (moved up to avoid circular import) ===
# ============================================================================

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

# ============================================================================
# === 测试配置常量 ===
# ============================================================================

# 模拟云端配置凭证
MOCK_CLOUD_CREDENTIALS = {
    CONF_LIFESMART_APPKEY: DEFAULT_TEST_VALUES["appkey"],
    CONF_LIFESMART_APPTOKEN: DEFAULT_TEST_VALUES["apptoken"],
    CONF_LIFESMART_USERID: DEFAULT_TEST_VALUES["userid"],
    CONF_REGION: DEFAULT_TEST_VALUES["region"],
}

# ============================================================================
# === conftest.py 测试基础设施常量 ===
# ============================================================================

# 配置流程标识符
CONFIG_FLOW_IDENTIFIERS = {
    "cloud": "cloud",
    "cloud_token": "cloud_token",
    "local": "local",
    "password": "password",
}

# 区域标识符
REGION_IDENTIFIERS = {
    "china_region": "cn2",
}

# 测试环境配置
TEST_ENVIRONMENT_CONFIG = {
    "service": "test_service",
    "admin_role": "admin",
    "test_user": "test_user",
}

# 测试配置条目常量
TEST_CONFIG_ENTRY = {
    "mock_entry_id": "mock_entry_id_12345",
    "mock_title": "LifeSmart Mock",
}

# 测试排除配置
TEST_EXCLUSION_CONFIG = {
    "excluded_device": "excluded_device",
    "excluded_hub": "excluded_hub",
}

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
    "White Light Bulb": "SL_LI_WW",  # 用于brightness light测试
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

# 测试用的错误消息常量
TEST_ERROR_MESSAGES = {
    "device_not_found": "Device with me '{}' not found in devices list",
    "invalid_hub_id": "Invalid hub ID format: {}",
    "missing_data_field": "Required data field '{}' is missing",
}

# 测试覆盖率相关常量
TEST_COVERAGE_TARGETS = {
    "factories": 95,  # 工厂函数覆盖率目标
    "helpers": 90,  # helper函数覆盖率目标
    "integration": 85,  # 集成测试覆盖率目标
}


# ============================================================================
# === 协议和TCP客户端测试常量 (Phase 2.3 Batch 3) ===
# ============================================================================

# 协议测试相关常量
PROTOCOL_TEST_VALUES = {
    # 测试网络参数
    "test_agt": "test_agt",
    "test_node": "test_node",
    "localhost": "localhost",
    "test_port": 9999,
    # 测试设备标识符
    "test_device_001": "dev_001",
    "test_device_1": "device_1",
    "test_device_2": "device_2",
    # 协议测试标识符
    "worker_data_prefix": "worker_{worker_id}_data",
    "ai_ir_prefix": "AI_IR_ir_device",
    # 时间戳测试值
    "test_timestamp": 1634567890,
    # 红外设备测试值
    "ir_device_id": "ir_device",
    "ir_dev_id": "ir_dev",
    "scene_123": "scene123",
}

# TCP客户端测试相关常量
TCP_CLIENT_TEST_VALUES = {
    # 连接参数
    "test_host_local": "localhost",
    "test_host_ip": "192.168.1.100",
    "test_port_8080": 8080,
    "test_port_8888": 8888,
    "test_port_1234": 1234,
    # 认证参数
    "test_admin_user": "admin",
    "test_admin_pass": "password",
    "test_generic_user": "user",
    "test_generic_pass": "pass",
    "test_user_name": "test_user",
    "test_user_pass": "test_pass",
    # 温度测试值
    "test_temp_celsius": 23.5,
    "test_temp_decimal": 235,
    "test_temp_25c": 25.0,
    "test_temp_250": 250,
    # 网络超时值
    "timeout_1s": 1.0,
    "timeout_100ms": 0.1,
    "timeout_200ms": 0.2,
    # 设备控制测试值
    "test_brightness_80": 80,
    "test_rgb_white": 16777215,  # RGB白色值
    "test_fan_delay": 15,  # 风扇模式延迟值
}

# 协议和网络错误码常量 (保留业务验证值)
PROTOCOL_ERROR_CODES = {
    # 这些是协议标准值，不应该常量化
    "LOGIN_ERROR_CODE": -2001,  # 协议标准登录失败错误码
}

# 测试场景和定时器常量
TEST_SCENARIOS = {
    # 场景控制测试
    "door_open_trigger": "door_open_trigger",
    "test_ai_device": "test_ai_device",
    "config_device": "config_device",
    "timer_device": "timer_device",
    "icon_device": "icon_device",
    # 配置和命令
    "network_settings": "network_settings",
    "network_config": "192.168.1.100:8080",
    "weekday_morning": "0 8 * * 1-5",  # 工作日早上8点
    "light_bulb_icon": "light_bulb",
    "trigger_commands": "L1=ON;L2=OFF;DELAY=1000;L3=ON",
    "timer_commands": "L1=ON;BRI=100",
}


# ============================================================================
# === 业务逻辑测试常量 (Phase 2.4 Batch 4) ===
# ============================================================================

# Hub业务逻辑测试相关常量
HUB_BUSINESS_LOGIC_TEST_VALUES = {
    # Hub和设备标识符常量
    "test_hub_primary": "test_hub",
    "test_device_primary": "test_device",
    "hub_identifier_1": "hub1",
    "hub_identifier_2": "hub2",
    "device_identifier_1": "dev1",
    "device_identifier_2": "dev2",
    "test_device_type": "test_type",
    # OAPI认证测试常量
    "test_appkey_oapi": "test_appkey",
    "test_apptoken_oapi": "test_apptoken",
    "test_userid_oapi": "test_userid",
    "test_usertoken_oapi": "test_usertoken",
    "new_token_refresh": "new_token",
    "token_expiry_time": 9999999999,
    # 本地网络配置常量
    "local_test_ip": "192.168.1.100",
    "local_test_port": 8888,
    "local_admin_user": "admin",
    "local_admin_pass": "admin",
    # WebSocket测试常量
    "test_websocket_url": "wss://test.com/ws",
    "test_websocket_local": "ws://localhost/test",
    # 设备数据测试常量
    "test_device_name": "Test Device",
    "scene_device_prefix": "scene",
    "ai_device_identifier": "ai_device",
    "ai_hub_identifier": "ai_hub",
    "filtered_device_id": "filtered_device",
    "filtered_hub_id": "filtered_hub",
    # 测试配置条目ID
    "test_entry_oapi_id": "test_entry_oapi",
    "test_entry_local_id": "test_entry_local",
    "test_reauth_id": "test_reauth",
    "test_unique_id": "test_entry",
}

# 客户端基础测试常量
CLIENT_BASE_TEST_VALUES = {
    # 客户端命令测试标识符
    "command_agt_1": "agt1",
    "command_device_1": "dev1",
    "command_io_l1": "L1",
    "command_type_generic": "type",
    # 场景控制测试常量
    "scene_identifier_1": "scene1",
    "scene_hub_default": "0000",
    "scene_device_default": "LS",
    # IO口标识符常量
    "io_port_p1": "P1",
    "io_port_open": "OP",
    "io_port_close": "CL",
    "io_port_stop": "ST",
    "io_port_position": "PE",
    # 客户端测试数值参数（保留为业务验证值）
    # 注意：以下数值是业务逻辑验证值，不应修改
    # "command_value_on": 1,
    # "command_value_off": 0,
    # "hvac_mode_value": 2,
    # "fan_speed_value": 3,
    # "temperature_decimal": 245,
    # "brightness_value": 128,
    # "position_value": 75,
}

# Hub业务逻辑测试扩展常量
HUB_BUSINESS_LOGIC_EXTENDED = {
    # 排除配置测试常量
    "exclude_devices_list": "dev1,dev2",
    "exclude_hubs_list": "hub2",
    "exclude_device_1": "dev1",
    "exclude_device_2": "dev2",
    "exclude_hub_2": "hub2",
    # 本地测试账号常量
    "local_test_user": "test_user",
    "local_test_password": "test_pass",
    # 设备类型测试常量
    "device_type_switch": "SL_SW",
    "device_type_scene": "SL_SCENE",
    # AI事件测试常量
    "ai_include_devices": "ai_device",
    "ai_include_hubs": "ai_hub",
    "ai_filtered_device": "filtered_device",
    "ai_filtered_hub": "filtered_hub",
    # 测试数据标识符
    "test_data_generic": "test",
    "test_data_value": "data",
    "test_invalid_key": "invalid",
    "test_invalid_value": "data",
}

# 网络配置常量
NETWORK_CONFIG = {
    # 网络配置常量
    "test_ip": "192.168.1.100",
    "test_port": 3000,
    "alt_port": 8888,
    "local_port": 8080,
    "test_username": "admin",
    "test_password": "admin_password",
    # 认证令牌常量
    "new_token": "newly_fetched_token",
    "existing_token": "existing_token",
    "test_token": "test_token",
    "original_token": "original_token",
    "invalid_token": "invalid_token",
    "any_token": "any_token",
    "new_password": "new_password",
    "mock_password": "mock_password",
    "wrong_password": "wrong_password",
    "wrong_new_password": "wrong_new_password",
    "test_password_auth": "test_password",
    # 测试条目ID常量
    "cloud_entry_id": "test_entry_cloud",
    "reauth_entry_id": "test_reauth",
    "options_entry_id": "test_options",
    "auth_token_entry_id": "test_auth_token",
    "auth_password_entry_id": "test_auth_password",
    "unique_test_id": "test_unique_id",
    "mock_entry_id_12345": "mock_entry_id_12345",
    "non_existent_entry_id": "non_existent_entry_id",
    # 连接类型标识符
    "cloud_connection": "cloud_push",
    "local_connection": "local_push",
    # 认证方法标识符
    "token_auth_method": "token",
    "password_auth_method": "password",
    # 用户和服务标识符
    "test_user_source": "user",
    "normalized_user_id": "normalized_user_id",
    "original_user_id": "original_user_id",
    "test_device_id": "test_device",
    # 标题格式常量
    "local_hub_title_format": "Local Hub ({})",  # 用于格式化本地Hub标题
}
