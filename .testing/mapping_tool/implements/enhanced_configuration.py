"""
Enhanced Configuration Port Implementation

This module provides enhanced configuration management capabilities by
extracting and upgrading the configuration logic from RUN_THIS_TOOL.py.

Key Features:
- Multi-source configuration (CLI arguments + config files + environment)
- Hot reload support with change notification
- Configuration validation with detailed error messages
- Default value management with type coercion
- Environment variable mapping
- Configuration profiles (dev, test, prod)

Author: Platform Engineer Agent
Date: 2025-08-15
Based on: RUN_THIS_TOOL.py configuration patterns + JSONConfigurationPort
"""

from __future__ import annotations

import os
import json
import argparse
import threading
from abc import ABC
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
import time

# Import architecture interfaces (with fallbacks)
try:
    from ..architecture.ports import ConfigurationPort, PortAdapter
    from ..data_types.core_types import (
        AnalysisConfig,
        ConfigValue,
        FilePath,
        LogLevel,
        ReportFormat,
        ConfigurationError,
        MappingToolError,
        validate_analysis_config,
    )
except ImportError:
    # Fallback for development/testing
    class ConfigurationError(Exception):
        pass

    class MappingToolError(Exception):
        pass

    LogLevel = str
    ReportFormat = str
    ConfigValue = Any
    FilePath = Union[str, Path]


# =============================================================================
# Enhanced Configuration Data Structures
# =============================================================================


@dataclass
class ConfigurationProfile:
    """Configuration profile for different deployment environments."""

    name: str
    config_data: Dict[str, Any]
    source_file: Optional[str] = None
    is_active: bool = False
    created_at: float = field(default_factory=time.time)
    last_modified: float = field(default_factory=time.time)


@dataclass
class ConfigurationSource:
    """Configuration source metadata."""

    source_type: str  # 'cli_args', 'config_file', 'env_vars', 'defaults'
    source_path: Optional[str] = None
    priority: int = 0  # Higher priority overrides lower
    data: Dict[str, Any] = field(default_factory=dict)
    last_loaded: float = field(default_factory=time.time)


@dataclass
class ConfigurationSchema:
    """Configuration schema definition for validation."""

    key: str
    value_type: type
    default_value: Any
    required: bool = False
    choices: Optional[List[Any]] = None
    validator: Optional[Callable[[Any], bool]] = None
    description: str = ""
    env_var: Optional[str] = None
    cli_arg: Optional[str] = None


# =============================================================================
# Enhanced Configuration Port - Extracted from RUN_THIS_TOOL.py
# =============================================================================


class EnhancedConfigurationPort:
    """
    Enhanced configuration management port with multi-source support.

    Extracted and enhanced from RUN_THIS_TOOL.py configuration logic:
    - CLI argument parsing (from SmartIOAllocationAnalyzer)
    - Configuration file loading
    - Environment variable support
    - Hot reload capabilities
    - Configuration validation
    """

    def __init__(self, name: str = "EnhancedConfigurationPort"):
        self.name = name
        self._sources: Dict[str, ConfigurationSource] = {}
        self._profiles: Dict[str, ConfigurationProfile] = {}
        self._active_profile: Optional[str] = None
        self._merged_config: Dict[str, Any] = {}
        self._schema: Dict[str, ConfigurationSchema] = {}
        self._change_listeners: List[Callable[[Dict[str, Any]], None]] = []
        self._lock = threading.RLock()
        self._last_reload: float = 0.0

        # Initialize schema from RUN_THIS_TOOL.py patterns
        self._initialize_configuration_schema()

    def _initialize_configuration_schema(self):
        """Initialize configuration schema based on RUN_THIS_TOOL.py patterns."""
        # Core schemas extracted from RUN_THIS_TOOL.py argument parsing
        schemas = [
            ConfigurationSchema(
                key="input_file",
                value_type=str,
                default_value=None,
                required=False,
                description="Input file path for device data",
                env_var="MAPPING_TOOL_INPUT_FILE",
                cli_arg="--input",
            ),
            ConfigurationSchema(
                key="output_file",
                value_type=str,
                default_value=None,
                required=False,
                description="Output file path for results",
                env_var="MAPPING_TOOL_OUTPUT_FILE",
                cli_arg="--output",
            ),
            ConfigurationSchema(
                key="output_format",
                value_type=str,
                default_value="markdown",
                required=False,
                choices=["json", "markdown", "html", "plain"],
                description="Output format",
                env_var="MAPPING_TOOL_OUTPUT_FORMAT",
                cli_arg="--format",
            ),
            ConfigurationSchema(
                key="verbose",
                value_type=bool,
                default_value=False,
                required=False,
                description="Enable verbose output",
                env_var="MAPPING_TOOL_VERBOSE",
                cli_arg="--verbose",
            ),
            ConfigurationSchema(
                key="log_level",
                value_type=str,
                default_value="INFO",
                required=False,
                choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                description="Set logging level",
                env_var="MAPPING_TOOL_LOG_LEVEL",
                cli_arg="--log-level",
            ),
            ConfigurationSchema(
                key="config_file",
                value_type=str,
                default_value=None,
                required=False,
                description="Configuration file path",
                env_var="MAPPING_TOOL_CONFIG_FILE",
                cli_arg="--config",
            ),
            ConfigurationSchema(
                key="cache_size",
                value_type=int,
                default_value=512,  # Enhanced from original 128
                required=False,
                description="Cache size for performance optimization",
                env_var="MAPPING_TOOL_CACHE_SIZE",
                cli_arg="--cache-size",
                validator=lambda x: isinstance(x, int) and x > 0,
            ),
            ConfigurationSchema(
                key="timeout",
                value_type=float,
                default_value=300.0,
                required=False,
                description="Operation timeout in seconds",
                env_var="MAPPING_TOOL_TIMEOUT",
                cli_arg="--timeout",
                validator=lambda x: isinstance(x, (int, float)) and x > 0,
            ),
            ConfigurationSchema(
                key="max_workers",
                value_type=int,
                default_value=4,
                required=False,
                description="Maximum worker threads for concurrent operations",
                env_var="MAPPING_TOOL_MAX_WORKERS",
                cli_arg="--max-workers",
                validator=lambda x: isinstance(x, int) and 1 <= x <= 16,
            ),
            ConfigurationSchema(
                key="enable_performance_monitoring",
                value_type=bool,
                default_value=False,
                required=False,
                description="Enable performance monitoring",
                env_var="MAPPING_TOOL_ENABLE_PERF_MONITORING",
                cli_arg="--enable-perf-monitoring",
            ),
            ConfigurationSchema(
                key="nlp_available",
                value_type=bool,
                default_value=True,
                required=False,
                description="NLP dependencies availability",
                env_var="MAPPING_TOOL_NLP_AVAILABLE",
            ),
            ConfigurationSchema(
                key="ai_analyzer_available",
                value_type=bool,
                default_value=True,
                required=False,
                description="AI analyzer availability",
                env_var="MAPPING_TOOL_AI_ANALYZER_AVAILABLE",
            ),
        ]

        for schema in schemas:
            self._schema[schema.key] = schema

    def load_from_cli_arguments(
        self, args: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Load configuration from CLI arguments using RUN_THIS_TOOL.py patterns.

        Extracted from SmartIOAllocationAnalyzer.__init__ argument parsing logic.
        """
        try:
            if args is None:
                import sys

                args = sys.argv[1:]

            parser = argparse.ArgumentParser(
                description="Mapping Tool - Enhanced Device Analysis and Comparison",
                formatter_class=argparse.RawDescriptionHelpFormatter,
            )

            # Add arguments based on schema
            for key, schema in self._schema.items():
                if schema.cli_arg:
                    self._add_argument_to_parser(parser, schema)

            # Parse arguments
            parsed_args = parser.parse_args(args)
            cli_config = vars(parsed_args)

            # Create configuration source
            cli_source = ConfigurationSource(
                source_type="cli_args",
                priority=300,  # High priority
                data=cli_config,
                last_loaded=time.time(),
            )

            with self._lock:
                self._sources["cli_args"] = cli_source
                self._merge_configurations()

            print(f"✅ CLI configuration loaded: {len(cli_config)} parameters")
            return cli_config

        except SystemExit as e:
            if e.code != 0:
                raise ConfigurationError(f"CLI argument parsing failed: {e}")
            raise
        except Exception as e:
            raise ConfigurationError(f"Failed to load CLI configuration: {e}")

    def _add_argument_to_parser(
        self, parser: argparse.ArgumentParser, schema: ConfigurationSchema
    ):
        """Add argument to parser based on schema definition."""
        kwargs = {"help": schema.description, "default": schema.default_value}

        # Handle different argument types
        if schema.value_type == bool:
            if schema.default_value:
                kwargs["action"] = "store_false"
            else:
                kwargs["action"] = "store_true"
        else:
            kwargs["type"] = schema.value_type

            if schema.choices:
                kwargs["choices"] = schema.choices

        # Add the argument
        if schema.cli_arg:
            short_arg = schema.cli_arg.replace("--", "-").split("-")[1][:1]
            parser.add_argument(f"-{short_arg}", schema.cli_arg, **kwargs)
        else:
            parser.add_argument(f"--{schema.key.replace('_', '-')}", **kwargs)

    def load_from_config_file(
        self, config_file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Load configuration from JSON config file."""
        try:
            # Determine config file path
            if not config_file_path:
                config_file_path = self.get_value("config_file")

            if not config_file_path:
                return {}

            config_path = Path(config_file_path)
            if not config_path.exists():
                print(f"⚠️ Configuration file not found: {config_file_path}")
                return {}

            # Load JSON config
            with open(config_path, "r", encoding="utf-8") as f:
                file_config = json.load(f)

            # Create configuration source
            file_source = ConfigurationSource(
                source_type="config_file",
                source_path=str(config_path),
                priority=200,  # Medium priority
                data=file_config,
                last_loaded=time.time(),
            )

            with self._lock:
                self._sources["config_file"] = file_source
                self._merge_configurations()

            print(f"✅ Configuration file loaded: {config_file_path}")
            return file_config

        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON in config file {config_file_path}: {e}"
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load config file {config_file_path}: {e}"
            )

    def load_from_environment(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        try:
            env_config = {}

            for key, schema in self._schema.items():
                if schema.env_var and schema.env_var in os.environ:
                    raw_value = os.environ[schema.env_var]

                    # Type coercion
                    try:
                        if schema.value_type == bool:
                            env_config[key] = raw_value.lower() in (
                                "true",
                                "1",
                                "yes",
                                "on",
                            )
                        elif schema.value_type == int:
                            env_config[key] = int(raw_value)
                        elif schema.value_type == float:
                            env_config[key] = float(raw_value)
                        else:
                            env_config[key] = raw_value
                    except ValueError as e:
                        print(f"⚠️ Invalid environment variable {schema.env_var}: {e}")
                        continue

            # Create configuration source
            if env_config:
                env_source = ConfigurationSource(
                    source_type="env_vars",
                    priority=250,  # Higher than config file, lower than CLI
                    data=env_config,
                    last_loaded=time.time(),
                )

                with self._lock:
                    self._sources["env_vars"] = env_source
                    self._merge_configurations()

                print(
                    f"✅ Environment configuration loaded: {len(env_config)} variables"
                )

            return env_config

        except Exception as e:
            raise ConfigurationError(f"Failed to load environment configuration: {e}")

    def load_defaults(self) -> Dict[str, Any]:
        """Load default configuration values."""
        try:
            default_config = {}

            for key, schema in self._schema.items():
                if schema.default_value is not None:
                    default_config[key] = schema.default_value

            # Create configuration source
            default_source = ConfigurationSource(
                source_type="defaults",
                priority=100,  # Lowest priority
                data=default_config,
                last_loaded=time.time(),
            )

            with self._lock:
                self._sources["defaults"] = default_source
                self._merge_configurations()

            print(f"✅ Default configuration loaded: {len(default_config)} defaults")
            return default_config

        except Exception as e:
            raise ConfigurationError(f"Failed to load default configuration: {e}")

    def _merge_configurations(self):
        """Merge all configuration sources by priority."""
        merged = {}

        # Sort sources by priority (ascending)
        sorted_sources = sorted(self._sources.values(), key=lambda x: x.priority)

        # Merge configurations
        for source in sorted_sources:
            merged.update(source.data)

        # Validate merged configuration
        self._validate_configuration(merged)

        # Update merged config
        old_config = self._merged_config.copy()
        self._merged_config = merged

        # Notify listeners of changes
        if old_config != merged:
            self._notify_change_listeners(merged)

    def _validate_configuration(self, config: Dict[str, Any]):
        """Validate configuration against schema."""
        errors = []

        for key, schema in self._schema.items():
            if schema.required and key not in config:
                errors.append(f"Required configuration key '{key}' is missing")
                continue

            if key in config:
                value = config[key]

                # Type validation
                if not isinstance(value, schema.value_type):
                    try:
                        # Attempt type coercion
                        config[key] = schema.value_type(value)
                    except (ValueError, TypeError):
                        errors.append(
                            f"Configuration key '{key}' has invalid type. Expected {schema.value_type.__name__}, got {type(value).__name__}"
                        )
                        continue

                # Choices validation
                if schema.choices and config[key] not in schema.choices:
                    errors.append(
                        f"Configuration key '{key}' has invalid value '{config[key]}'. Must be one of: {schema.choices}"
                    )

                # Custom validator
                if schema.validator and not schema.validator(config[key]):
                    errors.append(f"Configuration key '{key}' failed validation")

        if errors:
            raise ConfigurationError(
                f"Configuration validation failed: {'; '.join(errors)}"
            )

    def get_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        with self._lock:
            return self._merged_config.get(key, default)

    def set_value(self, key: str, value: Any, source: str = "runtime") -> None:
        """Set configuration value at runtime."""
        with self._lock:
            # Create or update runtime source
            if source not in self._sources:
                self._sources[source] = ConfigurationSource(
                    source_type=source,
                    priority=400,  # Highest priority
                    data={},
                    last_loaded=time.time(),
                )

            self._sources[source].data[key] = value
            self._merge_configurations()

    def get_all_values(self) -> Dict[str, Any]:
        """Get all configuration values."""
        with self._lock:
            return self._merged_config.copy()

    def reload_configuration(self) -> None:
        """Reload configuration from all sources."""
        try:
            with self._lock:
                # Clear existing sources except defaults
                sources_to_keep = ["defaults", "runtime"]
                self._sources = {
                    k: v for k, v in self._sources.items() if k in sources_to_keep
                }

                # Reload from sources
                self.load_defaults()
                self.load_from_environment()

                config_file = self.get_value("config_file")
                if config_file:
                    self.load_from_config_file(config_file)

                self._last_reload = time.time()
                print("✅ Configuration reloaded successfully")

        except Exception as e:
            raise ConfigurationError(f"Failed to reload configuration: {e}")

    def add_change_listener(self, listener: Callable[[Dict[str, Any]], None]) -> None:
        """Add configuration change listener."""
        self._change_listeners.append(listener)

    def remove_change_listener(
        self, listener: Callable[[Dict[str, Any]], None]
    ) -> None:
        """Remove configuration change listener."""
        if listener in self._change_listeners:
            self._change_listeners.remove(listener)

    def _notify_change_listeners(self, new_config: Dict[str, Any]) -> None:
        """Notify all change listeners."""
        for listener in self._change_listeners:
            try:
                listener(new_config)
            except Exception as e:
                print(f"⚠️ Configuration change listener error: {e}")

    def get_configuration_summary(self) -> Dict[str, Any]:
        """Get configuration summary and metadata."""
        with self._lock:
            return {
                "total_keys": len(self._merged_config),
                "sources": {
                    name: {
                        "type": source.source_type,
                        "priority": source.priority,
                        "keys": len(source.data),
                        "last_loaded": source.last_loaded,
                    }
                    for name, source in self._sources.items()
                },
                "last_reload": self._last_reload,
                "schema_keys": len(self._schema),
                "active_profile": self._active_profile,
            }

    def create_profile(self, name: str, config_override: Dict[str, Any]) -> None:
        """Create a configuration profile."""
        profile = ConfigurationProfile(name=name, config_data=config_override.copy())
        self._profiles[name] = profile
        print(f"✅ Configuration profile '{name}' created")

    def activate_profile(self, name: str) -> None:
        """Activate a configuration profile."""
        if name not in self._profiles:
            raise ConfigurationError(f"Configuration profile '{name}' not found")

        # Deactivate current profile
        if self._active_profile:
            self._profiles[self._active_profile].is_active = False

        # Activate new profile
        profile = self._profiles[name]
        profile.is_active = True
        self._active_profile = name

        # Apply profile configuration
        profile_source = ConfigurationSource(
            source_type="profile",
            priority=350,  # Higher than env, lower than CLI
            data=profile.config_data,
            last_loaded=time.time(),
        )

        with self._lock:
            self._sources["profile"] = profile_source
            self._merge_configurations()

        print(f"✅ Configuration profile '{name}' activated")


# =============================================================================
# Enhanced Configuration Factory
# =============================================================================


class EnhancedConfigurationFactory:
    """Factory for creating enhanced configuration ports."""

    def __init__(self):
        self._config_instances = {}

    def create_configuration_port(
        self, config_sources: Optional[List[str]] = None, auto_load: bool = True
    ) -> EnhancedConfigurationPort:
        """Create enhanced configuration port with specified sources."""
        port = EnhancedConfigurationPort()

        if auto_load:
            # Load configurations in order of priority
            sources = config_sources or [
                "defaults",
                "environment",
                "config_file",
                "cli_args",
            ]

            for source in sources:
                try:
                    if source == "defaults":
                        port.load_defaults()
                    elif source == "environment":
                        port.load_from_environment()
                    elif source == "config_file":
                        port.load_from_config_file()
                    elif source == "cli_args":
                        port.load_from_cli_arguments()
                except Exception as e:
                    print(f"⚠️ Failed to load {source} configuration: {e}")

        return port

    def create_configuration_from_run_this_tool(
        self, cli_args: Optional[List[str]] = None
    ) -> EnhancedConfigurationPort:
        """
        Create configuration port compatible with RUN_THIS_TOOL.py.

        This method provides a drop-in replacement for RUN_THIS_TOOL.py
        configuration management.
        """
        port = EnhancedConfigurationPort()

        # Load in the same order as RUN_THIS_TOOL.py
        port.load_defaults()
        port.load_from_environment()

        if cli_args is not None:
            port.load_from_cli_arguments(cli_args)
        else:
            port.load_from_cli_arguments()

        # Load config file if specified
        config_file = port.get_value("config_file")
        if config_file:
            port.load_from_config_file(config_file)

        return port


# =============================================================================
# Helper Functions
# =============================================================================


def create_enhanced_configuration(
    cli_args: Optional[List[str]] = None,
    config_file: Optional[str] = None,
    profile: Optional[str] = None,
) -> EnhancedConfigurationPort:
    """
    Create enhanced configuration port with RUN_THIS_TOOL.py compatibility.

    Provides a simple interface for creating configuration with the same
    patterns used in RUN_THIS_TOOL.py.
    """
    factory = EnhancedConfigurationFactory()

    # Create configuration port
    config_port = factory.create_configuration_from_run_this_tool(cli_args)

    # Load specific config file if provided
    if config_file:
        config_port.set_value("config_file", config_file)
        config_port.load_from_config_file(config_file)

    # Activate profile if provided
    if profile:
        # Create a basic profile if it doesn't exist
        try:
            config_port.activate_profile(profile)
        except ConfigurationError:
            print(f"⚠️ Profile '{profile}' not found, using default configuration")

    return config_port


def get_run_this_tool_compatible_config(
    cli_args: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Get configuration in format compatible with RUN_THIS_TOOL.py.

    This function provides the same configuration interface that
    SmartIOAllocationAnalyzer expects.
    """
    config_port = create_enhanced_configuration(cli_args)
    return config_port.get_all_values()
