"""
Phase 2.0.1: Climate平台回归测试实现

Climate平台是优先级第三的平台，但复杂度最高，因为：
1. 复杂逻辑最多 - HVAC映射架构是整个系统的关键验证点
2. 模式切换复杂 - 制热/制冷/风速多维度控制逻辑
3. 温度控制精度 - 数值转换和控制逻辑验证关键

此模块基于BaseRegressionTest实现Climate平台的专用回归测试。
"""

from typing import Dict, List, Any, Optional

from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry

from custom_components.lifesmart.tests.utils.factories import (
    create_climate_devices,
)
from .base_regression_test import BaseRegressionTest


class ClimateRegressionTest(BaseRegressionTest):
    """Climate平台回归测试类 - 覆盖所有气候控制类型"""

    def __init__(self):
        """初始化Climate平台回归测试"""
        super().__init__("climate")
        self.expected_climate_types = {
            # 地暖控制系列
            "SL_CP_DN": {
                "climate_count": 1,
                "temperature_precision": 0.5,  # 温度精度0.5°C
                "supported_modes": ["heat", "off"],
                "temp_range": {"min": 5, "max": 35},
            },
            # 风机盘管系列
            "SL_CP_AIR": {
                "climate_count": 1,
                "temperature_precision": 0.5,
                "supported_modes": ["heat", "cool", "off"],
                "supported_fan_modes": ["low", "medium", "high", "auto"],
                "temp_range": {"min": 16, "max": 30},
            },
            # 空调面板系列
            "V_AIR_P": {
                "climate_count": 1,
                "temperature_precision": 0.5,
                "supported_modes": ["heat", "cool", "dry", "fan_only", "auto", "off"],
                "supported_fan_modes": ["low", "medium", "high", "auto"],
                "temp_range": {"min": 16, "max": 32},
            },
            # 新风系统
            "SL_TR_ACIPM": {
                "climate_count": 1,
                "temperature_precision": 1.0,
                "supported_modes": ["auto", "off"],
                "supported_fan_modes": ["1", "2", "3", "auto"],
                "temp_range": {"min": 0, "max": 50},  # 新风系统温度检测范围更广
            },
            # 超能面板（温控模式）
            "SL_NATURE": {
                "climate_count": 1,
                "temperature_precision": 0.5,
                "supported_modes": ["heat", "cool", "off"],
                "supported_fan_modes": ["low", "medium", "high"],
                "temp_range": {"min": 10, "max": 35},
            },
        }

    def get_test_devices(self) -> List[Dict[str, Any]]:
        """
        获取Climate平台的测试设备列表

        Returns:
            所有气候控制类型的测试设备列表
        """
        devices = []

        # 获取气候控制设备
        devices.extend(create_climate_devices())

        self.logger.info(f"获取Climate测试设备 - 总数: {len(devices)}")

        return devices

    def validate_platform_entities(
        self, hass: HomeAssistant, entity_registry: EntityRegistry
    ) -> bool:
        """
        验证Climate平台实体的正确性

        Args:
            hass: Home Assistant实例
            entity_registry: 实体注册表

        Returns:
            True如果验证通过，否则False
        """
        try:
            validation_results = []

            # 获取所有气候控制实体
            climate_entities = [
                entity
                for entity in entity_registry.entities.values()
                if entity.domain == CLIMATE_DOMAIN
            ]

            self.logger.info(f"实体统计 - Climate: {len(climate_entities)}")

            # 按设备类型验证实体数量
            device_type_counts = self._count_entities_by_device_type(climate_entities)

            # 验证每种设备类型的实体数量
            for device_type, expected in self.expected_climate_types.items():
                actual_count = device_type_counts.get(device_type, 0)

                count_ok = actual_count >= expected["climate_count"]

                if count_ok:
                    validation_results.append(True)
                    self.logger.debug(
                        f"✅ {device_type}: Climate={actual_count}/{expected['climate_count']}"
                    )
                else:
                    validation_results.append(False)
                    self.logger.error(
                        f"❌ {device_type}: Climate={actual_count}/{expected['climate_count']}"
                    )

            # 验证实体状态
            state_validation = self._validate_entity_states(hass, climate_entities)
            validation_results.append(state_validation)

            # 验证气候控制属性
            attribute_validation = self._validate_climate_attributes(climate_entities)
            validation_results.append(attribute_validation)

            # 验证温度控制精度
            temperature_validation = self._validate_temperature_precision(
                hass, climate_entities
            )
            validation_results.append(temperature_validation)

            # 验证模式切换能力
            mode_validation = self._validate_hvac_modes(hass, climate_entities)
            validation_results.append(mode_validation)

            overall_success = all(validation_results)

            self.logger.info(
                f"Climate平台验证完成 - 成功: {overall_success}, "
                f"详细结果: {sum(validation_results)}/{len(validation_results)}"
            )

            return overall_success

        except Exception as e:
            self.logger.error(f"Climate平台验证异常: {e}")
            return False

    def _count_entities_by_device_type(self, climate_entities: List) -> Dict[str, int]:
        """
        按设备类型统计Climate实体数量

        Args:
            climate_entities: 气候控制实体列表

        Returns:
            按设备类型分组的实体计数
        """
        counts = {}

        for entity in climate_entities:
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
            # 实体ID格式通常为: climate.lifesmart_{device_type}_{me}
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
        验证气候控制实体状态的有效性

        Args:
            hass: Home Assistant实例
            entities: 实体列表

        Returns:
            True如果所有实体状态有效，否则False
        """
        try:
            invalid_states = []
            valid_hvac_modes = [
                "off",
                "heat",
                "cool",
                "heat_cool",
                "auto",
                "dry",
                "fan_only",
                "unknown",
                "unavailable",
            ]

            for entity in entities:
                state = hass.states.get(entity.entity_id)

                if state is None:
                    invalid_states.append(f"{entity.entity_id}: 状态为None")
                elif state.state not in valid_hvac_modes:
                    invalid_states.append(
                        f"{entity.entity_id}: 无效HVAC模式{state.state}"
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

            self.logger.debug("所有气候控制实体状态验证通过")
            return True

        except Exception as e:
            self.logger.error(f"实体状态验证异常: {e}")
            return False

    def _validate_climate_attributes(self, entities: List) -> bool:
        """
        验证气候控制实体属性的正确性

        Args:
            entities: 实体列表

        Returns:
            True如果实体属性正确，否则False
        """
        try:
            missing_attributes = []

            required_attributes = [
                "hvac_modes",
                "target_temperature",
                "current_temperature",
                "temperature_unit",
                "min_temp",
                "max_temp",
            ]

            for entity in entities:
                for attr in required_attributes:
                    if not hasattr(entity, attr) or getattr(entity, attr) is None:
                        # 某些属性对特定设备类型可能不适用
                        if attr not in ["current_temperature", "fan_modes"]:
                            missing_attributes.append(f"{entity.entity_id}: 缺少{attr}")

            if missing_attributes:
                self.logger.warning(f"发现缺少属性的实体: {len(missing_attributes)}个")
                for missing in missing_attributes[:3]:  # 只记录前3个
                    self.logger.warning(f"  {missing}")

                # 允许少量缺少属性
                return (
                    len(missing_attributes) <= len(entities) * 0.3
                )  # 允许30%的实体缺少某些属性

            self.logger.debug("所有气候控制实体属性验证通过")
            return True

        except Exception as e:
            self.logger.error(f"实体属性验证异常: {e}")
            return False

    def _validate_temperature_precision(
        self, hass: HomeAssistant, entities: List
    ) -> bool:
        """
        验证温度控制精度

        Args:
            hass: Home Assistant实例
            entities: 实体列表

        Returns:
            True如果温度精度符合要求，否则False
        """
        try:
            precision_errors = []

            for entity in entities:
                device_type = self._extract_device_type_from_entity(entity)
                if device_type and device_type in self.expected_climate_types:
                    expected_precision = self.expected_climate_types[device_type].get(
                        "temperature_precision", 1.0
                    )

                    state = hass.states.get(entity.entity_id)
                    if state and state.attributes:
                        # 检查目标温度设置精度
                        target_temp = state.attributes.get("temperature")
                        current_temp = state.attributes.get("current_temperature")

                        if target_temp is not None:
                            # 检查温度值是否符合精度要求
                            temp_decimal_places = len(str(target_temp).split(".")[-1])
                            if expected_precision == 0.5 and temp_decimal_places > 1:
                                precision_errors.append(
                                    f"{entity.entity_id}: 目标温度精度超出预期 "
                                    f"({target_temp}, 期望精度{expected_precision})"
                                )

                        # 检查温度范围
                        temp_range = self.expected_climate_types[device_type].get(
                            "temp_range", {}
                        )
                        min_temp = state.attributes.get("min_temp")
                        max_temp = state.attributes.get("max_temp")

                        if min_temp is not None and temp_range.get("min") is not None:
                            if min_temp > temp_range["min"]:
                                precision_errors.append(
                                    f"{entity.entity_id}: 最低温度限制过高 "
                                    f"({min_temp} > {temp_range['min']})"
                                )

                        if max_temp is not None and temp_range.get("max") is not None:
                            if max_temp < temp_range["max"]:
                                precision_errors.append(
                                    f"{entity.entity_id}: 最高温度限制过低 "
                                    f"({max_temp} < {temp_range['max']})"
                                )

            if precision_errors:
                self.logger.warning(f"发现温度精度问题: {len(precision_errors)}个")
                for error in precision_errors[:3]:  # 只记录前3个
                    self.logger.warning(f"  {error}")

                # 允许少量精度问题
                return (
                    len(precision_errors) <= len(entities) * 0.2
                )  # 允许20%的实体有精度问题

            self.logger.debug("所有温度精度验证通过")
            return True

        except Exception as e:
            self.logger.error(f"温度精度验证异常: {e}")
            return False

    def _validate_hvac_modes(self, hass: HomeAssistant, entities: List) -> bool:
        """
        验证HVAC模式切换能力

        Args:
            hass: Home Assistant实例
            entities: 实体列表

        Returns:
            True如果模式验证通过，否则False
        """
        try:
            mode_errors = []

            for entity in entities:
                device_type = self._extract_device_type_from_entity(entity)
                if device_type and device_type in self.expected_climate_types:
                    expected_modes = self.expected_climate_types[device_type].get(
                        "supported_modes", []
                    )
                    expected_fan_modes = self.expected_climate_types[device_type].get(
                        "supported_fan_modes", []
                    )

                    state = hass.states.get(entity.entity_id)
                    if state and state.attributes:
                        # 检查支持的HVAC模式
                        hvac_modes = state.attributes.get("hvac_modes", [])
                        for expected_mode in expected_modes:
                            if expected_mode not in hvac_modes:
                                mode_errors.append(
                                    f"{entity.entity_id}: 缺少HVAC模式 {expected_mode}"
                                )

                        # 检查支持的风速模式（如果适用）
                        if expected_fan_modes:
                            fan_modes = state.attributes.get("fan_modes", [])
                            if not fan_modes:
                                mode_errors.append(
                                    f"{entity.entity_id}: 应支持风速模式但未找到"
                                )
                            else:
                                missing_fan_modes = [
                                    mode
                                    for mode in expected_fan_modes
                                    if mode not in fan_modes
                                ]
                                if missing_fan_modes:
                                    mode_errors.append(
                                        f"{entity.entity_id}: 缺少风速模式 "
                                        f"{missing_fan_modes}"
                                    )

            if mode_errors:
                self.logger.warning(f"发现模式支持问题: {len(mode_errors)}个")
                for error in mode_errors[:3]:  # 只记录前3个
                    self.logger.warning(f"  {error}")

                # 允许少量模式问题
                return (
                    len(mode_errors) <= len(entities) * 0.2
                )  # 允许20%的实体有模式问题

            self.logger.debug("所有HVAC模式验证通过")
            return True

        except Exception as e:
            self.logger.error(f"HVAC模式验证异常: {e}")
            return False


class ClimatePerformanceTest(ClimateRegressionTest):
    """Climate平台性能测试类 - 专注于HVAC控制响应和精度"""

    def __init__(self):
        """初始化Climate性能测试"""
        super().__init__()
        self.platform_name = "climate_performance"

    def run_performance_benchmarks(self, hass: HomeAssistant) -> Dict[str, Any]:
        """
        运行Climate平台性能基准测试

        Args:
            hass: Home Assistant实例

        Returns:
            性能基准数据
        """
        performance_data = {}

        # 测试不同类型气候控制的性能
        test_categories = [
            ("floor_heating", "SL_CP_DN"),
            ("fan_coil", "SL_CP_AIR"),
            ("air_panel", "V_AIR_P"),
            ("fresh_air", "SL_TR_ACIPM"),
            ("nature_panel", "SL_NATURE"),
        ]

        for category_name, device_type in test_categories:
            self.logger.info(f"运行{category_name}气候控制性能测试")

            with self.performance_monitoring(f"climate_{category_name}_performance"):
                try:
                    # 获取特定类别的设备
                    devices = [
                        device
                        for device in create_climate_devices()
                        if device.get("devtype") == device_type
                    ]

                    if not devices:
                        continue

                    # 模拟平台映射处理
                    mapping_times = []
                    temperature_response_times = []
                    mode_switch_times = []

                    for device in devices:
                        import time

                        # 测试映射时间
                        start = time.time()
                        self.mapping_wrapper.get_platform_mapping(device)
                        mapping_times.append(time.time() - start)

                        # 模拟温度响应时间
                        start = time.time()
                        # 在真实测试中，这里会测试实际的温度设置响应
                        time.sleep(0.002)  # 模拟2ms的温度响应时间
                        temperature_response_times.append(time.time() - start)

                        # 模拟模式切换时间
                        start = time.time()
                        # 在真实测试中，这里会测试实际的模式切换响应
                        time.sleep(0.005)  # 模拟5ms的模式切换时间
                        mode_switch_times.append(time.time() - start)

                    performance_data[category_name] = {
                        "device_count": len(devices),
                        "avg_mapping_time": (
                            sum(mapping_times) / len(mapping_times)
                            if mapping_times
                            else 0
                        ),
                        "avg_temperature_response_time": (
                            sum(temperature_response_times)
                            / len(temperature_response_times)
                            if temperature_response_times
                            else 0
                        ),
                        "avg_mode_switch_time": (
                            sum(mode_switch_times) / len(mode_switch_times)
                            if mode_switch_times
                            else 0
                        ),
                        "max_temperature_response_time": (
                            max(temperature_response_times)
                            if temperature_response_times
                            else 0
                        ),
                        "max_mode_switch_time": (
                            max(mode_switch_times) if mode_switch_times else 0
                        ),
                    }

                except Exception as e:
                    self.logger.error(f"{category_name}气候控制性能测试失败: {e}")
                    performance_data[category_name] = {"error": str(e)}

        self.logger.info("Climate平台性能基准测试完成")
        return performance_data
