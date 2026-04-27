"""
针对 LifeSmart 客户端基类 (client_base.py) 的单元测试。

此测试套件专注于验证抽象基类 LifeSmartClientBase 的核心功能，使用utils工厂函数：
- 设备控制业务逻辑的准确性（灯光、窗帘、温控等）
- 不同设备类型的特殊处理逻辑
- 错误处理和边界条件的处理
"""

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.climate import HVACMode

from custom_components.lifesmart.core.client_base import LifeSmartClientBase
from custom_components.lifesmart.core.const import (
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_SET_VAL,
    CMD_TYPE_SET_CONFIG,
)
from ..utils.constants import (
    CLIENT_BASE_TEST_VALUES,
)
from ..utils.typed_factories import (
    create_gen2_devices,
)


class MockLifeSmartClient(LifeSmartClientBase):
    """用于测试的具体客户端实现，简化的mock架构。"""

    def __init__(self):
        # 创建简化的mock对象
        self._send_single_command = AsyncMock(return_value=0)
        self._send_multi_command = AsyncMock(return_value=0)
        self._get_all_devices = AsyncMock(return_value=[])

    async def _async_get_all_devices(self, timeout=None):
        """实现抽象设备列表接口，委托给测试用 mock。"""
        return await self._get_all_devices()

    async def _async_send_single_command(
        self, agt: str, me: str, idx: str, command_type: int, val: Any
    ) -> int:
        """实现抽象单命令接口，委托给测试用 mock。"""
        return await self._send_single_command(agt, me, idx, command_type, val)

    async def _async_send_multi_command(
        self, agt: str, me: str, io_list: list[dict]
    ) -> int:
        """实现抽象多命令接口，委托给测试用 mock。"""
        return await self._send_multi_command(agt, me, io_list)

    async def _async_set_scene(self, agt: str, scene_name: str) -> int:
        """实现抽象场景触发接口。"""
        return 0

    async def _async_send_ir_key(
        self,
        agt: str,
        me: str,
        category: str,
        brand: str,
        keys: str,
        ai: str = "",
        idx: str = "",
    ) -> int:
        """实现抽象红外按键接口。"""
        return 0

    async def _async_add_scene(self, agt: str, scene_name: str, actions: str) -> int:
        """实现抽象新增场景接口。"""
        return 0

    async def _async_delete_scene(self, agt: str, scene_name: str) -> int:
        """实现抽象删除场景接口。"""
        return 0

    async def _async_get_scene_list(self, agt: str) -> list[dict[str, Any]]:
        """实现抽象场景列表接口。"""
        return []

    async def _async_get_room_list(self, agt: str) -> list[dict[str, Any]]:
        """实现抽象房间列表接口。"""
        return []

    async def _async_get_hub_list(self) -> list[dict[str, Any]]:
        """实现抽象中枢列表接口。"""
        return []

    async def _async_change_device_icon(self, device_id: str, icon: str) -> int:
        """实现抽象设备图标修改接口。"""
        return 0

    async def _async_set_device_eeprom(
        self, device_id: str, key: str, value: Any
    ) -> int:
        """实现抽象 EEPROM 设置接口。"""
        return 0

    async def _async_add_device_timer(
        self, device_id: str, cron_info: str, key: str
    ) -> int:
        """实现抽象设备定时器接口。"""
        return 0

    async def _async_ir_control(self, device_id: str, options: dict) -> int:
        """实现抽象红外控制接口。"""
        return 0

    async def _async_send_ir_code(self, device_id: str, ir_data: list | bytes) -> int:
        """实现抽象红外码发送接口。"""
        return 0

    async def _async_ir_raw_control(self, device_id: str, raw_data: str) -> int:
        """实现抽象原始红外控制接口。"""
        return 0

    async def _async_get_ir_remote_list(self, agt: str) -> dict[str, Any]:
        """实现抽象红外遥控器列表接口。"""
        return {}


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
        mock_devices = create_gen2_devices(["SL_OL", "SL_SW_IF3"])
        mock_client._get_all_devices.return_value = mock_devices

        devices = await mock_client.async_get_all_devices()

        assert devices == mock_devices
        mock_client._get_all_devices.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_set_scene_interface(self, mock_client):
        """测试当前Gen2场景命令公共接口。"""
        with patch.object(
            mock_client, "_async_set_scene", new_callable=AsyncMock
        ) as mock_set_scene:
            mock_set_scene.return_value = 0

            result = await mock_client.async_set_scene(
                CLIENT_BASE_TEST_VALUES["scene_hub_default"],
                CLIENT_BASE_TEST_VALUES["scene_identifier_1"],
            )

            assert result == 0
            mock_set_scene.assert_called_once_with(
                CLIENT_BASE_TEST_VALUES["scene_hub_default"],
                CLIENT_BASE_TEST_VALUES["scene_identifier_1"],
            )

    def test_removed_legacy_helper_aliases_are_absent(self, mock_client):
        """Gen2-only客户端不再暴露旧版helper别名。"""
        assert not hasattr(mock_client, "get_devices")
        assert not hasattr(mock_client, "lifesmart_scene_command")
        assert not hasattr(mock_client, "set_hvac_mode")
        assert not hasattr(mock_client, "set_fan_speed")
        assert not hasattr(mock_client, "set_temperature_decimal")
        assert not hasattr(mock_client, "set_light_brightness_async")

    @pytest.mark.asyncio
    async def test_async_send_single_command_interface(self, mock_client):
        """测试发送单个命令的公共接口。"""
        mock_client._send_single_command.return_value = 0

        result = await mock_client.async_send_single_command(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            CLIENT_BASE_TEST_VALUES["command_io_l1"],
            CMD_TYPE_ON,
            1,
        )

        assert result == 0
        mock_client._send_single_command.assert_called_once_with(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            CLIENT_BASE_TEST_VALUES["command_io_l1"],
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
    async def test_current_gen2_climate_commands(self, mock_client):
        """测试当前Gen2气候控制公共接口使用设备字典和显式命令配置。"""
        mock_client._send_single_command.return_value = 0
        device = create_gen2_devices(["SL_CP_AIR"])[0]

        result = await mock_client.async_set_climate_hvac_mode(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            device,
            HVACMode.COOL,
        )
        assert result == 0
        mock_client._send_single_command.assert_any_call(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            "P1",
            CMD_TYPE_ON,
            1,
        )
        mock_client._send_single_command.assert_called_with(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            "P1",
            CMD_TYPE_SET_CONFIG,
            0,
        )

        mock_client._send_single_command.reset_mock()

        result = await mock_client.async_set_climate_temperature(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            device,
            24.5,
        )
        assert result == 0
        mock_client._send_single_command.assert_called_with(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            "P4",
            CMD_TYPE_SET_CONFIG,
            245,
        )

    @pytest.mark.asyncio
    async def test_current_light_commands(self, mock_client):
        """测试当前灯光控制命令调用Gen2单命令接口。"""
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
            CMD_TYPE_OFF,
            0,
        )

    @pytest.mark.asyncio
    async def test_current_gen2_cover_commands(self, mock_client):
        """测试当前Gen2窗帘控制接口使用设备字典和显式命令配置。"""
        mock_client._send_single_command.return_value = 0
        device = create_gen2_devices(["SL_DOOYA"])[0]

        # 测试打开窗帘命令
        result = await mock_client.open_cover_async(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            device,
        )
        assert result == 0
        mock_client._send_single_command.assert_called_with(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            "P2",
            CMD_TYPE_SET_VAL,
            100,
        )

        # 测试关闭窗帘命令
        result = await mock_client.close_cover_async(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            device,
        )
        assert result == 0
        mock_client._send_single_command.assert_called_with(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            "P2",
            CMD_TYPE_SET_VAL,
            0,
        )

        # 测试停止窗帘命令
        result = await mock_client.stop_cover_async(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            device,
        )
        assert result == 0
        mock_client._send_single_command.assert_called_with(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            "P2",
            CMD_TYPE_SET_CONFIG,
            128,
        )

        # 测试设置窗帘位置命令
        result = await mock_client.set_cover_position_async(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            75,
            device,
        )
        assert result == 0
        mock_client._send_single_command.assert_called_with(
            CLIENT_BASE_TEST_VALUES["command_agt_1"],
            CLIENT_BASE_TEST_VALUES["command_device_1"],
            "P2",
            CMD_TYPE_SET_VAL,
            75,
        )
