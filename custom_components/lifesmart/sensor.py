"""Support for LifeSmart sensors by @MapleEve"""

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    LIGHT_LUX,
    PERCENTAGE,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfSoundPressure,
    UnitOfElectricCurrent,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import LifeSmartDevice, generate_unique_id
from .const import (
    # 核心常量
    DOMAIN,
    MANUFACTURER,
    HUB_ID_KEY,
    DEVICE_ID_KEY,
    DEVICE_TYPE_KEY,
    DEVICE_NAME_KEY,
    DEVICE_DATA_KEY,
    DEVICE_VERSION_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    # --- 设备类型常量导入 ---
    ALL_SENSOR_TYPES,
    EV_SENSOR_TYPES,
    ENVIRONMENT_SENSOR_TYPES,
    GAS_SENSOR_TYPES,
    NOISE_SENSOR_TYPES,
    POWER_METER_PLUG_TYPES,
    SMART_PLUG_TYPES,
    POWER_METER_TYPES,
    LOCK_TYPES,
    COVER_TYPES,
    DEFED_SENSOR_TYPES,
    WATER_SENSOR_TYPES,
    SUPPORTED_SWITCH_TYPES,
    GARAGE_DOOR_TYPES,
    CLIMATE_TYPES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up LifeSmart from a config entry."""
    entry_id = config_entry.entry_id
    devices = hass.data[DOMAIN][entry_id]["devices"]
    client = hass.data[DOMAIN][entry_id]["client"]
    exclude_devices = hass.data[DOMAIN][entry_id]["exclude_devices"]
    exclude_hubs = hass.data[DOMAIN][entry_id]["exclude_hubs"]

    sensors = []
    for device in devices:
        if (
            device[DEVICE_ID_KEY] in exclude_devices
            or device[HUB_ID_KEY] in exclude_hubs
        ):
            continue

        device_type = device[DEVICE_TYPE_KEY]

        if device_type == "SL_NATURE":
            p5_val = device.get(DEVICE_DATA_KEY, {}).get("P5", {}).get("val", 1) & 0xFF
            if p5_val == 3:  # 是温控面板
                # P4 是当前温度
                if "P4" in device[DEVICE_DATA_KEY]:
                    sensors.append(
                        LifeSmartSensor(
                            raw_device=device,
                            sub_device_key="P4",
                            sub_device_data=device[DEVICE_DATA_KEY]["P4"],
                            client=client,
                            entry_id=entry_id,
                        )
                    )
            continue  # 处理完 SL_NATURE，跳过

        if device_type not in ALL_SENSOR_TYPES:
            continue

        for sub_key, sub_data in device[DEVICE_DATA_KEY].items():
            if not _is_sensor_subdevice(device_type, sub_key):
                continue

            sensors.append(
                LifeSmartSensor(
                    raw_device=device,
                    sub_device_key=sub_key,
                    sub_device_data=sub_data,
                    client=client,
                    entry_id=entry_id,
                )
            )

    async_add_entities(sensors)


def _is_sensor_subdevice(device_type: str, sub_key: str) -> bool:
    """判断一个子设备是否为有效的数值传感器。"""
    if device_type in CLIMATE_TYPES:
        # 温控设备的温度/阀门等状态由 climate 实体内部管理
        if device_type == "SL_CP_DN" and sub_key == "P5":
            return True
        if device_type == "SL_CP_VL" and sub_key == "P6":
            return True
        if device_type == "SL_TR_ACIPM" and sub_key in {"P4", "P5"}:
            return True
        return False

    # 环境感应器（包括温度、湿度、光照、电压）
    if device_type in EV_SENSOR_TYPES and sub_key in {
        "T",
        "H",
        "Z",
        "V",
        "P1",
        "P2",
        "P3",
        "P4",
        "P5",
    }:
        return True

    # TVOC, CO2, CH2O 传感器
    if device_type in ENVIRONMENT_SENSOR_TYPES and sub_key in {"P1", "P3", "P4"}:
        return True

    # 气体感应器
    if device_type in GAS_SENSOR_TYPES and sub_key in {"P1", "P2"}:
        return True

    # 门锁电量
    if device_type in LOCK_TYPES and sub_key == "BAT":
        return True

    # 窗帘位置
    if device_type in COVER_TYPES and sub_key == "P8":
        return True

    # 智能插座
    if device_type in POWER_METER_PLUG_TYPES and sub_key in {"P2", "P3", "P4"}:
        return True

    # 智能插座 (非计量版，但也可能带计量功能)
    if device_type in SMART_PLUG_TYPES and sub_key in {"EV", "EI", "EP", "EPA"}:
        return True

    # 噪音感应器
    if device_type in NOISE_SENSOR_TYPES and sub_key in {"P1", "P2"}:
        return True

    # ELIQ电量计量器
    if device_type in POWER_METER_TYPES and sub_key in {"EPA", "EE", "EP"}:
        return True

    # 云防系列传感器
    if device_type in DEFED_SENSOR_TYPES and sub_key in {"T", "V"}:
        return True

    # 水浸传感器（只保留电压）
    if device_type in WATER_SENSOR_TYPES and sub_key == "V":
        return True

    # SL_SW* 和 SL_MC* 系列的 P4 是电量传感器
    if device_type in SUPPORTED_SWITCH_TYPES and sub_key == "P4":
        return True

    # SL_SC_BB_V2 的 P2 是电量传感器
    if device_type == "SL_SC_BB_V2" and sub_key == "P2":
        return True

    if device_type in GARAGE_DOOR_TYPES:
        return False

    return False


class LifeSmartSensor(LifeSmartDevice, SensorEntity):
    """LifeSmart sensor entity with enhanced compatibility."""

    _attr_has_entity_name = False

    def __init__(
        self,
        raw_device: dict[str, Any],
        sub_device_key: str,
        sub_device_data: dict[str, Any],
        client: Any,
        entry_id: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(raw_device, client)
        self._raw_device = raw_device
        self._sub_key = sub_device_key
        self._sub_data = sub_device_data
        self._entry_id = entry_id
        self._attr_unique_id = generate_unique_id(
            self.devtype,
            self.agt,
            self.me,
            sub_device_key,
        )
        self._attr_name = self._generate_sensor_name()
        self._attr_device_class = self._determine_device_class()
        self._attr_state_class = self._determine_state_class()
        self._attr_native_unit_of_measurement = self._determine_unit()
        self._attr_native_value = self._extract_initial_value()
        self._attr_extra_state_attributes = self._get_extra_attributes()

    @callback
    def _generate_sensor_name(self) -> str | None:
        """Generate user-friendly sensor name."""
        base_name = self._raw_device.get(DEVICE_NAME_KEY, "Unknown Sensor")
        # 如果子设备有自己的名字 (如多联开关的按键名)，则使用它
        sub_name = self._sub_data.get(DEVICE_NAME_KEY)
        if sub_name and sub_name != self._sub_key:
            return f"{base_name} {sub_name}"
        # 否则，使用基础名 + IO口索引
        return f"{base_name} {self._sub_key.upper()}"

    @callback
    def _determine_device_class(self) -> SensorDeviceClass | None:
        """Automatically determine device class based on sub-device."""
        device_type = self._raw_device[DEVICE_TYPE_KEY]
        sub_key = self._sub_key

        # 气体传感器优先判断
        if device_type in GAS_SENSOR_TYPES and sub_key in {"P1", "P2"}:
            return SensorDeviceClass.GAS

        # 温控设备特殊处理
        if device_type in CLIMATE_TYPES:
            if sub_key == "P5":
                return (
                    SensorDeviceClass.TEMPERATURE
                    if device_type == "SL_CP_DN"
                    else SensorDeviceClass.PM25
                )
            if sub_key == "P6":
                return SensorDeviceClass.BATTERY
            if sub_key == "P4":
                return SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS
            return None

        # 根据子设备键判断
        if sub_key == "BAT":
            return SensorDeviceClass.BATTERY
        if sub_key == "T":
            return SensorDeviceClass.TEMPERATURE
        if sub_key == "H":
            return SensorDeviceClass.HUMIDITY
        if sub_key == "Z":
            return SensorDeviceClass.ILLUMINANCE
        if sub_key == "V":
            return SensorDeviceClass.VOLTAGE

        # TVOC 传感器的设备
        if device_type in ENVIRONMENT_SENSOR_TYPES:
            if device_type == "SL_SC_CQ":
                return SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS
            if device_type == "SL_SC_CA":
                return SensorDeviceClass.CO2
            if device_type == "SL_SC_CH":
                return SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS  # 甲醛也属于VOC

        # 计量插座特殊处理
        if device_type in POWER_METER_PLUG_TYPES:
            if sub_key == "P2":
                return SensorDeviceClass.ENERGY
            if sub_key == "P3":
                return SensorDeviceClass.POWER

        # 智能插座的电压、电流、功率等传感器
        if device_type in SMART_PLUG_TYPES:
            if sub_key == "EV":
                return SensorDeviceClass.VOLTAGE
            if sub_key == "EI":
                return SensorDeviceClass.CURRENT
            if sub_key == "EP":
                return SensorDeviceClass.POWER
            if sub_key == "EPA":
                return SensorDeviceClass.ENERGY

        # 噪音感应器
        if device_type in NOISE_SENSOR_TYPES and sub_key == "P1":
            return SensorDeviceClass.SOUND_PRESSURE  # 噪音等级

        # 电量计量器
        if device_type in POWER_METER_TYPES:
            if sub_key in {"EPA", "EP"}:
                return SensorDeviceClass.POWER
            if sub_key == "EE":
                return SensorDeviceClass.ENERGY

        # 云防系列的温度传感器
        if device_type in DEFED_SENSOR_TYPES and sub_key == "T":
            return SensorDeviceClass.TEMPERATURE

        # 环境感应器（EV系列）
        if device_type in EV_SENSOR_TYPES:
            if sub_key == "T":
                return SensorDeviceClass.TEMPERATURE
            if sub_key == "H":
                return SensorDeviceClass.HUMIDITY
            if sub_key == "V":
                return SensorDeviceClass.VOLTAGE
            if sub_key == "Z":
                return SensorDeviceClass.ILLUMINANCE
            if device_type in ENVIRONMENT_SENSOR_TYPES and device_type != "SL_SC_CH":
                if sub_key == "P1":
                    return SensorDeviceClass.TEMPERATURE
                if sub_key == "P2":
                    return SensorDeviceClass.HUMIDITY

        # 插座开关等电量传感器
        if (device_type in SUPPORTED_SWITCH_TYPES and sub_key == "P4") or (
            device_type == "SL_SC_BB_V2" and sub_key == "P2"
        ):
            return SensorDeviceClass.BATTERY

        return None

    @callback
    def _determine_unit(self) -> str | None:
        """Map sub-device to unit."""
        device_type = self._raw_device[DEVICE_TYPE_KEY]
        sub_key = self._sub_key

        if self.device_class == SensorDeviceClass.BATTERY:
            return PERCENTAGE
        if self.device_class == SensorDeviceClass.TEMPERATURE:
            return UnitOfTemperature.CELSIUS
        if self.device_class == SensorDeviceClass.HUMIDITY:
            return PERCENTAGE
        if self.device_class == SensorDeviceClass.ILLUMINANCE:
            return LIGHT_LUX
        if self.device_class == SensorDeviceClass.VOLTAGE:
            return UnitOfElectricPotential.VOLT
        if self.device_class == SensorDeviceClass.CURRENT:
            return UnitOfElectricCurrent.AMPERE
        if self.device_class == SensorDeviceClass.POWER:
            return UnitOfPower.WATT
        if self.device_class == SensorDeviceClass.ENERGY:
            return UnitOfEnergy.KILO_WATT_HOUR
        if self.device_class == SensorDeviceClass.PM25:
            return CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
        if self.device_class == SensorDeviceClass.CO2:
            return CONCENTRATION_PARTS_PER_MILLION
        if self.device_class == SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS:
            return CONCENTRATION_MICROGRAMS_PER_CUBIC_METER
        if self.device_class == SensorDeviceClass.SOUND_PRESSURE:
            return UnitOfSoundPressure.DECIBEL

        # 燃气浓度单位
        if device_type in GAS_SENSOR_TYPES and sub_key == "P1":
            return CONCENTRATION_PARTS_PER_MILLION  # 一般为甲烷等气体

        return None

    @callback
    def _determine_state_class(self) -> SensorStateClass | None:
        """Determine state class for long-term statistics."""
        # 为传感器设置状态类别，以支持历史图表
        if self.device_class in {
            SensorDeviceClass.TEMPERATURE,
            SensorDeviceClass.HUMIDITY,
            SensorDeviceClass.ILLUMINANCE,
            SensorDeviceClass.POWER,
            SensorDeviceClass.CO2,
            SensorDeviceClass.PM25,
            SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
            SensorDeviceClass.SOUND_PRESSURE,
            SensorDeviceClass.BATTERY,
            SensorDeviceClass.VOLTAGE,
        }:
            return SensorStateClass.MEASUREMENT
        if self.device_class == SensorDeviceClass.ENERGY:
            return SensorStateClass.TOTAL_INCREASING
        return None

    @callback
    def _extract_initial_value(self) -> float | int | None:
        """Extract initial value from device data."""
        # 优先使用友好值
        value = self._sub_data.get("v")
        if value is not None:
            return value

        # 使用原始值并进行必要的转换
        raw_value = self._sub_data.get("val")
        if raw_value is not None:
            return self._convert_raw_value(raw_value)

        return None

    @callback
    def _convert_raw_value(self, raw_value: int) -> float | int:
        """Convert raw value to actual value based on device type."""
        device_type = self._raw_device[DEVICE_TYPE_KEY]

        # 温度值通常需要除以10
        if (
            self._sub_key in {"T", "P1"}
            and self.device_class == SensorDeviceClass.TEMPERATURE
        ):
            return raw_value / 10.0

        # 湿度值需要除以10
        if (
            self._sub_key in {"H", "P2"}
            and self.device_class == SensorDeviceClass.HUMIDITY
        ):
            return raw_value / 10.0

        # CO2传感器的P1(温度)和P2(湿度)也需要除以10
        if device_type in EV_SENSOR_TYPES:
            if self._sub_key == "P1":  # 温度
                return raw_value / 10.0
            if self._sub_key == "P2":  # 湿度
                return raw_value / 10.0

        if device_type in CLIMATE_TYPES:
            # 地暖底板温度和新风VOC都需要除以10
            if (device_type == "SL_CP_DN" and self._sub_key == "P5") or (
                device_type == "SL_TR_ACIPM" and self._sub_key == "P4"
            ):
                return raw_value / 10.0
            # 其他值（如电量、PM2.5）直接使用
            return raw_value

        # 电量百分比值直接使用
        if self._sub_key in {"BAT", "V", "P4", "P5"}:
            return raw_value

        # 其他值直接返回
        return raw_value

    @callback
    def _get_extra_attributes(self) -> dict[str, Any] | None:
        """Get extra state attributes."""
        device_type = self._raw_device[DEVICE_TYPE_KEY]

        # CO2传感器的空气质量等级
        if device_type == "SL_SC_CA" and self._sub_key == "P3":
            val = self._sub_data.get("val", 0)
            return {"air_quality": val}

        # 水浸传感器的导电率等级
        if device_type in WATER_SENSOR_TYPES and self._sub_key == "WA":
            val = self._sub_data.get("val", 0)
            return {"conductivity_level": val}

        return None

    @property
    def device_info(self) -> DeviceInfo:
        """返回设备信息以链接实体到单个设备。"""
        # 从 self._raw_device 中安全地获取 hub_id 和 device_id
        hub_id = self._raw_device.get(HUB_ID_KEY)
        device_id = self._raw_device.get(DEVICE_ID_KEY)

        # 确保 identifiers 即使在 hub_id 或 device_id 为 None 的情况下也不会出错
        identifiers = set()
        if hub_id and device_id:
            identifiers.add((DOMAIN, hub_id, device_id))

        return DeviceInfo(
            identifiers=identifiers,
            name=self._raw_device.get(
                DEVICE_NAME_KEY, "Unnamed Device"
            ),  # 安全获取名称
            manufacturer=MANUFACTURER,
            model=self._raw_device.get(DEVICE_TYPE_KEY),  # 安全获取型号
            sw_version=self._raw_device.get(DEVICE_VERSION_KEY, "unknown"),
            via_device=((DOMAIN, hub_id) if hub_id else None),
        )

    async def async_added_to_hass(self) -> None:
        """Register update listeners."""
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
        """Handle real-time updates."""
        try:
            # 处理WebSocket推送的数据格式
            if "msg" in new_data:
                sub_data = new_data.get("msg", {}).get(self._sub_key, {})
                val = sub_data.get("v") or sub_data.get("val")
            else:
                val = new_data.get("v") or new_data.get("val")

            if val is not None:
                self._attr_native_value = (
                    self._convert_raw_value(val) if "v" not in new_data else val
                )
                self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error("Error handling update for %s: %s", self._attr_unique_id, e)

    async def _handle_global_refresh(self) -> None:
        """Handle periodic full data refresh."""
        # 从hass.data获取最新设备列表
        devices = self.hass.data[DOMAIN][self._entry_id]["devices"]
        # 查找当前设备
        current_device = next(
            (
                d
                for d in devices
                if d[HUB_ID_KEY] == self.agt and d[DEVICE_ID_KEY] == self.me
            ),
            None,
        )
        if current_device is None:
            _LOGGER.warning(
                "LifeSmartSensor: Device not found during global refresh: %s",
                self._attr_unique_id,
            )
            return

        sub_data = current_device.get(DEVICE_DATA_KEY, {}).get(self._sub_key, {})
        val = sub_data.get("v") or sub_data.get("val")
        if val is not None:
            self._attr_native_value = self._convert_raw_value(val)
            self.async_write_ha_state()
        else:
            _LOGGER.debug(
                "LifeSmartSensor: No value found for sub-device '%s' during global refresh",
                self._sub_key,
            )
