"""HACS implementation of LifeSmart by @MapleEve"""

import asyncio
import json
import logging
from importlib import reload

import websockets
from homeassistant.config_entries import ConfigEntry, CONN_CLASS_CLOUD_PUSH
from homeassistant.const import (
    CONF_URL,
    CONF_TYPE,
    CONF_HOST,
    CONF_PORT,
    CONF_USERNAME,
    CONF_PASSWORD,
    EVENT_HOMEASSISTANT_STOP,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import dispatcher_send
from homeassistant.helpers.entity import Entity
from homeassistant.util.ssl import get_default_context

from . import lifesmart_protocol
from .const import (
    BINARY_SENSOR_TYPES,
    CLIMATE_TYPES,
    CONF_AI_INCLUDE_AGTS,
    CONF_AI_INCLUDE_ITEMS,
    CONF_EXCLUDE_AGTS,
    CONF_EXCLUDE_ITEMS,
    CONF_LIFESMART_APPKEY,
    CONF_LIFESMART_APPTOKEN,
    CONF_LIFESMART_USERID,
    CONF_LIFESMART_USERTOKEN,
    COVER_TYPES,
    DEVICE_ID_KEY,
    DEVICE_NAME_KEY,
    DEVICE_TYPE_KEY,
    DOMAIN,
    EV_SENSOR_TYPES,
    GAS_SENSOR_TYPES,
    HUB_ID_KEY,
    LIFESMART_SIGNAL_UPDATE_ENTITY,
    LIFESMART_STATE_MANAGER,
    LIGHT_DIMMER_TYPES,
    LIGHT_SWITCH_TYPES,
    LOCK_TYPES,
    OT_SENSOR_TYPES,
    SMART_PLUG_TYPES,
    SPOT_TYPES,
    SUBDEVICE_INDEX_KEY,
    SUPPORTED_PLATFORMS,
    SUPPORTED_SUB_BINARY_SENSORS,
    SUPPORTED_SUB_SWITCH_TYPES,
    SUPPORTED_SWTICH_TYPES,
    UPDATE_LISTENER,
)
from .lifesmart_client import LifeSmartClient

# from .lifesmart_protocol import LifeSmartLocalClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    hass.data.setdefault(DOMAIN, {})

    exclude_devices = config_entry.data.get(CONF_EXCLUDE_ITEMS, [])
    exclude_hubs = config_entry.data.get(CONF_EXCLUDE_AGTS, [])
    ai_include_hubs = config_entry.data.get(CONF_AI_INCLUDE_AGTS, [])
    ai_include_items = config_entry.data.get(CONF_AI_INCLUDE_ITEMS, [])

    if config_entry.data.get(CONF_TYPE, CONN_CLASS_CLOUD_PUSH) == CONN_CLASS_CLOUD_PUSH:
        app_key = config_entry.data.get(CONF_LIFESMART_APPKEY)
        app_token = config_entry.data.get(CONF_LIFESMART_APPTOKEN)
        user_token = config_entry.data.get(CONF_LIFESMART_USERTOKEN)
        user_id = config_entry.data.get(CONF_LIFESMART_USERID)
        baseurl = config_entry.data.get(CONF_URL)

        lifesmart_client = LifeSmartClient(
            baseurl,
            app_key,
            app_token,
            user_token,
            user_id,
        )
    else:
        reload(lifesmart_protocol)
        host = config_entry.data.get(CONF_HOST)
        port = config_entry.data.get(CONF_PORT)
        username = config_entry.data.get(CONF_USERNAME)
        password = config_entry.data.get(CONF_PASSWORD)
        lifesmart_client = lifesmart_protocol.LifeSmartLocalClient(
            host, port, username, password, config_entry.entry_id
        )

        config_entry.async_on_unload(
            hass.bus.async_listen_once(
                EVENT_HOMEASSISTANT_STOP, lifesmart_client.async_disconnect
            )
        )

        def callback(msg):
            if msg.get("msg"):
                _LOGGER.debug("Received message: %s", msg)
                asyncio.create_task(data_update_handler(hass, config_entry, msg))
            elif msg.get("reload"):
                asyncio.create_task(
                    hass.config_entries.async_reload(config_entry.entry_id)
                )

        hass.async_create_background_task(
            lifesmart_client.async_connect(callback), "lifesmart-connect"
        )

    # 监听配置选项更新
    update_listener = config_entry.add_update_listener(_async_update_listener)

    devices = await lifesmart_client.get_all_device_async()

    hass.data[DOMAIN][config_entry.entry_id] = {
        "client": lifesmart_client,
        "exclude_devices": exclude_devices,
        "exclude_hubs": exclude_hubs,
        "ai_include_hubs": ai_include_hubs,
        "ai_include_items": ai_include_items,
        "devices": devices,
        UPDATE_LISTENER: update_listener,
    }

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(
            config_entry, SUPPORTED_PLATFORMS
        )
    )

    async def send_keys(call):
        """Handle the service call."""
        agt = call.data[HUB_ID_KEY]
        me = call.data[DEVICE_ID_KEY]
        ai = call.data["ai"]
        category = call.data["category"]
        brand = call.data["brand"]
        keys = call.data["keys"]
        restkey = await hass.data[DOMAIN][config_entry.entry_id][
            "client"
        ].send_ir_key_async(
            agt,
            ai,
            me,
            category,
            brand,
            keys,
        )
        _LOGGER.debug("sendkey: %s", str(restkey))

    async def send_ackeys(call):
        """Handle the service call."""
        agt = call.data[HUB_ID_KEY]
        me = call.data[DEVICE_ID_KEY]
        ai = call.data["ai"]
        category = call.data["category"]
        brand = call.data["brand"]
        keys = call.data["keys"]
        power = call.data["power"]
        mode = call.data["mode"]
        temp = call.data["temp"]
        wind = call.data["wind"]
        swing = call.data["swing"]
        restackey = await hass.data[DOMAIN][config_entry.entry_id][
            "client"
        ].send_ir_ackey_async(
            agt,
            ai,
            me,
            category,
            brand,
            keys,
            power,
            mode,
            temp,
            wind,
            swing,
        )
        _LOGGER.debug("sendkey: %s", str(restackey))

    async def scene_set_async(call):
        """Handle the service call."""
        agt = call.data[HUB_ID_KEY]
        sceneid = call.data["id"]
        restkey = await hass.data[DOMAIN][config_entry.entry_id][
            "client"
        ].set_scene_async(
            agt,
            sceneid,
        )
        _LOGGER.debug("scene_set: %s", str(restkey))

    hass.services.async_register(DOMAIN, "send_keys", send_keys)
    hass.services.async_register(DOMAIN, "send_ackeys", send_ackeys)
    hass.services.async_register(DOMAIN, "scene_set", scene_set_async)

    if isinstance(lifesmart_client, LifeSmartClient):
        ws_url = lifesmart_client.get_wss_url()
        hass.data[DOMAIN][LIFESMART_STATE_MANAGER] = LifeSmartStatesManager(
            hass, config_entry, ws_url=ws_url
        )
        hass.data[DOMAIN][LIFESMART_STATE_MANAGER].start()

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, SUPPORTED_PLATFORMS
    )
    if isinstance(
        hass.data[DOMAIN][entry.entry_id]["client"],
        lifesmart_protocol.LifeSmartLocalClient,
    ):
        await hass.data[DOMAIN][entry.entry_id]["client"].async_disconnect(None)
    return unload_ok


async def data_update_handler(hass, config_entry, msg):
    data = msg["msg"]
    device_type = data[DEVICE_TYPE_KEY]
    hub_id = data[HUB_ID_KEY]
    device_id = data[DEVICE_ID_KEY]
    sub_device_key = data[SUBDEVICE_INDEX_KEY]
    exclude_devices = config_entry.data.get(CONF_EXCLUDE_ITEMS, [])
    exclude_hubs = config_entry.data.get(CONF_EXCLUDE_AGTS, [])
    ai_include_hubs = config_entry.data.get(CONF_AI_INCLUDE_AGTS, [])
    ai_include_items = config_entry.data.get(CONF_AI_INCLUDE_ITEMS, [])

    if (
        sub_device_key != "s"
        and device_id not in exclude_devices
        and hub_id not in exclude_hubs
    ):
        entity_id = generate_entity_id(device_type, hub_id, device_id, sub_device_key)
        _LOGGER.debug(
            "已生成实体id - 设备号：%s 中枢：%s 设备类型：%s IDX:%s ",
            str(device_id),
            str(hub_id),
            str(device_type),
            str(sub_device_key),
        )

        if (
            device_type in SUPPORTED_SWTICH_TYPES
            and sub_device_key in SUPPORTED_SUB_SWITCH_TYPES
        ):
            dispatcher_send(hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data)
        elif (
            device_type in BINARY_SENSOR_TYPES
            and sub_device_key in SUPPORTED_SUB_BINARY_SENSORS
        ):
            dispatcher_send(hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data)

        elif device_type in COVER_TYPES and sub_device_key == "P1":
            dispatcher_send(hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data)
        elif device_type in EV_SENSOR_TYPES:
            dispatcher_send(hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data)
        elif device_type in GAS_SENSOR_TYPES and data["val"] > 0:
            dispatcher_send(hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data)
        elif device_type in SPOT_TYPES or device_type in LIGHT_SWITCH_TYPES:
            _LOGGER.debug("websocket_light_msg: %s ", str(msg))
            dispatcher_send(hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data)

        elif device_type in LIGHT_DIMMER_TYPES:
            dispatcher_send(hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data)

        elif device_type in CLIMATE_TYPES:
            dispatcher_send(hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data)
        elif device_type in LOCK_TYPES:
            if sub_device_key in ["BAT", "ALM"]:
                dispatcher_send(
                    hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data
                )
            elif sub_device_key == "EVTLO":
                dispatcher_send(
                    hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data
                )
                _LOGGER.debug(
                    "状态更新已推送 %s - 设备编号：%s -门锁更新数据:%s ",
                    str(LIFESMART_SIGNAL_UPDATE_ENTITY),
                    str(entity_id),
                    str(data),
                )

        elif device_type in OT_SENSOR_TYPES and sub_device_key in [
            "Z",
            "V",
            "P3",
            "P4",
        ]:
            dispatcher_send(hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data)
        elif device_type in SMART_PLUG_TYPES:
            dispatcher_send(hass, f"{LIFESMART_SIGNAL_UPDATE_ENTITY}_{entity_id}", data)
        else:
            _LOGGER.debug("Event is not supported")

    # AI event
    if (
        sub_device_key == "s"
        and device_id in ai_include_items
        and data[HUB_ID_KEY] in ai_include_hubs
    ):
        _LOGGER.info("AI Event: %s", str(msg))
        # device_type = data["devtype"]
        # hub_id = data[HUB_ID_KEY]
        # entity_id = (
        #     "switch."
        #     + (
        #         device_type + "_" + hub_id + "_" + device_id + "_" + sub_device_key
        #     ).lower()
        # )


async def _async_update_listener(hass, config_entry):
    """Handle options update."""
    print("reload")
    await hass.config_entries.async_reload(config_entry.entry_id)


class LifeSmartDevice(Entity):
    """LifeSmart base device."""

    def __init__(self, dev, lifesmart_client) -> None:
        """Initialize the switch."""

        self._name = dev[DEVICE_NAME_KEY]
        self._device_name = dev[DEVICE_NAME_KEY]
        self._agt = dev[HUB_ID_KEY]
        self._me = dev[DEVICE_ID_KEY]
        self._devtype = dev["devtype"]
        self._client = lifesmart_client
        attrs = {
            HUB_ID_KEY: self._agt,
            DEVICE_ID_KEY: self._me,
            "devtype": self._devtype,
        }
        self._attributes = attrs

    @property
    def object_id(self):
        """Return LifeSmart device id."""
        return self.entity_id

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        return self._attributes

    @property
    def name(self):
        """Return LifeSmart device name."""
        return self._name

    @property
    def assumed_state(self):
        """Return true if we do optimistic updates."""
        return False

    @property
    def should_poll(self):
        """check with the entity.py for an updated state."""
        return False

    async def async_lifesmart_epset(self, type, val, idx):
        """Send command to lifesmart device"""
        agt = self._agt
        me = self._me
        responsecode = await self._client.send_epset_async(type, val, idx, agt, me)
        return responsecode

    async def async_lifesmart_epget(self):
        """Get lifesmart device info"""
        agt = self._agt
        me = self._me
        response = await self._client.get_epget_async(agt, me)
        return response

    async def async_lifesmart_sceneset(self, type, rgbw):
        """Set the scene"""
        agt = self._agt
        id = self._me
        response = self._client.set_scene_async(agt, id)
        return response["code"]


class LifeSmartStatesManager:
    """Instance to manage websocket to get push data from LifeSmart service"""

    def __init__(self, hass, config_entry, ws_url):
        self._hass = hass
        self._config_entry = config_entry
        self._ws_url = ws_url
        self._ws = None
        self._lock = asyncio.Lock()
        self._task = None

    async def connect(self):
        async with self._lock:
            if self._ws is None:
                try:
                    # 使用HA提供的SSL上下文
                    ssl_context = get_default_context()
                    self._ws = await websockets.connect(
                        self._ws_url,
                        ping_interval=None,
                        ssl=ssl_context,  # 添加SSL上下文参数
                    )
                    _LOGGER.debug("Lifesmart HACS: WebSocket connected")

                    # 发送验证数据
                    client = self._hass.data[DOMAIN][self._config_entry.entry_id][
                        "client"
                    ]
                    send_data = client.generate_wss_auth()
                    await self._ws.send(send_data)
                    _LOGGER.debug("LifeSmart WebSocket sending auth data")

                except websockets.exceptions.InvalidURI as e:
                    _LOGGER.error("Lifesmart HACS: Invalid WebSocket URL: %s", str(e))
                except websockets.exceptions.InvalidHandshake as e:
                    _LOGGER.error(
                        "Lifesmart HACS: WebSocket handshake failed: %s", str(e)
                    )
                except Exception as e:
                    _LOGGER.error(
                        "Lifesmart HACS: WebSocket connection error: %s", str(e)
                    )
                    self._ws = None

    async def disconnect(self):
        async with self._lock:
            if self._ws is not None:
                await self._ws.close()
                self._ws = None
                _LOGGER.warning("Lifesmart HACS: WebSocket disconnected")

    async def _keep_alive(self):
        while True:
            await self.connect()
            if self._ws is None:
                _LOGGER.warning(
                    "Lifesmart HACS: WebSocket is not connected, waiting for next retry"
                )
                await asyncio.sleep(10)
                continue

            try:
                async for message in self._ws:
                    _LOGGER.debug("Lifesmart HACS: Received raw message: %s", message)
                    if message == "wb closed":
                        _LOGGER.error(
                            "Lifesmart HACS: WebSocket closed without authentication. Check if the authentication process is working correctly."
                        )
                        await asyncio.sleep(3600)  # 等待3600秒再重试
                        break

                    try:
                        msg = json.loads(message)
                        if msg.get("message") == "success" and msg.get("code") == 0:
                            _LOGGER.info(
                                "Lifesmart HACS: WebSocket authentication successful"
                            )
                        elif msg.get("type") == "io":
                            _LOGGER.debug("Lifesmart HACS: Received IO message")
                            asyncio.create_task(
                                data_update_handler(self._hass, self._config_entry, msg)
                            )
                        else:
                            _LOGGER.warning(
                                "Lifesmart HACS: Received unknown message type: %s",
                                str(msg),
                            )
                    except json.JSONDecodeError as e:
                        _LOGGER.error(
                            "Lifesmart HACS: Failed to parse WebSocket message as JSON: %s",
                            str(e),
                        )
            except websockets.exceptions.ConnectionClosed as e:
                _LOGGER.warning(
                    f"Lifesmart HACS: WebSocket connection closed: code={e.code}, reason={e.reason}"
                )
            except Exception as e:
                _LOGGER.error(
                    "Lifesmart HACS: Error in WebSocket communication: %s", str(e)
                )
            finally:
                await self.disconnect()
                _LOGGER.warning(
                    "Lifesmart HACS: WebSocket disconnected, reconnecting in 10 seconds"
                )
                await asyncio.sleep(10)

    def start(self):
        self._task = asyncio.create_task(self._keep_alive())

    def stop(self):
        if self._task is not None:
            self._task.cancel()
            self._task = None


def get_platform_by_device(device_type, sub_device=None):
    if device_type in SUPPORTED_SWTICH_TYPES:
        return Platform.SWITCH
    elif device_type in BINARY_SENSOR_TYPES:
        return Platform.BINARY_SENSOR
    elif device_type in COVER_TYPES:
        return Platform.COVER
    elif device_type in EV_SENSOR_TYPES + GAS_SENSOR_TYPES + OT_SENSOR_TYPES:
        return Platform.SENSOR
    elif device_type in SPOT_TYPES + LIGHT_SWITCH_TYPES + LIGHT_DIMMER_TYPES:
        return Platform.LIGHT
    elif device_type in CLIMATE_TYPES:
        return Platform.CLIMATE
    elif device_type in LOCK_TYPES and sub_device == "BAT":
        return Platform.SENSOR
    elif device_type in LOCK_TYPES and sub_device in ["EVTLO", "ALM"]:
        return Platform.BINARY_SENSOR
    elif device_type in SMART_PLUG_TYPES and sub_device == "P1":
        return Platform.SWITCH
    elif device_type in SMART_PLUG_TYPES and sub_device in ["P2", "P3"]:
        return Platform.SENSOR
    return ""


def generate_entity_id(device_type, hub_id, device_id, idx=None):
    hub_id = hub_id.replace("__", "_").replace("-", "_").replace("/", "_")
    if idx:
        sub_device = idx
    else:
        sub_device = None

    if device_type in [
        *SUPPORTED_SWTICH_TYPES,
        *BINARY_SENSOR_TYPES,
        *EV_SENSOR_TYPES,
        *GAS_SENSOR_TYPES,
        *SPOT_TYPES,
        *LIGHT_SWITCH_TYPES,
        *OT_SENSOR_TYPES,
        *SMART_PLUG_TYPES,
        *LOCK_TYPES,
    ]:
        if sub_device:
            return (
                get_platform_by_device(device_type, sub_device)
                + (
                    "."
                    + device_type
                    + "_"
                    + hub_id
                    + "_"
                    + device_id
                    + "_"
                    + sub_device
                ).lower()
            )
        else:
            return (
                # no sub device (idx)
                get_platform_by_device(device_type)
                + ("." + device_type + "_" + hub_id + "_" + device_id).lower()
            )

    elif device_type in COVER_TYPES:
        return (
            Platform.COVER
            + ("." + device_type + "_" + hub_id + "_" + device_id).lower()
        )
    elif device_type in LIGHT_DIMMER_TYPES:
        return (
            Platform.LIGHT
            + ("." + device_type + "_" + hub_id + "_" + device_id + "_P1P2").lower()
        )
    elif device_type in CLIMATE_TYPES:
        return Platform.CLIMATE + (
            "." + device_type + "_" + hub_id + "_" + device_id
        ).lower().replace(":", "_").replace("@", "_")
