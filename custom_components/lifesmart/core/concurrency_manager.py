"""LifeSmart 集成的并发控制管理器。

此模块提供统一的并发控制机制，包括：
- 锁和信号量管理
- 死锁预防
- 性能监控
- 资源清理

由 @MapleEve 创建，用于解决竞态条件风险。
"""

import asyncio
import logging
import time
from collections import defaultdict
from typing import Any, Callable, Dict, Optional, Set

from .const import CONCURRENCY_QUEUE_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class ConcurrencyManager:
    """并发控制管理器，负责协调所有异步操作的并发控制。

    设计原则：
    1. 统一管理所有锁和信号量
    2. 提供上下文管理器确保资源释放
    3. 死锁检测和预防
    4. 性能监控和统计
    """

    def __init__(self):
        """初始化并发控制管理器。"""
        # 核心锁机制
        self._token_refresh_lock = asyncio.Lock()
        self._device_update_semaphore = asyncio.Semaphore(10)
        self._connection_lock = asyncio.Lock()
        self._message_processing_lock = asyncio.Lock()
        self._config_update_lock = asyncio.Lock()
        self._device_sync_lock = asyncio.Lock()
        self._recovery_lock = asyncio.Lock()

        # 消息处理队列和限流
        self._message_queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._message_processing_semaphore = asyncio.Semaphore(5)

        # 设备级别锁管理 - 实用版本
        self._device_locks: Dict[str, asyncio.Lock] = {}

        # 性能统计
        self._lock_stats = defaultdict(lambda: {"acquired": 0, "wait_time": 0.0})
        self._active_operations: Set[str] = set()

        # 死锁检测
        self._lock_order = {
            "token_refresh": 1,
            "config_update": 2,
            "connection": 3,
            "message_processing": 4,
            "device_sync": 5,
            "recovery": 6,
        }
        self._held_locks: Dict[asyncio.Task, str] = {}

    async def safe_token_refresh(self, refresh_func: Callable, *args, **kwargs) -> Any:
        """线程安全的令牌刷新操作。

        Args:
            refresh_func: 刷新函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            刷新函数的返回值

        Raises:
            Exception: 刷新过程中的异常
        """
        operation_id = f"token_refresh_{id(refresh_func)}"
        start_time = time.time()

        try:
            self._active_operations.add(operation_id)
            async with self._token_refresh_lock:
                current_task = asyncio.current_task()
                if current_task:
                    self._held_locks[current_task] = "token_refresh"
                _LOGGER.debug("获取令牌刷新锁: %s", operation_id)

                # 执行令牌刷新
                result = await refresh_func(*args, **kwargs)

                # 更新性能统计
                self._lock_stats["token_refresh"]["acquired"] += 1
                self._lock_stats["token_refresh"]["wait_time"] += (
                    time.time() - start_time
                )

                return result
        except Exception as e:
            _LOGGER.error("令牌刷新操作异常: %s", e)
            raise
        finally:
            current_task = asyncio.current_task()
            if current_task:
                self._held_locks.pop(current_task, None)
            self._active_operations.discard(operation_id)

    async def safe_config_update(self, update_func: Callable, *args, **kwargs) -> Any:
        """线程安全的配置更新操作。

        Args:
            update_func: 更新函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            更新函数的返回值

        Raises:
            Exception: 更新过程中的异常
        """
        operation_id = f"config_update_{id(update_func)}"

        try:
            self._active_operations.add(operation_id)
            async with self._config_update_lock:
                current_task = asyncio.current_task()
                if current_task:
                    self._held_locks[current_task] = "config_update"
                _LOGGER.debug("获取配置更新锁: %s", operation_id)

                return await update_func(*args, **kwargs)
        except Exception as e:
            _LOGGER.error("配置更新操作异常: %s", e)
            raise
        finally:
            current_task = asyncio.current_task()
            if current_task:
                self._held_locks.pop(current_task, None)
            self._active_operations.discard(operation_id)

    async def safe_device_update(self, update_func: Callable, *args, **kwargs) -> Any:
        """限流的设备更新操作。

        Args:
            update_func: 更新函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            更新函数的返回值

        Raises:
            Exception: 更新过程中的异常
        """
        operation_id = f"device_update_{id(update_func)}"

        try:
            self._active_operations.add(operation_id)
            async with self._device_update_semaphore:
                _LOGGER.debug("获取设备更新信号量: %s", operation_id)
                return await update_func(*args, **kwargs)
        except Exception as e:
            _LOGGER.error("设备更新操作异常: %s", e)
            raise
        finally:
            self._active_operations.discard(operation_id)

    async def safe_message_processing(
        self, process_func: Callable, *args, **kwargs
    ) -> Any:
        """安全的消息处理操作，防止消息处理竞态。

        Args:
            process_func: 处理函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            处理函数的返回值

        Raises:
            Exception: 处理过程中的异常
        """
        operation_id = f"message_proc_{id(process_func)}"

        try:
            self._active_operations.add(operation_id)
            async with self._message_processing_semaphore:
                _LOGGER.debug("获取消息处理信号量: %s", operation_id)
                return await process_func(*args, **kwargs)
        except Exception as e:
            _LOGGER.error("消息处理操作异常: %s", e)
            raise
        finally:
            self._active_operations.discard(operation_id)

    async def safe_device_sync(self, sync_func: Callable, *args, **kwargs) -> Any:
        """线程安全的设备同步操作。

        Args:
            sync_func: 同步函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            同步函数的返回值

        Raises:
            Exception: 同步过程中的异常
        """
        operation_id = f"device_sync_{id(sync_func)}"

        try:
            self._active_operations.add(operation_id)
            async with self._device_sync_lock:
                current_task = asyncio.current_task()
                if current_task:
                    self._held_locks[current_task] = "device_sync"
                _LOGGER.debug("获取设备同步锁: %s", operation_id)

                return await sync_func(*args, **kwargs)
        except Exception as e:
            _LOGGER.error("设备同步操作异常: %s", e)
            raise
        finally:
            current_task = asyncio.current_task()
            if current_task:
                self._held_locks.pop(current_task, None)
            self._active_operations.discard(operation_id)

    async def safe_recovery_operation(
        self, recovery_func: Callable, *args, **kwargs
    ) -> Any:
        """线程安全的故障恢复操作。

        Args:
            recovery_func: 恢复函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            恢复函数的返回值

        Raises:
            Exception: 恢复过程中的异常
        """
        operation_id = f"recovery_{id(recovery_func)}"

        try:
            self._active_operations.add(operation_id)
            async with self._recovery_lock:
                current_task = asyncio.current_task()
                if current_task:
                    self._held_locks[current_task] = "recovery"
                _LOGGER.debug("获取故障恢复锁: %s", operation_id)

                return await recovery_func(*args, **kwargs)
        except Exception as e:
            _LOGGER.error("故障恢复操作异常: %s", e)
            raise
        finally:
            current_task = asyncio.current_task()
            if current_task:
                self._held_locks.pop(current_task, None)
            self._active_operations.discard(operation_id)

    async def safe_connection_operation(
        self, conn_func: Callable, *args, **kwargs
    ) -> Any:
        """线程安全的连接操作。

        Args:
            conn_func: 连接函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            连接函数的返回值

        Raises:
            Exception: 连接过程中的异常
        """
        operation_id = f"connection_{id(conn_func)}"

        try:
            self._active_operations.add(operation_id)
            async with self._connection_lock:
                current_task = asyncio.current_task()
                if current_task:
                    self._held_locks[current_task] = "connection"
                _LOGGER.debug("获取连接锁: %s", operation_id)

                return await conn_func(*args, **kwargs)
        except Exception as e:
            _LOGGER.error("连接操作异常: %s", e)
            raise
        finally:
            current_task = asyncio.current_task()
            if current_task:
                self._held_locks.pop(current_task, None)
            self._active_operations.discard(operation_id)

    def get_concurrency_stats(self) -> Dict[str, Any]:
        """获取并发控制统计信息。

        Returns:
            包含统计信息的字典
        """
        return {
            "active_operations": len(self._active_operations),
            "operations": list(self._active_operations),
            "lock_stats": dict(self._lock_stats),
            "held_locks": {str(task): lock for task, lock in self._held_locks.items()},
            "queue_size": (
                self._message_queue.qsize()
                if hasattr(self._message_queue, "qsize")
                else 0
            ),
        }

    async def add_message_to_queue(self, message: str) -> None:
        """将消息添加到处理队列。

        Args:
            message: 待处理的消息

        Raises:
            asyncio.QueueFull: 队列已满
        """
        try:
            await self._message_queue.put(message)
        except asyncio.QueueFull:
            _LOGGER.warning("消息队列已满，丢弃消息: %s", message[:100])

    async def get_message_from_queue(self) -> Optional[str]:
        """从队列获取消息。

        Returns:
            队列中的消息，如果队列为空则返回 None
        """
        try:
            return await asyncio.wait_for(
                self._message_queue.get(), timeout=CONCURRENCY_QUEUE_TIMEOUT
            )
        except asyncio.TimeoutError:
            return None

    async def shutdown(self) -> None:
        """关闭并发控制管理器，清理资源。"""
        _LOGGER.info("关闭并发控制管理器...")

        # 等待活跃操作完成
        max_wait = 30  # 最大等待30秒
        wait_count = 0
        while self._active_operations and wait_count < max_wait:
            _LOGGER.info("等待 %d 个活跃操作完成...", len(self._active_operations))
            await asyncio.sleep(1)
            wait_count += 1

        if self._active_operations:
            _LOGGER.warning(
                "仍有 %d 个活跃操作未完成: %s",
                len(self._active_operations),
                list(self._active_operations),
            )

        # 清空消息队列
        if hasattr(self._message_queue, "qsize"):
            while not self._message_queue.empty():
                try:
                    self._message_queue.get_nowait()
                except asyncio.QueueEmpty:
                    break

        # 清理持有的锁引用
        self._held_locks.clear()

        _LOGGER.info("并发控制管理器已关闭")

    def log_performance_stats(self) -> None:
        """记录性能统计信息。"""
        if self._lock_stats:
            _LOGGER.info("并发控制性能统计:")
            for lock_name, stats in self._lock_stats.items():
                avg_wait = stats["wait_time"] / max(stats["acquired"], 1)
                _LOGGER.info(
                    "  %s: 获取 %d 次, 平均等待 %.3f 秒",
                    lock_name,
                    stats["acquired"],
                    avg_wait,
                )

    # ================= 设备级别锁管理 - 实用版本 =================

    def get_device_lock(self, device_id: str) -> asyncio.Lock:
        """获取设备级别的锁 - 实用版本

        Args:
            device_id: 设备ID

        Returns:
            设备专用的异步锁
        """
        if device_id not in self._device_locks:
            self._device_locks[device_id] = asyncio.Lock()
        return self._device_locks[device_id]

    async def execute_device_operation(
        self, device_id: str, operation: Callable, *args, **kwargs
    ) -> Any:
        """在设备锁保护下执行操作 - 实用版本

        Args:
            device_id: 设备ID
            operation: 要执行的操作函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            操作执行结果
        """
        device_lock = self.get_device_lock(device_id)

        async with device_lock:
            try:
                # 简单的速率限制 - 适合家用规模
                await asyncio.sleep(0.01)  # 10ms基础延迟

                if asyncio.iscoroutinefunction(operation):
                    return await operation(*args, **kwargs)
                else:
                    return operation(*args, **kwargs)

            except Exception as e:
                _LOGGER.warning("设备 %s 操作执行失败: %s", device_id, str(e))
                raise

    def cleanup_device_locks(self, device_ids: Optional[Set[str]] = None) -> None:
        """清理设备锁 - 实用版本

        Args:
            device_ids: 要清理的设备ID集合，None表示清理所有
        """
        if device_ids is None:
            self._device_locks.clear()
            _LOGGER.debug("清理所有设备锁")
        else:
            for device_id in device_ids:
                if device_id in self._device_locks:
                    del self._device_locks[device_id]
            _LOGGER.debug("清理设备锁: %s", device_ids)
