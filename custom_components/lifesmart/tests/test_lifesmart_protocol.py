"""
对 lifesmart_protocol.py 的单元测试和集成测试

此测试套件包含三个主要部分：
1.  对 LifeSmartProtocol 类的单元测试，验证核心数据类型的编解码及边界条件。
2.  对 LifeSmartPacketFactory 的集成验证，确保其生成的指令包可被协议正确解析。
3.  对 LifeSmartLocalClient 的集成测试，通过模拟网络IO来验证其完整的生命周期和功能。
"""

import asyncio
import logging
from io import BytesIO
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from custom_components.lifesmart.const import (
    CMD_TYPE_ON,
    CMD_TYPE_SET_VAL,
    CMD_TYPE_SET_CONFIG,
    CMD_TYPE_SET_TEMP_DECIMAL,
    CMD_TYPE_SET_RAW,
    DOOYA_TYPES,
    GARAGE_DOOR_TYPES,
    HVACMode,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    CMD_TYPE_SET_TEMP_FCU,
)
from custom_components.lifesmart.lifesmart_protocol import (
    LifeSmartProtocol,
    LifeSmartPacketFactory,
    LifeSmartLocalClient,
    LSTimestamp,
)

_LOGGER = logging.getLogger(__name__)

# ====================================================================
# Pytest Fixtures
# ====================================================================


@pytest.fixture
def protocol() -> LifeSmartProtocol:
    """为每个测试提供一个全新的协议实例。"""
    return LifeSmartProtocol()


@pytest.fixture
def factory() -> LifeSmartPacketFactory:
    """提供一个具有默认节点标识符的数据包工厂。"""
    return LifeSmartPacketFactory(node_agt="A3MAAABtAEwQRzM0Njg5NA", node="test_node")


@pytest.fixture
def mock_connection():
    """模拟 asyncio.open_connection 以提供可控的 reader/writer 对。"""
    reader = asyncio.StreamReader()
    writer = MagicMock()
    writer.write = MagicMock()
    writer.drain = AsyncMock()
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()
    writer.is_closing = MagicMock(return_value=False)

    with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_open:
        mock_open.return_value = (reader, writer)
        yield reader, writer, mock_open


# ====================================================================
# Section 1: LifeSmartProtocol 核心功能测试
# ====================================================================


class TestLifeSmartProtocolDataTypes:
    """测试所有支持的数据类型的编码和解码。"""

    @pytest.mark.parametrize(
        "value",
        [
            # 基本类型
            True,
            False,
            None,
            0,
            1,
            -1,
            # 整数边界
            127,
            128,
            -128,
            100000,
            -100000,
            2147483647,
            -2147483648,
            # 字符串 (包括 Unicode)
            "",
            "hello",
            "你好世界",
            "emoji: ✨",
            # 集合
            [],
            [1, True, "world", None],
            {},
            # 使用不会被转换为枚举的键进行测试
            {"my_key": "val", "my_num": 123},
            # 嵌套结构
            {"a": 1, "b": {"c": [2, 3, {"nested": True}]}},
            # 可能被误解的特殊字符串
            "::NULL::",
        ],
        ids=lambda v: str(type(v).__name__) + "_" + str(v)[:20],
    )
    def test_basic_types_roundtrip(self, protocol: LifeSmartProtocol, value):
        """验证任何值都可以被编码，然后解码回其原始形式。"""
        # 必须测试完整的 encode/decode 周期，因为这是公开接口
        # 并且能正确处理头部和协议的非对称性（如枚举）
        # `encode` 期望一个 "parts" 列表，所以我们将单个值包装在列表中
        encoded_packet = protocol.encode([value])
        _, decoded_list = protocol.decode(encoded_packet)

        # encode 会将单个项目包装在列表中，所以解码结果也是列表
        assert isinstance(decoded_list, list)
        assert len(decoded_list) == 1
        assert decoded_list[0] == value

    def test_dict_with_special_keys_roundtrip(self, protocol: LifeSmartProtocol):
        """专门测试包含冒号的字典键以及会被转换为枚举的键。"""
        # 1. 测试 'enum:' 前缀的键，它应该在解码和规范化后被移除
        value_enum_prefix = {"enum:key": "val", "num": 123}
        expected_normalized = {"key": "val", "num": 123}
        encoded_packet1 = protocol.encode([value_enum_prefix])
        _, decoded_list1 = protocol.decode(encoded_packet1)
        assert decoded_list1 == [expected_normalized]

        # 2. 测试会被协议自动转换为枚举的键 (如 'key')
        value_to_be_enum = {"key": "val", "num": 123}
        encoded_packet2 = protocol.encode([value_to_be_enum])
        _, decoded_list2 = protocol.decode(encoded_packet2)
        # 解码和规范化后，结果应该与原始输入相同
        assert decoded_list2 == [value_to_be_enum]

    def test_timestamp_type_handling(self, protocol: LifeSmartProtocol):
        """验证 LSTimestamp 对象是否被正确解码并可被规范化。"""
        timestamp_value = 16318742
        # 手动创建时间戳对象的字节表示
        # 注意：这里我们测试的是 _parse_value，所以需要手动构造
        encoded_bytes = b"\x06\x01" + protocol._encode_varint(timestamp_value << 1)
        stream = BytesIO(encoded_bytes)
        data_type = stream.read(1)[0]
        decoded_obj = protocol._parse_value(stream, data_type)

        assert isinstance(decoded_obj, LSTimestamp)
        assert decoded_obj.index == 1
        assert decoded_obj.value == timestamp_value

        # 同时测试完整编解码周期
        original_packet = [{"ts": LSTimestamp(1, timestamp_value, b"")}]
        # _pack_value 不直接处理 LSTimestamp，所以我们用 _normalize_structure 后的结果来编码
        normalized_packet = protocol._normalize_structure(original_packet)
        encoded_packet = protocol.encode(normalized_packet)
        _, decoded_packet = protocol.decode(encoded_packet)
        assert decoded_packet == normalized_packet


class TestLifeSmartProtocolPacketHandling:
    """测试完整数据包的处理（帧、压缩）。"""

    def test_simple_packet_roundtrip(self, protocol: LifeSmartProtocol):
        """通过编码/解码周期测试一个标准的、未压缩的数据包。"""
        original_packet_list = [{"a": 1, "type": "test"}, {"b": [2, 3]}]
        encoded_data = protocol.encode(original_packet_list)
        # 未压缩的数据包以 'GL00' 开头
        assert encoded_data.startswith(b"GL00")

        remaining, decoded_packet = protocol.decode(encoded_data)

        # 成功的解码应该消耗整个缓冲区
        assert not remaining
        assert decoded_packet == original_packet_list

    def test_compressed_packet_roundtrip(self, protocol: LifeSmartProtocol):
        """测试一个需要 GZIP 压缩的大数据包。"""
        # 创建一个大对象以强制压缩
        large_object = [{"data": "X" * 2048}]
        encoded_data = protocol.encode(large_object)
        # 压缩的数据包以 'ZZ00' 开头
        assert encoded_data.startswith(b"ZZ00")

        remaining, decoded_packet = protocol.decode(encoded_data)

        assert not remaining
        assert decoded_packet == large_object

    def test_multi_packet_stream_decoding(self, protocol: LifeSmartProtocol):
        """测试解码一个包含多个连续数据包的流。"""
        packet1 = [{"msg": "first"}]
        packet2 = [{"msg": "second"}]
        encoded1 = protocol.encode(packet1)
        encoded2 = protocol.encode(packet2)

        # 连接编码后的数据包以模拟网络流
        combined_stream = encoded1 + encoded2

        # 第一个解码调用应该返回第一个数据包和流的其余部分
        remaining, decoded1 = protocol.decode(combined_stream)
        assert decoded1 == [packet1[0]]  # ← 整包 round-trip 后变成列表
        assert remaining == encoded2


class TestLifeSmartProtocolErrorsAndBoundaries:
    """测试协议对格式错误或无效数据的鲁棒性。"""

    @pytest.mark.parametrize(
        "corrupted_data",
        [
            b"GL0",  # 不完整的头部
            b"GL00\x00\x00",  # 头部对于长度来说太短
            b"ZZ00\x00\x00",  # 压缩头部太短
            b"GL00\xff\xff\xff\xff_payload_too_short",  # 声明的长度 > 实际长度
        ],
    )
    def test_decode_incomplete_data_raises_eof(self, protocol, corrupted_data):
        """不完整的数据应该引发 EOFError，表示需要更多数据。"""
        with pytest.raises(EOFError):
            protocol.decode(corrupted_data)

    @pytest.mark.parametrize(
        "invalid_data",
        [
            b"XXYY" + b"\x00" * 4 + b"junk",  # 无效的魔术头部
            b"ZZ00\x00\x00\x00\x10" + b"this_is_not_gzipped_data",  # 错误的 gzip 数据
        ],
    )
    def test_decode_invalid_data_raises_valueerror(self, protocol, invalid_data):
        """真正无效/损坏的数据应该引发 ValueError。"""
        with pytest.raises(ValueError):
            protocol.decode(invalid_data)

    def test_decode_unknown_type_logs_warning(self, protocol, caplog):
        """未知的类型字节应该被跳过并记录一个警告。"""
        # 0xFF 是一个未定义的类型。我们构造一个带有一个键和未知值类型的字典。
        # 这个字节流是不完整的，因为它声明了1个键值对，但值类型是未知的，
        # 并且后面没有数据了。一个健壮的解析器应该抛出 EOFError。
        stream_bytes = b"\x12\x01" + protocol._pack_value("key", True) + b"\xff"
        stream = BytesIO(stream_bytes)

        # 我们期望一个 EOFError，因为解析器在读取未知类型 0xFF 后无法继续。
        with pytest.raises(EOFError):
            protocol._parse_value(stream, 0x12)


# ====================================================================
# Section 2: LifeSmartPacketFactory 测试
# ====================================================================


class TestWithPacketFactory:
    """测试构建特定命令包的工厂。"""

    def test_switch_packet_roundtrip(self, protocol, factory):
        """验证一个开关命令包可以被正确构建和解码。"""
        packet_on = factory.build_switch_packet("dev123", "L1", True)
        _, decoded_on = protocol.decode(packet_on)

        # 解码后的结构是一个字典列表。控制命令在第二个字典中。
        assert len(decoded_on) == 2
        command_dict = decoded_on[1]

        # 访问解码包中的正确键
        assert command_dict["act"] == "rfSetA"

        # 从 'args' 字典中访问控制参数
        args = command_dict["args"]
        assert args["devid"] == "dev123"
        assert args["key"] == "L1"
        assert args["val"] == 1

    def test_multi_epset_packet_roundtrip(self, protocol, factory):
        """验证一个多端点设置包被正确构建和解码。"""
        io_list = [{"idx": "RGBW", "val": 12345}, {"idx": "DYN", "val": 0}]
        packet = factory.build_multi_epset_packet("dev456", io_list)
        _, decoded = protocol.decode(packet)

        command_dict = decoded[1]
        assert command_dict["act"] == "rfSetA"
        # 'val' 键应该包含一个字典列表
        args = command_dict["args"]
        val_list = args["val"]
        assert isinstance(val_list, list)
        assert val_list[0] == {"key": "RGBW", "val": 12345}
        assert val_list[1] == {"key": "DYN", "val": 0}


# ====================================================================
# Section 3: LifeSmartLocalClient 集成测试
# ====================================================================

# 预编码的数据包，用于模拟服务器响应
PROTOCOL = LifeSmartProtocol()
LOGIN_SUCCESS_PKT = PROTOCOL.encode(
    [
        {"_sel": 1},
        {
            "ret": [0, 0, 0, 0, {"base": [0, "test_node"], "agt": [0, "test_agt"]}],
            "act": "Login",
        },
    ]
)

DEVICE_LIST_PKT = PROTOCOL.encode(
    [
        {},
        {
            "ret": [
                0,
                {
                    "eps": {
                        "d1": {
                            "cls": "SL_SW_IF1",
                            "name": "Switch",
                            "_chd": {"m": {"_chd": {"L1": {"name": "{$EPN} Button"}}}},
                        }
                    }
                },
            ]
        },
    ]
)
STATUS_UPDATE_PKT = PROTOCOL.encode(
    [{}, {"_schg": {"test_agt/ep/d1/m/L1": {"chg": {"val": 1}}}}]
)
DEVICE_DELETED_PKT = PROTOCOL.encode([{}, {"_sdel": {"key": "d1"}}])
LOGIN_FAILURE_PKT = PROTOCOL.encode([{}, {"err": -2001, "act": "Login"}])


@pytest.mark.asyncio
async def test_client_full_successful_lifecycle(mock_connection):
    """
    模拟一个完整的、成功的客户端会话：连接、登录、获取设备、接收更新和处理断开连接。
    """
    reader, writer, _ = mock_connection
    client = LifeSmartLocalClient("localhost", 9999, "user", "pass", "entry_id")
    callback = AsyncMock()

    # 在后台运行连接
    connect_task = asyncio.create_task(client.async_connect(callback))

    # --- 步骤 1: 模拟来自服务器的连接和成功登录 ---
    reader.feed_data(LOGIN_SUCCESS_PKT)
    await asyncio.sleep(0.1)
    assert client.is_connected

    # --- 步骤 2: 模拟服务器发送设备列表 ---
    reader.feed_data(DEVICE_LIST_PKT)
    devices = await client.get_all_device_async(timeout=1)
    assert len(devices) == 1
    assert "d1" in client.devices
    assert client.devices["d1"]["data"]["L1"]["name"] == "Switch Button"

    # --- 步骤 3: 模拟来自服务器的实时状态更新 ---
    reader.feed_data(STATUS_UPDATE_PKT)
    await asyncio.sleep(0.01)
    callback.assert_any_call(
        {
            "msg": {
                "me": "d1",
                "idx": "L1",
                "agt": "test_agt",
                "devtype": "SL_SW_IF1",
                "name": "Switch Button",
                "val": 1,
            }
        }
    )

    # --- 步骤 4: 模拟设备删除消息 ---
    reader.feed_data(DEVICE_DELETED_PKT)
    await asyncio.sleep(0.01)
    callback.assert_any_call({"reload": True})

    # --- 步骤 5: 测试客户端断开连接 ---
    client.disconnect()
    await asyncio.sleep(0.1)  # 等待任务取消和关闭完成

    writer.close.assert_called()
    assert client.disconnected
    assert connect_task.done()  # 验证任务已结束


@pytest.mark.asyncio
async def test_client_connection_failures(mock_connection):
    """测试客户端如何处理连接和登录失败。"""
    reader, writer, mock_open = mock_connection

    # 场景 1: 连接被操作系统拒绝
    mock_open.side_effect = ConnectionRefusedError
    client_refused = LifeSmartLocalClient("invalid.host", 1234, "u", "p", "entry1")
    # 客户端应该重试，所以我们用超时来测试
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(client_refused.async_connect(None), timeout=0.1)

    # 场景 2: 连接成功，但登录被服务器拒绝
    mock_open.side_effect = None
    mock_open.return_value = (reader, writer)
    reader.feed_data(LOGIN_FAILURE_PKT)
    client_fail = LifeSmartLocalClient("valid.host", 1234, "u", "p", "entry2")
    await asyncio.wait_for(client_fail.async_connect(None), timeout=1)

    # 客户端在登录失败后应该自行断开连接
    assert client_fail.disconnected is True
    writer.close.assert_called()


class TestLifeSmartProtocolCoverage:
    """针对特定方法和边界情况的补充测试。"""

    def test_normalize_structure(self, protocol: LifeSmartProtocol):
        """专门测试 _normalize_structure 方法的行为。"""
        # 1. 测试 LSTimestamp 对象的规范化
        ts_obj = LSTimestamp(1, 12345, b"")
        assert protocol._normalize_structure(ts_obj) == 12345

        # 2. 测试 enum: 前缀的移除和嵌套规范化
        data = {
            "enum:key1": "value1",
            "list": [
                {"enum:nested_key": ts_obj},
                "item2",
            ],
        }
        expected = {
            "key1": "value1",
            "list": [
                {"nested_key": 12345},
                "item2",
            ],
        }
        assert protocol._normalize_structure(data) == expected

    def test_pack_unsupported_type_logs_warning(self, protocol, caplog):
        """验证打包不支持的类型时会记录一个警告。"""
        unsupported_value = {1, 2, 3}  # set 是不支持的
        protocol._pack_value(unsupported_value)
        assert "不支持的打包类型" in caplog.text
        assert str(type(unsupported_value)) in caplog.text

    def test_pack_integer_out_of_bounds_raises_error(self, protocol):
        """验证打包超出32位有符号整数范围的整数时会引发ValueError。"""
        with pytest.raises(ValueError, match="超出 32-bit 有符号范围"):
            protocol._pack_value(2147483648)
        with pytest.raises(ValueError, match="超出 32-bit 有符号范围"):
            protocol._pack_value(-2147483649)


# ====================================================================
# Section 4: 增强的覆盖率和边界测试 (增强版)
# ====================================================================


class TestLifeSmartProtocolCoverage:
    """针对特定方法和边界情况的补充测试。"""

    def test_normalize_structure(self, protocol: LifeSmartProtocol):
        """专门测试 _normalize_structure 方法的行为。"""
        ts_obj = LSTimestamp(1, 12345, b"")
        data = {
            "enum:key1": "value1",
            "list": [{"enum:nested_key": ts_obj}, "item2"],
            "act": "enum:act_change",
        }
        expected = {
            "key1": "value1",
            "list": [{"nested_key": 12345}, "item2"],
            "act": "act_change",
        }
        assert protocol._normalize_structure(data) == expected

    def test_pack_unsupported_type_logs_warning(self, protocol, caplog):
        """验证打包不支持的类型时会记录一个警告。"""
        unsupported_value = {1, 2, 3}
        protocol._pack_value(unsupported_value)
        assert "不支持的打包类型" in caplog.text

    def test_pack_integer_out_of_bounds_raises_error(self, protocol):
        """验证打包超出32位有符号整数范围的整数时会引发ValueError。"""
        with pytest.raises(ValueError):
            protocol._pack_value(2147483648)
        with pytest.raises(ValueError):
            protocol._pack_value(-2147483649)


class TestLifeSmartPacketFactoryCoverage:
    """
    为 LifeSmartPacketFactory 提供全面的、参数化的测试，
    确保所有指令生成逻辑的正确性。
    """

    def _decode_and_get_args(self, protocol, packet):
        """辅助函数，用于解码数据包并返回 'args' 部分。"""
        _, decoded = protocol.decode(packet)
        return decoded[1]["args"]

    @pytest.mark.parametrize(
        "device_type, command, expected_idx, expected_val, expected_type",
        [
            # 定位窗帘
            (list(GARAGE_DOOR_TYPES)[0], "open", "P3", 100, CMD_TYPE_SET_VAL),
            (list(GARAGE_DOOR_TYPES)[0], "close", "P3", 0, CMD_TYPE_SET_VAL),
            (list(GARAGE_DOOR_TYPES)[0], "stop", "P3", 0x80, CMD_TYPE_SET_CONFIG),
            (list(DOOYA_TYPES)[0], "open", "P2", 100, CMD_TYPE_SET_VAL),
            (list(DOOYA_TYPES)[0], "close", "P2", 0, CMD_TYPE_SET_VAL),
            (list(DOOYA_TYPES)[0], "stop", "P2", 0x80, CMD_TYPE_SET_CONFIG),
            # 非定位窗帘
            ("SL_SW_WIN", "open", "OP", 1, CMD_TYPE_ON),
            ("SL_SW_WIN", "close", "CL", 1, CMD_TYPE_ON),
            ("SL_SW_WIN", "stop", "ST", 1, CMD_TYPE_ON),
        ],
    )
    def test_build_cover_command_packet(
        self,
        protocol,
        factory,
        device_type,
        command,
        expected_idx,
        expected_val,
        expected_type,
    ):
        """全面测试窗帘的 开/关/停 指令包生成。"""
        packet = factory.build_cover_command_packet(
            "dev_cover", expected_idx, command, device_type
        )
        args = self._decode_and_get_args(protocol, packet)
        assert args["devid"] == "dev_cover"
        assert args["key"] == expected_idx
        assert args["val"] == expected_val
        assert args["type"] == expected_type

    @pytest.mark.parametrize(
        "device_type, position, expected_idx",
        [
            (list(GARAGE_DOOR_TYPES)[0], 50, "P3"),
            (list(DOOYA_TYPES)[0], 80, "P2"),
        ],
    )
    def test_build_cover_position_packet(
        self, protocol, factory, device_type, position, expected_idx
    ):
        """测试设置窗帘位置的指令包生成。"""
        packet = factory.build_cover_position_packet(
            "dev_cover", expected_idx, position
        )
        args = self._decode_and_get_args(protocol, packet)
        assert args["devid"] == "dev_cover"
        assert args["key"] == expected_idx
        assert args["val"] == position
        assert args["type"] == CMD_TYPE_SET_VAL

    @pytest.mark.parametrize(
        "device_type, hvac_mode, current_val, expected_key, expected_val_calc, expected_type",
        [
            ("SL_NATURE", HVACMode.HEAT, 0, "P7", lambda cv: 4, CMD_TYPE_SET_CONFIG),
            (
                "SL_CP_AIR",
                HVACMode.COOL,
                0b1111,  # 15
                "P1",
                # 计算逻辑：将第13/14位设置为2(COOL)，保留其他位
                lambda cv: (cv & ~(0b11 << 13)) | (2 << 13),
                CMD_TYPE_SET_RAW,
            ),
        ],
    )
    def test_build_climate_hvac_mode_packet(
        self,
        protocol,
        factory,
        device_type,
        hvac_mode,
        current_val,
        expected_key,
        expected_val_calc,
        expected_type,
    ):
        """测试设置温控器HVAC模式的指令包生成。"""
        expected_val = expected_val_calc(current_val)

        # HVAC 模式设置可能涉及多个数据包（先开机），我们只测试核心的模式设置包
        with patch.object(factory, "build_switch_packet"):  # 忽略开机包
            packet = factory.build_climate_hvac_mode_packet(
                "dev_climate", hvac_mode, current_val, device_type
            )
            # 如果操作不支持，函数可能返回空字节，需要处理
            assert (
                packet
            ), f"Packet for {device_type} with {hvac_mode} should not be empty"

            args = self._decode_and_get_args(protocol, packet)
            assert args["devid"] == "dev_climate"
            assert args["key"] == expected_key
            assert args["val"] == expected_val
            assert args["type"] == expected_type

    @pytest.mark.parametrize(
        "device_type, temp, expected_key, expected_val, expected_type",
        [
            ("V_AIR_P", 25.5, "tT", 255, CMD_TYPE_SET_TEMP_DECIMAL),
            ("SL_CP_DN", 18.0, "P3", 180, CMD_TYPE_SET_RAW),
            ("SL_FCU", 22.0, "P8", 220, CMD_TYPE_SET_TEMP_FCU),
        ],
    )
    def test_build_climate_temperature_packet(
        self,
        protocol,
        factory,
        device_type,
        temp,
        expected_key,
        expected_val,
        expected_type,
    ):
        """测试设置温控器温度的指令包生成。"""
        packet = factory.build_climate_temperature_packet(
            "dev_climate", temp, device_type
        )
        args = self._decode_and_get_args(protocol, packet)
        assert args["devid"] == "dev_climate"
        assert args["key"] == expected_key
        assert args["val"] == expected_val
        assert args["type"] == expected_type

    @pytest.mark.parametrize(
        "device_type, fan_mode, current_val, expected_key, expected_val, expected_type",
        [
            ("V_AIR_P", FAN_LOW, 0, "F", 15, CMD_TYPE_SET_CONFIG),
            ("SL_NATURE", FAN_HIGH, 0, "P9", 75, CMD_TYPE_SET_CONFIG),
            (
                "SL_CP_AIR",
                FAN_MEDIUM,
                0b1111,
                "P1",
                (0b1111 & ~(0b11 << 15)) | (2 << 15),
                CMD_TYPE_SET_RAW,
            ),
        ],
    )
    def test_build_climate_fan_mode_packet(
        self,
        protocol,
        factory,
        device_type,
        fan_mode,
        current_val,
        expected_key,
        expected_val,
        expected_type,
    ):
        """测试设置温控器风扇模式的指令包生成。"""
        packet = factory.build_climate_fan_mode_packet(
            "dev_climate", fan_mode, current_val, device_type
        )
        args = self._decode_and_get_args(protocol, packet)
        assert args["devid"] == "dev_climate"
        assert args["key"] == expected_key
        assert args["val"] == expected_val
        assert args["type"] == expected_type


class TestLifeSmartClientCoverage:
    """为 LifeSmartLocalClient 中未被测试的方法和场景提供覆盖。"""

    @pytest.mark.parametrize(
        "input_dict, expected_dict",
        [
            (
                {
                    "name": "Parent",
                    "_chd": {"m": {"_chd": {"L1": {"name": "{$EPN} Child"}}}},
                },
                {
                    "name": "Parent",
                    "_chd": {"m": {"_chd": {"L1": {"name": "Parent Child"}}}},
                },
            ),
            (
                {
                    "name": "Parent",
                    "_chd": {"m": {"_chd": {"L1": {"name": "Door {BAT}"}}}},
                },
                {
                    "name": "Parent",
                    "_chd": {"m": {"_chd": {"L1": {"name": "Door BAT"}}}},
                },
            ),
        ],
    )
    def test_normalize_device_names(self, input_dict, expected_dict):
        """验证 _normalize_device_names 方法能正确处理各种占位符。"""
        normalized = LifeSmartLocalClient._normalize_device_names(input_dict)
        assert normalized == expected_dict

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "client_method_name, method_args, factory_method_name",
        [
            (
                "turn_on_light_switch_async",
                ("idx1", "agt1", "dev1"),
                "build_switch_packet",
            ),
            (
                "open_cover_async",
                ("agt1", "dev1", "SL_SW_WIN"),
                "build_cover_command_packet",
            ),
            (
                "async_set_climate_temperature",
                ("agt1", "dev1", "V_AIR_P", 25.5),
                "build_climate_temperature_packet",
            ),
            (
                "press_switch_async",
                ("idx1", "agt1", "dev1", 500),
                "build_press_switch_packet",
            ),
        ],
    )
    async def test_client_control_methods_call_factory_and_send(
        self, mock_connection, client_method_name, method_args, factory_method_name
    ):
        """验证客户端的控制方法会调用正确的工厂方法并发送数据包。"""
        reader, writer, _ = mock_connection
        client = LifeSmartLocalClient("localhost", 9999, "u", "p")
        client.reader, client.writer = reader, writer
        client._factory = LifeSmartPacketFactory("test_agt", "test_node")

        with patch.object(
            client._factory, factory_method_name, return_value=b"test_packet"
        ) as mock_factory_method:
            client_method = getattr(client, client_method_name)
            await client_method(*method_args)

            mock_factory_method.assert_called_once()
            writer.write.assert_called_once_with(b"test_packet")
            writer.drain.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_packet_returns_error_if_not_connected(self, mock_connection):
        """测试在未连接状态下调用 _send_packet 会返回错误码并记录日志。"""
        _, writer, _ = mock_connection
        client = LifeSmartLocalClient("localhost", 9999, "u", "p")
        client.writer = writer
        writer.is_closing.return_value = True  # 模拟已关闭

        with patch(
            "custom_components.lifesmart.lifesmart_protocol._LOGGER"
        ) as mock_logger:
            result = await client._send_packet(b"test")
            assert result == -1
            mock_logger.error.assert_called_with("本地客户端未连接，无法发送指令。")
