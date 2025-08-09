"""
测试工厂函数，用于创建模拟对象和测试数据。

此模块包含：
1. Mock对象工厂函数（OAPI客户端、配置数据等）
2. 设备数据工厂函数（按类别组织的完整设备列表）

所有工厂函数都基于LifeSmart智慧设备规格属性说明文档和const.py中的设备分类。
"""

from unittest.mock import AsyncMock, MagicMock

from homeassistant import config_entries
from homeassistant.const import CONF_REGION, CONF_TYPE

from custom_components.lifesmart.core.const import (
    CONF_LIFESMART_APPKEY,
    CONF_LIFESMART_APPTOKEN,
    CONF_LIFESMART_USERID,
    CONF_LIFESMART_USERTOKEN,
)
from custom_components.lifesmart.core.devices import (
    DYN_EFFECT_MAP,
)
from .constants import (
    DEFAULT_TEST_VALUES,
    SPECIALIZED_TEST_DEVICE_IDS,
    STANDARD_CONFIG_FIELDS,
    VIRTUAL_TEST_DEVICES,
)
from .helpers import get_hub_id, validate_device_data


# ============================================================================
# === Mock对象工厂函数 ===
# ============================================================================


def create_mock_oapi_client(*, spec=None):
    """
    创建正确配置的OAPI客户端mock，区分同步和异步方法。

    Args:
        spec: 可选的spec类，用于限制mock的属性和方法

    Returns:
        MagicMock: 配置好的OAPI客户端mock对象
    """
    # 创建带有spec的mock客户端
    mock_client = MagicMock(spec=spec) if spec else MagicMock()

    # 异步方法使用AsyncMock
    mock_client.async_refresh_token = AsyncMock()
    mock_client.async_get_all_devices = AsyncMock()
    mock_client.login_async = AsyncMock()

    # 同步方法使用普通Mock（返回值）
    mock_client.get_wss_url = MagicMock(return_value=DEFAULT_TEST_VALUES["wss_url"])
    mock_client.generate_wss_auth = MagicMock(
        return_value=DEFAULT_TEST_VALUES["wss_auth"]
    )

    # 设置默认的成功响应
    mock_client.async_refresh_token.return_value = True
    mock_client.async_get_all_devices.return_value = []
    mock_client.login_async.return_value = True

    return mock_client


def create_mock_config_data():
    """
    创建标准的模拟配置数据。

    Returns:
        dict: 标准的LifeSmart集成配置数据
    """
    return {
        CONF_TYPE: config_entries.CONN_CLASS_CLOUD_PUSH,
        CONF_LIFESMART_APPKEY: DEFAULT_TEST_VALUES["appkey"],
        CONF_LIFESMART_APPTOKEN: DEFAULT_TEST_VALUES["apptoken"],
        CONF_LIFESMART_USERID: DEFAULT_TEST_VALUES["userid"],
        CONF_LIFESMART_USERTOKEN: DEFAULT_TEST_VALUES["usertoken"],
        CONF_REGION: DEFAULT_TEST_VALUES["region"],
    }


def create_mock_oapi_client_with_devices(devices_list=None):
    """
    创建带有预配置设备列表的OAPI客户端mock。

    Args:
        devices_list: 可选的设备列表，如果未提供则使用空列表

    Returns:
        MagicMock: 配置好的OAPI客户端mock对象
    """
    mock_client = create_mock_oapi_client()

    if devices_list is None:
        devices_list = []

    mock_client.async_get_all_devices.return_value = devices_list
    return mock_client


def create_mock_failed_oapi_client():
    """
    创建模拟失败场景的OAPI客户端mock。

    Returns:
        MagicMock: 配置为失败响应的OAPI客户端mock对象
    """
    mock_client = create_mock_oapi_client()

    # 设置失败响应
    mock_client.async_refresh_token.return_value = False
    mock_client.login_async.return_value = False
    mock_client.async_get_all_devices.side_effect = Exception("Connection failed")

    return mock_client


# ============================================================================
# === 设备数据工厂函数 ===
# ============================================================================

# ================= 插座系列 (Outlet/Plug Series) =================


def create_smart_plug_devices():
    """创建智慧插座设备的模拟数据列表 - 基于LifeSmart智慧设备规格属性说明文档。"""
    devices = [
        # 基于文档2.1.1的SL_OL真实规格
        {
            "agt": get_hub_id(0),  # 使用第一个hub ID
            "me": "sw_ol",  # 友好设备ID，用于测试
            "devtype": "SL_OL",
            "name": "Smart Outlet",
            "data": {"O": {"type": 129, "val": 1}},  # 开启状态，符合文档规范
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


def create_power_meter_plug_devices():
    """创建计量插座设备的模拟数据列表 - 基于LifeSmart智慧设备规格属性说明文档2.1.2。"""
    devices = [
        # 基于文档2.1.2的SL_OE_3C真实规格
        {
            "agt": get_hub_id(1),  # 使用第二个hub ID
            "me": "sensor_power_plug",  # 友好设备ID，用于测试
            "devtype": "SL_OE_3C",
            "name": "Washing Machine Plug",
            "data": {
                "P1": {"type": 129, "val": 1},  # 开关状态
                "P2": {"v": 1.5, "val": 1084227584},  # 累计用电量 IEEE754
                "P3": {"v": 1200.0, "val": 1149239296},  # 当前功率 IEEE754
                "P4": {"type": 128, "val": 3000},  # 功率门限
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


# ================= 开关系列 (Switch Series) =================


def create_traditional_switch_devices():
    """创建传统开关设备的模拟数据列表 - 基于LifeSmart智慧设备规格属性说明文档2.2.1。"""
    devices = [
        # 基于文档2.2.1的SL_SW_IF3真实规格
        {
            "agt": get_hub_id(1),  # 使用不同的hub ID
            "me": "sw_if3",  # 友好设备ID，用于测试
            "devtype": "SL_SW_IF3",
            "fullCls": "SL_SW_IF3_V2",
            "name": "smart Switch",  # 文档中的真实名称
            "data": {
                "L1": {"type": 129, "val": 1, "name": "Living", "v": 1},
                "L2": {"type": 128, "val": 0, "name": "study", "v": 0},
                "L3": {"type": 129, "val": 1, "name": "Kid", "v": 1},
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 添加一个额外的SL_SW_IF3设备，用于特定测试
        {
            "agt": get_hub_id(1),
            "me": "if3b2",  # 用于test_helpers.py中的特定测试
            "devtype": "SL_SW_IF3",
            "fullCls": "SL_SW_IF3_V2",
            "name": "Test Switch IF3B2",
            "data": {
                "L1": {"type": 129, "val": 1, "name": "TestL1", "v": 1},
                "L2": {"type": 128, "val": 0, "name": "TestL2", "v": 0},
                "L3": {"type": 129, "val": 1, "name": "TestL3", "v": 1},
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # SL_SW_IF2 - 双联开关
        {
            "agt": get_hub_id(1),  # 使用相同的hub ID
            "me": "2d12",
            "devtype": "SL_SW_IF2",
            "fullCls": "SL_SW_IF2_V2",
            "name": "Dual Switch",
            "data": {
                "L1": {"type": 129, "val": 1, "name": "Room1", "v": 1},
                "L2": {"type": 128, "val": 0, "name": "Room2", "v": 0},
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # SL_SW_IF1 - 单联开关
        {
            "agt": get_hub_id(1),
            "me": "2d13",
            "devtype": "SL_SW_IF1",
            "fullCls": "SL_SW_IF1_V2",
            "name": "Single Switch",
            "data": {
                "L1": {"type": 129, "val": 1, "name": "MainLight", "v": 1},
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # SL_SW_ND3 - 恒星/辰星/极星开关三联
        {
            "agt": get_hub_id(1),
            "me": "3e22",
            "devtype": "SL_SW_ND3",
            "fullCls": "SL_SW_ND3_V2",
            "name": "Star Switch Triple",
            "data": {
                "P1": {"type": 129, "val": 1, "v": 1},
                "P2": {"type": 128, "val": 0, "v": 0},
                "P3": {"type": 129, "val": 1, "v": 1},
                "P4": {"val": 3000, "v": 85},  # 电量百分比
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # SL_SW_ND2 - 恒星/辰星/极星开关双联
        {
            "agt": get_hub_id(1),
            "me": "3e23",
            "devtype": "SL_SW_ND2",
            "fullCls": "SL_SW_ND2_V2",
            "name": "Star Switch Dual",
            "data": {
                "P1": {"type": 129, "val": 1, "v": 1},
                "P2": {"type": 128, "val": 0, "v": 0},
                "P3": {"val": 3200, "v": 90},  # 电量百分比
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # SL_SW_ND1 - 恒星/辰星/极星开关单联
        {
            "agt": get_hub_id(1),
            "me": "3e24",
            "devtype": "SL_SW_ND1",
            "fullCls": "SL_SW_ND1_V2",
            "name": "Star Switch Single",
            "data": {
                "P1": {"type": 129, "val": 1, "v": 1},
                "P2": {"val": 3400, "v": 95},  # 电量百分比
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


def create_advanced_switch_devices():
    """创建高级开关设备的模拟数据列表 - 基于LifeSmart智慧设备规格属性说明文档2.2.3。"""
    devices = [
        # 基于文档2.2.3的SL_P_SW九路开关控制器真实规格
        {
            "agt": get_hub_id(2),  # Advanced switches
            "me": "sw_p9",  # 友好设备ID，用于测试
            "devtype": "SL_P_SW",
            "name": "9-Way Controller",
            "data": {
                "P1": {"type": 129, "val": 1},
                "P2": {"type": 128, "val": 0},
                "P3": {"type": 129, "val": 1},
                "P4": {"type": 128, "val": 0},
                "P5": {"type": 129, "val": 1},
                "P6": {"type": 128, "val": 0},
                "P7": {"type": 129, "val": 1},
                "P8": {"type": 128, "val": 0},
                "P9": {"type": 129, "val": 1},
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.10.1的SL_P通用控制器真实规格 (开关模式)
        {
            "agt": get_hub_id(2),  # Advanced switches
            "me": "generic_p_switch_mode",  # 友好设备ID，用于测试
            "devtype": "SL_P",
            "name": "Generic Controller Switch",
            "data": {
                "P1": {"val": (8 << 24)},  # Mode 8: 3-way switch
                "P2": {"type": 129, "val": 1},
                "P3": {"type": 128, "val": 0},
                "P4": {"type": 129, "val": 1},
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.14.1的SL_NATURE超能面板真实规格 (开关版)
        {
            "agt": get_hub_id(2),  # Advanced switches
            "me": "sw_nature",  # 友好设备ID，用于测试
            "devtype": "SL_NATURE",
            "name": "Nature Panel Switch",
            "data": {
                "P1": {"type": 129, "val": 1},
                "P2": {"type": 128, "val": 0},
                "P3": {"type": 129, "val": 1},
                "P5": {"val": 1},  # P5=1 表示开关面板
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.2.5的SL_SW_DM1动态调光开关真实规格
        {
            "agt": get_hub_id(2),  # Advanced switches
            "me": "4f5g",
            "devtype": "SL_SW_DM1",
            "fullCls": "SL_SW_DM1_V1",  # 文档中的版本标识
            "name": "Dimmer Motion Controller",
            "data": {
                "P1": {"type": 129, "val": 200},  # 开关状态+亮度值[0-255    ]
                "P2": {
                    "type": 129,
                    "val": 12825,
                },  # 指示灯亮度 (bit8-15:开启亮度=50, bit0-7:关闭亮度=25)
                "P3": {"val": 1},  # 移动检测: 1=检测到移动
                "P4": {"val": 350},  # 环境光照值(lux)
                "P5": {"val": 0b00000000},  # 调光设置: 自动模式+8倍速度+高灵敏度
                "P6": {"val": 30},  # 动态设置值
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # SL_SW_RC - 极星开关(零火版)
        {
            "agt": get_hub_id(2),  # Advanced switches
            "me": "6h7i",
            "devtype": "SL_SW_RC",
            "name": "Polar Switch RC",
            "data": {
                "L1": {"type": 129, "val": 1},
                "L2": {"type": 128, "val": 0},
                "L3": {"type": 129, "val": 1},
                "dark": {"type": 129, "val": 512},  # 关状态指示灯亮度[0-1023]
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # SL_SF_RC - 单火触摸开关/入墙开关 - 基于官方文档2.2.1规格
        {
            "agt": get_hub_id(2),  # Advanced switches
            "me": "9k0l",
            "devtype": "SL_SF_RC",
            "name": "Single Fire Touch Switch",
            "data": {
                "L1": {"type": 129, "val": 1},  # 第一路开关控制口
                "L2": {"type": 128, "val": 0},  # 第二路开关控制口
                "L3": {"type": 129, "val": 1},  # 第三路开关控制口
                "dark": {"type": 129, "val": 256},  # 关状态时指示灯亮度[0-1023]
                "bright": {"type": 129, "val": 768},  # 开状态时指示灯亮度[0-1023]
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # SL_SW_NS3 - 星玉开关(Nature Switch)
        {
            "agt": get_hub_id(2),  # Advanced switches
            "me": "8j9k",
            "devtype": "SL_SW_NS3",
            "name": "Nature Switch Triple",
            "data": {
                "L1": {"type": 129, "val": 1},
                "L2": {"type": 128, "val": 0},
                "L3": {"type": 129, "val": 1},
                "dark1": {"type": 129, "val": 0xFF0000},  # Red色指示灯
                "dark2": {"type": 128, "val": 0x00FF00},  # Green色指示灯
                "dark3": {"type": 129, "val": 0x0000FF},  # Blue色指示灯
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # SL_SW_MJ3 - 奇点开关模块(CUBE Switch Module)
        {
            "agt": get_hub_id(2),  # Advanced switches
            "me": "0l1m",
            "devtype": "SL_SW_MJ3",
            "name": "CUBE Switch Module Triple",
            "data": {
                "P1": {"type": 129, "val": 1},
                "P2": {"type": 128, "val": 0},
                "P3": {"type": 129, "val": 1},
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # SL_SW_MJ2 - 奇点开关模块(双路)
        {
            "agt": get_hub_id(2),  # Advanced switches
            "me": "2n3o",
            "devtype": "SL_SW_MJ2",
            "name": "CUBE Switch Module Dual",
            "data": {
                "P1": {"type": 129, "val": 1},
                "P2": {"type": 128, "val": 0},
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # SL_SW_DM1_V2 - 星玉调光开关(可控硅版) - 基础调光功能
        {
            "agt": get_hub_id(2),  # Advanced switches
            "me": "0v1w",
            "devtype": "SL_SW_DM1",
            "fullCls": "SL_SW_DM1_V2",  # V2版本标识
            "name": "Jade Triac Dimmer Switch",
            "data": {
                "P1": {"type": 129, "val": 180},  # 开关状态+亮度值[0-255]
                "P2": {
                    "type": 129,
                    "val": 8960,
                },  # 指示灯亮度 (bit8-15:开启亮度=35, bit0-7:关闭亮度=0)
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # SL_MC_ND1 - 恒星/辰星/极星开关伴侣(单键)
        {
            "agt": get_hub_id(2),  # Advanced switches
            "me": "4p5q",
            "devtype": "SL_MC_ND1",
            "name": "Star Switch Companion Single",
            "data": {
                "P1": {"type": 129, "val": 1, "v": 1},  # 第一路开关控制口
                "P2": {"val": 3200, "v": 88},  # 电量监测: 原始电压值3200, 88%电量
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # SL_MC_ND2 - 恒星/辰星/极星开关伴侣(双键)
        {
            "agt": get_hub_id(2),  # Advanced switches
            "me": "6r7s",
            "devtype": "SL_MC_ND2",
            "name": "Star Switch Companion Dual",
            "data": {
                "P1": {"type": 129, "val": 1, "v": 1},  # 第一路开关控制口
                "P2": {"type": 128, "val": 0, "v": 0},  # 第二路开关控制口
                "P3": {"val": 3100, "v": 85},  # 电量监测: 原始电压值3100, 85%电量
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # SL_MC_ND3 - 恒星/辰星/极星开关伴侣(三键)
        {
            "agt": get_hub_id(2),  # Advanced switches
            "me": "8t9u",
            "devtype": "SL_MC_ND3",
            "name": "Star Switch Companion Triple",
            "data": {
                "P1": {"type": 129, "val": 1, "v": 1},  # 第一路开关控制口
                "P2": {"type": 128, "val": 0, "v": 0},  # 第二路开关控制口
                "P3": {"type": 129, "val": 1, "v": 1},  # 第三路开关控制口
                "P4": {"val": 3300, "v": 92},  # 电量监测: 原始电压值3300, 92%电量
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


# ================= 灯光系列 (Light Series) =================


def create_dimmer_light_devices():
    """创建调光调色灯设备的模拟数据列表 - 基于LifeSmart智慧设备规格属性说明文档2.4.3。"""
    devices = [
        # 基于文档2.4.3的SL_LI_WW白光智能灯泡真实规格
        {
            "agt": get_hub_id(3),  # Dimmer lights
            "me": "light_bright",  # 友好设备ID，用于测试
            "devtype": "SL_LI_WW",
            "name": "White Light Bulb",
            "data": {"P1": {"type": 129, "val": 80}},  # 亮度80%
            "stat": 1,
            "ver": "0.0.0.7",
        },
        {
            "agt": get_hub_id(3),  # Dimmer lights
            "me": "light_dimmer",  # 友好设备ID，用于测试
            "devtype": "SL_LI_WW_V1",  # SL_LI_WW_V1:智能灯泡(冷暖白)
            "name": "Smart Bulb Cool Warm",
            "data": {
                "P1": {"type": 129, "val": 100},  # 亮度100%
                "P2": {"val": 27},  # 色温
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        {
            "agt": get_hub_id(3),  # Dimmer lights
            "me": "7d1c",
            "devtype": "SL_LI_WW_V2",  # SL_LI_WW_V2:调光调色智控器(0-10V)
            "name": "Dimmer Controller 0-10V",
            "data": {
                "P1": {"type": 129, "val": 75},
                "P2": {"val": 35},
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


def create_rgb_light_devices():
    """创建RGB/RGBW灯光设备的模拟数据列表 - 基于LifeSmart智慧设备规格属性说明文档2.4.1。"""
    devices = [
        # 基于文档2.4.1的SL_SC_RGB幻彩灯带(不带白光)真实规格
        {
            "agt": get_hub_id(4),  # RGB lights
            "me": "6c0b",
            "devtype": "SL_SC_RGB",
            "name": "RGB Light Strip",
            "data": {"RGB": {"type": 129, "val": 0xFF0000}},  # 红色
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.4.1的SL_CT_RGBW幻彩灯带真实规格
        {
            "agt": get_hub_id(4),  # RGB lights
            "me": "5b9a",
            "devtype": "SL_CT_RGBW",
            "name": "RGBW Light Strip",
            "data": {
                "RGBW": {"type": 129, "val": 0x00FF0000},  # 绿色
                "DYN": {"type": 128, "val": 0},
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.4.1的SL_LI_RGBW胶囊灯泡真实规格
        {
            "agt": get_hub_id(4),  # RGB lights
            "me": "4a89",
            "devtype": "SL_LI_RGBW",
            "name": "RGBW Light Bulb",
            "data": {
                "RGBW": {"type": 129, "val": 0x0000FF00},  # 蓝色
                "DYN": {"type": 129, "val": DYN_EFFECT_MAP.get("彩虹", 1)},
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # SL_SW_WW - 星玉调光开关(可控硅)
        {
            "agt": get_hub_id(4),  # RGB lights
            "me": "3p9q",
            "devtype": "SL_SW_WW",
            "fullCls": "SL_SW_WW_V1",
            "name": "Jade Dimmer Switch",
            "data": {
                "P1": {"type": 129, "val": 200},  # 亮度控制[0-255    ]
                "P2": {"val": 128},  # 色温控制[0-255], 128=中性色温
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # SL_LI_GD1 - 调光壁灯
        {
            "agt": get_hub_id(4),  # RGB lights
            "me": "2r8s",
            "devtype": "SL_LI_GD1",
            "name": "Wall Dimmer Light",
            "data": {
                "P1": {"type": 129, "val": 180},  # 开关+亮度[0-255]
                "P2": {"val": 1},  # 移动检测: 1=检测到移动
                "P3": {"val": 420},  # 环境光照值(lux)
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # SL_LI_UG1 - 花园地灯
        {
            "agt": get_hub_id(4),  # RGB lights
            "me": "1t7u",
            "devtype": "SL_LI_UG1",
            "name": "Garden Underground Light",
            "data": {
                "P1": {"type": 129, "val": 0x80FF4000},  # RGB+动态模式
                "P2": {"val": 250},  # 环境光照值(lux)
                "P3": {"val": 0},  # 充电指示: 0=未充电
                "P4": {"val": 3600, "v": 92},  # 电量: v=92%
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # SL_LI_IR - 红外吸顶灯
        {
            "agt": get_hub_id(4),  # RGB lights
            "me": "0v6w",
            "devtype": "SL_LI_IR",
            "name": "IR Ceiling Light",
            "data": {
                "P3": {"val": 127},  # 夜灯亮度控制: 127=第三档亮度
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


def create_spot_light_devices():
    """创建射灯设备的模拟数据列表 - 基于LifeSmart智慧设备规格属性说明文档2.5。"""
    devices = [
        # 基于文档2.5的MSL_IRCTL超级碗(基础版、蓝牙版)真实规格
        {
            "agt": get_hub_id(2),  # 使用不同的hub ID
            "me": "light_spotrgbw",  # 友好设备ID，用于测试
            "devtype": "MSL_IRCTL",
            "name": "Super Bowl Bluetooth",
            "data": {
                "RGBW": {"type": 129, "val": 0xFF8040FF},
                "DYN": {"type": 129, "val": DYN_EFFECT_MAP.get("海浪", 2)},
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.5的SL_SPOT超级碗(CoSS版)真实规格
        {
            "agt": get_hub_id(3),  # 使用不同的hub ID
            "me": "light_spotrgb",  # 友好设备ID，用于测试
            "devtype": "SL_SPOT",
            "name": "Super Bowl CoSS",
            "data": {
                "RGB": {"type": 129, "val": 0xFF8040},
                "P1": {"type": 129, "val": 200},  # 亮度控制
                "P2": {"val": 128},  # 色温控制
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


def create_quantum_light_devices():
    """创建量子灯设备的模拟数据列表 - 基于LifeSmart智慧设备规格属性说明文档2.4.2。"""
    devices = [
        # 基于文档2.4.2的OD_WE_QUAN量子灯真实规格 - 完整IO口
        {
            "agt": get_hub_id(4),  # 使用不同的hub ID
            "me": "light_quantum",  # 友好设备ID，用于测试
            "devtype": "OD_WE_QUAN",
            "name": "Quantum Light",
            "data": {
                "P1": {"type": 129, "val": 85},  # 亮度控制 85%
                "P2": {"val": 0x04810130},  # 颜色控制 - 马戏团效果
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


# ================= 传感器和二进制传感器系列 =================


def create_environment_sensor_devices():
    """创建环境传感器设备的模拟数据列表 - 基于LifeSmart智慧设备规格属性说明文档2.6.3。"""
    devices = [
        # 基于文档2.6.3的SL_SC_THL环境传感器真实规格
        {
            "agt": get_hub_id(5),  # 使用不同的hub ID
            "me": "sensor_env",  # 友好设备ID，用于测试
            "devtype": "SL_SC_THL",
            "name": "Living Room Env",
            "data": {
                "T": {"v": 23.5, "val": 235},  # 温度 23.5°C (原始值*10)
                "H": {"v": 65.2, "val": 652},  # 湿度 65.2% (原始值*10)
                "Z": {"v": 800, "val": 800},  # 光照 800 lux
                "V": {"val": 85},  # 电池电量 85%
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.6.3的SL_SC_BE CUBE环境传感器真实规格
        {
            "agt": get_hub_id(6),  # 使用不同的hub ID
            "me": "9f8h",
            "devtype": "SL_SC_BE",
            "name": "CUBE Env Sensor",
            "data": {
                "T": {"v": 22.8, "val": 228},  # 温度 22.8°C (原始值*10)
                "H": {"v": 58.3, "val": 583},  # 湿度 58.3% (原始值*10)
                "Z": {"v": 1200, "val": 1200},  # 光照 1200 lux
                "V": {"val": 92},  # 电池电量 92%
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.6.10的SL_SC_CA CO2传感器真实规格
        {
            "agt": get_hub_id(5),  # Environment sensors
            "me": "sensor_co2",  # 友好设备ID，用于测试
            "devtype": "SL_SC_CA",
            "name": "Study CO2",
            "data": {
                "P1": {"v": 23.2, "val": 232},  # 当前环境温度 (原始值*10)
                "P2": {"v": 55.0, "val": 550},  # 当前环境湿度 (原始值*10)
                "P3": {"v": 750, "val": 750},  # 当前CO2浓度值 ppm
                "P4": {"val": 88},  # 电量
                "P5": {"val": 450},  # USB供电电压
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.6.7的SL_SC_CQ TVOC+CO2环境传感器真实规格
        {
            "agt": get_hub_id(5),  # Environment sensors
            "me": "0i1j",
            "devtype": "SL_SC_CQ",
            "name": "TVOC CO2 Sensor",
            "data": {
                "P1": {"v": 24.1, "val": 241},  # 当前环境温度 (原始值*10)
                "P2": {"v": 62.5, "val": 625},  # 当前环境湿度 (原始值*10)
                "P3": {"v": 680, "val": 680},  # 当前CO2浓度值 ppm (良)
                "P4": {"v": 0.45, "val": 450},  # 当前TVOC浓度值 mg/m³ (原始值/1000)
                "P5": {"val": 75},  # 电量
                "P6": {"val": 520},  # USB供电电压
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.6.8的ELIQ_EM电量计量器真实规格
        {
            "agt": get_hub_id(5),  # Environment sensors
            "me": "2k3l",
            "devtype": "ELIQ_EM",
            "name": "Power Meter ELIQ",
            "data": {
                "EPA": {"val": 2500},  # 平均功率 2500W
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


def create_binary_sensor_devices():
    """创建二进制传感器设备的模拟数据列表 - 基于LifeSmart智慧设备规格属性说明文档。"""
    devices = [
        # 基于文档2.6.1的SL_SC_G门禁感应器真实规格
        {
            "agt": get_hub_id(6),  # Binary sensors
            "me": "bs_door",  # 友好设备ID，用于测试
            "devtype": "SL_SC_G",
            "name": "Door Sensor",
            "data": {
                "G": {"val": 0, "type": 0},  # 关闭状态 (0:打开, 1:关闭)
                "V": {"val": 92},  # 电池电量
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.6.1的SL_SC_BG CUBE门禁感应器真实规格
        {
            "agt": get_hub_id(6),  # Binary sensors
            "me": "4m5n",
            "devtype": "SL_SC_BG",
            "name": "CUBE Door Sensor",
            "data": {
                "G": {"val": 1, "type": 0},  # 关闭状态 (0:打开, 1:关闭)
                "V": {"val": 86},  # 电池电量
                "KB": {"val": 0},  # 按键状态 (0:未按下, 1:按下)
                "AXS": {"val": 0},  # 震动状态 (0:无震动, 非0:震动)
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.6.1的SL_SC_GS门窗感应器真实规格
        {
            "agt": get_hub_id(6),  # Binary sensors
            "me": "6o7p",
            "devtype": "SL_SC_GS",
            "name": "Window Sensor",
            "data": {
                "P1": {
                    "type": 0,
                    "val": 0,
                },  # 门禁状态 (type&1==1:打开, type&1==0:吸合)
                "AXS": {
                    "type": 0,
                    "val": 0,
                },  # 震动状态 (type&1==1:震动, type&1==0:无震动)
                "V": {"val": 91},  # 电池电量
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.6.2的SL_SC_MHW动态感应器真实规格
        {
            "agt": get_hub_id(6),  # Binary sensors
            "me": "bs_motion",  # 友好设备ID，用于测试
            "devtype": "SL_SC_MHW",
            "name": "Motion Sensor",
            "data": {
                "M": {"val": 1, "type": 0},  # 检测到运动
                "V": {"val": 82},  # 电池电量
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.6.2的SL_SC_BM CUBE动态感应器真实规格
        {
            "agt": get_hub_id(6),  # Binary sensors
            "me": "8q9r",
            "devtype": "SL_SC_BM",
            "name": "CUBE Motion Sensor",
            "data": {
                "M": {"val": 0, "type": 0},  # 未检测到运动
                "V": {"val": 95},  # 电池电量
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.6.2的SL_SC_CM 7号电池版动态感应器真实规格
        {
            "agt": get_hub_id(6),  # Binary sensors
            "me": "0s1t",
            "devtype": "SL_SC_CM",
            "name": "Battery Motion Sensor",
            "data": {
                "P1": {"val": 1},  # 检测到运动
                "P3": {"val": 78},  # 电池电量
                "P4": {"val": 520},  # USB供电电压
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.6.2的SL_BP_MZ移动感应器Pro真实规格
        {
            "agt": get_hub_id(6),  # Binary sensors
            "me": "2u3v",
            "devtype": "SL_BP_MZ",
            "name": "Motion Sensor Pro",
            "data": {
                "P1": {"val": 0},  # 未检测到运动
                "P2": {"v": 350, "val": 350},  # 环境光照值 350 lux
                "P3": {"val": 88},  # 电池电量
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.6.4的SL_SC_WA水浸传感器真实规格
        {
            "agt": get_hub_id(6),  # Binary sensors
            "me": "bs_water",  # 友好设备ID，用于测试
            "devtype": "SL_SC_WA",
            "name": "Water Leak Sensor",
            "data": {
                "WA": {"val": 1, "type": 0},  # 检测到水
                "V": {"val": 78},  # 电池电量
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.8.1的SL_LK_LS智能门锁真实规格
        {
            "agt": get_hub_id(6),  # Binary sensors
            "me": "bs_lock",  # 友好设备ID，用于测试
            "devtype": "SL_LK_LS",
            "name": "Main Lock",
            "data": {
                "EVTLO": {"val": 4121, "type": 1},  # 实时开锁信息
                "ALM": {"val": 2},  # 告警信息
                "BAT": {"val": 88},  # 电池电量
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.2.4的SL_SC_BB随心开关真实规格 (V1版本)
        {
            "agt": get_hub_id(6),  # Binary sensors
            "me": "3j2l",
            "devtype": "SL_SC_BB",
            "fullCls": "SL_SC_BB_V1",  # V1版本标识
            "name": "Panic Button Basic",
            "data": {
                "B": {"type": 0, "val": 0},  # 按键状态 (0:未按下, 1:按下)
                "V": {"val": 90},  # 电池电量
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.2.4的SL_SC_BB随心开关真实规格 (V2版本) - 高级手势识别
        {
            "agt": get_hub_id(6),  # Binary sensors
            "me": "7x8y",
            "devtype": "SL_SC_BB",
            "fullCls": "SL_SC_BB_V2",  # V2版本标识
            "name": "Panic Button Advanced",
            "data": {
                "P1": {"val": 1},  # 按键状态: 1=单击, 2=双击, 255=长按
                "P2": {"val": 85},  # 电池电量
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.6.9的SL_P_A烟雾感应器真实规格
        {
            "agt": get_hub_id(6),  # Binary sensors
            "me": "4w5x",
            "devtype": "SL_P_A",
            "name": "Smoke Detector",
            "data": {
                "P1": {"val": 0},  # 当前是否有烟雾告警 (0:无告警, 1:有告警)
                "P2": {"v": 85, "val": 950},  # 电压和电量百分比
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 门锁电池电量传感器 - 用于测试
        {
            "agt": get_hub_id(6),  # Binary sensors
            "me": "sensor_lock_battery",  # 友好设备ID，用于测试
            "devtype": "SL_LK_LS",
            "name": "Lock Battery Sensor",
            "data": {
                "EVTLO": {"val": 0},  # 解锁事件
                "ALM": {"val": 0},  # 报警事件
                "BAT": {"val": 65, "v": 65},  # 电量65% - 这是主要的传感器数据
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


def create_gas_sensor_devices():
    """创建气体传感器设备的模拟数据列表 - 基于LifeSmart智慧设备规格属性说明文档2.6.5-2.6.6。"""
    devices = [
        # 基于文档2.6.5的SL_SC_CH 甲醛传感器真实规格
        {
            "agt": get_hub_id(7),  # Gas sensors
            "me": "5y6z",
            "devtype": "SL_SC_CH",
            "name": "Formaldehyde Sensor",
            "data": {
                "P1": {
                    "v": 45,
                    "val": 45000,
                    "type": 0,
                },  # 甲醛浓度 45ug/m³, type&1==0表示未超过告警门限
                "P2": {"val": 100},  # 甲醛浓度告警门限 中灵敏度
                "P3": {"type": 0, "val": 0},  # 警报音 未响
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.6.6的SL_SC_CP 燃气传感器真实规格
        {
            "agt": get_hub_id(7),  # Gas sensors
            "me": "7a8b",
            "devtype": "SL_SC_CP",
            "name": "Gas Sensor",
            "data": {
                "P1": {
                    "type": 0,
                    "val": 65,
                },  # 燃气浓度 65, type&1==0表示未超过告警门限
                "P2": {"val": 120},  # 燃气浓度告警门限 中灵敏度
                "P3": {"type": 0, "val": 0},  # 警报音 未响
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


def create_specialized_sensor_devices():
    """创建专用传感器设备的模拟数据列表 - 基于LifeSmart智慧设备规格属性说明文档。"""
    devices = [
        # 基于文档2.10.4的V_485_P 485控制器传感器真实规格
        {
            "agt": get_hub_id(7),  # Specialized sensors
            "me": "9c0d",
            "devtype": "V_485_P",
            "name": "485 Controller Sensor",
            "data": {
                "P1": {"v": 1250.5, "val": 1149379072},  # 传感器值 IEEE754浮点数
                "T": {"v": 26.2, "val": 262},  # 温度值 26.2°C
                "H": {"v": 58.8, "val": 588},  # 湿度值 58.8%
                "PM": {"v": 15, "val": 15},  # PM2.5值 15ug/m³
                "PMX": {"v": 22, "val": 22},  # PM10值 22ug/m³
                "CO2PPM": {"v": 680, "val": 680},  # CO2浓度 680ppm
                "CH20PPM": {"v": 0.035, "val": 35},  # 甲醛浓度 0.035ppm
                "TVOC": {"v": 0.45, "val": 450},  # TVOC浓度 0.45mg/m³
                "PHM": {"v": 42, "val": 42},  # 噪音 42dB
            },
            "stat": 1,
            "ver": "0.0.0.7",
            "modelKey": "0x12",  # 第三方设备标识
        },
        # 基于文档的SL_SC_B1 环境传感器真实规格
        {
            "agt": get_hub_id(7),  # Specialized sensors
            "me": "1e2f",
            "devtype": "SL_SC_B1",
            "name": "Advanced Env Sensor",
            "data": {
                "T": {"v": 24.8, "val": 248},  # 温度 24.8°C
                "H": {"v": 61.2, "val": 612},  # 湿度 61.2%
                "CO2": {"v": 720, "val": 720},  # CO2浓度 720ppm
                "TVOC": {"v": 0.32, "val": 320},  # TVOC浓度 0.32mg/m³
                "V": {"val": 87},  # 电池电量 87%
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.6.16的SL_SC_CN 噪音传感器真实规格 - 完整IO口
        {
            "agt": get_hub_id(7),  # Specialized sensors
            "me": "3g4h",
            "devtype": "SL_SC_CN",
            "name": "Noise Sensor",
            "data": {
                "P1": {
                    "type": 0,
                    "val": 38,
                },  # 噪音值 38dB, type&1==0表示未超过告警门限
                "P2": {
                    "val": 0x00460A46
                },  # 告警门限设置 - 默认配置(DD=70dB, BB=10, AA=20, CC=6)
                "P3": {"type": 0, "val": 0x00000001},  # 报警设置 - 指示音模式
                "P4": {"val": 0},  # 噪音校正值
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档的SL_SC_CV 语音小Q真实规格
        {
            "agt": get_hub_id(7),  # Specialized sensors
            "me": "5i6j",
            "devtype": "SL_SC_CV",
            "name": "Voice Assistant Q",
            "data": {
                "VOICE": {"val": 0, "type": 0},  # 语音状态
                "V": {"val": 92},  # 电池电量 92%
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.6.11的SL_P_RM 人体存在感应器真实规格
        {
            "agt": get_hub_id(7),  # Specialized sensors
            "me": "7k8l",
            "devtype": "SL_P_RM",
            "name": "Radar Human Presence Sensor",
            "data": {
                "P1": {"val": 1},  # 移动检测: 0=无移动 非0=有移动
                "P2": {
                    "val": 0x00040010,
                    "type": 0,
                },  # 移动检测参数设置: bit0-7动态锁定时间(16*4=64秒), bit8-25灵敏度(4=默认)
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


def create_alarm_and_security_devices():
    """创建报警器和安防设备的模拟数据列表 - 基于LifeSmart智慧设备规格属性说明文档2.12。"""
    devices = [
        # 基于文档2.12的SL_ALM智能报警器(CoSS版)真实规格
        {
            "agt": get_hub_id(8),  # Alarm and security devices
            "me": "9m0n",
            "devtype": "SL_ALM",
            "name": "CoSS Smart Alarm",
            "data": {
                "P1": {
                    "type": 0,
                    "val": 0x00030005,
                },  # 播放控制: type&1==0没有播放, val=时间/次数+音量+音频序号
                "P2": {
                    "type": 1,
                    "val": 0x000000F0,
                },  # 音量控制: type&1==1正常模式, val=音量值(高4位)
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档的LSSSMINIV1多功能报警器真实规格
        {
            "agt": get_hub_id(8),  # Alarm and security devices
            "me": "1o2p",
            "devtype": "LSSSMINIV1",
            "name": "Multi-Function Alarm",
            "data": {
                "ALARM": {"type": 0, "val": 0},  # 报警状态
                "SOUND": {"type": 0, "val": 0},  # 声音状态
                "V": {"val": 88},  # 电池电量
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


def create_defed_security_devices():
    """创建云防系列设备的模拟数据列表 - 基于LifeSmart智慧设备规格属性说明文档2.6.13。"""
    devices = [
        # 基于文档2.6.13的SL_DF_GG云防门窗感应器真实规格
        {
            "agt": get_hub_id(9),  # Cloud security devices
            "me": "df1_door",
            "devtype": "SL_DF_GG",
            "name": "DEFED Door Sensor",
            "data": {
                "A": {"type": 0, "val": 0},  # 门禁状态: type&1==0吸合(关闭)
                "A2": {"type": 1, "val": 0},  # 外部感应器状态: type值为1表示无外接
                "T": {"v": 22.5, "val": 225},  # 温度: 22.5°C (原始值*10)
                "V": {"v": 85, "val": 3200, "type": 0},  # 电量85%, type&1==0正常电量
                "TR": {"type": 0, "val": 0},  # 防拆状态: type&1==0正常
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.6.13的SL_DF_MM云防动态感应器真实规格
        {
            "agt": get_hub_id(9),  # Cloud security devices
            "me": "df2_motion",
            "devtype": "SL_DF_MM",
            "name": "DEFED Motion Sensor",
            "data": {
                "M": {"type": 1, "val": 1},  # 当前状态: type&1==1检测到移动
                "T": {"v": 24.2, "val": 242},  # 温度: 24.2°C (原始值*10)
                "V": {"v": 78, "val": 2900, "type": 0},  # 电量78%, type&1==0正常电量
                "TR": {"type": 0, "val": 0},  # 防拆状态: type&1==0正常
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.6.13的SL_DF_SR云防室内警铃真实规格
        {
            "agt": get_hub_id(9),  # Cloud security devices
            "me": "df3_siren",
            "devtype": "SL_DF_SR",
            "name": "DEFED Indoor Siren",
            "data": {
                "SR": {"type": 0, "val": 0},  # 当前状态: type&1==0正常(无播放)
                "T": {"v": 23.8, "val": 238},  # 温度: 23.8°C (原始值*10)
                "V": {"v": 92, "val": 3400, "type": 0},  # 电量92%, type&1==0正常电量
                "TR": {"type": 0, "val": 0},  # 防拆状态: type&1==0正常
                "P1": {
                    "val": 0x00050088,
                    "type": 0x80,
                },  # 报警设置: 0.5秒持续+音量136+音频1
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.6.13的SL_DF_BB云防遥控器真实规格
        {
            "agt": get_hub_id(9),  # Cloud security devices
            "me": "df4_remote",
            "devtype": "SL_DF_BB",
            "name": "DEFED Key Fob",
            "data": {
                "eB1": {"type": 0, "val": 0},  # 按键1状态(布防图标): type&1==0松开状态
                "eB2": {"type": 0, "val": 0},  # 按键2状态(撤防图标): type&1==0松开状态
                "eB3": {"type": 0, "val": 0},  # 按键3状态(警告图标): type&1==0松开状态
                "eB4": {"type": 0, "val": 0},  # 按键4状态(在家图标): type&1==0松开状态
                "V": {"v": 65, "val": 2400, "type": 0},  # 电量65%, type&1==0正常电量
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.6.13的SL_DF_KP云防KeyPad真实规格
        {
            "agt": get_hub_id(9),  # Cloud security devices
            "me": "df5_keypad",
            "devtype": "SL_DF_KP",
            "name": "DEFED KeyPad",
            "data": {
                "KP": {"type": 0, "val": 0},  # KeyPad状态
                "V": {"v": 88, "val": 3300, "type": 0},  # 电量88%, type&1==0正常电量
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


def create_additional_lock_devices():
    """创建额外的门锁设备的模拟数据列表 - 基于LifeSmart智慧设备规格属性说明文档。"""
    devices = [
        # 基于文档的SL_LK_GTM智能门锁 盖特曼真实规格
        {
            "agt": get_hub_id(8),  # Additional lock devices
            "me": "3q4r",
            "devtype": "SL_LK_GTM",
            "name": "Gateman Lock",
            "data": {
                "EVTLO": {"val": 2052, "type": 1},  # 实时开锁信息: 指纹开锁
                "ALM": {"val": 0},  # 告警信息: 无告警
                "BAT": {"val": 75},  # 电池电量 75%
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档的SL_LK_AG智能门锁 西勒奇真实规格
        {
            "agt": get_hub_id(8),  # Additional lock devices
            "me": "5s6t",
            "devtype": "SL_LK_AG",
            "name": "Schlage Lock",
            "data": {
                "EVTLO": {"val": 1028, "type": 1},  # 实时开锁信息: 密码开锁
                "ALM": {"val": 1},  # 告警信息: 低电量告警
                "BAT": {"val": 25},  # 电池电量 25%
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档的SL_LK_YL智能门锁 耶鲁真实规格
        {
            "agt": get_hub_id(8),  # Additional lock devices
            "me": "7u8v",
            "devtype": "SL_LK_YL",
            "name": "Yale Lock",
            "data": {
                "EVTLO": {"val": 3076, "type": 1},  # 实时开锁信息: NFC开锁
                "ALM": {"val": 0},  # 告警信息: 无告警
                "BAT": {"val": 92},  # 电池电量 92%
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档的SL_LK_DJ智能门锁 C200/C210真实规格
        {
            "agt": get_hub_id(8),  # Additional lock devices
            "me": "9w0x",
            "devtype": "SL_LK_DJ",
            "fullCls": "SL_LK_DJ_V2",  # C200版本
            "name": "Smart Lock C200",
            "data": {
                "EVTLO": {"val": 7168, "type": 1},  # 实时开锁信息: 蓝牙开锁
                "ALM": {"val": 0},  # 告警信息: 无告警
                "BAT": {"val": 68},  # 电池电量 68%
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


# ================= 窗帘系列 (Cover Series) =================


def create_cover_devices():
    """创建窗帘设备的模拟数据列表 - 基于LifeSmart智慧设备规格属性说明文档2.3。"""
    devices = [
        # 基于文档2.3.2的SL_DOOYA DOOYA窗帘电机真实规格
        {
            "agt": get_hub_id(7),  # 使用不同的hub ID
            "me": "cover_dooya",  # 友好设备ID，用于测试
            "devtype": "SL_DOOYA",
            "name": "DOOYA Curtain Motor",
            "data": {
                "P1": {
                    "val": 100,
                    "type": 128,
                },  # 窗帘状态: 位置100%, 没有运行 (完全打开状态)
                "P2": {"type": 128, "val": 0},  # 窗帘控制口
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.11的SL_ETDOOR车库门真实规格
        {
            "agt": get_hub_id(7),  # Cover devices
            "me": "cover_garage",  # 友好设备ID，用于测试
            "devtype": "SL_ETDOOR",
            "name": "Garage Door Controller",
            "data": {
                "P1": {"type": 128, "val": 0},  # 灯光控制: 关闭状态
                "P2": {"val": 0, "type": 128},  # 车库门状态: 0%关闭, 没有运行
                "P3": {"type": 128, "val": 0},  # 车库门控制口
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.3.1的SL_SW_WIN窗帘控制开关真实规格
        {
            "agt": get_hub_id(7),  # Cover devices
            "me": "cover_generic",  # 友好设备ID，用于测试
            "devtype": "SL_SW_WIN",
            "name": "Curtain Control Switch",
            "data": {
                "OP": {"type": 128, "val": 0},  # 打开窗帘
                "CL": {"type": 128, "val": 0},  # 关闭窗帘
                "ST": {"type": 128, "val": 0},  # 停止
                "P1": {"type": 128, "val": 0},  # 打开窗帘
                "P2": {"type": 128, "val": 0},  # 停止
                "P3": {"type": 128, "val": 0},  # 关闭窗帘
                "dark": {"type": 128, "val": 100},  # 关闭状态时指示灯亮度
                "bright": {"type": 128, "val": 200},  # 开启状态时指示灯亮度
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.10.1的SL_P通用控制器真实规格 (三线窗帘模式)
        {
            "agt": get_hub_id(7),  # Cover devices
            "me": "7p6q",
            "devtype": "SL_P",
            "name": "Generic Controller Curtain",
            "data": {
                "P1": {"val": (4 << 24)},  # Mode 4: 三线窗帘模式
                "P2": {"type": 128, "val": 0},  # 打开窗帘
                "P3": {"type": 128, "val": 0},  # 关闭窗帘
                "P4": {"type": 128, "val": 0},  # 停止窗帘
                "P5": {"type": 128, "val": 0},  # 状态1 (仅自由模式有效)
                "P6": {"type": 128, "val": 0},  # 状态2 (仅自由模式有效)
                "P7": {"type": 128, "val": 0},  # 状态3 (仅自由模式有效)
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 无位置反馈的窗帘设备 - 用于测试
        {
            "agt": get_hub_id(7),  # Cover devices
            "me": "cover_nonpos",  # 友好设备ID，用于测试
            "devtype": "SL_P",
            "name": "Non-Position Curtain",
            "data": {
                "P1": {"val": (2 << 24)},  # Mode 2: 开关模式，无位置反馈
                "P2": {"type": 128, "val": 0},  # 打开状态
                "P3": {"type": 128, "val": 0},  # 关闭状态
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


# ================= 气候控制系列 (Climate Series) =================


def create_climate_devices():
    """创建气候控制设备的模拟数据列表 - 基于LifeSmart智慧设备规格属性说明文档2.9。"""
    devices = [
        # 基于文档2.14.1的SL_NATURE超能面板 PRO(温控)真实规格
        {
            "agt": get_hub_id(8),  # 使用不同的hub ID
            "me": "climate_nature_thermo",  # 友好设备ID，用于测试
            "devtype": "SL_NATURE",
            "name": "Nature Panel Thermo",
            "data": {
                "P1": {"type": 129, "val": 1},  # 开关: 开启
                "P4": {"v": 22.5, "val": 225},  # T当前温度 (原始值*10)
                "P5": {"val": 3},  # 设备种类: 3=温控面板
                "P6": {"val": (1 << 6)},  # CFG配置: 1=风机盘管(单阀)模式
                "P7": {"val": 3},  # MODE模式: 3=制冷
                "P8": {"v": 24.0, "val": 240},  # tT目标温度 (原始值*10)
                "P9": {"val": 45},  # tF目标风速: 45=中档
                "P10": {"val": 15},  # F当前风速: 15=低风速
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.9.3的SL_CP_DN地暖温控器真实规格
        {
            "agt": get_hub_id(8),  # Climate devices
            "me": "climate_floor_heat",  # 友好设备ID，用于测试
            "devtype": "SL_CP_DN",
            "name": "Floor Heating Controller",
            "data": {
                "P1": {"type": 1, "val": 2147483648},  # 系统配置: 控制位
                "P2": {"type": 129, "val": 1},  # 继电器开关: 打开
                "P3": {"v": 23.0, "val": 230},  # 目标温度 (原始值*10)
                "P4": {"v": 21.5, "val": 215},  # 室内温度 (原始值*10)
                "P5": {"v": 45.0, "val": 450},  # 底版温度 (原始值/10)
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.9.4的SL_CP_AIR风机盘管真实规格
        {
            "agt": get_hub_id(8),  # Climate devices
            "me": "climate_fancoil",  # 友好设备ID，用于测试
            "devtype": "SL_CP_AIR",
            "name": "Fan Coil Unit",
            "data": {
                "P1": {
                    "type": 1,
                    "val": (1 << 15) | (1 << 13),
                },  # 系统配置: 低风速+制热
                "P2": {"type": 129, "val": 1},  # 阀门状态: 开
                "P3": {"val": 1},  # 风速状态: 1=低速
                "P4": {"v": 25.0, "val": 250},  # 目标温度 (原始值*10)
                "P5": {"v": 23.5, "val": 235},  # 室内温度 (原始值*10)
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 基于文档2.9.1的V_AIR_P智控器空调面板真实规格
        {
            "agt": get_hub_id(8),  # Climate devices
            "me": "climate_airpanel",  # 友好设备ID，用于测试
            "devtype": "V_AIR_P",
            "name": "Air Conditioner Panel",
            "data": {
                "O": {"type": 129, "val": 1},  # 开关: 开启状态
                "MODE": {"type": 206, "val": 3},  # 模式: 3=Cool制冷
                "F": {"type": 206, "val": 45},  # 风速: 45=中档
                "T": {"v": 24.5, "val": 245},  # 当前温度 (原始值*10)
                "tT": {"v": 26.0, "val": 260},  # 目标温度 (原始值*10)
            },
            "stat": 1,
            "ver": "0.0.0.7",
            "modelKey": "0xd2",  # 第三方设备标识
        },
        # 基于文档2.9.2的SL_TR_ACIPM新风系统真实规格
        {
            "agt": get_hub_id(8),  # Climate devices
            "me": "climate_airsystem",  # 友好设备ID，用于测试
            "devtype": "SL_TR_ACIPM",
            "name": "Air System",
            "data": {
                "P1": {"type": 129, "val": 2},  # 系统配置: 2=手动模式, type=129表示开启
                "P2": {"val": 2},  # 风速: 2=2档
                "P3": {"v": 0.5, "val": 5},  # 设置VOC (原始值/10)
                "P4": {"v": 0.3, "val": 3},  # VOC值 (原始值/10)
                "P5": {"v": 25, "val": 25},  # PM2.5值
                "P6": {"v": 22.0, "val": 220},  # 当前温度 (原始值/10)
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


# ================= 组合工厂函数 =================


def create_mock_lifesmart_devices():
    """
    创建一个全面的模拟设备列表，覆盖所有平台的测试需求。

    基于 LifeSmart 智慧设备规格属性说明文档和 const.py 中的设备分类，
    提供完整的设备类型覆盖。

    Returns:
        list: 包含各种设备类型的完整设备列表
    """
    devices = []

    # 插座系列
    devices.extend(create_smart_plug_devices())
    devices.extend(create_power_meter_plug_devices())

    # 开关系列
    devices.extend(create_traditional_switch_devices())
    devices.extend(create_advanced_switch_devices())

    # 灯光系列 - 使用新的工厂函数架构
    devices.extend(create_dimmer_light_devices())
    devices.extend(create_brightness_light_devices())
    devices.extend(create_rgb_light_devices())
    devices.extend(create_rgbw_light_devices())
    devices.extend(create_spot_light_devices())
    devices.extend(create_quantum_light_devices())
    devices.extend(create_outdoor_light_devices())

    # 传感器系列
    devices.extend(create_environment_sensor_devices())
    devices.extend(create_binary_sensor_devices())
    devices.extend(create_gas_sensor_devices())
    devices.extend(create_specialized_sensor_devices())
    devices.extend(create_air_purifier_devices())  # 空气净化器 - 包含多种传感器IO口

    # 安防和报警系列
    devices.extend(create_alarm_and_security_devices())
    devices.extend(create_defed_security_devices())  # Phase 2: 云防系列安防设备
    devices.extend(create_additional_lock_devices())

    # 窗帘系列
    devices.extend(create_cover_devices())

    # 气候控制系列
    devices.extend(create_climate_devices())

    return devices


def create_devices_by_category(categories=None):
    """
    根据指定的类别创建设备列表。

    Args:
        categories: 需要包含的设备类别列表。可选值：
                   'smart_plug', 'power_meter_plug', 'traditional_switch',
                   'advanced_switch', 'dimmer_light', 'rgb_light', 'spot_light',
                   'environment_sensor', 'binary_sensor', 'cover', 'climate'
                   如果为None，则返回所有类别的设备

    Returns:
        list: 指定类别的设备列表
    """
    if categories is None:
        return create_mock_lifesmart_devices()

    devices = []
    category_functions = {
        # 插座系列
        "smart_plug": create_smart_plug_devices,
        "power_meter_plug": create_power_meter_plug_devices,
        # 开关系列
        "traditional_switch": create_traditional_switch_devices,
        "advanced_switch": create_advanced_switch_devices,
        # 灯光系列
        "dimmer_light": create_dimmer_light_devices,
        "brightness_light": create_brightness_light_devices,
        "rgb_light": create_rgb_light_devices,
        "rgbw_light": create_rgbw_light_devices,
        "spot_light": create_spot_light_devices,
        "quantum_light": create_quantum_light_devices,
        "outdoor_light": create_outdoor_light_devices,
        # 传感器系列
        "environment_sensor": create_environment_sensor_devices,
        "binary_sensor": create_binary_sensor_devices,
        "gas_sensor": create_gas_sensor_devices,
        "specialized_sensor": create_specialized_sensor_devices,
        "air_purifier": create_air_purifier_devices,
        # 安防和报警系列
        "alarm_security": create_alarm_and_security_devices,
        "defed_security": create_defed_security_devices,
        "additional_locks": create_additional_lock_devices,
        # 窗帘系列
        "cover": create_cover_devices,
        # 气候控制系列
        "climate": create_climate_devices,
    }

    for category in categories:
        if category in category_functions:
            devices.extend(category_functions[category]())

    return devices


# ================= 专用设备数据创建函数 =================


def create_mock_device_climate_fancoil() -> dict:
    """
    提供一个标准的风机盘管设备 (SL_CP_AIR) 的模拟数据。
    """
    device_ids = SPECIALIZED_TEST_DEVICE_IDS["climate_fancoil"]
    return {
        "agt": device_ids["agt"],
        "me": device_ids["me"],
        "devtype": "SL_CP_AIR",
        "name": "Fancoil Single Test",
        "data": {
            "P1": {"type": 1, "val": (1 << 15) | (1 << 13)},  # 低风速+制热
            "P4": {"v": 24.0},  # 当前温度
            "P5": {"v": 26.0},  # 目标温度
        },
    }


def create_mock_device_spot_rgb_light() -> dict:
    """
    提供一个标准的RGB射灯设备的模拟数据。
    """
    device_ids = SPECIALIZED_TEST_DEVICE_IDS["spot_rgb_light"]
    return {
        "agt": device_ids["agt"],
        "me": device_ids["me"],
        "devtype": "SL_SPOT",
        "name": "Spot RGB Single Test",
        "data": {"RGB": {"type": 129, "val": 0xFF8040}},
    }


def create_mock_device_dual_io_rgbw_light() -> dict:
    """
    提供一个标准的双路I/O RGBW灯控设备的模拟数据。
    """
    device_ids = SPECIALIZED_TEST_DEVICE_IDS["dual_io_rgbw_light"]
    return {
        "agt": device_ids["agt"],
        "me": device_ids["me"],
        "devtype": "SL_CT_RGBW",
        "name": "Dual IO RGBW Single Test",
        "data": {
            "RGBW": {"type": 129, "val": 0x00FF0080},
            "DYN": {"type": 128, "val": 0},
        },
    }


def create_mock_device_single_io_rgb_light() -> dict:
    """
    提供一个标准的单路I/O RGB灯控设备的模拟数据。
    """
    device_ids = SPECIALIZED_TEST_DEVICE_IDS["single_io_rgb_light"]
    return {
        "agt": device_ids["agt"],
        "me": device_ids["me"],
        "devtype": "SL_SC_RGB",
        "name": "Single IO RGB Single Test",
        "data": {"RGB": {"type": 129, "val": 0x64010203}},
    }


# ================= 补充的灯光设备类型 =================


def create_brightness_light_devices():
    """创建亮度调节灯光设备。"""
    devices = [
        # 可调亮度开关智控器 SL_SPWM
        {
            "agt": get_hub_id(3),  # Light hub
            "me": "brightness_controller",  # 友好设备ID，用于测试
            "devtype": "SL_SPWM",
            "name": "Brightness Controller",
            "data": {"P1": {"type": 129, "val": 128}},  # 中等亮度
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


def create_rgbw_light_devices():
    """创建RGBW彩色灯光设备。"""
    devices = [
        # RGBW灯泡 SL_LI_RGBW
        {
            "agt": get_hub_id(3),  # Light hub
            "me": "light_dualrgbw",  # 友好设备ID，用于测试
            "devtype": "SL_LI_RGBW",
            "name": "RGBW Light Bulb",
            "data": {
                "RGBW": {"type": 129, "val": 0x00FF0000},  # 红色
                "DYN": {"type": 128, "val": 0},  # 动态效果关闭
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 单IO RGBW灯
        {
            "agt": get_hub_id(3),
            "me": "light_singlergb",  # 友好设备ID，用于测试
            "devtype": "SL_CT_RGBW",
            "name": "Single RGB Light Strip",
            "data": {
                "RGBW": {"type": 129, "val": 0x0000FF00},  # 绿色
                "DYN": {"type": 128, "val": 0},
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


def create_outdoor_light_devices():
    """创建户外灯光设备。"""
    devices = [
        # 调光壁灯(门廊壁灯) SL_LI_GD1
        {
            "agt": get_hub_id(3),  # Light hub
            "me": "light_outdoor",  # 友好设备ID，用于测试
            "devtype": "SL_LI_GD1",
            "name": "Garden Wall Light",
            "data": {
                "P1": {"type": 129, "val": 200},  # 亮度控制
                "P2": {"val": 0},  # 无移动检测
                "P3": {"val": 500},  # 环境光照
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        # 花园地灯 SL_LI_UG1
        {
            "agt": get_hub_id(3),
            "me": "light_cover",  # 友好设备ID，用于测试
            "devtype": "SL_LI_UG1",
            "name": "Garden Underground Light",
            "data": {
                "P1": {"type": 129, "val": 0x00FFFF00},  # 黄色
                "P2": {"val": 300},  # 环境光照
                "P3": {"val": 1},  # 正在充电
                "P4": {"val": 3800, "v": 85},  # 电量85%
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


def create_air_purifier_devices():
    """创建空气净化器设备。"""
    devices = [
        # 空气净化器 OD_MFRESH_M8088
        {
            "agt": get_hub_id(7),  # Special devices hub
            "me": "air_purifier",
            "devtype": "OD_MFRESH_M8088",
            "name": "Air Purifier M8088",
            "data": {
                "O": {"type": 129, "val": 1},  # 开启状态
                "RM": {"val": 0},  # 自动模式
                "T": {"val": 235, "v": 23.5},  # 温度23.5℃
                "H": {"val": 550, "v": 55.0},  # 湿度55%
                "PM": {"val": 25, "v": 25},  # PM2.5浓度25μg/m³
                "FL": {"val": 2400},  # 滤芯剩余2400小时
                "UV": {"val": 0},  # 紫外线指数0
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]

    # 验证设备数据完整性
    for device in devices:
        validate_device_data(device)

    return devices


def validate_config_data_completeness(config_data):
    """
    验证配置数据是否包含所有标准字段。

    Args:
        config_data: 配置数据字典

    Returns:
        bool: 如果包含所有必需字段则返回True

    Raises:
        ValueError: 如果缺少必需的配置字段
    """
    # 将字符串映射到实际的常量
    field_mapping = {
        "CONF_TYPE": CONF_TYPE,
        "CONF_LIFESMART_APPKEY": CONF_LIFESMART_APPKEY,
        "CONF_LIFESMART_APPTOKEN": CONF_LIFESMART_APPTOKEN,
        "CONF_LIFESMART_USERID": CONF_LIFESMART_USERID,
        "CONF_LIFESMART_USERTOKEN": CONF_LIFESMART_USERTOKEN,
        "CONF_REGION": CONF_REGION,
    }

    missing_fields = []
    for field_name in STANDARD_CONFIG_FIELDS:
        actual_field = field_mapping.get(field_name, field_name)
        if actual_field not in config_data:
            missing_fields.append(field_name)

    if missing_fields:
        raise ValueError(f"配置数据缺少必需字段: {', '.join(missing_fields)}")

    return True


def create_virtual_test_devices():
    """
    创建虚拟测试设备列表，用于错误处理测试。

    Returns:
        list: 虚拟测试设备列表
    """
    devices = []

    for i, virtual_name in enumerate(VIRTUAL_TEST_DEVICES):
        device = {
            "agt": get_hub_id(i),
            "me": virtual_name,
            "devtype": "VIRTUAL_TEST",
            "name": f"Virtual Test Device {i+1}",
            "data": {"TEST": {"type": 129, "val": 1}},
            "stat": 1,
            "ver": "0.0.0.1",
            "_virtual": True,  # 标记为虚拟设备
        }

        # 验证设备数据完整性
        validate_device_data(device)
        devices.append(device)

    return devices


def create_mock_config_data_with_validation():
    """
    创建并验证标准的模拟配置数据。

    Returns:
        dict: 验证过的标准LifeSmart集成配置数据

    Raises:
        ValueError: 如果生成的配置数据不完整
    """
    config_data = create_mock_config_data()
    validate_config_data_completeness(config_data)
    return config_data


def create_mock_device(
    device_type: str, data: dict, name: str = None, hub_id: str = None
) -> dict:
    """
    创建通用的模拟设备对象，用于测试。

    Args:
        device_type: 设备类型（如'SL_SW_RC3'）
        data: 设备数据字典（IO端口数据）
        name: 设备名称（可选）
        hub_id: Hub ID（可选，默认使用test hub）

    Returns:
        dict: 完整的设备对象
    """
    return {
        "agt": hub_id or get_hub_id(1),
        "me": f"test_{device_type.lower()}",
        "devtype": device_type,
        "name": name or f"Test {device_type}",
        "data": data,
        "stat": 1,
        "ver": "0.0.0.7",
    }
