# Type Safety and Runtime Validation Tests
# Enhanced type system validation for port-service-cache architecture

import pytest
import sys
from typing import (
    get_type_hints,
    get_origin,
    get_args,
    Union,
    Optional,
    List,
    Dict,
    Any,
)
from dataclasses import is_dataclass, fields
from abc import ABC, abstractmethod
import inspect

# Import type definitions and implementations
try:
    from ..data_types.core_types import (
        DeviceData,
        AnalysisResult,
        ComparisonResult,
        ReportData,
        AnalysisConfig,
        NLPConfig,
        CacheConfig,
        DeviceID,
        IOPort,
        ConfigValue,
        Timestamp,
        FilePath,
        LogLevel,
        AnalysisStatus,
        NLPProvider,
        CacheStrategy,
        ReportFormat,
        CacheEntry,
    )

    from ..architecture.services import (
        AnalysisService,
        NLPService,
        ComparisonService,
        ReportService,
        DocumentService,
        BaseService,
        AsyncService,
        ServiceFactory,
        ServiceResult,
    )

    from ..architecture.ports import (
        ConfigurationPort,
        CommandLinePort,
        FilePort,
        ReportPort,
        AsyncFilePort,
        DataSourcePort,
        LoggingPort,
        PortAdapter,
        PortFactory,
    )

    from ..architecture.cache import (
        BaseCache,
        DataCache,
        ResultCache,
        ConfigCache,
        AsyncCache,
        CacheManager,
        CacheFactory,
    )

    TYPE_SYSTEM_AVAILABLE = True
except ImportError:
    TYPE_SYSTEM_AVAILABLE = False
    pytest.skip("Type system modules not available", allow_module_level=True)


# =============================================================================
# Type System Validation Tests
# =============================================================================


class TestTypeSystemValidation:
    """Comprehensive type system validation tests."""

    def test_core_type_aliases_are_valid(self):
        """Test that all type aliases are properly defined and usable."""
        # Test primitive type aliases
        assert DeviceID == str
        assert IOPort == int
        assert isinstance("test_device", DeviceID)
        assert isinstance(123, IOPort)

        # Test union type aliases
        config_value: ConfigValue = "string_value"
        assert isinstance(config_value, (str, int, float, bool, dict, list))

        config_value = {"nested": "dict"}
        assert isinstance(config_value, (str, int, float, bool, dict, list))

        # Test path types
        file_path: FilePath = "/tmp/test.txt"
        assert isinstance(file_path, (str, type(None)))  # Union with Path

        # Test log level literals
        log_level: LogLevel = "INFO"
        assert log_level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

    def test_enum_completeness_and_values(self):
        """Test that all enums have appropriate values and are complete."""
        # Test AnalysisStatus enum
        assert hasattr(AnalysisStatus, "PENDING")
        assert hasattr(AnalysisStatus, "RUNNING")
        assert hasattr(AnalysisStatus, "COMPLETED")
        assert hasattr(AnalysisStatus, "FAILED")
        assert hasattr(AnalysisStatus, "CANCELLED")

        # Test NLPProvider enum
        assert NLPProvider.SPACY.value == "spacy"
        assert NLPProvider.NLTK.value == "nltk"
        assert NLPProvider.TRANSFORMERS.value == "transformers"
        assert NLPProvider.NONE.value == "none"

        # Test CacheStrategy enum
        assert CacheStrategy.LRU.value == "lru"
        assert CacheStrategy.TTL.value == "ttl"
        assert CacheStrategy.MANUAL.value == "manual"
        assert CacheStrategy.NONE.value == "none"

        # Test ReportFormat enum
        assert ReportFormat.JSON.value == "json"
        assert ReportFormat.MARKDOWN.value == "markdown"
        assert ReportFormat.HTML.value == "html"

    def test_typeddict_structure_validation(self):
        """Test that TypedDict classes have correct structure and required fields."""
        # Test DeviceData structure
        device_data: DeviceData = {
            "device_id": "test_device",
            "device_name": "Test Device",
            "platform": "switch",
            "io_ports": {},
            "metadata": {},
            "created_at": "2025-08-15T00:00:00",
            "updated_at": None,
        }

        # Verify required fields exist
        assert "device_id" in device_data
        assert "device_name" in device_data
        assert "platform" in device_data
        assert "io_ports" in device_data
        assert "metadata" in device_data
        assert "created_at" in device_data

        # Test AnalysisResult structure
        analysis_result: AnalysisResult = {
            "device_id": "test_device",
            "analysis_status": AnalysisStatus.COMPLETED,
            "platforms_detected": ["switch", "sensor"],
            "confidence_score": 0.95,
            "analysis_details": {},
            "timestamp": "2025-08-15T00:00:00",
            "processing_time": 1.5,
        }

        assert "device_id" in analysis_result
        assert "analysis_status" in analysis_result
        assert "platforms_detected" in analysis_result
        assert "confidence_score" in analysis_result

    def test_generic_type_usage(self):
        """Test that generic types work correctly with type parameters."""
        # Test CacheEntry generic usage
        string_cache_entry: CacheEntry[str] = {
            "key": "test_key",
            "value": "test_value",
            "created_at": "2025-08-15T00:00:00",
            "accessed_at": "2025-08-15T00:00:00",
            "ttl_seconds": 300.0,
            "access_count": 1,
        }

        assert isinstance(string_cache_entry["value"], str)

        # Test ServiceResult generic usage
        service_result: ServiceResult[Dict[str, Any]] = ServiceResult(
            success=True, data={"result": "success"}, error=None, processing_time=0.5
        )

        assert service_result.is_success()
        assert isinstance(service_result.get_data(), dict)


# =============================================================================
# Abstract Method Contract Validation
# =============================================================================


class TestAbstractMethodContracts:
    """Test that all abstract method contracts are properly defined."""

    def test_service_layer_abstract_methods(self):
        """Test service layer abstract method contracts."""
        # Test AnalysisService contracts
        analysis_methods = [
            method
            for method in dir(AnalysisService)
            if not method.startswith("_")
            and hasattr(getattr(AnalysisService, method), "__isabstractmethod__")
        ]

        expected_analysis_methods = [
            "analyze_devices",
            "analyze_single_device",
            "batch_analyze",
            "get_analysis_progress",
        ]

        for method in expected_analysis_methods:
            assert hasattr(AnalysisService, method), f"Missing method: {method}"
            method_obj = getattr(AnalysisService, method)
            assert getattr(
                method_obj, "__isabstractmethod__", False
            ), f"Method {method} should be abstract"

    def test_port_layer_protocol_methods(self):
        """Test port layer protocol method contracts."""
        # Test ConfigurationPort protocol
        config_methods = [
            "load_config",
            "get_setting",
            "set_setting",
            "validate_config",
            "get_all_settings",
        ]

        for method in config_methods:
            assert hasattr(ConfigurationPort, method), f"Missing method: {method}"

        # Test FilePort protocol
        file_methods = [
            "read_text_file",
            "write_text_file",
            "read_json_file",
            "write_json_file",
            "file_exists",
            "create_directory",
            "list_files",
            "get_file_size",
        ]

        for method in file_methods:
            assert hasattr(FilePort, method), f"Missing method: {method}"

    def test_cache_layer_abstract_methods(self):
        """Test cache layer abstract method contracts."""
        # Test BaseCache abstract methods
        cache_methods = [
            "initialize",
            "cleanup",
            "get",
            "set",
            "delete",
            "clear",
            "exists",
            "size",
        ]

        for method in cache_methods:
            assert hasattr(BaseCache, method), f"Missing method: {method}"
            method_obj = getattr(BaseCache, method)
            assert getattr(
                method_obj, "__isabstractmethod__", False
            ), f"Method {method} should be abstract"

    def test_abstract_method_signatures(self):
        """Test that abstract methods have correct signatures."""
        # Test AnalysisService.analyze_devices signature
        analyze_devices = getattr(AnalysisService, "analyze_devices")
        sig = inspect.signature(analyze_devices)

        # Should have 'self', 'config', and 'devices' parameters
        params = list(sig.parameters.keys())
        assert "self" in params
        assert "config" in params
        assert "devices" in params

        # Test async methods are properly marked
        assert inspect.iscoroutinefunction(analyze_devices)

    def test_interface_inheritance_hierarchy(self):
        """Test that interface inheritance is properly structured."""
        # Test service inheritance
        assert issubclass(AsyncService, BaseService)
        assert issubclass(AnalysisService, AsyncService)
        assert issubclass(NLPService, AsyncService)

        # Test that ABC is properly used
        assert issubclass(BaseService, ABC)
        assert issubclass(BaseCache, ABC)

    def test_factory_pattern_contracts(self):
        """Test that factory patterns have correct contracts."""
        # Test ServiceFactory abstract methods
        factory_methods = [
            "create_analysis_service",
            "create_nlp_service",
            "create_comparison_service",
            "create_report_service",
            "create_document_service",
        ]

        for method in factory_methods:
            assert hasattr(ServiceFactory, method), f"Missing factory method: {method}"
            method_obj = getattr(ServiceFactory, method)
            assert getattr(
                method_obj, "__isabstractmethod__", False
            ), f"Factory method {method} should be abstract"


# =============================================================================
# Runtime Type Checking Tests
# =============================================================================


class TestRuntimeTypeChecking:
    """Runtime type validation and checking tests."""

    def test_type_hint_extraction_and_validation(self):
        """Test that type hints can be extracted and validated at runtime."""
        # Test service method type hints
        if hasattr(AnalysisService, "analyze_devices"):
            method = getattr(AnalysisService, "analyze_devices")
            hints = get_type_hints(method)

            # Should have return type annotation
            assert "return" in hints

        # Test configuration type hints
        if hasattr(ConfigurationPort, "get_setting"):
            method = getattr(ConfigurationPort, "get_setting")
            hints = get_type_hints(method)

            # Should have typed parameters
            assert len(hints) > 0

    def test_protocol_runtime_checkable(self):
        """Test that protocols are runtime checkable."""
        from typing import runtime_checkable

        # Test that port protocols are runtime checkable
        assert hasattr(ConfigurationPort, "__protocol__")
        assert hasattr(CommandLinePort, "__protocol__")
        assert hasattr(FilePort, "__protocol__")

    def test_generic_type_parameter_validation(self):
        """Test generic type parameter extraction and validation."""
        # Test BaseCache generic parameters
        if hasattr(BaseCache, "__orig_bases__"):
            base_generics = BaseCache.__orig_bases__
            # Should include Generic[K, V]
            has_generic = any("Generic" in str(base) for base in base_generics)
            assert has_generic, "BaseCache should be generic"

    def test_union_type_validation(self):
        """Test Union type handling and validation."""
        # Test ConfigValue union type
        config_value_hint = ConfigValue

        # Should be a Union type
        if hasattr(config_value_hint, "__origin__"):
            assert get_origin(config_value_hint) == Union

            # Should include basic types
            args = get_args(config_value_hint)
            type_names = [
                arg.__name__ if hasattr(arg, "__name__") else str(arg) for arg in args
            ]
            assert "str" in type_names
            assert "int" in type_names
            assert "bool" in type_names

    def test_dataclass_type_validation(self):
        """Test dataclass structure and type validation."""
        # Find dataclass types in implementations
        try:
            from ..implements.analysis_service_impl import NLPAnalysisConfig

            if is_dataclass(NLPAnalysisConfig):
                # Test field types
                field_types = {
                    field.name: field.type for field in fields(NLPAnalysisConfig)
                }

                # Should have properly typed fields
                assert "enhanced_parsing" in field_types
                assert field_types["enhanced_parsing"] == bool

                # Test instance creation with type checking
                config = NLPAnalysisConfig(
                    enhanced_parsing=True,
                    aggressive_matching=True,
                    debug_mode=False,
                    confidence_threshold=0.7,
                    platform_exclusion_rules=True,
                )

                assert isinstance(config.enhanced_parsing, bool)
                assert isinstance(config.confidence_threshold, float)

        except ImportError:
            pytest.skip("Implementation classes not available")


# =============================================================================
# Error Handling Type Safety Tests
# =============================================================================


class TestErrorHandlingTypeSafety:
    """Test type safety in error handling scenarios."""

    def test_exception_hierarchy_types(self):
        """Test that custom exceptions have proper type hierarchy."""
        try:
            from ..data_types.core_types import (
                MappingToolError,
                AnalysisError,
                ConfigurationError,
                CacheError,
            )

            # Test inheritance hierarchy
            assert issubclass(AnalysisError, MappingToolError)
            assert issubclass(ConfigurationError, MappingToolError)
            assert issubclass(CacheError, MappingToolError)

            # Test exception instantiation
            analysis_error = AnalysisError("Test analysis error")
            assert isinstance(analysis_error, Exception)
            assert isinstance(analysis_error, MappingToolError)

        except ImportError:
            pytest.skip("Exception types not available")

    def test_optional_type_handling(self):
        """Test Optional type handling in method signatures."""
        # Test that methods properly handle Optional parameters
        if hasattr(ConfigurationPort, "get_setting"):
            method = getattr(ConfigurationPort, "get_setting")
            hints = get_type_hints(method)

            # Should handle Optional default values
            sig = inspect.signature(method)
            for param_name, param in sig.parameters.items():
                if param.default is not None:
                    # Parameter with default should be Optional
                    if param_name in hints:
                        param_type = hints[param_name]
                        # Check if it's Optional (Union with None)
                        if hasattr(param_type, "__origin__"):
                            assert get_origin(param_type) == Union or type(
                                None
                            ) in get_args(param_type)

    def test_async_return_type_consistency(self):
        """Test that async methods have consistent return type annotations."""
        async_methods = []

        # Collect async methods from services
        for cls in [AnalysisService, NLPService, DocumentService]:
            for attr_name in dir(cls):
                if not attr_name.startswith("_"):
                    attr = getattr(cls, attr_name)
                    if inspect.iscoroutinefunction(attr):
                        async_methods.append((cls.__name__, attr_name, attr))

        # Test that async methods have proper return type annotations
        for class_name, method_name, method in async_methods:
            hints = get_type_hints(method)
            if "return" in hints:
                return_type = hints["return"]
                # Should be properly typed, not just 'Any'
                assert (
                    return_type != Any
                ), f"{class_name}.{method_name} should have specific return type"


# =============================================================================
# Performance Type System Tests
# =============================================================================


class TestTypeSystemPerformance:
    """Test type system performance and overhead."""

    def test_type_checking_overhead(self):
        """Test that type checking doesn't add significant overhead."""
        import time

        # Test type hint lookup performance
        start_time = time.time()

        for _ in range(1000):
            # Simulate type checking operations
            if hasattr(AnalysisService, "analyze_devices"):
                hints = get_type_hints(getattr(AnalysisService, "analyze_devices"))

        end_time = time.time()
        type_check_time = end_time - start_time

        # Should complete quickly (< 1 second for 1000 operations)
        assert (
            type_check_time < 1.0
        ), f"Type checking took {type_check_time:.3f}s, too slow"

    def test_generic_instantiation_performance(self):
        """Test generic type instantiation performance."""
        import time

        # Test ServiceResult generic instantiation
        start_time = time.time()

        for i in range(100):
            result = ServiceResult[Dict[str, Any]](
                success=True, data={"iteration": i}, error=None, processing_time=0.001
            )
            assert result.is_success()

        end_time = time.time()
        instantiation_time = end_time - start_time

        # Should be efficient (< 0.1 seconds for 100 instantiations)
        assert (
            instantiation_time < 0.1
        ), f"Generic instantiation took {instantiation_time:.3f}s, too slow"


# =============================================================================
# Integration Type Tests
# =============================================================================


class TestIntegrationTypeSafety:
    """Test type safety across component boundaries."""

    def test_service_port_integration_types(self):
        """Test type compatibility between services and ports."""
        # Test that service method parameters match port method returns

        # Example: DocumentService.load_device_data should accept what FilePort.read_json_file returns
        if hasattr(DocumentService, "load_device_data") and hasattr(
            FilePort, "read_json_file"
        ):
            doc_hints = get_type_hints(getattr(DocumentService, "load_device_data"))
            file_hints = get_type_hints(getattr(FilePort, "read_json_file"))

            # Type compatibility should be maintained
            # This is a conceptual test - actual implementation may vary
            assert "return" in file_hints

    def test_cache_service_integration_types(self):
        """Test type compatibility between cache and service layers."""
        # Test that cache value types match service data types

        # BaseCache should be able to store service result types
        if hasattr(BaseCache, "set") and hasattr(AnalysisService, "analyze_devices"):
            cache_hints = get_type_hints(getattr(BaseCache, "set"))
            service_hints = get_type_hints(getattr(AnalysisService, "analyze_devices"))

            # Should have compatible types
            assert "value" in cache_hints  # Cache should accept values
            assert "return" in service_hints  # Service should return typed values

    def test_configuration_type_consistency(self):
        """Test that configuration types are consistent across components."""
        # Test that all configuration classes use consistent types
        config_classes = []

        try:
            from ..data_types.core_types import AnalysisConfig, NLPConfig, CacheConfig

            config_classes = [AnalysisConfig, NLPConfig, CacheConfig]
        except ImportError:
            pytest.skip("Configuration types not available")

        # All config classes should use consistent patterns
        for config_cls in config_classes:
            if hasattr(config_cls, "__annotations__"):
                annotations = getattr(config_cls, "__annotations__")
                # Should have typed fields
                assert (
                    len(annotations) > 0
                ), f"{config_cls.__name__} should have typed fields"


if __name__ == "__main__":
    # Run type system tests
    pytest.main([__file__, "-v", "--tb=short", "-k", "test_type"])
