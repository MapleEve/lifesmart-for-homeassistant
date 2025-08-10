"""
LifeSmart 动态设备分类器 - 支持复杂条件评估
由 @MapleEve 初始创建和维护

此模块负责分析动态分类设备的运行时数据，
根据复杂的位运算和逻辑表达式确定设备的当前模式。

主要功能:
- 处理SL_NATURE的温控/开关模式切换
- 处理SL_P/SL_JEMA的多种控制模式切换
- 支持复杂位运算表达式：(P1>>24)&0xe == 0
- 支持集合包含判断：P5&0xFF in [3,6]
- 安全的表达式解析，防止代码注入
"""

import ast
import logging
import operator
from typing import Any, Dict, Optional, List, Tuple

_LOGGER = logging.getLogger(__name__)


class SafeExpressionEvaluator:
    """安全的表达式评估器，支持位运算和逻辑操作"""

    # 支持的运算符映射
    OPERATORS = {
        # 算术运算
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        # 位运算
        ast.BitOr: operator.or_,
        ast.BitXor: operator.xor,
        ast.BitAnd: operator.and_,
        ast.LShift: operator.lshift,
        ast.RShift: operator.rshift,
        ast.Invert: operator.invert,
        # 一元运算
        ast.UAdd: operator.pos,
        ast.USub: operator.neg,
        ast.Not: operator.not_,
        # 比较运算
        ast.Eq: operator.eq,
        ast.NotEq: operator.ne,
        ast.Lt: operator.lt,
        ast.LtE: operator.le,
        ast.Gt: operator.gt,
        ast.GtE: operator.ge,
        ast.In: lambda x, y: x in y,
        ast.NotIn: lambda x, y: x not in y,
        # 逻辑运算
        ast.And: lambda x, y: x and y,
        ast.Or: lambda x, y: x or y,
    }

    def __init__(self):
        self.variables = {}

    def evaluate(self, expression: str, variables: dict[str, Any]) -> Any:
        """
        安全评估表达式

        Args:
            expression: 表达式字符串，如 "(P1>>24)&0xe == 0"
            variables: 变量字典，如 {"P1": 123456}

        Returns:
            评估结果

        Raises:
            ValueError: 表达式不安全或无效
        """
        self.variables = variables

        try:
            # 解析为AST
            tree = ast.parse(expression, mode="eval")
            return self._eval_node(tree.body)
        except Exception as e:
            _LOGGER.error(f"Expression evaluation failed: {expression}, error: {e}")
            raise ValueError(f"Invalid expression: {expression}") from e

    def _eval_node(self, node) -> Any:
        """递归评估AST节点"""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Num):  # Python < 3.8 兼容性
            return node.n
        elif isinstance(node, ast.Str):  # Python < 3.8 兼容性
            return node.s
        elif isinstance(node, ast.Name):
            # 变量引用
            if node.id in self.variables:
                return self.variables[node.id]
            else:
                raise NameError(f"Variable '{node.id}' not defined")
        elif isinstance(node, ast.List):
            # 列表字面量，如 [3,6]
            return [self._eval_node(item) for item in node.elts]
        elif isinstance(node, ast.BinOp):
            # 二元运算
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op = self.OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op)}")
            return op(left, right)
        elif isinstance(node, ast.UnaryOp):
            # 一元运算
            operand = self._eval_node(node.operand)
            op = self.OPERATORS.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op)}")
            return op(operand)
        elif isinstance(node, ast.Compare):
            # 比较运算
            left = self._eval_node(node.left)

            for op, comparator in zip(node.ops, node.comparators):
                right = self._eval_node(comparator)
                op_func = self.OPERATORS.get(type(op))
                if op_func is None:
                    raise ValueError(f"Unsupported comparison: {type(op)}")

                result = op_func(left, right)
                if not result:
                    return False
                left = right  # Chain comparisons

            return True
        elif isinstance(node, ast.BoolOp):
            # 布尔运算 (and/or)
            if isinstance(node.op, ast.And):
                return all(self._eval_node(value) for value in node.values)
            elif isinstance(node.op, ast.Or):
                return any(self._eval_node(value) for value in node.values)
            else:
                raise ValueError(f"Unsupported boolean operator: {type(node.op)}")
        else:
            raise ValueError(f"Unsupported AST node: {type(node)}")


class DeviceClassifier:
    """动态设备分类器，根据运行时数据确定设备模式和智能IO分类"""

    def __init__(self):
        self.evaluator = SafeExpressionEvaluator()

        # IO模式特征库（增强版）
        self.io_classification_patterns = {
            "switch_pattern": {
                "indicators": {
                    "type_values": [128, 129],
                    "val_binary": True,
                    "rw_capability": True,
                },
                "confidence_weight": 0.9,
                "platform_mapping": "switch",
                "description": "开关控制模式",
            },
            "light_dimmer_pattern": {
                "indicators": {
                    "type_values": [129],
                    "val_range": (0, 255),
                    "rw_capability": True,
                },
                "confidence_weight": 0.8,
                "platform_mapping": "light",
                "description": "调光灯光模式",
            },
            "temperature_sensor_pattern": {
                "indicators": {
                    "has_v_field": True,
                    "val_temperature_range": (-400, 800),
                    "read_only": True,
                },
                "confidence_weight": 0.95,
                "platform_mapping": "sensor",
                "device_class": "temperature",
                "description": "温度传感器模式",
            },
            "binary_sensor_pattern": {
                "indicators": {
                    "type_values": [132, 133],
                    "val_binary": True,
                    "read_only": True,
                },
                "confidence_weight": 0.85,
                "platform_mapping": "binary_sensor",
                "description": "二进制传感器模式",
            },
            "generic_sensor_pattern": {
                "indicators": {"read_only": True, "numeric_value": True},
                "confidence_weight": 0.6,
                "platform_mapping": "sensor",
                "description": "通用传感器模式",
            },
        }

    def classify_io_port_intelligent(
        self,
        io_data: Dict[str, Any],
        io_port: str,
        historical_data: Optional[List[Dict]] = None,
    ) -> Tuple[str, float, Dict[str, Any]]:
        """
        智能分类IO端口类型（增强版）

        Args:
            io_data: IO端口当前数据
            io_port: IO端口名称
            historical_data: 历史数据用于模式分析

        Returns:
            (platform_type, confidence, classification_details)
        """
        if not io_data:
            return "unknown", 0.0, {"reason": "No data available"}

        classification_scores = {}
        analysis_details = {
            "io_port": io_port,
            "current_data": io_data,
            "pattern_analysis": {},
        }

        # 分析各种模式
        for pattern_name, pattern_config in self.io_classification_patterns.items():
            score = self._evaluate_io_pattern(io_data, pattern_config, historical_data)
            weighted_score = score * pattern_config["confidence_weight"]
            classification_scores[pattern_name] = weighted_score

            analysis_details["pattern_analysis"][pattern_name] = {
                "raw_score": score,
                "weighted_score": weighted_score,
                "description": pattern_config["description"],
            }

        # 选择最佳匹配
        if classification_scores:
            best_pattern = max(classification_scores, key=classification_scores.get)
            best_score = classification_scores[best_pattern]
            best_config = self.io_classification_patterns[best_pattern]

            platform_type = best_config["platform_mapping"]

            # 置信度调整
            confidence = self._calculate_adjusted_confidence(
                best_score, io_data, historical_data
            )

            analysis_details.update(
                {
                    "best_pattern": best_pattern,
                    "platform_type": platform_type,
                    "base_confidence": best_score,
                    "adjusted_confidence": confidence,
                    "device_class": best_config.get("device_class"),
                    "reasoning": self._generate_classification_reasoning(
                        best_pattern, best_config, io_data
                    ),
                }
            )

            return platform_type, confidence, analysis_details

        return "unknown", 0.0, analysis_details

    def analyze_io_patterns_multi_mode(
        self, device_data: Dict[str, Any], device_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        分析多模式设备的IO模式（支持动态切换）

        Args:
            device_data: 设备数据，包含所有IO端口
            device_mode: 当前设备模式（可选）

        Returns:
            多模式分析结果
        """
        analysis_result = {
            "device_mode": device_mode,
            "io_classifications": {},
            "platform_summary": {},
            "mode_compatibility": {},
            "recommendations": [],
        }

        # 分析每个IO端口
        for io_port, io_data in device_data.items():
            if not isinstance(io_data, dict):
                continue

            platform_type, confidence, details = self.classify_io_port_intelligent(
                io_data, io_port
            )

            analysis_result["io_classifications"][io_port] = {
                "platform_type": platform_type,
                "confidence": confidence,
                "details": details,
            }

            # 统计平台分布
            if platform_type != "unknown":
                if platform_type not in analysis_result["platform_summary"]:
                    analysis_result["platform_summary"][platform_type] = []
                analysis_result["platform_summary"][platform_type].append(
                    {"io_port": io_port, "confidence": confidence}
                )

        # 生成建议
        analysis_result["recommendations"] = self._generate_io_recommendations(
            analysis_result["platform_summary"]
        )

        return analysis_result

    def detect_mode_switching_capability(
        self, raw_config: Dict, device_data: Dict
    ) -> Dict[str, Any]:
        """
        检测设备的模式切换能力

        Args:
            raw_config: 设备原始配置
            device_data: 当前设备数据

        Returns:
            模式切换能力分析结果
        """
        capability_analysis = {
            "is_dynamic": raw_config.get("dynamic", False),
            "available_modes": [],
            "current_mode": None,
            "mode_conditions": {},
            "switching_parameters": set(),
            "mode_stability": "unknown",
        }

        if not capability_analysis["is_dynamic"]:
            return capability_analysis

        # 分析可用模式
        variables = self._extract_variables_from_device_data(device_data)

        # SL_NATURE风格的模式检测
        if "switch_mode" in raw_config and "climate_mode" in raw_config:
            capability_analysis["available_modes"] = ["switch_mode", "climate_mode"]

            # 检测当前模式
            current_mode = self._classify_nature_device(raw_config, variables)
            capability_analysis["current_mode"] = current_mode

            # 记录模式条件
            capability_analysis["mode_conditions"] = {
                "switch_mode": raw_config["switch_mode"].get("condition"),
                "climate_mode": raw_config["climate_mode"].get("condition"),
            }

        # SL_P风格的模式检测
        elif "control_modes" in raw_config:
            control_modes = raw_config["control_modes"]
            capability_analysis["available_modes"] = list(control_modes.keys())

            # 检测当前模式
            current_mode = self._classify_control_device(raw_config, variables)
            capability_analysis["current_mode"] = current_mode

            # 记录模式条件
            for mode_name, mode_config in control_modes.items():
                if "condition" in mode_config:
                    capability_analysis["mode_conditions"][mode_name] = mode_config[
                        "condition"
                    ]

        # 提取切换参数
        for condition in capability_analysis["mode_conditions"].values():
            if condition:
                params = self.get_supported_variables(condition)
                capability_analysis["switching_parameters"].update(params)

        capability_analysis["switching_parameters"] = list(
            capability_analysis["switching_parameters"]
        )

        return capability_analysis

    def _evaluate_io_pattern(
        self,
        io_data: Dict,
        pattern_config: Dict,
        historical_data: Optional[List] = None,
    ) -> float:
        """评估IO数据与特定模式的匹配度"""
        indicators = pattern_config.get("indicators", {})
        score = 0.0
        total_checks = 0

        # 检查type值模式
        if "type_values" in indicators:
            total_checks += 1
            if io_data.get("type") in indicators["type_values"]:
                score += 1.0

        # 检查二进制值模式
        if "val_binary" in indicators and indicators["val_binary"]:
            total_checks += 1
            if io_data.get("val") in [0, 1]:
                score += 1.0

        # 检查数值范围
        if "val_range" in indicators:
            total_checks += 1
            val = io_data.get("val")
            if val is not None:
                min_val, max_val = indicators["val_range"]
                if min_val <= val <= max_val:
                    score += 1.0

        # 检查v字段存在
        if "has_v_field" in indicators and indicators["has_v_field"]:
            total_checks += 1
            if "v" in io_data:
                score += 1.0

        # 检查温度范围（特殊处理）
        if "val_temperature_range" in indicators:
            total_checks += 1
            val = io_data.get("val")
            if val is not None:
                min_temp, max_temp = indicators["val_temperature_range"]
                if min_temp <= val <= max_temp:
                    score += 1.0

        # 检查数值类型
        if "numeric_value" in indicators and indicators["numeric_value"]:
            total_checks += 1
            val = io_data.get("val")
            if isinstance(val, (int, float)):
                score += 1.0

        # 历史数据一致性
        if historical_data:
            total_checks += 1
            consistency = self._check_pattern_consistency(
                io_data, historical_data, indicators
            )
            score += consistency

        return score / total_checks if total_checks > 0 else 0.0

    def _calculate_adjusted_confidence(
        self, base_score: float, io_data: Dict, historical_data: Optional[List] = None
    ) -> float:
        """计算调整后的置信度"""
        confidence = base_score

        # 数据质量调整
        if "v" in io_data and "val" in io_data:
            confidence += 0.1  # 数据完整性奖励

        # 历史数据支持
        if historical_data and len(historical_data) >= 5:
            confidence += 0.05  # 历史数据丰富性奖励

        # 确保在有效范围内
        return min(1.0, max(0.0, confidence))

    def _check_pattern_consistency(
        self, current_data: Dict, historical_data: List, indicators: Dict
    ) -> float:
        """检查模式一致性"""
        if not historical_data:
            return 0.0

        consistency_score = 0.0
        checks = 0

        # 检查type值一致性
        if "type_values" in indicators:
            checks += 1
            current_type = current_data.get("type")
            if current_type in indicators["type_values"]:
                consistency_score += 1.0

        # 检查值范围一致性
        if "val_range" in indicators:
            checks += 1
            current_val = current_data.get("val")
            if current_val is not None:
                min_val, max_val = indicators["val_range"]
                if min_val <= current_val <= max_val:
                    consistency_score += 1.0

        return consistency_score / checks if checks > 0 else 0.0

    def _extract_variables_from_device_data(self, device_data: Dict) -> Dict[str, Any]:
        """从设备数据中提取变量"""
        variables = {}
        for io_port, io_data in device_data.items():
            if isinstance(io_data, dict) and "val" in io_data:
                variables[io_port] = io_data["val"]
        return variables

    def _generate_classification_reasoning(
        self, pattern_name: str, pattern_config: Dict, io_data: Dict
    ) -> str:
        """生成分类推理说明"""
        reasoning_parts = [f"匹配模式: {pattern_config['description']}"]

        # 分析关键指标
        indicators = pattern_config.get("indicators", {})
        current_type = io_data.get("type")
        current_val = io_data.get("val")

        if "type_values" in indicators and current_type in indicators["type_values"]:
            reasoning_parts.append(f"type值({current_type})符合模式")

        if "val_binary" in indicators and current_val in [0, 1]:
            reasoning_parts.append("二进制值特征")

        if "has_v_field" in indicators and "v" in io_data:
            reasoning_parts.append("具有v字段（温度特征）")

        return "; ".join(reasoning_parts)

    def _generate_io_recommendations(self, platform_summary: Dict) -> List[str]:
        """生成IO配置建议"""
        recommendations = []

        for platform_type, ios in platform_summary.items():
            high_confidence_ios = [io for io in ios if io["confidence"] >= 0.8]
            if high_confidence_ios:
                io_list = [io["io_port"] for io in high_confidence_ios]
                recommendations.append(
                    f"建议将{', '.join(io_list)}配置为{platform_type}平台"
                )

        return recommendations

    def classify_device(self, raw_config: Dict, device_data: Dict) -> Optional[str]:
        """
        分析设备数据并确定当前模式

        Args:
            raw_config: 设备的原始配置，包含动态分类规则
            device_data: 设备的运行时数据，如 {"P1": {"val": 123}, "P5": {"val": 1}}

        Returns:
            设备模式字符串，如 "switch_mode", "climate_mode" 等，None表示无法确定
        """
        if not raw_config.get("dynamic", False):
            return None

        # 准备变量字典 - 提取各个IO口的值
        variables = {}
        for io_port, io_data in device_data.items():
            if isinstance(io_data, dict) and "val" in io_data:
                variables[io_port] = io_data["val"]

        _LOGGER.debug(f"Classifying device with variables: {variables}")

        # 检查不同的模式配置

        # 方法1：检查switch_mode和climate_mode (SL_NATURE风格)
        if "switch_mode" in raw_config and "climate_mode" in raw_config:
            return self._classify_nature_device(raw_config, variables)

        # 方法2：检查control_modes (SL_P/SL_JEMA风格)
        if "control_modes" in raw_config:
            return self._classify_control_device(raw_config, variables)

        _LOGGER.warning(f"Unknown dynamic device structure: {list(raw_config.keys())}")
        return None

    def _classify_nature_device(
        self, raw_config: Dict, variables: Dict
    ) -> Optional[str]:
        """
        分类SL_NATURE类型设备

        Args:
            raw_config: 设备配置
            variables: 变量字典

        Returns:
            模式字符串或None
        """
        # 检查climate_mode条件: P5&0xFF in [3,6]
        climate_condition = raw_config.get("climate_mode", {}).get("condition")
        if climate_condition:
            try:
                if self.evaluator.evaluate(climate_condition, variables):
                    _LOGGER.debug(
                        f"SL_NATURE classified as climate_mode: {climate_condition}"
                    )
                    return "climate_mode"
            except Exception as e:
                _LOGGER.warning(
                    f"Failed to evaluate climate condition '{climate_condition}': {e}"
                )

        # 检查switch_mode条件: P5&0xFF==1
        switch_condition = raw_config.get("switch_mode", {}).get("condition")
        if switch_condition:
            try:
                if self.evaluator.evaluate(switch_condition, variables):
                    _LOGGER.debug(
                        f"SL_NATURE classified as switch_mode: {switch_condition}"
                    )
                    return "switch_mode"
            except Exception as e:
                _LOGGER.warning(
                    f"Failed to evaluate switch condition '{switch_condition}': {e}"
                )

        _LOGGER.debug("SL_NATURE could not be classified")
        return None

    def _classify_control_device(
        self, raw_config: Dict, variables: Dict
    ) -> Optional[str]:
        """
        分类SL_P/SL_JEMA类型通用控制设备

        Args:
            raw_config: 设备配置
            variables: 变量字典

        Returns:
            模式字符串或None
        """
        control_modes = raw_config.get("control_modes", {})

        # 遍历所有控制模式，按优先级检查
        # switch_mode应该优先检查，因为开关是最基本的功能
        mode_priority = [
            "switch_mode",
            "cover_mode",
            "curtain_mode",
            "sensor_mode",
            "free_mode",
        ]

        for mode_name in mode_priority:
            if mode_name not in control_modes:
                continue

            mode_config = control_modes[mode_name]
            condition = mode_config.get("condition")

            if not condition:
                continue

            try:
                if self.evaluator.evaluate(condition, variables):
                    _LOGGER.debug(
                        f"Control device classified as {mode_name}: {condition}"
                    )
                    return mode_name
            except Exception as e:
                _LOGGER.warning(
                    f"Failed to evaluate {mode_name} condition '{condition}': {e}"
                )

        # 如果所有条件都不匹配，检查是否还有其他模式
        for mode_name, mode_config in control_modes.items():
            if mode_name in mode_priority:
                continue

            condition = mode_config.get("condition")
            if condition:
                try:
                    if self.evaluator.evaluate(condition, variables):
                        _LOGGER.debug(
                            f"Control device classified as {mode_name}: {condition}"
                        )
                        return mode_name
                except Exception as e:
                    _LOGGER.warning(
                        f"Failed to evaluate {mode_name} condition '{condition}': {e}"
                    )

        # 如果所有条件都无法评估，为SL_P设备提供默认模式
        # 检查是否有任何条件因为缺少变量而无法评估
        has_evaluation_failures = False
        for mode_name, mode_config in control_modes.items():
            condition = mode_config.get("condition")
            if condition:
                try:
                    # 尝试获取条件中使用的变量
                    required_vars = self.get_supported_variables(condition)
                    # 检查是否所有必需的变量都不存在
                    if required_vars and not any(
                        var in variables for var in required_vars
                    ):
                        has_evaluation_failures = True
                        break
                except Exception:
                    has_evaluation_failures = True
                    break

        # 如果存在评估失败且包含free_mode，默认使用free_mode
        if has_evaluation_failures and "free_mode" in control_modes:
            _LOGGER.debug("Control device defaulting to free_mode due to missing data")
            return "free_mode"

        _LOGGER.debug("Control device could not be classified")
        return None

    def get_supported_variables(self, condition: str) -> list[str]:
        """
        获取条件表达式中使用的变量列表

        Args:
            condition: 条件表达式

        Returns:
            变量名列表，如 ["P1", "P5"]
        """
        try:
            tree = ast.parse(condition, mode="eval")
            variables = []

            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    variables.append(node.id)

            return list(set(variables))  # 去重
        except Exception:
            return []

    def validate_condition_syntax(self, condition: str) -> bool:
        """
        验证条件表达式的语法是否正确

        Args:
            condition: 条件表达式

        Returns:
            True if valid, False otherwise
        """
        try:
            # 尝试解析AST
            ast.parse(condition, mode="eval")
            return True
        except SyntaxError:
            return False


# 创建全局分类器实例
device_classifier = DeviceClassifier()
