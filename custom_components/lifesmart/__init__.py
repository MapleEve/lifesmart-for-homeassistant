"""由 @MapleEve 实现的 LifeSmart 集成。

此模块是 LifeSmart 集成的入口点，负责初始化中央协调器 Hub，
并管理集成的生命周期。

架构重构后，此文件只专注于集成的初始化和卸载逻辑，
具体的功能被分散到专门的模块中：
- hub.py: 中央协调器，管理客户端和设备数据
- entity.py: 所有平台实体的基类
- services.py: 服务注册和处理
- helpers.py: 通用工具函数
"""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .core.const import DOMAIN, SUPPORTED_PLATFORMS, UPDATE_LISTENER
from .core.hub import LifeSmartHub
from .core import compatibility  # Expose compatibility for backward compatibility
from .services import LifeSmartServiceManager

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """设置 LifeSmart 集成。

    此函数是 Home Assistant 加载集成时的主要入口点，负责：
    1. 创建和初始化 LifeSmart Hub
    2. 设置平台组件
    3. 注册服务
    4. 设置配置更新监听器

    Args:
        hass: Home Assistant 的核心实例
        config_entry: 当前集成的配置条目实例

    Returns:
        如果集成设置成功，则返回 True

    Raises:
        ConfigEntryNotReady: 如果设置过程中发生可重试的错误
    """
    # 确保域数据结构存在
    hass.data.setdefault(DOMAIN, {})

    try:
        # 1. 创建和初始化 Hub
        hub = LifeSmartHub(hass, config_entry)
        await hub.async_setup()

        # 2. 将 Hub 存储到 hass.data
        hass.data[DOMAIN][config_entry.entry_id] = {
            "hub": hub,
            "devices": hub.get_devices(),
            "client": hub.get_client(),
            UPDATE_LISTENER: config_entry.add_update_listener(_async_update_listener),
        }

        # 3. 转发到平台
        await hass.config_entries.async_forward_entry_setups(
            config_entry, SUPPORTED_PLATFORMS
        )

        # 4. 注册服务
        service_manager = LifeSmartServiceManager(hass, hub.get_client())
        service_manager.register_services()

        _LOGGER.info("LifeSmart 集成设置完成。")
        return True

    except (ConfigEntryNotReady, Exception):
        # 如果设置失败，清理已创建的数据
        if config_entry.entry_id in hass.data.get(DOMAIN, {}):
            hass.data[DOMAIN].pop(config_entry.entry_id)
        raise


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """卸载 LifeSmart 集成。

    此函数负责清理所有相关资源，包括：
    1. 卸载平台组件
    2. 清理 Hub 资源
    3. 移除配置更新监听器
    4. 清理 hass.data 中的数据

    Args:
        hass: Home Assistant 的核心实例
        config_entry: 正在被卸载的配置条目

    Returns:
        如果卸载成功，则返回 True
    """
    entry_id = config_entry.entry_id

    try:
        # 1. 卸载所有平台组件
        unload_ok = await hass.config_entries.async_unload_platforms(
            config_entry, SUPPORTED_PLATFORMS
        )

        if unload_ok:
            # 2. 获取并清理 Hub
            hub_data = hass.data[DOMAIN].get(entry_id, {})
            if "hub" in hub_data:
                try:
                    await hub_data["hub"].async_unload()
                except Exception as e:
                    _LOGGER.error("卸载 Hub 时发生错误: %s", e)

            # 3. 移除配置更新监听器
            if UPDATE_LISTENER in hub_data:
                hub_data[UPDATE_LISTENER]()

            # 4. 清理 hass.data
            hass.data[DOMAIN].pop(entry_id)

            # 如果这是最后一个配置条目，清理整个域和服务
            if not hass.data[DOMAIN]:
                hass.data.pop(DOMAIN)
                # 清理服务
                if hass.services.has_service(DOMAIN, "send_ir_keys"):
                    hass.services.async_remove(DOMAIN, "send_ir_keys")
                if hass.services.has_service(DOMAIN, "send_ackeys"):
                    hass.services.async_remove(DOMAIN, "send_ackeys")
                if hass.services.has_service(DOMAIN, "trigger_scene"):
                    hass.services.async_remove(DOMAIN, "trigger_scene")
                if hass.services.has_service(DOMAIN, "press_switch"):
                    hass.services.async_remove(DOMAIN, "press_switch")

        _LOGGER.info("LifeSmart 集成卸载完成。")
        return unload_ok

    except Exception as e:
        _LOGGER.error("卸载 LifeSmart 集成时发生错误: %s", e)
        return False


async def _async_update_listener(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> None:
    """处理配置选项更新。

    当用户通过"选项"流程修改配置后，此函数被调用，
    触发集成的重新加载以应用新设置。

    Args:
        hass: Home Assistant 的核心实例
        config_entry: 已更新的配置条目
    """
    _LOGGER.info("检测到配置更新，正在重新加载 LifeSmart 集成...")
    await hass.config_entries.async_reload(config_entry.entry_id)
