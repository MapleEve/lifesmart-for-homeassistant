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
from ..utils.factories import (
    create_mock_oapi_client,
    create_mock_failed_oapi_client,
    create_devices_by_category,
)


class MockLifeSmartClient(LifeSmartClientBase):
    """用于测试的具体客户端实现，简化的mock架构。"""

    def __init__(self):
        # 创建简化的mock对象
        self._send_single_command = AsyncMock(return_value=0)
        self._send_multi_command = AsyncMock(return_value=0)
        self._get_all_devices = AsyncMock(return_value=[])

    async def _async_get_all_devices(self, timeout=10):
        return await self._get_all_devices(timeout)

    async def _async_send_single_command(self, agt, me, idx, command_type, val):
        return await self._send_single_command(agt, me, idx, command_type, val)

    async def _async_send_multi_command(self, agt, me, io_list):
        return await self._send_multi_command(agt, me, io_list)

    # 其他抽象方法的简化实现
    async def _async_set_scene(self, agt, scene_name):
        return 0

    async def _async_send_ir_key(self, agt, me, category, brand, keys, ai="", idx=""):
        return 0

    async def _async_add_scene(self, agt, scene_name, actions):
        return 0

    async def _async_delete_scene(self, agt, scene_name):
        return 0

    async def _async_get_scene_list(self, agt):
        return []

    async def _async_get_room_list(self, agt):
        return []

    async def _async_get_hub_list(self):
        return []

    async def _async_change_device_icon(self, device_id, icon):
        return 0

    async def _async_set_device_eeprom(self, device_id, key, value):
        return 0

    async def _async_add_device_timer(self, device_id, cron_info, key):
        return 0

    async def _async_ir_control(self, device_id, options):
        return 0

    async def _async_send_ir_code(self, device_id, ir_data):
        return 0

    async def _async_ir_raw_control(self, device_id, raw_data):
        return 0

    async def _async_get_ir_remote_list(self, agt):
        return {}


@pytest.fixture
def mock_client():
    """创建模拟客户端实例。"""
    return MockLifeSmartClient()


class TestAbstractBaseClass:
    """测试抽象基类行为。"""

    def test_abstract_methods_cannot_be_instantiated(self):
        """测试抽象基类不能直接实例化。"""
        with pytest.raises(TypeError):
            LifeSmartClientBase()

    def test_mock_client_creation(self, mock_client):
        """测试模拟客户端的创建。"""
        assert mock_client is not None
        assert hasattr(mock_client, "_send_single_command")
        assert hasattr(mock_client, "_get_all_devices")


class TestClientBasePublicInterfaces:
    """测试客户端基类的公共接口方法。"""

    @pytest.mark.asyncio
    async def test_async_get_all_devices_interface(self, mock_client):
        """测试获取所有设备的公共接口。"""
        expected_devices = create_devices_by_category(["smart_plug"])
        mock_client._get_all_devices.return_value = expected_devices

        result = await mock_client.async_get_all_devices(timeout=15)

        assert result == expected_devices
        # 公共接口使用默认timeout
        mock_client._get_all_devices.assert_called_once_with(10)

    @pytest.mark.asyncio
    async def test_async_send_single_command_interface(self, mock_client):
        """测试发送单个命令的公共接口。"""
        from custom_components.lifesmart.const import CMD_TYPE_ON

        mock_client._send_single_command.return_value = 0

        result = await mock_client.async_send_single_command(
            "agt1", "dev1", "P1", CMD_TYPE_ON, 1
        )

        assert result == 0
        mock_client._send_single_command.assert_called_once_with(
            "agt1", "dev1", "P1", CMD_TYPE_ON, 1
        )

    @pytest.mark.asyncio
    async def test_async_send_multi_command_interface(self, mock_client):
        """测试发送多个命令的公共接口。"""
        io_list = [{"idx": "P1", "type": 0x81, "val": 1}]
        mock_client._send_multi_command.return_value = 0

        result = await mock_client.async_send_multi_command("agt1", "dev1", io_list)

        assert result == 0
        mock_client._send_multi_command.assert_called_once_with("agt1", "dev1", io_list)


class TestLightSwitchControl:
    """测试通用开关/灯光控制方法。"""

    @pytest.mark.asyncio
    async def test_turn_on_light_switch_async(self, mock_client):
        """测试开启灯光或开关。"""
        from custom_components.lifesmart.const import CMD_TYPE_ON

        result = await mock_client.turn_on_light_switch_async("P1", "agt1", "switch1")

        assert result == 0
        mock_client._send_single_command.assert_called_once_with(
            "agt1", "switch1", "P1", CMD_TYPE_ON, 1
        )

    @pytest.mark.asyncio
    async def test_turn_off_light_switch_async(self, mock_client):
        """测试关闭灯光或开关。"""
        from custom_components.lifesmart.const import CMD_TYPE_OFF

        result = await mock_client.turn_off_light_switch_async("P2", "agt1", "switch1")

        assert result == 0
        mock_client._send_single_command.assert_called_once_with(
            "agt1", "switch1", "P2", CMD_TYPE_OFF, 0
        )

    @pytest.mark.asyncio
    async def test_press_switch_async_basic_duration(self, mock_client):
        """测试点动操作的基本持续时间。"""
        from custom_components.lifesmart.const import CMD_TYPE_PRESS

        result = await mock_client.press_switch_async("P3", "agt1", "switch1", 500)

        assert result == 0
        # 500ms / 100 = 5
        mock_client._send_single_command.assert_called_once_with(
            "agt1", "switch1", "P3", CMD_TYPE_PRESS, 5
        )

    @pytest.mark.asyncio
    async def test_press_switch_async_minimum_duration(self, mock_client):
        """测试点动操作的最小持续时间处理。"""
        from custom_components.lifesmart.const import CMD_TYPE_PRESS

        result = await mock_client.press_switch_async("P1", "agt1", "switch1", 10)

        assert result == 0
        # max(1, round(10/100)) = max(1, 0) = 1
        mock_client._send_single_command.assert_called_once_with(
            "agt1", "switch1", "P1", CMD_TYPE_PRESS, 1
        )


class TestCoverControl:
    """测试窗帘/覆盖物控制方法。"""

    @pytest.mark.asyncio
    async def test_open_cover_garage_door(self, mock_client):
        """测试开启车库门类型的窗帘。"""
        from custom_components.lifesmart.const import (
            GARAGE_DOOR_TYPES,
            CMD_TYPE_SET_VAL,
        )

        garage_door_type = list(GARAGE_DOOR_TYPES)[0]

        result = await mock_client.open_cover_async("agt1", "cover1", garage_door_type)

        assert result == 0
        mock_client._send_single_command.assert_called_once_with(
            "agt1", "cover1", "P3", CMD_TYPE_SET_VAL, 100
        )

    @pytest.mark.asyncio
    async def test_open_cover_dooya_type(self, mock_client):
        """测试开启杜亚类型的窗帘。"""
        from custom_components.lifesmart.const import DOOYA_TYPES, CMD_TYPE_SET_VAL

        dooya_type = list(DOOYA_TYPES)[0]

        result = await mock_client.open_cover_async("agt1", "cover1", dooya_type)

        assert result == 0
        mock_client._send_single_command.assert_called_once_with(
            "agt1", "cover1", "P2", CMD_TYPE_SET_VAL, 100
        )

    @pytest.mark.asyncio
    async def test_open_cover_non_positional_type(self, mock_client):
        """测试开启非位置控制类型的窗帘。"""
        from custom_components.lifesmart.const import (
            NON_POSITIONAL_COVER_CONFIG,
            CMD_TYPE_ON,
        )

        with patch.dict(NON_POSITIONAL_COVER_CONFIG, {"TEST_COVER": {"open": "O1"}}):
            result = await mock_client.open_cover_async("agt1", "cover1", "TEST_COVER")

            assert result == 0
            mock_client._send_single_command.assert_called_once_with(
                "agt1", "cover1", "O1", CMD_TYPE_ON, 1
            )

    @pytest.mark.asyncio
    async def test_open_cover_unsupported_type(self, mock_client):
        """测试开启不支持的窗帘类型。"""
        with patch(
            "custom_components.lifesmart.core.client_base._LOGGER"
        ) as mock_logger:
            result = await mock_client.open_cover_async(
                "agt1", "cover1", "UNSUPPORTED_TYPE"
            )

            assert result == -1
            assert mock_logger.warning.called

    @pytest.mark.asyncio
    async def test_set_cover_position_garage_door(self, mock_client):
        """测试设置车库门类型窗帘的位置。"""
        from custom_components.lifesmart.const import (
            GARAGE_DOOR_TYPES,
            CMD_TYPE_SET_VAL,
        )

        garage_door_type = list(GARAGE_DOOR_TYPES)[0]

        result = await mock_client.set_cover_position_async(
            "agt1", "cover1", 75, garage_door_type
        )

        assert result == 0
        mock_client._send_single_command.assert_called_once_with(
            "agt1", "cover1", "P3", CMD_TYPE_SET_VAL, 75
        )


class TestClimateControl:
    """测试温控设备控制方法。"""

    @pytest.mark.asyncio
    async def test_set_climate_hvac_mode_off(self, mock_client):
        """测试设置HVAC模式为关闭。"""
        from homeassistant.components.climate import HVACMode
        from custom_components.lifesmart.const import CMD_TYPE_OFF

        result = await mock_client.async_set_climate_hvac_mode(
            "agt1", "climate1", "SL_NATURE", HVACMode.OFF
        )

        assert result == 0
        mock_client._send_single_command.assert_called_once_with(
            "agt1", "climate1", "P1", CMD_TYPE_OFF, 0
        )

    @pytest.mark.asyncio
    async def test_set_climate_temperature_v_air_p(self, mock_client):
        """测试设置V_AIR_P设备的温度。"""
        from custom_components.lifesmart.const import CMD_TYPE_SET_TEMP_DECIMAL

        result = await mock_client.async_set_climate_temperature(
            "agt1", "climate1", "V_AIR_P", 25.5
        )

        assert result == 0
        # 25.5 * 10 = 255
        mock_client._send_single_command.assert_called_once_with(
            "agt1", "climate1", "tT", CMD_TYPE_SET_TEMP_DECIMAL, 255
        )

    @pytest.mark.asyncio
    async def test_set_climate_temperature_unsupported_type(self, mock_client):
        """测试设置不支持设备类型的温度。"""
        result = await mock_client.async_set_climate_temperature(
            "agt1", "climate1", "UNSUPPORTED_TYPE", 25.0
        )

        assert result == -1
        assert not mock_client._send_single_command.called

    @pytest.mark.asyncio
    async def test_set_climate_fan_mode_unsupported_device(self, mock_client):
        """测试设置不支持设备类型的风扇模式。"""
        with patch(
            "custom_components.lifesmart.core.client_base._LOGGER"
        ) as mock_logger:
            result = await mock_client.async_set_climate_fan_mode(
                "agt1", "climate1", "UNSUPPORTED_TYPE", "auto"
            )

            assert result == -1
            assert mock_logger.warning.called
            assert not mock_client._send_single_command.called


class TestEdgeCasesAndErrorHandling:
    """测试边缘情况和错误处理。"""

    def test_safe_get_function_import(self):
        """测试safe_get函数的导入和使用。"""
        from custom_components.lifesmart.helpers import safe_get

        test_dict = {"level1": {"level2": {"value": "test"}}}
        result = safe_get(test_dict, "level1", "level2", "value")
        assert result == "test"

        result = safe_get(test_dict, "nonexistent", default="default_value")
        assert result == "default_value"

    @pytest.mark.asyncio
    async def test_climate_fan_mode_none_values(self, mock_client):
        """测试风扇模式映射返回None值的情况。"""
        from custom_components.lifesmart.const import LIFESMART_F_FAN_MAP

        with patch.dict(LIFESMART_F_FAN_MAP, {}, clear=True):
            with patch(
                "custom_components.lifesmart.core.client_base._LOGGER"
            ) as mock_logger:
                result = await mock_client.async_set_climate_fan_mode(
                    "agt1", "climate1", "V_AIR_P", "auto"
                )

                assert result == -1
                assert mock_logger.warning.called
                assert not mock_client._send_single_command.called


class TestDeviceControlWithFactoryDevices:
    """使用工厂函数创建的设备测试控制逻辑。"""

    @pytest.mark.asyncio
    async def test_switch_control_with_factory_switch(self, mock_client):
        """使用工厂函数创建的开关设备测试控制。"""
        from custom_components.lifesmart.const import CMD_TYPE_ON

        # 获取工厂函数创建的开关设备
        switch_devices = create_devices_by_category(["smart_plug"])
        assert len(switch_devices) > 0

        test_switch = switch_devices[0]
        agt = test_switch["agt"]
        me = test_switch["me"]

        result = await mock_client.turn_on_light_switch_async("O", agt, me)

        assert result == 0
        mock_client._send_single_command.assert_called_once_with(
            agt, me, "O", CMD_TYPE_ON, 1
        )

    @pytest.mark.asyncio
    async def test_climate_control_with_factory_climate(self, mock_client):
        """使用工厂函数创建的温控设备测试控制。"""
        from homeassistant.components.climate import HVACMode

        # 获取工厂函数创建的温控设备
        climate_devices = create_devices_by_category(["climate"])
        assert len(climate_devices) > 0

        test_climate = climate_devices[0]
        agt = test_climate["agt"]
        me = test_climate["me"]
        devtype = test_climate["devtype"]

        result = await mock_client.async_set_climate_hvac_mode(
            agt, me, devtype, HVACMode.OFF
        )

        assert result == 0
        # 验证调用参数，根据设备类型确定IO口
        mock_client._send_single_command.assert_called_once()


class TestMockClientIntegration:
    """测试Mock客户端集成功能。"""

    def test_failed_client_creation(self):
        """测试失败客户端的创建。"""
        failed_client = create_mock_failed_oapi_client()

        assert failed_client._mock_get_all_devices.side_effect is not None
        assert failed_client._mock_refresh_token.return_value is False

    def test_successful_client_creation(self):
        """测试成功客户端的创建。"""
        success_client = create_mock_oapi_client()

        assert success_client._mock_get_all_devices.return_value == []
        assert success_client._mock_refresh_token.return_value is True
