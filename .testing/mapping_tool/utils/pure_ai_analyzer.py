#!/usr/bin/env python3
"""
Agent3: 独立分析vs项目配置对比分析器
基于Agent1和Agent2的结果，进行真实的对比分析
由 @MapleEve 创建和维护
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the custom component to path for importing
sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "../../../custom_components/lifesmart")
)

try:
    from core.config.device_specs import _RAW_DEVICE_DATA
except ImportError as e:
    print(f"⚠️ Import warning: {e}")
    # 如果无法导入，直接读取device_specs.py文件
    device_specs_path = os.path.join(
        os.path.dirname(__file__),
        "../../../custom_components/lifesmart/core/config/device_specs.py",
    )
    _RAW_DEVICE_DATA = {}

    try:
        # 动态导入device_specs
        import importlib.util

        spec = importlib.util.spec_from_file_location("device_specs", device_specs_path)
        if spec and spec.loader:
            device_specs = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(device_specs)
            _RAW_DEVICE_DATA = device_specs._RAW_DEVICE_DATA
            print(f"✅ 成功加载设备数据: {len(_RAW_DEVICE_DATA)}个设备")
    except Exception as import_error:
        print(f"⚠️ 动态导入失败: {import_error}")


class Agent3ComparisonAnalyzer:
    """Agent3: 独立分析vs项目配置对比分析器"""

    def __init__(self):
        self.supported_platforms = {
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
            "valve",
            "air_quality",
            "siren",
            "scene",
            "event",
        }

        self.doc_path = self._get_doc_path()

    def _get_doc_path(self) -> str:
        """获取文档路径"""
        return os.path.join(
            os.path.dirname(__file__), "../../../docs/LifeSmart 智慧设备规格属性说明.md"
        )

    def run_agent1_extract_existing_mappings(self) -> Dict[str, Any]:
        """Agent1: 提取现有映射配置"""
        print("🔄 Agent1: 提取现有映射配置...")

        existing_mappings = {}
        total_ios = 0

        # 从 _RAW_DEVICE_DATA 提取现有映射
        for device_name, device_config in _RAW_DEVICE_DATA.items():
            if not isinstance(device_config, dict):
                continue

            device_mapping = {
                "name": device_config.get("name", device_name),
                "platforms": {},
            }

            # 遍历所有平台配置
            for key, value in device_config.items():
                if key in ["name", "versioned", "dynamic"]:
                    continue

                if key in self.supported_platforms and isinstance(value, dict):
                    ios = []
                    for io_name, io_config in value.items():
                        ios.append(
                            {
                                "name": io_name,
                                "config": (
                                    io_config
                                    if isinstance(io_config, dict)
                                    else {"raw": io_config}
                                ),
                            }
                        )
                        total_ios += 1

                    if ios:
                        device_mapping["platforms"][key] = ios

            if device_mapping["platforms"]:
                existing_mappings[device_name] = device_mapping

        result = {
            "metadata": {
                "agent": "Agent1",
                "task": "Extract existing mappings from project configuration",
                "timestamp": datetime.now().isoformat(),
                "total_devices": len(existing_mappings),
                "total_ios": total_ios,
                "covered_platforms": list(self.supported_platforms),
            },
            "devices": existing_mappings,
        }

        print(f"✅ Agent1 完成: {len(existing_mappings)}个设备, {total_ios}个IO")
        return result

    def run_agent2_independent_ai_analysis(self) -> Dict[str, Any]:
        """Agent2: 基于纯文档的独立AI分析"""
        print("🧠 Agent2: 执行独立AI分析...")

        # 解析文档内容
        doc_devices = self._parse_documentation()

        ai_allocations = {}
        total_analysis_ios = 0

        for device_name, device_info in doc_devices.items():
            ios = device_info.get("ios", [])
            if not ios:
                continue

            # AI分析每个IO应该分配到哪个平台
            platform_analysis = {}

            for io_info in ios:
                io_name = io_info["name"]
                io_description = io_info.get("description", "")

                # 基于AI逻辑分析平台分配
                suggested_platform = self._ai_analyze_platform(
                    io_name, io_description, io_info
                )

                if suggested_platform:
                    if suggested_platform not in platform_analysis:
                        platform_analysis[suggested_platform] = []

                    platform_analysis[suggested_platform].append(
                        {
                            "io_name": io_name,
                            "description": io_description,
                            "confidence": io_info.get("confidence", 0.8),
                            "reasoning": io_info.get(
                                "reasoning",
                                "Based on IO name and description pattern matching",
                            ),
                        }
                    )

                    total_analysis_ios += 1

            if platform_analysis:
                ai_allocations[device_name] = {
                    "device_name_cn": device_info.get("name_cn", device_name),
                    "total_ios": len(ios),
                    "platform_allocations": platform_analysis,
                    "analysis_confidence": device_info.get("overall_confidence", 0.75),
                }

        result = {
            "metadata": {
                "agent": "Agent2",
                "task": "Independent AI analysis based on pure documentation",
                "timestamp": datetime.now().isoformat(),
                "total_devices": len(ai_allocations),
                "total_ios": total_analysis_ios,
                "analysis_method": "Pure AI reasoning from documentation",
            },
            "device_allocations": ai_allocations,
        }

        print(
            f"✅ Agent2 完成: {len(ai_allocations)}个设备, {total_analysis_ios}个IO分析"
        )
        return result

    def _parse_documentation(self) -> Dict[str, Any]:
        """解析官方文档提取设备和IO信息"""
        doc_devices = {}

        if not os.path.exists(self.doc_path):
            print(f"⚠️ 文档文件不存在: {self.doc_path}")
            return doc_devices

        try:
            with open(self.doc_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 按行分割内容
            lines = content.split("\n")
            current_section = None
            current_devices = []
            in_table = False

            for line in lines:
                line = line.strip()

                # 检测章节标题 (如 "### 2.1 插座系列(Outlet Series)")
                if line.startswith("### 2."):
                    current_section = line
                    current_devices = []
                    in_table = False
                    continue

                # 检测子章节标题 (如 "#### 2.1.1 传统插座系列")
                if line.startswith("#### 2."):
                    in_table = False
                    continue

                # 检测表格开始 (表头行)
                if "| **Devtype/cls**" in line:
                    in_table = True
                    continue

                # 跳过表格分隔符行
                if line.startswith("|---"):
                    continue

                # 解析表格数据行
                if in_table and line.startswith("|") and "**Devtype/cls**" not in line:
                    parts = [p.strip() for p in line.split("|")]
                    if len(parts) >= 6:  # 至少6列：空|设备类型|IO|名称|描述|RW|命令
                        device_types_raw = parts[1]  # Devtype/cls 列
                        io_idx = parts[2]  # IO idx 列
                        io_name = parts[3]  # IO名称 列
                        description = parts[4]  # 属性值描述 列
                        rw = parts[5]  # RW 列

                        # 解析设备类型（可能包含多个用<br/>分隔）
                        device_types = []
                        for dt in device_types_raw.split("<br/>"):
                            dt_clean = dt.replace("`", "").strip()
                            if dt_clean and dt_clean not in device_types:
                                device_types.append(dt_clean)

                        # 解析IO索引（可能包含多个用逗号或空格分隔）
                        io_indices = []
                        for io in io_idx.replace("`", "").replace(",", " ").split():
                            io_clean = io.strip()
                            if io_clean and io_clean not in io_indices:
                                io_indices.append(io_clean)

                        # 为每个设备类型和每个IO创建记录
                        for device_type in device_types:
                            if device_type not in doc_devices:
                                doc_devices[device_type] = {
                                    "name_cn": f"设备{device_type}",
                                    "name_en": device_type,
                                    "section": current_section or "未知章节",
                                    "ios": [],
                                }

                            for io_index in io_indices:
                                # 避免重复添加相同的IO
                                existing_ios = [
                                    io["name"] for io in doc_devices[device_type]["ios"]
                                ]
                                if io_index not in existing_ios:
                                    doc_devices[device_type]["ios"].append(
                                        {
                                            "name": io_index,
                                            "description": io_name,
                                            "rw": rw,
                                            "detail": description,
                                            "confidence": 0.9,  # 基于表格解析的高置信度
                                            "reasoning": f"从文档表格解析: {current_section}",
                                        }
                                    )

            print(f"📚 文档解析完成: 找到 {len(doc_devices)} 个设备类型")
            for device_name, device_info in doc_devices.items():
                io_count = len(device_info["ios"])
                print(f"  - {device_name}: {io_count} 个IO")

        except Exception as e:
            print(f"⚠️ 解析文档失败: {e}")

        return doc_devices

    def _infer_device_code(self, device_name_cn: str) -> str:
        """根据中文设备名推断设备代码"""
        # 简单的映射规则
        mapping = {
            "智慧插座": "SL_OL",
            "智慧开关": "SL_SW_IF",
            "窗帘控制器": "SL_CT",
            "智能灯": "SL_LT",
            "智能面板": "SL_P",
            # 更多映射...
        }

        for cn_name, code in mapping.items():
            if cn_name in device_name_cn:
                return code

        # 默认返回处理过的名称
        return (
            device_name_cn.replace(" ", "_")
            .replace("（", "_")
            .replace("）", "")
            .upper()
        )

    def _ai_analyze_platform(
        self, io_name: str, io_description: str, io_info: Dict
    ) -> Optional[str]:
        """AI分析IO应该分配到哪个平台"""

        # 基于IO名称的模式匹配
        io_name_lower = io_name.lower()
        desc_lower = io_description.lower()

        # Switch platform patterns
        if any(pattern in io_name_lower for pattern in ["o", "switch", "开关", "插座"]):
            if "状态" in desc_lower or "state" in desc_lower:
                return "binary_sensor"  # 状态反馈
            else:
                return "switch"  # 控制

        # Sensor platform patterns
        if any(
            pattern in desc_lower
            for pattern in [
                "温度",
                "temperature",
                "湿度",
                "humidity",
                "电流",
                "current",
                "电压",
                "voltage",
                "功率",
                "power",
            ]
        ):
            return "sensor"

        # Light platform patterns
        if any(
            pattern in io_name_lower
            for pattern in ["r", "g", "b", "w", "c", "brightness", "color"]
        ):
            return "light"

        # Cover platform patterns
        if any(
            pattern in desc_lower
            for pattern in [
                "窗帘",
                "curtain",
                "位置",
                "position",
                "开启",
                "open",
                "关闭",
                "close",
            ]
        ):
            return "cover"

        # Climate platform patterns
        if any(
            pattern in desc_lower
            for pattern in [
                "温度",
                "temperature",
                "模式",
                "mode",
                "制热",
                "heat",
                "制冷",
                "cool",
            ]
        ):
            if "设定" in desc_lower or "set" in desc_lower:
                return "climate"

        # Lock platform patterns
        if any(pattern in desc_lower for pattern in ["锁", "lock", "解锁", "unlock"]):
            return "lock"

        # Fan platform patterns
        if any(pattern in desc_lower for pattern in ["风扇", "fan", "风速", "speed"]):
            return "fan"

        # Number platform patterns
        if any(
            pattern in desc_lower for pattern in ["数值", "number", "设置", "setting"]
        ):
            return "number"

        # Binary sensor patterns
        if any(
            pattern in desc_lower
            for pattern in ["状态", "state", "检测", "detect", "传感", "sensor"]
        ):
            return "binary_sensor"

        # Default fallback based on RW type
        rw = io_info.get("rw", "").upper()
        if rw == "R":
            return "sensor"  # 只读通常是传感器
        elif rw == "W":
            return "switch"  # 只写通常是开关控制
        elif rw == "RW":
            return "switch"  # 可读写通常是开关控制

        return None  # 无法确定

    def run_agent3_comparison_analysis(
        self, agent1_data: Dict, agent2_data: Dict
    ) -> Dict[str, Any]:
        """Agent3: 执行对比分析"""
        print("⚖️ Agent3: 执行对比分析...")

        existing_devices = agent1_data.get("devices", {})
        ai_allocations = agent2_data.get("device_allocations", {})

        comparison_results = []
        match_statistics = {
            "perfect_match": 0,
            "partial_match": 0,
            "platform_mismatch": 0,
            "io_missing": 0,
            "ai_only": 0,
            "existing_only": 0,
        }

        # 获取所有设备名称
        all_devices = set(existing_devices.keys()) | set(ai_allocations.keys())

        for device_name in all_devices:
            existing_config = existing_devices.get(device_name)
            ai_config = ai_allocations.get(device_name)

            comparison = self._compare_device_config(
                device_name, existing_config, ai_config
            )
            comparison_results.append(comparison)

            # 更新统计
            match_type = comparison["match_type"]
            if match_type == "完全匹配":
                match_statistics["perfect_match"] += 1
            elif match_type == "部分匹配":
                match_statistics["partial_match"] += 1
            elif match_type == "平台不匹配":
                match_statistics["platform_mismatch"] += 1
            elif match_type == "IO缺失":
                match_statistics["io_missing"] += 1
            elif match_type == "AI独有":
                match_statistics["ai_only"] += 1
            elif match_type == "现有独有":
                match_statistics["existing_only"] += 1

        # 计算总体匹配率
        total_devices = len(all_devices)
        perfect_rate = (
            match_statistics["perfect_match"] / total_devices
            if total_devices > 0
            else 0
        )

        result = {
            "metadata": {
                "agent": "Agent3",
                "task": "Comparison analysis between existing config and AI suggestions",
                "timestamp": datetime.now().isoformat(),
                "total_devices": total_devices,
                "comparison_count": len(comparison_results),
            },
            "overall_statistics": {
                "total_devices": total_devices,
                "perfect_match_rate": round(perfect_rate * 100, 1),
                "match_distribution": match_statistics,
            },
            "comparison_results": comparison_results,
        }

        print(
            f"✅ Agent3 完成: {total_devices}个设备对比, 完全匹配率: {perfect_rate*100:.1f}%"
        )
        return result

    def _compare_device_config(
        self,
        device_name: str,
        existing_config: Optional[Dict],
        ai_config: Optional[Dict],
    ) -> Dict[str, Any]:
        """比较单个设备的配置"""

        if not existing_config and not ai_config:
            return {
                "device_name": device_name,
                "match_type": "无配置",
                "confidence_score": 0.0,
                "differences": [],
                "existing_platforms": [],
                "ai_platforms": [],
            }

        if not existing_config:
            return {
                "device_name": device_name,
                "match_type": "AI独有",
                "confidence_score": ai_config.get("analysis_confidence", 0.5),
                "differences": ["设备仅存在于AI建议中"],
                "existing_platforms": [],
                "ai_platforms": list(ai_config.get("platform_allocations", {}).keys()),
            }

        if not ai_config:
            return {
                "device_name": device_name,
                "match_type": "现有独有",
                "confidence_score": 0.3,
                "differences": ["设备仅存在于现有配置中"],
                "existing_platforms": list(existing_config.get("platforms", {}).keys()),
                "ai_platforms": [],
            }

        # 两边都有配置，进行详细对比
        existing_platforms = set(existing_config.get("platforms", {}).keys())
        ai_platforms = set(ai_config.get("platform_allocations", {}).keys())

        differences = []

        # 平台对比
        common_platforms = existing_platforms & ai_platforms
        existing_only = existing_platforms - ai_platforms
        ai_only = ai_platforms - existing_platforms

        if existing_only:
            differences.append(f"现有独有平台: {list(existing_only)}")
        if ai_only:
            differences.append(f"AI独有平台: {list(ai_only)}")

        # IO对比
        io_differences = self._compare_ios(existing_config, ai_config)
        differences.extend(io_differences)

        # 确定匹配类型
        if not differences:
            match_type = "完全匹配"
            confidence = 1.0
        elif len(common_platforms) > 0 and len(differences) <= 2:
            match_type = "部分匹配"
            confidence = 0.7
        elif len(common_platforms) == 0:
            match_type = "平台不匹配"
            confidence = 0.2
        else:
            match_type = "显著差异"
            confidence = 0.4

        return {
            "device_name": device_name,
            "match_type": match_type,
            "confidence_score": confidence,
            "differences": differences,
            "existing_platforms": list(existing_platforms),
            "ai_platforms": list(ai_platforms),
            "common_platforms": list(common_platforms),
            "platform_coverage": len(common_platforms)
            / max(len(existing_platforms | ai_platforms), 1),
        }

    def _compare_ios(self, existing_config: Dict, ai_config: Dict) -> List[str]:
        """比较IO配置"""
        differences = []

        existing_ios = set()
        ai_ios = set()

        # 提取现有配置的IO
        for platform_config in existing_config.get("platforms", {}).values():
            for io_info in platform_config:
                existing_ios.add(io_info["name"])

        # 提取AI配置的IO
        for platform_config in ai_config.get("platform_allocations", {}).values():
            for io_info in platform_config:
                ai_ios.add(io_info["io_name"])

        existing_only_ios = existing_ios - ai_ios
        ai_only_ios = ai_ios - existing_ios

        if existing_only_ios:
            differences.append(f"现有独有IO: {list(existing_only_ios)}")
        if ai_only_ios:
            differences.append(f"AI独有IO: {list(ai_only_ios)}")

        return differences

    def generate_comprehensive_analysis(self) -> Dict[str, Any]:
        """生成完整的对比分析结果"""
        print("🚀 开始完整的3-Agent分析流程...")

        # 运行三个Agent
        agent1_result = self.run_agent1_extract_existing_mappings()
        agent2_result = self.run_agent2_independent_ai_analysis()
        agent3_result = self.run_agent3_comparison_analysis(
            agent1_result, agent2_result
        )

        # 生成综合分析报告
        comprehensive_result = {
            "analysis_metadata": {
                "tool": "Agent3 Comparison Analyzer",
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "analysis_flow": "Agent1(Extract) → Agent2(AI Analysis) → Agent3(Comparison)",
            },
            "agent1_results": {
                "summary": f"提取了{agent1_result['metadata']['total_devices']}个设备的现有配置",
                "total_devices": agent1_result["metadata"]["total_devices"],
                "total_ios": agent1_result["metadata"]["total_ios"],
            },
            "agent2_results": {
                "summary": f"AI分析了{agent2_result['metadata']['total_devices']}个设备",
                "total_devices": agent2_result["metadata"]["total_devices"],
                "total_ios": agent2_result["metadata"]["total_ios"],
            },
            "agent3_results": agent3_result,
            "key_findings": self._extract_key_findings(agent3_result),
            "priority_recommendations": self._generate_priority_recommendations(
                agent3_result
            ),
        }

        return comprehensive_result

    def _extract_key_findings(self, agent3_result: Dict) -> Dict[str, Any]:
        """提取关键发现"""
        stats = agent3_result["overall_statistics"]
        results = agent3_result["comparison_results"]

        # 找到最需要关注的设备
        critical_devices = [r for r in results if r["confidence_score"] < 0.3]
        opportunity_devices = [r for r in results if r["match_type"] == "AI独有"]

        return {
            "total_devices_analyzed": stats["total_devices"],
            "perfect_match_rate": f"{stats['perfect_match_rate']}%",
            "critical_issues": len(critical_devices),
            "ai_opportunities": len(opportunity_devices),
            "most_critical_device": (
                critical_devices[0]["device_name"] if critical_devices else "None"
            ),
            "biggest_opportunity": (
                opportunity_devices[0]["device_name"] if opportunity_devices else "None"
            ),
        }

    def _generate_priority_recommendations(
        self, agent3_result: Dict
    ) -> List[Dict[str, Any]]:
        """生成优先级建议"""
        results = agent3_result["comparison_results"]

        # 按置信度排序，找出最需要关注的设备
        priority_devices = sorted(
            [r for r in results if r["confidence_score"] < 0.8],
            key=lambda x: x["confidence_score"],
        )

        recommendations = []
        for i, device in enumerate(priority_devices[:10]):  # 前10个最需要关注的
            rec = {
                "rank": i + 1,
                "device_name": device["device_name"],
                "issue_type": device["match_type"],
                "confidence": device["confidence_score"],
                "action": self._suggest_action(device),
                "priority": "High" if device["confidence_score"] < 0.3 else "Medium",
            }
            recommendations.append(rec)

        return recommendations

    def _suggest_action(self, device_comparison: Dict) -> str:
        """建议具体行动"""
        match_type = device_comparison["match_type"]
        confidence = device_comparison["confidence_score"]

        if match_type == "AI独有":
            return "考虑将AI建议的设备配置添加到项目中"
        elif match_type == "现有独有":
            return "验证现有配置是否仍然有效，考虑清理"
        elif match_type == "平台不匹配":
            return "重新审查平台分配，考虑采用AI建议"
        elif confidence < 0.3:
            return "需要手动深入分析和重新配置"
        else:
            return "微调配置以提高一致性"

    def save_results(self, results: Dict[str, Any], output_path: str):
        """保存分析结果"""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"✅ 分析结果已保存到: {output_path}")
        except Exception as e:
            print(f"❌ 保存失败: {e}")


def main():
    """主函数"""
    analyzer = Agent3ComparisonAnalyzer()

    # 生成完整分析
    results = analyzer.generate_comprehensive_analysis()

    # 保存结果
    output_path = "/Volumes/LocalRAW/lifesmart-HACS-for-hass/.testing/mapping_tool/tmp/agent3_comparison_analysis_results.json"
    analyzer.save_results(results, output_path)

    # 打印关键统计
    print("\n" + "=" * 60)
    print("🎯 Agent3 对比分析结果摘要")
    print("=" * 60)

    key_findings = results["key_findings"]
    print(f"总分析设备数: {key_findings['total_devices_analyzed']}")
    print(f"完全匹配率: {key_findings['perfect_match_rate']}")
    print(f"关键问题数: {key_findings['critical_issues']}")
    print(f"AI机会数: {key_findings['ai_opportunities']}")
    print(f"最关键设备: {key_findings['most_critical_device']}")
    print(f"最大机会设备: {key_findings['biggest_opportunity']}")

    # 显示前几个优先级建议
    recs = results["priority_recommendations"]
    if recs:
        print("\n🎯 优先级建议 (前5个):")
        for rec in recs[:5]:
            print(
                f"  {rec['rank']}. {rec['device_name']} - {rec['issue_type']} (置信度: {rec['confidence']:.3f})"
            )

    print(f"\n✅ 详细结果已保存到: {output_path}")


if __name__ == "__main__":
    main()
