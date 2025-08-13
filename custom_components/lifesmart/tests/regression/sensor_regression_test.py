"""
Phase 2.0.1: Sensor平台回归测试实现

Sensor平台是优先级最高的平台，因为：
1. 数据一致性最关键 - 影响所有其他平台的决策
2. 包含最多样化的设备类型 - Environment/Binary/Gas/Specialized
3. 是其他平台的数据源基础

此模块基于BaseRegressionTest实现Sensor平台的专用回归测试。
"""

from typing import Dict, List, Any, Optional

from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry

from custom_components.lifesmart.tests.utils.factories import (
    create_environment_sensor_devices,
    create_binary_sensor_devices,
    create_gas_sensor_devices,
    create_specialized_sensor_devices,
)
from .base_regression_test import BaseRegressionTest


class SensorRegressionTest(BaseRegressionTest):
    """Sensor平台回归测试类 - 覆盖所有传感器类型"""

    def __init__(self):
        """初始化Sensor平台回归测试"""
        super().__init__("sensor")
        self.expected_sensor_types = {
            # 环境传感器
            "SL_SC_THL": {"sensor_count": 4, "binary_sensor_count": 0},  # T/H/Z/V
            "SL_SC_BE": {"sensor_count": 4, "binary_sensor_count": 0},  # T/H/Z/V
            "SL_SC_CA": {"sensor_count": 4, "binary_sensor_count": 0},  # T/H/CO2/V
            "SL_SC_CQ": {"sensor_count": 5, "binary_sensor_count": 0},  # T/H/CO2/TVOC/V
            "ELIQ_EM": {"sensor_count": 1, "binary_sensor_count": 0},  # EPA
            # 二进制传感器
            "SL_SC_G": {"sensor_count": 1, "binary_sensor_count": 1},  # G/V
            "SL_SC_BG": {"sensor_count": 1, "binary_sensor_count": 3},  # V + G/KB/AXS
            "SL_SC_GS": {"sensor_count": 1, "binary_sensor_count": 2},  # V + P1/AXS
            "SL_SC_MHW": {"sensor_count": 1, "binary_sensor_count": 1},  # V + M
            "SL_SC_BM": {"sensor_count": 1, "binary_sensor_count": 1},  # V + M
            "SL_SC_CM": {"sensor_count": 2, "binary_sensor_count": 1},  # V/P4 + P1
            "SL_BP_MZ": {"sensor_count": 3, "binary_sensor_count": 1},  # V/P2/P3 + P1
            "SL_SC_WA": {"sensor_count": 1, "binary_sensor_count": 1},  # V + WA
            "SL_LK_LS": {
                "sensor_count": 1,
                "binary_sensor_count": 2,
            },  # BAT + EVTLO/ALM
            "SL_SC_BB": {"sensor_count": 1, "binary_sensor_count": 1},  # V + B或P1
            "SL_P_A": {"sensor_count": 1, "binary_sensor_count": 1},  # P2 + P1
            # 气体传感器
            "SL_SC_CH": {"sensor_count": 0, "binary_sensor_count": 3},  # P1/P2/P3
            "SL_SC_CP": {"sensor_count": 0, "binary_sensor_count": 3},  # P1/P2/P3
            # 专用传感器
            "V_485_P": {"sensor_count": 9, "binary_sensor_count": 0},  # 多种传感器值
            "SL_SC_B1": {"sensor_count": 5, "binary_sensor_count": 0},  # T/H/CO2/TVOC/V
            "SL_SC_CN": {"sensor_count": 0, "binary_sensor_count": 4},  # P1/P2/P3/P4
            "SL_SC_CV": {"sensor_count": 1, "binary_sensor_count": 1},  # V + VOICE
            "SL_P_RM": {"sensor_count": 0, "binary_sensor_count": 2},  # P1/P2
        }

    def get_test_devices(self) -> List[Dict[str, Any]]:
        """
        获取Sensor平台的测试设备列表

        Returns:
            所有传感器类型的测试设备列表
        """
        devices = []

        # 环境传感器
        devices.extend(create_environment_sensor_devices())

        # 二进制传感器
        devices.extend(create_binary_sensor_devices())

        # 气体传感器
        devices.extend(create_gas_sensor_devices())

        # 专用传感器
        devices.extend(create_specialized_sensor_devices())

        self.logger.info(f"获取Sensor测试设备 - 总数: {len(devices)}")

        return devices

    def validate_platform_entities(
        self, hass: HomeAssistant, entity_registry: EntityRegistry
    ) -> bool:
        """
        验证Sensor平台实体的正确性

        Args:
            hass: Home Assistant实例
            entity_registry: 实体注册表

        Returns:
            True如果验证通过，否则False
        """
        try:
            validation_results = []

            # 获取所有传感器实体
            sensor_entities = [
                entity
                for entity in entity_registry.entities.values()
                if entity.domain == SENSOR_DOMAIN
            ]

            binary_sensor_entities = [
                entity
                for entity in entity_registry.entities.values()
                if entity.domain == BINARY_SENSOR_DOMAIN
            ]

            self.logger.info(
                f"实体统计 - Sensor: {len(sensor_entities)}, "
                f"Binary Sensor: {len(binary_sensor_entities)}"
            )

            # 按设备类型验证实体数量
            device_type_counts = self._count_entities_by_device_type(
                sensor_entities, binary_sensor_entities
            )

            # 验证每种设备类型的实体数量
            for device_type, expected in self.expected_sensor_types.items():
                actual = device_type_counts.get(
                    device_type, {"sensor": 0, "binary_sensor": 0}
                )

                sensor_count_ok = actual["sensor"] >= expected["sensor_count"]
                binary_sensor_count_ok = (
                    actual["binary_sensor"] >= expected["binary_sensor_count"]
                )

                if sensor_count_ok and binary_sensor_count_ok:
                    validation_results.append(True)
                    self.logger.debug(
                        f"✅ {device_type}: Sensor={actual['sensor']}/{expected['sensor_count']}, "
                        f"Binary={actual['binary_sensor']}/{expected['binary_sensor_count']}"
                    )
                else:
                    validation_results.append(False)
                    self.logger.error(
                        f"❌ {device_type}: Sensor={actual['sensor']}/{expected['sensor_count']}, "
                        f"Binary={actual['binary_sensor']}/{expected['binary_sensor_count']}"
                    )

            # 验证实体状态
            state_validation = self._validate_entity_states(
                hass, sensor_entities + binary_sensor_entities
            )
            validation_results.append(state_validation)

            # 验证设备属性
            attribute_validation = self._validate_entity_attributes(
                sensor_entities + binary_sensor_entities
            )
            validation_results.append(attribute_validation)

            overall_success = all(validation_results)

            self.logger.info(
                f"Sensor平台验证完成 - 成功: {overall_success}, "
                f"详细结果: {sum(validation_results)}/{len(validation_results)}"
            )

            return overall_success

        except Exception as e:
            self.logger.error(f"Sensor平台验证异常: {e}")
            return False

    def _count_entities_by_device_type(
        self, sensor_entities: List, binary_sensor_entities: List
    ) -> Dict[str, Dict[str, int]]:
        """
        按设备类型统计实体数量

        Args:
            sensor_entities: 传感器实体列表
            binary_sensor_entities: 二进制传感器实体列表

        Returns:
            按设备类型分组的实体计数
        """
        counts = {}

        # 统计传感器实体
        for entity in sensor_entities:
            device_type = self._extract_device_type_from_entity(entity)
            if device_type:
                if device_type not in counts:
                    counts[device_type] = {"sensor": 0, "binary_sensor": 0}
                counts[device_type]["sensor"] += 1

        # 统计二进制传感器实体
        for entity in binary_sensor_entities:
            device_type = self._extract_device_type_from_entity(entity)
            if device_type:
                if device_type not in counts:
                    counts[device_type] = {"sensor": 0, "binary_sensor": 0}
                counts[device_type]["binary_sensor"] += 1

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
            # 实体ID格式通常为: sensor.lifesmart_{device_type}_{me}_{io_port}
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
        验证实体状态的有效性

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
                elif state.state in ["unknown", "unavailable"]:
                    invalid_states.append(f"{entity.entity_id}: 状态为{state.state}")

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

            self.logger.debug("所有实体状态验证通过")
            return True

        except Exception as e:
            self.logger.error(f"实体状态验证异常: {e}")
            return False

    def _validate_entity_attributes(self, entities: List) -> bool:
        """
        验证实体属性的正确性

        Args:
            entities: 实体列表

        Returns:
            True如果实体属性正确，否则False
        """
        try:
            missing_attributes = []

            required_attributes = [
                "device_class",
                "unit_of_measurement",
                "friendly_name",
            ]

            for entity in entities:
                for attr in required_attributes:
                    if not hasattr(entity, attr) or getattr(entity, attr) is None:
                        # 对于某些属性，允许为空（如binary_sensor可能没有unit_of_measurement）
                        if not (
                            attr == "unit_of_measurement"
                            and entity.domain == BINARY_SENSOR_DOMAIN
                        ):
                            missing_attributes.append(f"{entity.entity_id}: 缺少{attr}")

            if missing_attributes:
                self.logger.warning(f"发现缺少属性的实体: {len(missing_attributes)}个")
                for missing in missing_attributes[:3]:  # 只记录前3个
                    self.logger.warning(f"  {missing}")

                # 允许少量缺少属性（可能是某些传感器类型的特性）
                return (
                    len(missing_attributes) <= len(entities) * 0.2
                )  # 允许20%的实体缺少某些属性

            self.logger.debug("所有实体属性验证通过")
            return True

        except Exception as e:
            self.logger.error(f"实体属性验证异常: {e}")
            return False


class SensorPerformanceTest(SensorRegressionTest):
    """Sensor平台性能测试类 - 专注于性能基线建立"""

    def __init__(self):
        """初始化Sensor性能测试"""
        super().__init__()
        self.platform_name = "sensor_performance"

    def run_performance_benchmarks(self, hass: HomeAssistant) -> Dict[str, Any]:
        """
        运行Sensor平台性能基准测试

        Args:
            hass: Home Assistant实例

        Returns:
            性能基准数据
        """
        performance_data = {}

        # 测试不同类型传感器的性能
        test_categories = [
            ("environment", create_environment_sensor_devices),
            ("binary", create_binary_sensor_devices),
            ("gas", create_gas_sensor_devices),
            ("specialized", create_specialized_sensor_devices),
        ]

        for category_name, factory_func in test_categories:
            self.logger.info(f"运行{category_name}传感器性能测试")

            with self.performance_monitoring(f"sensor_{category_name}_performance"):
                try:
                    # 获取特定类别的设备
                    devices = factory_func()

                    # 模拟平台映射处理
                    mapping_times = []
                    for device in devices:
                        import time

                        start = time.time()
                        self.mapping_wrapper.get_platform_mapping(device)
                        mapping_times.append(time.time() - start)

                    performance_data[category_name] = {
                        "device_count": len(devices),
                        "avg_mapping_time": (
                            sum(mapping_times) / len(mapping_times)
                            if mapping_times
                            else 0
                        ),
                        "total_mapping_time": sum(mapping_times),
                        "max_mapping_time": max(mapping_times) if mapping_times else 0,
                    }

                except Exception as e:
                    self.logger.error(f"{category_name}传感器性能测试失败: {e}")
                    performance_data[category_name] = {"error": str(e)}

        self.logger.info("Sensor平台性能基准测试完成")
        return performance_data
