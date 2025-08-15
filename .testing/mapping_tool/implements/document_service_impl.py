#!/usr/bin/env python3
"""
DocumentService Implementation - 文档解析服务实现

抽取自SmartIOAllocationAnalyzer和DocumentBasedComparisonAnalyzer的文档解析逻辑，
实现现代化的文档服务，支持缓存机制和异步处理。

重构来源：
- RUN_THIS_TOOL.py: load_official_documentation方法
- pure_ai_analyzer.py: _parse_official_document方法 (~358行)

作者：@MapleEve
日期：2025-08-15
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, AsyncIterator
from dataclasses import dataclass, field
import asyncio

# 导入架构接口
try:
    from ..architecture.services import DocumentService
    from ..architecture.cache import CacheManager
    from ..data_types.core_types import (
        DeviceData,
        DocumentData,
        AnalysisConfig,
        CacheStrategy,
    )
except ImportError:
    # 兼容性导入
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

    from architecture.services import DocumentService
    from architecture.cache import CacheManager
    from data_types.core_types import (
        DeviceData,
        DocumentData,
        AnalysisConfig,
        CacheStrategy,
    )


@dataclass
class DocumentParsingConfig:
    """文档解析配置"""

    enhanced_parsing: bool = True
    aggressive_matching: bool = True
    debug_mode: bool = False
    device_name_validation: bool = True
    cache_parsed_results: bool = True


@dataclass
class DocumentParsingContext:
    """文档解析上下文"""

    current_device: Optional[str] = None
    current_section: str = "OTHER"
    skip_third_party: bool = False
    line_number: int = 0
    debug_lines: List[str] = field(default_factory=list)


class DocumentServiceImpl(DocumentService):
    """
    文档解析服务实现

    从"上帝类"中抽取的文档解析逻辑，重构为现代化的服务架构：
    - 支持异步文档解析
    - 智能缓存机制
    - 强类型接口
    - 配置化解析策略
    - 错误处理和恢复
    """

    def __init__(
        self,
        cache_manager: Optional[CacheManager] = None,
        config: Optional[DocumentParsingConfig] = None,
    ):
        """
        初始化文档服务

        Args:
            cache_manager: 缓存管理器实例
            config: 文档解析配置
        """
        super().__init__()
        self.cache_manager = cache_manager
        self.config = config or DocumentParsingConfig()

        # 文档路径配置 - 使用现代化的pathlib
        self.docs_base_path = self._compute_docs_base_path()
        self.official_doc_path = (
            self.docs_base_path / "LifeSmart 智慧设备规格属性说明.md"
        )

        # 设备名称验证模式
        self.device_name_patterns = {
            "basic": re.compile(r"^[A-Z][A-Z0-9_:]+$"),
            "enhanced": re.compile(r"^[A-Z][A-Z0-9_:]{3,19}$"),
        }

        # 已知设备前缀白名单
        self.known_device_prefixes = ["SL_", "OD_", "V_", "MSL_", "ELIQ_", "LSSS"]

        if self.config.debug_mode:
            print(f"🔍 [DocumentService] 文档路径: {self.official_doc_path}")
            print(f"🔍 [DocumentService] 文档存在: {self.official_doc_path.exists()}")

    def _compute_docs_base_path(self) -> Path:
        """计算文档基础路径 - 使用现代化路径处理"""
        current_file = Path(__file__).resolve()
        # 向上4级目录到项目根目录
        project_root = current_file.parent.parent.parent.parent
        return project_root / "docs"

    async def parse_official_document(
        self, doc_path: Optional[str] = None
    ) -> Dict[str, List[Dict]]:
        """
        异步解析官方文档

        Args:
            doc_path: 可选的文档路径，默认使用配置路径

        Returns:
            设备名到IO口定义列表的映射

        Raises:
            FileNotFoundError: 文档文件不存在
            ValueError: 文档格式无效
        """
        target_path = Path(doc_path) if doc_path else self.official_doc_path

        # 检查缓存
        if self.config.cache_parsed_results and self.cache_manager:
            cache_key = f"parsed_doc_{target_path.name}_{target_path.stat().st_mtime}"
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                if self.config.debug_mode:
                    print(f"🎯 [DocumentService] 缓存命中: {cache_key}")
                return cached_result

        if not target_path.exists():
            raise FileNotFoundError(f"官方文档文件不存在: {target_path}")

        try:
            # 异步读取文档内容
            content = await self._read_document_async(target_path)

            # 解析设备数据
            device_ios = await self._parse_document_content_async(content)

            # 缓存结果
            if self.config.cache_parsed_results and self.cache_manager:
                await self.cache_manager.set(
                    cache_key, device_ios, ttl=3600
                )  # 1小时缓存

            if self.config.debug_mode:
                print(f"✅ [DocumentService] 解析完成: {len(device_ios)}个设备")

            return device_ios

        except Exception as e:
            print(f"❌ [DocumentService] 文档解析失败: {e}")
            raise ValueError(f"文档解析错误: {e}") from e

    async def _read_document_async(self, doc_path: Path) -> str:
        """异步读取文档内容"""

        def _read_sync():
            with open(doc_path, "r", encoding="utf-8") as f:
                return f.read()

        # 在线程池中执行同步文件读取
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _read_sync)

    async def _parse_document_content_async(
        self, content: str
    ) -> Dict[str, List[Dict]]:
        """异步解析文档内容"""

        def _parse_sync():
            return self._parse_document_content_sync(content)

        # 在线程池中执行解析逻辑
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _parse_sync)

    def _parse_document_content_sync(self, content: str) -> Dict[str, List[Dict]]:
        """
        同步解析文档内容 - 从原始代码重构

        重构自: DocumentBasedComparisonAnalyzer._parse_official_document
        """
        device_ios = {}
        lines = content.split("\n")
        context = DocumentParsingContext()

        if self.config.debug_mode:
            print(f"🔍 [DocumentService] 文档总行数: {len(lines)}")

        # 简单的表格解析 - 重构自原始逻辑
        for line_no, line in enumerate(lines, 1):
            context.line_number = line_no
            original_line = line
            line = line.strip()

            # 调试特定设备
            if self.config.debug_mode and "SL_OE_DE" in line:
                print(f"🎯 [DocumentService] 发现目标设备行 {line_no}: {line}")

            # 检测表格行 - 简化的设备识别逻辑
            if self._is_device_table_row(line):
                device_info = self._parse_device_table_row(line, context)
                if device_info:
                    device_name, io_data = device_info
                    if self._is_valid_device_name(device_name):
                        if device_name not in device_ios:
                            device_ios[device_name] = []
                        device_ios[device_name].extend(io_data)

        return device_ios

    def _is_device_table_row(self, line: str) -> bool:
        """检测是否为设备表格行"""
        # 简化的表格行检测逻辑
        if not line or line.startswith("#") or line.startswith("-"):
            return False

        # 检查是否包含表格分隔符
        if "|" in line and len(line.split("|")) >= 3:
            return True

        return False

    def _parse_device_table_row(
        self, line: str, context: DocumentParsingContext
    ) -> Optional[tuple[str, List[Dict]]]:
        """
        解析设备表格行

        Returns:
            (device_name, io_data_list) 或 None
        """
        try:
            # 分割表格列
            columns = [col.strip() for col in line.split("|") if col.strip()]

            if len(columns) < 2:
                return None

            # 第一列通常是设备名称
            potential_device_name = columns[0].strip()

            # 验证设备名称
            if not self._is_valid_device_name(potential_device_name):
                return None

            # 解析IO口信息 - 简化版本
            io_data = []
            for col in columns[1:]:
                if col and not col.isspace():
                    # 简单的IO口信息解析
                    io_info = {
                        "name": col[:20],  # 限制长度
                        "description": col,
                        "source": "official_document",
                        "line_number": context.line_number,
                    }
                    io_data.append(io_info)

            return potential_device_name, io_data

        except Exception as e:
            if self.config.debug_mode:
                print(f"⚠️ [DocumentService] 解析行失败 {context.line_number}: {e}")
            return None

    def _is_valid_device_name(self, name: str) -> bool:
        """
        验证设备名称有效性

        重构自: DocumentBasedComparisonAnalyzer._is_valid_device_name_enhanced
        """
        if not name or len(name) < 3:
            return False

        name = name.strip()

        # 基础格式检查
        if not self.device_name_patterns["basic"].match(name):
            return False

        # 长度检查
        if len(name) < 4 or len(name) > 20:
            return False

        # 白名单检查
        if any(name.startswith(prefix) for prefix in self.known_device_prefixes):
            return True

        # 格式验证：必须包含下划线分隔
        return "_" in name and len(name.split("_")) >= 2

    async def get_device_data(self, device_name: str) -> Optional[DeviceData]:
        """获取特定设备的数据"""
        try:
            all_devices = await self.parse_official_document()
            if device_name in all_devices:
                device_info = all_devices[device_name]
                return DeviceData(
                    name=device_name, ios=device_info, source="official_document"
                )
            return None
        except Exception as e:
            print(f"❌ [DocumentService] 获取设备数据失败: {device_name}, {e}")
            return None

    async def search_devices(
        self, pattern: str, limit: int = 10
    ) -> AsyncIterator[DeviceData]:
        """搜索设备"""
        try:
            all_devices = await self.parse_official_document()
            count = 0

            for device_name, device_info in all_devices.items():
                if pattern.lower() in device_name.lower() and count < limit:
                    yield DeviceData(
                        name=device_name, ios=device_info, source="official_document"
                    )
                    count += 1

        except Exception as e:
            print(f"❌ [DocumentService] 搜索设备失败: {pattern}, {e}")

    async def validate_document(self, doc_path: str) -> bool:
        """验证文档格式和内容"""
        try:
            target_path = Path(doc_path)
            if not target_path.exists():
                return False

            content = await self._read_document_async(target_path)

            # 基本格式验证
            if len(content) < 100:  # 文档太短
                return False

            # 检查是否包含设备表格
            lines = content.split("\n")
            table_lines = [line for line in lines if "|" in line]

            return len(table_lines) > 5  # 至少包含一些表格内容

        except Exception:
            return False

    async def get_parsing_stats(self) -> Dict[str, Any]:
        """获取解析统计信息"""
        try:
            all_devices = await self.parse_official_document()

            total_devices = len(all_devices)
            total_ios = sum(len(ios) for ios in all_devices.values())

            # 设备类型分布
            device_types = {}
            for device_name in all_devices.keys():
                prefix = device_name.split("_")[0] if "_" in device_name else "OTHER"
                device_types[prefix] = device_types.get(prefix, 0) + 1

            return {
                "total_devices": total_devices,
                "total_ios": total_ios,
                "device_types": device_types,
                "avg_ios_per_device": (
                    total_ios / total_devices if total_devices > 0 else 0
                ),
                "document_path": str(self.official_doc_path),
                "document_exists": self.official_doc_path.exists(),
            }

        except Exception as e:
            return {
                "error": str(e),
                "document_path": str(self.official_doc_path),
                "document_exists": self.official_doc_path.exists(),
            }

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查文档文件是否存在和可读
            if not self.official_doc_path.exists():
                return False

            # 尝试读取文档前几行
            content = await self._read_document_async(self.official_doc_path)
            return len(content) > 0

        except Exception:
            return False


# 工厂函数
def create_document_service(
    cache_manager: Optional[CacheManager] = None, debug_mode: bool = False
) -> DocumentServiceImpl:
    """
    创建文档服务实例

    Args:
        cache_manager: 可选的缓存管理器
        debug_mode: 是否启用调试模式

    Returns:
        配置好的文档服务实例
    """
    config = DocumentParsingConfig(
        enhanced_parsing=True,
        aggressive_matching=True,
        debug_mode=debug_mode,
        device_name_validation=True,
        cache_parsed_results=True,
    )

    return DocumentServiceImpl(cache_manager=cache_manager, config=config)


if __name__ == "__main__":
    # 简单测试
    async def test_document_service():
        service = create_document_service(debug_mode=True)

        print("🧪 测试文档服务...")

        # 健康检查
        health = await service.health_check()
        print(f"健康检查: {health}")

        # 获取统计信息
        stats = await service.get_parsing_stats()
        print(f"解析统计: {stats}")

        if health:
            # 测试设备搜索
            print("\n🔍 搜索SL_开头的设备:")
            count = 0
            async for device in service.search_devices("SL_", limit=3):
                print(f"  {device.name}: {len(device.ios)}个IO口")
                count += 1

            if count == 0:
                print("  未找到匹配设备")

    # 运行测试
    asyncio.run(test_document_service())
