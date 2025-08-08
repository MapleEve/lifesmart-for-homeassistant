#!/usr/bin/env python3
"""
设备映射分析策略模式实现
提供可扩展的算法接口，支持不同的分析策略
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Set, List, Any, Tuple

try:
    from .optimized_core_utils import IOExtractor, MatchingAlgorithms, DeviceNameUtils
    from .regex_cache import RegexCache
except ImportError:
    # Fallback for development
    import sys
    import os

    sys.path.append(os.path.dirname(__file__))
    from optimized_core_utils import IOExtractor, MatchingAlgorithms, DeviceNameUtils
    from regex_cache import RegexCache


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
            if device_name not in doc_ios_map:
                continue

            # 选择合适的分析策略
            strategy = self.factory.get_strategy(device_mapping)

            # 执行分析
            result = strategy.analyze_device(
                device_name, device_mapping, doc_ios_map[device_name]
            )

            results.append(result)

        return results

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
