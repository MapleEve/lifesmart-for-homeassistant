"""
ExtendedStaticConfigPreprocessor单元测试
验证Legacy处理逻辑修复后的功能完整性
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from custom_components.lifesmart.core.config.extended_static_config_preprocessor import (
    ExtendedStaticConfigPreprocessor,
    SPECIAL_DEVICE_FEATURES,
    COVER_POSITIONING_MAP,
    VERSIONED_DEVICE_CONFIG,
)


class TestExtendedStaticConfigPreprocessor:
    """ExtendedStaticConfigPreprocessor测试类"""

    @pytest.fixture
    def sample_legacy_device_data(self) -> Dict[str, Any]:
        """Legacy格式的示例设备数据"""
        return {
            "SL_NATURE": {
                "name": "超能温控面板",
                "dynamic": True,
                "switch_mode": {
                    "condition": "P5&0xFF==1",
                    "io": ["P1", "P2", "P3"],
                    "sensor_io": ["P4", "P5"],
                },
                "climate_mode": {
                    "condition": "P5&0xFF in [3,6]",
                    "climate": {
                        "P1": {
                            "description": "开关",
                            "rw": "RW",
                            "data_type": "binary_switch",
                        },
                        "P4": {
                            "description": "T当前温度",
                            "rw": "R",
                            "data_type": "temperature",
                        },
                    },
                },
            },
            "SL_OL": {
                "name": "单路开关",
                "versioned": True,
                "switch": {
                    "P1": {
                        "description": "开关控制",
                        "rw": "RW",
                        "data_type": "binary_switch",
                    }
                },
            },
            "SL_DOOYA": {
                "name": "杜亚窗帘",
                "cover": {
                    "P1": {
                        "description": "开启",
                        "rw": "RW",
                        "data_type": "binary_switch",
                    },
                    "P2": {
                        "description": "关闭",
                        "rw": "RW",
                        "data_type": "binary_switch",
                    },
                },
            },
        }

    @pytest.fixture
    def sample_device_centric_data(self) -> Dict[str, Any]:
        """Device-Centric格式的示例设备数据"""
        return {
            "TEST_DEVICE_NEW": {
                "name": "测试新格式设备",
                "category": "switch",
                "_generation": 2,
                "climate_config": {
                    "modes": ["heat", "cool"],
                    "temperature_range": {"min": 16, "max": 30},
                },
            }
        }

    @pytest.fixture
    def preprocessor(self, sample_legacy_device_data):
        """创建预处理器实例"""
        return ExtendedStaticConfigPreprocessor(sample_legacy_device_data)

    def test_constants_exist(self):
        """测试常量数据是否正确定义"""
        # 测试SPECIAL_DEVICE_FEATURES
        assert isinstance(SPECIAL_DEVICE_FEATURES, dict)
        assert "SL_NATURE" in SPECIAL_DEVICE_FEATURES
        assert "SL_DOOYA" in SPECIAL_DEVICE_FEATURES
        assert "mode_switch_field" in SPECIAL_DEVICE_FEATURES["SL_NATURE"]

        # 测试COVER_POSITIONING_MAP
        assert isinstance(COVER_POSITIONING_MAP, dict)
        assert "SL_DOOYA" in COVER_POSITIONING_MAP
        assert COVER_POSITIONING_MAP["SL_DOOYA"] is True

        # 测试VERSIONED_DEVICE_CONFIG
        assert isinstance(VERSIONED_DEVICE_CONFIG, dict)
        assert "SL_LI_WW" in VERSIONED_DEVICE_CONFIG

    def test_init(self, sample_legacy_device_data):
        """测试初始化"""
        preprocessor = ExtendedStaticConfigPreprocessor(sample_legacy_device_data)

        assert preprocessor.raw_data == sample_legacy_device_data
        assert isinstance(preprocessor.static_configs, dict)
        assert isinstance(preprocessor.preprocessing_stats, dict)
        assert hasattr(preprocessor, "_SPECIAL_DEVICE_FEATURES")
        assert hasattr(preprocessor, "_COVER_POSITIONING_MAP")
        assert hasattr(preprocessor, "_VERSIONED_DEVICE_CONFIG")

    def test_detect_config_format_legacy(self, preprocessor):
        """测试Legacy格式检测"""
        # Legacy格式应该被正确检测
        config_format = preprocessor.config_format
        assert config_format in ["legacy", "mixed"]

    def test_detect_config_format_device_centric(self, sample_device_centric_data):
        """测试Device-Centric格式检测"""
        preprocessor = ExtendedStaticConfigPreprocessor(sample_device_centric_data)
        assert preprocessor.config_format in ["device_centric", "mixed"]

    def test_process_legacy_device_basic(self, preprocessor):
        """测试基本Legacy设备处理"""
        device_type = "SL_OL"
        raw_config = preprocessor.raw_data[device_type]

        result = preprocessor._process_legacy_device(device_type, raw_config)

        assert isinstance(result, dict)
        assert "name" in result
        assert "_features" in result
        assert "platforms" in result
        assert result["name"] == "单路开关"

    def test_process_legacy_device_dynamic(self, preprocessor):
        """测试动态Legacy设备处理"""
        device_type = "SL_NATURE"
        raw_config = preprocessor.raw_data[device_type]

        result = preprocessor._process_legacy_device(device_type, raw_config)

        assert isinstance(result, dict)
        assert result["_features"]["is_dynamic"] is True
        assert "_mode_configs" in result
        assert isinstance(result["_mode_configs"], dict)

    def test_extract_legacy_features(self, preprocessor):
        """测试Legacy特性提取"""
        device_type = "SL_NATURE"
        raw_config = preprocessor.raw_data[device_type]

        features = preprocessor._extract_legacy_features(device_type, raw_config)

        assert isinstance(features, dict)
        assert features["is_dynamic"] is True
        assert features["generation"] == 1
        assert "default_mode" in features  # 来自SPECIAL_DEVICE_FEATURES

    def test_process_legacy_platforms(self, preprocessor):
        """测试Legacy平台处理"""
        raw_config = {"switch": {"P1": {"description": "test"}}}

        platforms = preprocessor._process_legacy_platforms(raw_config)

        assert isinstance(platforms, dict)
        assert "switch" in platforms
        assert platforms["switch"]["P1"]["description"] == "test"

    def test_process_legacy_dynamic_modes(self, preprocessor):
        """测试Legacy动态模式处理"""
        raw_config = preprocessor.raw_data["SL_NATURE"]

        mode_configs = preprocessor._process_legacy_dynamic_modes(raw_config)

        assert isinstance(mode_configs, dict)
        assert "switch_mode" in mode_configs
        assert "climate_mode" in mode_configs

        # 验证条件转换
        switch_mode = mode_configs["switch_mode"]
        assert "condition" in switch_mode
        assert "platforms" in switch_mode

    def test_detect_positioning_capability(self, preprocessor):
        """测试定位能力检测"""
        assert preprocessor._detect_positioning_capability("SL_DOOYA") is True
        assert preprocessor._detect_positioning_capability("SL_SW_WIN") is False
        assert preprocessor._detect_positioning_capability("UNKNOWN") is False

    def test_get_cover_type(self, preprocessor):
        """测试窗帘类型获取"""
        assert preprocessor._get_cover_type("SL_DOOYA") == "positional"
        assert preprocessor._get_cover_type("SL_SW_WIN") == "non_positional"
        assert preprocessor._get_cover_type("UNKNOWN") is None

    def test_extract_static_condition(self, preprocessor):
        """测试静态条件提取"""
        mode_config = {"condition": "P5&0xFF==1"}

        condition = preprocessor._extract_static_condition("test_mode", mode_config)

        assert isinstance(condition, dict)
        assert condition["type"] == "expression"
        assert condition["field"] == "P5"
        assert condition["value"] == 1

    def test_extract_static_condition_list(self, preprocessor):
        """测试列表条件提取"""
        mode_config = {"condition": "P5&0xFF in [3,6]"}

        condition = preprocessor._extract_static_condition("test_mode", mode_config)

        assert isinstance(condition, dict)
        assert condition["field"] == "P5"
        assert condition["values"] == [3, 6]

    def test_process_mode_platforms(self, preprocessor):
        """测试模式平台处理"""
        mode_config = {
            "io": ["P1", "P2"],
            "sensor_io": ["P4"],
            "switch": {"P3": {"description": "test"}},
        }

        platforms = preprocessor._process_mode_platforms(mode_config)

        assert isinstance(platforms, dict)
        assert "switch" in platforms
        assert "sensor" in platforms
        assert "P1" in platforms["switch"]
        assert "P4" in platforms["sensor"]

    def test_create_version_config(self, preprocessor):
        """测试版本配置创建"""
        base_config = {"name": "test", "_features": {"base": True}}
        version_specific = {"version_feature": True}

        versioned = preprocessor._create_version_config(base_config, version_specific)

        assert versioned["name"] == "test"
        assert versioned["_features"]["base"] is True
        assert versioned["_features"]["version_feature"] is True
        assert versioned["_features"]["is_versioned_instance"] is True

    def test_generate_static_configs_integration(self, preprocessor):
        """测试完整的静态配置生成"""
        configs = preprocessor.generate_static_configs()

        assert isinstance(configs, dict)
        assert len(configs) > 0

        # 验证基本设备存在
        assert "SL_NATURE" in configs
        assert "SL_OL" in configs
        assert "SL_DOOYA" in configs

        # 验证SL_NATURE的处理结果
        nature_config = configs["SL_NATURE"]
        assert nature_config["_features"]["is_dynamic"] is True
        assert "_mode_configs" in nature_config

    def test_preprocessing_stats(self, preprocessor):
        """测试预处理统计"""
        configs = preprocessor.generate_static_configs()
        stats = preprocessor.get_preprocessing_stats()

        assert isinstance(stats, dict)
        assert "total_devices" in stats
        assert "legacy_devices" in stats
        assert "dynamic_devices" in stats
        assert stats["total_devices"] > 0

    def test_virtual_subdevice_detection(self, preprocessor):
        """测试虚拟子设备检测"""
        # 创建包含ALM的设备配置
        raw_config = {
            "binary_sensor": {
                "ALM": {
                    "description": "报警位掩码",
                    "rw": "R",
                }
            }
        }

        subdevice_type = preprocessor._get_virtual_subdevice_type(raw_config)
        assert subdevice_type == "bitmask"

    def test_special_device_features_integration(self, preprocessor):
        """测试特殊设备特性集成"""
        configs = preprocessor.generate_static_configs()

        # SL_NATURE应该包含特殊特性
        nature_config = configs["SL_NATURE"]
        features = nature_config["_features"]

        assert "default_mode" in features
        assert "mode_switch_field" in features
        assert features["default_mode"] == "switch_mode"
