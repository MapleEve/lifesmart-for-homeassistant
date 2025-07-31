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

        assert entity._raw_device == sample_device_data
        assert entity._device_name == "测试设备"
        assert entity._agt == "test_hub_123"
        assert entity._me == "test_device_456"
        assert entity._devtype == "SL_SW_IF3"
        assert entity._client == mock_client

    def test_entity_initialization_without_name(
        self, mock_client, sample_device_without_name
    ):
        """测试没有名称的设备初始化。"""
        entity = LifeSmartEntity(sample_device_without_name, mock_client)

        assert entity._device_name == "Unnamed SL_SW_IF3"

    def test_entity_initialization_empty_device_type(self, mock_client):
        """测试空设备类型的初始化。"""
        device_data = {
            HUB_ID_KEY: "test_hub_123",
            DEVICE_ID_KEY: "test_device_456",
        }

        entity = LifeSmartEntity(device_data, mock_client)

        assert entity._device_name == "Unnamed Device"
        assert entity._devtype is None

    def test_extra_state_attributes(self, mock_client, sample_device_data):
        """测试额外状态属性。"""
        entity = LifeSmartEntity(sample_device_data, mock_client)

        attributes = entity.extra_state_attributes

        assert attributes[HUB_ID_KEY] == "test_hub_123"
        assert attributes[DEVICE_ID_KEY] == "test_device_456"
        assert attributes[DEVICE_TYPE_KEY] == "SL_SW_IF3"

    def test_property_accessors(self, mock_client, sample_device_data):
        """测试属性访问器。"""
        entity = LifeSmartEntity(sample_device_data, mock_client)

        assert entity.agt == "test_hub_123"
        assert entity.me == "test_device_456"
        assert entity.devtype == "SL_SW_IF3"

    def test_assumed_state_property(self, mock_client, sample_device_data):
        """测试假定状态属性。"""
        entity = LifeSmartEntity(sample_device_data, mock_client)

        # LifeSmart 集成不使用假定状态
        assert entity.assumed_state is False

    def test_should_poll_property(self, mock_client, sample_device_data):
        """测试轮询属性。"""
        entity = LifeSmartEntity(sample_device_data, mock_client)

        # LifeSmart 集成通过实时推送接收更新，不需要轮询
        assert entity.should_poll is False

    def test_attributes_with_none_values(self, mock_client):
        """测试包含 None 值的属性。"""
        device_data = {
            HUB_ID_KEY: None,
            DEVICE_ID_KEY: None,
            DEVICE_TYPE_KEY: None,
        }

        entity = LifeSmartEntity(device_data, mock_client)

        assert entity.agt is None
        assert entity.me is None
        assert entity.devtype is None
        assert entity._device_name == "Unnamed None"

    def test_attributes_initialization(self, mock_client, sample_device_data):
        """测试属性字典的正确初始化。"""
        entity = LifeSmartEntity(sample_device_data, mock_client)

        # 验证 _attributes 字典包含正确的键值对
        expected_attributes = {
            HUB_ID_KEY: "test_hub_123",
            DEVICE_ID_KEY: "test_device_456",
            DEVICE_TYPE_KEY: "SL_SW_IF3",
        }

        assert entity._attributes == expected_attributes

        # 确保 extra_state_attributes 返回相同的字典
        assert entity.extra_state_attributes == expected_attributes

    def test_entity_inheritance_compatibility(self, mock_client, sample_device_data):
        """测试实体继承兼容性。"""
        entity = LifeSmartEntity(sample_device_data, mock_client)

        # 验证它是 Home Assistant Entity 的实例
        from homeassistant.helpers.entity import Entity

        assert isinstance(entity, Entity)

        # 验证必要的方法存在
        assert hasattr(entity, "extra_state_attributes")
        assert hasattr(entity, "assumed_state")
        assert hasattr(entity, "should_poll")

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
        assert entity._device_name == expected_name
