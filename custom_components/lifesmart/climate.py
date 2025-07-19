"""Support for the LifeSmart climate devices by @MapleEve"""

import logging
from typing import Any

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature, PRECISION_TENTHS
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import generate_entity_id
from .const import (
    DOMAIN,
    MANUFACTURER,
    HUB_ID_KEY,
    DEVICE_ID_KEY,
    DEVICE_TYPE_KEY,
    DEVICE_NAME_KEY,
    DEVICE_DATA_KEY,
    DEVICE_VERSION_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    CLIMATE_TYPES,
    LIFESMART_HVAC_MODE_MAP,
    LIFESMART_CP_AIR_MODE_MAP,
    LIFESMART_CP_AIR_FAN_MAP,
    LIFESMART_ACIPM_FAN_MAP,
    LIFESMART_F_FAN_MODE_MAP,
    LIFESMART_TF_FAN_MODE_MAP,
    get_f_fan_mode,
    get_tf_fan_mode,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """从配置条目设置 LifeSmart 温控设备。"""
    entry_id = config_entry.entry_id
    devices = hass.data[DOMAIN][entry_id]["devices"]
    client = hass.data[DOMAIN][entry_id]["client"]
    exclude_devices = hass.data[DOMAIN][entry_id]["exclude_devices"]
    exclude_hubs = hass.data[DOMAIN][entry_id]["exclude_hubs"]

    climates = []
    for device in devices:
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        if _is_climate_device(device):
            climates.append(
                LifeSmartClimate(
                    raw_device=device,
                    client=client,
                    entry_id=entry_id,
                )
            )

    async_add_entities(climates)


def _is_climate_device(device: dict) -> bool:
    """判断一个设备是否为有效的温控实体，对 SL_NATURE 进行特殊处理。"""
    device_type = device[DEVICE_TYPE_KEY]

    if device_type == "SL_NATURE":
        # 温控版 SL_NATURE 必须存在 P5 且值为 3
        p5_data = device.get(DEVICE_DATA_KEY, {}).get("P5", {})
        return p5_data.get("val", 0) & 0xFF == 3

    return device_type in CLIMATE_TYPES


class LifeSmartClimate(ClimateEntity):
    """LifeSmart 温控设备实体。"""

    _attr_has_entity_name = True
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = PRECISION_TENTHS
    _attr_precision = PRECISION_TENTHS

    def __init__(
        self,
        raw_device: dict[str, Any],
        client: Any,
        entry_id: str,
    ) -> None:
        """初始化温控设备。"""
        self._raw_device = raw_device
        self._client = client
        self._entry_id = entry_id
        self.device_type = raw_device[DEVICE_TYPE_KEY]
        self._hub_id = raw_device[HUB_ID_KEY]
        self._device_id = raw_device[DEVICE_ID_KEY]

        self._attr_unique_id = generate_entity_id(
            self.device_type, self._hub_id, self._device_id, "climate"
        )
        self._attr_name = raw_device.get(DEVICE_NAME_KEY, "Unknown Climate")

        # 使用分派模式初始化特性和状态
        self._initialize_features()
        self._update_state(raw_device.get(DEVICE_DATA_KEY, {}))

    @callback
    def _initialize_features(self) -> None:
        """根据设备类型初始化支持的特性。"""
        init_method = getattr(
            self, f"_init_{self.device_type.lower()}", self._init_default
        )
        init_method()

    @callback
    def _update_state(self, data: dict) -> None:
        """根据设备数据解析并更新实体状态。"""
        update_method = getattr(
            self, f"_update_{self.device_type.lower()}", self._update_default
        )
        update_method(data)
        self.async_write_ha_state()

    # --- 设备专属初始化方法 ---
    def _init_default(self):
        """默认温控器初始化 (如仅支持制热的地暖)。"""
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT]
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE

    def _init_v_air_p(self):
        """初始化 V_AIR_P 空调面板。"""
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE
        )
        self._attr_hvac_modes = [
            HVACMode.OFF,
            HVACMode.AUTO,
            HVACMode.FAN_ONLY,
            HVACMode.COOL,
            HVACMode.HEAT,
            HVACMode.DRY,
        ]
        self._attr_fan_modes = list(LIFESMART_F_FAN_MODE_MAP.keys())
        self._attr_min_temp, self._attr_max_temp = 10, 35

    def _init_sl_uaccb(self):
        """初始化 SL_UACCB 空调控制器 (逻辑与 V_AIR_P 相同)。"""
        self._init_v_air_p()

    def _init_sl_nature(self):
        """初始化 SL_NATURE 超能温控面板。"""
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE
        )
        # 根据 P6(CFG) 的值动态确定支持的 HVAC 模式
        p6_cfg = self._raw_device.get(DEVICE_DATA_KEY, {}).get("P6", {}).get("val", 0)
        cfg_mode = (p6_cfg >> 6) & 0x7
        modes = {
            1: [HVACMode.FAN_ONLY, HVACMode.COOL, HVACMode.HEAT],
            3: [HVACMode.FAN_ONLY, HVACMode.COOL, HVACMode.HEAT, HVACMode.HEAT_COOL],
            4: [
                HVACMode.AUTO,
                HVACMode.FAN_ONLY,
                HVACMode.COOL,
                HVACMode.HEAT,
                HVACMode.HEAT_COOL,
            ],
            5: [HVACMode.FAN_ONLY, HVACMode.HEAT_COOL],
        }.get(cfg_mode, [])
        self._attr_hvac_modes = [HVACMode.OFF] + modes
        self._attr_fan_modes = list(LIFESMART_TF_FAN_MODE_MAP.keys())
        self._attr_min_temp, self._attr_max_temp = 10, 35

    def _init_sl_fcu(self):
        """初始化 SL_FCU 星玉温控面板 (逻辑与 SL_NATURE 相同)。"""
        self._init_sl_nature()

    def _init_sl_cp_dn(self):
        """初始化 SL_CP_DN 地暖温控器。"""
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.HEAT, HVACMode.AUTO]
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
        self._attr_min_temp, self._attr_max_temp = 5, 35

    def _init_sl_cp_air(self):
        """初始化 SL_CP_AIR 风机盘管。"""
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE
        )
        self._attr_hvac_modes = [
            HVACMode.OFF,
            HVACMode.COOL,
            HVACMode.HEAT,
            HVACMode.FAN_ONLY,
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
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE
        self._attr_min_temp, self._attr_max_temp = 5, 35

    def _init_sl_tr_acipm(self):
        """初始化 SL_TR_ACIPM 新风系统。"""
        self._attr_supported_features = ClimateEntityFeature.FAN_MODE
        self._attr_hvac_modes = [
            HVACMode.OFF,
            HVACMode.FAN_ONLY,
        ]  # 简化模式，主要控制风速
        self._attr_fan_modes = list(LIFESMART_ACIPM_FAN_MAP.keys())

    def _init_sl_tr_xx(self):
        """初始化 SL_TR_XX 多功能中央空调智控网关 (逻辑与 SL_TR_ACIPM 相同)。"""
        self._init_sl_tr_acipm()

    def _init_v_fresh_p(self):
        """初始化 V_FRESH_P 新风系统。"""
        self._attr_supported_features = ClimateEntityFeature.FAN_MODE
        self._attr_hvac_modes = [HVACMode.OFF, HVACMode.FAN_ONLY]
        self._attr_fan_modes = [FAN_LOW, FAN_MEDIUM, FAN_HIGH]

    # --- 设备专属状态更新方法 ---
    def _update_default(self, data: dict):
        _LOGGER.warning("没有为 %s 类型设备指定的状态更新方法", self.device_type)

    def _update_v_air_p(self, data: dict):
        is_on = data.get("O", {}).get("type", 0) % 2 == 1
        self._attr_hvac_mode = (
            LIFESMART_HVAC_MODE_MAP.get(data.get("MODE", {}).get("val"))
            if is_on
            else HVACMode.OFF
        )
        self._attr_current_temperature = data.get("T", {}).get("v")
        self._attr_target_temperature = data.get("tT", {}).get("v")
        self._attr_fan_mode = get_f_fan_mode(data.get("F", {}).get("val", 0))

    def _update_sl_uaccb(self, data: dict):
        """更新 SL_UACCB 状态 (逻辑与 V_AIR_P 相同)。"""
        is_on = data.get("P1", {}).get("type", 0) % 2 == 1
        self._attr_hvac_mode = (
            LIFESMART_HVAC_MODE_MAP.get(data.get("P2", {}).get("val"))
            if is_on
            else HVACMode.OFF
        )
        self._attr_current_temperature = data.get("P6", {}).get("v")
        self._attr_target_temperature = data.get("P3", {}).get("v")
        self._attr_fan_mode = get_f_fan_mode(data.get("P4", {}).get("val", 0))

    def _update_sl_cp_vl(self, data: dict):
        """更新 SL_CP_VL 温控阀门状态。"""
        p1_data = data.get("P1", {})
        self._attr_is_on = p1_data.get("type", 0) % 2 == 1
        if self._attr_is_on:
            # 解析 val 的 bit 1-2
            mode_val = (p1_data.get("val", 0) >> 1) & 0b11
            mode_map = {
                0: HVACMode.HEAT,  # 手动模式
                1: HVACMode.HEAT,  # 节能模式 (视为HEAT的一种)
                2: HVACMode.AUTO,  # 自动模式
            }
            self._attr_hvac_mode = mode_map.get(mode_val, HVACMode.HEAT)
        else:
            self._attr_hvac_mode = HVACMode.OFF
        self._attr_current_temperature = data.get("P4", {}).get("v")
        self._attr_target_temperature = data.get("P3", {}).get("v")
        self._p1_val = p1_data.get("val", 0)

    def _update_sl_nature(self, data: dict):
        is_on = data.get("P1", {}).get("type", 0) % 2 == 1
        self._attr_hvac_mode = (
            LIFESMART_HVAC_MODE_MAP.get(data.get("P7", {}).get("val"))
            if is_on
            else HVACMode.OFF
        )
        self._attr_current_temperature = data.get("P4", {}).get("v")
        self._attr_target_temperature = data.get("P8", {}).get("v")
        self._attr_fan_mode = get_tf_fan_mode(data.get("P10", {}).get("val", 0))

    def _update_sl_fcu(self, data: dict):
        """更新 SL_FCU 状态 (逻辑与 SL_NATURE 相同)。"""
        self._update_sl_nature(data)

    def _update_sl_cp_dn(self, data: dict):
        p1_data = data.get("P1", {})
        self._attr_is_on = p1_data.get("type", 0) % 2 == 1
        if self._attr_is_on:
            # 解析 val 的 bit 31 来确定模式
            is_auto_mode = (p1_data.get("val", 0) >> 31) & 0b1
            self._attr_hvac_mode = HVACMode.AUTO if is_auto_mode else HVACMode.HEAT
        else:
            self._attr_hvac_mode = HVACMode.OFF
        self._attr_current_temperature = data.get("P4", {}).get("v")
        self._attr_target_temperature = data.get("P3", {}).get("v")
        self._p1_val = p1_data.get("val", 0)

    def _update_sl_cp_air(self, data: dict):
        p1_data = data.get("P1", {})
        self._attr_is_on = p1_data.get("type", 0) % 2 == 1
        if self._attr_is_on:
            val = p1_data.get("val", 0)
            mode_val = (val >> 13) & 0b11
            fan_val = (val >> 15) & 0b11
            self._attr_hvac_mode = LIFESMART_CP_AIR_MODE_MAP.get(mode_val)
            self._attr_fan_mode = LIFESMART_CP_AIR_FAN_MAP.get(fan_val)
        else:
            self._attr_hvac_mode = HVACMode.OFF
        self._attr_current_temperature = data.get("P5", {}).get("v")
        self._attr_target_temperature = data.get("P4", {}).get("v")
        self._p1_val = p1_data.get("val", 0)

    def _update_v_fresh_p(self, data: dict):
        """更新 V_FRESH_P 新风系统状态。"""
        is_on = data.get("O", {}).get("type", 0) % 2 == 1
        self._attr_hvac_mode = HVACMode.FAN_ONLY if is_on else HVACMode.OFF
        # 该设备有送风(F1)和排风(F2)，这里简化为取送风风速
        self._attr_fan_mode = get_f_fan_mode(data.get("F1", {}).get("val", 0))
        self._attr_current_temperature = data.get("T", {}).get("v")

    def _update_sl_tr_acipm(self, data: dict):
        """更新 SL_TR_ACIPM 新风系统状态。"""
        # SL_TR_ACIPM 新风系统主要通过 P1 控制开关，P2 控制风速
        p1_data = data.get("P1", {})
        is_on = p1_data.get("type", 0) % 2 == 1
        self._attr_hvac_mode = HVACMode.FAN_ONLY if is_on else HVACMode.OFF
        
        # P2 用于风速控制
        fan_val = data.get("P2", {}).get("val", 1)
        from .const import REVERSE_LIFESMART_ACIPM_FAN_MAP
        self._attr_fan_mode = REVERSE_LIFESMART_ACIPM_FAN_MAP.get(fan_val, FAN_LOW)

    def _update_sl_tr_xx(self, data: dict):
        """更新 SL_TR_XX 多功能中央空调智控网关状态 (逻辑与 SL_TR_ACIPM 相同)。"""
        self._update_sl_tr_acipm(data)

    # --- 控制方法 ---
    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """设置新的HVAC模式。"""
        current_val = getattr(self, "_p1_val", 0)
        await self._client.async_set_climate_hvac_mode(
            self._hub_id, self._device_id, self.device_type, hvac_mode, current_val
        )

    async def async_set_fan_mode(self, fan_mode: str) -> None:
        """设置新的风扇模式。"""
        current_val = getattr(self, "_p1_val", 0)
        await self._client.async_set_climate_fan_mode(
            self._hub_id, self._device_id, self.device_type, fan_mode, current_val
        )

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """设置新的目标温度。"""
        if (temp := kwargs.get(ATTR_TEMPERATURE)) is not None:
            await self._client.async_set_climate_temperature(
                self._hub_id, self._device_id, self.device_type, temp
            )

    @property
    def device_info(self) -> DeviceInfo:
        """返回设备信息以链接实体到单个设备。"""
        return DeviceInfo(
            identifiers={
                (DOMAIN, self._raw_device[HUB_ID_KEY], self._raw_device[DEVICE_ID_KEY])
            },
            name=self._raw_device[DEVICE_NAME_KEY],
            manufacturer=MANUFACTURER,
            model=self._raw_device[DEVICE_TYPE_KEY],
            sw_version=self._raw_device.get(DEVICE_VERSION_KEY, "unknown"),
            via_device=(
                (DOMAIN, self._raw_device[HUB_ID_KEY])
                if self._raw_device[HUB_ID_KEY]
                else None
            ),
        )

    async def async_added_to_hass(self) -> None:
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{self.unique_id}",
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
        if new_data:
            self._update_state(new_data)

    @callback
    def _handle_global_refresh(self) -> None:
        try:
            devices = self.hass.data[DOMAIN][self._entry_id]["devices"]
            current_device = next(
                (d for d in devices if d[DEVICE_ID_KEY] == self._device_id), None
            )
            if current_device:
                self._update_state(current_device.get(DEVICE_DATA_KEY, {}))
        except (KeyError, StopIteration):
            _LOGGER.warning(
                "Could not find device %s during global refresh.", self.unique_id
            )
