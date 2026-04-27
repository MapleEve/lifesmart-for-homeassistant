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
        attrs = {
            "category": self._category,
            "brand": self._brand,
            "model_index": self._idx,
            "hub_id": self._hub_id,
            "device_id": self._device_id,
            "available_keys": self._available_keys,
            "remote_id": self._remote_id,
        }

        # 为空调设备添加详细的功能信息
        if self._category == "ac" and hasattr(self, "_ac_features"):
            ac_features = self._ac_features

            # 温度范围信息
            if "temp_range" in ac_features:
                temp_range = ac_features["temp_range"]
                attrs["temperature_range"] = {
                    "min": temp_range.get("min"),
                    "max": temp_range.get("max"),
                    "unit": "℃",
                }
                attrs["temperature_values"] = temp_range.get("values", [])

            # 支持的运行模式
            if "supported_modes" in ac_features:
                attrs["supported_modes"] = ac_features["supported_modes"]

            # 风速档位信息
            if "wind_levels" in ac_features:
                attrs["wind_levels"] = ac_features["wind_levels"]

            # 摆风模式
            if "swing_modes" in ac_features:
                attrs["swing_modes"] = ac_features["swing_modes"]

            # 电源选项
            if "power_values" in ac_features:
                attrs["power_options"] = ac_features["power_values"]

            # 原始按键列表(针对keys模式)
            if "available_keys" in ac_features:
                attrs["raw_keys"] = ac_features["available_keys"]

            # 功能完整性标识
            attrs["feature_completeness"] = {
                "has_temperature_range": "temp_range" in ac_features,
                "has_mode_list": "supported_modes" in ac_features,
                "has_wind_levels": "wind_levels" in ac_features,
                "has_swing_modes": "swing_modes" in ac_features,
                "parsing_method": (
                    "ability_array" if "temp_range" in ac_features else "keys_array"
                ),
            }

        return attrs

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
        """解析空调设备的功能特性。

        根据API返回的数据结构解析空调遥控器支持的功能：
        - code_mode="full": 解析ability数组，获取详细功能信息
        - code_mode="keys": 直接使用keys列表
        - 其他情况: 回退到默认功能列表
        """
        try:
            # 检查API数据格式
            if not isinstance(features, dict):
                _LOGGER.warning(
                    "遥控器 %s 收到非字典格式的features数据: %s",
                    self._attr_name,
                    type(features),
                )
                return self._get_default_ac_keys()

            code_mode = features.get("code_mode", "unknown")

            if code_mode == "full":
                # 解析完整模式的ability数组
                return self._parse_full_mode_ac(features)
            elif code_mode == "keys":
                # 解析按键模式的keys数组
                return self._parse_keys_mode_ac(features)
            elif "keys" in features:
                # 无code_mode但有keys字段，按普通设备处理
                return self._parse_keys_mode_ac(features)
            elif "ability" in features:
                # 无code_mode但有ability字段，按完整模式处理
                return self._parse_full_mode_ac(features)
            else:
                _LOGGER.debug(
                    "遥控器 %s 收到未知格式的features，使用默认功能: %s",
                    self._attr_name,
                    features,
                )
                return self._get_default_ac_keys()

        except Exception as e:
            _LOGGER.warning(
                "遥控器 %s 解析features时发生错误: %s，使用默认功能",
                self._attr_name,
                e,
            )
            return self._get_default_ac_keys()

    def _parse_full_mode_ac(self, features: dict[str, Any]) -> list[str]:
        """解析完整模式的空调功能 (code_mode="full")。

        解析ability数组中的详细功能信息，生成对应的按键列表。
        """
        available_keys = []
        abilities = features.get("ability", [])

        # 初始化附加信息存储
        if not hasattr(self, "_ac_features"):
            self._ac_features = {}

        for ability_info in abilities:
            if not isinstance(ability_info, dict):
                continue

            ability_name = ability_info.get("ability")
            ability_values = ability_info.get("values", [])

            if ability_name == "power":
                # 电源控制
                available_keys.append("power")
                self._ac_features["power_values"] = ability_values

            elif ability_name == "mode":
                # 模式控制
                available_keys.append("mode")
                self._ac_features["supported_modes"] = ability_values
                # 为支持的模式添加对应按键
                for mode in ability_values:
                    if mode in ["auto", "cool", "heat", "dry", "fan"]:
                        mode_key = f"mode_{mode}"
                        if mode_key not in available_keys:
                            available_keys.append(mode_key)

            elif ability_name == "temp":
                # 温度控制
                available_keys.extend(["temp_up", "temp_down"])
                # 计算温度范围
                try:
                    temp_values = [int(v) for v in ability_values if str(v).isdigit()]
                    if temp_values:
                        self._ac_features["temp_range"] = {
                            "min": min(temp_values),
                            "max": max(temp_values),
                            "values": sorted(temp_values),
                        }
                except (ValueError, TypeError) as e:
                    _LOGGER.debug(
                        "遥控器 %s 解析温度范围时出错: %s",
                        self._attr_name,
                        e,
                    )

            elif ability_name == "wind":
                # 风速控制
                available_keys.append("wind")
                self._ac_features["wind_levels"] = ability_values
                # 为不同风速添加具体按键
                for level in ability_values:
                    if str(level).lower() != "auto":  # auto已经包含在wind中
                        wind_key = f"wind_{level}"
                        if wind_key not in available_keys:
                            available_keys.append(wind_key)

            elif ability_name == "swing":
                # 摆风控制
                available_keys.append("swing")
                self._ac_features["swing_modes"] = ability_values

        # 如果没有解析到任何功能，返回默认功能
        if not available_keys:
            _LOGGER.debug(
                "遥控器 %s 未从完整模式中解析到功能，使用默认功能",
                self._attr_name,
            )
            return self._get_default_ac_keys()

        # 去重并排序
        return sorted(list(set(available_keys)))

    def _parse_keys_mode_ac(self, features: dict[str, Any]) -> list[str]:
        """解析按键模式的空调功能 (code_mode="keys")。

        对于code_mode为"keys"的空调，直接使用keys列表作为按键。
        """
        keys = features.get("keys", [])

        if not isinstance(keys, list):
            _LOGGER.debug(
                "遥控器 %s 的keys不是列表格式: %s",
                self._attr_name,
                type(keys),
            )
            return self._get_default_ac_keys()

        # 过滤并清理keys
        processed_keys = []
        for key in keys:
            if isinstance(key, (str, int, float)):
                key_str = str(key).strip()
                if key_str:
                    processed_keys.append(key_str)

        if not processed_keys:
            _LOGGER.debug(
                "遥控器 %s 的keys列表为空或无效",
                self._attr_name,
            )
            return self._get_default_ac_keys()

        # 存储keys信息供状态属性使用
        if not hasattr(self, "_ac_features"):
            self._ac_features = {}
        self._ac_features["available_keys"] = processed_keys

        _LOGGER.debug(
            "遥控器 %s 从按键模式解析到 %d 个功能: %s",
            self._attr_name,
            len(processed_keys),
            processed_keys[:10],  # 显示前10个避免日志过长
        )

        return processed_keys

    def _get_default_ac_keys(self) -> list[str]:
        """获取默认的空调功能列表。

        在API解析失败或数据不完整时作为回退方案。
        """
        return [
            "power",
            "mode",
            "temp_up",
            "temp_down",
            "wind",
            "swing",
        ]

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
