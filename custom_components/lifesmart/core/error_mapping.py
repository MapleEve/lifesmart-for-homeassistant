"""LifeSmart API 错误代码映射和用户友好错误处理模块。

此模块提供从 LifeSmart API 错误代码到本地化描述、解决方案建议和逻辑分类的映射，
以改善用户体验和故障排除。这有助于在日志中提供更清晰的错误消息并指导用户解决问题。

架构重构的一部分，由 @MapleEve 创建。

API错误处理的核心模块：
- 错误代码映射：将数字错误代码转换为可读的错误描述
- 分类管理：按照错误类型进行逻辑分组（认证、设备、网络等）
- 多语言支持：支持中英文错误信息（预留国际化接口）
- 用户指导：为每个错误提供具体的解决建议
- 动态范围处理：对未定义的错误代码提供智能分类
"""

from typing import Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

# 错误代码映射 -> (翻译键前缀, 分类键)
# 翻译键格式将是: {prefix}.description, {prefix}.advice
# 每个错误代码对应一个翻译键前缀和逻辑分类，便于统一管理和本地化
ERROR_CODE_MAPPING = {
    # --- 请求和认证相关错误 ---
    10001: ("error.api.10001", "data_validation"),
    10002: ("error.api.10002", "config_issues"),
    10003: ("error.api.10003", "method_call"),
    10004: ("error.api.10004", "security_policy"),
    10005: ("error.api.10005", "user_authorization"),
    10006: ("error.api.10006", "user_authorization"),
    10007: ("error.api.10007", "security_policy"),
    10010: ("error.api.10010", "method_call"),
    10012: ("error.api.10012", "config_issues"),
    10015: ("error.api.10015", "permission_management"),
    10018: ("error.api.10018", "security_policy"),
    10022: ("error.api.10022", "server_error"),
    # --- 服务器和网络相关错误 ---
    10008: ("error.api.10008", "server_error"),
    10011: ("error.api.10011", "network_issues"),
    # --- 设备和资源相关错误 ---
    10009: ("error.api.10009", "device_operation"),
    10013: ("error.api.10013", "device_operation"),
    10014: ("error.api.10014", "device_management"),
    10016: ("error.api.10016", "device_operation"),
    10017: ("error.api.10017", "data_validation"),
    10019: ("error.api.10019", "resource_location"),
    10020: ("error.api.10020", "device_management"),
}

# 错误分类的翻译键映射
# 将错误分类的内部标识符映射到对应的翻译键，用于显示用户友好的分类名称
CATEGORY_TRANSLATION_KEYS = {
    "config_issues": "error.category.config_issues",
    "user_authorization": "error.category.user_authorization",
    "security_policy": "error.category.security_policy",
    "permission_management": "error.category.permission_management",
    "server_error": "error.category.server_error",
    "network_issues": "error.category.network_issues",
    "device_operation": "error.category.device_operation",
    "device_management": "error.category.device_management",
    "data_validation": "error.category.data_validation",
    "method_call": "error.category.method_call",
    "resource_location": "error.category.resource_location",
    "default": "error.category.default",
}

# 解决建议分组的翻译键
# 为每个错误分类提供对应的解决建议翻译键，便于统一管理解决方案
RECOMMENDATION_TRANSLATION_KEYS = {
    "config_issues": "error.recommendation.config_issues",
    "user_authorization": "error.recommendation.user_authorization",
    "security_policy": "error.recommendation.security_policy",
    "permission_management": "error.recommendation.permission_management",
    "server_error": "error.recommendation.server_error",
    "network_issues": "error.recommendation.network_issues",
    "device_operation": "error.recommendation.device_operation",
    "device_management": "error.recommendation.device_management",
    "data_validation": "error.recommendation.data_validation",
    "method_call": "error.recommendation.method_call",
    "resource_location": "error.recommendation.resource_location",
    "default": "error.recommendation.default",
}


def get_error_advice(
    error_code: int,
    hass: Optional["HomeAssistant"] = None,
    translation_domain: str = "lifesmart",
) -> Tuple[str, str, Optional[str]]:
    """获取错误代码的描述、建议和分类信息。

    这是错误处理的核心函数，将API返回的数字错误代码转换为用户友好的描述、
    解决建议和逻辑分类，支持多语言本地化。

    Args:
        error_code: 来自API响应的数字错误代码
        hass: HomeAssistant实例，用于翻译（可选）
        translation_domain: 使用的翻译域（默认: "lifesmart"）

    Returns:
        包含以下内容的元组:
        - desc (str): 错误描述（如果提供hass则为翻译版本）
        - advice (str): 解决建议（如果提供hass则为翻译版本）
        - category (str | None): 错误逻辑分类，或None
    """
    if error_code in ERROR_CODE_MAPPING:
        translation_key_prefix, category_key = ERROR_CODE_MAPPING[error_code]

        if hass is not None:
            # TODO: 使用 hass.localize() 实现完整的国际化翻译
            # 目前使用中文回退消息，直到实现完整的异步集成
            desc, advice = _get_chinese_messages(error_code) or _get_fallback_messages(
                error_code
            )
            category = category_key
        else:
            # 回退模式 - 使用中文消息
            desc, advice = _get_chinese_messages(error_code) or _get_fallback_messages(
                error_code
            )
            category = category_key

        return desc, advice, category

    # 对于未定义的错误代码，根据数值范围生成动态描述
    # 通过错误代码的数值范围来判断可能的错误类型和处理方式
    error_ranges = {
        (10000, 10100): "api_auth",
        (10100, 10200): "device_operation",
        (20000, 20100): "server_internal",
    }

    range_key = next(
        (v for k, v in error_ranges.items() if k[0] <= error_code < k[1]),
        "unknown",
    )

    if hass is not None:
        desc = _get_range_description_with_fallback(
            translation_domain, range_key, error_code
        )

        advice = "这是一个未定义的错误，请检查日志 " "或联系开发者获取帮助。"
    else:
        # 回退消息
        range_descriptions = {
            "api_auth": "API请求或认证错误",
            "device_operation": "设备操作或状态错误",
            "server_internal": "服务器内部错误",
            "unknown": "未知业务错误",
        }
        desc = range_descriptions.get(range_key, "未知错误")
        advice = "这是一个未定义的错误，请检查日志 " "或联系开发者获取帮助。"

    return desc, advice, None


def _get_range_description_with_fallback(
    translation_domain: str, range_key: str, error_code: int
) -> str:
    """获取范围描述，在无翻译时回退到中文。

    对于未定义的错误代码，根据其数值范围提供合适的描述。
    支持多语言翻译，但目前使用中文回退消息。

    Args:
        translation_domain: 翻译域
        range_key: 范围键（api_auth, device_operation 等）
        error_code: 错误代码数字

    Returns:
        范围描述字符串
    """
    # 目前使用中文回退描述，直到实现完整的异步集成
    range_descriptions = {
        "api_auth": "API请求或认证错误",
        "device_operation": "设备操作或状态错误",
        "server_internal": "服务器内部错误",
        "unknown": "未知业务错误",
    }
    return range_descriptions.get(range_key, f"错误 {error_code}")


def _get_fallback_messages(error_code: int) -> Tuple[str, str]:
    """在翻译不可用时获取错误代码的回退中文消息。

    这个函数为所有已知的LifeSmart API错误代码提供中文的错误描述和
    解决建议，确保用户在任何情况下都能获得有用的错误信息。

    Args:
        error_code: 数字错误代码

    Returns:
        包含中文（描述，建议）的元组
    """
    fallback_messages = {
        10001: (
            "请求格式无效",
            "请验证JSON数据结构和字段类型 " "是否符合API文档要求。",
        ),
        10002: (
            "AppKey不存在",
            "请检查您的AppKey是否在 " "集成配置中正确填写。",
        ),
        10003: (
            "不支持HTTP GET请求",
            "这是一个开发错误，该接口应使用POST方法。",
        ),
        10004: (
            "签名无效",
            "请检查签名算法、时间戳 " "或凭据是否正确。",
        ),
        10005: (
            "用户未授权",
            "请检查用户令牌（UserToken）是否正确， " "或检查在LifeSmart平台上的授权。",
        ),
        10006: (
            "用户授权已过期",
            "用户令牌（UserToken）已过期，请在选项中 " "重新认证以获取新令牌。",
        ),
        10007: (
            "非法访问",
            "您的IP地址可能不在白名单中， " "请检查LifeSmart平台安全设置。",
        ),
        10008: (
            "内部错误",
            "LifeSmart服务器内部发生未知错误， " "请稍后重试或联系技术支持。",
        ),
        10009: (
            "设置属性失败",
            "检查设备是否在线并支持此属性设置， " "或查看日志获取详细信息。",
        ),
        10010: (
            "非法方法",
            "调用的API方法名不存在或已被弃用。",
        ),
        10011: (
            "操作超时",
            "网络连接不稳定或LifeSmart服务器响应 " "超时，请检查您的网络连接。",
        ),
        10012: (
            "用户名已存在",
            "此用户名已被注册，请更换用户名。",
        ),
        10013: (
            "设备未就绪",
            "设备可能当前处于离线或繁忙状态， " "请确保设备在线后重试。",
        ),
        10014: (
            "设备已被其他账户注册",
            "请先从原账户解绑此设备，然后再尝试添加。",
        ),
        10015: (
            "权限不足",
            "当前账户权限不足以执行 " "此操作，请联系管理员提升权限。",
        ),
        10016: (
            "设备不支持此操作",
            "您尝试的操作不被此设备 " "型号支持，请查阅设备文档。",
        ),
        10017: (
            "数据无效",
            "提交给设备的参数值或格式 " "不正确，请检查。",
        ),
        10018: (
            "GPS位置非法访问被拒绝",
            "请检查应用程序的地理位置权限 " "或相关场景地理围栏设置。",
        ),
        10019: (
            "请求的对象不存在",
            "请求中的设备ID、场景ID等不存在， " "请检查配置或设备是否已被删除。",
        ),
        10020: (
            "设备已在账户中存在",
            "此设备已在您的账户下，无需重复添加。",
        ),
        10022: (
            "请求地址需要重定向",
            "API服务器地址可能已更改，请尝试更新集成。",
        ),
    }

    return fallback_messages.get(
        error_code,
        (
            f"未知错误 {error_code}",
            "这是一个未定义的错误，请检查日志 " "或联系开发者获取帮助。",
        ),
    )


def _get_chinese_messages(error_code: int) -> Tuple[str, str] | None:
    """获取错误代码的中文消息。

    这个函数提供所有LifeSmart API错误代码的中文版本描述和建议。
    目前直接返回完整的中文错误消息，为未来的国际化集成留出接口。

    Args:
        error_code: 数字错误代码

    Returns:
        包含中文（描述，建议）的元组，如果未找到则返回None
    """
    # 目前直接使用完整的中文错误消息 - 为未来的i18n集成留出接口
    chinese_messages = {
        10001: (
            "请求格式无效",
            "请验证JSON数据结构和字段类型是否符合API文档要求。",
        ),
        10002: (
            "AppKey不存在",
            "请检查您的AppKey是否在集成配置中正确填写。",
        ),
        10003: (
            "不支持HTTP GET请求",
            "这是一个开发错误，该接口应使用POST方法。",
        ),
        10004: (
            "签名无效",
            "请检查签名算法、时间戳或凭据是否正确。",
        ),
        10005: (
            "用户未授权",
            "请检查用户令牌（UserToken）是否正确，或检查在LifeSmart平台上的授权。",
        ),
        10006: (
            "用户授权已过期",
            "用户令牌（UserToken）已过期，请在选项中重新认证以获取新令牌。",
        ),
        10007: (
            "非法访问",
            "您的IP地址可能不在白名单中，请检查LifeSmart平台安全设置。",
        ),
        10008: (
            "内部错误",
            "LifeSmart服务器内部发生未知错误，请稍后重试或联系技术支持。",
        ),
        10009: (
            "设置属性失败",
            "检查设备是否在线并支持此属性设置，或查看日志获取详细信息。",
        ),
        10010: (
            "非法方法",
            "调用的API方法名不存在或已被弃用。",
        ),
        10011: (
            "操作超时",
            "网络连接不稳定或LifeSmart服务器响应超时，请检查您的网络连接。",
        ),
        10012: (
            "用户名已存在",
            "此用户名已被注册，请更换用户名。",
        ),
        10013: (
            "设备未就绪",
            "设备可能当前处于离线或繁忙状态，请确保设备在线后重试。",
        ),
        10014: (
            "设备已被其他账户注册",
            "请先从原账户解绑此设备，然后再尝试添加。",
        ),
        10015: (
            "权限不足",
            "当前账户权限不足以执行此操作，请联系管理员提升权限。",
        ),
        10016: (
            "设备不支持此操作",
            "您尝试的操作不被此设备型号支持，请查阅设备文档。",
        ),
        10017: (
            "数据无效",
            "提交给设备的参数值或格式不正确，请检查。",
        ),
        10018: (
            "GPS位置非法访问被拒绝",
            "请检查应用程序的地理位置权限或相关场景地理围栏设置。",
        ),
        10019: (
            "请求的对象不存在",
            "请求中的设备ID、场景ID等不存在，请检查配置或设备是否已被删除。",
        ),
        10020: (
            "设备已在账户中存在",
            "此设备已在您的账户下，无需重复添加。",
        ),
        10022: (
            "请求地址需要重定向",
            "API服务器地址可能已更改，请尝试更新集成。",
        ),
    }

    return chinese_messages.get(error_code)
