"""
Gen2-only device resolver package exports.

The package-level facade exposes the current static Gen2 resolver functions only.
The legacy dynamic resolver and compatibility bridge resolver are intentionally not
exported here, so production callers cannot select fallback-capable paths through
this facade.
"""

import time
from typing import Any, Dict, Optional

from homeassistant.exceptions import HomeAssistantError

from ..config.device_specs import _RAW_DEVICE_DATA
from ..config.extended_static_config_preprocessor import (
    ExtendedStaticConfigPreprocessor,
)
from ..config.static_config_validator import StaticConfigValidator
from .static_device_resolver import (
    StaticDeviceResolver,
    ResolutionResult as StaticResolutionResult,
    ResolutionStatus,
)

from .types import (
    DeviceConfig,
    PlatformConfig,
    IOConfig,
    ResolutionResult,
    SupportLevel,
    ValidationStatus,
    DeviceData,
    MappingData,
    PlatformName,
    IOKey,
)


class Gen2StaticDeviceResolver:
    """Production Gen2-only resolver facade over the strict static resolver."""

    def __init__(self) -> None:
        preprocessor = ExtendedStaticConfigPreprocessor(_RAW_DEVICE_DATA)
        self._static_configs = preprocessor.generate_static_configs()

        validation_result = StaticConfigValidator().validate_all_configs(
            self._static_configs
        )
        if not validation_result.valid:
            raise RuntimeError(
                "Gen2 static configuration validation failed: "
                f"{validation_result.errors}"
            )

        self._static_resolver = StaticDeviceResolver(self._static_configs)
        self._cache_stats = {"hits": 0, "misses": 0, "errors": 0}

    def resolve_device_config(self, device: DeviceData) -> ResolutionResult:
        start_time = time.time()
        try:
            if not device or not isinstance(device, dict):
                return ResolutionResult.error_result(
                    "Invalid device data: must be non-empty dict"
                )

            static_result = self._static_resolver.resolve_device_config(device)
            result = self._convert_static_result(static_result, device)
            result.resolution_time_ms = (time.time() - start_time) * 1000
            if result.success:
                self._cache_stats["hits"] += 1
            else:
                self._cache_stats["misses"] += 1
            return result
        except Exception as err:  # pragma: no cover - defensive strict error path
            self._cache_stats["errors"] += 1
            result = ResolutionResult.error_result(
                f"Failed to resolve device {device.get('me', 'unknown')}: {err}"
            )
            result.resolution_time_ms = (time.time() - start_time) * 1000
            return result

    def get_platform_config(
        self, device: DeviceData, platform: PlatformName
    ) -> Optional[PlatformConfig]:
        result = self.resolve_device_config(device)
        if not result.success:
            raise HomeAssistantError(
                result.error_message
                or f"Failed to resolve device {device.get('me', 'unknown')}"
            )
        if result.device_config:
            return result.device_config.get_platform_config(platform)
        return None

    def validate_device_support(
        self, device: DeviceData, platform: PlatformName
    ) -> bool:
        try:
            platform_config = self.get_platform_config(device, platform)
            return platform_config is not None and platform_config.supported
        except Exception:
            return False

    def get_io_config(
        self, device: DeviceData, platform: PlatformName, io_key: IOKey
    ) -> Optional[IOConfig]:
        platform_config = self.get_platform_config(device, platform)
        if platform_config:
            return platform_config.ios.get(io_key)
        return None

    def get_supported_platforms(self, device: DeviceData) -> list[PlatformName]:
        result = self.resolve_device_config(device)
        if result.success and result.device_config:
            return result.device_config.supported_platforms
        return []

    def get_cache_stats(self) -> Dict[str, Any]:
        return self._cache_stats.copy()

    def clear_cache(self) -> None:
        self._cache_stats = {"hits": 0, "misses": 0, "errors": 0}

    def get_static_resolver_stats(self) -> Dict[str, Any]:
        return self._static_resolver.get_resolver_stats()

    def _convert_static_result(
        self, static_result: StaticResolutionResult, device: DeviceData
    ) -> ResolutionResult:
        if static_result.status == ResolutionStatus.ERROR:
            return ResolutionResult.error_result(
                static_result.error_message or "Unknown resolution error"
            )

        static_config = static_result.device_config
        if not static_config:
            return ResolutionResult.error_result("No device configuration")

        source_mapping = self._static_configs.get(static_config.device_type, {})
        features = source_mapping.get("_features", {})

        compatible_config = DeviceConfig(
            device_type=static_config.device_type,
            name=static_config.name,
            category=features.get("category"),
            manufacturer=features.get("manufacturer"),
            model=features.get("model"),
            raw_device=device,
            source_mapping=source_mapping,
        )
        compatible_config.platforms = {
            platform_name: platform_config
            for platform_name, platform_config in (
                (
                    platform_name,
                    self._convert_static_platform(platform_name, platform_data),
                )
                for platform_name, platform_data in static_config.platforms.items()
            )
            if platform_config is not None
        }
        compatible_config.__post_init__()

        if static_result.status == ResolutionStatus.WARNING:
            return ResolutionResult.warning_result(
                compatible_config,
                static_result.warnings[0] if static_result.warnings else "Warning",
            )
        return ResolutionResult.success_result(compatible_config)

    def _convert_static_platform(
        self, platform_name: str, platform_data: Dict[str, Any]
    ) -> Optional[PlatformConfig]:
        if not isinstance(platform_data, dict):
            return None

        platform_config = PlatformConfig(platform_type=platform_name, supported=True)
        platform_config.ios = {
            io_key: io_config
            for io_key, io_config in (
                (io_key, self._convert_static_io(io_data))
                for io_key, io_data in platform_data.items()
            )
            if io_config is not None
        }
        platform_config.__post_init__()
        return platform_config

    def _convert_static_io(self, io_data: Dict[str, Any]) -> Optional[IOConfig]:
        if not isinstance(io_data, dict) or not io_data.get("description"):
            return None
        return IOConfig(
            description=io_data["description"],
            data_type=io_data.get("data_type"),
            cmd_type=io_data.get("cmd_type"),
            idx=io_data.get("idx"),
            device_class=io_data.get("device_class"),
            state_class=io_data.get("state_class"),
            unit_of_measurement=io_data.get("unit_of_measurement"),
            conversion=io_data.get("conversion"),
            processor_type=io_data.get("processor_type"),
            attribute_generator=io_data.get("attribute_generator"),
            icon=io_data.get("icon"),
            entity_category=io_data.get("entity_category"),
            value_template=io_data.get("value_template"),
            state_mapping=io_data.get("state_mapping"),
            commands=io_data.get("commands", {}),
        )


_global_device_resolver: Optional[Gen2StaticDeviceResolver] = None


def get_device_resolver() -> Gen2StaticDeviceResolver:
    global _global_device_resolver
    if _global_device_resolver is None:
        _global_device_resolver = Gen2StaticDeviceResolver()
    return _global_device_resolver


def resolve_device_config(device: DeviceData) -> ResolutionResult:
    return get_device_resolver().resolve_device_config(device)


def get_platform_config(
    device: DeviceData, platform: PlatformName
) -> Optional[PlatformConfig]:
    return get_device_resolver().get_platform_config(device, platform)


def validate_device_support(device: DeviceData, platform: PlatformName) -> bool:
    return get_device_resolver().validate_device_support(device, platform)


__all__ = [
    "DeviceConfig",
    "PlatformConfig",
    "IOConfig",
    "ResolutionResult",
    "SupportLevel",
    "ValidationStatus",
    "DeviceData",
    "MappingData",
    "PlatformName",
    "IOKey",
    "Gen2StaticDeviceResolver",
    "get_device_resolver",
    "resolve_device_config",
    "get_platform_config",
    "validate_device_support",
]
