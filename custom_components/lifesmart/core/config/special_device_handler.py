"""
SpecialDeviceHandler - 特殊设备分类处理器
===========================================

专门处理LifeSmart生态中的特殊设备类型：
- 动态设备 (Dynamic Devices)
- 版本设备 (Versioned Devices)
- CAM设备 (Camera Devices)
- DYN动态颜色设备

基于官方文档分析结果创建，支持复杂设备结构的智能识别和处理。
由 @MapleEve 创建，遵循项目第一条原则。
"""

from typing import Dict, Any, List, Optional, Set, Union
import logging
from dataclasses import dataclass
from enum import Enum
import re

_LOGGER = logging.getLogger(__name__)


class SpecialDeviceType(Enum):
    """特殊设备类型枚举"""

    DYNAMIC = "dynamic"
    VERSIONED = "versioned"
    CAM = "cam"
    DYN_COLOR = "dyn_color"
    STANDARD = "standard"


@dataclass
class SpecialDeviceInfo:
    """特殊设备信息"""

    device_type: str
    special_type: SpecialDeviceType
    metadata: Dict[str, Any]
    resolved_config: Optional[Dict[str, Any]] = None
    processing_notes: List[str] = None

    def __post_init__(self):
        if self.processing_notes is None:
            self.processing_notes = []


class DynamicDeviceResolver:
    """动态设备解析器 - 处理根据运行时条件切换工作模式的设备"""

    # 已知的动态设备列表
    DYNAMIC_DEVICES = {
        "SL_P": {
            "name": "通用控制器",
            "modes": ["switch_mode", "sensor_mode", "climate_mode"],
            "default_mode": "switch_mode",
        },
        "SL_JEMA": {
            "name": "通用控制器HA",
            "modes": ["switch_mode", "sensor_mode", "climate_mode"],
            "default_mode": "switch_mode",
        },
        "SL_NATURE": {
            "name": "超能面板系列",
            "modes": ["switch_mode", "climate_mode"],
            "default_mode": "switch_mode",
        },
    }

    def is_dynamic_device(self, device_type: str, device_spec: Dict[str, Any]) -> bool:
        """检查是否为动态设备"""
        # 方法1: 直接标记检查
        if device_spec.get("dynamic", False):
            return True

        # 方法2: 已知列表检查
        if device_type in self.DYNAMIC_DEVICES:
            return True

        # 方法3: 结构模式检查
        dynamic_indicators = [
            "control_modes",
            "switch_mode",
            "climate_mode",
            "dynamic_config",
        ]
        return any(indicator in device_spec for indicator in dynamic_indicators)

    def resolve_dynamic_config(
        self, device_type: str, device_spec: Dict[str, Any], runtime_mode: str = None
    ) -> Dict[str, Any]:
        """解析动态设备配置"""
        if device_type in self.DYNAMIC_DEVICES:
            device_info = self.DYNAMIC_DEVICES[device_type]
            target_mode = runtime_mode or device_info["default_mode"]

            if target_mode in device_info["modes"]:
                # 构建目标模式的配置
                resolved_config = {
                    "name": device_info["name"],
                    "resolved_mode": target_mode,
                    "available_modes": device_info["modes"],
                }

                # 根据模式提取相应的平台配置
                if target_mode in device_spec:
                    resolved_config.update(device_spec[target_mode])

                return resolved_config

        return device_spec

    def get_dynamic_metadata(
        self, device_type: str, device_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取动态设备元数据"""
        if device_type in self.DYNAMIC_DEVICES:
            return self.DYNAMIC_DEVICES[device_type].copy()

        # 从设备配置中推断
        modes = []
        for key in device_spec.keys():
            if key.endswith("_mode"):
                modes.append(key)

        return {
            "name": device_spec.get("name", device_type),
            "modes": modes,
            "default_mode": modes[0] if modes else None,
        }


class VersionedDeviceResolver:
    """版本设备解析器 - 处理多版本配置的设备"""

    # 已知的版本设备列表
    VERSIONED_DEVICES = {
        "SL_SW_DM1": {
            "name": "动态调光开关",
            "versions": ["V1", "V2"],
            "default_version": "V2",
        },
        "SL_LI_WW": {
            "name": "智能灯泡",
            "versions": ["V1", "V2"],
            "default_version": "V2",
        },
    }

    def is_versioned_device(
        self, device_type: str, device_spec: Dict[str, Any]
    ) -> bool:
        """检查是否为版本设备"""
        # 方法1: 直接标记检查
        if device_spec.get("versioned", False) and "version_modes" in device_spec:
            return True

        # 方法2: 已知列表检查
        if device_type in self.VERSIONED_DEVICES:
            return True

        # 方法3: 版本模式结构检查
        return "version_modes" in device_spec

    def resolve_version_config(
        self, device_type: str, device_spec: Dict[str, Any], target_version: str = None
    ) -> Dict[str, Any]:
        """解析版本设备配置"""
        version_modes = device_spec.get("version_modes", {})
        if not version_modes:
            return device_spec

        # 确定目标版本
        if not target_version:
            if device_type in self.VERSIONED_DEVICES:
                target_version = self.VERSIONED_DEVICES[device_type]["default_version"]
            else:
                target_version = list(version_modes.keys())[0]

        # 解析版本配置
        if target_version in version_modes:
            version_config = version_modes[target_version]
            resolved_config = {
                "resolved_version": target_version,
                "available_versions": list(version_modes.keys()),
            }

            # 合并版本特定配置
            if isinstance(version_config, dict):
                resolved_config.update(version_config)

            # 保留非版本相关的字段
            for key, value in device_spec.items():
                if key not in ["version_modes", "versioned"]:
                    resolved_config.setdefault(key, value)

            return resolved_config

        return device_spec

    def get_version_metadata(
        self, device_type: str, device_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取版本设备元数据"""
        if device_type in self.VERSIONED_DEVICES:
            return self.VERSIONED_DEVICES[device_type].copy()

        # 从版本模式推断
        version_modes = device_spec.get("version_modes", {})
        return {
            "name": device_spec.get("name", device_type),
            "versions": list(version_modes.keys()),
            "default_version": list(version_modes.keys())[0] if version_modes else None,
        }


class CamDeviceResolver:
    """CAM设备解析器 - 处理摄像头设备的型号识别和配置"""

    # CAM设备型号映射
    CAM_MODELS = {
        "LSCAMV1": {
            "name": "LifeSmart 摄像头 V1",
            "features": ["video_stream", "motion_detection", "night_vision"],
            "dev_rt": "LSCAMV1",
        },
        "LSICAMEZ1": {
            "name": "LifeSmart 易看摄像头 EZ1",
            "features": ["video_stream", "motion_detection", "two_way_audio"],
            "dev_rt": "LSICAMEZ1",
        },
        "LSICAMEZ2": {
            "name": "LifeSmart 易看摄像头 EZ2",
            "features": [
                "video_stream",
                "motion_detection",
                "two_way_audio",
                "pan_tilt",
            ],
            "dev_rt": "LSICAMEZ2",
        },
        "LSLKCAMV1": {
            "name": "LifeSmart 灵看摄像头 V1",
            "features": ["video_stream", "motion_detection", "ai_recognition"],
            "dev_rt": "LSLKCAMV1",
        },
        "LSICAMGOS1": {
            "name": "LifeSmart 随行摄像头 GO S1",
            "features": ["video_stream", "motion_detection", "portable"],
            "dev_rt": "LSICAMGOS1",
        },
    }

    def is_cam_device(self, device_type: str, device_spec: Dict[str, Any]) -> bool:
        """检查是否为CAM设备"""
        # 方法1: 设备类型检查
        if device_type == "cam":
            return True

        # 方法2: 型号检查
        if device_type in self.CAM_MODELS:
            return True

        # 方法3: 配置结构检查
        cam_indicators = ["camera", "video_stream", "motion_detection"]
        spec_keys = " ".join(
            str(device_spec.get(key, "")).lower() for key in device_spec.keys()
        )
        return any(indicator in spec_keys for indicator in cam_indicators)

    def resolve_cam_model(
        self, device_type: str, device_spec: Dict[str, Any], dev_rt: str = None
    ) -> Dict[str, Any]:
        """解析CAM设备型号"""
        # 通过dev_rt识别具体型号
        if dev_rt and dev_rt in self.CAM_MODELS:
            model_info = self.CAM_MODELS[dev_rt].copy()
            resolved_config = device_spec.copy()
            resolved_config.update(
                {
                    "resolved_model": dev_rt,
                    "model_name": model_info["name"],
                    "features": model_info["features"],
                }
            )
            return resolved_config

        # 通过设备类型识别
        if device_type in self.CAM_MODELS:
            model_info = self.CAM_MODELS[device_type].copy()
            resolved_config = device_spec.copy()
            resolved_config.update(
                {
                    "resolved_model": device_type,
                    "model_name": model_info["name"],
                    "features": model_info["features"],
                }
            )
            return resolved_config

        # 默认CAM配置
        resolved_config = device_spec.copy()
        resolved_config.update(
            {
                "resolved_model": "generic_cam",
                "model_name": "通用摄像头",
                "features": ["video_stream"],
            }
        )
        return resolved_config

    def get_cam_metadata(
        self, device_type: str, device_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取CAM设备元数据"""
        return {
            "available_models": list(self.CAM_MODELS.keys()),
            "model_features": {
                model: info["features"] for model, info in self.CAM_MODELS.items()
            },
            "is_generic": device_type not in self.CAM_MODELS,
        }


class DynColorProcessor:
    """DYN动态颜色处理器 - 处理支持动态颜色效果的设备"""

    # DYN颜色支持的设备模式
    DYN_SUPPORTED_PLATFORMS = {"light", "switch"}

    # DYN颜色字段模式
    DYN_FIELD_PATTERNS = [
        re.compile(r".*dyn.*", re.IGNORECASE),
        re.compile(r".*dynamic.*color.*", re.IGNORECASE),
        re.compile(r".*rgb.*", re.IGNORECASE),
    ]

    def has_dyn_color_support(
        self, device_type: str, device_spec: Dict[str, Any]
    ) -> bool:
        """检查设备是否支持DYN动态颜色"""
        # 检查平台配置中是否有DYN相关字段
        for platform_key, platform_config in device_spec.items():
            if platform_key in self.DYN_SUPPORTED_PLATFORMS and isinstance(
                platform_config, dict
            ):
                for io_key, io_config in platform_config.items():
                    if isinstance(io_config, dict):
                        # 检查描述信息
                        description = io_config.get("detailed_description", "").lower()
                        if "dyn" in description or "动态" in description:
                            return True

                        # 检查数据类型
                        data_type = io_config.get("data_type", "").lower()
                        if any(
                            pattern.match(data_type)
                            for pattern in self.DYN_FIELD_PATTERNS
                        ):
                            return True

        return False

    def extract_dyn_capabilities(
        self, device_type: str, device_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """提取DYN颜色能力"""
        capabilities = {
            "supports_dyn": False,
            "dyn_io_ports": [],
            "color_modes": [],
            "supported_platforms": [],
        }

        for platform_key, platform_config in device_spec.items():
            if platform_key in self.DYN_SUPPORTED_PLATFORMS and isinstance(
                platform_config, dict
            ):
                platform_has_dyn = False

                for io_key, io_config in platform_config.items():
                    if isinstance(io_config, dict):
                        description = io_config.get("detailed_description", "").lower()
                        if "dyn" in description:
                            capabilities["dyn_io_ports"].append(
                                {
                                    "platform": platform_key,
                                    "io_port": io_key,
                                    "description": io_config.get("description", ""),
                                }
                            )
                            platform_has_dyn = True

                if platform_has_dyn:
                    capabilities["supported_platforms"].append(platform_key)

        capabilities["supports_dyn"] = len(capabilities["dyn_io_ports"]) > 0
        return capabilities

    def get_dyn_metadata(
        self, device_type: str, device_spec: Dict[str, Any]
    ) -> Dict[str, Any]:
        """获取DYN颜色元数据"""
        capabilities = self.extract_dyn_capabilities(device_type, device_spec)
        return {
            "dyn_support_level": "full" if capabilities["supports_dyn"] else "none",
            "dyn_io_count": len(capabilities["dyn_io_ports"]),
            "platforms_with_dyn": capabilities["supported_platforms"],
        }


class SpecialDeviceHandler:
    """特殊设备处理器主类 - 统一管理所有特殊设备类型"""

    def __init__(self):
        """初始化特殊设备处理器"""
        self.dynamic_resolver = DynamicDeviceResolver()
        self.versioned_resolver = VersionedDeviceResolver()
        self.cam_resolver = CamDeviceResolver()
        self.dyn_processor = DynColorProcessor()

        # 处理器统计
        self._stats = {
            "processed_devices": 0,
            "dynamic_devices": 0,
            "versioned_devices": 0,
            "cam_devices": 0,
            "dyn_color_devices": 0,
            "standard_devices": 0,
        }

        _LOGGER.info("SpecialDeviceHandler initialized with 4 processors")

    def classify_device(
        self, device_type: str, device_spec: Dict[str, Any]
    ) -> SpecialDeviceInfo:
        """分类设备并返回特殊设备信息"""
        self._stats["processed_devices"] += 1

        # 按优先级检查设备类型

        # 1. 检查动态设备
        if self.dynamic_resolver.is_dynamic_device(device_type, device_spec):
            self._stats["dynamic_devices"] += 1
            metadata = self.dynamic_resolver.get_dynamic_metadata(
                device_type, device_spec
            )
            return SpecialDeviceInfo(
                device_type=device_type,
                special_type=SpecialDeviceType.DYNAMIC,
                metadata=metadata,
                processing_notes=[
                    f"识别为动态设备，支持模式: {metadata.get('modes', [])}"
                ],
            )

        # 2. 检查版本设备
        if self.versioned_resolver.is_versioned_device(device_type, device_spec):
            self._stats["versioned_devices"] += 1
            metadata = self.versioned_resolver.get_version_metadata(
                device_type, device_spec
            )
            return SpecialDeviceInfo(
                device_type=device_type,
                special_type=SpecialDeviceType.VERSIONED,
                metadata=metadata,
                processing_notes=[
                    f"识别为版本设备，支持版本: {metadata.get('versions', [])}"
                ],
            )

        # 3. 检查CAM设备
        if self.cam_resolver.is_cam_device(device_type, device_spec):
            self._stats["cam_devices"] += 1
            metadata = self.cam_resolver.get_cam_metadata(device_type, device_spec)
            return SpecialDeviceInfo(
                device_type=device_type,
                special_type=SpecialDeviceType.CAM,
                metadata=metadata,
                processing_notes=[
                    f"识别为CAM设备，型号支持: {metadata.get('available_models', [])}"
                ],
            )

        # 4. 检查DYN颜色设备
        if self.dyn_processor.has_dyn_color_support(device_type, device_spec):
            self._stats["dyn_color_devices"] += 1
            metadata = self.dyn_processor.get_dyn_metadata(device_type, device_spec)
            return SpecialDeviceInfo(
                device_type=device_type,
                special_type=SpecialDeviceType.DYN_COLOR,
                metadata=metadata,
                processing_notes=[
                    f"识别为DYN动态颜色设备，支持平台: {metadata.get('platforms_with_dyn', [])}"
                ],
            )

        # 5. 标准设备
        self._stats["standard_devices"] += 1
        return SpecialDeviceInfo(
            device_type=device_type,
            special_type=SpecialDeviceType.STANDARD,
            metadata={"name": device_spec.get("name", device_type)},
            processing_notes=["标准设备，无特殊处理需求"],
        )

    def process_special_device(
        self,
        device_info: SpecialDeviceInfo,
        device_spec: Dict[str, Any],
        **processing_options,
    ) -> SpecialDeviceInfo:
        """处理特殊设备，解析最终配置"""
        device_type = device_info.device_type
        special_type = device_info.special_type

        try:
            if special_type == SpecialDeviceType.DYNAMIC:
                runtime_mode = processing_options.get("runtime_mode")
                resolved_config = self.dynamic_resolver.resolve_dynamic_config(
                    device_type, device_spec, runtime_mode
                )
                device_info.resolved_config = resolved_config
                device_info.processing_notes.append(
                    f"解析动态配置，当前模式: {resolved_config.get('resolved_mode', 'default')}"
                )

            elif special_type == SpecialDeviceType.VERSIONED:
                target_version = processing_options.get("target_version")
                resolved_config = self.versioned_resolver.resolve_version_config(
                    device_type, device_spec, target_version
                )
                device_info.resolved_config = resolved_config
                device_info.processing_notes.append(
                    f"解析版本配置，当前版本: {resolved_config.get('resolved_version', 'default')}"
                )

            elif special_type == SpecialDeviceType.CAM:
                dev_rt = processing_options.get("dev_rt")
                resolved_config = self.cam_resolver.resolve_cam_model(
                    device_type, device_spec, dev_rt
                )
                device_info.resolved_config = resolved_config
                device_info.processing_notes.append(
                    f"解析CAM型号: {resolved_config.get('resolved_model', 'generic')}"
                )

            elif special_type == SpecialDeviceType.DYN_COLOR:
                capabilities = self.dyn_processor.extract_dyn_capabilities(
                    device_type, device_spec
                )
                device_info.resolved_config = device_spec.copy()
                device_info.resolved_config["dyn_capabilities"] = capabilities
                device_info.processing_notes.append(
                    f"提取DYN颜色能力，IO口数: {len(capabilities['dyn_io_ports'])}"
                )

            else:
                # 标准设备，无特殊处理
                device_info.resolved_config = device_spec.copy()

        except Exception as e:
            _LOGGER.error(f"处理特殊设备 {device_type} 失败: {e}")
            device_info.processing_notes.append(f"处理失败: {str(e)}")
            device_info.resolved_config = device_spec.copy()

        return device_info

    def get_handler_stats(self) -> Dict[str, Any]:
        """获取处理器统计信息"""
        return self._stats.copy()

    def get_supported_special_types(self) -> List[str]:
        """获取支持的特殊设备类型列表"""
        return [t.value for t in SpecialDeviceType]

    def validate_special_device(self, device_info: SpecialDeviceInfo) -> List[str]:
        """验证特殊设备配置的有效性"""
        issues = []

        if device_info.special_type == SpecialDeviceType.DYNAMIC:
            if not device_info.metadata.get("modes"):
                issues.append("动态设备缺少工作模式定义")

        elif device_info.special_type == SpecialDeviceType.VERSIONED:
            if not device_info.metadata.get("versions"):
                issues.append("版本设备缺少版本列表")

        elif device_info.special_type == SpecialDeviceType.CAM:
            if device_info.metadata.get("is_generic", False):
                issues.append("CAM设备使用通用配置，可能功能受限")

        elif device_info.special_type == SpecialDeviceType.DYN_COLOR:
            if device_info.metadata.get("dyn_io_count", 0) == 0:
                issues.append("DYN颜色设备未找到支持动态颜色的IO口")

        return issues

    def reset_stats(self):
        """重置统计信息"""
        for key in self._stats:
            self._stats[key] = 0
        _LOGGER.debug("SpecialDeviceHandler stats reset")


# 便捷函数
def create_special_device_handler() -> SpecialDeviceHandler:
    """创建特殊设备处理器实例"""
    return SpecialDeviceHandler()


def classify_device_type(
    device_type: str, device_spec: Dict[str, Any]
) -> SpecialDeviceInfo:
    """便捷函数：分类单个设备类型"""
    handler = create_special_device_handler()
    return handler.classify_device(device_type, device_spec)


def is_special_device(device_type: str, device_spec: Dict[str, Any]) -> bool:
    """便捷函数：检查是否为特殊设备"""
    device_info = classify_device_type(device_type, device_spec)
    return device_info.special_type != SpecialDeviceType.STANDARD
