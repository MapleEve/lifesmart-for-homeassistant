"""
针对 LifeSmart 灯光 (Light) 平台的单元和集成测试。

此测试套件旨在全面验证 LifeSmartLight 及其所有子类的行为，包括：
- 平台设置逻辑，确保所有类型的灯光设备都能被正确创建。
- 每种灯光实体的初始属性（颜色模式、支持特性、初始状态等）是否正确。
- 服务调用（开、关、设置亮度/颜色/色温/效果）的完整流程。
- 乐观更新（Optimistic Update）效果的验证，确保UI即时响应。
- 通过 dispatcher 接收到状态更新后，实体状态的精确解析。
- 对边界条件（如数据缺失、特殊设备类型）的处理是否健壮。
"""

from unittest.mock import MagicMock

import pytest
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_EFFECT,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_COLOR_TEMP_KELVIN,
    DOMAIN as LIGHT_DOMAIN,
    SERVICE_TURN_ON,
    SERVICE_TURN_OFF,
    ColorMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, STATE_ON, STATE_OFF
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.lifesmart.const import *
from custom_components.lifesmart.light import (
    _is_light_subdevice,
    _parse_color_value,
    DEFAULT_MIN_KELVIN,
    DEFAULT_MAX_KELVIN,
)


# --- 辅助函数 ---
def get_entity_unique_id(hass: HomeAssistant, entity_id: str) -> str:
    """通过 entity_id 获取实体的 unique_id。"""
    from homeassistant.helpers.entity_registry import (
        async_get as async_get_entity_registry,
    )

    entity_registry = async_get_entity_registry(hass)
    entry = entity_registry.async_get(entity_id)
    assert entry is not None, f"实体 {entity_id} 未在注册表中找到"
    return entry.unique_id


# --- 辅助函数测试 ---
def test_parse_color_value():
    """测试 _parse_color_value 辅助函数。"""
    assert _parse_color_value(0x00AABBCC, has_white=False) == (0xAA, 0xBB, 0xCC)
    assert _parse_color_value(0xDDEEFF00, has_white=True) == (0xEE, 0xFF, 0x00, 0xDD)


@pytest.mark.parametrize(
    ("device_type", "sub_key", "expected"),
    [
        ("SL_SW_IF3", "L1", True),
        ("ANY_TYPE", "P1", True),
        ("ANY_TYPE", "P5", False),
    ],
)
def test_is_light_subdevice(device_type: str, sub_key: str, expected: bool) -> None:
    """测试 _is_light_subdevice 辅助函数。"""
    assert _is_light_subdevice(device_type, sub_key) is expected


# ==================== 测试套件 ====================


class TestLightSetup:
    """测试灯光平台的设置逻辑。"""

    async def test_setup_entry_creates_all_entities(
        self, hass: HomeAssistant, setup_integration: ConfigEntry
    ) -> None:
        """测试从共享 fixtures 成功设置所有灯光实体类型。"""
        # 根据 conftest.py 中定义的灯光设备，期望数量为 11
        assert len(hass.states.async_entity_ids(LIGHT_DOMAIN)) == 11

        # 验证所有预期的灯光实体都已创建
        assert hass.states.get("light.brightness_light_p1") is not None
        assert hass.states.get("light.dimmer_light") is not None
        assert hass.states.get("light.quantum_light") is not None
        assert hass.states.get("light.single_io_rgb_light_rgb") is not None
        assert hass.states.get("light.dual_io_rgbw_light") is not None
        assert hass.states.get("light.spot_rgb_light_rgb") is not None
        assert hass.states.get("light.spot_rgbw_light") is not None
        assert hass.states.get("light.cover_light_p1") is not None
        assert hass.states.get("light.wall_outlet_light_p1") is not None
        assert hass.states.get("light.simple_bulb_p1") is not None
        assert hass.states.get("light.outdoor_light_p1") is not None

        # 确认非灯光设备或子项没有被错误创建
        assert hass.states.get("light.garage_door_p2") is None
        assert hass.states.get("light.3_gang_switch_l1") is None  # 应为 switch


class TestLifeSmartBrightnessLight:
    """测试亮度灯 (LifeSmartBrightnessLight)。"""

    ENTITY_ID = "light.brightness_light_p1"
    DEVICE_ME = "light_bright"
    HUB_ID = "hub_light"
    SUB_KEY = "P1"

    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get("color_mode") == ColorMode.BRIGHTNESS
        assert state.attributes.get(ATTR_BRIGHTNESS) == 100

    async def test_turn_on_off_services(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        # Turn Off
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )
        assert hass.states.get(self.ENTITY_ID).state == STATE_OFF
        mock_client.turn_off_light_switch_async.assert_called_with(
            self.SUB_KEY, self.HUB_ID, self.DEVICE_ME
        )
        # Turn On (no params)
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )
        assert hass.states.get(self.ENTITY_ID).state == STATE_ON
        mock_client.turn_on_light_switch_async.assert_called_with(
            self.SUB_KEY, self.HUB_ID, self.DEVICE_ME
        )

    async def test_attribute_services(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self.ENTITY_ID, ATTR_BRIGHTNESS: 150},
            blocking=True,
        )
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get(ATTR_BRIGHTNESS) == 150
        mock_client.set_single_ep_async.assert_called_with(
            self.HUB_ID, self.DEVICE_ME, self.SUB_KEY, CMD_TYPE_SET_VAL, 150
        )

    async def test_state_update(self, hass: HomeAssistant, setup_integration):
        unique_id = get_entity_unique_id(hass, self.ENTITY_ID)
        # 场景 1: 灯关闭
        async_dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}",
            {"type": 128, "val": 50},
        )
        await hass.async_block_till_done()
        assert hass.states.get(self.ENTITY_ID).state == STATE_OFF
        # 场景 2: 灯开启
        async_dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}",
            {"type": 129, "val": 75},
        )
        await hass.async_block_till_done()
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get(ATTR_BRIGHTNESS) == 75


class TestLifeSmartDimmerLight:
    """测试色温灯 (LifeSmartDimmerLight)。"""

    ENTITY_ID = "light.dimmer_light"
    DEVICE_ME = "light_dimmer"
    HUB_ID = "hub_light"

    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get("color_mode") == ColorMode.COLOR_TEMP
        assert state.attributes.get(ATTR_BRIGHTNESS) == 100
        expected_kelvin = DEFAULT_MIN_KELVIN + ((255 - 27) / 255.0) * (
            DEFAULT_MAX_KELVIN - DEFAULT_MIN_KELVIN
        )
        assert state.attributes.get(ATTR_COLOR_TEMP_KELVIN) == pytest.approx(
            expected_kelvin, 1
        )

    async def test_turn_on_off_services(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        # Turn Off
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )
        assert hass.states.get(self.ENTITY_ID).state == STATE_OFF
        mock_client.turn_off_light_switch_async.assert_called_with(
            "P1", self.HUB_ID, self.DEVICE_ME
        )
        # Turn On (no params)
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )
        assert hass.states.get(self.ENTITY_ID).state == STATE_ON
        mock_client.turn_on_light_switch_async.assert_called_with(
            "P1", self.HUB_ID, self.DEVICE_ME
        )

    async def test_attribute_services(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: self.ENTITY_ID,
                ATTR_BRIGHTNESS: 200,
                ATTR_COLOR_TEMP_KELVIN: 3726,
            },
            blocking=True,
        )
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get(ATTR_BRIGHTNESS) == 200
        assert state.attributes.get(ATTR_COLOR_TEMP_KELVIN) == 3726
        expected_temp_val = round(
            255
            - (
                (
                    (3726 - DEFAULT_MIN_KELVIN)
                    / (DEFAULT_MAX_KELVIN - DEFAULT_MIN_KELVIN)
                )
                * 255
            )
        )
        mock_client.set_multi_eps_async.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            [
                {"idx": "P1", "type": CMD_TYPE_SET_VAL, "val": 200},
                {"idx": "P2", "type": CMD_TYPE_SET_VAL, "val": expected_temp_val},
            ],
        )

    async def test_state_update(self, hass: HomeAssistant, setup_integration):
        unique_id = get_entity_unique_id(hass, self.ENTITY_ID)
        async_dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}",
            {"P1": {"type": 128, "val": 10}, "P2": {"val": 200}},
        )
        await hass.async_block_till_done()
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_OFF


class TestLifeSmartQuantumLight:
    """测试量子灯 (LifeSmartQuantumLight)。"""

    ENTITY_ID = "light.quantum_light"
    DEVICE_ME = "light_quantum"
    HUB_ID = "hub_light"

    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get("color_mode") == ColorMode.RGBW
        assert state.attributes.get(ATTR_RGBW_COLOR) == (1, 2, 3, 1)
        assert state.attributes.get(ATTR_EFFECT) is None

    async def test_turn_on_off_services(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        # Turn Off
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )
        assert hass.states.get(self.ENTITY_ID).state == STATE_OFF
        mock_client.turn_off_light_switch_async.assert_called_with(
            "P1", self.HUB_ID, self.DEVICE_ME
        )
        # Turn On (no params)
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )
        assert hass.states.get(self.ENTITY_ID).state == STATE_ON
        mock_client.turn_on_light_switch_async.assert_called_with(
            "P1", self.HUB_ID, self.DEVICE_ME
        )

    async def test_attribute_services(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        # Test Effect
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self.ENTITY_ID, ATTR_EFFECT: "魔力红"},
            blocking=True,
        )
        state = hass.states.get(self.ENTITY_ID)
        assert state.attributes.get(ATTR_EFFECT) == "魔力红"
        mock_client.set_multi_eps_async.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            [{"idx": "P2", "type": CMD_TYPE_SET_RAW, "val": ALL_EFFECT_MAP["魔力红"]}],
        )
        # Test Color (without brightness)
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self.ENTITY_ID, ATTR_RGBW_COLOR: (10, 20, 30, 40)},
            blocking=True,
        )
        state = hass.states.get(self.ENTITY_ID)
        assert state.attributes.get(ATTR_RGBW_COLOR) == (10, 20, 30, 40)
        assert state.attributes.get(ATTR_EFFECT) is None
        mock_client.set_multi_eps_async.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            [{"idx": "P2", "type": CMD_TYPE_SET_RAW, "val": 0x280A141E}],
        )

    async def test_service_call_with_brightness_and_color(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        """测试量子灯的颜色和亮度组合服务调用。"""
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: self.ENTITY_ID,
                ATTR_BRIGHTNESS: 128,
                ATTR_RGBW_COLOR: (10, 20, 30, 40),
            },
            blocking=True,
        )

        # 验证发送了多个命令：一个用于亮度，一个用于颜色
        mock_client.set_multi_eps_async.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            [
                {"idx": "P1", "type": CMD_TYPE_SET_VAL, "val": 128},
                {"idx": "P2", "type": CMD_TYPE_SET_RAW, "val": 0x280A141E},
            ],
        )
        # 验证确保灯开启的命令也被调用
        mock_client.turn_on_light_switch_async.assert_called_with(
            "P1", self.HUB_ID, self.DEVICE_ME
        )

    async def test_state_update(self, hass: HomeAssistant, setup_integration):
        unique_id = get_entity_unique_id(hass, self.ENTITY_ID)
        async_dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}",
            {"P1": {"type": 129, "val": 200}, "P2": {"val": 0x100A141E}},
        )
        await hass.async_block_till_done()
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get(ATTR_BRIGHTNESS) == 200
        assert state.attributes.get(ATTR_RGBW_COLOR) == (10, 20, 30, 16)


class TestLifeSmartSingleIORGBWLight:
    """测试单IO口RGBW灯 (LifeSmartSingleIORGBWLight)。"""

    ENTITY_ID = "light.single_io_rgb_light_rgb"
    DEVICE_ME = "light_singlergb"
    HUB_ID = "hub_light"
    SUB_KEY = "RGB"

    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get("color_mode") == ColorMode.RGBW
        assert state.attributes.get(ATTR_BRIGHTNESS) == 255
        assert state.attributes.get(ATTR_RGBW_COLOR) == (1, 2, 3, 255)

    # --- 关键修复：删除旧的 test_turn_on_off_services ---
    # async def test_turn_on_off_services(...) 已被下面的新测试取代

    @pytest.mark.parametrize(
        ("service_data", "expected_type", "expected_val", "test_id"),
        [
            # --- 核心修复：将期望的 type 从整数改为字符串 ---
            # 1. 简单开灯
            ({}, "0x81", 1, "turn_on_simple"),
            # 2. 设置颜色 (同时提供亮度，但协议决定了亮度被忽略)
            (
                {ATTR_RGBW_COLOR: (10, 20, 30, 40), ATTR_BRIGHTNESS: 128},
                "0xFF",
                0x280A141E,
                "set_color_ignores_brightness",
            ),
            # 3. 设置效果
            (
                {ATTR_EFFECT: "魔力红"},
                "0xFF",
                DYN_EFFECT_MAP["魔力红"],
                "set_effect",
            ),
            # 4. 只设置亮度 (应被解释为设置白光)
            (
                {ATTR_BRIGHTNESS: 200},
                "0xFF",
                (200 << 24),  # W=200, R=G=B=0
                "set_brightness_as_white",
            ),
        ],
        ids=lambda x: x[2] if isinstance(x, tuple) else None,
    )
    async def test_turn_on_protocol(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        setup_integration,
        service_data,
        expected_type,
        expected_val,
        test_id,
    ):
        """测试单IO口灯的各种开灯服务调用是否符合协议。"""
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self.ENTITY_ID, **service_data},
            blocking=True,
        )
        mock_client.set_single_ep_async.assert_called_with(
            self.HUB_ID, self.DEVICE_ME, self.SUB_KEY, expected_type, expected_val
        )

    async def test_turn_off_protocol(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        """测试单IO口灯的关灯服务调用是否符合协议。"""
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )
        # --- 核心修复：将期望的 type 从整数改为字符串 ---
        mock_client.set_single_ep_async.assert_called_with(
            self.HUB_ID, self.DEVICE_ME, self.SUB_KEY, "0x80", 0
        )

    async def test_state_update(self, hass: HomeAssistant, setup_integration):
        unique_id = get_entity_unique_id(hass, self.ENTITY_ID)
        # w_flag = 50 (0x32), round(50 / 100 * 255) = round(127.5) = 128
        async_dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}",
            {"type": 129, "val": 0x320A141E},
        )
        await hass.async_block_till_done()
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get(ATTR_BRIGHTNESS) == 128
        assert state.attributes.get(ATTR_RGBW_COLOR) == (10, 20, 30, 255)


class TestLifeSmartDualIORGBWLight:
    """测试双IO口RGBW灯 (LifeSmartDualIORGBWLight)。"""

    ENTITY_ID = "light.dual_io_rgbw_light"
    DEVICE_ME = "light_dualrgbw"
    HUB_ID = "hub_light"
    COLOR_IO = "RGBW"
    EFFECT_IO = "DYN"

    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get("color_mode") == ColorMode.RGBW
        assert state.attributes.get(ATTR_RGBW_COLOR) == (0, 0, 0, 0)
        assert state.attributes.get(ATTR_EFFECT) is None

    async def test_turn_on_off_services(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        # Turn Off
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )
        assert hass.states.get(self.ENTITY_ID).state == STATE_OFF
        mock_client.set_multi_eps_async.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            [
                {"idx": self.COLOR_IO, "type": CMD_TYPE_OFF, "val": 0},
                {"idx": self.EFFECT_IO, "type": CMD_TYPE_OFF, "val": 0},
            ],
        )
        # Turn On (no params)
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )
        assert hass.states.get(self.ENTITY_ID).state == STATE_ON
        mock_client.turn_on_light_switch_async.assert_called_with(
            self.COLOR_IO, self.HUB_ID, self.DEVICE_ME
        )

    async def test_effect_and_color_priority(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        # 1. 设置效果 -> 验证RGBW被置为开灯状态
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self.ENTITY_ID, ATTR_EFFECT: "魔力红"},
            blocking=True,
        )
        state = hass.states.get(self.ENTITY_ID)
        assert state.attributes.get(ATTR_EFFECT) == "魔力红"
        assert state.attributes.get(ATTR_RGBW_COLOR) is None
        mock_client.set_multi_eps_async.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            [
                {"idx": self.COLOR_IO, "type": CMD_TYPE_ON, "val": 1},
                {
                    "idx": self.EFFECT_IO,
                    "type": CMD_TYPE_SET_RAW,
                    "val": DYN_EFFECT_MAP["魔力红"],
                },
            ],
        )

    async def test_service_call_with_brightness_and_color(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        """测试双IO口灯的颜色和亮度组合服务调用。"""
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: self.ENTITY_ID,
                ATTR_BRIGHTNESS: 128,
                ATTR_RGBW_COLOR: (10, 20, 30, 40),
            },
            blocking=True,
        )
        # 亮度被应用到颜色上，计算最终颜色值
        # ratio = 128/255, (10*r, 20*r, 30*r, 40*r) -> (5, 10, 15, 20)
        # val = 0x14050A0F
        expected_val = (20 << 24) | (5 << 16) | (10 << 8) | 15

        mock_client.set_multi_eps_async.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            [
                {"idx": self.COLOR_IO, "type": CMD_TYPE_SET_RAW, "val": expected_val},
                {"idx": self.EFFECT_IO, "type": CMD_TYPE_OFF, "val": 0},
            ],
        )

    async def test_state_update(self, hass: HomeAssistant, setup_integration):
        unique_id = get_entity_unique_id(hass, self.ENTITY_ID)
        update_data = {
            self.COLOR_IO: {"type": 129, "val": 0x11223344},
            self.EFFECT_IO: {"type": 129, "val": DYN_EFFECT_MAP["魔力红"]},
        }
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", update_data
        )
        await hass.async_block_till_done()
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get(ATTR_EFFECT) == "魔力红"
        assert state.attributes.get(ATTR_RGBW_COLOR) == (0x22, 0x33, 0x44, 0x11)


class TestLifeSmartSPOTRGBLight:
    """测试SPOT RGB灯 (LifeSmartSPOTRGBLight)。"""

    ENTITY_ID = "light.spot_rgb_light_rgb"
    DEVICE_ME = "light_spotrgb"
    HUB_ID = "hub_light"
    SUB_KEY = "RGB"

    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get("color_mode") == ColorMode.RGB
        assert state.attributes.get(ATTR_RGB_COLOR) == (255, 128, 64)
        assert state.attributes.get(ATTR_EFFECT) is None

    async def test_turn_on_off_services(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        # Turn Off
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )
        assert hass.states.get(self.ENTITY_ID).state == STATE_OFF
        mock_client.turn_off_light_switch_async.assert_called_with(
            self.SUB_KEY, self.HUB_ID, self.DEVICE_ME
        )
        # Turn On (no params)
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )
        assert hass.states.get(self.ENTITY_ID).state == STATE_ON
        mock_client.set_single_ep_async.assert_called_with(
            self.HUB_ID, self.DEVICE_ME, self.SUB_KEY, CMD_TYPE_ON, 1
        )

    async def test_attribute_services(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        setup_integration,
    ):
        # Test Effect
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self.ENTITY_ID, ATTR_EFFECT: "魔力红"},
            blocking=True,
        )
        state = hass.states.get(self.ENTITY_ID)
        assert state.attributes.get(ATTR_EFFECT) == "魔力红"
        mock_client.set_single_ep_async.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            self.SUB_KEY,
            CMD_TYPE_SET_RAW,
            DYN_EFFECT_MAP["魔力红"],
        )
        # Test Color
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self.ENTITY_ID, ATTR_RGB_COLOR: (10, 20, 30)},
            blocking=True,
        )
        state = hass.states.get(self.ENTITY_ID)
        assert state.attributes.get(ATTR_RGB_COLOR) == (10, 20, 30)
        assert state.attributes.get(ATTR_EFFECT) is None
        mock_client.set_single_ep_async.assert_called_with(
            self.HUB_ID, self.DEVICE_ME, self.SUB_KEY, CMD_TYPE_SET_RAW, 0x0A141E
        )

    @pytest.mark.parametrize(
        ("service_data", "expected_api_val", "test_id"),
        [
            # 1. 仅提供颜色，亮度应为全亮 (255)
            (
                {ATTR_RGB_COLOR: (255, 128, 64)},
                0xFF8040,
                "color_only_full_brightness",
            ),
            # 2. 提供颜色和全亮度
            (
                {ATTR_BRIGHTNESS: 255, ATTR_RGB_COLOR: (255, 128, 64)},
                0xFF8040,
                "color_with_max_brightness",
            ),
            # 3. 提供颜色和中等亮度
            # HA 内部会进行 HS 转换和亮度调整，最终的 RGB 会变化
            (
                {ATTR_BRIGHTNESS: 128, ATTR_RGB_COLOR: (255, 0, 0)},  # 纯红色
                0x800000,  # 亮度减半，R分量减半
                "color_with_medium_brightness",
            ),
            # 4. 提供颜色和低亮度
            (
                {ATTR_BRIGHTNESS: 1, ATTR_RGB_COLOR: (0, 255, 0)},  # 纯绿色
                0x000100,  # 亮度最低，G分量为1
                "color_with_min_brightness",
            ),
            # 5. 复杂的颜色和亮度组合
            # (255, 128, 64) @ 50% brightness -> (128, 64, 32)
            (
                {ATTR_BRIGHTNESS: 128, ATTR_RGB_COLOR: (255, 128, 64)},
                0x804020,
                "complex_color_with_medium_brightness",
            ),
        ],
        ids=lambda x: x[2] if isinstance(x, tuple) else None,
    )
    async def test_service_call_with_brightness_and_color(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        setup_integration,
        service_data,
        expected_api_val,
        test_id,
    ):
        """
        /**
         * test_service_call_with_brightness_and_color() - 验证颜色和亮度组合的正确处理。
         * @service_data: 包含有效颜色和亮度值的服务调用数据。
         * @expected_api_val: 经过 Home Assistant 核心颜色/亮度转换后，预期发送给 API 的十六进制值。
         * @test_id: 测试用例的ID。
         *
         * 此测试验证当同时提供 brightness 和 rgb_color 时，集成是否能正确计算
         * 最终的颜色值并调用底层 API。这反映了 HA 的真实颜色处理逻辑。
         */
        """
        # 准备完整的服务调用数据
        full_service_data = {ATTR_ENTITY_ID: self.ENTITY_ID, **service_data}

        # 调用服务
        await hass.services.async_call(
            LIGHT_DOMAIN, SERVICE_TURN_ON, full_service_data, blocking=True
        )

        # 验证底层 API 是否以正确的、经过亮度调整后的颜色值被调用
        mock_client.set_single_ep_async.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            self.SUB_KEY,
            CMD_TYPE_SET_RAW,
            expected_api_val,
        )

    async def test_state_update(self, hass: HomeAssistant, setup_integration):
        unique_id = get_entity_unique_id(hass, self.ENTITY_ID)
        async_dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}",
            {"type": 129, "val": DYN_EFFECT_MAP["海浪"]},
        )
        await hass.async_block_till_done()
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get(ATTR_EFFECT) == "海浪"


class TestLifeSmartSPOTRGBWLight:
    """测试SPOT RGBW灯 (LifeSmartSPOTRGBWLight)。"""

    ENTITY_ID = "light.spot_rgbw_light"
    DEVICE_ME = "light_spotrgbw"
    HUB_ID = "hub_light"
    COLOR_IO = "RGBW"
    EFFECT_IO = "DYN"

    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get("color_mode") == ColorMode.RGBW
        assert state.attributes.get(ATTR_RGBW_COLOR) == (0x22, 0x33, 0x44, 0x11)
        assert state.attributes.get(ATTR_EFFECT) == "海浪"

    async def test_turn_on_off_services(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        # Turn Off
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )
        assert hass.states.get(self.ENTITY_ID).state == STATE_OFF
        mock_client.set_multi_eps_async.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            [
                {"idx": self.COLOR_IO, "type": CMD_TYPE_OFF, "val": 0},
                {"idx": self.EFFECT_IO, "type": CMD_TYPE_OFF, "val": 0},
            ],
        )
        # Turn On (no params)
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )
        assert hass.states.get(self.ENTITY_ID).state == STATE_ON
        mock_client.turn_on_light_switch_async.assert_called_with(
            self.COLOR_IO, self.HUB_ID, self.DEVICE_ME
        )

    async def test_effect_and_color_priority(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        # 设置效果
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self.ENTITY_ID, ATTR_EFFECT: "魔力红"},
            blocking=True,
        )
        mock_client.set_multi_eps_async.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            [
                {"idx": self.COLOR_IO, "type": CMD_TYPE_ON, "val": 1},
                {
                    "idx": self.EFFECT_IO,
                    "type": CMD_TYPE_SET_RAW,
                    "val": DYN_EFFECT_MAP["魔力红"],
                },
            ],
        )

    async def test_service_call_with_brightness_and_color(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        """测试SPOT RGBW灯的颜色和亮度组合服务调用。"""
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: self.ENTITY_ID,
                ATTR_BRIGHTNESS: 128,
                ATTR_RGBW_COLOR: (10, 20, 30, 40),
            },
            blocking=True,
        )
        # 亮度被应用到颜色上，计算最终颜色值
        # ratio = 128/255, (10*r, 20*r, 30*r, 40*r) -> (5, 10, 15, 20)
        # val = 0x14050A0F
        expected_val = (20 << 24) | (5 << 16) | (10 << 8) | 15

        mock_client.set_multi_eps_async.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            [
                {"idx": self.COLOR_IO, "type": CMD_TYPE_SET_RAW, "val": expected_val},
                {"idx": self.EFFECT_IO, "type": CMD_TYPE_OFF, "val": 0},
            ],
        )

    async def test_state_update(self, hass: HomeAssistant, setup_integration):
        unique_id = get_entity_unique_id(hass, self.ENTITY_ID)
        update_data = {
            self.COLOR_IO: {"type": 128, "val": 0},
            self.EFFECT_IO: {"type": 128, "val": 0},
        }
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", update_data
        )
        await hass.async_block_till_done()
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_OFF
        assert state.attributes.get(ATTR_EFFECT) is None


class TestLifeSmartCoverLight:
    """测试车库门附属灯 (LifeSmartCoverLight)。"""

    ENTITY_ID = "light.cover_light_p1"
    DEVICE_ME = "light_cover"
    HUB_ID = "hub_light"
    SUB_KEY = "P1"

    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get("color_mode") == ColorMode.ONOFF

    async def test_turn_on_off_services(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        # Turn Off
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )
        assert hass.states.get(self.ENTITY_ID).state == STATE_OFF
        mock_client.turn_off_light_switch_async.assert_called_with(
            self.SUB_KEY, self.HUB_ID, self.DEVICE_ME
        )
        # Turn On
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )
        assert hass.states.get(self.ENTITY_ID).state == STATE_ON
        mock_client.turn_on_light_switch_async.assert_called_with(
            self.SUB_KEY, self.HUB_ID, self.DEVICE_ME
        )

    async def test_state_update(self, hass: HomeAssistant, setup_integration):
        unique_id = get_entity_unique_id(hass, self.ENTITY_ID)
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", {"type": 128}
        )
        await hass.async_block_till_done()
        assert hass.states.get(self.ENTITY_ID).state == STATE_OFF


class TestLifeSmartSimpleOnOffLight:
    """
    测试简单的开关灯，适用于 LIGHT_SWITCH_TYPES 和 LIGHT_BULB_TYPES。
    """

    @pytest.mark.parametrize(
        ("entity_id", "device_me", "sub_key"),
        [
            ("light.wall_outlet_light_p1", "light_switch", "P1"),
            ("light.simple_bulb_p1", "light_bulb", "P1"),
        ],
    )
    async def test_on_off_and_state(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        setup_integration,
        entity_id,
        device_me,
        sub_key,
    ):
        # Initial state (from conftest)
        initial_state = STATE_ON if device_me == "light_switch" else STATE_OFF
        state = hass.states.get(entity_id)
        assert state.state == initial_state

        if state.state == STATE_ON:
            assert state.attributes.get("color_mode") == ColorMode.ONOFF

        # Turn Off
        await hass.services.async_call(
            LIGHT_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )
        assert hass.states.get(entity_id).state == STATE_OFF
        mock_client.turn_off_light_switch_async.assert_called_with(
            sub_key, "hub_light", device_me
        )

        # State Update to ON
        unique_id = get_entity_unique_id(hass, entity_id)
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", {"type": 129}
        )
        await hass.async_block_till_done()
        state = hass.states.get(entity_id)
        assert state.state == STATE_ON
        assert state.attributes.get("color_mode") == ColorMode.ONOFF


class TestLifeSmartOutdoorLight(TestLifeSmartSingleIORGBWLight):
    """
    测试户外灯 (SL_LI_UG1)。
    其行为与单IO RGBW灯完全相同，因此直接继承其测试类。
    """

    ENTITY_ID = "light.outdoor_light_p1"
    DEVICE_ME = "light_outdoor"
    SUB_KEY = "P1"
