"""LifeSmart helpers module - Backwards compatibility layer.

This module provides backward compatibility for test functions that expect
the old helpers.py structure. The actual implementation now uses the new
architecture with platform detection.

By @MapleEve - Created during architecture refactoring to maintain test compatibility.
"""

from .core.platform.platform_detection import (
    get_device_platform_mapping,
    get_sensor_subdevices,
    get_binary_sensor_subdevices,
    get_switch_subdevices,
    get_light_subdevices,
    get_cover_subdevices,
    get_climate_subdevices,
    safe_get,
    expand_wildcard_ios,
    get_device_effective_type,
)


def is_sensor(device: dict) -> bool:
    """Check if device supports sensor platform.

    Args:
        device: Device dictionary with devtype and data

    Returns:
        True if device has sensor capabilities
    """
    platforms = get_device_platform_mapping(device)
    return "sensor" in platforms


def is_binary_sensor(device: dict) -> bool:
    """Check if device supports binary_sensor platform.

    Args:
        device: Device dictionary with devtype and data

    Returns:
        True if device has binary_sensor capabilities
    """
    platforms = get_device_platform_mapping(device)
    return "binary_sensor" in platforms


def is_switch(device: dict) -> bool:
    """Check if device supports switch platform.

    Args:
        device: Device dictionary with devtype and data

    Returns:
        True if device has switch capabilities
    """
    platforms = get_device_platform_mapping(device)
    return "switch" in platforms


def is_light(device: dict) -> bool:
    """Check if device supports light platform.

    Args:
        device: Device dictionary with devtype and data

    Returns:
        True if device has light capabilities
    """
    platforms = get_device_platform_mapping(device)
    return "light" in platforms


def is_cover(device: dict) -> bool:
    """Check if device supports cover platform.

    Args:
        device: Device dictionary with devtype and data

    Returns:
        True if device has cover capabilities
    """
    platforms = get_device_platform_mapping(device)
    return "cover" in platforms


def is_climate(device: dict) -> bool:
    """Check if device supports climate platform.

    Args:
        device: Device dictionary with devtype and data

    Returns:
        True if device has climate capabilities
    """
    platforms = get_device_platform_mapping(device)
    return "climate" in platforms


# Re-export platform detection functions for backward compatibility
__all__ = [
    "is_sensor",
    "is_binary_sensor",
    "is_switch",
    "is_light",
    "is_cover",
    "is_climate",
    "get_device_platform_mapping",
    "get_sensor_subdevices",
    "get_binary_sensor_subdevices",
    "get_switch_subdevices",
    "get_light_subdevices",
    "get_cover_subdevices",
    "get_climate_subdevices",
    "safe_get",
    "expand_wildcard_ios",
    "get_device_effective_type",
]
