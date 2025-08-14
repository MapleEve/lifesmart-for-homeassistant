"""
DeviceStrategyFactory 单元测试 - Phase 2 核心组件

测试策略工厂的核心功能：
- 根据优先级正确选择策略
- 在策略的 can_handle 方法失败时能够优雅降级
- 当没有策略匹配时返回正确的错误
- 策略执行和错误处理机制

基于 @MapleEve 的 Phase 2.5 重构设计
"""

from unittest.mock import MagicMock, patch

import pytest

from custom_components.lifesmart.core.strategies.strategy_factory import (
    DeviceStrategyFactory,
)
from custom_components.lifesmart.core.strategies.base_strategy import BaseDeviceStrategy

# 从强类型工厂导入测试数据
from ...utils.typed_factories import (
    create_typed_smart_plug,
    create_typed_thermostat_panel,
)


@pytest.fixture
def mock_strategies():
    """提供一组带有不同优先级的模拟策略。"""
    strategy1 = MagicMock(spec=BaseDeviceStrategy)
    strategy1.priority = 10
    strategy1.get_strategy_name.return_value = "Strategy10"
    strategy1.can_handle.return_value = False

    strategy2 = MagicMock(spec=BaseDeviceStrategy)
    strategy2.priority = 20
    strategy2.get_strategy_name.return_value = "Strategy20"
    strategy2.can_handle.return_value = False

    strategy3 = MagicMock(spec=BaseDeviceStrategy)
    strategy3.priority = 30
    strategy3.get_strategy_name.return_value = "Strategy30"
    strategy3.can_handle.return_value = False

    return [strategy1, strategy2, strategy3]


@pytest.fixture
def factory(mock_strategies) -> DeviceStrategyFactory:
    """提供一个带有模拟策略的 DeviceStrategyFactory 实例。"""
    # 使用 patch 来替换初始化时的策略列表
    with patch.object(DeviceStrategyFactory, "__init__", lambda s: None):
        f = DeviceStrategyFactory()
        f.strategies = mock_strategies
        f.strategies.sort(key=lambda s: s.priority)
        return f


class TestDeviceStrategyFactoryCore:
    """DeviceStrategyFactory 核心功能测试套件。"""

    def test_strategy_selection_by_priority(
        self, factory: DeviceStrategyFactory, mock_strategies
    ):
        """
        测试策略是否根据优先级被正确选择。
        Hypothesis: 工厂应按优先级顺序检查策略，并选择第一个 can_handle 返回 True 的策略。
        """
        # Arrange
        mock_strategies[1].can_handle.return_value = True  # Strategy20 应该被选中
        mock_strategies[0].can_handle.return_value = False
        mock_strategies[2].can_handle.return_value = True  # 这个不应该被检查到

        device_data = {"devtype": "TEST_DEVICE"}
        raw_config = {"name": "Test Config"}

        # Act
        selected_strategy = factory.get_strategy("TEST_DEVICE", device_data, raw_config)

        # Assert
        assert selected_strategy is not None
        assert selected_strategy.get_strategy_name() == "Strategy20"
        # 验证优先级更高的策略被检查过
        mock_strategies[0].can_handle.assert_called_once()
        # 验证选中的策略被检查过
        mock_strategies[1].can_handle.assert_called_once()
        # 验证优先级更低的策略没有被检查
        mock_strategies[2].can_handle.assert_not_called()

    def test_first_strategy_selected(
        self, factory: DeviceStrategyFactory, mock_strategies
    ):
        """
        测试第一个匹配的策略被选中。
        Hypothesis: 优先级最高(数字最小)且can_handle返回True的策略应被选中。
        """
        # Arrange
        mock_strategies[0].can_handle.return_value = True  # Strategy10 应该被选中
        mock_strategies[1].can_handle.return_value = True  # 不应该被检查到
        mock_strategies[2].can_handle.return_value = True  # 不应该被检查到

        device_data = {"devtype": "TEST_DEVICE"}
        raw_config = {"name": "Test Config"}

        # Act
        selected_strategy = factory.get_strategy("TEST_DEVICE", device_data, raw_config)

        # Assert
        assert selected_strategy is not None
        assert selected_strategy.get_strategy_name() == "Strategy10"
        # 只有第一个策略被检查
        mock_strategies[0].can_handle.assert_called_once()
        mock_strategies[1].can_handle.assert_not_called()
        mock_strategies[2].can_handle.assert_not_called()

    def test_no_strategy_found(self, factory: DeviceStrategyFactory, mock_strategies):
        """
        测试当没有策略能处理设备时的行为。
        Hypothesis: 如果所有策略的 can_handle 都返回 False，get_strategy 应返回 None。
        """
        # Arrange - 所有策略的can_handle都返回False（在fixture中已设置）
        device_data = {"devtype": "UNKNOWN_DEVICE"}
        raw_config = {}

        # Act
        selected_strategy = factory.get_strategy(
            "UNKNOWN_DEVICE", device_data, raw_config
        )

        # Assert
        assert selected_strategy is None
        # 验证所有策略都被检查过
        for strategy in mock_strategies:
            strategy.can_handle.assert_called_once()

    def test_strategy_can_handle_raises_exception(
        self, factory: DeviceStrategyFactory, mock_strategies
    ):
        """
        测试当一个策略的 can_handle 方法抛出异常时的容错能力。
        Hypothesis: 工厂应捕获异常，记录警告，并继续尝试下一个策略。
        """
        # Arrange
        mock_strategies[0].can_handle.side_effect = ValueError("Test Exception")
        mock_strategies[1].can_handle.return_value = True  # 第二个策略应被选中

        device_data = {"devtype": "TEST_DEVICE"}
        raw_config = {}

        # Act
        selected_strategy = factory.get_strategy("TEST_DEVICE", device_data, raw_config)

        # Assert
        assert selected_strategy is not None
        assert selected_strategy.get_strategy_name() == "Strategy20"
        mock_strategies[0].can_handle.assert_called_once()
        mock_strategies[1].can_handle.assert_called_once()
        mock_strategies[2].can_handle.assert_not_called()

    def test_all_strategies_raise_exceptions(
        self, factory: DeviceStrategyFactory, mock_strategies
    ):
        """
        测试当所有策略都抛出异常时的处理。
        Hypothesis: 应该返回None，并且所有策略都被尝试过。
        """
        # Arrange
        for strategy in mock_strategies:
            strategy.can_handle.side_effect = RuntimeError("Strategy failed")

        device_data = {"devtype": "TEST_DEVICE"}
        raw_config = {}

        # Act
        selected_strategy = factory.get_strategy("TEST_DEVICE", device_data, raw_config)

        # Assert
        assert selected_strategy is None
        for strategy in mock_strategies:
            strategy.can_handle.assert_called_once()


class TestDeviceStrategyFactoryMapping:
    """DeviceStrategyFactory 设备映射测试套件。"""

    def test_resolve_device_mapping_success(
        self, factory: DeviceStrategyFactory, mock_strategies
    ):
        """
        测试成功的设备映射解析。
        Hypothesis: 当策略被成功选择并执行时，应返回策略的解析结果。
        """
        # Arrange
        expected_mapping = {
            "switch": {"P1": {"description": "Test Switch"}},
            "name": "Test Mapping",
        }
        mock_strategies[0].can_handle.return_value = True
        mock_strategies[0].resolve_device_mapping.return_value = expected_mapping

        device_data = create_typed_smart_plug().to_dict()
        raw_config = {"name": "Test Config"}

        # Act
        result = factory.resolve_device_mapping("SL_OL", device_data, raw_config)

        # Assert
        assert result == expected_mapping
        mock_strategies[0].resolve_device_mapping.assert_called_once_with(
            device_data, raw_config
        )

    def test_resolve_device_mapping_no_strategy(
        self, factory: DeviceStrategyFactory, mock_strategies
    ):
        """
        测试当没有策略匹配时，resolve_device_mapping 的返回值。
        Hypothesis: 应返回一个标准的错误字典。
        """
        # Arrange - 所有策略都返回False（在fixture中默认设置）
        device_data = {"devtype": "UNKNOWN_DEVICE"}
        raw_config = {}

        # Act
        result = factory.resolve_device_mapping(
            "UNKNOWN_DEVICE", device_data, raw_config
        )

        # Assert
        assert "_error" in result
        assert "No suitable strategy found" in result["_error"]
        assert result["_factory"] == "DeviceStrategyFactory"

    def test_resolve_device_mapping_strategy_execution_error(
        self, factory: DeviceStrategyFactory, mock_strategies
    ):
        """
        测试当选中的策略在解析时抛出异常。
        Hypothesis: resolve_device_mapping 应捕获异常并返回一个错误字典。
        """
        # Arrange
        mock_strategies[1].can_handle.return_value = True
        mock_strategies[1].resolve_device_mapping.side_effect = RuntimeError(
            "Resolve Failed"
        )

        device_data = {"devtype": "TEST_DEVICE"}
        raw_config = {}

        # Act
        result = factory.resolve_device_mapping("TEST_DEVICE", device_data, raw_config)

        # Assert
        assert "_error" in result
        assert "Strategy Strategy20 failed: Resolve Failed" in result["_error"]
        assert result["_factory"] == "DeviceStrategyFactory"
        assert result["_strategy"] == "Strategy20"

    def test_resolve_device_mapping_with_real_device_data(
        self, factory: DeviceStrategyFactory, mock_strategies
    ):
        """
        测试使用真实设备数据的映射解析。
        Hypothesis: 真实的强类型设备数据应能正确传递给策略。
        """
        # Arrange
        expected_mapping = {
            "climate": {
                "P1": {"description": "Power"},
                "P4": {"description": "Current Temperature"},
            }
        }
        mock_strategies[2].can_handle.return_value = True  # 使用第三个策略
        mock_strategies[2].resolve_device_mapping.return_value = expected_mapping

        device_data = create_typed_thermostat_panel().to_dict()
        raw_config = {"name": "Thermostat Config", "dynamic": True}

        # Act
        result = factory.resolve_device_mapping("SL_NATURE", device_data, raw_config)

        # Assert
        assert result == expected_mapping
        # 验证传递给策略的参数
        args, kwargs = mock_strategies[2].resolve_device_mapping.call_args
        assert args[0] == device_data  # device参数
        assert args[1] == raw_config  # raw_config参数


class TestDeviceStrategyFactoryUtilities:
    """DeviceStrategyFactory 辅助功能测试套件。"""

    def test_get_available_strategies(
        self, factory: DeviceStrategyFactory, mock_strategies
    ):
        """
        测试获取可用策略列表。
        Hypothesis: 应返回所有策略的名称列表。
        """
        # Act
        strategies = factory.get_available_strategies()

        # Assert
        expected_names = ["Strategy10", "Strategy20", "Strategy30"]
        assert strategies == expected_names

    def test_get_strategy_by_name_found(
        self, factory: DeviceStrategyFactory, mock_strategies
    ):
        """
        测试根据名称获取策略 - 成功情况。
        Hypothesis: 存在的策略名称应返回对应的策略实例。
        """
        # Act
        strategy = factory.get_strategy_by_name("Strategy20")

        # Assert
        assert strategy is not None
        assert strategy == mock_strategies[1]
        assert strategy.get_strategy_name() == "Strategy20"

    def test_get_strategy_by_name_not_found(self, factory: DeviceStrategyFactory):
        """
        测试根据名称获取策略 - 未找到情况。
        Hypothesis: 不存在的策略名称应返回None。
        """
        # Act
        strategy = factory.get_strategy_by_name("NonexistentStrategy")

        # Assert
        assert strategy is None

    def test_get_factory_stats(self, factory: DeviceStrategyFactory, mock_strategies):
        """
        测试获取工厂统计信息。
        Hypothesis: 应返回包含策略数量和详细信息的统计字典。
        """
        # Act
        stats = factory.get_factory_stats()

        # Assert
        assert stats["total_strategies"] == 3
        assert len(stats["strategies"]) == 3

        # 验证策略信息
        strategy_info = stats["strategies"]
        assert strategy_info[0]["name"] == "Strategy10"
        assert strategy_info[0]["priority"] == 10
        assert strategy_info[1]["name"] == "Strategy20"
        assert strategy_info[1]["priority"] == 20
        assert strategy_info[2]["name"] == "Strategy30"
        assert strategy_info[2]["priority"] == 30


class TestDeviceStrategyFactoryIntegration:
    """DeviceStrategyFactory 集成测试套件。"""

    def test_priority_sorting_during_initialization(self):
        """
        测试初始化时策略的优先级排序。
        Hypothesis: 策略应该按优先级从小到大排序。
        """
        # Arrange
        strategy_high = MagicMock(spec=BaseDeviceStrategy)
        strategy_high.priority = 90
        strategy_high.get_strategy_name.return_value = "HighPriority"

        strategy_low = MagicMock(spec=BaseDeviceStrategy)
        strategy_low.priority = 10
        strategy_low.get_strategy_name.return_value = "LowPriority"

        strategy_mid = MagicMock(spec=BaseDeviceStrategy)
        strategy_mid.priority = 50
        strategy_mid.get_strategy_name.return_value = "MidPriority"

        # Act
        with patch.object(DeviceStrategyFactory, "__init__", lambda s: None):
            factory = DeviceStrategyFactory()
            factory.strategies = [strategy_high, strategy_low, strategy_mid]
            factory.strategies.sort(key=lambda s: s.priority)

        # Assert
        assert factory.strategies[0] == strategy_low  # 优先级10
        assert factory.strategies[1] == strategy_mid  # 优先级50
        assert factory.strategies[2] == strategy_high  # 优先级90

    def test_complex_strategy_selection_scenario(
        self, factory: DeviceStrategyFactory, mock_strategies
    ):
        """
        测试复杂的策略选择场景。
        Hypothesis: 在多种条件下策略选择应该稳定可靠。
        """
        # Arrange
        # 第一个策略抛异常，第二个策略返回False，第三个策略返回True
        mock_strategies[0].can_handle.side_effect = ImportError("Import failed")
        mock_strategies[1].can_handle.return_value = False
        mock_strategies[2].can_handle.return_value = True

        expected_mapping = {"test": "mapping"}
        mock_strategies[2].resolve_device_mapping.return_value = expected_mapping

        device_data = {"devtype": "COMPLEX_DEVICE", "data": {"test": "value"}}
        raw_config = {"dynamic": True, "special_handling": True}

        # Act
        selected_strategy = factory.get_strategy(
            "COMPLEX_DEVICE", device_data, raw_config
        )
        mapping_result = factory.resolve_device_mapping(
            "COMPLEX_DEVICE", device_data, raw_config
        )

        # Assert
        assert selected_strategy is not None
        assert selected_strategy.get_strategy_name() == "Strategy30"
        assert mapping_result == expected_mapping

        # 验证策略调用顺序
        mock_strategies[0].can_handle.assert_called_once()
        mock_strategies[1].can_handle.assert_called_once()
        mock_strategies[2].can_handle.assert_called_once()
        mock_strategies[2].resolve_device_mapping.assert_called_once()

    def test_empty_strategies_list(self):
        """
        测试空策略列表的处理。
        Hypothesis: 空策略列表应该优雅地处理，返回None。
        """
        # Arrange
        with patch.object(DeviceStrategyFactory, "__init__", lambda s: None):
            factory = DeviceStrategyFactory()
            factory.strategies = []

        device_data = {"devtype": "TEST_DEVICE"}
        raw_config = {}

        # Act
        selected_strategy = factory.get_strategy("TEST_DEVICE", device_data, raw_config)
        mapping_result = factory.resolve_device_mapping(
            "TEST_DEVICE", device_data, raw_config
        )

        # Assert
        assert selected_strategy is None
        assert "_error" in mapping_result
        assert "No suitable strategy found" in mapping_result["_error"]
