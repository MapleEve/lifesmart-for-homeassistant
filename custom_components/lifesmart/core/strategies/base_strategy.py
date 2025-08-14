"""
BaseDeviceStrategy - 设备解析策略基础接口

定义所有设备解析策略的统一接口，替代mapping_engine的巨型类设计。
每个具体策略类负责单一类型的设备解析，实现单一职责原则。

由 @MapleEve 创建，基于Phase 2.5关键重构任务
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseDeviceStrategy(ABC):
    """
    设备解析策略基础接口

    所有具体策略类必须实现此接口，确保统一的调用方式。
    替代原始mapping_engine中77个方法的混合职责设计。
    """

    @abstractmethod
    def can_handle(
        self, device_type: str, device: Dict[str, Any], raw_config: Dict[str, Any]
    ) -> bool:
        """
        判断此策略是否能处理指定设备

        Args:
            device_type: 设备类型
            device: 设备数据字典
            raw_config: 原始设备配置

        Returns:
            bool: 是否能处理此设备
        """
        pass

    @abstractmethod
    def resolve_device_mapping(
        self, device: Dict[str, Any], raw_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解析设备映射配置

        Args:
            device: 设备数据字典，包含devtype、data等信息
            raw_config: 从device_spec_registry获取的原始配置

        Returns:
            Dict[str, Any]: HA规范的设备配置字典
        """
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        """
        获取策略名称，用于调试和日志记录

        Returns:
            str: 策略名称
        """
        pass

    @property
    @abstractmethod
    def priority(self) -> int:
        """
        策略优先级，数字越小优先级越高

        Returns:
            int: 优先级数值
        """
        pass

    def validate_device_data(self, device: Dict[str, Any]) -> bool:
        """
        验证设备数据的基础结构

        Args:
            device: 设备数据字典

        Returns:
            bool: 数据是否有效
        """
        if not isinstance(device, dict):
            return False

        required_fields = ["devtype"]
        return all(field in device for field in required_fields)

    def validate_raw_config(self, raw_config: Dict[str, Any]) -> bool:
        """
        验证原始配置的基础结构

        Args:
            raw_config: 原始配置字典

        Returns:
            bool: 配置是否有效
        """
        return isinstance(raw_config, dict) and bool(raw_config)

    def get_device_type(self, device: Dict[str, Any]) -> str:
        """
        获取设备类型，提供默认实现

        Args:
            device: 设备数据字典

        Returns:
            str: 设备类型
        """
        return device.get("devtype", "unknown")

    def get_device_data(self, device: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取设备数据部分，提供默认实现

        Args:
            device: 设备数据字典

        Returns:
            Dict[str, Any]: 设备数据
        """
        return device.get("data", {})

    def create_error_result(
        self, error_message: str, device_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        创建错误结果的标准格式

        Args:
            error_message: 错误消息
            device_mode: 设备模式(可选)

        Returns:
            Dict[str, Any]: 错误结果字典
        """
        result = {"_error": error_message, "_strategy": self.get_strategy_name()}
        if device_mode:
            result["_device_mode"] = device_mode
        return result
