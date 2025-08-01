"""
LifeSmart 协议层测试套件。

此测试套件专门测试 protocol.py 中的协议处理功能，包括：
- 数据类型编码和解码（基础类型、复杂类型、特殊类型）
- 数据包处理（帧结构、压缩、多包处理）
- 协议工厂（指令包构建和验证）
- 错误处理和边界条件
- 协议鲁棒性和容错能力

测试使用结构化的类组织，每个类专注于特定的功能领域，
并包含详细的中文注释以确保可维护性。
"""

import json
from io import BytesIO

import pytest

from custom_components.lifesmart.core.protocol import (
    LifeSmartProtocol,
    LifeSmartPacketFactory,
    LSTimestamp,
    LSEncoder,
)


# ==================== 测试数据和Fixtures ====================


@pytest.fixture
def protocol():
    """提供标准的协议实例。"""
    return LifeSmartProtocol()


@pytest.fixture
def packet_factory():
    """提供标准的数据包工厂实例。"""
    return LifeSmartPacketFactory(node_agt="test_agt", node="test_node")


@pytest.fixture
def sample_data_types():
    """提供各种数据类型的测试样本。"""
    return {
        "boolean_true": True,
        "boolean_false": False,
        "null_value": None,
        "integer_zero": 0,
        "integer_positive": 12345,
        "integer_negative": -6789,
        "integer_max": 2147483647,
        "integer_min": -2147483648,
        "string_empty": "",
        "string_ascii": "hello world",
        "string_unicode": "你好世界",
        "string_emoji": "测试 ✨ 数据",
        "list_empty": [],
        "list_mixed": [1, True, "test", None, {"nested": "value"}],
        "dict_empty": {},
        "dict_simple": {"key": "value", "number": 42},
        "dict_complex": {"level1": {"level2": {"list": [1, 2, 3], "boolean": True}}},
        "special_null": "::NULL::",
    }


# ==================== 数据类型编解码测试类 ====================


class TestProtocolDataTypeEncoding:
    """测试所有支持的数据类型的编码和解码功能。"""

    @pytest.mark.parametrize(
        "test_name, test_value",
        [
            ("BooleanTrue", True),
            ("BooleanFalse", False),
            ("NullValue", None),
            ("IntegerZero", 0),
            ("IntegerPositive", 12345),
            ("IntegerNegative", -6789),
            ("IntegerMax", 2147483647),
            ("IntegerMin", -2147483648),
            ("StringEmpty", ""),
            ("StringASCII", "hello world"),
            ("StringUnicode", "你好世界"),
            ("StringEmoji", "测试 ✨ 数据"),
            ("ListEmpty", []),
            ("ListMixed", [1, True, "test", None]),
            ("DictEmpty", {}),
            ("DictSimple", {"key": "value", "number": 42}),
            ("SpecialNull", "::NULL::"),
        ],
    )
    def test_basic_data_type_roundtrip(
        self, protocol: LifeSmartProtocol, test_name: str, test_value
    ):
        """测试基础数据类型的编码解码往返。"""
        original_message = [{"test_data": test_value}]
        encoded_packet = protocol.encode(original_message)
        remaining_data, decoded_message = protocol.decode(encoded_packet)

        assert not remaining_data, "解码后不应有剩余数据"
        assert (
            decoded_message == original_message
        ), f"{test_name}类型的往返编解码应该保持数据一致"

    def test_complex_nested_structures(self, protocol: LifeSmartProtocol):
        """测试复杂嵌套结构的编解码。"""
        complex_data = [
            {
                "device_info": {
                    "id": "dev_001",
                    "type": "switch",
                    "properties": {
                        "channels": ["L1", "L2", "L3"],
                        "status": {"L1": True, "L2": False, "L3": None},
                        "metadata": {
                            "firmware": "1.2.3",
                            "capabilities": [1, 2, 4, 8],
                            "config": {"timeout": 30, "retry": 3},
                        },
                    },
                }
            }
        ]

        encoded_packet = protocol.encode(complex_data)
        _, decoded_data = protocol.decode(encoded_packet)

        assert decoded_data == complex_data, "复杂嵌套结构应该正确编解码"

    def test_large_data_structures(self, protocol: LifeSmartProtocol):
        """测试大数据结构的处理。"""
        large_list = [{"item": i, "data": "X" * 100} for i in range(100)]
        large_dict = {f"key_{i}": f"value_{i}" * 50 for i in range(50)}
        large_message = [{"large_list": large_list, "large_dict": large_dict}]

        encoded_packet = protocol.encode(large_message)
        _, decoded_message = protocol.decode(encoded_packet)

        assert decoded_message == large_message, "大数据结构应该正确处理"

    def test_unicode_edge_cases(self, protocol: LifeSmartProtocol):
        """测试Unicode字符的边界情况。"""
        unicode_test_cases = [
            "ASCII only",
            "中文字符",
            "🎉🔥✨🚀💡",  # 表情符号
            "Ñiño España",  # 带重音符号
            "Русский текст",  # 西里尔字母
            "العربية",  # 阿拉伯文
            "🏳️‍🌈👨‍👩‍👧‍👦",  # 复合表情符号
            "\x00\x01\x02",  # 控制字符
            "Line1\nLine2\tTabbed",  # 换行和制表符
        ]

        for i, unicode_text in enumerate(unicode_test_cases):
            test_message = [{"unicode_test": unicode_text, "index": i}]
            encoded_packet = protocol.encode(test_message)
            _, decoded_message = protocol.decode(encoded_packet)

            assert decoded_message == test_message, f"Unicode案例 {i} 应该正确处理"


class TestProtocolSpecialTypes:
    """测试协议中的特殊数据类型处理。"""

    def test_timestamp_type_encoding_decoding(self, protocol: LifeSmartProtocol):
        """测试时间戳类型的编码和解码。"""
        timestamp_value = 1634567890

        # 手动构建时间戳数据
        encoded_bytes = b"\x06\x01" + protocol._encode_varint(timestamp_value << 1)
        stream = BytesIO(encoded_bytes)
        data_type = stream.read(1)[0]
        decoded_timestamp = protocol._parse_value(stream, data_type)

        assert isinstance(
            decoded_timestamp, LSTimestamp
        ), "解码结果应该是LSTimestamp类型"
        assert decoded_timestamp.value == timestamp_value, "时间戳值应该正确"

        # 测试标准化后的编解码
        normalized_packet = protocol._normalize_structure(
            [{"timestamp": decoded_timestamp}]
        )
        encoded_packet = protocol.encode(normalized_packet)
        _, decoded_packet = protocol.decode(encoded_packet)

        assert decoded_packet == [
            {"timestamp": timestamp_value}
        ], "时间戳应该被正确标准化"

    def test_enum_key_normalization(self, protocol: LifeSmartProtocol):
        """测试带enum前缀的键的标准化处理。"""
        # 测试带enum前缀的字典
        enum_dict = {
            "enum:device_type": "switch",
            "enum:status": "on",
            "normal_key": "value",
        }
        expected_normalized = {
            "device_type": "switch",
            "status": "on",
            "normal_key": "value",
        }

        original_message = [enum_dict]
        encoded_packet = protocol.encode(original_message)
        _, decoded_message = protocol.decode(encoded_packet)

        assert decoded_message == [expected_normalized], "enum前缀应该被正确移除"

        # 测试不含enum前缀的字典保持不变
        normal_dict = {"device_type": "light", "status": "off"}
        normal_message = [normal_dict]
        encoded_packet = protocol.encode(normal_message)
        _, decoded_message = protocol.decode(encoded_packet)

        assert decoded_message == normal_message, "不含enum前缀的字典应该保持不变"

    def test_special_null_handling(self, protocol: LifeSmartProtocol):
        """测试特殊NULL值的处理。"""
        test_cases = [
            {"null_field": None},
            {"special_null": "::NULL::"},
            {"mixed": [None, "::NULL::", "normal_value"]},
        ]

        for test_case in test_cases:
            original_message = [test_case]
            encoded_packet = protocol.encode(original_message)
            _, decoded_message = protocol.decode(encoded_packet)

            assert decoded_message == original_message, f"特殊NULL值处理: {test_case}"

    def test_ls_encoder_custom_types(self):
        """测试自定义JSON编码器对特殊类型的处理。"""
        encoder = LSEncoder()

        # 测试LSTimestamp编码
        timestamp = LSTimestamp(index=1, value=1634567890, raw_data=b"\x01\x02\x03")
        timestamp_json = encoder.encode({"ts": timestamp})
        decoded_timestamp = json.loads(timestamp_json)

        assert decoded_timestamp["ts"] == 1634567890, "LSTimestamp应该被编码为数值"

        # 测试普通类型保持不变
        normal_data = {"string": "test", "number": 42, "boolean": True, "null": None}
        normal_json = encoder.encode(normal_data)
        decoded_normal = json.loads(normal_json)

        assert decoded_normal == normal_data, "普通数据类型应该保持不变"


# ==================== 数据包处理测试类 ====================


class TestProtocolPacketHandling:
    """测试数据包的帧结构、压缩和多包处理。"""

    def test_simple_packet_structure(self, protocol: LifeSmartProtocol):
        """测试简单数据包的结构和处理。"""
        test_message = [{"action": "test"}, {"data": {"value": 123}}]
        encoded_packet = protocol.encode(test_message)

        # 验证数据包头部
        assert encoded_packet.startswith(b"GL00"), "简单数据包应该以GL00头部开始"
        assert len(encoded_packet) > 8, "数据包应该包含头部和负载"

        # 验证解码
        remaining_data, decoded_message = protocol.decode(encoded_packet)
        assert not remaining_data, "解码后不应有剩余数据"
        assert decoded_message == test_message, "解码后的数据应该与原始数据一致"

    def test_compressed_packet_handling(self, protocol: LifeSmartProtocol):
        """测试压缩数据包的处理。"""
        # 创建一个足够大的数据包以触发压缩
        large_message = [{"large_data": "X" * 2048, "repeat": i} for i in range(10)]
        encoded_packet = protocol.encode(large_message)

        # 验证压缩数据包头部
        assert encoded_packet.startswith(b"ZZ00"), "大数据包应该以ZZ00头部开始（压缩）"

        # 验证解码
        remaining_data, decoded_message = protocol.decode(encoded_packet)
        assert not remaining_data, "压缩包解码后不应有剩余数据"
        assert decoded_message == large_message, "压缩包解码后的数据应该与原始数据一致"

    def test_multi_packet_stream_processing(self, protocol: LifeSmartProtocol):
        """测试多个数据包的流式处理。"""
        packet1 = [{"seq": 1, "data": "first"}]
        packet2 = [{"seq": 2, "data": "second"}]
        packet3 = [{"seq": 3, "data": "third"}]

        encoded1 = protocol.encode(packet1)
        encoded2 = protocol.encode(packet2)
        encoded3 = protocol.encode(packet3)

        # 合并多个数据包
        combined_stream = encoded1 + encoded2 + encoded3

        # 逐个解码
        remaining = combined_stream
        decoded_packets = []

        while remaining:
            remaining, packet = protocol.decode(remaining)
            decoded_packets.append(packet)

        assert len(decoded_packets) == 3, "应该解码出3个数据包"
        assert decoded_packets[0] == packet1, "第一个包应该正确"
        assert decoded_packets[1] == packet2, "第二个包应该正确"
        assert decoded_packets[2] == packet3, "第三个包应该正确"

    def test_partial_packet_handling(self, protocol: LifeSmartProtocol):
        """测试部分数据包的处理。"""
        test_message = [{"test": "partial_packet"}]
        encoded_packet = protocol.encode(test_message)

        # 只提供部分数据
        partial_data = encoded_packet[:8]  # 只有头部

        with pytest.raises(EOFError):
            protocol.decode(partial_data)

    @pytest.mark.parametrize(
        "packet_size",
        [1, 10, 100, 1000, 5000],
        ids=["Tiny", "Small", "Medium", "Large", "ExtraLarge"],
    )
    def test_various_packet_sizes(self, protocol: LifeSmartProtocol, packet_size: int):
        """测试不同大小数据包的处理。"""
        # 生成指定大小的测试数据
        test_data = [
            {"item": i, "payload": "X" * (packet_size // 10)}
            for i in range(packet_size // 100 + 1)
        ]

        encoded_packet = protocol.encode(test_data)
        remaining_data, decoded_data = protocol.decode(encoded_packet)

        assert not remaining_data, f"大小为{packet_size}的包解码后不应有剩余数据"
        assert decoded_data == test_data, f"大小为{packet_size}的包数据应该一致"


# ==================== 协议错误处理测试类 ====================


class TestProtocolErrorHandling:
    """测试协议对各种错误情况的处理能力。"""

    @pytest.mark.parametrize(
        "corrupted_data, expected_error",
        [
            (b"GL0", EOFError),  # 不完整的头部
            (b"GL00\x00\x00", EOFError),  # 头部完整但缺少长度信息
            (b"ZZ00\x00\x00", EOFError),  # 压缩包头部不完整
            (b"GL00\xff\xff\xff\xff", EOFError),  # 声明的长度过大
        ],
        ids=[
            "IncompleteHeader",
            "MissingLength",
            "IncompleteCompressed",
            "InvalidLength",
        ],
    )
    def test_corrupted_packet_handling(
        self, protocol: LifeSmartProtocol, corrupted_data: bytes, expected_error
    ):
        """测试损坏数据包的错误处理。"""
        with pytest.raises(expected_error):
            protocol.decode(corrupted_data)

    @pytest.mark.parametrize(
        "invalid_data",
        [
            b"INVALID_HEADER\x00\x00\x00\x10" + b"some_data",
            b"ZZ00\x00\x00\x00\x10" + b"not_gzipped_data",
            b"GL00\x00\x00\x00\x04" + b"\xff\xff\xff\xff",
        ],
        ids=["InvalidHeader", "BadCompression", "InvalidPayload"],
    )
    def test_invalid_data_handling(
        self, protocol: LifeSmartProtocol, invalid_data: bytes
    ):
        """测试无效数据的错误处理。"""
        with pytest.raises((ValueError, EOFError)):
            protocol.decode(invalid_data)

    def test_integer_overflow_handling(self, protocol: LifeSmartProtocol):
        """测试整数溢出的处理。"""
        # 测试正溢出
        with pytest.raises(ValueError, match="超出 32-bit 有符号范围"):
            protocol._pack_value(2147483648)  # 2^31

        # 测试负溢出
        with pytest.raises(ValueError, match="超出 32-bit 有符号范围"):
            protocol._pack_value(-2147483649)  # -(2^31 + 1)

    def test_unsupported_type_handling(self, protocol: LifeSmartProtocol, caplog):
        """测试不支持类型的处理。"""

        class UnsupportedType:
            pass

        # 应该记录警告但不崩溃
        test_message = [{"unsupported": UnsupportedType()}]
        encoded_packet = protocol.encode(test_message)

        assert "不支持的打包类型" in caplog.text, "应该记录不支持类型的警告"
        assert encoded_packet is not None, "即使有不支持的类型，编码也应该继续"

    def test_incomplete_string_data(self, protocol: LifeSmartProtocol):
        """测试字符串数据不完整的情况。"""
        # 模拟声明长度为10但实际数据不足的字符串
        incomplete_string_data = b"\x0a"  # 声明长度为10的varint

        with pytest.raises(EOFError, match="字符串数据不足"):
            protocol._parse_value(BytesIO(incomplete_string_data), 0x11)  # 字符串类型码

    def test_incomplete_hex_data(self, protocol: LifeSmartProtocol):
        """测试十六进制数据不完整的情况。"""
        # 模拟HEX数据不完整（需要8字节但只有4字节）
        incomplete_hex_data = b"\x01\x11\x22\x33"

        with pytest.raises(EOFError, match="HEX 数据不完整"):
            protocol._parse_value(BytesIO(incomplete_hex_data), 0x05)  # HEX类型码

    def test_incomplete_timestamp_data(self, protocol: LifeSmartProtocol):
        """测试时间戳数据不完整的情况。"""
        # 模拟时间戳数据不完整
        incomplete_timestamp_data = b"\x01"

        with pytest.raises(EOFError):
            protocol._parse_value(
                BytesIO(incomplete_timestamp_data), 0x06
            )  # 时间戳类型码


# ==================== 数据包工厂测试类 ====================


class TestPacketFactoryConstruction:
    """测试数据包工厂的指令构建功能。"""

    def test_factory_initialization(self):
        """测试工厂的初始化。"""
        factory = LifeSmartPacketFactory(node_agt="test_agt", node="test_node")

        assert factory.node_agt == "test_agt", "节点AGT应该正确设置"
        assert factory.node == "test_node", "节点名称应该正确设置"

    @pytest.mark.parametrize(
        "method_name, args, expected_structure",
        [
            ("build_epset_packet", ("dev1", "L1", 0x81, 1), {"action": "EpSet"}),
            (
                "build_multi_epset_packet",
                ("dev1", [{"idx": "L1", "val": 1}]),
                {"action": "EpsSet"},
            ),
            ("build_scene_trigger_packet", ("scene1",), {"action": "SceneTrigger"}),
            ("build_get_config_packet", ("config_key",), {"action": "GetConfig"}),
            ("build_change_icon_packet", ("dev1", "icon1"), {"action": "ChangeIcon"}),
            (
                "build_add_trigger_packet",
                ("trigger1", "cmdlist"),
                {"action": "AddTrigger"},
            ),
            ("build_del_ai_packet", ("ai1",), {"action": "DelAI"}),
            (
                "build_ir_control_packet",
                ("ir_dev", {"keys": "power"}),
                {"action": "IrControl"},
            ),
            ("build_send_code_packet", ("ir_dev", [1, 2, 3]), {"action": "SendCode"}),
            (
                "build_send_ir_keys_packet",
                ("ai1", "dev1", "tv", "samsung", '["power"]'),
                {"action": "SendIrKeys"},
            ),
            (
                "build_ir_raw_control_packet",
                ("ir_dev", '{"data": "raw"}'),
                {"action": "IrRawControl"},
            ),
            (
                "build_set_eeprom_packet",
                ("dev1", "key1", "val1"),
                {"action": "SetEEPROM"},
            ),
            (
                "build_add_timer_packet",
                ("dev1", "0 8 * * *", "L1=ON"),
                {"action": "AddTimer"},
            ),
        ],
        ids=[
            "EpSet",
            "MultiEpSet",
            "SceneTrigger",
            "GetConfig",
            "ChangeIcon",
            "AddTrigger",
            "DelAI",
            "IrControl",
            "SendCode",
            "SendIrKeys",
            "IrRawControl",
            "SetEEPROM",
            "AddTimer",
        ],
    )
    def test_packet_factory_methods(
        self,
        packet_factory: LifeSmartPacketFactory,
        protocol: LifeSmartProtocol,
        method_name: str,
        args: tuple,
        expected_structure: dict,
    ):
        """测试数据包工厂的各种构建方法。"""
        method = getattr(packet_factory, method_name)
        packet = method(*args)

        # 验证包可以被正确解码
        _, decoded_data = protocol.decode(packet)

        assert isinstance(decoded_data, list), "解码结果应该是列表"
        assert len(decoded_data) == 2, "应该包含两个元素"
        assert isinstance(decoded_data[0], dict), "第一个元素应该是字典"
        assert isinstance(decoded_data[1], dict), "第二个元素应该是字典"

        # 验证基本结构
        assert "args" in decoded_data[1], "第二个元素应该包含args"

        # 验证特定字段（如果存在）
        for key, expected_value in expected_structure.items():
            if key in decoded_data[1]:
                assert (
                    decoded_data[1][key] == expected_value
                ), f"{method_name}的{key}字段应该正确"

    def test_multi_epset_packet_structure(
        self, packet_factory: LifeSmartPacketFactory, protocol: LifeSmartProtocol
    ):
        """测试多端点设置包的特殊结构。"""
        io_list = [
            {"idx": "RGBW", "val": 12345},
            {"idx": "DYN", "val": 0},
            {"idx": "TEMP", "val": 250},
        ]

        packet = packet_factory.build_multi_epset_packet("test_device", io_list)
        _, decoded_data = protocol.decode(packet)

        args = decoded_data[1]["args"]
        assert "val" in args, "args中应该包含val字段"

        val_list = args["val"]
        assert isinstance(val_list, list), "val应该是列表类型"
        assert len(val_list) == 3, "应该包含3个元素"

        # 验证结构转换（idx -> key）
        for i, expected_item in enumerate(io_list):
            actual_item = val_list[i]
            assert (
                actual_item["key"] == expected_item["idx"]
            ), f"第{i + 1}个元素的key应该正确"
            assert (
                actual_item["val"] == expected_item["val"]
            ), f"第{i + 1}个元素的val应该正确"

    def test_ir_control_packet_special_fields(
        self, packet_factory: LifeSmartPacketFactory, protocol: LifeSmartProtocol
    ):
        """测试红外控制包的特殊字段。"""
        ir_options = {"keys": "power", "delay": 300}
        packet = packet_factory.build_ir_control_packet("ir_device", ir_options)
        _, decoded_data = protocol.decode(packet)

        args = decoded_data[1]["args"]
        assert "cron_name" in args, "应该包含cron_name字段"
        assert args["cron_name"] == "AI_IR_ir_device", "cron_name应该按规则生成"
        assert args["opt"] == ir_options, "选项应该正确传递"

    def test_send_ir_keys_packet_structure(
        self, packet_factory: LifeSmartPacketFactory, protocol: LifeSmartProtocol
    ):
        """测试红外按键发送包的结构。"""
        packet = packet_factory.build_send_ir_keys_packet(
            "ai1", "remote1", "tv", "samsung", '["power"]'
        )
        _, decoded_data = protocol.decode(packet)

        args = decoded_data[1]["args"]
        expected_fields = ["cron_name", "devid", "category", "brand", "opt"]

        for field in expected_fields:
            assert field in args, f"应该包含{field}字段"

        assert args["cron_name"] == "ai1", "cron_name字段应该正确"
        assert args["devid"] == "remote1", "devid字段应该正确"
        assert args["category"] == "tv", "category字段应该正确"
        assert args["brand"] == "samsung", "brand字段应该正确"
        assert args["opt"]["keys"] == ["power"], "opt.keys字段应该正确"


# ==================== 协议性能和边界测试类 ====================


class TestProtocolPerformanceAndLimits:
    """测试协议的性能和边界条件。"""

    def test_large_dataset_handling(self, protocol: LifeSmartProtocol):
        """测试大数据集的处理性能。"""
        # 创建一个大型数据集
        large_dataset = []
        for i in range(1000):
            device_data = {
                f"device_{i}": {
                    "id": f"dev_{i:04d}",
                    "type": f"type_{i % 10}",
                    "channels": [f"ch_{j}" for j in range(i % 5 + 1)],
                    "data": "X" * (i % 100 + 1),
                    "metadata": {
                        "version": f"1.{i % 10}.{i % 100}",
                        "properties": [f"prop_{k}" for k in range(i % 3 + 1)],
                    },
                }
            }
            large_dataset.append(device_data)

        # 编码和解码应该在合理时间内完成
        encoded_packet = protocol.encode(large_dataset)
        assert len(encoded_packet) > 0, "大数据集应该能够编码"

        _, decoded_dataset = protocol.decode(encoded_packet)
        assert decoded_dataset == large_dataset, "大数据集解码应该正确"

    def test_deep_nesting_handling(self, protocol: LifeSmartProtocol):
        """测试深度嵌套结构的处理。"""
        # 创建深度嵌套的数据结构
        deep_nested = {"level_0": {}}
        current_level = deep_nested["level_0"]

        for i in range(1, 50):  # 50层深度
            current_level[f"level_{i}"] = {}
            current_level = current_level[f"level_{i}"]

        current_level["final_data"] = "reached_bottom"

        test_message = [deep_nested]
        encoded_packet = protocol.encode(test_message)
        _, decoded_message = protocol.decode(encoded_packet)

        assert decoded_message == test_message, "深度嵌套结构应该正确处理"

    def test_concurrent_encoding_decoding(self, protocol: LifeSmartProtocol):
        """测试并发编码解码的数据一致性。"""
        import threading
        import time

        results = []
        errors = []

        def encode_decode_worker(worker_id: int):
            try:
                test_data = [
                    {
                        "worker_id": worker_id,
                        "timestamp": int(time.time()),
                        "data": f"worker_{worker_id}_data",
                    }
                ]

                for _ in range(10):  # 每个worker执行10次
                    encoded = protocol.encode(test_data)
                    _, decoded = protocol.decode(encoded)

                    if decoded != test_data:
                        errors.append(f"Worker {worker_id}: 数据不一致")
                    else:
                        results.append(worker_id)
            except Exception as e:
                errors.append(f"Worker {worker_id}: {str(e)}")

        # 启动多个并发worker
        threads = []
        for i in range(5):
            thread = threading.Thread(target=encode_decode_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        assert len(errors) == 0, f"并发处理不应该产生错误: {errors}"
        assert len(results) == 50, "所有worker操作都应该成功"  # 5个worker × 10次操作

    @pytest.mark.parametrize(
        "string_length",
        [0, 1, 255, 256, 1023, 1024, 4095, 4096, 65535],
        ids=[
            "Empty",
            "Single",
            "Small255",
            "Medium256",
            "Medium1K",
            "Large1K",
            "Large4K",
            "ExtraLarge4K",
            "Max64K",
        ],
    )
    def test_string_length_boundaries(
        self, protocol: LifeSmartProtocol, string_length: int
    ):
        """测试不同长度字符串的边界条件。"""
        test_string = "A" * string_length
        test_message = [{"test_string": test_string, "length": string_length}]

        encoded_packet = protocol.encode(test_message)
        _, decoded_message = protocol.decode(encoded_packet)

        assert (
            decoded_message == test_message
        ), f"长度为{string_length}的字符串应该正确处理"

    def test_memory_usage_patterns(self, protocol: LifeSmartProtocol):
        """测试内存使用模式和垃圾回收。"""
        import gc

        # 创建大量临时对象
        for i in range(100):
            temp_data = [{"iteration": i, "data": [j for j in range(i % 50)]}]
            encoded = protocol.encode(temp_data)
            _, decoded = protocol.decode(encoded)

            # 验证数据正确性
            assert decoded == temp_data, f"迭代{i}的数据应该正确"

        # 强制垃圾回收
        gc.collect()

        # 验证协议对象仍然正常工作
        final_test = [{"final_test": True, "status": "ok"}]
        encoded_final = protocol.encode(final_test)
        _, decoded_final = protocol.decode(encoded_final)

        assert decoded_final == final_test, "垃圾回收后协议应该仍然正常工作"
