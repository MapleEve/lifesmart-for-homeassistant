"""
测试环境兼容性处理模块
专门处理pytest和pytest-homeassistant-custom-component插件的兼容性问题
"""

import logging

_LOGGER = logging.getLogger(__name__)


def ensure_script_compatibility():
    """
    确保script模块兼容性
    
    在不同HA版本中，script模块的内部函数名称可能不同：
    - HA 2023.3.0: _async_stop_scripts_after_shutdown
    - HA 新版本: _schedule_stop_scripts_after_shutdown
    
    pytest-homeassistant-custom-component插件期望新版本的函数名，我们需要创建兼容性别名
    """
    try:
        import homeassistant.helpers.script as script_module
        
        # 检查是否已经有新版本函数名
        if hasattr(script_module, '_schedule_stop_scripts_after_shutdown'):
            return
            
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
            return
            
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


def setup_test_compatibility():
    """设置所有测试兼容性函数"""
    _LOGGER.info("设置测试环境兼容性...")
    ensure_script_compatibility()
    ensure_restore_state_compatibility()
    ensure_async_create_task_compatibility()
    _LOGGER.info("测试环境兼容性设置完成")