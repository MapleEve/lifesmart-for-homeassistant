"""转发模块：compatibility layer for core.local_web_client

这是为了测试兼容性而创建的转发模块，将旧的 core.local_web_client 导入
转发到新的架构位置。
"""

# 从client/local_web_client.py导入Web客户端
from .client.local_web_client import (
    LifeSmartWebClient,
)

__all__ = [
    "LifeSmartWebClient",
]