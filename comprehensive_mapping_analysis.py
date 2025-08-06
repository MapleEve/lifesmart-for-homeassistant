#!/usr/bin/env python3
"""
全面的设备IO口映射分析脚本
基于官方文档表格和const.py设备集合进行完整分析
"""

import re
import sys
from typing import Dict, List, Set

# Add the custom component to path for importing const.py
sys.path.append("custom_components/lifesmart")
from const import *


def get_all_devices_from_const() -> Set[str]:
    """从const.py的所有设备类型集合中获取完整设备列表（排除_V版本设备）"""

    sets_to_check = [
        "BASIC_OUTLET_TYPES",
        "MULTI_FUNCTION_OUTLET_TYPES",
        "METERING_OUTLET_TYPES",
        "SPOT_TYPES",
        "GENERIC_CONTROLLER_TYPES",
        "CAMERA_TYPES",
        "STAR_SERIES_TYPES",
        "SUPPORTED_SWITCH_TYPES",
        "BUTTON_SWITCH_TYPES",
        "LIGHT_DIMMER_TYPES",
        "BRIGHTNESS_LIGHT_TYPES",
        "QUANTUM_TYPES",
        "RGB_LIGHT_TYPES",
        "RGBW_LIGHT_TYPES",
        "OUTDOOR_LIGHT_TYPES",
        "DOOYA_TYPES",
        "COVER_TYPES",
        "COVER_WITH_LIGHT_TYPES",
        "GARAGE_DOOR_TYPES",
        "GUARD_SENSOR_TYPES",
        "MOTION_SENSOR_TYPES",
        "WATER_SENSOR_TYPES",
        "SMOKE_SENSOR_TYPES",
        "RADAR_SENSOR_TYPES",
        "DEFED_SENSOR_TYPES",
        "BASIC_ENV_SENSOR_TYPES",
        "AIR_QUALITY_SENSOR_TYPES",
        "GAS_SENSOR_TYPES",
        "NOISE_SENSOR_TYPES",
        "POWER_METER_TYPES",
        "VOICE_SENSOR_TYPES",
        "AIR_PURIFIER_TYPES",
        "CONTROLLER_485_TYPES",
        "ALARM_TYPES",
        "THIRD_PARTY_CONTROLLER_TYPES",
        "CLIMATE_TYPES",
        "LOCK_TYPES",
    ]

    all_devices = set()
    for set_name in sets_to_check:
        try:
            device_set = globals()[set_name]
            all_devices.update(device_set)
        except KeyError:
            print(f"警告: 未找到设备集合 {set_name}")

    # 排除带_V数字的版本设备
    filtered_devices = {
        device for device in all_devices if not re.search(r"_V\d+$", device)
    }

    print(f"🔍 const.py设备总数（含版本）: {len(all_devices)}")
    print(f"🔍 const.py设备总数（排除版本）: {len(filtered_devices)}")
    version_devices = all_devices - filtered_devices
    if version_devices:
        print(f"🔍 排除的版本设备: {sorted(version_devices)}")

    return filtered_devices


def extract_appendix_device_names() -> Set[str]:
    """从附录3.1智慧设备规格名称表格中提取设备名称"""
    docs_file = "docs/LifeSmart 智慧设备规格属性说明.md"

    try:
        with open(docs_file, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ 文档文件未找到: {docs_file}")
        return set()

    appendix_devices = set()
    lines = content.split("\n")
    in_appendix_table = False

    for line in lines:
        line = line.strip()

        # 找到附录3.1开始
        if "### 3.1 智慧设备规格名称" in line:
            in_appendix_table = True
            continue

        # 找到下一个章节，结束解析
        if in_appendix_table and line.startswith("###") and "3.1" not in line:
            break

        # 解析表格行
        if in_appendix_table and line.startswith("|") and "----" not in line:
            columns = [col.strip() for col in line.split("|")[1:-1]]  # 去掉首尾空列

            if len(columns) >= 2:
                device_col = columns[0].strip()

                # 跳过表格标题和分类行
                if (
                    device_col == "Devtype/c1s"
                    or device_col.startswith("**")
                    or not device_col
                ):
                    continue

                # 处理版本设备名称，如 "SL_MC_ND1/<<SL_MC_ND1_V2>>"
                if "/<<" in device_col and ">>" in device_col:
                    # 提取基础设备名
                    base_device = device_col.split("/")[0].strip()
                    appendix_devices.add(base_device)
                    # 注意：不再添加版本设备名(如SL_MC_ND1_V2)，因为版本通过VERSIONED_DEVICE_TYPES处理
                else:
                    # 普通设备名
                    appendix_devices.add(device_col)

    # 过滤掉带_V数字的版本设备，与const.py的处理保持一致
    filtered_devices = {
        device for device in appendix_devices if not re.search(r"_V\d+$", device)
    }

    print(f"🔍 附录3.1设备总数（含版本）: {len(appendix_devices)}")
    print(f"🔍 附录3.1设备总数（排除版本）: {len(filtered_devices)}")
    version_devices = appendix_devices - filtered_devices
    if version_devices:
        print(f"🔍 附录3.1排除的版本设备: {sorted(version_devices)}")

    return filtered_devices


def extract_device_ios_from_docs() -> Dict[str, List[Dict]]:
    """从官方文档中提取设备IO口定义（权威数据源）"""
    docs_file = "docs/LifeSmart 智慧设备规格属性说明.md"

    # 特殊设备类型映射：文档通用类型 -> 实际设备列表
    special_device_mapping = {
        "cam": [  # 摄像头设备特殊处理
            "LSCAM:LSCAMV1",  # FRAME - 有V和CFST
            "LSCAM:LSICAMEZ1",  # 户外摄像头 - 仅M
            "LSCAM:LSICAMEZ2",  # 户外摄像头 - 仅M
            "LSCAM:LSICAMGOS1",  # 高清摄像头 - 仅M
            "LSCAM:LSLKCAMV1",  # 视频门锁摄像头 - 仅M
        ]
    }

    try:
        with open(docs_file, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ 文档文件未找到: {docs_file}")
        return {}

    device_ios = {}
    lines = content.split("\n")
    current_device = None
    debug_lines = []  # 调试用，记录处理的行

    skip_third_party_table = False
    for line_num, line in enumerate(lines, 1):
        original_line = line
        line = line.strip()

        # 检测到第三方设备控制器接入列表表格，开始跳过
        if "### 3.6 第三方设备通过控制器接入列表" in line:
            skip_third_party_table = True
            debug_lines.append(f"行{line_num}: 开始跳过第三方设备控制器接入列表表格")
            continue

        # 跳过第三方设备表格内容
        if skip_third_party_table:
            # 遇到下一个章节或文件结束时停止跳过
            if line.startswith("##") and "3.6" not in line:
                skip_third_party_table = False
                debug_lines.append(
                    f"行{line_num}: 结束跳过第三方设备控制器接入列表表格"
                )
            else:
                continue

        if not line.startswith("|") or "----" in line:
            continue

        # 分割表格列
        columns = [col.strip() for col in line.split("|")[1:-1]]  # 去掉首尾空列

        if len(columns) >= 5:
            device_col, io_port, io_name, description, permissions = columns[:5]

            # 处理设备名称列
            if device_col:
                # 处理多个设备在同一单元格的情况 (用<br/>或 / 分隔)
                device_names = re.split(r"<br\s*/?>\s*|/", device_col)
                # 清理每个设备名称，只保留有效的设备名
                cleaned_devices = []
                for name in device_names:
                    name = name.strip()
                    # 匹配设备名模式: SL_*, V_*, ELIQ_*, cam等
                    device_match = re.search(r"([A-Z][A-Z0-9_]*|cam)", name)
                    if device_match:
                        device_name = device_match.group(1)
                        # 调试：记录所有提取到的设备名称
                        debug_lines.append(
                            f"行{line_num}: 提取到设备名 '{device_name}' 来自 '{name}' 原行: {original_line[:100]}..."
                        )

                        # 正确的过滤逻辑 - 排除表格标题和格式标记
                        if (
                            not re.search(r"_V\d+$", device_name)  # 排除版本标识符
                            and len(device_name) > 1  # 排除单字符
                            and device_name
                            not in [
                                "D",
                                "T",
                                "IO",
                                "RW",
                                "NAME",
                                "IDX",
                                "TYPE",
                            ]  # 排除表格标记
                            and not device_name.startswith("**")  # 排除markdown格式标记
                            and not re.match(
                                r"^[0-9：；，\.\s\-~]+$", device_name
                            )  # 排除纯数字和标点符号
                            and "evtype" not in device_name.lower()  # 排除Devtype相关
                            and "type" not in device_name.lower()
                        ):  # 排除Type相关
                            cleaned_devices.append(device_name)
                        else:
                            debug_lines.append(
                                f"  -> 过滤掉设备名 '{device_name}' (来自 '{name}')"
                            )

                if cleaned_devices:
                    current_device = cleaned_devices[0]  # 使用第一个设备作为当前设备

                    # 为每个设备创建记录，包括特殊设备映射
                    for device_name in cleaned_devices:
                        target_devices = [device_name]  # 默认使用原设备名

                        # 检查是否为特殊设备类型，需要映射到多个实际设备
                        if device_name in special_device_mapping:
                            target_devices = special_device_mapping[device_name]
                            debug_lines.append(
                                f"  -> 特殊设备映射: '{device_name}' -> {target_devices}"
                            )

                        for target_device in target_devices:
                            if target_device not in device_ios:
                                device_ios[target_device] = []

                        # 清理IO口和名称
                        io_port = io_port.strip()
                        io_name = io_name.strip()
                        permissions = permissions.strip()

                        if io_port and io_name:  # 确保IO口和名称都存在
                            # 处理多个IO口在同一单元格的情况 (如 `L1`, `L2`, `L3`)
                            io_ports = re.split(r"[,\s]+", io_port)
                            for single_io in io_ports:
                                # 清理IO口名称，移除反引号和空格
                                clean_io_port = single_io.strip("`").strip()
                                if clean_io_port:  # 确保IO口不为空
                                    for target_device in target_devices:
                                        # 摄像头设备特殊处理：V和CFST只有FRAME设备有
                                        if (
                                            device_name == "cam"
                                            and clean_io_port in ["V", "CFST"]
                                            and target_device != "LSCAM:LSCAMV1"
                                        ):
                                            debug_lines.append(
                                                f"  -> 跳过IO口 '{clean_io_port}' 对设备 '{target_device}' (仅FRAME设备支持)"
                                            )
                                            continue

                                        device_ios[target_device].append(
                                            {
                                                "io": clean_io_port,
                                                "name": io_name,
                                                "rw": permissions,
                                                "description": description.strip(),
                                            }
                                        )
                else:
                    continue
            elif current_device and io_port:
                # 这是一个IO口行，使用当前设备
                io_port = io_port.strip()
                io_name = io_name.strip()
                permissions = permissions.strip()

                if io_port and io_name:
                    if current_device not in device_ios:
                        device_ios[current_device] = []
                    # 处理多个IO口在同一单元格的情况 (如 `L1`, `L2`, `L3`)
                    io_ports = re.split(r"[,\s]+", io_port)
                    for single_io in io_ports:
                        # 清理IO口名称，移除反引号和空格
                        clean_io_port = single_io.strip("`").strip()
                        if clean_io_port:  # 确保IO口不为空
                            device_ios[current_device].append(
                                {
                                    "io": clean_io_port,
                                    "name": io_name,
                                    "rw": permissions,
                                    "description": description.strip(),
                                }
                            )

    # 输出调试信息
    print(f"\n🔍 文档解析调试信息:")
    # 特别显示D和T设备的来源
    d_t_lines = [line for line in debug_lines if "⚠️ 发现问题设备" in line]
    if d_t_lines:
        print("⚠️ D和T设备抓取来源:")
        for line in d_t_lines:
            print(line)
        print()

    print(f"前30行调试信息:")
    for debug_line in debug_lines[:30]:
        print(debug_line)
    if len(debug_lines) > 30:
        print(f"... 还有 {len(debug_lines) - 30} 行调试信息")

    return device_ios


def extract_current_mappings() -> Dict[str, Dict]:
    """从const.py中提取当前的MULTI_PLATFORM_DEVICE_MAPPING"""

    current_mappings = {}

    for device, mapping in MULTI_PLATFORM_DEVICE_MAPPING.items():
        # 排除带_V数字的设备(fullCls版本标识符)
        if re.search(r"_V\d+$", device):
            continue

        current_mappings[device] = {}

        for platform, platform_info in mapping.items():
            if platform == "dynamic":
                continue

            io_list = platform_info.get("io", [])
            if isinstance(io_list, str):
                io_list = [io_list]
            elif isinstance(io_list, list):
                pass
            else:
                continue

            current_mappings[device][platform] = io_list

    return current_mappings


def analyze_comprehensive_mapping() -> Dict:
    """进行全面的设备映射分析"""
    print("🔍 开始全面设备IO口映射分析...")

    # 获取所有数据源
    all_const_devices = get_all_devices_from_const()  # const.py中的所有设备
    doc_device_ios = extract_device_ios_from_docs()  # 官方文档中的IO定义
    current_mappings = extract_current_mappings()  # 当前的映射关系
    appendix_devices = extract_appendix_device_names()  # 附录3.1中的完整官方设备列表

    print(f"📊 const.py设备集合: {len(all_const_devices)} 个设备")
    print(f"📊 官方文档表格: {len(doc_device_ios)} 个设备有详细IO定义")
    print(f"📊 当前映射: {len(current_mappings)} 个设备")
    print(f"📊 附录3.1官方设备列表: {len(appendix_devices)} 个设备")

    analysis_results = {
        "total_const_devices": len(all_const_devices),
        "total_doc_devices": len(doc_device_ios),
        "total_mapped_devices": len(current_mappings),
        "total_appendix_devices": len(appendix_devices),
        "doc_with_correct_mapping": 0,
        "doc_with_incorrect_mapping": 0,
        "doc_missing_mapping": 0,
        "mapping_errors": {},
        "missing_mappings": {},
        "correct_mappings": {},
        "const_only_devices": [],  # 只在const.py中存在的设备
        "doc_only_devices": [],  # 只在文档中存在的设备
        "mapping_only_devices": [],  # 只在映射中存在的设备
        "appendix_devices": list(appendix_devices),  # 附录3.1中的设备列表
        "const_missing_from_appendix": [],  # const.py有但附录3.1缺失的设备
        "appendix_missing_from_const": [],  # 附录3.1有但const.py缺失的设备
    }

    # 找出各种设备分布
    doc_devices = set(doc_device_ios.keys())
    mapped_devices = set(current_mappings.keys())

    # 排除版本设备的映射设备集合
    mapped_devices_no_version = {
        device for device in mapped_devices if not re.search(r"_V\d+$", device)
    }

    # 分析const.py设备与附录3.1的关系
    analysis_results["const_missing_from_appendix"] = list(
        all_const_devices - appendix_devices
    )
    analysis_results["appendix_missing_from_const"] = list(
        appendix_devices - all_const_devices
    )

    # 修改原有的分析逻辑，将const_only_devices与附录3.1进行对比
    # 而不是简单地标记为"只在映射中存在"
    remaining_const_devices = (
        all_const_devices - doc_devices - mapped_devices_no_version
    )
    analysis_results["const_only_devices"] = list(remaining_const_devices)

    analysis_results["doc_only_devices"] = list(doc_devices - mapped_devices_no_version)
    analysis_results["mapping_only_devices"] = list(
        mapped_devices_no_version - doc_devices - appendix_devices
    )

    # 新增：专门列出缺失的设备类型
    analysis_results["doc_missing_from_const"] = list(
        doc_devices - all_const_devices
    )  # 文档有但const set缺失
    analysis_results["doc_missing_from_mapping"] = list(
        doc_devices - mapped_devices_no_version
    )  # 文档有但映射缺失

    # 新增：set里存在但官方文档不存在的设备
    analysis_results["const_missing_from_docs"] = list(
        all_const_devices - doc_devices
    )  # const.py set里存在但官方文档表格不存在的设备

    # 新增：映射里存在但官方文档不存在的设备
    analysis_results["mapping_missing_from_docs"] = list(
        mapped_devices_no_version - doc_devices
    )  # MULTI_PLATFORM_DEVICE_MAPPING里存在但官方文档表格不存在的设备

    # 分析有文档定义的设备
    for device, ios in doc_device_ios.items():
        if not ios:  # 跳过没有IO口定义的设备
            continue

        # 获取文档中定义的IO口
        doc_ios = {io["io"] for io in ios}

        if device not in current_mappings:
            # 设备在文档中有定义但没有映射
            analysis_results["doc_missing_mapping"] += 1
            analysis_results["missing_mappings"][device] = {
                "doc_ios": list(doc_ios),
                "ios_details": ios,
            }
        else:
            # 设备既在文档中也在映射中，检查映射正确性
            mapped_ios = set()
            for platform, platform_ios in current_mappings[device].items():
                mapped_ios.update(platform_ios)

            missing_ios = doc_ios - mapped_ios  # 文档有但映射缺失的IO口
            incorrect_ios = mapped_ios - doc_ios  # 映射有但文档没有的IO口（错误映射）

            if missing_ios or incorrect_ios:
                analysis_results["doc_with_incorrect_mapping"] += 1
                analysis_results["mapping_errors"][device] = {
                    "doc_ios": list(doc_ios),
                    "mapped_ios": list(mapped_ios),
                    "missing_ios": list(missing_ios),
                    "incorrect_ios": list(incorrect_ios),
                    "ios_details": ios,
                    "current_mapping": current_mappings[device],
                }
            else:
                analysis_results["doc_with_correct_mapping"] += 1
                analysis_results["correct_mappings"][device] = {
                    "doc_ios": list(doc_ios),
                    "mapped_ios": list(mapped_ios),
                }

    return analysis_results


def generate_comprehensive_report(analysis_results: Dict) -> str:
    """生成全面分析报告"""
    report = []
    report.append("=" * 80)
    report.append("📊 全面设备IO口映射分析报告")
    report.append("=" * 80)
    report.append("")

    # 统计概览
    report.append("📈 设备分布统计:")
    report.append(f"   • const.py中设备总数: {analysis_results['total_const_devices']}")
    report.append(f"   • 官方文档定义设备数: {analysis_results['total_doc_devices']}")
    report.append(f"   • 当前已映射设备数: {analysis_results['total_mapped_devices']}")
    report.append(
        f"   • 附录3.1官方设备列表: {analysis_results['total_appendix_devices']}"
    )
    report.append("")

    report.append("📈 映射质量统计:")
    report.append(
        f"   • 文档设备映射正确: {analysis_results['doc_with_correct_mapping']}"
    )
    report.append(
        f"   • 文档设备映射错误: {analysis_results['doc_with_incorrect_mapping']}"
    )
    report.append(f"   • 文档设备缺失映射: {analysis_results['doc_missing_mapping']}")
    report.append("")

    # 映射错误详情（关键问题）
    if analysis_results["mapping_errors"]:
        report.append("🚨 映射错误详情 (需要立即修复):")
        report.append("")
        for device, error_info in analysis_results["mapping_errors"].items():
            report.append(f"🔸 {device}")
            report.append(f"   官方文档IO口: {error_info['doc_ios']}")
            report.append(f"   当前映射IO口: {error_info['mapped_ios']}")

            if error_info["missing_ios"]:
                report.append(f"   ❌ 缺失IO口: {error_info['missing_ios']}")

            if error_info["incorrect_ios"]:
                report.append(f"   ❌ 错误映射IO口: {error_info['incorrect_ios']}")
                report.append("      这些IO口在官方文档中不存在，可能属于其他设备")

            report.append("")

    # 缺失映射的设备
    if analysis_results["missing_mappings"]:
        report.append("⚠️ 缺失映射的设备 (文档中有定义但未映射):")
        report.append("")
        for device, info in analysis_results["missing_mappings"].items():
            report.append(f"🔸 {device}")
            report.append(f"   官方文档IO口: {info['doc_ios']}")
            for io_detail in info["ios_details"]:
                report.append(
                    f"     {io_detail['io']}({io_detail['rw']}): {io_detail['name']}"
                )
            report.append("")

    # 重点分析：缺失的设备
    if analysis_results["doc_missing_from_const"]:
        report.append(
            f"🚨 文档有但const set缺失的设备 ({len(analysis_results['doc_missing_from_const'])}个):"
        )
        report.append("   (这些设备需要添加到相应的设备类型集合中)")
        for device in sorted(analysis_results["doc_missing_from_const"]):
            report.append(f"     • {device}")
        report.append("")

    if analysis_results["doc_missing_from_mapping"]:
        report.append(
            f"🚨 文档有但映射缺失的设备 ({len(analysis_results['doc_missing_from_mapping'])}个):"
        )
        report.append("   (这些设备需要添加到MULTI_PLATFORM_DEVICE_MAPPING中)")
        for device in sorted(analysis_results["doc_missing_from_mapping"]):
            report.append(f"     • {device}")
        report.append("")

    # 新增：set里存在但官方文档不存在的设备
    if analysis_results["const_missing_from_docs"]:
        report.append(
            f"🚨 const.py set里存在但官方文档不存在的设备 ({len(analysis_results['const_missing_from_docs'])}个):"
        )
        report.append("   (这些设备在const.py中定义但官方文档表格中没有对应的IO口说明)")
        for device in sorted(analysis_results["const_missing_from_docs"]):
            report.append(f"     • {device}")
        report.append("")

    # 新增：映射里存在但官方文档不存在的设备
    if analysis_results["mapping_missing_from_docs"]:
        report.append(
            f"🚨 映射里存在但官方文档不存在的设备 ({len(analysis_results['mapping_missing_from_docs'])}个):"
        )
        report.append(
            "   (这些设备在MULTI_PLATFORM_DEVICE_MAPPING中有映射但官方文档表格中没有对应的IO口说明)"
        )
        for device in sorted(analysis_results["mapping_missing_from_docs"]):
            report.append(f"     • {device}")
        report.append("")

    # 附录3.1设备分析
    if analysis_results.get("const_missing_from_appendix"):
        report.append(
            f"📋 const.py有但附录3.1缺失的设备 ({len(analysis_results['const_missing_from_appendix'])}个):"
        )
        report.append("   (这些设备可能是新增设备或需要更新到官方附录)")
        for device in sorted(analysis_results["const_missing_from_appendix"]):
            report.append(f"     • {device}")
        report.append("")

    if analysis_results.get("appendix_missing_from_const"):
        report.append(
            f"📋 附录3.1有但const.py缺失的设备 ({len(analysis_results['appendix_missing_from_const'])}个):"
        )
        report.append("   (这些设备需要添加到相应的const.py设备类型集合中)")
        for device in sorted(analysis_results["appendix_missing_from_const"]):
            report.append(f"     • {device}")
        report.append("")

    # 设备分布情况
    if analysis_results["const_only_devices"]:
        report.append(
            f"📋 只在const.py中存在的设备 ({len(analysis_results['const_only_devices'])}个):"
        )
        report.append("   (这些设备可能没有详细文档或使用默认映射)")
        for device in sorted(analysis_results["const_only_devices"]):
            report.append(f"     • {device}")
        report.append("")

    if analysis_results["mapping_only_devices"]:
        report.append(
            f"📋 只在映射中存在的设备 ({len(analysis_results['mapping_only_devices'])}个):"
        )
        report.append("   (这些设备既不在IO文档也不在附录3.1中，可能需要检查)")
        for device in sorted(analysis_results["mapping_only_devices"]):
            report.append(f"     • {device}")
        report.append("")

    # 映射质量评估
    total_doc_devices = analysis_results["total_doc_devices"]
    if total_doc_devices > 0:
        accuracy = (
            analysis_results["doc_with_correct_mapping"] / total_doc_devices
        ) * 100
        report.append(
            f"🎯 文档设备映射准确率: {analysis_results['doc_with_correct_mapping']}/{total_doc_devices} ({accuracy:.1f}%)"
        )

    coverage = (
        analysis_results["total_mapped_devices"]
        / analysis_results["total_const_devices"]
    ) * 100
    report.append(
        f"🎯 设备映射覆盖率: {analysis_results['total_mapped_devices']}/{analysis_results['total_const_devices']} ({coverage:.1f}%)"
    )

    return "\n".join(report)


if __name__ == "__main__":
    # 执行全面分析
    results = analyze_comprehensive_mapping()

    # 生成报告
    report = generate_comprehensive_report(results)
    print("\n" + report)

    # 保存报告
    with open("comprehensive_mapping_analysis.txt", "w", encoding="utf-8") as f:
        f.write(report)

    print("\n📄 详细报告已保存到: comprehensive_mapping_analysis.txt")
