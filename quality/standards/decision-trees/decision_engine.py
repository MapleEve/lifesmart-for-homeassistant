#!/usr/bin/env python3
"""
开发场景决策引擎 - Phase 3.2 标准体系核心组件

基于Phase 1-2成功经验，建立标准化的开发场景决策支持系统。
为各种开发情况提供专业指导和最佳实践推荐。

Version: 1.0.0
Created: 2025-08-14
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ScenarioType(Enum):
    """开发场景类型"""

    HARDCODE_ELIMINATION = "hardcode_elimination"
    ARCHITECTURE_REFACTOR = "architecture_refactor"
    TESTING_STRATEGY = "testing_strategy"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    ERROR_HANDLING = "error_handling"
    NEW_FEATURE_DEVELOPMENT = "new_feature_development"
    CODE_QUALITY_IMPROVEMENT = "code_quality_improvement"
    MAINTENANCE_TASK = "maintenance_task"


class DecisionType(Enum):
    """决策节点类型"""

    CONDITION = "condition"  # 条件判断节点
    ACTION = "action"  # 行动建议节点
    BRANCH = "branch"  # 分支选择节点
    REFERENCE = "reference"  # 参考资料节点


class ConfidenceLevel(Enum):
    """置信度级别"""

    HIGH = "high"  # 90%+ 置信度
    MEDIUM = "medium"  # 70-90% 置信度
    LOW = "low"  # 50-70% 置信度
    UNCERTAIN = "uncertain"  # <50% 置信度


@dataclass
class DecisionNode:
    """决策树节点"""

    id: str
    title: str
    node_type: DecisionType
    description: str
    conditions: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    next_nodes: Dict[str, str] = field(default_factory=dict)  # 条件 -> 下一节点ID
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    evidence: List[str] = field(default_factory=list)  # 支持证据
    best_practices: List[str] = field(default_factory=list)  # 相关最佳实践ID

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "title": self.title,
            "node_type": self.node_type.value,
            "description": self.description,
            "conditions": self.conditions,
            "actions": self.actions,
            "next_nodes": self.next_nodes,
            "confidence": self.confidence.value,
            "evidence": self.evidence,
            "best_practices": self.best_practices,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "DecisionNode":
        """从字典创建实例"""
        return cls(
            id=data["id"],
            title=data["title"],
            node_type=DecisionType(data["node_type"]),
            description=data["description"],
            conditions=data.get("conditions", []),
            actions=data.get("actions", []),
            next_nodes=data.get("next_nodes", {}),
            confidence=ConfidenceLevel(data.get("confidence", "medium")),
            evidence=data.get("evidence", []),
            best_practices=data.get("best_practices", []),
        )


@dataclass
class DecisionTree:
    """决策树完整定义"""

    id: str
    scenario_type: ScenarioType
    title: str
    description: str
    root_node_id: str
    nodes: Dict[str, DecisionNode] = field(default_factory=dict)
    metadata: Dict = field(default_factory=dict)
    created_date: datetime = field(default_factory=datetime.now)
    updated_date: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "scenario_type": self.scenario_type.value,
            "title": self.title,
            "description": self.description,
            "root_node_id": self.root_node_id,
            "nodes": {node_id: node.to_dict() for node_id, node in self.nodes.items()},
            "metadata": self.metadata,
            "created_date": self.created_date.isoformat(),
            "updated_date": self.updated_date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "DecisionTree":
        """从字典创建实例"""
        tree = cls(
            id=data["id"],
            scenario_type=ScenarioType(data["scenario_type"]),
            title=data["title"],
            description=data["description"],
            root_node_id=data["root_node_id"],
            metadata=data.get("metadata", {}),
            created_date=datetime.fromisoformat(data["created_date"]),
            updated_date=datetime.fromisoformat(data["updated_date"]),
        )

        # 加载节点
        for node_id, node_data in data.get("nodes", {}).items():
            tree.nodes[node_id] = DecisionNode.from_dict(node_data)

        return tree


@dataclass
class ScenarioContext:
    """场景上下文信息"""

    file_paths: List[str] = field(default_factory=list)
    problem_description: str = ""
    current_state: Dict = field(default_factory=dict)
    constraints: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    available_resources: List[str] = field(default_factory=list)
    risk_tolerance: str = "medium"  # low, medium, high
    timeline: str = ""

    def get_context_hash(self) -> str:
        """获取上下文哈希值用于缓存"""
        context_str = (
            f"{self.problem_description}_{len(self.file_paths)}_{self.risk_tolerance}"
        )
        return str(hash(context_str) % 10000)


@dataclass
class DecisionResult:
    """决策结果"""

    scenario_type: ScenarioType
    recommended_actions: List[str]
    next_steps: List[str]
    confidence: ConfidenceLevel
    reasoning: List[str]
    best_practices: List[str]
    warnings: List[str] = field(default_factory=list)
    estimated_effort: str = ""
    success_criteria: List[str] = field(default_factory=list)


class ScenarioDetector:
    """场景检测器 - 识别开发场景类型"""

    def __init__(self):
        """初始化检测器"""
        self.scenario_patterns = {
            ScenarioType.HARDCODE_ELIMINATION: [
                "硬编码",
                "hardcode",
                "常量",
                "const",
                "magic number",
                "字符串常量",
            ],
            ScenarioType.ARCHITECTURE_REFACTOR: [
                "重构",
                "refactor",
                "架构",
                "architecture",
                "设计模式",
                "代码结构",
            ],
            ScenarioType.TESTING_STRATEGY: [
                "测试",
                "test",
                "单元测试",
                "集成测试",
                "覆盖率",
                "mock",
                "fixture",
            ],
            ScenarioType.PERFORMANCE_OPTIMIZATION: [
                "性能",
                "performance",
                "优化",
                "慢",
                "内存",
                "CPU",
                "响应时间",
            ],
            ScenarioType.ERROR_HANDLING: [
                "错误处理",
                "异常",
                "exception",
                "error",
                "fail",
                "try-catch",
            ],
            ScenarioType.NEW_FEATURE_DEVELOPMENT: [
                "新功能",
                "feature",
                "需求",
                "开发",
                "添加",
                "实现",
            ],
            ScenarioType.CODE_QUALITY_IMPROVEMENT: [
                "代码质量",
                "code quality",
                "clean code",
                "可读性",
                "维护性",
            ],
        }

    def detect_scenario(
        self, context: ScenarioContext
    ) -> List[tuple[ScenarioType, float]]:
        """检测场景类型，返回类型和置信度"""
        scores = {}

        # 分析问题描述
        problem_text = context.problem_description.lower()

        for scenario_type, keywords in self.scenario_patterns.items():
            score = 0.0
            for keyword in keywords:
                if keyword.lower() in problem_text:
                    score += 1.0

            # 归一化分数
            if keywords:
                scores[scenario_type] = score / len(keywords)

        # 基于文件路径增加权重
        for file_path in context.file_paths:
            file_path_lower = file_path.lower()

            if "test" in file_path_lower:
                scores[ScenarioType.TESTING_STRATEGY] = (
                    scores.get(ScenarioType.TESTING_STRATEGY, 0) + 0.3
                )

            if "const" in file_path_lower:
                scores[ScenarioType.HARDCODE_ELIMINATION] = (
                    scores.get(ScenarioType.HARDCODE_ELIMINATION, 0) + 0.3
                )

        # 排序并返回
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [
            (scenario_type, min(confidence, 1.0))
            for scenario_type, confidence in sorted_scores
            if confidence > 0.1
        ]


class DecisionEngine:
    """决策引擎主类"""

    def __init__(self, storage_path: Path):
        """初始化决策引擎"""
        self.storage_path = storage_path
        self.decision_trees: Dict[str, DecisionTree] = {}
        self.scenario_detector = ScenarioDetector()
        self._ensure_storage_path()
        self._load_decision_trees()

    def _ensure_storage_path(self) -> None:
        """确保存储路径存在"""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        (self.storage_path / "scenarios").mkdir(exist_ok=True)

    def _load_decision_trees(self) -> None:
        """加载决策树"""
        scenarios_path = self.storage_path / "scenarios"

        for tree_file in scenarios_path.glob("*.json"):
            try:
                with open(tree_file, "r", encoding="utf-8") as f:
                    tree_data = json.load(f)
                    tree = DecisionTree.from_dict(tree_data)
                    self.decision_trees[tree.id] = tree
                logger.info(f"加载决策树: {tree.title}")
            except Exception as e:
                logger.error(f"加载决策树失败 {tree_file}: {e}")

    def _save_decision_tree(self, tree: DecisionTree) -> None:
        """保存单个决策树"""
        tree_file = self.storage_path / "scenarios" / f"{tree.id}.json"
        try:
            with open(tree_file, "w", encoding="utf-8") as f:
                json.dump(tree.to_dict(), f, ensure_ascii=False, indent=2)
            logger.info(f"保存决策树: {tree.title}")
        except Exception as e:
            logger.error(f"保存决策树失败: {e}")

    def add_decision_tree(self, tree: DecisionTree) -> bool:
        """添加新的决策树"""
        if tree.id in self.decision_trees:
            logger.error(f"决策树ID已存在: {tree.id}")
            return False

        # 验证决策树完整性
        if not self._validate_decision_tree(tree):
            return False

        tree.updated_date = datetime.now()
        self.decision_trees[tree.id] = tree
        self._save_decision_tree(tree)
        return True

    def _validate_decision_tree(self, tree: DecisionTree) -> bool:
        """验证决策树完整性"""
        # 检查根节点是否存在
        if tree.root_node_id not in tree.nodes:
            logger.error(f"根节点不存在: {tree.root_node_id}")
            return False

        # 检查节点引用的完整性
        for node in tree.nodes.values():
            for next_node_id in node.next_nodes.values():
                if next_node_id not in tree.nodes:
                    logger.error(f"引用的节点不存在: {next_node_id}")
                    return False

        return True

    def make_decision(self, context: ScenarioContext) -> DecisionResult:
        """为给定上下文做出决策"""

        # 检测场景类型
        detected_scenarios = self.scenario_detector.detect_scenario(context)

        if not detected_scenarios:
            return self._create_fallback_result(context)

        # 选择最匹配的场景
        primary_scenario, confidence = detected_scenarios[0]

        # 查找对应的决策树
        matching_tree = self._find_matching_tree(primary_scenario)

        if not matching_tree:
            return self._create_fallback_result(context, primary_scenario)

        # 遍历决策树
        return self._traverse_decision_tree(matching_tree, context, confidence)

    def _find_matching_tree(
        self, scenario_type: ScenarioType
    ) -> Optional[DecisionTree]:
        """查找匹配的决策树"""
        for tree in self.decision_trees.values():
            if tree.scenario_type == scenario_type:
                return tree
        return None

    def _traverse_decision_tree(
        self, tree: DecisionTree, context: ScenarioContext, base_confidence: float
    ) -> DecisionResult:
        """遍历决策树并生成结果"""

        current_node_id = tree.root_node_id
        path = []
        recommended_actions = []
        reasoning = []
        best_practices = []
        warnings = []

        # 最大遍历深度防止死循环
        max_depth = 20
        depth = 0

        while current_node_id and depth < max_depth:
            if current_node_id not in tree.nodes:
                warnings.append(f"决策树节点缺失: {current_node_id}")
                break

            current_node = tree.nodes[current_node_id]
            path.append(current_node.title)

            # 添加节点的行动建议
            recommended_actions.extend(current_node.actions)

            # 添加推理过程
            if current_node.description:
                reasoning.append(f"{current_node.title}: {current_node.description}")

            # 添加最佳实践引用
            best_practices.extend(current_node.best_practices)

            # 确定下一个节点
            next_node_id = self._determine_next_node(current_node, context)

            # 如果是行动节点且没有下一步，结束遍历
            if current_node.node_type == DecisionType.ACTION and not next_node_id:
                break

            current_node_id = next_node_id
            depth += 1

        if depth >= max_depth:
            warnings.append("决策树遍历达到最大深度限制")

        # 确定最终置信度
        final_confidence = self._calculate_final_confidence(base_confidence, len(path))

        return DecisionResult(
            scenario_type=tree.scenario_type,
            recommended_actions=list(set(recommended_actions)),  # 去重
            next_steps=self._generate_next_steps(tree, context),
            confidence=self._confidence_float_to_enum(final_confidence),
            reasoning=reasoning,
            best_practices=list(set(best_practices)),  # 去重
            warnings=warnings,
            estimated_effort=self._estimate_effort(recommended_actions),
            success_criteria=self._generate_success_criteria(tree, context),
        )

    def _determine_next_node(
        self, node: DecisionNode, context: ScenarioContext
    ) -> Optional[str]:
        """根据上下文确定下一个节点"""

        if not node.next_nodes:
            return None

        # 简单的条件匹配逻辑
        for condition, next_node_id in node.next_nodes.items():
            if self._evaluate_condition(condition, context):
                return next_node_id

        # 如果没有匹配的条件，返回默认选项
        return next(iter(node.next_nodes.values())) if node.next_nodes else None

    def _evaluate_condition(self, condition: str, context: ScenarioContext) -> bool:
        """评估条件是否满足"""
        condition_lower = condition.lower()

        # 基于文件数量的条件
        if "多个文件" in condition and len(context.file_paths) > 3:
            return True
        if "单个文件" in condition and len(context.file_paths) <= 1:
            return True

        # 基于风险承受度的条件
        if "低风险" in condition and context.risk_tolerance == "low":
            return True
        if "高风险" in condition and context.risk_tolerance == "high":
            return True

        # 基于时间线的条件
        if "紧急" in condition and "急" in context.timeline:
            return True

        return False

    def _calculate_final_confidence(
        self, base_confidence: float, path_length: int
    ) -> float:
        """计算最终置信度"""
        # 路径越长，置信度稍微降低
        confidence_penalty = min(0.1, path_length * 0.01)
        return max(0.1, base_confidence - confidence_penalty)

    def _confidence_float_to_enum(self, confidence: float) -> ConfidenceLevel:
        """将浮点置信度转换为枚举"""
        if confidence >= 0.9:
            return ConfidenceLevel.HIGH
        elif confidence >= 0.7:
            return ConfidenceLevel.MEDIUM
        elif confidence >= 0.5:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNCERTAIN

    def _generate_next_steps(
        self, tree: DecisionTree, context: ScenarioContext
    ) -> List[str]:
        """生成下一步行动"""
        steps = ["审查推荐的行动建议", "评估所需资源和时间", "制定详细实施计划"]

        if tree.scenario_type == ScenarioType.HARDCODE_ELIMINATION:
            steps.extend(
                [
                    "扫描代码识别所有硬编码位置",
                    "设计常量结构和命名规范",
                    "执行批量替换操作",
                ]
            )

        return steps

    def _estimate_effort(self, actions: List[str]) -> str:
        """估算工作量"""
        action_count = len(actions)

        if action_count <= 3:
            return "1-2小时"
        elif action_count <= 6:
            return "半天"
        elif action_count <= 10:
            return "1-2天"
        else:
            return "3天以上"

    def _generate_success_criteria(
        self, tree: DecisionTree, context: ScenarioContext
    ) -> List[str]:
        """生成成功标准"""
        criteria = ["所有推荐行动已完成", "代码质量检查通过", "测试覆盖率保持或提升"]

        if tree.scenario_type == ScenarioType.HARDCODE_ELIMINATION:
            criteria.extend(
                ["硬编码数量减少 > 90%", "常量定义符合命名规范", "相关测试用例已更新"]
            )
        elif tree.scenario_type == ScenarioType.ARCHITECTURE_REFACTOR:
            criteria.extend(
                ["代码复杂度显著降低", "模块职责更加清晰", "性能指标无明显下降"]
            )

        return criteria

    def _create_fallback_result(
        self, context: ScenarioContext, scenario_type: Optional[ScenarioType] = None
    ) -> DecisionResult:
        """创建兜底决策结果"""

        return DecisionResult(
            scenario_type=scenario_type or ScenarioType.CODE_QUALITY_IMPROVEMENT,
            recommended_actions=[
                "分析具体问题和需求",
                "查阅相关最佳实践文档",
                "制定分步实施计划",
                "寻求专家意见和指导",
            ],
            next_steps=[
                "明确问题定义和目标",
                "收集更多上下文信息",
                "选择合适的解决方案",
            ],
            confidence=ConfidenceLevel.LOW,
            reasoning=["未找到匹配的决策树，提供通用建议"],
            best_practices=[],
            warnings=["建议获取更多上下文信息以获得更精确的指导"],
            estimated_effort="待评估",
            success_criteria=["问题得到有效解决", "代码质量得到改善"],
        )

    def get_scenario_types(self) -> List[ScenarioType]:
        """获取所有支持的场景类型"""
        return list(set(tree.scenario_type for tree in self.decision_trees.values()))

    def get_tree_by_scenario(
        self, scenario_type: ScenarioType
    ) -> Optional[DecisionTree]:
        """根据场景类型获取决策树"""
        return self._find_matching_tree(scenario_type)


def create_hardcode_elimination_tree() -> DecisionTree:
    """创建硬编码消除决策树"""

    # 根节点：识别硬编码类型
    root_node = DecisionNode(
        id="hardcode_root",
        title="硬编码识别与分析",
        node_type=DecisionType.CONDITION,
        description="分析硬编码的类型和分布情况",
        conditions=["存在字符串硬编码", "存在数值硬编码", "存在配置硬编码"],
        actions=["扫描代码中的硬编码", "分析硬编码的类型和用途", "评估修复的优先级"],
        next_nodes={
            "多个文件": "hardcode_batch",
            "单个文件": "hardcode_single",
            "配置相关": "hardcode_config",
        },
        confidence=ConfidenceLevel.HIGH,
        evidence=["Phase 1成功消除98个硬编码", "建立了200+专业常量"],
        best_practices=["phase1_constant_extraction", "phase1_mapping_driven_design"],
    )

    # 批量处理节点
    batch_node = DecisionNode(
        id="hardcode_batch",
        title="批量硬编码消除",
        node_type=DecisionType.ACTION,
        description="对多个文件中的硬编码进行批量处理",
        actions=[
            "建立常量分类体系",
            "在const.py中定义统一常量",
            "使用批量替换工具",
            "逐个验证功能正确性",
            "更新相关测试用例",
        ],
        confidence=ConfidenceLevel.HIGH,
        evidence=["Phase 1成功经验", "5个文件12处硬编码批量修复"],
        best_practices=["phase1_constant_extraction"],
    )

    # 单文件处理节点
    single_node = DecisionNode(
        id="hardcode_single",
        title="单文件硬编码消除",
        node_type=DecisionType.ACTION,
        description="对单个文件中的硬编码进行精细处理",
        actions=[
            "分析硬编码的上下文",
            "设计合适的常量名称",
            "手动替换并验证",
            "确保代码逻辑不变",
        ],
        confidence=ConfidenceLevel.HIGH,
        best_practices=["phase1_constant_extraction"],
    )

    # 配置相关节点
    config_node = DecisionNode(
        id="hardcode_config",
        title="配置硬编码处理",
        node_type=DecisionType.ACTION,
        description="处理配置相关的硬编码",
        actions=[
            "识别配置项和默认值",
            "建立配置常量定义",
            "考虑配置文件外部化",
            "保持向后兼容性",
        ],
        confidence=ConfidenceLevel.MEDIUM,
        best_practices=["phase1_constant_extraction"],
    )

    # 创建决策树
    tree = DecisionTree(
        id="hardcode_elimination_v1",
        scenario_type=ScenarioType.HARDCODE_ELIMINATION,
        title="硬编码消除标准决策流程",
        description="基于Phase 1成功经验制定的硬编码消除标准化流程",
        root_node_id="hardcode_root",
        metadata={
            "version": "1.0",
            "based_on": "Phase 1 经验",
            "success_rate": "100%",
            "avg_time": "2-4小时",
        },
    )

    # 添加节点
    tree.nodes = {
        "hardcode_root": root_node,
        "hardcode_batch": batch_node,
        "hardcode_single": single_node,
        "hardcode_config": config_node,
    }

    return tree


if __name__ == "__main__":
    # 示例使用
    storage_path = Path("quality/standards/decision-trees")
    engine = DecisionEngine(storage_path)

    # 创建并添加硬编码消除决策树
    hardcode_tree = create_hardcode_elimination_tree()
    if engine.add_decision_tree(hardcode_tree):
        print(f"成功添加决策树: {hardcode_tree.title}")

    # 测试决策过程
    context = ScenarioContext(
        file_paths=["const.py", "mapping.py", "switch.py"],
        problem_description="代码中存在大量硬编码字符串，需要进行标准化处理",
        risk_tolerance="low",
        timeline="2天内完成",
    )

    result = engine.make_decision(context)
    print(f"\n决策结果:")
    print(f"场景类型: {result.scenario_type.value}")
    print(f"置信度: {result.confidence.value}")
    print(f"推荐行动: {result.recommended_actions}")
    print(f"预估工作量: {result.estimated_effort}")
