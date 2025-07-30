"""LifeSmart 本地 TCP 客户端实现。

此模块包含 LifeSmartLocalTCPClient 类，负责通过 TCP Socket 与 LifeSmart 中枢
进行通信。它使用 protocol.py 中的工具来构建和解析数据包，并实现了与云端客户端
对齐的异步控制接口。
"""

import asyncio
import logging
import re
from typing import Callable, Any

from .client_base import LifeSmartClientBase
from .protocol import LifeSmartPacketFactory, LifeSmartProtocol

_LOGGER = logging.getLogger(__name__)


class LifeSmartLocalTCPClient(LifeSmartClientBase):
    """LifeSmart 本地客户端，负责与中枢进行 TCP 通信。"""

    IDLE_TIMEOUT = 65.0

    def __init__(self, host, port, username, password, config_agt=None) -> None:
        self.host, self.port, self.username, self.password, self.config_agt = (
            host,
            port,
            username,
            password,
            config_agt,
        )
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self._proto = LifeSmartProtocol()
        self._factory: LifeSmartPacketFactory = LifeSmartPacketFactory("", "")
        self.disconnected = False
        self.device_ready = asyncio.Event()
        self.devices, self.node, self.node_agt = {}, "", ""
        self._connect_task = None

    @property
    def is_connected(self) -> bool:
        """
        如果读写器都存在且写入器未关闭，则返回 True。
        """
        return (
            self.writer is not None
            and self.reader is not None
            and not self.writer.is_closing()
        )

    def disconnect(self):
        """断开与本地客户端的连接。"""
        _LOGGER.info("请求断开本地客户端连接。")
        self.disconnected = True
        # 只取消任务，让任务自己的 finally 块来处理关闭
        if self._connect_task and not self._connect_task.done():
            self._connect_task.cancel()

    async def check_login(self):
        """检查登录凭据是否有效。"""
        self.reader, self.writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port), timeout=5
        )
        try:
            pkt = LifeSmartPacketFactory("", "").build_login_packet(
                self.username, self.password
            )
            _LOGGER.debug(
                "Sending login packet to %s:%s with username '%s'.",
                self.host,
                self.port,
                self.username,
            )
            self.writer.write(pkt)
            await self.writer.drain()
            response = b""
            while not self.disconnected:
                # 在读取操作上增加超时，防止无限期等待
                buf = await asyncio.wait_for(self.reader.read(4096), timeout=10)
                if not buf:
                    # 如果读取到空字节，说明对端关闭了连接
                    raise asyncio.TimeoutError(
                        "Connection closed by peer during login."
                    )
                response += buf
                if response:
                    try:
                        _, decoded = self._proto.decode(response)
                        if decoded and decoded[1].get("ret") is None:
                            _LOGGER.error("本地登录失败 -> %s", decoded[1].get("err"))
                            raise asyncio.InvalidStateError(
                                "Login failed with error response."
                            )
                        break  # 成功解码并验证，跳出循环
                    except EOFError:
                        # 数据包尚不完整，继续读取
                        pass
            return True
        finally:
            if self.writer:
                self.writer.close()
                try:
                    await self.writer.wait_closed()
                except (ConnectionResetError, BrokenPipeError):
                    # 这是一个预期的异常，如果连接已经被重置，可以忽略
                    pass

    async def get_all_device_async(self, timeout=10):
        """获取所有设备数据，带超时控制"""
        try:
            await asyncio.wait_for(self.device_ready.wait(), timeout=timeout)
            return list(self.devices.values()) if self.devices else []
        except asyncio.TimeoutError:
            _LOGGER.error("等待本地设备就绪超时 (timeout=%ds)", timeout)
            return False

    async def async_connect(self, callback: None | Callable):
        """主连接循环，负责登录、获取设备和监听状态更新。"""

        def _safe_get(data, *path, default=None):
            """安全地按路径取值，支持 dict/list 混合。"""
            cur = data
            for key in path:
                if isinstance(cur, dict):
                    cur = cur.get(key, default)
                elif isinstance(cur, list) and isinstance(key, int):
                    try:
                        cur = cur[key]
                    except IndexError:
                        return default
                else:
                    return default
            return cur

        self._connect_task = asyncio.current_task()
        while not self.disconnected:
            self.reader, self.writer = None, None
            try:
                _LOGGER.info("正在尝试建立本地连接到 %s:%s...", self.host, self.port)
                self.reader, self.writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, self.port), timeout=5
                )
                _LOGGER.info("本地连接已建立。")
                pkt = LifeSmartPacketFactory("", "").build_login_packet(
                    self.username, self.password
                )
                self.writer.write(pkt)
                await self.writer.drain()
                response, stage = b"", "login"
                while not self.disconnected:
                    # 为读取操作增加超时，防止无限期阻塞
                    try:
                        buf = await asyncio.wait_for(
                            self.reader.read(4096), timeout=self.IDLE_TIMEOUT
                        )
                    except asyncio.TimeoutError:
                        if stage == "loaded":
                            _LOGGER.debug("连接空闲超时，发送心跳包以维持连接...")
                            try:
                                # 发送一个无害的 getconfig 包作为心跳检测，看是不是真的断了
                                pkt = self._factory.build_get_config_packet(self.node)
                                self.writer.write(pkt)
                                await self.writer.drain()
                                continue  # 发送心跳后，继续下一次 read 等待
                            except Exception as e:
                                _LOGGER.warning("发送心跳包失败，连接可能已断开: %s", e)
                                break  # 心跳失败，则重连
                        else:
                            # 如果在 login 或 loading 阶段超时，说明确实有问题
                            _LOGGER.error(
                                "在 '%s' 阶段等待响应超时，将进行重连。", stage
                            )
                            break

                    if not buf:
                        _LOGGER.warning(
                            "Socket 连接被对方关闭 (在 '%s' 阶段)，将进行重连。", stage
                        )
                        break
                    # _LOGGER.debug(
                    #     "收到本地 %d 字节原始数据 <- : %s", len(buf), buf.hex(" ")
                    # )
                    response += buf
                    # _LOGGER.debug(
                    #     "当前响应缓冲区 (总长度 %d): %s",
                    #     len(response),
                    #     response.hex(" "),
                    # )
                    while response:
                        try:
                            _LOGGER.debug("尝试解码缓冲区数据...")
                            remaining_response, decoded = self._proto.decode(response)
                            if decoded is None:
                                _LOGGER.error(
                                    "解码器返回了 None，但未抛出异常。可能存在未知错误。清空缓冲区。"
                                )
                                response = b""
                                break

                            # _LOGGER.debug(
                            #     "🔑解码成功，解析出的结构: \n%s", pformat(decoded)
                            # )
                            response = remaining_response
                            _LOGGER.debug(
                                "解码后剩余数据 (长度 %d): %s",
                                len(response),
                                response.hex(" ") if response else "无",
                            )

                            if stage == "login":

                                if _safe_get(decoded, 1, "ret") is None:
                                    _LOGGER.error(
                                        "本地登录失败 -> %s",
                                        _safe_get(decoded, 1, "err", "未知登录错误"),
                                    )
                                    self.disconnected = True
                                    continue
                                node_info = _safe_get(decoded, 1, "ret", 4)
                                if not node_info:
                                    _LOGGER.error("登录响应缺少 node 信息")
                                    break
                                self.node = _safe_get(node_info, "base", 1, default="")
                                self.node_agt = _safe_get(
                                    node_info, "agt", 1, default=""
                                )
                                _LOGGER.info(
                                    "本地登录成功，Node: %s, Agt: %s",
                                    self.node,
                                    self.node_agt,
                                )
                                self._factory.node = self.node
                                self._factory.node_agt = self.node_agt
                                stage = "loading"
                                pkt = self._factory.build_get_config_packet(self.node)
                                self.writer.write(pkt)
                                await self.writer.drain()
                            elif stage == "loading":
                                eps = _safe_get(decoded, 1, "ret", 1, "eps", default={})
                                self.devices = {}
                                for devid, dev in eps.items():
                                    dev = self._normalize_device_names(dev)
                                    dev_meta = {
                                        "me": devid,
                                        "devtype": (
                                            dev["cls"][:-3]
                                            if dev["cls"][-3:-1] == "_V"
                                            else dev["cls"]
                                        ),
                                        "agt": self.node_agt,
                                        "name": dev["name"],
                                        "data": _safe_get(
                                            dev, "_chd", "m", "_chd", default={}
                                        ),
                                    }
                                    dev_meta.update(dev)
                                    if "_chd" in dev_meta:
                                        del dev_meta["_chd"]
                                    self.devices[devid] = dev_meta
                                _LOGGER.info(
                                    "成功加载 %d 个本地设备。", len(self.devices)
                                )
                                self.device_ready.set()  # 通知 get_all_device_async 可以返回了
                                stage = "loaded"
                            else:  # 实时状态推送
                                if schg := _safe_get(decoded, 1, "_schg"):
                                    _LOGGER.debug(
                                        "收到本地状态更新 (_schg) <- : %s", schg
                                    )
                                    for schg_key, schg_data in schg.items():
                                        if not isinstance(schg_key, str):
                                            continue
                                        parts = schg_key.split("/")

                                        # 6段路径: agt/me/ep/devid/m/idx
                                        # 5段路径 (兼容旧格式): agt/ep/devid/m/idx

                                        dev_id, sub_key = None, None

                                        if (
                                            len(parts) == 6
                                            and parts[1] == "me"
                                            and parts[2] == "ep"
                                            and parts[4] == "m"
                                        ):
                                            dev_id, sub_key = parts[3], parts[5]
                                        elif (
                                            len(parts) == 5
                                            and parts[1] == "ep"
                                            and parts[3] == "m"
                                        ):
                                            dev_id, sub_key = parts[2], parts[4]

                                        if (
                                            dev_id
                                            and sub_key
                                            and dev_id in self.devices
                                        ):
                                            device_data = self.devices[
                                                dev_id
                                            ].setdefault("data", {})
                                            sub_device_data = device_data.setdefault(
                                                sub_key, {}
                                            )
                                            sub_device_data.update(
                                                schg_data.get("chg", {})
                                            )

                                            if callback and callable(callback):
                                                msg = {
                                                    "me": dev_id,
                                                    "idx": sub_key,
                                                    "agt": self.node_agt,
                                                    "devtype": self.devices[dev_id][
                                                        "devtype"
                                                    ],
                                                    **sub_device_data,
                                                }
                                                # 构造一个与云端推送格式完全一致的字典
                                                # 以便 data_update_handler 可以统一处理
                                                await callback(
                                                    {"type": "io", "msg": msg}
                                                )
                                elif _safe_get(decoded, 1, "_sdel"):
                                    _LOGGER.warning(
                                        "检测到设备被删除，将触发重新加载: %s",
                                        _safe_get(decoded, 1, "_sdel"),
                                    )
                                    if callback and callable(callback):
                                        await callback({"reload": True})
                        except EOFError:
                            _LOGGER.debug(
                                "捕获到 EOFError，数据包不完整，等待更多数据..."
                            )
                            break  # 跳出内层 while response 循环，去外层循环读取更多数据
                        except Exception as e:
                            _LOGGER.error(
                                "处理数据时发生意外错误: %s", e, exc_info=True
                            )
                            response = b""  # 清空缓冲区以避免死循环
                            break  # 出现意外错误，中断内部循环以重连

            except (
                ConnectionResetError,
                asyncio.TimeoutError,
                ConnectionRefusedError,
                OSError,
            ) as e:
                _LOGGER.warning(
                    "本地连接失败: %s: %s，将稍后重试。", e.__class__.__name__, str(e)
                )
            except asyncio.CancelledError:
                _LOGGER.info("本地连接任务已被取消。")
                self.disconnected = True
                break
            except Exception as e:
                _LOGGER.error("本地连接主循环发生未知异常: %s", e, exc_info=True)
            finally:
                if self.writer:
                    try:
                        self.writer.close()
                        await self.writer.wait_closed()
                    except (ConnectionResetError, BrokenPipeError):
                        pass
                    except Exception as e:
                        _LOGGER.warning("关闭 writer 时发生未知错误: %s", e)
                    self.writer = None
                if not self.disconnected:
                    await asyncio.sleep(5.0)
                else:
                    # 如果已请求断开，则跳出主循环
                    break

    async def _send_packet(self, packet: bytes):
        if self.writer and not self.writer.is_closing():
            self.writer.write(packet)
            await self.writer.drain()
            return 0
        _LOGGER.error("本地客户端未连接，无法发送指令。")
        return -1

    # ====================================================================
    # 基类抽象方法的实现
    # ====================================================================
    async def _async_get_all_devices(self, timeout=10) -> list[dict[str, Any]]:
        """
        [本地实现] 等待本地连接成功并加载完所有设备。

        此方法不直接发送请求，而是等待后台的 `async_connect` 任务
        在成功加载设备（该过程会发送 get_config 包）后设置一个 `device_ready` 事件。
        """
        try:
            _LOGGER.debug("等待本地设备列表就绪 (超时: %ds)...", timeout)
            await asyncio.wait_for(self.device_ready.wait(), timeout=timeout)
            return list(self.devices.values()) if self.devices else []
        except asyncio.TimeoutError:
            _LOGGER.error("等待本地设备就绪超时。")
            return []

    async def _async_send_single_command(
        self, agt: str, me: str, idx: str, command_type: str, val: Any
    ) -> int:
        """
        [本地实现] 发送单个IO口命令。
        此方法通过调用包工厂构建二进制包，并发送到TCP Socket。
        """
        pkt = self._factory.build_epset_packet(me, idx, command_type, val)
        return await self._send_packet(pkt)

    async def _async_send_multi_command(
        self, agt: str, me: str, io_list: list[dict]
    ) -> int:
        """
        [本地实现] 同时发送多个IO口的命令。
        此方法通过调用包工厂构建二进制包，并发送到TCP Socket。
        """
        pkt = self._factory.build_multi_epset_packet(me, io_list)
        return await self._send_packet(pkt)

    async def _async_set_scene(self, agt: str, scene_id: str) -> int:
        """
        [本地实现] 激活一个本地场景。
        此方法通过调用包工厂构建二进制包，并发送到TCP Socket。
        """
        if not self._factory:
            _LOGGER.error("本地客户端工厂未初始化，无法发送场景指令。")
            return -1
        pkt = self._factory.build_scene_trigger_packet(scene_id)
        return await self._send_packet(pkt)

    async def _async_send_ir_key(
        self, agt: str, ai: str, me: str, category: str, brand: str, keys: str
    ) -> int:
        """
        [本地实现] 发送一个本地红外按键命令。
        此方法通过调用包工厂构建二进制包，并发送到TCP Socket。
        """
        if not self._factory:
            _LOGGER.error("本地客户端工厂未初始化，无法发送红外指令。")
            return -1
        pkt = self._factory.build_send_ir_keys_packet(ai, me, category, brand, keys)
        return await self._send_packet(pkt)

    # ====================================================================
    # 设备直接控制的辅助方法
    #
    # 以下所有高层设备控制方法 (`turn_on_light_switch_async`, `open_cover_async`,
    # `async_set_climate_hvac_mode` 等) 现已移至 `client_base.py` 中，
    # 并由该类继承。
    # ====================================================================

    async def change_icon_async(self, devid: str, icon: str) -> int:
        """修改设备图标。"""
        pkt = self._factory.build_change_icon_packet(devid, icon)
        return await self._send_packet(pkt)

    async def add_trigger_async(self, trigger_name: str, cmdlist: str) -> int:
        """添加一个触发器。"""
        pkt = self._factory.build_add_trigger_packet(trigger_name, cmdlist)
        return await self._send_packet(pkt)

    async def del_ai_async(self, ai_name: str) -> int:
        """删除一个AI（场景或触发器）。"""
        pkt = self._factory.build_del_ai_packet(ai_name)
        return await self._send_packet(pkt)

    async def ir_control_async(self, devid: str, opt: dict) -> int:
        """通过运行AI场景来控制红外设备。"""
        pkt = self._factory.build_ir_control_packet(devid, opt)
        return await self._send_packet(pkt)

    async def send_ir_code_async(self, devid: str, data: list | bytes) -> int:
        """发送原始红外码。"""
        pkt = self._factory.build_send_code_packet(devid, data)
        return await self._send_packet(pkt)

    async def ir_raw_control_async(self, devid: str, datas: str) -> int:
        """发送原始红外控制数据。"""
        pkt = self._factory.build_ir_raw_control_packet(devid, datas)
        return await self._send_packet(pkt)

    async def set_eeprom_async(self, devid: str, key: str, val: Any) -> int:
        """设置设备的EEPROM。"""
        pkt = self._factory.build_set_eeprom_packet(devid, key, val)
        return await self._send_packet(pkt)

    async def add_timer_async(self, devid: str, croninfo: str, key: str) -> int:
        """为设备添加一个定时器。"""
        pkt = self._factory.build_add_timer_packet(devid, croninfo, key)
        return await self._send_packet(pkt)

    # ====================================================================
    # 设备名称规范化
    # ====================================================================
    @staticmethod
    def _normalize_device_names(dev_dict: dict) -> dict:
        """
        递归地规范化设备及其子设备的名称，替换所有已知占位符。
        - '{$EPN}' -> 替换为父设备名称。
        - '{SUB_KEY}' -> 替换为 'SUB_KEY'。
        """
        base_name = dev_dict.get("name", "")
        if (
            "_chd" in dev_dict
            and "m" in dev_dict["_chd"]
            and "_chd" in dev_dict["_chd"]["m"]
        ):
            sub_devices = dev_dict["_chd"]["m"]["_chd"]
            for sub_key, sub_data in sub_devices.items():
                if (
                    isinstance(sub_data, dict)
                    and (sub_name := sub_data.get("name"))
                    and isinstance(sub_name, str)
                ):
                    processed_name = sub_name.replace("{$EPN}", base_name).strip()
                    processed_name = re.sub(r"\{([A-Z0-9_]+)\}", r"\1", processed_name)
                    sub_data["name"] = " ".join(processed_name.split())
        return dev_dict
