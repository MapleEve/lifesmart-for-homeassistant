"""转发模块：compatibility layer for core.local_tcp_client

这是为了测试兼容性而创建的转发模块，将旧的 core.local_tcp_client 导入
转发到新的架构位置。
"""

# 从client/local_tcp_client.py导入TCP客户端
from .client.local_tcp_client import (
    LifeSmartTCPClient,
)

# 为兼容性提供别名
LifeSmartLocalTCPClient = LifeSmartTCPClient

__all__ = [
    "LifeSmartTCPClient",
    "LifeSmartLocalTCPClient",  # 兼容别名
]