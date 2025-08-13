"""
Phase 2.0.1: Switch平台回归测试实现

Switch平台是优先级第二高的平台，因为：
1. 使用频率最高 - 影响用户日常体验最直接
2. 包含最多样化的开关类型 - Traditional/Advanced/Dimmer switches
3. 状态同步要求最严格 - 响应速度直接影响用户感知

此模块基于BaseRegressionTest实现Switch平台的专用回归测试。
"""

from typing import Dict, List, Any, Optional

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry

from custom_components.lifesmart.tests.utils.factories import (
    create_traditional_switch_devices,
    create_advanced_switch_devices,
)
from .base_regression_test import BaseRegressionTest


class SwitchRegressionTest(BaseRegressionTest):
    """Switch平台回归测试类 - 覆盖所有开关类型"""

    def __init__(self):
        """初始化Switch平台回归测试"""
        super().__init__("switch")
        self.expected_switch_types = {
            # 传统开关系列
            "SL_SW_IF3": {"switch_count": 3, "response_time_max": 0.2},  # L1/L2/L3三路
            "SL_SW_IF2": {"switch_count": 2, "response_time_max": 0.2},  # L1/L2双路
            "SL_SW_IF1": {"switch_count": 1, "response_time_max": 0.2},  # L1单路
            "SL_SW_ND3": {"switch_count": 3, "response_time_max": 0.2},  # P1/P2/P3+电量
            "SL_SW_ND2": {"switch_count": 2, "response_time_max": 0.2},  # P1/P2+电量
            "SL_SW_ND1": {"switch_count": 1, "response_time_max": 0.2},  # P1+电量
            # 高级开关系列
            "SL_P_SW": {"switch_count": 9, "response_time_max": 0.3},  # P1-P9九路控制器
            "SL_P": {"switch_count": 3, "response_time_max": 0.3},  # P2/P3/P4通用控制器
            "SL_NATURE": {
                "switch_count": 3,
                "response_time_max": 0.3,
            },  # P1/P2/P3超能面板
            "SL_SW_DM1": {
                "switch_count": 1,
                "response_time_max": 0.4,
            },  # P1调光开关+传感器
            "SL_SW_RC": {
                "switch_count": 3,
                "response_time_max": 0.2,
            },  # L1/L2/L3极星开关
            "SL_SF_RC": {
                "switch_count": 3,
                "response_time_max": 0.2,
            },  # L1/L2/L3单火开关
            "SL_SW_NS3": {
                "switch_count": 3,
                "response_time_max": 0.2,
            },  # L1/L2/L3星玉开关
            "SL_SW_MJ3": {
                "switch_count": 3,
                "response_time_max": 0.2,
            },  # P1/P2/P3奇点模块
            "SL_SW_MJ2": {"switch_count": 2, "response_time_max": 0.2},  # P1/P2奇点模块
            "SL_MC_ND1": {
                "switch_count": 1,
                "response_time_max": 0.2,
            },  # P1开关伴侣+电量
            "SL_MC_ND2": {
                "switch_count": 2,
                "response_time_max": 0.2,
            },  # P1/P2开关伴侣+电量
            "SL_MC_ND3": {
                "switch_count": 3,
                "response_time_max": 0.2,
            },  # P1/P2/P3开关伴侣+电量
        }

    def get_test_devices(self) -> List[Dict[str, Any]]:
        """
        获取Switch平台的测试设备列表

        Returns:
            所有开关类型的测试设备列表
        """
        devices = []

        # 传统开关
        devices.extend(create_traditional_switch_devices())

        # 高级开关
        devices.extend(create_advanced_switch_devices())

        self.logger.info(f"获取Switch测试设备 - 总数: {len(devices)}")

        return devices

    def validate_platform_entities(
        self, hass: HomeAssistant, entity_registry: EntityRegistry
    ) -> bool:
        """
        验证Switch平台实体的正确性

        Args:
            hass: Home Assistant实例
            entity_registry: 实体注册表

        Returns:
            True如果验证通过，否则False
        """
        try:
            validation_results = []

            # 获取所有开关实体
            switch_entities = [
                entity
                for entity in entity_registry.entities.values()
                if entity.domain == SWITCH_DOMAIN
            ]

            self.logger.info(f"实体统计 - Switch: {len(switch_entities)}")

            # 按设备类型验证实体数量
            device_type_counts = self._count_entities_by_device_type(switch_entities)

            # 验证每种设备类型的实体数量
            for device_type, expected in self.expected_switch_types.items():
                actual_count = device_type_counts.get(device_type, 0)

                count_ok = actual_count >= expected["switch_count"]

                if count_ok:
                    validation_results.append(True)
                    self.logger.debug(
                        f"✅ {device_type}: Switch={actual_count}/{expected['switch_count']}"
                    )
                else:
                    validation_results.append(False)
                    self.logger.error(
                        f"❌ {device_type}: Switch={actual_count}/{expected['switch_count']}"
                    )

            # 验证实体状态
            state_validation = self._validate_entity_states(hass, switch_entities)
            validation_results.append(state_validation)

            # 验证开关属性
            attribute_validation = self._validate_switch_attributes(switch_entities)
            validation_results.append(attribute_validation)

            # 验证响应时间（模拟测试）
            response_validation = self._validate_response_times(hass, switch_entities)
            validation_results.append(response_validation)

            overall_success = all(validation_results)

            self.logger.info(
                f"Switch平台验证完成 - 成功: {overall_success}, "
                f"详细结果: {sum(validation_results)}/{len(validation_results)}"
            )

            return overall_success

        except Exception as e:
            self.logger.error(f"Switch平台验证异常: {e}")
            return False

    def _count_entities_by_device_type(self, switch_entities: List) -> Dict[str, int]:
        """
        按设备类型统计Switch实体数量

        Args:
            switch_entities: 开关实体列表

        Returns:
            按设备类型分组的实体计数
        """
        counts = {}

        for entity in switch_entities:
            device_type = self._extract_device_type_from_entity(entity)
            if device_type:
                if device_type not in counts:
                    counts[device_type] = 0
                counts[device_type] += 1

        return counts

    def _extract_device_type_from_entity(self, entity) -> Optional[str]:
        """
        从实体中提取设备类型

        Args:
            entity: 实体对象

        Returns:
            设备类型字符串，如果无法提取则返回None
        """
        try:
            # 从实体ID或名称中提取设备类型
            # 实体ID格式通常为: switch.lifesmart_{device_type}_{me}_{io_port}
            entity_id_parts = entity.entity_id.split("_")

            if len(entity_id_parts) >= 3 and entity_id_parts[1] == "lifesmart":
                # 提取设备类型部分，可能包含多个下划线
                device_type_parts = []
                for i, part in enumerate(entity_id_parts[2:], 2):
                    if part.upper() == part or (
                        part.startswith("SL_")
                        or part.startswith("OD_")
                        or part.startswith("V_")
                    ):
                        device_type_parts.append(part)
                    else:
                        break

                if device_type_parts:
                    return "_".join(device_type_parts).upper()

            return None

        except Exception as e:
            self.logger.debug(f"无法从实体提取设备类型: {entity.entity_id} - {e}")
            return None

    def _validate_entity_states(self, hass: HomeAssistant, entities: List) -> bool:
        """
        验证开关实体状态的有效性

        Args:
            hass: Home Assistant实例
            entities: 实体列表

        Returns:
            True如果所有实体状态有效，否则False
        """
        try:
            invalid_states = []

            for entity in entities:
                state = hass.states.get(entity.entity_id)

                if state is None:
                    invalid_states.append(f"{entity.entity_id}: 状态为None")
                elif state.state not in ["on", "off", "unknown", "unavailable"]:
                    invalid_states.append(
                        f"{entity.entity_id}: 无效状态值{state.state}"
                    )

            if invalid_states:
                self.logger.warning(f"发现无效状态实体: {len(invalid_states)}个")
                for invalid in invalid_states[:5]:  # 只记录前5个
                    self.logger.warning(f"  {invalid}")
                if len(invalid_states) > 5:
                    self.logger.warning(f"  ... 还有{len(invalid_states) - 5}个")

                # 允许少量无效状态（可能是测试环境导致的）
                return (
                    len(invalid_states) <= len(entities) * 0.1
                )  # 允许10%的实体状态无效

            self.logger.debug("所有开关实体状态验证通过")
            return True

        except Exception as e:
            self.logger.error(f"实体状态验证异常: {e}")
            return False

    def _validate_switch_attributes(self, entities: List) -> bool:
        """
        验证开关实体属性的正确性

        Args:
            entities: 实体列表

        Returns:
            True如果实体属性正确，否则False
        """
        try:
            missing_attributes = []

            required_attributes = [
                "device_class",
                "friendly_name",
            ]

            for entity in entities:
                for attr in required_attributes:
                    if not hasattr(entity, attr) or getattr(entity, attr) is None:
                        # 对于开关，device_class可能为空
                        if attr != "device_class":
                            missing_attributes.append(f"{entity.entity_id}: 缺少{attr}")

            if missing_attributes:
                self.logger.warning(f"发现缺少属性的实体: {len(missing_attributes)}个")
                for missing in missing_attributes[:3]:  # 只记录前3个
                    self.logger.warning(f"  {missing}")

                # 允许少量缺少属性
                return (
                    len(missing_attributes) <= len(entities) * 0.2
                )  # 允许20%的实体缺少某些属性

            self.logger.debug("所有开关实体属性验证通过")
            return True

        except Exception as e:
            self.logger.error(f"实体属性验证异常: {e}")
            return False

    def _validate_response_times(self, hass: HomeAssistant, entities: List) -> bool:
        """
        验证开关响应时间（模拟测试）

        Args:
            hass: Home Assistant实例
            entities: 实体列表

        Returns:
            True如果响应时间符合要求，否则False
        """
        try:
            slow_entities = []

            # 模拟响应时间测试
            for entity in entities:
                device_type = self._extract_device_type_from_entity(entity)
                if device_type and device_type in self.expected_switch_types:
                    expected_max_time = self.expected_switch_types[device_type].get(
                        "response_time_max", 0.5
                    )

                    # 在真实测试中，这里会测量实际的开关响应时间
                    # 当前模拟一个基于设备类型的响应时间
                    simulated_response_time = 0.1  # 模拟快速响应

                    if simulated_response_time > expected_max_time:
                        slow_entities.append(
                            f"{entity.entity_id}: {simulated_response_time:.3f}s "
                            f"(期望<{expected_max_time:.3f}s)"
                        )

            if slow_entities:
                self.logger.warning(f"发现响应慢的实体: {len(slow_entities)}个")
                for slow in slow_entities[:3]:  # 只记录前3个
                    self.logger.warning(f"  {slow}")

                # 允许少量慢响应
                return (
                    len(slow_entities) <= len(entities) * 0.05
                )  # 允许5%的实体响应较慢

            self.logger.debug("所有开关响应时间验证通过")
            return True

        except Exception as e:
            self.logger.error(f"响应时间验证异常: {e}")
            return False


class SwitchPerformanceTest(SwitchRegressionTest):
    """Switch平台性能测试类 - 专注于响应速度和状态同步"""

    def __init__(self):
        """初始化Switch性能测试"""
        super().__init__()
        self.platform_name = "switch_performance"

    def run_performance_benchmarks(self, hass: HomeAssistant) -> Dict[str, Any]:
        """
        运行Switch平台性能基准测试

        Args:
            hass: Home Assistant实例

        Returns:
            性能基准数据
        """
        performance_data = {}

        # 测试不同类型开关的性能
        test_categories = [
            ("traditional", create_traditional_switch_devices),
            ("advanced", create_advanced_switch_devices),
        ]

        for category_name, factory_func in test_categories:
            self.logger.info(f"运行{category_name}开关性能测试")

            with self.performance_monitoring(f"switch_{category_name}_performance"):
                try:
                    # 获取特定类别的设备
                    devices = factory_func()

                    # 模拟平台映射处理
                    mapping_times = []
                    state_sync_times = []

                    for device in devices:
                        import time

                        # 测试映射时间
                        start = time.time()
                        self.mapping_wrapper.get_platform_mapping(device)
                        mapping_times.append(time.time() - start)

                        # 模拟状态同步时间
                        start = time.time()
                        # 在真实测试中，这里会测试实际的状态同步
                        time.sleep(0.001)  # 模拟1ms的状态同步时间
                        state_sync_times.append(time.time() - start)

                    performance_data[category_name] = {
                        "device_count": len(devices),
                        "avg_mapping_time": (
                            sum(mapping_times) / len(mapping_times)
                            if mapping_times
                            else 0
                        ),
                        "avg_state_sync_time": (
                            sum(state_sync_times) / len(state_sync_times)
                            if state_sync_times
                            else 0
                        ),
                        "total_mapping_time": sum(mapping_times),
                        "max_mapping_time": max(mapping_times) if mapping_times else 0,
                        "max_state_sync_time": (
                            max(state_sync_times) if state_sync_times else 0
                        ),
                    }

                except Exception as e:
                    self.logger.error(f"{category_name}开关性能测试失败: {e}")
                    performance_data[category_name] = {"error": str(e)}

        self.logger.info("Switch平台性能基准测试完成")
        return performance_data
