"""Strict Gen2 sensor platform tests."""

from unittest.mock import MagicMock

import pytest
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    LIGHT_LUX,
    PERCENTAGE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.lifesmart.core import const as lifesmart_const
from custom_components.lifesmart.core.data.processors import process_io_data
from custom_components.lifesmart.core.helpers import generate_unique_id
from custom_components.lifesmart.sensor import LifeSmartSensor

from ..utils.constants import TEST_HUB_IDS
from ..utils.helpers import (
    create_mock_hub,
    filter_devices_by_hub,
    get_hub_id,
    group_devices_by_hub,
    validate_device_data,
)


def _sensor_platform_devices():
    """Deterministic strict Gen2 sensor devices used by this platform file."""
    return [
        {
            "agt": get_hub_id(5),
            "me": "SL_SC_THL",
            "devtype": "SL_SC_THL",
            "name": "Living Room Env",
            "data": {
                "T": {"v": 25.5, "val": 255},
                "H": {"v": 60.1, "val": 601},
                "Z": {"v": 1000, "val": 1000},
                "V": {"v": 95, "val": 95},
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        {
            "agt": get_hub_id(1),
            "me": "4c7d",
            "devtype": "SL_OE_3C",
            "name": "Washing Machine Plug",
            "data": {
                "P1": {"type": lifesmart_const.CMD_TYPE_ON, "val": 1},
                "P2": {"v": 1.5, "val": 1069547520},
                "P3": {"v": 1200.0, "val": 1150681088},
                "P4": {"type": lifesmart_const.CMD_TYPE_OFF, "val": 3000},
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        {
            "agt": get_hub_id(6),
            "me": "SL_LK_LS",
            "devtype": "SL_LK_LS",
            "name": "Main Lock",
            "data": {
                "EVTLO": {"val": 4121, "type": 1},
                "ALM": {"val": 2},
                "BAT": {"val": 88},
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        {
            "agt": get_hub_id(2),
            "me": "sensor_co2",
            "devtype": "SL_SC_CA",
            "name": "Study CO2",
            "data": {
                "P1": {"v": 22.0, "val": 220},
                "P2": {"v": 50, "val": 500},
                "P3": {"v": 800, "val": 80},
                "P4": {"v": 90, "val": 90},
                "P5": {"val": 5},
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
        {
            "agt": get_hub_id(3),
            "me": "boundary_test_sensor",
            "devtype": "SL_SC_THL",
            "name": "Boundary Test Sensor",
            "data": {
                "T": {"val": 0},
                "H": {"v": None, "val": None},
                "Z": {"v": None, "val": None},
                "V": {"v": 0, "val": 0},
            },
            "stat": 1,
            "ver": "0.0.0.7",
        },
    ]


def create_gen2_devices(_gen2_keys=None):
    """Return this file's deterministic Gen2 sensor set for legacy lookups."""
    return _sensor_platform_devices()


@pytest.fixture
async def setup_integration_sensor_only(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client,
    mock_hub_class,
):
    """File-local Gen2 sensor setup with unique supported devices only."""
    devices = _sensor_platform_devices()
    mock_config_entry.add_to_hass(hass)
    mock_hub_class.return_value = create_mock_hub(devices, mock_client)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED
    yield mock_config_entry

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED


def _device_by_me(me: str) -> dict:
    return next(device for device in _sensor_platform_devices() if device["me"] == me)


def _unique_id_for(me: str, sub_key: str) -> str:
    device = _device_by_me(me)
    return generate_unique_id(
        device[lifesmart_const.DEVICE_TYPE_KEY],
        device[lifesmart_const.HUB_ID_KEY],
        device[lifesmart_const.DEVICE_ID_KEY],
        sub_key,
    )


class TestSensorSetup:
    """Strict Gen2 sensor setup behavior."""

    @pytest.mark.asyncio
    async def test_setup_creates_current_gen2_sensor_entities(
        self,
        hass: HomeAssistant,
        setup_integration_sensor_only: ConfigEntry,
    ):
        devices = _sensor_platform_devices()
        for device in devices:
            validate_device_data(device)

        grouped_devices = group_devices_by_hub(devices)
        assert grouped_devices
        for hub_index in range(len(TEST_HUB_IDS)):
            assert isinstance(filter_devices_by_hub(devices, hub_index), list)

        assert len(hass.states.async_entity_ids("sensor")) == 18

        entity_registry = er.async_get(hass)
        created_entities = {
            entry.entity_id
            for entry in entity_registry.entities.values()
            if entry.platform == lifesmart_const.DOMAIN and entry.domain == "sensor"
        }
        assert {
            "sensor.living_room_env_t",
            "sensor.living_room_env_h",
            "sensor.living_room_env_z",
            "sensor.living_room_env_v",
            "sensor.study_co2_p1",
            "sensor.study_co2_p2",
            "sensor.study_co2_p3",
            "sensor.study_co2_p4",
            "sensor.study_co2_p5",
            "sensor.washing_machine_plug_p2",
            "sensor.washing_machine_plug_p3",
            "sensor.main_lock_bat",
            "sensor.boundary_test_sensor_t",
            "sensor.boundary_test_sensor_h",
            "sensor.boundary_test_sensor_z",
            "sensor.boundary_test_sensor_v",
        }.issubset(created_entities)

    @pytest.mark.asyncio
    async def test_setup_does_not_create_absent_or_excluded_entities(
        self,
        hass: HomeAssistant,
        setup_integration_sensor_only: ConfigEntry,
    ):
        entity_registry = er.async_get(hass)
        absent_unique_id = generate_unique_id(
            "SL_SC_THL",
            "excluded_hub",
            "excluded_device",
            "T",
        )
        assert (
            entity_registry.async_get_entity_id(
                "sensor", lifesmart_const.DOMAIN, absent_unique_id
            )
            is None
        )
        assert hass.states.get("sensor.legacy_unknown_sensor_t") is None


class TestSensorEntity:
    """Core Gen2 sensor entity behavior restored without broad skip."""

    @pytest.mark.parametrize(
        (
            "entity_id, expected_name, expected_class, expected_unit, "
            "expected_state_class, expected_value"
        ),
        [
            (
                "sensor.living_room_env_t",
                "Living Room Env T",
                SensorDeviceClass.TEMPERATURE,
                UnitOfTemperature.CELSIUS,
                SensorStateClass.MEASUREMENT,
                25.5,
            ),
            (
                "sensor.living_room_env_h",
                "Living Room Env H",
                SensorDeviceClass.HUMIDITY,
                PERCENTAGE,
                SensorStateClass.MEASUREMENT,
                60.1,
            ),
            (
                "sensor.living_room_env_z",
                "Living Room Env Z",
                SensorDeviceClass.ILLUMINANCE,
                LIGHT_LUX,
                SensorStateClass.MEASUREMENT,
                1000,
            ),
            (
                "sensor.living_room_env_v",
                "Living Room Env V",
                SensorDeviceClass.BATTERY,
                PERCENTAGE,
                SensorStateClass.MEASUREMENT,
                95,
            ),
            (
                "sensor.main_lock_bat",
                "Main Lock BAT",
                SensorDeviceClass.BATTERY,
                PERCENTAGE,
                SensorStateClass.MEASUREMENT,
                88,
            ),
            (
                "sensor.washing_machine_plug_p2",
                "Washing Machine Plug P2",
                SensorDeviceClass.ENERGY,
                UnitOfEnergy.KILO_WATT_HOUR,
                SensorStateClass.TOTAL_INCREASING,
                1.5,
            ),
            (
                "sensor.washing_machine_plug_p3",
                "Washing Machine Plug P3",
                SensorDeviceClass.POWER,
                UnitOfPower.WATT,
                SensorStateClass.MEASUREMENT,
                1200,
            ),
            (
                "sensor.study_co2_p3",
                "Study CO2 P3",
                SensorDeviceClass.CO2,
                CONCENTRATION_PARTS_PER_MILLION,
                SensorStateClass.MEASUREMENT,
                800,
            ),
        ],
        ids=[
            "temperature",
            "humidity",
            "illuminance",
            "battery-env",
            "battery-lock",
            "energy-ieee754",
            "power-ieee754",
            "co2-scaled",
        ],
    )
    @pytest.mark.asyncio
    async def test_sensor_properties_and_initial_state(
        self,
        hass: HomeAssistant,
        setup_integration_sensor_only: ConfigEntry,
        entity_id,
        expected_name,
        expected_class,
        expected_unit,
        expected_state_class,
        expected_value,
    ):
        state = hass.states.get(entity_id)
        assert state is not None, f"entity {entity_id} should exist"
        assert state.name == expected_name
        assert state.attributes.get("device_class") == expected_class.value
        assert state.attributes.get("state_class") == expected_state_class.value
        assert state.attributes.get("unit_of_measurement") == expected_unit
        assert float(state.state) == pytest.approx(expected_value)

    @pytest.mark.asyncio
    async def test_sensor_boundary_and_invalid_data(
        self, hass: HomeAssistant, setup_integration_sensor_only: ConfigEntry
    ):
        assert float(hass.states.get("sensor.boundary_test_sensor_t").state) == 0.0
        assert hass.states.get("sensor.boundary_test_sensor_h").state == STATE_UNKNOWN
        assert hass.states.get("sensor.boundary_test_sensor_z").state == STATE_UNKNOWN
        assert float(hass.states.get("sensor.boundary_test_sensor_v").state) == 0.0

    @pytest.mark.asyncio
    async def test_sensor_becomes_unavailable_on_global_refresh_missing_device(
        self, hass: HomeAssistant, setup_integration_sensor_only: ConfigEntry
    ):
        entity_id = "sensor.living_room_env_t"
        assert hass.states.get(entity_id).state != STATE_UNAVAILABLE

        domain_data = hass.data[lifesmart_const.DOMAIN][
            setup_integration_sensor_only.entry_id
        ]
        devices = domain_data["devices"]
        domain_data["devices"] = [
            device for device in devices if device.get("me") != "SL_SC_THL"
        ]

        async_dispatcher_send(hass, lifesmart_const.LIFESMART_SIGNAL_UPDATE_ENTITY)
        await hass.async_block_till_done()

        assert hass.states.get(entity_id).state == STATE_UNAVAILABLE

    @pytest.mark.parametrize(
        "entity_id, me, sub_key, initial_value, update_payload, expected_value",
        [
            (
                "sensor.living_room_env_t",
                "SL_SC_THL",
                "T",
                25.5,
                {"val": 288},
                28.8,
            ),
            (
                "sensor.washing_machine_plug_p3",
                "4c7d",
                "P3",
                1200,
                {"val": 1153142784},
                1500.5,
            ),
            (
                "sensor.main_lock_bat",
                "SL_LK_LS",
                "BAT",
                88,
                {"val": 50},
                50,
            ),
            (
                "sensor.study_co2_p3",
                "sensor_co2",
                "P3",
                800,
                {"v": 810, "val": 81},
                810,
            ),
        ],
        ids=["temperature-val", "power-ieee-val", "battery-val", "co2-v-final"],
    )
    @pytest.mark.asyncio
    async def test_sensor_update_from_dispatcher(
        self,
        hass: HomeAssistant,
        setup_integration_sensor_only: ConfigEntry,
        entity_id,
        me,
        sub_key,
        initial_value,
        update_payload,
        expected_value,
    ):
        assert float(hass.states.get(entity_id).state) == pytest.approx(initial_value)

        async_dispatcher_send(
            hass,
            (
                f"{lifesmart_const.LIFESMART_SIGNAL_UPDATE_ENTITY}_"
                f"{_unique_id_for(me, sub_key)}"
            ),
            update_payload,
        )
        await hass.async_block_till_done()

        assert float(hass.states.get(entity_id).state) == pytest.approx(expected_value)

    @pytest.mark.asyncio
    async def test_sensor_update_accepts_nested_msg_format(
        self, hass: HomeAssistant, setup_integration_sensor_only: ConfigEntry
    ):
        async_dispatcher_send(
            hass,
            (
                f"{lifesmart_const.LIFESMART_SIGNAL_UPDATE_ENTITY}_"
                f"{_unique_id_for('SL_SC_THL', 'T')}"
            ),
            {"msg": {"T": {"val": 301}}},
        )
        await hass.async_block_till_done()

        assert float(hass.states.get("sensor.living_room_env_t").state) == 30.1

    @pytest.mark.asyncio
    async def test_sensor_invalid_and_empty_updates_keep_previous_state(
        self, hass: HomeAssistant, setup_integration_sensor_only: ConfigEntry
    ):
        entity_id = "sensor.living_room_env_t"
        signal = (
            f"{lifesmart_const.LIFESMART_SIGNAL_UPDATE_ENTITY}_"
            f"{_unique_id_for('SL_SC_THL', 'T')}"
        )
        assert float(hass.states.get(entity_id).state) == 25.5

        async_dispatcher_send(hass, signal, {"v": "invalid_float"})
        await hass.async_block_till_done()
        assert float(hass.states.get(entity_id).state) == 25.5

        async_dispatcher_send(hass, signal, {})
        await hass.async_block_till_done()
        assert float(hass.states.get(entity_id).state) == 25.5

    @pytest.mark.asyncio
    async def test_global_refresh_missing_subdevice_marks_unavailable(
        self, hass: HomeAssistant, setup_integration_sensor_only: ConfigEntry
    ):
        entity_id = "sensor.living_room_env_h"
        devices = hass.data[lifesmart_const.DOMAIN][
            setup_integration_sensor_only.entry_id
        ]["devices"]
        env_device = next(device for device in devices if device["me"] == "SL_SC_THL")
        env_device["data"].pop("H")

        async_dispatcher_send(hass, lifesmart_const.LIFESMART_SIGNAL_UPDATE_ENTITY)
        await hass.async_block_till_done()

        assert hass.states.get(entity_id).state == STATE_UNAVAILABLE

    def test_unknown_sensor_config_raises_strict_error(self):
        device = {
            "agt": "hub1",
            "me": "unknown_sensor",
            "devtype": "UNKNOWN_SENSOR",
            "name": "Unknown Sensor",
            "data": {"T": {"val": 25}},
            "stat": 1,
        }
        with pytest.raises(HomeAssistantError, match="Unknown device type"):
            LifeSmartSensor(device, MagicMock(), "entry-id", "T", {"val": 25})


def test_ieee754_float_processor_decodes_raw_val_not_human_v():
    io_config = {"conversion": "ieee754_float"}
    assert process_io_data(
        io_config, {"v": 9999, "val": 1069547520}
    ) == pytest.approx(1.5)
    assert process_io_data(
        io_config, {"v": 1200.0, "val": 1150681088}
    ) == pytest.approx(
        1200.0,
    )
    assert process_io_data(io_config, {"v": 1.5}) is None


def test_co2_scaled_processor_uses_final_v_and_scales_raw_val_fallback():
    io_config = {"conversion": "co2_scaled"}
    assert process_io_data(io_config, {"v": 800, "val": 800}) == 800
    assert process_io_data(io_config, {"val": 80}) == 800
    assert process_io_data(io_config, {"val": 5}) == 500
    assert process_io_data(io_config, {"v": "bad", "val": 80}) is None
