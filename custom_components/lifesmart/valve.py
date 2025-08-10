"""
LifeSmart 阀门平台支持模块

由 @MapleEve 创建和维护

本模块为LifeSmart平台提供阀门设备(Valve)支持，实现了对各种智能阀门的
全面控制和状态监测。

支持的阀门功能：
- 阀门开启/关闭控制
- 位置设置(0-100%)
- 实时状态监测
- 优化的状态更新机制

阀门设备类型：
- 水阀门：水流控制、灭火系统
- 气体阀门：燃气、氧气等气体控制
- 物理阀门：通风、温控系统

技术特性：
- 配置驱动的IO口检测
- 统一的状态更新机制
- 实时数据与全局刷新双重监听
- 优雅的异常处理和日志记录
"""

import logging
from typing import Any

from homeassistant.components.valve import ValveEntity, ValveEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core.const import (
    # 核心常量
    DOMAIN,
    MANUFACTURER,
    HUB_ID_KEY,
    DEVICE_ID_KEY,
    DEVICE_TYPE_KEY,
    DEVICE_NAME_KEY,
    DEVICE_DATA_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    # 阀门平台相关
    # 命令常量
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_SET_VAL,
)
from .core.data.processors import process_io_data
from .core.entity import LifeSmartEntity
from .core.helpers import generate_unique_id
from .core.platform.platform_detection import get_valve_subdevices
from .core.platform.platform_detection import safe_get

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    从配置条目异步设置 LifeSmart 阀门设备。

    此函数是阀门平台的入口点，负责扫描所有设备并创建阀门实体。

    Args:
        hass: Home Assistant 核心实例
        config_entry: 集成的配置条目，包含认证信息等
        async_add_entities: 用于向 HA 添加实体的回调函数

    Returns:
        None

    处理流程:
        1. 获取 hub 实例和排除配置
        2. 遍历所有设备，检查是否被排除
        3. 使用平台检测函数识别阀门子设备
        4. 为每个阀门子设备创建对应实体
        5. 批量添加到 Home Assistant
    """
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    valves = []
    for device in hub.get_devices():
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device.get(DEVICE_TYPE_KEY)
        if not device_type:
            continue

        # 使用平台检测函数获取valve子设备
        valve_subdevices = get_valve_subdevices(device)

        # 为每个支持的valve子设备创建实体
        for sub_key in valve_subdevices:
            sub_device_data = safe_get(device, DEVICE_DATA_KEY, sub_key, default={})
            if sub_device_data:  # 只有当存在实际数据时才创建实体
                valve = LifeSmartValve(
                    raw_device=device,
                    client=hub.get_client(),
                    entry_id=config_entry.entry_id,
                    sub_device_key=sub_key,
                    sub_device_data=sub_device_data,
                )
                valves.append(valve)
                _LOGGER.debug(
                    "Added valve %s for device %s",
                    sub_key,
                    device.get(DEVICE_NAME_KEY),
                )

    if valves:
        async_add_entities(valves)
        _LOGGER.info("Added %d LifeSmart valves", len(valves))


class LifeSmartValve(LifeSmartEntity, ValveEntity):
    """
    LifeSmart 阀门设备实现类。

    这个类实现了 Home Assistant 的 ValveEntity 接口，提供完整的阀门控制功能。
    支持的操作包括开启、关闭、位置设置以及实时状态监控。

    主要特性:
        - 支持 0-100% 的位置控制
        - 实时状态更新和全局刷新
        - 优雅的错误处理和日志记录
        - 配置驱动的 IO 口检测
        - 自动生成友好的设备名称

    属性:
        _sub_key: 子设备的 IO 口标识符
        _sub_data: 子设备的数据字典
        _entry_id: 配置条目 ID
        _attr_name: 显示名称
        _attr_unique_id: 唯一标识符
        _attr_supported_features: 支持的功能特性
        _attr_is_closed: 阀门是否关闭
        _attr_current_valve_position: 当前阀门位置 (0-100%)
    """

    def __init__(
        self,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
        sub_device_key: str,
        sub_device_data: dict[str, Any],
    ) -> None:
        """
        初始化阀门实体。

        Args:
            raw_device: 原始设备数据字典
            client: LifeSmart API 客户端实例
            entry_id: 配置条目的唯一标识符
            sub_device_key: 子设备(IO口)的键名，如 'P1', 'V1' 等
            sub_device_data: 子设备的具体数据

        初始化过程:
            1. 调用父类构造函数
            2. 设置实例变量
            3. 生成友好的设备名称
            4. 创建唯一 ID
            5. 配置支持的特性
            6. 提取初始状态和位置
        """
        super().__init__(raw_device, client)
        self._sub_key = sub_device_key
        self._sub_data = sub_device_data
        self._entry_id = entry_id

        # 生成阀门名称和ID
        self._attr_name = self._generate_valve_name()
        self._attr_unique_id = generate_unique_id(
            self.devtype,
            self.agt,
            self.me,
            sub_device_key,
        )

        # 阀门特性支持
        self._attr_supported_features = (
            ValveEntityFeature.OPEN
            | ValveEntityFeature.CLOSE
            | ValveEntityFeature.SET_POSITION
        )

        # 从子设备数据获取初始状态
        self._attr_is_closed = self._extract_initial_state()
        self._attr_current_valve_position = self._extract_position()

    @callback
    def _generate_valve_name(self) -> str | None:
        """
        生成用户友好的阀门名称。

        名称生成逻辑:
            1. 如果子设备有自定义名称且不等于 IO 口键名，使用自定义名称
            2. 否则使用 "基础设备名 + Valve + IO口键名" 的格式

        Returns:
            生成的阀门显示名称字符串

        Example:
            - "客厅控制器 主阀门" (有自定义名称)
            - "厨房控制器 Valve P1" (使用默认格式)
        """
        base_name = self._name
        # 如果子设备有自己的名字，则使用它
        sub_name = self._sub_data.get(DEVICE_NAME_KEY)
        if sub_name and sub_name != self._sub_key:
            return f"{base_name} {sub_name}"
        # 否则，使用基础名 + IO口索引
        return f"{base_name} Valve {self._sub_key.upper()}"

    @callback
    def _extract_initial_state(self) -> bool:
        """
        从设备数据中提取阀门的初始状态。

        状态提取逻辑:
            - 检查 type 字段的最低位 (type & 1)
            - 0 = 关闭状态，1 = 开启状态
            - 返回 is_closed 状态 (与 is_open 相反)

        Returns:
            True: 阀门关闭
            False: 阀门开启

        Note:
            这是 LifeSmart 协议的标准状态解析方式，
            适用于所有支持开关状态的 IO 设备。
        """
        # 检查type字段的最低位确定开关状态，0=关闭，1=打开
        valve_type = self._sub_data.get("type", 0)
        is_open = bool(valve_type & 1)
        return not is_open  # is_closed 与 is_open 相反

    @callback
    def _extract_position(self) -> int | None:
        """
        从设备数据中提取阀门位置信息。

        位置提取优先级:
            1. 使用配置的位置处理器 (如果可用)
            2. 从 val 字段直接读取百分比值
            3. 根据开关状态推断 (关闭=0%, 开启=100%)

        Returns:
            int: 阀门位置百分比 (0-100)
            None: 无法确定位置

        位置范围限制:
            所有返回值都会被限制在 0-100 范围内，
            确保符合 Home Assistant 的阀门位置规范。
        """
        # 尝试使用数据处理器获取位置值
        position_config = self._get_io_config("position")
        if position_config:
            position_value = process_io_data(
                self.devtype, self._sub_key, position_config, self._sub_data
            )
            if position_value is not None:
                # 确保位置在0-100范围内
                return max(0, min(100, int(position_value)))

        # 如果没有配置，从val字段获取位置
        position = self._sub_data.get("val")
        if position is not None:
            try:
                # 假设val字段表示百分比位置
                position = max(0, min(100, int(position)))
                return position
            except (ValueError, TypeError):
                pass

        # 根据开关状态推断位置
        if hasattr(self, "_attr_is_closed"):
            return 0 if self._attr_is_closed else 100

        return None

    def _get_io_config(self, metric: str) -> dict | None:
        """
        从 DEVICE_MAPPING 中获取阀门指标的配置信息。

        这个方法用于获取特定阀门指标（如位置、流量等）的处理配置，
        支持配置驱动的数据处理架构。

        Args:
            metric: 要查找的指标类型，如 'position', 'flow_rate' 等

        Returns:
            dict: 包含处理器配置的字典
            None: 未找到对应的配置

        配置结构示例:
        {
            "processor_type": "direct_value",
            "metric": "position",
            "scale_factor": 1.0,
            "unit": "%"
        }
        """
        from .core.config.mapping import DEVICE_MAPPING

        device_type = self._raw_device.get(DEVICE_TYPE_KEY)
        if not device_type or device_type not in DEVICE_MAPPING:
            return None

        mapping = DEVICE_MAPPING[device_type]
        valve_config = mapping.get("valve", {})

        # 查找特定指标的配置
        for io_key, io_config in valve_config.items():
            if isinstance(io_config, dict) and io_config.get("metric") == metric:
                return io_config

        return None

    @property
    def is_closed(self) -> bool:
        """
        返回阀门是否处于关闭状态。

        Returns:
            True: 阀门完全关闭
            False: 阀门开启或部分开启

        Note:
            这是 Home Assistant ValveEntity 的必需属性，
            用于确定阀门的基本状态显示。
        """
        return self._attr_is_closed

    @property
    def current_valve_position(self) -> int | None:
        """
        返回阀门的当前位置百分比。

        Returns:
            int: 阀门位置 (0-100%)
            None: 位置未知或不支持位置反馈

        位置含义:
            - 0%: 完全关闭
            - 100%: 完全开启
            - 50%: 半开状态
        """
        return self._attr_current_valve_position

    async def async_open_valve(self, **kwargs) -> None:
        """
        异步开启阀门到完全开启状态。

        这个方法会发送开启命令到设备，并立即更新本地状态以提供
        即时的用户界面反馈。如果命令发送失败，会记录错误日志。

        Args:
            **kwargs: 额外的关键字参数（当前未使用）

        执行步骤:
            1. 发送 CMD_TYPE_ON 命令到设备
            2. 更新本地状态：is_closed = False, position = 100%
            3. 通知 Home Assistant 更新界面
            4. 记录操作日志

        异常处理:
            如果命令发送失败，会捕获异常并记录详细的错误信息，
            但不会抛出异常以避免影响 Home Assistant 的稳定性。
        """
        try:
            await self._client.async_send_single_command(
                self.agt,
                self.me,
                self._sub_key,
                CMD_TYPE_ON,
                1,
            )

            self._attr_is_closed = False
            self._attr_current_valve_position = 100
            self.async_write_ha_state()

            _LOGGER.debug(
                "Opened valve %s on device %s",
                self._sub_key,
                self._name,
            )

        except Exception as err:
            _LOGGER.error(
                "Failed to open valve %s on device %s: %s",
                self._sub_key,
                self._name,
                err,
            )

    async def async_close_valve(self, **kwargs) -> None:
        """
        异步关闭阀门到完全关闭状态。

        这个方法会发送关闭命令到设备，并立即更新本地状态。
        关闭操作通常用于安全目的，如紧急切断供水或燃气。

        Args:
            **kwargs: 额外的关键字参数（当前未使用）

        执行步骤:
            1. 发送 CMD_TYPE_OFF 命令到设备
            2. 更新本地状态：is_closed = True, position = 0%
            3. 通知 Home Assistant 更新界面
            4. 记录操作日志

        安全考虑:
            关闭操作具有最高优先级，即使设备响应较慢，
            本地状态也会立即更新以确保用户界面的准确性。
        """
        try:
            await self._client.async_send_single_command(
                self.agt,
                self.me,
                self._sub_key,
                CMD_TYPE_OFF,
                0,
            )

            self._attr_is_closed = True
            self._attr_current_valve_position = 0
            self.async_write_ha_state()

            _LOGGER.debug(
                "Closed valve %s on device %s",
                self._sub_key,
                self._name,
            )

        except Exception as err:
            _LOGGER.error(
                "Failed to close valve %s on device %s: %s",
                self._sub_key,
                self._name,
                err,
            )

    async def async_set_valve_position(self, position: int, **kwargs) -> None:
        """
        异步设置阀门到指定位置。

        这个方法允许精确控制阀门的开度，适用于需要流量控制
        的应用场景，如暖通系统的流量调节。

        Args:
            position: 目标位置百分比 (0-100)
                - 0: 完全关闭
                - 100: 完全开启
                - 其他值: 对应的开度百分比
            **kwargs: 额外的关键字参数（当前未使用）

        执行步骤:
            1. 验证并限制位置值到 0-100 范围
            2. 发送 CMD_TYPE_SET_VAL 命令到设备
            3. 更新本地状态和关闭标志
            4. 通知 Home Assistant 更新界面
            5. 记录操作日志

        位置映射:
            position == 0 时，is_closed 会被设置为 True
            position > 0 时，is_closed 会被设置为 False
        """
        try:
            # 确保位置在有效范围内
            position = max(0, min(100, position))

            await self._client.async_send_single_command(
                self.agt,
                self.me,
                self._sub_key,
                CMD_TYPE_SET_VAL,
                position,
            )

            self._attr_current_valve_position = position
            self._attr_is_closed = position == 0
            self.async_write_ha_state()

            _LOGGER.debug(
                "Set valve position to %s%% for valve %s on device %s",
                position,
                self._sub_key,
                self._name,
            )

        except Exception as err:
            _LOGGER.error(
                "Failed to set valve position for valve %s on device %s: %s",
                self._sub_key,
                self._name,
                err,
            )

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """
        返回阀门的额外状态属性。

        这些属性会显示在 Home Assistant 的设备详情页面中，
        为用户和自动化系统提供额外的状态信息。

        Returns:
            dict: 包含以下键的属性字典:
                - position: 当前位置百分比
                - position_percentage: 位置百分比（兼容性）
                - valve_state: 文本状态描述 ("open" 或 "closed")
                - 其他从父类继承的属性

        属性用途:
            - 用于模板和自动化中的条件判断
            - 在 Lovelace UI 中显示详细信息
            - 供第三方集成和脚本使用
        """
        # Get base attributes from parent class
        base_attrs = super().extra_state_attributes or {}

        # Add valve-specific attributes
        valve_attrs = {}

        if self._attr_current_valve_position is not None:
            valve_attrs["position"] = self._attr_current_valve_position
            valve_attrs["position_percentage"] = self._attr_current_valve_position

        valve_attrs["valve_state"] = "closed" if self._attr_is_closed else "open"

        # Merge attributes
        return {**base_attrs, **valve_attrs}

    @property
    def device_info(self) -> DeviceInfo:
        """
        返回设备信息，用于在 Home Assistant UI 中将实体链接到物理设备。

        Returns:
            DeviceInfo: 包含设备标识、名称、制造商等信息的对象

        设备信息包含:
            - identifiers: 唯一设备标识符组合 (DOMAIN, hub_id, device_id)
            - name: 设备显示名称
            - manufacturer: 制造商 (LifeSmart)
            - model: 设备型号 (从 devtype 获取)
            - via_device: 通过哪个 hub 连接

        用途:
            - 在设备页面中分组显示相关实体
            - 提供设备级别的控制和信息
            - 支持设备自动发现和配置
        """
        return DeviceInfo(
            identifiers={(DOMAIN, self.agt, self.me)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=self.devtype,
            via_device=(DOMAIN, self.agt),
        )

    async def async_added_to_hass(self) -> None:
        """
        当实体被添加到 Home Assistant 时调用。

        这个方法设置必要的事件监听器，确保阀门实体能够
        接收和处理来自设备的状态更新。

        设置的监听器:
            1. 实体特定更新监听器 - 接收针对此阀门的状态变化
            2. 全局更新监听器 - 接收周期性的全设备列表刷新

        监听器管理:
            所有监听器都通过 async_on_remove 注册，确保在实体
            被移除时能够正确清理，避免内存泄漏。

        调用时机:
            - 集成初始化时
            - 设备重新发现时
            - 配置更新后的实体重建时
        """
        await super().async_added_to_hass()

        # 实体特定更新
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{self._attr_unique_id}",
                self._handle_update,
            )
        )

        # 全局更新
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                LIFESMART_SIGNAL_UPDATE_ENTITY,
                self._handle_global_refresh,
            )
        )

    async def _handle_update(self, new_data: dict) -> None:
        """
        处理来自设备的实时状态更新。

        这个方法处理通过 WebSocket 或其他实时通道接收到的
        设备状态变化，确保 Home Assistant 界面能够及时反映设备的真实状态。

        Args:
            new_data: 包含更新数据的字典，可能包含以下结构:
                - 直接 IO 数据：{'type': 1, 'val': 50}
                - 嵌套消息：{'msg': {'P1': {'type': 1, 'val': 50}}}
                - 子设备数据：{'P1': {'type': 1, 'val': 50}}

        处理步骤:
            1. 解析数据结构，提取相关的 IO 口数据
            2. 更新阀门开关状态 (基于 type 字段)
            3. 更新阀门位置 (基于 val 字段)
            4. 根据位置自动更新关闭状态
            5. 如有变化，通知 Home Assistant 更新界面

        错误处理:
            捕获并记录所有异常，确保单个更新失败不会影响整个系统。
        """
        try:
            if not new_data:
                return

            # 提取IO数据
            io_data = {}
            if "msg" in new_data and isinstance(new_data["msg"], dict):
                io_data = new_data["msg"].get(self._sub_key, {})
            elif self._sub_key in new_data:
                io_data = new_data[self._sub_key]
            else:
                io_data = new_data

            if not io_data:
                return

            state_changed = False

            # 更新阀门状态
            if "type" in io_data:
                is_open = bool(io_data["type"] & 1)
                new_is_closed = not is_open
                if self._attr_is_closed != new_is_closed:
                    self._attr_is_closed = new_is_closed
                    state_changed = True

            # 更新位置
            if "val" in io_data:
                try:
                    new_position = max(0, min(100, int(io_data["val"])))
                    if self._attr_current_valve_position != new_position:
                        self._attr_current_valve_position = new_position
                        # 根据位置更新关闭状态
                        self._attr_is_closed = new_position == 0
                        state_changed = True
                except (ValueError, TypeError):
                    pass

            if state_changed:
                self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(
                "Error handling valve update for %s: %s", self._attr_unique_id, e
            )

    async def _handle_global_refresh(self) -> None:
        """
        处理周期性的全局设备列表刷新。

        这个方法处理来自 LifeSmart API 的完整设备状态更新，
        通常由定时轮询触发，用于确保长期状态一致性。

        处理步骤:
            1. 从全局设备列表中查找当前设备
            2. 检查设备和子设备是否仍然存在
            3. 更新可用性状态 (available 属性)
            4. 重新提取状态和位置信息
            5. 比较变化并更新界面

        可用性管理:
            - 如果设备或子设备不存在，标记为不可用
            - 如果之前不可用但现在找到了，恢复可用状态
            - 可用性变化会立即反映在 Home Assistant 界面中

        数据同步:
            这个方法确保即使实时更新丢失，设备状态也能通过
            周期性刷新保持同步。

        异常处理:
            捕获所有异常并记录，确保全局刷新失败不会导致
            实体崩溃或系统不稳定。
        """
        try:
            devices = self.hass.data[DOMAIN][self._entry_id]["devices"]
            current_device = next(
                (
                    d
                    for d in devices
                    if d[HUB_ID_KEY] == self.agt and d[DEVICE_ID_KEY] == self.me
                ),
                None,
            )

            if current_device is None:
                if self.available:
                    _LOGGER.warning(
                        "Valve device %s not found during global refresh, "
                        "marking as unavailable.",
                        self.unique_id,
                    )
                    self._attr_available = False
                    self.async_write_ha_state()
                return

            new_sub_data = safe_get(current_device, DEVICE_DATA_KEY, self._sub_key)
            if new_sub_data is None:
                if self.available:
                    _LOGGER.warning(
                        "Valve sub-device %s for %s not found, marking as unavailable.",
                        self._sub_key,
                        self.unique_id,
                    )
                    self._attr_available = False
                    self.async_write_ha_state()
                return

            if not self.available:
                self._attr_available = True

            # 保存旧值用于比较
            old_is_closed = self._attr_is_closed
            old_position = self._attr_current_valve_position

            # 更新数据并重新提取状态和位置
            self._sub_data = new_sub_data
            new_is_closed = self._extract_initial_state()
            new_position = self._extract_position()

            state_changed = False
            if old_is_closed != new_is_closed:
                self._attr_is_closed = new_is_closed
                state_changed = True

            if old_position != new_position:
                self._attr_current_valve_position = new_position
                state_changed = True

            if state_changed:
                self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(
                "Error during valve global refresh for %s: %s", self.unique_id, e
            )
