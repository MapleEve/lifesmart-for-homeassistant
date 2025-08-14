"""
强类型设备工厂函数。
这些函数返回 `models.py` 中定义的强类型 `TypedDevice` 实例，
用于替代基于字典的旧工厂。

本文件是Phase 1增量基础设施建设的核心组件，实现10个核心设备类型的强类型工厂。
基于ZEN专家指导设计，确保与现有factories.py完全兼容。
"""

from typing import List

from custom_components.lifesmart.core.const import (
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_SET_CONFIG,
)
from custom_components.lifesmart.core.config.effect_mappings import DYN_EFFECT_MAP
from .models import (
    IOConfig,
    TypedDevice,
    TypedSwitchDevice,
    TypedSensorDevice,
    TypedLightDevice,
    TypedClimateDevice,
    TypedCoverDevice,
    create_typed_device,
)
from .helpers import get_hub_id


# ============================================================================
# === 10个核心设备类型的强类型工厂函数 ===
# ============================================================================


# 1. SL_OL - 智慧插座 (Switch平台，简单开关)
def create_typed_smart_plug() -> TypedSwitchDevice:
    """
    创建强类型的智慧插座设备 (SL_OL)。
    基于官方文档2.1.1的SL_OL真实规格。
    """
    return TypedSwitchDevice(
        agt=get_hub_id(0),
        me="sw_ol",
        devtype="SL_OL",
        name="Smart Outlet",
        data={"O": IOConfig(type=CMD_TYPE_ON, val=1)},  # 开启状态，符合文档规范
        stat=1,
        ver="0.0.0.7",
    )


# 2. SL_OE_3C - 计量插座 (Sensor平台，功率监测)
def create_typed_power_meter_plug() -> TypedSensorDevice:
    """
    创建强类型的计量插座设备 (SL_OE_3C)。
    基于官方文档2.1.2的SL_OE_3C真实规格。
    """
    return TypedSensorDevice(
        agt=get_hub_id(1),
        me="sensor_power_plug",
        devtype="SL_OE_3C",
        name="Washing Machine Plug",
        data={
            "P1": IOConfig(type=CMD_TYPE_ON, val=1),  # 开关状态
            "P2": IOConfig(v=1.5, val=1084227584),  # 累计用电量 IEEE754
            "P3": IOConfig(v=1200.0, val=1149239296),  # 当前功率 IEEE754
            "P4": IOConfig(type=CMD_TYPE_OFF, val=3000),  # 功率门限
        },
        stat=1,
        ver="0.0.0.7",
    )


# 3. SL_SW_IF3 - 三联开关 (Switch平台，多路控制)
def create_typed_switch_if3() -> TypedSwitchDevice:
    """
    创建强类型的三联开关设备 (SL_SW_IF3)。
    基于官方文档2.2.1的SL_SW_IF3真实规格。
    """
    return TypedSwitchDevice(
        agt=get_hub_id(1),
        me="sw_if3",
        devtype="SL_SW_IF3",
        fullCls="SL_SW_IF3_V2",  # 指定版本信息
        name="smart Switch",
        data={
            "L1": IOConfig(type=CMD_TYPE_ON, val=1, name="Living", v=1),
            "L2": IOConfig(type=CMD_TYPE_OFF, val=0, name="study", v=0),
            "L3": IOConfig(type=CMD_TYPE_ON, val=1, name="Kid", v=1),
        },
        stat=1,
        ver="0.0.0.7",
    )


# 4. SL_LI_WW - 调光灯泡 (Light平台，亮度+色温)
def create_typed_dimmer_light() -> TypedLightDevice:
    """
    创建强类型的调光调色灯设备 (SL_LI_WW)。
    基于官方文档2.4.3的SL_LI_WW真实规格。
    """
    return TypedLightDevice(
        agt=get_hub_id(3),
        me="light_dimmer",
        devtype="SL_LI_WW",
        fullCls="SL_LI_WW_V1",  # 指定V1版本
        name="Smart Bulb Cool Warm",
        data={
            "P1": IOConfig(type=CMD_TYPE_ON, val=100),  # 亮度100%
            "P2": IOConfig(val=27),  # 色温
        },
        stat=1,
        ver="0.0.0.7",
    )


# 5. SL_CT_RGBW - RGBW灯带 (Light平台，颜色+效果)
def create_typed_rgbw_light() -> TypedLightDevice:
    """
    创建强类型的RGBW灯带设备 (SL_CT_RGBW)。
    基于官方文档2.4.1的SL_CT_RGBW真实规格。
    """
    return TypedLightDevice(
        agt=get_hub_id(4),
        me="5b9a",
        devtype="SL_CT_RGBW",
        name="RGBW Light Strip",
        data={
            "RGBW": IOConfig(type=CMD_TYPE_ON, val=0x00FF0000),  # 绿色
            "DYN": IOConfig(type=CMD_TYPE_OFF, val=0),
        },
        stat=1,
        ver="0.0.0.7",
    )


# 6. SL_SC_THL - 环境传感器 (Sensor平台，多传感器)
def create_typed_environment_sensor() -> TypedSensorDevice:
    """
    创建强类型的环境传感器设备 (SL_SC_THL)。
    基于官方文档2.6.3的SL_SC_THL真实规格。
    """
    return TypedSensorDevice(
        agt=get_hub_id(5),
        me="sensor_env",
        devtype="SL_SC_THL",
        name="Living Room Env",
        data={
            "T": IOConfig(v=23.5, val=235),  # 温度 23.5°C (原始值*10)
            "H": IOConfig(v=65.2, val=652),  # 湿度 65.2% (原始值*10)
            "Z": IOConfig(v=800, val=800),  # 光照 800 lux
            "V": IOConfig(val=85),  # 电池电量 85%
        },
        stat=1,
        ver="0.0.0.7",
    )


# 7. SL_SC_G - 门窗传感器 (Binary Sensor平台，状态检测)
def create_typed_door_sensor() -> TypedDevice:
    """
    创建强类型的门窗传感器设备 (SL_SC_G)。
    基于官方文档2.6.1的SL_SC_G真实规格。
    """
    return TypedDevice(
        agt=get_hub_id(6),
        me="bs_door",
        devtype="SL_SC_G",
        name="Door Sensor",
        data={
            "G": IOConfig(val=0, type=0),  # 关闭状态 (0:打开, 1:关闭)
            "V": IOConfig(val=92),  # 电池电量
        },
        stat=1,
        ver="0.0.0.7",
    )


# 8. SL_DOOYA - 窗帘电机 (Cover平台，位置控制)
def create_typed_curtain_motor() -> TypedCoverDevice:
    """
    创建强类型的DOOYA窗帘电机设备 (SL_DOOYA)。
    基于官方文档2.3.2的SL_DOOYA真实规格。
    """
    return TypedCoverDevice(
        agt=get_hub_id(7),
        me="cover_dooya",
        devtype="SL_DOOYA",
        name="DOOYA Curtain Motor",
        data={
            "P1": IOConfig(
                val=100,
                type=CMD_TYPE_OFF,
            ),  # 窗帘状态: 位置100%, 没有运行 (完全打开状态)
            "P2": IOConfig(type=CMD_TYPE_OFF, val=0),  # 窗帘控制口
        },
        stat=1,
        ver="0.0.0.7",
    )


# 9. SL_NATURE - 温控面板 (Climate平台，温度控制)
def create_typed_thermostat_panel() -> TypedClimateDevice:
    """
    创建强类型的SL_NATURE超能面板温控设备。
    基于官方文档2.14.1的SL_NATURE真实规格。
    """
    return TypedClimateDevice(
        agt=get_hub_id(8),
        me="climate_nature_thermo",
        devtype="SL_NATURE",
        name="Nature Panel Thermo",
        data={
            "P1": IOConfig(type=CMD_TYPE_ON, val=1),  # 开关: 开启
            "P4": IOConfig(v=22.5, val=225),  # T当前温度 (原始值*10)
            "P5": IOConfig(val=3),  # 设备种类: 3=温控面板
            "P6": IOConfig(val=(1 << 6)),  # CFG配置: 1=风机盘管(单阀)模式
            "P7": IOConfig(val=3),  # MODE模式: 3=制冷
            "P8": IOConfig(v=24.0, val=240),  # tT目标温度 (原始值*10)
            "P9": IOConfig(val=45),  # tF目标风速: 45=中档
            "P10": IOConfig(val=15),  # F当前风速: 15=低风速
        },
        stat=1,
        ver="0.0.0.7",
    )


# 10. SL_LK_LS - 智能门锁 (Lock平台，安全设备)
def create_typed_smart_lock() -> TypedDevice:
    """
    创建强类型的智能门锁设备 (SL_LK_LS)。
    基于官方文档2.8.1的SL_LK_LS真实规格。
    """
    return TypedDevice(
        agt=get_hub_id(6),
        me="bs_lock",
        devtype="SL_LK_LS",
        name="Main Lock",
        data={
            "EVTLO": IOConfig(val=4121, type=1),  # 实时开锁信息
            "ALM": IOConfig(val=2),  # 告警信息
            "BAT": IOConfig(val=88),  # 电池电量
        },
        stat=1,
        ver="0.0.0.7",
    )


# ============================================================================
# === 组合工厂函数 ===
# ============================================================================


def create_typed_core_devices() -> List[TypedDevice]:
    """
    创建所有10个核心设备类型的强类型设备实例。

    Returns:
        包含10个核心设备类型的强类型设备列表
    """
    return [
        create_typed_smart_plug(),
        create_typed_power_meter_plug(),
        create_typed_switch_if3(),
        create_typed_dimmer_light(),
        create_typed_rgbw_light(),
        create_typed_environment_sensor(),
        create_typed_door_sensor(),
        create_typed_curtain_motor(),
        create_typed_thermostat_panel(),
        create_typed_smart_lock(),
    ]


def create_typed_devices_by_platform(platform: str) -> List[TypedDevice]:
    """
    根据平台类型创建相应的强类型设备列表。

    Args:
        platform: 平台类型 ('switch', 'sensor', 'light', etc.)

    Returns:
        指定平台的强类型设备列表
    """
    platform_device_map = {
        "switch": [
            create_typed_smart_plug(),
            create_typed_switch_if3(),
        ],
        "sensor": [
            create_typed_power_meter_plug(),
            create_typed_environment_sensor(),
        ],
        "light": [
            create_typed_dimmer_light(),
            create_typed_rgbw_light(),
        ],
        "binary_sensor": [
            create_typed_door_sensor(),
        ],
        "cover": [
            create_typed_curtain_motor(),
        ],
        "climate": [
            create_typed_thermostat_panel(),
        ],
        "lock": [
            create_typed_smart_lock(),
        ],
    }

    return platform_device_map.get(platform, [])


# ============================================================================
# === 兼容性适配器 ===
# ============================================================================


def convert_typed_devices_to_dict(typed_devices: List[TypedDevice]) -> List[dict]:
    """
    将强类型设备列表转换为字典列表，用于与现有系统兼容。

    Args:
        typed_devices: 强类型设备列表

    Returns:
        字典格式的设备列表
    """
    return [device.to_dict() for device in typed_devices]


def create_typed_device_from_dict(device_dict: dict) -> TypedDevice:
    """
    从字典创建强类型设备，用于从现有数据转换。

    Args:
        device_dict: 字典格式的设备数据

    Returns:
        强类型设备实例
    """
    # 提取基础字段
    basic_fields = {
        "agt": device_dict["agt"],
        "me": device_dict["me"],
        "devtype": device_dict["devtype"],
        "name": device_dict["name"],
        "stat": device_dict.get("stat", 1),
        "ver": device_dict.get("ver", "0.0.0.7"),
        "fullCls": device_dict.get("fullCls"),
    }

    # 转换IO数据
    io_data = {}
    for key, io_dict in device_dict.get("data", {}).items():
        io_data[key] = IOConfig(
            type=io_dict.get("type"),
            val=io_dict.get("val"),
            v=io_dict.get("v"),
            name=io_dict.get("name"),
        )

    basic_fields["data"] = io_data

    # 创建适当的强类型设备
    return create_typed_device(device_dict["devtype"], **basic_fields)
