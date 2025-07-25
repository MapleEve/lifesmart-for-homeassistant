"""
对 lifesmart_protocol.py 的单元测试和集成测试

此测试套件包含三个主要部分：
1.  对 LifeSmartProtocol 类的单元测试，验证核心数据类型的编解码及边界条件。
2.  对 LifeSmartPacketFactory 的集成验证，确保其生成的指令包可被协议正确解析。
3.  对 LifeSmartLocalClient 的集成测试，通过模拟网络IO来验证其完整的生命周期和功能。
"""

import asyncio
from io import BytesIO
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from custom_components.lifesmart.lifesmart_protocol import (
    LifeSmartProtocol,
    LifeSmartPacketFactory,
    LifeSmartLocalClient,
    LSTimestamp,
)


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
            {"key": "val", "num": 123},
            # 嵌套结构
            {"a": 1, "b": {"c": [2, 3, {"nested": True}]}},
            # 可能被误解的特殊字符串
            "::NULL::",
        ],
        ids=lambda v: str(type(v).__name__) + "_" + str(v)[:20],
    )
    def test_basic_types_roundtrip(self, protocol: LifeSmartProtocol, value):
        """验证任何值都可以被编码，然后解码回其原始形式。"""
        encoded_value = protocol._pack_value(value)
        stream = BytesIO(encoded_value)
        # 第一个字节是类型标识符
        data_type = stream.read(1)[0]
        decoded_value = protocol._parse_value(stream, data_type)
        assert decoded_value == value

    def test_dict_with_special_keys_roundtrip(self, protocol: LifeSmartProtocol):
        """专门测试包含冒号的字典键，这曾引起问题。"""
        value = {"enum:key": "val", "num": 123}
        # 为了正确测试，我们必须编码/解码一个完整的数据包列表
        encoded_packet = protocol.encode([value])
        _, decoded_list = protocol.decode(encoded_packet)
        # 解码后的数据包应该是一个包含我们原始字典的列表
        assert isinstance(decoded_list, list)
        assert len(decoded_list) == 1
        assert decoded_list[0] == value

    def test_timestamp_type_handling(self, protocol: LifeSmartProtocol):
        """验证 LSTimestamp 对象是否被正确解码。"""
        timestamp_value = 16318742
        # 手动创建时间戳对象的字节表示
        encoded_bytes = b"\x06\x01" + protocol._encode_varint(timestamp_value << 1)
        stream = BytesIO(encoded_bytes)
        data_type = stream.read(1)[0]
        decoded_obj = protocol._parse_value(stream, data_type)
        # 断言解码后的对象是正确的自定义类型并且具有正确的值
        assert isinstance(decoded_obj, LSTimestamp)
        assert decoded_obj.index == 1
        assert decoded_obj.value == timestamp_value


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
        assert decoded1 == packet1
        assert remaining == encoded2  # 第二个数据包应该在 'remaining' 中保持不变


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
        stream_bytes = b"\x12\x01" + protocol._pack_value("key", True) + b"\xFF"
        stream = BytesIO(stream_bytes)

        parsed_dict = protocol._parse_value(stream, 0x12)

        # 键应该被解析，但其值应该是 None
        assert "key" in parsed_dict
        assert parsed_dict["key"] is None
        # 应该记录一个警告
        assert "Unknown data type to decode: 0xff" in caplog.text


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

        # CORRECTED: 访问解码包中的正确键
        assert command_dict["act"] == "EpSet"
        assert command_dict["devid"] == "dev123"
        assert command_dict["key"] == "L1"
        assert command_dict["val"] == 1
        assert command_dict["valtype"] == "i"  # 断言值类型

    def test_multi_epset_packet_roundtrip(self, protocol, factory):
        """验证一个多端点设置包被正确构建和解码。"""
        io_list = [{"idx": "RGBW", "val": 12345}, {"idx": "DYN", "val": 0}]
        packet = factory.build_multi_epset_packet("dev456", io_list)
        _, decoded = protocol.decode(packet)

        command_dict = decoded[1]
        assert command_dict["act"] == "MultiEpSet"
        # 'val' 键应该包含一个字典列表
        val_list = command_dict["val"]
        assert isinstance(val_list, list)
        assert val_list[0] == {"key": "RGBW", "val": 12345, "valtype": "i"}
        assert val_list[1] == {"key": "DYN", "val": 0, "valtype": "i"}


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
    模拟一个完整的、成功的客户端会话：连接、登录、获取设备、
    接收更新和处理断开连接。这取代了脆弱的 `test_client_full_successful_lifecycle`。
    """
    reader, writer, _ = mock_connection

    client = LifeSmartLocalClient("localhost", 9999, "user", "pass", "entry_id")
    callback = AsyncMock()

    # 在后台运行连接
    connect_task = asyncio.create_task(client.async_connect(callback))

    # --- 步骤 1: 模拟来自服务器的连接和成功登录 ---
    reader.feed_data(LOGIN_SUCCESS_PKT)
    await asyncio.sleep(0.01)  # 允许登录协程处理
    assert client.is_connected

    # --- 步骤 2: 模拟服务器发送设备列表 ---
    reader.feed_data(DEVICE_LIST_PKT)
    devices = await client.get_all_device_async(timeout=1)
    assert len(devices) == 1
    assert "d1" in client.devices
    # 测试设备名称模板 '{$EPN} Button' 是否被正确解析
    assert client.devices["d1"]["data"]["L1"]["name"] == "Switch Button"

    # --- 步骤 3: 模拟来自服务器的实时状态更新 ---
    reader.feed_data(STATUS_UPDATE_PKT)
    await asyncio.sleep(0.01)  # 允许 reader 任务处理
    # 回调函数应该被调用，并带有解析后的更新消息
    callback.assert_any_call(
        {
            "msg": {
                "me": "d1",
                "idx": "L1",
                "agt": "test_agt",
                "devtype": "SL_SW_IF1",
                "val": 1,
            }
        }
    )

    # --- 步骤 4: 模拟设备删除消息 ---
    reader.feed_data(DEVICE_DELETED_PKT)
    await asyncio.sleep(0.01)
    # 这应该触发一个 "reload" 消息到回调函数
    callback.assert_any_call({"reload": True})

    # --- 步骤 5: 测试客户端断开连接 ---
    client.disconnect()
    await asyncio.sleep(0.01)
    writer.close.assert_called()
    assert client.disconnected

    # 清理后台任务
    connect_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await connect_task


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
