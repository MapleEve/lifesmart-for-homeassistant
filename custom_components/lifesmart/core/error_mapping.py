"""LifeSmart API error code mapping and user-friendly error handling module.

This module provides mapping from LifeSmart API error codes to localized descriptions,
solution suggestions, and logical categories for improved user experience and
troubleshooting. This helps provide clearer error messages in logs and guides
users to resolve issues.

Created by @MapleEve as part of the integration architecture refactoring.
"""

from typing import Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

# Error code -> (translation_key_prefix, category_key)
# Translation keys will be: {prefix}.description, {prefix}.advice
ERROR_CODE_MAPPING = {
    # --- Request & Auth ---
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
    # --- Server & Network ---
    10008: ("error.api.10008", "server_error"),
    10011: ("error.api.10011", "network_issues"),
    # --- Device & Resource ---
    10009: ("error.api.10009", "device_operation"),
    10013: ("error.api.10013", "device_operation"),
    10014: ("error.api.10014", "device_management"),
    10016: ("error.api.10016", "device_operation"),
    10017: ("error.api.10017", "data_validation"),
    10019: ("error.api.10019", "resource_location"),
    10020: ("error.api.10020", "device_management"),
}

# Category key mapping for translation
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

# Recommendation group translation keys
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
    """Get error description, advice, and category for an error code.

    Args:
        error_code: The numeric error code from API response.
        hass: HomeAssistant instance for translation (optional).
        translation_domain: Translation domain to use (default: "lifesmart").

    Returns:
        A tuple containing:
        - desc (str): Error description (translated if hass provided).
        - advice (str): Solution advice (translated if hass provided).
        - category (str | None): Error logical category, or None.
    """
    if error_code in ERROR_CODE_MAPPING:
        translation_key_prefix, category_key = ERROR_CODE_MAPPING[error_code]

        if hass is not None:
            # TODO: Implement proper async translation integration with HA
            # For now, use fallback mode until proper async context is available
            desc, advice = _get_fallback_messages(error_code)
            category = category_key
        else:
            # Fallback mode - use hardcoded English messages
            desc, advice = _get_fallback_messages(error_code)
            category = category_key

        return desc, advice, category

    # For undefined error codes, generate dynamic description
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

        advice = (
            "This is an undefined error, please check logs "
            "or contact developer for help."
        )
    else:
        # Fallback messages
        range_descriptions = {
            "api_auth": "API request or authentication error",
            "device_operation": "Device operation or status error",
            "server_internal": "Server internal error",
            "unknown": "Unknown business error",
        }
        desc = range_descriptions.get(range_key, "Unknown error")
        advice = (
            "This is an undefined error, please check logs "
            "or contact developer for help."
        )

    return desc, advice, None


def _get_range_description_with_fallback(
    translation_domain: str, range_key: str, error_code: int
) -> str:
    """Get range description with fallback to English.

    Args:
        translation_domain: Translation domain.
        range_key: The range key (api_auth, device_operation, etc).
        error_code: The error code number.

    Returns:
        Range description string.
    """
    # For now, use fallback descriptions until proper async integration is implemented
    range_descriptions = {
        "api_auth": "API request or authentication error",
        "device_operation": "Device operation or status error",
        "server_internal": "Server internal error",
        "unknown": "Unknown business error",
    }
    return range_descriptions.get(range_key, f"Error {error_code}")


def _get_fallback_messages(error_code: int) -> Tuple[str, str]:
    """Get fallback English messages for error codes when translations are unavailable.

    Args:
        error_code: The numeric error code.

    Returns:
        A tuple of (description, advice) in English.
    """
    fallback_messages = {
        10001: (
            "Invalid request format",
            "Please verify the JSON data structure and field types "
            "conform to the API documentation.",
        ),
        10002: (
            "AppKey does not exist",
            "Please check that your AppKey is correctly filled "
            "in the integration configuration.",
        ),
        10003: (
            "HTTP GET request not supported",
            "This is a development error, this interface should use POST method.",
        ),
        10004: (
            "Invalid signature",
            "Please check if the signature algorithm, timestamp "
            "or credentials are correct.",
        ),
        10005: (
            "User not authorized",
            "Please check if the user token (UserToken) is correct, "
            "or check authorization on LifeSmart platform.",
        ),
        10006: (
            "User authorization expired",
            "User token (UserToken) has expired, please re-authenticate "
            "in options to get a new token.",
        ),
        10007: (
            "Illegal access",
            "Your IP address may not be in the whitelist, "
            "please check LifeSmart platform security settings.",
        ),
        10008: (
            "Internal error",
            "LifeSmart server internal unknown error occurred, "
            "please retry later or contact technical support.",
        ),
        10009: (
            "Failed to set property",
            "Check if device is online and supports this property setting, "
            "or view logs for detailed information.",
        ),
        10010: (
            "Illegal method",
            "The called API method name does not exist or has been deprecated.",
        ),
        10011: (
            "Operation timeout",
            "Network connection is unstable or LifeSmart server response "
            "timeout, please check your network connection.",
        ),
        10012: (
            "Username already exists",
            "This username has been registered, please change username.",
        ),
        10013: (
            "Device not ready",
            "Device may currently be offline or busy, "
            "please ensure device is online then retry.",
        ),
        10014: (
            "Device already registered by another account",
            "Please first unbind this device from original account, then try adding.",
        ),
        10015: (
            "Insufficient permissions",
            "Current account permissions are insufficient to perform "
            "this operation, please contact administrator to elevate permissions.",
        ),
        10016: (
            "Device does not support this operation",
            "The operation you attempted is not supported by this device "
            "model, please consult device documentation.",
        ),
        10017: (
            "Invalid data",
            "Parameter values or formats submitted to device are "
            "incorrect, please check.",
        ),
        10018: (
            "GPS location illegal access denied",
            "Please check application's geographic location permissions "
            "or related scene geofence settings.",
        ),
        10019: (
            "Requested object does not exist",
            "Device ID, scene ID etc. in request do not exist, "
            "please check configuration or if device has been deleted.",
        ),
        10020: (
            "Device already exists in account",
            "This device is already under your account, no need to add repeatedly.",
        ),
        10022: (
            "Request address needs redirection",
            "API server address may have changed, please try updating integration.",
        ),
    }

    return fallback_messages.get(
        error_code,
        (
            f"Unknown error {error_code}",
            "This is an undefined error, please check logs "
            "or contact developer for help.",
        ),
    )
