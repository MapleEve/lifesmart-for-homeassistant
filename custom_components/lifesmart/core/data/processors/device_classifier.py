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
from typing import Any, Dict, Optional

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
    """动态设备分类器，根据运行时数据确定设备模式"""

    def __init__(self):
        self.evaluator = SafeExpressionEvaluator()

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
        mode_priority = ["cover_mode", "curtain_mode", "sensor_mode", "free_mode"]

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
