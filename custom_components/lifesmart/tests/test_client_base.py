"""
针对 LifeSmart 客户端基类 (client_base.py) 的单元测试。

此测试套件专注于验证抽象基类 LifeSmartClientBase 的核心功能，包括：
- 设备控制业务逻辑的准确性（灯光、窗帘、温控等）
- 不同设备类型的特殊处理逻辑
- 错误处理和边界条件的处理

使用纯Python执行的方式，避免pytest-homeassistant-custom-component插件冲突。
"""

import asyncio
import sys
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

from custom_components.lifesmart.core.client_base import LifeSmartClientBase


def run_test_safe(test_name, test_func):
    """安全运行测试函数"""
    try:
        if asyncio.iscoroutinefunction(test_func):
            asyncio.run(test_func())
        else:
            test_func()
        print(f"✓ {test_name}")
        return True
    except Exception as e:
        print(f"✗ {test_name}: {e}")
        return False


class MockLifeSmartClient(LifeSmartClientBase):
    """用于测试的具体客户端实现，模拟所有抽象方法。"""

    def __init__(self):
        # 为每个抽象方法创建模拟
        self._mock_get_all_devices = AsyncMock(return_value=[])
        self._mock_send_single_command = AsyncMock(return_value=0)
        self._mock_send_multi_command = AsyncMock(return_value=0)
        self._mock_set_scene = AsyncMock(return_value=0)
        self._mock_send_ir_key = AsyncMock(return_value=0)
        self._mock_add_scene = AsyncMock(return_value=0)
        self._mock_delete_scene = AsyncMock(return_value=0)
        self._mock_get_scene_list = AsyncMock(return_value=[])
        self._mock_get_room_list = AsyncMock(return_value=[])
        self._mock_get_hub_list = AsyncMock(return_value=[])
        self._mock_change_device_icon = AsyncMock(return_value=0)
        self._mock_set_device_eeprom = AsyncMock(return_value=0)
        self._mock_add_device_timer = AsyncMock(return_value=0)
        self._mock_ir_control = AsyncMock(return_value=0)
        self._mock_send_ir_code = AsyncMock(return_value=0)
        self._mock_ir_raw_control = AsyncMock(return_value=0)
        self._mock_get_ir_remote_list = AsyncMock(return_value={})

    async def _async_get_all_devices(self, timeout=10) -> List[Dict[str, Any]]:
        return await self._mock_get_all_devices(timeout)

    async def _async_send_single_command(self, agt: str, me: str, idx: str, command_type: int, val: Any) -> int:
        return await self._mock_send_single_command(agt, me, idx, command_type, val)

    async def _async_send_multi_command(self, agt: str, me: str, io_list: List[Dict]) -> int:
        return await self._mock_send_multi_command(agt, me, io_list)

    async def _async_set_scene(self, agt: str, scene_name: str) -> int:
        return await self._mock_set_scene(agt, scene_name)

    async def _async_send_ir_key(
        self, agt: str, me: str, category: str, brand: str, keys: str, ai: str = "", idx: str = ""
    ) -> int:
        return await self._mock_send_ir_key(agt, me, category, brand, keys, ai, idx)

    async def _async_add_scene(self, agt: str, scene_name: str, actions: str) -> int:
        return await self._mock_add_scene(agt, scene_name, actions)

    async def _async_delete_scene(self, agt: str, scene_name: str) -> int:
        return await self._mock_delete_scene(agt, scene_name)

    async def _async_get_scene_list(self, agt: str) -> List[Dict[str, Any]]:
        return await self._mock_get_scene_list(agt)

    async def _async_get_room_list(self, agt: str) -> List[Dict[str, Any]]:
        return await self._mock_get_room_list(agt)

    async def _async_get_hub_list(self) -> List[Dict[str, Any]]:
        return await self._mock_get_hub_list()

    async def _async_change_device_icon(self, device_id: str, icon: str) -> int:
        return await self._mock_change_device_icon(device_id, icon)

    async def _async_set_device_eeprom(self, device_id: str, key: str, value: Any) -> int:
        return await self._mock_set_device_eeprom(device_id, key, value)

    async def _async_add_device_timer(self, device_id: str, cron_info: str, key: str) -> int:
        return await self._mock_add_device_timer(device_id, cron_info, key)

    async def _async_ir_control(self, device_id: str, options: Dict) -> int:
        return await self._mock_ir_control(device_id, options)

    async def _async_send_ir_code(self, device_id: str, ir_data: List | bytes) -> int:
        return await self._mock_send_ir_code(device_id, ir_data)

    async def _async_ir_raw_control(self, device_id: str, raw_data: str) -> int:
        return await self._mock_ir_raw_control(device_id, raw_data)

    async def _async_get_ir_remote_list(self, agt: str) -> Dict[str, Any]:
        return await self._mock_get_ir_remote_list(agt)


# ==================== 测试类定义 ====================


class TestConstantsImport:
    """测试常量导入功能。"""

    def test_command_type_constants(self):
        """测试命令类型常量的导入。"""
        from custom_components.lifesmart.const import (
            CMD_TYPE_ON,
            CMD_TYPE_OFF,
            CMD_TYPE_PRESS,
            CMD_TYPE_SET_VAL,
            CMD_TYPE_SET_CONFIG,
            CMD_TYPE_SET_TEMP_DECIMAL,
            CMD_TYPE_SET_RAW,
            CMD_TYPE_SET_TEMP_FCU,
        )

        assert CMD_TYPE_ON is not None, "CMD_TYPE_ON 常量应该存在"
        assert CMD_TYPE_OFF is not None, "CMD_TYPE_OFF 常量应该存在"
        assert CMD_TYPE_PRESS is not None, "CMD_TYPE_PRESS 常量应该存在"
        assert CMD_TYPE_SET_VAL is not None, "CMD_TYPE_SET_VAL 常量应该存在"
        assert CMD_TYPE_SET_CONFIG is not None, "CMD_TYPE_SET_CONFIG 常量应该存在"
        assert CMD_TYPE_SET_TEMP_DECIMAL is not None, "CMD_TYPE_SET_TEMP_DECIMAL 常量应该存在"
        assert CMD_TYPE_SET_RAW is not None, "CMD_TYPE_SET_RAW 常量应该存在"
        assert CMD_TYPE_SET_TEMP_FCU is not None, "CMD_TYPE_SET_TEMP_FCU 常量应该存在"

    def test_device_type_constants(self):
        """测试设备类型常量的导入。"""
        from custom_components.lifesmart.const import (
            DOOYA_TYPES,
            GARAGE_DOOR_TYPES,
            NON_POSITIONAL_COVER_CONFIG,
        )

        assert DOOYA_TYPES is not None, "DOOYA_TYPES 常量应该存在"
        assert GARAGE_DOOR_TYPES is not None, "GARAGE_DOOR_TYPES 常量应该存在"
        assert NON_POSITIONAL_COVER_CONFIG is not None, "NON_POSITIONAL_COVER_CONFIG 常量应该存在"

    def test_hvac_mode_mapping_constants(self):
        """测试HVAC模式映射常量的导入。"""
        from custom_components.lifesmart.const import (
            REVERSE_F_HVAC_MODE_MAP,
            REVERSE_LIFESMART_HVAC_MODE_MAP,
            REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP,
        )

        assert REVERSE_F_HVAC_MODE_MAP is not None, "REVERSE_F_HVAC_MODE_MAP 常量应该存在"
        assert REVERSE_LIFESMART_HVAC_MODE_MAP is not None, "REVERSE_LIFESMART_HVAC_MODE_MAP 常量应该存在"
        assert REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP is not None, "REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP 常量应该存在"

    def test_fan_mode_mapping_constants(self):
        """测试风扇模式映射常量的导入。"""
        from custom_components.lifesmart.const import (
            LIFESMART_F_FAN_MAP,
            LIFESMART_TF_FAN_MAP,
            LIFESMART_ACIPM_FAN_MAP,
            LIFESMART_CP_AIR_FAN_MAP,
        )

        assert LIFESMART_F_FAN_MAP is not None, "LIFESMART_F_FAN_MAP 常量应该存在"
        assert LIFESMART_TF_FAN_MAP is not None, "LIFESMART_TF_FAN_MAP 常量应该存在"
        assert LIFESMART_ACIPM_FAN_MAP is not None, "LIFESMART_ACIPM_FAN_MAP 常量应该存在"
        assert LIFESMART_CP_AIR_FAN_MAP is not None, "LIFESMART_CP_AIR_FAN_MAP 常量应该存在"


class TestAbstractBaseClass:
    """测试抽象基类行为。"""

    def test_abstract_methods_cannot_be_instantiated(self):
        """测试抽象基类不能直接实例化。"""
        try:
            LifeSmartClientBase()
            assert False, "抽象基类不应该能够直接实例化"
        except TypeError:
            pass  # 期望的行为

    def test_mock_client_creation(self):
        """测试模拟客户端的创建。"""
        mock_client = MockLifeSmartClient()
        assert mock_client is not None, "模拟客户端应该能够成功创建"
        assert hasattr(mock_client, "_mock_get_all_devices"), "模拟客户端应该包含_mock_get_all_devices属性"
        assert hasattr(mock_client, "_mock_send_single_command"), "模拟客户端应该包含_mock_send_single_command属性"


class TestClientBasePublicInterfaces:
    """测试客户端基类的公共接口方法。"""

    async def test_async_get_all_devices_interface(self):
        """测试获取所有设备的公共接口。"""
        mock_client = MockLifeSmartClient()
        expected_devices = [{"me": "device1", "name": "Test Device"}]
        mock_client._mock_get_all_devices.return_value = expected_devices

        result = await mock_client.async_get_all_devices(timeout=15)

        assert result == expected_devices, "返回的设备列表应该与预期一致"
        # 注意：公共接口不会传递timeout参数，它使用默认的内部超时时间
        mock_client._mock_get_all_devices.assert_called_once_with(10)

    async def test_async_send_single_command_interface(self):
        """测试发送单个命令的公共接口。"""
        from custom_components.lifesmart.const import CMD_TYPE_ON

        mock_client = MockLifeSmartClient()
        mock_client._mock_send_single_command.return_value = 0

        result = await mock_client.async_send_single_command("agt1", "dev1", "P1", CMD_TYPE_ON, 1)

        assert result == 0, "命令发送应该返回成功状态码"
        mock_client._mock_send_single_command.assert_called_once_with("agt1", "dev1", "P1", CMD_TYPE_ON, 1)

    async def test_async_send_multi_command_interface(self):
        """测试发送多个命令的公共接口。"""
        mock_client = MockLifeSmartClient()
        io_list = [{"idx": "P1", "type": 0x81, "val": 1}]
        mock_client._mock_send_multi_command.return_value = 0

        result = await mock_client.async_send_multi_command("agt1", "dev1", io_list)

        assert result == 0, "多命令发送应该返回成功状态码"
        mock_client._mock_send_multi_command.assert_called_once_with("agt1", "dev1", io_list)


class TestLightSwitchControl:
    """测试通用开关/灯光控制方法。"""

    async def test_turn_on_light_switch_async(self):
        """测试开启灯光或开关。"""
        from custom_components.lifesmart.const import CMD_TYPE_ON

        mock_client = MockLifeSmartClient()
        mock_client._mock_send_single_command.return_value = 0

        result = await mock_client.turn_on_light_switch_async("P1", "agt1", "switch1")

        assert result == 0, "开启灯光开关应该返回成功状态码"
        mock_client._mock_send_single_command.assert_called_once_with("agt1", "switch1", "P1", CMD_TYPE_ON, 1)

    async def test_turn_off_light_switch_async(self):
        """测试关闭灯光或开关。"""
        from custom_components.lifesmart.const import CMD_TYPE_OFF

        mock_client = MockLifeSmartClient()
        mock_client._mock_send_single_command.return_value = 0

        result = await mock_client.turn_off_light_switch_async("P2", "agt1", "switch1")

        assert result == 0, "关闭灯光开关应该返回成功状态码"
        mock_client._mock_send_single_command.assert_called_once_with("agt1", "switch1", "P2", CMD_TYPE_OFF, 0)

    async def test_press_switch_async_basic_duration(self):
        """测试点动操作的基本持续时间。"""
        from custom_components.lifesmart.const import CMD_TYPE_PRESS

        mock_client = MockLifeSmartClient()
        mock_client._mock_send_single_command.return_value = 0

        result = await mock_client.press_switch_async("P3", "agt1", "switch1", 500)

        assert result == 0, "点动操作应该返回成功状态码"
        # 500ms / 100 = 5
        mock_client._mock_send_single_command.assert_called_once_with("agt1", "switch1", "P3", CMD_TYPE_PRESS, 5)

    async def test_press_switch_async_minimum_duration(self):
        """测试点动操作的最小持续时间处理。"""
        from custom_components.lifesmart.const import CMD_TYPE_PRESS

        mock_client = MockLifeSmartClient()
        mock_client._mock_send_single_command.return_value = 0

        result = await mock_client.press_switch_async("P1", "agt1", "switch1", 50)

        assert result == 0, "最小持续时间的点动操作应该返回成功状态码"
        # max(1, round(50/100)) = max(1, 1) = 1
        mock_client._mock_send_single_command.assert_called_once_with("agt1", "switch1", "P1", CMD_TYPE_PRESS, 1)

    async def test_press_switch_async_very_short_duration(self):
        """测试点动操作的极短持续时间处理。"""
        from custom_components.lifesmart.const import CMD_TYPE_PRESS

        mock_client = MockLifeSmartClient()
        mock_client._mock_send_single_command.return_value = 0

        result = await mock_client.press_switch_async("P1", "agt1", "switch1", 10)

        assert result == 0, "极短持续时间的点动操作应该返回成功状态码"
        # max(1, round(10/100)) = max(1, 0) = 1，确保最小值为1
        mock_client._mock_send_single_command.assert_called_once_with("agt1", "switch1", "P1", CMD_TYPE_PRESS, 1)


class TestCoverControl:
    """测试窗帘/覆盖物控制方法。"""

    async def test_open_cover_garage_door(self):
        """测试开启车库门类型的窗帘。"""
        from custom_components.lifesmart.const import GARAGE_DOOR_TYPES, CMD_TYPE_SET_VAL

        mock_client = MockLifeSmartClient()
        mock_client._mock_send_single_command.return_value = 0
        garage_door_type = list(GARAGE_DOOR_TYPES)[0]  # 获取第一个车库门类型

        result = await mock_client.open_cover_async("agt1", "cover1", garage_door_type)

        assert result == 0, "开启车库门应该返回成功状态码"
        mock_client._mock_send_single_command.assert_called_once_with("agt1", "cover1", "P3", CMD_TYPE_SET_VAL, 100)

    async def test_open_cover_dooya_type(self):
        """测试开启杜亚类型的窗帘。"""
        from custom_components.lifesmart.const import DOOYA_TYPES, CMD_TYPE_SET_VAL

        mock_client = MockLifeSmartClient()
        mock_client._mock_send_single_command.return_value = 0
        dooya_type = list(DOOYA_TYPES)[0]  # 获取第一个杜亚类型

        result = await mock_client.open_cover_async("agt1", "cover1", dooya_type)

        assert result == 0, "开启杜亚窗帘应该返回成功状态码"
        mock_client._mock_send_single_command.assert_called_once_with("agt1", "cover1", "P2", CMD_TYPE_SET_VAL, 100)

    async def test_open_cover_non_positional_type(self):
        """测试开启非位置控制类型的窗帘。"""
        from custom_components.lifesmart.const import NON_POSITIONAL_COVER_CONFIG, CMD_TYPE_ON

        mock_client = MockLifeSmartClient()
        mock_client._mock_send_single_command.return_value = 0

        # 模拟NON_POSITIONAL_COVER_CONFIG中的配置
        with patch.dict(NON_POSITIONAL_COVER_CONFIG, {"TEST_COVER": {"open": "O1"}}):
            result = await mock_client.open_cover_async("agt1", "cover1", "TEST_COVER")

            assert result == 0, "开启非位置控制窗帘应该返回成功状态码"
            mock_client._mock_send_single_command.assert_called_once_with("agt1", "cover1", "O1", CMD_TYPE_ON, 1)

    async def test_open_cover_unsupported_type(self):
        """测试开启不支持的窗帘类型。"""
        mock_client = MockLifeSmartClient()

        with patch("custom_components.lifesmart.core.client_base._LOGGER") as mock_logger:
            result = await mock_client.open_cover_async("agt1", "cover1", "UNSUPPORTED_TYPE")

            assert result == -1, "不支持的窗帘类型应该返回错误状态码"
            assert mock_logger.warning.called, "应该记录警告信息"

    async def test_close_cover_garage_door(self):
        """测试关闭车库门类型的窗帘。"""
        from custom_components.lifesmart.const import GARAGE_DOOR_TYPES, CMD_TYPE_SET_VAL

        mock_client = MockLifeSmartClient()
        mock_client._mock_send_single_command.return_value = 0
        garage_door_type = list(GARAGE_DOOR_TYPES)[0]

        result = await mock_client.close_cover_async("agt1", "cover1", garage_door_type)

        assert result == 0, "关闭车库门应该返回成功状态码"
        mock_client._mock_send_single_command.assert_called_once_with("agt1", "cover1", "P3", CMD_TYPE_SET_VAL, 0)

    async def test_set_cover_position_garage_door(self):
        """测试设置车库门类型窗帘的位置。"""
        from custom_components.lifesmart.const import GARAGE_DOOR_TYPES, CMD_TYPE_SET_VAL

        mock_client = MockLifeSmartClient()
        mock_client._mock_send_single_command.return_value = 0
        garage_door_type = list(GARAGE_DOOR_TYPES)[0]

        result = await mock_client.set_cover_position_async("agt1", "cover1", 75, garage_door_type)

        assert result == 0, "设置车库门位置应该返回成功状态码"
        mock_client._mock_send_single_command.assert_called_once_with("agt1", "cover1", "P3", CMD_TYPE_SET_VAL, 75)

    async def test_set_cover_position_unsupported_type(self):
        """测试设置不支持位置控制的窗帘类型。"""
        mock_client = MockLifeSmartClient()

        with patch("custom_components.lifesmart.core.client_base._LOGGER") as mock_logger:
            result = await mock_client.set_cover_position_async("agt1", "cover1", 50, "UNSUPPORTED_TYPE")

            assert result == -1, "不支持位置控制的窗帘类型应该返回错误状态码"
            assert mock_logger.warning.called, "应该记录警告信息"


class TestClimateControl:
    """测试温控设备控制方法。"""

    async def test_set_climate_hvac_mode_off(self):
        """测试设置HVAC模式为关闭。"""
        from homeassistant.components.climate import HVACMode
        from custom_components.lifesmart.const import CMD_TYPE_OFF

        mock_client = MockLifeSmartClient()
        mock_client._mock_send_single_command.return_value = 0

        result = await mock_client.async_set_climate_hvac_mode("agt1", "climate1", "SL_NATURE", HVACMode.OFF)

        assert result == 0, "设置HVAC模式为关闭应该返回成功状态码"
        mock_client._mock_send_single_command.assert_called_once_with("agt1", "climate1", "P1", CMD_TYPE_OFF, 0)

    async def test_set_climate_temperature_v_air_p(self):
        """测试设置V_AIR_P设备的温度。"""
        from custom_components.lifesmart.const import CMD_TYPE_SET_TEMP_DECIMAL

        mock_client = MockLifeSmartClient()
        mock_client._mock_send_single_command.return_value = 0

        result = await mock_client.async_set_climate_temperature("agt1", "climate1", "V_AIR_P", 25.5)

        assert result == 0, "设置V_AIR_P设备温度应该返回成功状态码"
        # 25.5 * 10 = 255
        mock_client._mock_send_single_command.assert_called_once_with(
            "agt1", "climate1", "tT", CMD_TYPE_SET_TEMP_DECIMAL, 255
        )

    async def test_set_climate_temperature_unsupported_type(self):
        """测试设置不支持设备类型的温度。"""
        mock_client = MockLifeSmartClient()

        result = await mock_client.async_set_climate_temperature("agt1", "climate1", "UNSUPPORTED_TYPE", 25.0)

        assert result == -1, "不支持的设备类型应该返回错误状态码"
        assert not mock_client._mock_send_single_command.called, "不应该调用发送命令方法"

    async def test_set_climate_fan_mode_unsupported_device(self):
        """测试设置不支持设备类型的风扇模式。"""
        mock_client = MockLifeSmartClient()

        with patch("custom_components.lifesmart.core.client_base._LOGGER") as mock_logger:
            result = await mock_client.async_set_climate_fan_mode("agt1", "climate1", "UNSUPPORTED_TYPE", "auto")

            assert result == -1, "不支持的风扇模式设备类型应该返回错误状态码"
            assert mock_logger.warning.called, "应该记录警告信息"
            assert not mock_client._mock_send_single_command.called, "不应该调用发送命令方法"


class TestClientBaseEdgeCases:
    """测试客户端基类的边缘情况和错误处理。"""

    def test_safe_get_function_import(self):
        """测试safe_get函数的导入和使用。"""
        from custom_components.lifesmart.helpers import safe_get

        test_dict = {"level1": {"level2": {"value": "test"}}}
        result = safe_get(test_dict, "level1", "level2", "value")
        assert result == "test", "safe_get应该能够正确获取嵌套字典的值"

        # 测试默认值
        result = safe_get(test_dict, "nonexistent", default="default_value")
        assert result == "default_value", "safe_get应该在键不存在时返回默认值"

    async def test_climate_fan_mode_none_values(self):
        """测试风扇模式映射返回None值的情况。"""
        from custom_components.lifesmart.const import LIFESMART_F_FAN_MAP

        mock_client = MockLifeSmartClient()

        with patch.dict(LIFESMART_F_FAN_MAP, {}, clear=True):
            with patch("custom_components.lifesmart.core.client_base._LOGGER") as mock_logger:
                result = await mock_client.async_set_climate_fan_mode("agt1", "climate1", "V_AIR_P", "auto")

                assert result == -1, "没有映射的风扇模式应该返回错误状态码"
                assert mock_logger.warning.called, "应该记录警告信息"
                assert not mock_client._mock_send_single_command.called, "不应该调用发送命令方法"


def main():
    """运行所有测试的主函数。"""
    print("运行 LifeSmart 客户端基类测试...")
    print("=" * 50)

    test_classes = [
        TestConstantsImport(),
        TestAbstractBaseClass(),
        TestClientBasePublicInterfaces(),
        TestLightSwitchControl(),
        TestCoverControl(),
        TestClimateControl(),
        TestClientBaseEdgeCases(),
    ]

    total_tests = 0
    passed_tests = 0

    for test_class in test_classes:
        class_name = test_class.__class__.__name__
        print(f"\n--- {class_name} ---")

        # 获取测试方法
        test_methods = [method for method in dir(test_class) if method.startswith("test_")]

        for method_name in test_methods:
            test_method = getattr(test_class, method_name)
            test_display_name = f"{class_name}.{method_name}"

            total_tests += 1
            if run_test_safe(test_display_name, test_method):
                passed_tests += 1

    print("=" * 50)
    print(f"测试完成: {passed_tests}/{total_tests} 通过")

    if passed_tests == total_tests:
        print("✓ 所有测试通过!")
        return 0
    else:
        print("✗ 部分测试失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
