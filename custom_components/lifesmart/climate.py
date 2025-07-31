"""
此模块为 LifeSmart 平台提供温控设备 (Climate) 支持。

由 @MapleEve 初始创建和维护。

主要功能:
- 定义 LifeSmartClimate 实体，用于表示各种温控设备，如空调面板、地暖、风机盘管等。
- 通过动态分派机制，为不同 devtype 的设备提供专属的特性初始化和状态更新逻辑。
- 处理与 Home Assistant 核心的交互，包括实体设置、状态上报和服务调用。
- 对复杂的设备状态（如通过位掩码表示的模式和风速）进行解析和转换。
"""

import logging
from typing import Any

# 导入 Home Assistant 温控组件所需的核心类和常量
from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
)
from homeassistant.config_entries import ConfigEntry
# 导入 Home Assistant 的通用常量和核心对象类型
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature, PRECISION_TENTHS
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

# 导入项目内部的工具函数和常量
from . import LifeSmartDevice
from .const import (
    DOMAIN,
    MANUFACTURER,
    HUB_ID_KEY,
    DEVICE_ID_KEY,
    DEVICE_DATA_KEY,
    DEVICE_VERSION_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    CONF_EXCLUDE_ITEMS,
    CONF_EXCLUDE_AGTS,
    LIFESMART_HVAC_MODE_MAP,
    LIFESMART_CP_AIR_HVAC_MODE_MAP,
    LIFESMART_CP_AIR_FAN_MAP,
    LIFESMART_ACIPM_FAN_MAP,
    LIFESMART_F_HVAC_MODE_MAP,
    LIFESMART_TF_FAN_MAP,
    REVERSE_LIFESMART_CP_AIR_FAN_MAP,
    get_f_fan_mode,
    get_tf_fan_mode,
)
from .helpers import generate_unique_id, is_climate, safe_get

# 初始化模块级日志记录器
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """
    从配置条目异步设置 LifeSmart 温控设备。

    此函数在 Home Assistant 加载 LifeSmart 集成时被调用。
    它会从 hass.data 中获取已发现的设备列表，并筛选出温控设备，
    然后为每个温控设备创建一个 LifeSmartClimate 实体实例。
    """
    entry_id = config_entry.entry_id
    devices = hass.data[DOMAIN][entry_id]["devices"]
    client = hass.data[DOMAIN][entry_id]["client"]
    # 从配置选项中获取需要排除的设备和网关列表
    exclude_devices_str = config_entry.options.get(CONF_EXCLUDE_ITEMS, "")
    exclude_hubs_str = config_entry.options.get(CONF_EXCLUDE_AGTS, "")

    # 解析排除列表字符串为集合，以提高查找效率
    exclude_devices = {
        dev.strip() for dev in exclude_devices_str.split(",") if dev.strip()
    }
    exclude_hubs = {hub.strip() for hub in exclude_hubs_str.split(",") if hub.strip()}

    climates = []
    for device in devices:
        # 如果设备或其所属网关在排除列表中，则跳过
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        # 使用helpers中的统一判断函数
        if is_climate(device):
            climates.append(
                LifeSmartClimate(
                    raw_device=device,
                    client=client,
                    entry_id=entry_id,
                )
            )

    # 将创建的实体列表添加到 Home Assistant
    async_add_entities(climates)


class LifeSmartBaseClimate(LifeSmartDevice, ClimateEntity):
    """
    LifeSmart 温控设备基类。

    此类继承自 LifeSmartDevice (提供设备基础信息) 和 ClimateEntity (HA温控实体接口)。
    它实现了所有温控设备共有的逻辑，如设备信息、实体唯一ID、以及通过 dispatcher
    进行状态更新的监听和处理机制。
    """

    _attr_hvac_mode: HVACMode | None = None

    def __init__(
        self,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
    ) -> None:
        """初始化温控设备基类。"""
        super().__init__(raw_device, client)
        self._entry_id = entry_id

        self._attr_name = self._name
        device_name_slug = self._name.lower().replace(" ", "_")
        self._attr_object_id = device_name_slug

        self._attr_unique_id = generate_unique_id(self.devtype, self.agt, self.me, None)

    @property
    def device_info(self) -> DeviceInfo:
        """返回设备信息，用于在 Home Assistant UI 中将实体链接到物理设备。"""
        return DeviceInfo(
            identifiers={(DOMAIN, self.agt, self.me)},
            name=self._device_name,
            manufacturer=MANUFACTURER,
            model=self.devtype,
            sw_version=self._raw_device.get(DEVICE_VERSION_KEY, "unknown"),
            via_device=(DOMAIN, self.agt),  # 声明其通过哪个网关设备接入
        )

    async def async_added_to_hass(self) -> None:
        """
        当实体被添加到 Home Assistant 时调用的生命周期钩子。

        主要用于注册两个 dispatcher 监听器：
        1. 针对本实体的特定更新信号。
        2. 针对全局设备列表刷新信号。
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
                self.hass, LIFESMART_SIGNAL_UPDATE_ENTITY, self._handle_global_refresh
            )
        )

    @callback
    def _handle_update(self, new_data: dict) -> None:
        """
        处理来自 WebSocket 的实时状态更新。

        这是一个回调函数，当接收到特定于此实体的更新信号时被调用。
        它会调用 _update_state 方法来解析新数据，并请求 HA 更新前端状态。
        """
        if new_data:
            self._update_state(new_data)
            self.async_write_ha_state()

    @callback
    def _handle_global_refresh(self) -> None:
        """
        处理来自 API 轮询的全局设备列表刷新。

        当整个设备列表被刷新时，此回调被触发。它会从新的设备列表中
        找到代表当前实体的数据，并用它来更新自身状态。
        这确保了即使错过了 WebSocket 推送，状态也能最终保持一致。
        """
        try:
            devices = self.hass.data[DOMAIN][self._entry_id]["devices"]
            current_device = next(
                (d for d in devices if d[DEVICE_ID_KEY] == self.me), None
            )
            if current_device:
                self._raw_device = current_device
                self._update_state(current_device.get(DEVICE_DATA_KEY, {}))
                self.async_write_ha_state()
        except (KeyError, StopIteration):
            _LOGGER.warning("在全局刷新期间未能找到设备 %s。", self._attr_unique_id)

    @callback
    def _update_state(self, data: dict) -> None:
        """

        根据设备数据解析并更新实体状态的抽象方法。

        这个方法是状态更新的核心，但其具体实现被推迟到子类中，
        因为不同类型的温控设备解析数据的方式完全不同。
        这是一种模板方法设计模式。
        """
        raise NotImplementedError


class LifeSmartClimate(LifeSmartBaseClimate):
    """
    LifeSmart 温控设备实体的主实现类。

    此类实现了 _update_state 方法，并通过动态分派模式，为每种
    具体的 devtype 调用其专属的 `_init_*` 和 `_update_*` 方法。
    """

    # 为所有温控设备设置通用的温度单位、步长和精度
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = PRECISION_TENTHS
    _attr_precision = PRECISION_TENTHS

    def __init__(
        self,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
    ) -> None:
        """初始化温控设备实体。"""
        super().__init__(raw_device, client, entry_id)

        # 使用分派模式初始化特性和初始状态
        self._initialize_features()
        self._update_state(self._raw_device.get(DEVICE_DATA_KEY, {}))

    @callback
    def _initialize_features(self) -> None:
        """
        根据设备类型动态初始化支持的特性。

        使用 getattr 查找名为 `_init_{devtype}` 的方法。如果找不到，
        则调用 `_init_default` 作为后备。这使得添加新设备类型变得容易，
        只需增加一个新的 `_init_*` 方法即可。
        """
        init_method = getattr(self, f"_init_{self.devtype.lower()}", self._init_default)
        init_method()

    @callback
    def _update_state(self, data: dict) -> None:
        """
        根据设备数据动态解析并更新实体状态。

        与 _initialize_features 类似，此方法使用 getattr 动态调用
        特定于设备类型的 `_update_*` 方法来处理状态更新。
        """
        update_method = getattr(
            self,
            f"_update_{self.devtype.lower()}",
            self._update_default,
        )
        update_method(data)

    # --- 设备专属初始化方法 ---
    # 每个 `_init_*` 方法负责定义一种设备所支持的模式、特性和温度范围。
    def _init_default(self):
        """默认温控器初始化 (例如，仅支持制热的地暖)。"""
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )

    def _init_v_air_p(self):
        """初始化 V_AIR_P 空调面板。"""
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )
        self._attr_hvac_modes = [
            HVACMode.OFF,
            HVACMode.AUTO,
            HVACMode.FAN_ONLY,
            HVACMode.COOL,
            HVACMode.HEAT,
            HVACMode.DRY,
        ]
        self._attr_fan_modes = list(LIFESMART_F_HVAC_MODE_MAP.keys())
        self._attr_min_temp, self._attr_max_temp = 10, 35

    def _init_sl_uaccb(self):
        """初始化 SL_UACCB 空调控制器 (其逻辑与 V_AIR_P 几乎相同)。"""
        self._init_v_air_p()

    def _init_sl_nature(self):
        """
        初始化 SL_NATURE 超能温控面板。

        这是一个复杂的例子，其支持的HVAC模式是动态的，
        取决于设备配置IO口 'P6' 的值。
        """
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )
        # 根据 P6(CFG) 的值动态确定支持的 HVAC 模式
        p6_cfg = safe_get(self._raw_device, DEVICE_DATA_KEY, "P6", "val", default=0)
        cfg_mode = (p6_cfg >> 6) & 0x7
        modes_map = {
            1: [HVACMode.FAN_ONLY, HVACMode.COOL, HVACMode.HEAT],
            3: [HVACMode.FAN_ONLY, HVACMode.COOL, HVACMode.HEAT, HVACMode.HEAT_COOL],
            4: [HVACMode.AUTO, HVACMode.FAN_ONLY, HVACMode.COOL, HVACMode.HEAT],
            5: [HVACMode.FAN_ONLY, HVACMode.HEAT_COOL],
        }
        modes = modes_map.get(cfg_mode, [])
        self._attr_hvac_modes = [HVACMode.OFF] + modes
        self._attr_fan_modes = list(LIFESMART_TF_FAN_MAP.keys())
        self._attr_min_temp, self._attr_max_temp = 10, 35

    def _init_sl_fcu(self):
        """初始化 SL_FCU 星玉温控面板 (其逻辑与 SL_NATURE 相同)。"""
        self._init_sl_nature()

    def _init_sl_cp_dn(self):
        """初始化 SL_CP_DN 地暖温控器。"""
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO]
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )
        self._attr_min_temp, self._attr_max_temp = 5, 35

    def _init_sl_cp_air(self):
        """初始化 SL_CP_AIR 风机盘管。"""
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )
        self._attr_hvac_modes = [
            HVACMode.OFF,
            HVACMode.COOL,
            HVACMode.HEAT,
            HVACMode.FAN_ONLY,
            # 'auto' 模式由风速的 'auto' 档实现，但这里仍需声明
            HVACMode.AUTO,
        ]
        self._attr_fan_modes = list(LIFESMART_CP_AIR_FAN_MAP.keys())
        self._attr_min_temp, self._attr_max_temp = 10, 35

    def _init_sl_cp_vl(self):
        """初始化 SL_CP_VL 温控阀门。"""
        self._attr_hvac_modes = [
            HVACMode.OFF,
            HVACMode.HEAT,
            HVACMode.AUTO,
        ]  # 手动/节能 -> HEAT, 自动 -> AUTO
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )
        self._attr_min_temp, self._attr_max_temp = 5, 35

    def _init_sl_tr_acipm(self):
        """初始化 SL_TR_ACIPM 新风系统。"""
        self._attr_supported_features = (
            ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )
        self._attr_hvac_modes = [
            HVACMode.OFF,
            HVACMode.FAN_ONLY,
        ]  # 简化模式，主要控制风速
        self._attr_fan_modes = list(LIFESMART_ACIPM_FAN_MAP.keys())

    def _init_v_fresh_p(self):
        """初始化 V_FRESH_P 新风系统。"""
        self._attr_supported_features = (
            ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.TURN_ON
            | ClimateEntityFeature.TURN_OFF
        )
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.FAN_ONLY]
        self._attr_fan_modes = [FAN_LOW, FAN_MEDIUM, FAN_HIGH]

    # --- 设备专属状态更新方法 ---
    # 每个 `_update_*` 方法负责从原始数据 `data` 中解析出实体的各个状态属性。
    def _update_default(self, data: dict):
        """默认的更新方法，当没有找到特定类型的更新方法时调用。"""
        _LOGGER.warning("没有为 %s 类型设备指定的状态更新方法", self.devtype)

    def _update_v_air_p(self, data: dict):
        """更新 V_AIR_P 空调面板的状态。"""
        o_type = safe_get(data, "O", "type", default=0)
        is_on = o_type % 2 == 1
        if is_on:
            mode_val = safe_get(data, "MODE", "val")
            if mode_val is not None:
                self._attr_hvac_mode = LIFESMART_HVAC_MODE_MAP.get(mode_val)
        else:
            self._attr_hvac_mode = HVACMode.OFF

        if (temp := safe_get(data, "T", "v")) is not None:
            self._attr_current_temperature = temp
        if (target_temp := safe_get(data, "tT", "v")) is not None:
            self._attr_target_temperature = target_temp
        if (fan_val := safe_get(data, "F", "val", default=0)) is not None:
            self._attr_fan_mode = get_f_fan_mode(fan_val)

    def _update_sl_uaccb(self, data: dict):
        """更新 SL_UACCB 状态 (其逻辑与 V_AIR_P 几乎相同)。"""
        p1_type = safe_get(data, "P1", "type", default=0)
        is_on = p1_type % 2 == 1
        if is_on:
            p2_val = safe_get(data, "P2", "val")
            if p2_val is not None:
                self._attr_hvac_mode = LIFESMART_HVAC_MODE_MAP.get(p2_val)
        else:
            self._attr_hvac_mode = HVACMode.OFF

        if (temp := safe_get(data, "P6", "v")) is not None:
            self._attr_current_temperature = temp
        if (target_temp := safe_get(data, "P3", "v")) is not None:
            self._attr_target_temperature = target_temp
        if (fan_val := safe_get(data, "P4", "val", default=0)) is not None:
            self._attr_fan_mode = get_f_fan_mode(fan_val)

    def _update_sl_cp_vl(self, data: dict):
        """更新 SL_CP_VL 温控阀门状态。"""
        self._p1_val = safe_get(data, "P1", "val", default=0)
        p1_type = safe_get(data, "P1", "type", default=0)
        self._attr_is_on = p1_type % 2 == 1
        if self._attr_is_on:
            mode_val = (self._p1_val >> 1) & 0b11
            mode_map = {0: HVACMode.HEAT, 1: HVACMode.HEAT, 2: HVACMode.AUTO}
            self._attr_hvac_mode = mode_map.get(mode_val, HVACMode.HEAT)
        else:
            self._attr_hvac_mode = HVACMode.OFF

        if (temp := safe_get(data, "P4", "v")) is not None:
            self._attr_current_temperature = temp
        if (target_temp := safe_get(data, "P3", "v")) is not None:
            self._attr_target_temperature = target_temp

    def _update_sl_nature(self, data: dict):
        """更新 SL_NATURE 超能面板的状态。"""
        p1_type = safe_get(data, "P1", "type", default=0)
        is_on = p1_type % 2 == 1
        if is_on:
            p7_val = safe_get(data, "P7", "val")
            if p7_val is not None:
                self._attr_hvac_mode = LIFESMART_HVAC_MODE_MAP.get(p7_val)
        else:
            self._attr_hvac_mode = HVACMode.OFF

        if (temp := safe_get(data, "P4", "v")) is not None:
            self._attr_current_temperature = temp
        if (target_temp := safe_get(data, "P8", "v")) is not None:
            self._attr_target_temperature = target_temp
        if (fan_val := safe_get(data, "P10", "val", default=0)) is not None:
            self._attr_fan_mode = get_tf_fan_mode(fan_val)

    def _update_sl_fcu(self, data: dict):
        """更新 SL_FCU 状态 (其逻辑与 SL_NATURE 相同)。"""
        self._update_sl_nature(data)

    def _update_sl_cp_dn(self, data: dict):
        """更新 SL_CP_DN 地暖温控器状态。"""
        self._p1_val = safe_get(data, "P1", "val", default=0)
        p1_type = safe_get(data, "P1", "type", default=0)
        self._attr_is_on = p1_type % 2 == 1
        if self._attr_is_on:
            is_auto_mode = (self._p1_val >> 31) & 0b1
            self._attr_hvac_mode = HVACMode.AUTO if is_auto_mode else HVACMode.HEAT
        else:
            self._attr_hvac_mode = HVACMode.OFF

        if (temp := safe_get(data, "P4", "v")) is not None:
            self._attr_current_temperature = temp
        if (target_temp := safe_get(data, "P3", "v")) is not None:
            self._attr_target_temperature = target_temp

    def _update_sl_cp_air(self, data: dict):
        """更新 SL_CP_AIR 风机盘管状态。"""
        self._p1_val = safe_get(data, "P1", "val", default=0)
        p1_type = safe_get(data, "P1", "type", default=0)
        self._attr_is_on = p1_type % 2 == 1
        if self._attr_is_on:
            mode_val = (self._p1_val >> 13) & 0b11
            fan_val = (self._p1_val >> 15) & 0b11
            self._attr_hvac_mode = LIFESMART_CP_AIR_HVAC_MODE_MAP.get(mode_val)
            self._attr_fan_mode = REVERSE_LIFESMART_CP_AIR_FAN_MAP.get(fan_val)
        else:
            self._attr_hvac_mode = HVACMode.OFF

        if (temp := safe_get(data, "P5", "v")) is not None:
            self._attr_current_temperature = temp
        if (target_temp := safe_get(data, "P4", "v")) is not None:
            self._attr_target_temperature = target_temp

    def _update_sl_tr_acipm(self, data: dict):
        """更新 SL_TR_ACIPM 新风系统状态。"""
        p1_type = safe_get(data, "P1", "type", default=0)
        is_on = p1_type % 2 == 1
        self._attr_hvac_mode = HVACMode.FAN_ONLY if is_on else HVACMode.OFF
        fan_val = safe_get(data, "P1", "val", default=0)
        self._attr_fan_mode = next(
            (k for k, v in LIFESMART_ACIPM_FAN_MAP.items() if v == fan_val), None
        )

    def _update_v_fresh_p(self, data: dict):
        """更新 V_FRESH_P 新风系统状态。"""
        o_type = safe_get(data, "O", "type", default=0)
        is_on = o_type % 2 == 1
        self._attr_hvac_mode = HVACMode.FAN_ONLY if is_on else HVACMode.OFF
        if (f1_val := safe_get(data, "F1", "val", default=0)) is not None:
            self._attr_fan_mode = get_f_fan_mode(f1_val)
        if (temp := safe_get(data, "T", "v")) is not None:
            self._attr_current_temperature = temp

    # --- 控制方法 ---
    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """
        设置新的HVAC模式。

        此方法被 Home Assistant 的服务调用触发。
        它会获取当前设备的状态值（特别是对于需要位操作的设备），
        然后调用底层的 client 方法来发送命令。
        """
        # 原始代码错误地使用了 `getattr(self, "val", 0)`。
        # 正确的做法是使用 `_p1_val`，这个值在 `_update_*` 方法中被正确地缓存了。
        # 对于不使用位掩码的设备，此值为0，不影响 client 侧的逻辑。
        current_val = getattr(self, "_p1_val", 0)
        await self._client.async_set_climate_hvac_mode(
            self.agt,
            self.me,
            self.devtype,
            hvac_mode,
            current_val,
        )

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """
        设置新的风扇模式。

        与 async_set_hvac_mode 类似，此方法也需要传递正确的当前状态值
        给 client，以便进行正确的位掩码计算。
        """
        current_val = getattr(self, "_p1_val", 0)
        await self._client.async_set_climate_fan_mode(
            self.agt, self.me, self.devtype, fan_mode, current_val
        )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """设置新的目标温度。"""
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is not None:
            await self._client.async_set_climate_temperature(
                self.agt, self.me, self.devtype, temp
            )
