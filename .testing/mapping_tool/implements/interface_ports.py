"""
User Interface Port Implementations

This module provides implementations for user interaction ports including
command-line interface and logging functionality. These ports handle
user experience and monitoring aspects of the application.

Implementation Strategy:
- ClickCommandLinePort: CLI interaction using click library patterns
- StructuredLoggingPort: Enhanced logging with structured output

Author: Architecture Implementation Agent
Date: 2025-08-15
"""

from __future__ import annotations

import sys
import time
import logging
from typing import Any, Dict, List, Optional

# Import architecture interfaces
from ..architecture.ports import (
    CommandLinePort,
    LoggingPort,
)

# Import base classes
from .port_implementations import PortAdapterBase

# Import core types
from ..data_types.core_types import (
    LogLevel,
    MappingToolError,
)


# =============================================================================
# Click Command Line Port Implementation - CLI Interface
# =============================================================================


class ClickCommandLinePort(PortAdapterBase):
    """
    Click-based command line port implementation.

    Provides command-line argument parsing, user input/output, and
    interactive prompts using patterns similar to the click library.
    Maintains backward compatibility with existing CLI functionality.
    """

    def __init__(self, name: str = "ClickCommandLinePort") -> None:
        super().__init__(name)
        self._colored_output = self._check_color_support()
        self._verbose = False

    def _initialize_port(self) -> None:
        """Initialize command line port."""
        # Verify we can access stdout/stderr
        try:
            sys.stdout.write("")
            sys.stderr.write("")
        except Exception as e:
            raise MappingToolError(f"CLI output not available: {e}")

    def parse_arguments(self, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """Parse command-line arguments."""
        try:
            import argparse

            if args is None:
                args = sys.argv[1:]

            parser = argparse.ArgumentParser(
                description="Mapping Tool - Device Analysis and Comparison",
                formatter_class=argparse.RawDescriptionHelpFormatter,
            )

            # Add standard arguments
            parser.add_argument(
                "-i", "--input", type=str, help="Input file path for device data"
            )

            parser.add_argument(
                "-o", "--output", type=str, help="Output file path for results"
            )

            parser.add_argument(
                "-f",
                "--format",
                choices=["json", "markdown", "html", "plain"],
                default="markdown",
                help="Output format (default: markdown)",
            )

            parser.add_argument(
                "-v", "--verbose", action="store_true", help="Enable verbose output"
            )

            parser.add_argument(
                "--log-level",
                choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                default="INFO",
                help="Set logging level (default: INFO)",
            )

            parser.add_argument("--config", type=str, help="Configuration file path")

            parser.add_argument(
                "--cache-size",
                type=int,
                default=128,
                help="Cache size for performance optimization (default: 128)",
            )

            parser.add_argument(
                "--timeout",
                type=float,
                default=300.0,
                help="Operation timeout in seconds (default: 300)",
            )

            # Parse arguments
            parsed_args = parser.parse_args(args)

            # Set verbose mode
            self._verbose = parsed_args.verbose

            # Convert to dictionary
            return vars(parsed_args)

        except SystemExit as e:
            # argparse calls sys.exit() on error or help
            if e.code != 0:
                raise MappingToolError(f"Argument parsing failed: {e}")
            raise
        except Exception as e:
            self._record_error(f"Failed to parse arguments: {e}")
            raise MappingToolError(f"CLI argument error: {e}")

    def print_message(self, message: str, level: LogLevel = "INFO") -> None:
        """Print message to command line with appropriate formatting."""
        try:
            # Format message based on level
            if self._colored_output:
                formatted_message = self._format_colored_message(message, level)
            else:
                formatted_message = self._format_plain_message(message, level)

            # Choose output stream
            if level in ["ERROR", "CRITICAL"]:
                output_stream = sys.stderr
            else:
                output_stream = sys.stdout

            # Print message
            output_stream.write(formatted_message + "\n")
            output_stream.flush()

        except Exception as e:
            self._record_error(f"Failed to print message: {e}")
            # Fallback to basic print
            print(f"[{level}] {message}")

    def print_error(self, error: str) -> None:
        """Print error message to stderr."""
        self.print_message(error, "ERROR")

    def prompt_user(self, question: str, default: Optional[str] = None) -> str:
        """Prompt user for input."""
        try:
            if default:
                prompt = f"{question} [{default}]: "
            else:
                prompt = f"{question}: "

            # Print prompt to stderr to avoid mixing with output
            sys.stderr.write(prompt)
            sys.stderr.flush()

            # Read from stdin
            response = input().strip()

            # Use default if no response
            if not response and default:
                return default

            return response

        except KeyboardInterrupt:
            self.print_message("\nOperation cancelled by user.", "WARNING")
            raise MappingToolError("User cancelled operation")
        except EOFError:
            if default:
                return default
            raise MappingToolError("No user input available")
        except Exception as e:
            self._record_error(f"Failed to prompt user: {e}")
            raise MappingToolError(f"User input error: {e}")

    def confirm_action(self, message: str) -> bool:
        """Ask user for yes/no confirmation."""
        try:
            response = self.prompt_user(f"{message} (y/N)", "n").lower()
            return response.startswith("y")

        except Exception as e:
            self._record_error(f"Failed to get confirmation: {e}")
            return False

    def display_progress(self, current: int, total: int, message: str = "") -> None:
        """Display progress information."""
        try:
            if total <= 0:
                return

            percentage = (current / total) * 100

            # Create progress bar
            bar_width = 40
            filled_width = int(bar_width * current / total)
            bar = "█" * filled_width + "░" * (bar_width - filled_width)

            # Format progress message
            if message:
                progress_text = (
                    f"\r{message} [{bar}] {percentage:5.1f}% ({current}/{total})"
                )
            else:
                progress_text = f"\r[{bar}] {percentage:5.1f}% ({current}/{total})"

            # Write to stderr to avoid mixing with output
            sys.stderr.write(progress_text)
            sys.stderr.flush()

            # Add newline when complete
            if current >= total:
                sys.stderr.write("\n")
                sys.stderr.flush()

        except Exception as e:
            self._record_error(f"Failed to display progress: {e}")

    def print_table(self, headers: List[str], rows: List[List[str]]) -> None:
        """Print formatted table to stdout."""
        try:
            if not headers or not rows:
                return

            # Calculate column widths
            all_rows = [headers] + rows
            col_widths = []

            for col_idx in range(len(headers)):
                max_width = max(
                    len(str(row[col_idx])) for row in all_rows if col_idx < len(row)
                )
                col_widths.append(max_width)

            # Print header
            header_row = " | ".join(
                str(headers[i]).ljust(col_widths[i]) for i in range(len(headers))
            )
            separator = "-+-".join("-" * width for width in col_widths)

            print(header_row)
            print(separator)

            # Print data rows
            for row in rows:
                data_row = " | ".join(
                    (
                        str(row[i]).ljust(col_widths[i])
                        if i < len(row)
                        else " " * col_widths[i]
                    )
                    for i in range(len(headers))
                )
                print(data_row)

        except Exception as e:
            self._record_error(f"Failed to print table: {e}")
            # Fallback to simple print
            print(f"Headers: {headers}")
            for row in rows:
                print(f"Row: {row}")

    def _check_color_support(self) -> bool:
        """Check if terminal supports colored output."""
        try:
            # Check if we're in a terminal
            if not sys.stdout.isatty():
                return False

            # Check for common color support indicators
            import os

            term = os.environ.get("TERM", "").lower()
            colorterm = os.environ.get("COLORTERM", "").lower()

            return (
                "color" in term
                or "xterm" in term
                or "ansi" in term
                or colorterm in ["truecolor", "24bit"]
            )

        except Exception:
            return False

    def _format_colored_message(self, message: str, level: LogLevel) -> str:
        """Format message with color codes."""
        color_codes = {
            "DEBUG": "\033[36m",  # Cyan
            "INFO": "\033[32m",  # Green
            "WARNING": "\033[33m",  # Yellow
            "ERROR": "\033[31m",  # Red
            "CRITICAL": "\033[35m",  # Magenta
        }

        reset_code = "\033[0m"
        color = color_codes.get(level, "")

        if self._verbose:
            timestamp = time.strftime("%H:%M:%S")
            return f"{color}[{timestamp}] [{level}]{reset_code} {message}"
        else:
            return f"{color}[{level}]{reset_code} {message}"

    def _format_plain_message(self, message: str, level: LogLevel) -> str:
        """Format message without color codes."""
        if self._verbose:
            timestamp = time.strftime("%H:%M:%S")
            return f"[{timestamp}] [{level}] {message}"
        else:
            return f"[{level}] {message}"


# =============================================================================
# Structured Logging Port Implementation - Enhanced Logging
# =============================================================================


class StructuredLoggingPort(PortAdapterBase):
    """
    Structured logging port implementation.

    Provides enhanced logging capabilities with structured output,
    context management, and performance timing. Integrates with
    Python's standard logging module.
    """

    def __init__(self, name: str = "StructuredLoggingPort") -> None:
        super().__init__(name)
        self._logger: Optional[logging.Logger] = None
        self._timers: Dict[str, float] = {}
        self._metrics: Dict[str, List[float]] = {}
        self._context: Dict[str, Any] = {}

    def _initialize_port(self) -> None:
        """Initialize logging port."""
        try:
            # Create logger
            self._logger = logging.getLogger("mapping_tool")
            self._logger.setLevel(logging.INFO)

            # Remove existing handlers to avoid duplicates
            self._logger.handlers.clear()

            # Create console handler
            console_handler = logging.StreamHandler(sys.stderr)

            # Create formatter
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            console_handler.setFormatter(formatter)

            # Add handler to logger
            self._logger.addHandler(console_handler)

        except Exception as e:
            raise MappingToolError(f"Failed to initialize logging: {e}")

    def _cleanup_port(self) -> None:
        """Cleanup logging port."""
        if self._logger:
            # Close all handlers
            for handler in self._logger.handlers:
                handler.close()
            self._logger.handlers.clear()

        self._timers.clear()
        self._metrics.clear()
        self._context.clear()

    def log_message(
        self, level: LogLevel, message: str, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log message with specified level and context."""
        try:
            if not self._logger:
                raise MappingToolError("Logger not initialized")

            # Merge context with current context
            full_context = self._context.copy()
            if context:
                full_context.update(context)

            # Create structured message
            if full_context:
                context_str = " | ".join(f"{k}={v}" for k, v in full_context.items())
                structured_message = f"{message} | {context_str}"
            else:
                structured_message = message

            # Log at appropriate level
            log_level = getattr(logging, level.upper(), logging.INFO)
            self._logger.log(log_level, structured_message)

        except Exception as e:
            self._record_error(f"Failed to log message: {e}")
            # Fallback to print
            print(f"[{level}] {message}")

    def log_error(
        self, error: Exception, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log error with stack trace and context."""
        try:
            import traceback

            error_context = {
                "error_type": type(error).__name__,
                "error_message": str(error),
            }

            if context:
                error_context.update(context)

            # Log error message
            self.log_message("ERROR", f"Exception occurred: {error}", error_context)

            # Log stack trace if logger is in debug mode
            if self._logger and self._logger.isEnabledFor(logging.DEBUG):
                stack_trace = traceback.format_exc()
                self.log_message("DEBUG", f"Stack trace:\n{stack_trace}")

        except Exception as e:
            self._record_error(f"Failed to log error: {e}")
            # Fallback to print
            print(f"[ERROR] {error}")

    def start_timing(self, operation_name: str) -> str:
        """Start timing an operation."""
        try:
            timer_id = f"{operation_name}_{int(time.time() * 1000)}"
            self._timers[timer_id] = time.time()

            self.log_message(
                "DEBUG",
                f"Started timing: {operation_name}",
                {"timer_id": timer_id, "operation": operation_name},
            )

            return timer_id

        except Exception as e:
            self._record_error(f"Failed to start timing: {e}")
            return ""

    def end_timing(self, timer_id: str) -> float:
        """End timing and get duration."""
        try:
            if timer_id not in self._timers:
                self.log_message("WARNING", f"Timer not found: {timer_id}")
                return 0.0

            start_time = self._timers[timer_id]
            end_time = time.time()
            duration = end_time - start_time

            # Remove timer
            del self._timers[timer_id]

            # Extract operation name from timer_id
            operation_name = timer_id.rsplit("_", 1)[0]

            # Record metric
            if operation_name not in self._metrics:
                self._metrics[operation_name] = []
            self._metrics[operation_name].append(duration)

            self.log_message(
                "DEBUG",
                f"Completed timing: {operation_name}",
                {
                    "timer_id": timer_id,
                    "duration_seconds": round(duration, 3),
                    "operation": operation_name,
                },
            )

            return duration

        except Exception as e:
            self._record_error(f"Failed to end timing: {e}")
            return 0.0

    def record_metric(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a metric value."""
        try:
            # Store metric
            if name not in self._metrics:
                self._metrics[name] = []
            self._metrics[name].append(value)

            # Create context with tags
            metric_context = {"metric_name": name, "metric_value": value}
            if tags:
                metric_context.update(tags)

            self.log_message(
                "DEBUG", f"Recorded metric: {name} = {value}", metric_context
            )

        except Exception as e:
            self._record_error(f"Failed to record metric: {e}")

    def set_context(self, context: Dict[str, Any]) -> None:
        """Set global context for all log messages."""
        self._context.update(context)

    def clear_context(self) -> None:
        """Clear global context."""
        self._context.clear()

    def get_metrics_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary of recorded metrics."""
        summary = {}

        for name, values in self._metrics.items():
            if values:
                summary[name] = {
                    "count": len(values),
                    "total": sum(values),
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                }
            else:
                summary[name] = {
                    "count": 0,
                    "total": 0.0,
                    "average": 0.0,
                    "min": 0.0,
                    "max": 0.0,
                }

        return summary

    def set_log_level(self, level: LogLevel) -> None:
        """Set the logging level."""
        try:
            if self._logger:
                log_level = getattr(logging, level.upper(), logging.INFO)
                self._logger.setLevel(log_level)

        except Exception as e:
            self._record_error(f"Failed to set log level: {e}")

    def add_file_handler(self, file_path: str) -> None:
        """Add file handler for logging to file."""
        try:
            if not self._logger:
                raise MappingToolError("Logger not initialized")

            # Create file handler
            file_handler = logging.FileHandler(file_path, mode="a", encoding="utf-8")

            # Create formatter
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(formatter)

            # Add handler
            self._logger.addHandler(file_handler)

            self.log_message("INFO", f"Added file logging: {file_path}")

        except Exception as e:
            self._record_error(f"Failed to add file handler: {e}")
            raise MappingToolError(f"File logging setup error: {e}")


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # CLI Implementation
    "ClickCommandLinePort",
    # Logging Implementation
    "StructuredLoggingPort",
]
