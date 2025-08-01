"""
测试 Entity 模块的基类功能。

此测试文件专门测试 entity.py 中的 LifeSmartEntity 基类，包括：
- 实体的基本初始化
- 通用属性访问
- 状态管理方法
- 与 Home Assistant 的集成接口
"""

from unittest.mock import MagicMock

import pytest

from custom_components.lifesmart.const import (
    DEVICE_ID_KEY,
    DEVICE_NAME_KEY,
    DEVICE_TYPE_KEY,
    HUB_ID_KEY,
)
from custom_components.lifesmart.entity import LifeSmartEntity


class TestLifeSmartEntity:
    """测试 LifeSmartEntity 基类的功能。"""

    @pytest.fixture
    def mock_client(self):
        """提供模拟的客户端。"""
        return MagicMock()

    @pytest.fixture
    def sample_device_data(self):
        """提供示例设备数据。"""
        return {
            HUB_ID_KEY: "test_hub_123",
            DEVICE_ID_KEY: "test_device_456",
            DEVICE_NAME_KEY: "测试设备",
            DEVICE_TYPE_KEY: "SL_SW_IF3",
            "data": {"L1": {"type": 129}, "L2": {"type": 128}},
        }

    @pytest.fixture
    def sample_device_without_name(self):
        """提供没有名称的设备数据。"""
        return {
            HUB_ID_KEY: "test_hub_123",
            DEVICE_ID_KEY: "test_device_456",
            DEVICE_TYPE_KEY: "SL_SW_IF3",
            "data": {"L1": {"type": 129}},
        }

    def test_entity_initialization(self, mock_client, sample_device_data):
        """测试实体的基本初始化。"""
        entity = LifeSmartEntity(sample_device_data, mock_client)

        assert entity._raw_device == sample_device_data, "原始设备数据应该被正确保存"
        assert entity._device_name == "测试设备", "设备名称应该被正确解析"
        assert entity._agt == "test_hub_123", "Hub ID应该被正确设置"
        assert entity._me == "test_device_456", "设备ID应该被正确设置"
        assert entity._devtype == "SL_SW_IF3", "设备类型应该被正确设置"
        assert entity._client == mock_client, "客户端应该被正确设置"

    def test_entity_initialization_without_name(
        self, mock_client, sample_device_without_name
    ):
        """测试没有名称的设备初始化。"""
        entity = LifeSmartEntity(sample_device_without_name, mock_client)

        assert entity._device_name == "Unnamed SL_SW_IF3", "无名设备应该使用默认名称"

    def test_entity_initialization_empty_device_type(self, mock_client):
        """测试空设备类型的初始化。"""
        device_data = {
            HUB_ID_KEY: "test_hub_123",
            DEVICE_ID_KEY: "test_device_456",
        }

        entity = LifeSmartEntity(device_data, mock_client)

        assert entity._device_name == "Unnamed Device", "无类型设备应该使用通用默认名称"
        assert entity._devtype is None, "设备类型应该为None"

    def test_extra_state_attributes(self, mock_client, sample_device_data):
        """测试额外状态属性。"""
        entity = LifeSmartEntity(sample_device_data, mock_client)

        attributes = entity.extra_state_attributes

        assert attributes[HUB_ID_KEY] == "test_hub_123", "Hub ID应该在属性中"
        assert attributes[DEVICE_ID_KEY] == "test_device_456", "设备ID应该在属性中"
        assert attributes[DEVICE_TYPE_KEY] == "SL_SW_IF3", "设备类型应该在属性中"

    def test_property_accessors(self, mock_client, sample_device_data):
        """测试属性访问器。"""
        entity = LifeSmartEntity(sample_device_data, mock_client)

        assert entity.agt == "test_hub_123", "agt属性应该返回Hub ID"
        assert entity.me == "test_device_456", "me属性应该返回设备ID"
        assert entity.devtype == "SL_SW_IF3", "devtype属性应该返回设备类型"

    def test_assumed_state_property(self, mock_client, sample_device_data):
        """测试假定状态属性。"""
        entity = LifeSmartEntity(sample_device_data, mock_client)

        # LifeSmart 集成不使用假定状态
        assert entity.assumed_state is False, "assumed_state应该默认为False"

    def test_should_poll_property(self, mock_client, sample_device_data):
        """测试轮询属性。"""
        entity = LifeSmartEntity(sample_device_data, mock_client)

        # LifeSmart 集成通过实时推送接收更新，不需要轮询
        assert entity.should_poll is False, "should_poll应该默认为False"

    def test_attributes_with_none_values(self, mock_client):
        """测试包含 None 值的属性。"""
        device_data = {
            HUB_ID_KEY: None,
            DEVICE_ID_KEY: None,
            DEVICE_TYPE_KEY: None,
        }

        entity = LifeSmartEntity(device_data, mock_client)

        assert entity.agt is None, "空设备的agt应该为None"
        assert entity.me is None, "空设备的me应该为None"
        assert entity.devtype is None, "空设备的devtype应该为None"
        assert entity._device_name == "Unnamed None", "空设备的名称应该是Unnamed None"

    def test_attributes_initialization(self, mock_client, sample_device_data):
        """测试属性字典的正确初始化。"""
        entity = LifeSmartEntity(sample_device_data, mock_client)

        # 验证 _attributes 字典包含正确的键值对
        expected_attributes = {
            HUB_ID_KEY: "test_hub_123",
            DEVICE_ID_KEY: "test_device_456",
            DEVICE_TYPE_KEY: "SL_SW_IF3",
        }

        assert entity._attributes == expected_attributes, "实体属性应该被正确设置"

        # 确保 extra_state_attributes 返回相同的字典
        assert (
            entity.extra_state_attributes == expected_attributes
        ), "extra_state_attributes应该返回正确的属性"

    def test_entity_inheritance_compatibility(self, mock_client, sample_device_data):
        """测试实体继承兼容性。"""
        entity = LifeSmartEntity(sample_device_data, mock_client)

        # 验证它是 Home Assistant Entity 的实例
        from homeassistant.helpers.entity import Entity

        assert isinstance(entity, Entity), "应该是Entity的实例"

        # 验证必要的方法存在
        assert hasattr(
            entity, "extra_state_attributes"
        ), "应该有extra_state_attributes方法"
        assert hasattr(entity, "assumed_state"), "应该有assumed_state属性"
        assert hasattr(entity, "should_poll"), "应该有should_poll属性"

    @pytest.mark.parametrize(
        "device_data,expected_name",
        [
            (
                {DEVICE_NAME_KEY: "客厅开关", DEVICE_TYPE_KEY: "SL_SW"},
                "客厅开关",
            ),
            (
                {DEVICE_NAME_KEY: "", DEVICE_TYPE_KEY: "SL_SW"},
                "Unnamed SL_SW",
            ),
            (
                {DEVICE_NAME_KEY: None, DEVICE_TYPE_KEY: "SL_SW"},
                "Unnamed SL_SW",
            ),
            (
                {DEVICE_TYPE_KEY: "SL_SW"},
                "Unnamed SL_SW",
            ),
            (
                {},
                "Unnamed Device",
            ),
        ],
    )
    def test_device_name_generation(self, mock_client, device_data, expected_name):
        """参数化测试设备名称生成。"""
        # 添加必要的基础字段
        device_data.update(
            {
                HUB_ID_KEY: "test_hub",
                DEVICE_ID_KEY: "test_device",
            }
        )

        entity = LifeSmartEntity(device_data, mock_client)
        assert entity._device_name == expected_name, f"设备名称应该为{expected_name}"
