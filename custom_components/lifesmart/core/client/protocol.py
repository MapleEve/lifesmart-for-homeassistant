"""由 @MagicBear 实现的 LifeSmart 本地协议解析与客户端。 @MapleEve 进行重构

此模块提供了一个纯粹的协议处理库，不涉及任何网络I/O。包含两个核心部分：
- LifeSmartProtocol: 负责二进制数据的编码与解码。
- LifeSmartPacketFactory: 负责构建各种控制指令的数据包。
"""

import gzip
import json
import logging
import struct
from collections import OrderedDict
from dataclasses import dataclass
from io import BytesIO
from typing import Any

from ..const import (
    # --- 核心常量 ---
    CMD_TYPE_SET_RAW_ON,
    SUBDEVICE_INDEX_KEY,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class LSTimestamp:
    """用于表示 LifeSmart 协议中时间戳对象的数据类。"""

    index: int
    value: int
    raw_data: bytes

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
            return obj.value
        return list(obj) if isinstance(obj, bytes) else super().default(obj)


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
        self.debug = debug

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
        value, shift = 0, 0
        while True:
            byte = stream.read(1)
            if not byte:
                # 如果我们期望读取一个字节但流已耗尽，这总是一个错误。
                # 这同时覆盖了“初始流为空”和“多字节varint不完整”两种情况。
                raise EOFError("Incomplete varint data in stream.")
            b = ord(byte)
            value |= (b & 0x7F) << shift
            if not (b & 0x80):
                break
            shift += 7
        return value

    def _string_to_bin(self, value):
        """将字符串编码为二进制格式。"""
        encoded_str = value.encode("utf-8")
        return b"\x11" + self._encode_varint(len(encoded_str)) + encoded_str

    def _pack_value(self, value, isKey=False):
        """递归地将 Python 对象打包成二进制格式。"""

        if isinstance(value, bool):  # 处理布尔值
            return b"\x02" if value else b"\x03"

        if isinstance(value, int):  # 处理整数
            if not -0x80000000 <= value <= 0x7FFFFFFF:
                raise ValueError(f"int 超出 32-bit 有符号范围: {value}")
            zz = (value << 1) ^ (value >> 31)
            return b"\x04" + self._encode_varint(zz)

        if isinstance(value, str):  # 处理字符串
            if value == "::NULL::":
                return b"\x11\x08::NULL::"
            if value.startswith("enum:"):
                key = value[5:]
                enum_id = self.REVERSE_KEY_MAPPING.get(key)
                if enum_id is not None:
                    return struct.pack("BB", 0x13, enum_id)
                # 如果没有找到对应的enum_id，则作为普通字符串处理
                return self._string_to_bin(value)
            if isKey and self.REVERSE_KEY_MAPPING.get(value):
                enum_id = self.REVERSE_KEY_MAPPING.get(value)
                return struct.pack("BB", 0x13, enum_id)
            return self._string_to_bin(value)

        if isinstance(value, bytes):  # 处理字节串
            # 像处理字符串一样，添加类型码(0x11)和长度，然后附加原始字节
            return b"\x11" + self._encode_varint(len(value)) + value

        if isinstance(value, list):  # 处理列表
            if not value:
                return b"\x01"
            data = b"\x12" + struct.pack("B", len(value))
            for i, item in enumerate(value):
                data += self._pack_value(i) + self._pack_value(item)
            return data

        if isinstance(value, dict):  # 处理字典
            data = b"\x12" + struct.pack("B", len(value))
            for k, v in value.items():
                data += self._pack_value(k, True) + self._pack_value(v)
            return data

        if value is None:
            return b"\x00"
        _LOGGER.warning("不支持的打包类型: %s", type(value))
        return b""

    def encode(self, parts):
        """将多个部分编码成一个完整的 LifeSmart 数据包。"""
        header, data = b"GL00\x00\x00", b""
        for part in parts:
            packed = self._pack_value(part)
            # 官方文档要求顶级列表中的每个元素（必须是字典）都被移除类型头
            # 这里假设 _pack_value 返回的第一个字节始终是类型头（如 0x12），否则抛出异常
            if not packed or len(packed) < 2:
                raise ValueError("_pack_value 返回的内容过短，无法移除类型头")
            # 检查类型头是否为预期的字典类型（0x12），如有需要可调整
            if packed[0] != 0x12:
                raise ValueError(
                    f"_pack_value 返回的类型头不是预期的 0x12，而是 {packed[0]:#x}"
                )
            data += packed[1:]
        pkt = header + struct.pack(">I", len(data)) + data
        if len(pkt) >= 1000:
            compressed = gzip.compress(pkt)
            return b"ZZ00\x00\x00" + struct.pack(">I", len(pkt)) + compressed
        return pkt

    def _parse_value(self, stream, data_type, call_stack=""):
        """递归地从字节流中解析出 Python 对象。"""
        try:
            if data_type == 0x01:  # 识别空列表的特殊标记
                return []

            if data_type == 0x00:  # NULL
                return None

            elif data_type == 0x02:  # True
                return True

            elif data_type == 0x03:  # False
                return False

            elif data_type == 0x04:  # Integer
                zz = self._decode_varint(stream)
                return (zz >> 1) ^ -(zz & 1)  # 反 ZigZag

            if data_type == 0x05:  # HEX类型处理
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
                zz = self._decode_varint(stream)
                value = (zz >> 1) ^ -(zz & 1)
                return LSTimestamp(index=index, value=value, raw_data=b"")

            elif data_type == 0x11:  # String or Bytes
                length = self._decode_varint(stream)
                raw = stream.read(length)
                if len(raw) != length:
                    raise EOFError("字符串数据不足")

                try:
                    # 优先尝试解码为UTF-8字符串
                    return raw.decode("utf-8")
                except UnicodeDecodeError:
                    # 如果解码失败，说明它很可能不是一个字符串，而是原始的二进制数据
                    _LOGGER.debug("UTF-8解码失败，将数据作为原始bytes返回: %s", raw)
                    return raw

            elif data_type == 0x12:  # Array/Dict
                count = ord(stream.read(1))
                items = []
                for i in range(count):
                    if stream.tell() >= len(stream.getvalue()):
                        raise EOFError(f"解析第{i + 1}/{count}个键时数据流提前结束")
                    key_type = ord(stream.read(1))
                    key = self._parse_value(stream, key_type, f"{call_stack}[{i}].key")
                    if stream.tell() >= len(stream.getvalue()):
                        raise EOFError(f"解析第{i + 1}/{count}个值时数据流提前结束")
                    value_type = ord(stream.read(1))
                    value = self._parse_value(
                        stream, value_type, f"{call_stack}[{i}].val"
                    )
                    items.append((key, value))
                keys = [k for k, _ in items]
                is_list = (
                    count > 0
                    and all(isinstance(k, int) for k in keys)
                    and keys == list(range(count))
                )
                return [v for _, v in items] if is_list else dict(items)
            if data_type == 0x13:
                if stream.tell() + 1 > len(stream.getvalue()):
                    raise EOFError("数据意外结束")
                enum_id = ord(stream.read(1))
                return f"enum:{self.KEY_MAPPING.get(enum_id, enum_id)}"
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
            if len(data) < 10:
                raise EOFError("数据包不完整 (至少需要 10 字节)")
            header = data[:4]
            # 统一从字节 6-10 读取长度
            pkt_len = struct.unpack(">I", data[6:10])[0]

            if header == b"ZZ00":  # 压缩包处理
                # 在我们的 encode 实现中，pkt_len 是未压缩数据的长度。
                # 压缩数据从字节 10 开始，直到数据流结束。
                compressed_data = data[10:]
                try:
                    decompressed = gzip.decompress(compressed_data)
                    if len(decompressed) != pkt_len:
                        _LOGGER.warning(
                            "解压后尺寸不匹配 (预期 %d, 实际 %d)",
                            pkt_len,
                            len(decompressed),
                        )
                except (OSError, gzip.BadGzipFile) as e:
                    raise ValueError(f"解压失败: {str(e)}") from e

                # 递归解码解压后的数据 (它是一个 GL00 包)
                # 整个压缩包都被消耗掉了
                _, structure = self.decode(decompressed)
                return b"", structure

            elif header == b"GL00":  # 标准包处理
                total_length = 10 + pkt_len
                if len(original_data) < total_length:
                    raise EOFError(f"数据包长度不匹配 (需要 {total_length} 字节)")
                packet_data = original_data[10:total_length]
                remaining_data = original_data[total_length:]
                stream = BytesIO(packet_data)
                result = []
                while stream.tell() < len(packet_data):
                    # 官方要求每个块都是一个字典
                    # _parse_value 会处理读取类型、长度和内容
                    parsed = self._parse_value(stream, 0x12)
                    result.append(parsed)
                return remaining_data, self._normalize_structure(result)
            raise ValueError(f"未知的包头: {header.hex()}")
        except EOFError as e:
            _LOGGER.debug("解码时遇到 EOF: %s", str(e))
            raise
        except Exception as e:
            _LOGGER.error("解码时出错: %s", str(e), exc_info=True)
            raise

    def _normalize_key(self, key):
        """确保字典键为基本类型。"""
        if isinstance(key, (str, int, float, bool, type(None))):
            return key
        try:
            return str(key)
        except Exception:
            return "invalid_key"

    def _normalize_structure(self, data):
        """递归地将数据结构规范化：
        1. 将 OrderedDict 转换为标准 dict。
        2. 将 LSTimestamp 对象转换为其整数值。
        3. 确保所有字典键都是可哈希的，并移除 'enum:' 前缀。
        """
        if isinstance(data, (dict, OrderedDict)):
            normalized_dict = {}
            for k, v in data.items():
                normalized_key = self._normalize_key(k)
                if isinstance(normalized_key, str) and normalized_key.startswith(
                    "enum:"
                ):
                    normalized_key = normalized_key[5:]
                normalized_dict[normalized_key] = self._normalize_structure(v)
            return normalized_dict
        if isinstance(data, list):
            return [self._normalize_structure(item) for item in data]
        if isinstance(data, LSTimestamp):
            return data.value
        return data[5:] if isinstance(data, str) and data.startswith("enum:") else data


class LifeSmartPacketFactory:
    """LifeSmart 本地协议的指令包工厂。

    此类不直接与网络通信，它的唯一职责是构建各种控制命令的二进制数据包。
    """

    def __init__(self, node_agt: str, node: str = ""):
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
            {"args": args, "node": f"{self.node_agt}{node_suffix}", "act": act},
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

    def build_epset_packet(
        self, devid: str, idx: str, command_type: int, val: Any
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
        args = {"val": translated_io_list, "valtag": "m", "devid": devid}
        return self._build_packet(args)

    def build_change_icon_packet(self, devid: str, icon: str) -> bytes:
        """构建修改设备图标的指令包。"""
        args = {"icon": icon}
        return self._build_packet(args, act="enum:92", node_suffix=f"/me/ep/{devid}")

    def build_add_scene_packet(self, scene_name: str, cmdlist: str) -> bytes:
        """构建添加场景触发器的指令包。"""
        args = {
            "cmdlist": cmdlist,
            "_": "trigger",
            "name": "enum:1",
            "enum:13": scene_name,
        }
        return self._build_packet(args, act="AddA", node_suffix=f"{self.node}/me/ai")

    def build_delete_scene_packet(self, scene_name: str) -> bytes:
        """构建删除场景（AI）的指令包。"""
        args = {"cmdlist": "enum:1", "enum:13": scene_name}
        return self._build_packet(args, act="DelA", node_suffix=f"{self.node}/me/ai")

    def build_ir_control_packet(self, devid: str, opt: dict) -> bytes:
        """构建红外控制（运行AI场景）的指令包。"""
        args = {"opt": opt, "cron_name": f"AI_IR_{devid}"}
        return self._build_packet(args, act="RunA", node_suffix="/ai")

    def build_set_scene_packet(self, scene_name: str) -> bytes:
        """构建运行场景（通过RunA执行AI场景）的指令包。"""
        args = {"cron_name": scene_name}
        return self._build_packet(args, act="RunA", node_suffix="/ai")

    def build_send_code_packet(self, devid: str, data: list | bytes) -> bytes:
        """构建发送原始红外码的指令包。"""
        if isinstance(data, list):
            data = "C*".encode("ascii") + bytes(data)
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
        args = {"data": json.loads(datas), "devid": devid, "key": "193", "cmd": 0}
        return self._build_packet(args, act="rfSetVarA")

    def build_set_eeprom_packet(self, devid: str, key: str, val: Any) -> bytes:
        """构建设置设备EEPROM的指令包。"""
        args = {
            "type": CMD_TYPE_SET_RAW_ON,
            "valtag": "m",
            "devid": devid,
            "key": key,
            "val": val,
        }
        return self._build_packet(args, act="rfSetEEPromA")

    def build_add_timer_packet(self, devid: str, croninfo: str, key: str) -> bytes:
        """构建添加设备定时器的指令包。"""
        args = {
            "cmdlist": (
                f"SCHDEF({{pause=false;}},'0 {croninfo} *',"
                f"SET,io,'/ep/{devid}',{{{key}}});"
            ),
            "enum:13": f"sys_sch_{devid}_CL",
        }
        return self._build_packet(args, act="SetA", node_suffix=f"{self.node}/me/ai")
