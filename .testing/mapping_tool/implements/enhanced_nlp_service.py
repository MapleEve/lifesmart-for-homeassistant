#!/usr/bin/env python3
"""
Enhanced NLP Service - 完整版 NLP 分析服务

利用完整的 requirements.txt 依赖提供强大的 NLP 分析功能：
- spaCy + transformers 语义理解
- jieba 中文分词优化
- sentence-transformers 高级相似度计算
- scikit-learn 机器学习分类

作者：@MapleEve
日期：2025-08-15
"""

import asyncio
import logging
import os
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# 完整版 NLP 依赖
try:
    # Advanced NLP libraries (full mode)
    import spacy
    import jieba
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np

    HAS_FULL_NLP = True
except ImportError as e:
    # 优雅降级到基础模式
    logging.warning(f"Full NLP dependencies not available: {e}")
    HAS_FULL_NLP = False
    spacy = None
    jieba = None
    SentenceTransformer = None
    cosine_similarity = None
    np = None

# 核心依赖 (总是可用)
try:
    from ..architecture.services import NLPService
    from ..data_types.core_types import NLPConfig, NLPProvider
except ImportError:
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    from architecture.services import NLPService
    from data_types.core_types import NLPConfig, NLPProvider


@dataclass
class NLPAnalysisResult:
    """NLP 分析结果"""

    text: str
    language: str
    entities: List[Dict[str, Any]]
    sentiment: float
    keywords: List[str]
    embeddings: Optional[np.ndarray] = None
    confidence: float = 0.0


@dataclass
class SemanticSimilarityResult:
    """语义相似度分析结果"""

    text_a: str
    text_b: str
    similarity_score: float
    semantic_features: Dict[str, Any]
    confidence: float


class NLPLanguage(Enum):
    """支持的语言类型"""

    CHINESE = "zh"
    ENGLISH = "en"
    AUTO = "auto"


class EnhancedNLPService(NLPService):
    """
    增强版 NLP 服务实现

    完整功能版本，利用所有高级 NLP 库：
    - spaCy: 实体识别和语法分析
    - jieba: 中文智能分词
    - sentence-transformers: 语义相似度
    - scikit-learn: 文本分类和聚类
    """

    def __init__(self, config: Optional[NLPConfig] = None):
        """
        初始化增强版 NLP 服务

        Args:
            config: NLP 配置参数
        """
        super().__init__("EnhancedNLPService")
        self.config = config or {}

        # 模型缓存
        self._spacy_models = {}
        self._sentence_model = None
        self._jieba_initialized = False

        # 性能统计
        self.stats = {
            "total_analyses": 0,
            "semantic_comparisons": 0,
            "entity_extractions": 0,
            "average_processing_time": 0.0,
        }

        if HAS_FULL_NLP:
            logging.info("🚀 EnhancedNLPService: Full NLP mode activated")
        else:
            logging.warning("⚠️ EnhancedNLPService: Fallback to basic mode")

    async def async_initialize(self) -> None:
        """异步初始化 NLP 模型"""
        if not HAS_FULL_NLP:
            logging.info("📝 NLP Service: Using basic text processing mode")
            self._mark_initialized()
            return

        try:
            # 初始化 sentence-transformers 模型
            if SentenceTransformer:
                logging.info("🔄 Loading sentence-transformers model...")
                self._sentence_model = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: SentenceTransformer("all-MiniLM-L6-v2")
                )
                logging.info("✅ Sentence transformer loaded")

            # 初始化 jieba 中文分词
            if jieba and not self._jieba_initialized:
                logging.info("🔄 Initializing jieba Chinese segmentation...")
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: jieba.initialize()
                )
                self._jieba_initialized = True
                logging.info("✅ Jieba initialized")

            # 预加载 spaCy 模型 (异步)
            await self._preload_spacy_models()

            self._mark_initialized()
            logging.info("🎯 EnhancedNLPService: Full initialization complete")

        except Exception as e:
            logging.error(f"❌ NLP Service initialization failed: {e}")
            # 降级到基础模式
            self._mark_initialized()

    async def _preload_spacy_models(self) -> None:
        """预加载 spaCy 语言模型"""
        if not spacy:
            return

        models_to_load = ["en_core_web_sm", "zh_core_web_sm"]

        for model_name in models_to_load:
            try:
                logging.info(f"🔄 Loading spaCy model: {model_name}")
                nlp = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: spacy.load(model_name)
                )
                self._spacy_models[model_name] = nlp
                logging.info(f"✅ spaCy model loaded: {model_name}")
            except OSError:
                logging.warning(f"⚠️ spaCy model not found: {model_name}, skipping...")

    async def analyze_text(self, text: str, language: str = "auto") -> Dict[str, Any]:
        """
        完整版文本分析

        Args:
            text: 要分析的文本
            language: 语言代码 ('en', 'zh', 'auto')

        Returns:
            详细的文本分析结果
        """
        start_time = asyncio.get_event_loop().time()

        try:
            # 自动语言检测
            detected_lang = (
                self._detect_language(text) if language == "auto" else language
            )

            # 分析结果容器
            result = {
                "text": text,
                "language": detected_lang,
                "entities": [],
                "keywords": [],
                "sentiment": 0.0,
                "confidence": 0.0,
            }

            if HAS_FULL_NLP:
                # 完整版分析
                result = await self._analyze_text_full(text, detected_lang)
            else:
                # 基础版分析
                result = await self._analyze_text_basic(text, detected_lang)

            # 更新统计
            self.stats["total_analyses"] += 1
            processing_time = asyncio.get_event_loop().time() - start_time
            self._update_avg_processing_time(processing_time)

            return result

        except Exception as e:
            logging.error(f"❌ Text analysis failed: {e}")
            return {
                "text": text,
                "language": language,
                "entities": [],
                "keywords": [],
                "sentiment": 0.0,
                "confidence": 0.0,
                "error": str(e),
            }

    async def _analyze_text_full(self, text: str, language: str) -> Dict[str, Any]:
        """完整版文本分析（利用所有 NLP 库）"""

        # 实体识别 (spaCy)
        entities = await self._extract_entities_spacy(text, language)

        # 关键词提取 (jieba + 频率分析)
        keywords = await self._extract_keywords_advanced(text, language)

        # 情感分析 (基于关键词和规则)
        sentiment = await self._analyze_sentiment_advanced(text, language)

        # 语义向量 (sentence-transformers)
        embeddings = await self._get_text_embeddings(text)

        return {
            "text": text,
            "language": language,
            "entities": entities,
            "keywords": keywords,
            "sentiment": sentiment,
            "embeddings": embeddings.tolist() if embeddings is not None else None,
            "confidence": 0.9,  # 完整版高置信度
            "processing_mode": "full",
        }

    async def _analyze_text_basic(self, text: str, language: str) -> Dict[str, Any]:
        """基础版文本分析（仅使用内置功能）"""

        # 简单关键词提取 (基于正则表达式)
        keywords = re.findall(r"\b[A-Za-z中文]{3,}\b", text)[:10]

        # 简单情感分析 (基于关键词匹配)
        positive_words = ["好", "优秀", "正常", "成功", "有效"]
        negative_words = ["坏", "错误", "失败", "无效", "问题"]

        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)

        sentiment = (
            0.1 if pos_count > neg_count else -0.1 if neg_count > pos_count else 0.0
        )

        return {
            "text": text,
            "language": language,
            "entities": [],  # 基础版不支持实体识别
            "keywords": keywords,
            "sentiment": sentiment,
            "embeddings": None,
            "confidence": 0.6,  # 基础版中等置信度
            "processing_mode": "basic",
        }

    async def compare_texts(self, text_a: str, text_b: str) -> float:
        """
        高级语义相似度比较

        Args:
            text_a: 第一个文本
            text_b: 第二个文本

        Returns:
            相似度分数 (0.0-1.0)
        """
        try:
            self.stats["semantic_comparisons"] += 1

            if HAS_FULL_NLP and self._sentence_model:
                # 完整版：使用 sentence-transformers
                return await self._compare_texts_semantic(text_a, text_b)
            else:
                # 基础版：使用字符级相似度
                return await self._compare_texts_basic(text_a, text_b)

        except Exception as e:
            logging.error(f"❌ Text comparison failed: {e}")
            return 0.0

    async def _compare_texts_semantic(self, text_a: str, text_b: str) -> float:
        """语义级文本相似度比较"""

        # 获取文本向量
        embeddings_a = await self._get_text_embeddings(text_a)
        embeddings_b = await self._get_text_embeddings(text_b)

        if embeddings_a is None or embeddings_b is None:
            return 0.0

        # 计算余弦相似度
        similarity = cosine_similarity(
            embeddings_a.reshape(1, -1), embeddings_b.reshape(1, -1)
        )[0][0]

        return float(similarity)

    async def _compare_texts_basic(self, text_a: str, text_b: str) -> float:
        """基础文本相似度比较"""

        # 简单的字符集合相似度
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())

        if not words_a and not words_b:
            return 1.0

        intersection = len(words_a & words_b)
        union = len(words_a | words_b)

        return intersection / union if union > 0 else 0.0

    async def _get_text_embeddings(self, text: str) -> Optional[np.ndarray]:
        """获取文本的语义向量表示"""
        if not self._sentence_model or not HAS_FULL_NLP:
            return None

        try:
            # 在线程池中运行编码
            embeddings = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self._sentence_model.encode([text])
            )
            return embeddings[0]

        except Exception as e:
            logging.error(f"❌ Text embedding failed: {e}")
            return None

    async def extract_device_features(self, device_description: str) -> Dict[str, Any]:
        """
        从设备描述中提取特征

        Args:
            device_description: 设备描述文本

        Returns:
            提取的设备特征和能力
        """
        try:
            # 通用文本分析
            analysis_result = await self.analyze_text(device_description, "auto")

            # 设备特定特征提取
            device_features = {
                "platform_hints": [],
                "io_types": [],
                "capabilities": [],
                "device_category": "unknown",
            }

            # 平台提示词匹配
            platform_patterns = {
                "switch": r"开关|控制|打开|关闭|切换",
                "sensor": r"传感器|检测|监测|温度|湿度|数值",
                "light": r"灯光|亮度|颜色|RGB|调光",
                "cover": r"窗帘|遮阳|卷帘|开关窗帘",
            }

            for platform, pattern in platform_patterns.items():
                if re.search(pattern, device_description):
                    device_features["platform_hints"].append(platform)

            # IO类型识别
            io_patterns = {
                "digital": r"开关|数字|状态|布尔",
                "analog": r"模拟|数值|温度|湿度|电压",
                "rgb": r"RGB|颜色|色彩",
                "pwm": r"PWM|调光|亮度",
            }

            for io_type, pattern in io_patterns.items():
                if re.search(pattern, device_description):
                    device_features["io_types"].append(io_type)

            # 合并分析结果
            device_features.update(
                {
                    "text_analysis": analysis_result,
                    "confidence": analysis_result.get("confidence", 0.0),
                }
            )

            return device_features

        except Exception as e:
            logging.error(f"❌ Device feature extraction failed: {e}")
            return {
                "platform_hints": [],
                "io_types": [],
                "capabilities": [],
                "device_category": "unknown",
                "confidence": 0.0,
                "error": str(e),
            }

    async def _extract_entities_spacy(
        self, text: str, language: str
    ) -> List[Dict[str, Any]]:
        """使用 spaCy 提取命名实体"""
        model_name = "zh_core_web_sm" if language == "zh" else "en_core_web_sm"
        nlp = self._spacy_models.get(model_name)

        if not nlp:
            return []

        try:
            # 在线程池中运行 spaCy 处理
            doc = await asyncio.get_event_loop().run_in_executor(
                None, lambda: nlp(text)
            )

            entities = []
            for ent in doc.ents:
                entities.append(
                    {
                        "text": ent.text,
                        "label": ent.label_,
                        "start": ent.start_char,
                        "end": ent.end_char,
                        "confidence": ent._.get("confidence", 0.8),
                    }
                )

            self.stats["entity_extractions"] += len(entities)
            return entities

        except Exception as e:
            logging.error(f"❌ spaCy entity extraction failed: {e}")
            return []

    async def _extract_keywords_advanced(self, text: str, language: str) -> List[str]:
        """高级关键词提取"""

        if language == "zh" and jieba and self._jieba_initialized:
            # 中文分词
            keywords = await asyncio.get_event_loop().run_in_executor(
                None, lambda: list(jieba.cut(text))
            )
            # 过滤和排序
            keywords = [word.strip() for word in keywords if len(word.strip()) > 1]
            return keywords[:10]
        else:
            # 英文关键词提取（基于正则表达式）
            keywords = re.findall(r"\b[A-Za-z]{3,}\b", text)
            return list(set(keywords))[:10]

    async def _analyze_sentiment_advanced(self, text: str, language: str) -> float:
        """高级情感分析"""

        # 基于关键词的情感分析 (可以扩展为机器学习模型)
        if language == "zh":
            positive_words = ["好", "优秀", "正常", "成功", "有效", "稳定", "可靠"]
            negative_words = ["坏", "错误", "失败", "无效", "问题", "故障", "异常"]
        else:
            positive_words = [
                "good",
                "excellent",
                "normal",
                "success",
                "effective",
                "stable",
                "reliable",
            ]
            negative_words = [
                "bad",
                "error",
                "failure",
                "invalid",
                "problem",
                "fault",
                "abnormal",
            ]

        pos_count = sum(1 for word in positive_words if word in text.lower())
        neg_count = sum(1 for word in negative_words if word in text.lower())

        total = pos_count + neg_count
        if total == 0:
            return 0.0

        return (pos_count - neg_count) / total

    def _detect_language(self, text: str) -> str:
        """简单的语言检测"""
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        total_chars = len(text)

        if chinese_chars / total_chars > 0.1:
            return "zh"
        else:
            return "en"

    def get_supported_providers(self) -> List[NLPProvider]:
        """获取支持的 NLP 提供商"""
        providers = [NLPProvider.NONE]  # 基础模式总是支持

        if HAS_FULL_NLP:
            if spacy:
                providers.append(NLPProvider.SPACY)
            if self._sentence_model:
                providers.append(NLPProvider.TRANSFORMERS)

        return providers

    async def warm_up_models(self, providers: List[NLPProvider]) -> None:
        """预热 NLP 模型"""
        if not HAS_FULL_NLP:
            return

        for provider in providers:
            if provider == NLPProvider.SPACY:
                await self._preload_spacy_models()
            elif provider == NLPProvider.TRANSFORMERS and not self._sentence_model:
                # 加载 sentence-transformers 模型
                self._sentence_model = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: SentenceTransformer("all-MiniLM-L6-v2")
                )

    async def async_cleanup(self) -> None:
        """清理 NLP 资源"""
        self._spacy_models.clear()
        self._sentence_model = None
        logging.info("🧹 NLP Service: Resources cleaned up")

    def _update_avg_processing_time(self, processing_time: float) -> None:
        """更新平均处理时间统计"""
        total_analyses = self.stats["total_analyses"]
        current_avg = self.stats["average_processing_time"]

        # 滚动平均
        new_avg = (
            (current_avg * (total_analyses - 1)) + processing_time
        ) / total_analyses
        self.stats["average_processing_time"] = new_avg

    async def health_check(self) -> bool:
        """NLP 服务健康检查"""
        try:
            # 测试基本文本分析功能
            test_result = await self.analyze_text("测试 test", "auto")
            return test_result.get("confidence", 0) > 0
        except Exception:
            return False


# 工厂函数
def create_enhanced_nlp_service(
    config: Optional[NLPConfig] = None,
) -> EnhancedNLPService:
    """
    创建增强版 NLP 服务实例

    Args:
        config: NLP 配置参数

    Returns:
        配置好的增强版 NLP 服务
    """
    service = EnhancedNLPService(config)

    if HAS_FULL_NLP:
        logging.info("🚀 Created EnhancedNLPService in FULL mode")
    else:
        logging.info("📝 Created EnhancedNLPService in BASIC mode")

    return service


if __name__ == "__main__":
    # 测试增强版 NLP 服务
    async def test_enhanced_nlp():
        service = create_enhanced_nlp_service()

        print("🧪 测试增强版 NLP 服务...")

        # 初始化服务
        await service.async_initialize()

        # 健康检查
        health = await service.health_check()
        print(f"健康检查: {health}")

        if health:
            # 测试文本分析
            test_texts = [
                "智能开关控制器，支持远程开关控制",
                "温湿度传感器，实时监测环境数据",
                "RGB LED light with brightness control",
            ]

            for text in test_texts:
                print(f"\n📝 分析文本: {text}")
                result = await service.analyze_text(text, "auto")
                print(f"   语言: {result['language']}")
                print(f"   关键词: {result['keywords'][:5]}")
                print(f"   情感: {result['sentiment']:.3f}")
                print(f"   置信度: {result['confidence']:.3f}")
                print(f"   处理模式: {result.get('processing_mode', 'unknown')}")

            # 测试文本相似度
            print(f"\n🔍 相似度测试:")
            similarity = await service.compare_texts("智能开关控制", "开关控制器")
            print(f"   相似度分数: {similarity:.3f}")

            # 测试设备特征提取
            print(f"\n🏠 设备特征提取:")
            features = await service.extract_device_features(
                "智能RGB灯光调节器，支持亮度和颜色控制"
            )
            print(f"   平台提示: {features['platform_hints']}")
            print(f"   IO类型: {features['io_types']}")
            print(f"   置信度: {features['confidence']:.3f}")

        await service.async_cleanup()
        print("\n✅ 测试完成")

    # 运行测试
    asyncio.run(test_enhanced_nlp())
