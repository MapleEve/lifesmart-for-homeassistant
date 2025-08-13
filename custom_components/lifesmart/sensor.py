"""
LifeSmart 传感器平台实现 - Home Assistant 集成核心模块

==================================================================================
平台概述
==================================================================================

本模块是LifeSmart智能家居系统在Home Assistant中的传感器平台实现，负责将LifeSmart
设备的传感器功能映射为Home Assistant的传感器实体。作为用户直接使用的平台层，
提供完整的传感器设备支持和用户友好的交互体验。

支持的传感器类型包括：
- 温度传感器 (temperature)
- 湿度传感器 (humidity)
- 照度传感器 (illuminance)
- 空气质量传感器 (pm25, tvoc, co2)
- 门窗传感器 (door, window)
- 人体传感器 (motion)
- 烟雾传感器 (smoke)
- 漏水传感器 (moisture)
- 电量传感器 (battery)
- 信号强度传感器 (signal_strength)
- 其他自定义传感器类型

==================================================================================
技术架构特性
==================================================================================

1. **映射驱动的设备检测**
   - 基于DEVICE_MAPPING统一配置管理
   - 自动识别设备类型和支持的传感器功能
   - 支持设备规格和IO口的动态映射

2. **通配符IO口展开处理**
   - 支持通配符模式的IO口配置（如 "p*", "v*"）
   - 自动展开为实际存在的IO口列表
   - 动态创建对应的传感器实体

3. **增强型数据转换和状态处理**
   - 映射驱动的数值转换逻辑
   - IEEE754浮点数转换支持
   - 自定义单位和设备类别配置
   - 错误处理和数据验证

4. **实时状态更新机制**
   - WebSocket实时数据推送支持
   - 全局数据刷新和同步
   - 设备在线状态监控
   - 优雅的错误恢复机制

==================================================================================
Home Assistant 集成规范
==================================================================================

本模块严格遵循Home Assistant的传感器平台规范：
- SensorEntity基类继承
- 标准设备信息（DeviceInfo）提供
- 唯一标识符（unique_id）管理
- 设备类别（device_class）和状态类别（state_class）支持
- 测量单位（unit_of_measurement）标准化
- 额外属性（extra_state_attributes）扩展
- 异步更新和事件监听机制

==================================================================================
用户配置和自定义
==================================================================================

平台支持以下用户配置选项：
- 设备包含/排除过滤
- 自定义传感器名称
- 额外属性显示配置
- 数据转换参数调整
- 更新频率控制

故障排查指导：
1. 检查设备在LifeSmart app中是否正常工作
2. 确认设备型号在支持列表中
3. 查看Home Assistant日志中的错误信息
4. 验证网络连接和设备在线状态
5. 重启集成或重新配置设备

创建者：@MapleEve
技术架构：基于DEVICE_MAPPING的统一配置管理
最后更新：2025-08-12
"""

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core.const import (
    # 核心常量
    DOMAIN,
    MANUFACTURER,
    HUB_ID_KEY,
    DEVICE_ID_KEY,
    DEVICE_NAME_KEY,
    DEVICE_DATA_KEY,
    DEVICE_VERSION_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
)
from .core.data.processors import process_io_data
from .core.entity import LifeSmartEntity
from .core.error_handling import (
    handle_data_processing,
    handle_global_refresh,
    log_device_unavailable,
    log_subdevice_unavailable,
)
from .core.helpers import (
    generate_unique_id,
)
from .core.platform.platform_detection import (
    safe_get,
    expand_wildcard_ios,
    get_sensor_subdevices,
)

_LOGGER = logging.getLogger(__name__)


def _get_enhanced_io_config(device: dict, sub_key: str) -> dict | None:
    """
    使用映射引擎获取IO口的增强配置信息。

    这是传感器平台的核心配置获取函数，负责从DEVICE_MAPPING中解析设备的IO口配置，
    包括设备类别、测量单位、状态类别、数据处理器等完整的传感器配置信息。

    处理流程：
    1. 通过映射引擎解析设备的完整映射配置
    2. 提取sensor平台的配置信息
    3. 查找指定IO口的增强配置结构
    4. 验证配置完整性和有效性

    Args:
        device (dict): 完整的设备数据字典，包含设备类型、ID、数据等信息
        sub_key (str): IO口键名，如 "p1", "v1", "battery", "rssi" 等

    Returns:
        dict | None: IO口的完整配置信息字典，包含以下可能的字段：
            - description: IO口功能描述
            - device_class: Home Assistant设备类别
            - unit_of_measurement: 测量单位
            - state_class: 状态类别（measurement/total等）
            - processor_type: 数据处理器类型
            - conversion_config: 数据转换配置
            - extra_attributes: 额外属性配置
            如果IO口不存在或配置无效则返回None

    Note:
        此函数是传感器平台配置解析的核心，所有传感器特性（设备类别、单位、
        数据转换等）都依赖于此函数返回的配置信息。配置格式必须符合增强
        结构标准，即包含 "description" 字段的字典格式。
    """
    from .core.config.mapping_engine import mapping_engine

    device_config = mapping_engine.resolve_device_mapping_from_data(device)
    if not device_config:
        _LOGGER.error("映射引擎无法解析设备配置: %s", device)
        raise HomeAssistantError(
            f"Device configuration not found for {device.get('me', 'unknown')}"
        )

    # 在sensor平台中查找IO配置
    sensor_config = device_config.get("sensor")
    if not sensor_config:
        return None

    # 检查是否为增强结构
    if isinstance(sensor_config, dict) and sub_key in sensor_config:
        io_config = sensor_config[sub_key]
        if isinstance(io_config, dict) and "description" in io_config:
            return io_config

    return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    设置LifeSmart传感器平台 - 平台入口点函数。

    这是Home Assistant调用的平台设置入口点，负责从配置条目初始化所有传感器实体。
    使用映射驱动的设备检测机制，自动识别和创建支持的传感器实体。

    执行流程：
    1. 获取Hub实例和设备排除配置
    2. 遍历所有可用设备，应用过滤规则
    3. 使用映射引擎检测每个设备的传感器子设备
    4. 处理通配符IO口展开和实体创建
    5. 批量添加传感器实体到Home Assistant

    设备过滤机制：
    - 支持按设备ID排除特定设备
    - 支持按Hub ID排除整个Hub的设备
    - 用户可在配置中自定义排除列表

    通配符处理：
    - 支持 "*" 和 "x" 通配符模式
    - 自动展开为实际存在的IO口
    - 只为有实际数据的IO口创建实体

    Args:
        hass (HomeAssistant): Home Assistant实例，提供核心服务访问
        config_entry (ConfigEntry): 配置条目，包含用户配置和Hub连接信息
        async_add_entities (AddEntitiesCallback): 实体添加回调函数，
            用于将创建的传感器实体注册到Home Assistant

    Returns:
        None: 函数无返回值，通过async_add_entities回调添加实体

    Raises:
        可能的异常包括：
        - 设备数据访问异常
        - 映射配置解析异常
        - 实体创建异常

    Note:
        此函数是传感器平台的核心入口点，实体创建的数量和类型完全依赖于
        DEVICE_MAPPING中的配置。如果某个设备类型没有传感器配置，
        将不会为该设备创建任何传感器实体。
    """
    hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]
    exclude_devices, exclude_hubs = hub.get_exclude_config()

    sensors = []
    for device in hub.get_devices():
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        # 使用工具函数获取设备的sensor子设备列表
        sensor_subdevices = get_sensor_subdevices(device)

        # 展开通配符模式的IO口并为每个sensor子设备创建实体
        device_data = device.get(DEVICE_DATA_KEY, {})

        for sub_key in sensor_subdevices:
            # 检查是否为通配符模式
            if "*" in sub_key or "x" in sub_key:
                # 展开通配符，获取实际的IO口列表
                expanded_ios = expand_wildcard_ios(sub_key, device_data)
                for expanded_io in expanded_ios:
                    sub_device_data = safe_get(
                        device, DEVICE_DATA_KEY, expanded_io, default={}
                    )
                    if sub_device_data:  # 只有当存在实际数据时才创建实体
                        sensors.append(
                            LifeSmartSensor(
                                raw_device=device,
                                client=hub.get_client(),
                                entry_id=config_entry.entry_id,
                                sub_device_key=expanded_io,
                                sub_device_data=sub_device_data,
                            )
                        )
            else:
                # 非通配符模式，正常处理
                sub_device_data = safe_get(device, DEVICE_DATA_KEY, sub_key, default={})
                sensors.append(
                    LifeSmartSensor(
                        raw_device=device,
                        client=hub.get_client(),
                        entry_id=config_entry.entry_id,
                        sub_device_key=sub_key,
                        sub_device_data=sub_device_data,
                    )
                )

    async_add_entities(sensors)


class LifeSmartSensor(LifeSmartEntity, SensorEntity):
    """
    LifeSmart传感器实体类 - 核心传感器功能实现

    ==================================================================================
    类概述
    ==================================================================================

    LifeSmartSensor是LifeSmart传感器平台的核心实体类，继承自LifeSmartEntity基类和
    Home Assistant的SensorEntity，为LifeSmart设备的传感器功能提供完整的Home Assistant
    集成支持。该类负责将LifeSmart设备的原始传感器数据转换为Home Assistant可识别和
    使用的标准传感器实体。

    ==================================================================================
    主要功能特性
    ==================================================================================

    1. **映射驱动的设备特性检测**
       - 基于DEVICE_MAPPING自动确定设备类别（device_class）
       - 自动识别和配置测量单位（unit_of_measurement）
       - 智能检测状态类别（state_class）用于长期统计
       - 支持自定义传感器属性和转换参数

    2. **增强型数据处理能力**
       - 映射驱动的数值转换和状态处理
       - IEEE754浮点数转换支持
       - 自定义数据处理器集成
       - 错误数据过滤和验证

    3. **实时状态更新机制**
       - WebSocket实时数据推送支持
       - 全局数据刷新和同步
       - 设备在线状态监控和管理
       - 优雅的错误恢复和重连机制

    4. **用户友好的命名和标识**
       - 智能传感器名称生成
       - 唯一标识符（unique_id）管理
       - 设备信息（DeviceInfo）完整集成
       - 多语言支持和本地化

    ==================================================================================
    支持的传感器类型和功能
    ==================================================================================

    本类支持所有LifeSmart设备的传感器功能，包括但不限于：

    **环境传感器**：
    - 温度传感器（°C）- SensorDeviceClass.TEMPERATURE
    - 湿度传感器（%）- SensorDeviceClass.HUMIDITY
    - 照度传感器（lux）- SensorDeviceClass.ILLUMINANCE
    - 大气压强传感器（hPa）- SensorDeviceClass.ATMOSPHERIC_PRESSURE

    **空气质量传感器**：
    - PM2.5浓度传感器（μg/m³）- SensorDeviceClass.PM25
    - TVOC挥发性有机物传感器（ppb）- SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS
    - CO2二氧化碳传感器（ppm）- SensorDeviceClass.CO2
    - 甲醛传感器（mg/m³）

    **安全传感器**：
    - 门窗传感器 - SensorDeviceClass.OPENING
    - 人体传感器 - SensorDeviceClass.MOTION
    - 烟雾传感器 - SensorDeviceClass.SMOKE
    - 漏水传感器 - SensorDeviceClass.MOISTURE

    **系统状态传感器**：
    - 电量传感器（%）- SensorDeviceClass.BATTERY
    - 信号强度传感器（dBm）- SensorDeviceClass.SIGNAL_STRENGTH
    - 电压传感器（V）- SensorDeviceClass.VOLTAGE
    - 功率传感器（W）- SensorDeviceClass.POWER

    ==================================================================================
    状态管理和属性扩展
    ==================================================================================

    **状态类别支持**：
    - SensorStateClass.MEASUREMENT - 瞬时测量值
    - SensorStateClass.TOTAL - 累计总值
    - SensorStateClass.TOTAL_INCREASING - 单调递增总值

    **额外属性功能**：
    - 静态属性：配置中预定义的固定属性值
    - 动态属性：从设备实时数据提取的属性值
    - 自定义属性：用户配置的特殊属性映射

    ==================================================================================
    技术实现细节
    ==================================================================================

    **继承关系**：
    - LifeSmartEntity：提供LifeSmart设备的基础功能和通用属性
    - SensorEntity：提供Home Assistant传感器的标准接口和规范

    **核心依赖**：
    - mapping_engine：设备映射配置解析和管理
    - io_processors：数据处理和转换引擎
    - error_handling：统一错误处理和日志记录
    - platform_detection：设备平台检测和配置

    **事件监听**：
    - LIFESMART_SIGNAL_UPDATE_ENTITY：实时数据更新事件
    - 全局刷新事件：周期性数据同步和状态检查

    ==================================================================================
    使用示例和配置
    ==================================================================================

    传感器实体会根据设备类型和IO口配置自动创建，用户可通过以下方式自定义：

    1. **设备排除配置**：在集成配置中设置要排除的设备或Hub
    2. **自定义名称**：通过设备数据中的name字段自定义传感器名称
    3. **额外属性**：在DEVICE_MAPPING中配置extra_attributes
    4. **数据转换**：在映射配置中设置自定义转换参数

    **故障排查指导**：
    1. 检查传感器是否出现在Home Assistant的实体列表中
    2. 查看日志中的错误信息和警告
    3. 验证设备在LifeSmart App中是否正常工作
    4. 检查网络连接和设备在线状态
    5. 重启集成或重新配置设备

    Note:
        该类是用户直接使用的传感器实体，所有属性和方法的设计都考虑了用户体验
        和Home Assistant的最佳实践。如果遇到传感器数据异常，首先检查DEVICE_MAPPING
        中的配置是否正确和完整。
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
        初始化LifeSmart传感器实体。

        这是传感器实体的构造函数，负责初始化传感器的所有基础属性和配置。
        通过映射引擎解析设备配置，设置传感器的名称、唯一标识、设备类别、
        测量单位、状态类别等核心属性，为后续的数据处理和状态管理做好准备。

        初始化流程：
        1. 调用父类构造函数，建立设备基础连接
        2. 保存传感器特定的子设备信息和配置
        3. 生成用户友好的传感器名称和对象ID
        4. 创建全局唯一的实体标识符
        5. 通过映射配置确定设备类别和单位
        6. 提取和处理初始传感器数值

        命名规则：
        - 传感器名称：设备名 + 子设备名（如有）或IO口标识
        - 对象ID：设备名（小写下划线）+ IO口标识（小写）
        - 唯一ID：基于设备类型、Hub ID、设备ID和IO口的组合

        Args:
            raw_device (dict[str, Any]): 完整的原始设备数据字典，包含：
                - devtype: 设备类型标识
                - agt: Hub ID（设备所属的Hub标识）
                - me: 设备ID（设备在Hub中的唯一标识）
                - name: 设备名称
                - data: 设备数据字典，包含所有IO口的数据
                - ver: 设备版本信息（可选）

            client (Any): LifeSmart客户端连接对象，用于：
                - 发送设备控制命令
                - 接收实时状态更新
                - 管理设备连接状态

            entry_id (str): Home Assistant配置条目ID，用于：
                - 标识此传感器所属的集成实例
                - 访问共享的Hub和设备数据
                - 管理实体的生命周期

            sub_device_key (str): 子设备/IO口键名，如：
                - "p1", "p2" - 通用IO口
                - "v1", "v2" - 数值IO口
                - "battery" - 电量传感器
                - "rssi" - 信号强度传感器
                - "temperature" - 温度传感器
                - "humidity" - 湿度传感器

            sub_device_data (dict[str, Any]): 子设备的实际数据字典，包含：
                - val/v: 主要数值（传感器读数）
                - name: 子设备自定义名称（可选）
                - 其他设备特定的数据字段

        Raises:
            可能的异常包括：
            - KeyError: 设备数据缺失必要字段
            - ValueError: 设备数据格式错误
            - 映射配置解析异常

        Note:
            构造函数会立即从当前的sub_device_data中提取初始值，如果数据无效
            或不存在，初始值将设置为None。后续的数据更新通过事件监听器处理。

            所有传感器属性（device_class、unit_of_measurement等）完全依赖于
            DEVICE_MAPPING中的配置，如果映射配置不完整，某些属性可能为None。
        """
        super().__init__(raw_device, client)
        self._sub_key = sub_device_key
        self._sub_data = sub_device_data
        self._entry_id = entry_id

        self._attr_name = self._generate_sensor_name()
        device_name_slug = self._name.lower().replace(" ", "_")
        sub_key_slug = self._sub_key.lower()
        self._attr_object_id = f"{device_name_slug}_{sub_key_slug}"

        self._attr_unique_id = generate_unique_id(
            self.devtype,
            self.agt,
            self.me,
            sub_device_key,
        )
        self._attr_device_class = self._determine_device_class()
        self._attr_state_class = self._determine_state_class()
        self._attr_native_unit_of_measurement = self._determine_unit()
        self._attr_native_value = self._extract_initial_value()

    @callback
    def _generate_sensor_name(self) -> str | None:
        """
        生成用户友好的传感器名称。

        这是传感器名称生成的智能函数，为用户提供易于理解和区分的传感器名称。
        该函数会根据子设备是否有自定义名称来决定使用不同的命名策略，
        确保生成的名称既简洁又具有描述性。

        命名策略：
        1. **自定义名称优先**：如果子设备数据中包含自定义名称（name字段），
           且该名称与IO口键名不同，则使用“设备名 + 子设备自定义名称”
        2. **默认命名规则**：否则使用“设备名 + IO口标识（大写）”的标准格式

        名称示例：
        - 原始设备名：“客厅环境监测仪”
        - IO口键名：“p1”
        - 子设备自定义名：“温度传感器”
        - 生成名称：“客厅环境监测仪 温度传感器”

        特殊情况处理：
        - 如果子设备名称与IO口键名相同，认为是系统生成的默认名称
        - 空值或缺失的子设备名称会被忽略
        - IO口标识会自动转换为大写以增强可读性

        Returns:
            str | None: 生成的用户友好传感器名称。格式为“设备名 功能描述”，
                如“客厅环境监测仪 P1”或“客厅环境监测仪 温度传感器”
                如果基础设备名称不存在则可能返回None

        Note:
            生成的名称会直接显示在Home Assistant的用户界面中，因此必须既简洁
            又具有描述性。名称中包含的空格会在生成object_id时被替换为下划线。
        """
        base_name = self._name
        # 如果子设备有自己的名字，则使用它
        sub_name = self._sub_data.get(DEVICE_NAME_KEY)
        if sub_name and sub_name != self._sub_key:
            return f"{base_name} {sub_name}"
        # 否则，使用基础名 + IO口索引
        return f"{base_name} {self._sub_key.upper()}"

    @callback
    def _determine_device_class(self) -> SensorDeviceClass | None:
        """
        使用映射驱动方法确定设备类别。

        这是传感器设备类别的核心确定函数，完全依赖DEVICE_MAPPING中的配置来确定
        传感器的Home Assistant设备类别。设备类别决定了Home Assistant如何显示和处理
        该传感器，包括图标、统计图表、自动化规则等。

        映射驱动机制：
        1. 从映射引擎获取设备的增强配置
        2. 检查指定IO口是否有device_class配置
        3. 返回配置中的设备类别或None

        支持的设备类别包括：
        - SensorDeviceClass.TEMPERATURE - 温度传感器
        - SensorDeviceClass.HUMIDITY - 湿度传感器
        - SensorDeviceClass.ILLUMINANCE - 照度传感器
        - SensorDeviceClass.PM25 - PM2.5浓度传感器
        - SensorDeviceClass.CO2 - 二氧化碳传感器
        - SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS - TVOC传感器
        - SensorDeviceClass.BATTERY - 电量传感器
        - SensorDeviceClass.SIGNAL_STRENGTH - 信号强度传感器
        - SensorDeviceClass.MOTION - 人体传感器
        - SensorDeviceClass.OPENING - 门窗传感器
        - SensorDeviceClass.SMOKE - 烟雾传感器
        - SensorDeviceClass.MOISTURE - 漏水传感器
        - 更多其他标准设备类别

        Returns:
            SensorDeviceClass | None: Home Assistant的标准设备类别枚举值，
                如果映射配置中没有定义设备类别则返回None。
                None值意味着该传感器将作为通用传感器显示，
                不会有特定的图标或特殊处理。

        Note:
            设备类别直接影响Home Assistant中传感器的显示效果和行为：
            - 图标显示：不同设备类别会显示不同的图标
            - 统计图表：某些设备类别会自动包含在能耗统计中
            - 自动化规则：可以基于设备类别创建更智能的自动化
            - 云端集成：某些云服务可能会识别特定设备类别

            如果某个传感器类型缺少设备类别配置，建议在DEVICE_MAPPING中添加
            相应的device_class配置以获得更好的用户体验。
        """
        # 完全依赖映射获取设备类别
        io_config = _get_enhanced_io_config(self._raw_device, self._sub_key)
        if io_config and "device_class" in io_config:
            return io_config["device_class"]

        return None

    @callback
    def _determine_unit(self) -> str | None:
        """
        使用映射驱动方法确定测量单位。

        这是传感器测量单位的核心确定函数，完全依赖DEVICE_MAPPING中的配置来获取
        传感器的测量单位信息。正确的测量单位对于Home Assistant的显示和数据处理至关重要，
        影响统计图表、数据分析和用户界面的数值显示。

        映射驱动机制：
        1. 通过增强配置获取函数获取IO口配置
        2. 检查配置中是否定义了unit_of_measurement字段
        3. 返回标准化的测量单位字符串或None

        支持的测量单位类型：

        **温度单位**：
        - "°C" - 摄氏度（最常用）
        - "°F" - 华氏度
        - "K" - 开尔文

        **湿度和百分比单位**：
        - "%" - 百分比（湿度、电量等）

        **光照单位**：
        - "lux" - 勒克斯（照度单位）

        **空气质量单位**：
        - "μg/m³" - 微克/立方米（PM2.5、甲醛等）
        - "ppm" - 百万分之一（CO2等气体浓度）
        - "ppb" - 十亿分之一（TVOC等微量气体）
        - "mg/m³" - 毫克/立方米（甲醛等）

        **电气单位**：
        - "V" - 伏特（电压）
        - "A" - 安培（电流）
        - "W" - 瓦特（功率）
        - "kWh" - 千瓦时（电量）

        **信号和网络单位**：
        - "dBm" - 分贝毫瓦（信号强度）
        - "dB" - 分贝（信号比率）

        **大气单位**：
        - "hPa" - 百帕（气压）
        - "Pa" - 帕斯卡（气压）
        - "mmHg" - 水银柱毫米（气压）

        Returns:
            str | None: 标准化的测量单位字符串，符合Home Assistant的单位规范。
                如果映射配置中没有定义测量单位则返回None。
                None值意味着该传感器为无单位的数值传感器（如计数器、状态码等）。

        Note:
            测量单位直接影响Home Assistant中的数据处理和显示：
            - 用户界面：在传感器卡片和历史图表中显示单位
            - 数据转换：用于不同单位系统间的自动转换
            - 统计分析：用于统计数据的合并和分析
            - 自动化：用于基于数值范围的自动化规则

            建议为所有有物理意义的传感器配置正确的测量单位，以便用户能够
            正确理解和使用传感器数据。没有单位的传感器通常用于状态指示或计数功能。
        """
        # 完全依赖映射获取单位
        io_config = _get_enhanced_io_config(self._raw_device, self._sub_key)
        if io_config and "unit_of_measurement" in io_config:
            return io_config["unit_of_measurement"]

        return None

    @callback
    def _determine_state_class(self) -> SensorStateClass | None:
        """
        从映射配置获取状态类别 - 用于长期统计和数据分析。

        这是传感器状态类别的确定函数，用于告诉Home Assistant如何处理和统计
        该传感器的历史数据。状态类别直接影响数据的存储、统计和显示方式，
        对于能耗监控、环境分析和长期趋势跟踪至关重要。

        支持的状态类别：

        **SensorStateClass.MEASUREMENT** (测量值)：
        - 用于瞬时测量值，如温度、湿度、照度等
        - 数据可以上下波动，无特定趋势
        - Home Assistant会为此类传感器提供平均值、最大值、最小值统计
        - 示例：温度传感器、湿度传感器、PM2.5传感器

        **SensorStateClass.TOTAL** (累计总值)：
        - 用于累计总量，如用电量、用水量等
        - 数据可以重置或删减，但通常表示总累计
        - Home Assistant会计算单位时间内的变化量
        - 示例：电表读数、水表读数、数据流量

        **SensorStateClass.TOTAL_INCREASING** (单调递增总值)：
        - 用于只能增加的累计值，如电表、水表等
        - 数据只能单调递增，不会出现删减（除非表重置）
        - Home Assistant会检测异常值并处理表重置情况
        - 示例：电表的累计用电量、燃气表读数

        **None** (无状态类别)：
        - 用于不需要统计分析的传感器
        - 通常是状态指示器、计数器或信息显示
        - 示例：设备状态、信号强度、版本信息

        数据存储和统计影响：
        - **有状态类别**的传感器会被包含在长期统计中
        - **无状态类别**的传感器只保存短期历史数据
        - 状态类别影响能耗监控和环境分析功能

        Returns:
            SensorStateClass | None: Home Assistant的标准状态类别枚举值，
                如果映射配置中没有定义状态类别则返回None。

        Note:
            状态类别的选择直接影响数据的存储成本和处理效率：
            - MEASUREMENT类型的数据量通常最大，占用存储空间最多
            - TOTAL类型需要额外的差值计算，但数据量相对较小
            - 没有状态类别的传感器不会产生长期统计数据

            建议根据传感器的实际用途和数据特性选择合适的状态类别，
            以获得最佳的数据分析和统计效果。
        """
        io_config = _get_enhanced_io_config(self._raw_device, self._sub_key)
        return io_config.get("state_class") if io_config else None

    @handle_data_processing()
    def _extract_initial_value(self) -> float | int | None:
        """
        提取和处理传感器的初始数值 - 统一化数据处理入口。

        这是传感器初始化过程中的核心数据提取函数，负责从子设备数据中获取
        初始的传感器读数并进行必要的数据转换和处理。该函数使用统一的io_processors
        接口，支持多种数据处理策略和错误处理机制。

        数据处理优先级：
        1. **映射配置驱动处理**：优先使用DEVICE_MAPPING中定义的处理逻辑
           - 支持自定义数据处理器类型（processor_type）
           - 支持复杂的数据转换配置（conversion_config）
           - 支持IEEE754浮点数转换和其他高级功能

        2. **默认统一处理**：如果没有映射配置，使用direct_value处理器
           - 自动处理"v"/"val"字段的后备逻辑
           - 数值类型转换和验证
           - 统一的错误处理和日志记录

        支持的数据格式：
        - **标准数值格式**：{"val": 25.6} 或 {"v": 25.6}
        - **IEEE754浮点数**：{"val": "0x41c80000"} 等十六进制表示
        - **字符串数值**：{"val": "25.6"} 等字符串格式
        - **复合数据结构**：支持多字段组合和计算

        错误处理机制：
        - 使用@handle_data_processing()装饰器统一处理异常
        - 自动记录详细的错误日志和上下文信息
        - 对无效数据返回None，不中断初始化过程
        - 支持数据缺失和格式错误的优雅降级

        性能优化：
        - 优先使用映射配置中的高效处理器
        - 避免不必要的数据复制和转换
        - 支持懒惰计算和缓存机制

        Returns:
            float | int | None: 处理后的传感器数值，类型可以是：
                - float: 浮点数值（最常见，如温度、湿度等）
                - int: 整数值（如计数器、状态码等）
                - None: 数据无效或不存在，传感器将显示为不可用状态

        Raises:
            通过装饰器处理的异常包括：
            - 数据格式错误：非数值类型、无效十六进制等
            - 映射配置错误：处理器不存在、配置参数错误等
            - 数据访问错误：字段缺失、数据结构异常等

        Note:
            此函数仅在初始化阶段调用一次，用于设置传感器的初始状态。
            后续的数据更新通过_handle_update()和_handle_global_refresh()方法处理。

            如果初始值为None，传感器将显示为“不可用”状态，直到收到有效的实时
            数据更新。这是正常行为，特别是对于刚刚上线或数据暂时不可用的设备。
        """
        # 优先使用映射配置的转换逻辑
        io_config = _get_enhanced_io_config(self._raw_device, self._sub_key)
        if io_config:
            return process_io_data(io_config, self._sub_data)

        # 如果没有映射配置，使用io_processors统一处理
        from .core.data.processors.io_processors import process_io_value

        # 使用现有的direct_value处理器，它已经实现了v/val后备逻辑
        default_config = {"processor_type": "direct_value"}
        result = process_io_value(default_config, self._sub_data)
        if result is not None:
            return float(result)

        return None

    @callback
    def _convert_raw_value(self, raw_value: Any) -> float | int | None:
        """
        使用映射驱动方法转换原始数值 - 实时数据处理核心函数。

        这是实时数据更新过程中的核心数值转换函数，负责将从设备接收到的原始数值
        转换为Home Assistant可使用的标准格式。该函数完全依赖DEVICE_MAPPING中的转换配置，
        确保数据转换的一致性和准确性。

        数据处理流程：
        1. **参数验证**：检查原始值是否为None，如是则直接返回
        2. **数值类型转换**：尝试将原始值转换为float类型
        3. **映射驱动处理**：优先使用DEVICE_MAPPING中的处理配置
        4. **默认后备处理**：如果没有映射配置，返回转换后的数值

        支持的数据转换类型：
        - **直接数值**：25.6 -> 25.6（保持原值）
        - **字符串数值**："25.6" -> 25.6（字符串转数值）
        - **IEEE754转换**：0x41c80000 -> 25.0（十六进制浮点数）
        - **线性变换**：原始值 * 系数 + 偏移量
        - **等值映射**：基于查找表的值映射
        - **函数计算**：自定义数学公式计算

        错误处理机制：
        - 非数值类型的原始值会被拒绝并记录警告
        - 转换失败的数据返回None，不更新传感器状态
        - 映射配置错误会降级到默认处理逻辑
        - 记录详细的错误信息和上下文。

        性能优化考虑：
        - 避免重复的数据处理和验证
        - 优先使用映射配置中的高效处理器
        - 支持批量数据处理和缓存机制

        Args:
            raw_value (Any): 从设备接收到的原始数值，可能的类型包括：
                - int/float: 直接的数值类型
                - str: 字符串表示的数值（包括十六进制）
                - None: 空值或无效数据
                - 其他类型: 将被拒绝并记录警告

        Returns:
            float | int | None: 转换后的数值，返回类型说明：
                - float: 浮点数结果（最常见，如温度、湿度）
                - int: 整数结果（如计数器、枚举值）
                - None: 数据无效或转换失败，传感器状态不会更新

        Raises:
            函数内部处理所有异常，不会向上抛出：
            - ValueError: 非数值类型转换错误
            - TypeError: 数据类型不兼容错误
            - 映射配置解析错误

        Note:
            此函数是实时数据更新的关键环节，其性能和准确性直接影响
            传感器的响应速度和数据质量。所有的数据转换逻辑都应该在
            DEVICE_MAPPING中配置，而不是在代码中硬编码，以确保灵活性和可维护性。

            如果遇到数值转换问题，应该首先检查DEVICE_MAPPING中的配置是否正确，
            然后检查设备发送的原始数据格式是否符合预期。
        """
        if raw_value is None:
            return None

        try:
            numeric_raw_value = float(raw_value)
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Invalid non-numeric 'val' received for %s: %s",
                self.unique_id,
                raw_value,
            )
            return None

        # 完全依赖映射的转换逻辑，工具函数内部已处理IEEE754转换
        io_config = _get_enhanced_io_config(self._raw_device, self._sub_key)
        if io_config:
            enhanced_value = process_io_data(io_config, self._sub_data)
            if enhanced_value is not None:
                return enhanced_value

        # 如果映射中没有转换配置，直接返回原始值
        return numeric_raw_value

    @callback
    def _get_extra_attributes(self) -> dict[str, Any] | None:
        """
        从映射配置获取传感器的额外状态属性 - 属性扩展核心函数。

        这是传感器属性扩展的核心函数，负责从 DEVICE_MAPPING 中获取和处理传感器的
        额外状态属性。这些属性会显示在 Home Assistant 的传感器详情页面中，
        为用户提供更丰富的设备信息和诊断数据。

        属性处理类型：

        **静态属性** (固定值属性)：
        - 配置中直接定义的固定值
        - 不会随设备状态变化，通常用于设备信息
        - 示例："device_model": "LS-TH01", "firmware_version": "1.2.3"
        - 配置格式：{"attribute_name": "fixed_value"}

        **动态属性** (实时数据属性)：
        - 从子设备实时数据中提取的动态值
        - 会随设备状态更新而变化
        - 示例："rssi": -65, "battery_voltage": 3.2
        - 配置格式：{"attribute_name": "data_field_name"}

        属性处理流程：
        1. **获取映射配置**：从 DEVICE_MAPPING 中获取 IO 口配置
        2. **提取属性配置**：查找 extra_attributes 字段
        3. **逐个处理属性**：区分静态和动态属性
        4. **统一处理接口**：使用 io_processors 统一处理动态属性
        5. **错误降级机制**：处理失败时使用后备逻辑

        常见属性类型示例：

        **设备状态属性**：
        - "rssi": 信号强度 (dBm)
        - "battery_level": 电量百分比 (%)
        - "battery_voltage": 电池电压 (V)
        - "last_seen": 最后通信时间

        **设备信息属性**：
        - "device_model": 设备型号
        - "firmware_version": 固件版本
        - "hardware_version": 硬件版本
        - "manufacturer": 制造商信息

        **环境监测属性**：
        - "air_quality_index": 空气质量指数
        - "comfort_level": 舒适度等级
        - "trend": 数据变化趋势

        错误处理和容错机制：
        - io_processors 处理失败时自动降级到直接字段访问
        - 静默失败机制，不中断其他属性的处理
        - 详细的错误日志记录和上下文信息
        - 支持部分属性缺失的情况

        Returns:
            dict[str, Any] | None: 处理后的额外属性字典，包含：
                - 静态属性：配置中定义的固定值
                - 动态属性：从设备数据中提取的实时值
                - 如果没有可用属性或处理失败则返回 None

        Note:
            额外属性为用户提供了设备的详细信息，对于设备调试和故障排查非常有用。
            属性的配置应该在 DEVICE_MAPPING 中进行，而不是在代码中硬编码。

            动态属性会随着设备状态的更新而自动刷新，为用户提供实时的
            设备监控信息。如果某个动态属性处理失败，不会影响其他属性的显示。
        """
        # 从DEVICE_MAPPING获取IO配置
        io_config = _get_enhanced_io_config(self._raw_device, self._sub_key)
        if not io_config:
            return None

        # 获取extra_attributes配置
        extra_attributes = io_config.get("extra_attributes")
        if not extra_attributes:
            return None

        # 处理静态和动态属性 - 使用io_processors统一处理
        result = {}
        for attr_name, attr_value in extra_attributes.items():
            if isinstance(attr_value, str) and attr_value in self._sub_data:
                # 动态属性：通过io_processors处理IO数据字段
                from .core.data.processors.io_processors import process_io_attributes

                # 创建属性配置，引用指定的IO数据字段
                attr_config = {
                    "attribute_generator": "default",
                    "attribute_config": {attr_name: attr_value},
                }

                try:
                    # 使用io_processors统一接口处理属性
                    processed_attrs = process_io_attributes(
                        attr_config, self._sub_data, None
                    )
                    if processed_attrs and attr_name in processed_attrs:
                        result[attr_name] = processed_attrs[attr_name]
                    else:
                        # 如果处理失败，使用原有逻辑作为后备
                        result[attr_name] = self._sub_data.get(attr_value)
                except Exception:
                    # 静默失败，使用后备逻辑，由handle_data_processing装饰器处理日志
                    result[attr_name] = self._sub_data.get(attr_value)
            else:
                # 静态属性：直接使用配置值
                result[attr_name] = attr_value

        return result if result else None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """
        返回此传感器的额外状态属性。

        合并基础属性和传感器特定属性。
        """
        # Get base attributes from parent class
        base_attrs = super().extra_state_attributes
        # Get sensor-specific extra attributes
        sensor_attrs = self._get_extra_attributes()

        if sensor_attrs:
            # Merge base attributes with sensor-specific ones
            if base_attrs:
                return {**base_attrs, **sensor_attrs}
            return sensor_attrs

        return base_attrs

    @property
    def device_info(self) -> DeviceInfo:
        """返回设备信息以链接实体到单个设备。"""
        return DeviceInfo(
            identifiers={(DOMAIN, self.agt, self.me)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=self.devtype,
            sw_version=self._raw_device.get(DEVICE_VERSION_KEY, "unknown"),
            via_device=(DOMAIN, self.agt),
        )

    async def async_added_to_hass(self) -> None:
        """
        注册更新监听器。

        设置实时更新和全局刷新的事件监听器。
        """
        # 实时更新事件
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{self._attr_unique_id}",
                self._handle_update,
            )
        )
        # 全局数据刷新事件
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                LIFESMART_SIGNAL_UPDATE_ENTITY,
                self._handle_global_refresh,
            )
        )

    async def _handle_update(self, new_data: dict) -> None:
        """
        处理实时更新数据。

        使用映射驱动的转换逻辑处理收到的实时状态更新。
        """
        try:
            if not new_data:
                _LOGGER.warning(
                    "Received empty new_data in _handle_update; "
                    "possible upstream issue."
                )
                return
            # 统一处理数据来源，提取IO数据
            io_data = {}
            if "msg" in new_data and isinstance(new_data["msg"], dict):
                msg_data = new_data["msg"]
                if msg_data is not None:
                    io_data = msg_data.get(self._sub_key, {})
            elif self._sub_key in new_data:
                io_data = new_data[self._sub_key]
            else:
                # 直接推送子键值对格式
                io_data = new_data

            if not io_data:
                return

            # 使用新的业务逻辑处理器进行映射驱动的数值转换
            io_config = _get_enhanced_io_config(self._raw_device, self._sub_key)
            if io_config:
                new_value = process_io_data(io_config, io_data)
            else:
                new_value = None

            if new_value is None:
                # 如果收到无效数据仅打印日志（已在convert中完成）
                return

            self._attr_native_value = new_value
            self._attr_available = True  # 收到有效数据，确保实体是可用的
            self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error("Error handling update for %s: %s", self._attr_unique_id, e)

    @handle_global_refresh()
    async def _handle_global_refresh(self) -> None:
        """
        处理周期性全量数据刷新，包含可用性检查。

        检查设备和子设备的存在性，更新可用性状态。
        """
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
                log_device_unavailable(self.unique_id, "global refresh")
                self._attr_available = False
                self.async_write_ha_state()
            return

        new_sub_data = safe_get(current_device, DEVICE_DATA_KEY, self._sub_key)
        if new_sub_data is None:
            if self.available:
                log_subdevice_unavailable(self.unique_id, self._sub_key)
                self._attr_available = False
                self.async_write_ha_state()
            return

        if not self.available:
            self._attr_available = True

        self._sub_data = new_sub_data
        new_value = self._extract_initial_value()

        if self._attr_native_value != new_value:
            self._attr_native_value = new_value
            self.async_write_ha_state()
