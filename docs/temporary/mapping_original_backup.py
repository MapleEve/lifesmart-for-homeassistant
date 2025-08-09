"""
LifeSmart 设备配置映射和helper函数。

此文件包含从const.py迁移的设备映射配置和所有helper函数，
以提高代码组织性和可维护性。

主要内容:
- 设备配置helper函数
- 设备描述常量
- DEVICE_MAPPING 主配置
"""

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.components.button import ButtonDeviceClass
from homeassistant.components.climate.const import (
    HVACMode,
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
)
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfEnergy, UnitOfPower

# 处理ButtonDeviceClass.IDENTIFY的兼容性
try:
    # 在HA 2024.2.0+版本中，ButtonDeviceClass.IDENTIFY存在
    _BUTTON_IDENTIFY = ButtonDeviceClass.IDENTIFY
except AttributeError:
    # 在HA 2023.6.0版本中，ButtonDeviceClass.IDENTIFY不存在，使用None
    _BUTTON_IDENTIFY = None

# 从const.py导入需要的常量
from ..const import (
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_SET_VAL,
    CMD_TYPE_SET_CONFIG,
    CMD_TYPE_SET_RAW_ON,
    CMD_TYPE_SET_RAW_OFF,
    CMD_TYPE_SET_TEMP_DECIMAL,
)

# ================= 设备映射重构辅助函数 (Device Mapping Helper Functions) =================


def _switch_binary_on_off():
    """生成标准开关控制配置"""
    return {
        "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
        "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
    }


def _switch_light_on_off():
    """生成灯光开关控制配置"""
    return {
        "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
        "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
    }


def _switch_light_dimmer():
    """生成调光灯完整控制配置"""
    return {
        "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
        "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
        "set_brightness_on": {
            "type": CMD_TYPE_SET_RAW_ON,
            "description": "开灯设置亮度",
        },
        "set_brightness_off": {
            "type": CMD_TYPE_SET_RAW_OFF,
            "description": "关灯设置亮度",
        },
    }


def _switch_power_threshold():
    """生成功率门限控制配置"""
    return {
        "enable": {"type": CMD_TYPE_ON, "val": 1, "description": "使能"},
        "disable": {"type": CMD_TYPE_OFF, "val": 0, "description": "不使能"},
        "set_threshold_enable": {
            "type": CMD_TYPE_SET_VAL,
            "description": "使能并且设置门限",
        },
        "set_threshold_disable": {
            "type": CMD_TYPE_SET_CONFIG,
            "description": "不使能并且设置门限",
        },
    }


def _binary_switch_io(io_port, description="开关", detail_desc=None):
    """生成二进制开关IO端口配置"""
    if detail_desc is None:
        detail_desc = _BINARY_SWITCH_DESC
    return {
        io_port: {
            "description": description,
            "rw": "RW",
            "data_type": "binary_switch",
            "conversion": "type_bit_0",
            "detailed_description": detail_desc,
            "commands": _switch_binary_on_off(),
        }
    }


def _light_switch_io(io_port, description="开关"):
    """生成灯光开关IO端口配置"""
    return {
        io_port: {
            "description": description,
            "rw": "RW",
            "data_type": "binary_switch",
            "conversion": "type_bit_0",
            "detailed_description": _BINARY_SWITCH_DESC,
            "commands": _switch_light_on_off(),
        }
    }


def _dimmer_light_io(io_port, description="亮度"):
    """生成调光灯IO端口配置"""
    return {
        io_port: {
            "description": description,
            "rw": "RW",
            "data_type": "brightness_switch",
            "conversion": "brightness",
            "detailed_description": "`type&1==1` 表示开灯，`val` 为亮度(1-100)；`type&1==0` 表示关灯(忽略 `val` 值)",
            "commands": _switch_light_dimmer(),
        }
    }


def _energy_sensor_io(io_port="P2"):
    """生成用电量传感器IO端口配置"""
    return {
        io_port: {
            "description": "用电量",
            "rw": "R",
            "data_type": "energy",
            "conversion": "ieee754_float",
            "detailed_description": "为累计用电量，`val` 值为 `IEEE754` 浮点数的32位整数表示，`v` 值为浮点数，单位为度(kwh)",
            "device_class": SensorDeviceClass.ENERGY,
            "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
            "state_class": SensorStateClass.TOTAL_INCREASING,
        }
    }


def _power_sensor_io(io_port="P3"):
    """生成功率传感器IO端口配置"""
    return {
        io_port: {
            "description": "功率",
            "rw": "R",
            "data_type": "power",
            "conversion": "ieee754_float",
            "detailed_description": "为当前负载功率，`v` 值为浮点数，单位为w",
            "device_class": SensorDeviceClass.POWER,
            "unit_of_measurement": UnitOfPower.WATT,
            "state_class": SensorStateClass.MEASUREMENT,
        }
    }


def _power_threshold_switch_io(io_port="P4"):
    """生成功率门限开关IO端口配置"""
    return {
        io_port: {
            "description": "功率门限",
            "rw": "RW",
            "data_type": "power_threshold",
            "conversion": "val_direct",
            "detailed_description": "功率门限，用电保护，值为整数，超出门限则会断电，单位为w",
            "commands": _switch_power_threshold(),
        }
    }


def _indicator_light_io(io_port, description):
    """生成指示灯IO端口配置"""
    return {
        io_port: {
            "description": description,
            "rw": "RW",
            "data_type": "indicator_light",
            "conversion": "val_direct",
            "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，取值范围：0~1023",
            "commands": _switch_light_dimmer(),
        }
    }


def _multi_switch_device(name, switch_ports):
    """生成多路开关控制器设备配置"""
    config = {"name": name, "switch": {}}

    for port in switch_ports:
        config["switch"].update(_binary_switch_io(port))

    return config


def _star_switch_device(name, switch_ports, temp_sensor_port):
    """生成恒星开关系列设备配置"""
    config = {
        "name": name,
        "switch": {},
        "sensor": _temperature_sensor_io(temp_sensor_port),
    }

    for port in switch_ports:
        config["switch"].update(_binary_switch_io(port))

    return config


def _energy_monitoring_outlet(switch_port="P1"):
    """生成计量插座完整配置"""
    return {
        "switch": _binary_switch_io(switch_port),
        "sensor": {**_energy_sensor_io(), **_power_sensor_io()},
        "switch_extra": _power_threshold_switch_io(),
    }


# ================= 开关描述常量 (Switch Description Constants) =================
_SWITCH_DESC_1 = "第一路开关控制口"
_SWITCH_DESC_2 = "第二路开关控制口"
_SWITCH_DESC_3 = "第三路开关控制口"

# ================= 灯光描述常量 (Light Description Constants) =================
_LIGHT_DARK_1 = "第一路关状态时指示灯亮度"
_LIGHT_DARK_2 = "第二路关状态时指示灯亮度"
_LIGHT_DARK_3 = "第三路关状态时指示灯亮度"
_LIGHT_BRIGHT_1 = "第一路开状态时指示灯亮度"
_LIGHT_BRIGHT_2 = "第二路开状态时指示灯亮度"
_LIGHT_BRIGHT_3 = "第三路开状态时指示灯亮度"
_LIGHT_DARK_SINGLE = "关状态时指示灯亮度"
_LIGHT_BRIGHT_SINGLE = "开状态时指示灯亮度"

# ================= RGBW 灯光详细描述常量 =================
_RGBW_LIGHT_DESC = "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White（当 White>0 时，表示动态模式）具体动态值请参考：附录3.1动态颜色（`DYN`）定义"

# ================= 命令描述常量 (Command Description Constants) =================
_CMD_SET_COLOR_ON = "开灯并设置颜色或动态值，val=颜色或动态值"
_CMD_SET_COLOR_OFF = "关灯并设置颜色值或动态值，val=颜色或动态值"

# ================= 通用详细描述常量 (Common Detailed Description Constants) =================
_BINARY_SWITCH_DESC = (
    "`type&1==1` 表示打开(忽略 `val` 值)；`type&1==0` 表示关闭(忽略 `val` 值)"
)
_BINARY_SWITCH_DESC_ALT = (
    "type&1==1,表示打开(忽略`val` 值)；type&1==0,表示关闭(忽略`val` 值)；"
)
_BATTERY_DESC_DETAIL = "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据 `val` 电压值换算的"

# ================= 窗帘控制描述常量 (Curtain Control Description Constants) =================
_CURTAIN_OPEN_DESC = "`type&1==1`表示打开窗帘"
_CURTAIN_CLOSE_DESC = "`type&1==1`表示关闭窗帘"
_CURTAIN_STOP_DESC = "`type&1==1`表示停止当前动作"
_CMD_CURTAIN_OPEN = "执行打开窗帘"
_CMD_CURTAIN_CLOSE = "执行关闭窗帘"
_CMD_CURTAIN_STOP = "执行停止窗帘"
_CURTAIN_STOP_LABEL = "停止 (stop)"
_CURTAIN_CLOSE_LABEL = "关闭窗帘 (close)"


def _rgbw_light_commands():
    """生成RGBW灯光命令配置"""
    return {
        "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
        "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
        "set_color_on": {"type": CMD_TYPE_SET_RAW_ON, "description": _CMD_SET_COLOR_ON},
        "set_color_off": {
            "type": CMD_TYPE_SET_RAW_OFF,
            "description": _CMD_SET_COLOR_OFF,
        },
    }


def _rgbw_light_io(io_port, description):
    """生成RGBW灯光IO端口配置"""
    return {
        io_port: {
            "description": description,
            "rw": "RW",
            "data_type": "rgbw_light",
            "conversion": "val_direct",
            "detailed_description": _RGBW_LIGHT_DESC,
            "commands": _rgbw_light_commands(),
        }
    }


def _multi_key_switch_with_lights(name, switch_configs, light_configs):
    """生成多键开关带指示灯配置"""
    config = {"name": name, "switch": {}, "light": {}}

    for port, desc in switch_configs.items():
        config["switch"].update(_binary_switch_io(port, desc))

    for port, desc in light_configs.items():
        config["light"].update(_rgbw_light_io(port, desc))

    return config


# ================= 传感器相关常量和函数 (Sensor Related Constants and Functions) =================
_BATTERY_DESC = "电量"
_MOTION_DESC = "移动检测"
_TEMP_DESC = "当前环境温度"
_HUMIDITY_DESC = "当前环境湿度"
_ILLUMINANCE_DESC = "当前环境光照"
_USB_VOLTAGE_DESC = "USB供电电压"
_DOOR_STATUS_DESC = "当前状态"
_VIBRATION_DESC = "震动状态"
_SMOKE_ALARM_DESC = "当前是否有烟雾告警"
_GAS_CONCENTRATION_DESC = "燃气浓度"
_CO2_CONCENTRATION_DESC = "当前CO2浓度值"
_TVOC_CONCENTRATION_DESC = "当前TVOC浓度值"
_FORMALDEHYDE_DESC = "甲醛浓度"
_NOISE_LEVEL_DESC = "噪音值"
_TEMP_DESC_DETAIL = "`val` 值表示原始温度值，它是温度值*10，`v` 值表示实际值(单位：℃)"
_TEMP_DESC_DETAIL_V2 = (
    "`val` 值表示原始温度值，它是实际温度值*10，`v` 值表示实际值(单位：℃)"
)
_HUMIDITY_DESC_DETAIL = (
    "`val` 值表示原始湿度值，它是湿度值*10，`v` 值表示实际值(单位：%)"
)
_ILLUMINANCE_DESC_DETAIL = "`val` 值表示原始光照值，`v` 值表示实际值(单位：lux)"
_MOTION_DESC_DETAIL = "`val` 值定义如下：0：没有检测到移动，1：有检测到移动"
_MOTION_DESC_DETAIL_RADAR = "`val` 值定义如下：0：没有检测到移动，非0：有检测到移动"
_BATTERY_DESC_DETAIL_ALARM = "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据`val`电压值换算的。注意：`type&1==1`表示低电报警状态"
_BUTTON_STATUS_DETAIL = "`type&1==1`表示按键处于按下状态(忽略`val` 值)；`type&1==0`表示按键处于松开状态(忽略`val` 值)"
_TAMPER_STATUS_DETAIL = "`type&1==1`则表示触发防拆警报；`type&1==0`则表示状态正常"
_USB_VOLTAGE_DETAIL = (
    "`val`表示原始电压值，若`val` 值大于430则表明供电在工作，否则表明未供电工作"
)
_DOOR_STATUS_DETAIL = "`val` 值定义如下：0：打开，1：关闭"
_DOOR_STATUS_DETAIL_TYPE = "`type&1==1`表示处于打开状态(忽略`val` 值)；`type&1==0`表示处于吸合状态(忽略`val` 值)"
_VIBRATION_DETAIL = "`val` 值定义如下：0：无震动，非0：震动"
_VIBRATION_DETAIL_TYPE = (
    "`type&1==1`表示处于震动状态；`type&1==0`表示无震动状态；`val` 值表示震动强度"
)


def _battery_sensor_io(io_port, conversion="v_field"):
    """生成电量传感器IO端口配置"""
    return {
        io_port: {
            "description": _BATTERY_DESC,
            "rw": "R",
            "data_type": "battery",
            "conversion": conversion,
            "detailed_description": _BATTERY_DESC_DETAIL,
            "device_class": SensorDeviceClass.BATTERY,
            "unit_of_measurement": PERCENTAGE,
            "state_class": SensorStateClass.MEASUREMENT,
        }
    }


def _motion_binary_sensor_io(io_port):
    """生成移动检测二进制传感器IO端口配置"""
    return {
        io_port: {
            "description": _MOTION_DESC,
            "rw": "R",
            "data_type": "motion_status",
            "conversion": "val_direct",
            "detailed_description": _MOTION_DESC_DETAIL,
            "device_class": BinarySensorDeviceClass.MOTION,
        }
    }


def _motion_sensor_device(name, motion_port, battery_port):
    """生成带电量的移动传感器设备配置"""
    return {
        "name": name,
        "binary_sensor": _motion_binary_sensor_io(motion_port),
        "sensor": _battery_sensor_io(battery_port),
    }


def _temperature_sensor_io(
    io_port, description=None, conversion="v_field", detail_desc=None
):
    """生成温度传感器IO端口配置"""
    if description is None:
        description = _TEMP_DESC
    if detail_desc is None:
        detail_desc = _TEMP_DESC_DETAIL

    return {
        io_port: {
            "description": description,
            "rw": "R",
            "data_type": "temperature",
            "conversion": conversion,
            "detailed_description": detail_desc,
            "device_class": SensorDeviceClass.TEMPERATURE,
            "unit_of_measurement": UnitOfTemperature.CELSIUS,
            "state_class": SensorStateClass.MEASUREMENT,
        }
    }


def _humidity_sensor_io(io_port, description=None):
    """生成湿度传感器IO端口配置"""
    if description is None:
        description = _HUMIDITY_DESC

    return {
        io_port: {
            "description": description,
            "rw": "R",
            "data_type": "humidity",
            "conversion": "v_field",
            "detailed_description": _HUMIDITY_DESC_DETAIL,
            "device_class": SensorDeviceClass.HUMIDITY,
            "unit_of_measurement": PERCENTAGE,
            "state_class": SensorStateClass.MEASUREMENT,
        }
    }


def _illuminance_sensor_io(io_port, description=None, unit="lx"):
    """生成光照传感器IO端口配置"""
    if description is None:
        description = _ILLUMINANCE_DESC

    return {
        io_port: {
            "description": description,
            "rw": "R",
            "data_type": "illuminance",
            "conversion": "v_field",
            "detailed_description": _ILLUMINANCE_DESC_DETAIL,
            "device_class": SensorDeviceClass.ILLUMINANCE,
            "unit_of_measurement": unit,
            "state_class": SensorStateClass.MEASUREMENT,
        }
    }


def _door_sensor_io(io_port, conversion="val_direct", detail_desc=None):
    """生成门禁传感器IO端口配置"""
    if detail_desc is None:
        detail_desc = _DOOR_STATUS_DETAIL
    return {
        io_port: {
            "description": _DOOR_STATUS_DESC,
            "rw": "R",
            "data_type": "door_status",
            "conversion": conversion,
            "detailed_description": detail_desc,
            "device_class": BinarySensorDeviceClass.DOOR,
        }
    }


def _vibration_sensor_io(io_port, conversion="val_direct", detail_desc=None):
    """生成震动传感器IO端口配置"""
    if detail_desc is None:
        detail_desc = _VIBRATION_DETAIL
    return {
        io_port: {
            "description": _VIBRATION_DESC,
            "rw": "R",
            "data_type": "vibration_status",
            "conversion": conversion,
            "detailed_description": detail_desc,
            "device_class": BinarySensorDeviceClass.VIBRATION,
        }
    }


def _button_sensor_io(io_port, description, conversion="val_direct"):
    """生成按键状态传感器IO端口配置"""
    return {
        io_port: {
            "description": description,
            "rw": "R",
            "data_type": "button_status",
            "conversion": conversion,
            "detailed_description": _BUTTON_STATUS_DETAIL,
            "device_class": BinarySensorDeviceClass.MOVING,
        }
    }


def _tamper_sensor_io(io_port):
    """生成防拆传感器IO端口配置"""
    return {
        io_port: {
            "description": "防拆状态",
            "rw": "R",
            "data_type": "tamper_status",
            "conversion": "type_bit_0",
            "detailed_description": _TAMPER_STATUS_DETAIL,
            "device_class": BinarySensorDeviceClass.TAMPER,
        }
    }


def _basic_door_sensor_device(
    name, door_port, battery_port, door_conversion="val_direct"
):
    """生成基础门窗传感器设备配置（门状态+电量）"""
    return {
        "name": name,
        "binary_sensor": _door_sensor_io(door_port, door_conversion),
        "sensor": _battery_sensor_io(battery_port),
    }


def _enhanced_door_sensor_device(name, door_port, battery_port, extra_sensors=None):
    """生成增强型门窗传感器设备配置"""
    config = {
        "name": name,
        "binary_sensor": _door_sensor_io(
            door_port, "type_bit_0", _DOOR_STATUS_DETAIL_TYPE
        ),
        "sensor": _battery_sensor_io(battery_port, "v_field"),
    }

    if extra_sensors:
        config["binary_sensor"].update(extra_sensors)

    return config


def _defed_sensor_device(
    name, main_sensor, battery_port, temp_port=None, tamper_port="TR"
):
    """生成云防系列传感器设备配置（主传感器+防拆+温度+低电报警电量）"""
    config = {
        "name": name,
        "binary_sensor": {
            **main_sensor,
            **_tamper_sensor_io(tamper_port),
        },
        "sensor": {
            **_battery_sensor_io(battery_port, "v_field"),
        },
    }

    # 电量传感器使用报警版本的详细描述
    config["sensor"][battery_port]["detailed_description"] = _BATTERY_DESC_DETAIL_ALARM

    if temp_port:
        config["sensor"].update(
            _temperature_sensor_io(
                temp_port, description="温度", detail_desc=_TEMP_DESC_DETAIL_V2
            )
        )

    return config


def _usb_voltage_sensor_io(io_port, description=None):
    """生成USB供电电压传感器IO端口配置"""
    if description is None:
        description = _USB_VOLTAGE_DESC

    return {
        io_port: {
            "description": description,
            "rw": "R",
            "data_type": "voltage",
            "conversion": "val_direct",
            "detailed_description": _USB_VOLTAGE_DETAIL,
            "device_class": SensorDeviceClass.VOLTAGE,
            "unit_of_measurement": "V",
            "state_class": SensorStateClass.MEASUREMENT,
        }
    }


def _comprehensive_env_sensor_device(name, sensors_config):
    """生成综合环境传感器设备配置"""
    return {"name": name, "sensor": sensors_config}


def _gas_sensor_device(
    name, concentration_port, threshold_port, alarm_port, gas_type="燃气"
):
    """生成气体传感器设备配置"""
    device_class_map = {
        "燃气": SensorDeviceClass.GAS,
        "甲醛": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
    }

    unit_map = {
        "燃气": "ppm",
        "甲醛": "µg/m³",
    }

    conversion_map = {
        "燃气": "val_direct",
        "甲醛": "v_field",
    }

    return {
        "name": name,
        "sensor": {
            concentration_port: {
                "description": f"{gas_type}浓度",
                "rw": "R",
                "data_type": f"{gas_type}_concentration",
                "conversion": conversion_map[gas_type],
                "detailed_description": f"`type&1==1`表示{gas_type}浓度值超过告警门限；`val` 值表示{gas_type}浓度值",
                "device_class": device_class_map[gas_type],
                "unit_of_measurement": unit_map[gas_type],
                "state_class": SensorStateClass.MEASUREMENT,
            }
        },
        "switch": {
            threshold_port: {
                "description": f"{gas_type}浓度告警门限",
                "rw": "RW",
                "data_type": "threshold_setting",
                "conversion": "val_direct",
                "detailed_description": "`val` 值越大则灵敏度越低，门限越高",
                "commands": {
                    "set_sensitivity": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "description": "设置报警器灵敏度",
                    },
                },
            },
            alarm_port: {
                "description": "警报音",
                "rw": "RW",
                "data_type": "alarm_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`指示报警音正在响，反之则没有报警音",
                "commands": {
                    "on": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "手工触发报警音",
                    },
                    "off": {
                        "type": CMD_TYPE_OFF,
                        "val": 0,
                        "description": "手动消除报警音",
                    },
                },
            },
        },
    }


def _env_sensor_device(name, sensor_ios):
    """生成环境传感器设备配置"""
    return {"name": name, "sensor": sensor_ios}


# ================= 窗帘控制辅助函数 (Curtain Control Helper Functions) =================
def _curtain_control_io(open_port, close_port, stop_port):
    """生成通用窗帘控制IO端口配置"""
    return {
        open_port: {
            "description": "打开窗帘",
            "rw": "RW",
            "data_type": "binary_switch",
            "conversion": "type_bit_0",
            "detailed_description": _CURTAIN_OPEN_DESC,
            "commands": {
                "on": {
                    "type": CMD_TYPE_ON,
                    "val": 1,
                    "description": _CMD_CURTAIN_OPEN,
                },
            },
        },
        stop_port: {
            "description": _CURTAIN_STOP_LABEL,
            "rw": "RW",
            "data_type": "binary_switch",
            "conversion": "type_bit_0",
            "detailed_description": _CURTAIN_STOP_DESC,
            "commands": {
                "on": {
                    "type": CMD_TYPE_ON,
                    "val": 1,
                    "description": _CMD_CURTAIN_STOP,
                },
            },
        },
        close_port: {
            "description": _CURTAIN_CLOSE_LABEL,
            "rw": "RW",
            "data_type": "binary_switch",
            "conversion": "type_bit_0",
            "detailed_description": _CURTAIN_CLOSE_DESC,
            "commands": {
                "on": {
                    "type": CMD_TYPE_ON,
                    "val": 1,
                    "description": _CMD_CURTAIN_CLOSE,
                },
            },
        },
    }


def _basic_curtain_device(name, open_port, close_port, stop_port):
    """生成基础窗帘控制设备配置"""
    return {
        "name": name,
        "cover": _curtain_control_io(open_port, close_port, stop_port),
    }


def _switch_companion_device(name, switch_ports, battery_port):
    """生成开关伴侣设备配置（带电量传感器）"""
    config = {"name": name, "switch": {}, "sensor": _battery_sensor_io(battery_port)}

    for i, port in enumerate(switch_ports, 1):
        desc = (
            [_SWITCH_DESC_1, _SWITCH_DESC_2, _SWITCH_DESC_3][i - 1]
            if i <= 3
            else f"第{i}路开关控制口"
        )
        config["switch"].update(_binary_switch_io(port, desc))

    return config


def _singularity_switch_device(name, switch_ports):
    """生成奇点开关模块设备配置"""
    config = {"name": name, "switch": {}}

    for port in switch_ports:
        config["switch"].update(
            _binary_switch_io(port, "开关", _BINARY_SWITCH_DESC_ALT)
        )

    return config


# ================= 调光开关辅助函数 (Dimmer Switch Helper Functions) =================
def _pwm_dimmer_io(io_port, description="开关", brightness_range="0-255"):
    """生成PWM调光开关IO端口配置"""
    return {
        io_port: {
            "description": description,
            "rw": "RW",
            "data_type": "dimmer_switch",
            "conversion": "type_bit_0",
            "detailed_description": f"type&1==1 表示处于打开状态；type&1==0 表示处于关闭状态；val 值为亮度值，可调范围：[{brightness_range}]，值越大表示光越亮，0处于最暗，光完全熄灭，255处于最亮",
            "commands": {
                "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                "set_brightness_on": {
                    "type": CMD_TYPE_SET_VAL,
                    "description": "打开并且设置亮度，val=亮度值[0,255]",
                },
                "set_brightness_off": {
                    "type": CMD_TYPE_SET_CONFIG,
                    "description": "关闭并设置亮度，val=亮度值[0,255]",
                },
            },
        }
    }


def _brightness_light_io(
    io_port, description, brightness_range="0-255", brightness_desc=None
):
    """生成亮度控制灯光IO端口配置"""
    if brightness_desc is None:
        brightness_desc = f"`type&1==1`表示处于打开状态；`type&1==0`表示处于关闭状态；`val` 值为亮度值，可调范围：[{brightness_range}], 值越大表示光越亮，0处于最暗，光完全熄灭，255处于最亮"

    return {
        io_port: {
            "description": description,
            "rw": "RW",
            "data_type": "brightness_light",
            "conversion": "val_direct",
            "range": brightness_range,
            "detailed_description": brightness_desc,
            "commands": {
                "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                "set_brightness": {
                    "type": CMD_TYPE_SET_VAL,
                    "description": f"设置亮度，val=亮度值[{brightness_range}]",
                },
            },
        }
    }


def _color_temp_io(io_port, description="色温控制", temp_range="0-255"):
    """生成色温控制IO端口配置"""
    return {
        io_port: {
            "description": description,
            "rw": "RW",
            "data_type": "color_temperature",
            "conversion": "val_direct",
            "range": temp_range,
            "detailed_description": f"`val` 值为色温值，取值范围[{temp_range}]，0表示暖光，255表示冷光",
            "commands": {
                "set_color_temp": {
                    "type": CMD_TYPE_SET_VAL,
                    "description": f"设置色温，val=色温值[{temp_range}]",
                },
            },
        }
    }


def _nightlight_io(
    io_port, description="夜灯亮度控制", brightness_levels="0、63、127、195、255"
):
    """生成夜灯控制IO端口配置"""
    return {
        io_port: {
            "description": description,
            "rw": "RW",
            "data_type": "nightlight_brightness",
            "conversion": "val_direct",
            "range": "0,63,127,195,255",
            "detailed_description": f"`val` 值为夜灯亮度，共有5档，亮度从低到高分别如下：{brightness_levels}。0表示夜灯处于关闭状态，255表示夜灯处于最亮状态。注意：若亮度值为其它值则根据如下规则判断亮度档位：0：关闭档，>=196：最亮档，>=128并且<=195：次亮档，>=64并且<=127：第三亮档，>0并且<=63：第四亮档",
            "commands": {
                "set_brightness": {
                    "type": CMD_TYPE_SET_VAL,
                    "description": f"设置亮度，val=亮度值[{brightness_levels}]",
                },
            },
        }
    }


# ================= 通用RGBW灯光辅助函数 (Universal RGBW Light Helper Functions) =================
def _rgbw_device(name, rgbw_port="RGBW", dyn_port="DYN", has_dynamic=True):
    """生成标准RGBW灯光设备配置"""
    config = {"name": name, "light": _rgbw_light_io(rgbw_port, "RGBW颜色值")}

    if has_dynamic:
        config["light"].update(
            {
                dyn_port: {
                    "description": "动态颜色值",
                    "rw": "RW",
                    "data_type": "dynamic_effect",
                    "conversion": "val_direct",
                    "detailed_description": "`type&1==1`表示打开动态；`type&1==0`表示关闭动态；`val`表示动态颜色值，具体动态值请参考：附录3.2 动态颜色（DYN）定义",
                    "commands": {
                        "enable": {
                            "type": CMD_TYPE_ON,
                            "val": 1,
                            "description": "使能",
                        },
                        "disable": {
                            "type": CMD_TYPE_OFF,
                            "val": 0,
                            "description": "关闭",
                        },
                        "set_effect_on": {
                            "type": CMD_TYPE_SET_RAW_ON,
                            "description": "使能并设置动态值，val=动态值",
                        },
                        "set_effect_off": {
                            "type": CMD_TYPE_SET_RAW_OFF,
                            "description": "关闭并设置动态值，val=动态值",
                        },
                    },
                }
            }
        )

    return config


def _rgb_device(name, rgb_port="RGB"):
    """生成RGB灯光设备配置（无白光）"""
    return {
        "name": name,
        "light": {
            rgb_port: {
                "description": "RGB颜色值",
                "rw": "RW",
                "data_type": "rgb_light",
                "conversion": "val_direct",
                "range": "0x00000000-0xFFFFFFFF",
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭；`val` 值为颜色值，大小4个字节，定义如下：`bit0`~`bit7`:Blue, `bit8`~`bit15`:Green, `bit16`~`bit23`:Red, `bit24`~`bit31`:White, （当White>0时，表示动态模式）具体动态值请参考：附录3.2动态颜色(DYN)定义",
                "commands": _rgbw_light_commands(),
            }
        },
    }


def _brightness_color_temp_device(
    name, brightness_port="P1", temp_port="P2", night_port=None
):
    """生成亮度+色温控制设备配置"""
    config = {
        "name": name,
        "light": {
            **_brightness_light_io(brightness_port, "亮度控制"),
            **_color_temp_io(temp_port),
        },
    }

    if night_port:
        config["light"].update(_nightlight_io(night_port))

    return config


# ================= 开关带指示灯辅助函数 (Switch with Light Helper Functions) =================
def _single_switch_with_lights(name, switch_port="L1"):
    """生成单键开关带指示灯配置"""
    return _multi_key_switch_with_lights(
        name,
        {switch_port: _SWITCH_DESC_1},
        {"dark": _LIGHT_DARK_SINGLE, "bright": _LIGHT_BRIGHT_SINGLE},
    )


def _switch_with_indicator_device(name, switch_ports, has_bright_lights=True):
    """生成开关控制器带指示灯设备配置"""
    config = {"name": name, "switch": {}, "light": {}}

    # 添加开关端口
    for i, port in enumerate(switch_ports, 1):
        desc = (
            [_SWITCH_DESC_1, _SWITCH_DESC_2, _SWITCH_DESC_3][i - 1]
            if i <= 3
            else f"第{i}路开关控制口"
        )
        config["switch"].update(_binary_switch_io(port, desc))

    # 添加指示灯端口
    light_descs = [_LIGHT_DARK_1, _LIGHT_DARK_2, _LIGHT_DARK_3]
    bright_descs = [_LIGHT_BRIGHT_1, _LIGHT_BRIGHT_2, _LIGHT_BRIGHT_3]

    for i in range(len(switch_ports)):
        if i < 3:
            config["light"].update(_rgbw_light_io(f"dark{i+1}", light_descs[i]))
            if has_bright_lights:
                config["light"].update(_rgbw_light_io(f"bright{i+1}", bright_descs[i]))

    return config


# ================= 窗帘指示灯辅助函数 (Curtain Indicator Light Helper Functions) =================
def _curtain_indicator_lights_io(brightness_range="0~1023"):
    """生成窗帘控制开关的指示灯IO配置"""
    return {
        "dark": {
            "description": "关闭状态时指示灯亮度",
            "rw": "RW",
            "data_type": "brightness_light",
            "conversion": "val_direct",
            "range": brightness_range,
            "detailed_description": f"`type&1==1`表示打开；`type&1==0`表示关闭；`val`表示指示灯亮度值，取值范围：{brightness_range}",
            "commands": _switch_light_dimmer(),
        },
        "bright": {
            "description": "开启状态时指示灯亮度",
            "rw": "RW",
            "data_type": "brightness_light",
            "conversion": "val_direct",
            "range": brightness_range,
            "detailed_description": f"`val`表示指示灯亮度值，取值范围：{brightness_range}",
            "commands": _switch_light_dimmer(),
        },
    }


def _curtain_rgbw_lights_io(descriptions):
    """生成窗帘控制器的RGBW指示灯IO配置"""
    config = {}
    for port, desc in descriptions.items():
        config[port] = {
            "description": desc,
            "rw": "RW",
            "data_type": "rgbw_light",
            "conversion": "val_direct",
            "detailed_description": _RGBW_LIGHT_DESC,
            "commands": _rgbw_light_commands(),
        }
    return config


def _quantum_light_device(name):
    """生成量子灯设备配置"""
    return {
        "name": name,
        "light": {
            **_brightness_light_io(
                "P1",
                "亮度控制",
                "0-100",
                "`type&1==1`表示打开(忽略`val` 值)；`type&1==0`表示关闭(忽略`val` 值)；`val`指示灯光的亮度值范围[0,100]，100亮度最大",
            ),
            "P2": {
                "description": "颜色控制",
                "rw": "RW",
                "data_type": "quantum_light",
                "conversion": "val_direct",
                "range": "0x00000000-0xFFFFFFFF",
                "detailed_description": "`val` 值为颜色值，大小4个字节，定义如下：`bit0`~`bit7`:Blue, `bit8`~`bit15`:Green, `bit16`~`bit23`:Red, `bit24~bit31`:White, （当White>0时，表示动态模式）具体动态值请参考：附录3.2动态颜色(DYN)定义, 附录3.3量子灯特殊(DYN)定义",
                "commands": {
                    "set_color": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "设置颜色或动态值，val=颜色或动态值",
                    },
                },
            },
        },
    }


def _motion_light_device(
    name, light_port, motion_port, illuminance_port, brightness_range="0-255"
):
    """生成带移动检测的灯光设备配置"""
    return {
        "name": name,
        "light": _brightness_light_io(light_port, "开关", brightness_range),
        "binary_sensor": _motion_binary_sensor_io(motion_port),
        "sensor": _illuminance_sensor_io(illuminance_port, unit="lux"),
    }


def _garden_light_device(name):
    """生成花园地灯设备配置"""
    return {
        "name": name,
        "light": {
            "P1": {
                "description": "开关/颜色设置",
                "rw": "RW",
                "data_type": "rgbw_light",
                "conversion": "val_direct",
                "range": "0x00000000-0xFFFFFFFF",
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭；`val` 值为颜色值，大小4个字节，定义如下：- `bit0~bit7`: Blue - `bit8~bit15`: Green - `bit16~bit23`: Red - `bit24~bit31`: White/DYN。例如：红色：`0x00FF0000`, 白色：`0xFF000000`。`bit24~bit31`即可以设置白光又可以设置动态。当其值在[0~100]表示设置的是白光，0表示不显示白光，100表示白光最亮；当其值大于等于128表示设置为动态模式，具体动态值请参考：附录3.2 动态颜色(DYN)定义",
                "commands": _rgbw_light_commands(),
            }
        },
        "sensor": {
            **_illuminance_sensor_io("P2", unit="lux"),
            "P3": {
                "description": "充电指示",
                "rw": "R",
                "data_type": "charging_status",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0：没有充电, 1：正在充电，`val`表示原始电压值",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": "V",
                "state_class": SensorStateClass.MEASUREMENT,
            },
            **_battery_sensor_io("P4"),
        },
    }


def _defed_base_device(name, main_sensor, extra_sensors=None):
    """生成云防系列基础设备配置（主传感器+防拆+温度+低电报警电量）"""
    config = {
        "name": name,
        "binary_sensor": {
            **main_sensor,
            **_tamper_sensor_io("TR"),
        },
        "sensor": {
            **_temperature_sensor_io("T", detail_desc=_TEMP_DESC_DETAIL_V2),
            "V": {
                "description": _BATTERY_DESC,
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": _BATTERY_DESC_DETAIL_ALARM,
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    }

    if extra_sensors:
        config["binary_sensor"].update(extra_sensors)

    return config


def _defed_door_sensor_device(name):
    """生成云防门窗感应器设备配置"""
    main_sensor = {
        "A": {
            "description": "当前状态",
            "rw": "R",
            "data_type": "door_status",
            "conversion": "type_bit_0",
            "detailed_description": _DOOR_STATUS_DETAIL_TYPE,
            "device_class": BinarySensorDeviceClass.DOOR,
        }
    }
    extra_sensors = {
        "A2": {
            "description": "外部感应器状态",
            "rw": "R",
            "data_type": "door_status",
            "conversion": "type_bit_0",
            "detailed_description": "`type&1==1`表示处于打开状态(忽略`val` 值)；`type&1==0`表示处于吸合状态(忽略`val` 值)；需要接外部感应器，如果没有接则type值为1",
            "device_class": BinarySensorDeviceClass.DOOR,
        }
    }
    return _defed_base_device(name, main_sensor, extra_sensors)


def _siren_control_commands():
    """生成警铃控制命令配置"""
    return {
        "on": {"type": CMD_TYPE_ON, "val": 1, "description": "播放"},
        "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "停止"},
        "set_config_on": {
            "type": CMD_TYPE_SET_RAW_ON,
            "description": "设置值并播放",
        },
        "set_config_off": {
            "type": CMD_TYPE_SET_RAW_OFF,
            "description": "设置值并停止",
        },
    }


def _single_command_set_config(description):
    """生成单个SET_CONFIG命令配置"""
    return {
        "set_config": {
            "type": CMD_TYPE_SET_CONFIG,
            "description": description,
        }
    }


def _single_command_set_mode():
    """生成设置模式命令配置"""
    return _single_command_set_config("设置模式")


def _single_command_set_fan_speed():
    """生成设置风速命令配置"""
    return _single_command_set_config("设置风速")


def _co2_concentration_sensor_io(io_port):
    """生成CO2浓度传感器IO端口配置"""
    return {
        io_port: {
            "description": "当前CO2浓度值",
            "rw": "R",
            "data_type": "co2_concentration",
            "conversion": "v_field",
            "detailed_description": "`val` 值表示co2浓度值，`v` 值表示实际值(单位：ppm)，参考：`val`<=500：优，`val`<=700：良，`val`<=1000：中，`val`>1000：差",
            "device_class": SensorDeviceClass.CO2,
            "unit_of_measurement": "ppm",
            "state_class": SensorStateClass.MEASUREMENT,
        }
    }


def _defed_keyfob_buttons():
    """生成云防遥控器4个按键的配置"""
    button_descriptions = {
        "eB1": "按键1状态(为布防图标)",
        "eB2": "按键2状态(为撤防图标)",
        "eB3": "按键3状态(为警告图标)",
        "eB4": "按键4状态(为在家图标)",
    }

    config = {}
    for port, desc in button_descriptions.items():
        config[port] = {
            "description": desc,
            "rw": "R",
            "data_type": "button_status",
            "conversion": "type_bit_0",
            "detailed_description": "`type&1==1`表示按键处于按下状态(忽略`val` 值)；`type&1==0`表示按键处于松开状态(忽略`val` 值)",
            "device_class": BinarySensorDeviceClass.MOVING,
        }

    return config


# ================= 温控器映射 (Climate Mappings) =================
# 用于在 Home Assistant 的标准 HVAC 模式与 LifeSmart 的私有模式值之间进行转换。

# --- V_AIR_P (智控器空调面板) 模式映射 ---
LIFESMART_F_HVAC_MODE_MAP = {
    1: HVACMode.AUTO,
    2: HVACMode.FAN_ONLY,
    3: HVACMode.COOL,
    4: HVACMode.HEAT,
}
REVERSE_F_HVAC_MODE_MAP = {v: k for k, v in LIFESMART_F_HVAC_MODE_MAP.items()}

# --- SL_UACCB, SL_NATURE, SL_FCU 等设备的模式映射 ---
# 这个映射包含了地暖等特殊模式
LIFESMART_HVAC_MODE_MAP = {
    1: HVACMode.AUTO,
    2: HVACMode.FAN_ONLY,
    3: HVACMode.COOL,
    4: HVACMode.HEAT,
    5: HVACMode.DRY,
    7: HVACMode.HEAT,  # SL_NATURE/FCU 地暖模式
    8: HVACMode.HEAT_COOL,  # SL_NATURE/FCU 地暖+空调模式
}
# 注意：由于一个HA模式可能对应多个设备模式，反向映射只用于那些没有歧义的设备
REVERSE_LIFESMART_HVAC_MODE_MAP = {
    HVACMode.AUTO: 1,
    HVACMode.FAN_ONLY: 2,
    HVACMode.COOL: 3,
    HVACMode.HEAT: 4,  # 默认将制热映射回 4
    HVACMode.DRY: 5,
    HVACMode.HEAT_COOL: 8,
}


# --- SL_CP_AIR (风机盘管) 模式与风速映射 (来自P1 bitmask) ---
LIFESMART_CP_AIR_HVAC_MODE_MAP = {
    0: HVACMode.COOL,
    1: HVACMode.HEAT,
    2: HVACMode.FAN_ONLY,
}
REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP = {
    v: k for k, v in LIFESMART_CP_AIR_HVAC_MODE_MAP.items()
}

# --- SL_TR_ACIPM (新风) 风速映射 ---
LIFESMART_ACIPM_FAN_MAP = {
    FAN_LOW: 1,
    FAN_MEDIUM: 2,
    FAN_HIGH: 3,
}
REVERSE_LIFESMART_ACIPM_FAN_MAP = {v: k for k, v in LIFESMART_ACIPM_FAN_MAP.items()}

# --- SL_CP_AIR (风机盘管) 风速映射 (P1 bitmask) ---
LIFESMART_CP_AIR_FAN_MAP = {
    FAN_AUTO: 0,
    FAN_LOW: 1,
    FAN_MEDIUM: 2,
    FAN_HIGH: 3,
}
REVERSE_LIFESMART_CP_AIR_FAN_MAP = {v: k for k, v in LIFESMART_CP_AIR_FAN_MAP.items()}

# --- SL_NATURE / SL_FCU (超能面板) 风速映射 (tF) ---
LIFESMART_TF_FAN_MAP = {
    FAN_AUTO: 101,
    FAN_LOW: 15,
    FAN_MEDIUM: 45,
    FAN_HIGH: 75,
}
REVERSE_LIFESMART_TF_FAN_MODE_MAP = {v: k for k, v in LIFESMART_TF_FAN_MAP.items()}

# --- V_AIR_P 风速映射 (F) ---
LIFESMART_F_FAN_MAP = {
    FAN_LOW: 15,
    FAN_MEDIUM: 45,
    FAN_HIGH: 75,
}
REVERSE_LIFESMART_F_FAN_MODE_MAP = {v: k for k, v in LIFESMART_F_FAN_MAP.items()}

# --- 动态分类设备列表 (Dynamic Classification Devices) ---
# 这些设备的平台归属由 helpers.py 中的逻辑决定
DYNAMIC_CLASSIFICATION_DEVICES = {
    "SL_NATURE",  # 根据P5值决定是开关版还是温控版
    "SL_P",  # 根据P1工作模式决定功能
    "SL_JEMA",  # 同SL_P，但额外支持P8/P9/P10独立开关
}

# --- 需要根据fullCls区分版本的设备类型 ---
# 注意：只有在IO口和功能上真正有差异的设备才需要版本区分
VERSIONED_DEVICE_TYPES = {
    # 调光开关系列 - 根据fullCls区分不同版本功能
    "SL_SW_DM1": {
        # SL_SW_DM1_V1为动态调光开关 - 具有传感器和智能控制功能
        # IO口: P1(开关+亮度 RW) P2(指示灯 RW) P3(移动检测 R) P4(环境光照 R) P5(调光设置 RW) P6(动态设置 RW)
        "V1": "motion_dimmer",
        # SL_SW_DM1_V2为星玉调光开关(可控硅) - 基础调光功能
        # IO口: P1(开关+亮度 RW) P2(指示灯亮度 RW)
        "V2": "triac_dimmer",
    },
    # 白光调光灯版本区分 - 基于相同的IO口功能
    "SL_LI_WW": {
        # SL_LI_WW_V1智能灯泡(冷暖白) - 同SL_LI_WW规范
        # IO口: P1(亮度控制 RW) P2(色温控制 RW)
        "V1": "dimmable_light_v1",
        # SL_LI_WW_V2调光调色智控器(0-10V) - 同SL_LI_WW规范
        # IO口: P1(亮度控制 RW) P2(色温控制 RW)
        "V2": "dimmable_light_v2",
    },
}

# --- Home Assistant 平台支持已迁移到const.py ---

# ================= 技术定义 (Technical Constants) =================

# 第三方设备版本映射 - 参考官方文档附录3.6
# 当设备通过通用控制器接入第三方设备时，可根据ver值判别具体设备型号
THIRD_PARTY_DEVICES = {
    "V_AIR_P": {
        "0.0.0.1": {
            "code": "000001",
            "model": "DTA116A621",
            "name": "大金空调DTA116A621",
        },
        "0.0.0.2": {"code": "000002", "model": "KRAVEN_VRV", "name": "空调VRV控制器"},
        "0.0.0.7": {"code": "000007", "model": "TM8X", "name": "特灵"},
        "0.0.0.10": {"code": "00000A", "model": "KL420", "name": "开利420C"},
        "0.0.0.15": {
            "code": "00000F",
            "model": "MEDIA-CCM18",
            "name": "美的多联机MODBUS网关-CCM18",
        },
        "0.0.0.17": {
            "code": "000011",
            "model": "PHNIX-ST800",
            "name": "芬尼ST800二合一温控面板",
        },
        "0.0.0.18": {
            "code": "000012",
            "model": "SHINEFAN-G9",
            "name": "祥帆新风G9面板",
        },
        "0.0.0.19": {
            "code": "000013",
            "model": "TCB-IFMB646TLE",
            "name": "东芝空调网关TCB-IFMB646TLE",
        },
        "0.0.0.21": {
            "code": "000015",
            "model": "THT420B",
            "name": "开利空调面板THT420B",
        },
        "0.0.0.24": {
            "code": "000018",
            "model": "NetproDual",
            "name": "NetPro Dual DAIKIN",
        },
        "0.0.0.31": {"code": "00001F", "model": "CLP5DO", "name": "三恒系统"},
    },
    "V_FRESH_P": {
        "0.0.0.3": {"code": "000003", "model": "KV11_RTU", "name": "艾弗纳KV11"},
        "0.0.0.8": {"code": "000008", "model": "CA-S2", "name": "森德"},
        "0.0.0.22": {
            "code": "000016",
            "model": "NAVIEN-TAC550",
            "name": "NAVIEN新风主机NAVIEN-TAC550",
        },
        "0.0.0.23": {
            "code": "000017",
            "model": "KD-1-E",
            "name": "兰舍新风控制器KD-1-E",
        },
        "0.0.0.31": {"code": "00001F", "model": "CLP5DO", "name": "三恒系统"},
    },
    "V_485_P": {
        "0.0.0.12": {
            "code": "00000C",
            "model": "RY-A101",
            "name": "气体压力传感器RY_A101",
        },
        "0.0.0.13": {"code": "00000D", "model": "KL-19XR", "name": "KL-19XR"},
        "0.0.0.25": {"code": "000019", "model": "GD-H2S", "name": "GD-H2S"},
        "0.0.0.26": {
            "code": "00001A",
            "model": "HQ100-S12",
            "name": "智能照明控制模块HQ100-S12",
        },
        "0.0.0.27": {"code": "00001B", "model": "DTSR958", "name": "导轨电能表"},
        "0.0.0.28": {
            "code": "00001C",
            "model": "ZXB1L-125",
            "name": "智能断路器ZXB1L-125",
        },
        "0.0.0.29": {
            "code": "00001D",
            "model": "ZXB1L-3-125",
            "name": "智能断路器3相ZXB1L-3-125",
        },
        "0.0.0.30": {
            "code": "00001E",
            "model": "HD120A16GK",
            "name": "HDHK智能电流采集器HD120A16GK",
        },
        "0.0.0.32": {
            "code": "000020",
            "model": "BF-12LI",
            "name": "BF-12LI智能采集模块",
        },
    },
    "V_DLT645_P": {
        "0.0.0.6": {"code": "000006", "model": "DLT645", "name": "DLT645"},
    },
}


# ================= 动态效果映射 (Dynamic Effects Mappings) =================
# --- 通用动态效果 ---
# 动态颜色（DYN）定义 - 参考官方文档附录3.2
# 这些值用于设备的动态颜色效果，如彩灯、开关指示灯等
DYN_EFFECT_MAP = {
    "青草": 0x8218CC80,
    "海浪": 0x8318CC80,
    "深蓝山脈": 0x8418CC80,
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
# 量子灯特殊（DYN）定义 - 参考官方文档附录3.3
# 量子灯专用的特殊动态效果
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
    "听音变色": 0x07BD0990,  # 第二代量子灯才支持
}

# 将动态效果和量子灯光效果映射合并
DYN_EFFECT_LIST = list(DYN_EFFECT_MAP.keys())
ALL_EFFECT_MAP = {**DYN_EFFECT_MAP, **QUANTUM_EFFECT_MAP}
ALL_EFFECT_LIST = list(ALL_EFFECT_MAP.keys())


# 无位置窗帘配置映射 (用于将开/关/停动作映射到正确的IO口)
NON_POSITIONAL_COVER_CONFIG = {
    "SL_SW_WIN": {"open": "OP", "close": "CL", "stop": "ST"},
    "SL_P_V2": {
        "open": "P2",
        "close": "P3",
        "stop": "P4",
    },  # 不是版本设备，真实设备名称
    "SL_CN_IF": {"open": "P1", "close": "P2", "stop": "P3"},
    "SL_CN_FE": {"open": "P1", "close": "P2", "stop": "P3"},
    # 通用控制器
    "SL_P": {"open": "P2", "close": "P3", "stop": "P4"},
    "SL_JEMA": {"open": "P2", "close": "P3", "stop": "P4"},
}


# ================= 平台聚合已废弃 (Platform Aggregation Deprecated) =================
# 注意：ALL_*_TYPES聚合列表已被完全废弃并移除。
#
# 🔄 **新的设备平台映射架构**：
# - 使用 helpers.py 中的 get_device_platform_mapping() 函数获取设备支持的平台
# - 基于 MULTI_PLATFORM_DEVICE_MAPPING精确映射
# - 支持单设备多平台，避免了设备重复定义问题
# - 动态分类设备（如SL_NATURE、SL_P）根据IO状态自动判断平台归属
#
# 📋 **迁移指南**：
# - 旧代码: `if device_type in ALL_SWITCH_TYPES`
# - 新代码: `platforms = get_device_platform_mapping(devices);`
#           `if Platform.SWITCH in platforms`
#
# 🔍 **技术优势**：
# - ✅ 消除设备重复定义
# - ✅ 支持多平台设备（如SL_OL_W：开关+灯光）
# - ✅ 动态分类（如超能面板根据配置变化功能）
# - ✅ IO口级别的精确控制
# - ✅ 更好的可维护性和扩展性

# ================= 智能门锁辅助函数 (Smart Lock Helper Functions) =================


def _smart_lock_common_sensors():
    """生成智能门锁共同的传感器配置（BAT, ALM, EVTLO, HISLK）"""
    return {
        "BAT": {
            "description": "电量",
            "rw": "R",
            "data_type": "battery",
            "conversion": "val_direct",
            "detailed_description": "`Val`表示电量值",
            "device_class": SensorDeviceClass.BATTERY,
            "unit_of_measurement": PERCENTAGE,
            "state_class": SensorStateClass.MEASUREMENT,
        },
        "ALM": {
            "description": "告警信息",
            "rw": "R",
            "data_type": "alarm_status",
            "conversion": "val_direct",
            "detailed_description": "`val` 值定义如下: `bit0`：1为错误报警（输入错误密码或指纹 或卡片超过10次就报警) `bit1`：1为劫持报警（输入防劫持密码或防 劫持指纹开锁就报警) `bit2`：1为防撬报警 (锁被撬开) `bit3`：1为机械钥匙报警（使用机械钥匙开 `bit4`：1为低电压报警（电池电量不足) `bit5`：1为异动告警 `bit6`：1为门铃 `bit7`：1为火警 `bit8`：1为入侵告警 `bit11`：1为恢复出厂告警",
        },
        "EVTLO": {
            "description": "实时开锁",
            "rw": "R",
            "data_type": "lock_event",
            "conversion": "val_direct",
            "detailed_description": "`type&1==1`表示打开； `type&1==0` 表示关闭； `val` 值定义如下: `bit0~11`表示用户编号; 0：未定义； 1：密码； 2：指纹； 3:`NFC`; 4：机械钥匙； 5：远程开锁(12v开锁信号开锁)； 7：APP开启； 8：蓝牙开锁； 9：手动开锁； 15：出错) `bit16~27`表示用户编号； `bit28~31`表示开锁方式：(同上定义) (注：因有可能存在两种方式同时开启门锁 的情况，单开时`bit0~15`为开锁信息，其 他位为0；双开时`bit0~15`和`bit16~31` 分别为相应的开锁信息) `val`的长度有8/24/32bit三种类型",
        },
        "HISLK": {
            "description": "最近一次开锁信息",
            "rw": "R",
            "data_type": "recent_unlock",
            "conversion": "val_direct",
            "detailed_description": "`type&1==1`表示打开； `type&1==0`表示关闭； `val` 值定义如下： `bit0~11`表示用户编号； `bit12~15`表示开锁方式：( 0：未定义； 1：密码； 2：指纹； 3:`NFC`; 4：机械钥匙； 5：远程开锁； 7：APP开启) `bit16~27`表示用户编号； `bit28~31`表示开锁方式: （同上定义）",
        },
    }


def _smart_lock_basic_config(name):
    """生成基础智能门锁设备配置（标准门锁 + EVTOP）"""
    return {
        "name": name,
        "sensor": {
            **_smart_lock_common_sensors(),
            "EVTOP": {
                "description": "操作记录",
                "rw": "R",
                "data_type": "operation_record",
                "conversion": "val_direct",
                "detailed_description": "`type`可以获知长度，方法是： (`type=0x40+(8-1)*2` or `type=0x40+(16-1)*2` or `type=0x40+(32-1)*2`) `val`的通用的编码次序是：[1Byte的记录 类型][2Byte的用户id][1Byte的用户 flag] 用户标志flag：`bit01=11`表示管理 员，01表示普通用户，00表示已经删除了",
            },
        },
    }


def _smart_lock_c_series_config(name):
    """生成C100/C200门锁设备配置（标准门锁 + EVTBEL）"""
    return {
        "name": name,
        "sensor": {
            **_smart_lock_common_sensors(),
            "EVTBEL": {
                "description": "门铃消息",
                "rw": "R",
                "data_type": "doorbell_message",
                "conversion": "val_direct",
                "detailed_description": "门铃消息状态，与EVTLO共享，`type&1=1`表示有门铃消息",
            },
        },
    }


def _air_controller_climate_config():
    """生成智控器空调面板完整配置（用于V_AIR_P、V_SZJSXR_P、V_T8600_P等参考设备）"""
    return {
        "climate": {
            "O": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`,`val` 值忽略表示打开；`type&1==0`,`val` 值忽略表示关闭；",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开空调"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭空调"},
                },
            },
            "MODE": {
                "description": "模式",
                "rw": "RW",
                "data_type": "hvac_mode",
                "conversion": "val_direct",
                "detailed_description": "`type==0xCE`,`val` 值表示模式，定义如下：1:Auto自动; 2:Fan 吹风; 3:Cool 制冷; 4:Heat 制热; 5:Dry除湿",
                "commands": {
                    "set_mode": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "description": "设置模式，val=模式值",
                    },
                },
            },
            "F": {
                "description": "风速",
                "rw": "RW",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "detailed_description": "`type==0xCE`,`val` 值表示风速，定义如下：`val<30`:低档; `val<65`:中档; `val>=65`:高档",
                "commands": {
                    "set_fan_speed": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "description": "设置风速，低档val=15; 中档val=45; 高档val=75",
                    },
                },
            },
            "tT": {
                "description": "目标温度",
                "rw": "RW",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`type==0x88`,`v` 值表示实际温度值，`val` 值表示原始温度值，它是温度值*10",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_SET_TEMP_DECIMAL,
                        "description": "设置目标温度，val=目标温度值*10",
                    },
                },
            },
            "T": {
                "description": "当前温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`type==0x08`,`v` 值表示实际温度值，`val` 值表示原始温度值，它是温度值*10",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    }


# ================= 设备IO特征映射 (Device IO Feature Mapping) =================
# 基于设备实际IO口功能的平台支持映射，解决多平台设备问题
# 每个设备只在一个主要集合中定义，但可支持多个平台

DEVICE_MAPPING = {
    # ================= 设备映射按官方文档顺序排列 (Device Mapping in Official Documentation Order) =================
    # 🚨 严格按照官方文档 "LifeSmart 智慧设备规格属性说明.md" 的章节顺序排列
    # 🚨 2.1 插座系列 → 2.2 开关系列 → 2.3 窗帘控制 → 2.4 灯光系列 → ... → 2.14 超能面板
    # ================= 2.1 插座系列 (Outlet Series) =================
    # 2.1.1 传统插座系列 (Traditional Outlet Series)
    "SL_OL": {
        "name": "智慧插座",
        "switch": _binary_switch_io("O"),
    },
    "SL_OL_3C": {
        "name": "智慧插座",
        "switch": _binary_switch_io("O"),
    },
    "SL_OL_DE": {
        "name": "德标插座",
        "switch": _binary_switch_io("O"),
    },
    "SL_OL_UK": {
        "name": "英标插座",
        "switch": _binary_switch_io("O"),
    },
    "SL_OL_UL": {
        "name": "美标插座",
        "switch": _binary_switch_io("O"),
    },
    "OD_WE_OT1": {
        "name": "Wi-Fi插座",
        "switch": _binary_switch_io("P1"),
    },
    # 2.1.2 计量插座系列 (Energy Monitoring Outlet Series)
    "SL_OE_3C": {
        "name": "计量插座",
        **_energy_monitoring_outlet("P1"),
    },
    "SL_OE_DE": {
        "name": "计量插座德标",
        **_energy_monitoring_outlet("P1"),
    },
    "SL_OE_W": {
        "name": "入墙插座",
        **_energy_monitoring_outlet("P1"),
    },
    # ================= 2.2 开关系列 (Switch Series) =================
    # 2.2.1 随心开关系列 (Freestyle Switch Series)
    "SL_SW_RC1": {
        "name": "随心开关一位",
        "switch": {**_binary_switch_io("L1", "第一路开关控制口")},
        "light": {
            **_indicator_light_io("dark", "关状态时指示灯亮度"),
            **_indicator_light_io("bright", "开状态时指示灯亮度"),
        },
    },
    "SL_SW_RC2": {
        **_multi_key_switch_with_lights(
            "流光开关二键",
            {"L1": _SWITCH_DESC_1, "L2": _SWITCH_DESC_2},
            {
                "dark1": _LIGHT_DARK_1,
                "dark2": _LIGHT_DARK_2,
                "bright1": _LIGHT_BRIGHT_1,
                "bright2": _LIGHT_BRIGHT_2,
            },
        )
    },
    "SL_SW_RC3": {
        **_multi_key_switch_with_lights(
            "流光开关三键",
            {"L1": _SWITCH_DESC_1, "L2": _SWITCH_DESC_2, "L3": _SWITCH_DESC_3},
            {
                "dark1": _LIGHT_DARK_1,
                "dark2": _LIGHT_DARK_2,
                "dark3": _LIGHT_DARK_3,
                "bright1": _LIGHT_BRIGHT_1,
                "bright2": _LIGHT_BRIGHT_2,
                "bright3": _LIGHT_BRIGHT_3,
            },
        )
    },
    # 2.2.1 传统开关系列补充 (Traditional Switch Series Supplement)
    "SL_SF_RC": {
        "name": "单火触摸开关",
        "switch": {
            **_binary_switch_io("L1", "第一路开关控制口"),
            **_binary_switch_io("L2", "第二路开关控制口"),
            **_binary_switch_io("L3", "第三路开关控制口"),
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "indicator_light",
                "conversion": "val_direct",
                "range": "0-1023",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，取值范围：0~1023",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_brightness_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置亮度值",
                    },
                    "set_brightness_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置亮度值",
                    },
                },
            },
            "bright": {
                "description": "开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "indicator_light",
                "conversion": "val_direct",
                "range": "0-1023",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，取值范围：0~1023",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_brightness_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置亮度值",
                    },
                    "set_brightness_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置亮度值",
                    },
                },
            },
        },
    },
    "SL_SW_RC": {
        "name": "触摸开关/极星开关(零火版)",
        "switch": {
            **_binary_switch_io("L1", "第一路开关控制口"),
            **_binary_switch_io("L2", "第二路开关控制口"),
            **_binary_switch_io("L3", "第三路开关控制口"),
        },
        "light": {
            "dark": {
                "description": "关状态时指示灯亮度",
                "rw": "RW",
                "data_type": "indicator_light",
                "conversion": "val_direct",
                "range": "0-1023",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，取值范围：0~1023",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_brightness_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置亮度值",
                    },
                    "set_brightness_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置亮度值",
                    },
                },
            },
            "bright": {
                "description": "开状态时指示灯亮度",
                "rw": "RW",
                "data_type": "indicator_light",
                "conversion": "val_direct",
                "range": "0-1023",
                "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭；`val` 表示指示灯亮度值，取值范围：0~1023",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_brightness_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "开灯并设置亮度值",
                    },
                    "set_brightness_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "关灯并设置亮度值",
                    },
                },
            },
        },
    },
    "SL_SW_IF3": _multi_key_switch_with_lights(
        "流光开关三键",
        {"L1": _SWITCH_DESC_1, "L2": _SWITCH_DESC_2, "L3": _SWITCH_DESC_3},
        {
            "dark1": _LIGHT_DARK_1,
            "dark2": _LIGHT_DARK_2,
            "dark3": _LIGHT_DARK_3,
            "bright1": _LIGHT_BRIGHT_1,
            "bright2": _LIGHT_BRIGHT_2,
            "bright3": _LIGHT_BRIGHT_3,
        },
    ),
    "SL_SF_IF3": _multi_key_switch_with_lights(
        "单火流光开关三键",
        {"L1": _SWITCH_DESC_1, "L2": _SWITCH_DESC_2, "L3": _SWITCH_DESC_3},
        {
            "dark1": _LIGHT_DARK_1,
            "dark2": _LIGHT_DARK_2,
            "dark3": _LIGHT_DARK_3,
            "bright1": _LIGHT_BRIGHT_1,
            "bright2": _LIGHT_BRIGHT_2,
            "bright3": _LIGHT_BRIGHT_3,
        },
    ),
    "SL_SW_CP3": _multi_key_switch_with_lights(
        "橙朴开关三键",
        {"L1": _SWITCH_DESC_1, "L2": _SWITCH_DESC_2, "L3": _SWITCH_DESC_3},
        {
            "dark1": _LIGHT_DARK_1,
            "dark2": _LIGHT_DARK_2,
            "dark3": _LIGHT_DARK_3,
            "bright1": _LIGHT_BRIGHT_1,
            "bright2": _LIGHT_BRIGHT_2,
            "bright3": _LIGHT_BRIGHT_3,
        },
    ),
    "SL_SW_IF2": _multi_key_switch_with_lights(
        "零火流光开关二键",
        {"L1": _SWITCH_DESC_1, "L2": _SWITCH_DESC_2},
        {
            "dark1": _LIGHT_DARK_1,
            "dark2": _LIGHT_DARK_2,
            "bright1": _LIGHT_BRIGHT_1,
            "bright2": _LIGHT_BRIGHT_2,
        },
    ),
    "SL_SF_IF2": _multi_key_switch_with_lights(
        "单火流光开关二键",
        {"L1": _SWITCH_DESC_1, "L2": _SWITCH_DESC_2},
        {
            "dark1": _LIGHT_DARK_1,
            "dark2": _LIGHT_DARK_2,
            "bright1": _LIGHT_BRIGHT_1,
            "bright2": _LIGHT_BRIGHT_2,
        },
    ),
    "SL_SW_CP2": _multi_key_switch_with_lights(
        "橙朴开关二键",
        {"L1": _SWITCH_DESC_1, "L2": _SWITCH_DESC_2},
        {
            "dark1": _LIGHT_DARK_1,
            "dark2": _LIGHT_DARK_2,
            "bright1": _LIGHT_BRIGHT_1,
            "bright2": _LIGHT_BRIGHT_2,
        },
    ),
    "SL_SW_FE2": _multi_key_switch_with_lights(
        "塞纳开关二键",
        {"L1": _SWITCH_DESC_1, "L2": _SWITCH_DESC_2},
        {
            "dark1": _LIGHT_DARK_1,
            "dark2": _LIGHT_DARK_2,
            "bright1": _LIGHT_BRIGHT_1,
            "bright2": _LIGHT_BRIGHT_2,
        },
    ),
    "SL_SW_IF1": _single_switch_with_lights("零火流光开关单键"),
    "SL_SF_IF1": _single_switch_with_lights("单火流光开关单键"),
    "SL_SW_CP1": _single_switch_with_lights("橙朴开关单键"),
    "SL_SW_FE1": _single_switch_with_lights("塞纳开关单键"),
    "SL_OL_W": _single_switch_with_lights("智慧插座开关版"),
    # 2.2.2 恒星/辰星/极星开关系列 (Star Series Switch)
    "SL_SW_ND1": {**_star_switch_device("恒星开关一键", ["P1"], "P2")},
    "SL_SW_ND2": {**_star_switch_device("恒星开关二键", ["P1", "P2"], "P3")},
    "SL_SW_ND3": {**_star_switch_device("恒星开关三键", ["P1", "P2", "P3"], "P4")},
    "SL_MC_ND1": _switch_companion_device("恒星/辰星开关伴侣一键", ["P1"], "P2"),
    "SL_MC_ND2": _switch_companion_device("恒星/辰星开关伴侣二键", ["P1", "P2"], "P3"),
    "SL_MC_ND3": _switch_companion_device(
        "恒星/辰星开关伴侣三键", ["P1", "P2", "P3"], "P4"
    ),
    # 2.2.3 开关控制器系列 (Switch Controller Series)
    "SL_S": {
        "name": "单路开关控制器",
        "switch": {
            "P2": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "-",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
    },
    "SL_SPWM": {
        "name": "PWM调光开关控制器",
        "switch": _pwm_dimmer_io("P1"),
    },
    "SL_P_SW": {
        **_multi_switch_device(
            "九路开关控制器", ["P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8", "P9"]
        )
    },
    # 2.2.4 随心开关 (CUBE Clicker)
    "SL_SC_BB": {
        "name": "随心开关",
        "button": {
            "B": {
                "description": "按键状态",
                "rw": "R",
                "data_type": "button_state",
                "conversion": "val_direct",
                "detailed_description": "`val` 的值定义如下：- 0：未按下按键 - 1：按下按键",
                "device_class": ButtonDeviceClass.IDENTIFY,
            },
        },
        "sensor": {
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始电压值 `v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据 `val` 电压值换算的",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    #### 2.2.5 动态调光开关(Dimmer Motion Controller) - 版本设备
    "SL_SW_DM1": {
        "versioned": True,
        "version_modes": {
            "V1": {
                "name": "动态调光开关",
                "light": {
                    "P1": {
                        "description": "开关",
                        "rw": "RW",
                        "data_type": "brightness_light",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "detailed_description": "`type&1==1`表示处于打开状态；`type&1==0`表示处于关闭状态；`val` 值为亮度值，可调范围：[0,255], 值越大表示光越亮，0处于最暗，光完全熄灭，255处于最亮",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                            "set_brightness_on": {
                                "type": 0xCF,
                                "description": "打开并且设置亮度，val=亮度值[0,255]",
                            },
                            "set_brightness_off": {
                                "type": 0xCE,
                                "description": "关闭并设置亮度，val=亮度值[0,255]",
                            },
                        },
                    },
                    "P2": {
                        "description": "指示灯",
                        "rw": "RW",
                        "data_type": "indicator_light",
                        "conversion": "val_direct",
                        "detailed_description": "`type&1==1`表示处于打开状态；`type&1==0`表示处于关闭状态；`val` 值为亮度值，它有灯光处于打开状态下的指示灯亮度和灯光处于关闭状态下的指示灯亮度。`bit8-bit15`：用于指示灯光处于打开状态下的指示灯亮度 `bit0-bit7`：用于指示灯光处于关闭状态下的指示灯亮度 每8个bit可调范围：[0,255], 值越大表示光越亮，0处于最暗，光完全熄灭，255处于最亮。",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                            "set_brightness": {
                                "type": 223,
                                "description": "设置亮度，val=亮度值[0,65535]",
                            },
                        },
                    },
                },
                "binary_sensor": {
                    "P3": {
                        "description": "移动检测",
                        "rw": "R",
                        "data_type": "motion_status",
                        "conversion": "val_direct",
                        "detailed_description": "`val` 值定义如下：0：没有检测到移动 1：有检测到移动",
                        "device_class": BinarySensorDeviceClass.MOTION,
                    },
                },
                "sensor": {
                    "P4": {
                        "description": "环境光照",
                        "rw": "R",
                        "data_type": "illuminance",
                        "conversion": "val_direct",
                        "detailed_description": "`val` 值表示原始光照值(单位：lux)",
                        "device_class": SensorDeviceClass.ILLUMINANCE,
                        "unit_of_measurement": "lx",
                        "state_class": SensorStateClass.MEASUREMENT,
                    },
                    "P5": {
                        "description": "调光设置",
                        "rw": "RW",
                        "data_type": "dimming_config",
                        "conversion": "val_direct",
                        "detailed_description": "当前调光设置值",
                        "commands": {
                            "set_config": {
                                "type": CMD_TYPE_SET_CONFIG,
                                "description": "设置调光参数配置",
                            },
                        },
                    },
                    "P6": {
                        "description": "动态设置",
                        "rw": "RW",
                        "data_type": "dynamic_config",
                        "conversion": "val_direct",
                        "detailed_description": "当前动态设置值",
                        "commands": {
                            "set_config": {
                                "type": CMD_TYPE_SET_CONFIG,
                                "description": "设置动态参数配置",
                            },
                        },
                    },
                },
            },
            "V2": {
                "name": "星玉调光开关(可控硅)",
                "light": {
                    "P1": {
                        "description": "开关",
                        "rw": "RW",
                        "data_type": "brightness_light",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "detailed_description": "`type&1==1`表示处于打开状态；`type&1==0`表示处于关闭状态；`val` 值为亮度值，可调范围：[0,255], 值越大表示光越亮，0处于最暗，光完全熄灭，255处于最亮",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                            "set_brightness_on": {
                                "type": CMD_TYPE_SET_VAL,
                                "description": "打开并且设置亮度，val=亮度值[0,255]",
                            },
                            "set_brightness_off": {
                                "type": CMD_TYPE_SET_CONFIG,
                                "description": "关闭并设置亮度，val=亮度值[0,255]",
                            },
                        },
                    },
                    "P2": {
                        "description": "指示灯亮度",
                        "rw": "RW",
                        "data_type": "indicator_light",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "detailed_description": "`type&1==1`表示处于打开状态；`type&1==0`表示处于关闭状态；`val` 值为亮度值，可调范围：[0,255], 值越大表示光越亮，0处于最暗，光完全熄灭，255处于最亮",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                            "set_brightness": {
                                "type": CMD_TYPE_SET_VAL,
                                "description": "设置亮度，val=亮度值[0,255]",
                            },
                        },
                    },
                },
            },
        },
    },
    # 2.2.6 奇点开关模块系列 (Singularity Switch Module Series)
    "SL_SW_MJ1": _singularity_switch_device("奇点开关模块一键", ["P1"]),
    "SL_SW_MJ2": _singularity_switch_device("奇点开关模块二键", ["P1", "P2"]),
    "SL_SW_MJ3": _singularity_switch_device("奇点开关模块三键", ["P1", "P2", "P3"]),
    # 2.2.7 随心按键 (CUBE Clicker2)
    "SL_SC_BB_V2": {
        "name": "随心按键",
        "button": {
            "P1": {
                "description": "按键状态",
                "rw": "R",
                "data_type": "button_events",
                "conversion": "val_direct",
                "detailed_description": "`type` 的值定义如下: `type&1==1`，表示有按键事件产生；`type&1==0`,表示按键事件消失；`val` 值指明按键事件类型，只有在 `type&1==1` 才有效，`val` 的值定义如下：1：单击事件 2：双击事件 255：长按事件",
                "device_class": ButtonDeviceClass.IDENTIFY,
            },
        },
        "sensor": {
            "P2": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery_level",
                "conversion": "voltage_to_percentage",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0，100]，它是根据 `val` 电压值换算的。",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    # 2.2.8 星玉开关系列 (Nature Switch Series)
    "SL_SW_NS1": _multi_key_switch_with_lights(
        "星玉开关一键",
        {"L1": _SWITCH_DESC_1},
        {"dark": _LIGHT_DARK_SINGLE, "bright": _LIGHT_BRIGHT_SINGLE},
    ),
    "SL_SW_NS2": _multi_key_switch_with_lights(
        "星玉开关二键",
        {"L1": _SWITCH_DESC_1, "L2": _SWITCH_DESC_2},
        {
            "dark1": _LIGHT_DARK_1,
            "dark2": _LIGHT_DARK_2,
            "bright1": _LIGHT_BRIGHT_1,
            "bright2": _LIGHT_BRIGHT_2,
        },
    ),
    "SL_SW_NS3": _multi_key_switch_with_lights(
        "星玉开关三键",
        {"L1": _SWITCH_DESC_1, "L2": _SWITCH_DESC_2, "L3": _SWITCH_DESC_3},
        {
            "dark1": _LIGHT_DARK_1,
            "dark2": _LIGHT_DARK_2,
            "dark3": _LIGHT_DARK_3,
            "bright1": _LIGHT_BRIGHT_1,
            "bright2": _LIGHT_BRIGHT_2,
            "bright3": _LIGHT_BRIGHT_3,
        },
    ),
    # 2.2.11 极星开关(120零火版) (BS Series)
    "SL_SW_BS1": {
        "name": "极星开关(120零火版)一键",
        "switch": _binary_switch_io("P1", "第一路开关控制口"),
    },
    "SL_SW_BS2": {
        "name": "极星开关(120零火版)二键",
        "switch": {
            **_binary_switch_io("P1", "第一路开关控制口"),
            **_binary_switch_io("P2", "第二路开关控制口"),
        },
    },
    "SL_SW_BS3": {
        "name": "极星开关(120零火版)三键",
        "switch": {
            **_binary_switch_io("P1", "第一路开关控制口"),
            **_binary_switch_io("P2", "第二路开关控制口"),
            **_binary_switch_io("P3", "第三路开关控制口"),
        },
    },
    # 2.2.12 星玉调光开关（可控硅）Dimming Light Switch
    "SL_SW_WW": {
        "name": "星玉调光开关",
        "light": {
            "P1": {
                "description": "亮度控制",
                "rw": "RW",
                "data_type": "brightness",
                "conversion": "val_to_brightness",
                "detailed_description": "`type&1==1`表示打开(忽略`val` 值);`type&1==0`表示关闭(忽略`val` 值);val指示灯光的亮度值范围[0，255]，255亮度最大。",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关灯"},
                    "set_brightness": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置亮度，val=亮度值[0,255]",
                    },
                },
            },
            "P2": {
                "description": "色温控制",
                "rw": "RW",
                "data_type": "color_temp",
                "conversion": "val_to_color_temp",
                "detailed_description": "`val` 值为色温值，取值范围[0，255]，0表示暖光，255表示冷光",
                "commands": {
                    "set_color_temp": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置色温，val=色温值[0,255]",
                    },
                },
            },
        },
        # 注意：SL_SW_DM1_V2也在星玉调光开关范畴内，通过fullCls区分版本
    },
    # 2.2.14 星玉情景面板（Nature Switch Scene Panel)
    "SL_SW_NS6": {
        "name": "星玉情景面板",
        "switch": {
            **_binary_switch_io("P1", "情景开关1"),
            **_binary_switch_io("P2", "情景开关2"),
            **_binary_switch_io("P3", "情景开关3"),
            **_binary_switch_io("P4", "情景开关4"),
            **_binary_switch_io("P5", "情景开关5"),
            **_binary_switch_io("P6", "情景开关6"),
        },
        "sensor": {
            "P7": {
                "description": "开关控制器配置",
                "rw": "RW",
                "data_type": "scene_config",
                "conversion": "val_direct",
                "detailed_description": "`val` 值为面板上六个按键的功能配置参数。`bit0-bit3`:设置P1;`bit4-bit7`:设置P2;`bit8-bit11`：设置P3;`bit12-bit15`: 设置P4;`bit16-bit19`:设置P5;`bit20-bit23`：设置P6;如上划分每4个bit分别代表对应面板上的按钮设置，我们按照每4个bit的值来看功能的定义设置，以P1的设置为例：值为0时：表示自复位开关，默认5s自动关;值为1、2、3时：分别对应面板物理设备上的继电器L1，那么该P1的开关操作就是操作的继电器L1的开关；值为4~14时：表示自复位开关自定义延迟关的时间，若x表示满足当前区间的值，那么延迟关时间的计算公式为：(5+(X-3)*15) 单位为秒S。值为15时：表示通用开关，不会自动关。当P1~P6设置为绑定继电器时，当前为普通开关控制器。",
                "commands": {
                    "config": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "下发配置，val=bit0~bit23按对应Px配置值后合并的一个数值",
                    },
                },
            },
        },
    },
    # ================= 2.3 窗帘控制系列 (Curtain Controller) =================
    # 2.3.1 窗帘控制开关
    "SL_SW_WIN": {
        **_basic_curtain_device("窗帘控制开关", "OP", "CL", "ST"),
        "light": _curtain_indicator_lights_io(),
    },
    "SL_CN_IF": {
        **_basic_curtain_device("流光窗帘控制器", "P1", "P3", "P2"),
        "light": _curtain_rgbw_lights_io(
            {
                "P4": "打开面板指示灯的颜色值",
                "P5": "停止(stop)时指示灯的颜色值",
                "P6": "关闭面板指示灯的颜色值",
            }
        ),
    },
    "SL_CN_FE": _basic_curtain_device("塞纳三键窗帘", "P1", "P3", "P2"),
    # 2.3.2 DOOYA窗帘电机
    "SL_DOOYA": {
        "name": "DOOYA窗帘电机",
        "cover": {
            "P1": {
                "description": "窗帘状态",
                "rw": "R",
                "data_type": "position_status",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1`表示控制正在运行；`type&1==0`表示没有运行；当正在运行的时候即(`type&1==1`):,`val%0x80==0x80`表示正在开，否则表示正在关；`val%0x7F`的值表示窗帘打开的百分比([0,100]);若`val%0x7F`大于100则表示获取不到位置信息，只有执行全开或全关之后才能重新获取位置信息。",
            },
            "P2": {
                "description": "窗帘控制",
                "rw": "W",
                "data_type": "position_control",
                "conversion": "val_direct",
                "commands": {
                    "open": {"type": 0xCF, "val": 100, "description": "完全打开"},
                    "close": {"type": 0xCF, "val": 0, "description": "完全关闭"},
                    "stop": {"type": 0xCE, "val": 0x80, "description": "停止窗帘"},
                    "set_position": {
                        "type": 0xCF,
                        "description": "开到百分比，val=percent，percent取值:[0,100]",
                    },
                },
            },
        },
    },
    "SL_P_V2": {
        **_basic_curtain_device("智界窗帘电机智控器", "P2", "P3", "P4"),
        "sensor": {
            "P8": {
                "description": "电压(V)",
                "rw": "R",
                "data_type": "voltage",
                "conversion": "friendly_val",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0，100]，它是根据val电压值换算的。",
                "device_class": SensorDeviceClass.VOLTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    # ================= 2.4 灯光系列 (Light Series) =================
    # 2.4.1 灯光系列 (RGBW/RGB Light Series)
    "SL_CT_RGBW": _rgbw_device("RGBW灯带"),
    "SL_LI_RGBW": _rgbw_device("RGBW灯泡"),
    "SL_SC_RGB": _rgb_device("RGB灯带无白光"),
    # 2.4.2 量子灯 (Quantum Light)
    "OD_WE_QUAN": _quantum_light_device("量子灯"),
    # 2.4.3 调光调色控制器/白光智能灯泡 (Smart Bulb) - 版本设备
    "SL_LI_WW": {
        "versioned": True,
        "version_modes": {
            "V1": {
                "name": "智能灯泡(冷暖白)",
                "light": {
                    "P1": {
                        "description": "亮度控制",
                        "rw": "RW",
                        "data_type": "brightness_light",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "detailed_description": "`type&1==1`表示处于打开状态；`type&1==0`表示处于关闭状态；`val` 值为亮度值，可调范围：[0-255], 值越大表示光越亮，0处于最暗，光完全熄灭，255处于最亮",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                            "set_brightness": {
                                "type": CMD_TYPE_SET_VAL,
                                "description": "设置亮度，val=亮度值[0-255]",
                            },
                        },
                    },
                    "P2": {
                        "description": "色温控制",
                        "rw": "RW",
                        "data_type": "color_temperature",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "detailed_description": "`val` 值为色温值，取值范围[0-255]，0表示暖光，255表示冷光",
                        "commands": {
                            "set_color_temp": {
                                "type": CMD_TYPE_SET_VAL,
                                "description": "设置色温，val=色温值[0-255]",
                            },
                        },
                    },
                },
            },
            "V2": {
                "name": "调光调色智控器(0-10V)",
                "light": {
                    "P1": {
                        "description": "亮度控制",
                        "rw": "RW",
                        "data_type": "brightness_light",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "detailed_description": "`type&1==1`表示处于打开状态；`type&1==0`表示处于关闭状态；`val` 值为亮度值，可调范围：[0-255], 值越大表示光越亮，0处于最暗，光完全熄灭，255处于最亮",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                            "set_brightness": {
                                "type": CMD_TYPE_SET_VAL,
                                "description": "设置亮度，val=亮度值[0-255]",
                            },
                        },
                    },
                    "P2": {
                        "description": "色温控制",
                        "rw": "RW",
                        "data_type": "color_temperature",
                        "conversion": "val_direct",
                        "range": "0-255",
                        "detailed_description": "`val` 值为色温值，取值范围[0-255]，0表示暖光，255表示冷光",
                        "commands": {
                            "set_color_temp": {
                                "type": CMD_TYPE_SET_VAL,
                                "description": "设置色温，val=色温值[0-255]",
                            },
                        },
                    },
                },
            },
        },
    },
    # 2.4.4 门廊壁灯 (Porch Wall Lamp)
    "SL_LI_GD1": _motion_light_device("门廊壁灯", "P1", "P2", "P3"),
    # 2.4.5 花园地灯 (Garden Landscape Light)
    "SL_LI_UG1": _garden_light_device("花园地灯"),
    # 2.5 超级碗 (SPOT Series)
    "MSL_IRCTL": _rgbw_device("超级碗RGB灯", "RGBW", "DYN"),
    "OD_WE_IRCTL": _rgb_device("超级碗RGB灯(OD)"),
    "SL_SPOT": _rgb_device("超级碗RGB灯"),
    "SL_LI_IR": _brightness_color_temp_device("红外吸顶灯", night_port="P3"),
    "SL_P_IR": _brightness_color_temp_device("红外模块", night_port="P3"),
    "SL_SC_CV": {
        "name": "语音小Q",
        "switch": _binary_switch_io("P1"),
    },
    # ================= 2.6 感应器系列 (Sensor Series) =================
    # 2.6.1 门禁感应器（Guard Sensor)
    "SL_SC_G": _basic_door_sensor_device("门禁感应器", "G", "V"),
    "SL_SC_BG": {
        **_enhanced_door_sensor_device(
            "门禁感应器（带按键震动）",
            "G",
            "V",
            {
                **_button_sensor_io("B", "按键状态"),
                **_vibration_sensor_io("AXS"),
            },
        )
    },
    "SL_SC_GS": {
        **_enhanced_door_sensor_device(
            "门禁感应器（增强版）",
            "P1",
            "V",
            _vibration_sensor_io("AXS", "type_bit_0", _VIBRATION_DETAIL_TYPE),
        )
    },
    # 2.6.2 动态感应器（Motion Sensor)
    "SL_SC_MHW": _motion_sensor_device("动态感应器", "M", "V"),
    "SL_SC_BM": _motion_sensor_device("动态感应器", "M", "V"),
    "SL_SC_CM": {
        "name": "动态感应器（带USB供电）",
        "binary_sensor": _motion_binary_sensor_io("P1"),
        "sensor": {
            **_battery_sensor_io("P3"),
            **_usb_voltage_sensor_io("P4", "USB供电电压"),
        },
    },
    "SL_BP_MZ": {
        "name": "动态感应器PRO",
        "binary_sensor": _motion_binary_sensor_io("P1"),
        "sensor": {
            **_illuminance_sensor_io("P2", "当前环境光照"),
            **_battery_sensor_io("P3"),
        },
    },
    # 2.6.3 环境感应器（Env Sensor)
    "SL_SC_THL": _comprehensive_env_sensor_device(
        "环境感应器（温湿度光照）",
        {
            **_temperature_sensor_io(
                "T",
                conversion="val_div_10",
                detail_desc="`val` 值表示原始温度值，它是温度值*10值(单位：℃)",
            ),
            **_humidity_sensor_io("H"),
            **_illuminance_sensor_io("Z"),
            **_battery_sensor_io("V"),
        },
    ),
    "SL_SC_BE": _comprehensive_env_sensor_device(
        "环境感应器（温湿度光照）",
        {
            **_temperature_sensor_io(
                "T",
                conversion="val_div_10",
                detail_desc="`val` 值表示原始温度值，它是温度值*10值(单位：℃)",
            ),
            **_humidity_sensor_io("H"),
            **_illuminance_sensor_io("Z"),
            **_battery_sensor_io("V"),
        },
    ),
    # 2.6.4 水浸传感器（Water Flooding Sensor)
    "SL_SC_WA": {
        "name": "水浸传感器",
        "sensor": {
            "WA": {
                "description": "导电率",
                "rw": "R",
                "data_type": "conductivity",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0：未检测到水；值越大表示水越多，导电率越高",
                "device_class": SensorDeviceClass.MOISTURE,
                "unit_of_measurement": "µS/cm",
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据`val`电压值换算的",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    # 2.6.5 气体感应器(甲醛)(CH2O Sensor)
    "SL_SC_CH": _gas_sensor_device("甲醛感应器", "P1", "P2", "P3", "甲醛"),
    # 2.6.6 气体感应器(燃气）(Gas Sensor)
    "SL_SC_CP": _gas_sensor_device("燃气感应器", "P1", "P2", "P3", "燃气"),
    # 2.6.7 环境感应器 (TVOC+CO2) (TVOC+CO2 Sensor)
    "SL_SC_CQ": {
        "name": "TVOC+CO2环境感应器",
        "sensor": {
            **_temperature_sensor_io("P1"),
            **_humidity_sensor_io("P2"),
            **_co2_concentration_sensor_io("P3"),
            "P4": {
                "description": "当前TVOC浓度值",
                "rw": "R",
                "data_type": "tvoc_concentration",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示tvoc原始浓度值，它是TVOC浓度值*1000，实际浓度值=原始浓度值/1000，`v` 值表示实际值(单位：mg/m3)，参考：`val`<0.34：优，`val`<0.68：良，`val`<=1.02：中，`val`>1.02：差",
                "device_class": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
                "unit_of_measurement": "mg/m³",
                "state_class": SensorStateClass.MEASUREMENT,
            },
            **_battery_sensor_io("P5"),
            **_usb_voltage_sensor_io("P6"),
        },
    },
    # 2.6.8 ELIQ电量计量器(ELIQ)
    "ELIQ_EM": {
        "name": "ELIQ电量计量器",
        "sensor": {
            "EPA": {
                "description": "平均功率",
                "rw": "R",
                "data_type": "power",
                "conversion": "val_direct",
                "detailed_description": "`val` 值表示平均功率",
                "device_class": SensorDeviceClass.POWER,
                "unit_of_measurement": UnitOfPower.WATT,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    # 2.6.9 烟雾感应器(Smoke Sensor)
    "SL_P_A": {
        "name": "烟雾感应器",
        "binary_sensor": {
            "P1": {
                "description": "当前是否有烟雾告警",
                "rw": "R",
                "data_type": "smoke_alarm",
                "conversion": "val_direct",
                "detailed_description": "`val`等于0表示没有烟雾告警，等于1表示有烟雾告警",
                "device_class": BinarySensorDeviceClass.SMOKE,
            },
        },
        "sensor": {
            "P2": {
                "description": "电压",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "如果使用9V的电池，则实际电压值=(`val`/100)*3，注意：其值可能会超过9V，例如9.58V；如果外接12V供电，则该值无效。`v` 值将表示当前剩余电量百分比，值范围[0,100]",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    # 2.6.10 环境感应器(CO2）(CO2 Sensor)
    "SL_SC_CA": {
        "name": "CO2环境感应器",
        "sensor": {
            **_temperature_sensor_io("P1"),
            **_humidity_sensor_io("P2"),
            **_co2_concentration_sensor_io("P3"),
            **_battery_sensor_io("P4"),
            "P5": {
                "description": "USB供电电压",
                "rw": "R",
                "data_type": "voltage",
                "conversion": "val_direct",
                "detailed_description": "`val`表示原始电压值，若`val` 值大于430则表明供电在工作，否则表明未供电工作",
                "device_class": SensorDeviceClass.VOLTAGE,
                "unit_of_measurement": "V",
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    # 2.6.11 人体存在感应器（Radar Motion Sensor)
    "SL_P_RM": {
        "name": "雷达人体存在感应器",
        "binary_sensor": {
            "P1": {
                "description": "移动检测(Motion)",
                "rw": "R",
                "data_type": "motion_status",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0：没有检测到移动，非0：有检测到移动",
                "device_class": BinarySensorDeviceClass.MOTION,
            },
        },
        "switch": {
            "P2": {
                "description": "移动检测参数设置",
                "rw": "RW",
                "data_type": "radar_config",
                "conversion": "val_direct",
                "detailed_description": "包含动态锁定时间与灵敏度设置。其中：`bit0-bit7`：动态锁定时间，取值范围为：1-255，具体锁定时间为：配置值*4，单位为秒，例如`bit0-bit7`配置值为16，则表示动态锁定时间为64秒。`bit8-bit25`：灵敏度，灵敏度默认值为4，范围1-255，值越小则越灵敏",
                "commands": {
                    "set_config": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "description": "设置感应器动态锁定时间与灵敏度",
                    },
                },
            },
        },
    },
    # 2.6.12 云防门窗感应器（DEFED Window/Door)
    "SL_DF_GG": _defed_door_sensor_device("云防门窗感应器"),
    # 2.6.13 云防动态感应器（DEFED Motion)
    "SL_DF_MM": {
        "name": "云防动态感应器",
        "binary_sensor": {
            "M": {
                "description": "当前状态",
                "rw": "R",
                "data_type": "motion_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示侦测到人体移动(忽略`val` 值)；`type&1==0`表示没有侦测到人体移动(忽略`val` 值)",
                "device_class": BinarySensorDeviceClass.MOTION,
            },
            "TR": {
                "description": "防拆状态",
                "rw": "R",
                "data_type": "tamper_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`则表示触发防拆警报；`type&1==0`则表示状态正常",
                "device_class": BinarySensorDeviceClass.TAMPER,
            },
        },
        "sensor": {
            "T": {
                "description": "温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始温度值，它是实际温度值*10，`v` 值表示实际值(单位：℃)",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据`val`电压值换算的。注意：`type&1==1`表示低电报警状态",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    # 2.6.14 云防室内警铃(DEFED Indoor Siren)
    "SL_DF_SR": {
        "name": "云防室内警铃",
        "binary_sensor": {
            "SR": {
                "description": "当前状态",
                "rw": "R",
                "data_type": "siren_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示警铃播放(忽略`val` 值)；`type&1==0`表示正常(忽略`val` 值)",
                "device_class": BinarySensorDeviceClass.SOUND,
            },
            "TR": {
                "description": "防拆状态",
                "rw": "R",
                "data_type": "tamper_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`则表示触发防拆警报；`type&1==0`则表示状态正常",
                "device_class": BinarySensorDeviceClass.TAMPER,
            },
        },
        "sensor": {
            "T": {
                "description": "温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始温度值，它是实际温度值*10，`v` 值表示实际值(单位：℃)",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据val电压值换算的。注意：`type&1==1`表示低电报警状态",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
        "switch": {
            "P1": {
                "description": "报警设置",
                "rw": "RW",
                "data_type": "alarm_config",
                "conversion": "val_direct",
                "detailed_description": "`val`为32bit值，描述如下(16进制)：`0xAABBCCDD`：`AABB`表示警报持续时长，单位为0.1秒；`CC`是声音强度(136-255)，255最强，136最弱；`DD`表示音频序号：0：无，1：信息，2：告警",
                "commands": _siren_control_commands(),
            },
        },
    },
    # 2.6.15 云防遥控器（DEFED Key Fob)
    "SL_DF_BB": {
        "name": "云防遥控器",
        "binary_sensor": _defed_keyfob_buttons(),
        "sensor": {
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val` 值表示原始电压值，`v` 值将表示当前剩余电量百分比，值范围[0,100]，它是根据`val`电压值换算的。注意：`type&1==1`表示低电报警状态",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    # 2.6.17 噪音感应器（Noise Sensor)
    "SL_SC_CN": {
        "name": "噪音感应器",
        "sensor": {
            "P1": {
                "description": "噪音值",
                "rw": "R",
                "data_type": "noise_level",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1`表示噪音值大于告警门限；`type&1==0`表示噪音值没有超过告警门限；`val`表示当前噪音值，单位为分贝",
                "device_class": SensorDeviceClass.SOUND_PRESSURE,
                "unit_of_measurement": "dB",
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "P4": {
                "description": "噪音校正值",
                "rw": "RW",
                "data_type": "noise_calibration",
                "conversion": "val_direct",
                "detailed_description": "取值范围为[-128~127]，如果噪音采样有误差，可以配置噪音校正值校正",
                "device_class": SensorDeviceClass.SOUND_PRESSURE,
                "unit_of_measurement": "dB",
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
        "switch": {
            "P2": {
                "description": "告警门限设置",
                "rw": "RW",
                "data_type": "threshold_config",
                "conversion": "val_direct",
                "detailed_description": "`val`为32bit值(十六进制)：`0xAABBCCDD`：`DD`表示告警门限值，数值单位为分贝，取值范围[0,255]；`CC`表示采样值1，取值范围[0,255]；`BB`表示采样值2，取值范围[0,255]；`CCBB`共同作用形成越限率",
                "commands": {
                    "set_threshold": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "修改门限值",
                    },
                },
            },
            "P3": {
                "description": "报警设置",
                "rw": "RW",
                "data_type": "alarm_config",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1`表示处于报警状态；`type&1==0`表示处于正常状态；`val`为32bit值，描述如下(16进制)：`0xAABBCCDD`：`AABB`表示警报持续时长，单位为0.1秒，等于65535则表示一直持续；`CC`是声音强度，0表示没有声音，其它值表示有声音；`DD`表示音频模式：0：无声音，1：指示音，2：告警音，0x7F：测试音，0x80-0xFF：自定义模式",
                "commands": _siren_control_commands(),
            },
        },
    },
    # ================= 2.7 空气净化器 (Air Purifier) =================
    "OD_MFRESH_M8088": {
        "name": "空气净化器",
        "switch": {
            "O": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit0",
                "detailed_description": "`type&1==1`表示打开,`val` 值忽略；`type&1==0`表示关闭；",
                "commands": _switch_binary_on_off(),
            },
            "RM": {
                "description": "运行模式",
                "rw": "RW",
                "data_type": "run_mode",
                "conversion": "val_direct",
                "detailed_description": "`val` 值定义如下：0:auto 1~3:风量1~3 4：风量最大 5:睡眠模式",
                "commands": {
                    "set_mode": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置运行模式",
                    },
                },
            },
        },
        "sensor": {
            "T": {
                "description": "温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "friendly_value",
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "device_class": SensorDeviceClass.TEMPERATURE,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "`val` 值表示原始温度值，它是温度值*10，`v` 值表示实际值(单位：℃)",
            },
            "H": {
                "description": "湿度",
                "rw": "R",
                "data_type": "humidity",
                "conversion": "friendly_value",
                "unit_of_measurement": PERCENTAGE,
                "device_class": SensorDeviceClass.HUMIDITY,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "`val` 值表示原始湿度值，它是湿度值*10，`v` 值表示实际值(单位：%)",
            },
            "PM": {
                "description": "PM2.5",
                "rw": "R",
                "data_type": "pm25",
                "conversion": "friendly_value",
                "unit_of_measurement": "µg/m³",
                "device_class": SensorDeviceClass.PM25,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "`val` 值表示PM2.5值，`v` 值表示实际值(单位：ug/m³)",
            },
            "FL": {
                "description": "滤芯寿命",
                "rw": "R",
                "data_type": "filter_life",
                "conversion": "val_direct",
                "unit_of_measurement": "h",
                "detailed_description": "`val` 值表示滤芯寿命，范围：0~4800(单位：h)",
            },
            "UV": {
                "description": "紫外线指数",
                "rw": "R",
                "data_type": "uv_index",
                "conversion": "val_direct",
                "detailed_description": "`val` 值表示紫外线指数",
            },
        },
    },
    # ================= 2.8 智能门锁 (Smart Door Lock) =================
    # 2.8.1 智能门锁系列 (Smart Door Lock Series)
    "SL_LK_LS": _smart_lock_basic_config("思锁智能门锁"),
    "SL_LK_GTM": _smart_lock_basic_config("盖特曼智能门锁"),
    "SL_LK_AG": _smart_lock_basic_config("Aqara智能门锁"),
    "SL_LK_SG": _smart_lock_basic_config("思哥智能门锁"),
    "SL_LK_YL": _smart_lock_basic_config("Yale智能门锁"),
    "SL_LK_SWIFTE": _smart_lock_basic_config("SWIFTE智能门锁"),
    "OD_JIUWANLI_LOCK1": _smart_lock_basic_config("久万里智能门锁"),
    "SL_P_BDLK": _smart_lock_basic_config("百度智能门锁"),
    # 2.8.2 C100/C200门锁系列 (C100/C200 Door Lock Series)
    "SL_LK_TY": _smart_lock_c_series_config("C200门锁"),
    "SL_LK_DJ": _smart_lock_c_series_config("C100门锁"),
    # ================= 2.9 温控器 (Climate Controller) =================
    # 2.9.1 智控器空调面板 (Central AIR Board)
    "V_AIR_P": {
        "name": "智控器空调面板",
        **_air_controller_climate_config(),
    },
    # 2.9.2 新风系统 (Fresh Air System)
    "SL_TR_ACIPM": {
        "name": "新风系统",
        "climate": {
            "P1": {
                "description": "系统配置",
                "rw": "RW",
                "data_type": "hvac_mode",
                "conversion": "val_direct",
                "detailed_description": "1:自动; 2:手动; 3:定时",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_mode": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "description": "设置模式，val=模式值",
                    },
                },
            },
            "P2": {
                "description": "风速",
                "rw": "RW",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "detailed_description": "`val`值定义如下: 0:关闭; 1:1档; 2:2档; 3:3档 注意：只有在模式处于手动模式下该参数设置才有效",
                "commands": _single_command_set_fan_speed(),
            },
            "P3": {
                "description": "设置VOC",
                "rw": "RW",
                "data_type": "voc_concentration",
                "conversion": "val_div_10",
                "detailed_description": "`val`值减小10倍为真实值，`v`值表示实际值(单位：ppm)",
                "device_class": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
                "unit_of_measurement": "ppm",
                "commands": {
                    "set_voc": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "description": "设置VOC值，需要将真实值扩大10倍",
                    },
                },
            },
        },
        "sensor": {
            "P4": {
                "description": "VOC",
                "rw": "R",
                "data_type": "voc_concentration",
                "conversion": "val_div_10",
                "detailed_description": "`val`值表示原始VOC值，且`val`值减小10倍为真实值，`v`值表示实际值(单位：ppm)",
                "device_class": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
                "unit_of_measurement": "ppm",
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "P5": {
                "description": "PM2.5",
                "rw": "R",
                "data_type": "pm25",
                "conversion": "v_field",
                "detailed_description": "`val`值表示原始PM2.5值，`v`为实际值(单位：μg/m³)",
                "device_class": SensorDeviceClass.PM25,
                "unit_of_measurement": "μg/m³",
                "state_class": SensorStateClass.MEASUREMENT,
            },
            **_temperature_sensor_io(
                "P6",
                "当前温度",
                conversion="val_div_10",
                detail_desc="`val`值除以10为真实温度值，`v`值表示实际值(单位：℃)",
            ),
        },
    },
    # 2.9.3 地暖温控器 (Thermostat)
    "SL_CP_DN": {
        "name": "地暖温控器",
        "climate": {
            "P1": {
                "description": "系统配置",
                "rw": "RW",
                "data_type": "hvac_mode",
                "conversion": "val_direct",
                "detailed_description": "该IO的type和val字段说明，详见文档表2-17-1",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_config": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "description": "设置配置，需要保留其他位",
                    },
                },
            },
            "P3": {
                "description": "目标温度",
                "rw": "RW",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "detailed_description": "`val`值表示原始温度值，真实温度值为原始值除以10倍，`v`值表示实际值",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "description": "设置目标温度",
                    },
                },
            },
        },
        "binary_sensor": {
            "P2": {
                "description": "继电器开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                "device_class": BinarySensorDeviceClass.OPENING,
            },
        },
        "sensor": {
            **_temperature_sensor_io(
                "P4",
                "室内温度",
                conversion="val_div_10",
                detail_desc="`val`值表示原始温度值，真实温度值为原始值除以10倍，精度为0.1，`v`值表示实际值",
            ),
            **_temperature_sensor_io(
                "P5",
                "底版温度",
                conversion="val_div_10",
                detail_desc="`val`值表示原始温度值，真实温度值为原始值除以10，精度为0.1，`v`值表示实际值",
            ),
        },
    },
    # 2.9.4 风机盘管 (Fan Coil Unit)
    "SL_CP_AIR": {
        "name": "风机盘管",
        "climate": {
            "P1": {
                "description": "系统配置",
                "rw": "RW",
                "data_type": "hvac_mode",
                "conversion": "val_direct",
                "detailed_description": "该IO的type和val字段说明，详见文档表2-18-1",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_config": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "description": "设置配置，需要保留其他位",
                    },
                },
            },
            "P4": {
                "description": "目标温度",
                "rw": "RW",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "detailed_description": "`val`值表示原始温度值，真实温度值为原始值除以10倍，精度为0.5，`v`值表示实际值",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "description": "设置目标温度",
                    },
                },
            },
        },
        "binary_sensor": {
            "P2": {
                "description": "阀门状态",
                "rw": "R",
                "data_type": "valve_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type`值定义如下: 0x80:阀门关; 0x81:阀门开",
                "device_class": BinarySensorDeviceClass.OPENING,
            },
        },
        "sensor": {
            "P3": {
                "description": "风速状态",
                "rw": "R",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "detailed_description": "`val`值定义如下: 0:自动; 1:低速; 2:中速; 3:高速",
            },
            **_temperature_sensor_io(
                "P5",
                "室内温度",
                conversion="val_div_10",
                detail_desc="`val`值表示原始温度值，真实温度值为原始值除以10，精度为0.1，`v`值表示实际值",
            ),
        },
    },
    # 2.9.5 空调控制面板 (AIR Board)
    "SL_UACCB": {
        "name": "空调控制面板",
        "climate": {
            "P1": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`,`val`值忽略表示打开；`type&1==0`，`val`值忽略表示关闭",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开空调"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭空调"},
                },
            },
            "P2": {
                "description": "模式",
                "rw": "RW",
                "data_type": "hvac_mode",
                "conversion": "val_direct",
                "detailed_description": "`type==0xCE`，`val`值表示模式，定义如下：1:Auto自动；2:Fan吹风；3:Cool制冷；4:Heat制热；5:Dry除湿",
                "commands": _single_command_set_mode(),
            },
            "P3": {
                "description": "目标温度",
                "rw": "RW",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`type==0x88`,`v`值表示实际温度值，`val`值表示原始温度值，它是温度值*10",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_SET_TEMP_DECIMAL,
                        "description": "设置目标温度，val=目标温度值*10",
                    },
                },
            },
            "P4": {
                "description": "风速",
                "rw": "RW",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "detailed_description": "`val<30`:低档；`val<65`:中档；`val>=65`:高档",
                "commands": {
                    "set_fan_speed": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "description": "设置风速，低档val=15；中档val=45；高档val=75",
                    },
                },
            },
        },
        "sensor": {
            **_temperature_sensor_io(
                "P6",
                "当前温度",
                conversion="v_field",
                detail_desc="`type==0x08`,`v`值表示实际温度值，`val`值表示原始温度值，它是温度值*10",
            ),
        },
    },
    # 2.9.6 温控阀门 (Thermostat Valve)
    "SL_CP_VL": {
        "name": "温控阀门",
        "climate": {
            "P1": {
                "description": "开关及系统配置",
                "rw": "RW",
                "data_type": "hvac_mode",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`,`val`值忽略表示打开；该IO的type和val字段说明，详见文档表2-19-1",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    "set_config": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "description": "设置配置，需要保留其他位",
                    },
                },
            },
            "P3": {
                "description": "目标温度",
                "rw": "RW",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`v`值表示实际温度值，`val`值表示原始温度值，它是温度值*10",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_SET_TEMP_DECIMAL,
                        "description": "设置目标温度，val=目标温度值*10",
                    },
                },
            },
        },
        "sensor": {
            **_temperature_sensor_io(
                "P4",
                "当前温度",
                conversion="v_field",
                detail_desc="`v`值表示实际温度值，`val`值表示原始温度值，它是温度值*10",
            ),
            "P5": {
                "description": "告警",
                "rw": "R",
                "data_type": "alarm_status",
                "conversion": "val_direct",
                "detailed_description": "`val`表示告警信息，可参考：bit0:高温保护；bit1:低温保护；bit2:int_sensor；bit3:ext_sensor；bit4:低电量；bit5:设备掉线",
            },
            **_battery_sensor_io(
                "P6",
                conversion="v_field",
            ),
        },
    },
    # 2.9.8 星玉地暖 (Smart Controller)
    "SL_DN": {
        "name": "星玉地暖",
        "climate": {
            "P1": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`，`val`值忽略表示打开；`type&1==0`，`val`值忽略表示关闭",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开地暖"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭地暖"},
                },
            },
            "P2": {
                "description": "模式",
                "rw": "RW",
                "data_type": "config_bitmask",
                "conversion": "val_direct",
                "detailed_description": "`val`值定义如下：温度限制0-5位：17+val(17~80)；回差6-9位：使用温度(v+1)*0.5作为回差参数；控温模式10-11位：0/1:in；2:out；3:all",
                "commands": _single_command_set_config("设置模式配置"),
            },
            "P8": {
                "description": "目标温度",
                "rw": "RW",
                "data_type": "temperature",
                "conversion": "val_div_10",
                "detailed_description": "`val`值表示原始温度值，真实温度值为原始值除以10倍，精度为0.5，`v`值表示实际值",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "description": "设置目标温度",
                    },
                },
            },
        },
        "binary_sensor": {
            "P3": {
                "description": "阀门状态",
                "rw": "R",
                "data_type": "valve_status",
                "conversion": "type_bit_0",
                "detailed_description": "type值定义如下：0x80:阀门关；0x81:阀门开；`val`值类型为浮点数值，表示的是电量统计",
                "device_class": BinarySensorDeviceClass.OPENING,
            },
        },
        "sensor": {
            **_temperature_sensor_io(
                "P4",
                "室内温度",
                conversion="val_div_10",
                detail_desc="`val`值表示原始温度值，真实温度值为原始值除以10倍，精度为0.1，`v`值表示实际值",
            ),
            **_temperature_sensor_io(
                "P9",
                "底版温度",
                conversion="val_div_10",
                detail_desc="`val`值表示原始温度值，真实温度值为原始值除以10，精度为0.1，`v`值表示实际值",
            ),
        },
    },
    # ================= 2.10 通用控制器系列 (General Controller Series) =================
    # 2.10.1 通用控制器 (General Controller)
    "SL_P": {
        "name": "通用控制器",
        "dynamic": True,
        "control_modes": {
            "free_mode": {
                "condition": "(P1>>24)&0xe == 0",
                "binary_sensor": {
                    "P5": {
                        "description": "Status1状态输入",
                        "rw": "R",
                        "data_type": "status_input",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示有状态触发，仅自由模式有效",
                        "device_class": BinarySensorDeviceClass.MOVING,
                    },
                    "P6": {
                        "description": "Status2状态输入",
                        "rw": "R",
                        "data_type": "status_input",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示有状态触发，仅自由模式有效",
                        "device_class": BinarySensorDeviceClass.MOVING,
                    },
                    "P7": {
                        "description": "Status3状态输入",
                        "rw": "R",
                        "data_type": "status_input",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示有状态触发，仅自由模式有效",
                        "device_class": BinarySensorDeviceClass.MOVING,
                    },
                },
            },
            "cover_mode": {
                "condition": "(P1>>24)&0xe in [2,4,6]",
                "cover": {
                    "P2": {
                        "description": "打开窗帘",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示打开窗帘",
                        "commands": {
                            "open": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开窗帘",
                            },
                        },
                    },
                    "P3": {
                        "description": "关闭窗帘",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示关闭窗帘",
                        "commands": {
                            "close": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "关闭窗帘",
                            },
                        },
                    },
                    "P4": {
                        "description": "停止窗帘",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示停止窗帘",
                        "commands": {
                            "stop": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "停止窗帘",
                            },
                        },
                    },
                },
            },
            "switch_mode": {
                "condition": "(P1>>24)&0xe in [8,10]",
                "switch": {
                    "P2": {
                        "description": "Ctrl1第一路开关",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                        },
                    },
                    "P3": {
                        "description": "Ctrl2第二路开关",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                        },
                    },
                    "P4": {
                        "description": "Ctrl3第三路开关",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示打开",
                        "commands": {
                            "on": {
                                "type": CMD_TYPE_ON,
                                "val": 1,
                                "description": "打开",
                            },
                            "off": {
                                "type": CMD_TYPE_OFF,
                                "val": 0,
                                "description": "关闭",
                            },
                        },
                    },
                },
            },
        },
        "sensor": {
            "P1": {
                "description": "控制参数",
                "rw": "RW",
                "data_type": "control_config",
                "conversion": "val_direct",
                "detailed_description": "32位控制参数：31bit软件配置标志，24-27bit工作模式，16-18bit延时使能，0-15bit延时秒数",
                "commands": {
                    "set_config": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "description": "设置控制参数，需要保留未修改的bit位",
                    },
                },
            },
        },
    },
    # 2.10.2 通用控制器HA (HA Interface Adapter)
    "SL_JEMA": {
        "name": "通用控制器HA",
        "dynamic": True,
        "control_modes": {
            "free_mode": {
                "condition": "(P1>>24)&0xe == 0",
                "binary_sensor": {
                    "P5": {
                        "description": "Status1状态输入",
                        "rw": "R",
                        "data_type": "status_input",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示有状态触发，仅自由模式有效",
                        "device_class": BinarySensorDeviceClass.MOVING,
                    },
                    "P6": {
                        "description": "Status2状态输入",
                        "rw": "R",
                        "data_type": "status_input",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示有状态触发，仅自由模式有效",
                        "device_class": BinarySensorDeviceClass.MOVING,
                    },
                    "P7": {
                        "description": "Status3状态输入",
                        "rw": "R",
                        "data_type": "status_input",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示有状态触发，仅自由模式有效",
                        "device_class": BinarySensorDeviceClass.MOVING,
                    },
                },
            },
            "cover_mode": {
                "condition": "(P1>>24)&0xe in [2,4,6]",
                "cover": {
                    "P2": {
                        "description": "Ctrl1打开窗帘",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                        "commands": {
                            "open": {"type": 0x81, "val": 1, "description": "打开窗帘"},
                        },
                    },
                    "P3": {
                        "description": "Ctrl2关闭窗帘",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                        "commands": {
                            "close": {
                                "type": 0x81,
                                "val": 1,
                                "description": "关闭窗帘",
                            },
                        },
                    },
                    "P4": {
                        "description": "Ctrl3停止窗帘",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                        "commands": {
                            "stop": {"type": 0x81, "val": 1, "description": "停止窗帘"},
                        },
                    },
                },
            },
            "switch_mode": {
                "condition": "(P1>>24)&0xe in [8,10]",
                "switch": {
                    "P2": {
                        "description": "Ctrl1第一路开关",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                        "commands": {
                            "on": {"type": 0x81, "val": 1, "description": "打开"},
                            "off": {"type": 0x80, "val": 0, "description": "关闭"},
                        },
                    },
                    "P3": {
                        "description": "Ctrl2第二路开关",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                        "commands": {
                            "on": {"type": 0x81, "val": 1, "description": "打开"},
                            "off": {"type": 0x80, "val": 0, "description": "关闭"},
                        },
                    },
                    "P4": {
                        "description": "Ctrl3第三路开关",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                        "commands": {
                            "on": {"type": 0x81, "val": 1, "description": "打开"},
                            "off": {"type": 0x80, "val": 0, "description": "关闭"},
                        },
                    },
                },
            },
        },
        "switch": {
            "P8": {
                "description": "HA1独立开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                "commands": {
                    "on": {"type": 0x81, "val": 1, "description": "打开"},
                    "off": {"type": 0x80, "val": 0, "description": "关闭"},
                },
            },
            "P9": {
                "description": "HA2独立开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                "commands": {
                    "on": {"type": 0x81, "val": 1, "description": "打开"},
                    "off": {"type": 0x80, "val": 0, "description": "关闭"},
                },
            },
            "P10": {
                "description": "HA3独立开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示打开；`type&1==0`表示关闭",
                "commands": {
                    "on": {"type": 0x81, "val": 1, "description": "打开"},
                    "off": {"type": 0x80, "val": 0, "description": "关闭"},
                },
            },
        },
        "sensor": {
            "P1": {
                "description": "控制参数",
                "rw": "RW",
                "data_type": "control_config",
                "conversion": "val_direct",
                "detailed_description": "32位控制参数：31bit恒为1(软件可配置)，24-27bit工作模式，16-18bit延时使能，0-15bit延时秒数",
                "commands": {
                    "set_config": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "description": "设置控制参数，需要保留未修改的bit位",
                    },
                },
            },
        },
    },
    # ================= 第三方设备 (Third-party Devices) =================
    "V_DLT645_P": {
        "name": "DLT电量计量器",
        "sensor": {
            "EE": {
                "description": "用电量",
                "rw": "R",
                "data_type": "energy_consumption",
                "conversion": "ieee754_or_friendly",
                "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
                "device_class": SensorDeviceClass.ENERGY,
                "state_class": SensorStateClass.TOTAL_INCREASING,
                "detailed_description": "为累计用电量，`val` 值为为IEEE754浮点数的32位整数表示，`v` 值为浮点数，单位为度(kwh)。注意：`v` 值可以直接使用，若不存在`v` 值，则需要手动转换。其值类型为IEEE 754浮点数的32位整数布局。",
            },
            "EP": {
                "description": "功率",
                "rw": "R",
                "data_type": "power",
                "conversion": "ieee754_or_friendly",
                "unit_of_measurement": UnitOfPower.WATT,
                "device_class": SensorDeviceClass.POWER,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "为当前负载功率，`v` 值为浮点数，单位为w。注意：`v` 值可以直接使用，若不存在`v` 值，则需要手动转换。其值类型为IEEE 754浮点数的32位整数布局。",
            },
        },
    },
    "V_DUNJIA_P": {
        "name": "X100人脸识别可视门锁",
        "sensor": {**_smart_lock_common_sensors()},
    },
    "V_HG_L": {
        "name": "极速开关组",
        "switch": {
            **_binary_switch_io("L1", "第一路开关控制口"),
            **_binary_switch_io("L2", "第二路开关控制口"),
            **_binary_switch_io("L3", "第三路开关控制口"),
        },
    },
    "V_HG_XX": {
        "name": "极速虚拟设备",
        "switch": _binary_switch_io("P1", "虚拟开关"),
    },
    # V_SZJSXR_P (该规格属性参考 V_AIR_P) - 新风控制器(深圳建设新风)
    "V_SZJSXR_P": {
        "name": "新风控制器(深圳建设新风)",
        # 参考V_AIR_P的IO口定义，使用相同的配置结构
        **_air_controller_climate_config(),
    },
    # V_T8600_P (该规格属性参考 V_AIR_P) - YORK温控器
    "V_T8600_P": {
        "name": "YORK温控器T8600",
        # 参考V_AIR_P的IO口定义，使用相同的配置结构
        **_air_controller_climate_config(),
    },
    "V_FRESH_P": {
        "name": "艾弗纳KV11新风控制器",
        "switch": {
            **_binary_switch_io("O", "开关"),
            "MODE": {
                "description": "工作模式",
                "rw": "RW",
                "data_type": "mode_config",
                "conversion": "val_direct",
                "detailed_description": "`val` 值为模式位掩码，0-1位和2-3位分别控制不同功能",
                "commands": {
                    "set_mode": {
                        "type": CMD_TYPE_SET_VAL,
                        "description": "设置工作模式",
                    },
                },
            },
        },
        "sensor": {
            "F1": {
                "description": "送风风速",
                "rw": "R",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "detailed_description": "`val` 值表示风速，0:停止, val<30:低档, val<65:中档, val>=65:高档",
            },
            "F2": {
                "description": "排风风速",
                "rw": "R",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "detailed_description": "`val` 值表示风速，0:停止, val<30:低档, val<65:中档, val>=65:高档",
            },
            **_temperature_sensor_io(
                "T",
                "环境温度",
                detail_desc="`val` 值除以10为真实温度值，`v` 值表示实际值(单位：℃)",
            ),
        },
    },
    "V_IND_S": {
        "name": "工业传感器",
        "sensor": {
            "P1": {
                "description": "传感器数值",
                "rw": "R",
                "data_type": "generic_value",
                "conversion": "ieee754_or_friendly",
                "detailed_description": "为当前接入设备的值，`val` 值为IEEE754浮点数的32位整数表示，`v` 值为浮点数，单位为具体接入设备当前的单位",
            },
        },
    },
    "V_485_P": {
        "name": "485控制器",
        "wildcard_support": True,
        "switch": {
            "O": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "type&1=1，`val` 值忽略表示打开；type&1=0，`val` 值忽略表示关闭；",
                "commands": _switch_binary_on_off(),
            },
            "L*": {
                "description": "多路开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "type&1=1,`val` 值忽略表示打开；type&1=0，`val` 值忽略表示关闭；(Lx，x为1时，即L1表示第一位开关的IO控制口，多位开关时x可取值为3，L3则表示第三位开关的IO控制口）",
                "commands": _switch_binary_on_off(),
            },
        },
        "sensor": {
            "P1": {
                "description": "当前接入设备的值",
                "rw": "R",
                "data_type": "generic_value",
                "conversion": "ieee754_or_friendly",
                "detailed_description": "为当前接入设备的值，`val` 值为为IEEE754浮点数的32位整数表示，`v` 值为浮点数，单位为具体接入设备当前的单位。如：接入设备为压力传感器，那么val为当前接入设备的压力值，单位以接入设备的单位设定为准。",
            },
            # 电力监测相关 - 支持通配符
            "EE": {
                "description": "用电量",
                "rw": "R",
                "data_type": "energy_consumption",
                "conversion": "ieee754_or_friendly",
                "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
                "device_class": SensorDeviceClass.ENERGY,
                "state_class": SensorStateClass.TOTAL_INCREASING,
                "detailed_description": "为累计用电量，`val` 值为为IEEE754浮点数的32位整数表示，`v` 值为浮点数，单位为度(kwh)。",
            },
            "EE*": {
                "description": "多路用电量",
                "rw": "R",
                "data_type": "energy_consumption",
                "conversion": "ieee754_or_friendly",
                "unit_of_measurement": UnitOfEnergy.KILO_WATT_HOUR,
                "device_class": SensorDeviceClass.ENERGY,
                "state_class": SensorStateClass.TOTAL_INCREASING,
                "detailed_description": "为累计用电量，`val` 值为为IEEE754浮点数的32位整数表示，`v` 值为浮点数，单位为度(kwh)。(EEx，x取值为数字)",
            },
            "EP": {
                "description": "功率",
                "rw": "R",
                "data_type": "power",
                "conversion": "ieee754_or_friendly",
                "unit_of_measurement": UnitOfPower.WATT,
                "device_class": SensorDeviceClass.POWER,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "为当前负载功率，`v` 值为浮点数，单位为w。",
            },
            "EPF": {
                "description": "功率因数",
                "rw": "R",
                "data_type": "power_factor",
                "conversion": "friendly_value",
                "device_class": SensorDeviceClass.POWER_FACTOR,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "功率因数，单位无。",
            },
            "EPF*": {
                "description": "多路功率因数",
                "rw": "R",
                "data_type": "power_factor",
                "conversion": "friendly_value",
                "device_class": SensorDeviceClass.POWER_FACTOR,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "功率因数，单位无。(EPFx，x取值为数字)",
            },
            "EF": {
                "description": "交流电频率",
                "rw": "R",
                "data_type": "frequency",
                "conversion": "friendly_value",
                "unit_of_measurement": "Hz",
                "device_class": SensorDeviceClass.FREQUENCY,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "交流电频率，单位为HZ。",
            },
            "EF*": {
                "description": "多路交流电频率",
                "rw": "R",
                "data_type": "frequency",
                "conversion": "friendly_value",
                "unit_of_measurement": "Hz",
                "device_class": SensorDeviceClass.FREQUENCY,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "交流电频率，单位为HZ。(EFx，x取值为数字)",
            },
            "EI": {
                "description": "电流",
                "rw": "R",
                "data_type": "current",
                "conversion": "friendly_value",
                "unit_of_measurement": "A",
                "device_class": SensorDeviceClass.CURRENT,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "电流，单位为A。",
            },
            "EI*": {
                "description": "多路电流",
                "rw": "R",
                "data_type": "current",
                "conversion": "friendly_value",
                "unit_of_measurement": "A",
                "device_class": SensorDeviceClass.CURRENT,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "电流，单位为A。(EIx，x取值为数字)",
            },
            "EV": {
                "description": "电压",
                "rw": "R",
                "data_type": "voltage",
                "conversion": "friendly_value",
                "unit_of_measurement": "V",
                "device_class": SensorDeviceClass.VOLTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "电压，单位为V。",
            },
            "EV*": {
                "description": "多路电压",
                "rw": "R",
                "data_type": "voltage",
                "conversion": "friendly_value",
                "unit_of_measurement": "V",
                "device_class": SensorDeviceClass.VOLTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "电压，单位为V。(EVx，x取值为数字)",
            },
            # 环境监测相关
            "T": {
                "description": "温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "friendly_value",
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "device_class": SensorDeviceClass.TEMPERATURE,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "`val` 值表示原始温度值，`v` 值为实际值(单位：℃)。",
            },
            "H": {
                "description": "湿度",
                "rw": "R",
                "data_type": "humidity",
                "conversion": "friendly_value",
                "unit_of_measurement": PERCENTAGE,
                "device_class": SensorDeviceClass.HUMIDITY,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "`val` 值表示原始湿度值，`v` 值为实际值(单位：%)。",
            },
            "PM": {
                "description": "PM2.5",
                "rw": "R",
                "data_type": "pm25",
                "conversion": "friendly_value",
                "unit_of_measurement": "µg/m³",
                "device_class": SensorDeviceClass.PM25,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "`val` 值表示PM2.5值，`v` 值为实际值(单位：ug/m³)。",
            },
            "PMx": {
                "description": "PM10",
                "rw": "R",
                "data_type": "pm10",
                "conversion": "friendly_value",
                "unit_of_measurement": "µg/m³",
                "device_class": SensorDeviceClass.PM10,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "`val` 值表示PM10值，`v` 值为实际值(单位：ug/m³)。",
            },
            # 气体监测相关
            "COPPM": {
                "description": "一氧化碳",
                "rw": "R",
                "data_type": "co_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "ppm",
                "device_class": SensorDeviceClass.CO,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "`val` 值表示co浓度值，`v` 值为实际值(单位：ppm)。",
            },
            "CO2PPM": {
                "description": "二氧化碳",
                "rw": "R",
                "data_type": "co2_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "ppm",
                "device_class": SensorDeviceClass.CO2,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "`val` 值表示co2浓度值，`v` 值为实际值(单位：ppm)。",
            },
            "CH20PPM": {
                "description": "甲醛",
                "rw": "R",
                "data_type": "formaldehyde_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "ppm",
                "device_class": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "`val` 值表示甲醛原始浓度值，`v` 值为实际值(单位：ppm)。",
            },
            "O2VOL": {
                "description": "氧气",
                "rw": "R",
                "data_type": "oxygen_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "vol%",
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "`val` 值表示氧气原始浓度值，`v` 值为实际值(单位：vol%)。",
            },
            "NH3PPM": {
                "description": "氨气",
                "rw": "R",
                "data_type": "ammonia_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "ppm",
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "`val` 值表示氨气原始浓度值，`v` 值为实际值(单位：ppm)。",
            },
            "H2SPPM": {
                "description": "硫化氢",
                "rw": "R",
                "data_type": "h2s_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "ppm",
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "`val` 值表示硫化氢原始浓度值，`v` 值为实际值(单位：ppm)。",
            },
            "TVOC": {
                "description": "TVOC",
                "rw": "R",
                "data_type": "tvoc_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "mg/m³",
                "device_class": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "`val` 值表示TVOC原始浓度值，`v` 值为实际值(单位：mg/m³)。",
            },
            "PHM": {
                "description": "噪音",
                "rw": "R",
                "data_type": "noise_level",
                "conversion": "friendly_value",
                "unit_of_measurement": "dB",
                "device_class": SensorDeviceClass.SOUND_PRESSURE,
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "`val` 值表示噪音原始值，`v` 值为实际值(单位：dB)。",
            },
            "SMOKE": {
                "description": "烟雾",
                "rw": "R",
                "data_type": "smoke_concentration",
                "conversion": "friendly_value",
                "unit_of_measurement": "ppm",
                "state_class": SensorStateClass.MEASUREMENT,
                "detailed_description": "`val` 值表示烟雾原始浓度值，`v` 值为实际值(单位：ppm)。",
            },
        },
    },
    "LSSSMINIV1": {
        "name": "红外夜灯",
        "light": {
            "P1": {
                "description": "夜灯控制",
                "rw": "RW",
                "data_type": "infrared_light",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示开启红外夜灯；`type&1==0`表示关闭红外夜灯",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "开启夜灯"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭夜灯"},
                },
            },
        },
        "binary_sensor": {
            "P2": {
                "description": "人体感应",
                "rw": "R",
                "data_type": "motion_status",
                "conversion": "val_direct",
                "detailed_description": "`val`值定义如下：0：没有检测到移动，1：有检测到移动",
                "device_class": BinarySensorDeviceClass.MOTION,
            },
        },
        "sensor": {
            **_illuminance_sensor_io("P3", "环境光照"),
            **_battery_sensor_io("P4"),
        },
    },
    "SL_DF_KP": {
        "name": "云防键盘",
        "binary_sensor": {
            "KY": {
                "description": "按键状态",
                "rw": "R",
                "data_type": "keypad_status",
                "conversion": "val_direct",
                "detailed_description": "`val`值表示按键编号，0表示无按键按下，其他值表示对应按键编号",
                "device_class": BinarySensorDeviceClass.MOVING,
            },
            "TR": {
                "description": "防拆状态",
                "rw": "R",
                "data_type": "tamper_status",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`则表示触发防拆警报；`type&1==0`则表示状态正常",
                "device_class": BinarySensorDeviceClass.TAMPER,
            },
        },
        "sensor": {
            "T": {
                "description": "温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`val`值表示原始温度值，它是实际温度值*10，`v`值表示实际值(单位：℃)",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "state_class": SensorStateClass.MEASUREMENT,
            },
            "V": {
                "description": "电量",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val`值表示原始电压值，`v`值将表示当前剩余电量百分比，值范围[0,100]，它是根据`val`电压值换算的。注意：`type&1==1`表示低电报警状态",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
            },
        },
    },
    # ================= 2.11 摄像头系列 (Camera Series) =================
    # 基于官方文档2.13摄像头系列规格
    # 基础设备类型: cam，通过dev_rt属性区分具体型号
    "cam": {
        "camera": True,
        "name": "摄像头",
        "dev_rt_variants": {
            "LSCAM:LSCAMV1": {
                "name": "FRAME摄像头",
                "supported_ios": ["M", "V", "CFST"],
            },
            "LSCAM:LSICAMEZ1": {"name": "户外摄像头", "supported_ios": ["M"]},
            "LSCAM:LSICAMEZ2": {"name": "户外摄像头", "supported_ios": ["M"]},
            "LSCAM:LSLKCAMV1": {"name": "视频门锁摄像头", "supported_ios": ["M"]},
            "LSCAM:LSICAMGOS1": {
                "name": "高清摄像头",
                "supported_ios": ["M"],
                "model_key_support": {
                    "0xd2": "高清摄像头",
                    "0xda": "云视户外摄像头",
                    "0xdb": "云瞳室内摄像头",
                    "0xdc": "云瞳室外摄像头",
                },
            },
        },
        "binary_sensor": {
            "M": {
                "description": "移动检测",
                "rw": "R",
                "data_type": "motion_detection",
                "conversion": "val_direct",
                "detailed_description": "`val`值定义如下：0：没有检测到移动，1：有检测到移动",
                "device_class": BinarySensorDeviceClass.MOTION,
            },
        },
        "sensor": {
            "V": {
                "description": "电压",
                "rw": "R",
                "data_type": "battery",
                "conversion": "v_field",
                "detailed_description": "`val`表示原始电压值，`v`值将表示当前剩余电量百分比，值范围[0,100]，它是根据val电压值换算的。注意：当前只有FRAME设备有该属性",
                "device_class": SensorDeviceClass.BATTERY,
                "unit_of_measurement": PERCENTAGE,
                "state_class": SensorStateClass.MEASUREMENT,
                "availability_condition": "dev_rt == 'LSCAM:LSCAMV1'",
            },
            "CFST": {
                "description": "摄像头状态",
                "rw": "R",
                "data_type": "camera_status",
                "conversion": "val_direct",
                "detailed_description": "`val`值定义如下（按位表示值）：第0位：表示是否有外接电源，1表示有外接电源，0表示没有；第1位：是否为旋转云台，1表示摄像头在旋转云台上，0表示没有；第2位：表示是否正在旋转，1表示正在旋转。注意：当前只有FRAME设备有该属性",
                "availability_condition": "dev_rt == 'LSCAM:LSCAMV1'",
            },
        },
    },
    # ================= 2.12 车库门控制 (Garage Door Control) =================
    "SL_ETDOOR": {
        "name": "车库门控制器",
        "light": {
            "P1": {
                "description": "灯光控制",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "type_bit_0",
                "detailed_description": "`type&1==1`表示打开(忽略`val`值)；`type&1==0`表示关闭(忽略`val`值)",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                },
            },
        },
        "cover": {
            "P2": {
                "description": "车库门状态",
                "rw": "R",
                "data_type": "garage_door_status",
                "conversion": "val_direct",
                "detailed_description": "`type&1==1`表示控制正在运行；`type&1==0`表示没有运行；当正在运行的时候即(`type&1==1`):`val&0x80==0x80`表示正在开，否则表示正在关；`val&0x7F`的值表示车库门打开的百分比",
            },
            "P3": {
                "description": "车库门控制",
                "rw": "W",
                "data_type": "garage_door_control",
                "conversion": "val_direct",
                "detailed_description": "百分比取值范围：[0,100]",
                "commands": {
                    "open": {"type": 0xCF, "val": 100, "description": "完全打开"},
                    "close": {"type": 0xCF, "val": 0, "description": "完全关闭"},
                    "stop": {
                        "type": 0xCE,
                        "val": 0x80,
                        "description": "停止车库门开合",
                    },
                    "set_position": {
                        "type": 0xCF,
                        "description": "开到百分比，val=percent，percent取值:[0,100]",
                    },
                },
            },
        },
    },
    # ================= 2.13 智能报警器(CoSS版) (Smart Alarm CoSS) =================
    # 基于官方文档2.12 智能报警器（CoSS版）规格
    "SL_ALM": {
        "name": "智能报警器(CoSS版)",
        "switch": {
            "P1": {
                "description": "播放控制",
                "rw": "RW",
                "data_type": "alarm_playback",
                "conversion": "type_bit_0",
                "detailed_description": "type&1==1,表示正在播放(忽略`val` 值)；type&1==0,表示没有播放(忽略`val` 值)；val为32bit值，描述如下(16进制)：0xAABBCCDD AABB表示时间或者循环次数(最高位1表示次数，否则为时间，时间单位为秒)；CC是音量(只有16级，使用高4位，若CC值等于0将采用P2 IO定义的音量值，否则将使用CC值做为音量值)；DD表示音频序号；",
                "commands": {
                    "on": {"type": CMD_TYPE_ON, "val": 1, "description": "播放"},
                    "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "停止"},
                    "set_config_on": {
                        "type": CMD_TYPE_SET_RAW_ON,
                        "description": "设置值并播放，val=需要设置的值",
                    },
                    "set_config_off": {
                        "type": CMD_TYPE_SET_RAW_OFF,
                        "description": "设置值并停止，val=需要设置的值",
                    },
                },
            },
            "P2": {
                "description": "音量控制",
                "rw": "RW",
                "data_type": "volume_control",
                "conversion": "type_bit_0",
                "detailed_description": "type&1==1表示处于正常模式；type&1==0表示处于静音模式；`val` 值表示音量值，只有16级，使用高4位。即有效位为：0x000000F0",
                "commands": {
                    "unmute": {
                        "type": CMD_TYPE_ON,
                        "val": 1,
                        "description": "取消静音",
                    },
                    "mute": {"type": CMD_TYPE_OFF, "val": 0, "description": "设置静音"},
                    "set_volume": {
                        "type": CMD_TYPE_SET_CONFIG,
                        "description": "设置音量，val=音量值",
                    },
                },
            },
        },
    },
    # ================= 超能面板设备 (NATURE Series Devices) =================
    # 基于官方文档2.14 超能面板系列（NATURE Series)
    # 注意：这是动态分类设备，根据P5值决定是开关版还是温控版
    "SL_NATURE": {
        "dynamic": True,
        "switch_mode": {
            "condition": "P5&0xFF==1",
            "io": ["P1", "P2", "P3"],
            "sensor_io": ["P4", "P5"],
        },
        "climate_mode": {
            "condition": "P5&0xFF in [3,6]",
            "climate": {
                "P1": {
                    "description": "开关",
                    "rw": "RW",
                    "data_type": "binary_switch",
                    "conversion": "type_bit_0",
                    "detailed_description": "type&1==1,表示打开(忽略`val` 值)；type&1==0,表示关闭(忽略`val` 值)；",
                    "commands": {
                        "on": {"type": CMD_TYPE_ON, "val": 1, "description": "打开"},
                        "off": {"type": CMD_TYPE_OFF, "val": 0, "description": "关闭"},
                    },
                },
                "P4": {
                    "description": "T当前温度",
                    "rw": "R",
                    "data_type": "temperature",
                    "conversion": "v_field",
                    "detailed_description": "`v` 值表示温度值 `val` 值表示原始温度值，它是温度值*10",
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "unit_of_measurement": UnitOfTemperature.CELSIUS,
                    "state_class": SensorStateClass.MEASUREMENT,
                },
                "P5": {
                    "description": "设备种类",
                    "rw": "R",
                    "data_type": "device_type",
                    "conversion": "val_direct",
                    "detailed_description": "val&0xFF指示设备种类。1：开关面板 2：POE面板 3：温控面板 6：温控面板 注意：值必须是3或者6才是温控面板，否则是其它类型的设备。",
                },
                "P6": {
                    "description": "CFG配置",
                    "rw": "RW",
                    "data_type": "config_bitmask",
                    "conversion": "val_direct",
                    "detailed_description": "(val>>6)&0x7 指示设备类型 0：新风模式 1：风机盘管（单阀）模式 2：水地暖模式 3：风机盘管+水地暖模式 4: 风机盘管（双阀）模式 5：水地暖+新风模式",
                    "commands": {
                        "set_config": {
                            "type": CMD_TYPE_SET_RAW_ON,
                            "description": "设置配置，需要保留其它位",
                        },
                    },
                },
                "P7": {
                    "description": "MODE模式",
                    "rw": "RW",
                    "data_type": "hvac_mode",
                    "conversion": "val_direct",
                    "detailed_description": "3：Cool制冷 4：Heat 制热 7：DN地暖 8：DN_Heat 地暖+空调 注意：P6 CFG配置不同，支持的MODE也会不同",
                    "commands": _single_command_set_mode(),
                },
                "P8": {
                    "description": "tT目标温度",
                    "rw": "RW",
                    "data_type": "temperature",
                    "conversion": "v_field",
                    "detailed_description": "`v` 值表示温度值 `val` 值表示原始温度值，它是温度值*10",
                    "device_class": SensorDeviceClass.TEMPERATURE,
                    "unit_of_measurement": UnitOfTemperature.CELSIUS,
                    "commands": {
                        "set_temperature": {
                            "type": CMD_TYPE_SET_TEMP_DECIMAL,
                            "description": "设置目标温度，val=温度*10",
                        },
                    },
                },
                "P9": {
                    "description": "tF目标风速",
                    "rw": "RW",
                    "data_type": "fan_speed",
                    "conversion": "val_direct",
                    "detailed_description": "`val` 值表示风速，定义如下：0：Stop停止 0<val<30：Low低档 30<=val<65：Medium中档 65<=val<100：High高档 101：Auto自动 注意：P6 CFG配置不同，支持的tF也会不同",
                    "commands": _single_command_set_fan_speed(),
                },
                "P10": {
                    "description": "F当前风速",
                    "rw": "R",
                    "data_type": "fan_speed",
                    "conversion": "val_direct",
                    "detailed_description": "`val` 值表示风速，定义如下：0：stop停止 0<val<30：Low低档 30<=val<65：Medium中档 65<=val<100：High高档 101：Auto自动",
                },
            },
            "binary_sensor": {
                "P2": {
                    "description": "阀门状态",
                    "rw": "R",
                    "data_type": "valve_status",
                    "conversion": "val_direct",
                    "detailed_description": "阀门1状态(盘管的冷阀或者盘管的冷热阀)",
                    "device_class": BinarySensorDeviceClass.OPENING,
                },
                "P3": {
                    "description": "阀门状态",
                    "rw": "R",
                    "data_type": "valve_status",
                    "conversion": "val_direct",
                    "detailed_description": "阀门2状态（盘管的热阀或者地暖阀)",
                    "device_class": BinarySensorDeviceClass.OPENING,
                },
            },
        },
    },
    # ================= 2.14 智能面板系列 (Smart Panel Series) =================
    # 2.14.4 星玉温控面板 (Nature Thermostat)
    "SL_FCU": {
        "name": "星玉温控面板",
        "climate": {
            "P1": {
                "description": "开关",
                "rw": "RW",
                "data_type": "binary_switch",
                "conversion": "val_direct",
                "detailed_description": "开关状态：0关 1开",
                "commands": _switch_binary_on_off(),
            },
            "P6": {
                "description": "CFG配置",
                "rw": "RW",
                "data_type": "config_bitmask",
                "conversion": "val_direct",
                "detailed_description": "配置功能：bit0：热回水开关，bit1：地暖开关，bit2：制热开关，bit3：制冷开关，bit4：通风开关，bit5：除湿开关，bit6：加湿开关，bit7：应急通风开关，bit8：应急加热开关，bit9：应急制冷开关",
            },
            "P7": {
                "description": "MODE模式",
                "rw": "RW",
                "data_type": "hvac_mode",
                "conversion": "val_direct",
                "detailed_description": "运行模式：1制热、2制冷、3通风、4除湿、5加湿、6应急通风、7应急加热、8应急制冷、16自动",
                "commands": _single_command_set_mode(),
            },
            "P8": {
                "description": "tT目标温度",
                "rw": "RW",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`v` 值表示温度值 `val` 值表示原始温度值，它是温度值*10",
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
                "commands": {
                    "set_temperature": {
                        "type": CMD_TYPE_SET_TEMP_DECIMAL,
                        "description": "设置目标温度，val=温度*10",
                    },
                },
            },
            "P9": {
                "description": "tF目标风速",
                "rw": "RW",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "detailed_description": "`val` 值表示风速，定义如下：0：Stop停止 0<val<30：Low低档 30<=val<65：Medium中档 65<=val<100：High高档 101：Auto自动 注意：P6 CFG配置不同，支持的tF也会不同",
                "commands": _single_command_set_fan_speed(),
            },
        },
        "sensor": {
            "P4": {
                "description": "T当前温度",
                "rw": "R",
                "data_type": "temperature",
                "conversion": "v_field",
                "detailed_description": "`v` 值表示温度值 `val` 值表示原始温度值，它是温度值*10",
                "device_class": SensorDeviceClass.TEMPERATURE,
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
            },
            "P10": {
                "description": "F当前风速",
                "rw": "R",
                "data_type": "fan_speed",
                "conversion": "val_direct",
                "detailed_description": "`val` 值表示风速，定义如下：0：stop停止 0<val<30：Low低档 30<=val<65：Medium中档 65<=val<100：High高档 101：Auto自动",
            },
        },
        "binary_sensor": {
            "P2": {
                "description": "阀门状态",
                "rw": "R",
                "data_type": "valve_status",
                "conversion": "val_direct",
                "detailed_description": "阀门1状态(盘管的冷阀或者盘管的冷热阀)",
                "device_class": BinarySensorDeviceClass.OPENING,
            },
            "P3": {
                "description": "阀门状态",
                "rw": "R",
                "data_type": "valve_status",
                "conversion": "val_direct",
                "detailed_description": "阀门2状态（盘管的热阀或者地暖阀)",
                "device_class": BinarySensorDeviceClass.OPENING,
            },
        },
    },
}
