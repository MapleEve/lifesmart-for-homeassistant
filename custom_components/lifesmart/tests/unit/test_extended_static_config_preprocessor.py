"""Gen2-only ExtendedStaticConfigPreprocessor unit tests."""

from typing import Any, Dict

import pytest

from custom_components.lifesmart.core.config.extended_static_config_preprocessor import (
    DeviceCentricConfigProcessor,
    ExtendedStaticConfigPreprocessor,
)


class TestExtendedStaticConfigPreprocessor:
    """Strict Gen2 preprocessor tests."""

    @pytest.fixture
    def sample_gen2_device_data(self) -> Dict[str, Any]:
        return {
            "TEST_SWITCH": {
                "name": "测试开关",
                "category": "switch",
                "_generation": 2,
                "manufacturer": "lifesmart",
                "model": "TEST_SWITCH",
                "platforms": {
                    "switch": {
                        "io_configs": {
                            "P1": {
                                "description": "开关控制",
                                "rw": "RW",
                                "data_type": "binary_switch",
                            }
                        }
                    }
                },
            },
            "TEST_DYNAMIC": {
                "name": "测试动态设备",
                "category": "climate",
                "_generation": 2,
                "manufacturer": "lifesmart",
                "model": "TEST_DYNAMIC",
                "dynamic": True,
                "platforms": {},
                "switch_mode": {
                    "condition": "P5&0xFF==1",
                    "io": ["P1"],
                },
                "climate_mode": {
                    "condition": "P5&0xFF in [3,6]",
                    "climate": {
                        "P4": {
                            "description": "T当前温度",
                            "rw": "R",
                            "data_type": "temperature",
                        }
                    },
                },
            },
            "TEST_VERSIONED": {
                "name": "测试版本设备",
                "category": "switch",
                "_generation": 2,
                "manufacturer": "lifesmart",
                "model": "TEST_VERSIONED",
                "versioned": True,
                "platforms": {},
                "version_modes": {
                    "V1": {
                        "name": "测试版本设备 V1",
                        "platforms": {
                            "switch": {
                                "io_configs": {
                                    "P1": {
                                        "description": "开关控制",
                                        "rw": "RW",
                                        "data_type": "binary_switch",
                                    }
                                }
                            }
                        },
                    }
                },
            },
            "_metadata": {"note": "explicit non-device entry"},
            "cam": {"note": "lowercase appendix/example entry"},
        }

    @pytest.fixture
    def preprocessor(self, sample_gen2_device_data):
        return ExtendedStaticConfigPreprocessor(sample_gen2_device_data)

    def test_init_has_no_legacy_format_state(self, sample_gen2_device_data):
        preprocessor = ExtendedStaticConfigPreprocessor(sample_gen2_device_data)

        assert preprocessor.raw_data == sample_gen2_device_data
        assert isinstance(preprocessor.static_configs, dict)
        assert not hasattr(preprocessor, "config_format")
        assert not hasattr(preprocessor, "_SPECIAL_DEVICE_FEATURES")
        assert not hasattr(preprocessor, "_COVER_POSITIONING_MAP")
        assert not hasattr(preprocessor, "_VERSIONED_DEVICE_CONFIG")

    def test_generate_static_configs_accepts_only_gen2_devices(self, preprocessor):
        configs = preprocessor.generate_static_configs()

        assert set(configs) == {"TEST_SWITCH", "TEST_DYNAMIC", "TEST_VERSIONED"}
        assert all(
            config["_features"]["generation"] == 2 for config in configs.values()
        )
        assert configs["TEST_SWITCH"]["platforms"]["switch"]["P1"]["rw"] == "RW"

    def test_generate_static_configs_ignores_explicit_non_device_entries(
        self, preprocessor
    ):
        configs = preprocessor.generate_static_configs()
        stats = preprocessor.get_preprocessing_stats()

        assert "_metadata" not in configs
        assert "cam" not in configs
        assert stats["ignored_non_device_entries"] == 2
        assert stats["total_devices"] == 3
        assert "legacy_devices" not in stats
        assert "virtual_subdevices" not in stats

    def test_virtual_test_is_explicit_test_only_non_device_entry(self):
        data = {
            "VIRTUAL_TEST": {
                "name": "虚拟测试设备",
                "sensor": {
                    "TEST": {
                        "description": "hs",
                        "data_type": "generic",
                    }
                },
            },
            "REAL_DEVICE": {
                "name": "真实设备",
                "category": "switch",
                "_generation": 2,
                "manufacturer": "lifesmart",
                "model": "REAL_DEVICE",
                "platforms": {},
            },
        }

        preprocessor = ExtendedStaticConfigPreprocessor(data)
        configs = preprocessor.generate_static_configs()
        stats = preprocessor.get_preprocessing_stats()

        assert set(configs) == {"REAL_DEVICE"}
        assert stats["ignored_non_device_entries"] == 1
        assert stats["total_devices"] == 1

    def test_other_uppercase_legacy_shape_still_fails_hard(self):
        data = {
            "VIRTUAL_TEST_CLONE": {
                "name": "虚拟测试设备复制品",
                "sensor": {
                    "TEST": {
                        "description": "hs",
                        "data_type": "generic",
                    }
                },
            }
        }

        with pytest.raises(ValueError, match="legacy/non-Gen2 config rejected"):
            ExtendedStaticConfigPreprocessor(data).generate_static_configs()

    def test_legacy_shape_fails_hard(self):
        legacy_data = {
            "SL_OL": {
                "name": "单路开关",
                "switch": {
                    "P1": {
                        "description": "开关控制",
                        "rw": "RW",
                        "data_type": "binary_switch",
                    }
                },
            }
        }

        with pytest.raises(ValueError, match="legacy/non-Gen2 config rejected"):
            ExtendedStaticConfigPreprocessor(legacy_data).generate_static_configs()

    def test_generation_one_fails_hard(self):
        gen1_data = {
            "TEST_GEN1": {
                "name": "旧设备",
                "category": "switch",
                "_generation": 1,
                "platforms": {},
            }
        }

        with pytest.raises(ValueError, match="explicit _generation=2 is required"):
            ExtendedStaticConfigPreprocessor(gen1_data).generate_static_configs()

    def test_non_dict_device_entry_fails_hard(self):
        with pytest.raises(ValueError, match="Gen2 device config must be a dict"):
            ExtendedStaticConfigPreprocessor({"TEST_BAD": []}).generate_static_configs()

    def test_uppercase_none_device_entry_fails_hard(self):
        with pytest.raises(ValueError, match="Gen2 device config must be a dict"):
            ExtendedStaticConfigPreprocessor({"TEST_NONE": None}).generate_static_configs()

    def test_dynamic_modes_use_gen2_processor(self, preprocessor):
        configs = preprocessor.generate_static_configs()
        dynamic_config = configs["TEST_DYNAMIC"]

        assert dynamic_config["_features"]["is_dynamic"] is True
        assert set(dynamic_config["_mode_configs"]) == {"switch_mode", "climate_mode"}
        assert dynamic_config["_mode_configs"]["switch_mode"]["condition"] == {
            "type": "expression",
            "expression": "P5&0xFF==1",
            "evaluation_method": "bitwise_and",
            "field": "P5",
            "mask": 255,
            "bitwise_and": 255,
            "value": 1,
        }

    def test_version_modes_do_not_expand_legacy_version_constants(self, preprocessor):
        configs = preprocessor.generate_static_configs()

        assert "TEST_VERSIONED" in configs
        assert "TEST_VERSIONED_V1" not in configs
        assert set(configs["TEST_VERSIONED"]["_version_configs"]) == {"V1"}

    def test_no_legacy_processing_methods_remain(self, preprocessor):
        assert not hasattr(preprocessor, "_process_legacy_device")
        assert not hasattr(preprocessor, "_extract_legacy_features")
        assert not hasattr(preprocessor, "_process_legacy_dynamic_modes")
        assert not hasattr(preprocessor, "_get_virtual_subdevice_type")

    def test_device_centric_condition_parser_supports_list_condition(self):
        processor = DeviceCentricConfigProcessor()
        condition = processor._extract_static_condition(
            {"condition": "P5&0xFF in [3,6]"}
        )

        assert condition["field"] == "P5"
        assert condition["values"] == [3, 6]
        assert condition["evaluation_method"] == "bitwise_and"
