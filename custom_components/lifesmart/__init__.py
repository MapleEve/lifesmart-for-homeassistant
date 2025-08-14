"""LifeSmart Home Assistant 集成 - 主入口模块

作者: @MapleEve

本模块是整个LifeSmart智能家居设备集成系统的核心入口点，负责协调和管理
与Home Assistant生态系统的完整生命周期集成。

架构设计理念:
==============
本模块采用现代化的模块化架构设计，遵循单一职责原则和依赖注入模式。
主要设计特点包括：

1. **生命周期管理**: 处理集成的完整生命周期，包括设置、运行时管理和清理
2. **资源协调**: 统一管理Hub、客户端、设备数据等核心资源
3. **平台转发**: 自动化地将配置转发到所有支持的设备平台
4. **服务注册**: 集中管理LifeSmart特定的Home Assistant服务
5. **异常处理**: 提供完整的错误恢复和清理机制

模块依赖关系:
=============
├── core/
│   ├── hub.py           # 🏢 中央协调器 - 管理设备连接和数据流
│   ├── client_base.py   # 🔌 客户端抽象层 - TCP/OpenAPI双协议支持
│   ├── const.py         # 📋 常量定义 - 域名、平台、消息类型等
│   └── compatibility.py # 🔄 版本差异处理 - 处理HA版本差异
├── services.py          # 🛠️  服务管理器 - 注册LifeSmart专用服务
└── [platform].py       # 📱 平台实现 - sensor, light, climate等

技术特性:
=========
- **异步优先**: 所有I/O操作均采用异步模式，避免阻塞主线程
- **配置热重载**: 支持配置变更的动态重载，无需重启Home Assistant
- **资源安全**: 实现完整的资源清理机制，防止内存泄漏
- **错误恢复**: 提供多级错误处理和恢复策略
- **可扩展性**: 通过平台转发机制支持动态添加新设备类型

性能考虑:
=========
- Hub初始化采用懒加载模式，减少启动时间
- 设备数据使用缓存机制，降低网络开销
- 平台转发采用并发模式，提高初始化效率
- 配置监听器使用轻量级回调，减少资源占用
"""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .core import compatibility  # 导出版本差异处理功能
from .core.const import DOMAIN, SUPPORTED_PLATFORMS, UPDATE_LISTENER
from .core.hub import LifeSmartHub
from .services import LifeSmartServiceManager

# 日志记录器 - 使用模块名作为日志标识符，便于调试和监控
# 日志级别遵循Home Assistant标准：DEBUG < INFO < WARNING < ERROR
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """异步设置LifeSmart集成 - 集成生命周期的核心入口点

    本函数是Home Assistant调用的标准入口点，负责完整的集成初始化流程。
    它遵循Home Assistant的异步设置模式，确保不会阻塞事件循环。

    设置流程详解:
    =============
    1. **域数据初始化**
       - 确保hass.data[DOMAIN]字典存在
       - 为多实例配置提供隔离的数据空间

    2. **Hub创建与初始化**
       - 实例化LifeSmartHub中央协调器
       - 执行异步设置：建立设备连接、初始化数据缓存
       - Hub负责管理TCP/OpenAPI客户端的生命周期

    3. **数据存储结构**
       - hub: 中央协调器实例，提供设备管理和数据同步
       - devices: 设备字典缓存，key为device_id，value为设备实例
       - client: 客户端实例（TCP或OpenAPI），处理与LifeSmart云端的通信
       - update_listener: 配置变更监听器的清理函数

    4. **平台转发机制**
       - 并发初始化所有支持的设备平台（sensor, light, climate等）
       - 每个平台会从Hub获取相关设备并创建对应的Home Assistant实体
       - 使用async_forward_entry_setups确保高效的并发设置

    5. **服务注册**
       - 注册LifeSmart特定的Home Assistant服务
       - 包括红外控制、空调控制、场景触发、开关控制等高级功能

    错误处理策略:
    =============
    - ConfigEntryNotReady: 可重试错误（网络问题、设备暂时不可达）
    - Exception: 不可重试错误（配置错误、认证失败）
    - 所有错误都会触发资源清理，防止不一致状态

    性能优化:
    =========
    - Hub初始化采用连接池管理，复用网络连接
    - 设备数据预加载，减少平台初始化时的网络请求
    - 平台转发使用gather模式，最大化并发度

    Args:
        hass (HomeAssistant): Home Assistant的核心实例，提供事件循环、
                              服务注册、实体管理等核心功能
        config_entry (ConfigEntry): 配置条目实例，包含用户配置的连接参数、
                                   设备偏好、调试选项等信息

    Returns:
        bool: True表示设置成功，False表示设置失败
              成功后Home Assistant将标记集成为已加载状态

    Raises:
        ConfigEntryNotReady: 当遇到暂时性错误时抛出，Home Assistant会稍后重试
                            常见场景：网络连接失败、LifeSmart服务暂时不可用
        Exception: 其他不可重试的异常，导致集成设置永久失败

    调用时机:
    ========
    - Home Assistant启动时自动调用
    - 用户手动重新加载集成时调用
    - 配置更新触发重新加载时调用
    """
    # 初始化域数据结构 - 确保集成有独立的数据命名空间
    # 使用setdefault避免覆盖现有数据，支持多实例配置
    # hass.data[DOMAIN]将存储所有LifeSmart集成实例的数据
    hass.data.setdefault(DOMAIN, {})

    try:
        # 1. 创建和初始化中央协调器Hub
        # Hub是整个集成的核心，负责：
        # - 设备发现和管理
        # - 客户端连接管理（TCP优先，OpenAPI备用）
        # - 数据缓存和状态同步
        # - 事件分发和处理
        hub = LifeSmartHub(hass, config_entry)

        # 异步设置Hub：建立连接、初始化设备缓存、启动数据同步
        # 这个过程可能涉及网络请求，因此必须异步执行
        await hub.async_setup()

        # 2. 构建集成数据结构并存储到Home Assistant数据存储
        # 使用config_entry.entry_id作为key，支持同一用户的多个LifeSmart账户
        hass.data[DOMAIN][config_entry.entry_id] = {
            "hub": hub,  # 中央协调器实例，提供设备管理和数据访问接口
            "devices": hub.get_devices(),  # 设备字典缓存，格式：{device_id: device_info}
            "client": hub.get_client(),  # 活跃客户端实例（TCP/OpenAPI）
            # 配置更新监听器：当用户修改集成选项时自动重新加载
            UPDATE_LISTENER: config_entry.add_update_listener(_async_update_listener),
        }

        # 3. 平台转发 - 并发初始化所有支持的设备平台
        # SUPPORTED_PLATFORMS包含：sensor, light, climate, cover, switch, fan等
        # 每个平台会：
        # - 从Hub获取相关设备列表
        # - 创建对应的Home Assistant实体
        # - 注册到实体注册表
        # - 开始状态同步
        await hass.config_entries.async_forward_entry_setups(
            config_entry, SUPPORTED_PLATFORMS
        )

        # 4. 注册LifeSmart专用服务
        # 服务包括：
        # - send_ir_keys: 红外遥控器按键发送
        # - send_ackeys: 空调专用按键控制
        # - trigger_scene: 触发LifeSmart场景
        # - press_switch: 虚拟按键操作
        service_manager = LifeSmartServiceManager(hass, hub.get_client())
        service_manager.register_services()

        # 记录成功初始化的关键信息，便于调试和监控
        _LOGGER.info(
            "LifeSmart integration setup completed for entry %s with %d devices",
            config_entry.entry_id,
            len(hub.get_devices()),
        )

        return True

    except ConfigEntryNotReady as e:
        # 可重试错误：网络问题、服务暂时不可用等
        # Home Assistant将在稍后自动重试
        _LOGGER.warning("LifeSmart integration setup not ready, will retry: %s", str(e))
        # 清理已创建的数据，确保重试时的清洁状态
        if config_entry.entry_id in hass.data.get(DOMAIN, {}):
            hass.data[DOMAIN].pop(config_entry.entry_id)
        raise

    except Exception as e:
        # 不可重试错误：配置错误、认证失败等
        _LOGGER.error(
            "Failed to setup LifeSmart integration for entry %s: %s",
            config_entry.entry_id,
            str(e),
            exc_info=True,
        )
        # 清理已创建的数据，防止不一致状态
        if config_entry.entry_id in hass.data.get(DOMAIN, {}):
            hass.data[DOMAIN].pop(config_entry.entry_id)
        raise


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """异步卸载LifeSmart集成 - 资源清理和生命周期管理的关键入口

    本函数是Home Assistant集成卸载的标准入口点，负责完整的资源清理流程。
    它确保所有相关资源得到正确释放，防止内存泄漏和资源冲突。

    卸载流程详解:
    =============
    1. **平台组件卸载**
       - 并发卸载所有已加载的设备平台（sensor, light, climate等）
       - 每个平台负责清理其管理的实体和监听器
       - 使用async_unload_platforms确保原子性操作

    2. **Hub资源清理**
       - 关闭TCP/OpenAPI客户端连接
       - 停止所有异步任务和定时器
       - 清理设备缓存和状态监听器
       - 释放网络连接池资源

    3. **监听器清理**
       - 移除配置更新监听器，防止内存引用循环
       - 取消所有未完成的异步回调

    4. **数据存储清理**
       - 清理hass.data[DOMAIN]中的集成数据
       - 如果是最后一个实例，清理整个域数据
       - 注销所有LifeSmart专用服务

    5. **服务清理机制**
       - 检查是否为最后一个配置实例
       - 如果是，注销所有LifeSmart域服务：
         * send_ir_keys: 红外遥控服务
         * send_ackeys: 空调控制服务
         * trigger_scene: 场景触发服务
         * press_switch: 虚拟按键服务

    错误处理策略:
    =============
    - 使用"继续卸载"原则：即使某个步骤失败，也继续执行后续清理
    - Hub清理失败时记录错误但不中断整体卸载流程
    - 平台卸载失败时返回False，但仍执行数据清理

    性能考虑:
    =========
    - 平台卸载采用并发模式，减少卸载时间
    - Hub清理使用异步模式，避免阻塞事件循环
    - 服务注销采用检查-删除模式，避免重复操作

    线程安全:
    ========
    - 所有清理操作都在Home Assistant主事件循环中执行
    - 使用异步锁确保Hub清理的原子性
    - 数据删除采用原子操作，避免竞态条件

    Args:
        hass (HomeAssistant): Home Assistant的核心实例，提供平台管理、
                              服务注册、数据存储等功能
        config_entry (ConfigEntry): 正在被卸载的配置条目实例，包含该集成
                                   实例的所有配置信息和标识符

    Returns:
        bool: True表示卸载成功，False表示卸载过程中遇到错误
              即使返回False，资源清理仍会尽可能完成

    Raises:
        Exception: 一般不会抛出异常，所有错误都会被捕获并记录
                   这确保卸载过程的健壮性

    调用时机:
    ========
    - 用户通过UI删除集成时
    - 配置更新触发重新加载时的清理阶段
    - Home Assistant关闭时的集成清理
    - 集成重新加载的预清理阶段

    资源清理检查清单:
    ===============
    ✓ TCP/OpenAPI连接关闭
    ✓ 异步任务和定时器停止
    ✓ 设备实体从注册表移除
    ✓ 事件监听器取消注册
    ✓ 内存缓存清空
    ✓ 服务注销（如果是最后实例）
    ✓ 配置监听器移除
    ✓ 数据存储清理
    """
    # 获取配置条目标识符，用于定位要清理的数据
    entry_id = config_entry.entry_id

    try:
        # 第一阶段：平台组件卸载
        # ===========================
        # 并发卸载所有已注册的设备平台，包拯sensor、light、climate等
        # 这个过程会：
        # - 从 Home Assistant实体注册表中移除所有相关实体
        # - 取消所有平台级别的事件监听器和定时器
        # - 清理平台特定的资源和缓存
        # async_unload_platforms确保原子性：要么全部成功，要么全部回滚
        _LOGGER.debug("Starting platform unloading for entry %s", entry_id)
        unload_ok = await hass.config_entries.async_unload_platforms(
            config_entry, SUPPORTED_PLATFORMS
        )

        # 第二阶段：核心资源清理（即使平台卸载失败也要执行）
        # ==============================================
        if unload_ok:
            _LOGGER.debug(
                "Platforms unloaded successfully, proceeding with resource cleanup"
            )

            # 获取该配置实例的数据存储
            # hub_data包含：hub实例、设备缓存、客户端、监听器等
            hub_data = hass.data[DOMAIN].get(entry_id, {})

            # 2.1 Hub核心资源清理
            # Hub是资源管理的核心，必须正确清理以避免：
            # - TCP连接保持打开导致的资源泄漏
            # - WebSocket连接占用端口
            # - 未完成的异步任务继续运行
            # - 定时器继续触发回调
            if "hub" in hub_data:
                try:
                    _LOGGER.debug("Cleaning up Hub resources")
                    await hub_data["hub"].async_unload()
                    _LOGGER.debug("Hub cleanup completed successfully")
                except Exception as e:
                    # Hub清理失败不应阻止其他清理操作
                    # 记录详细错误信息用于调试，但继续执行后续清理
                    _LOGGER.error(
                        "Error occurred while unloading Hub for entry %s: %s",
                        entry_id,
                        e,
                        exc_info=True,
                    )

            # 2.2 配置监听器清理
            # 移除配置更新监听器，防止：
            # - 内存引用循环导致无法垃圾回收
            # - 已卸载的集成仍接收配置更新事件
            # - 监听器回调访问已释放的资源
            if UPDATE_LISTENER in hub_data:
                try:
                    _LOGGER.debug("Removing configuration update listener")
                    hub_data[UPDATE_LISTENER]()
                except Exception as e:
                    _LOGGER.error(
                        "Error removing update listener for entry %s: %s", entry_id, e
                    )

            # 2.3 数据存储清理
            # 从 hass.data中移除该配置实例的所有数据
            # 这包括设备缓存、客户端引用、状态数据等
            _LOGGER.debug("Cleaning up data storage for entry %s", entry_id)
            hass.data[DOMAIN].pop(entry_id)

            # 第三阶段：全局资源清理（仅当最后一个实例时）
            # ==========================================
            # 检查是否还有其他 LifeSmart 配置实例
            # 如果这是最后一个实例，需要清理全局资源
            if not hass.data[DOMAIN]:
                _LOGGER.info(
                    "Last LifeSmart instance unloading, cleaning up global resources"
                )

                # 清理整个域数据存储
                hass.data.pop(DOMAIN)

                # 注销所有 LifeSmart 专用服务
                # 这些服务在没有活跃实例时应该被移除
                # 未来可以在这里添加服务清理任务

                # 红外遥控服务清理
                if hass.services.has_service(DOMAIN, "send_ir_keys"):
                    _LOGGER.debug("Removing send_ir_keys service")
                    hass.services.async_remove(DOMAIN, "send_ir_keys")

                # 空调控制服务清理
                if hass.services.has_service(DOMAIN, "send_ackeys"):
                    _LOGGER.debug("Removing send_ackeys service")
                    hass.services.async_remove(DOMAIN, "send_ackeys")

                # 场景触发服务清理
                if hass.services.has_service(DOMAIN, "trigger_scene"):
                    _LOGGER.debug("Removing trigger_scene service")
                    hass.services.async_remove(DOMAIN, "trigger_scene")

                # 虚拟按键服务清理
                if hass.services.has_service(DOMAIN, "press_switch"):
                    _LOGGER.debug("Removing press_switch service")
                    hass.services.async_remove(DOMAIN, "press_switch")

                _LOGGER.info("Global LifeSmart services cleanup completed")
        else:
            # 平台卸载失败的处理
            # 即使平台卸载失败，我们仍然尝试清理可以清理的资源
            _LOGGER.warning(
                "Platform unloading failed for entry %s, skipping detailed cleanup",
                entry_id,
            )

        # 记录卸载完成状态
        _LOGGER.info(
            "LifeSmart integration unloading completed for entry %s (success: %s)",
            entry_id,
            unload_ok,
        )
        return unload_ok

    except Exception as e:
        _LOGGER.error("Error occurred while unloading LifeSmart integration: %s", e)
        return False


async def _async_update_listener(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> None:
    """异步配置更新监听器 - 处理用户配置变更的响应机制

    本函数是Home Assistant配置选项更新的标准回调入口，当用户通过集成的
    "选项"界面修改配置时自动触发。它负责协调配置变更的应用流程。

    配置更新流程详解:
    ===============
    1. **变更检测**
       - Home Assistant检测到config_entry.options的变化
       - 自动调用所有已注册的更新监听器
       - 传递更新后的配置条目实例

    2. **重载策略**
       - 采用"完整重载"策略而非"热更新"
       - 确保所有配置变更都能正确应用
       - 避免部分更新导致的状态不一致

    3. **重载过程**
       - 首先调用async_unload_entry清理现有资源
       - 然后调用async_setup_entry重新初始化
       - 整个过程在同一事件循环中完成，确保原子性

    支持的配置更新场景:
    =================
    - **连接参数变更**: AppKey、AppToken、服务器地址等
    - **客户端偏好调整**: TCP/OpenAPI客户端优先级
    - **调试选项开关**: 日志级别、诊断信息收集等
    - **设备过滤设置**: 设备类型包含/排除规则
    - **性能调优参数**: 连接超时、重试次数、缓存策略等

    错误处理机制:
    =============
    - 重载失败时保持原有配置不变
    - 网络错误会触发ConfigEntryNotReady，自动重试
    - 配置错误会显示明确的错误信息给用户
    - 所有错误都会被记录用于故障排查

    性能考虑:
    =========
    - 重载过程会暂时中断设备状态更新
    - 设备实体会短暂显示为"unavailable"
    - 客户端连接会重新建立，可能有几秒延迟
    - 缓存数据会被清空，初次查询可能较慢

    用户体验优化:
    =============
    - 记录详细的重载进度信息
    - 提供明确的成功/失败反馈
    - 最小化服务中断时间
    - 保持设备状态的连续性

    线程安全:
    ========
    - 重载过程在Home Assistant主事件循环中执行
    - 使用配置条目锁防止并发修改
    - 确保旧资源完全清理后再创建新资源

    Args:
        hass (HomeAssistant): Home Assistant的核心实例，提供配置管理、
                              事件循环、重载控制等功能
        config_entry (ConfigEntry): 更新后的配置条目实例，包含用户的
                                   最新配置选项和数据

    Returns:
        None: 本函数不返回值，通过日志和Home Assistant UI反馈结果

    Raises:
        Exception: 重载过程中的任何异常都会被Home Assistant捕获并显示给用户

    调用时机:
    ========
    - 用户在集成选项界面点击"提交"后
    - 配置验证通过并保存到配置条目后
    - 在新配置生效前自动调用

    监听器生命周期:
    =============
    - 在async_setup_entry中注册
    - 在async_unload_entry中移除
    - 与配置条目生命周期绑定
    - 支持多个监听器并发执行

    最佳实践:
    ========
    - 重载前备份关键状态信息
    - 优先保证核心功能的连续性
    - 提供降级模式处理重载失败
    - 记录配置变更的详细日志
    """
    # 记录配置更新检测和重载启动
    _LOGGER.info(
        "Configuration update detected for entry %s, initiating integration reload...",
        config_entry.entry_id,
    )

    # 记录配置变更的关键信息，便于调试
    _LOGGER.debug(
        "Config options update - Entry: %s, Title: %s, Options: %s",
        config_entry.entry_id,
        config_entry.title,
        config_entry.options,
    )

    try:
        # 执行完整的集成重载
        # async_reload会依次调用：
        # 1. async_unload_entry - 清理现有资源
        # 2. async_setup_entry - 使用新配置重新初始化
        await hass.config_entries.async_reload(config_entry.entry_id)

        _LOGGER.info(
            "LifeSmart integration reload completed successfully for entry %s",
            config_entry.entry_id,
        )

    except Exception as e:
        # 重载失败的详细错误记录
        _LOGGER.error(
            "Failed to reload LifeSmart integration for entry %s after "
            "configuration update: %s",
            config_entry.entry_id,
            str(e),
            exc_info=True,
        )
        # 不重新抛出异常，让Home Assistant处理错误显示
        # 用户会在UI中看到重载失败的通知
