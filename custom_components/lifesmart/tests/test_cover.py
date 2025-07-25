"""Unit and integration tests for the LifeSmart cover platform."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_POSITION,
    DOMAIN as COVER_DOMAIN,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_SET_COVER_POSITION,
    SERVICE_STOP_COVER,
    CoverDeviceClass,
    CoverEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_ENTITY_ID, STATE_CLOSED, STATE_OPEN, STATE_CLOSING
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from custom_components.lifesmart.const import *
from custom_components.lifesmart.cover import async_setup_entry

pytestmark = pytest.mark.asyncio


# --- 辅助函数 ---
def find_device(devices: list, me: str):
    """通过 'me' ID 从模拟设备列表中查找特定设备。"""
    return next((d for d in devices if d.get(DEVICE_ID_KEY) == me), None)


# --- 测试套件 ---


@pytest.mark.asyncio
class TestCoverSetup:
    """测试 cover 平台的设置和实体创建。"""

    async def test_setup_entry_creates_all_entities(
        self, hass: HomeAssistant, setup_integration: ConfigEntry
    ):
        """测试是否为所有支持的窗帘设备（包括通用控制器）创建了实体。"""
        # 期望创建: Garage Door, Dooya Curtain, Non-Positional Curtain, Generic Controller Curtain
        assert len(hass.states.async_entity_ids(COVER_DOMAIN)) == 4
        assert hass.states.get("cover.garage_door_p2") is not None
        assert hass.states.get("cover.living_room_curtain_p1") is not None
        assert hass.states.get("cover.bedroom_curtain_op") is not None
        assert hass.states.get("cover.generic_controller_curtain_p2") is not None

    async def test_setup_entry_with_exclusions(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        mock_config_entry: ConfigEntry,
        mock_lifesmart_devices: list,
    ):
        """测试被排除的设备不会被添加。"""
        mock_config_entry.add_to_hass(hass)

        # 更新配置以排除一个设备
        hass.config_entries.async_update_entry(
            mock_config_entry,
            options={
                CONF_EXCLUDE_ITEMS: "cover_dooya",  # 排除 Dooya 窗帘
                CONF_EXCLUDE_AGTS: "",
            },
        )
        await hass.async_block_till_done()

        async_add_entities_mock = AsyncMock()
        hass.data.setdefault(DOMAIN, {})[mock_config_entry.entry_id] = {
            "client": mock_client,
            "devices": mock_lifesmart_devices,
        }

        await async_setup_entry(hass, mock_config_entry, async_add_entities_mock)
        await hass.async_block_till_done()

        created_entities = async_add_entities_mock.call_args[0][0]
        created_names = {entity.name for entity in created_entities}

        assert "Garage Door P2" in created_names
        assert "Living Room Curtain P1" not in created_names  # 验证已被排除
        assert "Bedroom Curtain OP" in created_names
        assert "Generic Controller Curtain P2" in created_names
        assert len(created_names) == 3


@pytest.mark.asyncio
class TestCoverEntityProperties:
    """测试 LifeSmartCover 实体的属性和初始化。"""

    @pytest.mark.parametrize(
        "device_me, sub_key, expected_name, expected_class, expected_features",
        [
            (
                "cover_garage",
                "P2",
                "Garage Door P2",
                CoverDeviceClass.GARAGE,
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
                | CoverEntityFeature.STOP
                | CoverEntityFeature.SET_POSITION,
            ),
            (
                "cover_dooya",
                "P1",
                "Living Room Curtain P1",
                CoverDeviceClass.CURTAIN,
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
                | CoverEntityFeature.STOP
                | CoverEntityFeature.SET_POSITION,
            ),
            (
                "cover_nonpos",
                "OP",
                "Bedroom Curtain OP",
                CoverDeviceClass.CURTAIN,
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
                | CoverEntityFeature.STOP,
            ),
            (
                "cover_generic",
                "P2",
                "Generic Controller Curtain P2",
                CoverDeviceClass.CURTAIN,
                CoverEntityFeature.OPEN
                | CoverEntityFeature.CLOSE
                | CoverEntityFeature.STOP,
            ),
        ],
        ids=[
            "Garage",
            "PositionalCurtain",
            "NonPositionalCurtain",
            "GenericControllerCurtain",
        ],
    )
    async def test_entity_initialization(
        self,
        hass: HomeAssistant,
        setup_integration: ConfigEntry,
        mock_lifesmart_devices: list,
        device_me,
        sub_key,
        expected_name,
        expected_class,
        expected_features,
    ):
        """测试不同类型窗帘实体的特性、设备类别和名称。"""
        device = find_device(mock_lifesmart_devices, device_me)
        entity_id = f"cover.{device[DEVICE_NAME_KEY].lower().replace(' ', '_')}_{sub_key.lower()}"

        state = hass.states.get(entity_id)
        assert state is not None, f"实体 {entity_id} 未被创建"

        assert state.name == expected_name
        assert state.attributes.get("device_class") == expected_class
        assert state.attributes.get("supported_features") == expected_features


@pytest.mark.asyncio
class TestCoverStateAndServices:
    """测试窗帘实体的状态更新和服务调用。"""

    @pytest.mark.parametrize(
        "device_me, io_key, data, expected_pos, exp_state",
        [
            ("cover_garage", "P2", {"val": 0, "type": 128}, 0, STATE_CLOSED),
            ("cover_dooya", "P1", {"val": 100, "type": 128}, 100, STATE_OPEN),
            ("cover_garage", "P2", {"val": 50, "type": 128}, 50, STATE_OPEN),
            ("cover_dooya", "P1", {"val": 50 | 0x80, "type": 129}, 50, STATE_CLOSING),
        ],
        ids=["Closed", "Open", "Stopped", "Closing"],
    )
    async def test_positional_cover_state_update(
        self,
        hass: HomeAssistant,
        setup_integration: ConfigEntry,
        mock_lifesmart_devices: list,
        device_me,
        io_key,
        data,
        expected_pos,
        exp_state,
    ):
        """测试支持位置的窗帘的状态解析。"""
        device = find_device(mock_lifesmart_devices, device_me)
        entity_id = f"cover.{device[DEVICE_NAME_KEY].lower().replace(' ', '_')}_{io_key.lower()}"
        entity_registry = async_get_entity_registry(hass)
        entry = entity_registry.async_get(entity_id)

        full_update_data = device[DEVICE_DATA_KEY].copy()
        full_update_data[io_key] = data

        async_dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entry.unique_id}",
            full_update_data,
        )
        await hass.async_block_till_done()

        state = hass.states.get(entity_id)
        assert state.attributes.get(ATTR_CURRENT_POSITION) == expected_pos
        assert state.state == exp_state

    async def test_non_positional_cover_state_after_stop(
        self,
        hass: HomeAssistant,
        setup_integration: ConfigEntry,
        mock_lifesmart_devices: list,
    ):
        """测试非定位窗帘在停止后的状态变化。"""
        entity_id = "cover.bedroom_curtain_op"
        entity_registry = async_get_entity_registry(hass)
        entry = entity_registry.async_get(entity_id)
        assert entry is not None, f"实体 {entity_id} 未在注册表中找到"

        device_in_hass = find_device(
            hass.data[DOMAIN][setup_integration.entry_id]["devices"], "cover_nonpos"
        )

        # 1. 模拟开始关闭
        closing_data = device_in_hass[DEVICE_DATA_KEY].copy()
        closing_data["CL"] = {"val": 0, "type": 129}  # is_closing = True
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entry.unique_id}", closing_data
        )
        await hass.async_block_till_done()

        state_closing = hass.states.get(entity_id)
        assert state_closing.state == STATE_CLOSING

        # 2. 模拟停止关闭
        stopped_data = device_in_hass[DEVICE_DATA_KEY].copy()
        stopped_data["CL"] = {"val": 0, "type": 128}  # is_closing = False
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entry.unique_id}", stopped_data
        )
        await hass.async_block_till_done()

        state_stopped = hass.states.get(entity_id)
        assert state_stopped.state == STATE_CLOSED

    @pytest.mark.parametrize(
        "device_me, entity_id_suffix",
        [
            ("cover_dooya", "p1"),
            ("cover_garage", "p2"),
            ("cover_generic", "p2"),
        ],
        ids=["PositionalCurtain", "GarageDoor", "GenericController"],
    )
    async def test_service_calls(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        setup_integration: ConfigEntry,
        mock_lifesmart_devices: list,
        device_me,
        entity_id_suffix,
    ):
        """测试所有类型的窗帘服务调用是否正确。"""
        device = find_device(mock_lifesmart_devices, device_me)
        entity_id = f"cover.{device[DEVICE_NAME_KEY].lower().replace(' ', '_')}_{entity_id_suffix}"

        # 重置 mock 以进行干净的断言
        mock_client.reset_mock()

        # --- 测试 Open, Close, Stop ---
        await hass.services.async_call(
            COVER_DOMAIN, SERVICE_OPEN_COVER, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )
        mock_client.open_cover_async.assert_awaited_once_with(
            device[HUB_ID_KEY], device[DEVICE_ID_KEY], device[DEVICE_TYPE_KEY]
        )

        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )
        mock_client.close_cover_async.assert_awaited_once_with(
            device[HUB_ID_KEY], device[DEVICE_ID_KEY], device[DEVICE_TYPE_KEY]
        )

        await hass.services.async_call(
            COVER_DOMAIN, SERVICE_STOP_COVER, {ATTR_ENTITY_ID: entity_id}, blocking=True
        )
        mock_client.stop_cover_async.assert_awaited_once_with(
            device[HUB_ID_KEY], device[DEVICE_ID_KEY], device[DEVICE_TYPE_KEY]
        )

        # --- 仅对支持位置的设备测试 Set Position ---
        state = hass.states.get(entity_id)
        if state.attributes.get("supported_features") & CoverEntityFeature.SET_POSITION:
            await hass.services.async_call(
                COVER_DOMAIN,
                SERVICE_SET_COVER_POSITION,
                {ATTR_ENTITY_ID: entity_id, ATTR_POSITION: 60},
                blocking=True,
            )
            mock_client.set_cover_position_async.assert_awaited_once_with(
                device[HUB_ID_KEY], device[DEVICE_ID_KEY], 60, device[DEVICE_TYPE_KEY]
            )

    async def test_data_dispatcher(
        self,
        hass: HomeAssistant,
        setup_integration: ConfigEntry,
    ):
        """测试实体是否能通过特定和全局 dispatcher 更新。"""
        entity_id = "cover.living_room_curtain_p1"
        entity_registry = async_get_entity_registry(hass)
        entry = entity_registry.async_get(entity_id)

        assert hass.states.get(entity_id).attributes.get(ATTR_CURRENT_POSITION) == 100

        # 测试特定实体更新
        device_in_hass = find_device(
            hass.data[DOMAIN][setup_integration.entry_id]["devices"], "cover_dooya"
        )
        new_data_specific = device_in_hass[DEVICE_DATA_KEY].copy()
        new_data_specific["P1"] = {"val": 30, "type": 128}

        async_dispatcher_send(
            hass,
            f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entry.unique_id}",
            new_data_specific,
        )
        await hass.async_block_till_done()
        assert hass.states.get(entity_id).attributes.get(ATTR_CURRENT_POSITION) == 30

        # 测试全局刷新更新
        device_in_hass[DEVICE_DATA_KEY]["P1"] = {"val": 45, "type": 128}

        async_dispatcher_send(hass, LIFESMART_SIGNAL_UPDATE_ENTITY)
        await hass.async_block_till_done()
        assert hass.states.get(entity_id).attributes.get(ATTR_CURRENT_POSITION) == 45
