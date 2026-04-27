#!/usr/bin/env python3
"""
设备映射分析策略模式实现（增强版）
提供可扩展的算法接口，支持不同的分析策略
集成IO口逻辑分析和平台分配验证功能
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Set, List, Any, Tuple, Optional

try:
    from .core_utils import IOExtractor, MatchingAlgorithms, DeviceNameUtils
    from .regex_cache import RegexCache
    from .io_logic_analyzer import (
        IOLogicAnalyzer,
        PlatformAllocationValidator,
        PlatformAllocationIssue,
    )
    from .pure_ai_analyzer import PureAIAnalyzer, DeviceAnalysisResult, IOCapability
except ImportError:
    # Fallback for development
    import sys
    import os

    sys.path.append(os.path.dirname(__file__))
    from core_utils import IOExtractor, MatchingAlgorithms, DeviceNameUtils
    from regex_cache import RegexCache
    from io_logic_analyzer import (
        IOLogicAnalyzer,
        PlatformAllocationValidator,
        PlatformAllocationIssue,
    )
    from pure_ai_analyzer import PureAIAnalyzer, DeviceAnalysisResult, IOCapability


@dataclass
class AnalysisResult:
    """分析结果数据结构"""

    device_name: str
    doc_ios: Set[str]
    mapped_ios: Set[str]
    matched_pairs: List[Tuple[str, str]]
    unmatched_doc: List[str]
    unmatched_mapping: List[str]
    match_score: float
    analysis_type: str


@dataclass
class EnhancedAnalysisResult(AnalysisResult):
    """增强版分析结果，包含平台分配验证信息和纯AI分析"""

    platform_allocation_issues: List[PlatformAllocationIssue] = None
    io_capabilities: Dict[str, Any] = None
    platform_allocation_score: float = 1.0
    allocation_recommendations: List[str] = None
    # 新增纯AI分析字段
    ai_analysis_result: Optional[DeviceAnalysisResult] = None
    is_multi_io_device: bool = False
    bitmask_ios: List[str] = None
    multi_platform_ios: List[str] = None


class DeviceAnalysisStrategy(ABC):
    """设备分析策略基类"""

    @abstractmethod
    def analyze_device(
        self, device_name: str, device_mapping: Dict[str, Any], doc_ios: List[Dict]
    ) -> AnalysisResult:
        """分析单个设备的映射情况"""
        pass

    @abstractmethod
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        pass


class EnhancedDeviceAnalysisStrategy(DeviceAnalysisStrategy):
    """增强版设备分析策略基类"""

    def __init__(self, supported_platforms: Set[str]):
        self.supported_platforms = supported_platforms
        self.io_analyzer = IOLogicAnalyzer()
        self.platform_validator = PlatformAllocationValidator(supported_platforms)

    def analyze_device(
        self, device_name: str, device_mapping: Dict[str, Any], doc_ios: List[Dict]
    ) -> AnalysisResult:
        """分析单个设备的映射情况（标准实现）"""
        # 从文档IO字典列表中提取IO名称
        doc_io_names = set()
        if isinstance(doc_ios, list):
            for io_dict in doc_ios:
                if isinstance(io_dict, dict) and "name" in io_dict:
                    io_name = io_dict["name"].strip("`")
                    if io_name:
                        doc_io_names.add(io_name)

        # 提取映射的IO口
        mapped_ios = IOExtractor.extract_mapped_ios(device_mapping)

        # 执行匹配算法
        matched_pairs = []
        unmatched_doc = doc_io_names.copy()
        unmatched_mapping = set(mapped_ios)

        for doc_io in list(unmatched_doc):
            for mapped_io in list(unmatched_mapping):
                if MatchingAlgorithms.match_wildcard_io(mapped_io, doc_io):
                    matched_pairs.append((doc_io, mapped_io))
                    unmatched_doc.discard(doc_io)
                    unmatched_mapping.discard(mapped_io)
                    break

        # 计算匹配分数
        total_ios = len(doc_io_names) + len(mapped_ios)
        match_score = (len(matched_pairs) * 2 / total_ios) if total_ios > 0 else 1.0

        return AnalysisResult(
            device_name=device_name,
            doc_ios=doc_io_names,
            mapped_ios=mapped_ios,
            matched_pairs=matched_pairs,
            unmatched_doc=list(unmatched_doc),
            unmatched_mapping=list(unmatched_mapping),
            match_score=match_score,
            analysis_type="enhanced_standard",
        )

    def get_strategy_name(self) -> str:
        return "增强版设备分析"

    def analyze_device_with_platform_validation(
        self,
        device_name: str,
        device_mapping: Dict[str, Any],
        doc_ios: List[Dict],
        raw_device_data: Optional[Dict[str, Any]] = None,
    ) -> EnhancedAnalysisResult:
        """带平台分配验证的设备分析"""

        # 执行基础分析
        base_result = self.analyze_device(device_name, device_mapping, doc_ios)

        # 执行平台分配验证
        platform_issues = []
        io_capabilities = {}
        allocation_recommendations = []

        if raw_device_data:
            # 分析每个IO口的能力
            for platform, platform_config in raw_device_data.items():
                if platform in ["name", "description"] or not isinstance(
                    platform_config, dict
                ):
                    continue

                for io_name, io_config in platform_config.items():
                    if not isinstance(io_config, dict):
                        continue

                    # 分析IO口能力
                    capability = self.io_analyzer.infer_supported_platforms(
                        {
                            "name": io_name,
                            "description": io_config.get("description", ""),
                            "detailed_description": io_config.get(
                                "detailed_description", ""
                            ),
                            "rw": io_config.get("rw", ""),
                            "data_type": io_config.get("data_type", ""),
                        }
                    )

                    io_capabilities[f"{platform}.{io_name}"] = {
                        "supported_platforms": list(capability.supported_platforms),
                        "logic_patterns": [p.value for p in capability.logic_patterns],
                        "reason": capability.reason,
                    }

                    # 检查当前分配是否合理
                    if (
                        capability.supported_platforms
                        and platform not in capability.supported_platforms
                    ):
                        issue = PlatformAllocationIssue(
                            device_name=device_name,
                            io_name=io_name,
                            issue_type="misallocation",
                            current_platforms={platform},
                            recommended_platforms=capability.supported_platforms,
                            reason=f"IO口 {io_name} 当前分配到 {platform}，但根据逻辑分析应该分配到: {', '.join(capability.supported_platforms)}",
                            severity=(
                                "major"
                                if len(capability.supported_platforms) > 0
                                else "minor"
                            ),
                        )
                        platform_issues.append(issue)

            # 验证整体分配
            device_issues = self.platform_validator.validate_device_allocation(
                device_name, raw_device_data
            )
            platform_issues.extend(device_issues)

            # 生成建议
            if platform_issues:
                allocation_recommendations = self._generate_device_recommendations(
                    platform_issues
                )

        # 计算平台分配分数
        platform_score = self._calculate_platform_allocation_score(platform_issues)

        return EnhancedAnalysisResult(
            device_name=base_result.device_name,
            doc_ios=base_result.doc_ios,
            mapped_ios=base_result.mapped_ios,
            matched_pairs=base_result.matched_pairs,
            unmatched_doc=base_result.unmatched_doc,
            unmatched_mapping=base_result.unmatched_mapping,
            match_score=base_result.match_score,
            analysis_type=base_result.analysis_type,
            platform_allocation_issues=platform_issues,
            io_capabilities=io_capabilities,
            platform_allocation_score=platform_score,
            allocation_recommendations=allocation_recommendations,
        )

    def _calculate_platform_allocation_score(
        self, issues: List[PlatformAllocationIssue]
    ) -> float:
        """计算平台分配分数"""
        if not issues:
            return 1.0

        # 按严重程度计算扣分
        penalty = 0
        for issue in issues:
            if issue.severity == "critical":
                penalty += 0.3
            elif issue.severity == "major":
                penalty += 0.2
            elif issue.severity == "minor":
                penalty += 0.1

        return max(0.0, 1.0 - penalty)

    def _generate_device_recommendations(
        self, issues: List[PlatformAllocationIssue]
    ) -> List[str]:
        """为设备生成修复建议"""
        recommendations = []

        # 按问题类型分组
        over_allocations = [i for i in issues if i.issue_type == "over_allocation"]
        under_allocations = [i for i in issues if i.issue_type == "under_allocation"]
        misallocations = [i for i in issues if i.issue_type == "misallocation"]

        if misallocations:
            io_list = [i.io_name for i in misallocations]
            recommendations.append(f"重新分配IO口平台: {', '.join(io_list)}")

        if over_allocations:
            recommendations.append("移除过度分配的平台支持")

        if under_allocations:
            recommendations.append("添加缺失的平台支持")

        return recommendations


class StandardDeviceStrategy(DeviceAnalysisStrategy):
    """标准设备分析策略"""

    def analyze_device(
        self, device_name: str, device_mapping: Dict[str, Any], doc_ios: List[Dict]
    ) -> AnalysisResult:
        """分析标准设备的映射情况"""

        # 从文档IO字典列表中提取IO名称
        doc_io_names = set()
        if isinstance(doc_ios, list):
            for io_dict in doc_ios:
                if isinstance(io_dict, dict) and "name" in io_dict:
                    # 清理IO名称（移除反引号）
                    io_name = io_dict["name"].strip("`")
                    if io_name:
                        doc_io_names.add(io_name)

        # 提取映射的IO口
        mapped_ios = IOExtractor.extract_mapped_ios(device_mapping)

        # 执行匹配算法
        matched_pairs = []
        unmatched_doc = doc_io_names.copy()
        unmatched_mapping = set(mapped_ios)

        # 使用优化的匹配算法
        for doc_io in list(unmatched_doc):
            for mapped_io in list(unmatched_mapping):
                if MatchingAlgorithms.match_wildcard_io(mapped_io, doc_io):
                    matched_pairs.append((doc_io, mapped_io))
                    unmatched_doc.discard(doc_io)
                    unmatched_mapping.discard(mapped_io)
                    break

        # 计算匹配分数
        total_ios = len(doc_io_names) + len(mapped_ios)
        match_score = (len(matched_pairs) * 2 / total_ios) if total_ios > 0 else 1.0

        return AnalysisResult(
            device_name=device_name,
            doc_ios=doc_io_names,
            mapped_ios=mapped_ios,
            matched_pairs=matched_pairs,
            unmatched_doc=list(unmatched_doc),
            unmatched_mapping=list(unmatched_mapping),
            match_score=match_score,
            analysis_type="standard",
        )

    def get_strategy_name(self) -> str:
        return "标准设备分析"


class DynamicDeviceStrategy(DeviceAnalysisStrategy):
    """动态设备分析策略"""

    def analyze_device(
        self, device_name: str, device_mapping: Dict[str, Any], doc_ios: List[Dict]
    ) -> AnalysisResult:
        """分析动态设备的映射情况"""

        # 从文档IO字典列表中提取IO名称
        doc_io_names = set()
        if isinstance(doc_ios, list):
            for io_dict in doc_ios:
                if isinstance(io_dict, dict) and "name" in io_dict:
                    # 清理IO名称（移除反引号）
                    io_name = io_dict["name"].strip("`")
                    if io_name:
                        doc_io_names.add(io_name)

        # 使用IOExtractor的标准方法提取映射IO口
        mapped_ios = IOExtractor.extract_mapped_ios(device_mapping)

        # 执行匹配分析
        return self._perform_matching_analysis(
            device_name, doc_io_names, mapped_ios, "dynamic"
        )

    def _perform_matching_analysis(
        self,
        device_name: str,
        doc_ios: Set[str],
        mapped_ios: Set[str],
        analysis_type: str,
    ) -> AnalysisResult:
        """执行匹配分析的通用方法"""

        matched_pairs = []
        unmatched_doc = set(doc_ios)
        unmatched_mapping = set(mapped_ios)

        # 高级匹配算法 - 考虑动态设备的特殊性
        for doc_io in list(unmatched_doc):
            best_match = None
            best_score = 0

            for mapped_io in list(unmatched_mapping):
                # 使用增强的匹配逻辑
                if MatchingAlgorithms.match_wildcard_io(mapped_io, doc_io):
                    # 计算匹配质量分数
                    score = self._calculate_match_quality(doc_io, mapped_io)
                    if score > best_score:
                        best_match = mapped_io
                        best_score = score

            if best_match:
                matched_pairs.append((doc_io, best_match))
                unmatched_doc.discard(doc_io)
                unmatched_mapping.discard(best_match)

        # 计算综合匹配分数
        total_ios = len(doc_ios) + len(mapped_ios)
        match_score = (len(matched_pairs) * 2 / total_ios) if total_ios > 0 else 1.0

        return AnalysisResult(
            device_name=device_name,
            doc_ios=doc_ios,
            mapped_ios=mapped_ios,
            matched_pairs=matched_pairs,
            unmatched_doc=list(unmatched_doc),
            unmatched_mapping=list(unmatched_mapping),
            match_score=match_score,
            analysis_type=analysis_type,
        )

    def _calculate_match_quality(self, doc_io: str, mapped_io: str) -> float:
        """计算匹配质量分数"""
        if doc_io == mapped_io:
            return 1.0

        # 基于相似度的评分
        if doc_io.startswith(mapped_io) or mapped_io.startswith(doc_io):
            return 0.8

        # P系列IO口特殊处理
        if RegexCache.is_p_io_port(doc_io) and RegexCache.is_p_io_port(mapped_io):
            return 0.6

        # 通配符匹配
        if "*" in mapped_io or "(x取值为数字)" in doc_io:
            return 0.7

        return 0.5

    def get_strategy_name(self) -> str:
        return "动态设备分析"


class VersionedDeviceStrategy(DeviceAnalysisStrategy):
    """版本设备分析策略"""

    def analyze_device(
        self, device_name: str, device_mapping: Dict[str, Any], doc_ios: List[Dict]
    ) -> AnalysisResult:
        """分析版本设备的映射情况"""

        # 从文档IO字典列表中提取IO名称
        doc_io_names = set()
        if isinstance(doc_ios, list):
            for io_dict in doc_ios:
                if isinstance(io_dict, dict) and "name" in io_dict:
                    # 清理IO名称（移除反引号）
                    io_name = io_dict["name"].strip("`")
                    if io_name:
                        doc_io_names.add(io_name)

        # 使用IOExtractor的标准方法提取映射IO口
        mapped_ios = IOExtractor.extract_mapped_ios(device_mapping)

        # 执行匹配分析
        return self._perform_matching_analysis(
            device_name, doc_io_names, mapped_ios, "versioned"
        )

    def _perform_matching_analysis(
        self,
        device_name: str,
        doc_ios: Set[str],
        mapped_ios: Set[str],
        analysis_type: str,
    ) -> AnalysisResult:
        """版本设备的匹配分析"""

        matched_pairs = []
        unmatched_doc = set(doc_ios)
        unmatched_mapping = set(mapped_ios)

        # 版本设备的匹配策略更加严格
        for doc_io in list(unmatched_doc):
            for mapped_io in list(unmatched_mapping):
                if MatchingAlgorithms.match_wildcard_io(mapped_io, doc_io):
                    matched_pairs.append((doc_io, mapped_io))
                    unmatched_doc.discard(doc_io)
                    unmatched_mapping.discard(mapped_io)
                    break

        # 计算匹配分数 - 版本设备要求更高的匹配度
        total_ios = len(doc_ios) + len(mapped_ios)
        base_score = (len(matched_pairs) * 2 / total_ios) if total_ios > 0 else 1.0

        # 版本设备的惩罚因子 - 未匹配项影响更大
        penalty = len(unmatched_doc) + len(unmatched_mapping)
        match_score = max(0, base_score - (penalty * 0.1))

        return AnalysisResult(
            device_name=device_name,
            doc_ios=doc_ios,
            mapped_ios=mapped_ios,
            matched_pairs=matched_pairs,
            unmatched_doc=list(unmatched_doc),
            unmatched_mapping=list(unmatched_mapping),
            match_score=match_score,
            analysis_type=analysis_type,
        )

    def get_strategy_name(self) -> str:
        return "版本设备分析"


class AnalysisStrategyFactory:
    """分析策略工厂类"""

    _strategies = {
        "standard": StandardDeviceStrategy,
        "dynamic": DynamicDeviceStrategy,
        "versioned": VersionedDeviceStrategy,
    }

    @classmethod
    def get_strategy(cls, device_mapping: Dict[str, Any]) -> DeviceAnalysisStrategy:
        """根据设备映射结构选择合适的分析策略"""

        if device_mapping.get("dynamic", False):
            return cls._strategies["dynamic"]()
        elif device_mapping.get("versioned", False):
            return cls._strategies["versioned"]()
        else:
            return cls._strategies["standard"]()

    @classmethod
    def register_strategy(cls, name: str, strategy_class: type):
        """注册新的分析策略"""
        cls._strategies[name] = strategy_class

    @classmethod
    def list_strategies(cls) -> List[str]:
        """列出所有可用的策略"""
        return list(cls._strategies.keys())


class BatchAnalysisEngine:
    """批量分析引擎 - 整合所有策略"""

    def __init__(self):
        self.factory = AnalysisStrategyFactory()

    def analyze_devices(
        self, devices_data: Dict[str, Any], doc_ios_map: Dict[str, List[Dict]]
    ) -> List[AnalysisResult]:
        """批量分析设备映射情况"""

        results = []

        for device_name, device_mapping in devices_data.items():
            # 获取文档数据，如果没有则使用空列表（允许纯AI分析）
            doc_ios = doc_ios_map.get(device_name, [])

            # 选择合适的分析策略
            strategy = self.factory.get_strategy(device_mapping)

            # 执行分析
            result = strategy.analyze_device(device_name, device_mapping, doc_ios)

            results.append(result)

        return results


class EnhancedAnalysisEngine:
    """增强版分析引擎"""

    def __init__(self, supported_platforms: Set[str]):
        self.supported_platforms = supported_platforms
        self.strategies = {
            "standard": StandardDeviceStrategy(),  # 使用现有的标准策略
            "dynamic": DynamicDeviceStrategy(),
            "versioned": VersionedDeviceStrategy(),
        }
        # 新增纯AI分析器
        self.pure_ai_analyzer = PureAIAnalyzer(supported_platforms)

    def analyze_devices_with_platform_validation(
        self,
        devices_data: Dict[str, Any],
        doc_ios_map: Dict[str, List[Dict]],
        raw_devices_data: Optional[Dict[str, Any]] = None,
    ) -> List[EnhancedAnalysisResult]:
        """带平台分配验证的批量设备分析，集成纯AI分析"""

        results = []
        enhanced_strategy = EnhancedDeviceAnalysisStrategy(self.supported_platforms)

        for device_name, device_mapping in devices_data.items():
            # 获取文档数据，如果没有则使用空列表（允许纯AI分析）
            doc_ios = doc_ios_map.get(device_name, [])

            # 选择基础策略执行分析
            strategy_type = "standard"  # 默认策略
            if device_mapping.get("dynamic", False):
                strategy_type = "dynamic"
            elif device_mapping.get("versioned", False):
                strategy_type = "versioned"

            base_strategy = self.strategies[strategy_type]
            base_result = base_strategy.analyze_device(
                device_name, device_mapping, doc_ios
            )

            # 获取raw data
            raw_device_data = None
            if raw_devices_data and device_name in raw_devices_data:
                raw_device_data = raw_devices_data[device_name]

            # 执行纯AI分析
            ai_analysis_result = None
            bitmask_ios = []
            multi_platform_ios = []

            if raw_device_data:
                try:
                    ai_analysis_result = self.pure_ai_analyzer.analyze_device_specs(
                        raw_device_data
                    )

                    # 提取bitmask IO信息 - 修复：应该是单个IO的bitmask信息
                    bitmask_ios = []
                    if ai_analysis_result and ai_analysis_result.bitmask_devices:
                        # bitmask_devices现在包含的是"platform.io_name"格式的条目
                        bitmask_ios = [
                            entry.split(".")[-1] if "." in entry else entry
                            for entry in ai_analysis_result.bitmask_devices
                        ]

                    # 提取多平台分配IO信息
                    if ai_analysis_result and ai_analysis_result.ios:
                        multi_platform_ios = [
                            io.name
                            for io in ai_analysis_result.ios
                            if io.multi_platform_potential
                        ]
                except Exception as e:
                    print(f"⚠️ 纯AI分析设备{device_name}时出错: {e}")

            # 转换为增强结果并添加平台分配分析
            if raw_device_data:
                enhanced_result = (
                    enhanced_strategy.analyze_device_with_platform_validation(
                        device_name,
                        device_mapping,
                        doc_ios,
                        raw_device_data,
                    )
                )

                # 添加纯AI分析结果
                enhanced_result.ai_analysis_result = ai_analysis_result
                enhanced_result.is_multi_io_device = (
                    ai_analysis_result.is_multi_io_device
                    if ai_analysis_result
                    else False
                )
                enhanced_result.bitmask_ios = bitmask_ios or []
                enhanced_result.multi_platform_ios = multi_platform_ios or []

            else:
                # 没有raw data时创建基础的增强结果
                enhanced_result = EnhancedAnalysisResult(
                    device_name=base_result.device_name,
                    doc_ios=base_result.doc_ios,
                    mapped_ios=base_result.mapped_ios,
                    matched_pairs=base_result.matched_pairs,
                    unmatched_doc=base_result.unmatched_doc,
                    unmatched_mapping=base_result.unmatched_mapping,
                    match_score=base_result.match_score,
                    analysis_type=base_result.analysis_type,
                    platform_allocation_issues=[],
                    io_capabilities={},
                    platform_allocation_score=1.0,
                    allocation_recommendations=[],
                    ai_analysis_result=ai_analysis_result,
                    is_multi_io_device=False,
                    bitmask_ios=[],
                    multi_platform_ios=[],
                )

            results.append(enhanced_result)

        return results

    def _convert_to_enhanced_result(
        self, base_result: AnalysisResult
    ) -> EnhancedAnalysisResult:
        """将基础结果转换为增强结果"""
        return EnhancedAnalysisResult(
            device_name=base_result.device_name,
            doc_ios=base_result.doc_ios,
            mapped_ios=base_result.mapped_ios,
            matched_pairs=base_result.matched_pairs,
            unmatched_doc=base_result.unmatched_doc,
            unmatched_mapping=base_result.unmatched_mapping,
            match_score=base_result.match_score,
            analysis_type=base_result.analysis_type,
            platform_allocation_issues=[],
            io_capabilities={},
            platform_allocation_score=1.0,
            allocation_recommendations=[],
        )

    def generate_enhanced_report(
        self, results: List[EnhancedAnalysisResult]
    ) -> Dict[str, Any]:
        """生成增强版分析报告，包含纯AI分析结果"""

        # 基础统计
        total_devices = len(results)
        devices_with_issues = len([r for r in results if r.platform_allocation_issues])
        total_platform_issues = sum(
            len(r.platform_allocation_issues or []) for r in results
        )

        # 纯AI分析统计
        multi_io_devices = [r for r in results if r.is_multi_io_device]
        bitmask_devices = [r for r in results if r.bitmask_ios]
        multi_platform_devices = [r for r in results if r.multi_platform_ios]

        # 平台分配分数统计
        avg_platform_score = (
            sum(r.platform_allocation_score for r in results) / total_devices
            if total_devices > 0
            else 0
        )

        # AI分析置信度统计
        ai_analyzed_devices = [r for r in results if r.ai_analysis_result]
        if ai_analyzed_devices:
            avg_ai_confidence = sum(
                r.ai_analysis_result.analysis_confidence for r in ai_analyzed_devices
            ) / len(ai_analyzed_devices)
        else:
            avg_ai_confidence = 0

        # 问题分类统计
        issue_type_stats = {}
        for result in results:
            if result.platform_allocation_issues:
                for issue in result.platform_allocation_issues:
                    issue_type_stats[issue.issue_type] = (
                        issue_type_stats.get(issue.issue_type, 0) + 1
                    )

        # 生成设备详情（包含AI分析信息）
        problem_devices = []
        for result in results:
            if result.platform_allocation_issues or result.match_score < 0.9:
                device_info = {
                    "设备名称": result.device_name,
                    "IO口匹配分数": round(result.match_score, 3),
                    "平台分配分数": round(result.platform_allocation_score, 3),
                    "综合分数": round(
                        (result.match_score + result.platform_allocation_score) / 2, 3
                    ),
                    "分析类型": result.analysis_type,
                    "平台分配问题": len(result.platform_allocation_issues or []),
                    "IO口匹配问题": len(result.unmatched_doc)
                    + len(result.unmatched_mapping),
                    # 新增AI分析字段
                    "是否多IO设备": result.is_multi_io_device,
                    "Bitmask IO数": len(result.bitmask_ios or []),
                    "多平台IO数": len(result.multi_platform_ios or []),
                    "AI分析置信度": (
                        round(result.ai_analysis_result.analysis_confidence, 3)
                        if result.ai_analysis_result
                        else 0
                    ),
                }
                problem_devices.append(device_info)

        # 排序：综合分数最低的设备排在前面
        problem_devices.sort(key=lambda x: x["综合分数"])

        return {
            "分析概览": {
                "总设备数": total_devices,
                "有问题设备数": len(problem_devices),
                "总平台分配问题": total_platform_issues,
                "平均平台分配分数": round(avg_platform_score, 3),
                "问题类型分布": issue_type_stats,
                # 新增AI分析概览
                "纯AI分析设备数": len(ai_analyzed_devices),
                "多IO设备数": len(multi_io_devices),
                "Bitmask设备数": len(bitmask_devices),
                "多平台分配设备数": len(multi_platform_devices),
                "平均AI分析置信度": round(avg_ai_confidence, 3),
            },
            "纯AI分析结果": {
                "多IO设备列表": [r.device_name for r in multi_io_devices],
                "Bitmask设备列表": [r.device_name for r in bitmask_devices],
                "多平台分配设备列表": [r.device_name for r in multi_platform_devices],
                "详细AI分析": [
                    {
                        "设备名称": r.device_name,
                        "是否多IO设备": r.is_multi_io_device,
                        "Bitmask IO": r.bitmask_ios or [],
                        "多平台IO": r.multi_platform_ios or [],
                        "AI置信度": (
                            round(r.ai_analysis_result.analysis_confidence, 3)
                            if r.ai_analysis_result
                            else 0
                        ),
                        "推荐建议": (
                            r.ai_analysis_result.recommendations
                            if r.ai_analysis_result
                            else []
                        ),
                    }
                    for r in ai_analyzed_devices
                ],
            },
            "问题设备详情": problem_devices,
            "改进建议": [],  # 可以后续扩展
        }

    def generate_summary_report(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """生成汇总报告"""

        total_devices = len(results)
        total_matched_pairs = sum(len(r.matched_pairs) for r in results)
        total_unmatched_doc = sum(len(r.unmatched_doc) for r in results)
        total_unmatched_mapping = sum(len(r.unmatched_mapping) for r in results)

        avg_match_score = (
            sum(r.match_score for r in results) / total_devices
            if total_devices > 0
            else 0
        )

        # 按策略分类统计
        strategy_stats = {}
        for result in results:
            strategy = result.analysis_type
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    "count": 0,
                    "avg_score": 0,
                    "total_score": 0,
                }

            strategy_stats[strategy]["count"] += 1
            strategy_stats[strategy]["total_score"] += result.match_score

        # 计算每种策略的平均分数
        for stats in strategy_stats.values():
            stats["avg_score"] = stats["total_score"] / stats["count"]
            del stats["total_score"]  # 移除临时字段

        return {
            "总设备数": total_devices,
            "总匹配对数": total_matched_pairs,
            "总未匹配文档IO": total_unmatched_doc,
            "总未匹配映射IO": total_unmatched_mapping,
            "平均匹配分数": round(avg_match_score, 3),
            "策略统计": strategy_stats,
            "详细结果": [
                {
                    "设备名称": r.device_name,
                    "匹配分数": round(r.match_score, 3),
                    "分析策略": r.analysis_type,
                    "匹配对数": len(r.matched_pairs),
                    "未匹配文档IO": len(r.unmatched_doc),
                    "未匹配映射IO": len(r.unmatched_mapping),
                }
                for r in sorted(results, key=lambda x: x.match_score)
            ],
        }
