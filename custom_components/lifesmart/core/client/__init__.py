"""
LifeSmart Client Layer - 数据获取层
由 @MapleEve 初始创建和维护

此层负责从LifeSmart平台获取原始数据，包括：
- OpenAPI客户端：云端API调用
- TCP客户端：本地TCP连接
- 协议处理：数据协议解析
- Web客户端：HTTP接口
"""

from .local_tcp_client import LifeSmartTCPClient
from .openapi_client import LifeSmartOpenAPIClient

__all__ = [
    "LifeSmartOpenAPIClient",
    "LifeSmartTCPClient",
]
