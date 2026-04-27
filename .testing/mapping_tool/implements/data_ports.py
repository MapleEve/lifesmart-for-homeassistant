"""
Data Processing Port Implementations

This module provides implementations for data source and report generation ports.
These ports handle business logic integration for loading device data and
generating various output formats.

Implementation Strategy:
- CSVDataSourcePort: Device data loading from CSV and structured sources
- MarkdownReportPort: Report generation in multiple formats
- AsyncDataSourcePort: Asynchronous data loading for large datasets

Author: Architecture Implementation Agent
Date: 2025-08-15
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Import architecture interfaces
from ..architecture.ports import (
    DataSourcePort,
    ReportPort,
    AsyncFilePort,
)

# Import base classes
from .port_implementations import PortAdapterBase

# Import core types
from ..data_types.core_types import (
    DeviceData,
    AnalysisResult,
    ReportData,
    FilePath,
    ReportFormat,
    DevicePlatform,
    create_timestamp,
    MappingToolError,
)


# =============================================================================
# CSV Data Source Port Implementation - Device Data Loading
# =============================================================================


class CSVDataSourcePort(PortAdapterBase):
    """
    CSV-based data source port implementation.

    Handles loading device data from CSV files and other structured
    data sources. Provides validation and transformation of device data
    into the standard DeviceData format.
    """

    def __init__(self, name: str = "CSVDataSourcePort") -> None:
        super().__init__(name)
        self._supported_formats = [".csv", ".json", ".txt"]
        self._device_cache: Dict[str, List[DeviceData]] = {}

    def _initialize_port(self) -> None:
        """Initialize data source port."""
        # Verify CSV module is available
        try:
            csv.reader([])
        except Exception as e:
            raise MappingToolError(f"CSV module not available: {e}")

    def _cleanup_port(self) -> None:
        """Cleanup data source port."""
        self._device_cache.clear()

    def load_device_data(self, source_identifier: str) -> List[DeviceData]:
        """Load device data from CSV or JSON source."""
        try:
            source_path = Path(source_identifier)

            if not source_path.exists():
                raise MappingToolError(f"Data source not found: {source_identifier}")

            # Check cache first
            cache_key = str(source_path.absolute())
            if cache_key in self._device_cache:
                return self._device_cache[cache_key]

            # Load based on file extension
            extension = source_path.suffix.lower()

            if extension == ".csv":
                devices = self._load_csv_data(source_path)
            elif extension == ".json":
                devices = self._load_json_data(source_path)
            else:
                raise MappingToolError(f"Unsupported data format: {extension}")

            # Cache the loaded data
            self._device_cache[cache_key] = devices
            return devices

        except Exception as e:
            self._record_error(
                f"Failed to load device data from {source_identifier}: {e}"
            )
            if isinstance(e, MappingToolError):
                raise
            raise MappingToolError(f"Data source error: {e}")

    def save_device_data(self, devices: List[DeviceData], destination: str) -> None:
        """Save device data to CSV or JSON destination."""
        try:
            dest_path = Path(destination)
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            extension = dest_path.suffix.lower()

            if extension == ".csv":
                self._save_csv_data(devices, dest_path)
            elif extension == ".json":
                self._save_json_data(devices, dest_path)
            else:
                raise MappingToolError(f"Unsupported save format: {extension}")

        except Exception as e:
            self._record_error(f"Failed to save device data to {destination}: {e}")
            raise MappingToolError(f"Data save error: {e}")

    def validate_source(self, source_identifier: str) -> bool:
        """Validate that data source is accessible and valid."""
        try:
            source_path = Path(source_identifier)

            if not source_path.exists():
                return False

            if not source_path.is_file():
                return False

            extension = source_path.suffix.lower()
            if extension not in self._supported_formats:
                return False

            # Try to load a small sample to validate format
            try:
                if extension == ".csv":
                    with open(source_path, "r", encoding="utf-8") as f:
                        reader = csv.reader(f)
                        next(reader)  # Try to read header
                elif extension == ".json":
                    import json

                    with open(source_path, "r", encoding="utf-8") as f:
                        json.load(f)  # Try to parse JSON

                return True

            except Exception:
                return False

        except Exception:
            return False

    def get_source_metadata(self, source_identifier: str) -> Dict[str, Any]:
        """Get metadata about data source."""
        try:
            source_path = Path(source_identifier)

            if not source_path.exists():
                return {}

            stat = source_path.stat()

            metadata = {
                "file_size": stat.st_size,
                "modified_time": stat.st_mtime,
                "file_format": source_path.suffix.lower(),
                "absolute_path": str(source_path.absolute()),
                "is_cached": str(source_path.absolute()) in self._device_cache,
            }

            # Add format-specific metadata
            if source_path.suffix.lower() == ".csv":
                metadata.update(self._get_csv_metadata(source_path))

            return metadata

        except Exception as e:
            self._record_error(f"Failed to get metadata for {source_identifier}: {e}")
            return {}

    def _load_csv_data(self, file_path: Path) -> List[DeviceData]:
        """Load device data from CSV file."""
        devices = []

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=1):
                try:
                    device = self._csv_row_to_device(row, row_num)
                    if device:
                        devices.append(device)
                except Exception as e:
                    self._record_error(f"Failed to parse CSV row {row_num}: {e}")
                    continue

        return devices

    def _load_json_data(self, file_path: Path) -> List[DeviceData]:
        """Load device data from JSON file."""
        import json

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        devices = []

        if isinstance(data, list):
            # Array of device objects
            for i, item in enumerate(data):
                try:
                    device = self._json_item_to_device(item, i)
                    if device:
                        devices.append(device)
                except Exception as e:
                    self._record_error(f"Failed to parse JSON item {i}: {e}")
                    continue
        elif isinstance(data, dict):
            # Single device or devices object
            if "devices" in data:
                return self._load_json_data_from_dict(data["devices"])
            else:
                device = self._json_item_to_device(data, 0)
                if device:
                    devices.append(device)

        return devices

    def _csv_row_to_device(
        self, row: Dict[str, str], row_num: int
    ) -> Optional[DeviceData]:
        """Convert CSV row to DeviceData."""
        try:
            # Required fields
            device_id = row.get("device_id", f"device_{row_num}")
            device_name = row.get("device_name", row.get("name", ""))

            if not device_name:
                return None

            # Parse platform
            platform_str = row.get("platform", "unknown").lower()
            try:
                platform = DevicePlatform(platform_str)
            except ValueError:
                platform = DevicePlatform.UNKNOWN

            # Parse IO ports from string representation
            io_ports = {}
            io_ports_str = row.get("io_ports", "{}")

            try:
                if io_ports_str.startswith("{"):
                    import json

                    io_ports = json.loads(io_ports_str)
                else:
                    # Simple comma-separated format like "P1,P2,P3"
                    if io_ports_str.strip():
                        ports = [p.strip() for p in io_ports_str.split(",")]
                        io_ports = {i: port for i, port in enumerate(ports)}
            except Exception:
                io_ports = {}

            # Parse metadata
            metadata = {}
            for key, value in row.items():
                if key not in [
                    "device_id",
                    "device_name",
                    "name",
                    "platform",
                    "io_ports",
                ]:
                    metadata[key] = value

            return DeviceData(
                device_id=device_id,
                device_name=device_name,
                platform=platform,
                io_ports=io_ports,
                metadata=metadata,
                created_at=create_timestamp(),
                updated_at=None,
            )

        except Exception as e:
            raise MappingToolError(f"Failed to convert CSV row to device: {e}")

    def _json_item_to_device(
        self, item: Dict[str, Any], index: int
    ) -> Optional[DeviceData]:
        """Convert JSON item to DeviceData."""
        try:
            device_id = item.get("device_id", f"device_{index}")
            device_name = item.get("device_name", item.get("name", ""))

            if not device_name:
                return None

            # Parse platform
            platform_str = item.get("platform", "unknown")
            if isinstance(platform_str, str):
                try:
                    platform = DevicePlatform(platform_str.lower())
                except ValueError:
                    platform = DevicePlatform.UNKNOWN
            else:
                platform = DevicePlatform.UNKNOWN

            # IO ports should already be in correct format
            io_ports = item.get("io_ports", {})
            if not isinstance(io_ports, dict):
                io_ports = {}

            # Extract metadata
            metadata = item.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}

            return DeviceData(
                device_id=device_id,
                device_name=device_name,
                platform=platform,
                io_ports=io_ports,
                metadata=metadata,
                created_at=create_timestamp(),
                updated_at=None,
            )

        except Exception as e:
            raise MappingToolError(f"Failed to convert JSON item to device: {e}")

    def _save_csv_data(self, devices: List[DeviceData], file_path: Path) -> None:
        """Save device data to CSV file."""
        if not devices:
            return

        # Determine all unique fields for CSV header
        all_fields = set(["device_id", "device_name", "platform", "io_ports"])
        for device in devices:
            all_fields.update(device.get("metadata", {}).keys())

        fieldnames = sorted(all_fields)

        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for device in devices:
                row = {
                    "device_id": device["device_id"],
                    "device_name": device["device_name"],
                    "platform": (
                        device["platform"].value
                        if hasattr(device["platform"], "value")
                        else str(device["platform"])
                    ),
                    "io_ports": str(device["io_ports"]) if device["io_ports"] else "{}",
                }

                # Add metadata fields
                metadata = device.get("metadata", {})
                for field in fieldnames:
                    if field not in row and field in metadata:
                        row[field] = str(metadata[field])

                writer.writerow(row)

    def _save_json_data(self, devices: List[DeviceData], file_path: Path) -> None:
        """Save device data to JSON file."""
        import json

        # Convert devices to JSON-serializable format
        json_devices = []
        for device in devices:
            json_device = dict(device)
            # Convert enum to string
            if hasattr(json_device["platform"], "value"):
                json_device["platform"] = json_device["platform"].value
            # Convert timestamp to ISO string
            if json_device.get("created_at"):
                json_device["created_at"] = json_device["created_at"].isoformat()
            if json_device.get("updated_at"):
                json_device["updated_at"] = json_device["updated_at"].isoformat()

            json_devices.append(json_device)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(json_devices, f, indent=2, ensure_ascii=False)

    def _get_csv_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Get CSV-specific metadata."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = next(reader, [])

                row_count = sum(1 for _ in reader)

                return {
                    "column_count": len(header),
                    "row_count": row_count,
                    "columns": header,
                }
        except Exception:
            return {}


# =============================================================================
# Markdown Report Port Implementation - Report Generation
# =============================================================================


class MarkdownReportPort(PortAdapterBase):
    """
    Markdown-based report port implementation.

    Handles generation of analysis reports in multiple formats including
    Markdown, HTML, plain text, and JSON. Provides template-based formatting.
    """

    def __init__(self, name: str = "MarkdownReportPort") -> None:
        super().__init__(name)
        self._supported_formats = [
            ReportFormat.MARKDOWN,
            ReportFormat.HTML,
            ReportFormat.PLAIN_TEXT,
            ReportFormat.JSON,
        ]

    def _initialize_port(self) -> None:
        """Initialize report port."""
        # No special initialization required
        pass

    def generate_text_report(
        self, data: AnalysisResult, template: Optional[str] = None
    ) -> str:
        """Generate plain text report from analysis results."""
        try:
            if template:
                return self._apply_template(data, template)
            else:
                return self._generate_default_text_report(data)

        except Exception as e:
            self._record_error(f"Failed to generate text report: {e}")
            raise MappingToolError(f"Text report generation error: {e}")

    def generate_json_report(self, data: AnalysisResult) -> Dict[str, Any]:
        """Generate JSON report from analysis results."""
        try:
            import json

            # Convert AnalysisResult to JSON-serializable format
            json_data = dict(data)

            # Handle timestamp conversion
            if "created_at" in json_data and json_data["created_at"]:
                json_data["created_at"] = json_data["created_at"].isoformat()

            # Handle enum conversion
            if "status" in json_data and hasattr(json_data["status"], "value"):
                json_data["status"] = json_data["status"].value

            return json_data

        except Exception as e:
            self._record_error(f"Failed to generate JSON report: {e}")
            raise MappingToolError(f"JSON report generation error: {e}")

    def generate_markdown_report(self, data: AnalysisResult) -> str:
        """Generate Markdown report from analysis results."""
        try:
            md_lines = []

            # Title
            md_lines.append(f"# Analysis Report")
            md_lines.append("")

            # Summary
            md_lines.append("## Summary")
            md_lines.append(f"- **Status**: {data['status']}")
            md_lines.append(f"- **Device Count**: {data['device_count']}")
            md_lines.append(
                f"- **Processing Time**: {data['processing_time_seconds']:.2f} seconds"
            )
            md_lines.append(f"- **Created**: {data['created_at']}")
            md_lines.append("")

            if data.get("summary"):
                md_lines.append(f"**Description**: {data['summary']}")
                md_lines.append("")

            # Comparisons
            if data.get("comparisons"):
                md_lines.append("## Device Comparisons")
                md_lines.append("")

                for i, comparison in enumerate(data["comparisons"], 1):
                    md_lines.append(f"### Comparison {i}")
                    md_lines.append(
                        f"- **Devices**: {comparison['device_a']} vs {comparison['device_b']}"
                    )
                    md_lines.append(
                        f"- **Similarity**: {comparison['similarity_score']:.2%}"
                    )
                    md_lines.append(f"- **Confidence**: {comparison['confidence']:.2%}")

                    if comparison.get("differences"):
                        md_lines.append("- **Differences**:")
                        for diff in comparison["differences"]:
                            md_lines.append(f"  - {diff}")

                    if comparison.get("recommendations"):
                        md_lines.append("- **Recommendations**:")
                        for rec in comparison["recommendations"]:
                            md_lines.append(f"  - {rec}")

                    md_lines.append("")

            # Metadata
            if data.get("metadata"):
                md_lines.append("## Additional Information")
                md_lines.append("")
                for key, value in data["metadata"].items():
                    md_lines.append(f"- **{key.title()}**: {value}")
                md_lines.append("")

            return "\n".join(md_lines)

        except Exception as e:
            self._record_error(f"Failed to generate Markdown report: {e}")
            raise MappingToolError(f"Markdown report generation error: {e}")

    def generate_html_report(
        self, data: AnalysisResult, style_template: Optional[str] = None
    ) -> str:
        """Generate HTML report from analysis results."""
        try:
            # Convert Markdown to HTML (simple conversion)
            markdown_content = self.generate_markdown_report(data)
            html_content = self._markdown_to_html(markdown_content)

            # Wrap in HTML document
            style = style_template or self._get_default_css()

            html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analysis Report</title>
    <style>
{style}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""

            return html_doc

        except Exception as e:
            self._record_error(f"Failed to generate HTML report: {e}")
            raise MappingToolError(f"HTML report generation error: {e}")

    def save_report(
        self, report_content: str, output_path: FilePath, format: ReportFormat
    ) -> ReportData:
        """Save report content to file."""
        try:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Ensure file extension matches format
            if format == ReportFormat.MARKDOWN and not output_file.suffix:
                output_file = output_file.with_suffix(".md")
            elif format == ReportFormat.HTML and not output_file.suffix:
                output_file = output_file.with_suffix(".html")
            elif format == ReportFormat.JSON and not output_file.suffix:
                output_file = output_file.with_suffix(".json")
            elif format == ReportFormat.PLAIN_TEXT and not output_file.suffix:
                output_file = output_file.with_suffix(".txt")

            # Write content to file
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(report_content)

            # Create report metadata
            report_data = ReportData(
                title="Analysis Report",
                analysis_result={},  # Will be filled by caller
                format=format,
                generated_at=create_timestamp(),
                version="1.0",
                author="Mapping Tool",
            )

            return report_data

        except Exception as e:
            self._record_error(f"Failed to save report to {output_path}: {e}")
            raise MappingToolError(f"Report save error: {e}")

    def get_supported_formats(self) -> List[ReportFormat]:
        """Get list of supported report formats."""
        return self._supported_formats.copy()

    def _generate_default_text_report(self, data: AnalysisResult) -> str:
        """Generate default plain text report."""
        lines = []

        lines.append("ANALYSIS REPORT")
        lines.append("=" * 50)
        lines.append("")

        lines.append(f"Status: {data['status']}")
        lines.append(f"Device Count: {data['device_count']}")
        lines.append(f"Processing Time: {data['processing_time_seconds']:.2f} seconds")
        lines.append(f"Created: {data['created_at']}")
        lines.append("")

        if data.get("summary"):
            lines.append(f"Summary: {data['summary']}")
            lines.append("")

        if data.get("comparisons"):
            lines.append("DEVICE COMPARISONS")
            lines.append("-" * 30)

            for i, comparison in enumerate(data["comparisons"], 1):
                lines.append(f"Comparison {i}:")
                lines.append(
                    f"  Devices: {comparison['device_a']} vs {comparison['device_b']}"
                )
                lines.append(f"  Similarity: {comparison['similarity_score']:.2%}")
                lines.append(f"  Confidence: {comparison['confidence']:.2%}")
                lines.append("")

        return "\n".join(lines)

    def _apply_template(self, data: AnalysisResult, template: str) -> str:
        """Apply template to analysis data."""
        # Simple template substitution
        result = template

        replacements = {
            "{status}": str(data.get("status", "")),
            "{device_count}": str(data.get("device_count", 0)),
            "{processing_time}": f"{data.get('processing_time_seconds', 0):.2f}",
            "{created_at}": str(data.get("created_at", "")),
            "{summary}": data.get("summary", ""),
        }

        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)

        return result

    def _markdown_to_html(self, markdown: str) -> str:
        """Simple Markdown to HTML conversion."""
        html = markdown

        # Headers
        html = html.replace("# ", "<h1>").replace("\n", "</h1>\n", 1)
        html = html.replace("## ", "<h2>").replace("\n", "</h2>\n", 1)
        html = html.replace("### ", "<h3>").replace("\n", "</h3>\n", 1)

        # Bold text
        import re

        html = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", html)

        # Lists
        lines = html.split("\n")
        html_lines = []
        in_list = False

        for line in lines:
            if line.strip().startswith("- "):
                if not in_list:
                    html_lines.append("<ul>")
                    in_list = True
                item = line.strip()[2:]  # Remove '- '
                html_lines.append(f"  <li>{item}</li>")
            else:
                if in_list:
                    html_lines.append("</ul>")
                    in_list = False
                if line.strip():
                    html_lines.append(f"<p>{line}</p>")
                else:
                    html_lines.append("")

        if in_list:
            html_lines.append("</ul>")

        return "\n".join(html_lines)

    def _get_default_css(self) -> str:
        """Get default CSS styling for HTML reports."""
        return """
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1, h2, h3 {
            color: #333;
        }
        h1 {
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
        }
        ul {
            padding-left: 20px;
        }
        li {
            margin-bottom: 5px;
        }
        strong {
            color: #555;
        }
        """


# =============================================================================
# Module Exports
# =============================================================================

__all__ = [
    # Data Source Implementations
    "CSVDataSourcePort",
    # Report Generation Implementations
    "MarkdownReportPort",
]
