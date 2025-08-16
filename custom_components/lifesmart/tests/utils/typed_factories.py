""" "
简化的设备工厂函数 - 消除双轨制架构的重构版本
基于typed_factories.py重构，回归简单而有效的字典工厂模式。

此文件是双轨制架构彻底重构的结果：
- 消除TypedDevice和IOConfig的过度抽象
- 移除convert_typed_devices_to_dict()转换调用
- 统一到单一字典API
- 从1194行精简到约400行，复杂性降低70%
"""

from typing import List, Dict, Any

from custom_components.lifesmart.core.const import (
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
)
from .helpers import get_hub_id


# ============================================================================
# === 10个核心设备类型的字典工厂函数 (简化版本) ===
# ============================================================================


# 1. SL_OL - 智慧插座 (Switch平台，简单开关)
def create_smart_plug() -> Dict[str, Any]:
    """
    创建智慧插座设备 (SL_OL)。
    基于官方文档2.1.1的SL_OL真实规格。
    """
    return {
        "agt": get_hub_id(0),
        "me": "sw_ol",
        "devtype": "SL_OL",
        "name": "Smart Outlet",
        "data": {"O": {"type": CMD_TYPE_ON, "val": 1}},  # 开启状态，符合文档规范
        "stat": 1,
        "ver": "0.0.0.7",
    }


# 2. SL_OE_3C - 计量插座 (Sensor平台，功率监测)
def create_power_meter_plug() -> Dict[str, Any]:
    """
    创建计量插座设备 (SL_OE_3C)。
    基于官方文档2.1.2的SL_OE_3C真实规格。
    """
    return {
        "agt": get_hub_id(1),
        "me": "sensor_power_plug",
        "devtype": "SL_OE_3C",
        "name": "Washing Machine Plug",
        "data": {
            "P1": {"type": CMD_TYPE_ON, "val": 1},  # 开关状态
            "P2": {"v": 1.5, "val": 1084227584},  # 累计用电量 IEEE754
            "P3": {"v": 1200.0, "val": 1149239296},  # 当前功率 IEEE754
            "P4": {"type": CMD_TYPE_OFF, "val": 3000},  # 功率门限
        },
        "stat": 1,
        "ver": "0.0.0.7",
    }


# 3. SL_SW_IF3 - 三联开关 (Switch平台，多路控制)
def create_switch_if3() -> Dict[str, Any]:
    """
    创建三联开关设备 (SL_SW_IF3)。
    基于官方文档2.2.1的SL_SW_IF3真实规格。
    """
    return {
        "agt": get_hub_id(1),
        "me": "sw_if3",
        "devtype": "SL_SW_IF3",
        "fullCls": "SL_SW_IF3_V2",  # 指定版本信息
        "name": "smart Switch",
        "data": {
            "L1": {"type": CMD_TYPE_ON, "val": 1, "name": "Living", "v": 1},
            "L2": {"type": CMD_TYPE_OFF, "val": 0, "name": "study", "v": 0},
            "L3": {"type": CMD_TYPE_ON, "val": 1, "name": "Kid", "v": 1},
        },
        "stat": 1,
        "ver": "0.0.0.7",
    }


# 4. SL_LI_WW - 调光灯泡 (Light平台，亮度+色温)
def create_dimmer_light() -> Dict[str, Any]:
    """
    创建调光调色灯设备 (SL_LI_WW)。
    基于官方文档2.4.3的SL_LI_WW真实规格。
    """
    return {
        "agt": get_hub_id(3),
        "me": "light_dimmer",
        "devtype": "SL_LI_WW",
        "fullCls": "SL_LI_WW_V1",  # 指定V1版本
        "name": "Smart Bulb Cool Warm",
        "data": {
            "P1": {"type": CMD_TYPE_ON, "val": 100},  # 亮度100%
            "P2": {"val": 27},  # 色温
        },
        "stat": 1,
        "ver": "0.0.0.7",
    }


# 5. SL_CT_RGBW - RGBW灯带 (Light平台，颜色+效果)
def create_rgbw_light() -> Dict[str, Any]:
    """
    创建RGBW灯带设备 (SL_CT_RGBW)。
    基于官方文档2.4.1的SL_CT_RGBW真实规格。
    """
    return {
        "agt": get_hub_id(4),
        "me": "5b9a",
        "devtype": "SL_CT_RGBW",
        "name": "RGBW Light Strip",
        "data": {
            "RGBW": {"type": CMD_TYPE_ON, "val": 0x00FF0000},  # 绿色
            "DYN": {"type": CMD_TYPE_OFF, "val": 0},
        },
        "stat": 1,
        "ver": "0.0.0.7",
    }


# 6. SL_SC_THL - 环境传感器 (Sensor平台，多传感器)
def create_environment_sensor() -> Dict[str, Any]:
    """
    创建环境传感器设备 (SL_SC_THL)。
    基于官方文档2.6.3的SL_SC_THL真实规格。
    """
    return {
        "agt": get_hub_id(5),
        "me": "sensor_env",
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
    }


# 7. SL_SC_G - 门窗传感器 (Binary Sensor平台，状态检测)
def create_door_sensor() -> Dict[str, Any]:
    """
    创建门窗传感器设备 (SL_SC_G)。
    基于官方文档2.6.1的SL_SC_G真实规格。
    """
    return {
        "agt": get_hub_id(6),
        "me": "bs_door",
        "devtype": "SL_SC_G",
        "name": "Door Sensor",
        "data": {
            "G": {"val": 0, "type": 0},  # 关闭状态 (0:打开, 1:关闭)
            "V": {"val": 92},  # 电池电量
        },
        "stat": 1,
        "ver": "0.0.0.7",
    }


# 8. SL_DOOYA - 窗帘电机 (Cover平台，位置控制)
def create_curtain_motor() -> Dict[str, Any]:
    """
    创建DOOYA窗帘电机设备 (SL_DOOYA)。
    基于官方文档2.3.2的SL_DOOYA真实规格。
    """
    return {
        "agt": get_hub_id(7),
        "me": "cover_dooya",
        "devtype": "SL_DOOYA",
        "name": "DOOYA Curtain Motor",
        "data": {
            "P1": {
                "val": 100,
                "type": CMD_TYPE_OFF,
            },  # 窗帘状态: 位置100%, 没有运行 (完全打开状态)
            "P2": {"type": CMD_TYPE_OFF, "val": 0},  # 窗帘控制口
        },
        "stat": 1,
        "ver": "0.0.0.7",
    }


# 9. SL_NATURE - 温控面板 (Climate平台，温度控制)
def create_thermostat_panel() -> Dict[str, Any]:
    """
    创建SL_NATURE超能面板温控设备。
    基于官方文档2.14.1的SL_NATURE真实规格。
    """
    return {
        "agt": get_hub_id(8),
        "me": "climate_nature_thermo",
        "devtype": "SL_NATURE",
        "name": "Nature Panel Thermo",
        "data": {
            "P1": {"type": CMD_TYPE_ON, "val": 1},  # 开关: 开启
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
    }


# 10. SL_LK_LS - 智能门锁 (Lock平台，安全设备)
def create_smart_lock() -> Dict[str, Any]:
    """
    创建智能门锁设备 (SL_LK_LS)。
    基于官方文档2.8.1的SL_LK_LS真实规格。
    """
    return {
        "agt": get_hub_id(6),
        "me": "bs_lock",
        "devtype": "SL_LK_LS",
        "name": "Main Lock",
        "data": {
            "EVTLO": {"val": 4121, "type": 1},  # 实时开锁信息
            "ALM": {"val": 2},  # 告警信息
            "BAT": {"val": 88},  # 电池电量
        },
        "stat": 1,
        "ver": "0.0.0.7",
    }


# ============================================================================
# === 组合工厂函数 ===
# ============================================================================


def create_core_devices() -> List[Dict[str, Any]]:
    """
    创建所有10个核心设备类型的设备实例。

    Returns:
        包含10个核心设备类型的设备列表
    """
    return [
        create_smart_plug(),
        create_power_meter_plug(),
        create_switch_if3(),
        create_dimmer_light(),
        create_rgbw_light(),
        create_environment_sensor(),
        create_door_sensor(),
        create_curtain_motor(),
        create_thermostat_panel(),
        create_smart_lock(),
    ]


def create_devices_by_platform(platform: str) -> List[Dict[str, Any]]:
    """
    根据平台类型创建相应的设备列表。

    Args:
        platform: 平台类型 ('switch', 'sensor', 'light', etc.)

    Returns:
        指定平台的设备列表
    """
    platform_device_map = {
        "switch": [
            create_smart_plug(),
            create_switch_if3(),
        ],
        "sensor": [
            create_power_meter_plug(),
            create_environment_sensor(),
        ],
        "light": [
            create_dimmer_light(),
            create_rgbw_light(),
        ],
        "binary_sensor": [
            create_door_sensor(),
        ],
        "cover": [
            create_curtain_motor(),
        ],
        "climate": [
            create_thermostat_panel(),
        ],
        "lock": [
            create_smart_lock(),
        ],
    }

    return platform_device_map.get(platform, [])


# ============================================================================
# === 主要工厂函数 - 替代原有的create_mock_lifesmart_devices ===
# ============================================================================


def create_mock_lifesmart_devices() -> List[Dict[str, Any]]:
    """
    创建一个全面的模拟设备列表，覆盖所有平台的测试需求。
    这是原有复杂工厂系统的直接替代函数。

    Returns:
        list: 包含各种设备类型的完整设备列表
    """
    # 核心设备
    devices = create_core_devices()

    # 添加额外的测试设备
    devices.extend(create_additional_test_devices())

    return devices


def create_additional_test_devices() -> List[Dict[str, Any]]:
    """
    创建额外的测试设备以匹配原有覆盖范围。
    """
    additional_devices = []

    # 额外的开关设备 (用于特定测试)
    additional_devices.append(
        {
            "agt": get_hub_id(1),
            "me": "if3b2",  # test_helpers.py中的特定测试设备
            "devtype": "SL_SW_IF3",
            "fullCls": "SL_SW_IF3_V2",
            "name": "Test Switch IF3B2",
            "data": {
                "L1": {"type": CMD_TYPE_ON, "val": 1, "name": "TestL1", "v": 1},
                "L2": {"type": CMD_TYPE_OFF, "val": 0, "name": "TestL2", "v": 0},
                "L3": {"type": CMD_TYPE_ON, "val": 1, "name": "TestL3", "v": 1},
            },
            "stat": 1,
            "ver": "0.0.0.7",
        }
    )

    # 门锁电池传感器 (用于传感器测试)
    additional_devices.append(
        {
            "agt": get_hub_id(6),
            "me": "sensor_lock_battery",
            "devtype": "SL_LK_LS",
            "name": "Lock Battery Sensor",
            "data": {
                "EVTLO": {"val": 0},
                "ALM": {"val": 0},
                "BAT": {"val": 65, "v": 65},  # 电量65% - 主要的传感器数据
            },
            "stat": 1,
            "ver": "0.0.0.7",
        }
    )

    # 移动传感器
    additional_devices.append(
        {
            "agt": get_hub_id(6),
            "me": "bs_motion",
            "devtype": "SL_SC_MHW",
            "name": "Motion Sensor",
            "data": {
                "M": {"val": 1, "type": 0},  # 检测到运动
                "V": {"val": 82},  # 电池电量
            },
            "stat": 1,
            "ver": "0.0.0.7",
        }
    )

    # 水浸传感器
    additional_devices.append(
        {
            "agt": get_hub_id(6),
            "me": "bs_water",
            "devtype": "SL_SC_WA",
            "name": "Water Leak Sensor",
            "data": {
                "WA": {"val": 1, "type": 0},  # 检测到水
                "V": {"val": 78},  # 电池电量
            },
            "stat": 1,
            "ver": "0.0.0.7",
        }
    )

    return additional_devices


# ============================================================================
# === 保留的特殊设备工厂函数 (从原文件直接提取) ===
# ============================================================================


def create_mock_device_single_io_rgb_light() -> Dict[str, Any]:
    """
    提供一个标准的单路I/O RGB灯控设备的模拟数据。
    """
    from .constants import SPECIALIZED_TEST_DEVICE_IDS

    device_ids = SPECIALIZED_TEST_DEVICE_IDS["single_io_rgb_light"]
    return {
        "agt": device_ids["agt"],
        "me": device_ids["me"],
        "devtype": "SL_SC_RGB",
        "name": "Single IO RGB Single Test",
        "data": {"RGB": {"type": CMD_TYPE_ON, "val": 0x64010203}},
        "stat": 1,
        "ver": "0.0.0.7",
    }


def create_mock_device_spot_rgb_light() -> Dict[str, Any]:
    """
    提供一个标准的RGB射灯设备的模拟数据。
    """
    from .constants import SPECIALIZED_TEST_DEVICE_IDS

    device_ids = SPECIALIZED_TEST_DEVICE_IDS["spot_rgb_light"]
    return {
        "agt": device_ids["agt"],
        "me": device_ids["me"],
        "devtype": "SL_SPOT",
        "name": "Spot RGB Single Test",
        "data": {"RGB": {"type": CMD_TYPE_ON, "val": 0xFF8040}},
        "stat": 1,
        "ver": "0.0.0.7",
    }


def create_mock_device_dual_io_rgbw_light() -> Dict[str, Any]:
    """
    提供一个标准的双路I/O RGBW灯控设备的模拟数据。
    """
    from .constants import SPECIALIZED_TEST_DEVICE_IDS

    device_ids = SPECIALIZED_TEST_DEVICE_IDS["dual_io_rgbw_light"]
    return {
        "agt": device_ids["agt"],
        "me": device_ids["me"],
        "devtype": "SL_CT_RGBW",
        "name": "Dual IO RGBW Single Test",
        "data": {
            "RGBW": {"type": CMD_TYPE_ON, "val": 0x00FF0080},
            "DYN": {"type": CMD_TYPE_OFF, "val": 0},
        },
        "stat": 1,
        "ver": "0.0.0.7",
    }


# ============================================================================
# === Mock对象工厂函数 (保持向后兼容接口) ===
# ============================================================================


def create_mock_oapi_client(*, spec=None):
    """
    创建正确配置的OAPI客户端mock，区分同步和异步方法。
    """
    from unittest.mock import AsyncMock, MagicMock
    from .constants import DEFAULT_TEST_VALUES

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
    mock_client.async_refresh_token.return_value = {
        "usertoken": DEFAULT_TEST_VALUES["usertoken"],
        "expiredtime": 9999999999,
    }
    mock_client.async_get_all_devices.return_value = []
    mock_client.login_async.return_value = {
        "usertoken": DEFAULT_TEST_VALUES["usertoken"],
        "userid": DEFAULT_TEST_VALUES["userid"],
        "region": DEFAULT_TEST_VALUES["region"],
    }

    # 为测试兼容性添加_mock_*属性别名
    mock_client._mock_get_all_devices = mock_client.async_get_all_devices
    mock_client._mock_refresh_token = mock_client.async_refresh_token

    return mock_client


def create_mock_config_data() -> Dict[str, Any]:
    """
    创建标准的模拟配置数据。
    """
    from homeassistant import config_entries
    from homeassistant.const import CONF_REGION, CONF_TYPE
    from custom_components.lifesmart.core.const import (
        CONF_LIFESMART_APPKEY,
        CONF_LIFESMART_APPTOKEN,
        CONF_LIFESMART_USERID,
        CONF_LIFESMART_USERTOKEN,
    )
    from .constants import DEFAULT_TEST_VALUES

    return {
        CONF_TYPE: config_entries.CONN_CLASS_CLOUD_PUSH,
        CONF_LIFESMART_APPKEY: DEFAULT_TEST_VALUES["appkey"],
        CONF_LIFESMART_APPTOKEN: DEFAULT_TEST_VALUES["apptoken"],
        CONF_LIFESMART_USERID: DEFAULT_TEST_VALUES["userid"],
        CONF_LIFESMART_USERTOKEN: DEFAULT_TEST_VALUES["usertoken"],
        CONF_REGION: DEFAULT_TEST_VALUES["region"],
    }


def create_mock_oapi_client_with_devices(devices_list: List[Dict[str, Any]] = None):
    """
    创建带有预配置设备列表的OAPI客户端mock。
    """
    mock_client = create_mock_oapi_client()

    if devices_list is None:
        devices_list = []

    mock_client.async_get_all_devices.return_value = devices_list
    return mock_client


def create_mock_failed_oapi_client():
    """
    创建模拟失败场景的OAPI客户端mock。
    """
    mock_client = create_mock_oapi_client()

    # 设置失败响应
    mock_client.async_refresh_token.return_value = False
    mock_client.login_async.return_value = False
    mock_client.async_get_all_devices.side_effect = Exception("Connection failed")

    return mock_client
