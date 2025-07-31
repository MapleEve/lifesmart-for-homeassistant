"""
LifeSmart 二元传感器平台单元测试。

此测试套件旨在全面验证 `binary_sensor.py` 的功能，包括：
- 实体是否根据 `conftest.py` 中的模拟设备被正确创建。
- 每个实体的初始状态、设备类别和属性是否正确。
- 实体是否能正确响应实时更新和全局刷新事件。
- 对特殊设备（如门锁、瞬时按钮）的逻辑覆盖。
"""

from datetime import timedelta

import pytest
from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.lifesmart.const import *
from custom_components.lifesmart.helpers import (
    generate_unique_id,
)
from .test_utils import find_test_device


@pytest.mark.asyncio
async def test_all_binary_sensors_created(
    hass: HomeAssistant, setup_integration: ConfigEntry
):
    """
    /**
     * test_all_binary_sensors_created - 验证是否所有预期的二元传感器实体都被创建。
     *
     * 模拟场景:
     *   - 一个完整的集成设置。
     *
     * 预期结果:
     *   - 状态机中应存在所有在 `conftest.py` 中定义的、应被创建为二元传感器的实体。
     */
    """
    assert hass.states.get("binary_sensor.front_door_g") is not None
    assert hass.states.get("binary_sensor.main_lock_evtlo") is not None
    assert hass.states.get("binary_sensor.main_lock_alm") is not None
    assert hass.states.get("binary_sensor.panic_button_p1") is not None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "device_me, sub_key, expected_name_suffix, expected_class, initial_state",
    [
        ("bs_door", "G", "G", BinarySensorDeviceClass.DOOR, STATE_ON),
        ("bs_motion", "M", "M", BinarySensorDeviceClass.MOTION, STATE_ON),
        ("bs_water", "WA", "WA", BinarySensorDeviceClass.MOISTURE, STATE_ON),
        ("bs_defed", "M", "M", BinarySensorDeviceClass.MOTION, STATE_ON),
        ("bs_smoke", "P1", "P1", BinarySensorDeviceClass.SMOKE, STATE_ON),
        ("bs_radar", "P1", "P1", BinarySensorDeviceClass.OCCUPANCY, STATE_ON),
        ("bs_lock", "EVTLO", "EVTLO", BinarySensorDeviceClass.LOCK, STATE_ON),
        ("bs_lock", "ALM", "ALM", BinarySensorDeviceClass.PROBLEM, STATE_ON),
        ("bs_button", "P1", "P1", None, STATE_OFF),
    ],
)
async def test_entity_initialization_and_properties(
    hass: HomeAssistant,
    setup_integration: ConfigEntry,
    mock_lifesmart_devices: list,
    device_me: str,
    sub_key: str,
    expected_name_suffix: str,
    expected_class: BinarySensorDeviceClass | None,
    initial_state: str,
):
    """
    /**
     * test_entity_initialization_and_properties - 验证各种二元传感器的初始化状态和核心属性。
     *
     * 模拟场景:
     *   - 参数化测试，覆盖多种设备类型。
     *
     * 预期结果:
     *   - 每个实体的名称、设备类别、初始状态和 unique_id 都应符合预期。
     */
    """
    device = find_test_device(mock_lifesmart_devices, device_me)
    entity_registry = er.async_get(hass)
    unique_id = generate_unique_id(
        device[DEVICE_TYPE_KEY], device[HUB_ID_KEY], device[DEVICE_ID_KEY], sub_key
    )
    entity_id = entity_registry.async_get_entity_id("binary_sensor", DOMAIN, unique_id)

    assert entity_id is not None, f"实体 for {device_me}-{sub_key} 未在注册表中找到"

    state = hass.states.get(entity_id)
    assert state, f"实体 '{entity_id}' 不存在"
    assert state.name == f"{device['name']} {expected_name_suffix}"
    assert state.attributes.get("device_class") == (
        expected_class.value if expected_class else None
    )
    assert state.state == initial_state


@pytest.mark.asyncio
async def test_lock_attributes(hass: HomeAssistant, setup_integration: ConfigEntry):
    """
    /**
     * test_lock_attributes - 专门测试门锁传感器的附加属性。
     *
     * 模拟场景:
     *   - 检查 `bs_lock` 的 `EVTLO` 实体。
     *
     * 预期结果:
     *   - `unlocking_method` 和 `unlocking_user` 属性应根据初始 `val` (4121) 被正确解析。
     */
    """
    state = hass.states.get("binary_sensor.main_lock_evtlo")
    assert state is not None
    assert state.attributes.get("unlocking_method") == "Password"
    assert state.attributes.get("unlocking_user") == 25


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "event_val, expected_event_name",
    [(1, "single_click"), (2, "double_click"), (255, "long_press")],
    ids=["single_click", "double_click", "long_press"],
)
async def test_momentary_button_events(
    hass: HomeAssistant,
    setup_integration: ConfigEntry,
    mock_lifesmart_devices: list,
    freezer,
    event_val: int,
    expected_event_name: str,
):
    """
    /**
     * test_momentary_button_events - 测试瞬时按钮的事件响应和自动复位逻辑。
     *
     * 模拟场景:
     *   - 向按钮实体发送不同的 `val` (1, 2, 255) 来模拟单击、双击和长按。
     *
     * 预期结果:
     *   - 实体状态应短暂变为 'on'。
     *   - `last_event` 属性应正确反映事件类型。
     *   - 在短暂延迟后，实体状态应自动重置为 'off'。
     */
    """
    device = find_test_device(mock_lifesmart_devices, "bs_button")
    unique_id = generate_unique_id(
        device[DEVICE_TYPE_KEY], device[HUB_ID_KEY], device[DEVICE_ID_KEY], "P1"
    )
    entity_id = er.async_get(hass).async_get_entity_id(
        "binary_sensor", DOMAIN, unique_id
    )
    assert entity_id is not None

    # --- 步骤 1: 触发按钮并验证其变为 'on' 且属性正确 ---
    update_data = {"val": event_val}
    async_dispatcher_send(
        hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{unique_id}", update_data
    )
    await hass.async_block_till_done()

    state_on = hass.states.get(entity_id)
    assert state_on is not None
    assert state_on.state == STATE_ON
    assert state_on.attributes.get("last_event") == expected_event_name
    assert state_on.attributes.get("last_event_time") is not None

    # --- 步骤 2: 快进时间以触发自动重置 ---
    freezer.tick(timedelta(seconds=0.6))

    # 需要手动推进 Home Assistant 的事件循环
    import asyncio

    await asyncio.sleep(0)  # 让事件循环处理调度的回调
    await hass.async_block_till_done()

    # 再次推进时间确保回调被执行
    freezer.tick(timedelta(seconds=0.1))
    await hass.async_block_till_done()

    # --- 步骤 3: 验证状态已自动重置为 'off' ---
    state_off = hass.states.get(entity_id)
    assert state_off is not None
    assert state_off.state == STATE_OFF


async def test_global_refresh_update(
    hass: HomeAssistant,
    setup_integration: ConfigEntry,
):
    """Test entity state update via a global data refresh."""
    entity_id = "binary_sensor.front_door_g"
    assert hass.states.get(entity_id).state == STATE_ON

    # Find the door device in the live hass data and update it
    door_device = find_test_device(
        hass.data[DOMAIN][setup_integration.entry_id]["devices"], "bs_door"
    )
    door_device[DEVICE_DATA_KEY] = {"G": {"val": 1, "type": 0}}

    async_dispatcher_send(hass, LIFESMART_SIGNAL_UPDATE_ENTITY)
    await hass.async_block_till_done()

    assert hass.states.get(entity_id).state == STATE_OFF
