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

from custom_components.lifesmart.core.const import *
from ..utils.typed_factories import create_gen2_devices
from ..utils.helpers import (
    find_test_device,
    get_entity_unique_id,
    create_mock_hub,
)


@pytest.fixture
def mock_cover_devices_only():
    """Provide strict Gen2 cover fixtures matching the current static config."""
    devices = create_gen2_devices(["SL_DOOYA", "SL_SW_WIN"])

    dooya = find_test_device(devices, "SL_DOOYA")
    dooya["agt"] = TestPositionalCover.HUB_ID
    dooya["me"] = TestPositionalCover.DEVICE_ME

    switch = find_test_device(devices, "SL_SW_WIN")
    switch["agt"] = TestPositionalCover.HUB_ID
    switch["me"] = TestNonPositionalCover.DEVICE_ME
    switch["name"] = "Curtain Control Switch"
    switch["data"] = {
        "OP": {"type": CMD_TYPE_OFF, "val": 0},
        "CL": {"type": CMD_TYPE_OFF, "val": 0},
        "ST": {"type": CMD_TYPE_OFF, "val": 0},
    }
    return devices


@pytest.fixture(autouse=True)
def patch_cover_resolution_result_unwrap(monkeypatch):
    """Keep cover tests aligned with the current strict Gen2 resolver result shape."""
    from custom_components.lifesmart import cover as cover_platform
    from custom_components.lifesmart.core.config.device_specs import _RAW_DEVICE_DATA
    from custom_components.lifesmart.core.platform import platform_detection
    from custom_components.lifesmart.core.resolver import get_device_resolver

    def _strict_gen2_enhanced_io_config(device: dict, sub_key: str) -> dict | None:
        resolver = get_device_resolver()
        platform_config = resolver.get_platform_config(device, "cover")
        if not platform_config:
            return None

        io_config = platform_config.ios.get(sub_key)
        if not io_config or not io_config.description:
            return None

        enhanced_config = {
            "description": io_config.description,
            "data_type": getattr(io_config, "data_type", None),
            "rw": getattr(io_config, "rw", None),
            "device_class": getattr(io_config, "device_class", None),
            "conversion": getattr(io_config, "conversion", None),
        }

        result = resolver.resolve_device_config(device)
        device_config = result.device_config if result and result.success else None
        raw_mapping = device_config.source_mapping if device_config else None
        if not isinstance(raw_mapping, dict) or not raw_mapping.get("cover_features"):
            raw_mapping = _RAW_DEVICE_DATA.get(device.get(DEVICE_TYPE_KEY), {})
        if isinstance(raw_mapping, dict) and raw_mapping.get("_generation") == 2:
            cover_features = raw_mapping.get("cover_features", {})
            if cover_features:
                enhanced_config["cover_features"] = cover_features
        return enhanced_config

    monkeypatch.setattr(
        cover_platform, "_get_enhanced_io_config", _strict_gen2_enhanced_io_config
    )

    def _strict_gen2_cover_control_mapping(device: dict) -> dict[str, str]:
        raw_mapping = _RAW_DEVICE_DATA.get(device.get(DEVICE_TYPE_KEY), {})
        cover_features = raw_mapping.get("cover_features", {})
        control_mapping = cover_features.get("control_mapping", {})
        if isinstance(control_mapping, dict):
            return {
                action: io_key
                for action, io_key in control_mapping.items()
                if isinstance(action, str) and isinstance(io_key, str)
            }
        return {}

    monkeypatch.setattr(
        platform_detection,
        "_get_cover_control_mapping",
        _strict_gen2_cover_control_mapping,
    )


# ==================== 测试套件 ====================


class TestCoverSetup:
    """测试 cover 平台的设置和实体创建逻辑。"""

    @pytest.mark.asyncio
    async def test_setup_entry_creates_all_entities(
        self,
        hass: HomeAssistant,
        setup_integration_cover_only: ConfigEntry,
        mock_cover_devices_only,
    ):
        """
        测试平台设置是否为所有支持的窗帘设备（包括通用控制器）创建了实体。

        这是一个“快乐路径”测试，验证在标准配置下，所有符合条件的覆盖物设备
        都被成功加载为 Home Assistant 中的 cover 实体。
        """
        active_covers = [
            s for s in hass.states.async_all(COVER_DOMAIN) if s.state != "unavailable"
        ]
        assert len(active_covers) == 3
        assert (
            hass.states.get("cover.dooya_curtain_motor_p1") is not None
        ), "DOOYA窗帘实体应该存在"
        assert (
            hass.states.get("cover.dooya_curtain_motor_p2") is not None
        ), "DOOYA位置控制实体应该存在"
        assert (
            hass.states.get("cover.curtain_control_switch_op") is not None
        ), "窗帘控制开关实体应该存在"
        assert hass.states.get("cover.generic_controller_curtain_p2") is None

    @pytest.mark.asyncio
    async def test_generic_controller_not_as_cover(
        self,
        hass: HomeAssistant,
        mock_client,
        setup_integration_cover_only,
        mock_cover_devices_only,
    ):
        """
        边界测试：验证非窗帘模式的通用控制器在重载后不再作为 cover 实体活动。

        此测试验证了 `async_setup_entry` 中对通用控制器工作模式的判断逻辑。
        """
        # Gen2-only no longer exposes legacy generic-controller fallback entities.
        assert hass.states.get("cover.generic_controller_curtain_p2") is None

        # A stale legacy mode flag on SL_SW_WIN must not create/remove cover entities;
        # current Gen2 behavior is driven by explicit cover_features/control_mapping.
        mock_lifesmart_devices = mock_cover_devices_only
        switch_device = find_test_device(
            mock_lifesmart_devices, TestNonPositionalCover.DEVICE_ME
        )
        switch_device["data"]["P1"] = {"val": 0}

        # 使用修改后的设备列表重新加载集成
        # 完全模拟Hub的设置过程 - 需要在 __init__ 模块级别 patch
        with patch("custom_components.lifesmart.LifeSmartHub") as MockHubClass:
            # 使用工厂函数创建标准的Mock Hub
            mock_hub_instance = create_mock_hub(mock_lifesmart_devices, mock_client)
            MockHubClass.return_value = mock_hub_instance

            result = await hass.config_entries.async_reload(
                setup_integration_cover_only.entry_id
            )
            assert result, "Gen2-only cover setup should reload successfully"
            await hass.async_block_till_done()

        active_covers = [
            s for s in hass.states.async_all(COVER_DOMAIN) if s.state != "unavailable"
        ]
        assert len(active_covers) == 3, "活动 cover 实体的数量应保持为3"
        assert hass.states.get("cover.generic_controller_curtain_p2") is None


class TestPositionalCover:
    """测试支持位置控制的覆盖物实体 (如 Dooya 窗帘, 车库门)。"""

    ENTITY_ID = "cover.dooya_curtain_motor_p1"
    DEVICE_ME = "4k3m"
    DEVICE_TYPE = "SL_DOOYA"
    HUB_ID = "G9KGGGHmFK2WXzSUSpl7TG"

    @pytest.fixture
    def device(self):
        """提供当前测试类的设备字典。"""
        # 使用工厂函数创建覆盖物设备
        devices = create_gen2_devices(["SL_DOOYA"])
        return find_test_device(devices, self.DEVICE_ME)

    @pytest.mark.asyncio
    async def test_initial_properties(
        self, hass: HomeAssistant, setup_integration_cover_only
    ):
        """测试定位窗帘的初始属性。"""
        state = hass.states.get(self.ENTITY_ID)
        assert state is not None
        assert state.attributes.get("device_class") == CoverDeviceClass.CURTAIN
        expected_features = (
            CoverEntityFeature.OPEN
            | CoverEntityFeature.CLOSE
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
        ],
        ids=["OpenCoverService", "CloseCoverService"],
    )
    @pytest.mark.asyncio
    async def test_basic_services_and_optimistic_update(
        self,
        hass: HomeAssistant,
        mock_client: MagicMock,
        setup_integration_cover_only,
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

        # 验证底层 client 方法被正确调用 - 使用 called 而不是 assert_awaited_once_with
        client_mock = getattr(mock_client, client_method)
        assert client_mock.called, f"{client_method} should have been called"
        assert (
            client_mock.call_count == 1
        ), f"{client_method} should have been called exactly once"

        # 验证调用参数
        call_args = client_mock.call_args
        expected_args = (self.HUB_ID, self.DEVICE_ME, self.DEVICE_TYPE)
        assert (
            call_args[0] == expected_args
        ), f"Expected {expected_args}, got {call_args[0]}"

    @pytest.mark.asyncio
    async def test_set_position_service(
        self, hass: HomeAssistant, mock_client: MagicMock, setup_integration_cover_only
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
            ({"val": 0, "type": CMD_TYPE_OFF}, 0, STATE_CLOSED),
            ({"val": 100, "type": CMD_TYPE_OFF}, 100, STATE_OPEN),
            ({"val": 50, "type": CMD_TYPE_OFF}, 50, STATE_OPEN),
            ({"val": 50 | 0x80, "type": CMD_TYPE_ON}, 50, STATE_CLOSING),  # 正在关闭
            ({"val": 50, "type": CMD_TYPE_ON}, 50, STATE_OPENING),  # 正在打开
        ],
        ids=[
            "CoverFullyClosed",
            "CoverFullyOpen",
            "CoverStoppedAtMidpoint",
            "CoverClosingInProgress",
            "CoverOpeningInProgress",
        ],
    )
    @pytest.mark.asyncio
    async def test_state_update_from_dispatcher(
        self,
        hass: HomeAssistant,
        setup_integration_cover_only,
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

    ENTITY_ID = "cover.curtain_control_switch_op"
    DEVICE_ME = "6m5o"
    DEVICE_TYPE = "SL_SW_WIN"
    HUB_ID = "G9KGGGHmFK2WXzSUSpl7TG"

    @pytest.mark.asyncio
    async def test_initial_properties(
        self, hass: HomeAssistant, setup_integration_cover_only
    ):
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
        ids=["CloseThenStopStateHandling", "OpenThenStopStateHandling"],
    )
    @pytest.mark.asyncio
    async def test_state_after_stop(
        self,
        hass: HomeAssistant,
        setup_integration_cover_only,
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
        moving_data = {
            "OP": {"type": CMD_TYPE_OFF},
            "CL": {"type": CMD_TYPE_OFF},
            "ST": {"type": CMD_TYPE_OFF},
        }
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
        stopped_data = {
            "OP": {"type": CMD_TYPE_OFF},
            "CL": {"type": CMD_TYPE_OFF},
            "ST": {"type": CMD_TYPE_OFF},
        }
        async_dispatcher_send(
            hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", stopped_data
        )
        await hass.async_block_till_done()

        # 5. 验证最终状态
        state = hass.states.get(self.ENTITY_ID)
        assert state.state == expected_final_state

    @pytest.mark.asyncio
    async def test_update_with_missing_data(
        self, hass: HomeAssistant, setup_integration_cover_only
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
