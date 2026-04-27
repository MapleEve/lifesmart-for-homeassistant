"""Strict Gen2 version selection regression tests."""

from custom_components.lifesmart.core.config.special_device_handler import (
    SpecialDeviceType,
    VersionedDeviceResolver,
    create_special_device_handler,
)
from custom_components.lifesmart.core.config.third_party_mapping import (
    get_third_party_device_info,
    get_versioned_device_info,
)
from custom_components.lifesmart.core.resolver.static_device_resolver import (
    ResolutionStatus,
    StaticDeviceResolver,
)


VERSIONED_SPEC = {
    "name": "Strict version test device",
    "versioned": True,
    "version_modes": {
        "V1": {"platforms": {"switch": {"P1": {}}}, "features": ["v1"]},
        "V2": {"platforms": {"light": {"L1": {}}}, "features": ["v2"]},
    },
}


STATIC_CONFIGS = {
    "SL_STRICT": {
        "name": "Strict version test device",
        "_features": {"is_versioned": True},
        "_version_configs": {
            "V1": {"name": "Strict V1", "platforms": {"switch": {"P1": {}}}},
            "V2": {"name": "Strict V2", "platforms": {"light": {"L1": {}}}},
        },
    }
}


def test_special_device_handler_requires_explicit_version():
    resolver = VersionedDeviceResolver()

    assert resolver.resolve_version_config("SL_STRICT", VERSIONED_SPEC, None) is None
    assert resolver.resolve_version_config("SL_STRICT", VERSIONED_SPEC, "V9") is None

    resolved = resolver.resolve_version_config("SL_STRICT", VERSIONED_SPEC, "v2")
    assert resolved is not None
    assert resolved["resolved_version"] == "V2"
    assert resolved["platforms"] == {"light": {"L1": {}}}


def test_special_device_handler_process_records_strict_failure():
    handler = create_special_device_handler()
    device_info = handler.classify_device("SL_STRICT", VERSIONED_SPEC)

    processed = handler.process_special_device(device_info, VERSIONED_SPEC)

    assert processed.special_type is SpecialDeviceType.VERSIONED
    assert processed.resolved_config is None
    assert "版本配置解析失败：缺少或不支持明确版本" in processed.processing_notes


def test_third_party_mapping_requires_exact_version_key():
    assert get_third_party_device_info("V_AIR_P", "0.0.0.1") is not None
    assert get_third_party_device_info("V_AIR_P", "missing-version") is None
    assert get_versioned_device_info("SL_SW_DM1", "V1") is not None
    assert get_versioned_device_info("SL_SW_DM1", "missing-version") is None


def test_static_device_resolver_requires_explicit_supported_version():
    resolver = StaticDeviceResolver(STATIC_CONFIGS)

    missing = resolver.resolve_device_config({"devtype": "SL_STRICT", "data": {}})
    assert missing.status is ResolutionStatus.ERROR
    assert "Missing explicit version evidence" in missing.error_message

    unsupported = resolver.resolve_device_config(
        {"devtype": "SL_STRICT", "version": "V9", "data": {}}
    )
    assert unsupported.status is ResolutionStatus.ERROR
    assert "No strict configuration found" in unsupported.error_message

    resolved = resolver.resolve_device_config(
        {"devtype": "SL_STRICT", "fullCls": "whatever.SL_STRICT_V2", "data": {}}
    )
    assert resolved.status is ResolutionStatus.SUCCESS
    assert resolved.device_config.name == "Strict V2"
    assert resolved.device_config.platforms == {"light": {"L1": {}}}
    assert resolved.device_config.device_mode == "V2"
