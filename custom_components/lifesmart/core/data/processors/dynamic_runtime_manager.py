"""
LifeSmart 动态设备运行时管理器
由 @MapleEve 初始创建和维护

此模块负责管理动态分类设备的运行时状态变化，
包括设备模式切换、实体的动态添加/移除等功能。

主要功能:
- 监控动态分类设备的关键参数变化
- 重新评估设备模式并触发平台切换
- 管理实体的动态添加和移除
- 确保状态一致性
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Set, Callable, List, Tuple
import re

_LOGGER = logging.getLogger(__name__)


@dataclass
class DeviceModeChangeEvent:
    """设备模式变化事件"""

    device_id: str
    device_type: str
    old_mode: Optional[str]
    new_mode: Optional[str]
    changed_parameters: dict[str, Any]
    timestamp: datetime


@dataclass
class IOPortClassificationResult:
    """IO端口分类结果"""

    io_port: str
    platform_type: str  # 推断的平台类型: switch, sensor, light等
    confidence: float  # 置信度评分 (0.0-1.0)
    pattern_evidence: Dict[str, Any]  # 分类依据
    suggested_config: Dict[str, Any]  # 建议的配置
    reasoning: str  # 分类推理过程


@dataclass
class DynamicDeviceState:
    """动态设备状态追踪"""

    device_id: str
    device_type: str
    current_mode: Optional[str]
    supported_platforms: Set[str]
    active_entities: dict[str, list[str]]  # platform -> entity_ids
    last_evaluation: datetime
    watch_parameters: Set[str]  # 需要监控的参数，如 ["P1", "P5"]
    last_data: dict[str, Any] = field(default_factory=dict)  # 存储最后已知的设备数据
    discovered_ios: dict[str, IOPortClassificationResult] = field(
        default_factory=dict
    )  # 发现的IO端口


class RuntimeIODiscovery:
    """运行时IO端口发现和分类器

    负责识别未知IO端口并基于数据模式进行智能分类。
    适用于通用控制器(SL_P)和智能面板(SL_NATURE)等动态设备。
    """

    def __init__(self, device_classifier=None):
        """初始化IO发现器

        Args:
            device_classifier: 设备分类器实例
        """
        self.device_classifier = device_classifier
        self._classification_cache = {}

        # IO数据模式特征
        self._io_patterns = {
            "binary_switch": {
                "type_patterns": [128, 129],  # 开关状态
                "val_patterns": [0, 1],  # 二进制值
                "confidence_threshold": 0.8,
            },
            "dimmer_light": {
                "type_patterns": [129],  # 调光类型
                "val_range": (0, 255),  # 调光范围
                "confidence_threshold": 0.7,
            },
            "sensor_input": {
                "type_patterns": [132, 133],  # 传感器类型
                "read_only": True,  # 只读特征
                "confidence_threshold": 0.8,
            },
            "temperature_sensor": {
                "has_v_field": True,  # 温度传感器有v字段
                "val_range": (-400, 800),  # 温度范围(-40℃到80℃)*10
                "confidence_threshold": 0.9,
            },
        }

    def discover_unknown_ports(
        self, device: Dict[str, Any], known_config: Dict[str, Any]
    ) -> List[str]:
        """发现设备中未被映射配置的IO端口

        Args:
            device: 设备信息和数据
            known_config: 已知的设备配置

        Returns:
            未知IO端口列表
        """
        device_data = device.get("data", {})
        known_ios = set()

        # 收集所有已知的IO端口
        for platform_config in known_config.values():
            if isinstance(platform_config, dict):
                for io_port in platform_config.keys():
                    if io_port not in ["condition", "io", "sensor_io"]:
                        known_ios.add(io_port)

        # 处理SL_NATURE的特殊格式
        for mode_config in known_config.values():
            if isinstance(mode_config, dict):
                # 简化的io配置格式
                if "io" in mode_config:
                    known_ios.update(mode_config["io"])
                if "sensor_io" in mode_config:
                    known_ios.update(mode_config["sensor_io"])

        # 发现未知IO端口
        unknown_ports = []
        for io_port in device_data.keys():
            if io_port not in known_ios and self._is_valid_io_port(io_port):
                unknown_ports.append(io_port)

        _LOGGER.debug(
            "Discovered unknown IO ports: %s for device %s",
            unknown_ports,
            device.get("devtype"),
        )
        return unknown_ports

    def classify_io_by_pattern(
        self,
        device: Dict[str, Any],
        io_port: str,
        historical_data: Optional[List[Dict]] = None,
    ) -> IOPortClassificationResult:
        """基于数据模式分类IO端口类型

        Args:
            device: 设备信息
            io_port: IO端口名称
            historical_data: 历史数据用于模式分析（可选）

        Returns:
            IO端口分类结果
        """
        device_data = device.get("data", {})
        io_data = device_data.get(io_port, {})

        if not io_data:
            return IOPortClassificationResult(
                io_port=io_port,
                platform_type="unknown",
                confidence=0.0,
                pattern_evidence={},
                suggested_config={},
                reasoning="No data available for analysis",
            )

        # 分析当前数据
        classification_scores = {}
        evidence = {"current_data": io_data}

        # 历史数据分析
        if historical_data:
            evidence["historical_patterns"] = self._analyze_historical_patterns(
                historical_data, io_port
            )

        # 对每种IO模式评分
        for pattern_type, pattern_config in self._io_patterns.items():
            score = self._calculate_pattern_score(
                io_data, pattern_config, historical_data
            )
            classification_scores[pattern_type] = score

        # 选择最高分的分类
        best_pattern = max(classification_scores.items(), key=lambda x: x[1])
        pattern_type, confidence = best_pattern

        # 映射到HA平台类型
        platform_type = self._map_pattern_to_platform(pattern_type)

        # 生成建议配置
        suggested_config = self._generate_suggested_config(
            pattern_type, io_port, io_data
        )

        # 生成推理说明
        reasoning = self._generate_reasoning(
            classification_scores, io_data, historical_data
        )

        return IOPortClassificationResult(
            io_port=io_port,
            platform_type=platform_type,
            confidence=confidence,
            pattern_evidence=evidence,
            suggested_config=suggested_config,
            reasoning=reasoning,
        )

    def get_classification_confidence(
        self, classification: IOPortClassificationResult
    ) -> float:
        """获取分类置信度评分

        Args:
            classification: 分类结果

        Returns:
            置信度评分 (0.0-1.0)
        """
        base_confidence = classification.confidence

        # 置信度调整因子
        adjustments = 0.0

        # 如果有历史数据支持，提高置信度
        if "historical_patterns" in classification.pattern_evidence:
            historical_evidence = classification.pattern_evidence["historical_patterns"]
            if historical_evidence.get("consistency_score", 0) > 0.8:
                adjustments += 0.1

        # 如果有明确的数据模式，提高置信度
        current_data = classification.pattern_evidence.get("current_data", {})
        if self._has_clear_pattern_indicators(
            current_data, classification.platform_type
        ):
            adjustments += 0.1

        # 确保置信度在有效范围内
        final_confidence = min(1.0, max(0.0, base_confidence + adjustments))

        return final_confidence

    def _is_valid_io_port(self, port_name: str) -> bool:
        """检查是否为有效的IO端口名称"""
        # LifeSmart IO端口命名模式: P1-P99, L1-L99, O, ALM, EVTLO等
        patterns = [
            r"^P\d+$",  # P1, P2, ... P99
            r"^L\d+$",  # L1, L2, ... L99
            r"^O$",  # O端口
            r"^ALM$",  # 报警端口
            r"^EVTLO$",  # 事件端口
        ]

        return any(re.match(pattern, port_name) for pattern in patterns)

    def _calculate_pattern_score(
        self,
        io_data: Dict,
        pattern_config: Dict,
        historical_data: Optional[List] = None,
    ) -> float:
        """计算IO数据与特定模式的匹配分数"""
        score = 0.0
        max_score = 0.0

        # 检查type字段模式
        if "type_patterns" in pattern_config:
            max_score += 1.0
            if io_data.get("type") in pattern_config["type_patterns"]:
                score += 1.0

        # 检查val字段模式
        if "val_patterns" in pattern_config:
            max_score += 1.0
            if io_data.get("val") in pattern_config["val_patterns"]:
                score += 1.0

        # 检查val范围
        if "val_range" in pattern_config:
            max_score += 1.0
            val = io_data.get("val")
            if val is not None:
                min_val, max_val = pattern_config["val_range"]
                if min_val <= val <= max_val:
                    score += 1.0

        # 检查是否有v字段（温度传感器特征）
        if "has_v_field" in pattern_config:
            max_score += 1.0
            if pattern_config["has_v_field"] and "v" in io_data:
                score += 1.0

        # 检查读写特性
        if "read_only" in pattern_config:
            max_score += 0.5
            # 这里需要从历史数据或配置中推断读写特性
            # 暂时跳过此项检查

        # 历史数据一致性检查
        if historical_data:
            max_score += 1.0
            consistency = self._check_historical_consistency(
                io_data, historical_data, pattern_config
            )
            score += consistency

        # 避免除零
        if max_score == 0:
            return 0.0

        return score / max_score

    def _analyze_historical_patterns(
        self, historical_data: List[Dict], io_port: str
    ) -> Dict[str, Any]:
        """分析历史数据中的模式"""
        if not historical_data:
            return {}

        patterns = {
            "value_stability": 0.0,
            "type_consistency": 0.0,
            "consistency_score": 0.0,
            "data_points": len(historical_data),
        }

        # 提取该IO端口的历史数据
        io_history = []
        for data_point in historical_data:
            if "data" in data_point and io_port in data_point["data"]:
                io_history.append(data_point["data"][io_port])

        if not io_history:
            return patterns

        # 分析数值稳定性
        values = [
            point.get("val") for point in io_history if point.get("val") is not None
        ]
        if values:
            unique_values = len(set(values))
            patterns["value_stability"] = 1.0 - (unique_values / len(values))

        # 分析type字段一致性
        types = [
            point.get("type") for point in io_history if point.get("type") is not None
        ]
        if types:
            unique_types = len(set(types))
            patterns["type_consistency"] = 1.0 - (unique_types / len(types))

        # 计算总体一致性评分
        patterns["consistency_score"] = (
            patterns["value_stability"] + patterns["type_consistency"]
        ) / 2

        return patterns

    def _check_historical_consistency(
        self, current_data: Dict, historical_data: List, pattern_config: Dict
    ) -> float:
        """检查当前数据与历史数据的一致性"""
        # 简化实现：检查当前值是否在历史范围内
        current_val = current_data.get("val")
        current_type = current_data.get("type")

        if current_val is None and current_type is None:
            return 0.0

        consistency_score = 0.0
        checks = 0

        # 检查type一致性
        if "type_patterns" in pattern_config and current_type is not None:
            checks += 1
            if current_type in pattern_config["type_patterns"]:
                consistency_score += 1.0

        # 检查val一致性
        if "val_range" in pattern_config and current_val is not None:
            checks += 1
            min_val, max_val = pattern_config["val_range"]
            if min_val <= current_val <= max_val:
                consistency_score += 1.0

        return consistency_score / checks if checks > 0 else 0.0

    def _map_pattern_to_platform(self, pattern_type: str) -> str:
        """将模式类型映射到HA平台类型"""
        mapping = {
            "binary_switch": "switch",
            "dimmer_light": "light",
            "sensor_input": "sensor",
            "temperature_sensor": "sensor",
        }
        return mapping.get(pattern_type, "sensor")  # 默认为sensor平台

    def _generate_suggested_config(
        self, pattern_type: str, io_port: str, io_data: Dict
    ) -> Dict[str, Any]:
        """生成建议的配置"""
        base_config = {
            "description": f"自动发现的{io_port}端口",
            "rw": "R",  # 默认只读，可根据模式调整
            "detailed_description": f"通过模式分析发现的{pattern_type}类型IO端口",
        }

        # 根据模式类型添加特定配置
        if pattern_type == "binary_switch":
            base_config.update(
                {
                    "rw": "RW",
                    "data_type": "binary_switch",
                    "conversion": "type_bit_0",
                    "commands": {
                        "on": {"type": 129, "val": 1, "description": "打开"},
                        "off": {"type": 128, "val": 0, "description": "关闭"},
                    },
                }
            )
        elif pattern_type == "dimmer_light":
            base_config.update(
                {
                    "rw": "RW",
                    "data_type": "dimmer",
                    "conversion": "val_direct",
                    "commands": {
                        "set_brightness": {"type": 129, "description": "设置亮度"}
                    },
                }
            )
        elif pattern_type == "temperature_sensor":
            base_config.update(
                {
                    "data_type": "temperature",
                    "conversion": "v_field",
                    "device_class": "temperature",
                    "unit_of_measurement": "°C",
                    "state_class": "measurement",
                }
            )
        else:  # sensor_input or unknown
            base_config.update(
                {"data_type": "generic_sensor", "conversion": "val_direct"}
            )

        return base_config

    def _generate_reasoning(
        self,
        classification_scores: Dict[str, float],
        io_data: Dict,
        historical_data: Optional[List] = None,
    ) -> str:
        """生成分类推理说明"""
        reasoning_parts = []

        # 当前数据分析
        current_val = io_data.get("val")
        current_type = io_data.get("type")
        has_v_field = "v" in io_data

        reasoning_parts.append(
            f"当前数据: val={current_val}, type={current_type}, has_v={has_v_field}"
        )

        # 分类评分
        sorted_scores = sorted(
            classification_scores.items(), key=lambda x: x[1], reverse=True
        )
        reasoning_parts.append("模式匹配评分:")
        for pattern, score in sorted_scores[:3]:  # 显示前3名
            reasoning_parts.append(f"  {pattern}: {score:.2f}")

        # 历史数据分析
        if historical_data:
            reasoning_parts.append(f"历史数据点: {len(historical_data)}个")

        return "; ".join(reasoning_parts)

    def _has_clear_pattern_indicators(self, io_data: Dict, platform_type: str) -> bool:
        """检查是否有明确的模式指示器"""
        if platform_type == "switch":
            return io_data.get("type") in [128, 129] and io_data.get("val") in [0, 1]
        elif platform_type == "sensor" and "v" in io_data:
            return True  # 温度传感器有明确的v字段
        elif platform_type == "light":
            return io_data.get("type") == 129 and 0 <= io_data.get("val", 0) <= 255
        return False


class DynamicDeviceRuntimeManager:
    """动态设备运行时管理器"""

    def __init__(self, mapping_engine, hass=None):
        """
        初始化运行时管理器

        Args:
            mapping_engine: 映射引擎实例
            hass: Home Assistant实例（可选）
        """
        self.mapping_engine = mapping_engine
        self.hass = hass

        # 动态设备状态跟踪
        self.tracked_devices: dict[str, DynamicDeviceState] = {}

        # 模式变化回调
        self.mode_change_callbacks: list[Callable] = []

        # 支持的动态设备类型
        self.supported_dynamic_types = {"SL_NATURE", "SL_P", "SL_JEMA"}

        # 避免频繁重新评估的防抖机制
        self.evaluation_debounce = timedelta(seconds=5)

        # 初始化IO发现器
        self.io_discovery = RuntimeIODiscovery(
            device_classifier=getattr(mapping_engine, "device_classifier", None)
        )

        _LOGGER.debug("Dynamic device runtime manager initialized with IO discovery")

    def register_device(self, device: dict[str, Any]) -> bool:
        """
        注册需要动态管理的设备

        Args:
            device: 设备信息字典

        Returns:
            True if registered successfully
        """
        device_id = device.get("devid", "")
        device_type = device.get("devtype", "")

        if not device_id or device_type not in self.supported_dynamic_types:
            return False

        # 获取设备配置
        from ..config.device_specs import DEVICE_SPECS_DATA

        raw_config = DEVICE_SPECS_DATA.get(device_type, {})

        if not raw_config.get("dynamic", False):
            return False

        # 确定需要监控的参数
        watch_params = self._extract_watch_parameters(raw_config)

        # 进行初始评估
        current_mode = self._evaluate_device_mode(device, raw_config)
        supported_platforms = self._get_supported_platforms(raw_config, current_mode)

        # 创建设备状态跟踪
        device_state = DynamicDeviceState(
            device_id=device_id,
            device_type=device_type,
            current_mode=current_mode,
            supported_platforms=supported_platforms,
            active_entities={},
            last_evaluation=datetime.now(),
            watch_parameters=watch_params,
        )

        self.tracked_devices[device_id] = device_state

        _LOGGER.info(
            "Registered dynamic device %s (%s) in mode: %s",
            device_id,
            device_type,
            current_mode,
        )
        return True

    def update_device_data(
        self, device_id: str, new_data: dict[str, Any]
    ) -> Optional[DeviceModeChangeEvent]:
        """
        更新设备数据并检查是否需要模式切换

        Args:
            device_id: 设备ID
            new_data: 新的设备数据

        Returns:
            模式变化事件（如果发生了变化）
        """
        if device_id not in self.tracked_devices:
            return None

        device_state = self.tracked_devices[device_id]

        # 防抖机制：避免频繁评估
        now = datetime.now()
        if now - device_state.last_evaluation < self.evaluation_debounce:
            return None

        # 检查关键参数是否发生变化
        changed_params = self._detect_parameter_changes(device_state, new_data)

        if not changed_params:
            return None

        # 重新评估设备模式
        from ..config.device_specs import DEVICE_SPECS_DATA

        raw_config = DEVICE_SPECS_DATA.get(device_state.device_type, {})

        device = {
            "devid": device_id,
            "devtype": device_state.device_type,
            "data": new_data,
        }

        new_mode = self._evaluate_device_mode(device, raw_config)
        old_mode = device_state.current_mode

        # 更新评估时间
        device_state.last_evaluation = now

        # 检查是否发生模式变化
        if new_mode != old_mode:
            # 更新设备状态
            device_state.current_mode = new_mode
            device_state.supported_platforms = self._get_supported_platforms(
                raw_config, new_mode
            )

            # 创建变化事件
            change_event = DeviceModeChangeEvent(
                device_id=device_id,
                device_type=device_state.device_type,
                old_mode=old_mode,
                new_mode=new_mode,
                changed_parameters=changed_params,
                timestamp=now,
            )

            _LOGGER.warning(
                f"Device {device_id} mode changed: {old_mode} -> {new_mode}"
            )

            # 通知回调
            self._notify_mode_change(change_event)

            return change_event

        return None

    def discover_and_classify_ios(
        self, device: Dict[str, Any], device_state: DynamicDeviceState
    ) -> bool:
        """
        发现并分类设备的未知IO端口

        Args:
            device: 设备信息
            device_state: 设备状态

        Returns:
            True if new IOs were discovered
        """
        device_type = device.get("devtype", "")

        # 获取设备配置
        from ..config.device_specs import DEVICE_SPECS_DATA

        raw_config = DEVICE_SPECS_DATA.get(device_type, {})

        if not raw_config.get("dynamic", False):
            return False

        # 发现未知IO端口
        unknown_ports = self.io_discovery.discover_unknown_ports(device, raw_config)

        if not unknown_ports:
            return False

        newly_discovered = False

        # 对每个未知端口进行分类
        for io_port in unknown_ports:
            if io_port not in device_state.discovered_ios:
                # 进行IO分类
                classification_result = self.io_discovery.classify_io_by_pattern(
                    device, io_port
                )

                # 只接受高置信度的分类结果
                confidence = self.io_discovery.get_classification_confidence(
                    classification_result
                )

                if confidence >= 0.7:  # 置信度阈值
                    device_state.discovered_ios[io_port] = classification_result
                    newly_discovered = True

                    _LOGGER.info(
                        "Discovered new IO port %s on device %s: "
                        "classified as %s (confidence: %.2f)",
                        io_port,
                        device_state.device_id,
                        classification_result.platform_type,
                        confidence,
                    )
                else:
                    _LOGGER.debug(
                        "IO port %s classification confidence too low: %.2f",
                        io_port,
                        confidence,
                    )

        return newly_discovered

    def get_dynamic_platform_mapping(self, device_id: str) -> Dict[str, List[str]]:
        """
        获取设备的动态平台映射（包括发现的IO端口）

        Args:
            device_id: 设备ID

        Returns:
            平台到IO端口的映射，包括动态发现的端口
        """
        if device_id not in self.tracked_devices:
            return {}

        device_state = self.tracked_devices[device_id]

        # 基础映射（从设备模式获取）
        mapping = {}
        for platform in device_state.supported_platforms:
            mapping[platform] = []

        # 添加发现的IO端口
        for io_port, classification in device_state.discovered_ios.items():
            platform_type = classification.platform_type
            if platform_type != "unknown":
                if platform_type not in mapping:
                    mapping[platform_type] = []
                mapping[platform_type].append(io_port)

        return mapping

    def get_discovered_io_config(
        self, device_id: str, io_port: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取发现的IO端口的建议配置

        Args:
            device_id: 设备ID
            io_port: IO端口名称

        Returns:
            IO端口的建议配置或None
        """
        if device_id not in self.tracked_devices:
            return None

        device_state = self.tracked_devices[device_id]
        classification = device_state.discovered_ios.get(io_port)

        if classification:
            return classification.suggested_config

        return None

    def get_current_platforms(self, device_id: str) -> Set[str]:
        """
        获取设备当前支持的平台

        Args:
            device_id: 设备ID

        Returns:
            支持的平台集合
        """
        if device_id in self.tracked_devices:
            return self.tracked_devices[device_id].supported_platforms.copy()
        return set()

    def get_device_mode(self, device_id: str) -> Optional[str]:
        """
        获取设备当前模式

        Args:
            device_id: 设备ID

        Returns:
            当前模式或None
        """
        if device_id in self.tracked_devices:
            return self.tracked_devices[device_id].current_mode
        return None

    def register_mode_change_callback(
        self, callback: Callable[[DeviceModeChangeEvent], None]
    ):
        """
        注册模式变化回调函数

        Args:
            callback: 回调函数
        """
        self.mode_change_callbacks.append(callback)

    def _extract_watch_parameters(self, raw_config: Dict) -> Set[str]:
        """
        从配置中提取需要监控的参数

        Args:
            raw_config: 原始设备配置

        Returns:
            需要监控的参数集合
        """
        watch_params = set()

        # 从条件表达式中提取参数
        if "switch_mode" in raw_config:
            condition = raw_config["switch_mode"].get("condition", "")
            if self.mapping_engine.device_classifier:
                params = self.mapping_engine.device_classifier.get_supported_variables(
                    condition
                )
                watch_params.update(params)

        if "climate_mode" in raw_config:
            condition = raw_config["climate_mode"].get("condition", "")
            if self.mapping_engine.device_classifier:
                params = self.mapping_engine.device_classifier.get_supported_variables(
                    condition
                )
                watch_params.update(params)

        if "control_modes" in raw_config:
            for mode_config in raw_config["control_modes"].values():
                condition = mode_config.get("condition", "")
                if condition and self.mapping_engine.device_classifier:
                    params = (
                        self.mapping_engine.device_classifier.get_supported_variables(
                            condition
                        )
                    )
                    watch_params.update(params)

        return watch_params

    def _evaluate_device_mode(self, device: Dict, raw_config: Dict) -> Optional[str]:
        """
        评估设备模式

        Args:
            device: 设备信息
            raw_config: 原始配置

        Returns:
            设备模式
        """
        if self.mapping_engine.device_classifier:
            return self.mapping_engine.device_classifier.classify_device(
                raw_config, device.get("data", {})
            )
        return None

    def _get_supported_platforms(
        self, raw_config: Dict, mode: Optional[str]
    ) -> Set[str]:
        """
        根据模式获取支持的平台

        Args:
            raw_config: 原始配置
            mode: 当前模式

        Returns:
            支持的平台集合
        """
        if not mode:
            return set()

        platforms = set()

        # SL_NATURE风格
        if mode == "switch_mode" and "switch_mode" in raw_config:
            switch_config = raw_config["switch_mode"]
            if switch_config.get("io"):
                platforms.add("switch")
            if switch_config.get("sensor_io"):
                platforms.add("sensor")

        elif mode == "climate_mode" and "climate_mode" in raw_config:
            climate_config = raw_config["climate_mode"].get("climate", {})
            for platform in climate_config.keys():
                if platform != "climate":  # climate是配置键，不是平台名
                    platforms.add(platform)
            platforms.add("climate")  # 总是包含climate平台

        # SL_P/SL_JEMA风格
        elif "control_modes" in raw_config and mode in raw_config["control_modes"]:
            mode_config = raw_config["control_modes"][mode]
            for platform in mode_config.keys():
                if platform != "condition":
                    platforms.add(platform)

        return platforms

    def _detect_parameter_changes(
        self, device_state: DynamicDeviceState, new_data: Dict
    ) -> dict[str, Any]:
        """
        检测关键参数是否发生变化

        Args:
            device_state: 设备状态
            new_data: 新数据

        Returns:
            变化的参数字典
        """
        changed_params = {}

        # 获取上次保存的数据进行比较
        last_data = device_state.last_data

        for param in device_state.watch_parameters:
            if param in new_data:
                # 检查参数是否真正发生了变化
                if self._is_parameter_changed(last_data.get(param), new_data[param]):
                    changed_params[param] = new_data[param]
                    _LOGGER.debug(
                        "Parameter %s changed for device %s: %s -> %s",
                        param,
                        device_state.device_id,
                        last_data.get(param),
                        new_data[param],
                    )

        # 更新最后已知数据（只保存监控的参数以节省内存）
        if changed_params:
            for param in device_state.watch_parameters:
                if param in new_data:
                    device_state.last_data[param] = self._create_parameter_snapshot(
                        new_data[param]
                    )

        return changed_params

    def _is_parameter_changed(self, old_param: Any, new_param: Any) -> bool:
        """
        比较单个参数是否发生变化

        Args:
            old_param: 旧参数值
            new_param: 新参数值

        Returns:
            True if parameter changed
        """
        try:
            # 如果没有历史数据，认为是变化
            if old_param is None:
                return True

            # 对于字典类型（LifeSmart IO口数据格式）
            if isinstance(new_param, dict) and isinstance(old_param, dict):
                # 比较关键字段
                key_fields = ["val", "v", "type"]
                for field_name in key_fields:
                    old_val = old_param.get(field_name)
                    new_val = new_param.get(field_name)
                    if old_val != new_val:
                        return True
                return False

            # 对于其他类型，直接比较值
            return old_param != new_param

        except Exception as e:
            _LOGGER.debug("Error comparing parameters: %s", e)
            # 发生异常时，认为参数发生了变化（安全起见）
            return True

    def _create_parameter_snapshot(self, param_data: Any) -> Any:
        """
        创建参数数据快照（浅拷贝关键字段）

        Args:
            param_data: 参数数据

        Returns:
            参数快照
        """
        try:
            if isinstance(param_data, dict):
                # 只保存关键字段，减少内存使用
                snapshot = {}
                key_fields = ["val", "v", "type"]
                for field_name in key_fields:
                    if field_name in param_data:
                        snapshot[field_name] = param_data[field_name]
                return snapshot
            else:
                # 对于非字典类型，直接返回值
                return param_data
        except Exception as e:
            _LOGGER.debug("Error creating parameter snapshot: %s", e)
            return param_data

    def _notify_mode_change(self, event: DeviceModeChangeEvent):
        """
        通知所有注册的回调函数

        Args:
            event: 模式变化事件
        """
        for callback in self.mode_change_callbacks:
            try:
                callback(event)
            except Exception as e:
                _LOGGER.error(f"Mode change callback failed: {e}")


# 全局运行时管理器实例（延迟初始化）
_runtime_manager: Optional[DynamicDeviceRuntimeManager] = None


def get_runtime_manager(
    mapping_engine=None, hass=None
) -> Optional[DynamicDeviceRuntimeManager]:
    """
    获取全局运行时管理器实例

    Args:
        mapping_engine: 映射引擎（首次调用时需要）
        hass: Home Assistant实例（可选）

    Returns:
        运行时管理器实例
    """
    global _runtime_manager

    if _runtime_manager is None and mapping_engine is not None:
        _runtime_manager = DynamicDeviceRuntimeManager(mapping_engine, hass)

    return _runtime_manager
