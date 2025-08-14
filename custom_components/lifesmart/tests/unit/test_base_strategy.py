"""
BaseDeviceStrategy 单元测试 - Phase 2 核心组件

测试基础策略接口的核心功能：
- 抽象方法的正确实现要求
- 辅助方法的验证和错误处理
- 标准化错误结果生成
- 输入数据验证机制

基于 @MapleEve 的 Phase 2.5 重构设计
"""

from abc import ABC
from unittest.mock import MagicMock

import pytest

from custom_components.lifesmart.core.strategies.base_strategy import BaseDeviceStrategy

# 从强类型工厂导入测试数据
from ...utils.typed_factories import (
    create_typed_smart_plug,
    create_typed_thermostat_panel,
)


class ConcreteStrategy(BaseDeviceStrategy):
    """用于测试的具体策略实现。"""

    def __init__(self, name="TestStrategy", priority=50):
        self.name = name
        self._priority = priority

    def can_handle(self, device_type: str, device: dict, raw_config: dict) -> bool:
        return device_type == "TEST_DEVICE"

    def resolve_device_mapping(self, device: dict, raw_config: dict) -> dict:
        return {"test_mapping": True}

    def get_strategy_name(self) -> str:
        return self.name

    @property
    def priority(self) -> int:
        return self._priority


class IncompleteStrategy(BaseDeviceStrategy):
    """用于测试抽象方法要求的不完整策略。"""

    pass


@pytest.fixture
def strategy() -> ConcreteStrategy:
    """提供一个具体的策略实例用于测试。"""
    return ConcreteStrategy()


class TestBaseDeviceStrategyAbstractMethods:
    """BaseDeviceStrategy 抽象方法测试套件。"""

    def test_abstract_class_cannot_be_instantiated(self):
        """
        测试抽象类不能直接实例化。
        Hypothesis: BaseDeviceStrategy是抽象类，不能直接创建实例。
        """
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BaseDeviceStrategy()

    def test_incomplete_implementation_cannot_be_instantiated(self):
        """
        测试不完整的实现不能被实例化。
        Hypothesis: 未实现所有抽象方法的子类不能创建实例。
        """
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteStrategy()

    def test_concrete_implementation_can_be_instantiated(
        self, strategy: ConcreteStrategy
    ):
        """
        测试完整实现的策略可以被实例化。
        Hypothesis: 实现所有抽象方法的子类应该能正常创建实例。
        """
        assert isinstance(strategy, BaseDeviceStrategy)
        assert isinstance(strategy, ConcreteStrategy)

    def test_abstract_methods_are_implemented(self, strategy: ConcreteStrategy):
        """
        测试所有抽象方法都已实现。
        Hypothesis: 具体实现应该提供所有抽象方法的实现。
        """
        # Test can_handle
        result = strategy.can_handle("TEST_DEVICE", {}, {})
        assert isinstance(result, bool)

        # Test resolve_device_mapping
        mapping = strategy.resolve_device_mapping({}, {})
        assert isinstance(mapping, dict)

        # Test get_strategy_name
        name = strategy.get_strategy_name()
        assert isinstance(name, str)

        # Test priority property
        priority = strategy.priority
        assert isinstance(priority, int)


class TestBaseDeviceStrategyValidationMethods:
    """BaseDeviceStrategy 验证方法测试套件。"""

    def test_validate_device_data_valid_data(self, strategy: ConcreteStrategy):
        """
        测试有效设备数据的验证。
        Hypothesis: 包含所有必需字段的有效设备数据应该通过验证。
        """
        # Arrange
        valid_device = create_typed_smart_plug().to_dict()

        # Act
        is_valid = strategy.validate_device_data(valid_device)

        # Assert
        assert is_valid is True

    def test_validate_device_data_invalid_type(self, strategy: ConcreteStrategy):
        """
        测试无效数据类型的处理。
        Hypothesis: 非字典类型的设备数据应该验证失败。
        """
        # Test various invalid types
        invalid_inputs = [None, "string", 123, [], set()]

        for invalid_input in invalid_inputs:
            is_valid = strategy.validate_device_data(invalid_input)
            assert is_valid is False, f"Expected False for input: {invalid_input}"

    def test_validate_device_data_missing_required_fields(
        self, strategy: ConcreteStrategy
    ):
        """
        测试缺少必需字段的处理。
        Hypothesis: 缺少devtype字段的设备数据应该验证失败。
        """
        # Test missing devtype
        invalid_device = {"me": "test_device", "name": "Test Device"}

        is_valid = strategy.validate_device_data(invalid_device)
        assert is_valid is False

    def test_validate_raw_config_valid_data(self, strategy: ConcreteStrategy):
        """
        测试有效原始配置的验证。
        Hypothesis: 非空字典应该通过原始配置验证。
        """
        valid_configs = [
            {"name": "Test Config"},
            {"dynamic": True, "platforms": {"switch": {}}},
            {"priority": 10},
        ]

        for config in valid_configs:
            is_valid = strategy.validate_raw_config(config)
            assert is_valid is True

    def test_validate_raw_config_invalid_data(self, strategy: ConcreteStrategy):
        """
        测试无效原始配置的处理。
        Hypothesis: 非字典类型或空字典应该验证失败。
        """
        invalid_configs = [None, "string", 123, [], {}, set()]

        for invalid_config in invalid_configs:
            is_valid = strategy.validate_raw_config(invalid_config)
            assert is_valid is False, f"Expected False for config: {invalid_config}"


class TestBaseDeviceStrategyHelperMethods:
    """BaseDeviceStrategy 辅助方法测试套件。"""

    def test_get_device_type_with_devtype(self, strategy: ConcreteStrategy):
        """
        测试从设备数据中获取设备类型。
        Hypothesis: 包含devtype字段的设备应该返回正确的设备类型。
        """
        # Arrange
        device = {"devtype": "SL_OL", "me": "test_device"}

        # Act
        device_type = strategy.get_device_type(device)

        # Assert
        assert device_type == "SL_OL"

    def test_get_device_type_missing_devtype(self, strategy: ConcreteStrategy):
        """
        测试缺少devtype时的默认处理。
        Hypothesis: 缺少devtype字段时应该返回"unknown"。
        """
        # Arrange
        device = {"me": "test_device", "name": "Test Device"}

        # Act
        device_type = strategy.get_device_type(device)

        # Assert
        assert device_type == "unknown"

    def test_get_device_data_with_data(self, strategy: ConcreteStrategy):
        """
        测试从设备中获取数据部分。
        Hypothesis: 包含data字段的设备应该返回其数据部分。
        """
        # Arrange
        expected_data = {"P1": {"type": "on", "val": 1}}
        device = {"devtype": "SL_OL", "data": expected_data, "me": "test_device"}

        # Act
        device_data = strategy.get_device_data(device)

        # Assert
        assert device_data == expected_data

    def test_get_device_data_missing_data(self, strategy: ConcreteStrategy):
        """
        测试缺少data字段时的默认处理。
        Hypothesis: 缺少data字段时应该返回空字典。
        """
        # Arrange
        device = {"devtype": "SL_OL", "me": "test_device"}

        # Act
        device_data = strategy.get_device_data(device)

        # Assert
        assert device_data == {}

    def test_get_device_data_with_real_device(self, strategy: ConcreteStrategy):
        """
        测试使用真实设备数据的获取。
        Hypothesis: 真实的强类型设备数据应该能正确提取data部分。
        """
        # Arrange
        device = create_typed_thermostat_panel().to_dict()

        # Act
        device_data = strategy.get_device_data(device)

        # Assert
        assert isinstance(device_data, dict)
        assert len(device_data) > 0  # 真实设备应该有数据
        # 验证一些已知的温控设备IO口
        expected_ios = ["P1", "P4", "P5", "P6", "P7", "P8", "P9", "P10"]
        for io in expected_ios:
            assert io in device_data


class TestBaseDeviceStrategyErrorHandling:
    """BaseDeviceStrategy 错误处理测试套件。"""

    def test_create_error_result_basic(self, strategy: ConcreteStrategy):
        """
        测试基础错误结果创建。
        Hypothesis: 应该创建包含错误信息和策略名称的错误字典。
        """
        # Arrange
        error_message = "Test error occurred"

        # Act
        error_result = strategy.create_error_result(error_message)

        # Assert
        assert error_result["_error"] == error_message
        assert error_result["_strategy"] == "TestStrategy"
        assert "_device_mode" not in error_result

    def test_create_error_result_with_device_mode(self, strategy: ConcreteStrategy):
        """
        测试包含设备模式的错误结果创建。
        Hypothesis: 当提供设备模式时，应该包含在错误结果中。
        """
        # Arrange
        error_message = "Device mode specific error"
        device_mode = "switch_mode"

        # Act
        error_result = strategy.create_error_result(error_message, device_mode)

        # Assert
        assert error_result["_error"] == error_message
        assert error_result["_strategy"] == "TestStrategy"
        assert error_result["_device_mode"] == device_mode

    def test_create_error_result_different_strategies(self):
        """
        测试不同策略名称的错误结果。
        Hypothesis: 错误结果中的策略名称应该反映实际的策略实例。
        """
        # Arrange
        strategy1 = ConcreteStrategy("Strategy1", 10)
        strategy2 = ConcreteStrategy("Strategy2", 20)
        error_message = "Common error"

        # Act
        error1 = strategy1.create_error_result(error_message)
        error2 = strategy2.create_error_result(error_message)

        # Assert
        assert error1["_error"] == error_message
        assert error1["_strategy"] == "Strategy1"
        assert error2["_error"] == error_message
        assert error2["_strategy"] == "Strategy2"

    def test_create_error_result_empty_message(self, strategy: ConcreteStrategy):
        """
        测试空错误信息的处理。
        Hypothesis: 空错误信息也应该被正确处理。
        """
        # Act
        error_result = strategy.create_error_result("")

        # Assert
        assert error_result["_error"] == ""
        assert error_result["_strategy"] == "TestStrategy"


class TestBaseDeviceStrategyPriorityHandling:
    """BaseDeviceStrategy 优先级处理测试套件。"""

    def test_priority_property_different_values(self):
        """
        测试不同优先级值的处理。
        Hypothesis: 不同的策略应该能设置不同的优先级值。
        """
        strategies = [
            ConcreteStrategy("High", 10),
            ConcreteStrategy("Medium", 50),
            ConcreteStrategy("Low", 90),
        ]

        assert strategies[0].priority == 10
        assert strategies[1].priority == 50
        assert strategies[2].priority == 90

    def test_priority_sorting(self):
        """
        测试优先级排序逻辑。
        Hypothesis: 策略列表应该能够按优先级正确排序。
        """
        # Arrange
        strategies = [
            ConcreteStrategy("Low", 90),
            ConcreteStrategy("High", 10),
            ConcreteStrategy("Medium", 50),
        ]

        # Act
        sorted_strategies = sorted(strategies, key=lambda s: s.priority)

        # Assert
        assert sorted_strategies[0].get_strategy_name() == "High"
        assert sorted_strategies[1].get_strategy_name() == "Medium"
        assert sorted_strategies[2].get_strategy_name() == "Low"


class TestBaseDeviceStrategyIntegration:
    """BaseDeviceStrategy 集成测试套件。"""

    def test_full_validation_workflow(self, strategy: ConcreteStrategy):
        """
        测试完整的验证工作流。
        Hypothesis: 真实设备数据应该通过完整的验证工作流。
        """
        # Arrange
        device = create_typed_smart_plug().to_dict()
        raw_config = {"name": "Smart Plug Config", "dynamic": False}

        # Act & Assert - 步骤1: 验证设备数据
        assert strategy.validate_device_data(device) is True

        # Act & Assert - 步骤2: 验证原始配置
        assert strategy.validate_raw_config(raw_config) is True

        # Act & Assert - 步骤3: 获取设备类型
        device_type = strategy.get_device_type(device)
        assert device_type == "SL_OL"

        # Act & Assert - 步骤4: 获取设备数据
        device_data = strategy.get_device_data(device)
        assert isinstance(device_data, dict)
        assert "O" in device_data  # 智能插座应该有O口

        # Act & Assert - 步骤5: 检查策略能否处理(这个策略只处理TEST_DEVICE)
        can_handle = strategy.can_handle(device_type, device, raw_config)
        assert can_handle is False  # ConcreteStrategy只处理TEST_DEVICE

    def test_error_handling_workflow(self, strategy: ConcreteStrategy):
        """
        测试错误处理工作流。
        Hypothesis: 无效输入应该通过错误处理流程产生适当的错误结果。
        """
        # Arrange
        invalid_device = None
        invalid_config = "not_a_dict"

        # Act & Assert - 验证无效设备数据
        assert strategy.validate_device_data(invalid_device) is False

        # Act & Assert - 验证无效配置
        assert strategy.validate_raw_config(invalid_config) is False

        # Act & Assert - 创建错误结果
        error_result = strategy.create_error_result("Validation failed")
        assert "_error" in error_result
        assert "_strategy" in error_result
