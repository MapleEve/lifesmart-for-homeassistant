import asyncio
import gzip
import json
import logging
import struct
from collections import OrderedDict
from dataclasses import dataclass
from io import BytesIO
from typing import Callable

from homeassistant.core import Event, ServiceCall

_LOGGER = logging.getLogger(__name__)


@dataclass
class LSTimestamp:
    index: int
    value: int
    raw_data: bytes

    # @property
    # def datetime(self) -> datetime.datetime:
    #     """转换为datetime对象"""
    #     return datetime.datetime.fromtimestamp(self.value, tz=self.timezone)

    def as_dict(self) -> dict:
        """转换为字典格式（兼容旧代码）"""
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
    """自定义JSON编码器"""

    def default(self, obj):
        if isinstance(obj, LSTimestamp):
            return str(obj)
        if isinstance(obj, bytes):
            return list(obj)
        return super().default(obj)


class LifeSmartProtocol:
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
        self.decode_context = "binary"
        self.decode_direct_output = False
        self._offset = None
        self.need_bytes = 0

    @staticmethod
    def _encode_varint(value):
        data = bytearray()
        while value >= 128:
            data.append((value & 0x7F) | 0x80)
            value >>= 7
        data.append(value)
        return bytes(data)

    @staticmethod
    def _decode_varint(stream):
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
        data = b"\x11"
        data += self._encode_varint(len(value))
        data += value.encode("utf-8")
        return data

    def _pack_value(self, value, isKey=False):
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
            _LOGGER.warning("Unsupported type: %s", type(value))
            return b""

    def encode(self, parts):
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
        try:
            if data_type == 0x00:  # NULL
                return None

            elif data_type == 0x02:  # True
                return True

            elif data_type == 0x03:  # False
                return False

            elif data_type == 0x04:  # Integer
                varint = self._decode_varint(stream)
                # 处理32位系统的大整数问题
                if varint & 1:
                    result = -((varint >> 1) + 1)
                else:
                    result = varint >> 1
                return result if result <= 0x7FFFFFFF else result - 0x100000000

            elif data_type == 0x05:  # HEX类型处理
                start_pos = stream.tell()

                # 读取索引字节
                index = stream.read(1)
                if len(index) < 1:
                    raise EOFError("Missing index byte")
                index = index[0]

                # 读取HEX数据
                hex_data = stream.read(8)
                if len(hex_data) < 8:
                    raise EOFError(
                        f"HEX data incomplete, need 8 bytes got {len(hex_data)}"
                    )

                # 调试输出
                if self.debug:
                    stream.seek(start_pos)
                    debug_data = stream.read(9)
                    stream.seek(start_pos)
                    self._dump_decode_value(debug_data)
                    print(f"\033[31mpack index: 0x{index:02x}\033[0m hex (len: 8)")
                    if self.debug_level > 1:
                        print(f"0x{start_pos+5:08x}: ", end="")
                        self._dump_decode_value(hex_data[:4])

                # 处理长度判断
                return {
                    "type": "HEX",
                    "index": index,
                    "value": hex_data.hex(),
                    "raw": hex_data,
                }

            elif data_type == 0x06:  # 时间戳类型处理
                start_pos = stream.tell()

                # 读取索引字节
                index = stream.read(1)
                if len(index) < 1:
                    raise EOFError("Missing index byte")
                index = index[0]

                # 解码变长整数
                int_value = 0
                shift = 0
                intlen = 0
                while True:
                    byte = stream.read(1)
                    if len(byte) < 1:
                        raise EOFError("Unexpected end of varint")
                    int_value |= (byte[0] & 0x7F) << shift
                    shift += 7
                    intlen += 1
                    if not (byte[0] & 0x80):
                        break

                # 处理符号和数值
                sign = -1 if (int_value & 0x1) else 1
                final_value = (int_value >> 1) * sign

                # 调试输出
                if self.debug:
                    stream.seek(start_pos)
                    debug_data = stream.read(7)
                    stream.seek(start_pos)
                    self._dump_decode_value(debug_data)
                    print(
                        f"\033[32mpack index: 0x{index:02x}\033[0m time value: {final_value} intlen = {intlen}"
                    )

                return LSTimestamp(
                    index=index,
                    value=final_value,
                    raw_data=int_value.to_bytes(
                        (int_value.bit_length() + 7) // 8, "big"
                    ),
                )

            elif data_type == 0x11:  # String
                length = self._decode_varint(stream)
                # 检查字符串长度有效性
                if length < 0 or stream.tell() + length > len(stream.getvalue()):
                    raise ValueError("Invalid string length")
                return stream.read(length).decode("utf-8", errors="replace")

            elif data_type == 0x12:  # Array/Dict
                if stream.tell() + 1 > len(stream.getvalue()):
                    raise EOFError("Unexpected end of data")

                count = ord(stream.read(1))
                is_dict = False
                items = []

                for _ in range(count):
                    # 解析键
                    if stream.tell() + 1 > len(stream.getvalue()):
                        break
                    key_type = ord(stream.read(1))
                    key = self._parse_value(stream, key_type, call_stack + ".")

                    # 解析值
                    if stream.tell() + 1 > len(stream.getvalue()):
                        break
                    value_type = ord(stream.read(1))
                    value = self._parse_value(
                        stream, value_type, call_stack + ".%s" % key
                    )

                    # 检查键是否为可哈希类型
                    if not isinstance(key, (str, int, float, bool)):
                        # raise TypeError(f"Unhashable key type: {type(key)}")
                        print(f"Unhashable key type: {type(key)}")
                        continue

                    items.append((key, value))

                # 自动检测是否为字典结构
                try:
                    return dict(items)
                except TypeError:
                    return [v for _, v in items]

            elif data_type == 0x13:  # Enum
                # 添加长度检查
                if stream.tell() + 1 > len(stream.getvalue()):
                    raise EOFError("Unexpected end of data")

                enum_id = ord(stream.read(1))
                return "enum:" + self.KEY_MAPPING.get(enum_id, f"{enum_id}")

            else:
                _LOGGER.warning("Unknown data type: 0x%02x", data_type)
                return None

        except Exception as e:
            _LOGGER.error(
                "Parsing error at position %d: %s, Type[0x%x] %s",
                stream.tell(),
                str(e),
                data_type,
                call_stack,
            )
            raise

    def _normalize_structure(self, data):
        """递归规范化数据结构"""
        if isinstance(data, dict):
            # 转换所有子元素
            return {
                self._normalize_key(k): self._normalize_structure(v)
                for k, v in data.items()
            }
        elif isinstance(data, list):
            return [self._normalize_structure(item) for item in data]
        return data

    def _normalize_key(self, key):
        """确保字典键为基本类型"""
        if isinstance(key, (str, int, float, bool)):
            return key
        try:
            # 尝试转换为字符串
            return str(key)
        except:
            # 无法转换则使用固定值
            return "invalid_key"

    def decode(self, data):
        original_data = data
        try:
            # 保存原始数据用于计算剩余部分
            if len(data) < 4:
                raise EOFError("Packet header incomplete (need 4 bytes)")

            header = data[:4]
            remaining = data[4:]

            if header == b"ZZ00":  # 压缩包处理
                if len(remaining) < 4:
                    raise EOFError("Compressed packet incomplete (need orig_len)")

                orig_len = struct.unpack(">I", remaining[:4])[0]
                compressed_data = remaining[4:]

                try:
                    decompressed = gzip.decompress(compressed_data)
                except OSError as e:
                    raise ValueError(f"Decompression failed: {str(e)}") from e

                if len(decompressed) != orig_len:
                    raise ValueError(
                        f"Decompressed size mismatch ({len(decompressed)} vs {orig_len})"
                    )

                # 递归解码解压后的数据
                consumed_bytes = (
                    4 + 4 + len(compressed_data)
                )  # header + orig_len + compressed_data
                remaining_compressed, structure = self.decode(decompressed)

                if remaining_compressed:
                    _LOGGER.warning(
                        "Unprocessed data after decompression: %d bytes",
                        len(remaining_compressed),
                    )

                return original_data[consumed_bytes:], structure

            elif header == b"GL00":  # 标准包处理
                if len(original_data) < 10:
                    raise EOFError("Packet incomplete (need at least 10 bytes)")

                pkt_len = struct.unpack(">I", original_data[6:10])[0]
                total_length = 10 + pkt_len

                if len(original_data) < total_length:
                    raise EOFError(
                        f"Packet length mismatch (need {total_length} bytes)"
                    )

                packet_data = original_data[10:total_length]
                remaining_data = original_data[total_length:]

                try:
                    stream = BytesIO(packet_data)
                    result = []
                    while stream.tell() < len(packet_data):
                        parsed = self._parse_value(stream, 0x12)
                        result.append(parsed)
                except EOFError as e:
                    raise EOFError(f"Incomplete packet data: {str(e)}") from e

                return remaining_data, self._normalize_structure(result)

            else:
                raise ValueError(f"Unknown packet header: {header.hex()}")

        except EOFError as e:
            _LOGGER.debug("Decode EOF: %s", str(e))
            raise  # 重新抛出给上层处理
        except Exception as e:
            _LOGGER.error("Decoding error: %s", str(e), exc_info=True)
            return original_data, None

    def _normalize_structure(self, data):
        """将OrderedDict转换为标准字典"""
        if isinstance(data, OrderedDict):
            data = dict(data)
            for k, v in data.items():
                data[k] = self._normalize_structure(v)
            return data
        elif isinstance(data, list):
            return [self._normalize_structure(item) for item in data]
        return data

    def _build_structure(self, ops):
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


class LifeSmart:
    _proto = None
    node = ""
    node_agt = ""
    _sel = 1

    attr_mapping = {
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

    def __init__(self):
        self._proto = LifeSmartProtocol()

    def login(self, uid="admin", pwd="admin"):
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

    def loginAsCamera(self, uid="admin", pwd="admin"):
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

    def loginByToken(self, token):
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

    def switchControl(self, devid, state):
        return self._proto.encode(
            [
                {"_sel": self._sel, "req": False, "timestamp": 10},
                {
                    "args": {
                        "val": 1 if state else 0,
                        "valtag": "m",
                        "enum:53": "devid",
                        "devid": devid,
                        "key": "O",
                        "type": 128,
                    },
                    "node": f"{self.node_agt}/ep",
                    "act": "rfSetA",
                },
            ]
        )

    def lightControl(self, devid, button, state):
        return self._proto.encode(
            [
                {"_sel": self._sel, "timestamp": 10, "req": False},
                {
                    "args": {
                        "valtag": "m",
                        "val": 1 if state else 0,
                        "enum:53": "enum:devid",
                        "devid": devid,
                        "key": button,
                        "type": 128,
                    },
                    "node": f"{self.node_agt}/ep",
                    "act": "rfSetA",
                },
            ]
        )

    def curtainControl(self, devid, state, operate=True):
        return self._proto.encode(
            [
                {"_sel": self._sel, "req": False, "timestamp": 10},
                {
                    "args": {
                        "val": 1 if operate else 0,
                        "valtag": "m",
                        "enum:53": "devid",
                        "devid": devid,
                        "key": "OP" if state else "CL",
                        "type": 128,
                    },
                    "node": f"{self.node_agt}/ep",
                    "act": "rfSetA",
                },
            ]
        )

    def RGBWControl(self, devid, state):
        return self._proto.encode(
            [
                {"_sel": self._sel, "req": False, "timestamp": 10},
                {
                    "args": {
                        "val": 1 if state else 0,
                        "valtag": "m",
                        "enum:53": "devid",
                        "devid": devid,
                        "key": "RGBW",
                        "type": 128,
                    },
                    "node": f"{self.node_agt}/ep",
                    "act": "rfSetA",
                },
            ]
        )

    def setRGBW(self, devid, r, g, b, white):
        rgbwVal = (white << 24) | (r << 16) | (g << 8) | b
        return self._proto.encode(
            [
                {"_sel": self._sel, "req": False, "timestamp": 10},
                {
                    "args": {
                        "devid": devid,
                        "key": {
                            1: {"type": 255, "key": "RGBW", "val": rgbwVal},
                            2: {"type": 128, "key": "DYN"},
                        },
                    },
                    "node": f"{self.node_agt}/ep",
                    "act": "rfSetA",
                },
            ]
        )

    def IRControl(self, devid, opt):
        return self._proto.encode(
            [
                {"_sel": self._sel, "req": False, "timestamp": 10},
                {
                    "args": {"opt": opt, "cron_name": f"AI_IR_{devid}"},
                    "node": f"{self.node_agt}/ai",
                    "act": "RunA",
                },
            ]
        )

    def sendcode(self, devid, data):
        if isinstance(data, list):
            data.insert(0, "C*")
            data = bytes(data)
        return self._proto.encode(
            [
                {"_sel": self._sel, "req": False, "timestamp": 10},
                {
                    "enum:args": {
                        "ctrlcmd": "sendcode",
                        "enum:valtag": "m",
                        "cmd": "ctrl",
                        "enum:devid": devid,
                        "param": {"enum:type": 1, "data": data},
                    },
                    "enum:node": f"{self.node_agt}/ep",
                    "enum:act": "epCmdA",
                },
            ]
        )

    def IRRAWControl(self, devid, datas):
        return self._proto.encode(
            [
                {"_sel": self._sel, "req": False, "timestamp": 10},
                {
                    "args": {
                        "data": json.loads(datas),
                        "devid": devid,
                        "key": "193",
                        "cmd": 0,
                    },
                    "node": f"{self.node_agt}/ep",
                    "act": "rfSetVarA",
                },
            ]
        )

    def setEEPRom(self, devid, key, val):
        return self._proto.encode(
            [
                {"_sel": self._sel, "req": False, "timestamp": 10},
                {
                    "args": {
                        "type": 255,
                        "valtag": "m",
                        "devid": devid,
                        "key": key,
                        "val": val,
                    },
                    "node": f"{self.node_agt}/ep",
                    "act": "rfSetEEPromA",
                },
            ]
        )

    def addTimer(self, devid, croninfo, key):
        return self._proto.encode(
            [
                {"_sel": self._sel, "req": False, "timestamp": 10},
                {
                    "args": {
                        "cmdlist": f"SCHDEF({{pause=false;}},'0 {croninfo} *',SET,io,'/ep/{devid}',{{{key}}});",
                        "enum:13": f"sys_sch_{devid}_CL",
                    },
                    "node": f"{self.node}/me/ai",
                    "act": "SetA",
                },
            ]
        )

    def getver(self):
        return self._proto.encode(
            [
                {"_sel": self._sel, "req": False, "timestamp": 10},
                {
                    "args": {
                        "icon": False,
                        "cls": False,
                        "rfic": False,
                        "enum:90": False,
                        "_chd": 1,
                        "enum:14": {"s": False, "enum:106": 1},
                        "cgy": False,
                        "tmzone": False,
                        "nid": False,
                        "enum:108": False,
                        "agt_ver": False,
                        "name": False,
                        "enum:113": False,
                    },
                    "node": f"{self.node}/me",
                    "act": "enum:91",
                },
            ]
        )

    def getconfig(self):
        return self._proto.encode(
            [
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
                    "node": f"{self.node}/me/ep",
                    "act": "enum:91",
                },
            ]
        )

    def getAttrName(self, field):
        return self.attr_mapping.get(field, field)

    def getItemAttrs(self, item):
        rc = {}
        for field, value in item.items():
            if field == "RGBW":
                rc_key = f"{self.attr_mapping.get(field, field)}:TYPE"
                rc[rc_key] = value["type"]
            rc_key = self.attr_mapping.get(field, field)
            rc[rc_key] = value["val"]
        return rc

    def changeIcon(self, devid, icon):
        return self._proto.encode(
            [
                {"req": False, "timestamp": 10},
                {
                    "args": {
                        "icon": icon,
                    },
                    "node": f"{self.node}/me/ep/{devid}",
                    "act": "enum:92",
                },
            ]
        )

    def addTrigger(self, trigger_name, cmdlist):
        return self._proto.encode(
            [
                {
                    "_sel": 1,
                    "req": False,
                    "timestamp": 11,
                },
                {
                    "args": {
                        "cmdlist": cmdlist,
                        "_": "trigger",
                        "name": "enum:1",
                        "enum:13": trigger_name,
                    },
                    "node": f"{self.node}/me/ai",
                    "act": "AddA",
                },
            ]
        )

    def delAI(self, ai_name):
        return self._proto.encode(
            [
                {"_sel": self._sel, "req": False, "timestamp": 10},
                {
                    "args": {
                        "cmdlist": "enum:1",
                        "enum:13": ai_name,
                    },
                    "node": f"{self.node}/me/ai",
                    "act": "DelA",
                },
            ]
        )


class LifeSmartLocalClient(LifeSmart):
    def __init__(self, host, port, username, password, config_agt) -> None:
        super().__init__()
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.config_agt = config_agt
        self.reader, self.writer = None, None
        self.dev = LifeSmart()
        self.disconnected = False
        self.device_ready = asyncio.Event()
        self.devices = {}

    async def check_login(self):
        self.reader, self.writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port), timeout=5  # 设置5秒超时
        )

        pkt = self.dev.login(self.username, self.password)
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
            # 使用协议解码
            if response:
                try:
                    response, decoded = self.dev._proto.decode(response)

                    if decoded[1].get("ret", None) is None:
                        _LOGGER.error("Login Failed -> ", decoded[1].get("err"))
                        raise asyncio.InvalidStateError
                    else:
                        break
                except EOFError:
                    pass
        self.writer.close()
        await self.writer.wait_closed()
        return True

    async def get_all_device_async(self, timeout=5):
        """获取所有设备数据，带超时控制"""
        try:
            # 等待设备加载完成或超时
            await asyncio.wait_for(self.device_ready.wait(), timeout=timeout)
            return self.devices.values()
        except asyncio.TimeoutError as e:
            _LOGGER.error(e)
            return False

    async def async_connect(self, callback: None | Callable):
        while not self.disconnected:
            try:
                self.reader, self.writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port),
                    timeout=5,  # 设置5秒超时
                )

                pkt = self.dev.login(self.username, self.password)
                self.writer.write(pkt)
                await self.writer.drain()

                response = b""
                stage = "login"
                while not self.disconnected:
                    buf = await self.reader.read(4096)
                    if not buf:
                        self.writer.close()
                        await self.writer.wait_closed()
                        if self.disconnected:
                            return None
                        raise asyncio.TimeoutError
                    response += buf
                    # 使用协议解码
                    if response:
                        try:
                            response, decoded = self.dev._proto.decode(response)

                            if stage == "login":
                                if decoded[1].get("ret", None) is None:
                                    _LOGGER.error(
                                        "Login Failed -> ", decoded[1].get("err")
                                    )
                                    self.disconnected = True
                                else:
                                    self.dev.node = decoded[1]["ret"][4]["base"][1]
                                    self.dev.node_agt = decoded[1]["ret"][4]["agt"][1]
                                    stage = "loading"
                                    self.writer.write(self.dev.getconfig())
                                    await self.writer.drain()
                            elif stage == "loading":
                                payload = decoded[1]["ret"][1]
                                dev_ids = list(payload["eps_i"].values())
                                self.devices = {}
                                self.device_ready.set()
                                for devid, dev in payload["eps"].items():
                                    dev_meta = {
                                        "me": devid,
                                        "devtype": (
                                            dev["cls"][:-3]
                                            if dev["cls"][-3:-1] == "_V"
                                            else dev["cls"]
                                        ),
                                        "agt": self.dev.node_agt,
                                        "name": dev["name"],
                                        "data": dev["_chd"]["m"]["_chd"],
                                    }
                                    dev_meta.update(dev)
                                    del dev_meta["_chd"]
                                    self.devices[devid] = dev_meta

                                stage = "loaded"
                            else:
                                if schg := decoded[1].get("_schg", None):
                                    for schg_key, schg in schg.items():
                                        if schg_key.startswith(
                                            self.dev.node_agt + "/ep/"
                                        ):
                                            if schg_key.endswith("/s"):
                                                continue
                                            schg_key = schg_key[
                                                len(self.dev.node_agt) + len("/ep/") :
                                            ].split("/")
                                            if len(schg_key) > 2 and schg_key[1] == "m":
                                                if schg_key[0] in self.devices:
                                                    self.devices[schg_key[0]][
                                                        "data"
                                                    ].setdefault(schg_key[2], {})
                                                    self.devices[schg_key[0]]["data"][
                                                        schg_key[2]
                                                    ].update(schg["chg"])
                                                    if (
                                                        callback is not None
                                                        and callable(callback)
                                                    ):
                                                        msg = {
                                                            "me": schg_key[0],
                                                            "idx": schg_key[-1],
                                                            "agt": self.dev.node_agt,
                                                            "devtype": self.devices[
                                                                schg_key[0]
                                                            ]["devtype"],
                                                        }
                                                        msg.update(
                                                            self.devices[schg_key[0]][
                                                                "data"
                                                            ][schg_key[2]]
                                                        )
                                                        callback({"msg": msg})
                                                else:
                                                    if (
                                                        callback is not None
                                                        and callable(callback)
                                                    ):
                                                        callback({"reload": True})
                                                    _LOGGER.warning(
                                                        "Device invalid, reload"
                                                    )
                                            else:
                                                if callback is not None and callable(
                                                    callback
                                                ):
                                                    callback({"reload": True})
                                                _LOGGER.warning(
                                                    "Device property changed, reload"
                                                )
                                elif len(decoded[1].get("_sdel", {}).values()) > 0:
                                    if callback is not None and callable(callback):
                                        callback({"reload": True})
                                    _LOGGER.warning("Device deleted, reload")
                        except EOFError:
                            pass
                self.writer.close()
                await self.writer.wait_closed()
            except ConnectionResetError as e:
                _LOGGER.warning("%s: %s" % (e.__class__.__name__, str(e)))
                self.writer.close()
                await asyncio.sleep(1.0)
            except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
                _LOGGER.error("Connection failed %s: %s", e.__class__.__name__, str(e))
                # raise e
                await asyncio.sleep(1.0)

    async def async_disconnect(self, call: Event | ServiceCall):
        self.disconnected = True
        if self.writer is not None:
            self.writer.close()
            await self.writer.wait_closed()
            self.writer = None

    async def turn_on_light_switch_async(self, idx, agt, me):
        pkt = self.dev.lightControl(me, idx, True)
        self.writer.write(pkt)
        await self.writer.drain()
        return 0

    async def turn_off_light_switch_async(self, idx, agt, me):
        pkt = self.dev.lightControl(me, idx, False)
        self.writer.write(pkt)
        await self.writer.drain()
        return 0
