"""
共用的测试辅助函数。

此模块包含在多个测试文件中重复使用的辅助函数，避免代码重复。
"""

from unittest.mock import AsyncMock, MagicMock

from homeassistant import config_entries
from homeassistant.const import CONF_REGION
from homeassistant.const import CONF_TYPE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from custom_components.lifesmart.const import (
    DEVICE_ID_KEY,
    CONF_LIFESMART_APPKEY,
    CONF_LIFESMART_APPTOKEN,
    CONF_LIFESMART_USERID,
    CONF_LIFESMART_USERTOKEN,
    DYN_EFFECT_MAP,
)


def get_entity_unique_id(hass: HomeAssistant, entity_id: str) -> str:
    """
    通过 entity_id 获取实体的 unique_id。

    Args:
        hass: Home Assistant 实例。
        entity_id: 实体的 ID。

    Returns:
        实体的 unique_id。

    Raises:
        AssertionError: 如果实体在注册表中未找到。
    """
    entity_registry = async_get_entity_registry(hass)
    entry = entity_registry.async_get(entity_id)
    assert entry is not None, f"实体 {entity_id} 未在注册表中找到"
    return entry.unique_id


def find_test_device(devices: list, me: str):
    """
    测试专用辅助函数，用于从模拟设备列表中通过 'me' ID 查找设备。

    Args:
        devices: 包含模拟设备字典的列表。
        me: 要查找的设备的 'me' 标识符。

    Returns:
        找到的设备字典，或在未找到时返回 None。
    """
    return next((d for d in devices if d.get(DEVICE_ID_KEY) == me), None)


# ============================================================================
# === Mock创建工厂函数 ===
# ============================================================================


def create_mock_oapi_client():
    """创建正确配置的OAPI客户端mock，区分同步和异步方法。"""
    mock_client = MagicMock()

    # 异步方法使用AsyncMock
    mock_client.async_refresh_token = AsyncMock()
    mock_client.async_get_all_devices = AsyncMock()
    mock_client.login_async = AsyncMock()

    # 同步方法使用普通Mock（返回值）
    mock_client.get_wss_url = MagicMock(return_value="wss://test.com/ws")
    mock_client.generate_wss_auth = MagicMock(return_value='{"auth": "test"}')

    return mock_client


def create_mock_config_data():
    """
    创建标准的模拟配置数据。

    返回一套标准的云端模式配置信息，用于在测试中创建 MockConfigEntry。
    这确保了所有测试都使用一致的凭据，简化了测试的编写。
    """
    return {
        CONF_TYPE: config_entries.CONN_CLASS_CLOUD_PUSH,  # 明确设置为云端模式
        CONF_LIFESMART_APPKEY: "mock_appkey",
        CONF_LIFESMART_APPTOKEN: "mock_apptoken",
        CONF_LIFESMART_USERID: "mock_userid",
        CONF_LIFESMART_USERTOKEN: "mock_usertoken",
        CONF_REGION: "cn2",
    }


def create_mock_lifesmart_devices():
    """
    创建一个全面的模拟设备列表，覆盖所有平台的测试需求。

    这个函数提供了一个包含各种设备类型（开关、灯、传感器、温控器等）的列表，
    模拟了一个真实用户的完整家庭环境。

    用途:
    - 用于集成测试，以在 Home Assistant 中创建所有这些设备对应的实体。
    - 用于测试平台级别的功能，例如，确保 climate 平台在初始化时不会错误地创建 switch 实体。
    - 用于测试设备排除逻辑。
    """
    return [
        # --- Switch Devices ---
        # 1. 标准三路开关 (SUPPORTED_SWITCH_TYPES)
        {
            "agt": "hub_sw",
            "me": "sw_if3",
            "devtype": "SL_SW_IF3",
            "name": "3-Gang Switch",
            "data": {"L1": {"type": 129}, "L2": {"type": 128}, "L3": {"type": 129}},
        },
        # 2. 普通插座 (SMART_PLUG_TYPES)
        {
            "agt": "hub_sw",
            "me": "sw_ol",
            "devtype": "SL_OL",
            "name": "Smart Outlet",
            "data": {"O": {"type": 129}},
        },
        # 2.1. 入墙插座 (SL_OL_W) - 现在归类为插座而非灯光
        {
            "agt": "hub_sw",
            "me": "wall_outlet",
            "devtype": "SL_OL_W",
            "name": "Wall Outlet",
            "data": {"P1": {"type": 129}},
        },
        # 3. 计量插座 (POWER_METER_PLUG_TYPES) - 位于被排除的 hub
        {
            "agt": "excluded_hub",
            "me": "sw_oe3c",
            "devtype": "SL_OE_3C",
            "name": "Power Plug",
            "data": {"P1": {"type": 129}, "P4": {"type": 128}},
        },
        # 4. 超能面板开关版 (SL_NATURE)
        {
            "agt": "hub_sw",
            "me": "sw_nature",
            "devtype": "SL_NATURE",
            "name": "Nature Panel Switch",
            "data": {
                "P1": {"type": 129},
                "P2": {"type": 128},
                "P3": {"type": 129},
                "P5": {"val": 1},  # P5=1 表示其为开关模式
            },
        },
        # 5 通用控制器（三路开关模式）
        {
            "agt": "hub_sw",
            "me": "generic_p_switch_mode",
            "devtype": "SL_P",
            "name": "Generic Controller Switch",
            "data": {
                "P1": {"val": (8 << 24)},  # Mode 8: 3-way switch
                "P2": {"type": 129},
                "P3": {"type": 128},
                "P4": {"type": 129},
            },
        },
        # 6. 九路开关控制器 (SL_P_SW)
        {
            "agt": "hub_sw",
            "me": "sw_p9",
            "devtype": "SL_P_SW",
            "name": "9-Way Controller",
            "data": {
                "P1": {"type": 129},
                "P2": {"type": 128},
                "P3": {"type": 129},
                "P4": {"type": 128},
                "P5": {"type": 129},
                "P6": {"type": 128},
                "P7": {"type": 129},
                "P8": {"type": 128},
                "P9": {"type": 129},
                "P10": {"type": 128},
            },
        },
        # --- Light Devices ---
        # 1. BRIGHTNESS_LIGHT_TYPES -> SL_SPWM
        {
            "agt": "hub_light",
            "me": "light_bright",
            "devtype": "SL_SPWM",
            "name": "Brightness Light",
            "data": {"P1": {"type": 129, "val": 100}},
        },
        # 2. LIGHT_DIMMER_TYPES -> SL_LI_WW_V2
        {
            "agt": "hub_light",
            "me": "light_dimmer",
            "devtype": "SL_LI_WW_V2",
            "name": "Dimmer Light",
            "data": {"P1": {"type": 129, "val": 100}, "P2": {"val": 27}},
        },
        # 3. QUANTUM_TYPES -> OD_WE_QUAN
        {
            "agt": "hub_light",
            "me": "light_quantum",
            "devtype": "OD_WE_QUAN",
            "name": "Quantum Light",
            "data": {"P1": {"type": 129, "val": 100}, "P2": {"val": 0x01010203}},
        },
        # 4. RGB_LIGHT_TYPES -> SL_SC_RGB
        {
            "agt": "hub_light",
            "me": "light_singlergb",
            "devtype": "SL_SC_RGB",
            "name": "Single IO RGB Light",
            "data": {"RGB": {"type": 129, "val": 0x64010203}},
        },
        # 5. RGBW_LIGHT_TYPES -> SL_CT_RGBW
        {
            "agt": "hub_light",
            "me": "light_dualrgbw",
            "devtype": "SL_CT_RGBW",
            "name": "Dual IO RGBW Light",
            "data": {"RGBW": {"type": 129, "val": 0}, "DYN": {"type": 128}},
        },
        # 6. SPOT_TYPES -> SL_SPOT (RGB)
        {
            "agt": "hub_light",
            "me": "light_spotrgb",
            "devtype": "SL_SPOT",
            "name": "SPOT RGB Light",
            "data": {"RGB": {"type": 129, "val": 0xFF8040}},
        },
        # 7. SPOT_TYPES -> MSL_IRCTL (RGBW)
        {
            "agt": "hub_light",
            "me": "light_spotrgbw",
            "devtype": "MSL_IRCTL",
            "name": "SPOT RGBW Light",
            "data": {
                "RGBW": {"type": 129, "val": 0x11223344},
                "DYN": {"type": 129, "val": DYN_EFFECT_MAP["海浪"]},
            },
        },
        # 8. GARAGE_DOOR_TYPES -> SL_ETDOOR
        {
            "agt": "hub_light",
            "me": "light_cover",
            "devtype": "SL_ETDOOR",
            "name": "Cover Light",
            "data": {"P1": {"type": 129}},
        },
        # 9. SL_OL_W 已移动到插座类型，此处删除灯光设备定义
        # 10. 简单灯泡类型已删除，因为LIGHT_BULB_TYPES不存在
        # 11. OUTDOOR_LIGHT_TYPES -> SL_LI_UG1
        {
            "agt": "hub_light",
            "me": "light_outdoor",
            "devtype": "SL_LI_UG1",
            "name": "Outdoor Light",
            "data": {"P1": {"type": 129, "val": 0x64010203}},
        },
        # --- Binary Sensor Devices ---
        {
            "agt": "hub_bs",
            "me": "bs_door",
            "devtype": "SL_SC_G",
            "name": "Front Door",
            "data": {"G": {"val": 0, "type": 0}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_motion",
            "devtype": "SL_SC_MHW",
            "name": "Living Motion",
            "data": {"M": {"val": 1, "type": 0}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_water",
            "devtype": "SL_SC_WA",
            "name": "Kitchen Water",
            "data": {"WA": {"val": 50, "type": 0}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_defed",
            "devtype": "SL_DF_MM",
            "name": "Garage DEFED",
            "data": {"M": {"val": 1, "type": 129}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_lock",
            "devtype": "SL_LK_LS",
            "name": "Main Lock",
            "data": {"EVTLO": {"val": 4121, "type": 1}, "ALM": {"val": 2}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_smoke",
            "devtype": "SL_P_A",
            "name": "Hallway Smoke",
            "data": {"P1": {"val": 1, "type": 0}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_radar",
            "devtype": "SL_P_RM",
            "name": "Study Occupancy",
            "data": {"P1": {"val": 1, "type": 0}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_button",
            "devtype": "SL_SC_BB_V2",
            "name": "Panic Button",
            "data": {"P1": {"val": 0, "type": 0}},
        },
        # --- Sensor Devices ---
        {
            "agt": "hub_sensor",
            "me": "sensor_env",
            "devtype": "SL_SC_THL",
            "name": "Living Room Env",
            "data": {
                "T": {"v": 25.5},
                "H": {"v": 60.1},
                "Z": {"v": 1000},
                "V": {"val": 95},
            },
        },
        {
            "agt": "hub_sensor",
            "me": "sensor_co2",
            "devtype": "SL_SC_CA",
            "name": "Study CO2",
            "data": {"P3": {"val": 800}},
        },
        {
            "agt": "hub_sensor",
            "me": "sensor_power_plug",
            "devtype": "SL_OE_3C",
            "name": "Washing Machine Plug",
            "data": {"P2": {"v": 1.5}, "P3": {"v": 1200}},
        },
        {
            "agt": "hub_sensor",
            "me": "sensor_lock_battery",
            "devtype": "SL_LK_LS",
            "name": "Main Door Lock",
            "data": {"BAT": {"val": 88}},
        },
        {
            "agt": "hub_sensor",
            "me": "sensor_boundary",
            "devtype": "SL_SC_THL",
            "name": "Boundary Test Sensor",
            "data": {"T": {"val": 0}, "H": {}, "Z": {"val": "invalid_string"}},
        },
        # --- Cover Devices ---
        {
            "agt": "hub_cover",
            "me": "cover_garage",
            "devtype": "SL_ETDOOR",
            "name": "Garage Door",
            "data": {"P2": {"val": 0, "type": 128}},
        },
        {
            "agt": "hub_cover",
            "me": "cover_dooya",
            "devtype": "SL_DOOYA",
            "name": "Living Room Curtain",
            "data": {"P1": {"val": 100, "type": 128}},
        },
        {
            "agt": "hub_cover",
            "me": "cover_nonpos",
            "devtype": "SL_SW_WIN",
            "name": "Bedroom Curtain",
            "data": {"OP": {"type": 128}, "CL": {"type": 128}, "ST": {"type": 128}},
        },
        {
            "agt": "hub_cover",
            "me": "cover_generic",
            "devtype": "SL_P",
            "name": "Generic Controller Curtain",
            "data": {
                "P1": {"val": (2 << 24)},
                "P2": {"type": 128},
                "P3": {"type": 128},
                "P4": {"type": 128},
            },
        },
        # --- Climate Devices ---
        {
            "agt": "hub_climate",
            "me": "climate_nature_thermo",
            "devtype": "SL_NATURE",
            "name": "Nature Panel Thermo",
            "data": {
                "P1": {"type": 129, "val": 1},  # On
                "P4": {"v": 28.0},  # Current Temp
                "P5": {"val": 3},  # 关键：标识为温控面板
                "P6": {"val": (4 << 6)},  # CFG, 4 -> ⻛机盘管（双阀）模式
                "P7": {"val": 1},  # Mode, 1 -> Auto
                "P8": {"v": 26.0},  # Target Temp
                "P10": {"val": 15},  # Fan Speed, 15 -> Low
            },
        },
        {
            "agt": "hub_climate",
            "me": "climate_floor_heat",
            "devtype": "SL_CP_DN",
            "name": "Floor Heating",
            "data": {
                "P1": {"type": 1, "val": 2147483648},
                "P3": {"v": 25.0},
                "P4": {"v": 22.5},
            },
        },
        {
            "agt": "hub_climate",
            "me": "climate_fancoil",
            "devtype": "SL_CP_AIR",
            "name": "Fan Coil Unit",
            "data": {
                "P1": {"type": 1, "val": (1 << 15) | (1 << 13)},
                "P4": {"v": 24.0},
                "P5": {"v": 26.0},
            },
        },
        {
            "agt": "hub_climate",
            "me": "climate_airpanel",
            "devtype": "V_AIR_P",
            "name": "Air Panel",
            "data": {
                "O": {"type": 0},
                "MODE": {"val": 1},
                "F": {"val": 2},
                "T": {"v": 23.0},
                "tT": {"v": 25.0},
            },
        },
        {
            "agt": "hub_climate",
            "me": "climate_airsystem",
            "devtype": "SL_TR_ACIPM",
            "name": "Air System",
            "data": {"P1": {"type": 1, "val": 1}},
        },
        # --- Devices for Exclusion/Special Tests ---
        {
            "agt": "hub_bs",
            "me": "excluded_device",
            "devtype": "SL_SC_G",
            "name": "Excluded Sensor",
            "data": {"G": {"v": 20}},
        },
        {
            "agt": "excluded_hub",
            "me": "device_on_excluded_hub",
            "devtype": "SL_SC_THL",
            "name": "Sensor on Excluded Hub",
            "data": {"T": {"v": 21}},
        },
    ]


# ============================================================================
# === 专用设备数据创建函数 ===
# ============================================================================


def create_mock_device_climate_fancoil() -> dict:
    """
    创建一个标准的风机盘管设备 (SL_CP_AIR) 的模拟数据。

    此设备的状态由一个位掩码 (bitmask) `P1` 控制，这是测试的重点。
    - 初始状态: 制热模式 (Heat) + 低风速 (Low)。
      - `val` 的第 13 位为 1: 代表制热模式 (HEAT)。
      - `val` 的第 15 位为 1: 代表低风速 (FAN_LOW)。
      - 计算: `(1 << 15) | (1 << 13)`
    - 初始温度:
      - `P4`: 目标温度 (target_temperature) 为 24.0。
      - `P5`: 当前温度 (current_temperature) 为 26.0。
    """
    return {
        "agt": "hub_climate",
        "me": "climate_fancoil",
        "devtype": "SL_CP_AIR",
        "name": "Fan Coil Unit",
        "data": {
            "P1": {"type": 1, "val": (1 << 15) | (1 << 13)},
            "P4": {"v": 24.0},
            "P5": {"v": 26.0},
        },
    }


def create_mock_device_spot_rgb_light() -> dict:
    """
    创建一个 SPOT RGB 灯 (SL_SPOT) 的模拟数据。

    - 初始状态: 开，颜色为 (255, 128, 64)。
      - `val` 为 `0xFF8040`。
    """
    return {
        "agt": "hub_light",
        "me": "light_spotrgb",
        "devtype": "SL_SPOT",
        "name": "SPOT RGB Light",
        "data": {"RGB": {"type": 129, "val": 0xFF8040}},
    }


def create_mock_device_dual_io_rgbw_light() -> dict:
    """
    创建一个双 IO 口 RGBW 灯 (SL_CT_RGBW) 的模拟数据。

    - 初始状态: 开，但颜色和效果均未激活。
      - `RGBW` 口为开 (`type: 129`)，但值为 0。
      - `DYN` 口为关 (`type: 128`)。
    """
    return {
        "agt": "hub_light",
        "me": "light_dualrgbw",
        "devtype": "SL_CT_RGBW",
        "name": "Dual IO RGBW Light",
        "data": {"RGBW": {"type": 129, "val": 0}, "DYN": {"type": 128}},
    }


def create_mock_device_single_io_rgb_light() -> dict:
    """
    创建一个单 IO 口 RGB 灯 (SL_SC_RGB) 的模拟数据。

    此函数用于对该特定设备类型的协议进行精确测试。
    - 初始状态: 开，颜色为 (1, 2, 3)，亮度为 100%。
      - `val` 为 `0x64010203` (亮度100, R=1, G=2, B=3)。
    """
    return {
        "agt": "hub_light",
        "me": "light_singlergb",
        "devtype": "SL_SC_RGB",
        "name": "Single IO RGB Light",
        "data": {"RGB": {"type": 129, "val": 0x64010203}},
    }
