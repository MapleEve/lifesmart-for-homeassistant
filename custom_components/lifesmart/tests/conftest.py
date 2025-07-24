"""
共享的 pytest fixtures，用于 LifeSmart 集成测试。
"""

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_REGION
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.lifesmart import async_setup_entry
from custom_components.lifesmart.const import *

# 自动为所有测试加载 Home Assistant 的 pytest 插件
pytest_plugins = "pytest_homeassistant_custom_component"


# --- 统一的模拟配置 ---
@pytest.fixture(name="mock_config_data")
def mock_config_data_fixture():
    """提供标准的模拟配置数据。"""
    return {
        CONF_LIFESMART_APPKEY: "mock_appkey",
        CONF_LIFESMART_APPTOKEN: "mock_apptoken",
        CONF_LIFESMART_USERID: "mock_userid",
        CONF_LIFESMART_USERTOKEN: "mock_usertoken",
        CONF_REGION: "cn2",
    }


# --- 统一的模拟设备列表 ---
@pytest.fixture(name="mock_lifesmart_devices")
def mock_lifesmart_devices_fixture():
    """一个全面的模拟设备列表，覆盖所有平台的测试需求。"""
    return [
        # --- Switch Devices ---
        {
            "agt": "hub_sw",
            "me": "sw_if3",
            "devtype": "SL_SW_IF3",
            "name": "3-Gang Switch",
            "data": {"L1": {"type": 129}, "L2": {"type": 128}, "L3": {"type": 129}},
        },
        {
            "agt": "hub_sw",
            "me": "sw_ol",
            "devtype": "SL_OL",
            "name": "Smart Outlet",
            "data": {"O": {"type": 129}},
        },
        {
            "agt": "hub_sw_excluded",
            "me": "sw_oe3c",
            "devtype": "SL_OE_3C",
            "name": "Power Plug",
            "data": {"P1": {"type": 129}, "P4": {"type": 128}},
        },
        {
            "agt": "hub_sw",
            "me": "sw_nature",
            "devtype": "SL_NATURE",
            "name": "Nature Panel Switch",
            "data": {
                "P1": {"type": 129},
                "P2": {"type": 128},
                "P3": {"type": 129},
                "P5": {"val": 1},
            },
        },
        # --- Light Devices ---
        {
            "agt": "hub_light",
            "me": "light_bright",
            "devtype": "SL_SPWM",
            "name": "Brightness Light",
            "data": {"P1": {"type": 129, "val": 100}},
        },
        {
            "agt": "hub_light",
            "me": "light_dimmer",
            "devtype": "SL_LI_WW_V2",
            "name": "Dimmer Light",
            "data": {"P1": {"type": 129, "val": 100}, "P2": {"val": 27}},
        },
        {
            "agt": "hub_light",
            "me": "light_quantum",
            "devtype": "OD_WE_QUAN",
            "name": "Quantum Light",
            "data": {"P1": {"type": 129}, "P2": {"val": "some_effect_id"}},
        },
        {
            "agt": "hub_light",
            "me": "light_singlergb",
            "devtype": "SL_SC_RGB",
            "name": "Single IO RGB Light",
            "data": {"RGB": {"val": 0x64010203}},
        },
        {
            "agt": "hub_light",
            "me": "light_dualrgbw",
            "devtype": "SL_CT_RGBW",
            "name": "Dual IO RGBW Light",
            "data": {"RGBW": {"type": 129}, "DYN": {}},
        },
        {
            "agt": "hub_light",
            "me": "light_spotrgb",
            "devtype": "SL_SPOT",
            "name": "SPOT RGB Light",
            "data": {"RGB": {"val": 0xFF8040}},
        },
        {
            "agt": "hub_light",
            "me": "light_spotrgbw",
            "devtype": "MSL_IRCTL",
            "name": "SPOT RGBW Light",
            "data": {"RGBW": {"val": 0x11223344}, "DYN": {"type": 129}},
        },
        {
            "agt": "hub_light",
            "me": "light_cover",
            "devtype": "SL_ETDOOR",
            "name": "Cover Light",
            "data": {"P1": {"type": 129}},
        },
        {
            "agt": "hub_light",
            "me": "light_generic_hs",
            "devtype": "SL_P",
            "name": "Generic HS Light",
            "data": {"HS": {"val": 255}},
        },
        # --- Binary Sensor Devices ---
        {
            "agt": "hub_bs",
            "me": "bs_door",
            "devtype": "SL_SC_G",
            "name": "Front Door",
            "data": {"G": {"val": 0, "type": 0}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_motion",
            "devtype": "SL_SC_MHW",
            "name": "Living Motion",
            "data": {"M": {"val": 1, "type": 0}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_water",
            "devtype": "SL_SC_WA",
            "name": "Kitchen Water",
            "data": {"WA": {"val": 50, "type": 0}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_defed",
            "devtype": "SL_DF_MM",
            "name": "Garage DEFED",
            "data": {"M": {"val": 1, "type": 129}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_lock",
            "devtype": "SL_LK_LS",
            "name": "Main Lock",
            "data": {"EVTLO": {"val": 4121}, "ALM": {"val": 2}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_smoke",
            "devtype": "SL_P_A",
            "name": "Hallway Smoke",
            "data": {"P1": {"val": 1, "type": 0}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_radar",
            "devtype": "SL_P_RM",
            "name": "Study Occupancy",
            "data": {"P1": {"val": 1, "type": 0}},
        },
        {
            "agt": "hub_bs",
            "me": "bs_button",
            "devtype": "SL_SC_BB_V2",
            "name": "Panic Button",
            "data": {"P1": {"val": 0, "type": 0}},
        },
        # --- Sensor Devices ---
        {
            "agt": "hub_sensor",
            "me": "sensor_env",
            "devtype": "SL_SC_THL",
            "name": "Living Room Env",
            "data": {
                "T": {"v": 25.5},
                "H": {"v": 60.1},
                "Z": {"v": 1000},
                "V": {"val": 95},
            },
        },
        {
            "agt": "hub_sensor",
            "me": "sensor_co2",
            "devtype": "SL_SC_CA",
            "name": "Study CO2",
            "data": {"P3": {"val": 800}},
        },
        {
            "agt": "hub_sensor",
            "me": "sensor_power_plug",
            "devtype": "SL_OE_3C",
            "name": "Washing Machine Plug",
            "data": {"P2": {"v": 1.5}, "P3": {"v": 1200}},
        },
        {
            "agt": "hub_sensor",
            "me": "sensor_lock_battery",
            "devtype": "SL_LK_LS",
            "name": "Main Door Lock",
            "data": {"BAT": {"val": 88}},
        },
        {
            "agt": "hub_sensor",
            "me": "sensor_switch_battery",
            "devtype": "SL_SW_IF1",
            "name": "Bedroom Switch",
            "data": {"P4": {"val": 92}},
        },
        {
            "agt": "hub_sensor",
            "me": "sensor_nature_thermo",
            "devtype": "SL_NATURE",
            "name": "Nature Panel Thermo",
            "data": {"P4": {"val": 235}, "P5": {"val": 3}},
        },
        # --- Cover Devices ---
        {
            "agt": "hub_cover",
            "me": "cover_garage",
            "devtype": "SL_ETDOOR",
            "name": "Garage Door",
            "data": {"P2": {"val": 0, "type": 128}},
        },
        {
            "agt": "hub_cover",
            "me": "cover_dooya",
            "devtype": "SL_DOOYA",
            "name": "Living Room Curtain",
            "data": {"P1": {"val": 100, "type": 128}},
        },
        {
            "agt": "hub_cover",
            "me": "cover_nonpos",
            "devtype": "SL_LI_WW",
            "name": "Bedroom Curtain",
            "data": {"O": {"type": 128}, "C": {"type": 128}},
        },
        # --- Climate Devices ---
        {
            "agt": "hub_climate",
            "me": "climate_nature",
            "devtype": "SL_NATURE",
            "name": "Nature Panel Climate",
            "data": {"P5": {"val": 3}, "P6": {"val": (4 << 6)}},
        },
        {
            "agt": "hub_climate",
            "me": "climate_floor_heat",
            "devtype": "SL_CP_DN",
            "name": "Floor Heating",
            "data": {
                "P1": {"type": 1, "val": 2147483648},
                "P3": {"v": 25.0},
                "P4": {"v": 22.5},
            },
        },
        {
            "agt": "hub_climate",
            "me": "climate_fancoil",
            "devtype": "SL_CP_AIR",
            "name": "Fan Coil Unit",
            "data": {
                "P1": {"type": 1, "val": (1 << 15) | (1 << 13)},
                "P4": {"v": 24.0},
                "P5": {"v": 26.0},
            },
        },
        {
            "agt": "hub_climate",
            "me": "climate_airpanel",
            "devtype": "V_AIR_P",
            "name": "Air Panel",
            "data": {
                "O": {"type": 0},
                "MODE": {"val": 1},
                "F": {"val": 2},
                "T": {"v": 23.0},
                "tT": {"v": 25.0},
            },
        },
        {
            "agt": "hub_climate",
            "me": "climate_airsystem",
            "devtype": "SL_TR_ACIPM",
            "name": "Air System",
            "data": {"P1": {"type": 1, "val": 1}},
        },
        # --- Devices for Exclusion/Special Tests ---
        {
            "agt": "hub_bs",
            "me": "excluded_device",
            "devtype": "SL_SC_G",
            "name": "Excluded Sensor",
            "data": {"G": {"v": 20}},
        },
        {
            "agt": "excluded_hub",
            "me": "device_on_excluded_hub",
            "devtype": "SL_SC_THL",
            "name": "Sensor on Excluded Hub",
            "data": {"T": {"v": 21}},
        },
    ]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """自动为所有测试启用自定义组件集成。"""
    yield


@pytest.fixture
def mock_client(mock_lifesmart_devices):
    """
    提供一个默认的、配置了模拟设备的模拟 LifeSmartClient。
    """
    with patch(
        "custom_components.lifesmart.LifeSmartClient", autospec=True
    ) as mock_client_class:
        client_instance = mock_client_class.return_value
        client_instance.get_all_device_async.return_value = mock_lifesmart_devices
        client_instance.login_async = AsyncMock(
            return_value={
                "usertoken": "mock_new_usertoken",
                "userid": "mock_userid",
                "region": "cn2",
            }
        )
        client_instance.async_refresh_token = AsyncMock(
            return_value={
                "usertoken": "mock_refreshed_usertoken",
                "expiredtime": 9999999999,
            }
        )

        # 模拟所有控制方法
        client_instance.turn_on_light_switch_async = AsyncMock(return_value=0)
        client_instance.turn_off_light_switch_async = AsyncMock(return_value=0)
        client_instance.set_single_ep_async = AsyncMock(return_value=0)
        client_instance.set_multi_eps_async = AsyncMock(return_value=0)
        client_instance.open_cover_async = AsyncMock(return_value=0)
        client_instance.close_cover_async = AsyncMock(return_value=0)
        client_instance.stop_cover_async = AsyncMock(return_value=0)
        client_instance.set_cover_position_async = AsyncMock(return_value=0)
        client_instance.async_set_climate_hvac_mode = AsyncMock(return_value=0)
        client_instance.async_set_climate_fan_mode = AsyncMock(return_value=0)
        client_instance.async_set_climate_temperature = AsyncMock(return_value=0)

        # 模拟后台任务启动/停止
        client.ws_connect = AsyncMock()
        client.ws_disconnect = AsyncMock()

    yield client_instance


@pytest.fixture
def mock_config_entry(mock_config_data) -> MockConfigEntry:
    """提供一个模拟的 ConfigEntry 实例。"""
    return MockConfigEntry(
        domain=DOMAIN,
        data=mock_config_data,
        entry_id="mock_entry_id_12345",
        title="LifeSmart Mock",
        options={},
    )


@pytest.fixture
async def setup_integration(
    hass: HomeAssistant,
    mock_config_entry: ConfigEntry,
    mock_client: AsyncMock,
    mock_lifesmart_devices: list,
):
    """
    一个统一的 fixture，用于完整地设置和加载 LifeSmart 集成及其所有平台。
    """
    # 1. 将模拟配置条目添加到 HASS
    mock_config_entry.add_to_hass(hass)

    # 2. 配置模拟客户端以返回设备
    mock_client.get_all_device_async.return_value = mock_lifesmart_devices

    # 3. Patch LifeSmartClient 的创建过程，使其返回我们的 mock_client
    with patch(
        "custom_components.lifesmart.LifeSmartClient",
        return_value=mock_client,
    ):
        # 4. 运行主集成的 async_setup_entry
        assert await async_setup_entry(hass, mock_config_entry) is True
        # 5. 等待所有后台任务完成，确保平台已加载
        await hass.async_block_till_done()

    # 确保集成状态为 LOADED
    assert mock_config_entry.state == ConfigEntryState.LOADED

    yield mock_config_entry

    # 卸载集成以清理资源，防止任务泄露
    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED
