#!/usr/bin/env python3
"""
全面重构的设备映射与官方文档对比分析脚本
- 解决所有认知复杂度问题
- 模块化设计，易于维护
- 保持完整功能
"""

import re
import sys
from typing import Dict, Set, List, Any

# Add the custom component to path for importing const.py
sys.path.append("../custom_components/lifesmart")
from const import (
    DEVICE_MAPPING,
    VERSIONED_DEVICE_TYPES,
    DYNAMIC_CLASSIFICATION_DEVICES,
)

# 常量定义
LSCAM_PREFIX = "LSCAM:"
VERSION_PATTERN = r"_V\d+$"

# ================== 官方文档顺序定义 ==================

# 定义官方文档中的设备章节顺序 (按照文档 2.1-2.14 的章节编号)
OFFICIAL_DEVICE_ORDER = {
    # 2.1 插座系列 (优先级: 100-199)
    "SL_OL": 100,
    "SL_OL_3C": 101,
    "SL_OL_DE": 102,
    "SL_OL_UK": 103,
    "SL_OL_UL": 104,
    "OD_WE_OT1": 105,
    "SL_OE_3C": 110,
    "SL_OE_DE": 111,
    "SL_OE_W": 112,
    "SL_OE_DC": 113,
    # 2.2 开关系列 (优先级: 200-499)
    "SL_SW_IF3": 200,
    "SL_SF_IF3": 201,
    "SL_SW_CP3": 202,
    "SL_SW_RC3": 203,
    "SL_SW_IF2": 204,
    "SL_SF_IF2": 205,
    "SL_SW_CP2": 206,
    "SL_SW_FE2": 207,
    "SL_SW_RC2": 208,
    "SL_SW_IF1": 209,
    "SL_SF_IF1": 210,
    "SL_SW_CP1": 211,
    "SL_SW_FE1": 212,
    "SL_SW_RC1": 213,
    "SL_SW_ND1": 220,
    "SL_MC_ND1": 221,
    "SL_SW_ND2": 222,
    "SL_MC_ND2": 223,
    "SL_SW_ND3": 224,
    "SL_MC_ND3": 225,
    "SL_S": 230,
    "SL_SPWM": 231,
    "SL_P_SW": 232,
    "SL_SC_BB": 240,
    "SL_SW_DM1": 250,
    "SL_SW_MJ1": 260,
    "SL_SW_MJ2": 261,
    "SL_SW_MJ3": 262,
    "SL_SC_BB2": 270,
    "SL_SW_WW": 280,
    "SL_SW_BS1": 281,
    "SL_SW_BS2": 282,
    "SL_SW_BS3": 283,
    "SL_SW_NS1": 284,
    "SL_SW_NS2": 285,
    "SL_SW_NS3": 286,
    "SL_SW_NS6": 287,
    # 2.3 窗帘控制 (优先级: 500-599)
    "SL_SW_WIN": 500,
    "SL_CN_IF": 501,
    "SL_CN_FE": 502,
    "SL_DOOYA": 503,
    "SL_P_V2": 504,
    # 2.4 灯光系列 (优先级: 600-699)
    "SL_LI_RGBW": 600,
    "SL_CT_RGBW": 601,
    "SL_SC_RGB": 602,
    "SL_LI_WW": 603,
    "SL_LI_GD1": 604,
    "SL_LI_UG1": 605,
    "SL_SPOT": 606,
    "MSL_IRCTL": 607,
    "OD_WE_IRCTL": 608,
    "SL_LI_IR": 609,
    "SL_P_IR": 610,
    "OD_WE_QUAN": 611,
    # 2.5 第三方设备 (优先级: 700-799)
    "V_DLT645_P": 700,
    "V_485_P": 701,
    "V_DUNJIA_P": 702,
    "V_HG_L": 703,
    "V_HG_XX": 704,
    "V_IND_S": 705,
    "V_SZJSXR_P": 706,
    "V_T8600_P": 707,
    # 2.6 传感器系列 (优先级: 800-999)
    "SL_SC_THL": 800,
    "SL_SC_BE": 801,
    "SL_SC_CQ": 802,
    "SL_SC_CA": 803,
    "SL_SC_CH": 804,
    "SL_SC_CP": 805,
    "SL_SC_CN": 806,
    "SL_SC_WA": 807,
    "SL_SC_G": 808,
    "SL_SC_BG": 809,
    "SL_SC_MHW": 810,
    "SL_SC_CM": 811,
    "SL_SC_BM": 812,
    "SL_SC_GS": 813,
    "SL_SC_CV": 814,
    "SL_P_A": 815,
    "SL_P_RM": 816,
    "SL_DF_GG": 817,
    "SL_DF_MM": 818,
    "SL_DF_SR": 819,
    "SL_DF_BB": 820,
    "SL_DF_KP": 821,
    "ELIQ_EM": 822,
    "SL_BP_MZ": 823,
    # 2.7 空气净化器 (优先级: 1000-1099)
    "OD_MFRESH_M8088": 1000,
    # 2.8 智能门锁 (优先级: 1100-1199)
    "SL_LK_LS": 1100,
    "SL_LK_GTM": 1101,
    "SL_LK_AG": 1102,
    "SL_LK_SG": 1103,
    "SL_LK_YL": 1104,
    "SL_LK_SWIFTE": 1105,
    "SL_LK_TY": 1106,
    "SL_LK_DJ": 1107,
    "OD_JIUWANLI_LOCK1": 1108,
    "SL_P_BDLK": 1109,
    # 2.9 温控设备 (优先级: 1200-1299)
    "V_AIR_P": 1200,
    "SL_TR_ACIPM": 1201,
    "SL_CP_DN": 1202,
    "SL_CP_AIR": 1203,
    "SL_CP_VL": 1204,
    "SL_DN": 1205,
    "SL_FCU": 1206,
    "SL_UACCB": 1207,
    "V_FRESH_P": 1208,
    # 2.10 报警器 (优先级: 1300-1399)
    "SL_ALM": 1300,
    "LSSSMINIV1": 1301,
    # 2.11 其他设备 (优先级: 1400-1499)
    "SL_ETDOOR": 1400,
    # 2.12 通用控制器 (优先级: 1500-1599)
    "SL_P": 1500,
    "SL_JEMA": 1501,
    # 2.13 摄像头 (优先级: 1600-1699)
    "cam": 1600,
    "LSCAM": 1601,
    # 2.14 超能面板 (优先级: 1700-1799)
    "SL_NATURE": 1700,
}


def sort_devices_by_official_order(devices: List[str]) -> List[str]:
    """根据官方文档章节顺序排序设备列表"""

    def get_device_priority(device: str) -> int:
        # 处理版本设备（如SL_SW_DM1_V1 -> SL_SW_DM1）
        base_device = re.sub(VERSION_PATTERN, "", device)
        # 处理摄像头前缀设备（如LSCAM:xxx -> LSCAM）
        if device.startswith(LSCAM_PREFIX):
            base_device = "LSCAM"

        return OFFICIAL_DEVICE_ORDER.get(base_device, 9999)

    # 按照官方文档顺序排序
    return sorted(devices, key=lambda d: (get_device_priority(d), d))


def infer_sensor_attributes(
    io_name: str, description: str, doc_rw: str, doc_details: str
) -> Dict[str, Any]:
    """根据官方文档信息推断传感器属性，使用HA_STANDARD_MAPPINGS标准"""
    attrs = {
        "rw": doc_rw,
        "description": description,
        "data_type": "raw_value",
        "conversion": "raw_value",
        "commands": {},
    }

    # 规范化描述和详情文本
    desc_lower = description.lower()
    details_lower = doc_details.lower() if doc_details else ""
    combined_text = f"{desc_lower} {details_lower}"

    # 使用HA_STANDARD_MAPPINGS进行智能匹配
    best_match = None
    best_score = 0

    for func_type, standards in HA_STANDARD_MAPPINGS.items():
        if standards["platform"] != "sensor":
            continue

        # 计算关键词匹配分数
        keywords = standards.get("keywords", [])
        matches = sum(1 for keyword in keywords if keyword.lower() in combined_text)

        if matches > best_score:
            best_score = matches
            best_match = (func_type, standards)

    # 应用最佳匹配的标准
    if best_match:
        func_type, standards = best_match

        # 设置device_class
        if "device_class" in standards:
            attrs["device_class"] = standards["device_class"]

        # 设置单位
        units = standards.get("units", [])
        if units:
            attrs["unit_of_measurement"] = units[0]

        # 设置state_class（sensor平台默认为MEASUREMENT）
        if func_type in ["energy", "energy_total"]:
            attrs["state_class"] = "SensorStateClass.TOTAL_INCREASING"
        else:
            attrs["state_class"] = "SensorStateClass.MEASUREMENT"

        # 根据转换提示设置转换方式
        conversion_hints = standards.get("conversion_hints", [])
        for hint in conversion_hints:
            if hint.lower() in details_lower:
                if "ieee754" in hint.lower():
                    attrs.update(
                        {
                            "conversion": "ieee754_converter",
                            "data_type": f"{func_type}_ieee754",
                        }
                    )
                elif "/10" in hint or "值*10" in hint:
                    attrs.update(
                        {
                            "conversion": f"{func_type}_converter",
                            "data_type": f"{func_type}_raw",
                        }
                    )
                elif "v字段" in hint:
                    attrs.update(
                        {"conversion": "v_field", "data_type": f"{func_type}_friendly"}
                    )
                break

        # 特殊范围设置
        if func_type == "battery":
            attrs["range"] = [0, 100]

    # 如果没有匹配到sensor类型，可能是其他平台类型
    if not best_match:
        # 检查是否为binary_sensor类型
        for func_type, standards in HA_STANDARD_MAPPINGS.items():
            if standards["platform"] != "binary_sensor":
                continue

            keywords = standards.get("keywords", [])
            if any(keyword.lower() in combined_text for keyword in keywords):
                attrs.update(
                    {
                        "platform": "binary_sensor",
                        "device_class": standards["device_class"],
                        "data_type": "binary_state",
                    }
                )
                break
    return attrs


def infer_binary_sensor_attributes(
    io_name: str, description: str, doc_rw: str, doc_details: str
) -> Dict[str, Any]:
    """推断二进制传感器属性"""
    attrs = {
        "rw": doc_rw,
        "description": description,
        "data_type": "binary_state",
        "conversion": "binary_converter",
        "commands": {},
    }

    desc_lower = description.lower()
    details_lower = doc_details.lower() if doc_details else ""
    combined_text = f"{desc_lower} {details_lower}"

    # 推断 BinarySensorDeviceClass
    if any(
        keyword in combined_text
        for keyword in ["门", "door", "开关状态", "open", "close"]
    ):
        attrs["device_class"] = "BinarySensorDeviceClass.DOOR"

    elif any(keyword in combined_text for keyword in ["窗", "window"]):
        attrs["device_class"] = "BinarySensorDeviceClass.WINDOW"

    elif any(
        keyword in combined_text for keyword in ["移动", "motion", "人体", "检测"]
    ):
        attrs["device_class"] = "BinarySensorDeviceClass.MOTION"

    elif any(keyword in combined_text for keyword in ["烟雾", "smoke", "烟感"]):
        attrs["device_class"] = "BinarySensorDeviceClass.SMOKE"

    elif any(keyword in combined_text for keyword in ["燃气", "gas", "气体"]):
        attrs["device_class"] = "BinarySensorDeviceClass.GAS"

    elif any(keyword in combined_text for keyword in ["告警", "alarm", "报警", "警报"]):
        attrs["device_class"] = "BinarySensorDeviceClass.SAFETY"

    elif any(keyword in combined_text for keyword in ["低电", "电量", "battery"]):
        attrs["device_class"] = "BinarySensorDeviceClass.BATTERY"

    elif any(keyword in combined_text for keyword in ["连接", "connectivity", "网络"]):
        attrs["device_class"] = "BinarySensorDeviceClass.CONNECTIVITY"

    elif any(keyword in combined_text for keyword in ["防拆", "tamper", "撬开"]):
        attrs["device_class"] = "BinarySensorDeviceClass.TAMPER"

    elif any(keyword in combined_text for keyword in ["问题", "problem", "故障"]):
        attrs["device_class"] = "BinarySensorDeviceClass.PROBLEM"

    else:
        # 默认为通用类型
        attrs["device_class"] = "BinarySensorDeviceClass.GENERIC"

    return attrs


# ================ 设备属性分析类 ================


class DeviceAttributeAnalyzer:
    """设备属性分析器"""

    def __init__(self):
        self.official_data = {}
        self.device_mapping = DEVICE_MAPPING
        self.official_device_names = set()  # 官方设备名称集合

    def load_official_data(self):
        """加载官方文档数据"""
        self.official_data = extract_device_ios_from_docs()
        self.official_device_names = extract_official_device_names()

    def validate_device_names(self) -> Dict[str, Any]:
        """验证设备名称字段"""
        if not self.official_device_names:
            self.official_device_names = extract_official_device_names()

        validation_results = {
            "total_devices": len(self.device_mapping),
            "devices_with_name": 0,
            "devices_without_name": 0,
            "devices_with_invalid_name": 0,
            "missing_name_devices": [],
            "invalid_name_devices": [],
            "valid_name_devices": [],
        }

        print(f"📊 开始验证 {len(self.device_mapping)} 个设备的name字段...")
        print(f"📊 官方设备名称集合大小: {len(self.official_device_names)} 个")

        for device_id, device_config in self.device_mapping.items():
            device_name = device_config.get("name", "")

            if not device_name:
                # 设备缺失name字段
                validation_results["devices_without_name"] += 1
                validation_results["missing_name_devices"].append(
                    {
                        "device_id": device_id,
                        "issue": "缺失name字段",
                        "suggestion": "需要添加中文名称",
                    }
                )
            else:
                validation_results["devices_with_name"] += 1

                # 检查name是否在官方名称集合中
                if device_name in self.official_device_names:
                    validation_results["valid_name_devices"].append(
                        {"device_id": device_id, "name": device_name, "status": "valid"}
                    )
                else:
                    validation_results["devices_with_invalid_name"] += 1
                    validation_results["invalid_name_devices"].append(
                        {
                            "device_id": device_id,
                            "name": device_name,
                            "issue": "name不在官方设备名称集合中",
                            "suggestion": f"检查是否应为官方名称集合中的某个名称",
                        }
                    )

        return validation_results

    def generate_name_validation_report(
        self, validation_results: Dict[str, Any]
    ) -> str:
        """生成设备名称验证报告"""
        total = validation_results["total_devices"]
        with_name = validation_results["devices_with_name"]
        without_name = validation_results["devices_without_name"]
        invalid_name = validation_results["devices_with_invalid_name"]
        valid_name = len(validation_results["valid_name_devices"])

        report = [
            "# LifeSmart 设备名称验证报告",
            "",
            "## 摘要",
            f"- 分析设备总数: {total}",
            f"- 有name字段设备: {with_name} ({with_name/total*100:.1f}%)",
            f"- 无name字段设备: {without_name} ({without_name/total*100:.1f}%)",
            f"- name字段有效设备: {valid_name} ({valid_name/total*100:.1f}%)",
            f"- name字段无效设备: {invalid_name} ({invalid_name/total*100:.1f}%)",
            "",
            "## 问题详情",
            "",
        ]

        # 缺失name字段的设备
        if validation_results["missing_name_devices"]:
            report.extend(
                [
                    f"### ❌ 缺失name字段设备 ({len(validation_results['missing_name_devices'])}个)",
                    "",
                ]
            )

            for item in validation_results["missing_name_devices"]:
                report.append(f"- **{item['device_id']}**: {item['issue']}")
            report.append("")

        # name字段无效的设备
        if validation_results["invalid_name_devices"]:
            report.extend(
                [
                    f"### ⚠️ name字段无效设备 ({len(validation_results['invalid_name_devices'])}个)",
                    "",
                ]
            )

            for item in validation_results["invalid_name_devices"]:
                report.append(
                    f"- **{item['device_id']}** (name: \"{item['name']}\"): {item['issue']}"
                )
            report.append("")

        # 有效设备汇总
        if validation_results["valid_name_devices"]:
            report.extend(
                [
                    f"### ✅ name字段有效设备 ({len(validation_results['valid_name_devices'])}个)",
                    "",
                ]
            )

            # 只显示前20个，避免报告过长
            sample_valid = validation_results["valid_name_devices"][:20]
            for item in sample_valid:
                report.append(f"- **{item['device_id']}**: {item['name']}")

            if len(validation_results["valid_name_devices"]) > 20:
                remaining = len(validation_results["valid_name_devices"]) - 20
                report.append(f"- ... 还有 {remaining} 个有效设备")
            report.append("")

        return "\n".join(report)

    def analyze_missing_attributes(self) -> Dict[str, Any]:
        """分析缺失的设备属性"""
        if not self.official_data:
            self.load_official_data()

        missing_configs = {}
        suggestions = []

        print(f"📊 开始分析 {len(self.device_mapping)} 个设备的属性缺失情况...")

        for device_name, device_config in self.device_mapping.items():
            # 获取该设备的官方文档信息
            official_device_ios = self.official_data.get(device_name, [])

            current_mapping = device_config

            # 检查每个平台的IO配置
            device_suggestions = {"device": device_name, "platforms": {}}

            has_missing = False

            for platform in [
                "sensor",
                "binary_sensor",
                "switch",
                "light",
                "climate",
                "lock",
                "cover",
            ]:
                if platform not in current_mapping:
                    continue

                platform_config = current_mapping[platform]
                platform_suggestions = {}

                # 检查平台配置中是否有io字段
                if "io" not in platform_config:
                    continue

                io_list = platform_config["io"]

                # 检查每个IO的配置
                for io_name in io_list:
                    # 查找该IO在platform_config中的配置
                    io_config = platform_config.get(io_name, {})

                    # 查找官方文档中对应的IO信息
                    doc_io_info = None
                    for io_detail in official_device_ios:
                        if io_detail.get("io") == io_name:
                            doc_io_info = io_detail
                            break

                    # 如果找不到官方文档信息，使用基础信息
                    if not doc_io_info:
                        doc_description = io_name
                        doc_rw = "R"  # 默认只读
                        doc_details = ""
                    else:
                        doc_description = doc_io_info.get("name", io_name)
                        doc_rw = doc_io_info.get("rw", "R")
                        doc_details = doc_io_info.get("description", "")

                    # 检查缺失的属性
                    missing_attrs = []
                    suggestions_for_io = {}

                    # 基础属性检查
                    if "rw" not in io_config:
                        missing_attrs.append("rw")
                        suggestions_for_io["rw"] = f'"{doc_rw}"'

                    if "description" not in io_config:
                        missing_attrs.append("description")
                        suggestions_for_io["description"] = f'"{doc_description}"'

                    # 根据平台类型检查特定属性
                    if platform == "sensor":
                        attrs = infer_sensor_attributes(
                            io_name, doc_description, doc_rw, doc_details
                        )

                        for attr_name, attr_value in attrs.items():
                            if attr_name not in io_config:
                                missing_attrs.append(attr_name)
                                if isinstance(
                                    attr_value, str
                                ) and not attr_value.startswith('"'):
                                    suggestions_for_io[attr_name] = attr_value
                                else:
                                    suggestions_for_io[attr_name] = (
                                        f'"{attr_value}"'
                                        if isinstance(attr_value, str)
                                        else attr_value
                                    )

                    elif platform == "binary_sensor":
                        attrs = infer_binary_sensor_attributes(
                            io_name, doc_description, doc_rw, doc_details
                        )

                        for attr_name, attr_value in attrs.items():
                            if attr_name not in io_config:
                                missing_attrs.append(attr_name)
                                if isinstance(
                                    attr_value, str
                                ) and not attr_value.startswith('"'):
                                    suggestions_for_io[attr_name] = attr_value
                                else:
                                    suggestions_for_io[attr_name] = (
                                        f'"{attr_value}"'
                                        if isinstance(attr_value, str)
                                        else attr_value
                                    )

                    # 如果有缺失属性，添加到建议中
                    if missing_attrs:
                        has_missing = True
                        platform_suggestions[io_name] = {
                            "missing_attributes": missing_attrs,
                            "suggestions": suggestions_for_io,
                            "doc_info": {
                                "description": doc_description,
                                "rw": doc_rw,
                                "details": doc_details,
                            },
                        }

                if platform_suggestions:
                    device_suggestions["platforms"][platform] = platform_suggestions

            if has_missing:
                suggestions.append(device_suggestions)

        return {
            "missing_devices": suggestions,
            "total_devices": len(self.device_mapping),
            "devices_with_missing": len(suggestions),
        }

    def generate_attribute_report(self, analysis_results: Dict[str, Any]) -> str:
        """生成设备属性缺失报告"""
        missing_devices = analysis_results["missing_devices"]
        total_devices = analysis_results["total_devices"]
        devices_with_missing = analysis_results["devices_with_missing"]

        report = [
            "# LifeSmart 设备属性缺失分析报告",
            "",
            "## 摘要",
            f"- 分析设备总数: {total_devices}",
            f"- 发现属性缺失设备: {devices_with_missing}",
            "",
            "## 主要缺失属性类型",
            "- device_class: 设备分类",
            "- state_class: 状态分类 ",
            "- unit_of_measurement: 测量单位",
            "- rw: 读写权限",
            "- range: 取值范围",
            "- conversion: 数据转换方式",
            "",
            "---",
            "",
        ]

        for device_suggestion in missing_devices:
            device_name = device_suggestion["device"]
            report.append(f"## 🔸 **{device_name}**")
            report.append("")

            for platform, platform_data in device_suggestion["platforms"].items():
                report.append(f"### {platform.upper()}")
                report.append("")

                for io_name, io_data in platform_data.items():
                    missing_attrs = io_data["missing_attributes"]
                    suggestions_dict = io_data["suggestions"]
                    doc_info = io_data["doc_info"]

                    report.append(f"#### IO口: `{io_name}`")
                    report.append(f"- **官方描述**: {doc_info['description']}")
                    report.append(f"- **读写权限**: {doc_info['rw']}")
                    report.append(f"- **缺失属性**: {', '.join(missing_attrs)}")
                    report.append("")
                    report.append("**建议添加的配置**:")
                    report.append("```python")

                    for attr_name, attr_value in suggestions_dict.items():
                        report.append(f'"{attr_name}": {attr_value},')

                    report.append("```")
                    report.append("")

            report.append("")

        return "\n".join(report)

    def generate_patches_json(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成JSON格式的补丁建议"""
        missing_devices = analysis_results["missing_devices"]
        patches = {}

        for device_suggestion in missing_devices:
            device_name = device_suggestion["device"]
            patches[device_name] = {}

            for platform, platform_data in device_suggestion["platforms"].items():
                patches[device_name][platform] = {}

                for io_name, io_data in platform_data.items():
                    patches[device_name][platform][io_name] = io_data["suggestions"]

        return patches


# Home Assistant标准常量映射（用于映射质量验证）
# 使用HA官方device_class常量 - 涵盖所有16个支持的平台
HA_STANDARD_MAPPINGS = {
    # =============== SENSOR 平台标准 ===============
    # 温度相关
    "temperature": {
        "device_class": "SensorDeviceClass.TEMPERATURE",
        "units": ["UnitOfTemperature.CELSIUS"],
        "keywords": ["温度", "temp", "temperature", "℃", "度"],
        "conversion_hints": ["v字段", "/10", "ieee754", "温度值*10"],
        "platform": "sensor",
    },
    # 湿度相关
    "humidity": {
        "device_class": "SensorDeviceClass.HUMIDITY",
        "units": ["PERCENTAGE"],
        "keywords": ["湿度", "humidity", "RH", "%"],
        "conversion_hints": ["百分比", "相对湿度"],
        "platform": "sensor",
    },
    # 电量/电池相关
    "battery": {
        "device_class": "SensorDeviceClass.BATTERY",
        "units": ["PERCENTAGE"],
        "keywords": ["电量", "电池", "battery", "power", "剩余", "%"],
        "conversion_hints": ["百分比", "电压换算"],
        "platform": "sensor",
    },
    # 功率相关
    "power": {
        "device_class": "SensorDeviceClass.POWER",
        "units": ["UnitOfPower.WATT"],
        "keywords": ["功率", "power", "watt", "w"],
        "conversion_hints": ["浮点数", "ieee754"],
        "platform": "sensor",
    },
    # 能源/用电量相关
    "energy": {
        "device_class": "SensorDeviceClass.ENERGY",
        "units": ["UnitOfEnergy.KILO_WATT_HOUR"],
        "keywords": ["用电量", "电量", "energy", "kwh", "累计"],
        "conversion_hints": ["ieee754", "浮点数", "累计"],
        "platform": "sensor",
    },
    # 电压相关
    "voltage": {
        "device_class": "SensorDeviceClass.VOLTAGE",
        "units": ["UnitOfElectricPotential.VOLT"],
        "keywords": ["电压", "voltage", "v"],
        "conversion_hints": ["原始电压值"],
        "platform": "sensor",
    },
    # 亮度/照度相关
    "illuminance": {
        "device_class": "SensorDeviceClass.ILLUMINANCE",
        "units": ["UnitOfIlluminance.LUX"],
        "keywords": ["亮度", "照度", "光照", "light", "lux", "illuminance"],
        "conversion_hints": ["环境光照"],
        "platform": "sensor",
    },
    # 噪音相关
    "sound_pressure": {
        "device_class": "SensorDeviceClass.SOUND_PRESSURE",
        "units": ["UnitOfSoundPressure.DECIBEL"],
        "keywords": ["噪音", "noise", "分贝", "db"],
        "conversion_hints": ["声压级"],
        "platform": "sensor",
    },
    # CO2相关
    "co2": {
        "device_class": "SensorDeviceClass.CO2",
        "units": ["CONCENTRATION_PARTS_PER_MILLION"],
        "keywords": ["co2", "二氧化碳", "ppm"],
        "conversion_hints": ["浓度"],
        "platform": "sensor",
    },
    # TVOC/甲醛相关
    "volatile_organic_compounds": {
        "device_class": "SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS",
        "units": ["CONCENTRATION_MICROGRAMS_PER_CUBIC_METER"],
        "keywords": ["甲醛", "tvoc", "formaldehyde", "ug/m"],
        "conversion_hints": ["浓度"],
        "platform": "sensor",
    },
    # 燃气相关
    "gas": {
        "device_class": "SensorDeviceClass.GAS",
        "units": [],
        "keywords": ["燃气", "gas", "浓度"],
        "conversion_hints": ["气体浓度"],
        "platform": "sensor",
    },
    # =============== SWITCH 平台标准 ===============
    "switch": {
        "device_class": None,  # switch平台不使用device_class
        "units": [],
        "keywords": ["开关", "switch", "控制", "on", "off", "type&1"],
        "conversion_hints": ["type&1==1", "type&1==0", "忽略val值"],
        "platform": "switch",
    },
    # =============== BINARY_SENSOR 平台标准 ===============
    # 二进制传感器 - 运动检测
    "motion": {
        "device_class": "BinarySensorDeviceClass.MOTION",
        "units": [],
        "keywords": ["动态", "移动", "人体", "motion", "pir", "感应"],
        "conversion_hints": [],
        "platform": "binary_sensor",
    },
    # 二进制传感器 - 门窗状态
    "door": {
        "device_class": "BinarySensorDeviceClass.DOOR",
        "units": [],
        "keywords": ["门", "门窗", "door"],
        "conversion_hints": [],
        "platform": "binary_sensor",
    },
    # 二进制传感器 - 窗户状态
    "window": {
        "device_class": "BinarySensorDeviceClass.WINDOW",
        "units": [],
        "keywords": ["窗", "窗户", "window"],
        "conversion_hints": [],
        "platform": "binary_sensor",
    },
    # 二进制传感器 - 烟雾检测
    "smoke": {
        "device_class": "BinarySensorDeviceClass.SMOKE",
        "units": [],
        "keywords": ["烟雾", "smoke", "烟感"],
        "conversion_hints": [],
        "platform": "binary_sensor",
    },
    # 二进制传感器 - 燃气检测
    "gas_binary": {
        "device_class": "BinarySensorDeviceClass.GAS",
        "units": [],
        "keywords": ["燃气", "gas", "气体"],
        "conversion_hints": [],
        "platform": "binary_sensor",
    },
    # 二进制传感器 - 安全状态
    "safety": {
        "device_class": "BinarySensorDeviceClass.SAFETY",
        "units": [],
        "keywords": ["告警", "alarm", "报警", "警报"],
        "conversion_hints": [],
        "platform": "binary_sensor",
    },
    # 二进制传感器 - 电池状态
    "battery_binary": {
        "device_class": "BinarySensorDeviceClass.BATTERY",
        "units": [],
        "keywords": ["低电", "电量", "battery"],
        "conversion_hints": [],
        "platform": "binary_sensor",
    },
    # 二进制传感器 - 连接状态
    "connectivity": {
        "device_class": "BinarySensorDeviceClass.CONNECTIVITY",
        "units": [],
        "keywords": ["连接", "connectivity", "网络"],
        "conversion_hints": [],
        "platform": "binary_sensor",
    },
    # 二进制传感器 - 防拆状态
    "tamper": {
        "device_class": "BinarySensorDeviceClass.TAMPER",
        "units": [],
        "keywords": ["防拆", "tamper", "撬开"],
        "conversion_hints": [],
        "platform": "binary_sensor",
    },
    # 二进制传感器 - 问题状态
    "problem": {
        "device_class": "BinarySensorDeviceClass.PROBLEM",
        "units": [],
        "keywords": ["问题", "problem", "故障"],
        "conversion_hints": [],
        "platform": "binary_sensor",
    },
    # =============== COVER 平台标准 ===============
    "cover_curtain": {
        "device_class": "CoverDeviceClass.CURTAIN",
        "units": [],
        "keywords": ["窗帘", "curtain", "遮光", "打开", "关闭", "位置"],
        "conversion_hints": ["位置百分比", "0-100", "停止命令"],
        "platform": "cover",
    },
    "cover_blind": {
        "device_class": "CoverDeviceClass.BLIND",
        "units": [],
        "keywords": ["百叶窗", "blind", "遮阳", "角度"],
        "conversion_hints": ["角度控制", "倾斜角度"],
        "platform": "cover",
    },
    "cover_shutter": {
        "device_class": "CoverDeviceClass.SHUTTER",
        "units": [],
        "keywords": ["卷帘", "shutter", "遮光"],
        "conversion_hints": ["位置控制"],
        "platform": "cover",
    },
    "cover_garage": {
        "device_class": "CoverDeviceClass.GARAGE",
        "units": [],
        "keywords": ["车库门", "garage", "门"],
        "conversion_hints": ["开关控制"],
        "platform": "cover",
    },
    # =============== LIGHT 平台标准 ===============
    "light_brightness": {
        "device_class": None,  # light平台不使用device_class
        "units": [],
        "keywords": ["亮度", "brightness", "调光", "dimmer"],
        "conversion_hints": ["0-255", "百分比转换"],
        "platform": "light",
    },
    "light_color_temp": {
        "device_class": None,
        "units": ["mired"],
        "keywords": ["色温", "color_temp", "暖光", "冷光", "开尔文", "k"],
        "conversion_hints": ["mired转换", "2700K-6500K"],
        "platform": "light",
    },
    "light_rgb": {
        "device_class": None,
        "units": [],
        "keywords": ["rgb", "颜色", "color", "彩色"],
        "conversion_hints": ["RGB值", "0-255每通道"],
        "platform": "light",
    },
    "light_rgbw": {
        "device_class": None,
        "units": [],
        "keywords": ["rgbw", "彩色", "白光", "color", "white"],
        "conversion_hints": ["RGBW值", "包含白光通道"],
        "platform": "light",
    },
    "light_effect": {
        "device_class": None,
        "units": [],
        "keywords": ["效果", "effect", "动态", "场景"],
        "conversion_hints": ["效果列表", "场景模式"],
        "platform": "light",
    },
    # =============== CLIMATE 平台标准 ===============
    "climate_temperature": {
        "device_class": None,  # climate平台不使用device_class
        "units": ["UnitOfTemperature.CELSIUS"],
        "keywords": ["温度", "temperature", "温控", "thermostat"],
        "conversion_hints": ["当前温度", "目标温度"],
        "platform": "climate",
    },
    "climate_humidity": {
        "device_class": None,
        "units": ["PERCENTAGE"],
        "keywords": ["湿度", "humidity", "相对湿度"],
        "conversion_hints": ["当前湿度", "目标湿度"],
        "platform": "climate",
    },
    "climate_fan_mode": {
        "device_class": None,
        "units": [],
        "keywords": ["风速", "fan", "档位", "自动", "高", "中", "低"],
        "conversion_hints": ["风速档位", "自动模式"],
        "platform": "climate",
    },
    "climate_hvac_mode": {
        "device_class": None,
        "units": [],
        "keywords": ["模式", "制热", "制冷", "auto", "heat", "cool", "off"],
        "conversion_hints": ["工作模式", "制热制冷"],
        "platform": "climate",
    },
    # =============== LOCK 平台标准 ===============
    "lock_state": {
        "device_class": None,  # lock平台不使用device_class
        "units": [],
        "keywords": ["锁", "lock", "unlock", "开锁", "锁定", "门锁"],
        "conversion_hints": ["锁定状态", "开锁命令"],
        "platform": "lock",
    },
    "lock_battery": {
        "device_class": "SensorDeviceClass.BATTERY",
        "units": ["PERCENTAGE"],
        "keywords": ["门锁电量", "锁电量", "battery"],
        "conversion_hints": ["电量百分比"],
        "platform": "lock",
    },
    # =============== BUTTON 平台标准 ===============
    "button_press": {
        "device_class": "ButtonDeviceClass.RESTART",
        "units": [],
        "keywords": ["按钮", "button", "press", "触发", "执行"],
        "conversion_hints": ["按压触发", "一次性动作"],
        "platform": "button",
    },
    # =============== FAN 平台标准 ===============
    "fan_speed": {
        "device_class": None,  # fan平台不使用device_class
        "units": [],
        "keywords": ["风扇", "fan", "转速", "档位", "speed"],
        "conversion_hints": ["转速控制", "档位设置"],
        "platform": "fan",
    },
    # =============== EVENT 平台标准 ===============
    "event_trigger": {
        "device_class": None,  # event平台不使用device_class
        "units": [],
        "keywords": ["事件", "event", "trigger", "触发"],
        "conversion_hints": ["事件触发", "状态变化"],
        "platform": "event",
    },
    # =============== NUMBER 平台标准 ===============
    "number_value": {
        "device_class": None,  # number平台不使用device_class
        "units": [],
        "keywords": ["数值", "number", "value", "设置", "参数"],
        "conversion_hints": ["数值输入", "范围设置"],
        "platform": "number",
    },
    # =============== SIREN 平台标准 ===============
    "siren_alarm": {
        "device_class": None,  # siren平台不使用device_class
        "units": [],
        "keywords": ["警报", "siren", "alarm", "蜂鸣", "报警"],
        "conversion_hints": ["警报控制", "音量设置"],
        "platform": "siren",
    },
    # =============== VALVE 平台标准 ===============
    "valve_water": {
        "device_class": "ValveDeviceClass.WATER",
        "units": [],
        "keywords": ["阀门", "valve", "水阀", "开关"],
        "conversion_hints": ["阀门开关", "位置控制"],
        "platform": "valve",
    },
    # =============== AIR_QUALITY 平台标准 ===============
    "air_quality_index": {
        "device_class": "SensorDeviceClass.AQI",
        "units": [],
        "keywords": ["空气质量", "air_quality", "aqi", "pm2.5", "pm10"],
        "conversion_hints": ["空气质量指数"],
        "platform": "air_quality",
    },
    # =============== REMOTE 平台标准 ===============
    "remote_control": {
        "device_class": None,  # remote平台不使用device_class
        "units": [],
        "keywords": ["遥控", "remote", "红外", "ir", "控制"],
        "conversion_hints": ["红外发送", "遥控命令"],
        "platform": "remote",
    },
    # =============== CAMERA 平台标准 ===============
    "camera_stream": {
        "device_class": None,  # camera平台不使用device_class
        "units": [],
        "keywords": ["摄像头", "camera", "视频", "stream", "监控"],
        "conversion_hints": ["视频流", "图像捕获"],
        "platform": "camera",
    },
}


class ReportGenerator:
    """报告生成器 - 处理复杂的报告生成逻辑"""

    def __init__(self):
        self.report_lines = []

    def generate_comprehensive_report(self, results: Dict) -> str:
        """生成综合分析报告"""
        self.report_lines = []

        self._add_header()
        self._add_summary_section(results)
        self._add_device_differences_section(results)
        self._add_io_analysis_section(results)
        self._add_footer()

        return "\n".join(self.report_lines)

    def _add_header(self):
        """添加报告头部"""
        self.report_lines.extend(
            [
                "=" * 80,
                "🔍 LifeSmart 设备IO口映射全面分析报告",
                "=" * 80,
            ]
        )

    def _add_summary_section(self, results: Dict):
        """添加摘要部分"""
        self.report_lines.extend(
            [
                "",
                "📊 **分析摘要**",
                "-" * 40,
                f"• 官方文档表格设备: {results['total_doc_devices']} 个",
                f"• 官方文档综合设备: {results['total_official_devices']} 个",
                f"• 当前映射设备: {results['total_mapped_devices']} 个",
                f"• 当前映射设备（排除版本设备）: {results['total_mapped_no_version']} 个",
                "",
                "🔧 **特殊设备类型处理**",
                "-" * 40,
                f"• 版本设备 (VERSIONED_DEVICE_TYPES): {len(VERSIONED_DEVICE_TYPES)} 个",
                f"  - {', '.join(VERSIONED_DEVICE_TYPES.keys())}",
                f"• 动态分类设备 (DYNAMIC_CLASSIFICATION_DEVICES): {len(DYNAMIC_CLASSIFICATION_DEVICES)} 个",
                f"  - {', '.join(DYNAMIC_CLASSIFICATION_DEVICES)}",
                "",
                "🎯 **映射质量评估**",
                "-" * 40,
                f"✅ 映射正确设备: {results['doc_with_correct_mapping']} 个",
                f"❌ 映射错误设备: {results['doc_with_incorrect_mapping']} 个",
                f"❓ 缺失映射设备: {results['doc_missing_mapping']} 个",
            ]
        )

        # 计算覆盖率
        total_doc = results["total_doc_devices"]
        if total_doc > 0:
            coverage = (
                (
                    results["doc_with_correct_mapping"]
                    + results["doc_with_incorrect_mapping"]
                )
                / total_doc
            ) * 100
            quality = (
                (results["doc_with_correct_mapping"] / total_doc) * 100
                if total_doc > 0
                else 0
            )

            self.report_lines.extend(
                [
                    "",
                    f"📈 **质量指标**",
                    "-" * 40,
                    f"• 映射覆盖率: {coverage:.1f}%",
                    f"• 映射准确率: {quality:.1f}%",
                ]
            )

    def _add_device_differences_section(self, results: Dict):
        """添加设备差异部分"""
        self.report_lines.extend(
            [
                "",
                "🔄 **设备差异分析**",
                "-" * 40,
            ]
        )

        # 映射独有设备
        mapping_only = results.get("mapping_missing_from_official", [])
        if mapping_only:
            self.report_lines.extend(
                [
                    f"📋 只在映射中存在的设备 ({len(mapping_only)}个):",
                    *[
                        f"• {device}"
                        for device in sort_devices_by_official_order(mapping_only)
                    ],
                    "",
                ]
            )

        # 官方独有设备
        official_only = results.get("official_missing_from_mapping", [])
        if official_only:
            self.report_lines.extend(
                [
                    f"📋 只在官方文档中存在的设备 ({len(official_only)}个):",
                    *[
                        f"• {device}"
                        for device in sort_devices_by_official_order(official_only)
                    ],
                    "",
                ]
            )

        # 忽略设备
        ignored = results.get("ignored_devices", [])
        if ignored:
            self.report_lines.extend(
                [
                    f"🔇 已忽略设备 ({len(ignored)}个):",
                    *[
                        f"• {device}"
                        for device in sort_devices_by_official_order(ignored)
                    ],
                    "",
                ]
            )

    def _add_io_analysis_section(self, results: Dict):
        """添加IO分析部分"""
        self.report_lines.extend(
            [
                "🔍 **IO口映射详细分析**",
                "-" * 40,
                "",
            ]
        )

        # 映射错误详情
        self._add_mapping_errors_details(results.get("mapping_errors", {}))

        # 缺失映射详情
        self._add_missing_mappings_details(results.get("missing_mappings", {}))

        # 正确映射汇总
        self._add_correct_mappings_summary(results.get("correct_mappings", {}))

    def _add_mapping_errors_details(self, mapping_errors: Dict):
        """添加映射错误详情"""
        if not mapping_errors:
            return

        self.report_lines.extend(
            [
                f"❌ **映射错误设备详细信息** ({len(mapping_errors)}个)",
                "-" * 60,
            ]
        )

        sorted_devices = sort_devices_by_official_order(mapping_errors.keys())
        for device in sorted_devices:
            error_info = mapping_errors[device]
            self._add_single_device_error_info(device, error_info)

    def _add_single_device_error_info(self, device: str, error_info: Dict):
        """添加单个设备的错误信息"""
        self.report_lines.extend(
            [
                "",
                f"🔸 **{device}**",
                f"   官方文档IO口: {sorted(error_info.get('doc_ios', []))}",
                f"   当前映射IO口: {sorted(error_info.get('mapped_ios', []))}",
            ]
        )

        # 添加具体差异
        missing_ios = error_info.get("missing_ios", [])
        incorrect_ios = error_info.get("incorrect_ios", [])

        if missing_ios:
            self.report_lines.append(f"   ❌ 文档有但映射缺失: {sorted(missing_ios)}")
        if incorrect_ios:
            self.report_lines.append(f"   ❌ 映射有但文档没有: {sorted(incorrect_ios)}")

        # 添加匹配信息
        matched_pairs = error_info.get("matched_pairs", [])
        if matched_pairs:
            self.report_lines.append("   ✅ 成功匹配的IO口:")
            for doc_io, mapped_io in matched_pairs:
                if doc_io == mapped_io:
                    self.report_lines.append(f"      • {doc_io}")
                else:
                    self.report_lines.append(f"      • {doc_io} ↔ {mapped_io}")

        # 添加匹配分数
        match_score = error_info.get("match_score", 0)
        self.report_lines.append(f"   📊 匹配分数: {match_score:.1%}")

        # 添加官方文档的详细IO口功能信息
        self._add_official_doc_io_details(error_info.get("ios_details", []))

        # 添加RW权限对比分析
        self._add_rw_permission_analysis(
            device,
            error_info.get("ios_details", []),
            error_info.get("detailed_mapping", {}),
        )

        # 添加映射的详细配置信息
        self._add_mapping_details(error_info.get("detailed_mapping", {}))

        # 添加质量分析（如果有）
        self._add_quality_analysis_info(error_info.get("quality_analysis", {}))

    def _add_rw_permission_analysis(
        self, device: str, ios_details: List[Dict], detailed_mapping: Dict
    ):
        """添加RW权限对比分析"""
        if not ios_details or not detailed_mapping:
            return

        self.report_lines.append("   🔐 RW权限对比分析:")

        # 创建官方文档IO口的RW权限映射
        doc_rw_mapping = {}
        for io_detail in ios_details:
            io_port = io_detail.get("io", "")
            rw_permission = io_detail.get("rw", "")
            if io_port and rw_permission:
                doc_rw_mapping[io_port] = rw_permission

        # 检查映射中的RW权限
        rw_mismatches = []
        rw_matches = []

        for platform, platform_details in detailed_mapping.items():
            if (
                isinstance(platform_details, dict)
                and "detailed_ios" in platform_details
            ):
                for io_port, io_config in platform_details["detailed_ios"].items():
                    mapped_rw = io_config.get("rw", "")
                    doc_rw = doc_rw_mapping.get(io_port, "")

                    if doc_rw and mapped_rw:
                        if self._compare_rw_permissions(doc_rw, mapped_rw):
                            rw_matches.append((io_port, doc_rw, mapped_rw))
                        else:
                            rw_mismatches.append((io_port, doc_rw, mapped_rw))
                    elif doc_rw and not mapped_rw:
                        rw_mismatches.append((io_port, doc_rw, "未定义"))

        if rw_matches:
            for io_port, doc_rw, mapped_rw in rw_matches:
                self.report_lines.append(
                    f"      ✅ {io_port}: 文档({doc_rw}) = 映射({mapped_rw})"
                )

        if rw_mismatches:
            for io_port, doc_rw, mapped_rw in rw_mismatches:
                self.report_lines.append(
                    f"      ❌ {io_port}: 文档({doc_rw}) ≠ 映射({mapped_rw})"
                )

    def _compare_rw_permissions(self, doc_rw: str, mapped_rw: str) -> bool:
        """比较RW权限是否匹配"""

        # 标准化权限表示
        def normalize_rw(rw: str) -> str:
            rw = rw.upper().strip()
            if rw in ["RW", "R/W", "READ_WRITE"]:
                return "RW"
            elif rw in ["R", "READ"]:
                return "R"
            elif rw in ["W", "WRITE"]:
                return "W"
            return rw

        return normalize_rw(doc_rw) == normalize_rw(mapped_rw)

    def _add_official_doc_io_details(self, ios_details: List[Dict]):
        """添加官方文档IO口详细信息"""
        if not ios_details:
            return

        self.report_lines.append("   📖 官方文档IO口功能:")
        for io_detail in ios_details:
            io_port = io_detail.get("io", "")
            function = io_detail.get("name", "")
            description = io_detail.get("description", "")
            permissions = io_detail.get("rw", "")
            if io_port:
                self.report_lines.append(
                    f"      • {io_port}({permissions}): {function}"
                )
                if description and description != function:
                    # 只显示前100个字符，避免过长
                    desc_short = (
                        description[:100] + "..."
                        if len(description) > 100
                        else description
                    )
                    self.report_lines.append(f"        详细说明: {desc_short}")

    def _add_mapping_details(self, detailed_mapping: Dict):
        """添加映射详细配置信息"""
        if not detailed_mapping:
            return

        self.report_lines.append("   🔧 当前映射配置:")
        for platform, platform_details in detailed_mapping.items():
            if isinstance(platform_details, dict):
                if (
                    platform_details.get("detailed", False)
                    and "detailed_ios" in platform_details
                ):
                    self.report_lines.append(f"      • {platform}平台 (详细配置):")
                    for io_port, io_config in platform_details["detailed_ios"].items():
                        desc = io_config.get("description", "")
                        device_class = io_config.get("device_class", "")
                        unit = io_config.get("unit_of_measurement", "")
                        rw = io_config.get("rw", "")

                        config_info = []
                        if device_class:
                            config_info.append(f"class={device_class}")
                        if unit:
                            config_info.append(f"unit={unit}")
                        if rw:
                            config_info.append(f"rw={rw}")

                        config_str = (
                            f" ({', '.join(config_info)})" if config_info else ""
                        )
                        self.report_lines.append(
                            f"        {io_port}: {desc}{config_str}"
                        )
                else:
                    ios = platform_details.get("ios", [])
                    desc = platform_details.get("description", "")
                    if ios:
                        self.report_lines.append(f"      • {platform}平台: {ios}")
                        if desc:
                            self.report_lines.append(f"        说明: {desc}")

    def _add_quality_analysis_info(self, quality_analysis: Dict):
        """添加质量分析信息"""
        if not quality_analysis:
            return

        for io_port, quality_info in quality_analysis.items():
            if isinstance(quality_info, dict) and quality_info.get("issues"):
                issues = quality_info["issues"]
                self.report_lines.append(f"   ⚠️  {io_port}: {', '.join(issues)}")

    def _add_missing_mappings_details(self, missing_mappings: Dict):
        """添加缺失映射详情"""
        if not missing_mappings:
            return

        self.report_lines.extend(
            [
                "",
                f"❓ **缺失映射设备详细信息** ({len(missing_mappings)}个)",
                "-" * 60,
            ]
        )

        sorted_devices = sort_devices_by_official_order(missing_mappings.keys())
        for device in sorted_devices:
            missing_info = missing_mappings[device]
            doc_ios = sorted(missing_info.get("doc_ios", []))
            self.report_lines.extend(
                [
                    "",
                    f"🔸 **{device}**",
                    f"   需要映射的IO口: {doc_ios}",
                ]
            )

    def _add_correct_mappings_summary(self, correct_mappings: Dict):
        """添加正确映射汇总"""
        if not correct_mappings:
            return

        self.report_lines.extend(
            [
                "",
                f"✅ **映射正确设备汇总** ({len(correct_mappings)}个)",
                "-" * 60,
            ]
        )

        sorted_devices = sort_devices_by_official_order(correct_mappings.keys())
        for device in sorted_devices:
            correct_info = correct_mappings[device]
            match_score = correct_info.get("match_score", 1.0)
            platforms = list(correct_info.get("platforms", {}).keys())
            self.report_lines.extend(
                [
                    f"• {device} (匹配度: {match_score:.1%}, 平台: {', '.join(platforms)})",
                ]
            )

    def _add_footer(self):
        """添加报告尾部"""
        self.report_lines.extend(
            [
                "",
                "=" * 80,
                "📋 报告生成完成",
                "=" * 80,
            ]
        )


class MappingAnalyzer:
    """设备映射分析器 - 将复杂的分析逻辑拆分为可管理的组件"""

    def __init__(self):
        self.ignored_devices = {"SL_SC_B1", "V_IND_S"}
        self.report_generator = ReportGenerator()

    def analyze(self) -> Dict:
        """执行完整的映射分析"""
        print("🔍 开始全面设备IO口映射分析...")

        # 步骤1: 获取数据源
        data_sources = self._load_data_sources()

        # 步骤2: 构建设备集合
        device_sets = self._build_device_sets(data_sources)

        # 步骤3: 设备差异分析
        differences = self._analyze_device_differences(device_sets)

        # 步骤4: IO映射质量分析
        quality_analysis = self._analyze_io_mapping_quality(
            data_sources["doc_device_ios"], data_sources["current_mappings"]
        )

        # 步骤5: 整合分析结果
        return self._build_final_results(
            data_sources, device_sets, differences, quality_analysis
        )

    def _load_data_sources(self) -> Dict:
        """加载数据源"""
        doc_device_ios = extract_device_ios_from_docs()
        current_mappings = extract_current_mappings()
        appendix_devices = extract_appendix_device_names()

        print(f"📊 官方文档表格: {len(doc_device_ios)} 个设备有详细IO定义")
        print(f"📊 当前映射: {len(current_mappings)} 个设备")
        print(f"📊 官方文档综合: {len(appendix_devices)} 个设备")

        return {
            "doc_device_ios": doc_device_ios,
            "current_mappings": current_mappings,
            "appendix_devices": appendix_devices,
        }

    def _build_device_sets(self, data_sources: Dict) -> Dict:
        """构建设备集合"""
        # 构建官方设备集合
        doc_devices = set(data_sources["doc_device_ios"].keys())
        official_devices = doc_devices | data_sources["appendix_devices"]

        # 构建映射设备集合（排除版本设备，但保留VERSIONED_DEVICE_TYPES中的基础设备名）
        mapped_devices = set(data_sources["current_mappings"].keys())
        mapped_devices_no_version = set()

        for device in mapped_devices:
            # 特殊处理：这些看似版本设备但实际是真实设备名称
            special_real_devices = {"SL_P_V2", "SL_SC_BB_V2"}

            if device in special_real_devices:
                mapped_devices_no_version.add(device)
            # 排除版本标识符（如SL_MC_ND1_V2），但不排除VERSIONED_DEVICE_TYPES中的基础设备
            elif re.search(VERSION_PATTERN, device):
                base_device = re.sub(VERSION_PATTERN, "", device)
                if base_device in VERSIONED_DEVICE_TYPES:
                    # 对于版本设备，我们需要检查基础设备名是否已经存在映射
                    mapped_devices_no_version.add(base_device)
                # 其他版本设备（如SL_MC_ND1_V2）被排除
            else:
                mapped_devices_no_version.add(device)

        # 特殊处理：cam设备与LSCAM设备的关联
        official_devices = self._handle_cam_lscam_association(
            official_devices, mapped_devices_no_version
        )

        print(f"📊 官方设备总集合: {len(official_devices)} 个设备")
        print(f"📊 映射设备（去版本）: {len(mapped_devices_no_version)} 个设备")

        return {
            "official_devices": official_devices,
            "mapped_devices_no_version": mapped_devices_no_version,
            "doc_devices": doc_devices,
        }

    def _handle_cam_lscam_association(
        self, official_devices: Set[str], mapped_devices_no_version: Set[str]
    ) -> Set[str]:
        """处理cam设备与LSCAM设备的特殊关联"""
        has_lscam_devices = any(
            device.startswith(LSCAM_PREFIX) for device in official_devices
        )
        if has_lscam_devices and "cam" in mapped_devices_no_version:
            official_devices.add("cam")
        return official_devices

    def _analyze_device_differences(self, device_sets: Dict) -> Dict:
        """分析设备差异"""
        official_devices = device_sets["official_devices"]
        mapped_devices_no_version = device_sets["mapped_devices_no_version"]

        # 排除忽略设备进行对比
        mapping_for_comparison = mapped_devices_no_version - self.ignored_devices

        # 计算差异
        mapping_only = mapping_for_comparison - official_devices
        official_only = official_devices - mapping_for_comparison

        # 处理被忽略的设备
        actual_ignored = [
            device
            for device in self.ignored_devices
            if device in mapped_devices_no_version
        ]

        differences = {
            "mapping_missing_from_official": list(mapping_only),
            "official_missing_from_mapping": list(official_only),
            "ignored_devices": actual_ignored,
        }

        print(f"📊 映射独有设备: {len(mapping_only)} 个")
        print(f"📊 官方独有设备: {len(official_only)} 个")
        print(f"📊 已忽略设备: {len(actual_ignored)} 个")

        return differences

    def _analyze_io_mapping_quality(
        self, doc_device_ios: Dict, current_mappings: Dict
    ) -> Dict:
        """分析IO映射质量"""
        print("\n🔍 开始详细IO口映射分析...")

        quality_processor = IOQualityProcessor()
        return quality_processor.process_all_devices(doc_device_ios, current_mappings)

    def _build_final_results(
        self,
        data_sources: Dict,
        device_sets: Dict,
        differences: Dict,
        quality_analysis: Dict,
    ) -> Dict:
        """构建最终分析结果"""
        return {
            # 基础统计
            "total_doc_devices": len(data_sources["doc_device_ios"]),
            "total_mapped_devices": len(data_sources["current_mappings"]),
            "total_official_devices": len(device_sets["official_devices"]),
            "total_mapped_no_version": len(device_sets["mapped_devices_no_version"]),
            # 质量统计
            "doc_with_correct_mapping": quality_analysis["doc_with_correct_mapping"],
            "doc_with_incorrect_mapping": quality_analysis[
                "doc_with_incorrect_mapping"
            ],
            "doc_missing_mapping": quality_analysis["doc_missing_mapping"],
            # 详细信息
            "mapping_errors": quality_analysis["mapping_errors"],
            "missing_mappings": quality_analysis["missing_mappings"],
            "correct_mappings": quality_analysis["correct_mappings"],
            # 设备差异
            "ignored_devices": differences["ignored_devices"],
            "mapping_missing_from_official": differences[
                "mapping_missing_from_official"
            ],
            "official_missing_from_mapping": differences[
                "official_missing_from_mapping"
            ],
        }

    def generate_report(self, results: Dict) -> str:
        """生成分析报告"""
        return self.report_generator.generate_comprehensive_report(results)


class IOQualityProcessor:
    """IO质量处理器 - 专门处理IO映射质量分析"""

    def process_all_devices(self, doc_device_ios: Dict, current_mappings: Dict) -> Dict:
        """处理所有设备的质量分析"""
        print(f"📊 开始分析 {len(doc_device_ios)} 个文档中的设备...")

        # 过滤出真正有IO口定义的设备
        devices_with_io = {k: v for k, v in doc_device_ios.items() if v}
        devices_without_io = {k: v for k, v in doc_device_ios.items() if not v}

        print(f"✅ 有IO口定义的设备: {len(devices_with_io)} 个")
        print(f"❌ 无IO口定义的设备: {len(devices_without_io)} 个 (将被跳过)")
        if devices_without_io:
            print(
                f"   跳过的设备: {list(devices_without_io.keys())[:10]}{'...' if len(devices_without_io) > 10 else ''}"
            )

        doc_with_correct_mapping = 0
        doc_with_incorrect_mapping = 0
        doc_missing_mapping = 0
        mapping_errors = {}
        correct_mappings = {}
        missing_mappings = {}

        for device, ios in devices_with_io.items():  # 只分析有IO口定义的设备

            # 获取文档中定义的IO口
            doc_ios = {io["io"] for io in ios}

            if device not in current_mappings:
                # 设备在文档中有定义但没有映射
                doc_missing_mapping += 1
                missing_mappings[device] = {
                    "doc_ios": list(doc_ios),
                    "ios_details": ios,
                }
                continue

            # 分析设备映射质量
            quality_result = self._analyze_single_device_quality(
                device, doc_ios, ios, current_mappings[device]
            )

            if quality_result["has_errors"]:
                doc_with_incorrect_mapping += 1
                mapping_errors[device] = quality_result["error_info"]
            else:
                doc_with_correct_mapping += 1
                correct_mappings[device] = quality_result["correct_info"]

        print(f"✅ 映射正确设备: {doc_with_correct_mapping} 个")
        print(f"❌ 映射错误设备: {doc_with_incorrect_mapping} 个")
        print(f"❓ 缺失映射设备: {doc_missing_mapping} 个")

        return {
            "doc_with_correct_mapping": doc_with_correct_mapping,
            "doc_with_incorrect_mapping": doc_with_incorrect_mapping,
            "doc_missing_mapping": doc_missing_mapping,
            "mapping_errors": mapping_errors,
            "correct_mappings": correct_mappings,
            "missing_mappings": missing_mappings,
        }

    def _analyze_single_device_quality(
        self, device: str, doc_ios: Set[str], ios_details: List, device_mapping: Dict
    ) -> Dict:
        """分析单个设备的映射质量"""
        # 提取映射的IO口
        mapped_ios = self._extract_mapped_ios(device_mapping)

        # 使用通配符匹配逻辑计算匹配结果
        match_result = calculate_mapping_match_score(doc_ios, mapped_ios)

        missing_ios = match_result["unmatched_doc"]
        incorrect_ios = match_result["unmatched_mapping"]
        matched_pairs = match_result["matched_pairs"]
        match_score = match_result["match_score"]

        # 检查RW权限和其他属性是否匹配
        rw_errors = self._check_rw_permissions(device, ios_details, device_mapping)
        attribute_errors = self._check_device_attributes(
            device, ios_details, device_mapping
        )

        # 检查是否有错误 - 增加RW权限和属性错误的检查
        has_errors = bool(missing_ios or incorrect_ios or rw_errors or attribute_errors)

        if has_errors:
            return self._build_error_result(
                device,
                doc_ios,
                mapped_ios,
                missing_ios,
                incorrect_ios,
                matched_pairs,
                match_score,
                ios_details,
                device_mapping,
                rw_errors,
                attribute_errors,
            )
        else:
            return self._build_correct_result(
                doc_ios, mapped_ios, matched_pairs, match_score, device_mapping
            )

    def _extract_mapped_ios(self, device_mapping: Dict) -> Set[str]:
        """从设备映射中提取IO口列表，支持VERSIONED_DEVICE_TYPES和DYNAMIC_CLASSIFICATION_DEVICES特殊结构"""
        mapped_ios = set()

        # 1. 处理动态分类设备 (DYNAMIC_CLASSIFICATION_DEVICES)
        if device_mapping.get("dynamic", False):
            # 动态设备的各种模式都会用到不同的IO口
            for key, value in device_mapping.items():
                if key in ["dynamic", "description"]:
                    continue

                if isinstance(value, dict):
                    # 提取io字段
                    if "io" in value:
                        io_list = value["io"]
                        if isinstance(io_list, str):
                            mapped_ios.add(io_list)
                        elif isinstance(io_list, list):
                            mapped_ios.update(io_list)

                    # 提取sensor_io, binary_sensor等字段
                    if "sensor_io" in value:
                        sensor_io = value["sensor_io"]
                        if isinstance(sensor_io, list):
                            mapped_ios.update(sensor_io)

                    # 提取各平台的IO口定义
                    for platform in [
                        "climate",
                        "switch",
                        "sensor",
                        "binary_sensor",
                        "light",
                        "cover",
                    ]:
                        if platform in value:
                            platform_config = value[platform]
                            if isinstance(platform_config, dict):
                                # 从平台配置中提取IO口名称
                                mapped_ios.update(platform_config.keys())

            return mapped_ios

        # 2. 处理版本设备 (VERSIONED_DEVICE_TYPES)
        if device_mapping.get("versioned", False):
            # 版本设备的每个版本都有不同的IO口定义
            for key, value in device_mapping.items():
                if key == "versioned":
                    continue

                if isinstance(value, dict):
                    # 递归处理每个版本的配置
                    for platform, platform_config in value.items():
                        if isinstance(platform_config, dict):
                            mapped_ios.update(platform_config.keys())
                        elif isinstance(platform_config, list):
                            mapped_ios.update(platform_config)

            return mapped_ios

        # 3. 处理标准设备结构
        # 处理新的详细结构
        if "platforms" in device_mapping:
            for platform, platform_ios in device_mapping["platforms"].items():
                if isinstance(platform_ios, list):
                    mapped_ios.update(platform_ios)
                elif isinstance(platform_ios, str):
                    mapped_ios.add(platform_ios)
        else:
            # 向后兼容旧结构 - 直接从平台配置中提取IO口
            for platform, platform_ios in device_mapping.items():
                if platform not in [
                    "versioned",
                    "dynamic",
                    "detailed_platforms",
                    "name",
                ]:
                    if isinstance(platform_ios, dict):
                        # 提取IO口名称作为键
                        mapped_ios.update(platform_ios.keys())
                    elif isinstance(platform_ios, list):
                        mapped_ios.update(platform_ios)
                    elif isinstance(platform_ios, str):
                        mapped_ios.add(platform_ios)

        return mapped_ios

    def _build_error_result(
        self,
        device: str,
        doc_ios: Set[str],
        mapped_ios: Set[str],
        missing_ios: List,
        incorrect_ios: List,
        matched_pairs: List,
        match_score: float,
        ios_details: List,
        device_mapping: Dict,
        rw_errors: List,
        attribute_errors: List,
    ) -> Dict:
        """构建错误结果"""
        # 收集详细的映射信息和质量分析
        detailed_mapping_info = self._collect_detailed_mapping_info(device_mapping)
        quality_analysis = self._perform_quality_analysis(
            device, ios_details, detailed_mapping_info
        )

        error_info = {
            "doc_ios": list(doc_ios),
            "mapped_ios": list(mapped_ios),
            "missing_ios": missing_ios,
            "incorrect_ios": incorrect_ios,
            "matched_pairs": matched_pairs,
            "match_score": match_score,
            "ios_details": ios_details,
            "current_mapping": device_mapping.get("platforms", {}),
            "detailed_mapping": detailed_mapping_info,
            "quality_analysis": quality_analysis,
            "rw_errors": rw_errors,
            "attribute_errors": attribute_errors,
        }

        return {"has_errors": True, "error_info": error_info}

    def _build_correct_result(
        self,
        doc_ios: Set[str],
        mapped_ios: Set[str],
        matched_pairs: List,
        match_score: float,
        device_mapping: Dict,
    ) -> Dict:
        """构建正确结果"""
        correct_info = {
            "doc_ios": list(doc_ios),
            "mapped_ios": list(mapped_ios),
            "matched_pairs": matched_pairs,
            "match_score": match_score,
            "platforms": device_mapping.get("platforms", {}),
            "detailed_platforms": device_mapping.get("detailed_platforms", {}),
        }

        return {"has_errors": False, "correct_info": correct_info}

    def _collect_detailed_mapping_info(self, device_mapping: Dict) -> Dict:
        """收集详细的映射信息"""
        detailed_mapping_info = {}

        if "detailed_platforms" in device_mapping:
            for platform, details in device_mapping["detailed_platforms"].items():
                if details.get("detailed", False) and "detailed_ios" in details:
                    detailed_mapping_info[platform] = details["detailed_ios"]
                else:
                    detailed_mapping_info[platform] = {
                        "ios": details.get("ios", []),
                        "description": details.get("description", ""),
                        "detailed": details.get("detailed", False),
                    }

        return detailed_mapping_info

    def _perform_quality_analysis(
        self, device: str, ios_details: List, detailed_mapping_info: Dict
    ) -> Dict:
        """执行质量分析"""
        quality_analysis = {}

        if not detailed_mapping_info:
            return quality_analysis

        for io_detail in ios_details:
            doc_io_port = io_detail.get("io", "")

            # 在详细映射中查找对应的IO口
            for platform, platform_details in detailed_mapping_info.items():
                if (
                    isinstance(platform_details, dict)
                    and "detailed_ios" in platform_details
                ):
                    mapped_io_config = platform_details["detailed_ios"].get(doc_io_port)
                    if mapped_io_config:
                        quality_result = validate_io_quality_comprehensive(
                            device, io_detail, mapped_io_config
                        )
                        quality_analysis[doc_io_port] = quality_result
                        break

        return quality_analysis

    def _check_rw_permissions(
        self, device: str, ios_details: List, device_mapping: Dict
    ) -> List:
        """检查RW权限是否匹配"""
        rw_errors = []

        # 创建官方文档IO口的RW权限映射
        doc_rw_mapping = {}
        for io_detail in ios_details:
            io_port = io_detail.get("io", "")
            rw_permission = io_detail.get("rw", "")
            if io_port and rw_permission:
                doc_rw_mapping[io_port] = rw_permission

        # 检查映射中的RW权限
        if "detailed_platforms" in device_mapping:
            for platform, platform_details in device_mapping[
                "detailed_platforms"
            ].items():
                if (
                    isinstance(platform_details, dict)
                    and "detailed_ios" in platform_details
                ):
                    for io_port, io_config in platform_details["detailed_ios"].items():
                        mapped_rw = io_config.get("rw", "")
                        doc_rw = doc_rw_mapping.get(io_port, "")

                        if doc_rw and mapped_rw:
                            if not self._compare_rw_permissions(doc_rw, mapped_rw):
                                rw_errors.append(
                                    f"{io_port}: 文档权限({doc_rw}) vs 映射权限({mapped_rw})"
                                )
                        elif doc_rw and not mapped_rw:
                            rw_errors.append(
                                f"{io_port}: 文档定义权限({doc_rw})但映射未定义"
                            )

        return rw_errors

    def _compare_rw_permissions(self, doc_rw: str, mapped_rw: str) -> bool:
        """比较RW权限是否匹配"""

        # 标准化权限表示
        def normalize_rw(rw: str) -> str:
            rw = rw.upper().strip()
            if rw in ["RW", "R/W", "READ_WRITE"]:
                return "RW"
            elif rw in ["R", "READ"]:
                return "R"
            elif rw in ["W", "WRITE"]:
                return "W"
            return rw

        return normalize_rw(doc_rw) == normalize_rw(mapped_rw)

    def _check_device_attributes(
        self, device: str, ios_details: List, device_mapping: Dict
    ) -> List:
        """检查设备属性是否匹配官方文档"""
        attribute_errors = []

        # 检查映射中的设备属性是否符合官方文档描述
        if "detailed_platforms" in device_mapping:
            for platform, platform_details in device_mapping[
                "detailed_platforms"
            ].items():
                if (
                    isinstance(platform_details, dict)
                    and "detailed_ios" in platform_details
                ):
                    for io_port, io_config in platform_details["detailed_ios"].items():
                        # 查找对应的文档IO口信息
                        doc_io_info = None
                        for io_detail in ios_details:
                            if io_detail.get("io", "") == io_port:
                                doc_io_info = io_detail
                                break

                        if doc_io_info:
                            # 检查device_class是否合适
                            mapped_device_class = io_config.get("device_class", "")
                            doc_desc = doc_io_info.get("description", "").lower()
                            doc_name = doc_io_info.get("name", "").lower()

                            # 基于文档描述推断期望的device_class
                            expected_classes = []
                            if any(
                                keyword in doc_desc or keyword in doc_name
                                for keyword in ["温度", "temp", "℃"]
                            ):
                                expected_classes.append("temperature")
                            elif any(
                                keyword in doc_desc or keyword in doc_name
                                for keyword in ["湿度", "humidity", "%"]
                            ):
                                expected_classes.append("humidity")
                            elif any(
                                keyword in doc_desc or keyword in doc_name
                                for keyword in ["电量", "battery", "剩余"]
                            ):
                                expected_classes.append("battery")
                            elif any(
                                keyword in doc_desc or keyword in doc_name
                                for keyword in ["功率", "power", "w"]
                            ):
                                expected_classes.append("power")
                            elif any(
                                keyword in doc_desc or keyword in doc_name
                                for keyword in ["用电量", "energy", "kwh"]
                            ):
                                expected_classes.append("energy")
                            elif any(
                                keyword in doc_desc or keyword in doc_name
                                for keyword in ["电压", "voltage"]
                            ):
                                expected_classes.append("voltage")
                            elif any(
                                keyword in doc_desc or keyword in doc_name
                                for keyword in ["照度", "亮度", "lux"]
                            ):
                                expected_classes.append("illuminance")

                            # 检查是否匹配
                            if (
                                expected_classes
                                and mapped_device_class not in expected_classes
                            ):
                                if not mapped_device_class:
                                    attribute_errors.append(
                                        f"{io_port}: 缺失device_class，建议使用: {expected_classes[0]}"
                                    )
                                else:
                                    attribute_errors.append(
                                        f"{io_port}: device_class({mapped_device_class}) 可能不匹配文档描述，建议: {expected_classes[0]}"
                                    )

                            # 检查state_class
                            mapped_state_class = io_config.get("state_class", "")
                            if any(
                                keyword in doc_desc
                                for keyword in ["累计", "总计", "total"]
                            ):
                                if mapped_state_class not in [
                                    "total",
                                    "total_increasing",
                                ]:
                                    attribute_errors.append(
                                        f"{io_port}: state_class应为total_increasing (累计数据)"
                                    )
                            elif any(
                                keyword in doc_desc
                                for keyword in ["当前", "实时", "瞬时"]
                            ):
                                if mapped_state_class != "measurement":
                                    attribute_errors.append(
                                        f"{io_port}: state_class应为measurement (测量数据)"
                                    )

        return attribute_errors


def extract_official_device_names() -> Set[str]:
    """从附录3.1智慧设备规格名称表格中提取设备的中文名称集合"""
    docs_file = "../docs/LifeSmart 智慧设备规格属性说明.md"

    try:
        with open(docs_file, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ 文档文件未找到: {docs_file}")
        return set()

    device_names = set()
    lines = content.split("\n")
    in_device_names_table = False

    for line_num, line in enumerate(lines, 1):
        line = line.strip()

        # 找到设备规格名称表格开始
        if "### 3.1 智慧设备规格名称" in line:
            in_device_names_table = True
            continue

        # 找到下一个章节，结束解析
        if line.startswith("### 3.2") and in_device_names_table:
            break

        # 解析设备名称表格行
        if in_device_names_table and line.startswith("|") and "----" not in line:
            columns = [col.strip() for col in line.split("|")[1:-1]]  # 去掉首尾空列

            if len(columns) >= 2:
                device_type_col = columns[0].strip()
                device_name_col = columns[1].strip()

                # 跳过表格标题和分类行
                if (
                    device_type_col == "Devtype/c1s"
                    or device_name_col == "Name"
                    or device_type_col.startswith("**")
                    or device_name_col.startswith("**")
                    or not device_name_col
                ):
                    continue

                # 提取有效的中文设备名称
                if device_name_col and len(device_name_col) > 1:
                    # 处理复杂名称，如 "SL_LI_WW_V1:智能灯泡(冷暖白) SL_LI_WW_V2:调光调色智控器(O-10V)"
                    if ":" in device_name_col:
                        # 分割多个名称定义
                        parts = device_name_col.split()
                        for part in parts:
                            if ":" in part:
                                name_part = part.split(":", 1)[1]
                                # 移除括号内容
                                if "(" in name_part:
                                    name_part = name_part.split("(")[0]
                                if name_part and len(name_part) > 1:
                                    device_names.add(name_part)
                    else:
                        # 移除括号内容
                        clean_name = device_name_col
                        if "(" in clean_name:
                            clean_name = clean_name.split("(")[0].strip()
                        if "/" in clean_name:
                            # 处理如 "恒星/辰星开关伴侣一键" 这样的名称
                            device_names.add(clean_name)
                        else:
                            device_names.add(clean_name)

    print(f"🔍 从附录3.1提取到设备名称: {len(device_names)} 个")
    if device_names:
        # 显示前10个名称作为验证
        sample_names = list(sorted(device_names))[:10]
        print(f"🔍 示例设备名称: {sample_names}")

    return device_names


def extract_appendix_device_names() -> Set[str]:
    """从附录3.1智慧设备规格名称表格中提取设备名称"""
    docs_file = "../docs/LifeSmart 智慧设备规格属性说明.md"

    try:
        with open(docs_file, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ 文档文件未找到: {docs_file}")
        return set()

    appendix_devices = set()
    third_party_devices = set()  # 3.6章节的第三方设备
    lines = content.split("\n")
    in_appendix_table = False
    in_third_party_table = False

    for line_num, line in enumerate(lines, 1):
        original_line = line
        line = line.strip()

        # 找到附录3.1开始
        if "### 3.1 智慧设备规格名称" in line:
            in_appendix_table = True
            in_third_party_table = False
            continue

        # 找到附录3.6开始
        if "### 3.6 第三方设备通过控制器接入列表" in line:
            in_third_party_table = True
            in_appendix_table = False
            continue

        # 找到下一个章节，检查是否应该结束解析
        if line.startswith("###"):
            if "3.1" in line or "3.6" in line:
                # 这是我们要处理的章节，继续
                continue
            else:
                # 其他章节：只有在既不在3.1也不在3.6解析状态时才结束
                if in_appendix_table or in_third_party_table:
                    in_appendix_table = False
                    in_third_party_table = False
                # 不break，继续寻找3.6章节

        # 解析附录3.1表格行
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

        # 解析附录3.6第三方设备表格行
        elif in_third_party_table and line.startswith("|") and "----" not in line:
            columns = [col.strip() for col in line.split("|")[1:-1]]  # 去掉首尾空列

            if len(columns) >= 1:
                device_col = columns[0].strip()

                # 跳过表格标题行和空行
                if (
                    device_col == "Devtype/Cls"
                    or device_col.startswith("**")
                    or not device_col  # 跳过空行
                ):
                    continue

                # 处理设备名称列，包括非空行和重复设备行
                if device_col:
                    # 提取设备名，去掉注释部分 如 "V_T8600_P (该规格属性参考 V_AIR_P)"
                    if "(" in device_col:
                        device_name = device_col.split("(")[0].strip()
                    else:
                        device_name = device_col

                    # 验证是否为有效的设备名称
                    if (
                        device_name
                        and len(device_name) > 3  # 设备名至少4个字符
                        and (
                            device_name.startswith(
                                ("V_", "SL_", "ELIQ_", "OD_", "LSCAM:")
                            )
                            or device_name == "cam"
                        )  # 匹配设备名格式
                        and not device_name.startswith("0.0.0")
                    ):  # 排除版本号
                        third_party_devices.add(device_name)

    # 合并所有设备
    all_devices = appendix_devices | third_party_devices

    # 过滤掉带_V数字的版本设备，但保留真实设备名称
    special_real_devices = {"SL_P_V2", "SL_SC_BB_V2"}
    filtered_devices = {
        device
        for device in all_devices
        if not re.search(r"_V\d+$", device) or device in special_real_devices
    }

    print(f"🔍 附录3.1设备总数（含版本）: {len(appendix_devices)}")
    print(f"🔍 附录3.6第三方设备: {len(third_party_devices)}")
    if third_party_devices:
        print(f"🔍 第三方设备列表: {sorted(third_party_devices)}")
    print(f"🔍 合并后设备总数: {len(all_devices)}")
    print(f"🔍 过滤后设备总数（排除版本）: {len(filtered_devices)}")
    version_devices = all_devices - filtered_devices
    if version_devices:
        print(f"🔍 排除的版本设备: {sorted(version_devices)}")

    return filtered_devices


def match_wildcard_io(mapping_io: str, doc_io: str) -> bool:
    """
    匹配通配符IO口格式

    Args:
        mapping_io: 映射中的IO口，如 'EF*', 'L*'
        doc_io: 文档中的IO口，如 'EF/EFx(x取值为数字)', 'Lx(x取值为数字)'

    Returns:
        bool: 是否匹配
    """
    # 直接相等
    if mapping_io == doc_io:
        return True

    # 处理通配符匹配
    if mapping_io.endswith("*"):
        base_pattern = mapping_io[:-1]  # 移除*

        # 匹配 EF* -> EF/EFx(x取值为数字) 格式
        if re.match(rf"^{re.escape(base_pattern)}/.*x.*取值为数字", doc_io):
            return True

        # 匹配 L* -> Lx(x取值为数字) 格式
        if re.match(rf"^{re.escape(base_pattern)}x.*取值为数字", doc_io):
            return True

        # 匹配简单前缀
        if doc_io.startswith(base_pattern):
            return True

    # 反向匹配：文档通配符 -> 映射具体
    # 如文档中的 'EF/EFx(x取值为数字)' 匹配映射中的 'EF1', 'EF2' 等
    if "(x取值为数字)" in doc_io or "x(x取值为数字)" in doc_io:
        # 提取基础模式
        base_match = re.match(r"^([A-Z]+)/?([A-Z]*)", doc_io)
        if base_match:
            base1 = base_match.group(1)  # EF
            base2 = base_match.group(2) or base1  # EFx的EF部分

            # 检查映射IO是否匹配任何基础模式
            if (
                mapping_io.startswith(base1)
                or mapping_io.startswith(base2)
                or mapping_io == base1
                or mapping_io == base2
            ):
                return True

    return False


def validate_io_quality_comprehensive(
    device_name: str, doc_io_info: Dict, mapped_io_info: Dict
) -> Dict:
    """
    全面验证IO口映射质量，检查单位、转换方式、device_class等与HA标准和官方文档的匹配度

    Args:
        device_name: 设备名称
        doc_io_info: 文档中的IO口信息 {"io": "P1", "name": "开关", "description": "..."}
        mapped_io_info: 映射中的IO口信息 {"description": "...", "device_class": "...", "unit_of_measurement": "...", ...}

    Returns:
        dict: 详细的验证结果
    """
    validation_result = {
        "overall_quality": "unknown",  # excellent, good, fair, poor
        "issues": [],
        "suggestions": [],
        "ha_standard_compliance": {
            "device_class": "unknown",
            "unit_of_measurement": "unknown",
            "conversion": "unknown",
        },
        "matched_function_type": None,
    }

    doc_io = doc_io_info.get("io", "")
    doc_name = doc_io_info.get("name", "").lower()
    doc_desc = doc_io_info.get("description", "").lower()

    mapped_desc = mapped_io_info.get("description", "").lower()
    mapped_class = mapped_io_info.get("device_class", "")
    mapped_unit = mapped_io_info.get("unit_of_measurement", "")
    mapped_conversion = mapped_io_info.get("conversion", "")
    mapped_data_type = mapped_io_info.get("data_type", "")
    mapped_rw = mapped_io_info.get("rw", "")

    # 1. 确定IO口的功能类型
    function_type = None
    confidence_score = 0

    for func_type, standards in HA_STANDARD_MAPPINGS.items():
        keywords = standards["keywords"]
        matches = 0

        # 检查文档名称和描述中的关键词
        for keyword in keywords:
            if keyword in doc_name or keyword in doc_desc:
                matches += 1

        if matches > confidence_score:
            confidence_score = matches
            function_type = func_type

    validation_result["matched_function_type"] = function_type

    if not function_type:
        validation_result["issues"].append(
            f"IO口 {doc_io} 无法识别功能类型 - 不在HA_STANDARD_MAPPINGS中"
        )
        validation_result["overall_quality"] = "poor"

        # 🔥 关键修复：即使不在标准映射中，也要继续验证现有映射的问题
        if mapped_class:
            validation_result["issues"].append(
                f"IO口 {doc_io} 使用了未知的device_class: {mapped_class}"
            )
        if mapped_unit:
            validation_result["issues"].append(
                f"IO口 {doc_io} 使用了未验证的unit_of_measurement: {mapped_unit}"
            )
        if mapped_conversion:
            validation_result["issues"].append(
                f"IO口 {doc_io} 使用了未验证的conversion方式: {mapped_conversion}"
            )

        # 标记为非标准但继续处理
        validation_result["ha_standard_compliance"]["device_class"] = "non_standard"
        validation_result["ha_standard_compliance"][
            "unit_of_measurement"
        ] = "non_standard"
        validation_result["ha_standard_compliance"]["conversion"] = "non_standard"

        return validation_result

    standards = HA_STANDARD_MAPPINGS[function_type]

    # 2. 验证device_class
    expected_device_class = standards["device_class"]
    if expected_device_class:
        if mapped_class == expected_device_class:
            validation_result["ha_standard_compliance"]["device_class"] = "correct"
        elif not mapped_class:
            validation_result["ha_standard_compliance"]["device_class"] = "missing"
            validation_result["issues"].append(
                f"IO口 {doc_io} 缺失device_class，应为: {expected_device_class}"
            )
        else:
            validation_result["ha_standard_compliance"]["device_class"] = "incorrect"
            validation_result["issues"].append(
                f"IO口 {doc_io} device_class错误: {mapped_class}，应为: {expected_device_class}"
            )
    else:
        # 不需要device_class的情况（如switch）
        if mapped_class:
            validation_result["ha_standard_compliance"]["device_class"] = "unnecessary"
            validation_result["suggestions"].append(
                f"IO口 {doc_io} 不需要device_class (开关类型)"
            )
        else:
            validation_result["ha_standard_compliance"]["device_class"] = "correct"

    # 3. 验证unit_of_measurement
    expected_units = standards["units"]
    if expected_units:
        if mapped_unit in expected_units:
            validation_result["ha_standard_compliance"][
                "unit_of_measurement"
            ] = "correct"
        elif not mapped_unit:
            validation_result["ha_standard_compliance"][
                "unit_of_measurement"
            ] = "missing"
            validation_result["issues"].append(
                f"IO口 {doc_io} 缺失单位，建议使用: {expected_units}"
            )
        else:
            validation_result["ha_standard_compliance"][
                "unit_of_measurement"
            ] = "incorrect"
            validation_result["issues"].append(
                f"IO口 {doc_io} 单位错误: {mapped_unit}，建议使用: {expected_units}"
            )
    else:
        # 不需要单位的情况（如switch、motion）
        if mapped_unit:
            validation_result["ha_standard_compliance"][
                "unit_of_measurement"
            ] = "unnecessary"
            validation_result["suggestions"].append(
                f"IO口 {doc_io} 不需要单位 ({function_type}类型)"
            )
        else:
            validation_result["ha_standard_compliance"][
                "unit_of_measurement"
            ] = "correct"

    # 4. 验证数值转换方式
    conversion_hints = standards["conversion_hints"]
    if conversion_hints:
        conversion_correct = False
        for hint in conversion_hints:
            if hint in doc_desc or hint in mapped_conversion:
                conversion_correct = True
                break

        if conversion_correct:
            validation_result["ha_standard_compliance"]["conversion"] = "likely_correct"
        else:
            validation_result["ha_standard_compliance"]["conversion"] = "unclear"
            validation_result["suggestions"].append(
                f"IO口 {doc_io} 转换方式不明确，文档提示: {conversion_hints}"
            )
    else:
        validation_result["ha_standard_compliance"]["conversion"] = "not_applicable"

    # 5. 特殊验证逻辑

    # 温度设备特殊检查：IEEE754 vs 简单除法
    if function_type == "temperature":
        if "ieee754" in doc_desc.lower():
            if "ieee754" not in mapped_conversion.lower():
                validation_result["issues"].append(
                    f"IO口 {doc_io} 应使用IEEE754转换，当前: {mapped_conversion}"
                )
        elif "/10" in doc_desc or "温度值*10" in doc_desc:
            if "div_10" not in mapped_conversion and "/10" not in mapped_conversion:
                validation_result["suggestions"].append(
                    f"IO口 {doc_io} 可能需要除以10转换"
                )

    # 开关设备特殊检查：读写权限
    if function_type == "switch":
        if "type&1" in doc_desc:
            if "w" not in mapped_rw.lower():
                validation_result["issues"].append(
                    f"IO口 {doc_io} 开关控制需要写权限，当前: {mapped_rw}"
                )

    # 6. 计算整体质量评分
    correct_count = 0
    total_checks = 0

    for aspect, result in validation_result["ha_standard_compliance"].items():
        if result != "not_applicable":
            total_checks += 1
            if result in ["correct", "likely_correct"]:
                correct_count += 1

    if total_checks == 0:
        validation_result["overall_quality"] = "unknown"
    else:
        quality_score = correct_count / total_checks
        if quality_score >= 0.9:
            validation_result["overall_quality"] = "excellent"
        elif quality_score >= 0.7:
            validation_result["overall_quality"] = "good"
        elif quality_score >= 0.5:
            validation_result["overall_quality"] = "fair"
        else:
            validation_result["overall_quality"] = "poor"

    return validation_result


def calculate_mapping_match_score(doc_ios: Set[str], mapped_ios: Set[str]) -> Dict:
    """
    计算映射匹配分数，支持通配符匹配

    Returns:
        dict: {
            'matched_pairs': [(doc_io, mapped_io)],  # 匹配的IO对
            'unmatched_doc': [str],  # 文档中未匹配的IO
            'unmatched_mapping': [str],  # 映射中未匹配的IO
            'match_score': float  # 匹配分数 0-1
        }
    """
    matched_pairs = []
    unmatched_doc = set(doc_ios)
    unmatched_mapping = set(mapped_ios)

    # 寻找匹配的IO对
    for doc_io in list(unmatched_doc):
        for mapped_io in list(unmatched_mapping):
            if match_wildcard_io(mapped_io, doc_io):
                matched_pairs.append((doc_io, mapped_io))
                unmatched_doc.discard(doc_io)
                unmatched_mapping.discard(mapped_io)
                break

    # 计算匹配分数
    total_ios = len(doc_ios) + len(mapped_ios)
    if total_ios == 0:
        match_score = 1.0
    else:
        matched_count = len(matched_pairs) * 2  # 每个匹配对算2个（文档+映射）
        match_score = matched_count / total_ios

    return {
        "matched_pairs": matched_pairs,
        "unmatched_doc": list(unmatched_doc),
        "unmatched_mapping": list(unmatched_mapping),
        "match_score": match_score,
    }


def extract_device_ios_from_docs() -> Dict[str, List[Dict]]:
    """从官方文档中提取设备IO口定义（权威数据源）"""
    docs_file = "../docs/LifeSmart 智慧设备规格属性说明.md"

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
                    # 匹配设备名模式: SL_*, V_*, ELIQ_*, cam, LSCAM:*等
                    device_match = re.search(r"([A-Z][A-Z0-9_]*[:A-Z0-9_]*|cam)", name)
                    if device_match:
                        device_name = device_match.group(1)
                        # 调试：记录所有提取到的设备名称
                        debug_lines.append(
                            f"行{line_num}: 提取到设备名 '{device_name}' 来自 '{name}' 原行: {original_line[:100]}..."
                        )

                        # 正确的过滤逻辑 - 排除表格标题和格式标记
                        # 特殊设备列表：这些看似版本设备但实际是真实设备名称
                        special_real_devices = {"SL_P_V2", "SL_SC_BB_V2"}

                        if (
                            (
                                not re.search(r"_V\d+$", device_name)
                                or device_name in special_real_devices
                            )  # 排除版本标识符，但保留特殊真实设备
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
                                "Type",
                                "val",
                                "Bit",
                                "F",  # 排除风机F标记
                            ]  # 排除表格标记
                            and not device_name.startswith("**")  # 排除markdown格式标记
                            and not re.match(
                                r"^[0-9：；，\.\s\-~]+$", device_name
                            )  # 排除纯数字和标点符号
                            and not re.match(
                                r"^[0-9]+：[^；]*；?$", device_name
                            )  # 排除数字冒号格式如 "0：自动；"
                            and not re.match(
                                r"^[0-9]+~[0-9]+:[^；]*；?$", device_name
                            )  # 排除数字范围格式如 "1~3:1~3档；"
                            and "evtype" not in device_name.lower()  # 排除Devtype相关
                            and "type" not in device_name.lower()
                            and (
                                device_name.startswith(
                                    ("SL_", "V_", "ELIQ_", "OD_", "LSCAM:")
                                )
                                or device_name == "cam"
                            )  # 允许的设备名格式
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
                                # 清理IO口名称，移除反引号、HTML标签和空格
                                clean_io_port = single_io.strip("`").strip()
                                # 移除HTML标签如<br/>
                                clean_io_port = re.sub(
                                    r"<[^>]+>", "", clean_io_port
                                ).strip()
                                # 移除末尾的反引号（处理类似P1`的情况）
                                clean_io_port = clean_io_port.rstrip("`")

                                # 过滤掉非真实IO口的内容
                                if (
                                    clean_io_port  # 确保IO口不为空
                                    and not re.match(
                                        r"^[0-9]+：[^；]*；?$", clean_io_port
                                    )  # 排除数字冒号格式如 "0：自动；"
                                    and not re.match(
                                        r"^[0-9]+~[0-9]+:[^；]*；?$", clean_io_port
                                    )  # 排除数字范围格式如 "1~3:1~3档；"
                                    and not re.match(
                                        r"^[0-9]+:[^；]*；?$", clean_io_port
                                    )  # 排除类似 "1:ON" 格式
                                    and not re.match(
                                        r"^[A-Z]+:[A-Z]+$", clean_io_port
                                    )  # 排除类似 "O:OFF" 格式
                                    and len(clean_io_port) <= 20
                                ):  # 限制长度，真实IO口不会太长
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
                        # 清理IO口名称，移除反引号、HTML标签和空格
                        clean_io_port = single_io.strip("`").strip()
                        # 移除HTML标签如<br/>
                        clean_io_port = re.sub(r"<[^>]+>", "", clean_io_port).strip()
                        # 移除末尾的反引号（处理类似P1`的情况）
                        clean_io_port = clean_io_port.rstrip("`")

                        # 过滤掉非真实IO口的内容
                        if (
                            clean_io_port  # 确保IO口不为空
                            and not re.match(
                                r"^[0-9]+：[^；]*；?$", clean_io_port
                            )  # 排除数字冒号格式如 "0：自动；"
                            and not re.match(
                                r"^[0-9]+~[0-9]+:[^；]*；?$", clean_io_port
                            )  # 排除数字范围格式如 "1~3:1~3档；"
                            and not re.match(
                                r"^[0-9]+:[^；]*；?$", clean_io_port
                            )  # 排除类似 "1:ON" 格式
                            and not re.match(
                                r"^[A-Z]+:[A-Z]+$", clean_io_port
                            )  # 排除类似 "O:OFF" 格式
                            and len(clean_io_port) <= 20
                        ):  # 限制长度，真实IO口不会太长
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
    for debug_line in debug_lines:
        print(debug_line)

    return device_ios


def extract_current_mappings() -> Dict[str, Dict]:
    """从const.py中提取当前的DEVICE_MAPPING（支持增强结构）"""

    current_mappings = {}

    for device, device_config in DEVICE_MAPPING.items():
        # 处理版本设备的特殊逻辑
        if device in VERSIONED_DEVICE_TYPES:
            # 对于版本设备，我们需要验证每个版本的映射
            current_mappings[device] = {
                "platforms": {},
                "detailed_platforms": {},
                "versioned": True,
                "dynamic": False,
                "versions": {},
            }

            if isinstance(device_config, dict) and device_config.get("versioned"):
                for version_key, version_config in device_config.items():
                    if version_key != "versioned" and isinstance(version_config, dict):
                        # 提取每个版本的平台数据
                        version_platforms = extract_platform_data(version_config)
                        version_detailed = extract_detailed_platform_data(
                            version_config
                        )

                        current_mappings[device]["versions"][version_key] = {
                            "platforms": version_platforms,
                            "detailed_platforms": version_detailed,
                        }

                        # 同时添加到总的平台映射中（用于整体对比）
                        for platform, ios in version_platforms.items():
                            platform_key = f"{version_key}_{platform}"
                            current_mappings[device]["platforms"][platform_key] = ios

                        for platform, details in version_detailed.items():
                            platform_key = f"{version_key}_{platform}"
                            current_mappings[device]["detailed_platforms"][
                                platform_key
                            ] = details
            continue

        # 排除其他带_V数字的设备(fullCls版本标识符)，但保留SL_P_V2（它是真实设备名称）
        if re.search(r"_V\d+$", device) and device != "SL_P_V2":
            continue

        current_mappings[device] = {
            "platforms": {},
            "detailed_platforms": {},
            "versioned": False,
            "dynamic": device in DYNAMIC_CLASSIFICATION_DEVICES,
        }

        # 检查是否为版本化设备
        if isinstance(device_config, dict) and device_config.get("versioned"):
            current_mappings[device]["versioned"] = True
            # 处理每个版本
            for key, version_config in device_config.items():
                if key != "versioned" and isinstance(version_config, dict):
                    # 提取简化的平台数据
                    version_platforms = extract_platform_data(version_config)
                    for platform, ios in version_platforms.items():
                        platform_key = f"{key}_{platform}"
                        current_mappings[device]["platforms"][platform_key] = ios

                    # 提取详细的平台数据
                    version_detailed = extract_detailed_platform_data(version_config)
                    for platform, details in version_detailed.items():
                        platform_key = f"{key}_{platform}"
                        current_mappings[device]["detailed_platforms"][
                            platform_key
                        ] = details

        # 检查是否为动态分类设备
        elif isinstance(device_config, dict) and device_config.get("dynamic"):
            current_mappings[device]["dynamic"] = True
            # 处理动态设备的各种模式
            for key, value in device_config.items():
                if key in ["dynamic", "description"]:
                    continue

                if isinstance(value, dict):
                    # 动态设备的模式配置
                    if "io" in value:
                        io_list = value["io"]
                        if isinstance(io_list, str):
                            io_list = [io_list]
                        elif not isinstance(io_list, list):
                            continue

                        # 为动态设备的每个模式创建条目
                        mode_platform = key.replace("_mode", "").replace("always_", "")
                        current_mappings[device]["platforms"][mode_platform] = io_list
                        current_mappings[device]["detailed_platforms"][
                            mode_platform
                        ] = {
                            "ios": io_list,
                            "description": value.get("condition", ""),
                            "detailed": False,
                        }
                    else:
                        # 可能是平台映射
                        platform_data = extract_platform_data({key: value})
                        current_mappings[device]["platforms"].update(platform_data)

                        detailed_data = extract_detailed_platform_data({key: value})
                        current_mappings[device]["detailed_platforms"].update(
                            detailed_data
                        )

        # 处理普通设备映射
        elif isinstance(device_config, dict):
            platform_data = extract_platform_data(device_config)
            current_mappings[device]["platforms"] = platform_data

            detailed_data = extract_detailed_platform_data(device_config)
            current_mappings[device]["detailed_platforms"] = detailed_data

    return current_mappings


def extract_detailed_platform_data(config: Dict) -> Dict[str, Dict]:
    """从设备配置中提取详细的平台数据（包括IO口的详细属性）"""
    result = {}

    for platform, platform_info in config.items():
        # 跳过特殊键
        if platform in ["versioned", "dynamic", "description"]:
            continue

        if isinstance(platform_info, dict):
            if "io" in platform_info:
                # 旧格式的 {"io": [...], "description": "..."}
                io_list = platform_info["io"]
                if isinstance(io_list, str):
                    io_list = [io_list]
                elif not isinstance(io_list, list):
                    continue
                result[platform] = {
                    "ios": io_list,
                    "description": platform_info.get("description", ""),
                    "detailed": False,
                }
            else:
                # 新的详细映射结构: {"P1": {"description": "...", "rw": "RW", ...}}
                ios = {}
                for io_key, io_config in platform_info.items():
                    # 检查键是否是IO口格式
                    if re.match(r"^P\d+$", io_key) or io_key in [
                        "eB1",
                        "eB2",
                        "eB3",
                        "eB4",
                        "L1",
                        "L2",
                        "L3",
                        "A",
                        "A2",
                        "T",
                        "V",
                        "TR",
                        "M",
                        "SR",
                        "KP",
                        "EPA",
                        "EE",
                        "EP",
                        "EQ",
                        "bright",
                        "dark",
                        "bright1",
                        "bright2",
                        "bright3",
                        "dark1",
                        "dark2",
                        "dark3",
                    ]:

                        if isinstance(io_config, dict):
                            ios[io_key] = {
                                "description": io_config.get("description", ""),
                                "rw": io_config.get("rw", ""),
                                "data_type": io_config.get("data_type", ""),
                                "device_class": io_config.get("device_class", ""),
                                "unit_of_measurement": io_config.get(
                                    "unit_of_measurement", ""
                                ),
                                "state_class": io_config.get("state_class", ""),
                                "conversion": io_config.get("conversion", ""),
                                "commands": io_config.get("commands", {}),
                            }
                        else:
                            ios[io_key] = {
                                "description": str(io_config),
                                "rw": "",
                                "data_type": "",
                                "device_class": "",
                                "unit_of_measurement": "",
                                "state_class": "",
                                "conversion": "",
                                "commands": {},
                            }

                if ios:
                    result[platform] = {
                        "ios": list(ios.keys()),
                        "detailed_ios": ios,
                        "detailed": True,
                    }
        elif isinstance(platform_info, list):
            # 简单列表格式: ["P1", "P2"]
            result[platform] = {
                "ios": platform_info,
                "description": "",
                "detailed": False,
            }

    return result


def extract_platform_data(config: Dict) -> Dict[str, List]:
    """从设备配置中提取平台数据（支持新的详细映射结构）"""
    result = {}

    for platform, platform_info in config.items():
        # 跳过特殊键
        if platform in ["versioned", "dynamic", "description"]:
            continue

        if isinstance(platform_info, list):
            # 简单列表格式: ["P1", "P2"]
            result[platform] = platform_info
        elif isinstance(platform_info, dict):
            # 检查是否为旧格式的 {"io": [...]}
            if "io" in platform_info:
                io_list = platform_info["io"]
                if isinstance(io_list, str):
                    result[platform] = [io_list]
                elif isinstance(io_list, list):
                    result[platform] = io_list
            else:
                # 新的详细映射结构: {"P1": {"description": "...", "rw": "RW", ...}}
                io_list = []
                for io_key, io_config in platform_info.items():
                    # 检查键是否是IO口格式 (P1, P2, 等)
                    if re.match(r"^P\d+$", io_key):
                        io_list.append(io_key)
                    # 检查其他可能的IO口格式
                    elif io_key in [
                        "eB1",
                        "eB2",
                        "eB3",
                        "eB4",
                        "L1",
                        "L2",
                        "L3",
                        "A",
                        "A2",
                        "T",
                        "V",
                        "TR",
                        "M",
                        "SR",
                        "KP",
                        "EPA",
                        "EE",
                        "EP",
                        "EQ",
                        "bright",
                        "dark",
                        "bright1",
                        "bright2",
                        "bright3",
                        "dark1",
                        "dark2",
                        "dark3",
                    ]:
                        io_list.append(io_key)
                    elif isinstance(io_config, dict) and "description" in io_config:
                        io_list.append(io_key)
                    elif isinstance(io_config, str):
                        # 简单的键值对
                        io_list.append(io_key)
                if io_list:
                    result[platform] = io_list

    return result


def analyze_comprehensive_mapping() -> Dict:
    """进行全面的设备映射分析"""
    print("🔍 开始全面设备IO口映射分析...")

    # 需要忽略的设备列表（但在报告中标记为已忽略）
    IGNORED_DEVICES = {
        "SL_SC_B1",  # 需要忽略但标记
        "V_IND_S",  # 需要忽略但标记
    }

    # 获取数据源
    doc_device_ios = extract_device_ios_from_docs()  # 官方文档中的IO定义
    current_mappings = extract_current_mappings()  # 当前的映射关系
    appendix_devices = (
        extract_appendix_device_names()
    )  # 附录3.1和3.6中的完整官方设备列表

    print(f"📊 官方文档表格: {len(doc_device_ios)} 个设备有详细IO定义")
    print(f"📊 当前映射: {len(current_mappings)} 个设备")
    print(f"📊 官方文档综合: {len(appendix_devices)} 个设备")

    # 构建官方文档的完整设备集合（文档表格 + 附录）
    doc_devices = set(doc_device_ios.keys())
    official_devices = doc_devices | appendix_devices

    # 映射设备集合（排除版本设备）
    mapped_devices = set(current_mappings.keys())
    mapped_devices_no_version = {
        device
        for device in mapped_devices
        if not re.search(r"_V\d+$", device) or device == "SL_P_V2"
    }

    # 特殊处理：cam 设备应该被视为与 LSCAM: 设备等价
    # 如果官方文档中有 LSCAM: 设备，则认为 cam 是合法的
    has_lscam_devices = any(device.startswith("LSCAM:") for device in official_devices)
    if has_lscam_devices and "cam" in mapped_devices_no_version:
        # 将 cam 添加到官方设备集合中，这样它就不会被标记为映射独有
        official_devices.add("cam")

    print(f"📊 官方设备总集合: {len(official_devices)} 个设备")
    print(f"📊 映射设备（去版本）: {len(mapped_devices_no_version)} 个设备")

    analysis_results = {
        "total_doc_devices": len(doc_device_ios),
        "total_mapped_devices": len(current_mappings),
        "total_official_devices": len(official_devices),
        "total_mapped_no_version": len(mapped_devices_no_version),
        "doc_with_correct_mapping": 0,
        "doc_with_incorrect_mapping": 0,
        "doc_missing_mapping": 0,
        "mapping_errors": {},
        "missing_mappings": {},
        "correct_mappings": {},
        "ignored_devices": [],  # 被忽略的设备
        # 核心对比结果
        "mapping_missing_from_official": [],  # 映射有但官方没有的设备
        "official_missing_from_mapping": [],  # 官方有但映射没有的设备
    }

    # 核心对比分析：MAPPING vs 官方文档综合集合
    # 排除被忽略的设备
    mapping_for_comparison = mapped_devices_no_version - set(IGNORED_DEVICES)

    # 计算差异
    mapping_only = mapping_for_comparison - official_devices
    official_only = official_devices - mapping_for_comparison

    # 处理被忽略的设备
    for ignored_device in IGNORED_DEVICES:
        if ignored_device in mapped_devices_no_version:
            analysis_results["ignored_devices"].append(ignored_device)

    analysis_results["mapping_missing_from_official"] = list(mapping_only)
    analysis_results["official_missing_from_mapping"] = list(official_only)

    # 分析有文档定义的设备的映射正确性
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

            # 使用新的IO提取方法处理所有设备类型
            device_mapping = current_mappings[device]

            # 实例化分析器来使用提取方法
            analyzer = DeviceAttributeAnalyzer()
            mapped_ios = analyzer._extract_mapped_ios(device_mapping)

            # 使用新的通配符匹配逻辑
            match_result = calculate_mapping_match_score(doc_ios, mapped_ios)

            missing_ios = match_result["unmatched_doc"]  # 文档有但映射缺失的IO口
            incorrect_ios = match_result[
                "unmatched_mapping"
            ]  # 映射有但文档没有的IO口（错误映射）
            matched_pairs = match_result["matched_pairs"]  # 成功匹配的IO对
            match_score = match_result["match_score"]  # 匹配分数

            if missing_ios or incorrect_ios:
                analysis_results["doc_with_incorrect_mapping"] += 1
                # 收集详细的IO口信息
                detailed_mapping_info = {}
                if "detailed_platforms" in device_mapping:
                    for platform, details in device_mapping[
                        "detailed_platforms"
                    ].items():
                        if details.get("detailed", False) and "detailed_ios" in details:
                            detailed_mapping_info[platform] = details["detailed_ios"]
                        else:
                            detailed_mapping_info[platform] = {
                                "ios": details.get("ios", []),
                                "description": details.get("description", ""),
                                "detailed": details.get("detailed", False),
                            }

                # 添加质量验证分析
                quality_analysis = {}
                if detailed_mapping_info:
                    for io_detail in ios:
                        doc_io_port = io_detail.get("io", "")
                        # 在详细映射中查找对应的IO口
                        for platform, platform_details in detailed_mapping_info.items():
                            if (
                                isinstance(platform_details, dict)
                                and "detailed_ios" in platform_details
                            ):
                                mapped_io_config = platform_details["detailed_ios"].get(
                                    doc_io_port
                                )
                                if mapped_io_config:
                                    quality_result = validate_io_quality_comprehensive(
                                        device, io_detail, mapped_io_config
                                    )
                                    quality_analysis[doc_io_port] = quality_result
                                    break

                analysis_results["mapping_errors"][device] = {
                    "doc_ios": list(doc_ios),
                    "mapped_ios": list(mapped_ios),
                    "missing_ios": missing_ios,
                    "incorrect_ios": incorrect_ios,
                    "matched_pairs": matched_pairs,
                    "match_score": match_score,
                    "ios_details": ios,
                    "current_mapping": device_mapping.get("platforms", {}),
                    "detailed_mapping": detailed_mapping_info,
                    "quality_analysis": quality_analysis,  # 新增质量分析
                }
            else:
                analysis_results["doc_with_correct_mapping"] += 1
                analysis_results["correct_mappings"][device] = {
                    "doc_ios": list(doc_ios),
                    "mapped_ios": list(mapped_ios),
                    "matched_pairs": matched_pairs,
                    "match_score": match_score,
                    "platforms": device_mapping.get("platforms", {}),
                    "detailed_platforms": device_mapping.get("detailed_platforms", {}),
                }

    return analysis_results


def generate_comprehensive_report(analysis_results: Dict) -> str:
    """生成全面分析报告"""
    report = []
    report.append("=" * 80)
    report.append("📊 设备映射与官方文档对比分析报告")
    report.append("=" * 80)
    report.append("")

    # 统计概览
    report.append("📈 数据源统计:")
    report.append(f"   • 官方文档表格设备: {analysis_results['total_doc_devices']}")
    report.append(
        f"   • 官方文档综合设备: {analysis_results['total_official_devices']}"
    )
    report.append(
        f"   • 当前映射设备: {analysis_results['total_mapped_no_version']}（排除版本设备）"
    )
    report.append("")

    # 核心对比结果：只在有差异时显示
    has_differences = (
        analysis_results.get("mapping_missing_from_official")
        or analysis_results.get("official_missing_from_mapping")
        or analysis_results.get("ignored_devices")
    )

    if has_differences:
        report.append("🔍 映射与官方文档差异分析:")
        report.append("")

        # 映射有但官方没有的设备
        if analysis_results.get("mapping_missing_from_official"):
            report.append(
                f"🚨 映射独有设备 ({len(analysis_results['mapping_missing_from_official'])}个):"
            )
            report.append("   (这些设备在映射中存在但官方文档中找不到)")
            for device in sort_devices_by_official_order(
                analysis_results["mapping_missing_from_official"]
            ):
                report.append(f"     • {device}")
            report.append("")

        # 官方有但映射没有的设备
        if analysis_results.get("official_missing_from_mapping"):
            report.append(
                f"⚠️ 官方独有设备 ({len(analysis_results['official_missing_from_mapping'])}个):"
            )
            report.append("   (这些设备在官方文档中存在但映射中缺失)")
            for device in sort_devices_by_official_order(
                analysis_results["official_missing_from_mapping"]
            ):
                report.append(f"     • {device}")
            report.append("")

        # 显示被忽略的设备
        if analysis_results.get("ignored_devices"):
            report.append(
                f"🔇 已忽略设备 ({len(analysis_results['ignored_devices'])}个):"
            )
            report.append("   (这些设备被标记为忽略，不参与对比)")
            for device in sort_devices_by_official_order(
                analysis_results["ignored_devices"]
            ):
                report.append(f"     • {device}")
            report.append("")
    else:
        report.append("✅ 映射与官方文档完全一致，无差异设备")
        report.append("")

    # IO口映射质量分析（仅显示有错误的设备）
    if analysis_results["mapping_errors"]:
        report.append("📋 映射质量统计:")
        report.append(
            f"   • 文档设备映射正确: {analysis_results['doc_with_correct_mapping']}"
        )
        report.append(
            f"   • 文档设备映射错误: {analysis_results['doc_with_incorrect_mapping']}"
        )
        if analysis_results["doc_missing_mapping"] > 0:
            report.append(
                f"   • 文档设备缺失映射: {analysis_results['doc_missing_mapping']}"
            )
        report.append("")

        report.append("🚨 IO口映射错误详情:")
        report.append("")
        for device, error_info in analysis_results["mapping_errors"].items():
            report.append(f"🔸 {device}")
            report.append(f"   官方文档IO口: {error_info['doc_ios']}")
            report.append(f"   当前映射IO口: {error_info['mapped_ios']}")

            # 显示匹配信息
            if "matched_pairs" in error_info and error_info["matched_pairs"]:
                report.append("   ✅ 成功匹配的IO口:")
                for doc_io, mapped_io in error_info["matched_pairs"]:
                    if doc_io == mapped_io:
                        report.append(f"      • {doc_io}")
                    else:
                        report.append(f"      • {doc_io} ↔ {mapped_io}")

            if "match_score" in error_info:
                score_percent = error_info["match_score"] * 100
                report.append(f"   📊 匹配分数: {score_percent:.1f}%")

            if error_info["missing_ios"]:
                report.append(f"   ❌ 缺失IO口: {error_info['missing_ios']}")

            if error_info["incorrect_ios"]:
                report.append(f"   ❌ 错误映射IO口: {error_info['incorrect_ios']}")
                report.append("      这些IO口在官方文档中不存在")

            # 显示官方文档中该设备的详细IO口功能信息
            if "ios_details" in error_info and error_info["ios_details"]:
                report.append("   📖 官方文档IO口功能:")
                for io_detail in error_info["ios_details"]:
                    io_port = io_detail.get("io", "")
                    function = io_detail.get("name", "")
                    description = io_detail.get("description", "")
                    if io_port:
                        report.append(f"      • {io_port}: {function}")
                        if description and description != function:
                            report.append(f"        详细说明: {description}")

            # 显示映射质量分析结果
            if "quality_analysis" in error_info and error_info["quality_analysis"]:
                report.append("   🔍 映射质量分析:")
                for io_port, quality_result in error_info["quality_analysis"].items():
                    overall_quality = quality_result.get("overall_quality", "unknown")
                    function_type = quality_result.get(
                        "matched_function_type", "unknown"
                    )

                    # 质量等级图标
                    quality_icons = {
                        "excellent": "🟢",
                        "good": "🟡",
                        "fair": "🟠",
                        "poor": "🔴",
                        "unknown": "⚪",
                    }
                    quality_icon = quality_icons.get(overall_quality, "⚪")

                    report.append(
                        f"      • {io_port} ({function_type}) {quality_icon} {overall_quality}"
                    )

                    # 显示具体问题
                    issues = quality_result.get("issues", [])
                    if issues:
                        for issue in issues:
                            report.append(f"        ❌ {issue}")

                    # 显示建议
                    suggestions = quality_result.get("suggestions", [])
                    if suggestions:
                        for suggestion in suggestions:
                            report.append(f"        💡 {suggestion}")

                    # 显示HA标准合规性
                    compliance = quality_result.get("ha_standard_compliance", {})
                    compliance_summary = []
                    for aspect, status in compliance.items():
                        if status == "correct":
                            compliance_summary.append(f"{aspect}✅")
                        elif status in ["missing", "incorrect"]:
                            compliance_summary.append(f"{aspect}❌")
                        elif status == "unnecessary":
                            compliance_summary.append(f"{aspect}⚠️")

                    if compliance_summary:
                        report.append(
                            f"        📋 HA标准: {', '.join(compliance_summary)}"
                        )

            report.append("")

    # 缺失映射的设备
    if analysis_results["missing_mappings"]:
        report.append("⚠️ 缺失映射的设备:")
        report.append("")
        for device, info in analysis_results["missing_mappings"].items():
            report.append(f"🔸 {device}")
            report.append(f"   官方文档IO口: {info['doc_ios']}")
            for io_detail in info["ios_details"]:
                report.append(
                    f"     {io_detail['io']}({io_detail['rw']}): {io_detail['name']}"
                )
            report.append("")

    # 映射质量评估
    total_doc_devices = analysis_results["total_doc_devices"]
    if total_doc_devices > 0:
        accuracy = (
            analysis_results["doc_with_correct_mapping"] / total_doc_devices
        ) * 100
        report.append(
            f"🎯 IO口映射准确率: {analysis_results['doc_with_correct_mapping']}/{total_doc_devices} ({accuracy:.1f}%)"
        )

    # 设备覆盖率
    if analysis_results["total_official_devices"] > 0:
        coverage = (
            analysis_results["total_mapped_no_version"]
            / analysis_results["total_official_devices"]
        ) * 100
        report.append(
            f"🎯 设备映射覆盖率: {analysis_results['total_mapped_no_version']}/{analysis_results['total_official_devices']} ({coverage:.1f}%)"
        )

    return "\n".join(report)


if __name__ == "__main__":
    print("🔍 开始生成两份LifeSmart设备分析报告...")

    # 使用新的模块化分析器
    analyzer = MappingAnalyzer()
    results = analyzer.analyze()

    # 获取数据源
    doc_devices = set(results.get("doc_devices", []))
    current_devices = set(DEVICE_MAPPING.keys())
    doc_device_ios = extract_device_ios_from_docs()

    print("📊 生成报告1: 设备覆盖对比分析...")

    # 报告1：设备覆盖对比分析 + 设备name字段验证
    coverage_report = []
    coverage_report.append("=" * 80)
    coverage_report.append("📊 LifeSmart 设备覆盖对比分析报告")
    coverage_report.append("=" * 80)
    coverage_report.append("")

    # 数据摘要
    total_doc = results.get("total_official_devices", 0)
    total_mapped = results.get("total_mapped_no_version", 0)
    common_devices = len(doc_devices & current_devices)
    missing_devices = len(results.get("official_missing_from_mapping", []))
    extra_devices = len(results.get("mapping_missing_from_official", []))

    coverage_rate = (common_devices / total_doc * 100) if total_doc > 0 else 0

    coverage_report.append("📈 **数据摘要**")
    coverage_report.append("-" * 40)
    coverage_report.append(f"• 官方文档设备总数: {total_doc} 个")
    coverage_report.append(f"• 当前映射设备总数: {total_mapped} 个")
    coverage_report.append("")

    coverage_report.append("📊 **覆盖率分析**")
    coverage_report.append("-" * 40)
    coverage_report.append(f"• 映射覆盖率: {coverage_rate:.1f}%")
    coverage_report.append(f"• 已覆盖设备: {common_devices} 个")
    coverage_report.append(f"• 缺失设备: {missing_devices} 个")
    coverage_report.append(f"• 多余设备: {extra_devices} 个")
    coverage_report.append("")

    # 新增：设备name字段验证
    coverage_report.append("📋 **设备name字段验证**")
    coverage_report.append("-" * 40)

    # 执行name验证
    attribute_analyzer = DeviceAttributeAnalyzer()
    name_validation_results = attribute_analyzer.validate_device_names()

    total_devices = name_validation_results["total_devices"]
    with_name = name_validation_results["devices_with_name"]
    without_name = name_validation_results["devices_without_name"]
    invalid_name = name_validation_results["devices_with_invalid_name"]
    valid_name = len(name_validation_results["valid_name_devices"])

    coverage_report.append(f"• 分析设备总数: {total_devices} 个")
    coverage_report.append(
        f"• 有name字段: {with_name} ({with_name/total_devices*100:.1f}%)"
    )
    coverage_report.append(
        f"• 缺失name字段: {without_name} ({without_name/total_devices*100:.1f}%)"
    )
    coverage_report.append(
        f"• name字段有效: {valid_name} ({valid_name/total_devices*100:.1f}%)"
    )
    coverage_report.append(
        f"• name字段无效: {invalid_name} ({invalid_name/total_devices*100:.1f}%)"
    )
    coverage_report.append("")

    # name字段问题详情
    if name_validation_results["missing_name_devices"]:
        coverage_report.append(
            f"⚠️ **缺失name字段设备** ({len(name_validation_results['missing_name_devices'])}个):"
        )
        for item in name_validation_results["missing_name_devices"][
            :10
        ]:  # 只显示前10个
            coverage_report.append(f"   • {item['device_id']}")
        if len(name_validation_results["missing_name_devices"]) > 10:
            remaining = len(name_validation_results["missing_name_devices"]) - 10
            coverage_report.append(f"   • ... 还有 {remaining} 个设备缺失name字段")
        coverage_report.append("")

    if name_validation_results["invalid_name_devices"]:
        coverage_report.append(
            f"❌ **name字段无效设备** ({len(name_validation_results['invalid_name_devices'])}个):"
        )
        for item in name_validation_results["invalid_name_devices"][:5]:  # 只显示前5个
            coverage_report.append(
                f"   • {item['device_id']} (name: \"{item['name']}\")"
            )
        if len(name_validation_results["invalid_name_devices"]) > 5:
            remaining = len(name_validation_results["invalid_name_devices"]) - 5
            coverage_report.append(f"   • ... 还有 {remaining} 个设备name字段无效")
        coverage_report.append("")

    # 设备分类对比
    coverage_report.append("🔍 **设备分类对比**")
    coverage_report.append("-" * 40)

    # 缺失设备
    missing_list = results.get("official_missing_from_mapping", [])
    if missing_list:
        coverage_report.append(f"📋 **缺失设备列表** ({len(missing_list)}个):")
        for device in sort_devices_by_official_order(missing_list):
            coverage_report.append(f"   ❌ {device}")
        coverage_report.append("")

    # 多余设备
    extra_list = results.get("mapping_missing_from_official", [])
    if extra_list:
        coverage_report.append(f"🔧 **多余设备列表** ({len(extra_list)}个):")
        for device in sort_devices_by_official_order(extra_list):
            coverage_report.append(f"   ➕ {device}")
        coverage_report.append("")

    # 共同设备
    common_list = list(doc_devices & current_devices)
    if common_list:
        coverage_report.append(f"✅ **共同设备列表** ({len(common_list)}个):")
        for device in sort_devices_by_official_order(common_list):
            coverage_report.append(f"   ✓ {device}")
        coverage_report.append("")

    coverage_report.append("=" * 80)
    coverage_report.append("📋 设备覆盖对比分析报告生成完成")
    coverage_report.append("=" * 80)

    # 保存报告1
    with open("../device_coverage_analysis.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(coverage_report))
    print("✅ 设备覆盖对比分析报告（含name验证）已保存到: device_coverage_analysis.txt")

    print("🔍 生成报告2: IO口详细对比分析...")

    # 报告2：IO口详细对比分析
    io_report = []
    io_report.append("=" * 80)
    io_report.append("🔍 LifeSmart 设备IO口详细对比分析报告")
    io_report.append("=" * 80)
    io_report.append("")

    # 只分析有IO定义且有映射的设备
    common_devices_with_io = set(doc_device_ios.keys()) & current_devices

    io_report.append("📊 **IO口对比分析摘要**")
    io_report.append("-" * 40)
    io_report.append(f"• 可对比设备总数: {len(common_devices_with_io)} 个")

    # 分析结果统计
    perfect_match = []
    partial_match = []
    mismatch = []

    for device in sort_devices_by_official_order(common_devices_with_io):
        if device not in doc_device_ios or not doc_device_ios[device]:
            continue

        doc_ios_set = set(io_def["io"] for io_def in doc_device_ios[device])

        # 从当前映射中提取IO口
        mapped_ios_set = set()
        device_config = DEVICE_MAPPING.get(device, {})

        for platform, platform_config in device_config.items():
            if platform in ["dynamic", "versioned"]:
                continue
            if isinstance(platform_config, dict):
                for io_name in platform_config.keys():
                    if io_name not in [
                        "dynamic",
                        "switch_mode",
                        "climate_mode",
                        "condition",
                    ]:
                        mapped_ios_set.add(io_name)

        # 计算匹配情况
        matched_ios = doc_ios_set & mapped_ios_set
        total_ios = len(doc_ios_set | mapped_ios_set)
        match_score = len(matched_ios) / total_ios if total_ios > 0 else 0

        device_info = {
            "device": device,
            "doc_ios": sorted(doc_ios_set),
            "mapped_ios": sorted(mapped_ios_set),
            "match_score": match_score,
            "missing_ios": sorted(doc_ios_set - mapped_ios_set),
            "extra_ios": sorted(mapped_ios_set - doc_ios_set),
        }

        if match_score == 1.0:
            perfect_match.append(device_info)
        elif match_score >= 0.5:
            partial_match.append(device_info)
        else:
            mismatch.append(device_info)

    io_report.append(f"• 完美匹配设备: {len(perfect_match)} 个")
    io_report.append(f"• 部分匹配设备: {len(partial_match)} 个")
    io_report.append(f"• 不匹配设备: {len(mismatch)} 个")
    io_report.append("")

    # 完美匹配详情
    if perfect_match:
        io_report.append("✅ **完美匹配设备详情**")
        io_report.append("-" * 50)
        for device_info in perfect_match:
            io_report.append(f"🔸 **{device_info['device']}**")
            io_report.append(f"   IO口: {', '.join(device_info['doc_ios'])}")
            io_report.append(f"   匹配度: {device_info['match_score']:.1%}")
            io_report.append("")

    # 部分匹配详情
    if partial_match:
        io_report.append("⚠️ **部分匹配设备详情**")
        io_report.append("-" * 50)
        for device_info in partial_match:
            io_report.append(f"🔸 **{device_info['device']}**")
            io_report.append(f"   官方IO口: {', '.join(device_info['doc_ios'])}")
            io_report.append(f"   映射IO口: {', '.join(device_info['mapped_ios'])}")
            io_report.append(f"   匹配度: {device_info['match_score']:.1%}")
            if device_info["missing_ios"]:
                io_report.append(
                    f"   ❌ 缺失IO口: {', '.join(device_info['missing_ios'])}"
                )
            if device_info["extra_ios"]:
                io_report.append(
                    f"   ➕ 多余IO口: {', '.join(device_info['extra_ios'])}"
                )
            io_report.append("")

    # 不匹配详情
    if mismatch:
        io_report.append("❌ **不匹配设备详情**")
        io_report.append("-" * 50)
        for device_info in mismatch:
            io_report.append(f"🔸 **{device_info['device']}**")
            io_report.append(f"   官方IO口: {', '.join(device_info['doc_ios'])}")
            io_report.append(f"   映射IO口: {', '.join(device_info['mapped_ios'])}")
            io_report.append(f"   匹配度: {device_info['match_score']:.1%}")
            if device_info["missing_ios"]:
                io_report.append(
                    f"   ❌ 缺失IO口: {', '.join(device_info['missing_ios'])}"
                )
            if device_info["extra_ios"]:
                io_report.append(
                    f"   ➕ 多余IO口: {', '.join(device_info['extra_ios'])}"
                )
            io_report.append("")

    # 统计摘要
    missing_count = sum(len(info["missing_ios"]) for info in partial_match + mismatch)
    extra_count = sum(len(info["extra_ios"]) for info in partial_match + mismatch)

    io_report.append("📈 **IO口统计摘要**")
    io_report.append("-" * 50)
    io_report.append(
        f"• 需要补充IO口的设备: {len([d for d in partial_match + mismatch if d['missing_ios']])} 个"
    )
    io_report.append(
        f"• 有多余IO口的设备: {len([d for d in partial_match + mismatch if d['extra_ios']])} 个"
    )
    io_report.append(f"• 总计缺失IO口数: {missing_count} 个")
    io_report.append(f"• 总计多余IO口数: {extra_count} 个")
    io_report.append("")

    io_report.append("=" * 80)
    io_report.append("🔍 IO口详细对比分析报告生成完成")
    io_report.append("=" * 80)

    # 保存报告2
    with open("../io_mapping_detailed_analysis.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(io_report))
    print("✅ IO口详细对比分析报告已保存到: io_mapping_detailed_analysis.txt")

    print("📋 生成报告3: 设备属性缺失分析...")

    # 报告3：设备属性缺失分析 - 基于const.py中的详细设备定义
    attribute_analyzer = DeviceAttributeAnalyzer()
    attribute_results = attribute_analyzer.analyze_missing_attributes()

    # 始终生成第三份报告，无论是否有缺失
    attribute_report = attribute_analyzer.generate_attribute_report(attribute_results)

    with open("../device_attributes_missing_analysis.md", "w", encoding="utf-8") as f:
        f.write(attribute_report)
    print("✅ 设备属性缺失分析报告已保存到: device_attributes_missing_analysis.md")

    # 生成JSON格式补丁建议
    patches_json = attribute_analyzer.generate_patches_json(attribute_results)

    with open("../device_attributes_patches.json", "w", encoding="utf-8") as f:
        import json

        f.write(json.dumps(patches_json, indent=2, ensure_ascii=False))
    print("✅ 设备属性补丁建议已保存到: device_attributes_patches.json")

    if attribute_results["devices_with_missing"] > 0:
        print(
            "📊 发现 {} 个设备存在属性缺失".format(
                attribute_results["devices_with_missing"]
            )
        )
    else:
        print("📊 所有设备属性配置完整，无缺失")

    print("✅ 三份报告生成完成!")

    # 删除我创建的临时脚本文件
    import os

    if os.path.exists("dual_report_generator.py"):
        os.remove("dual_report_generator.py")
        print("🗑️ 已清理临时脚本文件")
