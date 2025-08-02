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
            # 官方实现: handles: list[TimerHandle] = loop._scheduled
            handles = loop._scheduled  # type: ignore[attr-defined]
            return handles
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


def setup_logging():
    """设置兼容性日志"""
    _LOGGER.info("LifeSmart兼容性模块已加载")
