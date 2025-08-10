"""LifeSmart 诊断数据收集器。

此模块实现Home Assistant标准的诊断功能，
收集集成状态、配置信息和设备数据用于故障排查。

修复版本：
- 使用正确的Hub架构方法
- 使用字典访问模式处理设备数据
- 添加错误处理和数据验证
- 保持安全的数据脱敏
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .core.const import (
    DOMAIN,
    DEVICE_ID_KEY,
    DEVICE_TYPE_KEY,
    DEVICE_NAME_KEY,
    DEVICE_DATA_KEY,
    DEVICE_FULLCLS_KEY,
    DEVICE_VERSION_KEY,
    HUB_ID_KEY,
    MANUFACTURER,
)

_LOGGER = logging.getLogger(__name__)

# 需要脱敏的敏感字段
TO_REDACT = {
    "password",
    "token",
    "usertoken",
    "apptoken",
    "userid",
    "username",
    "email",
    "phone",
    "deviceid",
    "serial",
    "mac",
    "ip",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict[str, Any]:
    """返回配置条目的诊断信息。

    Args:
        hass: Home Assistant实例
        config_entry: 配置条目

    Returns:
        诊断数据字典，已脱敏处理
    """
    # 获取Hub数据
    if DOMAIN not in hass.data or config_entry.entry_id not in hass.data[DOMAIN]:
        return {"error": "集成数据不存在"}

    hub_data = hass.data[DOMAIN][config_entry.entry_id]
    hub = hub_data.get("hub")

    if not hub:
        return {"error": "Hub实例不存在"}

    # 收集基础配置信息
    diagnostics_data = {
        "config_entry": {
            "title": config_entry.title,
            "version": config_entry.version,
            "domain": config_entry.domain,
            "entry_id": config_entry.entry_id,
            "state": str(config_entry.state),
            "source": str(config_entry.source),
            "data": async_redact_data(config_entry.data, TO_REDACT),
            "options": async_redact_data(config_entry.options, TO_REDACT),
        },
        "hub_info": {
            "type": config_entry.data.get("type", "unknown"),
            "device_count": 0,
            "hub_count": 0,
            "manufacturer": MANUFACTURER,
        },
        "client_status": {
            "client_type": "unknown",
            "connected": False,
        },
        "devices": [],
        "hubs": [],
        "exclude_config": {},
        "concurrency_stats": {},
    }

    try:
        # 收集Hub状态信息 - 使用正确的Hub方法
        devices = hub.get_devices()
        diagnostics_data["hub_info"]["device_count"] = len(devices)

        # 收集设备信息（限制前15个设备避免数据过大）
        device_sample = devices[:15] if len(devices) > 15 else devices

        # 统计Hub信息
        hubs = set()
        for device in devices:
            if HUB_ID_KEY in device:
                hubs.add(device[HUB_ID_KEY])
        diagnostics_data["hub_info"]["hub_count"] = len(hubs)

        for device in device_sample:
            try:
                # 使用字典访问模式，符合实际架构
                device_info = {
                    "device_id": device.get(DEVICE_ID_KEY, "unknown"),
                    "device_type": device.get(DEVICE_TYPE_KEY, "unknown"),
                    "device_name": device.get(DEVICE_NAME_KEY, "unknown"),
                    "hub_id": device.get(HUB_ID_KEY, "unknown"),
                    "full_class": device.get(DEVICE_FULLCLS_KEY, "unknown"),
                    "version": device.get(DEVICE_VERSION_KEY, "unknown"),
                    "data_keys": (
                        list(device.get(DEVICE_DATA_KEY, {}).keys())
                        if device.get(DEVICE_DATA_KEY)
                        else []
                    ),
                    "data_count": len(device.get(DEVICE_DATA_KEY, {})),
                }
                diagnostics_data["devices"].append(
                    async_redact_data(device_info, TO_REDACT)
                )
            except Exception as e:
                _LOGGER.warning("收集设备诊断信息时跳过异常设备: %s", e)
                diagnostics_data["devices"].append(
                    {"error": f"设备数据异常: {type(e).__name__}"}
                )

        # 收集客户端状态 - 使用正确的Hub方法
        client = hub.get_client()
        if client:
            diagnostics_data["client_status"] = {
                "client_type": type(client).__name__,
                "connected": hasattr(client, "is_connected")
                and callable(getattr(client, "is_connected", None)),
            }

            # 安全检查连接状态
            if hasattr(client, "is_connected"):
                try:
                    diagnostics_data["client_status"][
                        "connected"
                    ] = client.is_connected()
                except Exception as e:
                    diagnostics_data["client_status"]["connection_check_error"] = str(e)

        # 收集排除配置信息
        try:
            exclude_devices, exclude_hubs = hub.get_exclude_config()
            diagnostics_data["exclude_config"] = {
                "excluded_device_count": len(exclude_devices),
                "excluded_hub_count": len(exclude_hubs),
            }
        except Exception as e:
            diagnostics_data["exclude_config"] = {"error": str(e)}

        # 收集并发控制统计
        try:
            diagnostics_data["concurrency_stats"] = hub.get_concurrency_stats()
        except Exception as e:
            diagnostics_data["concurrency_stats"] = {"error": str(e)}

        # 收集Hub列表信息
        diagnostics_data["hubs"] = [
            async_redact_data({"hub_id": hub_id}, TO_REDACT) for hub_id in sorted(hubs)
        ]

        # 收集问题设备信息（如果存在）
        if hasattr(hub, "_problematic_devices"):
            diagnostics_data["problematic_devices"] = {
                device_type: {
                    "count": info.get("count", 0),
                    "last_seen": str(info.get("timestamp", "unknown")),
                }
                for device_type, info in hub._problematic_devices.items()
            }

    except Exception as e:
        # 如果收集过程出错，至少返回基本信息和错误
        _LOGGER.error("收集诊断数据时发生异常: %s", e, exc_info=True)
        diagnostics_data["collection_error"] = {
            "error_type": type(e).__name__,
            "error_message": str(e),
        }
        diagnostics_data["collection_success"] = False
    else:
        diagnostics_data["collection_success"] = True

    return async_redact_data(diagnostics_data, TO_REDACT)


async def async_get_device_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry, device: Any
) -> dict[str, Any]:
    """返回设备级别的诊断信息。

    Args:
        hass: Home Assistant实例
        config_entry: 配置条目
        device: HA设备注册表中的设备实例

    Returns:
        设备诊断数据字典，已脱敏处理
    """
    # 获取Hub数据以匹配设备
    if DOMAIN not in hass.data or config_entry.entry_id not in hass.data[DOMAIN]:
        return {"error": "集成数据不存在"}

    hub_data = hass.data[DOMAIN][config_entry.entry_id]
    hub = hub_data.get("hub")

    if not hub:
        return {"error": "Hub实例不存在"}

    # 从HA设备注册表设备构建诊断信息
    device_diagnostics = {
        "device_info": {
            "identifiers": list(device.identifiers) if device.identifiers else [],
            "name": device.name or "unknown",
            "model": device.model or "unknown",
            "manufacturer": device.manufacturer or MANUFACTURER,
            "sw_version": device.sw_version,
            "hw_version": device.hw_version,
            "entry_type": str(device.entry_type) if device.entry_type else None,
            "via_device_id": device.via_device_id,
            "area_id": device.area_id,
            "disabled_by": str(device.disabled_by) if device.disabled_by else None,
        },
        "raw_device_data": None,
        "collection_success": False,
    }

    try:
        # 尝试从Hub的设备列表中找到对应的原始设备数据
        devices = hub.get_devices()
        matched_device = None

        # 通过设备标识符匹配
        for lifesmart_device in devices:
            device_id = lifesmart_device.get(DEVICE_ID_KEY)
            if device_id and any(
                str(device_id) in identifier_tuple
                for identifier_tuple in (device.identifiers or [])
            ):
                matched_device = lifesmart_device
                break

        if matched_device:
            # 收集原始设备数据（安全访问）
            device_diagnostics["raw_device_data"] = {
                "device_id": matched_device.get(DEVICE_ID_KEY, "unknown"),
                "device_type": matched_device.get(DEVICE_TYPE_KEY, "unknown"),
                "device_name": matched_device.get(DEVICE_NAME_KEY, "unknown"),
                "hub_id": matched_device.get(HUB_ID_KEY, "unknown"),
                "full_class": matched_device.get(DEVICE_FULLCLS_KEY, "unknown"),
                "version": matched_device.get(DEVICE_VERSION_KEY, "unknown"),
                "io_data_summary": _summarize_io_data(
                    matched_device.get(DEVICE_DATA_KEY, {})
                ),
            }
            device_diagnostics["collection_success"] = True
        else:
            device_diagnostics["raw_device_data"] = "未找到对应的LifeSmart设备数据"

    except Exception as e:
        _LOGGER.error("收集设备诊断数据时发生异常: %s", e, exc_info=True)
        device_diagnostics["collection_error"] = {
            "error_type": type(e).__name__,
            "error_message": str(e),
        }

    return async_redact_data(device_diagnostics, TO_REDACT)


def _summarize_io_data(io_data: dict) -> dict[str, Any]:
    """安全地总结IO数据，避免暴露敏感信息。

    Args:
        io_data: 设备IO数据字典

    Returns:
        IO数据摘要
    """
    if not io_data or not isinstance(io_data, dict):
        return {"summary": "无IO数据"}

    summary = {
        "io_count": len(io_data),
        "io_keys": sorted(io_data.keys()),
        "io_types": {},
    }

    # 统计每个IO口的数据类型
    for key, value in io_data.items():
        if isinstance(value, dict):
            io_type = value.get("type", "unknown")
            io_val = value.get("val")
            summary["io_types"][key] = {
                "type": io_type,
                "has_val": io_val is not None,
                "val_type": type(io_val).__name__ if io_val is not None else None,
            }
        else:
            summary["io_types"][key] = {"data_format": "非标准格式"}

    return summary
