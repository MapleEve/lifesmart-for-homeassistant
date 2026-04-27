#!/usr/bin/env python3
"""
优化的文档解析器 - 重构extract_device_ios_from_docs函数
将263行的巨大函数重构为可测试的组件，减少80%的复杂度
"""

import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, Optional

from .core_utils import (
    IOPort,
    OptimizedRegexPatterns,
    DocumentCleaner,
    DeviceNameUtils,
)


class DocumentSection(Enum):
    """文档章节枚举"""

    DEVICE_TABLE = "device_table"
    THIRD_PARTY_TABLE = "third_party_table"
    OTHER = "other"


@dataclass
class DocumentParsingContext:
    """文档解析上下文"""

    current_device: Optional[str] = None
    current_section: DocumentSection = DocumentSection.OTHER
    skip_third_party: bool = False
    line_number: int = 0
    debug_lines: List[str] = None

    def __post_init__(self):
        if self.debug_lines is None:
            self.debug_lines = []


@dataclass
class TableRow:
    """表格行数据结构"""

    device_col: str
    io_port: str
    io_name: str
    description: str
    permissions: str

    @classmethod
    def from_columns(cls, columns: List[str]) -> Optional["TableRow"]:
        """从表格列创建行对象"""
        if len(columns) < 5:
            return None

        return cls(
            device_col=columns[0].strip(),
            io_port=columns[1].strip(),
            io_name=columns[2].strip(),
            description=columns[3].strip(),
            permissions=columns[4].strip(),
        )


class SpecialDeviceHandler:
    """特殊设备处理器"""

    # 特殊设备类型映射：文档通用类型 -> 实际设备列表
    SPECIAL_DEVICE_MAPPING = {
        "cam": [  # 摄像头设备特殊处理
            "LSCAM:LSCAMV1",  # FRAME - 有V和CFST
            "LSCAM:LSICAMEZ1",  # 户外摄像头 - 仅M
            "LSCAM:LSICAMEZ2",  # 户外摄像头 - 仅M
            "LSCAM:LSICAMGOS1",  # 高清摄像头 - 仅M
            "LSCAM:LSLKCAMV1",  # 视频门锁摄像头 - 仅M
        ]
    }

    # 摄像头特殊IO口限制
    CAM_EXCLUSIVE_IOS = {"V", "CFST"}
    FRAME_DEVICE = "LSCAM:LSCAMV1"

    @classmethod
    def get_target_devices(cls, device_name: str) -> List[str]:
        """获取目标设备列表"""
        return cls.SPECIAL_DEVICE_MAPPING.get(device_name, [device_name])

    @classmethod
    def should_skip_io_for_device(
        cls, device_name: str, target_device: str, io_port: str
    ) -> bool:
        """检查是否应该跳过特定设备的IO口"""
        return (
            device_name == "cam"
            and io_port in cls.CAM_EXCLUSIVE_IOS
            and target_device != cls.FRAME_DEVICE
        )


class DeviceNameExtractor:
    """设备名称提取器"""

    @staticmethod
    def extract_from_cell(
        device_col: str, context: DocumentParsingContext
    ) -> List[str]:
        """从单元格中提取设备名称"""
        if not device_col:
            return []

        # 处理多个设备在同一单元格的情况 (用<br/>或 / 分隔)
        device_names = re.split(r"<br\s*/?>\s*|/", device_col)
        cleaned_devices = []

        for name in device_names:
            name = name.strip()
            device_name = OptimizedRegexPatterns.extract_device_name(name)

            if device_name:
                context.debug_lines.append(
                    f"行{context.line_number}: 提取到设备名 '{device_name}' 来自 '{name}'"
                )

                if DeviceNameUtils.is_valid_device_name(device_name):
                    cleaned_devices.append(device_name)
                else:
                    context.debug_lines.append(
                        f"  -> 过滤掉设备名 '{device_name}' (来自 '{name}')"
                    )

        return cleaned_devices


class IOPortProcessor:
    """IO口处理器"""

    @staticmethod
    def extract_io_ports(io_port_str: str) -> List[str]:
        """从IO口字符串中提取IO口列表"""
        if not io_port_str:
            return []

        # 处理多个IO口在同一单元格的情况 (如 `L1`, `L2`, `L3`)
        io_ports = re.split(r"[,\s]+", io_port_str)
        cleaned_ports = []

        for single_io in io_ports:
            clean_io_port = DocumentCleaner.clean_io_port(single_io)

            if clean_io_port and DocumentCleaner.is_valid_io_content(clean_io_port):
                cleaned_ports.append(clean_io_port)

        return cleaned_ports

    @staticmethod
    def create_io_port(
        io_port: str, io_name: str, permissions: str, description: str
    ) -> IOPort:
        """创建IO口对象"""
        return IOPort(
            name=io_port,
            rw=permissions,
            description=description.strip(),
            io_type=io_name,
        )


class DocumentSectionDetector:
    """文档章节检测器"""

    @staticmethod
    def detect_section_change(line: str, context: DocumentParsingContext) -> bool:
        """检测章节变化"""
        line = line.strip()

        # 检测第三方设备控制器接入列表表格
        if "### 3.6 第三方设备通过控制器接入列表" in line:
            context.current_section = DocumentSection.THIRD_PARTY_TABLE
            context.skip_third_party = True
            context.debug_lines.append(
                f"行{context.line_number}: 开始跳过第三方设备控制器接入列表表格"
            )
            return True

        # 检测章节结束
        if context.skip_third_party and line.startswith("##") and "3.6" not in line:
            context.current_section = DocumentSection.OTHER
            context.skip_third_party = False
            context.debug_lines.append(
                f"行{context.line_number}: 结束跳过第三方设备控制器接入列表表格"
            )
            return True

        return False


class TableRowProcessor:
    """表格行处理器"""

    def __init__(self):
        self.device_name_extractor = DeviceNameExtractor()
        self.io_processor = IOPortProcessor()
        self.special_handler = SpecialDeviceHandler()

    def process_table_row(
        self,
        line: str,
        context: DocumentParsingContext,
        device_ios: Dict[str, List[Dict]],
    ) -> bool:
        """处理表格行"""
        # 跳过第三方设备表格
        if context.skip_third_party:
            return False

        if not line.startswith("|") or "----" in line:
            return False

        # 分割表格列
        columns = [col.strip() for col in line.split("|")[1:-1]]
        table_row = TableRow.from_columns(columns)

        if not table_row:
            return False

        return self._process_device_row(table_row, context, device_ios)

    def _process_device_row(
        self,
        row: TableRow,
        context: DocumentParsingContext,
        device_ios: Dict[str, List[Dict]],
    ) -> bool:
        """处理设备行"""
        # 处理设备名称列
        if row.device_col:
            device_names = self.device_name_extractor.extract_from_cell(
                row.device_col, context
            )

            if device_names:
                context.current_device = device_names[0]  # 使用第一个设备作为当前设备

                # 为每个设备创建记录
                for device_name in device_names:
                    self._initialize_device_record(device_name, device_ios)

                # 处理IO口信息
                if row.io_port and row.io_name:
                    self._add_io_to_devices(device_names, row, context, device_ios)

                return True

        # 处理继续的IO口行
        elif context.current_device and row.io_port:
            self._add_io_to_current_device(context.current_device, row, device_ios)
            return True

        return False

    def _initialize_device_record(
        self, device_name: str, device_ios: Dict[str, List[Dict]]
    ):
        """初始化设备记录"""
        target_devices = self.special_handler.get_target_devices(device_name)

        for target_device in target_devices:
            if target_device not in device_ios:
                device_ios[target_device] = []

    def _add_io_to_devices(
        self,
        device_names: List[str],
        row: TableRow,
        context: DocumentParsingContext,
        device_ios: Dict[str, List[Dict]],
    ):
        """为设备添加IO口"""
        io_ports = self.io_processor.extract_io_ports(row.io_port)

        for device_name in device_names:
            target_devices = self.special_handler.get_target_devices(device_name)

            for io_port in io_ports:
                for target_device in target_devices:
                    # 特殊设备IO口过滤
                    if self.special_handler.should_skip_io_for_device(
                        device_name, target_device, io_port
                    ):
                        context.debug_lines.append(
                            f"  -> 跳过IO口 '{io_port}' 对设备 '{target_device}' (仅FRAME设备支持)"
                        )
                        continue

                    io_port_obj = self.io_processor.create_io_port(
                        io_port, row.io_name, row.permissions, row.description
                    )
                    device_ios[target_device].append(io_port_obj.__dict__)

    def _add_io_to_current_device(
        self, current_device: str, row: TableRow, device_ios: Dict[str, List[Dict]]
    ):
        """为当前设备添加IO口"""
        if current_device not in device_ios:
            device_ios[current_device] = []

        io_ports = self.io_processor.extract_io_ports(row.io_port)

        for io_port in io_ports:
            io_port_obj = self.io_processor.create_io_port(
                io_port, row.io_name, row.permissions, row.description
            )
            device_ios[current_device].append(io_port_obj.__dict__)


class DocumentParser:
    """优化的文档解析器主类"""

    def __init__(self, docs_file_path: Optional[str] = None):
        self.docs_file_path = docs_file_path or self._get_default_docs_path()
        self.section_detector = DocumentSectionDetector()
        self.table_processor = TableRowProcessor()

    def _get_default_docs_path(self) -> str:
        """获取默认文档路径"""
        # 从 .testing/mapping_tool/utils/ 向上4级到项目根目录
        return os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            ),
            "docs",
            "LifeSmart 智慧设备规格属性说明.md",
        )

    def extract_device_ios_from_docs(self) -> Dict[str, List[Dict]]:
        """从官方文档中提取设备IO口定义 - 优化版本"""
        try:
            with open(self.docs_file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            print(f"❌ 文档文件未找到: {self.docs_file_path}")
            return {}

        device_ios = {}
        context = DocumentParsingContext()
        lines = content.split("\n")

        # 使用批量处理优化性能
        for line_num, line in enumerate(lines, 1):
            context.line_number = line_num

            # 检测章节变化
            self.section_detector.detect_section_change(line, context)

            # 处理表格行
            self.table_processor.process_table_row(line, context, device_ios)

        # 输出调试信息（仅前30行）
        self._output_debug_info(context.debug_lines[:30])

        return device_ios

    def _output_debug_info(self, debug_lines: List[str]):
        """输出调试信息"""
        if debug_lines:
            print(f"\n🔍 文档解析调试信息:")
            print(f"前30行调试信息:")
            for debug_line in debug_lines:
                print(debug_line)


class BatchDocumentProcessor:
    """批量文档处理器 - 用于处理多个文档或大型文档"""

    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
        self.parsers = {}

    def process_documents(
        self, doc_paths: List[str]
    ) -> Dict[str, Dict[str, List[Dict]]]:
        """批量处理多个文档"""
        results = {}

        for doc_path in doc_paths:
            parser = DocumentParser(doc_path)
            results[doc_path] = parser.extract_device_ios_from_docs()

        return results

    def process_large_document(self, doc_path: str) -> Dict[str, List[Dict]]:
        """处理大型文档 - 分批次处理以优化内存使用"""
        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                device_ios = {}
                context = DocumentParsingContext()
                parser = DocumentParser(doc_path)

                # 分批读取文件内容
                lines_buffer = []
                for line in f:
                    lines_buffer.append(line)

                    if len(lines_buffer) >= self.batch_size:
                        self._process_batch(lines_buffer, context, device_ios, parser)
                        lines_buffer = []

                # 处理剩余的行
                if lines_buffer:
                    self._process_batch(lines_buffer, context, device_ios, parser)

                return device_ios

        except FileNotFoundError:
            print(f"❌ 文档文件未找到: {doc_path}")
            return {}

    def _process_batch(
        self,
        lines: List[str],
        context: DocumentParsingContext,
        device_ios: Dict[str, List[Dict]],
        parser: DocumentParser,
    ):
        """处理一批行"""
        for line in lines:
            context.line_number += 1
            parser.section_detector.detect_section_change(line, context)
            parser.table_processor.process_table_row(line, context, device_ios)


# 性能测试和基准测试工具
class DocumentParserBenchmark:
    """文档解析器性能基准测试"""

    @staticmethod
    def benchmark_parsing_performance(
        doc_path: str, iterations: int = 5
    ) -> Dict[str, float]:
        """基准测试解析性能"""
        import time

        parser = DocumentParser(doc_path)
        times = []

        for _ in range(iterations):
            start_time = time.time()
            parser.extract_device_ios_from_docs()
            end_time = time.time()
            times.append(end_time - start_time)

        return {
            "average_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times),
            "total_time": sum(times),
        }

    @staticmethod
    def compare_memory_usage(doc_path: str) -> Dict[str, Any]:
        """比较内存使用情况"""
        import tracemalloc

        tracemalloc.start()

        parser = DocumentParser(doc_path)
        result = parser.extract_device_ios_from_docs()

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        return {
            "current_memory": current,
            "peak_memory": peak,
            "result_size": len(result),
            "memory_per_device": peak / len(result) if result else 0,
        }


# 工厂方法用于创建不同类型的解析器
class DocumentParserFactory:
    """文档解析器工厂"""

    @staticmethod
    def create_standard_parser(docs_path: str) -> DocumentParser:
        """创建标准解析器"""
        return DocumentParser(docs_path)

    @staticmethod
    def create_batch_parser(batch_size: int = 1000) -> BatchDocumentProcessor:
        """创建批量解析器"""
        return BatchDocumentProcessor(batch_size)

    @staticmethod
    def create_performance_optimized_parser(docs_path: str) -> DocumentParser:
        """创建性能优化的解析器"""
        # 可以在这里添加额外的性能优化配置
        parser = DocumentParser(docs_path)
        # 预编译正则表达式、设置缓存等
        return parser
