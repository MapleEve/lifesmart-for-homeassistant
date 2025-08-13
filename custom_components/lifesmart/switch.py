"""LifeSmart 开关平台支持模块。

本模块为 Home Assistant 提供 LifeSmart 智能开关设备的集成支持，
实现开关设备的状态监控和控制功能。支持多子设备开关控制，
包括墙面开关、智能插座、灯光开关等设备类型。

主要功能:
- 自动发现和配置 LifeSmart 开关设备
- 实时状态同步和WebSocket更新
- 多IO口开关的独立控制
- 设备分类和属性映射
- 错误处理和重连机制

作者: @MapleEve
"""

import logging
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core.const import (
    DOMAIN,
    MANUFACTURER,
    HUB_ID_KEY,
    DEVICE_ID_KEY,
    DEVICE_NAME_KEY,
    DEVICE_DATA_KEY,
    DEVICE_VERSION_KEY,
    SUBDEVICE_INDEX_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
)
from .core.entity import LifeSmartEntity
from .core.error_handling import (
    handle_device_control,
    handle_global_refresh,
    log_device_unavailable,
)
from .core.helpers import (
    generate_unique_id,
)
from .core.platform.platform_detection import (
    get_device_platform_mapping,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """从配置条目设置 LifeSmart 开关实体。

    此函数负责初始化和配置所有 LifeSmart 开关设备实体。
    通过平台映射系统自动识别设备支持的开关子设备，
    为每个开关IO口创建独立的实体对象。

    Args:
        hass: Home Assistant 核心实例
        config_entry: 配置条目，包含集成配置信息
        async_add_entities: 异步添加实体的回调函数

    处理流程:
    1. 获取hub实例和排除配置
    2. 遍历所有设备，跳过被排除的设备
    3. 使用平台映射系统获取开关子设备列表
    4. 为每个开关子设备创建 LifeSmartSwitch 实体
    5. 批量添加所有开关实体到 Home Assistant
    """
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    switches = []
    for device in hub.get_devices():
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        # 使用新的IO映射系统获取设备支持的平台
        platform_mapping = get_device_platform_mapping(device)
        switch_subdevices = platform_mapping.get("switch", [])

        # 为每个switch子设备创建实体
        for sub_key in switch_subdevices:
            # 获取子设备数据
            sub_device_data = device.get(DEVICE_DATA_KEY, {}).get(sub_key, {})
            switches.append(
                LifeSmartSwitch(
                    device,
                    sub_key,
                    hub.get_client(),
                    config_entry.entry_id,
                    sub_device_data,
                )
            )

    async_add_entities(switches)


class LifeSmartSwitch(LifeSmartEntity, SwitchEntity):
    """LifeSmart 开关实体类，提供完整的状态管理功能。

    此类继承自 LifeSmartEntity 和 SwitchEntity，实现了 LifeSmart
    开关设备的完整功能支持，包括状态解析、设备控制、实时更新等。

    核心特性:
    - 支持多IO口开关的独立控制
    - 基于映射引擎的智能状态解析
    - WebSocket实时状态更新
    - 设备类别自动识别
    - 完整的错误处理和恢复机制
    - 支持开关、插座、灯光等多种设备类型

    属性:
        _sub_key: 子设备标识符（如 'P1', 'P2'等）
        _entry_id: 配置条目ID
        _sub_data: 子设备数据字典
        _attr_is_on: 当前开关状态
    """

    _attr_has_entity_name = False

    def __init__(
        self,
        raw_device: dict[str, Any],
        sub_device_key: str,
        client: Any,
        entry_id: str,
        sub_device_data: dict[str, Any],
    ) -> None:
        """初始化 LifeSmart 开关实体。

        设置开关实体的基本属性和配置，包括唯一标识符、
        显示名称、设备类别等核心属性。

        Args:
            raw_device: 原始设备数据字典
            sub_device_key: 子设备键名（如 'P1', 'P2'等）
            client: LifeSmart 客户端实例
            entry_id: 配置条目标识符
            sub_device_data: 子设备的详细数据

        初始化步骤:
        1. 调用父类初始化方法
        2. 存储子设备相关参数
        3. 生成唯一标识符和显示名称
        4. 确定设备类别和初始状态
        5. 设置额外状态属性
        """
        super().__init__(raw_device, client)
        self._sub_key = sub_device_key
        self._entry_id = entry_id
        self._sub_data = sub_device_data

        self._attr_unique_id = generate_unique_id(
            self.devtype, self.agt, self.me, sub_device_key
        )
        self._attr_name = self._generate_switch_name()
        self._attr_device_class = self._determine_device_class()
        self._attr_extra_state_attributes = {
            HUB_ID_KEY: self.agt,
            DEVICE_ID_KEY: self.me,
            SUBDEVICE_INDEX_KEY: self._sub_key,
        }
        self._attr_is_on = self._parse_state(self._sub_data)

    @callback
    def _generate_switch_name(self) -> str:
        """生成用户友好的开关名称。

        根据设备基础名称和子设备配置生成易于理解的显示名称。
        优先使用配置中的自定义名称，否则使用标准化的子设备键名。

        Returns:
            str: 格式化的开关显示名称

        名称生成规则:
        - 如果子设备有自定义名称且不同于键名，使用 "基础名称 自定义名称"
        - 否则使用 "基础名称 键名（大写）" 格式
        - 确保名称在UI中清晰易懂
        """
        base_name = self._name
        sub_name = self._sub_data.get(DEVICE_NAME_KEY)
        if sub_name and sub_name != self._sub_key:
            return f"{base_name} {sub_name}"
        return f"{base_name} {self._sub_key.upper()}"

    @callback
    def _determine_device_class(self) -> SwitchDeviceClass:
        """使用映射引擎获取设备类别。"""
        from .core.config.mapping_engine import mapping_engine

        device_config = mapping_engine.resolve_device_mapping_from_data(
            self._raw_device
        )
        if not device_config:
            _LOGGER.error("映射引擎无法解析设备配置: %s", self._raw_device)
            raise HomeAssistantError(
                f"Device configuration not found for "
                f"{self._raw_device.get('me', 'unknown')}"
            )

        switch_config = device_config.get("switch", {})
        io_config = switch_config.get(self._sub_key, {})

        # 从配置中获取设备类别
        device_class = io_config.get("device_class")
        if device_class:
            return device_class

        # 默认为开关
        return SwitchDeviceClass.SWITCH

    @callback
    def _parse_state(self, data: dict) -> bool:
        """使用新的逻辑处理器系统解析开关状态。

        通过映射引擎和逻辑处理器系统智能解析设备的开关状态。
        支持多种数据格式和处理器类型，确保准确的状态识别。

        Args:
            data: 需要解析的设备数据字典

        Returns:
            bool: 解析后的开关状态（True为开，False为关）

        处理流程:
        1. 获取设备的映射配置
        2. 查找对应子设备的IO配置
        3. 确定适合的处理器类型
        4. 使用逻辑处理器解析状态数据
        5. 返回标准化的布尔状态值

        支持的处理器类型:
        - type_bit_0_switch: 基于bit 0位的开关状态
        - 其他根据设备特性配置的处理器
        """
        from .core.data.processors.logic_processors import process_io_data
        from .core.config.mapping_engine import mapping_engine

        # 使用映射引擎获取IO配置
        device_config = mapping_engine.resolve_device_mapping_from_data(
            self._raw_device
        )

        if not device_config:
            _LOGGER.error("映射引擎无法解析设备配置: %s", self._raw_device)
            raise HomeAssistantError(
                f"Device configuration not found for "
                f"{self._raw_device.get('me', 'unknown')}"
            )

        switch_config = device_config.get("switch", {})
        io_config = switch_config.get(self._sub_key, {})

        if not io_config:
            # 如果没有IO配置，使用默认的 type_bit_0_switch 处理器
            switch_processor_config = {"processor_type": "type_bit_0_switch"}
            return process_io_data(switch_processor_config, data)

        # 使用新的逻辑处理器系统和配置的处理器
        processor_type = io_config.get("processor_type", "type_bit_0_switch")
        processor_config = {"processor_type": processor_type}
        return process_io_data(processor_config, data)

    @property
    def device_info(self) -> DeviceInfo:
        """返回设备信息以将实体链接到对应的物理设备。

        生成标准的Home Assistant设备信息字典，用于在设备注册表中
        创建或更新设备条目，并建立实体与设备的关联关系。

        Returns:
            DeviceInfo: 包含设备标识、名称、制造商等信息的设备信息对象

        设备信息包含:
        - identifiers: 设备唯一标识符（域名、网关ID、设备ID）
        - name: 设备显示名称
        - manufacturer: 制造商名称（LifeSmart）
        - model: 设备型号
        - sw_version: 软件版本信息
        - via_device: 通过网关设备连接的标识
        """
        return DeviceInfo(
            identifiers={(DOMAIN, self.agt, self.me)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=self.devtype,
            sw_version=self._raw_device.get(DEVICE_VERSION_KEY, "unknown"),
            via_device=(DOMAIN, self.agt),
        )

    async def async_added_to_hass(self) -> None:
        """实体添加到Home Assistant时注册回调函数。

        设置实体的更新监听器，包括针对特定实体的更新信号
        和全局刷新信号，确保实体能够响应实时数据变化。

        注册的回调包括:
        1. 特定实体更新信号 - 处理该实体的实时WebSocket数据更新
        2. 全局刷新信号 - 处理整体数据同步和状态恢复

        回调函数会在实体被移除时自动清理，避免内存泄漏。
        """
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{self._attr_unique_id}",
                self._handle_update,
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                LIFESMART_SIGNAL_UPDATE_ENTITY,
                self._handle_global_refresh,
            )
        )

    @callback
    def _handle_update(self, new_data: dict) -> None:
        """处理来自WebSocket的实时更新数据。

        当设备状态通过WebSocket推送更新时调用此方法，
        解析新的状态数据并更新实体状态。

        Args:
            new_data: WebSocket推送的新设备状态数据

        处理步骤:
        1. 验证数据有效性
        2. 使用状态解析器处理新数据
        3. 更新实体的开关状态属性
        4. 触发Home Assistant状态更新

        此方法确保用户界面能够实时反映设备的最新状态。
        """
        if new_data:
            self._attr_is_on = self._parse_state(new_data)
            self.async_write_ha_state()

    @handle_global_refresh()
    async def _handle_global_refresh(self) -> None:
        """处理全局数据刷新以同步状态。

        当执行全局设备数据刷新时调用，用于同步本地缓存
        的设备状态与远程服务器的实际状态。

        处理流程:
        1. 从全局设备列表中查找当前设备
        2. 获取设备的最新子设备数据
        3. 解析并更新开关状态
        4. 如果设备不可用则记录日志

        此方法使用 @handle_global_refresh 装饰器，
        提供统一的错误处理和日志记录。

        应用场景:
        - 网络重连后的状态同步
        - 定期状态校验
        - 设备离线恢复后的状态更新
        """
        devices = self.hass.data[DOMAIN][self._entry_id]["devices"]
        current_device = next((d for d in devices if d[DEVICE_ID_KEY] == self.me), None)
        if current_device:
            self._raw_device = current_device
            sub_data = current_device.get(DEVICE_DATA_KEY, {}).get(self._sub_key)
            if sub_data:
                self._attr_is_on = self._parse_state(sub_data)
                self.async_write_ha_state()
        else:
            log_device_unavailable(self._attr_unique_id, "global refresh")

    @handle_device_control()
    async def async_turn_on(self, **kwargs: Any) -> None:
        """打开开关设备。

        向LifeSmart服务发送开关打开命令，并在成功时更新本地状态。
        使用 @handle_device_control 装饰器提供统一的错误处理。

        Args:
            **kwargs: 额外的控制参数（当前未使用）

        控制流程:
        1. 调用客户端的开关打开接口
        2. 检查操作结果（0表示成功）
        3. 成功时更新本地状态为True
        4. 触发Home Assistant状态更新

        错误处理由装饰器统一管理，包括网络异常、
        设备离线等各种异常情况的处理和重试。
        """
        result = await self._client.turn_on_light_switch_async(
            self._sub_key, self.agt, self.me
        )
        if result == 0:
            self._attr_is_on = True
            self.async_write_ha_state()

    @handle_device_control()
    async def async_turn_off(self, **kwargs: Any) -> None:
        """关闭开关设备。

        向LifeSmart服务发送开关关闭命令，并在成功时更新本地状态。
        使用 @handle_device_control 装饰器提供统一的错误处理。

        Args:
            **kwargs: 额外的控制参数（当前未使用）

        控制流程:
        1. 调用客户端的开关关闭接口
        2. 检查操作结果（0表示成功）
        3. 成功时更新本地状态为False
        4. 触发Home Assistant状态更新

        错误处理由装饰器统一管理，包括网络异常、
        设备离线等各种异常情况的处理和重试。
        """
        result = await self._client.turn_off_light_switch_async(
            self._sub_key, self.agt, self.me
        )
        if result == 0:
            self._attr_is_on = False
            self.async_write_ha_state()
