"""
对 protocol.py 的单元测试和集成测试

此测试套件包含四个主要部分：
1.  对 LifeSmartProtocol 类的单元测试，验证核心数据类型的编解码及边界条件。
2.  对 LifeSmartPacketFactory 的集成验证，确保其生成的指令包可被协议正确解析。
3.  对 LifeSmartLocalTCPClient 的集成测试，通过模拟网络IO来验证其完整的生命周期和功能。
4.  对 LifeSmartLocalTCPClient 控制方法的全面单元测试，确保所有业务逻辑正确。
"""

import asyncio
import json
import logging
from io import BytesIO
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from custom_components.lifesmart.const import (
    CMD_TYPE_ON,
    CMD_TYPE_OFF,
    CMD_TYPE_PRESS,
    CMD_TYPE_SET_VAL,
    CMD_TYPE_SET_CONFIG,
    CMD_TYPE_SET_TEMP_DECIMAL,
    CMD_TYPE_SET_TEMP_FCU,
    CMD_TYPE_SET_RAW,
    DOOYA_TYPES,
    GARAGE_DOOR_TYPES,
    HVACMode,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_HIGH,
    NON_POSITIONAL_COVER_CONFIG,
)
from custom_components.lifesmart.core.local_tcp_client import LifeSmartLocalTCPClient
from custom_components.lifesmart.core.protocol import (
    LifeSmartProtocol,
    LifeSmartPacketFactory,
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
    return LifeSmartPacketFactory(node_agt="test_agt", node="test_node")


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


@pytest.fixture
def mocked_client() -> LifeSmartLocalTCPClient:
    """
    提供一个客户端实例，其 factory 是真实的，但网络发送是 mock 的。
    这允许我们检查 factory 的调用情况，而无需实际发送网络包。
    """
    client = LifeSmartLocalTCPClient("host", 1234, "u", "p")
    # 客户端需要一个真实的 factory 实例来调用其 build 方法
    client._factory = LifeSmartPacketFactory("test_agt", "test_node")
    # Mock 掉最底层的网络发送，因为我们不关心网络 IO
    client._send_packet = AsyncMock(return_value=0)
    return client


# ====================================================================
# Section 1: LifeSmartProtocol 核心功能测试
# ====================================================================


class TestLifeSmartProtocolDataTypes:
    """测试所有支持的数据类型的编码和解码。"""

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
            2147483647,
            -2147483648,
            "",
            "hello",
            "你好世界",
            "emoji: ✨",
            [],
            [1, True, "world", None],
            {},
            {"my_key": "val", "my_num": 123},
            {"a": 1, "b": {"c": [2, 3, {"nested": True}]}},
            "::NULL::",
        ],
        ids=lambda v: str(type(v).__name__) + "_" + str(v)[:20],
    )
    def test_basic_types_roundtrip(self, protocol: LifeSmartProtocol, value):
        original_message = [{"key": value}]
        encoded_packet = protocol.encode(original_message)
        _, decoded_list = protocol.decode(encoded_packet)
        assert decoded_list == original_message

    def test_dict_with_special_keys_roundtrip(self, protocol: LifeSmartProtocol):
        value_enum_prefix = {"enum:key": "val", "num": 123}
        expected_normalized = {"key": "val", "num": 123}
        encoded_packet1 = protocol.encode([value_enum_prefix])
        _, decoded_list1 = protocol.decode(encoded_packet1)
        assert decoded_list1 == [expected_normalized]

        value_to_be_enum = {"key": "val", "num": 123}
        encoded_packet2 = protocol.encode([value_to_be_enum])
        _, decoded_list2 = protocol.decode(encoded_packet2)
        assert decoded_list2 == [value_to_be_enum]

    def test_timestamp_type_handling(self, protocol: LifeSmartProtocol):
        timestamp_value = 16318742
        encoded_bytes = b"\x06\x01" + protocol._encode_varint(timestamp_value << 1)
        stream = BytesIO(encoded_bytes)
        data_type = stream.read(1)[0]
        decoded_obj = protocol._parse_value(stream, data_type)
        assert (
            isinstance(decoded_obj, LSTimestamp)
            and decoded_obj.value == timestamp_value
        )

        normalized_packet = protocol._normalize_structure([{"ts": decoded_obj}])
        encoded_packet = protocol.encode(normalized_packet)
        _, decoded_packet = protocol.decode(encoded_packet)
        assert decoded_packet == [{"ts": timestamp_value}]


class TestLifeSmartProtocolPacketHandling:
    """测试完整数据包的处理（帧、压缩）。"""

    def test_simple_packet_roundtrip(self, protocol: LifeSmartProtocol):
        original_packet_list = [{"a": 1, "type": "test"}, {"b": [2, 3]}]
        encoded_data = protocol.encode(original_packet_list)
        assert encoded_data.startswith(b"GL00")
        remaining, decoded_packet = protocol.decode(encoded_data)
        assert not remaining and decoded_packet == original_packet_list

    def test_compressed_packet_roundtrip(self, protocol: LifeSmartProtocol):
        large_object = [{"data": "X" * 2048}]
        encoded_data = protocol.encode(large_object)
        assert encoded_data.startswith(b"ZZ00")
        remaining, decoded_packet = protocol.decode(encoded_data)
        assert not remaining and decoded_packet == large_object

    def test_multi_packet_stream_decoding(self, protocol: LifeSmartProtocol):
        packet1, packet2 = [{"msg": "first"}], [{"msg": "second"}]
        encoded1, encoded2 = protocol.encode(packet1), protocol.encode(packet2)
        remaining, decoded1 = protocol.decode(encoded1 + encoded2)
        assert decoded1 == packet1 and remaining == encoded2


class TestLifeSmartProtocolErrorsAndBoundaries:
    """测试协议对格式错误或无效数据的鲁棒性。"""

    @pytest.mark.parametrize(
        "corrupted_data",
        [
            b"GL0",
            b"GL00\x00\x00",
            b"ZZ00\x00\x00",
            b"GL00\xff\xff\xff\xff_payload_too_short",
        ],
    )
    def test_decode_incomplete_data_raises_eof(self, protocol, corrupted_data):
        with pytest.raises(EOFError):
            protocol.decode(corrupted_data)

    @pytest.mark.parametrize(
        "invalid_data",
        [
            b"XXYY" + b"\x00" * 4 + b"junk",
            b"ZZ00\x00\x00\x00\x10" + b"this_is_not_gzipped_data",
        ],
    )
    def test_decode_invalid_data_raises_valueerror(self, protocol, invalid_data):
        with pytest.raises(ValueError):
            protocol.decode(invalid_data)

    def test_pack_integer_out_of_bounds_raises_error(self, protocol):
        with pytest.raises(ValueError, match="超出 32-bit 有符号范围"):
            protocol._pack_value(2147483648)
        with pytest.raises(ValueError, match="超出 32-bit 有符号范围"):
            protocol._pack_value(-2147483649)


# ====================================================================
# Section 2: LifeSmartPacketFactory 单元测试
# ====================================================================


class TestPacketFactoryUnit:
    """对 PacketFactory 的核心方法进行单元测试，确保它们生成可解码的包。"""

    def _decode_and_get_args(self, protocol, packet):
        _, decoded = protocol.decode(packet)
        return decoded[1]["args"]

    def test_multi_epset_packet_roundtrip(self, protocol, factory):
        io_list = [{"idx": "RGBW", "val": 12345}, {"idx": "DYN", "val": 0}]
        packet = factory.build_multi_epset_packet("dev456", io_list)
        args = self._decode_and_get_args(protocol, packet)
        val_list = args["val"]
        assert isinstance(val_list, list)
        # Note: The factory translates 'idx' to 'key'
        assert val_list[0] == {"key": "RGBW", "val": 12345}
        assert val_list[1] == {"key": "DYN", "val": 0}

    def test_ir_control_packet_roundtrip(self, protocol, factory):
        packet = factory.build_ir_control_packet("ir_dev", {"keys": "power"})
        args = self._decode_and_get_args(protocol, packet)
        assert args["cron_name"] == "AI_IR_ir_dev"
        assert args["opt"] == {"keys": "power"}


# ====================================================================
# Section 3: LifeSmartLocalTCPClient 集成与辅助函数测试
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


class TestLifeSmartClientIntegration:
    """测试客户端的连接、生命周期和网络交互。"""

    @pytest.mark.asyncio
    async def test_client_full_successful_lifecycle(self, mock_connection):
        """
        测试客户端从连接、登录、加载设备、接收状态更新到断开的完整成功生命周期。
        """
        reader, writer, _ = mock_connection
        client = LifeSmartLocalTCPClient("localhost", 9999, "user", "pass")
        callback = AsyncMock()
        connect_task = asyncio.create_task(client.async_connect(callback))

        # 1. 模拟登录成功
        reader.feed_data(LOGIN_SUCCESS_PKT)
        await asyncio.sleep(0.1)
        assert client.is_connected, "客户端在登录后应处于连接状态"

        # 2. 模拟设备列表响应
        reader.feed_data(DEVICE_LIST_PKT)
        devices = await client.get_all_device_async(timeout=1)
        assert len(devices) == 1 and "d1" in client.devices, "应成功加载一个设备"
        assert (
            client.devices["d1"]["data"]["L1"]["name"] == "Switch Button"
        ), "设备子项名称应被正确解析"

        # 3. 模拟状态更新并验证回调
        reader.feed_data(STATUS_UPDATE_PKT)
        await asyncio.sleep(0.01)

        # 我们构造一个期望的 msg，它应该与客户端内部构造的完全一致
        expected_msg = {
            "me": "d1",
            "idx": "L1",
            "agt": "test_agt",
            "devtype": "SL_SW_IF1",
            **client.devices["d1"]["data"]["L1"],  # 包含所有子设备属性
        }
        callback.assert_any_call({"type": "io", "msg": expected_msg})

        # 4. 模拟设备删除事件
        reader.feed_data(DEVICE_DELETED_PKT)
        await asyncio.sleep(0.01)
        callback.assert_any_call({"reload": True})

        # 5. 断开连接并验证任务清理
        client.disconnect()
        try:
            await asyncio.wait_for(connect_task, timeout=1.0)
        except asyncio.CancelledError:
            pass  # 任务被取消是预期的行为

        writer.close.assert_called_once()
        assert connect_task.done(), "后台连接任务在断开后应处于完成状态"

    @pytest.mark.asyncio
    async def test_client_connection_failures(self, mock_connection):
        reader, writer, mock_open = mock_connection
        mock_open.side_effect = ConnectionRefusedError
        client_refused = LifeSmartLocalTCPClient("invalid.host", 1234, "u", "p")
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(client_refused.async_connect(None), timeout=0.1)

        mock_open.side_effect = None
        mock_open.return_value = (reader, writer)
        reader.feed_data(LOGIN_FAILURE_PKT)
        client_fail = LifeSmartLocalTCPClient("valid.host", 1234, "u", "p")
        await asyncio.wait_for(client_fail.async_connect(None), timeout=1)
        assert client_fail.disconnected is True

    @pytest.mark.asyncio
    async def test_send_packet_returns_error_if_not_connected(self):
        client = LifeSmartLocalTCPClient("localhost", 9999, "u", "p")
        client.writer = None
        with patch(
            "custom_components.lifesmart.core.local_tcp_client._LOGGER"
        ) as mock_logger:
            result = await client._send_packet(b"test")
            assert result == -1
            mock_logger.error.assert_called_with("本地客户端未连接，无法发送指令。")

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
            ({"name": "NoSub", "val": 1}, {"name": "NoSub", "val": 1}),
        ],
    )
    def test_normalize_device_names(self, input_dict, expected_dict):
        normalized = LifeSmartLocalTCPClient._normalize_device_names(input_dict)
        assert normalized == expected_dict

    @pytest.mark.asyncio
    async def test_client_keepalive_on_idle(self, mock_connection):
        """
        测试客户端在连接空闲时是否会正确发送心跳包以维持连接。
        这是针对 'loaded' 阶段超时问题的回归测试。
        """
        reader, writer, _ = mock_connection
        client = LifeSmartLocalTCPClient("localhost", 9999, "user", "pass")

        # Mock 掉 PacketFactory 的 build 方法，以便我们可以监视它的调用
        with patch.object(
            client._factory, "build_get_config_packet", return_value=b"heartbeat_pkt"
        ) as mock_build_heartbeat:

            # 将 read 操作的默认超时缩短，以便测试能快速触发心跳
            client.IDLE_TIMEOUT = 0.1

            connect_task = asyncio.create_task(client.async_connect(AsyncMock()))

            # 走完登录和加载流程
            reader.feed_data(LOGIN_SUCCESS_PKT)
            await asyncio.sleep(0.01)
            reader.feed_data(DEVICE_LIST_PKT)
            await asyncio.sleep(0.01)

            # 此时客户端进入 'loaded' 阶段，开始等待
            # 等待时间超过我们设置的 0.1 秒超时
            await asyncio.sleep(0.2)

            # 验证：心跳包是否被构建和发送
            mock_build_heartbeat.assert_any_call(client.node)

            # 清理
            client.disconnect()
            try:
                # 等待任务响应取消并完成
                await asyncio.wait_for(connect_task, timeout=1.0)
            except asyncio.CancelledError:
                pass


# ====================================================================
# Section 4: LifeSmartLocalTCPClient 控制方法单元测试 (全面覆盖)
# ====================================================================


class TestLifeSmartClientControlMethods:
    """全面测试 LifeSmartLocalTCPClient 的高层控制方法。"""

    @pytest.mark.asyncio
    async def test_turn_on_light_switch(self, mocked_client: LifeSmartLocalTCPClient):
        with patch.object(
            mocked_client._factory, "build_epset_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.turn_on_light_switch_async("L1", "agt", "dev1")
            mock_build.assert_called_once_with("dev1", "L1", CMD_TYPE_ON, 1)
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_turn_off_light_switch(self, mocked_client: LifeSmartLocalTCPClient):
        with patch.object(
            mocked_client._factory, "build_epset_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.turn_off_light_switch_async("L1", "agt", "dev1")
            mock_build.assert_called_once_with("dev1", "L1", CMD_TYPE_OFF, 0)
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "device_type, command_method, expected_idx, expected_type, expected_val",
        [
            (
                list(GARAGE_DOOR_TYPES)[0],
                "open_cover_async",
                "P3",
                CMD_TYPE_SET_VAL,
                100,
            ),
            (
                list(GARAGE_DOOR_TYPES)[0],
                "close_cover_async",
                "P3",
                CMD_TYPE_SET_VAL,
                0,
            ),
            (
                list(GARAGE_DOOR_TYPES)[0],
                "stop_cover_async",
                "P3",
                CMD_TYPE_SET_CONFIG,
                CMD_TYPE_OFF,
            ),
            (list(DOOYA_TYPES)[0], "open_cover_async", "P2", CMD_TYPE_SET_VAL, 100),
            (list(DOOYA_TYPES)[0], "close_cover_async", "P2", CMD_TYPE_SET_VAL, 0),
            (
                list(DOOYA_TYPES)[0],
                "stop_cover_async",
                "P2",
                CMD_TYPE_SET_CONFIG,
                CMD_TYPE_OFF,
            ),
            (
                "SL_SW_WIN",
                "open_cover_async",
                NON_POSITIONAL_COVER_CONFIG["SL_SW_WIN"]["open"],
                CMD_TYPE_ON,
                1,
            ),
            (
                "SL_SW_WIN",
                "close_cover_async",
                NON_POSITIONAL_COVER_CONFIG["SL_SW_WIN"]["close"],
                CMD_TYPE_ON,
                1,
            ),
            (
                "SL_SW_WIN",
                "stop_cover_async",
                NON_POSITIONAL_COVER_CONFIG["SL_SW_WIN"]["stop"],
                CMD_TYPE_ON,
                1,
            ),
        ],
    )
    async def test_cover_commands(
        self,
        mocked_client,
        device_type,
        command_method,
        expected_idx,
        expected_type,
        expected_val,
    ):
        with patch.object(
            mocked_client._factory, "build_epset_packet", return_value=b"packet"
        ) as mock_build:
            method_to_call = getattr(mocked_client, command_method)
            await method_to_call("agt", "dev1", device_type)
            mock_build.assert_called_once_with(
                "dev1", expected_idx, expected_type, expected_val
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "device_type, position, expected_idx",
        [(list(GARAGE_DOOR_TYPES)[0], 50, "P3"), (list(DOOYA_TYPES)[0], 80, "P2")],
    )
    async def test_set_cover_position(
        self, mocked_client, device_type, position, expected_idx
    ):
        with patch.object(
            mocked_client._factory, "build_epset_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.set_cover_position_async(
                "agt", "dev1", position, device_type
            )
            mock_build.assert_called_once_with(
                "dev1", expected_idx, CMD_TYPE_SET_VAL, position
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "device_type, hvac_mode, current_val, expected_calls",
        [
            (
                "SL_NATURE",
                HVACMode.HEAT,
                0,
                [("P1", CMD_TYPE_ON, 1), ("P7", CMD_TYPE_SET_CONFIG, 4)],
            ),
            (
                "SL_CP_AIR",
                HVACMode.COOL,
                15,
                [("P1", CMD_TYPE_ON, 1), ("P1", CMD_TYPE_SET_RAW, 15)],
            ),
            ("V_AIR_P", HVACMode.OFF, 0, [("P1", CMD_TYPE_OFF, 0)]),
        ],
    )
    async def test_set_climate_hvac_mode(
        self, mocked_client, device_type, hvac_mode, current_val, expected_calls
    ):
        with patch.object(
            mocked_client._factory, "build_epset_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.async_set_climate_hvac_mode(
                "agt", "dev1", device_type, hvac_mode, current_val
            )
            assert mock_build.call_count == len(expected_calls)
            for i, call_args in enumerate(expected_calls):
                assert mock_build.call_args_list[i].args == ("dev1", *call_args)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "device_type, temp, expected_idx, expected_type, expected_val",
        [
            ("V_AIR_P", 25.5, "tT", CMD_TYPE_SET_TEMP_DECIMAL, 255),
            ("SL_CP_DN", 18.0, "P3", CMD_TYPE_SET_RAW, 180),
            ("SL_FCU", 22.0, "P8", CMD_TYPE_SET_TEMP_FCU, 220),
        ],
    )
    async def test_set_climate_temperature(
        self,
        mocked_client,
        device_type,
        temp,
        expected_idx,
        expected_type,
        expected_val,
    ):
        with patch.object(
            mocked_client._factory, "build_epset_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.async_set_climate_temperature(
                "agt", "dev1", device_type, temp
            )
            mock_build.assert_called_once_with(
                "dev1", expected_idx, expected_type, expected_val
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "device_type, fan_mode, current_val, expected_idx, expected_type, expected_val",
        [
            ("V_AIR_P", FAN_LOW, 0, "F", CMD_TYPE_SET_CONFIG, 15),
            ("SL_NATURE", FAN_HIGH, 0, "P9", CMD_TYPE_SET_CONFIG, 75),
            (
                "SL_CP_AIR",
                FAN_MEDIUM,
                15,
                "P1",
                CMD_TYPE_SET_RAW,
                65551,
            ),  # (15 & ~(3<<15)) | (2<<15)
        ],
    )
    async def test_set_climate_fan_mode(
        self,
        mocked_client,
        device_type,
        fan_mode,
        current_val,
        expected_idx,
        expected_type,
        expected_val,
    ):
        with patch.object(
            mocked_client._factory, "build_epset_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.async_set_climate_fan_mode(
                "agt", "dev1", device_type, fan_mode, current_val
            )
            mock_build.assert_called_once_with(
                "dev1", expected_idx, expected_type, expected_val
            )

    @pytest.mark.asyncio
    async def test_press_switch(self, mocked_client: LifeSmartLocalTCPClient):
        with patch.object(
            mocked_client._factory, "build_epset_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.press_switch_async("L1", "agt", "dev1", 550)
            mock_build.assert_called_once_with("dev1", "L1", CMD_TYPE_PRESS, 6)

    @pytest.mark.asyncio
    async def test_set_scene(self, mocked_client: LifeSmartLocalTCPClient):
        with patch.object(
            mocked_client._factory, "build_scene_trigger_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.set_scene_async("agt", "scene123")
            mock_build.assert_called_once_with("scene123")
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_change_icon(self, mocked_client: LifeSmartLocalTCPClient):
        with patch.object(
            mocked_client._factory, "build_change_icon_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.change_icon_async("dev1", "icon_name")
            mock_build.assert_called_once_with("dev1", "icon_name")
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ir_control(self, mocked_client: LifeSmartLocalTCPClient):
        with patch.object(
            mocked_client._factory, "build_ir_control_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.ir_control_async("ir_dev", {"keys": "power"})
            mock_build.assert_called_once_with("ir_dev", {"keys": "power"})
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_ir_keys(self, mocked_client: LifeSmartLocalTCPClient):
        keys_json = json.dumps([{"key": "power", "delay": 300}])
        with patch.object(
            mocked_client._factory, "build_send_ir_keys_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.send_ir_key_async(
                "agt", "ai_id", "dev1", "cat1", "brand1", keys_json
            )
            mock_build.assert_called_once_with(
                "ai_id", "dev1", "cat1", "brand1", keys_json
            )
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_send_multi_command(
        self, mocked_client: LifeSmartLocalTCPClient
    ):
        """测试新的抽象方法"""
        io_list = [{"idx": "RGBW", "val": 12345}, {"idx": "DYN", "val": 0}]
        with patch.object(
            mocked_client._factory, "build_multi_epset_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client._async_send_multi_command("agt", "dev1", io_list)
            mock_build.assert_called_once_with("dev1", io_list)
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_add_trigger(self, mocked_client: LifeSmartLocalTCPClient):
        with patch.object(
            mocked_client._factory, "build_add_trigger_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.add_trigger_async("my_trigger", "cmd_list_str")
            mock_build.assert_called_once_with("my_trigger", "cmd_list_str")
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_del_ai(self, mocked_client: LifeSmartLocalTCPClient):
        with patch.object(
            mocked_client._factory, "build_del_ai_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.del_ai_async("my_ai_to_delete")
            mock_build.assert_called_once_with("my_ai_to_delete")
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_ir_code(self, mocked_client: LifeSmartLocalTCPClient):
        code_data = [1, 2, 3]
        with patch.object(
            mocked_client._factory, "build_send_code_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.send_ir_code_async("ir_dev", code_data)
            mock_build.assert_called_once_with("ir_dev", code_data)
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ir_raw_control(self, mocked_client: LifeSmartLocalTCPClient):
        raw_data_str = '{"some": "data"}'
        with patch.object(
            mocked_client._factory,
            "build_ir_raw_control_packet",
            return_value=b"packet",
        ) as mock_build:
            await mocked_client.ir_raw_control_async("ir_dev", raw_data_str)
            mock_build.assert_called_once_with("ir_dev", raw_data_str)
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_set_eeprom(self, mocked_client: LifeSmartLocalTCPClient):
        with patch.object(
            mocked_client._factory, "build_set_eeprom_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.set_eeprom_async("dev1", "config_key", "config_val")
            mock_build.assert_called_once_with("dev1", "config_key", "config_val")
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_add_timer(self, mocked_client: LifeSmartLocalTCPClient):
        with patch.object(
            mocked_client._factory, "build_add_timer_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.add_timer_async("dev1", "0 8 * * *", "L1=ON")
            mock_build.assert_called_once_with("dev1", "0 8 * * *", "L1=ON")
            mocked_client._send_packet.assert_awaited_once()
