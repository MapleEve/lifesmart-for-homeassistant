"""测试 LifeSmart 数值传感器组件的功能。"""

from unittest.mock import AsyncMock

import pytest
from homeassistant.components.sensor import (
    DOMAIN as SENSOR_DOMAIN,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfPower,
    UnitOfEnergy,
    LIGHT_LUX,
    UnitOfElectricPotential,
    CONCENTRATION_PARTS_PER_MILLION,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.lifesmart.const import DOMAIN, LIFESMART_SIGNAL_UPDATE_ENTITY
from custom_components.lifesmart.sensor import LifeSmartSensor, async_setup_entry

# --- Mock 设备数据 ---

# 模拟一个环境感应器 (温、湿、光、电)
MOCK_EV_SENSOR = {
    "agt": "mock_hub_1",
    "me": "ev_sensor_me",
    "devtype": "SL_SC_THL",
    "name": "Living Room Env",
    "data": {
        "T": {"v": 25.5, "val": 255},  # 温度，优先使用 v
        "H": {"val": 552},  # 湿度，没有 v，测试 val/10
        "Z": {"val": 1000},  # 光照
        "V": {"val": 95},  # 电量
    },
}

# 模拟一个CO2感应器
MOCK_CO2_SENSOR = {
    "agt": "mock_hub_1",
    "me": "co2_sensor_me",
    "devtype": "SL_SC_CA",
    "name": "Study CO2",
    "data": {
        "P1": {"v": 22.1, "val": 221},  # 温度
        "P3": {"v": 850, "val": 850},  # CO2浓度
        "P4": {"val": 88},  # 电量
    },
}

# 模拟一个计量插座
MOCK_POWER_METER_PLUG = {
    "agt": "mock_hub_1",
    "me": "plug_me",
    "devtype": "SL_OE_3C",
    "name": "Kitchen Plug",
    "data": {
        "P1": {"type": 129, "val": 1},  # 开关状态，不应创建sensor
        "P2": {"v": 12.34, "val": 1234},  # 累计电量 (kWh)
        "P3": {"v": 150.5, "val": 1505},  # 当前功率 (W)
    },
}

# 模拟一个带电量反馈的开关
MOCK_SWITCH_WITH_BATTERY = {
    "agt": "mock_hub_1",
    "me": "switch_me",
    "devtype": "SL_SW_ND1",
    "name": "Bedroom Switch",
    "data": {
        "L1": {"type": 128, "val": 0},  # 开关状态
        "P4": {"val": 75},  # 电量
    },
}

# 模拟一个被排除的设备
MOCK_EXCLUDED_SENSOR = {
    "agt": "mock_hub_1",
    "me": "excluded_me",
    "devtype": "SL_SC_THL",
    "name": "Excluded Sensor",
    "data": {"T": {"v": 20.0, "val": 200}},
}


@pytest.mark.asyncio
async def test_async_setup_entry(
    hass: HomeAssistant, mock_lifesmart_client, mock_config_entry
):
    """测试传感器的 async_setup_entry 函数。"""
    mock_devices = [
        MOCK_EV_SENSOR,
        MOCK_CO2_SENSOR,
        MOCK_POWER_METER_PLUG,
        MOCK_SWITCH_WITH_BATTERY,
        MOCK_EXCLUDED_SENSOR,
    ]
    hass.data[DOMAIN][mock_config_entry.entry_id] = {
        "client": mock_lifesmart_client,
        "devices": mock_devices,
        "exclude_devices": "excluded_me",  # 排除一个设备
        "exclude_hubs": "",
    }

    async_add_entities = AsyncMock()
    await async_setup_entry(hass, mock_config_entry, async_add_entities)

    # 验证是否创建了正确数量的实体
    # EV_SENSOR (4) + CO2_SENSOR (3) + POWER_METER_PLUG (2) + SWITCH_WITH_BATTERY (1) = 10
    assert async_add_entities.call_count == 1
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 10

    # 验证被排除的设备没有创建实体
    entity_ids = [e.unique_id for e in entities]
    assert f"{SENSOR_DOMAIN}.sl_sc_thl_mock_hub_1_excluded_me_t" not in entity_ids


@pytest.mark.parametrize(
    "device_data, sub_key, expected_name, expected_class, expected_unit, expected_state_class, expected_value",
    [
        # 环境感应器测试
        (
            MOCK_EV_SENSOR,
            "T",
            "Living Room Env T",
            SensorDeviceClass.TEMPERATURE,
            UnitOfTemperature.CELSIUS,
            SensorStateClass.MEASUREMENT,
            25.5,
        ),
        (
            MOCK_EV_SENSOR,
            "H",
            "Living Room Env H",
            SensorDeviceClass.HUMIDITY,
            PERCENTAGE,
            SensorStateClass.MEASUREMENT,
            55.2,  # 测试 val/10 的逻辑
        ),
        (
            MOCK_EV_SENSOR,
            "Z",
            "Living Room Env Z",
            SensorDeviceClass.ILLUMINANCE,
            LIGHT_LUX,
            SensorStateClass.MEASUREMENT,
            1000,
        ),
        (
            MOCK_EV_SENSOR,
            "V",
            "Living Room Env V",
            SensorDeviceClass.VOLTAGE,
            UnitOfElectricPotential.VOLT,
            SensorStateClass.MEASUREMENT,
            95,  # 电压类传感器 val 通常是原始值，sensor.py 中应直接使用
        ),
        # CO2 感应器测试
        (
            MOCK_CO2_SENSOR,
            "P3",
            "Study CO2 P3",
            SensorDeviceClass.CO2,
            CONCENTRATION_PARTS_PER_MILLION,
            SensorStateClass.MEASUREMENT,
            850,
        ),
        # 计量插座测试
        (
            MOCK_POWER_METER_PLUG,
            "P2",
            "Kitchen Plug P2",
            SensorDeviceClass.ENERGY,
            UnitOfEnergy.KILO_WATT_HOUR,
            SensorStateClass.TOTAL_INCREASING,
            12.34,
        ),
        (
            MOCK_POWER_METER_PLUG,
            "P3",
            "Kitchen Plug P3",
            SensorDeviceClass.POWER,
            UnitOfPower.WATT,
            SensorStateClass.MEASUREMENT,
            150.5,
        ),
        # 带电量反馈的开关测试
        (
            MOCK_SWITCH_WITH_BATTERY,
            "P4",
            "Bedroom Switch P4",
            SensorDeviceClass.BATTERY,
            PERCENTAGE,
            SensorStateClass.MEASUREMENT,
            75,
        ),
    ],
)
@pytest.mark.asyncio
async def test_sensor_initialization(
    hass: HomeAssistant,
    device_data,
    sub_key,
    expected_name,
    expected_class,
    expected_unit,
    expected_state_class,
    expected_value,
):
    """测试不同类型传感器的初始化属性和状态。"""
    entity = LifeSmartSensor(
        device=AsyncMock(),
        raw_device=device_data,
        sub_device_key=sub_key,
        sub_device_data=device_data["data"][sub_key],
        client=AsyncMock(),
        entry_id="mock_entry_id",
    )
    entity.hass = hass

    assert entity.name == expected_name
    assert entity.device_class == expected_class
    assert entity.native_unit_of_measurement == expected_unit
    assert entity.state_class == expected_state_class
    assert entity.native_value == expected_value
    assert (
        entity.unique_id
        == f"{SENSOR_DOMAIN}.{device_data['devtype'].lower()}_{device_data['agt']}_{device_data['me']}_{sub_key.lower()}"
    )


def test_value_conversion():
    """单独测试 _convert_raw_value 方法的转换逻辑。"""
    # 创建一个虚拟的传感器实例来调用方法
    dummy_sensor = LifeSmartSensor(
        device=AsyncMock(),
        raw_device={"devtype": "SL_SC_THL", "agt": "", "me": ""},
        sub_device_key="T",
        sub_device_data={},
        client=AsyncMock(),
        entry_id="",
    )

    # 测试温度转换
    dummy_sensor._sub_key = "T"
    dummy_sensor._attr_device_class = SensorDeviceClass.TEMPERATURE
    assert dummy_sensor._convert_raw_value(255) == 25.5
    assert dummy_sensor._convert_raw_value(-10) == -1.0

    # 测试湿度转换
    dummy_sensor._sub_key = "H"
    dummy_sensor._attr_device_class = SensorDeviceClass.HUMIDITY
    assert dummy_sensor._convert_raw_value(552) == 55.2

    # 测试不需要转换的值
    dummy_sensor._sub_key = "Z"
    dummy_sensor._attr_device_class = SensorDeviceClass.ILLUMINANCE
    assert dummy_sensor._convert_raw_value(1000) == 1000

    # 测试地暖底板温度
    dummy_sensor._raw_device["devtype"] = "SL_CP_DN"
    dummy_sensor._sub_key = "P5"
    dummy_sensor._attr_device_class = SensorDeviceClass.TEMPERATURE
    assert dummy_sensor._convert_raw_value(350) == 35.0


@pytest.mark.asyncio
async def test_sensor_update_via_dispatcher(hass: HomeAssistant):
    """测试通过 dispatcher 更新传感器状态。"""
    entity = LifeSmartSensor(
        device=AsyncMock(),
        raw_device=MOCK_EV_SENSOR,
        sub_device_key="T",
        sub_device_data=MOCK_EV_SENSOR["data"]["T"],
        client=AsyncMock(),
        entry_id="mock_entry_id",
    )
    entity.hass = hass
    # 初始状态
    assert entity.native_value == 25.5

    # 模拟添加到 HASS 以注册监听器
    await entity.async_added_to_hass()

    # 模拟 WebSocket 推送一个新状态 (使用 v)
    update_data_v = {"v": 26.1, "val": 261}
    async_dispatcher_send(
        hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity.unique_id}", update_data_v
    )
    await hass.async_block_till_done()

    # 验证状态已更新
    assert entity.native_value == 26.1

    # 模拟 WebSocket 推送一个新状态 (只使用 val)
    update_data_val = {"val": 248}
    async_dispatcher_send(
        hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity.unique_id}", update_data_val
    )
    await hass.async_block_till_done()

    # 验证状态已更新并正确转换
    assert entity.native_value == 24.8
