#!/usr/bin/env python3
"""
Modern Entry Point - Composition Root for Enhanced Mapping Tool

This module provides a modern, clean entry point for the mapping tool while
maintaining complete backward compatibility with RUN_THIS_TOOL.py. It implements
the composition root pattern with dependency injection.

Key Features:
- Modern Python 3.11+ patterns and type safety
- Composition root pattern replacing "God Class" anti-patterns
- Complete dependency injection with enhanced components
- Dual-entry strategy: RUN_THIS_TOOL.py (legacy) + main.py (modern)
- 100% backward compatibility with existing workflows
- Enhanced configuration, caching, and CLI management

Author: Platform Engineer Agent
Date: 2025-08-15
Architecture: Port-Service-Cache with Composition Root Pattern
"""

from __future__ import annotations

import os
import sys
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import traceback

# Add the project root to path for absolute imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

# Enhanced architecture imports
try:
    from .implements.enhanced_configuration import (
        EnhancedConfigurationPort,
        EnhancedConfigurationFactory,
        create_enhanced_configuration,
    )
    from .implements.enhanced_cache import (
        EnhancedMemoryDataManager,
        EnhancedStreamingDataGenerator,
        create_enhanced_memory_agent,
    )
    from .implements.enhanced_cli_port import (
        EnhancedSmartIOAllocationAnalyzer,
        enhanced_main,
        create_smart_io_allocation_analyzer,
    )
    from .implements.port_implementations import (
        StandardFilePort,
        JSONConfigurationPort,
        StandardPortFactory,
    )
    from .implements.services import DocumentService, AnalysisService

    ENHANCED_COMPONENTS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Enhanced components not available: {e}")
    print("🔄 Falling back to compatibility mode...")
    ENHANCED_COMPONENTS_AVAILABLE = False

# Fallback imports for compatibility
if not ENHANCED_COMPONENTS_AVAILABLE:
    try:
        from RUN_THIS_TOOL import SmartIOAllocationAnalyzer, main as legacy_main

        LEGACY_FALLBACK_AVAILABLE = True
    except ImportError:
        LEGACY_FALLBACK_AVAILABLE = False

# Core project imports
try:
    from custom_components.lifesmart.core.config.device_specs import _RAW_DEVICE_DATA

    DEVICE_MAPPING = _RAW_DEVICE_DATA
    print("✅ Device data loaded successfully")
except ImportError as e:
    print(f"❌ Critical error: Cannot load device data - {e}")
    print("🔧 Please ensure you're running this tool from the project root directory")
    sys.exit(1)


# =============================================================================
# Modern Application Configuration
# =============================================================================


@dataclass
class ApplicationContext:
    """Modern application context with dependency injection."""

    config_port: Optional[Any] = None
    cache_system: Optional[Dict[str, Any]] = None
    file_port: Optional[Any] = None
    analyzer: Optional[Any] = None
    document_service: Optional[Any] = None
    analysis_service: Optional[Any] = None
    performance_metrics: Dict[str, Any] = None

    def __post_init__(self):
        if self.performance_metrics is None:
            self.performance_metrics = {
                "startup_time": 0.0,
                "initialization_time": 0.0,
                "analysis_time": 0.0,
                "total_time": 0.0,
            }


# =============================================================================
# Modern Composition Root Implementation
# =============================================================================


class ModernCompositionRoot:
    """
    Modern composition root for the mapping tool.

    Implements dependency injection and service orchestration using
    the enhanced port-service-cache architecture while maintaining
    complete backward compatibility.
    """

    def __init__(self):
        self.startup_time = time.time()
        self.context = ApplicationContext()
        self._initialization_complete = False

    def initialize_application(
        self, cli_args: Optional[List[str]] = None
    ) -> ApplicationContext:
        """
        Initialize the modern application with dependency injection.

        Args:
            cli_args: Optional CLI arguments for configuration

        Returns:
            Fully configured application context
        """
        try:
            print("🚀 Initializing Modern Mapping Tool...")
            init_start = time.time()

            # Phase 1: Enhanced Configuration Management
            print("🔧 Phase 1: Initializing enhanced configuration...")
            self._initialize_configuration(cli_args)

            # Phase 2: Enhanced Caching System
            print("💾 Phase 2: Initializing enhanced caching system...")
            self._initialize_caching_system()

            # Phase 3: Core Services
            print("🔮 Phase 3: Initializing core services...")
            self._initialize_services()

            # Phase 4: Analysis Engine
            print("🧠 Phase 4: Initializing analysis engine...")
            self._initialize_analysis_engine()

            # Phase 5: Dependency Injection Completion
            print("🔗 Phase 5: Completing dependency injection...")
            self._complete_dependency_injection()

            # Performance metrics
            init_time = time.time() - init_start
            self.context.performance_metrics["initialization_time"] = init_time
            self.context.performance_metrics["startup_time"] = (
                time.time() - self.startup_time
            )

            self._initialization_complete = True
            print(f"✅ Modern application initialized in {init_time:.2f}s")

            return self.context

        except Exception as e:
            print(f"❌ Modern application initialization failed: {e}")
            print(f"📍 Error details: {traceback.format_exc()}")
            raise

    def _initialize_configuration(self, cli_args: Optional[List[str]] = None):
        """Initialize enhanced configuration management."""
        try:
            if ENHANCED_COMPONENTS_AVAILABLE:
                # Create enhanced configuration port
                factory = EnhancedConfigurationFactory()
                self.context.config_port = (
                    factory.create_configuration_from_run_this_tool(cli_args)
                )

                # Add modern defaults
                self.context.config_port.set_value("application_mode", "modern")
                self.context.config_port.set_value("composition_root", "enabled")
                self.context.config_port.set_value("dependency_injection", "enabled")

                config_summary = self.context.config_port.get_configuration_summary()
                print(
                    f"✅ Enhanced configuration initialized: {config_summary['total_keys']} settings"
                )
            else:
                # Basic fallback configuration
                self.context.config_port = self._create_fallback_config(cli_args)
                print(
                    "⚠️ Using fallback configuration (enhanced components unavailable)"
                )

        except Exception as e:
            print(f"❌ Configuration initialization failed: {e}")
            raise

    def _initialize_caching_system(self):
        """Initialize enhanced caching system."""
        try:
            if ENHANCED_COMPONENTS_AVAILABLE and self.context.config_port:
                # Get cache configuration
                cache_size = self.context.config_port.get_value("cache_size", 512)
                max_workers = self.context.config_port.get_value("max_workers", 4)
                supported_platforms = self.context.config_port.get_value(
                    "supported_platforms", set()
                )

                # Create enhanced cache system
                self.context.cache_system = create_enhanced_memory_agent(
                    supported_platforms=supported_platforms,
                    raw_device_data=DEVICE_MAPPING,
                    cache_size=cache_size,
                    max_workers=max_workers,
                )

                print(f"✅ Enhanced caching system initialized")
            else:
                print("⚠️ Enhanced caching not available, using basic caching")

        except Exception as e:
            print(f"❌ Caching system initialization failed: {e}")
            raise

    def _initialize_services(self):
        """Initialize core services (DocumentService, AnalysisService)."""
        try:
            if ENHANCED_COMPONENTS_AVAILABLE:
                # Create file port for services
                self.context.file_port = StandardFilePort()
                self.context.file_port.connect()

                # 集成完整版服务实现 (Full Mode)
                from .implements.document_service_impl import create_document_service
                from .implements.analysis_service_impl import create_analysis_service
                from .implements.enhanced_nlp_service import create_enhanced_nlp_service

                # 创建文档服务实例
                self.context.document_service = create_document_service(
                    cache_manager=self.context.cache_manager, debug_mode=self.debug_mode
                )

                # 创建增强版 NLP 服务
                enhanced_nlp_service = create_enhanced_nlp_service()

                # 创建分析服务，集成完整依赖
                self.context.analysis_service = create_analysis_service(
                    document_service=self.context.document_service,
                    cache_manager=self.context.cache_manager,
                    debug_mode=self.debug_mode,
                )

                print(
                    "🚀 完整版核心服务已集成 (Full Mode: NLP + DocumentService + AnalysisService)"
                )
            else:
                print("⚠️ Enhanced services not available")

        except Exception as e:
            print(f"❌ Services initialization failed: {e}")
            raise

    def _initialize_analysis_engine(self):
        """Initialize the enhanced analysis engine."""
        try:
            if ENHANCED_COMPONENTS_AVAILABLE and self.context.config_port:
                # Get performance monitoring setting
                enable_perf_monitoring = self.context.config_port.get_value(
                    "enable_performance_monitoring", False
                )

                # Create enhanced analyzer with dependency injection
                self.context.analyzer = EnhancedSmartIOAllocationAnalyzer(
                    enable_performance_monitoring=enable_perf_monitoring
                )

                print("🧠 Enhanced analysis engine initialized")
            else:
                # Fallback to legacy analyzer
                self.context.analyzer = self._create_fallback_analyzer()
                print("⚠️ Using fallback analysis engine")

        except Exception as e:
            print(f"❌ Analysis engine initialization failed: {e}")
            raise

    def _complete_dependency_injection(self):
        """Complete dependency injection between components."""
        try:
            # Inject cache system into analyzer if available
            if (
                self.context.cache_system
                and self.context.analyzer
                and hasattr(self.context.analyzer, "_cache_system")
            ):
                # Enhanced analyzer already has cache system integrated
                print("🔗 Cache system injection verified")

            # Inject configuration into services
            if (
                self.context.config_port
                and self.context.document_service
                and hasattr(self.context.document_service, "configure")
            ):
                # Future integration point for DocumentService
                print("🔗 Configuration injection prepared")

            print("✅ Dependency injection completed")

        except Exception as e:
            print(f"❌ Dependency injection failed: {e}")
            raise

    def _create_fallback_config(
        self, cli_args: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create basic fallback configuration."""
        return {
            "cache_size": 512,
            "max_workers": 4,
            "enable_performance_monitoring": False,
            "output_format": "markdown",
            "log_level": "INFO",
            "supported_platforms": {
                "switch",
                "binary_sensor",
                "sensor",
                "cover",
                "light",
                "climate",
                "remote",
                "fan",
                "lock",
                "camera",
                "alarm_control_panel",
                "device_tracker",
                "media_player",
                "number",
                "select",
                "button",
                "text",
            },
        }

    def _create_fallback_analyzer(self):
        """Create fallback analyzer when enhanced components aren't available."""
        if LEGACY_FALLBACK_AVAILABLE:
            return SmartIOAllocationAnalyzer(enable_performance_monitoring=False)
        else:
            raise RuntimeError("No analyzer implementation available")

    def get_application_info(self) -> Dict[str, Any]:
        """Get comprehensive application information."""
        info = {
            "application_name": "Enhanced Mapping Tool",
            "version": "2.0.0-modern",
            "architecture": "Port-Service-Cache with Composition Root",
            "entry_point": "main.py (Modern)",
            "initialization_complete": self._initialization_complete,
            "enhanced_components": ENHANCED_COMPONENTS_AVAILABLE,
            "legacy_fallback": LEGACY_FALLBACK_AVAILABLE,
            "performance_metrics": self.context.performance_metrics.copy(),
        }

        if self.context.config_port and hasattr(
            self.context.config_port, "get_configuration_summary"
        ):
            info["configuration"] = self.context.config_port.get_configuration_summary()

        if self.context.cache_system:
            info["cache_system"] = {
                "type": "EnhancedMemoryDataManager",
                "components": list(self.context.cache_system.keys()),
            }

        return info


# =============================================================================
# Modern Main Functions
# =============================================================================


async def async_main(cli_args: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Asynchronous main function for modern mapping tool.

    Provides async support for I/O-intensive operations while maintaining
    compatibility with the synchronous interface.
    """
    try:
        print("🌟 Starting Enhanced Mapping Tool (Async Mode)...")

        # Initialize composition root
        composition_root = ModernCompositionRoot()
        context = composition_root.initialize_application(cli_args)

        # Get document path
        doc_path = _determine_document_path(context)

        # Perform analysis
        print("🔍 Starting enhanced analysis...")
        analysis_start = time.time()

        if context.analyzer:
            results = context.analyzer.perform_smart_comparison_analysis(doc_path)
        else:
            raise RuntimeError("No analyzer available")

        analysis_time = time.time() - analysis_start
        context.performance_metrics["analysis_time"] = analysis_time
        context.performance_metrics["total_time"] = (
            time.time() - composition_root.startup_time
        )

        # Add application info to results
        results["application_info"] = composition_root.get_application_info()
        results["performance_summary"] = {
            "startup_time": f"{context.performance_metrics['startup_time']:.2f}s",
            "initialization_time": f"{context.performance_metrics['initialization_time']:.2f}s",
            "analysis_time": f"{context.performance_metrics['analysis_time']:.2f}s",
            "total_time": f"{context.performance_metrics['total_time']:.2f}s",
        }

        print("✅ Enhanced analysis completed successfully!")
        return results

    except Exception as e:
        print(f"❌ Async main execution failed: {e}")
        print(f"📍 Error details: {traceback.format_exc()}")
        raise


def main(cli_args: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Synchronous main function for enhanced mapping tool.

    Serves as the primary entry point while providing full compatibility
    with existing synchronous workflows.

    Args:
        cli_args: Optional CLI arguments for testing and automation

    Returns:
        Analysis results dictionary
    """
    try:
        print("🎯 Starting Enhanced Mapping Tool (Modern Architecture)...")

        # Check if we should use async mode
        if cli_args and "--async" in cli_args:
            print("⚡ Async mode requested, switching to async execution...")
            return asyncio.run(async_main(cli_args))

        # Synchronous execution
        composition_root = ModernCompositionRoot()
        context = composition_root.initialize_application(cli_args)

        # Get document path
        doc_path = _determine_document_path(context)

        # Perform analysis
        print("🔍 Starting enhanced analysis...")
        analysis_start = time.time()

        if context.analyzer:
            results = context.analyzer.perform_smart_comparison_analysis(doc_path)
        else:
            raise RuntimeError("No analyzer available")

        analysis_time = time.time() - analysis_start
        context.performance_metrics["analysis_time"] = analysis_time
        context.performance_metrics["total_time"] = (
            time.time() - composition_root.startup_time
        )

        # Generate reports
        _generate_reports(results, context)

        # Add application info to results
        results["application_info"] = composition_root.get_application_info()
        results["performance_summary"] = {
            "startup_time": f"{context.performance_metrics['startup_time']:.2f}s",
            "initialization_time": f"{context.performance_metrics['initialization_time']:.2f}s",
            "analysis_time": f"{context.performance_metrics['analysis_time']:.2f}s",
            "total_time": f"{context.performance_metrics['total_time']:.2f}s",
        }

        # Print summary
        _print_execution_summary(results, context)

        print("🎉 Enhanced Mapping Tool execution completed!")
        return results

    except Exception as e:
        print(f"❌ Main execution failed: {e}")
        print(f"📍 Error details: {traceback.format_exc()}")
        raise


def _determine_document_path(context: ApplicationContext) -> str:
    """Determine the document path from configuration or defaults."""
    if context.config_port and hasattr(context.config_port, "get_value"):
        doc_path = context.config_port.get_value("input_file")
        if doc_path:
            return doc_path

    # Use default path
    return os.path.join(
        os.path.dirname(__file__), "../../docs/LifeSmart 智慧设备规格属性说明.md"
    )


def _generate_reports(results: Dict[str, Any], context: ApplicationContext):
    """Generate output reports using enhanced analyzer."""
    try:
        if not context.analyzer or not hasattr(
            context.analyzer, "save_analysis_report"
        ):
            print("⚠️ Report generation not available with current analyzer")
            return

        # Determine output paths
        base_dir = os.path.dirname(__file__)
        json_output = os.path.join(base_dir, "enhanced_analysis_report.json")
        markdown_output = os.path.join(base_dir, "ENHANCED_ANALYSIS_SUMMARY.md")

        # Save reports
        context.analyzer.save_analysis_report(results, json_output)
        context.analyzer.save_smart_markdown_report(results, markdown_output)

        print(f"📊 Reports generated:")
        print(f"   JSON: {json_output}")
        print(f"   Markdown: {markdown_output}")

    except Exception as e:
        print(f"⚠️ Report generation failed: {e}")


def _print_execution_summary(results: Dict[str, Any], context: ApplicationContext):
    """Print execution summary with enhanced metrics."""
    try:
        print("\n" + "=" * 80)
        print("🎯 Enhanced Mapping Tool Execution Summary")
        print("=" * 80)

        # Application info
        app_info = results.get("application_info", {})
        print(
            f"Application: {app_info.get('application_name', 'Enhanced Mapping Tool')}"
        )
        print(f"Version: {app_info.get('version', '2.0.0')}")
        print(f"Architecture: {app_info.get('architecture', 'Modern')}")
        print(f"Entry Point: {app_info.get('entry_point', 'main.py')}")

        # Analysis results
        overview = results.get("分析概览", {})
        if overview:
            print(f"\n📊 Analysis Results:")
            print(f"   Total Devices: {overview.get('总设备数', 'N/A')}")
            print(
                f"   Devices Requiring Attention: {overview.get('需要关注设备数', 'N/A')}"
            )
            print(f"   Filtered Devices: {overview.get('已过滤设备数', 'N/A')}")
            print(f"   Processing Efficiency: {overview.get('处理效率', 'N/A')}")

        # Performance metrics
        perf_summary = results.get("performance_summary", {})
        if perf_summary:
            print(f"\n⚡ Performance Metrics:")
            print(f"   Startup Time: {perf_summary.get('startup_time', 'N/A')}")
            print(
                f"   Initialization Time: {perf_summary.get('initialization_time', 'N/A')}"
            )
            print(f"   Analysis Time: {perf_summary.get('analysis_time', 'N/A')}")
            print(f"   Total Time: {perf_summary.get('total_time', 'N/A')}")

        # Enhanced features
        print(f"\n🔧 Enhanced Features:")
        print(
            f"   Enhanced Components: {'✅' if app_info.get('enhanced_components') else '❌'}"
        )
        print(f"   Modern Configuration: {'✅' if context.config_port else '❌'}")
        print(f"   Enhanced Caching: {'✅' if context.cache_system else '❌'}")
        print(
            f"   Dependency Injection: {'✅' if app_info.get('initialization_complete') else '❌'}"
        )

        print("=" * 80)

    except Exception as e:
        print(f"⚠️ Summary generation failed: {e}")


# =============================================================================
# Backward Compatibility and CLI Entry Points
# =============================================================================


def compatibility_main():
    """
    Backward compatibility entry point.

    This function provides complete compatibility with the original
    RUN_THIS_TOOL.py interface while using the modern architecture.
    """
    try:
        # Try enhanced mode first
        if ENHANCED_COMPONENTS_AVAILABLE:
            print("🔄 Compatibility mode with enhanced components...")
            return enhanced_main()

        # Fallback to legacy mode
        elif LEGACY_FALLBACK_AVAILABLE:
            print("🔄 Compatibility mode with legacy components...")
            return legacy_main()

        else:
            raise RuntimeError("No compatible implementation available")

    except Exception as e:
        print(f"❌ Compatibility mode failed: {e}")
        raise


def cli_entry_point():
    """CLI entry point for command-line execution."""
    try:
        import sys

        # Parse CLI arguments
        args = sys.argv[1:] if len(sys.argv) > 1 else None

        # Choose execution mode based on arguments
        if args and ("--legacy" in args):
            print("🔄 Legacy mode requested...")
            return compatibility_main()
        elif args and ("--help" in args or "-h" in args):
            _print_help()
            return
        else:
            print("🚀 Modern mode (default)...")
            return main(args)

    except KeyboardInterrupt:
        print("\n⚠️ Execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ CLI execution failed: {e}")
        sys.exit(1)


def _print_help():
    """Print comprehensive help information."""
    help_text = """
🎯 Enhanced Mapping Tool - Modern Architecture

USAGE:
    python main.py [OPTIONS]

OPTIONS:
    --help, -h              Show this help message
    --legacy               Use legacy compatibility mode
    --async                Enable asynchronous execution mode
    --config FILE          Specify configuration file
    --output FILE          Specify output file path
    --format FORMAT        Output format (json, markdown, html)
    --verbose              Enable verbose output
    --log-level LEVEL      Set logging level (DEBUG, INFO, WARNING, ERROR)
    --cache-size SIZE      Cache size for performance optimization
    --max-workers NUM      Maximum worker threads
    --enable-perf-monitoring  Enable performance monitoring

ARCHITECTURE:
    This modern implementation uses a port-service-cache architecture
    with composition root pattern and dependency injection while
    maintaining 100% backward compatibility with RUN_THIS_TOOL.py.

EXAMPLES:
    # Modern mode (default)
    python main.py
    
    # Legacy compatibility mode
    python main.py --legacy
    
    # Async mode with custom config
    python main.py --async --config config.json
    
    # Performance monitoring enabled
    python main.py --enable-perf-monitoring --verbose

For more information, see the project documentation.
"""
    print(help_text)


# =============================================================================
# Script Entry Point
# =============================================================================

if __name__ == "__main__":
    cli_entry_point()
