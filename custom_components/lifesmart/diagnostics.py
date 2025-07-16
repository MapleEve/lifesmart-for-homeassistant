"""
LifeSmart Integration by @MapleEve - Diagnostics and Error Handling Utilities.
Provides mappings for error codes and functions to generate user-friendly advice.
"""

from typing import Tuple, Optional

# 错误码 -> (描述, 解决方案建议, 分类)
ERROR_CODE_MAPPING = {
    10001: ("请求格式错误", "请校验JSON数据结构及字段类型", "数据校验"),
    10002: ("AppKey不存在", "检查集成配置中的APPKey是否正确", "配置问题"),
    10003: ("不⽀持HTTP GET请求", "该接口要求使用POST方法", "方法调用"),
    10004: ("签名⾮法", "检查时间戳和签名算法是否正确", "安全策略"),
    10005: ("⽤户没有授权", "请到管理平台授予访问权限", "用户授权"),
    10007: ("⾮法访问", "检查请求来源IP白名单设置", "安全策略"),
    10010: ("Method⾮法", "检查API请求方法是否被支持", "方法调用"),
    10015: ("权限不够", "联系管理员提升账户权限等级", "权限管理"),
    10017: ("数据⾮法", "校验提交的字段取值范围及格式", "数据校验"),
    10019: ("对象不存在", "检查请求中的设备/用户ID是否正确", "资源定位"),
}

# 解决方案建议分组
RECOMMENDATION_GROUP = {
    "用户授权": "请重新登录或刷新令牌",
    "安全策略": "检查网络安全配置或联系运维",
    "方法调用": "参考最新版API文档确认调用方式",
    "权限管理": "联系账户管理员调整权限设置",
    "数据校验": "使用调试工具验证数据格式",
    "资源定位": "检查请求参数的资源ID有效性",
    "default": "查看官方文档或联系技术支持",
}


def get_error_advice(error_code: int) -> Tuple[str, str, Optional[str]]:
    """获取错误描述、解决方案和分类"""
    if error_code in ERROR_CODE_MAPPING:
        desc, advice, category = ERROR_CODE_MAPPING[error_code]
        return desc, advice, category

    # 动态生成未知错误描述
    error_ranges = {
        (10000, 10100): "API请求错误",
        (10100, 10200): "设备操作错误",
        (20000, 20100): "服务端内部错误",
    }
    desc = next(
        (v for k, v in error_ranges.items() if k[0] <= error_code < k[1]),
        "未知业务错误",
    )
    return desc, "", None
