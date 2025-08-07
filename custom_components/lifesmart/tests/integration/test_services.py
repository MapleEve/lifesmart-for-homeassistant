"""
测试 Services 模块的服务管理功能。

此测试文件专门测试 services.py 中的 LifeSmartServiceManager 类，包括：
- 服务的注册和管理
- 红外命令发送服务
- 场景触发服务
- 点动开关服务
- 错误处理和参数验证
"""

from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from custom_components.lifesmart.core.compatibility import create_service_call
from custom_components.lifesmart.core.const import (
    DEVICE_ID_KEY,
    DOMAIN,
    HUB_ID_KEY,
    SUBDEVICE_INDEX_KEY,
)
from custom_components.lifesmart.services import LifeSmartServiceManager


class TestLifeSmartServiceManager:
    """测试 LifeSmartServiceManager 服务管理器。"""

    @pytest.fixture
    def mock_client(self):
        """提供模拟的客户端。"""
        client = AsyncMock()
        client.async_send_ir_key = AsyncMock()
        client.async_ir_control = AsyncMock()
        client.async_set_scene = AsyncMock()
        client.press_switch_async = AsyncMock()
        return client

    @pytest.fixture
    def service_manager(self, hass: HomeAssistant, mock_client):
        """提供服务管理器实例。"""
        service_manager = LifeSmartServiceManager(hass, mock_client)
        # 确保客户端方法是 AsyncMock
        service_manager.client = mock_client
        return service_manager

    async def test_service_registration(self, hass: HomeAssistant, service_manager):
        """测试服务注册功能。"""
        service_manager.register_services()

        # 验证所有服务都已注册
        assert hass.services.has_service(DOMAIN, "send_ir_keys"), "应该注册红外发送服务"
        assert hass.services.has_service(DOMAIN, "send_ackeys"), "应该注册空调红外服务"
        assert hass.services.has_service(
            DOMAIN, "trigger_scene"
        ), "应该注册场景触发服务"
        assert hass.services.has_service(DOMAIN, "press_switch"), "应该注册点动开关服务"

    async def test_send_ir_keys_service(
        self, hass: HomeAssistant, service_manager, mock_client
    ):
        """测试发送红外按键服务。"""
        service_manager.register_services()

        # 准备服务调用数据
        service_data = {
            HUB_ID_KEY: "test_hub",
            "ai": "test_ai",
            DEVICE_ID_KEY: "test_device",
            "category": "tv",
            "brand": "samsung",
            "keys": ["power", "volume_up"],
        }

        # 创建服务调用
        call = create_service_call(DOMAIN, "send_ir_keys", service_data, hass)

        # 执行服务
        await service_manager._send_ir_keys(call)

        # 验证客户端方法被正确调用
        mock_client.async_send_ir_key.assert_called_once_with(
            "test_hub",
            "test_device",
            "tv",
            "samsung",
            ["power", "volume_up"],
            "test_ai",
            "",
        )

    async def test_send_ir_keys_service_with_exception(
        self, hass: HomeAssistant, service_manager, mock_client
    ):
        """测试红外按键服务遇到异常的情况。"""
        service_manager.register_services()

        # 设置客户端抛出异常
        mock_client.async_send_ir_key.side_effect = Exception("IR command failed")

        service_data = {
            HUB_ID_KEY: "test_hub",
            "ai": "test_ai",
            DEVICE_ID_KEY: "test_device",
            "category": "tv",
            "brand": "samsung",
            "keys": ["power"],
        }

        call = create_service_call(DOMAIN, "send_ir_keys", service_data, hass)

        # 服务不应该抛出异常，而是记录错误
        await service_manager._send_ir_keys(call)

        mock_client.async_send_ir_key.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_ackeys_service(
        self, hass: HomeAssistant, service_manager, mock_client
    ):
        """测试发送空调按键服务。"""
        service_manager.register_services()

        # 准备空调服务调用数据
        service_data = {
            HUB_ID_KEY: "test_hub",
            "ai": "test_ai_ac",
            DEVICE_ID_KEY: "test_spot",
            "category": "ac",
            "brand": "daikin",
            "keys": "power",
            "power": 1,
            "mode": 1,
            "temp": 26,
            "wind": 2,
            "swing": 0,
        }

        # 创建服务调用
        call = create_service_call(DOMAIN, "send_ackeys", service_data, hass)

        # 执行服务
        await service_manager._send_ackeys(call)

        # 验证客户端方法被正确调用
        expected_options = {
            "agt": "test_hub",
            "me": "test_spot",
            "ai": "test_ai_ac",
            "category": "ac",
            "brand": "daikin",
            "key": "power",
            "power": 1,
            "mode": 1,
            "temp": 26,
            "wind": 2,
            "swing": 0,
        }
        mock_client.async_ir_control.assert_called_once_with(
            "test_spot", expected_options
        )

    @pytest.mark.asyncio
    async def test_send_ackeys_service_with_exception(
        self, hass: HomeAssistant, service_manager, mock_client
    ):
        """测试空调按键服务遇到异常的情况。"""
        service_manager.register_services()

        # 设置客户端抛出异常
        mock_client.async_ir_control.side_effect = Exception("AC IR command failed")

        service_data = {
            HUB_ID_KEY: "test_hub",
            "ai": "test_ai_ac",
            DEVICE_ID_KEY: "test_spot",
            "category": "ac",
            "brand": "gree",
            "keys": "temp",
            "power": 1,
            "mode": 2,
            "temp": 24,
            "wind": 1,
            "swing": 1,
        }

        call = create_service_call(DOMAIN, "send_ackeys", service_data, hass)

        # 服务不应该抛出异常，而是记录错误
        await service_manager._send_ackeys(call)

        mock_client.async_ir_control.assert_called_once()

    @pytest.mark.asyncio
    async def test_trigger_scene_service_success(
        self, hass: HomeAssistant, service_manager, mock_client
    ):
        """测试触发场景服务成功的情况。"""
        service_manager.register_services()

        service_data = {
            "agt": "test_hub",
            "name": "scene_123",
        }

        call = create_service_call(DOMAIN, "trigger_scene", service_data, hass)

        await service_manager._trigger_scene(call)

        mock_client.async_set_scene.assert_called_once_with("test_hub", "scene_123")

    @pytest.mark.asyncio
    async def test_trigger_scene_service_missing_agt(
        self, hass: HomeAssistant, service_manager, mock_client
    ):
        """测试触发场景服务缺少 agt 参数的情况。"""
        service_manager.register_services()

        service_data = {
            "name": "scene_123",
            # 缺少 agt
        }

        call = create_service_call(DOMAIN, "trigger_scene", service_data, hass)

        # 应该抛出 HomeAssistantError
        with pytest.raises(HomeAssistantError, match="'agt' 参数不能为空"):
            await service_manager._trigger_scene(call)

        # 不应该调用客户端方法
        mock_client.async_set_scene.assert_not_called()

    @pytest.mark.asyncio
    async def test_trigger_scene_service_missing_name(
        self, hass: HomeAssistant, service_manager, mock_client
    ):
        """测试触发场景服务缺少 name 参数的情况。"""
        service_manager.register_services()

        service_data = {
            "agt": "test_hub",
            # 缺少 name
        }

        call = create_service_call(DOMAIN, "trigger_scene", service_data, hass)

        # 应该抛出 HomeAssistantError
        with pytest.raises(
            HomeAssistantError, match="'name' 和 'id' 参数必须提供其中一个"
        ):
            await service_manager._trigger_scene(call)

        # 不应该调用客户端方法
        mock_client.async_set_scene.assert_not_called()

    @pytest.mark.asyncio
    async def test_trigger_scene_service_with_exception(
        self, hass: HomeAssistant, service_manager, mock_client
    ):
        """测试触发场景服务遇到异常的情况。"""
        service_manager.register_services()

        mock_client.async_set_scene.side_effect = Exception("Scene trigger failed")

        service_data = {
            "agt": "test_hub",
            "name": "scene_123",
        }

        call = create_service_call(DOMAIN, "trigger_scene", service_data, hass)

        # 服务不应该抛出异常
        await service_manager._trigger_scene(call)

        mock_client.async_set_scene.assert_called_once()

    @pytest.mark.asyncio
    async def test_press_switch_service_success(
        self, hass: HomeAssistant, service_manager, mock_client
    ):
        """测试点动开关服务成功的情况。"""
        service_manager.register_services()

        # 创建模拟实体状态
        entity_attributes = {
            HUB_ID_KEY: "test_hub",
            DEVICE_ID_KEY: "test_device",
            SUBDEVICE_INDEX_KEY: "L1",
        }

        hass.states.async_set("switch.test_switch", "on", attributes=entity_attributes)

        service_data = {
            "entity_id": "switch.test_switch",
            "duration": 2000,
        }

        call = create_service_call(DOMAIN, "press_switch", service_data, hass)

        await service_manager._press_switch(call)

        mock_client.press_switch_async.assert_called_once_with(
            "L1", "test_hub", "test_device", 2000
        )

    @pytest.mark.asyncio
    async def test_press_switch_service_default_duration(
        self, hass: HomeAssistant, service_manager, mock_client
    ):
        """测试点动开关服务使用默认持续时间。"""
        service_manager.register_services()

        entity_attributes = {
            HUB_ID_KEY: "test_hub",
            DEVICE_ID_KEY: "test_device",
            SUBDEVICE_INDEX_KEY: "L1",
        }

        hass.states.async_set("switch.test_switch", "on", attributes=entity_attributes)

        service_data = {
            "entity_id": "switch.test_switch",
            # 没有指定 duration，应该使用默认值 1000
        }

        call = create_service_call(DOMAIN, "press_switch", service_data, hass)

        await service_manager._press_switch(call)

        mock_client.press_switch_async.assert_called_once_with(
            "L1", "test_hub", "test_device", 1000
        )

    @pytest.mark.asyncio
    async def test_press_switch_service_missing_entity_id(
        self, hass: HomeAssistant, service_manager, mock_client
    ):
        """测试点动开关服务缺少 entity_id 参数。"""
        service_manager.register_services()

        service_data = {
            "duration": 1000,
            # 缺少 entity_id
        }

        call = create_service_call(DOMAIN, "press_switch", service_data, hass)

        await service_manager._press_switch(call)

        # 不应该调用客户端方法
        mock_client.press_switch_async.assert_not_called()

    @pytest.mark.asyncio
    async def test_press_switch_service_entity_not_found(
        self, hass: HomeAssistant, service_manager, mock_client
    ):
        """测试点动开关服务实体不存在的情况。"""
        service_manager.register_services()

        service_data = {
            "entity_id": "switch.nonexistent_switch",
            "duration": 1000,
        }

        call = create_service_call(DOMAIN, "press_switch", service_data, hass)

        await service_manager._press_switch(call)

        # 不应该调用客户端方法
        mock_client.press_switch_async.assert_not_called()

    @pytest.mark.asyncio
    async def test_press_switch_service_missing_attributes(
        self, hass: HomeAssistant, service_manager, mock_client
    ):
        """测试点动开关服务实体缺少必要属性的情况。"""
        service_manager.register_services()

        # 创建缺少必要属性的实体状态
        hass.states.async_set("switch.test_switch", "on", attributes={})

        service_data = {
            "entity_id": "switch.test_switch",
            "duration": 1000,
        }

        call = create_service_call(DOMAIN, "press_switch", service_data, hass)

        await service_manager._press_switch(call)

        # 不应该调用客户端方法
        mock_client.press_switch_async.assert_not_called()

    @pytest.mark.asyncio
    async def test_press_switch_service_with_exception(
        self, hass: HomeAssistant, service_manager, mock_client
    ):
        """测试点动开关服务遇到异常的情况。"""
        service_manager.register_services()

        mock_client.press_switch_async.side_effect = Exception("Press switch failed")

        entity_attributes = {
            HUB_ID_KEY: "test_hub",
            DEVICE_ID_KEY: "test_device",
            SUBDEVICE_INDEX_KEY: "L1",
        }

        hass.states.async_set("switch.test_switch", "on", attributes=entity_attributes)

        service_data = {
            "entity_id": "switch.test_switch",
            "duration": 1000,
        }

        call = create_service_call(DOMAIN, "press_switch", service_data, hass)

        # 服务不应该抛出异常
        await service_manager._press_switch(call)

        mock_client.press_switch_async.assert_called_once()

    @pytest.mark.asyncio
    async def test_service_manager_initialization(
        self, hass: HomeAssistant, mock_client
    ):
        """测试服务管理器的初始化。"""
        manager = LifeSmartServiceManager(hass, mock_client)

        assert manager.hass == hass, "服务管理器的hass实例应该正确"
        assert manager.client == mock_client, "服务管理器的客户端应该正确"

    @pytest.mark.parametrize(
        "service_data,expected_calls",
        [
            # 正常的红外服务调用
            (
                {
                    HUB_ID_KEY: "hub1",
                    "ai": "ai1",
                    DEVICE_ID_KEY: "dev1",
                    "category": "tv",
                    "brand": "lg",
                    "keys": ["power"],
                },
                1,
            ),
            # 多个按键的红外服务调用
            (
                {
                    HUB_ID_KEY: "hub2",
                    "ai": "ai2",
                    DEVICE_ID_KEY: "dev2",
                    "category": "ac",
                    "brand": "daikin",
                    "keys": ["power", "temp_up", "temp_down"],
                },
                1,
            ),
        ],
    )
    @pytest.mark.asyncio
    async def test_send_ir_keys_parametrized(
        self,
        hass: HomeAssistant,
        service_manager,
        mock_client,
        service_data,
        expected_calls,
    ):
        """参数化测试红外按键服务。"""
        service_manager.register_services()

        call = create_service_call(DOMAIN, "send_ir_keys", service_data, hass)

        await service_manager._send_ir_keys(call)

        assert (
            mock_client.async_send_ir_key.call_count == expected_calls
        ), f"期望调用{expected_calls}次，实际调用{mock_client.async_send_ir_key.call_count}次"
        if expected_calls > 0:
            mock_client.async_send_ir_key.assert_called_with(
                service_data[HUB_ID_KEY],
                service_data[DEVICE_ID_KEY],
                service_data["category"],
                service_data["brand"],
                service_data["keys"],
                service_data["ai"],
                "",
            )
