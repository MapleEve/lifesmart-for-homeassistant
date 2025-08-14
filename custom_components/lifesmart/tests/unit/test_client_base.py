"""
针对 LifeSmart 客户端基类 (client_base.py) 的单元测试。

此测试套件专注于验证抽象基类 LifeSmartClientBase 的核心功能，使用utils工厂函数：
- 设备控制业务逻辑的准确性（灯光、窗帘、温控等）
- 不同设备类型的特殊处理逻辑
- 错误处理和边界条件的处理
"""

from unittest.mock import AsyncMock, patch

import pytest

from custom_components.lifesmart.core.client_base import LifeSmartClientBase
from custom_components.lifesmart.core.const import (
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_SET_VAL,
    CMD_TYPE_SET_CONFIG,
    CMD_TYPE_SET_TEMP_DECIMAL,
)
from ..utils.constants import (
    CLIENT_BASE_TEST_VALUES,
)
from ..utils.factories import (
    create_devices_by_category,
)


class MockLifeSmartClient(LifeSmartClientBase):
    """用于测试的具体客户端实现，简化的mock架构。"""

    def __init__(self):
        # 创建简化的mock对象
        self._send_single_command = AsyncMock(return_value=0)
        self._send_multi_command = AsyncMock(return_value=0)
        self._get_all_devices = AsyncMock(return_value=[])


class TestLifeSmartClientBase:
    """测试 LifeSmartClientBase 的核心功能。"""

    @pytest.fixture
    def mock_client(self):
        """返回一个简化的MockLifeSmartClient实例。"""
        return MockLifeSmartClient()

    @pytest.mark.asyncio
    async def test_get_devices(self, mock_client):
        """测试获取设备列表的方法。"""
        # 使用工厂函数创建测试设备
        mock_devices = create_devices_by_category(["basic_switch", "advanced_switch"])
        mock_client._get_all_devices.return_value = mock_devices

        devices = await mock_client.get_devices()

        assert devices == mock_devices
        mock_client._get_all_devices.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifesmart_scene_command_wrapper(self, mock_client):
        """测试LifeSmart场景命令包装器接口。"""
        with patch.object(
            mock_client, "_send_single_command", new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = 0

            result = await mock_client.lifesmart_scene_command(
                CLIENT_BASE_TEST_VALUES["scene_identifier_1"]
            )

            assert result == 0
            mock_send.assert_called_once_with(
                CLIENT_BASE_TEST_VALUES["scene_hub_default"],
                CLIENT_BASE_TEST_VALUES["scene_identifier_1"],
                CLIENT_BASE_TEST_VALUES["scene_device_default"],
                CLIENT_BASE_TEST_VALUES["scene_device_default"],
                CMD_TYPE_ON,
                1,
            )

    @pytest.mark.asyncio
    async def test_async_send_single_command_interface(self, mock_client):
        """测试发送单个命令的公共接口。"""
        mock_client._send_single_command.return_value = 0

        result = await mock_client.async_send_single_command(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            CLIENT_BASE_TEST_VALUES["command_io_l1"],
            CLIENT_BASE_TEST_VALUES["command_type_generic"],
            CMD_TYPE_ON,
            1,
        )

        assert result == 0
        mock_client._send_single_command.assert_called_once_with(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            CLIENT_BASE_TEST_VALUES["command_io_l1"],
            CLIENT_BASE_TEST_VALUES["command_type_generic"],
            CMD_TYPE_ON,
            1,
        )

    @pytest.mark.asyncio
    async def test_async_send_multi_command_interface(self, mock_client):
        """测试发送多个命令的公共接口。"""
        io_list = [
            {
                "idx": CLIENT_BASE_TEST_VALUES["io_port_p1"],
                "type": CMD_TYPE_ON,
                "val": 1,
            }
        ]
        mock_client._send_multi_command.return_value = 0

        result = await mock_client.async_send_multi_command(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            io_list,
        )

        assert result == 0
        mock_client._send_multi_command.assert_called_once_with(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            io_list,
        )

    @pytest.mark.asyncio
    async def test_legacy_climate_commands(self, mock_client):
        """测试传统气候控制命令的正确包装。"""
        mock_client._send_single_command.return_value = 0

        # 测试设置HVAC模式命令
        result = await mock_client.set_hvac_mode(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            CLIENT_BASE_TEST_VALUES["command_io_l1"],
            2,
        )
        assert result == 0
        mock_client._send_single_command.assert_called_with(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            CLIENT_BASE_TEST_VALUES["command_io_l1"],
            CLIENT_BASE_TEST_VALUES["command_type_generic"],
            CMD_TYPE_SET_CONFIG,
            2,
        )

        # 测试设置风扇速度命令
        result = await mock_client.set_fan_speed(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            CLIENT_BASE_TEST_VALUES["command_io_l1"],
            3,
        )
        assert result == 0
        mock_client._send_single_command.assert_called_with(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            CLIENT_BASE_TEST_VALUES["command_io_l1"],
            CLIENT_BASE_TEST_VALUES["command_type_generic"],
            CMD_TYPE_SET_CONFIG,
            3,
        )

        # 测试设置温度命令
        result = await mock_client.set_temperature_decimal(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            CLIENT_BASE_TEST_VALUES["command_io_l1"],
            245,
        )
        assert result == 0
        mock_client._send_single_command.assert_called_with(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            CLIENT_BASE_TEST_VALUES["command_io_l1"],
            CLIENT_BASE_TEST_VALUES["command_type_generic"],
            CMD_TYPE_SET_TEMP_DECIMAL,
            245,
        )

    @pytest.mark.asyncio
    async def test_legacy_light_commands(self, mock_client):
        """测试传统灯光控制命令的正确包装。"""
        mock_client._send_single_command.return_value = 0

        # 测试开灯命令
        result = await mock_client.turn_on_light_switch_async(
            CLIENT_BASE_TEST_VALUES["command_io_l1"],
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
        )
        assert result == 0
        mock_client._send_single_command.assert_called_with(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            CLIENT_BASE_TEST_VALUES["command_io_l1"],
            CLIENT_BASE_TEST_VALUES["command_type_generic"],
            CMD_TYPE_ON,
            1,
        )

        # 测试关灯命令
        result = await mock_client.turn_off_light_switch_async(
            CLIENT_BASE_TEST_VALUES["command_io_l1"],
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
        )
        assert result == 0
        mock_client._send_single_command.assert_called_with(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            CLIENT_BASE_TEST_VALUES["command_io_l1"],
            CLIENT_BASE_TEST_VALUES["command_type_generic"],
            CMD_TYPE_OFF,
            0,
        )

        # 测试设置亮度命令
        result = await mock_client.set_light_brightness_async(
            CLIENT_BASE_TEST_VALUES["command_io_l1"],
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            128,
        )
        assert result == 0
        mock_client._send_single_command.assert_called_with(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            CLIENT_BASE_TEST_VALUES["command_io_l1"],
            CLIENT_BASE_TEST_VALUES["command_type_generic"],
            CMD_TYPE_SET_VAL,
            128,
        )

    @pytest.mark.asyncio
    async def test_legacy_cover_commands(self, mock_client):
        """测试传统窗帘控制命令的正确包装。"""
        mock_client._send_single_command.return_value = 0

        # 测试打开窗帘命令
        result = await mock_client.open_cover_async(
            CLIENT_BASE_TEST_VALUES["io_port_open"],
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
        )
        assert result == 0
        mock_client._send_single_command.assert_called_with(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            CLIENT_BASE_TEST_VALUES["io_port_open"],
            CLIENT_BASE_TEST_VALUES["command_type_generic"],
            CMD_TYPE_ON,
            1,
        )

        # 测试关闭窗帘命令
        result = await mock_client.close_cover_async(
            CLIENT_BASE_TEST_VALUES["io_port_close"],
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
        )
        assert result == 0
        mock_client._send_single_command.assert_called_with(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            CLIENT_BASE_TEST_VALUES["io_port_close"],
            CLIENT_BASE_TEST_VALUES["command_type_generic"],
            CMD_TYPE_ON,
            1,
        )

        # 测试停止窗帘命令
        result = await mock_client.stop_cover_async(
            CLIENT_BASE_TEST_VALUES["io_port_stop"],
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
        )
        assert result == 0
        mock_client._send_single_command.assert_called_with(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            CLIENT_BASE_TEST_VALUES["io_port_stop"],
            CLIENT_BASE_TEST_VALUES["command_type_generic"],
            CMD_TYPE_ON,
            1,
        )

        # 测试设置窗帘位置命令
        result = await mock_client.set_cover_position_async(
            CLIENT_BASE_TEST_VALUES["io_port_position"],
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            75,
        )
        assert result == 0
        mock_client._send_single_command.assert_called_with(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            CLIENT_BASE_TEST_VALUES["io_port_position"],
            CLIENT_BASE_TEST_VALUES["command_type_generic"],
            CMD_TYPE_SET_VAL,
            75,
        )
