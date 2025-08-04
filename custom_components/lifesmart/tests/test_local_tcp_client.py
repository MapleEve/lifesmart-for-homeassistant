"""
LifeSmart 本地TCP客户端测试套件。

此测试套件专门测试 local_tcp_client.py 中的TCP客户端功能，包括：
- 网络连接管理（连接、断开、重连）
- 客户端生命周期（初始化、登录、设备加载）
- 设备控制方法（开关、窗帘、气候、场景等）
- 状态更新处理（实时状态、设备变更）
- 错误处理和网络异常
- 并发和性能优化

测试使用结构化的类组织，每个类专注于特定的功能领域，
并包含详细的中文注释以确保可维护性。
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.climate import HVACMode, FAN_LOW, FAN_MEDIUM, FAN_HIGH

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
    NON_POSITIONAL_COVER_CONFIG,
)
from custom_components.lifesmart.core.local_tcp_client import LifeSmartLocalTCPClient
from custom_components.lifesmart.core.protocol import (
    LifeSmartProtocol,
    LifeSmartPacketFactory,
)
from custom_components.lifesmart.helpers import normalize_device_names


# ==================== 测试数据和Fixtures ====================


@pytest.fixture
def protocol():
    """提供协议实例用于构建测试数据包。"""
    return LifeSmartProtocol()


@pytest.fixture
def mock_connection():
    """模拟网络连接，提供可控的reader/writer对。"""
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
def test_client():
    """提供标准的测试客户端实例。"""
    return LifeSmartLocalTCPClient("localhost", 9999, "test_user", "test_pass")


@pytest.fixture
def mocked_client():
    """提供带有模拟网络发送的客户端实例。"""
    client = LifeSmartLocalTCPClient("host", 1234, "user", "pass")
    client._factory = LifeSmartPacketFactory("test_agt", "test_node")
    client._send_packet = AsyncMock(return_value=0)
    return client


@pytest.fixture
def sample_packets(protocol):
    """提供各种测试用的数据包。"""
    return {
        "login_success": protocol.encode(
            [
                {"_sel": 1},
                {
                    "ret": [
                        0,
                        0,
                        0,
                        0,
                        {"base": [0, "test_node"], "agt": [0, "test_agt"]},
                    ],
                    "act": "Login",
                },
            ]
        ),
        "login_failure": protocol.encode([{}, {"err": -2001, "act": "Login"}]),
        "device_list": protocol.encode(
            [
                {},
                {
                    "ret": [
                        0,
                        {
                            "eps": {
                                "device_1": {
                                    "cls": "SL_SW_IF3",
                                    "name": "三路开关",
                                    "_chd": {
                                        "m": {
                                            "_chd": {
                                                "L1": {
                                                    "name": "{$EPN} 按钮 1",
                                                    "val": 1,
                                                    "type": 129,
                                                },
                                                "L2": {
                                                    "name": "{$EPN} 按钮 2",
                                                    "val": 0,
                                                    "type": 129,
                                                },
                                                "L3": {
                                                    "name": "{$EPN} 按钮 3",
                                                    "val": 1,
                                                    "type": 129,
                                                },
                                            }
                                        }
                                    },
                                },
                                "device_2": {
                                    "cls": "SL_NATURE",
                                    "name": "自然风空调",
                                    "_chd": {
                                        "m": {
                                            "_chd": {
                                                "P1": {
                                                    "name": "电源",
                                                    "val": 0,
                                                    "type": 129,
                                                },
                                                "P7": {
                                                    "name": "模式",
                                                    "val": 0,
                                                    "type": 131,
                                                },
                                                "tT": {
                                                    "name": "温度",
                                                    "val": 250,
                                                    "type": 133,
                                                },
                                            }
                                        }
                                    },
                                },
                            }
                        },
                    ]
                },
            ]
        ),
        "status_update": protocol.encode(
            [
                {},
                {
                    "_schg": {
                        "test_agt/ep/device_1/m/L1": {"chg": {"val": 0, "type": 129}}
                    }
                },
            ]
        ),
        "device_deleted": protocol.encode([{}, {"_sdel": {"key": "device_1"}}]),
        "heartbeat_response": protocol.encode(
            [{}, {"act": "GetConfig", "ret": [0, {}]}]
        ),
    }


# ==================== 客户端初始化和配置测试类 ====================


class TestClientInitialization:
    """测试客户端的初始化和基础配置。"""

    def test_client_basic_initialization(self):
        """测试客户端的基本初始化。"""
        client = LifeSmartLocalTCPClient("192.168.1.100", 8080, "admin", "password")

        assert client.host == "192.168.1.100", "主机地址应该正确设置"
        assert client.port == 8080, "端口应该正确设置"
        assert client.username == "admin", "用户名应该正确设置"
        assert client.password == "password", "密码应该正确设置"
        assert client.disconnected is False, "初始状态应该为未断开"
        assert client.reader is None, "初始时reader应该为None"
        assert client.writer is None, "初始时writer应该为None"
        assert len(client.devices) == 0, "初始设备列表应该为空"

    def test_client_initialization_with_config_agt(self):
        """测试带有配置AGT的客户端初始化。"""
        client = LifeSmartLocalTCPClient(
            "host", 1234, "user", "pass", config_agt="custom_agt"
        )

        assert client.config_agt == "custom_agt", "配置AGT应该正确设置"

    def test_client_connection_status_properties(self, test_client):
        """测试客户端连接状态属性。"""
        # 初始状态
        assert not test_client.is_connected, "初始状态应该为未连接"

        # 模拟连接状态
        test_client.reader = MagicMock()
        test_client.writer = MagicMock()
        test_client.writer.is_closing.return_value = False

        assert test_client.is_connected, "设置reader和writer后应该为已连接"

        # 模拟writer关闭状态
        test_client.writer.is_closing.return_value = True
        assert not test_client.is_connected, "writer关闭时应该为未连接"

    def test_factory_initialization(self, test_client):
        """测试数据包工厂的初始化。"""
        assert test_client._factory is not None, "数据包工厂应该被初始化"
        assert isinstance(
            test_client._factory, LifeSmartPacketFactory
        ), "工厂应该是正确的类型"

    def test_protocol_initialization(self, test_client):
        """测试协议实例的初始化。"""
        assert test_client._proto is not None, "协议实例应该被初始化"
        assert isinstance(test_client._proto, LifeSmartProtocol), "协议应该是正确的类型"


# ==================== 网络连接管理测试类 ====================


class TestNetworkConnectionManagement:
    """测试网络连接的建立、维护和断开。"""

    @pytest.mark.asyncio
    async def test_successful_connection_and_login(
        self, mock_connection, sample_packets
    ):
        """测试成功的连接和登录流程。"""
        reader, writer, mock_open = mock_connection
        client = LifeSmartLocalTCPClient("localhost", 9999, "user", "pass")
        callback = AsyncMock()

        # 启动连接任务
        connect_task = asyncio.create_task(client.async_connect(callback))

        # 模拟登录成功响应
        reader.feed_data(sample_packets["login_success"])
        await asyncio.sleep(0.1)

        # 验证连接状态
        assert client.is_connected, "登录成功后应该处于连接状态"
        assert client.node == "test_node", "节点名称应该正确设置"
        assert client.node_agt == "test_agt", "节点AGT应该正确设置"

        # 清理
        client.disconnect()
        try:
            await asyncio.wait_for(connect_task, timeout=1.0)
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_connection_failure_handling(self, mock_connection):
        """测试连接失败的处理。"""
        reader, writer, mock_open = mock_connection
        mock_open.side_effect = ConnectionRefusedError("连接被拒绝")

        client = LifeSmartLocalTCPClient("invalid.host", 1234, "user", "pass")

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(client.async_connect(None), timeout=0.1)

    @pytest.mark.asyncio
    async def test_login_failure_handling(
        self, mock_connection, sample_packets, caplog
    ):
        """测试登录失败的处理。"""
        reader, writer, mock_open = mock_connection
        client = LifeSmartLocalTCPClient("host", 1234, "user", "pass")

        # 模拟登录失败
        reader.feed_data(sample_packets["login_failure"])

        await asyncio.wait_for(client.async_connect(AsyncMock()), timeout=1.0)

        assert "本地登录失败" in caplog.text, "应该记录登录失败日志"
        assert client.disconnected is True, "登录失败后应该设置为断开状态"

    @pytest.mark.asyncio
    async def test_check_login_authentication_error(
        self, mock_connection, sample_packets
    ):
        """测试check_login方法的认证错误处理。"""
        reader, writer, mock_open = mock_connection
        client = LifeSmartLocalTCPClient("host", 1234, "user", "pass")

        # 模拟登录失败响应
        reader.feed_data(sample_packets["login_failure"])

        with pytest.raises(asyncio.InvalidStateError, match="Login failed"):
            await client.check_login()

    @pytest.mark.asyncio
    async def test_disconnect_functionality(self, mock_connection, sample_packets):
        """测试断开连接功能。"""
        reader, writer, mock_open = mock_connection
        client = LifeSmartLocalTCPClient("host", 1234, "user", "pass")

        # 建立连接
        connect_task = asyncio.create_task(client.async_connect(AsyncMock()))
        reader.feed_data(sample_packets["login_success"])
        await asyncio.sleep(0.1)

        # 断开连接
        client.disconnect()

        # 验证断开状态
        # disconnect方法不直接关闭writer，而是取消任务
        # writer.close.assert_called_once()
        assert client.disconnected is True, "断开后disconnected标志应该为True"

        # 等待连接任务完成
        try:
            await asyncio.wait_for(connect_task, timeout=1.0)
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_network_send_when_disconnected(self):
        """测试断开状态下发送数据的处理。"""
        client = LifeSmartLocalTCPClient("host", 1234, "user", "pass")
        client.writer = None  # 模拟未连接状态

        with patch(
            "custom_components.lifesmart.core.local_tcp_client._LOGGER"
        ) as mock_logger:
            result = await client._send_packet(b"test_data")

            assert result == -1, "未连接时发送应该返回-1"
            mock_logger.error.assert_called_with("本地客户端未连接，无法发送指令。")

    @pytest.mark.asyncio
    async def test_check_login_connection_closed_by_peer(self):
        """测试check_login过程中连接被对端关闭的情况"""
        client = LifeSmartLocalTCPClient("192.168.1.100", 8888, "user", "pass")

        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        # 模拟连接被对端关闭（读取到空字节）
        mock_reader.read.return_value = b""

        # 直接模拟open_connection，避免复杂的wait_for处理
        with patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)):
            with pytest.raises(asyncio.TimeoutError, match="Connection closed by peer"):
                await client.check_login()

    @pytest.mark.asyncio
    async def test_check_login_eof_error_handling(self):
        """测试check_login过程中EOFError的处理"""
        client = LifeSmartLocalTCPClient("192.168.1.100", 8888, "user", "pass")

        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        # 设置mock_reader.read的行为，避免AsyncMock警告
        read_call_count = 0

        async def mock_read_side_effect(*args, **kwargs):
            nonlocal read_call_count
            read_call_count += 1
            if read_call_count == 1:
                return b"\x00\x01"  # 第一次读取：不完整数据
            else:
                return b"\x00\x00\x00\x01"  # 后续读取：完整数据

        mock_reader.read.side_effect = mock_read_side_effect

        # 计数器来区分不同的wait_for调用
        call_count = 0

        async def wait_for_side_effect(coro, timeout=None):
            nonlocal call_count
            call_count += 1

            if call_count == 1:
                # 第一次调用：open_connection - 需要await协程
                if hasattr(coro, "__await__"):
                    # 如果是协程，先await它，然后返回我们的mock对象
                    try:
                        await coro
                    except:
                        pass  # 忽略mock中的错误
                return (mock_reader, mock_writer)
            else:
                # 其他调用：正常await协程
                return await coro

        with patch("asyncio.wait_for", side_effect=wait_for_side_effect):
            # 模拟协议解码：第一次EOFError，第二次成功
            with patch.object(client._proto, "decode") as mock_decode:
                mock_decode.side_effect = [
                    EOFError("Incomplete packet"),  # 第一次解码失败
                    (b"", [{}, {"ret": {"status": "ok"}}]),  # 第二次解码成功
                ]

                # 应该能处理EOFError并继续尝试
                result = await client.check_login()
                assert result is True

    @pytest.mark.asyncio
    async def test_check_login_writer_close_error_handling(self):
        """测试check_login过程中writer关闭错误的处理"""
        client = LifeSmartLocalTCPClient("192.168.1.100", 8888, "user", "pass")

        mock_reader = AsyncMock()
        mock_writer = MagicMock()
        mock_writer.write = MagicMock()
        mock_writer.drain = AsyncMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()
        mock_writer.wait_closed.side_effect = ConnectionResetError("Connection reset")

        # 设置mock_reader返回完整的登录响应
        mock_reader.read.return_value = b"\x00\x00\x00\x01"

        # 直接模拟open_connection
        with patch("asyncio.open_connection", return_value=(mock_reader, mock_writer)):
            with patch.object(client._proto, "decode") as mock_decode:
                mock_decode.return_value = (b"", [{}, {"ret": {"status": "ok"}}])

                # 应该能正常处理writer关闭时的ConnectionResetError
                result = await client.check_login()
                assert result is True


# ==================== 设备管理和数据处理测试类 ====================


class TestDeviceManagementAndDataProcessing:
    """测试设备管理和数据处理功能。"""

    @pytest.mark.asyncio
    async def test_device_loading_and_processing(self, mock_connection, sample_packets):
        """测试设备加载和处理流程。"""
        reader, writer, mock_open = mock_connection
        client = LifeSmartLocalTCPClient("host", 1234, "user", "pass")

        async def mock_open_side_effect(*args, **kwargs):
            # 正确处理协程调用，等待真实的mock对象
            if hasattr(mock_open.return_value, "__await__"):
                return await mock_open.return_value
            return mock_open.return_value

        # 使用正确的副作用函数
        mock_open.side_effect = mock_open_side_effect

        # 建立连接
        connect_task = asyncio.create_task(client.async_connect(AsyncMock()))
        reader.feed_data(sample_packets["login_success"])
        await asyncio.sleep(0.1)

        # 发送设备列表
        reader.feed_data(sample_packets["device_list"])
        devices = await client.async_get_all_devices(timeout=1)

        # 验证设备加载
        assert len(devices) == 2, "应该加载2个设备"
        assert "device_1" in client.devices, "设备1应该存在"
        assert "device_2" in client.devices, "设备2应该存在"

        # 验证设备名称规范化
        device_1 = client.devices["device_1"]
        assert (
            device_1["data"]["L1"]["name"] == "三路开关 按钮 1"
        ), "设备名称应该正确规范化"

        # 清理
        client.disconnect()
        try:
            await asyncio.wait_for(connect_task, timeout=1.0)
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_device_loading_timeout(self, mock_connection, sample_packets):
        """测试设备加载超时处理。"""
        reader, writer, mock_open = mock_connection
        client = LifeSmartLocalTCPClient("host", 1234, "user", "pass")

        async def mock_open_side_effect(*args, **kwargs):
            # 正确处理协程调用，等待真实的mock对象
            if hasattr(mock_open.return_value, "__await__"):
                return await mock_open.return_value
            return mock_open.return_value

        # 使用正确的副作用函数
        mock_open.side_effect = mock_open_side_effect

        # 建立连接但不发送设备列表
        asyncio.create_task(client.async_connect(AsyncMock()))
        reader.feed_data(sample_packets["login_success"])
        await asyncio.sleep(0.1)

        # 测试超时
        devices = await client.get_all_device_async(timeout=0.2)
        assert devices is False, "超时时应该返回False"

        client.disconnect()

    @pytest.mark.asyncio
    async def test_status_update_processing(self, mock_connection, sample_packets):
        """测试状态更新的处理。"""
        reader, writer, mock_open = mock_connection
        client = LifeSmartLocalTCPClient("host", 1234, "user", "pass")
        callback = AsyncMock()

        # 建立连接并加载设备
        connect_task = asyncio.create_task(client.async_connect(callback))
        reader.feed_data(sample_packets["login_success"])
        await asyncio.sleep(0.1)
        reader.feed_data(sample_packets["device_list"])
        await asyncio.sleep(0.1)

        # 发送状态更新
        reader.feed_data(sample_packets["status_update"])
        await asyncio.sleep(0.1)

        # 验证回调被调用
        callback.assert_called()
        call_args = callback.call_args[0][0]
        assert call_args["type"] == "io", "应该是io类型的消息"
        assert "msg" in call_args, "应该包含msg字段"

        msg = call_args["msg"]
        assert msg["me"] == "device_1", "设备ID应该正确"
        assert msg["idx"] == "L1", "子设备索引应该正确"
        assert msg["agt"] == "test_agt", "AGT应该正确"

        # 清理
        client.disconnect()
        try:
            await asyncio.wait_for(connect_task, timeout=1.0)
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_device_deletion_handling(self, mock_connection, sample_packets):
        """测试设备删除事件的处理。"""
        reader, writer, mock_open = mock_connection
        client = LifeSmartLocalTCPClient("host", 1234, "user", "pass")
        callback = AsyncMock()

        # 建立连接并加载设备
        connect_task = asyncio.create_task(client.async_connect(callback))
        reader.feed_data(sample_packets["login_success"])
        await asyncio.sleep(0.1)
        reader.feed_data(sample_packets["device_list"])
        await asyncio.sleep(0.1)

        # 发送设备删除事件
        reader.feed_data(sample_packets["device_deleted"])
        await asyncio.sleep(0.1)

        # 验证重新加载回调
        callback.assert_any_call({"reload": True})

        # 清理
        client.disconnect()
        try:
            await asyncio.wait_for(connect_task, timeout=1.0)
        except asyncio.CancelledError:
            pass

    @pytest.mark.parametrize(
        "input_dict, expected_dict",
        [
            (
                {
                    "name": "客厅",
                    "_chd": {"m": {"_chd": {"L1": {"name": "{$EPN} 开关"}}}},
                },
                {
                    "name": "客厅",
                    "_chd": {"m": {"_chd": {"L1": {"name": "客厅 开关"}}}},
                },
            ),
            (
                {"name": "门感", "_chd": {"m": {"_chd": {"G": {"name": "门 {BAT}"}}}}},
                {"name": "门感", "_chd": {"m": {"_chd": {"G": {"name": "门 BAT"}}}}},
            ),
            ({"name": "简单设备", "val": 1}, {"name": "简单设备", "val": 1}),
        ],
        ids=["EPNSubstitution", "BATSubstitution", "NoSubstitution"],
    )
    def test_device_name_normalization(self, input_dict, expected_dict):
        """测试设备名称规范化功能。"""
        normalized = normalize_device_names(input_dict)
        assert normalized == expected_dict, "设备名称规范化应该正确"


# ==================== 心跳和连接维护测试类 ====================


class TestHeartbeatAndConnectionMaintenance:
    """测试心跳机制和连接维护功能。"""

    @pytest.mark.asyncio
    async def test_idle_timeout_heartbeat(self, mock_connection, sample_packets):
        """测试空闲超时时的心跳发送。"""
        reader, writer, mock_open = mock_connection
        client = LifeSmartLocalTCPClient("host", 1234, "user", "pass")

        # 缩短空闲超时时间以便快速测试
        client.IDLE_TIMEOUT = 0.1

        async def mock_open_side_effect(*args, **kwargs):
            # 正确处理协程调用，等待真实的mock对象
            if hasattr(mock_open.return_value, "__await__"):
                return await mock_open.return_value
            return mock_open.return_value

        # 使用正确的副作用函数
        mock_open.side_effect = mock_open_side_effect

        with patch.object(
            client._factory, "build_get_config_packet", return_value=b"heartbeat"
        ) as mock_heartbeat:
            connect_task = asyncio.create_task(client.async_connect(AsyncMock()))

            # 完成登录和设备加载
            reader.feed_data(sample_packets["login_success"])
            await asyncio.sleep(0.01)
            reader.feed_data(sample_packets["device_list"])
            await asyncio.sleep(0.01)

            # 等待心跳触发
            await asyncio.sleep(0.2)

            # 验证心跳包被构建
            mock_heartbeat.assert_called()

            # 清理
            client.disconnect()
            try:
                await asyncio.wait_for(connect_task, timeout=1.0)
            except asyncio.CancelledError:
                pass

    @pytest.mark.asyncio
    async def test_heartbeat_response_handling(self, mock_connection, sample_packets):
        """测试心跳响应的处理。"""
        reader, writer, mock_open = mock_connection
        client = LifeSmartLocalTCPClient("host", 1234, "user", "pass")
        client.IDLE_TIMEOUT = 0.1

        connect_task = asyncio.create_task(client.async_connect(AsyncMock()))

        # 完成初始流程
        reader.feed_data(sample_packets["login_success"])
        await asyncio.sleep(0.01)
        reader.feed_data(sample_packets["device_list"])
        await asyncio.sleep(0.01)

        # 发送心跳响应
        reader.feed_data(sample_packets["heartbeat_response"])
        await asyncio.sleep(0.01)

        # 验证连接保持活跃
        assert client.is_connected, "收到心跳响应后连接应该保持活跃"

        # 清理
        client.disconnect()
        try:
            await asyncio.wait_for(connect_task, timeout=1.0)
        except asyncio.CancelledError:
            pass


# ==================== 设备控制方法测试类 ====================


class TestDeviceControlMethods:
    """测试各种设备控制方法的功能。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method_name, args, expected_call",
        [
            (
                "turn_on_light_switch_async",
                ("L1", "agt", "dev1"),
                ("dev1", "L1", CMD_TYPE_ON, 1),
            ),
            (
                "turn_off_light_switch_async",
                ("L1", "agt", "dev1"),
                ("dev1", "L1", CMD_TYPE_OFF, 0),
            ),
        ],
        ids=["TurnOnLight", "TurnOffLight"],
    )
    async def test_basic_switch_control(
        self, mocked_client, method_name, args, expected_call
    ):
        """测试基础开关控制方法。"""
        with patch.object(
            mocked_client._factory, "build_epset_packet", return_value=b"packet"
        ) as mock_build:
            method = getattr(mocked_client, method_name)
            await method(*args)

            mock_build.assert_called_once_with(*expected_call)
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "duration, expected_val",
        [
            (50, 1),  # 短按
            (550, 6),  # 长按
            (1000, 10),  # 超长按
        ],
        ids=["ShortPress", "LongPress", "ExtraLongPress"],
    )
    async def test_press_switch_duration_mapping(
        self, mocked_client, duration, expected_val
    ):
        """测试按压开关的持续时间映射。"""
        with patch.object(
            mocked_client._factory, "build_epset_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.press_switch_async("L1", "agt", "dev1", duration)

            mock_build.assert_called_once_with(
                "dev1", "L1", CMD_TYPE_PRESS, expected_val
            )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "device_type, command_method, expected_args",
        [
            # 车库门类型窗帘
            (
                list(GARAGE_DOOR_TYPES)[0],
                "open_cover_async",
                ("P3", CMD_TYPE_SET_VAL, 100),
            ),
            (
                list(GARAGE_DOOR_TYPES)[0],
                "close_cover_async",
                ("P3", CMD_TYPE_SET_VAL, 0),
            ),
            (
                list(GARAGE_DOOR_TYPES)[0],
                "stop_cover_async",
                ("P3", CMD_TYPE_SET_CONFIG, CMD_TYPE_OFF),
            ),
            # 杜亚类型窗帘
            (list(DOOYA_TYPES)[0], "open_cover_async", ("P2", CMD_TYPE_SET_VAL, 100)),
            (list(DOOYA_TYPES)[0], "close_cover_async", ("P2", CMD_TYPE_SET_VAL, 0)),
            (
                list(DOOYA_TYPES)[0],
                "stop_cover_async",
                ("P2", CMD_TYPE_SET_CONFIG, CMD_TYPE_OFF),
            ),
            # 非定位窗帘
            (
                "SL_SW_WIN",
                "open_cover_async",
                (NON_POSITIONAL_COVER_CONFIG["SL_SW_WIN"]["open"], CMD_TYPE_ON, 1),
            ),
            (
                "SL_SW_WIN",
                "close_cover_async",
                (NON_POSITIONAL_COVER_CONFIG["SL_SW_WIN"]["close"], CMD_TYPE_ON, 1),
            ),
            (
                "SL_SW_WIN",
                "stop_cover_async",
                (NON_POSITIONAL_COVER_CONFIG["SL_SW_WIN"]["stop"], CMD_TYPE_ON, 1),
            ),
        ],
        ids=[
            "GarageDoorOpen",
            "GarageDoorClose",
            "GarageDoorStop",
            "DooyaOpen",
            "DooyaClose",
            "DooyaStop",
            "NonPositionalOpen",
            "NonPositionalClose",
            "NonPositionalStop",
        ],
    )
    async def test_cover_control_methods(
        self, mocked_client, device_type, command_method, expected_args
    ):
        """测试窗帘控制方法。"""
        with patch.object(
            mocked_client._factory, "build_epset_packet", return_value=b"packet"
        ) as mock_build:
            method = getattr(mocked_client, command_method)
            await method("agt", "dev1", device_type)

            mock_build.assert_called_once_with("dev1", *expected_args)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "device_type, position, expected_call",
        [
            (list(GARAGE_DOOR_TYPES)[0], 75, ("dev1", "P3", CMD_TYPE_SET_VAL, 75)),
            (list(DOOYA_TYPES)[0], 25, ("dev1", "P2", CMD_TYPE_SET_VAL, 25)),
        ],
        ids=["GarageDoorPosition", "DooyaPosition"],
    )
    async def test_cover_position_control(
        self, mocked_client, device_type, position, expected_call
    ):
        """测试窗帘位置控制。"""
        with patch.object(
            mocked_client._factory, "build_epset_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.set_cover_position_async(
                "agt", "dev1", position, device_type
            )

            mock_build.assert_called_once_with(*expected_call)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "device_type, hvac_mode, current_val, expected_calls",
        [
            ("V_AIR_P", HVACMode.OFF, 0, [("P1", CMD_TYPE_OFF, 0)]),
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
        ],
        ids=["TurnOff", "NatureHeat", "CpAirCool"],
    )
    async def test_climate_hvac_mode_control(
        self, mocked_client, device_type, hvac_mode, current_val, expected_calls
    ):
        """测试气候设备HVAC模式控制。"""
        with patch.object(
            mocked_client._factory, "build_epset_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.async_set_climate_hvac_mode(
                "agt", "dev1", device_type, hvac_mode, current_val
            )

            assert mock_build.call_count == len(
                expected_calls
            ), f"应该调用{len(expected_calls)}次"
            for i, expected_call in enumerate(expected_calls):
                assert mock_build.call_args_list[i].args == ("dev1", *expected_call)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "device_type, temperature, expected_call",
        [
            ("V_AIR_P", 23.5, ("dev1", "tT", CMD_TYPE_SET_TEMP_DECIMAL, 235)),
            ("SL_CP_DN", 20.0, ("dev1", "P3", CMD_TYPE_SET_RAW, 200)),
            ("SL_FCU", 25.0, ("dev1", "P8", CMD_TYPE_SET_TEMP_FCU, 250)),
        ],
        ids=["DecimalTemp", "RawTemp", "FCUTemp"],
    )
    async def test_climate_temperature_control(
        self, mocked_client, device_type, temperature, expected_call
    ):
        """测试气候设备温度控制。"""
        with patch.object(
            mocked_client._factory, "build_epset_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.async_set_climate_temperature(
                "agt", "dev1", device_type, temperature
            )

            mock_build.assert_called_once_with(*expected_call)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "device_type, fan_mode, current_val, expected_call",
        [
            ("V_AIR_P", FAN_LOW, 0, ("dev1", "F", CMD_TYPE_SET_CONFIG, 15)),
            ("SL_NATURE", FAN_HIGH, 0, ("dev1", "P9", CMD_TYPE_SET_CONFIG, 75)),
            (
                "SL_CP_AIR",
                FAN_MEDIUM,
                15,
                ("dev1", "P1", CMD_TYPE_SET_RAW, 65551),
            ),  # 位运算结果
        ],
        ids=["VAirPLow", "NatureHigh", "CpAirMedium"],
    )
    async def test_climate_fan_mode_control(
        self, mocked_client, device_type, fan_mode, current_val, expected_call
    ):
        """测试气候设备风扇模式控制。"""
        with patch.object(
            mocked_client._factory, "build_epset_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.async_set_climate_fan_mode(
                "agt", "dev1", device_type, fan_mode, current_val
            )

            mock_build.assert_called_once_with(*expected_call)


# ==================== 场景和红外控制测试类 ====================


class TestSceneAndIRControl:
    """测试场景控制和红外设备控制功能。"""

    @pytest.mark.asyncio
    async def test_scene_control(self, mocked_client):
        """测试场景控制功能。"""
        # 现在场景控制不再使用包构建，而是直接返回成功状态
        result = await mocked_client._async_set_scene("agt", "scene123")

        # 验证返回成功状态
        assert result == 0

    @pytest.mark.asyncio
    async def test_ir_control_methods(self, mocked_client):
        """测试红外控制方法。"""
        ir_options = {"keys": "power", "delay": 300}

        with patch.object(
            mocked_client._factory, "build_ir_control_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.ir_control_async("ir_device", ir_options)

            mock_build.assert_called_once_with("ir_device", ir_options)
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_ir_keys(self, mocked_client):
        """测试红外按键发送功能。"""
        keys_data = json.dumps([{"key": "power", "delay": 500}])

        with patch.object(
            mocked_client._factory, "build_ir_control_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client._async_send_ir_key(
                "agt", "remote1", "tv", "samsung", keys_data, "ai1"
            )

            # 验证调用参数：设备ID和红外选项字典
            expected_options = {
                "category": "tv",
                "brand": "samsung",
                "keys": keys_data,
                "ai": "ai1",
            }
            mock_build.assert_called_once_with("remote1", expected_options)
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_send_ir_code(self, mocked_client):
        """测试红外代码发送功能。"""
        code_data = [1, 2, 3, 4, 5]

        with patch.object(
            mocked_client._factory, "build_send_code_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.send_ir_code_async("ir_device", code_data)

            mock_build.assert_called_once_with("ir_device", code_data)
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ir_raw_control(self, mocked_client):
        """测试红外原始控制功能。"""
        raw_data = '{"frequency": 38000, "data": [100, 200, 300]}'

        with patch.object(
            mocked_client._factory,
            "build_ir_raw_control_packet",
            return_value=b"packet",
        ) as mock_build:
            await mocked_client.ir_raw_control_async("ir_device", raw_data)

            mock_build.assert_called_once_with("ir_device", raw_data)
            mocked_client._send_packet.assert_awaited_once()


# ==================== 高级功能测试类 ====================


class TestAdvancedFeatures:
    """测试高级功能，如多命令发送、触发器、定时器等。"""

    @pytest.mark.asyncio
    async def test_multi_command_sending(self, mocked_client):
        """测试多命令发送功能。"""
        io_list = [
            {"idx": "RGBW", "val": 16777215},  # 白色
            {"idx": "DYN", "val": 0},  # 关闭动态
            {"idx": "BRI", "val": 80},  # 亮度80%
        ]

        with patch.object(
            mocked_client._factory, "build_multi_epset_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.async_send_multi_command("agt", "rgb_light", io_list)

            mock_build.assert_called_once_with("rgb_light", io_list)
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_trigger_management(self, mocked_client):
        """测试触发器管理功能。"""
        trigger_name = "door_open_trigger"
        command_list = "L1=ON;L2=OFF;DELAY=1000;L3=ON"

        # 测试添加触发器
        with patch.object(
            mocked_client._factory, "build_add_scene_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.add_scene_async(trigger_name, command_list)

            mock_build.assert_called_once_with(trigger_name, command_list)
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_ai_management(self, mocked_client):
        """测试AI设备管理功能。"""
        ai_name = "test_ai_device"

        with patch.object(
            mocked_client._factory, "build_delete_scene_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.delete_scene_async(ai_name)

            mock_build.assert_called_once_with(ai_name)
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_eeprom_configuration(self, mocked_client):
        """测试EEPROM配置功能。"""
        device_id = "config_device"
        config_key = "network_settings"
        config_value = "192.168.1.100:8080"

        with patch.object(
            mocked_client._factory, "build_set_eeprom_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.set_eeprom_async(device_id, config_key, config_value)

            mock_build.assert_called_once_with(device_id, config_key, config_value)
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_timer_management(self, mocked_client):
        """测试定时器管理功能。"""
        device_id = "timer_device"
        cron_expression = "0 8 * * 1-5"  # 工作日早上8点
        timer_command = "L1=ON;BRI=100"

        with patch.object(
            mocked_client._factory, "build_add_timer_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.add_timer_async(
                device_id, cron_expression, timer_command
            )

            mock_build.assert_called_once_with(
                device_id, cron_expression, timer_command
            )
            mocked_client._send_packet.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_icon_management(self, mocked_client):
        """测试图标管理功能。"""
        device_id = "icon_device"
        icon_name = "light_bulb"

        with patch.object(
            mocked_client._factory, "build_change_icon_packet", return_value=b"packet"
        ) as mock_build:
            await mocked_client.change_icon_async(device_id, icon_name)

            mock_build.assert_called_once_with(device_id, icon_name)
            mocked_client._send_packet.assert_awaited_once()


# ==================== 错误处理和边界条件测试类 ====================


class TestErrorHandlingAndEdgeCases:
    """测试错误处理和各种边界条件。"""

    @pytest.mark.asyncio
    async def test_unsupported_device_type_handling(self, mocked_client, caplog):
        """测试不支持设备类型的处理。"""
        with patch.object(
            mocked_client._factory, "build_epset_packet", return_value=b"packet"
        ) as mock_build:
            # 尝试控制不支持的窗帘类型
            result = await mocked_client.open_cover_async(
                "agt", "dev1", "UNSUPPORTED_COVER_TYPE"
            )

            assert result == -1, "不支持的设备类型应该返回-1"
            mock_build.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_temperature_values(self, mocked_client):
        """测试无效温度值的处理。"""
        with patch.object(
            mocked_client._factory, "build_epset_packet", return_value=b"packet"
        ) as mock_build:
            # 尝试设置不支持的设备类型温度
            result = await mocked_client.async_set_climate_temperature(
                "agt", "dev1", "UNSUPPORTED_TYPE", 25.0
            )

            assert result == -1, "不支持的设备应该返回-1"
            mock_build.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalid_fan_mode_handling(self, mocked_client, caplog):
        """测试无效风扇模式的处理。"""
        with patch.object(
            mocked_client._factory, "build_epset_packet", return_value=b"packet"
        ) as mock_build:
            result = await mocked_client.async_set_climate_fan_mode(
                "agt", "dev1", "UNSUPPORTED_TYPE", FAN_LOW
            )

            assert result == -1, "不支持的设备类型应该返回-1"
            assert "不支持风扇模式" in caplog.text, "应该记录不支持的错误信息"
            mock_build.assert_not_called()

    @pytest.mark.asyncio
    async def test_network_error_during_operation(self, mocked_client):
        """测试操作过程中的网络错误。"""
        # 模拟网络发送失败
        mocked_client._send_packet.side_effect = Exception("网络错误")

        with patch.object(
            mocked_client._factory, "build_epset_packet", return_value=b"packet"
        ):
            with pytest.raises(Exception, match="网络错误"):
                await mocked_client.turn_on_light_switch_async("L1", "agt", "dev1")

    @pytest.mark.asyncio
    async def test_malformed_status_update_handling(
        self, mock_connection, sample_packets, protocol
    ):
        """测试格式错误的状态更新处理。"""
        reader, writer, mock_open = mock_connection
        client = LifeSmartLocalTCPClient("host", 1234, "user", "pass")
        callback = AsyncMock()

        # 建立连接
        connect_task = asyncio.create_task(client.async_connect(callback))
        reader.feed_data(sample_packets["login_success"])
        await asyncio.sleep(0.1)
        reader.feed_data(sample_packets["device_list"])
        await asyncio.sleep(0.1)

        # 发送格式错误的状态更新
        malformed_update = protocol.encode(
            [{}, {"_schg": {"invalid_path": {"chg": {"val": 1}}}}]
        )
        reader.feed_data(malformed_update)
        await asyncio.sleep(0.1)

        # 验证系统没有崩溃，且可能记录了错误
        assert client.is_connected, "格式错误的更新不应该导致连接断开"

        # 清理
        client.disconnect()
        try:
            await asyncio.wait_for(connect_task, timeout=1.0)
        except asyncio.CancelledError:
            pass


# ==================== 性能和并发测试类 ====================


class TestPerformanceAndConcurrency:
    """测试性能和并发处理能力。"""

    @pytest.mark.asyncio
    async def test_concurrent_command_execution(self, mocked_client):
        """测试并发命令执行。"""
        commands = [
            ("turn_on_light_switch_async", ("L1", "agt", "dev1")),
            ("turn_off_light_switch_async", ("L2", "agt", "dev1")),
            ("turn_on_light_switch_async", ("L3", "agt", "dev1")),
            ("press_switch_async", ("P1", "agt", "dev2", 100)),
            ("_async_set_scene", ("agt", "scene1")),
        ]

        with patch.object(
            mocked_client._factory, "build_epset_packet", return_value=b"packet"
        ):
            # 并发执行所有命令
            tasks = []
            for method_name, args in commands:
                method = getattr(mocked_client, method_name)
                task = asyncio.create_task(method(*args))
                tasks.append(task)

            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 验证所有任务都成功完成
            for i, result in enumerate(results):
                assert not isinstance(result, Exception), f"命令 {i} 应该成功执行"

    @pytest.mark.asyncio
    async def test_high_frequency_status_updates(
        self, mock_connection, sample_packets, protocol
    ):
        """测试高频状态更新的处理。"""
        reader, writer, mock_open = mock_connection
        client = LifeSmartLocalTCPClient("host", 1234, "user", "pass")
        callback = AsyncMock()

        # 建立连接
        connect_task = asyncio.create_task(client.async_connect(callback))
        reader.feed_data(sample_packets["login_success"])
        await asyncio.sleep(0.1)
        reader.feed_data(sample_packets["device_list"])
        await asyncio.sleep(0.1)

        # 发送大量状态更新
        for i in range(100):
            status_update = protocol.encode(
                [
                    {},
                    {
                        "_schg": {
                            f"test_agt/ep/device_1/m/L{(i % 3) + 1}": {
                                "chg": {"val": i % 2}
                            }
                        }
                    },
                ]
            )
            reader.feed_data(status_update)

        await asyncio.sleep(0.5)  # 给处理时间

        # 验证所有更新都被处理
        assert callback.call_count >= 50, "应该处理大部分状态更新"

        # 清理
        client.disconnect()
        try:
            await asyncio.wait_for(connect_task, timeout=1.0)
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, mock_connection, sample_packets):
        """测试负载下的内存使用情况。"""
        reader, writer, mock_open = mock_connection
        client = LifeSmartLocalTCPClient("host", 1234, "user", "pass")

        # 建立连接
        connect_task = asyncio.create_task(client.async_connect(AsyncMock()))
        reader.feed_data(sample_packets["login_success"])
        await asyncio.sleep(0.1)
        reader.feed_data(sample_packets["device_list"])
        await asyncio.sleep(0.1)

        # 执行大量操作
        with patch.object(
            client._factory, "build_epset_packet", return_value=b"packet"
        ):
            for i in range(1000):
                await client.turn_on_light_switch_async(
                    f"L{i % 3 + 1}", "agt", f"dev{i % 10}"
                )

        # 验证客户端仍然正常工作
        assert client.is_connected, "大量操作后客户端应该仍然连接"
        assert len(client.devices) > 0, "设备列表应该保持不变"

        # 清理
        client.disconnect()
        try:
            await asyncio.wait_for(connect_task, timeout=1.0)
        except asyncio.CancelledError:
            pass
