"""LifeSmart 遥控器实体平台。

此模块提供遥控器实体的实现，支持通过配置流程创建的遥控器。
替代了之前的服务调用方式，提供更符合 Home Assistant 设计理念的实体操作。

由 @MapleEve 创建。
"""

import logging
from typing import Any

from homeassistant.components.remote import RemoteEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .core.const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """设置遥控器实体。"""
    hub_data = hass.data[DOMAIN][config_entry.entry_id]

    # 获取配置的遥控器列表
    remotes_config = config_entry.options.get("remotes", {})

    entities = []
    for remote_id, remote_config in remotes_config.items():
        entity = LifeSmartRemoteEntity(
            hub_data=hub_data,
            remote_id=remote_id,
            remote_config=remote_config,
        )
        entities.append(entity)

    if entities:
        async_add_entities(entities, True)
        _LOGGER.info("已添加 %d 个遥控器实体", len(entities))


class LifeSmartRemoteEntity(RemoteEntity):
    """LifeSmart 遥控器实体。

    代表一个配置的遥控器，可以发送红外命令到指定的设备。
    """

    def __init__(
        self,
        hub_data: dict,
        remote_id: str,
        remote_config: dict,
    ) -> None:
        """初始化遥控器实体。

        Args:
            hub_data: 集成的hub数据
            remote_id: 遥控器唯一标识
            remote_config: 遥控器配置信息
        """
        self._hub_data = hub_data
        self._client = hub_data["client"]
        self._remote_id = remote_id
        self._config = remote_config

        # 实体属性
        self._attr_name = remote_config.get("name", f"遥控器 {remote_id}")
        self._attr_unique_id = f"{hub_data['entry_id']}_remote_{remote_id}"

        # 遥控器配置
        self._hub_id = remote_config.get("hub_id")
        self._device_id = remote_config.get("device_id")
        self._category = remote_config.get("category")
        self._brand = remote_config.get("brand")
        self._idx = remote_config.get("idx")

        # 可用按键列表（将在实体添加到HA时获取）
        self._available_keys = []

        # 默认为开启状态（遥控器实体通常是虚拟的，总是可用的）
        self._attr_is_on = True

    async def async_added_to_hass(self) -> None:
        """实体添加到 Home Assistant 时的初始化。"""
        await super().async_added_to_hass()

        try:
            # 获取遥控器支持的按键列表
            features = await self._client.get_ir_remote_feature_async(
                category=self._category,
                brand=self._brand,
                idx=self._idx,
            )

            # 根据设备类别解析可用按键
            if self._category == "ac":
                # 空调设备有特殊的功能结构
                self._available_keys = self._parse_ac_features(features)
            else:
                # 普通设备的按键列表
                self._available_keys = self._parse_normal_features(features)

            _LOGGER.debug(
                "遥控器 %s 获取到 %d 个可用按键: %s",
                self._attr_name,
                len(self._available_keys),
                self._available_keys,
            )
        except Exception as e:
            _LOGGER.warning(
                "无法获取遥控器 %s 的按键列表: %s",
                self._attr_name,
                e,
            )
            # 提供一些基本按键作为后备
            self._available_keys = self._get_default_keys()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """返回实体的额外状态属性。"""
        return {
            "category": self._category,
            "brand": self._brand,
            "model_index": self._idx,
            "hub_id": self._hub_id,
            "device_id": self._device_id,
            "available_keys": self._available_keys,
            "remote_id": self._remote_id,
        }

    @property
    def device_info(self) -> dict[str, Any]:
        """返回设备信息。"""
        return {
            "identifiers": {(DOMAIN, self._attr_unique_id)},
            "name": self._attr_name,
            "manufacturer": "LifeSmart",
            "model": f"{self._brand} {self._category} Remote",
            "via_device": (DOMAIN, self._hub_id),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """打开遥控器（虚拟操作）。"""
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """关闭遥控器（虚拟操作）。"""
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_send_command(self, command: list[str], **kwargs: Any) -> None:
        """发送遥控器命令。

        Args:
            command: 要发送的命令列表
            **kwargs: 额外参数（用于空调等特殊设备）
        """
        if not self._attr_is_on:
            _LOGGER.warning("遥控器 %s 处于关闭状态，无法发送命令", self._attr_name)
            return

        if not command:
            _LOGGER.warning("遥控器 %s 收到空命令列表，未发送任何命令", self._attr_name)
            return

        try:
            if self._category == "ac":
                # 空调设备使用特殊的控制方法
                await self._send_ac_command(command, **kwargs)
            else:
                # 普通设备发送红外按键
                await self._send_ir_keys(command)

            _LOGGER.info(
                "遥控器 %s 成功发送命令: %s",
                self._attr_name,
                command,
            )
        except Exception as e:
            _LOGGER.error(
                "遥控器 %s 发送命令失败: %s",
                self._attr_name,
                e,
            )

    async def _send_ir_keys(self, commands: list[str]) -> None:
        """发送普通红外按键命令。"""
        # 根据遥控器配置选择合适的 ai 或 idx 参数
        if self._idx:
            # 虚拟遥控器使用 idx 参数
            await self._client.async_send_ir_key(
                agt=self._hub_id,
                me=self._device_id,
                category=self._category,
                brand=self._brand,
                keys=commands,
                ai="",
                idx=self._idx,
            )
        else:
            # 通用码库使用空 ai 参数
            await self._client.async_send_ir_key(
                agt=self._hub_id,
                me=self._device_id,
                category=self._category,
                brand=self._brand,
                keys=commands,
                ai="",
            )

    async def _send_ac_command(self, commands: list[str], **kwargs: Any) -> None:
        """发送空调控制命令。"""
        # 从命令和参数中构建空调控制选项
        key = commands[0] if commands else "power"

        ac_options = {
            "agt": self._hub_id,
            "me": self._device_id,
            "category": self._category,
            "brand": self._brand,
            "key": key,
            "power": kwargs.get("power", 1),
            "mode": kwargs.get("mode", 1),
            "temp": kwargs.get("temp", 25),
            "wind": kwargs.get("wind", 0),
            "swing": kwargs.get("swing", 0),
        }

        # 添加可选参数
        if "keyDetail" in kwargs:
            ac_options["keyDetail"] = kwargs["keyDetail"]

        await self._client.async_ir_control(self._device_id, ac_options)

    def _parse_ac_features(self, features: dict[str, Any]) -> list[str]:
        """解析空调设备的功能特性。"""
        # 空调设备的标准功能
        ac_keys = [
            "power",
            "mode",
            "temp_up",
            "temp_down",
            "wind",
            "swing",
        ]

        # TODO: 根据API返回的features进一步解析支持的功能
        return ac_keys

    def _parse_normal_features(self, features: dict[str, Any]) -> list[str]:
        """解析普通设备的功能特性。"""
        # 从API返回的features中提取按键列表
        if isinstance(features, dict):
            keys = features.get("keys", [])
            # 处理 keys 为字符串（如逗号分隔）或列表的情况
            if isinstance(keys, list):
                # 确保所有元素为字符串
                return [
                    str(k).strip() for k in keys if isinstance(k, (str, int, float))
                ]
            elif isinstance(keys, str):
                # 逗号分隔字符串转为列表
                return [k.strip() for k in keys.split(",") if k.strip()]
            elif isinstance(keys, (int, float)):
                # 单个数字转为字符串列表
                return [str(keys)]
            # 其他类型不处理，走默认

        # 如果无法解析，返回默认按键
        return self._get_default_keys()

    def _get_default_keys(self) -> list[str]:
        """获取设备类别的默认按键列表。"""
        default_keys = {
            "tv": ["POWER", "VOL_UP", "VOL_DOWN", "CH_UP", "CH_DOWN", "MUTE"],
            "ac": ["power", "mode", "temp_up", "temp_down", "wind", "swing"],
            "stb": ["POWER", "CH_UP", "CH_DOWN", "MENU", "OK", "BACK"],
            "dvd": ["POWER", "PLAY", "PAUSE", "STOP", "NEXT", "PREV"],
            "box": ["POWER", "HOME", "BACK", "OK", "UP", "DOWN", "LEFT", "RIGHT"],
            "fan": ["POWER", "SPEED", "TIMER", "SWING"],
            "acl": ["POWER", "MODE", "SPEED", "TIMER"],
        }

        return default_keys.get(self._category, ["POWER"])
