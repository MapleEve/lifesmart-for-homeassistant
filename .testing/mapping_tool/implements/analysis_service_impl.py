#!/usr/bin/env python3
"""
AnalysisService Implementation - 核心分析服务实现

抽取自DocumentBasedComparisonAnalyzer的核心AI分析算法，
实现现代化的分析服务，支持异步处理和NLP智能分析。

重构来源：
- pure_ai_analyzer.py: DocumentBasedComparisonAnalyzer.analyze_and_compare方法
- pure_ai_analyzer.py: _classify_io_platform, _analyze_device_platforms等核心算法 (~600行)

作者：@MapleEve
日期：2025-08-15
"""

import os
import re
import json
from typing import Dict, List, Any, Optional, AsyncIterator, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import asyncio

# 导入架构接口
try:
    from ..architecture.services import AnalysisService, DocumentService
    from ..architecture.cache import CacheManager
    from ..data_types.core_types import (
        DeviceData,
        AnalysisResult,
        ComparisonResult,
        AnalysisConfig,
        NLPConfig,
    )
    from ..implements.document_service_impl import DocumentServiceImpl
except ImportError:
    # 兼容性导入
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

    from architecture.services import AnalysisService, DocumentService
    from architecture.cache import CacheManager
    from data_types.core_types import (
        DeviceData,
        AnalysisResult,
        ComparisonResult,
        AnalysisConfig,
        NLPConfig,
    )
    from implements.document_service_impl import DocumentServiceImpl


class PlatformType(Enum):
    """支持的平台类型"""

    SWITCH = "switch"
    BINARY_SENSOR = "binary_sensor"
    SENSOR = "sensor"
    LIGHT = "light"
    COVER = "cover"
    CLIMATE = "climate"
    FAN = "fan"
    LOCK = "lock"
    CAMERA = "camera"


@dataclass
class IOClassificationResult:
    """IO口分类结果"""

    io_name: str
    platform: PlatformType
    confidence: float
    reasoning: str
    device_context: Optional[str] = None


@dataclass
class DeviceAnalysisResult:
    """设备分析结果"""

    device_name: str
    suggested_platforms: Set[str]
    ios_analysis: List[IOClassificationResult]
    confidence: float
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NLPAnalysisConfig:
    """NLP分析配置"""

    enhanced_parsing: bool = True
    aggressive_matching: bool = True
    debug_mode: bool = False
    confidence_threshold: float = 0.7
    platform_exclusion_rules: bool = True


class AnalysisServiceImpl(AnalysisService):
    """
    核心分析服务实现

    从"上帝类"中抽取的AI分析逻辑，重构为现代化的服务架构：
    - 异步NLP分析引擎
    - 智能平台分类算法
    - 设备上下文感知推理
    - 配置化分析策略
    - 性能优化和缓存
    """

    def __init__(
        self,
        document_service: DocumentService,
        cache_manager: Optional[CacheManager] = None,
        nlp_config: Optional[NLPAnalysisConfig] = None,
    ):
        """
        初始化分析服务

        Args:
            document_service: 文档服务实例
            cache_manager: 缓存管理器实例
            nlp_config: NLP分析配置
        """
        super().__init__()
        self.document_service = document_service
        self.cache_manager = cache_manager
        self.config = nlp_config or NLPAnalysisConfig()

        # 初始化NLP分类规则
        self._initialize_classification_rules()

        # 性能统计
        self.analysis_stats = {
            "total_devices_analyzed": 0,
            "total_ios_classified": 0,
            "cache_hits": 0,
            "average_confidence": 0.0,
        }

    def _initialize_classification_rules(self):
        """初始化NLP分类规则 - 从原始代码重构"""

        # 设备类型排除规则
        self.device_exclusion_rules = {
            "switch_devices": {
                "prefixes": ["SL_SW_", "SL_SF_"],
                "excluded_platforms": [
                    "binary_sensor",
                    "climate",
                    "sensor",
                    "cover",
                    "lock",
                ],
            },
            "light_devices": {
                "prefixes": ["SL_OL_", "SL_LI_", "SL_RGBW_", "SL_CT_"],
                "excluded_platforms": ["binary_sensor", "climate", "cover"],
            },
            "sensor_devices": {
                "prefixes": ["SL_SC_", "SL_WH_"],
                "excluded_platforms": ["switch", "light", "cover", "climate"],
            },
            "climate_devices": {
                "prefixes": ["SL_AC_"],
                "excluded_platforms": [
                    "switch",
                    "light",
                    "binary_sensor",
                    "sensor",
                    "cover",
                ],
            },
        }

        # 平台分类关键词
        self.platform_keywords = {
            PlatformType.SWITCH: {
                "io_names": ["L1", "L2", "L3", "P1", "P2", "P3", "O"],
                "descriptions": ["开关", "控制", "打开", "关闭"],
                "required_permissions": ["RW", "W"],
            },
            PlatformType.SENSOR: {
                "io_names": ["T", "H", "V", "PM"],
                "descriptions": [
                    "温度值",
                    "湿度值",
                    "电量",
                    "电压值",
                    "功率",
                    "百分比",
                ],
                "required_permissions": ["R", "RW"],
            },
            PlatformType.BINARY_SENSOR: {
                "io_names": ["M", "PIR", "DT"],
                "descriptions": [
                    "移动检测",
                    "门窗状态",
                    "检测",
                    "感应",
                    "事件",
                    "状态",
                ],
                "required_permissions": ["R", "RW"],
            },
            PlatformType.LIGHT: {
                "io_names": ["RGB", "RGBW", "BRI", "CT"],
                "descriptions": ["亮度", "颜色", "色温", "灯光", "RGB", "RGBW"],
                "required_permissions": ["RW", "W"],
            },
            PlatformType.COVER: {
                "io_names": ["OP", "CL", "POS"],
                "descriptions": ["窗帘", "打开窗帘", "关闭窗帘", "停止", "位置"],
                "required_permissions": ["RW", "W"],
            },
            PlatformType.CLIMATE: {
                "io_names": ["TEMP", "MODE", "FAN"],
                "descriptions": ["温度设置", "模式", "风扇", "制冷", "制热", "空调"],
                "required_permissions": ["RW", "W"],
            },
        }

    async def analyze_devices(
        self,
        config: AnalysisConfig,
        devices: List[DeviceData],
    ) -> AnalysisResult:
        """
        执行设备批量分析

        Args:
            config: 分析配置
            devices: 要分析的设备列表

        Returns:
            完整的分析结果
        """
        try:
            print(f"🚀 [AnalysisService] 开始分析{len(devices)}个设备...")

            analysis_results = []

            # 并行分析设备 (批量优化)
            batch_size = config.get("max_concurrent_jobs", 5)
            device_batches = [
                devices[i : i + batch_size] for i in range(0, len(devices), batch_size)
            ]

            for batch in device_batches:
                batch_tasks = [
                    self._analyze_single_device_internal(device) for device in batch
                ]

                batch_results = await asyncio.gather(
                    *batch_tasks, return_exceptions=True
                )

                for result in batch_results:
                    if isinstance(result, Exception):
                        print(f"⚠️ [AnalysisService] 设备分析失败: {result}")
                    else:
                        analysis_results.append(result)

            # 聚合分析结果
            total_confidence = sum(r.confidence for r in analysis_results)
            average_confidence = (
                total_confidence / len(analysis_results) if analysis_results else 0.0
            )

            # 更新统计信息
            self.analysis_stats["total_devices_analyzed"] += len(devices)
            self.analysis_stats["average_confidence"] = average_confidence

            return AnalysisResult(
                device_results=analysis_results,
                total_devices=len(devices),
                analyzed_devices=len(analysis_results),
                average_confidence=average_confidence,
                analysis_metadata={
                    "config": config,
                    "stats": self.analysis_stats.copy(),
                },
            )

        except Exception as e:
            print(f"❌ [AnalysisService] 批量分析失败: {e}")
            raise

    async def analyze_single_device(
        self,
        device: DeviceData,
        reference_devices: Optional[List[DeviceData]] = None,
    ) -> ComparisonResult:
        """
        分析单个设备

        Args:
            device: 目标设备
            reference_devices: 可选的参考设备列表

        Returns:
            设备对比分析结果
        """
        try:
            # 执行核心分析
            analysis_result = await self._analyze_single_device_internal(device)

            # 如果有参考设备，进行对比分析
            comparison_insights = []
            if reference_devices:
                comparison_insights = await self._compare_with_reference_devices(
                    analysis_result, reference_devices
                )

            return ComparisonResult(
                device_analysis=analysis_result,
                comparison_insights=comparison_insights,
                confidence=analysis_result.confidence,
            )

        except Exception as e:
            print(f"❌ [AnalysisService] 单设备分析失败: {device.name}, {e}")
            raise

    async def _analyze_single_device_internal(
        self, device: DeviceData
    ) -> DeviceAnalysisResult:
        """
        内部设备分析逻辑 - 从原始代码重构

        重构自: DocumentBasedComparisonAnalyzer._analyze_device_platforms
        """
        device_name = device.name
        ios_data = device.ios

        # 检查缓存
        if self.cache_manager:
            cache_key = f"device_analysis_{device_name}_{hash(str(ios_data))}"
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                self.analysis_stats["cache_hits"] += 1
                if self.config.debug_mode:
                    print(f"🎯 [AnalysisService] 缓存命中: {device_name}")
                return cached_result

        if self.config.debug_mode:
            print(
                f"🔍 [AnalysisService] 分析设备: {device_name} ({len(ios_data)}个IO口)"
            )

        platform_suggestions = set()
        ios_analysis = []

        # 逐个分析IO口
        for io_info in ios_data:
            io_name = io_info.get("name", "")
            io_description = io_info.get("description", "")
            rw_permission = io_info.get("rw", io_info.get("permission", "R"))

            if self.config.debug_mode and any(
                debug_device in device_name
                for debug_device in ["SL_OE_DE", "LI_RGBW", "CT_RGBW"]
            ):
                print(
                    f"     分析IO: {io_name}, 描述: {io_description}, 权限: {rw_permission}"
                )

            # NLP规则分析
            classification_results = await self._classify_io_platform(
                io_name, io_description, rw_permission, device_name
            )

            if classification_results:
                platform_suggestions.update(
                    r.platform.value for r in classification_results
                )
                ios_analysis.extend(classification_results)

        # 动态置信度计算 - 重构自原始逻辑
        confidence = self._calculate_device_confidence(
            platform_suggestions, ios_analysis, device_name
        )

        result = DeviceAnalysisResult(
            device_name=device_name,
            suggested_platforms=platform_suggestions,
            ios_analysis=ios_analysis,
            confidence=confidence,
            analysis_metadata={
                "total_ios": len(ios_data),
                "classified_ios": len(ios_analysis),
                "analysis_timestamp": asyncio.get_event_loop().time(),
            },
        )

        # 缓存结果
        if self.cache_manager:
            await self.cache_manager.set(cache_key, result, ttl=1800)  # 30分钟缓存

        if self.config.debug_mode:
            print(f"   最终平台建议: {list(platform_suggestions)}")
            print(f"   设备置信度: {confidence:.3f}\n")

        return result

    async def _classify_io_platform(
        self,
        io_name: str,
        io_description: str,
        rw_permission: str,
        device_name: str = "",
    ) -> List[IOClassificationResult]:
        """
        NLP规则分类IO口到平台 - 从原始代码重构

        重构自: DocumentBasedComparisonAnalyzer._classify_io_platform
        """
        results = []

        # 清理权限格式
        rw_permission = rw_permission.strip().replace("`", "")

        if self.config.debug_mode and "SL_OE_DE" in device_name:
            print(f"      [AnalysisService] 分类IO {io_name} (设备: {device_name})")

        # 遍历所有平台类型进行分类
        for platform_type in PlatformType:
            classification_result = await self._classify_single_platform(
                io_name, io_description, rw_permission, device_name, platform_type
            )

            if classification_result:
                results.append(classification_result)

        return results

    async def _classify_single_platform(
        self,
        io_name: str,
        io_description: str,
        rw_permission: str,
        device_name: str,
        platform_type: PlatformType,
    ) -> Optional[IOClassificationResult]:
        """分类单个平台类型"""

        # 检查设备类型排除规则
        if self._should_exclude_platform(device_name, platform_type.value):
            return None

        platform_rules = self.platform_keywords.get(platform_type)
        if not platform_rules:
            return None

        # 检查权限要求
        if rw_permission not in platform_rules["required_permissions"]:
            return None

        # 检查IO名称匹配
        io_name_match = any(
            keyword in io_name.upper() for keyword in platform_rules["io_names"]
        )

        # 检查描述匹配
        description_match = any(
            keyword in io_description for keyword in platform_rules["descriptions"]
        )

        if not (io_name_match or description_match):
            return None

        # 计算置信度和推理
        confidence, reasoning = self._calculate_classification_confidence(
            io_name, io_description, rw_permission, device_name, platform_type
        )

        if confidence < 0.5:  # 低置信度过滤
            return None

        return IOClassificationResult(
            io_name=io_name,
            platform=platform_type,
            confidence=confidence,
            reasoning=reasoning,
            device_context=device_name,
        )

    def _should_exclude_platform(self, device_name: str, platform: str) -> bool:
        """检查是否应该排除某个平台 - 从原始代码重构"""
        if not device_name:
            return False

        for device_type, rules in self.device_exclusion_rules.items():
            if any(device_name.startswith(prefix) for prefix in rules["prefixes"]):
                return platform in rules["excluded_platforms"]

        return False

    def _calculate_classification_confidence(
        self,
        io_name: str,
        io_description: str,
        rw_permission: str,
        device_name: str,
        platform_type: PlatformType,
    ) -> tuple[float, str]:
        """计算分类置信度和推理 - 重构自原始逻辑"""

        base_confidence = 0.7
        reasoning_parts = []

        # 特殊设备类型提升
        if platform_type == PlatformType.SWITCH:
            if device_name.startswith("SL_OE_") and io_name == "P1":
                base_confidence = 0.98
                reasoning_parts.append("计量插座开关控制IO口")
            elif device_name.startswith("SL_OE_") and (
                "控制" in io_description or "开关" in io_description
            ):
                base_confidence = 0.98
                reasoning_parts.append("SL_OE_系列开关控制")
            else:
                base_confidence = 0.9
                reasoning_parts.append("开关控制IO口")

        elif platform_type == PlatformType.SENSOR:
            if any(keyword in io_name.upper() for keyword in ["T", "H", "V", "PM"]):
                base_confidence = 0.95
                reasoning_parts.append("传感器数据读取")
            else:
                base_confidence = 0.8
                reasoning_parts.append("传感器相关")

        elif platform_type == PlatformType.LIGHT:
            if any(
                keyword in io_name.upper() for keyword in ["RGB", "RGBW", "BRI", "CT"]
            ):
                base_confidence = 0.95
                reasoning_parts.append("灯光控制IO口")
            else:
                base_confidence = 0.8
                reasoning_parts.append("灯光相关")

        # 权限匹配加分
        if rw_permission == "RW":
            base_confidence += 0.05
            reasoning_parts.append("RW权限")

        # 描述匹配加分
        platform_rules = self.platform_keywords.get(platform_type, {})
        description_keywords = platform_rules.get("descriptions", [])
        if any(keyword in io_description for keyword in description_keywords):
            base_confidence += 0.05
            reasoning_parts.append("描述匹配")

        # 限制最大置信度
        confidence = min(base_confidence, 0.99)
        reasoning = f"{platform_type.value}平台: {', '.join(reasoning_parts)}"

        return confidence, reasoning

    def _calculate_device_confidence(
        self,
        platform_suggestions: Set[str],
        ios_analysis: List[IOClassificationResult],
        device_name: str,
    ) -> float:
        """计算设备级别置信度 - 从原始逻辑重构"""

        confidence = 0.5  # 基础置信度

        if platform_suggestions:
            confidence = 0.7

            # 基于IO数量调整置信度
            io_count = len(ios_analysis)
            if io_count >= 2:
                confidence += min(io_count * 0.1, 0.2)  # 最多增加0.2

            # 基于分类质量调整
            if ios_analysis:
                avg_io_confidence = sum(io.confidence for io in ios_analysis) / len(
                    ios_analysis
                )
                confidence = (confidence + avg_io_confidence) / 2

        return min(confidence, 0.99)

    async def _compare_with_reference_devices(
        self, target_analysis: DeviceAnalysisResult, reference_devices: List[DeviceData]
    ) -> List[Dict[str, Any]]:
        """与参考设备进行对比分析"""
        insights = []

        # 找到相似设备
        similar_devices = [
            ref
            for ref in reference_devices
            if self._calculate_device_similarity(target_analysis.device_name, ref.name)
            > 0.7
        ]

        if similar_devices:
            insights.append(
                {
                    "type": "similar_devices",
                    "devices": [dev.name for dev in similar_devices],
                    "confidence": 0.8,
                }
            )

        return insights

    def _calculate_device_similarity(self, device1: str, device2: str) -> float:
        """计算设备名称相似度"""
        # 简单的前缀相似度计算
        if device1.startswith(device2[:6]) or device2.startswith(device1[:6]):
            return 0.8

        # 其他相似度算法可以在这里扩展
        return 0.0

    async def batch_analyze(
        self,
        device_batches: List[List[DeviceData]],
        config: AnalysisConfig,
    ) -> AsyncIterator[AnalysisResult]:
        """批量异步分析设备"""
        for batch in device_batches:
            try:
                result = await self.analyze_devices(config, batch)
                yield result
            except Exception as e:
                print(f"❌ [AnalysisService] 批次分析失败: {e}")

    def get_analysis_progress(self, analysis_id: str) -> Dict[str, Any]:
        """获取分析进度信息"""
        return {
            "analysis_id": analysis_id,
            "stats": self.analysis_stats.copy(),
            "status": (
                "running"
                if self.analysis_stats["total_devices_analyzed"] > 0
                else "idle"
            ),
        }

    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 检查文档服务健康状态
            if not await self.document_service.health_check():
                return False

            # 检查分类规则完整性
            required_platforms = [
                PlatformType.SWITCH,
                PlatformType.SENSOR,
                PlatformType.LIGHT,
            ]
            for platform in required_platforms:
                if platform not in self.platform_keywords:
                    return False

            return True

        except Exception:
            return False


# 工厂函数
def create_analysis_service(
    document_service: DocumentService,
    cache_manager: Optional[CacheManager] = None,
    debug_mode: bool = False,
) -> AnalysisServiceImpl:
    """
    创建分析服务实例

    Args:
        document_service: 文档服务实例
        cache_manager: 可选的缓存管理器
        debug_mode: 是否启用调试模式

    Returns:
        配置好的分析服务实例
    """
    nlp_config = NLPAnalysisConfig(
        enhanced_parsing=True,
        aggressive_matching=True,
        debug_mode=debug_mode,
        confidence_threshold=0.7,
        platform_exclusion_rules=True,
    )

    return AnalysisServiceImpl(
        document_service=document_service,
        cache_manager=cache_manager,
        nlp_config=nlp_config,
    )


if __name__ == "__main__":
    # 简单测试
    async def test_analysis_service():
        # 创建依赖服务
        from implements.document_service_impl import create_document_service

        doc_service = create_document_service(debug_mode=True)
        analysis_service = create_analysis_service(doc_service, debug_mode=True)

        print("🧪 测试分析服务...")

        # 健康检查
        health = await analysis_service.health_check()
        print(f"健康检查: {health}")

        if health:
            # 创建测试设备
            test_device = DeviceData(
                name="SL_OE_DE",
                ios=[
                    {"name": "P1", "description": "开关控制", "rw": "RW"},
                    {"name": "V", "description": "电压值", "rw": "R"},
                    {"name": "T", "description": "温度值", "rw": "R"},
                ],
                source="test",
            )

            # 分析单个设备
            result = await analysis_service.analyze_single_device(test_device)
            print(f"设备分析结果: {result.device_analysis.device_name}")
            print(f"建议平台: {result.device_analysis.suggested_platforms}")
            print(f"置信度: {result.device_analysis.confidence:.3f}")

    # 运行测试
    asyncio.run(test_analysis_service())
