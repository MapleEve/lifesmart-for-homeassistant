"""
静态配置预处理器 - 消除所有动态逻辑
由 @MapleEve 创建，基于Phase 5.5.7.3纯静态map架构设计

此模块将动态设备配置转换为纯静态配置，实现O(1)性能目标。
核心功能：
- 消除正则表达式匹配
- 预计算版本化设备配置
- 生成虚拟子设备静态映射
- 将动态表达式转换为静态条件
- 预处理特殊设备能力标记
"""

import logging
from typing import Dict, Any, List, Optional, Set
import re

_LOGGER = logging.getLogger(__name__)


class StaticConfigPreprocessor:
    """静态配置预处理器 - 将动态逻辑转换为静态配置"""

    def __init__(self, raw_device_data: Dict[str, Any]):
        """
        初始化预处理器

        Args:
            raw_device_data: 原始设备数据，来自device_specs.py
        """
        self.raw_data = raw_device_data
        self.static_configs = {}
        self.preprocessing_stats = {
            "total_devices": 0,
            "dynamic_devices": 0,
            "versioned_devices": 0,
            "virtual_subdevices": 0,
            "special_devices": 0,
        }

    def generate_static_configs(self) -> Dict[str, Any]:
        """
        生成完整的静态配置

        Returns:
            完整的静态设备配置字典
        """
        _LOGGER.info("开始生成静态配置...")

        # 处理所有设备
        for device_type, raw_config in self.raw_data.items():
            self.static_configs[device_type] = self._process_device(
                device_type, raw_config
            )
            self.preprocessing_stats["total_devices"] += 1

        # 生成版本化设备的独立配置
        self._expand_versioned_devices()

        # 预处理特殊设备能力
        self._preprocess_special_devices()

        # 生成虚拟子设备
        self._expand_virtual_subdevices()

        # 验证配置完整性
        self._validate_all_configs()

        _LOGGER.info(f"静态配置生成完成: {self.preprocessing_stats}")
        return self.static_configs

    def _process_device(
        self, device_type: str, raw_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        处理单个设备配置

        Args:
            device_type: 设备类型
            raw_config: 原始配置

        Returns:
            处理后的静态配置
        """
        static_config = {
            "name": raw_config.get("name", device_type),
            "_features": self._extract_features(device_type, raw_config),
            "platforms": self._process_platforms(raw_config),
        }

        # 处理动态设备模式
        if raw_config.get("dynamic"):
            static_config["_mode_configs"] = self._process_dynamic_modes(raw_config)
            self.preprocessing_stats["dynamic_devices"] += 1

        return static_config

    def _extract_features(
        self, device_type: str, raw_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        提取设备静态特性

        Args:
            device_type: 设备类型
            raw_config: 原始配置

        Returns:
            设备特性字典
        """
        features = {
            "is_dynamic": bool(raw_config.get("dynamic")),
            "is_versioned": bool(raw_config.get("versioned")),
            "has_positioning": self._detect_positioning_capability(device_type),
            "has_dyn_color": self._detect_dynamic_color(raw_config),
            "cover_type": self._get_cover_type(device_type),
            "light_type": self._get_light_type(device_type),
            "virtual_subdevice_type": self._get_virtual_subdevice_type(raw_config),
        }

        # 从特殊设备特性库添加
        if device_type in SPECIAL_DEVICE_FEATURES:
            features.update(SPECIAL_DEVICE_FEATURES[device_type])
            self.preprocessing_stats["special_devices"] += 1

        return features

    def _process_platforms(self, raw_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理平台配置

        Args:
            raw_config: 原始配置

        Returns:
            处理后的平台配置
        """
        platforms = {}

        # 支持的平台类型
        platform_types = [
            "switch",
            "sensor",
            "binary_sensor",
            "light",
            "cover",
            "climate",
            "camera",
        ]

        for platform_type in platform_types:
            if platform_type in raw_config:
                platforms[platform_type] = raw_config[platform_type]

        return platforms

    def _process_dynamic_modes(self, raw_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        预处理动态设备的所有模式

        Args:
            raw_config: 原始配置

        Returns:
            处理后的模式配置
        """
        mode_configs = {}

        # SL_NATURE风格：从顶层直接获取
        for mode_name in ["switch_mode", "climate_mode"]:
            if mode_name in raw_config:
                mode_config = raw_config[mode_name]

                # 转换动态条件为静态条件
                condition = self._extract_static_condition(mode_name, mode_config)
                platforms = self._process_mode_platforms(mode_config)

                mode_configs[mode_name] = {
                    "condition": condition,
                    "platforms": platforms,
                }

        # SL_P风格：从control_modes中获取
        if "control_modes" in raw_config:
            control_modes = raw_config["control_modes"]
            for mode_name, mode_config in control_modes.items():
                condition = self._extract_static_condition(mode_name, mode_config)
                platforms = self._process_mode_platforms(mode_config)

                mode_configs[mode_name] = {
                    "condition": condition,
                    "platforms": platforms,
                }

        return mode_configs

    def _extract_static_condition(
        self, mode_name: str, mode_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        将动态表达式转换为静态条件

        Args:
            mode_name: 模式名称
            mode_config: 模式配置

        Returns:
            静态条件字典
        """
        # 预定义的静态条件映射（替代AST表达式解析）
        static_conditions = {
            # SL_NATURE设备模式
            "switch_mode": {"P5": [1]},
            "climate_mode": {"P5": [2, 3, 6]},  # P5=2,3,6时为climate模式
            # SL_P设备模式
            "cover_mode": {"P1": [1]},
            "curtain_mode": {"P1": [1]},
            "free_mode": {"P1": [0]},
            "sensor_mode": {},  # 传感器模式无特定条件
        }

        # 从mode_config中提取原始条件
        original_condition = mode_config.get("condition")
        if original_condition:
            # TODO: 这里可以添加更复杂的表达式解析
            # 目前使用预定义映射
            pass

        return static_conditions.get(mode_name, {})

    def _process_mode_platforms(self, mode_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理模式的平台配置

        Args:
            mode_config: 模式配置

        Returns:
            平台配置字典
        """
        platforms = {}
        platform_types = [
            "switch",
            "sensor",
            "binary_sensor",
            "light",
            "cover",
            "climate",
        ]

        # 直接平台配置
        for platform_type in platform_types:
            if platform_type in mode_config:
                platforms[platform_type] = mode_config[platform_type]

        # 处理 SL_NATURE 风格的 io 和 sensor_io 列表
        if "io" in mode_config:
            io_list = mode_config["io"]
            # 为 io 列表生成基础的 switch 平台配置
            switch_config = {}
            for io_port in io_list:
                switch_config[io_port] = {
                    "description": f"开关控制口 {io_port}",
                    "rw": "RW",
                    "data_type": "binary_switch",
                }
            platforms["switch"] = switch_config

        if "sensor_io" in mode_config:
            sensor_io_list = mode_config["sensor_io"]
            # 为 sensor_io 列表生成基础的 sensor 平台配置
            sensor_config = {}
            for io_port in sensor_io_list:
                sensor_config[io_port] = {
                    "description": f"传感器 {io_port}",
                    "rw": "R",
                    "data_type": "sensor",
                }
            platforms["sensor"] = sensor_config

        return platforms

    def _detect_positioning_capability(self, device_type: str) -> bool:
        """
        检测窗帘定位能力

        Args:
            device_type: 设备类型

        Returns:
            是否有定位能力
        """
        # 基于设备类型的定位能力映射
        positioning_devices = {
            "SL_DOOYA": True,
            "SL_CURTAIN": True,
            "SL_SW_WIN": False,
            "SL_P_V2": False,
            "SL_CN_IF": False,
        }

        return positioning_devices.get(device_type, False)

    def _detect_dynamic_color(self, raw_config: Dict[str, Any]) -> bool:
        """
        检测动态颜色能力

        Args:
            raw_config: 原始配置

        Returns:
            是否有动态颜色
        """
        # 检查是否有RGBW灯光配置
        for platform_config in raw_config.values():
            if isinstance(platform_config, dict):
                for io_config in platform_config.values():
                    if isinstance(io_config, dict):
                        if io_config.get("data_type") == "rgbw_light":
                            return True
        return False

    def _get_cover_type(self, device_type: str) -> Optional[str]:
        """
        获取窗帘类型

        Args:
            device_type: 设备类型

        Returns:
            窗帘类型或None
        """
        cover_types = {
            "SL_DOOYA": "positional",
            "SL_CURTAIN": "positional",
            "SL_SW_WIN": "non_positional",
            "SL_P_V2": "non_positional",
            "SL_CN_IF": "non_positional",
        }

        return cover_types.get(device_type)

    def _get_light_type(self, device_type: str) -> Optional[str]:
        """
        获取灯光类型

        Args:
            device_type: 设备类型

        Returns:
            灯光类型或None
        """
        light_types = {
            "SL_LI_WW": "dimmer",
            "OD_WE_QUAN": "quantum",
            "SL_LI_C": "color",
            "SL_LI_CW": "color_temp",
        }

        return light_types.get(device_type)

    def _get_virtual_subdevice_type(self, raw_config: Dict[str, Any]) -> Optional[str]:
        """
        获取虚拟子设备类型

        Args:
            raw_config: 原始配置

        Returns:
            虚拟子设备类型或None
        """
        # 检查是否需要生成虚拟子设备
        for platform_config in raw_config.values():
            if isinstance(platform_config, dict):
                for io_port in platform_config.keys():
                    # 检查ALM、EVTLO等需要位分解的IO口
                    if io_port in ["ALM", "EVTLO"]:
                        return "bitmask"

        return None

    def _expand_versioned_devices(self):
        """生成版本化设备的独立配置"""
        versioned_configs = {}

        # 从原始数据中查找版本化设备
        for device_type, raw_config in self.raw_data.items():
            if raw_config.get("versioned") and "version_modes" in raw_config:
                version_modes = raw_config["version_modes"]

                for version, version_config in version_modes.items():
                    versioned_type = f"{device_type}_{version}"
                    versioned_configs[versioned_type] = (
                        self._create_version_config_from_raw(
                            device_type, version_config, version
                        )
                    )
                    self.preprocessing_stats["versioned_devices"] += 1

        # 合并版本化配置
        self.static_configs.update(versioned_configs)

    def _create_version_config_from_raw(
        self, device_type: str, version_config: Dict[str, Any], version: str
    ) -> Dict[str, Any]:
        """
        从原始版本配置创建静态配置

        Args:
            device_type: 基础设备类型
            version_config: 版本配置数据
            version: 版本号

        Returns:
            版本化静态配置
        """
        # 提取平台配置
        platforms = self._process_platforms(version_config)

        # 创建特性标记
        features = {
            "is_dynamic": False,
            "is_versioned": True,
            "version": version,
            "has_positioning": False,
            "has_dyn_color": self._detect_dynamic_color(version_config),
            "cover_type": None,
            "light_type": self._get_light_type(device_type),
            "virtual_subdevice_type": None,
        }

        # 根据设备类型添加特定功能
        if device_type == "SL_LI_WW":
            if version == "V1":
                features["has_dimmer"] = True
                features["light_type"] = "dimmer"
            elif version == "V2":
                features["has_dimmer"] = True
                features["has_color_temp"] = True
                features["light_type"] = "color_temp"

        static_config = {
            "name": version_config.get("name", f"{device_type} {version}"),
            "_features": features,
            "platforms": platforms,
        }

        return static_config

    def _create_version_config(
        self, device_type: str, base_config: Dict[str, Any], version: str
    ) -> Dict[str, Any]:
        """
        创建特定版本的配置

        Args:
            device_type: 基础设备类型
            base_config: 基础配置
            version: 版本号

        Returns:
            版本化配置
        """
        version_config = base_config.copy()

        # 更新特性标记
        features = version_config["_features"].copy()
        features["version"] = version
        features["is_versioned"] = True

        # 根据版本添加特定功能
        if device_type == "SL_LI_WW":
            if version == "V1":
                features["has_dimmer"] = True
            elif version == "V2":
                features["has_dimmer"] = True
                features["has_color_temp"] = True

        version_config["_features"] = features
        version_config["name"] = f"{base_config['name']} {version}"

        return version_config

    def _preprocess_special_devices(self):
        """预处理特殊设备能力"""
        for device_type, config in self.static_configs.items():
            features = config.get("_features", {})

            # SL_NATURE特殊处理
            if device_type == "SL_NATURE":
                features.update(
                    {
                        "default_mode": "switch_mode",
                        "mode_switch_field": "P5",
                        "temp_sensor_ios": ["P2", "P3"],
                    }
                )

            # 窗帘设备特殊处理
            elif features.get("cover_type"):
                if features["cover_type"] == "non_positional":
                    features["cover_operations"] = ["open", "close", "stop"]
                else:
                    features["cover_operations"] = [
                        "open",
                        "close",
                        "stop",
                        "set_position",
                    ]

    def _expand_virtual_subdevices(self):
        """生成虚拟子设备配置"""
        for device_type, config in self.static_configs.items():
            if config.get("_features", {}).get("virtual_subdevice_type") == "bitmask":
                self._generate_bitmask_subdevices(device_type, config)
                self.preprocessing_stats["virtual_subdevices"] += 1

    def _generate_bitmask_subdevices(self, device_type: str, config: Dict[str, Any]):
        """
        生成位掩码虚拟子设备

        Args:
            device_type: 设备类型
            config: 设备配置
        """
        platforms = config.get("platforms", {})

        for platform_type, platform_config in platforms.items():
            if platform_type == "binary_sensor":
                for io_port in list(platform_config.keys()):
                    if io_port in ["ALM", "EVTLO"]:
                        # 为每个位生成虚拟子设备
                        for bit_pos in range(10):  # 通常0-9位
                            virtual_io = f"{io_port}_bit{bit_pos}"
                            platform_config[virtual_io] = {
                                "description": f"{io_port}第{bit_pos}位",
                                "bit_position": bit_pos,
                                "parent_io": io_port,
                                "device_class": (
                                    "alarm" if io_port == "ALM" else "event"
                                ),
                            }

    def _validate_all_configs(self):
        """验证所有配置的完整性"""
        validation_errors = []

        for device_type, config in self.static_configs.items():
            # 基本结构验证
            required_fields = ["name", "_features", "platforms"]
            for field in required_fields:
                if field not in config:
                    validation_errors.append(f"{device_type}: 缺少必需字段 '{field}'")

            # 动态设备验证
            features = config.get("_features", {})
            if features.get("is_dynamic"):
                if "_mode_configs" not in config:
                    validation_errors.append(f"{device_type}: 动态设备缺少模式配置")

        if validation_errors:
            _LOGGER.warning(f"配置验证发现问题: {validation_errors}")
        else:
            _LOGGER.info("所有配置验证通过")

    def get_preprocessing_stats(self) -> Dict[str, Any]:
        """获取预处理统计信息"""
        return self.preprocessing_stats.copy()


# 特殊设备特性定义
SPECIAL_DEVICE_FEATURES = {
    "SL_NATURE": {
        "default_mode": "switch_mode",
        "mode_switch_field": "P5",
        "temp_sensor_ios": ["P2", "P3"],
    },
    "SL_DOOYA": {
        "cover_type": "non_positional",
        "cover_operations": ["open", "close", "stop"],
        "control_ios": {"open": "P1", "close": "P2", "stop": "P3"},
    },
    "OD_WE_QUAN": {
        "light_type": "quantum",
        "effect_support": True,
        "effect_list": ["rainbow", "breath", "strobe"],
        "special_ios": ["_QUANTUM"],
    },
    "SL_LI_WW": {
        "light_type": "dimmer",
        "brightness_support": True,
        "dimmer_ios": ["_DIMMER"],
    },
    "SL_P": {
        "is_multi_mode": True,
        "default_mode": "free_mode",
        "mode_detection_field": "P1",
    },
    "SL_JEMA": {
        "is_multi_mode": True,
        "default_mode": "free_mode",
        "supports_curtain_mode": True,
    },
}

# 窗帘定位能力映射
COVER_POSITIONING_MAP = {
    "SL_SW_WIN": False,  # 无定位
    "SL_P_V2": False,  # 无定位
    "SL_CN_IF": False,  # 无定位
    "SL_DOOYA": True,  # 有定位
    "SL_CURTAIN": True,  # 有定位
}

# 版本化设备配置
VERSIONED_DEVICE_CONFIG = {
    "SL_LI_WW": {
        "V1": {"brightness_support": True},
        "V2": {"brightness_support": True, "color_temp_support": True},
    },
    "SL_OL": {
        "V1": {"power_monitoring": False},
        "V2": {"power_monitoring": True, "energy_tracking": True},
    },
}
