"""
工厂兼容性验证测试。
验证强类型工厂函数与现有factories.py的完全兼容性，确保新旧系统无缝协作。

本文件是Phase 1增量基础设施建设的验证组件，基于ZEN专家指导设计。
提供完整的兼容性测试套件，确保强类型系统不会破坏现有功能。
"""

import pytest
from typing import Any, Dict, List

from custom_components.lifesmart.tests.utils.typed_factories import (
    create_typed_core_devices,
    create_typed_devices_by_platform,
    convert_typed_devices_to_dict,
    create_typed_device_from_dict,
    create_typed_smart_plug,
    create_typed_power_meter_plug,
    create_typed_switch_if3,
    create_typed_dimmer_light,
    create_typed_rgbw_light,
    create_typed_environment_sensor,
    create_typed_door_sensor,
    create_typed_curtain_motor,
    create_typed_thermostat_panel,
    create_typed_smart_lock,
)
from custom_components.lifesmart.tests.utils.factories import (
    create_smart_plug_ol,
    create_power_meter_plug,
    create_switch_if3,
    create_brightness_light,
    create_rgbw_light,
    create_environment_sensor,
    create_door_sensor,
    create_curtain_motor,
    create_fancoil_thermo,
    create_smart_lock,
    validate_device_data,
)
from custom_components.lifesmart.tests.utils.type_validators import (
    validate_typed_device,
    validate_device_compatibility,
    get_validation_summary,
)
from custom_components.lifesmart.tests.utils.models import TypedDevice


class TestTypedFactoryCompatibility:
    """测试强类型工厂与现有工厂的兼容性"""

    def test_core_device_types_coverage(self):
        """测试核心设备类型覆盖完整性"""
        # 获取强类型核心设备
        typed_devices = create_typed_core_devices()

        # 验证数量
        assert len(typed_devices) == 10, "应该有10个核心设备类型"

        # 验证设备类型覆盖
        expected_device_types = {
            "SL_OL",  # 智慧插座
            "SL_OE_3C",  # 计量插座
            "SL_SW_IF3",  # 三联开关
            "SL_LI_WW",  # 调光灯泡
            "SL_CT_RGBW",  # RGBW灯带
            "SL_SC_THL",  # 环境传感器
            "SL_SC_G",  # 门窗传感器
            "SL_DOOYA",  # 窗帘电机
            "SL_NATURE",  # 温控面板
            "SL_LK_LS",  # 智能门锁
        }

        actual_device_types = {device.devtype for device in typed_devices}
        assert (
            actual_device_types == expected_device_types
        ), f"设备类型不匹配：期望 {expected_device_types}，实际 {actual_device_types}"

    def test_platform_distribution(self):
        """测试平台分布正确性"""
        platform_expectations = {
            "switch": 2,  # SL_OL, SL_SW_IF3
            "sensor": 2,  # SL_OE_3C, SL_SC_THL
            "light": 2,  # SL_LI_WW, SL_CT_RGBW
            "binary_sensor": 1,  # SL_SC_G
            "cover": 1,  # SL_DOOYA
            "climate": 1,  # SL_NATURE
            "lock": 1,  # SL_LK_LS
        }

        for platform, expected_count in platform_expectations.items():
            devices = create_typed_devices_by_platform(platform)
            assert (
                len(devices) == expected_count
            ), f"平台 {platform} 期望 {expected_count} 个设备，实际 {len(devices)} 个"

    def test_dictionary_conversion_bidirectional(self):
        """测试字典转换的双向性"""
        typed_devices = create_typed_core_devices()

        for device in typed_devices:
            # 转换为字典
            dict_device = device.to_dict()

            # 验证字典结构
            assert isinstance(dict_device, dict)
            assert "agt" in dict_device
            assert "me" in dict_device
            assert "devtype" in dict_device
            assert "name" in dict_device
            assert "data" in dict_device

            # 从字典重建
            reconstructed_device = create_typed_device_from_dict(dict_device)

            # 验证重建设备的关键字段
            assert reconstructed_device.agt == device.agt
            assert reconstructed_device.me == device.me
            assert reconstructed_device.devtype == device.devtype
            assert reconstructed_device.name == device.name
            assert len(reconstructed_device.data) == len(device.data)

    def test_existing_factory_validation_compatibility(self):
        """测试与现有工厂验证函数的兼容性"""
        typed_devices = create_typed_core_devices()

        for device in typed_devices:
            dict_device = device.to_dict()

            # 使用现有的验证函数
            is_valid = validate_device_data(dict_device)
            assert is_valid, f"设备 {device.devtype} 未通过现有工厂验证"

    def test_specific_device_factory_equivalence(self):
        """测试特定设备工厂的等价性"""
        test_cases = [
            # (强类型工厂函数, 传统工厂函数, 设备类型)
            (create_typed_smart_plug, create_smart_plug_ol, "SL_OL"),
            (create_typed_power_meter_plug, create_power_meter_plug, "SL_OE_3C"),
            (create_typed_switch_if3, create_switch_if3, "SL_SW_IF3"),
            (create_typed_environment_sensor, create_environment_sensor, "SL_SC_THL"),
            (create_typed_door_sensor, create_door_sensor, "SL_SC_G"),
            (create_typed_curtain_motor, create_curtain_motor, "SL_DOOYA"),
            (create_typed_smart_lock, create_smart_lock, "SL_LK_LS"),
        ]

        for typed_factory, traditional_factory, device_type in test_cases:
            # 创建设备
            typed_device = typed_factory()
            traditional_device = traditional_factory()

            # 转换强类型设备为字典
            typed_as_dict = typed_device.to_dict()

            # 验证关键字段一致性
            assert typed_as_dict["devtype"] == traditional_device["devtype"]
            assert typed_as_dict["devtype"] == device_type

            # 验证数据结构一致性
            assert isinstance(typed_as_dict["data"], dict)
            assert isinstance(traditional_device["data"], dict)

            # 两者都应该通过现有验证
            assert validate_device_data(typed_as_dict)
            assert validate_device_data(traditional_device)


class TestTypedDeviceValidation:
    """测试强类型设备验证功能"""

    def test_all_core_devices_validation(self):
        """测试所有核心设备的验证"""
        typed_devices = create_typed_core_devices()

        for device in typed_devices:
            result = validate_typed_device(device)
            assert result.is_valid, f"设备 {device.devtype} 验证失败: {result.errors}"

    def test_device_compatibility_validation(self):
        """测试设备兼容性验证"""
        typed_devices = create_typed_core_devices()

        for device in typed_devices:
            result = validate_device_compatibility(device)
            assert (
                result.is_valid
            ), f"设备 {device.devtype} 兼容性验证失败: {result.errors}"

    def test_validation_summary(self):
        """测试验证摘要功能"""
        typed_devices = create_typed_core_devices()
        summary = get_validation_summary(typed_devices)

        assert summary["total_devices"] == 10
        assert summary["valid_devices"] == 10
        assert summary["invalid_devices"] == 0
        assert summary["success_rate"] == 1.0
        assert summary["total_errors"] == 0
        assert isinstance(summary["details"], dict)


class TestDataConsistency:
    """测试数据一致性"""

    def test_hub_id_consistency(self):
        """测试Hub ID的一致性"""
        typed_devices = create_typed_core_devices()

        # 检查Hub ID格式
        for device in typed_devices:
            assert len(device.agt) > 10, f"设备 {device.devtype} 的Hub ID太短"
            assert isinstance(
                device.agt, str
            ), f"设备 {device.devtype} 的Hub ID应该是字符串"

    def test_device_id_uniqueness(self):
        """测试设备ID的唯一性"""
        typed_devices = create_typed_core_devices()
        device_ids = [device.me for device in typed_devices]

        # 检查唯一性
        assert len(device_ids) == len(set(device_ids)), "设备ID应该唯一"

    def test_io_data_structure(self):
        """测试IO数据结构的一致性"""
        typed_devices = create_typed_core_devices()

        for device in typed_devices:
            assert isinstance(
                device.data, dict
            ), f"设备 {device.devtype} 的data字段应该是字典"

            for port_name, io_config in device.data.items():
                assert hasattr(
                    io_config, "to_dict"
                ), f"设备 {device.devtype} 端口 {port_name} 的IO配置应该有to_dict方法"

                # 验证IO配置可以转换为字典
                io_dict = io_config.to_dict()
                assert isinstance(
                    io_dict, dict
                ), f"设备 {device.devtype} 端口 {port_name} 的IO配置转换结果应该是字典"


class TestSpecializedDeviceTypes:
    """测试专用设备类型"""

    def test_switch_device_specialization(self):
        """测试开关设备专用功能"""
        switch_devices = create_typed_devices_by_platform("switch")

        for device in switch_devices:
            # 检查是否有专用方法
            assert hasattr(
                device, "get_switch_ports"
            ), f"开关设备 {device.devtype} 应该有get_switch_ports方法"

            switch_ports = device.get_switch_ports()
            assert isinstance(
                switch_ports, dict
            ), f"开关设备 {device.devtype} 的开关端口应该是字典"

    def test_sensor_device_specialization(self):
        """测试传感器设备专用功能"""
        sensor_devices = create_typed_devices_by_platform("sensor")

        for device in sensor_devices:
            # 检查是否有专用方法
            assert hasattr(
                device, "get_sensor_ports"
            ), f"传感器设备 {device.devtype} 应该有get_sensor_ports方法"

            sensor_ports = device.get_sensor_ports()
            assert isinstance(
                sensor_ports, dict
            ), f"传感器设备 {device.devtype} 的传感器端口应该是字典"

    def test_light_device_specialization(self):
        """测试灯光设备专用功能"""
        light_devices = create_typed_devices_by_platform("light")

        for device in light_devices:
            # 检查是否有专用方法
            assert hasattr(
                device, "get_color_ports"
            ), f"灯光设备 {device.devtype} 应该有get_color_ports方法"
            assert hasattr(
                device, "get_brightness_ports"
            ), f"灯光设备 {device.devtype} 应该有get_brightness_ports方法"

            color_ports = device.get_color_ports()
            brightness_ports = device.get_brightness_ports()
            assert isinstance(
                color_ports, dict
            ), f"灯光设备 {device.devtype} 的颜色端口应该是字典"
            assert isinstance(
                brightness_ports, dict
            ), f"灯光设备 {device.devtype} 的亮度端口应该是字典"


class TestErrorHandling:
    """测试错误处理"""

    def test_invalid_device_dict_conversion(self):
        """测试无效设备字典的转换处理"""
        invalid_dicts = [
            {},  # 空字典
            {"agt": "test"},  # 缺少必需字段
            {
                "agt": "test",
                "me": "test",
                "devtype": "",
                "name": "test",
                "data": {},
            },  # 空设备类型
            {
                "agt": "",
                "me": "test",
                "devtype": "SL_OL",
                "name": "test",
                "data": {},
            },  # 空Hub ID
        ]

        for invalid_dict in invalid_dicts:
            with pytest.raises((ValueError, KeyError, TypeError)):
                create_typed_device_from_dict(invalid_dict)

    def test_platform_not_found(self):
        """测试不存在的平台查询"""
        devices = create_typed_devices_by_platform("nonexistent_platform")
        assert devices == [], "不存在的平台应该返回空列表"

    def test_validation_with_warnings(self):
        """测试带警告的验证情况"""
        # 创建一个可能有警告的设备
        device = create_typed_smart_plug()
        result = validate_typed_device(device)

        # 验证结构正确
        assert hasattr(result, "is_valid")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)


@pytest.fixture
def typed_device_sample():
    """提供测试用的强类型设备样本"""
    return create_typed_core_devices()


def test_integration_with_existing_test_framework(typed_device_sample):
    """测试与现有测试框架的集成"""
    # 验证fixture正常工作
    assert len(typed_device_sample) == 10

    # 验证每个设备都能转换为字典并通过现有验证
    for device in typed_device_sample:
        dict_device = device.to_dict()
        assert validate_device_data(dict_device)


def test_batch_conversion_performance():
    """测试批量转换性能"""
    import time

    # 创建大量设备进行性能测试
    devices = []
    for _ in range(100):  # 创建100个设备实例
        devices.extend(create_typed_core_devices())

    start_time = time.time()
    dict_devices = convert_typed_devices_to_dict(devices)
    conversion_time = time.time() - start_time

    assert len(dict_devices) == len(devices)
    assert conversion_time < 1.0, f"批量转换耗时 {conversion_time:.3f}s，超过1秒阈值"


if __name__ == "__main__":
    # 直接运行时执行基本兼容性检查
    print("执行基本兼容性检查...")

    # 检查核心设备类型
    devices = create_typed_core_devices()
    print(f"✅ 创建了 {len(devices)} 个核心设备")

    # 检查字典转换
    dict_devices = convert_typed_devices_to_dict(devices)
    print(f"✅ 成功转换为 {len(dict_devices)} 个字典设备")

    # 检查验证
    all_valid = all(validate_device_data(device) for device in dict_devices)
    print(f"✅ 所有设备通过现有验证: {all_valid}")

    # 检查强类型验证
    summary = get_validation_summary(devices)
    print(
        f"✅ 强类型验证摘要: {summary['valid_devices']}/{summary['total_devices']} 成功"
    )

    print("兼容性检查完成！")
