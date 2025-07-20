"""测试 LifeSmart 协议的编码和解码功能。"""

import pytest

from custom_components.lifesmart.lifesmart_protocol import (
    LifeSmartPacketFactory,
    LifeSmartProtocol,
)


@pytest.fixture
def protocol():
    return LifeSmartProtocol()


@pytest.fixture
def factory():
    return LifeSmartPacketFactory(node_agt="A3MAAABtAEwQRzM0Njg5NA", node="mynode")


def test_varint_encoding_decoding(protocol):
    """测试变长整数的编码和解码。"""
    test_numbers = [0, 1, 127, 128, 255, 16384, 2097151]
    for number in test_numbers:
        encoded = protocol._encode_varint(number)
        from io import BytesIO

        stream = BytesIO(encoded)
        decoded = protocol._decode_varint(stream)
        assert decoded == number


def test_simple_packet_encode_decode(protocol):
    """测试简单数据包的编码和解码往返过程。"""
    original_packet = [
        {"_sel": 1, "req": False, "timestamp": 10},
        {
            "args": {"val": 1, "key": "L1", "type": "0x81"},
            "node": "some_node/ep",
            "act": "rfSetA",
        },
    ]
    encoded_data = protocol.encode(original_packet)
    assert encoded_data.startswith(b"GL00")

    remaining, decoded_packet = protocol.decode(encoded_data)
    assert not remaining
    # 比较核心内容，忽略可能由协议添加的默认值
    assert decoded_packet[1]["args"]["val"] == original_packet[1]["args"]["val"]
    assert decoded_packet[1]["node"] == original_packet[1]["node"]


def test_switch_packet_factory(factory):
    """测试开关指令包的构建。"""
    packet_on = factory.build_switch_packet("dev123", "L1", True)
    packet_off = factory.build_switch_packet("dev123", "L1", False)

    assert isinstance(packet_on, bytes)
    assert isinstance(packet_off, bytes)

    _, decoded_on = factory._proto.decode(packet_on)
    _, decoded_off = factory._proto.decode(packet_off)

    assert decoded_on[1]["args"]["val"] == 1
    assert decoded_on[1]["args"]["type"] == "0x81"
    assert decoded_off[1]["args"]["val"] == 0
    assert decoded_off[1]["args"]["type"] == "0x80"
    assert decoded_on[1]["args"]["devid"] == "dev123"


def test_multi_epset_packet_factory(factory):
    """测试多IO口指令包的构建。"""
    io_list = [
        {"idx": "RGBW", "type": "0xff", "val": 12345},
        {"idx": "DYN", "type": "0x80", "val": 0},
    ]
    packet = factory.build_multi_epset_packet("dev456", io_list)
    _, decoded = factory._proto.decode(packet)

    assert decoded[1]["args"]["devid"] == "dev456"
    sent_list = decoded[1]["args"]["val"]
    assert isinstance(sent_list, list)
    assert len(sent_list) == 2
    # 协议内部会将 'idx' 转换为 'key'
    assert sent_list[0]["key"] == "RGBW"
    assert sent_list[0]["val"] == 12345
    assert sent_list[1]["key"] == "DYN"
