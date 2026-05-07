# LifeSmart for Home Assistant 集成

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)
![GitHub License](https://img.shields.io/github/license/MapleEve/lifesmart-for-homeassistant)
[![version](https://img.shields.io/github/manifest-json/v/MapleEve/lifesmart-for-homeassistant?filename=custom_components%2Flifesmart%2Fmanifest.json)](https://github.com/MapleEve/lifesmart-for-homeassistant/releases/latest)
[![stars](https://img.shields.io/github/stars/MapleEve/lifesmart-for-homeassistant)](https://github.com/MapleEve/lifesmart-for-homeassistant/stargazers)
[![issues](https://img.shields.io/github/issues/MapleEve/lifesmart-for-homeassistant)](https://github.com/MapleEve/lifesmart-for-homeassistant/issues)
![haasfestworkflow](https://github.com/MapleEve/lifesmart-for-homeassistant/actions/workflows/haas-vali.yml/badge.svg)
![hacsworkflow](https://github.com/MapleEve/lifesmart-for-homeassistant/actions/workflows/hacs-vali.yml/badge.svg)

> 这是中文版文档。如需英文版，请参见 [README.md](./README.md)。

---

## 概述

LifeSmart for Home Assistant 是一款强大的智能家居集成插件，可将 LifeSmart 设备无缝接入 Home
Assistant。支持云端与本地两种模式，自动发现设备，并通过 Home Assistant 服务实现高级自动化。插件支持丰富的 LifeSmart
设备类型，包括开关、传感器、门锁、控制器、SPOT 超级碗、摄像头等。支持 HACS 一键安装与升级。

---

## 主要特性

- **双连接模式**：云端与本地模式（可选 LifeSmart API 或本地中枢）
- **全面设备支持**：开关、传感器、门锁、控制器、插座、窗帘电机、灯光、SPOT、摄像头
- **高级服务功能**：红外遥控（包括空调）、场景触发、开关点动
- **多区域支持**：中国、北美、欧洲、日本、亚太、全球自动
- **双语界面**：中英文 UI 支持
- **强力测试**：704+ 全面测试确保可靠性
- **版本兼容**：Home Assistant 2023.6.3+ 自动兼容层

### 近期重大改进 (2026年5月)

详细发布说明与 issue 处理建议见 [CHANGELOG.md](./CHANGELOG.md)。

- **📦 2026.05 main/current patch 发布准备**：文档已按待发布 `v2026.05.2` patch candidate 准备，manifest 版本已提升到 `v2026.05.2`，用于下一次 main/current 发布。该非破坏性 patch 取代失败的 `v2026.05.1`；后者因 release workflow 被 HassFest 阻塞，未产出可用 assets。
- **☁️ 云端认证**：密码登录流程会使用 LifeSmart 认证第一步返回的区域，并保存返回的 token/user/region 数据。
- **🏠 本地协议稳健性**：增强本地协议嵌套包解析，避免异常数据键触发 `TypeError: unhashable type: 'dict'`。
- **💡 设备反馈修复**：补充 `SL_SC_BG_V1`、`SL_P_V1` 运行时别名，恢复单 IO RGBW 灯创建，改善 SPOT 亮度/色温状态映射，修正杜亚窗帘方向/位置更新，并改善 climate 局部状态合并。
- **⚠️ 范围说明**：Gen2 / `v25.08.1` 架构线不参与本次 main/current 发布。
- **🔧 兼容性层**：新增 Home Assistant 2023.6.3 到 2026.05+ 版本的全面兼容支持
- **🧪 增强测试**：全面重写兼容性测试，包含14个专用测试用例
- **🏗️ 代码架构**：重大重构 -
  统一客户端接口，分离本地/OAPI客户端 ([#66](https://github.com/MapleEve/lifesmart-HACS-for-hass/pull/66))
- **🐛 Bug修复**：修复 OAPI 场景激活和删除功能 ([#73](https://github.com/MapleEve/lifesmart-HACS-for-hass/pull/73))
- **🐛 本地模式修复**：修复本地模式下设备状态更新问题 ([#65](https://github.com/MapleEve/lifesmart-HACS-for-hass/pull/65))
- **⚡ 性能优化**：用集合替换列表以提高查找速度 ([#55](https://github.com/MapleEve/lifesmart-HACS-for-hass/pull/55))
- **🛠️ 开发体验**：添加全面的 PR 模板和自动 PR 摘要
- **📊 代码质量**：集成 Black 代码格式化和 Flake8 代码检查，行长度88
- **🏷️ 许可证合规**：添加 FOSSA 许可证扫描和徽章 ([#60](https://github.com/MapleEve/lifesmart-HACS-for-hass/pull/60))

---

## 安装方法

### HACS 安装

1. 在 Home Assistant 中进入 HACS > 集成 > 搜索“LifeSmart for Home Assistant”。
2. 点击“安装”。
3. 安装完成后，点击“添加集成”，搜索“LifeSmart”。

[![通过HACS添加集成](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=MapleEve&repository=lifesmart-for-homeassistant&category=integration)
[![添加集成](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=lifesmart)

---

## 初始化配置

### 前置条件

云端模式：需在 [LifeSmart 开放平台](http://www.ilifesmart.com/open/login) 注册新应用，获取 App Key 和 App Token，并在手机
App 设置中获取 User ID。  
本地模式：需获取中枢网关的本地 IP、端口（默认 8888）、用户名（默认 admin）、密码（默认 admin）。

### 配置步骤

#### 云端模式

1. 选择“云端”作为连接方式。
2. 输入 App Key、App Token、User ID，选择区域，并选择认证方式（令牌或密码）。
3. 若选择密码认证，需输入 LifeSmart App 密码，Home Assistant 会自动刷新令牌。

#### 本地模式

1. 选择“本地”作为连接方式。
2. 输入网关 IP、端口（默认 8888）、用户名（默认 admin）、密码（默认 admin）。

---

## 使用说明

### Home Assistant 服务

发送红外按键（如电视、空调）、发送空调按键（支持电源、模式、温度、风速、摆风）、触发场景（指定中枢和场景 ID）、点动开关（指定持续时间）。

服务调用示例（YAML）：

```yaml
service: lifesmart.send_ir_keys
data:
  agt: "_xXXXXXXXXXXXXXXXXX"
  me: "sl_spot_xxxxxxxx"
  ai: "AI_IR_xxxx_xxxxxxxx"
  category: "tv"
  brand: "custom"
  keys: [ "power" ]
```

---

## 支持设备

插件支持丰富的 LifeSmart 设备类型，包括但不限于：

开关类：SL_MC_ND1、SL_MC_ND2、SL_MC_ND3、SL_NATURE、SL_P_SW、SL_S、SL_SF_IF1、SL_SF_IF2、SL_SF_IF3、SL_SF_RC、SL_SPWM、SL_SW_CP1、SL_SW_CP2、SL_SW_CP3、SL_SW_DM1、SL_SW_FE1、SL_SW_FE2、SL_SW_IF1、SL_SW_IF2、SL_SW_IF3、SL_SW_MJ1、SL_SW_MJ2、SL_SW_MJ3、SL_SW_ND1、SL_SW_ND2、SL_SW_ND3、SL_SW_RC、SL_SW_RC1、SL_SW_RC2、SL_SW_RC3、SL_SW_NS1、SL_SW_NS2、SL_SW_NS3、V_IND_S

门锁类：SL_LK_LS、SL_LK_GTM、SL_LK_AG、SL_LK_SG、SL_LK_YL、SL_P_BDLK、OD_JIUWANLI_LOCK1

控制器类：SL_P、SL_JEMA

插座类：SL_OE_DE、SL_OE_3C、SL_OL_W、OD_WE_OT1、SL_OL、SL_OL_3C、SL_OL_DE、SL_OL_UK、SL_OL_UL

窗帘电机类：SL_SW_WIN、SL_CN_IF、SL_CN_FE、SL_DOOYA、SL_P_V2

灯光类：SL_LI_RGBW、SL_CT_RGBW、SL_SC_RGB、OD_WE_QUAN、SL_LI_WW、SL_LI_GD1、SL_LI_UG1、MSL_IRCTL、OD_WE_IRCTL、SL_SPOT、SL_P_IR

传感器类：SL_SC_G、SL_SC_BG、SL_SC_MHW、SL_SC_CM、SL_SC_BM、SL_P_RM、SL_SC_THL、SL_SC_BE、SL_SC_CQ、SL_SC_CA、SL_SC_B1、SL_SC_WA、SL_SC_CH、SL_SC_CP、ELIQ_EM、SL_P_A、SL_DF_GG、SL_DF_MM、SL_DF_SR、SL_DF_BB、SL_SC_CN

SPOT 超级碗：MSL_IRCTL、OD_WE_IRCTL、SL_SPOT、SL_P_IR、SL_P_IR_V2

摄像头类：LSCAM:LSICAMGOS1、LSCAM:LSICAMEZ2

完整设备列表请参考 [代码库 const.py 文件](https://github.com/MapleEve/lifesmart-for-homeassistant/blob/main/custom_components/lifesmart/const.py)。

---

## 兼容性与测试

### Home Assistant 版本支持

本集成已在多个 Home Assistant 版本中使用conda环境进行全面测试：

| 环境       | Python  | Home Assistant | pytest | pytest-ha-custom | aiohttp | 测试状态               |
|----------|---------|----------------|--------|------------------|---------|--------------------|
| **环境1**  | 3.11.13 | **2023.6.0**   | 7.3.1  | 0.13.36          | 3.8.4   | ✅ **704/704 测试通过** |
| **环境2**  | 3.12.11 | **2024.2.0**   | 7.4.4  | 0.13.99          | 3.9.3   | ✅ **704/704 测试通过** |
| **环境3**  | 3.13.5  | **2024.12.0**  | 8.3.3  | 0.13.190         | 3.11.9  | ✅ **704/704 测试通过** |
| **当前环境** | 3.13.5  | **2026.05** | 8.4.1  | 0.13.266         | 3.12.15 | ✅ **704/704 测试通过** |

### 测试基础设施

- **Conda环境**: 为每个HA版本预配置的conda环境
- **自动化测试**: 本地CI脚本 (`.testing/test_ci_locally.sh`) 提供交互式界面
- **全面覆盖**: 704+ 单元测试，包含14个专用兼容性测试
- **CI/CD流水线**: 跨多个Python和Home Assistant版本的自动化测试

### 兼容性特性

- **自动版本检测**：无缝适配不同的 Home Assistant 和 aiohttp 版本
- **WebSocket 超时处理**：同时支持旧版本 float 超时和现代 ClientWSTimeout 对象
- **气候实体功能**：为 TURN_ON/TURN_OFF 属性提供向后兼容性
- **服务调用兼容**：处理新旧版本 Home Assistant 服务调用构造函数

### 代码质量标准

- **Black 代码格式化**：一致的代码风格，行长度88字符
- **Flake8 代码检查**：全面的代码质量检查
- **全面测试**：667+ 单元测试，包含14个专用兼容性测试
- **CI/CD 流水线**：跨多个 Python 和 Home Assistant 版本的自动化测试

---

## 开发与贡献

### 开发环境设置

```bash
# 克隆仓库
git clone https://github.com/MapleEve/lifesmart-HACS-for-hass.git
cd lifesmart-HACS-for-hass

# 设置conda测试环境（推荐）
# 首先安装conda/anaconda，然后创建测试环境：
conda create -n ci-test-ha2023.6.0-py3.11 python=3.11
conda create -n ci-test-ha2024.2.0-py3.12 python=3.12
conda create -n ci-test-ha2024.12.0-py3.13 python=3.13
conda create -n ci-test-ha-latest-py3.13 python=3.13

# 为每个环境安装依赖（以HA 2023.6.0为例）：
conda activate ci-test-ha2023.6.0-py3.11
pip install "pytest>=7.2.1,<8.0.0" "pytest-homeassistant-custom-component==0.13.36"
pip install pytest-asyncio pytest-cov flake8 black
```

### 测试

项目使用支持conda环境的综合测试脚本：

```bash
# 运行交互式测试脚本
./.testing/test_ci_locally.sh

# 可用选项：
# 1) ci-test-ha2023.6.0-py3.11  (HA 2023.6.0 + Python 3.11)
# 2) ci-test-ha2024.2.0-py3.12  (HA 2024.2.0 + Python 3.12)  
# 3) ci-test-ha2024.12.0-py3.13 (HA 2024.12.0 + Python 3.13)
# 4) ci-test-ha-latest-py3.13   (HA latest + Python 3.13)
# 5) 完整CI矩阵测试（所有环境）

# 在指定环境运行测试
conda activate ci-test-ha2023.6.0-py3.11
./.testing/test_ci_locally.sh --current

# 运行所有环境测试
./.testing/test_ci_locally.sh --all
```

### 代码质量

```bash
# 使用Black格式化代码（行长度88）
black custom_components/lifesmart/ --line-length 88

# 运行代码检查
flake8 custom_components/lifesmart/

# 运行测试
pytest custom_components/lifesmart/tests/

# 格式化代码
black custom_components/lifesmart/

# 检查代码质量
flake8 custom_components/lifesmart/
```

### 贡献指南

- 遵循现有代码风格（Black 格式化，88字符行长度）
- 为新功能添加全面测试
- 为面向用户的更改更新文档
- 使用约定式提交消息
- 在拉取请求中引用相关问题

详细的贡献指南请参见我们的 [PR 模板](.github/PULL_REQUEST_TEMPLATE.md)。

---

## 图例

**README 动态图例**

<img src="./docs/assets/zh-CN/hero.gif" alt="LifeSmart 智能家居 Home Assistant 集成" width="100%" />
<img src="./docs/assets/zh-CN/overview.gif" alt="LifeSmart 集成概述" width="100%" />
<img src="./docs/assets/zh-CN/features.gif" alt="功能特性" width="100%" />
<img src="./docs/assets/zh-CN/installation.gif" alt="通过 HACS 安装" width="100%" />
<img src="./docs/assets/zh-CN/initialization.gif" alt="初始化配置" width="100%" />
<img src="./docs/assets/zh-CN/usage.gif" alt="Home Assistant 服务" width="100%" />
<img src="./docs/assets/zh-CN/devices.gif" alt="支持的设备" width="100%" />
<img src="./docs/assets/zh-CN/compatibility.gif" alt="兼容性与测试" width="100%" />
<img src="./docs/assets/zh-CN/contributing.gif" alt="开发与贡献" width="100%" />
