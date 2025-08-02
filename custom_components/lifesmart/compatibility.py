"""
Home Assistant 版本兼容性处理模块
仅包含必要的兼容性函数，支持从 2023.3.0 开始的版本
"""

import logging

_LOGGER = logging.getLogger(__name__)


def get_ws_timeout(timeout_seconds: float):
    """
    获取兼容的WebSocket超时参数

    在不同aiohttp版本中，WebSocket连接的超时参数格式不同：
    - aiohttp 3.8.x: 使用 float 类型
    - aiohttp 3.9.x-3.10.x: 使用 ClientWSTimeout(ws_connect=timeout)
    - aiohttp 3.11.x+: 使用 ClientWSTimeout(ws_receive=timeout, ws_close=timeout)
    """
    try:
        # 尝试导入新版本的ClientWSTimeout (aiohttp 3.9.0+)
        from aiohttp import ClientWSTimeout

        try:
            # 尝试新版本参数 (aiohttp 3.11.0+)
            return ClientWSTimeout(ws_receive=timeout_seconds, ws_close=timeout_seconds)
        except TypeError:
            # 回退到中版本参数 (aiohttp 3.9.0-3.10.x)
            return ClientWSTimeout(ws_connect=timeout_seconds)
    except ImportError:
        # 回退到旧版本的float类型 (aiohttp 3.8.x)
        return timeout_seconds


def get_climate_entity_features():
    """
    获取兼容的气候实体功能常量

    在不同HA版本中，ClimateEntityFeature的属性不同
    """
    try:
        from homeassistant.components.climate import ClimateEntityFeature

        # 检查是否有TURN_ON和TURN_OFF属性
        if hasattr(ClimateEntityFeature, "TURN_ON"):
            # 新版本HA，直接使用官方的ClimateEntityFeature
            return ClimateEntityFeature
        else:
            # 旧版本没有TURN_ON/TURN_OFF，需要创建兼容类
            class CompatClimateEntityFeature:
                def __init__(self):
                    # 复制现有的属性
                    self.TARGET_TEMPERATURE = ClimateEntityFeature.TARGET_TEMPERATURE
                    self.FAN_MODE = ClimateEntityFeature.FAN_MODE
                    self.PRESET_MODE = ClimateEntityFeature.PRESET_MODE
                    self.SWING_MODE = ClimateEntityFeature.SWING_MODE
                    self.TARGET_TEMPERATURE_RANGE = (
                        ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
                    )
                    self.AUX_HEAT = ClimateEntityFeature.AUX_HEAT

                    # 添加缺失的属性（使用不会冲突的值）
                    self.TURN_ON = 128  # 新增的功能位
                    self.TURN_OFF = 256  # 新增的功能位

                    # 如果存在TARGET_HUMIDITY，也复制过来
                    if hasattr(ClimateEntityFeature, "TARGET_HUMIDITY"):
                        self.TARGET_HUMIDITY = ClimateEntityFeature.TARGET_HUMIDITY
                    else:
                        self.TARGET_HUMIDITY = 64  # 假设值

                def __getitem__(self, key):
                    return getattr(self, key)

            return CompatClimateEntityFeature()

    except ImportError:
        # 如果ClimateEntityFeature不存在，尝试旧的常量
        try:
            from homeassistant.components.climate import (
                SUPPORT_TARGET_TEMPERATURE,
                SUPPORT_FAN_MODE,
                SUPPORT_PRESET_MODE,
                SUPPORT_SWING_MODE,
                SUPPORT_TARGET_TEMPERATURE_RANGE,
                SUPPORT_AUX_HEAT,
            )

            # 创建一个兼容类来模拟新的枚举
            class CompatClimateEntityFeature:
                def __init__(self):
                    self.TARGET_TEMPERATURE = SUPPORT_TARGET_TEMPERATURE
                    self.FAN_MODE = SUPPORT_FAN_MODE
                    self.PRESET_MODE = SUPPORT_PRESET_MODE
                    self.SWING_MODE = SUPPORT_SWING_MODE
                    self.TARGET_TEMPERATURE_RANGE = SUPPORT_TARGET_TEMPERATURE_RANGE
                    self.AUX_HEAT = SUPPORT_AUX_HEAT
                    self.TURN_ON = 128  # 新增功能
                    self.TURN_OFF = 256  # 新增功能
                    self.TARGET_HUMIDITY = 64  # 新增功能

                def __getitem__(self, key):
                    return getattr(self, key)

            return CompatClimateEntityFeature()
        except ImportError:
            # 如果都不存在，返回None让调用方处理
            return None


def get_scheduled_timer_handles(loop):
    """
    获取事件循环中的定时器句柄

    完全匹配Home Assistant官方实现:
    - HA 2024.8+: homeassistant.util.async_.get_scheduled_timer_handles()
    - HA 2024.2.0等旧版本: 直接访问loop._scheduled属性 (与官方实现相同)
    """
    try:
        # HA 2024.8+ 版本
        from homeassistant.util.async_ import get_scheduled_timer_handles

        return get_scheduled_timer_handles(loop)
    except ImportError:
        # 旧版本：直接使用HA官方实现的方式
        # 这与HA core中的实现完全一致：loop._scheduled
        try:
            return loop._scheduled
        except AttributeError:
            # 如果_scheduled属性不存在，返回空列表
            return []


def create_service_call(
    domain: str, service: str, service_data: dict = None, hass=None
):
    """
    创建兼容的服务调用对象

    不同HA版本中，ServiceCall的创建方式可能不同
    - HA 2025.7.4+: 需要 hass 参数
    - HA 2024.x: 不需要 hass 参数
    """
    from homeassistant.core import ServiceCall

    try:
        # 尝试新版本格式 (HA 2025.7.4+)
        if hass is not None:
            return ServiceCall(
                domain=domain,
                service=service,
                data=service_data or {},
                hass=hass,
            )
        # 尝试旧版本格式
        return ServiceCall(
            domain=domain,
            service=service,
            data=service_data or {},
        )
    except TypeError:
        # 如果构造函数参数不匹配，尝试检查 ServiceCall 的签名
        import inspect

        sig = inspect.signature(ServiceCall.__init__)
        params = list(sig.parameters.keys())

        if "hass" in params and hass is not None:
            # 新版本需要 hass 参数
            return ServiceCall(
                domain=domain,
                service=service,
                data=service_data or {},
                hass=hass,
            )
        # 如果仍然失败，使用最基本的方式
        call = object.__new__(ServiceCall)
        call.domain = domain
        call.service = service
        call.data = service_data or {}
        return call


def ensure_script_compatibility():
    """
    确保script模块兼容性
    
    在不同HA版本中，script模块的内部函数名称可能不同：
    - HA 2023.3.0: _async_stop_scripts_after_shutdown
    - HA 新版本: _schedule_stop_scripts_after_shutdown
    
    pytest插件可能期望新版本的函数名，我们需要创建兼容性别名
    """
    try:
        import homeassistant.helpers.script as script_module
        
        # 检查是否已经有新版本函数名
        if hasattr(script_module, '_schedule_stop_scripts_after_shutdown'):
            return  # 新版本，无需处理
            
        # 检查是否有旧版本函数名
        if hasattr(script_module, '_async_stop_scripts_after_shutdown'):
            # 创建别名以兼容pytest插件
            script_module._schedule_stop_scripts_after_shutdown = script_module._async_stop_scripts_after_shutdown
            _LOGGER.debug("Created script compatibility alias: _schedule_stop_scripts_after_shutdown")
        else:
            # 如果都没有，创建一个空函数以避免AttributeError
            def _dummy_schedule_stop_scripts_after_shutdown(*args, **kwargs):
                """Dummy function for compatibility"""
                pass
            script_module._schedule_stop_scripts_after_shutdown = _dummy_schedule_stop_scripts_after_shutdown
            _LOGGER.debug("Created dummy script function: _schedule_stop_scripts_after_shutdown")
            
    except ImportError:
        _LOGGER.warning("Unable to import script module for compatibility")


def ensure_restore_state_compatibility():
    """
    确保restore_state模块兼容性
    
    在不同HA版本中，restore_state模块的API可能不同：
    - HA 新版本: 有async_load函数
    - HA 2023.3.0: 没有async_load函数
    
    pytest插件可能期望新版本的API，我们需要创建兼容性别名
    """
    try:
        import homeassistant.helpers.restore_state as rs_module
        
        # 检查是否已经有async_load函数
        if hasattr(rs_module, 'async_load'):
            return  # 新版本，无需处理
            
        # 为旧版本创建一个dummy async_load函数
        async def _dummy_async_load(hass):
            """Dummy async_load function for compatibility with old HA versions"""
            pass
            
        rs_module.async_load = _dummy_async_load
        _LOGGER.debug("Created restore_state compatibility function: async_load")
            
    except ImportError:
        _LOGGER.warning("Unable to import restore_state module for compatibility")


def ensure_async_create_task_compatibility():
    """
    确保async_create_task兼容性
    
    不同HA版本中，HomeAssistant.async_create_task的参数不同：
    - HA 2023.3.0: async_create_task(coroutine) - 只接受1个参数
    - HA 2024.x+: async_create_task(coroutine, name=None) - 接受2个参数
    
    pytest-homeassistant-custom-component插件可能传入name参数，
    我们需要monkey patch旧版本以兼容新版本的调用方式
    """
    try:
        from homeassistant.core import HomeAssistant
        
        # 检查async_create_task是否已经支持name参数
        import inspect
        sig = inspect.signature(HomeAssistant.async_create_task)
        params = list(sig.parameters.keys())
        
        if 'name' in params:
            # 新版本，无需处理
            return
            
        _LOGGER.debug("Patching HomeAssistant.async_create_task for HA 2023.3.0 compatibility")
        
        # 保存原始方法
        original_async_create_task = HomeAssistant.async_create_task
        
        def patched_async_create_task(self, coroutine, name=None):
            """兼容性封装，忽略name参数"""
            return original_async_create_task(self, coroutine)
            
        # 替换方法
        HomeAssistant.async_create_task = patched_async_create_task
        _LOGGER.info("Successfully patched HomeAssistant.async_create_task for HA 2023.3.0")
        
    except Exception as e:
        _LOGGER.error(f"Failed to patch async_create_task: {e}")


def setup_logging():
    """设置兼容性日志"""
    _LOGGER.info("LifeSmart兼容性模块已加载")
