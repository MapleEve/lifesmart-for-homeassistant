"""
针对 LifeSmart 覆盖物 (Cover) 平台的单元和集成测试。

此测试套件旨在全面验证 LifeSmartCover 实体的行为，包括：
- 平台设置逻辑，特别是对通用控制器和设备排除的处理。
- 不同设备类型（定位、非定位、车库门）的属性初始化。
- 服务调用（开、关、停、设置位置）及其乐观更新（Optimistic Update）效果。
- 通过 dispatcher 接收到状态更新后，实体状态的精确解析，
  包括对定位窗帘位置和移动方向的解析，以及对非定位窗帘停止后状态的判断。
- 对边界条件（如数据缺失）的容错能力。
"""

from unittest.mock import MagicMock, patch

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
from homeassistant.const import (
    ATTR_ENTITY_ID,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.entity_registry import async_get as async_get_entity_registry

from custom_components.lifesmart.const import *


# --- 辅助函数 ---
def find_device(devices: list, me: str):
    """通过 'me' ID 从模拟设备列表中查找特定设备。"""
    return next((d for d in devices if d.get(DEVICE_ID_KEY) == me), None)


def get_entity_unique_id(hass: HomeAssistant, entity_id: str) -> str:
    """通过 entity_id 获取实体的 unique_id。"""
    entity_registry = async_get_entity_registry(hass)
    entry = entity_registry.async_get(entity_id)
    assert entry is not None, f"实体 {entity_id} 未在注册表中找到"
    return entry.unique_id


# ==================== 测试套件 ====================


class TestCoverSetup:
    """测试 cover 平台的设置和实体创建逻辑。"""

    async def test_setup_entry_creates_all_entities(
        self, hass: HomeAssistant, setup_integration: ConfigEntry
    ):
        """
        测试平台设置是否为所有支持的窗帘设备（包括通用控制器）创建了实体。

        这是一个“快乐路径”测试，验证在标准配置下，所有符合条件的覆盖物设备
        都被成功加载为 Home Assistant 中的 cover 实体。
        """
        # 期望创建: 车库门, Dooya窗帘, 非定位窗帘, 通用控制器窗帘
        assert len(hass.states.async_entity_ids(COVER_DOMAIN)) == 4
        assert hass.states.get("cover.garage_door_p2") is not None
        assert hass.states.get("cover.living_room_curtain_p1") is not None
        assert hass.states.get("cover.bedroom_curtain_op") is not None
        assert hass.states.get("cover.generic_controller_curtain_p2") is not None

    async def test_generic_controller_not_as_cover(
        self,
        hass: HomeAssistant,
        mock_lifesmart_devices,
        mock_client,
        setup_integration,
    ):
        """
        边界测试：验证非窗帘模式的通用控制器在重载后不再作为 cover 实体活动。

        此测试验证了 `async_setup_entry` 中对通用控制器工作模式的判断逻辑。
        """
        # 确认初始状态下，通用控制器窗帘实体存在
        assert hass.states.get("cover.generic_controller_curtain_p2") is not None

        # 修改通用控制器的工作模式为非窗帘模式 (例如，设为0)
        generic_device = find_device(mock_lifesmart_devices, "cover_generic")
        generic_device["data"]["P1"]["val"] = 0

        # 使用修改后的设备列表重新加载集成
        with patch(
            "custom_components.lifesmart.LifeSmartClient", return_value=mock_client
        ):
            mock_client.get_all_device_async.return_value = mock_lifesmart_devices
            assert await hass.config_entries.async_reload(setup_integration.entry_id)
            await hass.async_block_till_done()

        # 断言：通用控制器的 cover 实体状态应变为 'unavailable'。
        # 它不会从状态机中完全消失，这是 Home Assistant 的标准行为。
        reloaded_state = hass.states.get("cover.generic_controller_curtain_p2")
        assert reloaded_state is not None, "实体对象在重载后依然存在于状态机中"
        assert (
            reloaded_state.state == "unavailable"
        ), "重载后，旧的 cover 实体状态应变为 'unavailable'"

        # 断言 cover 实体总数应减少一个
        # 注意：我们不能直接断言 len == 3，因为旧的 unavailable 实体仍然会计数。
        # 更准确的测试是检查活动实体的数量。
        active_covers = [
            s for s in hass.states.async_all(COVER_DOMAIN) if s.state != "unavailable"
        ]
        assert len(active_covers) == 3, "活动 cover 实体的数量应为3"


class TestPositionalCover:
    """测试支持位置控制的覆盖物实体 (如 Dooya 窗帘, 车库门)。"""

    ENTITY_ID = "cover.living_room_curtain_p1"
    DEVICE_ME = "cover_dooya"
    DEVICE_TYPE = "SL_DOOYA"
    HUB_ID = "hub_cover"

    @pytest.fixture
    def device(self, mock_lifesmart_devices):
        """提供当前测试类的设备字典。"""
        return find_device(mock_lifesmart_devices, self.DEVICE_ME)

    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        """测试定位窗帘的初始属性。"""
        state = hass.states.get(self.ENTITY_ID)
        assert state is not None
        assert state.attributes.get("device_class") == CoverDeviceClass.CURTAIN
        expected_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
            | CoverEntityFeature.STOP
            | CoverEntityFeature.SET_POSITION
        )
        assert state.attributes.get("supported_features") == expected_features
        assert state.attributes.get(ATTR_CURRENT_POSITION) == 100
        assert state.state == STATE_OPEN

    @pytest.mark.parametrize(
        "service, optimistic_state, client_method",
        [
            (SERVICE_OPEN_COVER, STATE_OPENING, "open_cover_async"),
            (SERVICE_CLOSE_COVER, STATE_CLOSING, "close_cover_async"),
            (SERVICE_STOP_COVER, STATE_OPEN, "stop_cover_async"),
        ],
        ids=["Open", "Close", "Stop"],
    )
    async def test_basic_services_and_optimistic_update(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        setup_integration,
        service,
        optimistic_state,
        client_method,
    ):
        """测试开/关/停服务及其乐观更新效果。"""
        await hass.services.async_call(
            COVER_DOMAIN, service, {ATTR_ENTITY_ID: self.ENTITY_ID}, blocking=True
        )
        # 验证乐观更新：在 client 方法被调用后，状态应立即改变
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == optimistic_state

        # 验证底层 client 方法被正确调用
        getattr(mock_client, client_method).assert_awaited_once_with(
            self.HUB_ID, self.DEVICE_ME, self.DEVICE_TYPE
        )

    async def test_set_position_service(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration
    ):
        """测试设置位置服务及其乐观更新。"""
        # 从100%位置设置到60%，应触发 'closing' 状态
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_SET_COVER_POSITION,
            {ATTR_ENTITY_ID: self.ENTITY_ID, ATTR_POSITION: 60},
            blocking=True,
        )
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == STATE_CLOSING
        mock_client.set_cover_position_async.assert_awaited_once_with(
            self.HUB_ID, self.DEVICE_ME, 60, self.DEVICE_TYPE
        )

    @pytest.mark.parametrize(
        "update_data, expected_pos, expected_state",
        [
            ({"val": 0, "type": 128}, 0, STATE_CLOSED),
            ({"val": 100, "type": 128}, 100, STATE_OPEN),
            ({"val": 50, "type": 128}, 50, STATE_OPEN),
            ({"val": 50 | 0x80, "type": 129}, 50, STATE_CLOSING),  # 正在关闭
            ({"val": 50, "type": 129}, 50, STATE_OPENING),  # 正在打开
        ],
        ids=["Closed", "Open", "StoppedAt50", "Closing", "Opening"],
    )
    async def test_state_update_from_dispatcher(
        self,
        hass: HomeAssistant,
        setup_integration,
        update_data,
        expected_pos,
        expected_state,
    ):
        """测试通过 dispatcher 更新定位窗帘的状态。"""
        unique_id = get_entity_unique_id(hass, self.ENTITY_ID)
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", {"P1": update_data}
        )
        await hass.async_block_till_done()

        state = hass.states.get(self.ENTITY_ID)
        assert state.attributes.get(ATTR_CURRENT_POSITION) == expected_pos
        assert state.state == expected_state


class TestNonPositionalCover:
    """测试仅支持开/关/停的覆盖物实体。"""

    ENTITY_ID = "cover.bedroom_curtain_op"
    DEVICE_ME = "cover_nonpos"
    DEVICE_TYPE = "SL_SW_WIN"
    HUB_ID = "hub_cover"

    async def test_initial_properties(self, hass: HomeAssistant, setup_integration):
        """
        测试非定位窗帘的初始属性。

        验证其设备类别、支持的特性，并确认其初始状态。
        """
        state = hass.states.get(self.ENTITY_ID)
        assert state is not None
        assert state.attributes.get("device_class") == CoverDeviceClass.CURTAIN
        expected_features = (
            CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
        )
        assert state.attributes.get("supported_features") == expected_features
        assert state.attributes.get(ATTR_CURRENT_POSITION) is None

        assert state.state == STATE_CLOSED, "初始时，非定位窗帘应默认为关闭状态"

    @pytest.mark.parametrize(
        "start_service, stop_service, expected_final_state",
        [
            (SERVICE_CLOSE_COVER, SERVICE_STOP_COVER, STATE_CLOSED),
            (SERVICE_OPEN_COVER, SERVICE_STOP_COVER, STATE_OPEN),
        ],
        ids=["CloseThenStop", "OpenThenStop"],
    )
    async def test_state_after_stop(
        self,
        hass: HomeAssistant,
        setup_integration,
        start_service,
        stop_service,
        expected_final_state,
    ):
        """
        测试非定位窗帘在“移动->停止”后的最终状态判断。

        这是对非定位窗帘核心逻辑的精确测试。它验证了实体能否正确记录
        最后一次的移动方向，并在停止后据此判断其最终状态。
        """
        unique_id = get_entity_unique_id(hass, self.ENTITY_ID)

        # 1. 模拟开始移动
        await hass.services.async_call(
            COVER_DOMAIN, start_service, {ATTR_ENTITY_ID: self.ENTITY_ID}, blocking=True
        )
        # 2. 模拟设备上报正在移动的状态，以更新内部的 `_last_known_is_opening` 标志
        moving_data = {"OP": {"type": 128}, "CL": {"type": 128}, "ST": {"type": 128}}
        if start_service == SERVICE_OPEN_COVER:
            moving_data["OP"]["type"] = 129
        else:
            moving_data["CL"]["type"] = 129
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", moving_data
        )
        await hass.async_block_till_done()

        # 3. 模拟发送停止命令
        await hass.services.async_call(
            COVER_DOMAIN, stop_service, {ATTR_ENTITY_ID: self.ENTITY_ID}, blocking=True
        )
        # 4. 模拟设备上报已停止的状态
        stopped_data = {"OP": {"type": 128}, "CL": {"type": 128}, "ST": {"type": 128}}
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", stopped_data
        )
        await hass.async_block_till_done()

        # 5. 验证最终状态
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == expected_final_state

    async def test_update_with_missing_data(
        self, hass: HomeAssistant, setup_integration
    ):
        """边界测试：当 dispatcher 推送的数据不完整时，实体不应报错或状态错乱。"""
        unique_id = get_entity_unique_id(hass, self.ENTITY_ID)
        initial_state = hass.states.get(self.ENTITY_ID)

        # 发送一个不包含任何窗帘IO口的数据
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", {"OTHER_KEY": {}}
        )
        await hass.async_block_till_done()

        # 状态应保持不变
        new_state = hass.states.get(self.ENTITY_ID)
        assert new_state.state == initial_state.state
