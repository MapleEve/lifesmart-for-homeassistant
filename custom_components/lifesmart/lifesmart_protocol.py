"""由 @MagicBear 实现的 LifeSmart 本地协议解析与客户端。 @MapleEve 进行重构

此模块包含两个核心部分：
1. LifeSmartPacketFactory: 一个纯粹的指令包工厂，负责根据不同的控制需求，
构建符合 LifeSmart 本地二进制协议的指令包。
2. LifeSmartLocalClient: 一个功能完备的本地客户端，它使用 LifeSmartPacketFactory
来构建指令，并通过 TCP Socket 与 LifeSmart 中枢进行通信。它提供了与云端客户端
(LifeSmartClient) 完全对齐的异步控制接口，使得上层平台可以无缝切换。
"""

import asyncio
import gzip
import json
import logging
import struct
from collections import OrderedDict
from dataclasses import dataclass
from io import BytesIO
from typing import Callable, Any

from homeassistant.components.climate import HVACMode
from homeassistant.core import Event, ServiceCall

from .const import (
    # --- 命令类型常量 ---
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_PRESS,
    CMD_TYPE_SET_VAL,
    CMD_TYPE_SET_CONFIG,
    CMD_TYPE_SET_TEMP_DECIMAL,
    CMD_TYPE_SET_RAW,
    CMD_TYPE_SET_TEMP_FCU,
    # --- 设备类型和映射 ---
    DOOYA_TYPES,
    GARAGE_DOOR_TYPES,
    REVERSE_LIFESMART_HVAC_MODE_MAP,
    REVERSE_LIFESMART_TF_FAN_MODE_MAP,
    LIFESMART_F_FAN_MODE_MAP,
    REVERSE_LIFESMART_ACIPM_FAN_MAP,
    REVERSE_LIFESMART_CP_AIR_FAN_MAP,
    REVERSE_LIFESMART_CP_AIR_MODE_MAP,
    # --- 核心常量 ---
    SUBDEVICE_INDEX_KEY,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class LSTimestamp:
    """用于表示 LifeSmart 协议中时间戳对象的数据类。"""

    index: int
    value: int
    raw_data: bytes

    # @property
    # def datetime(self) -> datetime.datetime:
    #     """转换为datetime对象"""
    #     return datetime.datetime.fromtimestamp(self.value, tz=self.timezone)

    def as_dict(self) -> dict:
        """将其转换为字典格式，以兼容旧代码或序列化需求。"""
        return {
            "type": "timestamp",
            "index": self.index,
            "value": self.value,
            "raw": self.raw_data,
        }

    def __str__(self) -> str:
        return f"<LSTimestamp {self.value}>"

    def __repr__(self) -> str:
        return self.__str__()


class LSEncoder(json.JSONEncoder):
    """自定义的 JSON 编码器，用于处理 LifeSmart 特殊数据类型。"""

    def default(self, obj):
        """重写默认编码方法。"""
        if isinstance(obj, LSTimestamp):
            return str(obj)
        if isinstance(obj, bytes):
            return list(obj)
        return super().default(obj)


class LifeSmartProtocol:
    """LifeSmart 二进制协议的编码器和解码器。

    此类实现了 LifeSmart 专有的二进制通信协议，能够将 Python 字典
    编码为二进制数据包，以及将二进制数据包解码回 Python 字典。
    """

    KEY_MAPPING = {
        2: "timestamp",
        3: "req",
        4: "args",
        7: "valtag",
        9: "act",
        10: "node",
        11: "ret",
        13: "cron_name",
        16: "name",
        21: "ts",
        22: "devid",
        38: "nid",
        39: "cls",
        40: "rf_button_status",
        41: "val",
        42: "ver",
        46: "cgy",
        47: "key",
        53: "response_token",
        78: "type",
        89: "icon",
        90: "uuid",
        92: "act_change",
        106: "_chd",
        113: "agtid",
        119: "tmzone",
        120: "rf_pair",
        121: "valtag",
        122: "valts",
        135: "dark",
        136: "bright",
    }

    REVERSE_KEY_MAPPING = {v: k for k, v in KEY_MAPPING.items()}

    def __init__(self, debug=False):
        """初始化协议处理器。"""
        self.debug = debug
        self.decode_context = "binary"
        self.decode_direct_output = False
        self._offset = None
        self.need_bytes = 0

    @staticmethod
    def _encode_varint(value):
        """将一个整数编码为变长整数 (Varint)。"""
        data = bytearray()
        while value >= 128:
            data.append((value & 0x7F) | 0x80)
            value >>= 7
        data.append(value)
        return bytes(data)

    @staticmethod
    def _decode_varint(stream):
        """从字节流中解码一个变长整数 (Varint)。"""
        value = 0
        shift = 0
        while True:
            byte = stream.read(1)
            if not byte:
                break
            b = ord(byte)
            value |= (b & 0x7F) << shift
            if not (b & 0x80):
                break
            shift += 7
        return value

    def _string_to_bin(self, value):
        """将字符串编码为二进制格式。"""
        data = b"\x11"
        data += self._encode_varint(len(value))
        data += value.encode("utf-8")
        return data

    def _pack_value(self, value, isKey=False):
        """递归地将 Python 对象打包成二进制格式。"""
        if isinstance(value, bool):
            return b"\x02" if value else b"\x03"

        elif isinstance(value, int):
            if value >= 0x7FFFFFFF:
                value = ((0xFFFFFFFF - value) << 1) | 1
            else:
                sign = 1
                if value < 0:
                    value = -value
                    sign = -1
                value <<= 1
                if sign == -1:
                    value = (value - 2) | 1
            return b"\x04" + self._encode_varint(value)

        elif isinstance(value, str):
            if value == "::NULL::":
                return b"\x00"
            elif value.startswith("enum:"):
                key = value[5:]
                enum_id = int(self.REVERSE_KEY_MAPPING.get(key, key))
                return struct.pack("BB", 0x13, enum_id)
            elif isKey and self.REVERSE_KEY_MAPPING.get(value, None) is not None:
                enum_id = self.REVERSE_KEY_MAPPING.get(value, None)
                return struct.pack("BB", 0x13, enum_id)
            else:
                return self._string_to_bin(value)

        elif isinstance(value, list):
            data = struct.pack("B", len(value))
            for idx, item in enumerate(value):
                data += self._pack_value(idx)
                data += self._pack_value(item)
            return data

        elif isinstance(value, dict):
            data = struct.pack("BB", 0x12, len(value))
            for k, v in value.items():
                data += self._pack_value(k, True)
                data += self._pack_value(v)
            return data

        elif value is None:
            return b"\x00"

        else:
            _LOGGER.warning("不支持的打包类型: %s", type(value))
            return b""

    def encode(self, parts):
        """将多个部分编码成一个完整的 LifeSmart 数据包。"""
        header = b"GL00\x00\x00"
        data = b""
        for part in parts:
            data += self._pack_value(part)[1:]
        pkt = header + struct.pack(">I", len(data)) + data

        if len(pkt) >= 1000:
            compressed = gzip.compress(pkt)
            return b"ZZ00\x00\x00" + struct.pack(">I", len(pkt)) + compressed

        return pkt

    def _parse_value(self, stream, data_type, call_stack=""):
        """递归地从字节流中解析出 Python 对象。"""
        try:
            if data_type == 0x00:  # NULL
                return None

            elif data_type == 0x02:  # True
                return True

            elif data_type == 0x03:  # False
                return False

            elif data_type == 0x04:  # Integer
                varint = self._decode_varint(stream)
                if varint & 1:
                    result = -((varint >> 1) + 1)
                else:
                    result = varint >> 1
                return result if result <= 0x7FFFFFFF else result - 0x100000000

            elif data_type == 0x05:  # HEX类型处理
                index = stream.read(1)[0]
                hex_data = stream.read(8)
                if len(hex_data) < 8:
                    raise EOFError("HEX 数据不完整")
                return {
                    "type": "HEX",
                    "index": index,
                    "value": hex_data.hex(),
                    "raw": hex_data,
                }

            elif data_type == 0x06:  # 时间戳类型处理
                index = stream.read(1)[0]
                int_value = 0
                shift = 0
                while True:
                    byte = stream.read(1)
                    if not byte:
                        raise EOFError("Varint 数据意外结束")
                    b = ord(byte)
                    int_value |= (b & 0x7F) << shift
                    if not (b & 0x80):
                        break
                    shift += 7
                final_value = -(int_value >> 1) if (int_value & 1) else (int_value >> 1)
                raw_bytes = int_value.to_bytes((int_value.bit_length() + 7) // 8, "big")
                return LSTimestamp(index=index, value=final_value, raw_data=raw_bytes)

            elif data_type == 0x11:  # String
                length = self._decode_varint(stream)
                if length < 0 or stream.tell() + length > len(stream.getvalue()):
                    raise ValueError("无效的字符串长度")
                return stream.read(length).decode("utf-8", errors="replace")

            elif data_type == 0x12:  # Array/Dict
                if stream.tell() + 1 > len(stream.getvalue()):
                    raise EOFError("数据意外结束")

                count = ord(stream.read(1))
                items = []

                for _ in range(count):
                    if stream.tell() + 1 > len(stream.getvalue()):
                        break
                    key_type = ord(stream.read(1))
                    key = self._parse_value(stream, key_type, call_stack + ".")

                    if stream.tell() + 1 > len(stream.getvalue()):
                        break
                    value_type = ord(stream.read(1))
                    value = self._parse_value(
                        stream, value_type, call_stack + f".{key}"
                    )

                    if not isinstance(key, (str, int, float, bool, type(None))):
                        _LOGGER.warning(
                            "解码时遇到不可哈希的键类型: %s，已跳过。", type(key)
                        )
                        continue

                    items.append((key, value))

                try:
                    return dict(items)
                except (TypeError, ValueError):
                    return [v for _, v in items]

            elif data_type == 0x13:  # Enum
                if stream.tell() + 1 > len(stream.getvalue()):
                    raise EOFError("数据意外结束")
                enum_id = ord(stream.read(1))
                return "enum:" + self.KEY_MAPPING.get(enum_id, f"{enum_id}")

            else:
                _LOGGER.warning("未知的解码数据类型: 0x%02x", data_type)
                return None

        except Exception as e:
            _LOGGER.error(
                "在位置 %d 解析时出错: %s, 类型[0x%x] 调用栈[%s]",
                stream.tell(),
                str(e),
                data_type,
                call_stack,
            )
            raise

    def decode(self, data):
        """解码一个完整的 LifeSmart 数据包。"""
        original_data = data
        try:
            if len(data) < 4:
                raise EOFError("包头不完整 (需要 4 字节)")

            header = data[:4]
            remaining = data[4:]

            if header == b"ZZ00":  # 压缩包处理
                if len(remaining) < 4:
                    raise EOFError("压缩包不完整 (需要原始长度)")
                orig_len = struct.unpack(">I", remaining[:4])[0]
                compressed_data = remaining[4:]
                try:
                    decompressed = gzip.decompress(compressed_data)
                except OSError as e:
                    raise ValueError(f"解压失败: {str(e)}") from e
                if len(decompressed) != orig_len:
                    raise ValueError(
                        f"解压后尺寸不匹配 ({len(decompressed)} vs {orig_len})"
                    )

                # 递归解码解压后的数据
                consumed_bytes = 4 + 4 + len(compressed_data)
                remaining_compressed, structure = self.decode(decompressed)

                if remaining_compressed:
                    _LOGGER.warning(
                        "解压后仍有未处理的数据: %d 字节",
                        len(remaining_compressed),
                    )
                return original_data[consumed_bytes:], structure

            elif header == b"GL00":  # 标准包处理
                if len(original_data) < 10:
                    raise EOFError("数据包不完整 (至少需要 10 字节)")
                pkt_len = struct.unpack(">I", original_data[6:10])[0]
                total_length = 10 + pkt_len

                if len(original_data) < total_length:
                    raise EOFError(f"数据包长度不匹配 (需要 {total_length} 字节)")

                packet_data = original_data[10:total_length]
                remaining_data = original_data[total_length:]

                try:
                    stream = BytesIO(packet_data)
                    result = []
                    while stream.tell() < len(packet_data):
                        parsed = self._parse_value(stream, 0x12)
                        result.append(parsed)
                except EOFError as e:
                    raise EOFError(f"不完整的数据包数据: {str(e)}") from e
                return remaining_data, self._normalize_structure(result)

            else:
                raise ValueError(f"未知的包头: {header.hex()}")

        except EOFError as e:
            _LOGGER.debug("解码时遇到 EOF: %s", str(e))
            raise  # 重新抛出给上层处理
        except Exception as e:
            _LOGGER.error("解码时出错: %s", str(e), exc_info=True)
            return original_data, None

    def _normalize_key(self, key):
        """确保字典键为基本类型。"""
        if isinstance(key, (str, int, float, bool, type(None))):
            return key
        try:
            return str(key)
        except Exception:
            return "invalid_key"

    def _normalize_structure(self, data):
        """递归地将 OrderedDict 转换为标准字典，并规范化键。"""
        if isinstance(data, (dict, OrderedDict)):
            return {
                self._normalize_key(k): self._normalize_structure(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._normalize_structure(item) for item in data]
        return data

    def _build_structure(self, ops):
        """根据操作列表构建数据结构。"""
        stack = []
        current = []
        for op in ops:
            if isinstance(op, tuple):
                key, value = op
                if isinstance(current, dict):
                    current[key] = value
                else:
                    current.append({key: value})
            elif isinstance(op, list):
                stack.append(current)
                current = []
            else:
                if stack:
                    parent = stack.pop()
                    parent.append(current)
                    current = parent
                else:
                    current.append(op)
        return current


class LifeSmartPacketFactory:
    """LifeSmart 本地协议的指令包工厂。

    此类不直接与网络通信，它的唯一职责是构建各种控制命令的二进制数据包。
    """

    def __init__(self, node_agt: str, node: str = ""):
        """初始化指令包工厂。"""
        self._proto = LifeSmartProtocol()
        self._sel = 1
        self.node_agt = node_agt
        self.node = node

    def _build_packet(
        self, args: dict, act: str = "rfSetA", node_suffix: str = "/ep"
    ) -> bytes:
        """构建一个标准的控制指令包。"""
        packet_data = [
            {"_sel": self._sel, "req": False, "timestamp": 10},
            {
                "args": args,
                "node": f"{self.node_agt}{node_suffix}",
                "act": act,
            },
        ]
        return self._proto.encode(packet_data)

    def build_login_packet(self, uid: str, pwd: str) -> bytes:
        """构建登录指令包。"""
        login_data = [
            {"_sel": 1, "sn": 1, "req": False},
            {
                "args": {
                    "cid": "6D56899B-82DA-403D-8291-50B57EE05DBA",
                    "cver": "1.0.48p1",
                    "uid": uid,
                    "nick": "admin",
                    "cname": "LifeSmart",
                    "pwd": pwd,
                },
                "node": "A3MAAABaAEkBRzQ0Mzc0OA/ac",
                "act": "Login",
            },
        ]
        return self._proto.encode(login_data)

    def build_login_as_camera_packet(self, uid: str, pwd: str) -> bytes:
        """构建作为摄像头登录的指令包。"""
        login_data = [
            {"_sel": 1, "sn": 1, "req": False},
            {
                "args": {
                    "cid": "A90306F9-BA3B-488A-952E-2FFF792D8553",
                    "uid": uid,
                    "pwd": pwd,
                    "vchn": 2,
                    "lsi_auth": {
                        "lsid": "apptable: 0x0113e95080",
                        "lsid_t": "A9IAAEJDMzQwMDJGMzIyQg",
                        "tk": "a582cd0b2ea1df5ad8e1767421d115b3",
                        "aid": 10001,
                        "ts": 16318742,
                    },
                    "camera": "A9IAAEJDMzQwMDJGMzIyQg:0001",
                },
                "node": "msv/ac",
                "act": "Login",
            },
        ]
        return self._proto.encode(login_data)

    def build_login_by_token_packet(self, token: str) -> bytes:
        """构建使用令牌登录的指令包。"""
        login_data = [
            {"_sel": 1, "sn": 1, "req": False},
            {
                "args": {
                    "cver": "1.0.28p4",
                    "uid": "test",
                    "uuid": "A3MAAABaAEkBRzQ0Mzc0OA",
                    "pwd": "test",
                    "token": token,
                },
                "node": "msv/st",
                "act": "LoginA",
            },
        ]
        return self._proto.encode(login_data)

    def build_get_config_packet(self, node: str) -> bytes:
        """构建获取所有设备配置的指令包。"""
        config_data = [
            {"req": False, "timestamp": 10},
            {
                "args": {
                    "enum:14": {
                        "enum:98": {
                            "uuid": False,
                            "enum:114": False,
                            "ver": False,
                            "enum:14": {"m": 1, "s": False, "_chd": 1},
                            "icon": False,
                            "cls": False,
                            "enum:56": False,
                            "_": "eps",
                            "P_Flip": False,
                            "ptzmr": False,
                            "enum:83": False,
                            "nid": False,
                            "devType": False,
                            "cgy": False,
                            "enum:108": False,
                            "rfic": False,
                            "name": False,
                            "agtid": False,
                        }
                    },
                    "enum:12": {"enum:13": False},
                    "_chd": 1,
                },
                "node": f"{node}/me/ep",
                "act": "enum:91",
            },
        ]
        return self._proto.encode(config_data)

    def build_switch_packet(self, devid: str, idx: str, on: bool) -> bytes:
        """构建开关指令包。"""
        args = {
            "val": 1 if on else 0,
            "valtag": "m",
            "devid": devid,
            "key": idx,  # 本地协议使用 'key'
            "type": CMD_TYPE_ON if on else CMD_TYPE_OFF,
        }
        return self._build_packet(args)

    def build_cover_command_packet(
        self, devid: str, idx: str, command: str, device_type: str
    ) -> bytes:
        """构建窗帘的开/关/停指令包。"""
        args = {
            "valtag": "m",
            "devid": devid,
            "key": idx,
        }
        if device_type in GARAGE_DOOR_TYPES or device_type in DOOYA_TYPES:
            args.update(
                {
                    "val": 100 if command == "open" else 0,
                    "type": CMD_TYPE_SET_VAL,
                }
            )
            if command == "stop":
                args["type"] = CMD_TYPE_SET_CONFIG
                args["val"] = 0x80
        else:
            args.update({"val": 1, "type": CMD_TYPE_ON})
        return self._build_packet(args)

    def build_cover_position_packet(self, devid: str, idx: str, position: int) -> bytes:
        """构建设置窗帘位置的指令包。"""
        args = {
            "val": position,
            "valtag": "m",
            "devid": devid,
            "key": idx,
            "type": CMD_TYPE_SET_VAL,
        }
        return self._build_packet(args)

    def build_climate_hvac_mode_packet(
        self, devid: str, hvac_mode: HVACMode, current_val: int, device_type: str
    ) -> bytes:
        """构建设置温控器HVAC模式的指令包。"""
        if hvac_mode == HVACMode.OFF:
            return self.build_switch_packet(devid, "P1", False)

        # 温控器开机
        self.build_switch_packet(devid, "P1", True)

        args = {"valtag": "m", "devid": devid}
        mode_val = REVERSE_LIFESMART_HVAC_MODE_MAP.get(hvac_mode)
        if mode_val is not None and device_type in [
            "SL_UACCB",
            "SL_NATURE",
            "SL_FCU",
            "V_AIR_P",
        ]:
            args.update(
                {
                    "key": "MODE" if device_type == "V_AIR_P" else "P7",
                    "type": CMD_TYPE_SET_CONFIG,
                    "val": mode_val,
                }
            )
        elif device_type == "SL_CP_AIR":
            mode_val = REVERSE_LIFESMART_CP_AIR_MODE_MAP.get(hvac_mode)
            if mode_val is not None:
                new_val = (current_val & ~(0b11 << 13)) | (mode_val << 13)
                args.update({"key": "P1", "type": CMD_TYPE_SET_RAW, "val": new_val})
        elif device_type == "SL_CP_DN":
            is_auto = 1 if hvac_mode == HVACMode.AUTO else 0
            new_val = (current_val & ~(1 << 31)) | (is_auto << 31)
            args.update({"key": "P1", "type": CMD_TYPE_SET_RAW, "val": new_val})
        elif device_type == "SL_CP_VL":
            mode_map = {HVACMode.HEAT: 0, HVACMode.AUTO: 2}
            mode_val = mode_map.get(hvac_mode, 0)
            new_val = (current_val & ~(0b11 << 1)) | (mode_val << 1)
            args.update({"key": "P1", "type": CMD_TYPE_SET_RAW, "val": new_val})
        return self._build_packet(args)

    def build_climate_temperature_packet(
        self, devid: str, temp: float, device_type: str
    ) -> bytes:
        """构建设置温控器目标温度的指令包。"""
        temp_val = int(temp * 10)
        idx_map = {
            "V_AIR_P": ("tT", CMD_TYPE_SET_TEMP_DECIMAL),
            "SL_UACCB": ("P3", CMD_TYPE_SET_TEMP_DECIMAL),
            "SL_CP_DN": ("P3", CMD_TYPE_SET_RAW),
            "SL_CP_AIR": ("P4", CMD_TYPE_SET_RAW),
            "SL_NATURE": ("P8", CMD_TYPE_SET_TEMP_DECIMAL),
            "SL_FCU": ("P8", CMD_TYPE_SET_TEMP_FCU),
            "SL_CP_VL": ("P3", CMD_TYPE_SET_RAW),
        }
        if device_type in idx_map:
            idx, cmd_type = idx_map[device_type]
            args = {"devid": devid, "key": idx, "type": cmd_type, "val": temp_val}
            return self._build_packet(args)
        return b""

    def build_climate_fan_mode_packet(
        self, devid: str, fan_mode: str, current_val: int, device_type: str
    ) -> bytes:
        """构建设置温控器风扇模式的指令包。"""
        args = {"devid": devid}
        if device_type == "V_AIR_P":
            fan_val = LIFESMART_F_FAN_MODE_MAP.get(fan_mode)
            args.update({"key": "F", "type": CMD_TYPE_SET_CONFIG, "val": fan_val})
        elif device_type == "SL_TR_ACIPM":
            fan_val = REVERSE_LIFESMART_ACIPM_FAN_MAP.get(fan_mode)
            args.update({"key": "P2", "type": CMD_TYPE_SET_RAW, "val": fan_val})
        elif device_type in ["SL_NATURE", "SL_FCU"]:
            fan_val = REVERSE_LIFESMART_TF_FAN_MODE_MAP.get(fan_mode)
            args.update({"key": "P9", "type": CMD_TYPE_SET_CONFIG, "val": fan_val})
        elif device_type == "SL_CP_AIR":
            fan_val = REVERSE_LIFESMART_CP_AIR_FAN_MAP.get(fan_mode)
            if fan_val is not None:
                new_val = (current_val & ~(0b11 << 15)) | (fan_val << 15)
                args.update({"key": "P1", "type": CMD_TYPE_SET_RAW, "val": new_val})
        if "val" in args:
            return self._build_packet(args)
        return b""

    def build_epset_packet(
        self, devid: str, idx: str, command_type: str, val: Any
    ) -> bytes:
        """构建一个标准的单IO口控制指令包 (EpSet)。"""
        args = {
            "val": val,
            "valtag": "m",
            "devid": devid,
            "key": idx,  # 本地协议使用 'key'
            "type": command_type,
        }
        return self._build_packet(args)

    def build_multi_epset_packet(self, devid: str, io_list: list[dict]) -> bytes:
        """构建一个多IO口同时控制的指令包 (EpSet)。"""
        # 本地协议通过将IO口列表作为val字段的值来实现多点控制
        # 翻译 io_list 中的 'idx' 为 'key'
        translated_io_list = []
        for item in io_list:
            new_item = item.copy()
            if SUBDEVICE_INDEX_KEY in new_item:
                new_item["key"] = new_item.pop(SUBDEVICE_INDEX_KEY)
            translated_io_list.append(new_item)

        args = {
            "val": translated_io_list,
            "valtag": "m",
            "devid": devid,
        }
        return self._build_packet(args)

    def build_change_icon_packet(self, devid: str, icon: str) -> bytes:
        """构建修改设备图标的指令包。"""
        args = {"icon": icon}
        node_suffix = f"/me/ep/{devid}"
        return self._build_packet(args, act="enum:92", node_suffix=node_suffix)

    def build_add_trigger_packet(self, trigger_name: str, cmdlist: str) -> bytes:
        """构建添加触发器的指令包。"""
        args = {
            "cmdlist": cmdlist,
            "_": "trigger",
            "name": "enum:1",
            "enum:13": trigger_name,
        }
        node_suffix = f"{self.node}/me/ai"
        return self._build_packet(args, act="AddA", node_suffix=node_suffix)

    def build_del_ai_packet(self, ai_name: str) -> bytes:
        """构建删除AI（场景或触发器）的指令包。"""
        args = {
            "cmdlist": "enum:1",
            "enum:13": ai_name,
        }
        node_suffix = f"{self.node}/me/ai"
        return self._build_packet(args, act="DelA", node_suffix=node_suffix)

    def build_ir_control_packet(self, devid: str, opt: dict) -> bytes:
        """构建红外控制（运行AI场景）的指令包。"""
        args = {"opt": opt, "cron_name": f"AI_IR_{devid}"}
        return self._build_packet(args, act="RunA", node_suffix="/ai")

    def build_send_code_packet(self, devid: str, data: list | bytes) -> bytes:
        """构建发送原始红外码的指令包。"""
        if isinstance(data, list):
            data.insert(0, "C*")
            data = bytes(data)
        args = {
            "ctrlcmd": "sendcode",
            "enum:valtag": "m",
            "cmd": "ctrl",
            "enum:devid": devid,
            "param": {"enum:type": 1, "data": data},
        }
        return self._build_packet(args, act="epCmdA")

    def build_ir_raw_control_packet(self, devid: str, datas: str) -> bytes:
        """构建发送原始红外控制数据的指令包。"""
        args = {
            "data": json.loads(datas),
            "devid": devid,
            "key": "193",
            "cmd": 0,
        }
        return self._build_packet(args, act="rfSetVarA")

    def build_set_eeprom_packet(self, devid: str, key: str, val: Any) -> bytes:
        """构建设置设备EEPROM的指令包。"""
        args = {
            "type": 255,
            "valtag": "m",
            "devid": devid,
            "key": key,
            "val": val,
        }
        return self._build_packet(args, act="rfSetEEPromA")

    def build_add_timer_packet(self, devid: str, croninfo: str, key: str) -> bytes:
        """构建添加设备定时器的指令包。"""
        args = {
            "cmdlist": f"SCHDEF({{pause=false;}},'0 {croninfo} *',SET,io,'/ep/{devid}',{{{key}}});",
            "enum:13": f"sys_sch_{devid}_CL",
        }
        node_suffix = f"{self.node}/me/ai"
        return self._build_packet(args, act="SetA", node_suffix=node_suffix)

    def build_press_switch_packet(
        self, devid: str, idx: str, duration_val: int
    ) -> bytes:
        """构建点动开关指令包。"""
        args = {
            "val": duration_val,
            "valtag": "m",
            "devid": devid,
            "key": idx,  # 本地协议使用 'key'
            "type": CMD_TYPE_PRESS,
        }
        return self._build_packet(args)

    def build_scene_trigger_packet(self, scene_id: str) -> bytes:
        """构建触发场景的指令包。"""
        args = {"id": scene_id}
        return self._build_packet(args, act="SceneSet", node_suffix="")

    def build_send_ir_keys_packet(
        self, ai: str, devid: str, category: str, brand: str, keys: str
    ) -> bytes:
        """构建发送红外按键的指令包。"""
        # 注意：本地协议的红外控制与云端API不同，通常通过运行AI场景实现
        # 此处我们模拟云端API的行为，通过运行一个预定义的AI场景来发送按键
        # AI名称格式通常为 AI_IR_{me}_{key}
        # 为简化，本地模式下我们直接使用 RunA
        args = {
            "opt": {"keys": json.loads(keys)},
            "cron_name": ai,
            "devid": devid,
            "category": category,
            "brand": brand,
        }
        return self._build_packet(args, act="RunA", node_suffix="/ai")


class LifeSmartLocalClient:
    """LifeSmart 本地客户端，负责与中枢进行 TCP 通信。"""

    def __init__(self, host, port, username, password, config_agt=None) -> None:
        """初始化本地客户端。"""
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.config_agt = config_agt
        self.reader, self.writer = None, None
        self._proto = LifeSmartProtocol()
        self._factory: LifeSmartPacketFactory | None = None
        self.disconnected = False
        self.device_ready = asyncio.Event()
        self.devices = {}
        self.node = ""
        self.node_agt = ""
        self._attr_mapping = {
            "M": "motion",
            "VU": "volt_USB",
            "V": "volt_Battery",
            "C": "charge",
            "T": "templature",
            "H": "humidity",
            "Z": "light",
            "O": "switch",
            "G": "gate",
            "OP": "OP",
            "ST": "ST",
            "CL": "CL",
        }

    def get_attr_name(self, field: str) -> str:
        """根据设备返回的字段名获取对应的友好属性名。"""
        return self._attr_mapping.get(field, field)

    def get_item_attrs(self, item: dict) -> dict:
        """解析设备状态字典，返回格式化的属性字典。"""
        rc = {}
        for field, value in item.items():
            if field == "RGBW":
                rc_key = f"{self._attr_mapping.get(field, field)}:TYPE"
                rc[rc_key] = value["type"]
            rc_key = self.get_attr_name(field)
            rc[rc_key] = value["val"]
        return rc

    async def check_login(self):
        """检查登录凭据是否有效。"""
        self.reader, self.writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port), timeout=5
        )

        pkt = self._proto.encode(
            [
                {"_sel": 1, "sn": 1, "req": False},
                {
                    "args": {
                        "cid": "6D56899B-82DA-403D-8291-50B57EE05DBA",
                        "cver": "1.0.48p1",
                        "uid": self.username,
                        "nick": "admin",
                        "cname": "LifeSmart",
                        "pwd": self.password,
                    },
                    "node": "A3MAAABaAEkBRzQ0Mzc0OA/ac",
                    "act": "Login",
                },
            ]
        )
        self.writer.write(pkt)
        await self.writer.drain()

        response = b""
        while not self.disconnected:
            buf = await self.reader.read(4096)
            if not buf:
                self.writer.close()
                await self.writer.wait_closed()
                raise asyncio.TimeoutError
            response += buf
            if response:
                try:
                    _, decoded = self._proto.decode(response)
                    if decoded and decoded[1].get("ret", None) is None:
                        _LOGGER.error("本地登录失败 -> %s", decoded[1].get("err"))
                        raise asyncio.InvalidStateError
                    else:
                        break
                except EOFError:
                    pass
        self.writer.close()
        await self.writer.wait_closed()
        return True

    async def get_all_device_async(self, timeout=5):
        """异步获取所有设备数据，带超时控制。"""
        try:
            await asyncio.wait_for(self.device_ready.wait(), timeout=timeout)
            return list(self.devices.values())
        except asyncio.TimeoutError as e:
            _LOGGER.error("获取本地设备超时: %s", e)
            return False

    async def async_connect(self, callback: None | Callable):
        """主连接循环，负责登录、获取设备和监听状态更新。"""
        while not self.disconnected:
            try:
                self.reader, self.writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port), timeout=5
                )

                # 阶段1: 登录
                pkt_factory = LifeSmartPacketFactory("", "")
                pkt = pkt_factory.build_login_packet(self.username, self.password)
                self.writer.write(pkt)
                await self.writer.drain()

                response = b""
                stage = "login"
                while not self.disconnected:
                    buf = await self.reader.read(4096)
                    if not buf:
                        if self.writer:
                            self.writer.close()
                            await self.writer.wait_closed()
                        if self.disconnected:
                            return None
                        raise asyncio.TimeoutError
                    response += buf
                    if response:
                        try:
                            response, decoded = self._proto.decode(response)
                            if not decoded:
                                continue

                            if stage == "login":
                                if decoded[1].get("ret", None) is None:
                                    _LOGGER.error(
                                        "本地登录失败 -> %s", decoded[1].get("err")
                                    )
                                    self.disconnected = True
                                else:
                                    self.node = decoded[1]["ret"][4]["base"][1]
                                    self.node_agt = decoded[1]["ret"][4]["agt"][1]
                                    self._factory = LifeSmartPacketFactory(
                                        self.node_agt, self.node
                                    )
                                    stage = "loading"
                                    # 阶段2: 获取设备
                                    pkt = self._factory.build_get_config_packet(
                                        self.node
                                    )
                                    self.writer.write(pkt)
                                    await self.writer.drain()
                            elif stage == "loading":
                                payload = decoded[1]["ret"][1]
                                self.devices = {}
                                for devid, dev in payload["eps"].items():
                                    dev_meta = {
                                        "me": devid,
                                        "devtype": (
                                            dev["cls"][:-3]
                                            if dev["cls"][-3:-1] == "_V"
                                            else dev["cls"]
                                        ),
                                        "agt": self.node_agt,
                                        "name": dev["name"],
                                        "data": dev["_chd"]["m"]["_chd"],
                                    }
                                    dev_meta.update(dev)
                                    del dev_meta["_chd"]
                                    self.devices[devid] = dev_meta
                                self.device_ready.set()
                                stage = "loaded"
                            else:
                                # 阶段3: 监听更新
                                if schg := decoded[1].get("_schg", None):
                                    for schg_key, schg_data in schg.items():
                                        if schg_key.startswith(f"{self.node_agt}/ep/"):
                                            parts = schg_key.split("/")
                                            if len(parts) >= 4:
                                                dev_id, _, sub_key = (
                                                    parts[2],
                                                    parts[3],
                                                    parts[4],
                                                )
                                                if dev_id in self.devices:
                                                    self.devices[dev_id][
                                                        "data"
                                                    ].setdefault(sub_key, {})
                                                    self.devices[dev_id]["data"][
                                                        sub_key
                                                    ].update(schg_data["chg"])
                                                    if callback and callable(callback):
                                                        msg = {
                                                            "me": dev_id,
                                                            "idx": sub_key,
                                                            "agt": self.node_agt,
                                                            "devtype": self.devices[
                                                                dev_id
                                                            ]["devtype"],
                                                        }
                                                        msg.update(
                                                            self.devices[dev_id][
                                                                "data"
                                                            ][sub_key]
                                                        )
                                                        callback({"msg": msg})
                                                else:
                                                    if callback and callable(callback):
                                                        callback({"reload": True})
                                                    _LOGGER.warning(
                                                        "设备 %s 无效，将重新加载。",
                                                        dev_id,
                                                    )
                                elif len(decoded[1].get("_sdel", {}).values()) > 0:
                                    if callback and callable(callback):
                                        callback({"reload": True})
                                    _LOGGER.warning("设备被删除，将重新加载。")
                        except EOFError:
                            pass
                if self.writer:
                    self.writer.close()
                    await self.writer.wait_closed()
            except (
                ConnectionResetError,
                asyncio.TimeoutError,
                ConnectionRefusedError,
                OSError,
            ) as e:
                _LOGGER.warning(
                    "本地连接失败: %s: %s，将稍后重试。", e.__class__.__name__, str(e)
                )
                if self.writer:
                    self.writer.close()
                await asyncio.sleep(5.0)

    async def async_disconnect(self, call: Event | ServiceCall | None):
        """断开与本地中枢的连接。"""
        self.disconnected = True
        if self.writer is not None:
            self.writer.close()
            await self.writer.wait_closed()
            self.writer = None

    async def _send_packet(self, packet: bytes):
        """一个集中的方法，用于发送已构建好的指令包。"""
        if self.writer and not self.writer.is_closing():
            self.writer.write(packet)
            await self.writer.drain()
            return 0
        _LOGGER.error("本地客户端未连接，无法发送指令。")
        return -1

    # --- 与云端客户端对齐的控制方法 ---

    async def turn_on_light_switch_async(self, idx: str, agt: str, me: str) -> int:
        """开启一个灯或开关。"""
        pkt = self._factory.build_switch_packet(me, idx, True)
        return await self._send_packet(pkt)

    async def turn_off_light_switch_async(self, idx: str, agt: str, me: str) -> int:
        """关闭一个灯或开关。"""
        pkt = self._factory.build_switch_packet(me, idx, False)
        return await self._send_packet(pkt)

    async def send_epset_async(
        self, agt: str, me: str, idx: str, command_type: str, val: Any
    ) -> int:
        """向本地设备端点发送通用命令。"""
        # agt 在本地模式下未使用，但为了保持签名一致而保留
        pkt = self._factory.build_epset_packet(me, idx, command_type, val)
        return await self._send_packet(pkt)

    async def async_set_multi_ep_async(
        self, agt: str, me: str, io_list: list[dict]
    ) -> int:
        """向本地设备端点同时发送多个IO口的命令。"""
        # agt 在本地模式下未使用，但为了保持签名一致而保留
        pkt = self._factory.build_multi_epset_packet(me, io_list)
        return await self._send_packet(pkt)

    async def open_cover_async(self, agt: str, me: str, device_type: str) -> int:
        """开启窗帘或车库门。"""
        idx = (
            "P3"
            if device_type in GARAGE_DOOR_TYPES
            else (
                "P2"
                if device_type in DOOYA_TYPES
                else "OP" if device_type == "SL_SW_WIN" else "P1"
            )
        )
        pkt = self._factory.build_cover_command_packet(me, idx, "open", device_type)
        return await self._send_packet(pkt)

    async def close_cover_async(self, agt: str, me: str, device_type: str) -> int:
        """关闭窗帘或车库门。"""
        idx = (
            "P3"
            if device_type in GARAGE_DOOR_TYPES
            else (
                "P2"
                if device_type in DOOYA_TYPES
                else "CL" if device_type == "SL_SW_WIN" else "P2"
            )
        )
        pkt = self._factory.build_cover_command_packet(me, idx, "close", device_type)
        return await self._send_packet(pkt)

    async def stop_cover_async(self, agt: str, me: str, device_type: str) -> int:
        """停止窗帘或车库门。"""
        idx = (
            "P3"
            if device_type in GARAGE_DOOR_TYPES
            else (
                "P2"
                if device_type in DOOYA_TYPES
                else "ST" if device_type == "SL_SW_WIN" else "P3"
            )
        )
        pkt = self._factory.build_cover_command_packet(me, idx, "stop", device_type)
        return await self._send_packet(pkt)

    async def set_cover_position_async(
        self, agt: str, me: str, position: int, device_type: str
    ) -> int:
        """设置窗帘或车库门到指定位置。"""
        idx = "P3" if device_type in GARAGE_DOOR_TYPES else "P2"
        pkt = self._factory.build_cover_position_packet(me, idx, position)
        return await self._send_packet(pkt)

    async def async_set_climate_hvac_mode(
        self,
        agt: str,
        me: str,
        device_type: str,
        hvac_mode: HVACMode,
        current_val: int = 0,
    ) -> int:
        """设置温控设备的 HVAC 模式。"""
        pkt = self._factory.build_climate_hvac_mode_packet(
            me, hvac_mode, current_val, device_type
        )
        return await self._send_packet(pkt)

    async def async_set_climate_temperature(
        self, agt: str, me: str, device_type: str, temp: float
    ) -> int:
        """设置温控设备的目标温度。"""
        pkt = self._factory.build_climate_temperature_packet(me, temp, device_type)
        return await self._send_packet(pkt)

    async def async_set_climate_fan_mode(
        self, agt: str, me: str, device_type: str, fan_mode: str, current_val: int = 0
    ) -> int:
        """设置温控设备的风扇模式。"""
        pkt = self._factory.build_climate_fan_mode_packet(
            me, fan_mode, current_val, device_type
        )
        return await self._send_packet(pkt)

    async def press_switch_async(
        self, idx: str, agt: str, me: str, duration_ms: int
    ) -> int:
        """执行本地模式的点动操作。"""
        val = max(1, round(duration_ms / 100))
        pkt = self._factory.build_press_switch_packet(me, idx, val)
        return await self._send_packet(pkt)

    async def set_scene_async(self, agt: str, scene_id: str) -> int:
        """激活一个本地场景。"""
        pkt = self._factory.build_scene_trigger_packet(scene_id)
        # 本地协议的返回不是code，但为保持一致性，成功发送返回0
        await self._send_packet(pkt)
        return 0

    async def send_ir_key_async(
        self, agt: str, ai: str, me: str, category: str, brand: str, keys: str
    ) -> int:
        """发送一个本地红外按键命令。"""
        pkt = self._factory.build_send_ir_keys_packet(ai, me, category, brand, keys)
        await self._send_packet(pkt)
        return 0
