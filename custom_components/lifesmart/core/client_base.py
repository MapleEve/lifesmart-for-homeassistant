"""
LifeSmart 客户端抽象基类模块 (Abstract Base Class Module)

=================================================================================
模块概述 (Module Overview)
=================================================================================

此模块定义了 LifeSmart 智能家居系统中所有客户端的抽象基类 LifeSmartClientBase，
是整个系统的核心架构基石之一。该模块实现了以下关键设计理念：

🏗️ 架构设计理念 (Architectural Design Philosophy)
------------------------------------------------------------
1. **协议无关性 (Protocol Agnosticism)**：
   - 将设备控制的业务逻辑与具体的通信协议分离
   - 上层平台代码无需关心底层是通过云端API还是本地TCP连接实现

2. **命令抽象化 (Command Abstraction)**：
   - 统一所有设备操作为标准化的命令接口
   - 例如"打开窗帘"被抽象为向特定IO端口发送特定值的标准命令

3. **职责分离 (Separation of Concerns)**：
   - 基类负责"做什么"（业务逻辑）
   - 子类负责"怎么做"（通信实现）

4. **DRY原则 (Don't Repeat Yourself)**：
   - 所有客户端共享的设备控制逻辑集中在基类中
   - 避免在不同客户端中重复实现相同的业务逻辑

🔧 技术架构 (Technical Architecture)
------------------------------------------------------------
```
                    上层平台层 (Platform Layer)
                  ┌─────────────────────────────┐
                  │ light.py │ cover.py │ ... │
                  └─────────────────────────────┘
                             │
                  ┌─────────────────────────────┐
                  │    LifeSmartClientBase     │  ← 本模块
                  │      (抽象基类)              │
                  └─────────────────────────────┘
                             │
              ┌─────────────────────────────────────┐
              │                                     │
    ┌─────────────────┐                  ┌─────────────────┐
    │  OpenAPIClient  │                  │ LocalTCPClient  │
    │   (云端实现)      │                  │   (本地实现)      │
    └─────────────────┘                  └─────────────────┘
```

🎯 设计模式应用 (Design Patterns Applied)
------------------------------------------------------------
1. **抽象基类模式 (Abstract Base Class Pattern)**：
   - 使用 ABC 和 @abstractmethod 确保子类实现必需的方法
   - 提供模板方法模式的基础结构

2. **模板方法模式 (Template Method Pattern)**：
   - 基类定义操作的骨架，子类实现具体步骤
   - 例如：turn_on_light_switch_async 定义了开灯的标准流程

3. **策略模式 (Strategy Pattern)**：
   - 不同的客户端实现代表不同的通信策略
   - 运行时可以选择使用云端或本地客户端

📡 网络通信架构 (Network Communication Architecture)
------------------------------------------------------------
本基类定义了统一的网络通信接口，支持多种通信方式：

1. **云端通信 (Cloud Communication)**：
   - 通过 HTTPS API 与 LifeSmart 云服务器通信
   - 适用于远程控制和云端场景管理

2. **本地通信 (Local Communication)**：
   - 通过 TCP Socket 与本地智慧中心直接通信
   - 提供更快的响应速度和更好的可靠性

3. **混合模式 (Hybrid Mode)**：
   - 可以根据网络状况和设备可达性动态选择通信方式
   - 优先使用本地通信，必要时回退到云端通信

🔒 错误处理规范 (Error Handling Standards)
------------------------------------------------------------
本基类建立了统一的错误处理规范：

1. **返回值约定**：
   - 所有操作方法返回 int 类型的状态码
   - 0 表示成功，非0值表示不同类型的错误

2. **异常处理**：
   - 网络异常由子类捕获并转换为状态码
   - 业务逻辑错误在基类中统一处理

3. **日志记录**：
   - 使用结构化日志记录关键操作和错误信息
   - 便于问题诊断和系统监控

🔄 并发安全保证 (Concurrency Safety Guarantees)
------------------------------------------------------------
本基类的设计考虑了高并发环境下的安全性：

1. **异步接口**：
   - 所有网络操作都是异步的，避免阻塞主线程
   - 使用 async/await 模式确保高性能

2. **无状态设计**：
   - 基类本身不维护可变状态
   - 每个操作都是独立的，避免并发冲突

3. **线程安全**：
   - 基类方法可以安全地在多线程环境中调用
   - 具体的线程安全实现由子类负责

📚 扩展指南 (Extension Guidelines)
------------------------------------------------------------
如需实现新的客户端类型，请遵循以下规范：

1. **继承要求**：
   - 必须继承 LifeSmartClientBase
   - 必须实现所有 @abstractmethod 标记的方法

2. **命名约定**：
   - 类名以 "Client" 结尾
   - 方法名遵循 async_xxx 或 _async_xxx 模式

3. **错误处理**：
   - 网络错误必须转换为相应的状态码
   - 不应该让异常传播到基类

4. **性能考虑**：
   - 实现连接池以提高性能
   - 合理处理超时和重试逻辑

由 @MapleEve 设计和实现。

核心设计思想:
- 将与协议无关的设备控制业务逻辑（例如，"打开窗帘"意味着向特定IO口发送特定值）
  集中到这个基类中，以遵循 DRY (Don't Repeat Yourself) 原则。
- 定义一组底层的、必须由具体客户端（如云端、本地）实现的抽象方法
  （如 `_async_send_single_command`），从而将"做什么"与"怎么做"分离。
- 为所有客户端提供一个统一、稳定的接口，便于上层平台（light, cover, climate等）调用。
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

from homeassistant.components.climate import HVACMode

from .config.device_specs import NON_POSITIONAL_COVER_CONFIG
from .config.device_specs import REVERSE_LIFESMART_HVAC_MODE_MAP
from .config.mapping_engine import mapping_engine
from .const import (
    # --- 命令类型常量 ---
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_PRESS,
    CMD_TYPE_SET_VAL,
    CMD_TYPE_SET_CONFIG,
)
from .const import HTTP_TIMEOUT
from .platform.platform_detection import (
    safe_get,
    is_cover,
    get_device_effective_type,
)

_LOGGER = logging.getLogger(__name__)

# 常量定义
COVER_PLATFORM_NOT_SUPPORTED = "设备不支持cover平台操作"


class LifeSmartClientBase(ABC):
    """
    LifeSmart 客户端抽象基类 - 智能家居系统的核心通信接口

    =============================================================================
    类设计概述 (Class Design Overview)
    =============================================================================

    本类是所有 LifeSmart 客户端实现的抽象基类，采用经典的抽象基类 (ABC) 设计模式。
    它定义了一套完整的智能家居设备控制接口，确保所有具体实现都遵循统一的规范。

    🎯 设计目标 (Design Goals)
    -----------------------------------------------------------------------------
    1. **接口统一性**: 为所有客户端提供一致的 API 接口
    2. **业务逻辑复用**: 将通用的设备控制逻辑集中在基类中
    3. **实现灵活性**: 允许子类选择不同的通信方式（云端/本地）
    4. **类型安全**: 通过抽象方法确保子类正确实现必需功能

    🏗️ 架构层次 (Architectural Layers)
    -----------------------------------------------------------------------------
    ```
    ┌─────────────────────────────────────────────────────────────┐
    │                   公共接口层 (Public API Layer)                │
    │  async_get_all_devices(), async_send_single_command(), ...   │
    └─────────────────────────────────────────────────────────────┘
                                     │
    ┌─────────────────────────────────────────────────────────────┐
    │                  抽象方法层 (Abstract Methods Layer)          │
    │  _async_get_all_devices(), _async_send_single_command(), ... │
    └─────────────────────────────────────────────────────────────┘
                                     │
    ┌─────────────────────────────────────────────────────────────┐
    │                  设备控制层 (Device Control Layer)            │
    │  turn_on_light_switch_async(), open_cover_async(), ...       │
    └─────────────────────────────────────────────────────────────┘
    ```

    🔧 核心职责 (Core Responsibilities)
    -----------------------------------------------------------------------------
    1. **命令接口定义**: 定义所有设备操作的标准接口
    2. **业务逻辑实现**: 实现通用的设备控制业务逻辑
    3. **协议抽象**: 将具体的通信协议实现委托给子类
    4. **错误处理规范**: 建立统一的错误处理和状态码规范

    📡 支持的操作类型 (Supported Operation Types)
    -----------------------------------------------------------------------------
    - **设备管理**: 获取设备列表、修改设备属性
    - **基础控制**: 开关、调节、设置数值
    - **窗帘控制**: 开启、关闭、停止、位置设置
    - **温控设备**: HVAC模式、温度设置、风扇控制
    - **红外控制**: 红外按键、原始红外码发送
    - **场景管理**: 场景激活、创建、删除
    - **高级功能**: 定时器、EEPROM设置、图标修改

    🔒 线程安全保证 (Thread Safety Guarantees)
    -----------------------------------------------------------------------------
    本类设计为线程安全的，但具体的线程安全实现依赖于子类：
    - 基类方法本身是无状态的，可以安全地并发调用
    - 子类必须确保其实现的抽象方法是线程安全的
    - 建议子类使用连接池和异步锁来保证并发安全

    📋 子类实现要求 (Subclass Implementation Requirements)
    -----------------------------------------------------------------------------
    子类必须实现以下抽象方法：
    1. **核心通信方法**: _async_send_single_command, _async_send_multi_command
    2. **设备管理方法**: _async_get_all_devices, _async_get_hub_list
    3. **场景管理方法**: _async_set_scene, _async_add_scene, _async_delete_scene
    4. **红外控制方法**: _async_send_ir_key, _async_send_ir_code
    5. **高级功能方法**: _async_change_device_icon, _async_set_device_eeprom

    ⚠️ 实现注意事项 (Implementation Notes)
    -----------------------------------------------------------------------------
    1. **错误处理**: 所有方法都应返回适当的状态码，0表示成功
    2. **超时控制**: 网络操作应实现合理的超时机制
    3. **重试逻辑**: 对于网络失败，应实现适当的重试策略
    4. **日志记录**: 关键操作应记录详细的日志信息

    示例用法 (Example Usage)
    -----------------------------------------------------------------------------
    ```python
    # 通过具体客户端实例使用
    client = SomeConcreteClient()

    # 获取所有设备
    devices = await client.async_get_all_devices()

    # 控制灯光开关
    result = await client.turn_on_light_switch_async("P1", "hub_id", "device_id")

    # 控制窗帘
    result = await client.open_cover_async("hub_id", "device_id", device_data)
    ```
    """

    # ==========================================================================
    # 公共接口层 (Public API Layer)
    # ==========================================================================
    #
    # 以下方法构成了客户端的公共 API，为上层代码提供稳定、统一的接口。
    # 这些方法采用门面模式 (Facade Pattern)，将复杂的底层实现隐藏在
    # 简洁的公共接口之后。
    # ==========================================================================

    async def async_get_all_devices(self, timeout=HTTP_TIMEOUT) -> list[dict[str, Any]]:
        """
        获取所有设备信息的公共接口 - 设备发现的统一入口

        这是整个系统中设备发现功能的核心入口点，为上层平台代码提供统一的
        设备信息获取接口。该方法采用门面模式 (Facade Pattern)，隐藏了底层
        通信协议的复杂性。

        🔍 功能说明 (Functionality)
        -------------------------------------------------------------------
        - 从 LifeSmart 系统（云端或本地）获取用户账户下的所有设备信息
        - 返回的设备信息包含设备类型、状态、配置等完整数据
        - 支持超时控制，防止网络请求无限等待

        📊 返回数据结构 (Return Data Structure)
        -------------------------------------------------------------------
        返回的每个设备字典通常包含以下字段：
        - me: 设备唯一标识符
        - agt: 所属智慧中心ID
        - devtype: 设备类型代码
        - name: 设备名称
        - data: 设备当前状态数据（包含各IO口的值）
        - idx: 设备在中心中的索引

        🚀 性能考虑 (Performance Considerations)
        -------------------------------------------------------------------
        - 此操作可能涉及网络请求，建议在后台线程中调用
        - 返回的设备列表可能很大，建议进行适当的缓存
        - 超时设置应根据网络环境和设备数量合理调整

        Args:
            timeout (int, optional): 请求超时时间（秒）。
                                    默认值来自 HTTP_TIMEOUT 常量。
                                    建议根据网络环境调整此值。

        Returns:
            list[dict[str, Any]]: 设备信息字典列表。每个字典包含一个设备的
                                完整信息。如果获取失败或无设备，返回空列表。

        Raises:
            子类可能会抛出以下异常（由具体实现决定）：
            - TimeoutError: 请求超时
            - ConnectionError: 网络连接失败
            - AuthenticationError: 认证失败

        Example:
            >>> client = SomeConcreteClient()
            >>> devices = await client.async_get_all_devices(timeout=30)
            >>> for device in devices:
            ...     print(f"设备: {device['name']}, 类型: {device['devtype']}")

        Note:
            此方法为公共接口，实际实现委托给子类的 _async_get_all_devices 方法。
            这种设计允许不同的客户端实现不同的获取策略（云端API vs 本地TCP）。
        """
        return await self._async_get_all_devices()

    async def async_send_single_command(
        self, agt: str, me: str, idx: str, command_type: int, val: Any
    ) -> int:
        """
        发送单个IO口命令的公共接口 - 设备控制的核心方法

        这是整个系统中最重要的方法之一，实现了对单个设备IO口的精确控制。
        几乎所有的设备操作最终都会通过此方法来执行，它是设备控制的原子操作。

        🎯 设计理念 (Design Philosophy)
        -------------------------------------------------------------------
        LifeSmart 设备采用 IO 口模型，每个设备有多个 IO 口（如 P1, P2, P3 等），
        每个 IO 口控制设备的一个特定功能。这种设计提供了极大的灵活性：
        - P1 可能控制设备的主开关
        - P2 可能控制亮度或速度
        - P3 可能控制颜色或模式

        📡 命令类型说明 (Command Types)
        -------------------------------------------------------------------
        command_type 参数定义了操作的类型：
        - CMD_TYPE_ON (1): 打开/激活操作
        - CMD_TYPE_OFF (0): 关闭/停用操作
        - CMD_TYPE_SET_VAL: 设置数值（如亮度、温度）
        - CMD_TYPE_SET_CONFIG: 设置配置（如模式、选项）
        - CMD_TYPE_PRESS: 点动操作（按下后自动弹起）
        - CMD_TYPE_SET_TEMP_DECIMAL: 设置温度（十进制）

        🔄 执行流程 (Execution Flow)
        -------------------------------------------------------------------
        1. 验证参数的有效性（由子类实现）
        2. 构造符合协议格式的命令
        3. 通过相应的通信通道发送命令
        4. 等待设备响应
        5. 解析响应并返回状态码

        ⚡ 性能特点 (Performance Characteristics)
        -------------------------------------------------------------------
        - 异步执行，不阻塞调用线程
        - 支持并发调用，可同时控制多个设备
        - 响应时间通常在几十毫秒到几秒之间
        - 本地TCP连接比云端API响应更快

        Args:
            agt (str): 智慧中心ID (Agent ID)。标识设备所属的智慧中心。
                      例如: "12345678" 或 "hub_001"

            me (str): 设备ID (Device ID)。设备的唯一标识符。
                     例如: "87654321" 或 "light_001"

            idx (str): IO口标识符。指定要控制的设备IO口。
                      常见值: "P1", "P2", "P3", "V1", "O1" 等

            command_type (int): 命令类型。定义了要执行的操作类型。
                               取值应为 const.py 中定义的 CMD_TYPE_* 常量之一。

            val (Any): 命令参数值。具体类型和取值范围取决于 command_type：
                      - 开关操作: 0 (关闭) 或 1 (打开)
                      - 数值设置: 0-100 (百分比) 或其他范围
                      - 模式设置: 特定的模式代码

        Returns:
            int: 操作状态码。遵循以下约定：
                - 0: 操作成功
                - -1: 一般错误
                - -2: 网络错误
                - -3: 认证错误
                - -4: 设备不存在或不可达
                - 其他负值: 特定错误类型

        Raises:
            具体异常类型由子类实现决定，但通常不应该抛出异常，
            而是通过返回值指示错误状态。

        Example:
            >>> # 打开灯光设备的主开关
            >>> result = await client.async_send_single_command(
            ...     agt="12345678",
            ...     me="87654321",
            ...     idx="P1",
            ...     command_type=CMD_TYPE_ON,
            ...     val=1
            ... )
            >>> if result == 0:
            ...     print("灯光已成功打开")

            >>> # 设置灯光亮度为 80%
            >>> result = await client.async_send_single_command(
            ...     agt="12345678",
            ...     me="87654321",
            ...     idx="P2",
            ...     command_type=CMD_TYPE_SET_VAL,
            ...     val=80
            ... )

        Warning:
            - 并发调用时注意避免对同一设备的冲突操作
            - 某些设备可能对命令频率有限制
            - 命令参数的有效性由设备固件决定，无效参数可能被忽略

        Note:
            此方法是所有设备控制操作的基础，上层的便捷方法（如 turn_on_light_switch_async）
            最终都会调用此方法。具体的通信实现由子类的 _async_send_single_command 方法完成。
        """
        return await self._async_send_single_command(agt, me, idx, command_type, val)

    async def async_send_multi_command(
        self, agt: str, me: str, io_list: list[dict]
    ) -> int:
        """
        同时发送多个IO口命令的公共接口 - 批量设备控制

        该方法实现了对单个设备多个IO口的批量控制，相比多次调用单个命令
        具有更好的性能和原子性保证。适用于需要同时调整设备多个参数的场景。

        🚀 性能优势 (Performance Advantages)
        -------------------------------------------------------------------
        - 减少网络往返次数，提高控制效率
        - 保证命令的原子性执行
        - 降低网络延迟对控制精度的影响
        - 减少设备端的处理开销

        📋 典型应用场景 (Typical Use Cases)
        -------------------------------------------------------------------
        - 同时设置灯光的开关状态、亮度和颜色
        - 批量配置空调的模式、温度和风速
        - 一次性设置窗帘的位置和倾斜角度
        - 同时调整音响的音量、低音和高音

        Args:
            agt (str): 智慧中心ID，所有命令将发送到此中心
            me (str): 目标设备ID，所有IO口都属于此设备
            io_list (list[dict]): IO口命令列表，每个字典包含：
                                 - "idx": IO口标识符
                                 - "type": 命令类型
                                 - "val": 命令值

        Returns:
            int: 批量操作状态码，0表示所有命令都成功执行

        Example:
            >>> # 同时设置灯光的开关、亮度和颜色
            >>> commands = [
            ...     {"idx": "P1", "type": CMD_TYPE_ON, "val": 1},
            ...     {"idx": "P2", "type": CMD_TYPE_SET_VAL, "val": 80},
            ...     {"idx": "P3", "type": CMD_TYPE_SET_VAL, "val": 255}
            ... ]
            >>> await client.async_send_multi_command("hub001", "light001", commands)
        """
        return await self._async_send_multi_command(agt, me, io_list)

    async def async_set_scene(self, agt: str, scene_name: str) -> int:
        """
        激活场景的公共接口 - 智能场景控制

        场景是 LifeSmart 系统的高级功能，可以通过单一命令同时控制
        多个设备，实现复杂的自动化场景。

        Args:
            agt (str): 智慧中心ID，场景所属的中心
            scene_name (str): 场景名称，必须是已存在的场景

        Returns:
            int: 场景激活状态码，0表示场景成功触发
        """
        return await self._async_set_scene(agt, scene_name)

    async def async_send_ir_key(
        self,
        agt: str,
        me: str,
        category: str,
        brand: str,
        keys: str,
        ai: str = "",
        idx: str = "",
    ) -> int:
        """
        发送红外按键命令的公共接口 - 红外设备控制

        该方法实现了对红外设备的精确控制，支持空调、电视、机顶盒等
        各类红外设备的操作。

        Args:
            agt (str): 智慧中心ID
            me (str): 红外发射器设备ID
            category (str): 设备类别（如 "air_conditioner", "tv"）
            brand (str): 设备品牌
            keys (str): 按键列表的JSON字符串
            ai (str, optional): 虚拟遥控器ID（与idx二选一）
            idx (str, optional): 通用码库索引（与ai二选一）

        Returns:
            int: 红外命令发送状态码，0表示成功
        """
        return await self._async_send_ir_key(agt, me, category, brand, keys, ai, idx)

    async def async_add_scene(self, agt: str, scene_name: str, actions: str) -> int:
        """
        创建新场景的公共接口

        Args:
            agt (str): 智慧中心ID
            scene_name (str): 新场景的名称
            actions (str): 场景动作的JSON配置

        Returns:
            int: 场景创建状态码
        """
        return await self._async_add_scene(agt, scene_name, actions)

    async def async_delete_scene(self, agt: str, scene_name: str) -> int:
        """删除场景的公共接口"""
        return await self._async_delete_scene(agt, scene_name)

    async def async_get_scene_list(self, agt: str) -> list[dict[str, Any]]:
        """获取场景列表的公共接口"""
        return await self._async_get_scene_list(agt)

    async def async_get_room_list(self, agt: str) -> list[dict[str, Any]]:
        """获取房间列表的公共接口"""
        return await self._async_get_room_list(agt)

    async def async_get_hub_list(self) -> list[dict[str, Any]]:
        """获取智慧中心列表的公共接口"""
        return await self._async_get_hub_list()

    async def async_change_device_icon(self, device_id: str, icon: str) -> int:
        """修改设备图标的公共接口"""
        return await self._async_change_device_icon(device_id, icon)

    async def async_set_device_eeprom(
        self, device_id: str, key: str, value: Any
    ) -> int:
        """设置设备EEPROM的公共接口"""
        return await self._async_set_device_eeprom(device_id, key, value)

    async def async_add_device_timer(
        self, device_id: str, cron_info: str, key: str
    ) -> int:
        """为设备添加定时器的公共接口"""
        return await self._async_add_device_timer(device_id, cron_info, key)

    async def async_ir_control(self, device_id: str, options: dict) -> int:
        """通过场景控制红外设备的公共接口"""
        return await self._async_ir_control(device_id, options)

    async def async_send_ir_code(self, device_id: str, ir_data: list | bytes) -> int:
        """发送原始红外码的公共接口"""
        return await self._async_send_ir_code(device_id, ir_data)

    async def async_ir_raw_control(self, device_id: str, raw_data: str) -> int:
        """发送原始红外控制数据的公共接口"""
        return await self._async_ir_raw_control(device_id, raw_data)

    async def async_get_ir_remote_list(self, agt: str) -> dict[str, Any]:
        """获取红外遥控器列表的公共接口"""
        return await self._async_get_ir_remote_list(agt)

    # ==========================================================================
    # 受保护的抽象方法 (Protected Abstract Methods)
    # ==========================================================================
    #
    # 以下方法必须由所有具体的客户端子类实现。这些方法定义了与 LifeSmart
    # 系统通信的核心接口，不同的子类可以选择不同的通信方式：
    #
    # 1. OpenAPIClient: 通过 HTTPS API 与云端服务器通信
    # 2. LocalTCPClient: 通过 TCP Socket 与本地智慧中心通信
    # 3. 未来可能的其他实现: WebSocket, MQTT 等
    #
    # 🔒 访问控制说明:
    # - 使用下划线前缀表示这些是受保护的内部方法
    # - 只应由子类实现，不应由外部代码直接调用
    # - 公共接口通过上面的 async_xxx 方法提供
    #
    # 📋 实现要求:
    # - 所有方法必须是异步的 (async def)
    # - 必须返回约定的类型
    # - 错误情况应返回适当的状态码或空值，而不是抛出异常
    # - 应实现合理的超时和重试机制
    # ==========================================================================

    @abstractmethod
    async def _async_get_all_devices(
        self, timeout=HTTP_TIMEOUT
    ) -> list[dict[str, Any]]:
        """
        [抽象方法] 获取所有设备信息的底层实现

        这是所有客户端子类必须实现的核心方法之一。不同的客户端实现将使用
        不同的通信方式来获取设备信息：

        🌐 实现方式对比 (Implementation Approaches)
        -------------------------------------------------------------------

        **云端客户端 (OpenAPIClient)**:
        - 通过 HTTPS API 调用 LifeSmart 云端服务
        - 需要用户认证和授权
        - 数据经过云端同步，可能存在轻微延迟
        - 适合远程控制和跨网络访问

        **本地客户端 (LocalTCPClient)**:
        - 通过 TCP Socket 直接连接本地智慧中心
        - 响应速度更快，实时性更好
        - 需要在同一局域网内
        - 适合本地控制和高频操作

        📊 返回数据规范 (Return Data Specification)
        -------------------------------------------------------------------
        返回的设备列表中，每个设备字典必须包含以下标准字段：

        必需字段:
        - "me" (str): 设备唯一ID
        - "agt" (str): 所属智慧中心ID
        - "devtype" (str): 设备类型代码
        - "name" (str): 设备显示名称
        - "data" (dict): 设备状态数据，包含各IO口当前值

        可选字段:
        - "idx" (str): 设备索引
        - "room" (str): 所属房间
        - "online" (bool): 在线状态
        - "battery" (int): 电池电量（如适用）

        🚀 性能要求 (Performance Requirements)
        -------------------------------------------------------------------
        - 方法应在合理时间内完成（通常 < 30秒）
        - 支持适当的超时控制
        - 对于大量设备，考虑分页或流式处理
        - 网络错误时应优雅降级

        🔒 错误处理规范 (Error Handling Specification)
        -------------------------------------------------------------------
        实现者应处理以下错误情况：
        1. **网络超时**: 返回空列表，记录警告日志
        2. **认证失败**: 返回空列表，记录错误日志
        3. **服务不可用**: 返回空列表，记录错误日志
        4. **数据格式错误**: 尝试修复或跳过异常数据

        Args:
            timeout (int): 请求超时时间（秒）。子类应遵循此超时设置，
                          防止网络请求无限等待。

        Returns:
            list[dict[str, Any]]: 设备信息字典列表。即使在错误情况下，
                                 也应返回列表（可能为空），而不是 None。

        Implementation Example:
            >>> async def _async_get_all_devices(self, timeout=HTTP_TIMEOUT):
            ...     try:
            ...         # 执行具体的网络请求
            ...         response = await self._make_request("/devices", timeout=timeout)
            ...         return response.get("devices", [])
            ...     except TimeoutError:
            ...         _LOGGER.warning("获取设备列表超时")
            ...         return []
            ...     except Exception as e:
            ...         _LOGGER.error("获取设备列表失败: %s", e)
            ...         return []

        Warning:
            - 不要在此方法中抛出异常，应通过返回空列表处理错误
            - 确保返回的数据格式符合上层代码的期望
            - 注意处理网络重连和认证刷新
        """
        pass

    @abstractmethod
    async def _async_send_single_command(
        self, agt: str, me: str, idx: str, command_type: int, val: Any
    ) -> int:
        """
        [抽象方法] 发送单个IO口命令的底层实现

        这是整个 LifeSmart 系统中最核心的抽象方法，所有设备控制操作的最终
        执行都依赖于此方法的具体实现。不同的客户端实现将采用不同的通信
        协议和数据格式。

        🎯 协议实现差异 (Protocol Implementation Differences)
        -------------------------------------------------------------------

        **云端客户端实现特点**:
        - 构造符合 LifeSmart Cloud API 规范的 HTTP 请求
        - 处理 OAuth 认证和令牌刷新
        - 实现请求签名和加密
        - 处理云端限流和重试逻辑

        **本地客户端实现特点**:
        - 构造符合本地TCP协议的二进制数据包
        - 实现本地认证和会话管理
        - 处理TCP连接池和重连逻辑
        - 优化低延迟和高并发性能

        📦 数据包格式要求 (Packet Format Requirements)
        -------------------------------------------------------------------
        无论采用何种协议，数据包都必须包含以下信息：
        - 目标智慧中心标识 (agt)
        - 目标设备标识 (me)
        - 目标IO口标识 (idx)
        - 操作类型 (command_type)
        - 操作参数 (val)
        - 时间戳和校验信息

        🔄 执行流程规范 (Execution Flow Specification)
        -------------------------------------------------------------------
        标准的实现流程应包括：

        1. **参数验证**:
           - 验证 agt 和 me 的格式有效性
           - 检查 idx 是否为有效的IO口标识
           - 验证 command_type 是否为支持的类型
           - 验证 val 的类型和取值范围

        2. **连接管理**:
           - 检查或建立与目标的连接
           - 处理认证和授权
           - 选择合适的通信通道

        3. **命令构造**:
           - 按照协议规范构造命令数据包
           - 添加必要的头信息和校验码
           - 处理数据编码和加密

        4. **命令发送**:
           - 通过网络发送命令
           - 等待设备响应
           - 处理超时和重试

        5. **响应处理**:
           - 解析响应数据
           - 验证操作结果
           - 转换为标准状态码

        🎨 状态码规范 (Status Code Specification)
        -------------------------------------------------------------------
        实现必须返回以下标准状态码：

        成功状态:
        - 0: 命令执行成功

        客户端错误 (负数):
        - -1: 一般错误或未知错误
        - -2: 网络连接错误
        - -3: 认证或授权失败
        - -4: 目标设备不存在或不可达
        - -5: 无效的命令参数
        - -6: 命令超时
        - -7: 设备繁忙或资源不足

        设备端错误 (正数):
        - 1-99: 设备特定的错误代码
        - 100+: 协议层错误代码

        🚀 性能优化建议 (Performance Optimization Guidelines)
        -------------------------------------------------------------------
        - 实现连接池以减少连接开销
        - 使用异步IO避免阻塞
        - 对频繁访问的设备实现本地缓存
        - 合理设置超时时间（建议3-10秒）
        - 实现指数退避的重试策略

        Args:
            agt (str): 智慧中心ID，用于标识命令的目标中心
            me (str): 设备ID，用于标识命令的目标设备
            idx (str): IO口标识，用于标识设备的具体控制端口
            command_type (int): 命令类型，必须是有效的 CMD_TYPE_* 常量
            val (Any): 命令参数，类型和范围取决于具体的命令类型

        Returns:
            int: 操作状态码，0表示成功，非零值表示各种错误情况

        Implementation Example:
            >>> async def _async_send_single_command(
            ...     self, agt, me, idx, command_type, val
            ... ):
            ...     # 参数验证
            ...     if not all([agt, me, idx]):
            ...         return -5  # 无效参数
            ...
            ...     try:
            ...         # 构造命令
            ...         command = self._build_command(agt, me, idx, command_type, val)
            ...
            ...         # 发送命令
            ...         response = await self._send_command(command, timeout=10)
            ...
            ...         # 解析响应
            ...         return self._parse_response(response)
            ...
            ...     except TimeoutError:
            ...         return -6  # 超时
            ...     except ConnectionError:
            ...         return -2  # 网络错误
            ...     except Exception:
            ...         return -1  # 一般错误

        Critical Notes:
            - 此方法的实现质量直接影响整个系统的可靠性
            - 必须处理所有可能的异常情况，不允许抛出未捕获的异常
            - 性能要求高，通常需要在100ms内完成
            - 必须是线程安全的，支持高并发调用
        """
        pass

    @abstractmethod
    async def _async_send_multi_command(
        self, agt: str, me: str, io_list: list[dict]
    ) -> int:
        """
        [抽象方法] 同时发送多个IO口的命令
        必须由具体的客户端子类（云端/本地）实现。
        """
        pass

    @abstractmethod
    async def _async_set_scene(self, agt: str, scene_name: str) -> int:
        """[抽象方法] 激活一个场景。"""
        pass

    @abstractmethod
    async def _async_send_ir_key(
        self,
        agt: str,
        me: str,
        category: str,
        brand: str,
        keys: str,
        ai: str = "",
        idx: str = "",
    ) -> int:
        """[抽象方法] 发送红外按键命令。"""
        pass

    @abstractmethod
    async def _async_add_scene(self, agt: str, scene_name: str, actions: str) -> int:
        """[抽象方法] 创建新场景。"""
        pass

    @abstractmethod
    async def _async_delete_scene(self, agt: str, scene_name: str) -> int:
        """[抽象方法] 删除场景。"""
        pass

    @abstractmethod
    async def _async_get_scene_list(self, agt: str) -> list[dict[str, Any]]:
        """[抽象方法] 获取场景列表。"""
        pass

    @abstractmethod
    async def _async_get_room_list(self, agt: str) -> list[dict[str, Any]]:
        """[抽象方法] 获取房间列表。"""
        pass

    @abstractmethod
    async def _async_get_hub_list(self) -> list[dict[str, Any]]:
        """[抽象方法] 获取中枢列表。"""
        pass

    @abstractmethod
    async def _async_change_device_icon(self, device_id: str, icon: str) -> int:
        """[抽象方法] 修改设备图标。"""
        pass

    @abstractmethod
    async def _async_set_device_eeprom(
        self, device_id: str, key: str, value: Any
    ) -> int:
        """[抽象方法] 设置设备EEPROM。"""
        pass

    @abstractmethod
    async def _async_add_device_timer(
        self, device_id: str, cron_info: str, key: str
    ) -> int:
        """[抽象方法] 为设备添加定时器。"""
        pass

    @abstractmethod
    async def _async_ir_control(self, device_id: str, options: dict) -> int:
        """[抽象方法] 通过场景控制红外设备。"""
        pass

    @abstractmethod
    async def _async_send_ir_code(self, device_id: str, ir_data: list | bytes) -> int:
        """[抽象方法] 发送原始红外码。"""
        pass

    @abstractmethod
    async def _async_ir_raw_control(self, device_id: str, raw_data: str) -> int:
        """[抽象方法] 发送原始红外控制数据。"""
        pass

    @abstractmethod
    async def _async_get_ir_remote_list(self, agt: str) -> dict[str, Any]:
        """[抽象方法] 获取红外遥控器列表。"""
        pass

    # ==========================================================================
    # 设备控制业务逻辑层 (Device Control Business Logic Layer)
    # ==========================================================================
    #
    # 以下方法实现了具体的设备控制业务逻辑，它们是在抽象方法基础上构建的
    # 高级接口。这些方法体现了 LifeSmart 系统的设备控制模式和最佳实践。
    #
    # 🎯 设计原则:
    # - 每个方法专注于一个特定的设备操作
    # - 隐藏底层IO口操作的复杂性
    # - 提供类型安全和参数验证
    # - 统一的错误处理和状态返回
    #
    # 🏗️ 架构层次:
    # 这些方法位于架构的中间层，连接上层平台代码和底层通信接口：
    # Platform Layer (light.py, cover.py) → Business Logic Layer → Communication Layer
    # ==========================================================================

    # --------------------------------------------------------------------------
    # 通用开关/灯光控制 (Generic Switch/Light Control)
    # --------------------------------------------------------------------------
    #
    # 以下方法实现了最基础的开关和灯光控制功能。这些操作适用于大多数
    # LifeSmart 设备，包括智能开关、智能灯具、智能插座等。
    # --------------------------------------------------------------------------

    async def turn_on_light_switch_async(self, idx: str, agt: str, me: str) -> int:
        """
        开启灯光或开关设备 - 通用开启操作的标准实现

        这是最常用的设备控制方法之一，实现了对各类开关设备的统一开启操作。
        该方法抽象了不同设备类型的差异，提供一致的控制接口。

        🔧 操作原理 (Operation Principle)
        -------------------------------------------------------------------
        - 向指定设备的指定IO口发送 CMD_TYPE_ON 命令
        - 命令值设为 1，表示"开启"状态
        - 适用于所有支持二进制开关状态的设备

        🎯 适用设备类型 (Compatible Device Types)
        -------------------------------------------------------------------
        - 智能开关 (Smart Switches)
        - 智能灯具 (Smart Lights)
        - 智能插座 (Smart Plugs)
        - 智能继电器 (Smart Relays)
        - 其他具有开关功能的设备

        📍 IO口约定 (IO Port Conventions)
        -------------------------------------------------------------------
        不同设备类型的常用IO口:
        - P1: 主开关口，大多数设备的默认控制端口
        - P2: 副开关口，用于多路开关设备
        - P3-P8: 扩展开关口，用于多路扩展设备

        Args:
            idx (str): IO口标识符。指定要控制的设备端口。
                      常用值: "P1" (主开关), "P2" (副开关), "P3"-"P8" (扩展)

            agt (str): 智慧中心ID。设备所属的智慧中心唯一标识。
                      格式通常为8位数字字符串，如 "12345678"

            me (str): 设备ID。要控制的设备唯一标识符。
                     格式通常为8位数字字符串，如 "87654321"

        Returns:
            int: 操作状态码
                - 0: 开启成功，设备已切换到开启状态
                - 负值: 操作失败，具体错误码请参考 _async_send_single_command

        Example:
            >>> # 开启客厅主灯的主开关
            >>> result = await client.turn_on_light_switch_async(
            ...     idx="P1",
            ...     agt="12345678",
            ...     me="87654321"
            ... )
            >>> if result == 0:
            ...     print("灯光已成功开启")
            ... else:
            ...     print(f"开启失败，错误码: {result}")

        Performance:
            - 典型响应时间: 50-500ms
            - 支持高并发调用
            - 建议避免频繁开关（< 1秒间隔）

        Note:
            某些智能灯具在开启后可能需要短暂时间来初始化，
            建议在连续操作之间留出适当的时间间隔。
        """
        return await self._async_send_single_command(agt, me, idx, CMD_TYPE_ON, 1)

    async def turn_off_light_switch_async(self, idx: str, agt: str, me: str) -> int:
        """
        关闭灯光或开关设备 - 通用关闭操作的标准实现

        与 turn_on_light_switch_async 相对应，实现设备的关闭操作。
        该方法确保设备安全、彻底地切换到关闭状态。

        🔧 操作原理 (Operation Principle)
        -------------------------------------------------------------------
        - 向指定设备的指定IO口发送 CMD_TYPE_OFF 命令
        - 命令值设为 0，表示"关闭"状态
        - 对于可调光设备，通常会同时关闭所有输出

        💡 智能节能特性 (Smart Energy Saving)
        -------------------------------------------------------------------
        关闭操作不仅停止设备的主要功能，还通常会：
        - 断开主电路，减少待机功耗
        - 停止状态指示灯（如适用）
        - 进入低功耗待机模式
        - 保存当前设置以备下次开启时恢复

        🎯 适用场景 (Use Cases)
        -------------------------------------------------------------------
        - 夜间关灯节能
        - 离家前关闭所有电器
        - 安全关闭防止过载
        - 定时控制场景
        - 场景切换时的状态重置

        Args:
            idx (str): IO口标识符。与开启操作保持一致，
                      通常使用相同的端口进行开关控制。

            agt (str): 智慧中心ID。必须与设备注册时的中心ID一致。

            me (str): 设备ID。确保指向正确的目标设备。

        Returns:
            int: 操作状态码
                - 0: 关闭成功，设备已切换到关闭状态
                - 负值: 操作失败，设备可能仍处于开启状态

        Example:
            >>> # 关闭卧室台灯
            >>> result = await client.turn_off_light_switch_async(
            ...     idx="P1",
            ...     agt="12345678",
            ...     me="87654321"
            ... )
            >>> if result == 0:
            ...     print("设备已安全关闭")

        Safety Notes:
            - 某些设备（如电机）关闭时可能有短暂的惯性运行
            - 关闭操作通常比开启操作更快完成
            - 频繁开关可能影响设备寿命，建议合理使用
        """
        return await self._async_send_single_command(agt, me, idx, CMD_TYPE_OFF, 0)

    async def press_switch_async(
        self, idx: str, agt: str, me: str, duration_ms: int
    ) -> int:
        """
        执行点动操作 - 模拟物理按钮的按下和释放

        点动操作是一种特殊的控制模式，模拟传统物理按钮的行为：按下触发，
        保持指定时间后自动释放。这种操作模式在某些特定场景下非常有用。

        🎯 点动操作的特点 (Momentary Operation Characteristics)
        -------------------------------------------------------------------
        - **短暂激活**: 设备被激活指定时间后自动恢复初始状态
        - **自动复位**: 无需手动发送关闭命令
        - **精确时控**: 支持毫秒级的时间控制精度
        - **防误操作**: 避免因忘记关闭而导致的持续运行

        🔧 典型应用场景 (Typical Use Cases)
        -------------------------------------------------------------------

        **门禁控制**:
        - 电子门锁的临时开启
        - 电动门的点动控制
        - 门禁系统的通行授权

        **照明控制**:
        - 楼道灯的定时照明
        - 感应灯的手动触发
        - 应急照明的测试

        **机械控制**:
        - 电动窗帘的微调
        - 车库门的点动开启
        - 工业设备的点动操作

        **安全控制**:
        - 报警器的测试
        - 安防设备的手动触发
        - 紧急设备的激活

        ⚙️ 时间计算机制 (Time Calculation Mechanism)
        -------------------------------------------------------------------
        duration_ms 参数会被转换为 LifeSmart 协议的时间单位：
        - 输入: 毫秒 (milliseconds)
        - 转换: 除以100后取整 (val = max(1, round(duration_ms / 100)))
        - 协议单位: 100毫秒为一个时间单位
        - 最小值: 1个时间单位 (100毫秒)

        示例转换:
        - 50ms → 1单位 (实际100ms)
        - 150ms → 2单位 (实际200ms)
        - 500ms → 5单位 (实际500ms)
        - 2000ms → 20单位 (实际2000ms)

        Args:
            idx (str): IO口标识符。指定执行点动操作的设备端口。
                      点动操作通常使用设备的主控制端口。

            agt (str): 智慧中心ID。必须是设备所属的有效中心ID。

            me (str): 设备ID。目标设备的唯一标识符。

            duration_ms (int): 点动持续时间（毫秒）。
                              有效范围: 50-25500 (0.05秒-25.5秒)
                              推荐范围: 100-5000 (0.1秒-5秒)

        Returns:
            int: 操作状态码
                - 0: 点动操作启动成功，设备将自动在指定时间后复位
                - 负值: 操作失败，设备状态未改变

        Example:
            >>> # 门锁点动开启3秒
            >>> result = await client.press_switch_async(
            ...     idx="P1",
            ...     agt="12345678",
            ...     me="87654321",
            ...     duration_ms=3000
            ... )
            >>> if result == 0:
            ...     print("门锁将在3秒后自动重新锁定")

            >>> # 楼道灯点动开启30秒
            >>> await client.press_switch_async(
            ...     idx="P1", agt="hub001", me="light001", duration_ms=30000
            ... )

        Performance Considerations:
            - 点动操作的响应时间通常比普通开关更快
            - 设备会在内部维护定时器，不占用网络资源
            - 多个点动操作可以并发执行，互不干扰

        Safety Notes:
            - 确保 duration_ms 设置合理，避免过长或过短
            - 某些设备可能对点动时间有硬件限制
            - 在点动期间，设备可能不响应其他控制命令
            - 紧急情况下，可以通过发送关闭命令提前终止点动

        Warning:
            点动操作启动后无法中途修改时间，如需提前结束，
            应发送相应的停止或关闭命令。
        """
        val = max(1, round(duration_ms / 100))
        return await self._async_send_single_command(agt, me, idx, CMD_TYPE_PRESS, val)

    # --------------------------------------------------------------------------
    # 窗帘/覆盖物控制 (Cover/Curtain Control)
    # --------------------------------------------------------------------------
    #
    # 以下方法实现了对窗帘、百叶窗、车库门等覆盖类设备的控制。这类设备
    # 的特点是具有位置概念，支持开启、关闭、停止和位置设置等操作。
    #
    # 🏗️ 窗帘控制架构特点:
    # - 支持有位置反馈和无位置反馈两种类型的设备
    # - 统一的命令接口适配不同的硬件实现
    # - 智能映射系统自动识别设备能力和配置
    # - 优雅降级处理不支持的操作
    # --------------------------------------------------------------------------

    async def open_cover_async(self, agt: str, me: str, device: dict) -> int:
        """
        开启窗帘或车库门 - 覆盖类设备的开启操作

        这是覆盖类设备控制的核心方法之一，实现了对各种覆盖设备的统一开启
        操作。该方法采用智能映射机制，能够自动适配不同类型的覆盖设备。

        🎯 设备类型支持 (Supported Device Types)
        -------------------------------------------------------------------

        **窗帘设备**:
        - 电动窗帘 (SL_CURTAIN)
        - 电动百叶窗 (SL_BLIND)
        - 卷帘门 (SL_ROLLERSHUTTER)
        - 天窗控制器 (SL_SKYLIGHT)

        **门控设备**:
        - 车库门控制器 (SL_GARAGE)
        - 电动大门 (SL_GATE)
        - 自动门控制器 (SL_AUTODOOR)

        **其他覆盖设备**:
        - 遮阳篷 (SL_AWNING)
        - 投影幕布 (SL_PROJECTOR_SCREEN)

        🔧 智能映射机制 (Intelligent Mapping Mechanism)
        -------------------------------------------------------------------
        该方法采用三层映射策略来适配不同的设备：

        **1. 新版映射系统 (映射引擎)**:
        - 从 mapping_engine 获取设备特定的配置
        - 支持复杂的命令配置和参数映射
        - 优先使用 commands.open 配置

        **2. 传统描述判断**:
        - 基于 IO 口描述字符串的模糊匹配
        - 支持 "position" 和 "open" 关键词识别
        - 向后兼容老版本的设备配置

        **3. 设备类型回退**:
        - 使用 NON_POSITIONAL_COVER_CONFIG 静态配置
        - 为不支持位置控制的设备提供基础开关控制

        🎛️ 操作模式详解 (Operation Modes)
        -------------------------------------------------------------------

        **位置控制模式**:
        - 命令类型: CMD_TYPE_SET_VAL
        - 参数值: 100 (表示完全开启)
        - 适用于支持位置反馈的智能窗帘

        **开关控制模式**:
        - 命令类型: CMD_TYPE_ON
        - 参数值: 1 (表示开启动作)
        - 适用于传统的继电器控制设备

        🔄 执行流程 (Execution Flow)
        -------------------------------------------------------------------
        1. **设备类型验证**: 确认设备支持 cover 平台操作
        2. **映射配置解析**: 获取设备的具体控制配置
        3. **IO口遍历**: 查找适合的控制端口
        4. **命令构造**: 根据配置构造合适的控制命令
        5. **命令发送**: 执行底层的设备控制操作
        6. **状态返回**: 返回操作结果状态码

        Args:
            agt (str): 智慧中心ID。设备所属的智慧中心标识符。

            me (str): 设备ID。目标覆盖设备的唯一标识符。

            device (dict): 设备完整信息字典。必须包含以下字段：
                          - "devtype": 设备类型代码
                          - "data": 设备状态数据
                          - 其他设备属性信息

        Returns:
            int: 操作状态码
                - 0: 开启成功，设备开始执行开启动作
                - -1: 操作失败，可能的原因：
                     * 设备不支持 cover 平台
                     * 设备类型不支持开启操作
                     * 网络通信失败

        Example:
            >>> # 开启客厅窗帘
            >>> device_info = {
            ...     "me": "87654321",
            ...     "devtype": "SL_CURTAIN",
            ...     "data": {"P1": 0, "P2": 50},
            ...     "name": "客厅窗帘"
            ... }
            >>> result = await client.open_cover_async(
            ...     agt="12345678",
            ...     me="87654321",
            ...     device=device_info
            ... )
            >>> if result == 0:
            ...     print("窗帘开始开启...")

        Performance Notes:
            - 机械设备的执行时间通常较长（几秒到几十秒）
            - 开启过程中设备可能不响应其他位置命令
            - 建议在连续操作前检查设备的忙碌状态

        Safety Considerations:
            - 开启操作会使设备移动到完全开启位置
            - 确保设备路径上没有障碍物
            - 某些设备支持防夹保护，遇阻时会自动停止
            - 可以随时发送停止命令中断开启过程

        Compatibility Notes:
            该方法向后兼容旧版本的设备配置，但新设备建议使用
            映射引擎的 commands 配置以获得更好的控制精度。
        """
        if not is_cover(device):
            device_type = get_device_effective_type(device)
            _LOGGER.warning("设备类型 %s 不支持cover平台操作", device_type)
            return -1

        device_type = get_device_effective_type(device)

        # Phase 2: 使用DeviceResolver统一接口 - 简化设备映射获取
        from .resolver import get_device_resolver

        resolver = get_device_resolver()
        platform_config = resolver.get_platform_config(device, "cover")

        if not platform_config:
            _LOGGER.warning("设备不支持cover平台: %s", device)
            return -1

        cover_config = platform_config.ios

        # 查找合适的IO口进行操作
        for io_port, io_config in cover_config.items():
            if isinstance(io_config, dict):
                # 检查是否有commands配置
                commands = io_config.get("commands", {})
                if "open" in commands:
                    open_cmd = commands["open"]
                    return await self._async_send_single_command(
                        agt,
                        me,
                        io_port,
                        open_cmd.get("type", CMD_TYPE_SET_VAL),
                        open_cmd.get("val", 100),
                    )

                # 旧的逻辑:通过描述判断
                description = io_config.get("description", "").lower()
                if "position" in description:
                    return await self._async_send_single_command(
                        agt, me, io_port, CMD_TYPE_SET_VAL, 100
                    )
                elif "open" in description:
                    return await self._async_send_single_command(
                        agt, me, io_port, CMD_TYPE_ON, 1
                    )

        # 回退到NON_POSITIONAL_COVER_CONFIG
        if device_type in NON_POSITIONAL_COVER_CONFIG:
            cmd_idx = safe_get(NON_POSITIONAL_COVER_CONFIG, device_type, "open")
            if cmd_idx is None:
                _LOGGER.warning("设备类型 %s 缺少 'open' 配置", device_type)
                return -1
            return await self._async_send_single_command(
                agt, me, cmd_idx, CMD_TYPE_ON, 1
            )

        _LOGGER.warning("设备类型 %s 的 'open_cover' 操作未被支持。", device_type)
        return -1

    async def close_cover_async(self, agt: str, me: str, device: dict) -> int:
        """关闭窗帘或车库门。"""
        if not is_cover(device):
            _LOGGER.warning(COVER_PLATFORM_NOT_SUPPORTED)
            return -1

        device_type = get_device_effective_type(device)

        # 获取设备映射配置
        device_mapping = mapping_engine.resolve_device_mapping_from_data(device)
        cover_config = device_mapping.get("cover", {})

        # 查找合适的IO口进行操作
        for io_port, io_config in cover_config.items():
            if isinstance(io_config, dict):
                # 检查是否有commands配置
                commands = io_config.get("commands", {})
                if "close" in commands:
                    close_cmd = commands["close"]
                    return await self._async_send_single_command(
                        agt,
                        me,
                        io_port,
                        close_cmd.get("type", CMD_TYPE_SET_VAL),
                        close_cmd.get("val", 0),
                    )

                # 旧的逻辑:通过描述判断
                description = io_config.get("description", "").lower()
                if "position" in description:
                    return await self._async_send_single_command(
                        agt, me, io_port, CMD_TYPE_SET_VAL, 0
                    )
                elif "close" in description:
                    return await self._async_send_single_command(
                        agt, me, io_port, CMD_TYPE_ON, 1
                    )

        # 回退到NON_POSITIONAL_COVER_CONFIG
        if device_type in NON_POSITIONAL_COVER_CONFIG:
            cmd_idx = safe_get(NON_POSITIONAL_COVER_CONFIG, device_type, "close")
            if cmd_idx is None:
                _LOGGER.warning("设备类型 %s 缺少 'close' 配置", device_type)
                return -1
            return await self._async_send_single_command(
                agt, me, cmd_idx, CMD_TYPE_ON, 1
            )

        _LOGGER.warning("设备类型 %s 的 'close_cover' 操作未被支持。", device_type)
        return -1

    async def stop_cover_async(self, agt: str, me: str, device: dict) -> int:
        """停止窗帘或车库门。"""
        if not is_cover(device):
            _LOGGER.warning(COVER_PLATFORM_NOT_SUPPORTED)
            return -1

        device_type = get_device_effective_type(device)

        # 获取设备映射配置
        device_mapping = mapping_engine.resolve_device_mapping_from_data(device)
        cover_config = device_mapping.get("cover", {})

        # 查找合适的IO口进行操作
        for io_port, io_config in cover_config.items():
            if isinstance(io_config, dict):
                # 检查是否有commands配置
                commands = io_config.get("commands", {})
                if "stop" in commands:
                    stop_cmd = commands["stop"]
                    return await self._async_send_single_command(
                        agt,
                        me,
                        io_port,
                        stop_cmd.get("type", CMD_TYPE_SET_CONFIG),
                        stop_cmd.get("val", CMD_TYPE_OFF),
                    )

                # 旧的逻辑:通过描述判断
                description = io_config.get("description", "").lower()
                if "position" in description:
                    return await self._async_send_single_command(
                        agt, me, io_port, CMD_TYPE_SET_CONFIG, CMD_TYPE_OFF
                    )
                elif "stop" in description:
                    return await self._async_send_single_command(
                        agt, me, io_port, CMD_TYPE_ON, 1
                    )

        # 回退到NON_POSITIONAL_COVER_CONFIG
        if device_type in NON_POSITIONAL_COVER_CONFIG:
            cmd_idx = safe_get(NON_POSITIONAL_COVER_CONFIG, device_type, "stop")
            if cmd_idx is None:
                _LOGGER.warning("设备类型 %s 缺少 'stop' 配置", device_type)
                return -1
            return await self._async_send_single_command(
                agt, me, cmd_idx, CMD_TYPE_ON, 1
            )

        _LOGGER.warning("设备类型 %s 的 'stop_cover' 操作未被支持。", device_type)
        return -1

    async def set_cover_position_async(
        self, agt: str, me: str, position: int, device: dict
    ) -> int:
        """设置窗帘或车库门到指定位置。"""
        if not is_cover(device):
            _LOGGER.warning(COVER_PLATFORM_NOT_SUPPORTED)
            return -1

        device_type = get_device_effective_type(device)

        # 获取设备映射配置
        device_mapping = mapping_engine.resolve_device_mapping_from_data(device)
        cover_config = device_mapping.get("cover", {})

        # 查找位置控制IO口
        for io_port, io_config in cover_config.items():
            if isinstance(io_config, dict):
                # 检查是否有commands配置
                commands = io_config.get("commands", {})
                if "set_position" in commands:
                    set_pos_cmd = commands["set_position"]
                    return await self._async_send_single_command(
                        agt,
                        me,
                        io_port,
                        set_pos_cmd.get("type", CMD_TYPE_SET_VAL),
                        position,
                    )

                # 旧的逻辑:通过描述判断
                description = io_config.get("description", "").lower()
                if "position" in description:
                    return await self._async_send_single_command(
                        agt, me, io_port, CMD_TYPE_SET_VAL, position
                    )

        _LOGGER.warning("设备类型 %s 不支持设置位置。", device_type)
        return -1

    # --------------------------------------------------------------------------
    # 温控设备控制 (Climate Device Control)
    # --------------------------------------------------------------------------
    #
    # 以下方法实现了对温控设备的控制，包括空调、地暖、热水器等。温控设备
    # 通常具有复杂的状态和多种操作模式，需要精确的参数控制和状态管理。
    #
    # 🌡️ 温控系统特点:
    # - 支持多种HVAC模式 (制冷、制热、除湿、送风等)
    # - 精确的温度控制 (通常精度为0.1°C)
    # - 复杂的风扇速度和模式管理
    # - 设备特定的参数映射和限制
    # --------------------------------------------------------------------------

    async def async_set_climate_hvac_mode(
        self,
        agt: str,
        me: str,
        device: dict,
        hvac_mode: HVACMode,
        current_val: int = 0,
    ) -> int:
        """
        设置温控设备的HVAC模式 - 温控系统的核心功能

        HVAC（Heating, Ventilation, and Air Conditioning）模式控制是温控设备
        的核心功能，决定了设备的工作方式和输出效果。该方法实现了对各种
        温控设备的统一模式控制。

        🌡️ HVAC模式详解 (HVAC Mode Explanation)
        -------------------------------------------------------------------

        **HomeAssistant标准模式**:
        - OFF: 设备关闭，停止所有温控功能
        - HEAT: 制热模式，设备加热到目标温度
        - COOL: 制冷模式，设备制冷到目标温度
        - AUTO: 自动模式，根据温差自动选择制热/制冷
        - DRY: 除湿模式，主要去除空气中的湿度
        - FAN_ONLY: 仅送风，不进行温度调节

        **设备特定模式** (取决于具体设备类型):
        - HEAT_COOL: 冷暖双向自动调节
        - ECO: 节能模式
        - SLEEP: 睡眠模式

        🔧 模式映射机制 (Mode Mapping Mechanism)
        -------------------------------------------------------------------

        由于不同厂商的设备使用不同的模式代码，系统采用分层映射策略：

        **1. 设备特定映射** (最高优先级):
        ```
        commands: {
            "set_mode": {
                "hvac_modes": {
                    "cool": 1,
                    "heat": 2,
                    "auto": 3
                }
            }
        }
        ```

        **2. 设备类型映射** (中等优先级):
        - SL_CP_AIR: 使用 REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP
        - V_AIR_P*: 使用 REVERSE_F_HVAC_MODE_MAP
        - SL_TR_ACIPM: 使用 REVERSE_F_HVAC_MODE_MAP
        - 其他: 使用 REVERSE_LIFESMART_HVAC_MODE_MAP

        **3. 默认映射** (最低优先级):
        - 所有未匹配的模式默认映射为 1

        🔄 执行流程 (Execution Flow)
        -------------------------------------------------------------------

        **关闭模式处理**:
        1. 检测到 HVACMode.OFF
        2. 查找设备的 off 命令配置
        3. 发送关闭命令到相应IO口
        4. 如无特定配置，默认向 P1 口发送 CMD_TYPE_OFF

        **其他模式处理**:
        1. 首先开启设备（如果需要）
        2. 查找模式控制IO口配置
        3. 根据映射规则确定模式值
        4. 发送 CMD_TYPE_SET_CONFIG 命令
        5. 返回操作结果

        🎛️ IO口分工 (IO Port Assignment)
        -------------------------------------------------------------------
        典型的温控设备IO口分工：
        - P1: 设备主开关 (ON/OFF)
        - P2: HVAC模式选择 (COOL/HEAT/AUTO等)
        - P3: 目标温度设置
        - P4: 风扇速度控制
        - P5: 特殊功能 (定时、节能等)

        Args:
            agt (str): 智慧中心ID。温控设备所属的中心标识符。

            me (str): 设备ID。目标温控设备的唯一标识符。

            device (dict): 设备完整信息。包含设备类型、当前状态等信息，
                          用于确定正确的模式映射规则。

            hvac_mode (HVACMode): 目标HVAC模式。必须是HomeAssistant
                                 定义的标准HVACMode枚举值之一。

            current_val (int, optional): 当前值参考。某些设备在模式
                                       切换时需要参考当前状态。默认为0。

        Returns:
            int: 操作状态码
                - 0: 模式设置成功，设备开始按新模式工作
                - -1: 设置失败，可能的原因：
                     * 设备不支持目标HVAC模式
                     * 设备当前状态不允许模式切换
                     * 网络通信失败

        Example:
            >>> # 设置空调为制冷模式
            >>> from homeassistant.components.climate import HVACMode
            >>> result = await client.async_set_climate_hvac_mode(
            ...     agt="12345678",
            ...     me="87654321",
            ...     device=device_info,
            ...     hvac_mode=HVACMode.COOL
            ... )
            >>> if result == 0:
            ...     print("空调已切换到制冷模式")

            >>> # 关闭温控设备
            >>> await client.async_set_climate_hvac_mode(
            ...     agt="12345678", me="87654321",
            ...     device=device_info, hvac_mode=HVACMode.OFF
            ... )

        Performance Notes:
            - 模式切换通常需要几秒钟完成
            - 某些设备在模式切换时会短暂停止工作
            - 频繁的模式切换可能影响设备寿命

        Compatibility:
            - 支持所有符合LifeSmart协议的温控设备
            - 自动适配不同厂商的模式代码差异
            - 向后兼容旧版本的设备固件

        Warning:
            某些模式切换可能会重置其他参数（如目标温度、风扇速度），
            建议在模式切换后重新设置相关参数。
        """
        device_type = get_device_effective_type(device)

        # 获取设备映射配置
        device_mapping = mapping_engine.resolve_device_mapping_from_data(device)
        climate_config = device_mapping.get("climate", {})

        if hvac_mode == HVACMode.OFF:
            # 查找开关IO口
            for io_port, io_config in climate_config.items():
                if isinstance(io_config, dict):
                    commands = io_config.get("commands", {})
                    if "off" in commands:
                        off_cmd = commands["off"]
                        return await self._async_send_single_command(
                            agt,
                            me,
                            io_port,
                            off_cmd.get("type", CMD_TYPE_OFF),
                            off_cmd.get("val", 0),
                        )
            # 默认使用P1口关闭
            return await self._async_send_single_command(agt, me, "P1", CMD_TYPE_OFF, 0)

        # 先打开设备
        for io_port, io_config in climate_config.items():
            if isinstance(io_config, dict):
                commands = io_config.get("commands", {})
                if "on" in commands:
                    on_cmd = commands["on"]
                    await self._async_send_single_command(
                        agt,
                        me,
                        io_port,
                        on_cmd.get("type", CMD_TYPE_ON),
                        on_cmd.get("val", 1),
                    )
                    break
        else:
            # 默认使用P1口打开
            await self._async_send_single_command(agt, me, "P1", CMD_TYPE_ON, 1)

        # 查找HVAC模式控制IO口
        for io_port, io_config in climate_config.items():
            if isinstance(io_config, dict):
                # description = io_config.get("description", "").lower()  # Unused
                commands = io_config.get("commands", {})

                # 优先使用commands配置
                if "set_mode" in commands or "set_config" in commands:
                    # 优先使用set_mode，如果没有则使用set_config
                    mode_cmd = commands.get("set_mode") or commands.get("set_config")

                    # 优先从命令配置中获取HVAC模式映射
                    mode_val = None
                    if "hvac_modes" in mode_cmd:
                        # 使用设备特定的HVAC模式映射
                        hvac_modes_mapping = mode_cmd["hvac_modes"]
                        mode_val = hvac_modes_mapping.get(hvac_mode)

                    # 如果没有设备特定映射，从设备类型推断使用相应的全局映射
                    if mode_val is None:
                        # 根据设备类型选择合适的HVAC映射
                        if device_type == "SL_CP_AIR":
                            from .config.device_specs import (
                                REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP,
                            )

                            mode_val = REVERSE_LIFESMART_CP_AIR_HVAC_MODE_MAP.get(
                                hvac_mode
                            )
                        elif device_type.startswith(("V_AIR_P", "SL_TR_ACIPM")):
                            from .config.device_specs import REVERSE_F_HVAC_MODE_MAP

                            mode_val = REVERSE_F_HVAC_MODE_MAP.get(hvac_mode)
                        else:
                            # 默认使用扩展HVAC映射
                            mode_val = REVERSE_LIFESMART_HVAC_MODE_MAP.get(hvac_mode)

                    # 最终回退到默认值
                    if mode_val is None:
                        mode_val = 1

                    return await self._async_send_single_command(
                        agt,
                        me,
                        io_port,
                        mode_cmd.get("type", CMD_TYPE_SET_CONFIG),
                        mode_val,
                    )

        _LOGGER.warning("设备类型 %s 不支持HVAC模式设置", device_type)
        return -1

    async def async_set_climate_temperature(
        self, agt: str, me: str, device: dict, temp: float
    ) -> int:
        """
        设置温控设备的目标温度 - 精确温度控制

        该方法实现了对温控设备目标温度的精确设置，支持0.1°C的温度精度。
        适用于空调、地暖、热水器等各类温控设备。

        🌡️ 温度处理机制 (Temperature Processing Mechanism)
        -------------------------------------------------------------------

        **温度精度转换**:
        - 输入: 摄氏度 (float)，如 23.5°C
        - 转换: 乘以10取整 (temp_val = int(temp * 10))
        - 协议值: 235 (表示23.5°C)
        - 精度: 0.1°C

        **温度范围限制**:
        不同设备类型有不同的温度范围：
        - 空调: 通常 16-30°C
        - 地暖: 通常 5-35°C
        - 热水器: 通常 30-70°C
        - 恒温器: 通常 10-40°C

        Args:
            agt (str): 智慧中心ID
            me (str): 温控设备ID
            device (dict): 设备信息，用于确定温度控制配置
            temp (float): 目标温度（摄氏度），支持一位小数精度

        Returns:
            int: 温度设置状态码
                - 0: 温度设置成功
                - -1: 设备不支持温度设置或参数无效

        Example:
            >>> # 设置空调温度为 24.5°C
            >>> result = await client.async_set_climate_temperature(
            ...     agt="12345678",
            ...     me="87654321",
            ...     device=device_info,
            ...     temp=24.5
            ... )
            >>> if result == 0:
            ...     print("温度已设置为 24.5°C")
        """
        temp_val = int(temp * 10)
        device_type = get_device_effective_type(device)

        # 获取设备映射配置
        device_mapping = mapping_engine.resolve_device_mapping_from_data(device)
        climate_config = device_mapping.get("climate", {})

        # 查找温度设置IO口
        for io_port, io_config in climate_config.items():
            if isinstance(io_config, dict):
                # description = io_config.get("description", "").lower()  # Unused
                commands = io_config.get("commands", {})

                # 优先使用commands配置
                if "set_temperature" in commands:
                    temp_cmd = commands["set_temperature"]
                    return await self._async_send_single_command(
                        agt,
                        me,
                        io_port,
                        temp_cmd.get("type", CMD_TYPE_SET_VAL),
                        temp_val,
                    )

        _LOGGER.warning("设备类型 %s 不支持温度设置", device_type)
        return -1

    async def async_set_climate_fan_mode(
        self, agt: str, me: str, device: dict, fan_mode: str, current_val: int = 0
    ) -> int:
        """
        设置温控设备的风扇模式 - 风扇控制优化

        该方法实现了对温控设备风扇模式的精确控制，包括风速等级和运行模式。
        支持自动风速、手动风速以及特殊风扇模式。

        🌪️ 风扇模式类型 (Fan Mode Types)
        -------------------------------------------------------------------

        **标准风速等级**:
        - auto: 自动风速，根据温差自动调节
        - low: 低风速，安静运行
        - medium: 中风速，平衡性能
        - high: 高风速，快速制冷/制热

        **扩展风扇模式**:
        - sleep: 睡眠风速，超静音运行
        - turbo: 超强风速，最大制冷/制热效果
        - eco: 节能风速，优化能耗
        - swing: 摆风模式，改善空气循环

        Args:
            agt (str): 智慧中心ID
            me (str): 温控设备ID
            device (dict): 设备信息，用于获取风扇控制配置
            fan_mode (str): 目标风扇模式
            current_val (int): 当前值参考，某些设备需要

        Returns:
            int: 风扇模式设置状态码
                - 0: 风扇模式设置成功
                - -1: 设备不支持该风扇模式或设置失败

        Example:
            >>> # 设置空调为自动风速
            >>> await client.async_set_climate_fan_mode(
            ...     agt="12345678", me="87654321",
            ...     device=device_info, fan_mode="auto"
            ... )
        """
        device_type = get_device_effective_type(device)

        # 获取设备映射配置
        device_mapping = mapping_engine.resolve_device_mapping_from_data(device)
        climate_config = device_mapping.get("climate", {})

        # 查找风扇模式控制IO口
        for io_port, io_config in climate_config.items():
            # 检查IO口是否在实际设备数据中存在
            if io_port not in device.get("data", {}):
                continue

            if isinstance(io_config, dict):
                # description = io_config.get("description", "").lower()  # Unused
                commands = io_config.get("commands", {})

                # 优先使用commands配置，回退到set_config
                if "set_fan_speed" in commands:
                    fan_cmd = commands["set_fan_speed"]
                    # 从 fan_modes 中获取值
                    fan_modes = fan_cmd.get("fan_modes", {})
                    fan_val = fan_modes.get(fan_mode)

                    if fan_val is None:
                        _LOGGER.warning(
                            "设备类型 %s 不支持风扇模式 %s", device_type, fan_mode
                        )
                        continue
                elif "set_config" in commands:
                    # 如果没有set_fan_speed，回退到set_config
                    fan_cmd = commands["set_config"]
                    # 从映射配置中获取风扇模式的值
                    fan_mappings = fan_cmd.get("fan_modes", {})
                    fan_val = fan_mappings.get(fan_mode)

                    if fan_val is None:
                        _LOGGER.warning(
                            "设备类型 %s 不支持风扇模式 %s", device_type, fan_mode
                        )
                        continue
                else:
                    continue

                return await self._async_send_single_command(
                    agt,
                    me,
                    io_port,
                    fan_cmd.get("type", CMD_TYPE_SET_CONFIG),
                    fan_val,
                )

        _LOGGER.warning("设备类型 %s 不支持风扇模式设置", device_type)
        return -1
