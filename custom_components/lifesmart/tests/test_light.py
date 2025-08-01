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
    _parse_color_value,
    DEFAULT_MIN_KELVIN,
    DEFAULT_MAX_KELVIN,
)
from .test_utils import get_entity_unique_id


# --- 辅助函数测试 ---
def test_parse_color_value():
    """测试 _parse_color_value 辅助函数。"""
    assert _parse_color_value(0x00AABBCC, has_white=False) == (
        0xAA,
        0xBB,
        0xCC,
    ), "RGB颜色解析应该正确"
    assert _parse_color_value(0xDDEEFF00, has_white=True) == (
        0xEE,
        0xFF,
        0x00,
        0xDD,
    ), "RGBW颜色解析应该正确"


# ==================== 测试套件 ====================


class TestLightSetup:
    """测试灯光平台的设置逻辑。"""

    @pytest.mark.asyncio
    async def test_setup_entry_creates_all_entities(
        self, hass: HomeAssistant, setup_integration: ConfigEntry
    ) -> None:
        """测试从共享 fixtures 成功设置所有灯光实体类型。"""
        # 根据 conftest.py 中定义的灯光设备，期望数量为 11
        assert (
            len(hass.states.async_entity_ids(LIGHT_DOMAIN)) == 11
        ), "应该有11个灯光实体"

        # 验证所有预期的灯光实体都已创建
        assert (
            hass.states.get("light.brightness_light_p1") is not None
        ), "亮度灯应该存在"
        assert hass.states.get("light.dimmer_light") is not None, "调光器灯应该存在"
        assert hass.states.get("light.quantum_light") is not None, "量子灯应该存在"
        assert (
            hass.states.get("light.single_io_rgb_light_rgb") is not None
        ), "单IO RGB灯应该存在"
        assert (
            hass.states.get("light.dual_io_rgbw_light") is not None
        ), "双IO RGBW灯应该存在"
        assert (
            hass.states.get("light.spot_rgb_light_rgb") is not None
        ), "射灯RGB应该存在"
        assert hass.states.get("light.spot_rgbw_light") is not None, "射灯RGBW应该存在"
        assert hass.states.get("light.cover_light_p1") is not None, "窗帘灯应该存在"
        assert (
            hass.states.get("light.wall_outlet_light_p1") is not None
        ), "插座灯应该存在"
        assert hass.states.get("light.simple_bulb_p1") is not None, "简单灯泡应该存在"
        assert hass.states.get("light.outdoor_light_p1") is not None, "室外灯应该存在"

        # 确认非灯光设备或子项没有被错误创建
        assert (
            hass.states.get("light.garage_door_p2") is None
        ), "车库门不应该作为灯光实体"
        assert (
            hass.states.get("light.3_gang_switch_l1") is None
        ), "3路开关不应该作为灯光实体"  # 应为 switch


class TestLifeSmartBrightnessLight:
    """测试亮度灯 (LifeSmartBrightnessLight)。"""

    ENTITY_ID = "light.brightness_light_p1"
    DEVICE_ME = "light_bright"
    HUB_ID = "hub_light"
    SUB_KEY = "P1"

    @pytest.mark.asyncio
    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON, "灯光状态应该为开启"
        assert (
            state.attributes.get("color_mode") == ColorMode.BRIGHTNESS
        ), "颜色模式应该为亮度模式"
        assert state.attributes.get(ATTR_BRIGHTNESS) == 100, "亮度值应该为100"

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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
        mock_client.async_send_single_command.assert_called_with(
            self.HUB_ID, self.DEVICE_ME, self.SUB_KEY, 0xCF, 150
        )

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_api_failure_reverts_state(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        """测试API调用失败时，亮度灯状态会回滚。"""
        # 初始状态: on, brightness 100
        initial_state = hass.states.get(self.ENTITY_ID)
        assert initial_state.state == STATE_ON
        assert initial_state.attributes.get(ATTR_BRIGHTNESS) == 100

        # 模拟API调用失败
        mock_client.turn_off_light_switch_async.side_effect = Exception("API Error")

        # 尝试关灯
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )

        # 验证状态已回滚到初始状态
        final_state = hass.states.get(self.ENTITY_ID)
        assert final_state.state == STATE_ON
        assert final_state.attributes.get(ATTR_BRIGHTNESS) == 100


class TestLifeSmartDimmerLight:
    """测试色温灯 (LifeSmartDimmerLight)。"""

    ENTITY_ID = "light.dimmer_light"
    DEVICE_ME = "light_dimmer"
    HUB_ID = "hub_light"

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
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
        mock_client.async_send_multi_command.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            [
                {"idx": "P1", "type": 0xCF, "val": 200},
                {"idx": "P2", "type": 0xCF, "val": expected_temp_val},
            ],
        )

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_api_failure_reverts_state(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        """测试API调用失败时，色温灯状态会回滚。"""
        # 记录初始状态
        initial_state = hass.states.get(self.ENTITY_ID)
        initial_brightness = initial_state.attributes.get(ATTR_BRIGHTNESS)
        initial_kelvin = initial_state.attributes.get(ATTR_COLOR_TEMP_KELVIN)

        # 模拟API调用失败
        mock_client.async_send_multi_command.side_effect = Exception("API Error")

        # 尝试改变亮度和色温
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: self.ENTITY_ID,
                ATTR_BRIGHTNESS: 200,
                ATTR_COLOR_TEMP_KELVIN: 4000,
            },
            blocking=True,
        )

        # 验证状态已回滚
        final_state = hass.states.get(self.ENTITY_ID)
        assert final_state.state == STATE_ON
        assert final_state.attributes.get(ATTR_BRIGHTNESS) == initial_brightness
        assert final_state.attributes.get(ATTR_COLOR_TEMP_KELVIN) == pytest.approx(
            initial_kelvin
        )


class TestLifeSmartQuantumLight:
    """测试量子灯 (LifeSmartQuantumLight)。"""

    ENTITY_ID = "light.quantum_light"
    DEVICE_ME = "light_quantum"
    HUB_ID = "hub_light"

    @pytest.mark.asyncio
    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get("color_mode") == ColorMode.RGBW
        assert state.attributes.get(ATTR_RGBW_COLOR) == (1, 2, 3, 1)
        assert state.attributes.get(ATTR_EFFECT) is None

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_api_failure_reverts_state(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        """测试API调用失败时，量子灯状态会回滚。"""
        # 初始状态: on, color (1,2,3,1), no effect
        initial_state = hass.states.get(self.ENTITY_ID)
        assert initial_state.attributes.get(ATTR_EFFECT) is None

        # 模拟API调用失败
        mock_client.async_send_multi_command.side_effect = Exception("API Error")

        # 尝试设置效果
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self.ENTITY_ID, ATTR_EFFECT: "魔力红"},
            blocking=True,
        )

        # 验证状态已回滚
        final_state = hass.states.get(self.ENTITY_ID)
        assert final_state.state == STATE_ON
        assert final_state.attributes.get(ATTR_EFFECT) is None
        assert final_state.attributes.get(ATTR_RGBW_COLOR) == (1, 2, 3, 1)

    @pytest.mark.asyncio
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
        mock_client.async_send_multi_command.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            [{"idx": "P2", "type": 0xFF, "val": ALL_EFFECT_MAP["魔力红"]}],
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
        mock_client.async_send_multi_command.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            [{"idx": "P2", "type": 0xFF, "val": 0x280A141E}],
        )

    @pytest.mark.asyncio
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
        mock_client.async_send_multi_command.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            [
                {"idx": "P1", "type": 0xCF, "val": 128},
                {"idx": "P2", "type": 0xFF, "val": 0x280A141E},
            ],
        )
        # 验证确保灯开启的命令也被调用
        mock_client.turn_on_light_switch_async.assert_called_with(
            "P1", self.HUB_ID, self.DEVICE_ME
        )

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get("color_mode") == ColorMode.RGBW
        assert state.attributes.get(ATTR_BRIGHTNESS) == 255
        assert state.attributes.get(ATTR_RGBW_COLOR) == (1, 2, 3, 255)

    @pytest.mark.parametrize(
        ("service_data", "expected_type", "expected_val", "test_id"),
        [
            # 1. 简单开灯
            ({}, 0x81, 1, "SimpleTurnOn"),
            # 2. 设置颜色 (同时提供亮度，但协议决定了亮度被忽略)
            (
                {ATTR_RGBW_COLOR: (10, 20, 30, 40), ATTR_BRIGHTNESS: 128},
                0xFF,
                0x280A141E,
                "SetColorIgnoresBrightness",
            ),
            # 3. 设置效果
            (
                {ATTR_EFFECT: "魔力红"},
                0xFF,
                DYN_EFFECT_MAP["魔力红"],
                "SetEffectMagicRed",
            ),
            # 4. 只设置亮度 (应被解释为设置白光)
            (
                {ATTR_BRIGHTNESS: 200},
                0xFF,
                (200 << 24),  # W=200, R=G=B=0
                "SetBrightnessAsWhite",
            ),
        ],
        ids=lambda x: x[3] if isinstance(x, tuple) else None,
    )
    @pytest.mark.asyncio
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
        mock_client.async_send_single_command.assert_called_with(
            self.HUB_ID, self.DEVICE_ME, self.SUB_KEY, expected_type, expected_val
        )

    @pytest.mark.asyncio
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
        # 根据文档，关灯命令是 type=0x80, val=0
        mock_client.async_send_single_command.assert_called_with(
            self.HUB_ID, self.DEVICE_ME, self.SUB_KEY, 0x80, 0
        )

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_api_failure_reverts_state(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        """测试API调用失败时，单IO RGBW灯状态会回滚。"""
        # 初始状态: on, brightness 255, color (1,2,3,255)
        initial_state = hass.states.get(self.ENTITY_ID)

        # 模拟API调用失败
        mock_client.async_send_single_command.side_effect = Exception("API Error")

        # 尝试关灯
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )

        # 验证状态已回滚
        final_state = hass.states.get(self.ENTITY_ID)
        assert final_state.state == STATE_ON
        assert final_state.attributes.get(
            ATTR_BRIGHTNESS
        ) == initial_state.attributes.get(ATTR_BRIGHTNESS)
        assert final_state.attributes.get(
            ATTR_RGBW_COLOR
        ) == initial_state.attributes.get(ATTR_RGBW_COLOR)


class TestLifeSmartDualIORGBWLight:
    """测试双IO口RGBW灯 (LifeSmartDualIORGBWLight)。"""

    ENTITY_ID = "light.dual_io_rgbw_light"
    DEVICE_ME = "light_dualrgbw"
    HUB_ID = "hub_light"
    COLOR_IO = "RGBW"
    EFFECT_IO = "DYN"

    @pytest.mark.asyncio
    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get("color_mode") == ColorMode.RGBW
        assert state.attributes.get(ATTR_RGBW_COLOR) == (0, 0, 0, 0)
        assert state.attributes.get(ATTR_EFFECT) is None

    @pytest.mark.asyncio
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
        mock_client.async_send_multi_command.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            [
                {"idx": self.COLOR_IO, "type": 0x80, "val": 0},
                {"idx": self.EFFECT_IO, "type": 0x80, "val": 0},
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

    @pytest.mark.asyncio
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
        mock_client.async_send_multi_command.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            [
                {"idx": self.COLOR_IO, "type": 0x81, "val": 1},
                {
                    "idx": self.EFFECT_IO,
                    "type": 0xFF,
                    "val": DYN_EFFECT_MAP["魔力红"],
                },
            ],
        )

    @pytest.mark.asyncio
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

        mock_client.async_send_multi_command.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            [
                {"idx": self.COLOR_IO, "type": 0xFF, "val": expected_val},
                {"idx": self.EFFECT_IO, "type": 0x80, "val": 0},
            ],
        )

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_api_failure_reverts_state(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        """测试API调用失败时，双IO RGBW灯状态会回滚。"""
        # 初始状态: on, color (0,0,0,0), no effect
        initial_state = hass.states.get(self.ENTITY_ID)

        # 模拟API调用失败
        mock_client.async_send_multi_command.side_effect = Exception("API Error")

        # 尝试设置效果
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self.ENTITY_ID, ATTR_EFFECT: "魔力红"},
            blocking=True,
        )

        # 验证状态已回滚
        final_state = hass.states.get(self.ENTITY_ID)
        assert final_state.state == initial_state.state
        assert final_state.attributes.get(ATTR_EFFECT) == initial_state.attributes.get(
            ATTR_EFFECT
        )
        assert final_state.attributes.get(
            ATTR_RGBW_COLOR
        ) == initial_state.attributes.get(ATTR_RGBW_COLOR)


class TestLifeSmartSPOTRGBLight:
    """测试SPOT RGB灯 (LifeSmartSPOTRGBLight)。"""

    ENTITY_ID = "light.spot_rgb_light_rgb"
    DEVICE_ME = "light_spotrgb"
    HUB_ID = "hub_light"
    SUB_KEY = "RGB"

    @pytest.mark.asyncio
    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get("color_mode") == ColorMode.RGB
        assert state.attributes.get(ATTR_RGB_COLOR) == (255, 128, 64)
        assert state.attributes.get(ATTR_EFFECT) is None

    @pytest.mark.asyncio
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
        mock_client.async_send_single_command.assert_called_with(
            self.HUB_ID, self.DEVICE_ME, self.SUB_KEY, 0x81, 1
        )

    @pytest.mark.asyncio
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
        mock_client.async_send_single_command.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            self.SUB_KEY,
            0xFF,
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
        mock_client.async_send_single_command.assert_called_with(
            self.HUB_ID, self.DEVICE_ME, self.SUB_KEY, 0xFF, 0x0A141E
        )

    @pytest.mark.parametrize(
        ("service_data", "expected_api_val", "test_id"),
        [
            # 1. 仅提供颜色，亮度应为全亮 (255)
            (
                {ATTR_RGB_COLOR: (255, 128, 64)},
                0xFF8040,
                "ColorOnlyFullBrightness",
            ),
            # 2. 提供颜色和全亮度
            (
                {ATTR_BRIGHTNESS: 255, ATTR_RGB_COLOR: (255, 128, 64)},
                0xFF8040,
                "ColorWithMaxBrightness",
            ),
            # 3. 提供颜色和中等亮度
            (
                {ATTR_BRIGHTNESS: 128, ATTR_RGB_COLOR: (255, 0, 0)},  # 纯红色
                0x800000,  # 亮度减半，R分量减半
                "ColorWithMediumBrightness",
            ),
            # 4. 提供颜色和低亮度
            (
                {ATTR_BRIGHTNESS: 1, ATTR_RGB_COLOR: (0, 255, 0)},  # 纯绿色
                0x000100,  # 亮度最低，G分量为1
                "ColorWithMinBrightness",
            ),
            # 5. 复杂的颜色和亮度组合
            # (255, 128, 64) @ 50% brightness -> (128, 64, 32)
            (
                {ATTR_BRIGHTNESS: 128, ATTR_RGB_COLOR: (255, 128, 64)},
                0x804020,
                "ComplexColorWithMediumBrightness",
            ),
        ],
        ids=lambda x: x[2] if isinstance(x, tuple) else None,
    )
    @pytest.mark.asyncio
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
        验证颜色和亮度组合的正确处理。

        此测试验证当同时提供 brightness 和 rgb_color 时，集成是否能正确计算
        最终的颜色值并调用底层 API。这反映了 HA 的真实颜色处理逻辑。

        Args:
            service_data: 包含有效颜色和亮度值的服务调用数据。
            expected_api_val: 经过 Home Assistant 核心颜色/亮度转换后，预期发送给 API 的十六进制值。
            test_id: 测试用例的ID。
        """
        # 准备完整的服务调用数据
        full_service_data = {ATTR_ENTITY_ID: self.ENTITY_ID, **service_data}

        # 调用服务
        await hass.services.async_call(
            LIGHT_DOMAIN, SERVICE_TURN_ON, full_service_data, blocking=True
        )

        # 验证底层 API 是否以正确的、经过亮度调整后的颜色值被调用
        mock_client.async_send_single_command.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            self.SUB_KEY,
            0xFF,
            expected_api_val,
        )

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_api_failure_reverts_state(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        """测试API调用失败时，SPOT RGB灯状态会回滚。"""
        # 初始状态: on, color (255, 128, 64)
        initial_state = hass.states.get(self.ENTITY_ID)

        # 模拟API调用失败
        mock_client.turn_off_light_switch_async.side_effect = Exception("API Error")

        # 尝试关灯
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )

        # 验证状态已回滚
        final_state = hass.states.get(self.ENTITY_ID)
        assert final_state.state == STATE_ON
        assert final_state.attributes.get(ATTR_RGB_COLOR) == (255, 128, 64)


class TestLifeSmartSPOTRGBWLight:
    """测试SPOT RGBW灯 (LifeSmartSPOTRGBWLight)。"""

    ENTITY_ID = "light.spot_rgbw_light"
    DEVICE_ME = "light_spotrgbw"
    HUB_ID = "hub_light"
    COLOR_IO = "RGBW"
    EFFECT_IO = "DYN"

    @pytest.mark.asyncio
    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get("color_mode") == ColorMode.RGBW
        assert state.attributes.get(ATTR_RGBW_COLOR) == (0x22, 0x33, 0x44, 0x11)
        assert state.attributes.get(ATTR_EFFECT) == "海浪"

    @pytest.mark.asyncio
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
        mock_client.async_send_multi_command.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            [
                {"idx": self.COLOR_IO, "type": 0x80, "val": 0},
                {"idx": self.EFFECT_IO, "type": 0x80, "val": 0},
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

    @pytest.mark.asyncio
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
        mock_client.async_send_multi_command.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            [
                {"idx": self.COLOR_IO, "type": 0x81, "val": 1},
                {
                    "idx": self.EFFECT_IO,
                    "type": 0xFF,
                    "val": DYN_EFFECT_MAP["魔力红"],
                },
            ],
        )

    @pytest.mark.asyncio
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

        mock_client.async_send_multi_command.assert_called_with(
            self.HUB_ID,
            self.DEVICE_ME,
            [
                {"idx": self.COLOR_IO, "type": 0xFF, "val": expected_val},
                {"idx": self.EFFECT_IO, "type": 0x80, "val": 0},
            ],
        )

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_api_failure_reverts_state(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        """测试API调用失败时，SPOT RGBW灯状态会回滚。"""
        # 初始状态: on, effect '海浪'
        initial_state = hass.states.get(self.ENTITY_ID)
        assert initial_state.attributes.get(ATTR_EFFECT) == "海浪"

        # 模拟API调用失败
        mock_client.async_send_multi_command.side_effect = Exception("API Error")

        # 尝试设置颜色，这会清除效果
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: self.ENTITY_ID, ATTR_RGBW_COLOR: (1, 1, 1, 1)},
            blocking=True,
        )

        # 验证状态已回滚
        final_state = hass.states.get(self.ENTITY_ID)
        assert final_state.state == STATE_ON
        assert final_state.attributes.get(ATTR_EFFECT) == "海浪"
        assert final_state.attributes.get(
            ATTR_RGBW_COLOR
        ) == initial_state.attributes.get(ATTR_RGBW_COLOR)


class TestLifeSmartCoverLight:
    """测试车库门附属灯 (LifeSmartCoverLight)。"""

    ENTITY_ID = "light.cover_light_p1"
    DEVICE_ME = "light_cover"
    HUB_ID = "hub_light"
    SUB_KEY = "P1"

    @pytest.mark.asyncio
    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_ON
        assert state.attributes.get("color_mode") == ColorMode.ONOFF

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_state_update(self, hass: HomeAssistant, setup_integration):
        unique_id = get_entity_unique_id(hass, self.ENTITY_ID)
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", {"type": 128}
        )
        await hass.async_block_till_done()
        assert hass.states.get(self.ENTITY_ID).state == STATE_OFF

    @pytest.mark.asyncio
    async def test_api_failure_reverts_state(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        """测试API调用失败时，车库门灯状态会回滚。"""
        # 初始状态: on
        assert hass.states.get(self.ENTITY_ID).state == STATE_ON

        # 模拟API调用失败
        mock_client.turn_off_light_switch_async.side_effect = Exception("API Error")

        # 尝试关灯
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: self.ENTITY_ID},
            blocking=True,
        )

        # 验证状态已回滚
        assert hass.states.get(self.ENTITY_ID).state == STATE_ON


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
        ids=["WallOutletLightOnOff", "SimpleBulbOnOff"],
    )
    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_api_failure_reverts_state(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        """测试API调用失败时，简单开关灯状态会回滚。"""
        entity_id = "light.wall_outlet_light_p1"
        device_me = "light_switch"
        sub_key = "P1"

        # 初始状态: on
        assert hass.states.get(entity_id).state == STATE_ON

        # 模拟API调用失败
        mock_client.turn_off_light_switch_async.side_effect = Exception("API Error")

        # 尝试关灯
        await hass.services.async_call(
            LIGHT_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )

        # 验证状态已回滚
        assert hass.states.get(entity_id).state == STATE_ON


class TestLifeSmartOutdoorLight(TestLifeSmartSingleIORGBWLight):
    """
    测试户外灯 (SL_LI_UG1)。
    其行为与单IO RGBW灯完全相同，因此直接继承其测试类。
    """

    ENTITY_ID = "light.outdoor_light_p1"
    DEVICE_ME = "light_outdoor"
    SUB_KEY = "P1"


# ============================================================================
# === 新增：协议细节与颜色逻辑的边际测试 ===
#
# 设计说明:
# 此测试类专注于验证灯光设备在处理颜色、亮度、效果等复杂逻辑时的边缘情况，
# 以及确保生成的 API 命令与设备协议文档精确匹配。
#
# 每个测试方法都使用一个专用的、只加载单个被测设备的 setup fixture，
# 以实现完全的测试隔离，确保断言的精确性。
# ============================================================================


class TestLightProtocolAndColorEdgeCases:
    """
    针对灯光协议细节和颜色计算逻辑的深度和边缘情况测试。
    """

    @pytest.mark.asyncio
    async def test_single_io_light_protocol_precision(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        setup_integration_single_io_rgbw_only: ConfigEntry,
    ):
        """
        测试单IO口灯(SL_SC_RGB)的 `turn_on` 服务调用是否精确匹配协议。

        根据协议文档，当设置颜色或效果时，应使用 `type=0xFF`。此测试
        旨在验证这一关键的协议细节，确保集成生成的命令是设备可以正确
        解析的。
        """
        # 定义测试中使用的常量
        entity_id = "light.single_io_rgb_light_rgb"
        hub_id = "hub_light"
        device_me = "light_singlergb"
        sub_key = "RGB"

        # 步骤 1: 设置一个RGBW颜色
        # 验证：API调用时，type 必须是 0xFF，val 是计算后的颜色值。
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, ATTR_RGBW_COLOR: (10, 20, 30, 40)},
            blocking=True,
        )
        # 断言：验证底层命令的 type 和 val 是否完全符合协议
        mock_client.async_send_single_command.assert_called_with(
            hub_id,
            device_me,
            sub_key,
            0xFF,  # 关键断言：type 必须是 0xFF
            0x280A141E,  # W=40, R=10, G=20, B=30
        )

        # 步骤 2: 设置一个动态效果
        # 验证：API调用时，type 同样必须是 0xFF，val 是效果的ID。
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "天上人间"},
            blocking=True,
        )
        # 断言：验证底层命令的 type 和 val 是否完全符合协议
        mock_client.async_send_single_command.assert_called_with(
            hub_id,
            device_me,
            sub_key,
            0xFF,  # 关键断言：type 必须是 0xFF
            DYN_EFFECT_MAP["天上人间"],
        )

    @pytest.mark.asyncio
    async def test_spot_rgb_light_color_brightness_edge_cases(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        setup_integration_spot_rgb_only: ConfigEntry,
    ):
        """
        测试SPOT RGB灯在颜色和亮度组合下的边缘计算情况。

        此测试旨在验证 Home Assistant 核心的颜色/亮度计算逻辑与我们的
        集成代码结合后，在边缘条件下（如亮度为1或0）是否能生成正确
        的最终颜色值并发送给设备。
        """
        # 定义测试中使用的常量
        entity_id = "light.spot_rgb_light_rgb"
        hub_id = "hub_light"
        device_me = "light_spotrgb"
        sub_key = "RGB"

        # 场景 1: 亮度极低 (brightness=1)
        # 预期：颜色 (255, 128, 64) 在亮度为 1/255 时，应缩放为 (1, 1, 0)。
        # 计算: R=round(255*1/255)=1, G=round(128*1/255)=1, B=round(64*1/255)=0
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: entity_id,
                ATTR_BRIGHTNESS: 1,
                ATTR_RGB_COLOR: (255, 128, 64),
            },
            blocking=True,
        )
        # 断言：验证API调用发送了正确缩放后的颜色值
        mock_client.async_send_single_command.assert_called_with(
            hub_id,
            device_me,
            sub_key,
            0xFF,
            0x010100,  # 修正后的预期值: R=1, G=1, B=0
        )

        # 场景 2: 亮度为0
        # 预期：虽然服务是 `turn_on`，但亮度为0应被视为关灯。
        # 集成代码应将此情况转换为一个明确的关灯命令。
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {
                ATTR_ENTITY_ID: entity_id,
                ATTR_BRIGHTNESS: 0,
                ATTR_RGB_COLOR: (255, 128, 64),
            },
            blocking=True,
        )
        # 断言：验证调用的是关灯方法，而不是发送颜色(0,0,0)
        mock_client.turn_off_light_switch_async.assert_called_with(
            sub_key, hub_id, device_me
        )

    @pytest.mark.asyncio
    async def test_dual_io_light_state_competition(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        setup_integration_dual_io_light_only: ConfigEntry,
    ):
        """
        测试双IO口灯在颜色和效果之间的状态竞争和互斥逻辑。

        此测试模拟用户连续切换颜色和动态效果，以验证：
        1. 设置效果时，会正确关闭颜色通道。
        2. 设置颜色时，会正确关闭效果通道。
        这确保了设备不会处于一个未定义的状态。
        """
        # 定义测试中使用的常量
        entity_id = "light.dual_io_rgbw_light"
        hub_id = "hub_light"
        device_me = "light_dualrgbw"
        color_io = "RGBW"
        effect_io = "DYN"

        # 步骤 1: 从初始状态（颜色和效果都关闭）切换到动态效果
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "天上人间"},
            blocking=True,
        )
        # 断言：效果通道被打开，颜色通道仅被置为开机状态以点亮灯珠
        mock_client.async_send_multi_command.assert_called_with(
            hub_id,
            device_me,
            [
                {"idx": color_io, "type": 0x81, "val": 1},  # 打开颜色IO以供电
                {"idx": effect_io, "type": 0xFF, "val": DYN_EFFECT_MAP["天上人间"]},
            ],
        )
        # 验证HA状态
        state = hass.states.get(entity_id)
        assert state.attributes.get(ATTR_EFFECT) == "天上人间"
        assert state.attributes.get(ATTR_RGBW_COLOR) is None

        # 步骤 2: 从动态效果切换到静态颜色
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, ATTR_RGBW_COLOR: (10, 20, 30, 40)},
            blocking=True,
        )
        # 断言：颜色通道被设置了具体值，效果通道被明确关闭
        mock_client.async_send_multi_command.assert_called_with(
            hub_id,
            device_me,
            [
                {"idx": color_io, "type": 0xFF, "val": 0x280A141E},
                {"idx": effect_io, "type": 0x80, "val": 0},  # 关闭效果IO
            ],
        )
        # 验证HA状态
        state = hass.states.get(entity_id)
        assert state.attributes.get(ATTR_EFFECT) is None
        assert state.attributes.get(ATTR_RGBW_COLOR) == (10, 20, 30, 40)

        # 步骤 3: 再次从静态颜色切换回动态效果
        await hass.services.async_call(
            LIGHT_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: entity_id, ATTR_EFFECT: "魔力红"},
            blocking=True,
        )
        # 断言：效果通道再次被打开，颜色通道被重置为简单的开机状态
        mock_client.async_send_multi_command.assert_called_with(
            hub_id,
            device_me,
            [
                {"idx": color_io, "type": 0x81, "val": 1},
                {"idx": effect_io, "type": 0xFF, "val": DYN_EFFECT_MAP["魔力红"]},
            ],
        )
        # 验证HA状态
        state = hass.states.get(entity_id)
        assert state.attributes.get(ATTR_EFFECT) == "魔力红"
        assert state.attributes.get(ATTR_RGBW_COLOR) is None
