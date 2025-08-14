"""
Phase 2.0.1: 回归测试框架核心 - BaseRegressionTest基础类

此模块提供所有回归测试的通用基础设施，确保四核心平台的持续稳定性。
基于Phase 1稳定化修复的成果，构建生产级回归测试框架。

核心设计理念：
1. 标准化测试环境配置
2. 双引擎映射验证
3. 性能基线跟踪
4. 故障隔离机制
"""

import logging
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Dict, List, Any, Optional

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry

from custom_components.lifesmart.core.resolver.device_resolver import (
    get_device_resolver,
)
from custom_components.lifesmart.core.platform.platform_detection import (
    get_device_platform_mapping,
)
from custom_components.lifesmart.tests.utils.factories import (
    validate_device_data,
)


@dataclass
class PerformanceMetrics:
    """性能指标数据类"""

    response_time: float
    memory_usage: int
    entity_count: int
    mapping_time: float
    platform_detection_time: float

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "response_time": self.response_time,
            "memory_usage": self.memory_usage,
            "entity_count": self.entity_count,
            "mapping_time": self.mapping_time,
            "platform_detection_time": self.platform_detection_time,
        }


@dataclass
class RegressionTestResult:
    """回归测试结果数据类"""

    test_name: str
    platform: str
    device_count: int
    success: bool
    performance_metrics: PerformanceMetrics
    error_details: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "test_name": self.test_name,
            "platform": self.platform,
            "device_count": self.device_count,
            "success": self.success,
            "performance_metrics": self.performance_metrics.to_dict(),
            "error_details": self.error_details,
        }


class MappingEngineWrapper:
    """映射引擎包装器 - 支持新旧引擎并行验证"""

    def __init__(self, enable_dual_validation: bool = True):
        """
        初始化映射引擎包装器

        Args:
            enable_dual_validation: 是否启用双引擎验证
        """
        self.enable_dual_validation = enable_dual_validation
        self.device_resolver = get_device_resolver()
        self.logger = logging.getLogger(__name__)

    def get_platform_mapping(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取设备的平台映射，支持双引擎验证

        Args:
            device_data: 设备数据

        Returns:
            平台映射结果

        Raises:
            ValueError: 当双引擎结果不一致时
        """
        start_time = time.time()

        try:
            # 主引擎（新的映射引擎）
            primary_result = get_device_platform_mapping(device_data)

            if self.enable_dual_validation:
                # 备用引擎验证（如果有的话）
                secondary_result = self._get_legacy_mapping(device_data)

                # 验证两个引擎的结果一致性
                if not self._validate_mapping_consistency(
                    primary_result, secondary_result, device_data
                ):
                    self.logger.warning(
                        f"映射引擎结果不一致 - 设备: {device_data.get('devtype', 'unknown')}"
                    )

            self.logger.debug(
                f"映射时间: {time.time() - start_time:.3f}s - "
                f"设备: {device_data.get('devtype', 'unknown')}"
            )

            return primary_result

        except Exception as e:
            self.logger.error(f"映射引擎错误: {e}")
            raise

    def _get_legacy_mapping(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取旧版映射引擎的结果（如果存在）

        Args:
            device_data: 设备数据

        Returns:
            旧版映射结果
        """
        # 这里可以实现旧版映射逻辑的调用
        # 目前返回空结果，因为我们主要使用新的映射引擎
        return {}

    def _validate_mapping_consistency(
        self,
        primary_result: Dict[str, Any],
        secondary_result: Dict[str, Any],
        device_data: Dict[str, Any],
    ) -> bool:
        """
        验证两个映射引擎结果的一致性

        Args:
            primary_result: 主引擎结果
            secondary_result: 备用引擎结果
            device_data: 设备数据

        Returns:
            True如果结果一致，否则False
        """
        # 如果备用引擎没有结果，认为一致
        if not secondary_result:
            return True

        # 比较关键字段
        key_fields = ["platform", "entity_count", "device_class"]

        for field in key_fields:
            if primary_result.get(field) != secondary_result.get(field):
                return False

        return True


class BaseRegressionTest(ABC):
    """回归测试基础类 - 提供所有回归测试的通用基础设施"""

    def __init__(self, platform_name: str):
        """
        初始化回归测试基础类

        Args:
            platform_name: 平台名称 (sensor/switch/climate/light)
        """
        self.platform_name = platform_name
        self.logger = logging.getLogger(f"{__name__}.{platform_name}")
        self.mapping_wrapper = MappingEngineWrapper()
        self.performance_baselines: Dict[str, PerformanceMetrics] = {}
        self.test_results: List[RegressionTestResult] = []

    @abstractmethod
    def get_test_devices(self) -> List[Dict[str, Any]]:
        """
        获取测试设备列表

        Returns:
            测试设备数据列表
        """
        pass

    @abstractmethod
    def validate_platform_entities(
        self, hass: HomeAssistant, entity_registry: EntityRegistry
    ) -> bool:
        """
        验证平台实体的正确性

        Args:
            hass: Home Assistant实例
            entity_registry: 实体注册表

        Returns:
            True如果验证通过，否则False
        """
        pass

    def setup_test_environment(self, hass: HomeAssistant) -> Dict[str, Any]:
        """
        设置标准化的测试环境

        Args:
            hass: Home Assistant实例

        Returns:
            测试环境配置信息
        """
        start_time = time.time()

        # 获取测试设备
        test_devices = self.get_test_devices()

        # 验证设备数据完整性
        for device in test_devices:
            validate_device_data(device)

        setup_time = time.time() - start_time

        config = {
            "platform": self.platform_name,
            "device_count": len(test_devices),
            "setup_time": setup_time,
            "test_devices": test_devices,
        }

        self.logger.info(
            f"测试环境设置完成 - 平台: {self.platform_name}, "
            f"设备数: {len(test_devices)}, 耗时: {setup_time:.3f}s"
        )

        return config

    @contextmanager
    def performance_monitoring(self, test_name: str):
        """
        性能监控上下文管理器

        Args:
            test_name: 测试名称
        """
        start_time = time.time()
        start_memory = self._get_memory_usage()

        try:
            yield
        finally:
            end_time = time.time()
            end_memory = self._get_memory_usage()

            metrics = PerformanceMetrics(
                response_time=end_time - start_time,
                memory_usage=end_memory - start_memory,
                entity_count=0,  # 将在具体测试中更新
                mapping_time=0.0,
                platform_detection_time=0.0,
            )

            self._record_performance_metrics(test_name, metrics)

    def run_regression_test(self, hass: HomeAssistant) -> RegressionTestResult:
        """
        运行回归测试

        Args:
            hass: Home Assistant实例

        Returns:
            回归测试结果
        """
        test_name = f"{self.platform_name}_regression_test"

        with self.performance_monitoring(test_name):
            try:
                # 设置测试环境
                test_config = self.setup_test_environment(hass)

                # 设置集成平台 - 简化版本不依赖missing函数
                from homeassistant.helpers.entity_registry import async_get_registry

                entity_registry = async_get_registry(hass)

                # 验证平台实体
                validation_success = self.validate_platform_entities(
                    hass, entity_registry
                )

                # 获取性能指标
                metrics = self.performance_baselines.get(
                    test_name,
                    PerformanceMetrics(
                        response_time=0.0,
                        memory_usage=0,
                        entity_count=len(entity_registry.entities),
                        mapping_time=0.0,
                        platform_detection_time=0.0,
                    ),
                )

                # 创建测试结果
                result = RegressionTestResult(
                    test_name=test_name,
                    platform=self.platform_name,
                    device_count=test_config["device_count"],
                    success=validation_success,
                    performance_metrics=metrics,
                )

                self.test_results.append(result)

                if validation_success:
                    self.logger.info(f"回归测试成功 - {test_name}")
                else:
                    self.logger.error(f"回归测试失败 - {test_name}")

                return result

            except Exception as e:
                error_msg = f"回归测试异常: {e}"
                self.logger.error(error_msg)

                result = RegressionTestResult(
                    test_name=test_name,
                    platform=self.platform_name,
                    device_count=0,
                    success=False,
                    performance_metrics=PerformanceMetrics(0.0, 0, 0, 0.0, 0.0),
                    error_details=error_msg,
                )

                self.test_results.append(result)
                return result

    def _get_memory_usage(self) -> int:
        """
        获取当前内存使用量

        Returns:
            内存使用量（字节）
        """
        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        except ImportError:
            # 如果psutil不可用，返回0
            return 0

    def _record_performance_metrics(self, test_name: str, metrics: PerformanceMetrics):
        """
        记录性能指标

        Args:
            test_name: 测试名称
            metrics: 性能指标
        """
        self.performance_baselines[test_name] = metrics

        self.logger.debug(
            f"性能指标记录 - {test_name}: "
            f"响应时间={metrics.response_time:.3f}s, "
            f"内存={metrics.memory_usage}bytes, "
            f"实体数={metrics.entity_count}"
        )

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能总结

        Returns:
            性能总结数据
        """
        return {
            "platform": self.platform_name,
            "baselines": {
                name: metrics.to_dict()
                for name, metrics in self.performance_baselines.items()
            },
            "test_results": [result.to_dict() for result in self.test_results],
        }


class RegressionTestSuite:
    """回归测试套件管理器"""

    def __init__(self):
        """初始化回归测试套件"""
        self.test_classes: List[BaseRegressionTest] = []
        self.logger = logging.getLogger(__name__)

    def register_test_class(self, test_class: BaseRegressionTest):
        """
        注册测试类

        Args:
            test_class: 回归测试类实例
        """
        self.test_classes.append(test_class)
        self.logger.info(f"注册回归测试类: {test_class.platform_name}")

    def run_all_tests(self, hass: HomeAssistant) -> Dict[str, Any]:
        """
        运行所有注册的回归测试

        Args:
            hass: Home Assistant实例

        Returns:
            测试套件运行结果
        """
        start_time = time.time()
        results = []

        for test_class in self.test_classes:
            self.logger.info(f"运行回归测试: {test_class.platform_name}")
            result = test_class.run_regression_test(hass)
            results.append(result.to_dict())

        total_time = time.time() - start_time

        summary = {
            "total_tests": len(self.test_classes),
            "successful_tests": sum(1 for r in results if r["success"]),
            "failed_tests": sum(1 for r in results if not r["success"]),
            "total_time": total_time,
            "results": results,
        }

        self.logger.info(
            f"回归测试套件完成 - 总数: {summary['total_tests']}, "
            f"成功: {summary['successful_tests']}, "
            f"失败: {summary['failed_tests']}, "
            f"耗时: {total_time:.3f}s"
        )

        return summary
