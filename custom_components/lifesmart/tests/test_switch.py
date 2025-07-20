"""Test cases for LifeSmart switch entities in Home Assistant."""

from unittest.mock import AsyncMock

import pytest
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN, SwitchDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from custom_components.lifesmart.const import DOMAIN, LIFESMART_SIGNAL_UPDATE_ENTITY
from custom_components.lifesmart.switch import async_setup_entry

# 模拟一个单火三键开关设备
MOCK_SWITCH_DEVICE = {
    "agt": "mock_hub_id",
    "me": "mock_switch_me",
    "devtype": "SL_SF_IF3",
    "name": "Living Room Switch",
    "data": {
        "L1": {"type": 129, "val": 1, "name": "Main Light"},  # On
        "L2": {"type": 128, "val": 0, "name": "Spotlight"},  # Off
        "L3": {"type": 129, "val": 1, "name": "LED Strip"},  # On
    },
}


@pytest.mark.asyncio
async def test_setup_switch(
    hass: HomeAssistant, mock_lifesmart_client, mock_config_entry
):
    """测试开关实体的设置。"""
    hass.data[DOMAIN][mock_config_entry.entry_id] = {
        "client": mock_lifesmart_client,
        "devices": [MOCK_SWITCH_DEVICE],
        "exclude_devices": "",
        "exclude_hubs": "",
    }

    async_add_entities = AsyncMock()
    await async_setup_entry(hass, mock_config_entry, async_add_entities)

    # 应该为3个按键创建3个实体
    assert async_add_entities.call_count == 1
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 3

    # 验证第一个实体的状态和属性
    entity_l1 = entities[0]
    assert (
        entity_l1.unique_id
        == f"{SWITCH_DOMAIN}.sl_sf_if3_mock_hub_id_mock_switch_me_l1"
    )
    assert entity_l1.name == "Living Room Switch Main Light"
    assert entity_l1.is_on is True
    assert entity_l1.device_class == SwitchDeviceClass.SWITCH

    # 验证第二个实体的状态
    entity_l2 = entities[1]
    assert entity_l2.is_on is False


@pytest.mark.asyncio
async def test_switch_turn_on_off(hass: HomeAssistant, mock_lifesmart_client):
    """测试开关的开关服务调用。"""
    # 创建一个模拟的开关实体
    from custom_components.lifesmart.switch import LifeSmartSwitch

    entity = LifeSmartSwitch(
        device=AsyncMock(),
        raw_device=MOCK_SWITCH_DEVICE,
        sub_device_key="L2",
        sub_device_data=MOCK_SWITCH_DEVICE["data"]["L2"],
        client=mock_lifesmart_client,
        entry_id="mock_entry_id",
    )
    entity.hass = hass
    entity._attr_is_on = False  # 初始状态为关

    # 测试打开
    await entity.async_turn_on()
    mock_lifesmart_client.turn_on_light_switch_async.assert_called_with(
        "L2", "mock_hub_id", "mock_switch_me"
    )
    assert entity.is_on is True  # 乐观更新

    # 测试关闭
    await entity.async_turn_off()
    mock_lifesmart_client.turn_off_light_switch_async.assert_called_with(
        "L2", "mock_hub_id", "mock_switch_me"
    )
    assert entity.is_on is False  # 乐观更新


@pytest.mark.asyncio
async def test_switch_update_via_dispatcher(hass: HomeAssistant):
    """测试通过dispatcher更新开关状态。"""
    from custom_components.lifesmart.switch import LifeSmartSwitch

    entity = LifeSmartSwitch(
        device=AsyncMock(),
        raw_device=MOCK_SWITCH_DEVICE,
        sub_device_key="L2",
        sub_device_data=MOCK_SWITCH_DEVICE["data"]["L2"],
        client=AsyncMock(),
        entry_id="mock_entry_id",
    )
    entity.hass = hass
    entity._attr_is_on = False

    # 模拟添加到HASS
    await entity.async_added_to_hass()

    # 模拟WebSocket推送一个“开”的状态
    update_data = {"type": 129, "val": 1}
    async_dispatcher_send(
        hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity.unique_id}", update_data
    )
    await hass.async_block_till_done()

    assert entity.is_on is True
