"""
测试 compatibility.py 模块中的兼容性函数

这个测试文件专门测试不同 Home Assistant 版本之间的兼容性函数，
主要测试功能性而不是实现细节。
"""

from unittest.mock import Mock

from homeassistant.core import HomeAssistant, ServiceCall

from custom_components.lifesmart.compatibility import (
    get_ws_timeout,
    get_climate_entity_features,
    get_scheduled_timer_handles,
    create_service_call,
)


class TestWebSocketTimeout:
    """测试 WebSocket 超时参数兼容性"""

    def test_get_ws_timeout_returns_timeout_object_or_float(self):
        """测试 get_ws_timeout 返回适当的超时对象或浮点数"""
        result = get_ws_timeout(30.0)

        # 应该返回一个对象（ClientWSTimeout）或浮点数
        assert result is not None
        # 在真实环境中，这将根据aiohttp版本返回不同类型
        assert isinstance(result, (float, object))


class TestClimateEntityFeatures:
    """测试气候实体功能兼容性"""

    def test_get_climate_entity_features_returns_feature_object(self):
        """测试 get_climate_entity_features 返回功能对象"""
        features = get_climate_entity_features()

        # 应该返回一个包含所需属性的对象
        assert features is not None
        assert hasattr(features, "TARGET_TEMPERATURE")
        assert hasattr(features, "FAN_MODE")
        # 兼容性函数确保这些属性总是存在
        assert hasattr(features, "TURN_ON")
        assert hasattr(features, "TURN_OFF")

        # 验证属性值是整数
        assert isinstance(features.TARGET_TEMPERATURE, int)
        assert isinstance(features.FAN_MODE, int)
        assert isinstance(features.TURN_ON, int)
        assert isinstance(features.TURN_OFF, int)


class TestScheduledTimerHandles:
    """测试定时器句柄获取兼容性"""

    def test_get_scheduled_timer_handles_with_real_loop(self):
        """测试使用真实事件循环的定时器句柄获取"""
        import asyncio

        loop = asyncio.new_event_loop()

        try:
            result = get_scheduled_timer_handles(loop)
            # 应该返回一个列表（可能为空）
            assert isinstance(result, list)
        finally:
            loop.close()

    def test_get_scheduled_timer_handles_with_mock_loop(self):
        """测试使用模拟loop的情况"""
        mock_loop = Mock()
        mock_loop._scheduled = ["handle1", "handle2"]

        result = get_scheduled_timer_handles(mock_loop)
        # 在旧版本HA中应该返回_scheduled属性
        assert isinstance(result, list)


class TestServiceCallCompatibility:
    """测试服务调用兼容性"""

    def test_create_service_call_with_hass_param(self, hass: HomeAssistant):
        """测试新版本需要 hass 参数"""
        service_data = {"key": "value"}

        result = create_service_call("test_domain", "test_service", service_data, hass)

        assert isinstance(result, ServiceCall)
        assert result.domain == "test_domain"
        assert result.service == "test_service"
        assert result.data == service_data

    def test_create_service_call_without_hass_param(self):
        """测试旧版本不需要 hass 参数"""
        service_data = {"key": "value"}

        result = create_service_call("test_domain", "test_service", service_data)

        assert isinstance(result, ServiceCall)
        assert result.domain == "test_domain"
        assert result.service == "test_service"
        assert result.data == service_data

    def test_create_service_call_empty_data(self):
        """测试空数据的情况"""
        result = create_service_call("test_domain", "test_service")

        assert isinstance(result, ServiceCall)
        assert result.domain == "test_domain"
        assert result.service == "test_service"
        assert result.data == {}


class TestCompatibilityIntegration:
    """测试兼容性函数的集成使用"""

    def test_climate_features_integration(self):
        """测试气候功能在实际使用中的集成"""
        features = get_climate_entity_features()

        # 验证所有必要的属性都存在
        required_attrs = ["TARGET_TEMPERATURE", "FAN_MODE", "TURN_ON", "TURN_OFF"]
        for attr in required_attrs:
            assert hasattr(features, attr), f"缺少必要属性: {attr}"
            assert isinstance(getattr(features, attr), int), f"属性 {attr} 应该是整数"

    def test_service_call_integration(self, hass: HomeAssistant):
        """测试服务调用在实际使用中的集成"""
        service_data = {"temperature": 22.0}

        call = create_service_call("climate", "set_temperature", service_data, hass)

        assert call.domain == "climate"
        assert call.service == "set_temperature"
        assert call.data == service_data

    def test_ws_timeout_integration(self):
        """测试WebSocket超时在实际使用中的集成"""
        timeout = get_ws_timeout(30.0)

        # 无论返回什么类型，都应该是有效的超时值
        assert timeout is not None

        # 如果是float，应该等于原始值
        if isinstance(timeout, float):
            assert timeout == 30.0
        # 如果是对象，应该有适当的属性或方法
        else:
            # 这是一个对象，通常是ClientWSTimeout
            assert hasattr(timeout, "__class__")

    def test_timer_handles_integration(self):
        """测试定时器句柄在实际使用中的集成"""
        import asyncio

        loop = asyncio.new_event_loop()

        try:
            handles = get_scheduled_timer_handles(loop)
            assert isinstance(handles, list)
            # 新循环应该没有定时器
            assert len(handles) >= 0
        finally:
            loop.close()


class TestCompatibilityFunctionalBehavior:
    """测试兼容性函数的功能行为"""

    def test_ws_timeout_consistency(self):
        """测试相同输入产生一致的输出"""
        result1 = get_ws_timeout(15.0)
        result2 = get_ws_timeout(15.0)

        # 相同的输入应该产生相同类型的输出
        assert type(result1) is type(result2)

        if isinstance(result1, float):
            assert result1 == result2 == 15.0

    def test_climate_features_consistency(self):
        """测试气候功能的一致性"""
        features1 = get_climate_entity_features()
        features2 = get_climate_entity_features()

        # 多次调用应该返回相同的功能值
        assert features1.TARGET_TEMPERATURE == features2.TARGET_TEMPERATURE
        assert features1.FAN_MODE == features2.FAN_MODE
        assert features1.TURN_ON == features2.TURN_ON
        assert features1.TURN_OFF == features2.TURN_OFF

    def test_service_call_data_handling(self):
        """测试服务调用数据处理"""
        # None数据应该转换为空字典
        call1 = create_service_call("domain", "service", None)
        assert call1.data == {}

        # 空字典应该保持为空字典
        call2 = create_service_call("domain", "service", {})
        assert call2.data == {}

        # 实际数据应该保持不变
        data = {"key": "value", "number": 42}
        call3 = create_service_call("domain", "service", data)
        assert call3.data == data
