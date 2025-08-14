"""
DynamicDeviceStrategy - 动态设备解析策略

替代mapping_engine._resolve_dynamic_device_with_logic的254行巨型方法。
将原始的4种设备模式(switch/climate/cover/free)硬编码逻辑拆分为独立处理。

从原始mapping_engine.py的503-756行提取，包括：
- switch_mode处理 (526-620行，94行)
- climate_mode处理 (622-658行，36行)
- cover_mode处理 (660-708行，48行)
- free_mode处理 (710-748行，38行)

由 @MapleEve 创建，基于Phase 2.5关键重构任务
"""

from typing import Dict, Any, Optional
from .base_strategy import BaseDeviceStrategy
from .ha_constant_strategy import HAConstantStrategy


class DynamicDeviceStrategy(BaseDeviceStrategy):
    """
    动态设备解析策略

    处理带有dynamic标记的设备，支持多种设备模式的动态分类。
    替代原始mapping_engine中254行的巨型方法，实现单一职责原则。
    """

    def __init__(self, ha_constant_strategy: HAConstantStrategy):
        """
        初始化动态设备策略

        Args:
            ha_constant_strategy: HA常量转换策略实例
        """
        self.ha_constant_strategy = ha_constant_strategy

        # 导入设备分类器
        try:
            from ..data.processors.device_classifier import device_classifier

            self.device_classifier = device_classifier
        except ImportError:
            self.device_classifier = None

    def can_handle(
        self, device_type: str, device: Dict[str, Any], raw_config: Dict[str, Any]
    ) -> bool:
        """
        判断是否为动态设备

        Args:
            device_type: 设备类型
            device: 设备数据
            raw_config: 原始配置

        Returns:
            bool: 是否能处理此设备
        """
        return raw_config.get("dynamic", False)

    def resolve_device_mapping(
        self, device: Dict[str, Any], raw_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        解析动态设备映射

        替代原始_resolve_dynamic_device_with_logic方法的254行逻辑

        Args:
            device: 设备数据字典
            raw_config: 原始动态设备配置

        Returns:
            解析后的设备配置
        """
        device_data = self.get_device_data(device)

        # 使用设备分类器确定设备模式
        device_mode = (
            self.device_classifier.classify_device(raw_config, device_data)
            if self.device_classifier
            else None
        )

        # 根据设备模式分派到对应的处理方法
        if device_mode == "switch_mode":
            return self._handle_switch_mode(
                device, raw_config, device_data, device_mode
            )
        elif device_mode == "climate_mode":
            return self._handle_climate_mode(
                device, raw_config, device_data, device_mode
            )
        elif device_mode == "cover_mode":
            return self._handle_cover_mode(device, raw_config, device_data, device_mode)
        elif device_mode == "free_mode":
            return self._handle_free_mode(device, raw_config, device_data, device_mode)
        else:
            # 未知模式，返回基础配置
            return self.create_error_result(
                f"Unknown device mode: {device_mode}", device_mode
            )

    def get_strategy_name(self) -> str:
        return "DynamicDeviceStrategy"

    @property
    def priority(self) -> int:
        return 10  # 高优先级，处理动态设备

    def _handle_switch_mode(
        self,
        device: Dict[str, Any],
        raw_config: Dict[str, Any],
        device_data: Dict[str, Any],
        device_mode: str,
    ) -> Dict[str, Any]:
        """
        处理开关模式 - 从原始526-620行提取

        支持两种配置结构:
        1. SL_NATURE风格 - 从顶层直接获取
        2. SL_P风格 - 从control_modes中获取
        """
        # 获取switch配置
        switch_config = self._get_mode_config(raw_config, "switch_mode")
        if not switch_config:
            return self.create_error_result(
                "switch_mode configuration not found", device_mode
            )

        result = {"_device_mode": device_mode}

        # 方法1: SL_NATURE风格 - 使用io列表
        if "io" in switch_config:
            io_list = switch_config.get("io", [])
            sensor_io_list = switch_config.get("sensor_io", [])

            # 添加开关平台 - 为所有io端口创建开关配置
            if io_list:
                result["switch"] = {}
                for io_port in io_list:
                    result["switch"][io_port] = {
                        "description": f"开关{io_port}",
                        "rw": "RW",
                        "data_type": "binary_switch",
                        "conversion": "type_bit_0",
                        "detailed_description": "`type&1==1` 表示打开；`type&1==0` 表示关闭",
                        "_logic_processor": "type_bit_0_switch",
                    }

            # 添加传感器平台 - 仅为存在于设备数据中的sensor_io端口
            if sensor_io_list:
                result["sensor"] = {}
                for io_port in sensor_io_list:
                    # 对于SL_NATURE的switch_mode，P5只是设备类型标识符
                    if (
                        io_port == "P5"
                        and device.get("devtype") == "SL_NATURE"
                        and device_mode == "switch_mode"
                    ):
                        continue

                    if io_port in device_data:
                        result["sensor"][io_port] = {
                            "description": f"传感器{io_port}",
                            "rw": "R",
                            "data_type": "sensor",
                            "conversion": "val_direct",
                            "_logic_processor": "direct_value_passthrough",
                        }

        # 方法2: SL_P风格 - 直接包含平台配置
        else:
            self._extract_platform_configurations(
                result, switch_config, device_data, device
            )

        # 合并设备的固有配置
        self._merge_inherent_platforms(
            result, raw_config, device_data, device.get("devtype", "")
        )

        return result

    def _handle_climate_mode(
        self,
        device: Dict[str, Any],
        raw_config: Dict[str, Any],
        device_data: Dict[str, Any],
        device_mode: str,
    ) -> Dict[str, Any]:
        """
        处理温控模式 - 从原始622-658行提取

        直接使用raw_config中定义的climate配置
        """
        climate_config = raw_config.get("climate_mode", {}).get("climate", {})
        result = {"_device_mode": device_mode}

        if climate_config:
            result["climate"] = {}
            sensor_ios = {}

            for io_port, io_config in climate_config.items():
                if isinstance(io_config, dict):
                    processed_config = self._process_io_config_with_logic(
                        io_config,
                        device_data.get(io_port, {}),
                        device.get("devtype", ""),
                    )

                    result["climate"][io_port] = processed_config

                    # 检查是否是传感器IO口
                    if self._is_sensor_io_config(io_config):
                        sensor_ios[io_port] = processed_config

            # 如果有传感器IO口，生成传感器平台
            if sensor_ios:
                result["sensor"] = sensor_ios

        # 合并设备的固有配置
        self._merge_inherent_platforms(
            result, raw_config, device_data, device.get("devtype", "")
        )

        return result

    def _handle_cover_mode(
        self,
        device: Dict[str, Any],
        raw_config: Dict[str, Any],
        device_data: Dict[str, Any],
        device_mode: str,
    ) -> Dict[str, Any]:
        """
        处理窗帘模式 - 从原始660-708行提取

        支持两种配置结构同switch_mode
        """
        cover_config = self._get_mode_config(raw_config, "cover_mode")
        if not cover_config:
            return self.create_error_result(
                "cover_mode configuration not found", device_mode
            )

        result = {"_device_mode": device_mode}

        # 提取平台配置
        self._extract_platform_configurations(result, cover_config, device_data, device)

        # 合并设备的固有配置
        self._merge_inherent_platforms(
            result, raw_config, device_data, device.get("devtype", "")
        )

        return result

    def _handle_free_mode(
        self,
        device: Dict[str, Any],
        raw_config: Dict[str, Any],
        device_data: Dict[str, Any],
        device_mode: str,
    ) -> Dict[str, Any]:
        """
        处理自由模式 - 从原始710-748行提取

        SL_P设备的默认模式
        """
        free_config = self._get_mode_config(raw_config, "free_mode")
        if not free_config:
            return self.create_error_result(
                "free_mode configuration not found", device_mode
            )

        result = {"_device_mode": device_mode}

        # 直接从free_config中提取平台配置
        for platform_name in [
            "binary_sensor",
            "sensor",
            "switch",
            "light",
            "cover",
            "climate",
        ]:
            if platform_name in free_config:
                result[platform_name] = free_config[platform_name]

        # 合并设备的固有配置
        self._merge_inherent_platforms(
            result, raw_config, device_data, device.get("devtype", "")
        )

        return result

    def _get_mode_config(
        self, raw_config: Dict[str, Any], mode_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取指定模式的配置，支持两种结构

        Args:
            raw_config: 原始配置
            mode_name: 模式名称

        Returns:
            模式配置或None
        """
        # 方法1: 从顶层直接获取 (SL_NATURE风格)
        if mode_name in raw_config:
            return raw_config[mode_name]

        # 方法2: 从control_modes中获取 (SL_P风格)
        if "control_modes" in raw_config and mode_name in raw_config["control_modes"]:
            return raw_config["control_modes"][mode_name]

        return None

    def _extract_platform_configurations(
        self,
        result: Dict[str, Any],
        mode_config: Dict[str, Any],
        device_data: Dict[str, Any],
        device: Dict[str, Any],
    ):
        """
        从模式配置中提取平台配置

        Args:
            result: 结果字典
            mode_config: 模式配置
            device_data: 设备数据
            device: 完整设备信息
        """
        supported_platforms = [
            "switch",
            "sensor",
            "binary_sensor",
            "light",
            "cover",
            "climate",
        ]

        for platform_name in supported_platforms:
            if platform_name in mode_config:
                result[platform_name] = {}
                platform_config = mode_config[platform_name]
                for io_port, io_config in platform_config.items():
                    if isinstance(io_config, dict):
                        result[platform_name][io_port] = (
                            self._process_io_config_with_logic(
                                io_config,
                                device_data.get(io_port, {}),
                                device.get("devtype", ""),
                            )
                        )

    def _process_io_config_with_logic(
        self, io_config: Dict[str, Any], io_data: Dict[str, Any], device_type: str
    ) -> Dict[str, Any]:
        """
        处理单个IO口配置，应用业务逻辑处理器

        从原始mapping_engine._process_io_config_with_logic方法简化提取

        Args:
            io_config: IO口原始配置
            io_data: IO口实际数据
            device_type: 设备类型

        Returns:
            处理后的IO口配置
        """
        if not isinstance(io_config, dict):
            return {
                "description": str(io_config) if io_config else "Unknown",
                "rw": "RW",
                "data_type": "generic",
                "conversion": "val_direct",
                "_logic_processor": "none",
                "_can_process_value": False,
            }

        # 使用HA常量转换策略
        processed_config = self.ha_constant_strategy.convert_data_to_ha_mapping(
            io_config
        )

        # 添加逻辑处理器信息（简化版本）
        processed_config["_logic_processor"] = processed_config.get(
            "processor_type", "none"
        )
        processed_config["_can_process_value"] = (
            processed_config.get("processor_type") is not None
        )

        return processed_config

    def _merge_inherent_platforms(
        self, result: Dict, raw_config: Dict, device_data: Dict, device_type: str
    ) -> None:
        """
        合并设备的固有平台配置到动态模式结果中

        从原始mapping_engine._merge_inherent_platforms方法提取

        Args:
            result: 动态模式的结果配置
            raw_config: 设备原始配置
            device_data: 设备数据
            device_type: 设备类型
        """
        inherent_platforms = [
            "sensor",
            "binary_sensor",
            "light",
            "switch",
            "cover",
            "climate",
        ]

        for platform_name in inherent_platforms:
            if platform_name in raw_config and platform_name not in result:
                platform_config = raw_config[platform_name]
                if isinstance(platform_config, dict):
                    result[platform_name] = {}
                    for io_port, io_config in platform_config.items():
                        if isinstance(io_config, dict):
                            result[platform_name][io_port] = (
                                self._process_io_config_with_logic(
                                    io_config, device_data.get(io_port, {}), device_type
                                )
                            )

    def _is_sensor_io_config(self, io_config: Dict) -> bool:
        """
        判断一个IO配置是否是传感器配置

        从原始mapping_engine._is_sensor_io_config方法提取

        Args:
            io_config: IO配置字典

        Returns:
            是否是传感器配置
        """
        if not isinstance(io_config, dict):
            return False

        # 检查传感器特征
        sensor_features = ["device_class", "unit_of_measurement", "state_class"]
        if any(feature in io_config for feature in sensor_features):
            return True

        # 检查data_type
        data_type = io_config.get("data_type", "")
        sensor_data_types = [
            "temperature",
            "humidity",
            "pressure",
            "voltage",
            "current",
            "power",
            "energy",
            "sensor",
        ]
        if data_type in sensor_data_types:
            return True

        # 检查rw特征
        rw = io_config.get("rw", "")
        if rw == "R" and data_type not in [
            "device_type",
            "config_bitmask",
            "hvac_mode",
            "fan_speed",
        ]:
            return True

        return False
