"""
强类型数据模型，用于定义LifeSmart设备及其组件的结构。
这些模型使用dataclasses实现，为测试提供类型安全和代码自动补全。

本文件是Phase 1增量基础设施建设的核心组件，基于ZEN专家指导设计。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Union


@dataclass
class IOConfig:
    """
    代表设备 'data' 字段中的单个IO端口配置。
    所有字段都是可选的，以适应不同设备规格的多样性。

    基于官方文档"LifeSmart智慧设备规格属性说明"的IO口定义设计。
    """

    type: Optional[Union[int, str]] = None
    val: Optional[Any] = None
    v: Optional[Any] = None
    name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于与现有系统兼容"""
        result = {}
        if self.type is not None:
            result["type"] = self.type
        if self.val is not None:
            result["val"] = self.val
        if self.v is not None:
            result["v"] = self.v
        if self.name is not None:
            result["name"] = self.name
        return result


@dataclass
class TypedDevice:
    """
    代表一个强类型的LifeSmart设备。

    这个类提供了类型安全的设备表示，同时保持与现有factories.py的完全兼容性。
    通过to_dict()方法可以无缝转换为原始字典格式。
    """

    agt: str  # Hub ID
    me: str  # Device ID
    devtype: str  # Device type
    name: str  # Device name
    data: Dict[str, IOConfig] = field(default_factory=dict)  # IO ports
    stat: int = 1  # Device status
    ver: str = "0.0.0.7"  # Device version
    fullCls: Optional[str] = None  # Full class name (for versioned devices)

    def to_dict(self) -> Dict[str, Any]:
        """
        将强类型设备对象转换回与旧工厂兼容的字典格式。

        这是保持向后兼容性的关键方法，确保强类型设备可以无缝
        替换原始的字典设备数据。
        """
        device_dict = {
            "agt": self.agt,
            "me": self.me,
            "devtype": self.devtype,
            "name": self.name,
            "data": {},
            "stat": self.stat,
            "ver": self.ver,
        }

        # 添加可选字段
        if self.fullCls:
            device_dict["fullCls"] = self.fullCls

        # 转换IO配置
        for key, io_config in self.data.items():
            device_dict["data"][key] = io_config.to_dict()

        return device_dict

    def validate_required_fields(self) -> bool:
        """验证必需字段是否存在且有效"""
        return all(
            [
                self.agt and isinstance(self.agt, str),
                self.me and isinstance(self.me, str),
                self.devtype and isinstance(self.devtype, str),
                self.name and isinstance(self.name, str),
            ]
        )

    def get_io_port_count(self) -> int:
        """获取IO端口数量"""
        return len(self.data)

    def has_io_port(self, port_name: str) -> bool:
        """检查是否存在指定的IO端口"""
        return port_name in self.data

    def get_io_port(self, port_name: str) -> Optional[IOConfig]:
        """获取指定的IO端口配置"""
        return self.data.get(port_name)


# 为特定平台定义专用的TypedDevice子类（可扩展）
@dataclass
class TypedSwitchDevice(TypedDevice):
    """专用于开关设备的强类型设备类"""

    def get_switch_ports(self) -> Dict[str, IOConfig]:
        """获取所有开关端口"""
        return {k: v for k, v in self.data.items() if k.startswith(("L", "P"))}


@dataclass
class TypedSensorDevice(TypedDevice):
    """专用于传感器设备的强类型设备类"""

    def get_sensor_ports(self) -> Dict[str, IOConfig]:
        """获取所有传感器端口"""
        return {
            k: v
            for k, v in self.data.items()
            if k in ["T", "H", "Z", "V", "P1", "P2", "P3", "P4"]
        }


@dataclass
class TypedLightDevice(TypedDevice):
    """专用于灯光设备的强类型设备类"""

    def get_color_ports(self) -> Dict[str, IOConfig]:
        """获取所有颜色控制端口"""
        return {k: v for k, v in self.data.items() if k in ["RGB", "RGBW", "DYN"]}

    def get_brightness_ports(self) -> Dict[str, IOConfig]:
        """获取所有亮度控制端口"""
        return {
            k: v
            for k, v in self.data.items()
            if k.startswith("P") and k != "RGB" and k != "RGBW"
        }


@dataclass
class TypedClimateDevice(TypedDevice):
    """专用于气候控制设备的强类型设备类"""

    def get_temperature_ports(self) -> Dict[str, IOConfig]:
        """获取所有温度相关端口"""
        return {
            k: v for k, v in self.data.items() if "T" in k or k in ["P3", "P4", "P5"]
        }


@dataclass
class TypedCoverDevice(TypedDevice):
    """专用于窗帘设备的强类型设备类"""

    def get_position_ports(self) -> Dict[str, IOConfig]:
        """获取所有位置控制端口"""
        return {
            k: v
            for k, v in self.data.items()
            if k in ["P1", "P2", "P3", "OP", "CL", "ST"]
        }


# 设备类型到专用类的映射
DEVICE_TYPE_CLASS_MAP = {
    # 开关类设备
    "SL_OL": TypedSwitchDevice,
    "SL_SW_IF1": TypedSwitchDevice,
    "SL_SW_IF2": TypedSwitchDevice,
    "SL_SW_IF3": TypedSwitchDevice,
    "SL_P_SW": TypedSwitchDevice,
    # 传感器类设备
    "SL_OE_3C": TypedSensorDevice,
    "SL_SC_THL": TypedSensorDevice,
    "SL_SC_BE": TypedSensorDevice,
    # 灯光类设备
    "SL_LI_WW": TypedLightDevice,
    "SL_CT_RGBW": TypedLightDevice,
    "SL_LI_RGBW": TypedLightDevice,
    "SL_SPOT": TypedLightDevice,
    # 气候控制设备
    "SL_NATURE": TypedClimateDevice,
    "SL_CP_AIR": TypedClimateDevice,
    "SL_CP_DN": TypedClimateDevice,
    # 窗帘设备
    "SL_DOOYA": TypedCoverDevice,
    "SL_ETDOOR": TypedCoverDevice,
}


def create_typed_device(device_type: str, **kwargs) -> TypedDevice:
    """
    根据设备类型创建适当的强类型设备实例

    Args:
        device_type: 设备类型（如'SL_SW_IF3'）
        **kwargs: 设备初始化参数

    Returns:
        对应的强类型设备实例
    """
    device_class = DEVICE_TYPE_CLASS_MAP.get(device_type, TypedDevice)
    return device_class(devtype=device_type, **kwargs)
