"""
测试 helpers 模块的所有辅助函数。

此测试文件专门测试 helpers.py 中的通用辅助函数，利用 conftest.py 中的现有测试数据。
覆盖范围包括：
- safe_get: 安全数据访问
- 设备类型检查函数: is_switch, is_light, is_cover, is_binary_sensor, is_sensor, is_climate
- find_test_device: 测试辅助函数

注意：generate_unique_id 和 normalize_device_names 已在其他测试文件中覆盖，此处不重复测试。
"""

import pytest

from custom_components.lifesmart.helpers import (
    get_switch_subdevices,
    get_binary_sensor_subdevices,
    get_cover_subdevices,
    get_sensor_subdevices,
    get_light_subdevices,
    is_binary_sensor,
    is_binary_sensor_subdevice,
    is_climate,
    is_cover,
    is_cover_subdevice,
    is_light,
    is_light_subdevice,
    is_sensor,
    is_sensor_subdevice,
    is_switch,
    is_switch_subdevice,
    safe_get,
)
from .test_utils import find_test_device


class TestSafeGet:
    """测试 safe_get 函数的所有场景。"""

    def test_dict_access_success(self):
        """测试字典访问成功的情况。"""
        data = {"a": {"b": {"c": "value"}}}
        assert safe_get(data, "a", "b", "c") == "value"

    def test_dict_access_missing_key(self):
        """测试字典访问键不存在的情况。"""
        data = {"a": {"b": {}}}
        assert safe_get(data, "a", "b", "missing") is None
        assert safe_get(data, "a", "b", "missing", default="default") == "default"

    def test_list_access_success(self):
        """测试列表访问成功的情况。"""
        data = [1, [2, [3, "value"]]]
        assert safe_get(data, 1, 1, 0) == 3

    def test_list_access_index_error(self):
        """测试列表访问索引超出范围的情况。"""
        data = [1, 2, 3]
        assert safe_get(data, 10) is None
        assert safe_get(data, 10, default="default") == "default"

    def test_mixed_access(self):
        """测试字典和列表混合访问。"""
        data = {"items": [{"name": "item1"}, {"name": "item2"}]}
        assert safe_get(data, "items", 1, "name") == "item2"

    def test_invalid_path_type(self):
        """测试无效的路径类型。"""
        data = {"a": "string"}
        # 尝试在字符串上使用键访问
        assert safe_get(data, "a", "invalid") is None
        # 尝试在字典上使用整数索引
        assert safe_get({"a": "value"}, 0) is None

    def test_none_data(self):
        """测试传入None数据的情况。"""
        assert safe_get(None, "key") is None


class TestDeviceTypeCheckers:
    """测试设备类型检查函数，使用 conftest.py 中的真实设备数据。"""

    def test_is_switch_with_real_devices(self, mock_lifesmart_devices):
        """使用真实设备数据测试 is_switch 函数。"""
        devices = mock_lifesmart_devices

        # 标准三路开关
        sw_if3 = find_test_device(devices, "sw_if3")
        assert is_switch(sw_if3) is True

        # 智能插座
        sw_ol = find_test_device(devices, "sw_ol")
        assert is_switch(sw_ol) is True

        # 超能面板开关版 (P5=1)
        sw_nature = find_test_device(devices, "sw_nature")
        assert is_switch(sw_nature) is True

        # 通用控制器开关模式 (Mode 8)
        generic_switch = find_test_device(devices, "generic_p_switch_mode")
        assert is_switch(generic_switch) is True

        # 九路开关控制器
        sw_p9 = find_test_device(devices, "sw_p9")
        assert is_switch(sw_p9) is True

    def test_is_light_with_real_devices(self, mock_lifesmart_devices):
        """使用真实设备数据测试 is_light 函数。"""
        devices = mock_lifesmart_devices

        # 亮度灯
        light_bright = find_test_device(devices, "light_bright")
        assert is_light(light_bright) is True

        # 调光灯
        light_dimmer = find_test_device(devices, "light_dimmer")
        assert is_light(light_dimmer) is True

        # 量子灯
        light_quantum = find_test_device(devices, "light_quantum")
        assert is_light(light_quantum) is True

        # RGB灯
        light_singlergb = find_test_device(devices, "light_singlergb")
        assert is_light(light_singlergb) is True

        # RGBW灯
        light_dualrgbw = find_test_device(devices, "light_dualrgbw")
        assert is_light(light_dualrgbw) is True

    def test_is_cover_with_real_devices(self, mock_lifesmart_devices):
        """使用真实设备数据测试 is_cover 函数。"""
        devices = mock_lifesmart_devices

        # 车库门
        cover_garage = find_test_device(devices, "cover_garage")
        assert is_cover(cover_garage) is True

        # 杜亚窗帘
        cover_dooya = find_test_device(devices, "cover_dooya")
        assert is_cover(cover_dooya) is True

        # 非定位窗帘
        cover_nonpos = find_test_device(devices, "cover_nonpos")
        assert is_cover(cover_nonpos) is True

        # 通用控制器窗帘模式
        cover_generic = find_test_device(devices, "cover_generic")
        assert is_cover(cover_generic) is True

    def test_is_binary_sensor_with_real_devices(self, mock_lifesmart_devices):
        """使用真实设备数据测试 is_binary_sensor 函数。"""
        devices = mock_lifesmart_devices

        # 门磁传感器
        bs_door = find_test_device(devices, "bs_door")
        assert is_binary_sensor(bs_door) is True

        # 运动传感器
        bs_motion = find_test_device(devices, "bs_motion")
        assert is_binary_sensor(bs_motion) is True

        # 水浸传感器
        bs_water = find_test_device(devices, "bs_water")
        assert is_binary_sensor(bs_water) is True

        # 智能锁
        bs_lock = find_test_device(devices, "bs_lock")
        assert is_binary_sensor(bs_lock) is True

        # 烟雾传感器
        bs_smoke = find_test_device(devices, "bs_smoke")
        assert is_binary_sensor(bs_smoke) is True

    def test_is_sensor_with_real_devices(self, mock_lifesmart_devices):
        """使用真实设备数据测试 is_sensor 函数。"""
        devices = mock_lifesmart_devices

        # 环境传感器
        sensor_env = find_test_device(devices, "sensor_env")
        assert is_sensor(sensor_env) is True

        # CO2传感器
        sensor_co2 = find_test_device(devices, "sensor_co2")
        assert is_sensor(sensor_co2) is True

        # 功率计量插座传感器
        sensor_power_plug = find_test_device(devices, "sensor_power_plug")
        assert is_sensor(sensor_power_plug) is True

        # 锁电池传感器
        sensor_lock_battery = find_test_device(devices, "sensor_lock_battery")
        assert is_sensor(sensor_lock_battery) is True

        # 超能面板温控版 (P5=3) 会产生温度传感器
        climate_nature_thermo = find_test_device(devices, "climate_nature_thermo")
        assert is_sensor(climate_nature_thermo) is True

    def test_is_climate_with_real_devices(self, mock_lifesmart_devices):
        """使用真实设备数据测试 is_climate 函数。"""
        devices = mock_lifesmart_devices

        # 超能面板温控版
        climate_nature_thermo = find_test_device(devices, "climate_nature_thermo")
        assert is_climate(climate_nature_thermo) is True

        # 地暖
        climate_floor_heat = find_test_device(devices, "climate_floor_heat")
        assert is_climate(climate_floor_heat) is True

        # 风机盘管
        climate_fancoil = find_test_device(devices, "climate_fancoil")
        assert is_climate(climate_fancoil) is True

        # 空调面板
        climate_airpanel = find_test_device(devices, "climate_airpanel")
        assert is_climate(climate_airpanel) is True

        # 空调系统
        climate_airsystem = find_test_device(devices, "climate_airsystem")
        assert is_climate(climate_airsystem) is True

    def test_device_type_edge_cases(self):
        """测试设备类型检查的边缘情况。"""
        # 空设备
        empty_device = {}
        assert is_switch(empty_device) is False
        assert is_light(empty_device) is False
        assert is_cover(empty_device) is False
        assert is_binary_sensor(empty_device) is False
        assert is_sensor(empty_device) is False
        assert is_climate(empty_device) is False

        # 无效设备类型
        invalid_device = {"devtype": "INVALID_TYPE"}
        assert is_switch(invalid_device) is False
        assert is_light(invalid_device) is False
        assert is_cover(invalid_device) is False
        assert is_binary_sensor(invalid_device) is False
        assert is_sensor(invalid_device) is False
        assert is_climate(invalid_device) is False

    def test_generic_controller_work_modes(self):
        """测试通用控制器不同工作模式的判断。"""
        # 测试通用控制器的不同工作模式
        base_device = {"devtype": "SL_P", "data": {"P1": {"val": 0}}}

        # 模式0: 自由模式 - 应该是二进制传感器
        base_device["data"]["P1"]["val"] = 0 << 24
        assert is_binary_sensor(base_device) is True
        assert is_switch(base_device) is False
        assert is_cover(base_device) is False

        # 模式2: 二线窗帘 - 应该是窗帘
        base_device["data"]["P1"]["val"] = 2 << 24
        assert is_cover(base_device) is True
        assert is_switch(base_device) is False
        assert is_binary_sensor(base_device) is False

        # 模式4: 三线窗帘 - 应该是窗帘
        base_device["data"]["P1"]["val"] = 4 << 24
        assert is_cover(base_device) is True
        assert is_switch(base_device) is False
        assert is_binary_sensor(base_device) is False

        # 模式8: 三路开关 - 应该是开关
        base_device["data"]["P1"]["val"] = 8 << 24
        assert is_switch(base_device) is True
        assert is_cover(base_device) is False
        assert is_binary_sensor(base_device) is False

        # 模式10: 三路开关(新) - 应该是开关
        base_device["data"]["P1"]["val"] = 10 << 24
        assert is_switch(base_device) is True
        assert is_cover(base_device) is False
        assert is_binary_sensor(base_device) is False

    def test_nature_panel_modes(self):
        """测试超能面板不同模式的判断。"""
        # 基础超能面板设备
        base_device = {"devtype": "SL_NATURE", "data": {"P5": {"val": 1}}}

        # 注意：根据helpers.py的实际逻辑，SL_NATURE在ALL_SWITCH_TYPES中
        # 所以is_switch()对SL_NATURE总是返回True，不管P5值如何
        # 而is_climate()和is_sensor()会根据P5值判断

        # P5=1: 开关模式
        base_device["data"]["P5"]["val"] = 1
        assert is_switch(base_device) is True  # SL_NATURE总是开关
        assert is_sensor(base_device) is False  # P5=1不是温控版
        assert is_climate(base_device) is False  # P5=1不是温控版

        # P5=3: 温控模式 - 仍然是开关，但也是温控和传感器
        base_device["data"]["P5"]["val"] = 3
        assert is_switch(base_device) is True  # SL_NATURE总是开关
        assert is_climate(base_device) is True  # P5=3是温控版
        assert is_sensor(base_device) is True  # P5=3是温控版，产生传感器

        # 测试位掩码处理: P5=0x0103 & 0xFF = 3
        base_device["data"]["P5"]["val"] = 0x0103
        assert is_switch(base_device) is True  # SL_NATURE总是开关
        assert is_climate(base_device) is True  # P5&0xFF=3是温控版
        assert is_sensor(base_device) is True  # P5&0xFF=3是温控版，产生传感器


class TestFindTestDevice:
    """测试 find_test_device 函数。"""

    def test_find_existing_device(self, mock_lifesmart_devices):
        """测试查找存在的设备。"""
        devices = mock_lifesmart_devices

        # 查找开关设备
        result = find_test_device(devices, "sw_if3")
        assert result is not None
        assert result["me"] == "sw_if3"
        assert result["devtype"] == "SL_SW_IF3"

    def test_find_nonexistent_device(self, mock_lifesmart_devices):
        """测试查找不存在的设备。"""
        devices = mock_lifesmart_devices
        result = find_test_device(devices, "nonexistent_device")
        assert result is None

    def test_empty_device_list(self):
        """测试空设备列表。"""
        devices = []
        result = find_test_device(devices, "any_device")
        assert result is None


class TestSwitchSubdeviceAndGetters:
    """测试开关相关的子设备判断和获取函数。"""

    def test_is_switch_subdevice_basic(self):
        """测试基本的开关子设备判断。"""
        # SL_P_SW 九路开关控制器
        assert is_switch_subdevice("SL_P_SW", "P1") is True
        assert is_switch_subdevice("SL_P_SW", "P9") is True
        assert is_switch_subdevice("SL_P_SW", "P10") is False

        # 智能插座
        assert is_switch_subdevice("SL_OL", "O") is True
        assert is_switch_subdevice("SL_OL", "P1") is False

        # 计量插座
        assert is_switch_subdevice("SL_OE_3C", "P1") is True
        assert is_switch_subdevice("SL_OE_3C", "P4") is True
        assert is_switch_subdevice("SL_OE_3C", "P2") is False

    def test_get_switch_subdevices_with_real_devices(self, mock_lifesmart_devices):
        """使用真实设备数据测试获取开关子设备。"""
        devices = mock_lifesmart_devices

        # 标准三路开关
        sw_if3 = find_test_device(devices, "sw_if3")
        subdevices = get_switch_subdevices(sw_if3)
        assert "L1" in subdevices
        assert "L2" in subdevices
        assert "L3" in subdevices

        # 智能插座
        sw_ol = find_test_device(devices, "sw_ol")
        subdevices = get_switch_subdevices(sw_ol)
        assert "O" in subdevices

        # 九路开关控制器
        sw_p9 = find_test_device(devices, "sw_p9")
        subdevices = get_switch_subdevices(sw_p9)
        assert len(subdevices) == 9  # P1-P9
        assert all(f"P{i}" in subdevices for i in range(1, 10))

    def test_get_switch_subdevices_generic_controller(self, mock_lifesmart_devices):
        """测试通用控制器的开关子设备获取。"""
        devices = mock_lifesmart_devices

        # 通用控制器开关模式
        generic_switch = find_test_device(devices, "generic_p_switch_mode")
        subdevices = get_switch_subdevices(generic_switch)
        # 通用控制器开关模式下应该返回P2,P3,P4
        expected_keys = {"P2", "P3", "P4"}
        actual_keys = set(subdevices)
        assert actual_keys.issubset(expected_keys)

    def test_get_switch_subdevices_nature_panel(self, mock_lifesmart_devices):
        """测试超能面板的开关子设备获取。"""
        devices = mock_lifesmart_devices

        # 超能面板开关版 (P5=1)
        sw_nature = find_test_device(devices, "sw_nature")
        subdevices = get_switch_subdevices(sw_nature)
        assert len(subdevices) > 0  # 开关版应该有子设备

        # 超能面板温控版 (P5=3) - 应该没有开关子设备
        climate_nature = find_test_device(devices, "climate_nature_thermo")
        subdevices = get_switch_subdevices(climate_nature)
        assert len(subdevices) == 0  # 温控版不应该有开关子设备

    def test_get_switch_subdevices_non_switch_device(self, mock_lifesmart_devices):
        """测试非开关设备不应该返回开关子设备。"""
        devices = mock_lifesmart_devices

        # 环境传感器不是开关设备
        sensor_env = find_test_device(devices, "sensor_env")
        subdevices = get_switch_subdevices(sensor_env)
        assert len(subdevices) == 0


class TestBinarySensorSubdeviceAndGetters:
    """测试二元传感器相关的子设备判断和获取函数。"""

    def test_get_binary_sensor_subdevices_with_real_devices(
        self, mock_lifesmart_devices
    ):
        """使用真实设备数据测试获取二元传感器子设备。"""
        devices = mock_lifesmart_devices

        # 门磁传感器 (SL_SC_G) 有子设备 G
        bs_door = find_test_device(devices, "bs_door")
        subdevices = get_binary_sensor_subdevices(bs_door)
        assert "G" in subdevices

        # 运动传感器 (SL_SC_MHW) 有子设备 M
        bs_motion = find_test_device(devices, "bs_motion")
        subdevices = get_binary_sensor_subdevices(bs_motion)
        assert "M" in subdevices

        # 水浸传感器 (SL_SC_WA) 有子设备 WA
        bs_water = find_test_device(devices, "bs_water")
        subdevices = get_binary_sensor_subdevices(bs_water)
        assert "WA" in subdevices

        # 智能锁 (SL_LK_LS) 有子设备 EVTLO 和 ALM
        bs_lock = find_test_device(devices, "bs_lock")
        subdevices = get_binary_sensor_subdevices(bs_lock)
        assert "EVTLO" in subdevices
        assert "ALM" in subdevices

    def test_get_binary_sensor_subdevices_non_binary_sensor_device(
        self, mock_lifesmart_devices
    ):
        """测试非二元传感器设备不应该返回二元传感器子设备。"""
        devices = mock_lifesmart_devices

        # 环境传感器不是二元传感器设备
        sensor_env = find_test_device(devices, "sensor_env")
        subdevices = get_binary_sensor_subdevices(sensor_env)
        assert len(subdevices) == 0


class TestCoverSubdeviceAndGetters:
    """测试窗帘相关的子设备判断和获取函数。"""

    def test_get_cover_subdevices_with_real_devices(self, mock_lifesmart_devices):
        """使用真实设备数据测试获取窗帘子设备。"""
        devices = mock_lifesmart_devices

        # 车库门
        cover_garage = find_test_device(devices, "cover_garage")
        subdevices = get_cover_subdevices(cover_garage)
        assert "P2" in subdevices

        # 杜亚窗帘
        cover_dooya = find_test_device(devices, "cover_dooya")
        subdevices = get_cover_subdevices(cover_dooya)
        assert "P1" in subdevices

        # 通用控制器窗帘模式
        cover_generic = find_test_device(devices, "cover_generic")
        subdevices = get_cover_subdevices(cover_generic)
        assert len(subdevices) > 0  # 应该有子设备

    def test_get_cover_subdevices_non_cover_device(self, mock_lifesmart_devices):
        """测试非窗帘设备不应该返回窗帘子设备。"""
        devices = mock_lifesmart_devices

        # 环境传感器不是窗帘设备
        sensor_env = find_test_device(devices, "sensor_env")
        subdevices = get_cover_subdevices(sensor_env)
        assert len(subdevices) == 0


class TestSensorSubdeviceAndGetters:
    """测试传感器相关的子设备判断和获取函数。"""

    def test_get_sensor_subdevices_with_real_devices(self, mock_lifesmart_devices):
        """使用真实设备数据测试获取传感器子设备。"""
        devices = mock_lifesmart_devices

        # 环境传感器
        sensor_env = find_test_device(devices, "sensor_env")
        subdevices = get_sensor_subdevices(sensor_env)
        assert "T" in subdevices
        assert "H" in subdevices
        assert "Z" in subdevices
        assert "V" in subdevices

        # CO2传感器
        sensor_co2 = find_test_device(devices, "sensor_co2")
        subdevices = get_sensor_subdevices(sensor_co2)
        assert "P3" in subdevices

        # 功率计量插座传感器
        sensor_power_plug = find_test_device(devices, "sensor_power_plug")
        subdevices = get_sensor_subdevices(sensor_power_plug)
        assert "P2" in subdevices
        assert "P3" in subdevices

        # 锁电池传感器
        sensor_lock_battery = find_test_device(devices, "sensor_lock_battery")
        subdevices = get_sensor_subdevices(sensor_lock_battery)
        assert "BAT" in subdevices

    def test_get_sensor_subdevices_nature_panel_thermo(self, mock_lifesmart_devices):
        """测试超能面板温控版的传感器子设备获取。"""
        devices = mock_lifesmart_devices

        # 超能面板温控版 (P5=3) 应该有P4温度传感器
        climate_nature_thermo = find_test_device(devices, "climate_nature_thermo")
        subdevices = get_sensor_subdevices(climate_nature_thermo)
        assert "P4" in subdevices

    def test_get_sensor_subdevices_non_sensor_device(self, mock_lifesmart_devices):
        """测试非传感器设备不应该返回传感器子设备。"""
        devices = mock_lifesmart_devices

        # 标准开关不是传感器设备
        sw_if3 = find_test_device(devices, "sw_if3")
        subdevices = get_sensor_subdevices(sw_if3)
        assert len(subdevices) == 0


class TestLightSubdeviceAndGetters:
    """测试灯光相关的子设备判断和获取函数。"""

    def test_get_light_subdevices_with_real_devices(self, mock_lifesmart_devices):
        """使用真实设备数据测试获取灯光子设备。"""
        devices = mock_lifesmart_devices

        # 亮度灯
        light_bright = find_test_device(devices, "light_bright")
        subdevices = get_light_subdevices(light_bright)
        assert "P1" in subdevices

        # 调光灯
        light_dimmer = find_test_device(devices, "light_dimmer")
        subdevices = get_light_subdevices(light_dimmer)
        assert "_DIMMER" in subdevices  # 特殊标记

        # 量子灯
        light_quantum = find_test_device(devices, "light_quantum")
        subdevices = get_light_subdevices(light_quantum)
        assert "_QUANTUM" in subdevices  # 特殊标记

        # 单IO RGB灯
        light_singlergb = find_test_device(devices, "light_singlergb")
        subdevices = get_light_subdevices(light_singlergb)
        assert "RGB" in subdevices

        # 双IO RGBW灯
        light_dualrgbw = find_test_device(devices, "light_dualrgbw")
        subdevices = get_light_subdevices(light_dualrgbw)
        assert "_DUAL_RGBW" in subdevices  # 特殊标记

        # 户外灯
        light_outdoor = find_test_device(devices, "light_outdoor")
        subdevices = get_light_subdevices(light_outdoor)
        assert "P1" in subdevices

    def test_get_light_subdevices_spot_devices(self, mock_lifesmart_devices):
        """测试SPOT类型设备的灯光子设备获取。"""
        devices = mock_lifesmart_devices

        # SPOT RGB灯
        light_spotrgb = find_test_device(devices, "light_spotrgb")
        subdevices = get_light_subdevices(light_spotrgb)
        assert "RGB" in subdevices

        # SPOT RGBW灯
        light_spotrgbw = find_test_device(devices, "light_spotrgbw")
        subdevices = get_light_subdevices(light_spotrgbw)
        assert "RGBW" in subdevices

    def test_get_light_subdevices_garage_door_light(self, mock_lifesmart_devices):
        """测试车库门灯光子设备获取。"""
        devices = mock_lifesmart_devices

        # 车库门附属灯
        light_cover = find_test_device(devices, "light_cover")
        subdevices = get_light_subdevices(light_cover)
        assert "P1" in subdevices

    def test_get_light_subdevices_non_light_device(self, mock_lifesmart_devices):
        """测试非灯光设备不应该返回灯光子设备。"""
        devices = mock_lifesmart_devices

        # 环境传感器不是灯光设备
        sensor_env = find_test_device(devices, "sensor_env")
        subdevices = get_light_subdevices(sensor_env)
        assert len(subdevices) == 0


class TestSubdeviceLogicParametrized:
    """参数化测试子设备判断逻辑，基于实际的helper函数逻辑。"""

    @pytest.mark.parametrize(
        "device_type,sub_key,expected",
        [
            # === 开关子设备测试 ===
            ("SL_P_SW", "P1", True),  # 九路开关P1-P9
            ("SL_P_SW", "P5", True),
            ("SL_P_SW", "P9", True),
            ("SL_P_SW", "P10", False),  # P10超出范围
            ("SL_OL", "O", True),  # 智能插座开关
            ("SL_OE_3C", "P1", True),  # 计量插座P1是开关
            ("SL_OE_3C", "P4", True),  # 计量插座P4是开关
            (
                "SL_ETDOOR",
                "P2",
                False,
            ),  # garage door P2不是开关（在GARAGE_DOOR_TYPES中）
            ("SL_SC_BB_V2", "P1", False),  # 按钮开关P1不是开关子设备
            ("SL_SW_IF3", "L1", True),  # 标准开关
            ("SL_SW_IF3", "P4", False),  # P4不是开关子设备（支持的开关类型中P4被排除）
            ("UNKNOWN_TYPE", "P1", True),  # 未知设备类型但P1符合通用规则
            ("UNKNOWN_TYPE", "P5", False),  # 未知设备类型P5不符合通用规则
        ],
    )
    def test_switch_subdevice_logic(self, device_type, sub_key, expected):
        """测试开关子设备判断逻辑。"""
        from custom_components.lifesmart.helpers import is_switch_subdevice

        result = is_switch_subdevice(device_type, sub_key)
        assert (
            result == expected
        ), f"开关设备类型 {device_type} 的子设备 {sub_key} 预期 {expected}, 实际 {result}"

    @pytest.mark.parametrize(
        "device_type,sub_key,expected",
        [
            # === 二元传感器子设备测试 ===
            ("SL_SC_G", "G", True),  # 门磁传感器
            ("SL_SC_MHW", "M", True),  # 运动传感器
            ("SL_SC_WA", "WA", True),  # 水浸传感器
            ("SL_LK_LS", "EVTLO", True),  # 智能锁事件
            ("SL_LK_LS", "ALM", True),  # 智能锁报警
            ("SL_P_A", "P1", True),  # 烟雾传感器
            ("SL_P_RM", "P1", True),  # 雷达传感器
            ("SL_SC_BB_V2", "P1", True),  # 按钮开关P1是二元传感器
            ("SL_CP_DN", "P2", True),  # 地暖温控器窗户开关检测
            ("SL_DF_GG", "A", True),  # 云防门窗感应器
            ("SL_SC_G", "INVALID", False),  # 无效子设备
            ("INVALID_TYPE", "G", False),  # 无效设备类型
        ],
    )
    def test_binary_sensor_subdevice_logic(self, device_type, sub_key, expected):
        """测试二元传感器子设备判断逻辑。"""

        result = is_binary_sensor_subdevice(device_type, sub_key)
        assert (
            result == expected
        ), f"二元传感器设备类型 {device_type} 的子设备 {sub_key} 预期 {expected}, 实际 {result}"

    @pytest.mark.parametrize(
        "device_type,sub_key,expected",
        [
            # === 窗帘子设备测试 ===
            ("SL_ETDOOR", "P2", True),  # garage door P2（在GARAGE_DOOR_TYPES中）
            ("SL_ETDOOR", "HS", True),  # garage door HS（在GARAGE_DOOR_TYPES中）
            ("SL_DOOYA", "P1", True),  # 杜亚窗帘（在DOOYA_TYPES中）
            (
                "SL_SW_WIN",
                "OP",
                True,
            ),  # 非定位窗帘开（在NON_POSITIONAL_COVER_CONFIG中）
            (
                "SL_SW_WIN",
                "CL",
                True,
            ),  # 非定位窗帘关（在NON_POSITIONAL_COVER_CONFIG中）
            (
                "SL_SW_WIN",
                "ST",
                True,
            ),  # 非定位窗帘停（在NON_POSITIONAL_COVER_CONFIG中）
            (
                "SL_CN_IF",
                "P1",
                True,
            ),  # 窗帘开关（但NON_POSITIONAL_COVER_CONFIG中key是OP对应P1）
            ("SL_CN_IF", "P2", True),  # 窗帘开关（close对应P2）
            ("SL_CN_IF", "P3", True),  # 窗帘开关（stop对应P3）
            ("SL_DOOYA", "INVALID", False),  # 无效子设备
            ("INVALID_TYPE", "P1", False),  # 无效设备类型
        ],
    )
    def test_cover_subdevice_logic(self, device_type, sub_key, expected):
        """测试窗帘子设备判断逻辑。"""

        result = is_cover_subdevice(device_type, sub_key)
        assert (
            result == expected
        ), f"窗帘设备类型 {device_type} 的子设备 {sub_key} 预期 {expected}, 实际 {result}"

    @pytest.mark.parametrize(
        "device_type,sub_key,expected",
        [
            # === 数值传感器子设备测试 ===
            ("SL_SC_THL", "T", True),  # 环境传感器温度
            ("SL_SC_THL", "H", True),  # 环境传感器湿度
            ("SL_SC_THL", "Z", True),  # 环境传感器光照
            ("SL_SC_THL", "V", True),  # 环境传感器电压
            ("SL_SC_CA", "P1", True),  # TVOC传感器
            ("SL_SC_CA", "P3", True),  # CO2传感器
            ("SL_SC_CP", "P1", True),  # 燃气传感器
            ("SL_LK_LS", "BAT", True),  # 锁电池
            ("SL_OE_3C", "P2", True),  # 计量插座P2是传感器
            ("SL_OE_3C", "P3", True),  # 计量插座P3是传感器
            ("SL_SC_BB_V2", "P2", True),  # 按钮开关电量传感器
            ("SL_SC_CN", "P1", True),  # 噪音传感器
            ("ELIQ_EM", "EPA", True),  # ELIQ电量计量器
            ("SL_CP_DN", "P5", True),  # 地暖温控器附加传感器
            ("SL_SC_GD", "P1", False),  # 车库门不创建传感器子设备
            ("SL_SC_THL", "INVALID", False),  # 无效子设备
            ("INVALID_TYPE", "T", False),  # 无效设备类型
        ],
    )
    def test_sensor_subdevice_logic(self, device_type, sub_key, expected):
        """测试数值传感器子设备判断逻辑。"""

        result = is_sensor_subdevice(device_type, sub_key)
        assert (
            result == expected
        ), f"数值传感器设备类型 {device_type} 的子设备 {sub_key} 预期 {expected}, 实际 {result}"

    @pytest.mark.parametrize(
        "device_type,sub_key,expected",
        [
            # === 灯光子设备测试 ===
            ("SL_SW_IF3", "L1", True),  # 灯光开关L1
            ("SL_SW_IF3", "P1", True),  # 灯光开关P1
            ("SL_SW_IF3", "P2", True),  # 灯光开关P2
            ("SL_SW_IF3", "P5", False),  # P5不是灯光子设备
            ("SL_SW_IF3", "P8", False),  # P8不是灯光子设备
            ("SL_SC_GD", "HS", True),  # 车库门HS是灯光
            ("INVALID_TYPE", "L1", True),  # 默认情况下，符合模式的会返回True
            ("SL_SW_IF3", "INVALID_KEY", False),  # 不符合模式的返回False
        ],
    )
    def test_light_subdevice_logic(self, device_type, sub_key, expected):
        """测试灯光子设备判断逻辑。"""

        result = is_light_subdevice(device_type, sub_key)
        assert (
            result == expected
        ), f"灯光设备类型 {device_type} 的子设备 {sub_key} 预期 {expected}, 实际 {result}"


class TestDeviceTypeClassificationParametrized:
    """参数化测试设备类型分类函数，覆盖所有设备类型。"""

    @pytest.mark.parametrize(
        "device_data,expected_switch,expected_light,expected_cover,expected_binary_sensor,expected_sensor,expected_climate",
        [
            # 标准开关设备
            (
                {
                    "devtype": "SL_SW_IF3",
                    "data": {"L1": {"type": 129}, "L2": {"type": 128}},
                },
                True,
                False,
                False,
                False,
                False,
                False,
            ),
            # 智能插座
            (
                {"devtype": "SL_OL", "data": {"O": {"type": 129}}},
                True,
                False,
                False,
                False,
                False,
                False,
            ),
            # 计量插座（既是开关又是传感器）
            (
                {
                    "devtype": "SL_OE_3C",
                    "data": {"P1": {"type": 129}, "P2": {"v": 100}, "P3": {"v": 200}},
                },
                True,
                False,
                False,
                False,
                True,
                False,
            ),
            # 亮度灯
            (
                {"devtype": "SL_SPWM", "data": {"P1": {"type": 129, "val": 100}}},
                False,
                True,
                False,
                False,
                False,
                False,
            ),
            # 调光灯
            (
                {
                    "devtype": "SL_LI_WW",
                    "data": {"P1": {"type": 129}, "P2": {"val": 50}},
                },
                False,
                True,
                False,
                False,
                False,
                False,
            ),
            # RGB灯
            (
                {
                    "devtype": "SL_SC_RGB",
                    "data": {"RGB": {"type": 129, "val": 0xFF0000}},
                },
                False,
                True,
                False,
                False,
                False,
                False,
            ),
            # 车库门（既是窗帘又是灯光） - 修正为实际存在的设备类型
            (
                {
                    "devtype": "SL_ETDOOR",
                    "data": {"P2": {"type": 128}, "P1": {"type": 129}},
                },
                False,
                True,
                True,
                False,
                False,
                False,
            ),
            # 杜亚窗帘
            (
                {"devtype": "SL_DOOYA", "data": {"P1": {"val": 100, "type": 128}}},
                False,
                False,
                True,
                False,
                False,
                False,
            ),
            # 门磁传感器 - 注意：在ALL_SENSOR_TYPES中包含ALL_BINARY_SENSOR_TYPES，所以也是传感器
            (
                {"devtype": "SL_SC_G", "data": {"G": {"val": 0, "type": 0}}},
                False,
                False,
                False,
                True,
                True,
                False,
            ),
            # 环境传感器
            (
                {
                    "devtype": "SL_SC_THL",
                    "data": {
                        "T": {"val": 250},
                        "H": {"val": 601},
                        "Z": {"val": 1000},
                        "V": {"val": 95},
                    },
                },
                False,
                False,
                False,
                False,
                True,
                False,
            ),
            # 智能锁（既是二元传感器又是数值传感器）
            (
                {
                    "devtype": "SL_LK_LS",
                    "data": {
                        "EVTLO": {"val": 4121, "type": 1},
                        "ALM": {"val": 2},
                        "BAT": {"val": 88},
                    },
                },
                False,
                False,
                False,
                True,
                True,
                False,
            ),
            # 超能面板开关版 (P5=1)
            (
                {
                    "devtype": "SL_NATURE",
                    "data": {
                        "P1": {"type": 129},
                        "P2": {"type": 128},
                        "P5": {"val": 1},
                    },
                },
                True,
                False,
                False,
                False,
                False,
                False,
            ),
            # 超能面板温控版 (P5=3)
            (
                {
                    "devtype": "SL_NATURE",
                    "data": {"P4": {"v": 28.0}, "P5": {"val": 3}, "P6": {"val": 256}},
                },
                True,
                False,
                False,
                False,
                True,
                True,
            ),
            # 地暖温控器
            (
                {
                    "devtype": "SL_CP_DN",
                    "data": {"P1": {"type": 1, "val": 2147483648}, "P3": {"v": 25.0}},
                },
                False,
                False,
                False,
                False,
                False,
                True,
            ),
            # 通用控制器开关模式 (工作模式8) - 注意：SL_P在ALL_SENSOR_TYPES中
            (
                {
                    "devtype": "SL_P",
                    "data": {
                        "P1": {"val": (8 << 24)},
                        "P2": {"type": 128},
                        "P3": {"type": 129},
                    },
                },
                True,
                False,
                False,
                False,
                True,
                False,
            ),
            # 通用控制器窗帘模式 (工作模式2) - 注意：SL_P在ALL_SENSOR_TYPES中
            (
                {
                    "devtype": "SL_P",
                    "data": {
                        "P1": {"val": (2 << 24)},
                        "P2": {"type": 128},
                        "P3": {"type": 128},
                    },
                },
                False,
                False,
                True,
                False,
                True,
                False,
            ),
            # 通用控制器自由模式 (工作模式0) - 注意：SL_P在ALL_SENSOR_TYPES中
            (
                {
                    "devtype": "SL_P",
                    "data": {
                        "P1": {"val": (0 << 24)},
                        "P5": {"val": 1},
                        "P6": {"val": 0},
                    },
                },
                False,
                False,
                False,
                True,
                True,
                False,
            ),
        ],
    )
    def test_device_classification_comprehensive(
        self,
        device_data,
        expected_switch,
        expected_light,
        expected_cover,
        expected_binary_sensor,
        expected_sensor,
        expected_climate,
    ):
        """全面测试设备类型分类函数。

        这个测试覆盖了所有主要设备类型的分类逻辑，包括：
        - 普通设备的直接类型匹配
        - 复合设备（如计量插座、智能锁）的多重分类
        - 特殊设备（如超能面板、通用控制器）的条件分类
        """
        from custom_components.lifesmart.helpers import (
            is_switch,
            is_light,
            is_cover,
            is_binary_sensor,
            is_sensor,
            is_climate,
        )

        assert (
            is_switch(device_data) == expected_switch
        ), f"is_switch failed for {device_data['devtype']}"
        assert (
            is_light(device_data) == expected_light
        ), f"is_light failed for {device_data['devtype']}"
        assert (
            is_cover(device_data) == expected_cover
        ), f"is_cover failed for {device_data['devtype']}"
        assert (
            is_binary_sensor(device_data) == expected_binary_sensor
        ), f"is_binary_sensor failed for {device_data['devtype']}"
        assert (
            is_sensor(device_data) == expected_sensor
        ), f"is_sensor failed for {device_data['devtype']}"
        assert (
            is_climate(device_data) == expected_climate
        ), f"is_climate failed for {device_data['devtype']}"
