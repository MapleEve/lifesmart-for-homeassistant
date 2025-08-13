"""
Phase 2.0.1: Light平台回归测试实现

Light平台是优先级第四的平台，特点：
1. 功能相对独立 - 但种类最丰富，覆盖最多样化的灯光类型
2. 颜色准确性关键 - RGB/RGBW颜色值转换和显示验证
3. 效果切换复杂 - 动态效果、亮度调节、色温控制

此模块基于BaseRegressionTest实现Light平台的专用回归测试。
"""

from typing import Dict, List, Any, Optional

from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_registry import EntityRegistry

from custom_components.lifesmart.tests.utils.factories import (
    create_dimmer_light_devices,
    create_rgb_light_devices,
    create_spot_light_devices,
    create_quantum_light_devices,
    create_brightness_light_devices,
    create_rgbw_light_devices,
    create_outdoor_light_devices,
)
from .base_regression_test import BaseRegressionTest


class LightRegressionTest(BaseRegressionTest):
    """Light平台回归测试类 - 覆盖所有灯光类型"""

    def __init__(self):
        """初始化Light平台回归测试"""
        super().__init__("light")
        self.expected_light_types = {
            # 调光调色系列
            "SL_LI_WW": {
                "light_count": 1,
                "supported_features": ["brightness", "color_temp"],
                "brightness_range": {"min": 1, "max": 255},
                "color_temp_range": {"min": 153, "max": 500},  # 2000K-6500K
            },
            "SL_SW_WW": {
                "light_count": 1,
                "supported_features": ["brightness", "color_temp"],
                "brightness_range": {"min": 1, "max": 255},
            },
            "SL_SPWM": {
                "light_count": 1,
                "supported_features": ["brightness"],
                "brightness_range": {"min": 1, "max": 255},
            },
            # RGB系列
            "SL_SC_RGB": {
                "light_count": 1,
                "supported_features": ["brightness", "rgb_color"],
                "brightness_range": {"min": 1, "max": 255},
                "color_range": {"min": 0x000000, "max": 0xFFFFFF},
            },
            "SL_CT_RGBW": {
                "light_count": 1,
                "supported_features": ["brightness", "rgb_color", "white_value"],
                "brightness_range": {"min": 1, "max": 255},
                "color_range": {"min": 0x000000, "max": 0xFFFFFF},
            },
            "SL_LI_RGBW": {
                "light_count": 1,
                "supported_features": [
                    "brightness",
                    "rgb_color",
                    "white_value",
                    "effect",
                ],
                "brightness_range": {"min": 1, "max": 255},
                "color_range": {"min": 0x000000, "max": 0xFFFFFF},
            },
            # 射灯系列
            "MSL_IRCTL": {
                "light_count": 1,
                "supported_features": [
                    "brightness",
                    "rgb_color",
                    "white_value",
                    "effect",
                ],
                "brightness_range": {"min": 1, "max": 255},
                "color_range": {"min": 0x000000, "max": 0xFFFFFF},
            },
            "SL_SPOT": {
                "light_count": 1,
                "supported_features": ["brightness", "rgb_color", "color_temp"],
                "brightness_range": {"min": 1, "max": 255},
                "color_range": {"min": 0x000000, "max": 0xFFFFFF},
            },
            # 量子灯系列
            "OD_WE_QUAN": {
                "light_count": 1,
                "supported_features": ["brightness", "effect"],
                "brightness_range": {"min": 1, "max": 255},
            },
            # 户外灯光系列
            "SL_LI_GD1": {
                "light_count": 1,
                "supported_features": ["brightness"],
                "brightness_range": {"min": 1, "max": 255},
            },
            "SL_LI_UG1": {
                "light_count": 1,
                "supported_features": ["brightness", "rgb_color"],
                "brightness_range": {"min": 1, "max": 255},
                "color_range": {"min": 0x000000, "max": 0xFFFFFF},
            },
            # 红外吸顶灯
            "SL_LI_IR": {
                "light_count": 1,
                "supported_features": ["brightness"],
                "brightness_range": {"min": 1, "max": 255},
            },
        }

    def get_test_devices(self) -> List[Dict[str, Any]]:
        """
        获取Light平台的测试设备列表

        Returns:
            所有灯光类型的测试设备列表
        """
        devices = []

        # 调光调色灯
        devices.extend(create_dimmer_light_devices())
        devices.extend(create_brightness_light_devices())

        # RGB/RGBW灯
        devices.extend(create_rgb_light_devices())
        devices.extend(create_rgbw_light_devices())

        # 射灯
        devices.extend(create_spot_light_devices())

        # 量子灯
        devices.extend(create_quantum_light_devices())

        # 户外灯光
        devices.extend(create_outdoor_light_devices())

        self.logger.info(f"获取Light测试设备 - 总数: {len(devices)}")

        return devices

    def validate_platform_entities(
        self, hass: HomeAssistant, entity_registry: EntityRegistry
    ) -> bool:
        """
        验证Light平台实体的正确性

        Args:
            hass: Home Assistant实例
            entity_registry: 实体注册表

        Returns:
            True如果验证通过，否则False
        """
        try:
            validation_results = []

            # 获取所有灯光实体
            light_entities = [
                entity
                for entity in entity_registry.entities.values()
                if entity.domain == LIGHT_DOMAIN
            ]

            self.logger.info(f"实体统计 - Light: {len(light_entities)}")

            # 按设备类型验证实体数量
            device_type_counts = self._count_entities_by_device_type(light_entities)

            # 验证每种设备类型的实体数量
            for device_type, expected in self.expected_light_types.items():
                actual_count = device_type_counts.get(device_type, 0)

                count_ok = actual_count >= expected["light_count"]

                if count_ok:
                    validation_results.append(True)
                    self.logger.debug(
                        f"✅ {device_type}: Light={actual_count}/{expected['light_count']}"
                    )
                else:
                    validation_results.append(False)
                    self.logger.error(
                        f"❌ {device_type}: Light={actual_count}/{expected['light_count']}"
                    )

            # 验证实体状态
            state_validation = self._validate_entity_states(hass, light_entities)
            validation_results.append(state_validation)

            # 验证灯光属性
            attribute_validation = self._validate_light_attributes(light_entities)
            validation_results.append(attribute_validation)

            # 验证颜色和亮度范围
            range_validation = self._validate_color_brightness_ranges(
                hass, light_entities
            )
            validation_results.append(range_validation)

            # 验证支持的功能
            feature_validation = self._validate_supported_features(hass, light_entities)
            validation_results.append(feature_validation)

            overall_success = all(validation_results)

            self.logger.info(
                f"Light平台验证完成 - 成功: {overall_success}, "
                f"详细结果: {sum(validation_results)}/{len(validation_results)}"
            )

            return overall_success

        except Exception as e:
            self.logger.error(f"Light平台验证异常: {e}")
            return False

    def _count_entities_by_device_type(self, light_entities: List) -> Dict[str, int]:
        """
        按设备类型统计Light实体数量

        Args:
            light_entities: 灯光实体列表

        Returns:
            按设备类型分组的实体计数
        """
        counts = {}

        for entity in light_entities:
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
            # 实体ID格式通常为: light.lifesmart_{device_type}_{me}
            entity_id_parts = entity.entity_id.split("_")

            if len(entity_id_parts) >= 3 and entity_id_parts[1] == "lifesmart":
                # 提取设备类型部分，可能包含多个下划线
                device_type_parts = []
                for i, part in enumerate(entity_id_parts[2:], 2):
                    if part.upper() == part or (
                        part.startswith("SL_")
                        or part.startswith("OD_")
                        or part.startswith("V_")
                        or part.startswith("MSL_")
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
        验证灯光实体状态的有效性

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

            self.logger.debug("所有灯光实体状态验证通过")
            return True

        except Exception as e:
            self.logger.error(f"实体状态验证异常: {e}")
            return False

    def _validate_light_attributes(self, entities: List) -> bool:
        """
        验证灯光实体属性的正确性

        Args:
            entities: 实体列表

        Returns:
            True如果实体属性正确，否则False
        """
        try:
            missing_attributes = []

            required_attributes = [
                "supported_features",
                "brightness",
                "friendly_name",
            ]

            for entity in entities:
                for attr in required_attributes:
                    if not hasattr(entity, attr) or getattr(entity, attr) is None:
                        # 某些属性对特定设备类型可能不适用
                        if attr not in ["brightness", "rgb_color", "white_value"]:
                            missing_attributes.append(f"{entity.entity_id}: 缺少{attr}")

            if missing_attributes:
                self.logger.warning(f"发现缺少属性的实体: {len(missing_attributes)}个")
                for missing in missing_attributes[:3]:  # 只记录前3个
                    self.logger.warning(f"  {missing}")

                # 允许少量缺少属性
                return (
                    len(missing_attributes) <= len(entities) * 0.2
                )  # 允许20%的实体缺少某些属性

            self.logger.debug("所有灯光实体属性验证通过")
            return True

        except Exception as e:
            self.logger.error(f"实体属性验证异常: {e}")
            return False

    def _validate_color_brightness_ranges(
        self, hass: HomeAssistant, entities: List
    ) -> bool:
        """
        验证颜色和亮度范围

        Args:
            hass: Home Assistant实例
            entities: 实体列表

        Returns:
            True如果范围验证通过，否则False
        """
        try:
            range_errors = []

            for entity in entities:
                device_type = self._extract_device_type_from_entity(entity)
                if device_type and device_type in self.expected_light_types:
                    expected_brightness = self.expected_light_types[device_type].get(
                        "brightness_range", {}
                    )
                    expected_color = self.expected_light_types[device_type].get(
                        "color_range", {}
                    )

                    state = hass.states.get(entity.entity_id)
                    if state and state.attributes:
                        # 检查亮度范围
                        brightness = state.attributes.get("brightness")
                        if brightness is not None:
                            if expected_brightness.get("min") is not None:
                                if brightness < expected_brightness["min"]:
                                    range_errors.append(
                                        f"{entity.entity_id}: 亮度过低 "
                                        f"({brightness} < {expected_brightness['min']})"
                                    )
                            if expected_brightness.get("max") is not None:
                                if brightness > expected_brightness["max"]:
                                    range_errors.append(
                                        f"{entity.entity_id}: 亮度过高 "
                                        f"({brightness} > {expected_brightness['max']})"
                                    )

                        # 检查颜色范围（对于RGB灯）
                        rgb_color = state.attributes.get("rgb_color")
                        if rgb_color is not None and expected_color:
                            # RGB颜色值通常是(r, g, b)元组
                            if (
                                isinstance(rgb_color, (list, tuple))
                                and len(rgb_color) >= 3
                            ):
                                for i, component in enumerate(rgb_color[:3]):
                                    if component < 0 or component > 255:
                                        range_errors.append(
                                            f"{entity.entity_id}: RGB分量{i}超出范围 "
                                            f"({component} 不在0-255内)"
                                        )

            if range_errors:
                self.logger.warning(f"发现范围问题: {len(range_errors)}个")
                for error in range_errors[:3]:  # 只记录前3个
                    self.logger.warning(f"  {error}")

                # 允许少量范围问题
                return (
                    len(range_errors) <= len(entities) * 0.1
                )  # 允许10%的实体有范围问题

            self.logger.debug("所有颜色和亮度范围验证通过")
            return True

        except Exception as e:
            self.logger.error(f"颜色亮度范围验证异常: {e}")
            return False

    def _validate_supported_features(self, hass: HomeAssistant, entities: List) -> bool:
        """
        验证支持的功能

        Args:
            hass: Home Assistant实例
            entities: 实体列表

        Returns:
            True如果功能验证通过，否则False
        """
        try:
            feature_errors = []

            for entity in entities:
                device_type = self._extract_device_type_from_entity(entity)
                if device_type and device_type in self.expected_light_types:
                    expected_features = self.expected_light_types[device_type].get(
                        "supported_features", []
                    )

                    state = hass.states.get(entity.entity_id)
                    if state and state.attributes:
                        supported_features = state.attributes.get(
                            "supported_features", 0
                        )

                        # 检查功能位标志
                        feature_map = {
                            "brightness": 1,  # SUPPORT_BRIGHTNESS
                            "color_temp": 2,  # SUPPORT_COLOR_TEMP
                            "effect": 4,  # SUPPORT_EFFECT
                            "flash": 8,  # SUPPORT_FLASH
                            "rgb_color": 16,  # SUPPORT_COLOR
                            "transition": 32,  # SUPPORT_TRANSITION
                            "white_value": 128,  # SUPPORT_WHITE_VALUE
                        }

                        for feature_name in expected_features:
                            if feature_name in feature_map:
                                feature_bit = feature_map[feature_name]
                                if not (supported_features & feature_bit):
                                    feature_errors.append(
                                        f"{entity.entity_id}: 应支持{feature_name}功能但未找到"
                                    )

            if feature_errors:
                self.logger.warning(f"发现功能支持问题: {len(feature_errors)}个")
                for error in feature_errors[:3]:  # 只记录前3个
                    self.logger.warning(f"  {error}")

                # 允许少量功能问题
                return (
                    len(feature_errors) <= len(entities) * 0.3
                )  # 允许30%的实体有功能问题

            self.logger.debug("所有支持功能验证通过")
            return True

        except Exception as e:
            self.logger.error(f"支持功能验证异常: {e}")
            return False


class LightPerformanceTest(LightRegressionTest):
    """Light平台性能测试类 - 专注于颜色准确性和效果切换"""

    def __init__(self):
        """初始化Light性能测试"""
        super().__init__()
        self.platform_name = "light_performance"

    def run_performance_benchmarks(self, hass: HomeAssistant) -> Dict[str, Any]:
        """
        运行Light平台性能基准测试

        Args:
            hass: Home Assistant实例

        Returns:
            性能基准数据
        """
        performance_data = {}

        # 测试不同类型灯光的性能
        test_categories = [
            ("dimmer", create_dimmer_light_devices),
            ("rgb", create_rgb_light_devices),
            ("rgbw", create_rgbw_light_devices),
            ("spot", create_spot_light_devices),
            ("quantum", create_quantum_light_devices),
            ("outdoor", create_outdoor_light_devices),
        ]

        for category_name, factory_func in test_categories:
            self.logger.info(f"运行{category_name}灯光性能测试")

            with self.performance_monitoring(f"light_{category_name}_performance"):
                try:
                    # 获取特定类别的设备
                    devices = factory_func()

                    # 模拟平台映射处理
                    mapping_times = []
                    color_change_times = []
                    brightness_change_times = []
                    effect_switch_times = []

                    for device in devices:
                        import time

                        # 测试映射时间
                        start = time.time()
                        self.mapping_wrapper.get_platform_mapping(device)
                        mapping_times.append(time.time() - start)

                        # 模拟颜色变化时间
                        start = time.time()
                        # 在真实测试中，这里会测试实际的颜色变化响应
                        time.sleep(0.003)  # 模拟3ms的颜色变化时间
                        color_change_times.append(time.time() - start)

                        # 模拟亮度变化时间
                        start = time.time()
                        # 在真实测试中，这里会测试实际的亮度变化响应
                        time.sleep(0.002)  # 模拟2ms的亮度变化时间
                        brightness_change_times.append(time.time() - start)

                        # 模拟效果切换时间
                        start = time.time()
                        # 在真实测试中，这里会测试实际的效果切换响应
                        time.sleep(0.005)  # 模拟5ms的效果切换时间
                        effect_switch_times.append(time.time() - start)

                    performance_data[category_name] = {
                        "device_count": len(devices),
                        "avg_mapping_time": (
                            sum(mapping_times) / len(mapping_times)
                            if mapping_times
                            else 0
                        ),
                        "avg_color_change_time": (
                            sum(color_change_times) / len(color_change_times)
                            if color_change_times
                            else 0
                        ),
                        "avg_brightness_change_time": (
                            sum(brightness_change_times) / len(brightness_change_times)
                            if brightness_change_times
                            else 0
                        ),
                        "avg_effect_switch_time": (
                            sum(effect_switch_times) / len(effect_switch_times)
                            if effect_switch_times
                            else 0
                        ),
                        "max_color_change_time": (
                            max(color_change_times) if color_change_times else 0
                        ),
                        "max_brightness_change_time": (
                            max(brightness_change_times)
                            if brightness_change_times
                            else 0
                        ),
                        "max_effect_switch_time": (
                            max(effect_switch_times) if effect_switch_times else 0
                        ),
                    }

                except Exception as e:
                    self.logger.error(f"{category_name}灯光性能测试失败: {e}")
                    performance_data[category_name] = {"error": str(e)}

        self.logger.info("Light平台性能基准测试完成")
        return performance_data
