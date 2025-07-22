"""
针对 lifesmart_protocol.py 的全覆盖单元测试与集成测试。

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
    """提供一个LifeSmartProtocol的实例。"""
    return LifeSmartProtocol()


@pytest.fixture
def factory() -> LifeSmartPacketFactory:
    """提供一个配置好的LifeSmartPacketFactory实例。"""
    return LifeSmartPacketFactory(node_agt="A3MAAABtAEwQRzM0Njg5NA", node="test_node")


@pytest.fixture
def mock_connection():
    """创建一个模拟的 asyncio StreamReader 和 StreamWriter 用于集成测试。"""
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
# Section 1: LifeSmartProtocol 单元测试
# ====================================================================


class TestLifeSmartProtocolDataTypes:
    """测试核心数据类型的编解码往返。"""

    @pytest.mark.parametrize(
        "value",
        [
            True,
            False,
            None,
            0,
            1,
            -1,
            127,
            128,
            -128,
            100000,
            -100000,
            0x7FFFFFFF,
            -0x7FFFFFFF - 1,
            "",
            "hello",
            "你好世界",
            [],
            [1, True, "world"],
            {},
            {"key": "val", "num": 123},
            {"a": 1, "b": {"c": [2, 3]}},
            "::NULL::",
        ],
    )
    def test_basic_types_roundtrip(self, protocol, value):
        """测试基础Python数据类型的编码和解码是否一致。"""
        encoded_value = protocol._pack_value(value)
        stream = BytesIO(encoded_value)
        data_type = stream.read(1)[0]
        decoded_value = protocol._parse_value(stream, data_type)
        assert decoded_value == value

    def test_enum_encoding(self, protocol):
        """测试枚举类型的编码。"""
        encoded_act = protocol._pack_value("act", isKey=True)
        assert encoded_act == b"\x13\x09"
        encoded_enum_act = protocol._pack_value("enum:act")
        assert encoded_enum_act == b"\x13\x09"
        encoded_custom = protocol._pack_value("my_custom_key", isKey=True)
        assert encoded_custom == protocol._string_to_bin("my_custom_key")

    def test_timestamp_decoding(self, protocol):
        """测试LSTimestamp类型的解码。"""
        ts_val = 16318742
        encoded_ts = b"\x06\x01" + protocol._encode_varint(ts_val << 1)
        stream = BytesIO(encoded_ts)
        data_type = stream.read(1)[0]
        decoded_obj = protocol._parse_value(stream, data_type)
        assert isinstance(decoded_obj, LSTimestamp)
        assert decoded_obj.index == 1
        assert decoded_obj.value == ts_val


class TestLifeSmartProtocolPacketHandling:
    """测试完整数据包（标准和压缩）的编解码。"""

    def test_simple_packet_roundtrip(self, protocol):
        original_packet_list = [{"a": 1}, {"b": 2}]
        encoded_data = protocol.encode(original_packet_list)
        assert encoded_data.startswith(b"GL00")
        remaining, decoded_packet = protocol.decode(encoded_data)
        assert not remaining
        assert decoded_packet == original_packet_list

    def test_compressed_packet_roundtrip(self, protocol):
        """测试一个ZZ00压缩包的往返。"""
        large_object = [{"data": "A" * 2000}]
        encoded_data = protocol.encode(large_object)
        assert encoded_data.startswith(b"ZZ00")
        remaining, decoded_packet = protocol.decode(encoded_data)
        assert not remaining
        assert decoded_packet == large_object

    def test_multi_packet_stream_decoding(self, protocol):
        """测试从一个包含多个包的流中解码。"""
        packet1 = [{"a": 1}]
        packet2 = [{"b": 2}]
        encoded1 = protocol.encode(packet1)
        encoded2 = protocol.encode(packet2)
        combined_stream = encoded1 + encoded2
        remaining, decoded1 = protocol.decode(combined_stream)
        assert decoded1 == packet1
        assert remaining == encoded2


class TestLifeSmartProtocolErrorsAndBoundaries:
    """测试协议处理中的错误和边界条件。"""

    @pytest.mark.parametrize(
        "corrupted_data",
        [
            b"GL0",
            b"GL00\x00\x00",
            b"ZZ00\x00\x00",
            b"GL00\x00\x00\x01\x00\x00",
        ],
    )
    def test_decode_incomplete_data(self, protocol, corrupted_data):
        with pytest.raises(EOFError):
            protocol.decode(corrupted_data)

    @pytest.mark.parametrize(
        "invalid_data, expected_error",
        [
            (b"XXYY", ValueError),
            (b"ZZ00\x00\x00\x00\x10" + b"not_gzipped", ValueError),
        ],
    )
    def test_decode_invalid_data(self, protocol, invalid_data, expected_error):
        with pytest.raises(expected_error):
            protocol.decode(invalid_data)

    def test_decode_unknown_type(self, protocol, caplog):
        stream_bytes = b"\x12\x01" + protocol._pack_value("key", True) + b"\xFF"
        stream = BytesIO(stream_bytes)
        parsed = protocol._parse_value(stream, 0x12)
        assert parsed["key"] is None
        assert "未知的解码数据类型: 0xff" in caplog.text


# ====================================================================
# Section 2: LifeSmartPacketFactory 与 Protocol 集成验证
# ====================================================================


class TestWithPacketFactory:
    """通过PacketFactory生成的真实指令来验证协议。"""

    def test_switch_packet_roundtrip(self, protocol, factory):
        packet_on = factory.build_switch_packet("dev123", "L1", True)
        _, decoded_on = protocol.decode(packet_on)
        args = decoded_on[1]["args"]
        assert args["devid"] == "dev123"
        assert args["key"] == "L1"
        assert args["val"] == 1

    def test_multi_epset_packet_roundtrip(self, protocol, factory):
        io_list = [{"idx": "RGBW", "val": 12345}, {"idx": "DYN", "val": 0}]
        packet = factory.build_multi_epset_packet("dev456", io_list)
        _, decoded = protocol.decode(packet)
        args = decoded[1]["args"]
        val_list = args["val"]
        assert isinstance(val_list, list)
        assert val_list[0]["key"] == "RGBW"
        assert val_list[1]["key"] == "DYN"


# ====================================================================
# Section 3: LifeSmartLocalClient 集成测试
# ====================================================================

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
    reader, writer, _ = mock_connection
    reader.feed_data(LOGIN_SUCCESS_PKT)
    reader.feed_data(DEVICE_LIST_PKT)
    reader.feed_data(STATUS_UPDATE_PKT)
    reader.feed_data(DEVICE_DELETED_PKT)

    client = LifeSmartLocalClient("localhost", 9999, "user", "pass")
    callback = AsyncMock()
    connect_task = asyncio.create_task(client.async_connect(callback))

    devices = await client.get_all_device_async(timeout=1)
    assert len(devices) == 1
    assert "d1" in client.devices
    assert client.devices["d1"]["data"]["L1"]["name"] == "Switch Button"

    await asyncio.sleep(0.1)  # 等待状态更新
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

    await asyncio.sleep(0.1)  # 等待设备删除
    callback.assert_any_call({"reload": True})

    connect_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await connect_task


@pytest.mark.asyncio
async def test_client_control_methods_send_correct_packet(mock_connection):
    reader, writer, _ = mock_connection
    reader.feed_data(LOGIN_SUCCESS_PKT)

    client = LifeSmartLocalClient("localhost", 9999, "user", "pass")
    connect_task = asyncio.create_task(client.async_connect(None))

    while client._factory is None:
        await asyncio.sleep(0.01)

    expected_packet = b"fake_packet"
    with patch.object(
        client._factory, "build_switch_packet", return_value=expected_packet
    ) as mock_build:
        await client.turn_on_light_switch_async("L1", "agt", "d1")
        mock_build.assert_called_once_with("d1", "L1", True)
        writer.write.assert_called_with(expected_packet)
        writer.drain.assert_called_once()

    connect_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await connect_task


@pytest.mark.asyncio
async def test_client_connection_and_login_failures(mock_connection):
    reader, writer, mock_open = mock_connection

    # 场景1: 连接被拒绝
    mock_open.side_effect = ConnectionRefusedError
    client_refused = LifeSmartLocalClient("x", 1, "u", "p")
    task_refused = asyncio.create_task(client_refused.async_connect(None))
    await asyncio.sleep(0.1)  # 等待进入重试
    task_refused.cancel()

    # 场景2: 登录失败
    mock_open.side_effect = None
    reader.feed_data(LOGIN_FAILURE_PKT)
    client_fail = LifeSmartLocalClient("x", 1, "u", "p")
    await asyncio.wait_for(client_fail.async_connect(None), timeout=1)  # 任务应自行退出
    assert client_fail.disconnected is True
