# 双Fork解决方案技术文档 (Dual Fork Solution Technical Documentation)

## 概述

本文档记录了为解决 macOS ARM64 环境下 lru-dict 编译问题而实施的双fork解决方案，支持 Python 3.10 (HA 2022.10.0) 和 Python
3.11 (HA 2023.6.0) 两个版本。

## 问题背景

### Python 3.11 (HA 2023.6.0)

- **核心问题**: lru-dict==1.1.8 在 macOS ARM64 Python 3.11 环境下编译失败
- **错误信息**: `lru.c:629:17: error: incompatible function pointer types initializing 'PyCFunction'`

### Python 3.10 (HA 2022.10.0)

- **核心问题**: 同样的 lru-dict==1.1.8 编译问题
- **目标**: 支持 pytest-homeassistant-custom-component 0.12.5 在 Python 3.10 环境下的测试

## 解决方案架构

### 双Fork策略

为每个Python版本创建独立的双fork解决方案：

#### Python 3.11 分支

1. **pytest插件fork**: `MapleEve/pytest-homeassistant-custom-component-fixed@macos-fix-branch`
2. **Home Assistant fork**: `MapleEve/homeassistant-lru-dict-macos-fix@macos-fix-branch`

#### Python 3.10 分支

1. **pytest插件fork**: `MapleEve/pytest-homeassistant-custom-component-fixed@py310-fix-branch`
2. **Home Assistant fork**: `MapleEve/homeassistant-lru-dict-macos-fix@py310-fix-branch`

### 版本对应关系

```
Python 3.11 (2023.6.0)               Python 3.10 (2022.10.0)
├── pytest-ha-plugin 0.13.36  →      ├── pytest-ha-plugin 0.12.5  →  py310-fix-branch
├── Home Assistant 2023.6.0   →      ├── Home Assistant 2022.10.0  →  py310-fix-branch  
└── lru-dict==1.3.0 兼容版本         └── lru-dict==1.3.0 兼容版本
```

## 技术实现细节

### 统一安装流程

两个Python版本现在使用相同的3步安装流程：

```bash
# Step 1: 安装兼容版本的lru-dict
pip install -q lru-dict==1.3.0

# Step 2: 安装移除了lru-dict依赖的forked HA
timeout 600 pip install git+https://github.com/MapleEve/homeassistant-lru-dict-macos-fix.git@[BRANCH]

# Step 3: 安装兼容的forked pytest插件
timeout 600 pip install git+https://github.com/MapleEve/pytest-homeassistant-custom-component-fixed.git@[BRANCH]
```

### Fork修改详情

#### 1. pytest-homeassistant-custom-component Fork修改

**Python 3.11 分支** (`macos-fix-branch`):

```python
# setup.py - 改进的需求解析，跳过git URLs
if not line.startswith("git+"):
    requirements.append(line)
```

**Python 3.10 分支** (`py310-fix-branch`):

```python
# setup.py - 修复目录结构问题
packages = find_packages(),  # 移除错误的src目录配置
python_requires = ">=3.10"
```

**共同修改**:

- `requirements_test.txt`: 添加 `lru-dict==1.3.0`
- `version`: 使用PEP 440兼容的版本号

#### 2. Home Assistant Fork修改

**共同修改原则**:

- `pyproject.toml`: 移除 `"lru-dict==1.1.8",` 依赖
- 添加注释: `# lru-dict removed - install separately to avoid macOS ARM64 compilation issues`

**Python 3.11** (`homeassistant-lru-dict-macos-fix@macos-fix-branch`):

- 基于 Home Assistant 2023.6.0
- 修复 fnv-hash-fast 包名错误

**Python 3.10** (`homeassistant-lru-dict-macos-fix@py310-fix-branch`):

- 基于 Home Assistant 2022.10.0
- 彻底移除pyproject.toml中的lru-dict==1.1.8

### CI脚本集成

**test_ci_locally.sh修改**:

```bash
# 测试矩阵支持
test_matrix["2022.10.0"]="3.10"
test_matrix["2023.6.0"]="3.11"

# Python 3.10安装逻辑
if [[ "$ha_version" == "2022.10.0" ]]; then
  if [ "$(python -c '...')" = "3.10" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
      echo 'Using dual-fork solution for macOS ARM64 lru-dict compatibility (2022.10.0)...'
      echo 'Step 1: Installing lru-dict==1.3.0 (compatible version)...'
      pip install -q lru-dict==1.3.0 &&
      echo 'Step 2: Installing forked HA 2022.10.0 (lru-dict dependencies removed)...'
      timeout 600 pip install git+https://github.com/MapleEve/homeassistant-lru-dict-macos-fix.git@py310-fix-branch &&
      echo 'Step 3: Installing forked pytest plugin (compatible with our HA fork)...'
      timeout 600 pip install git+https://github.com/MapleEve/pytest-homeassistant-custom-component-fixed.git@py310-fix-branch
    fi
  fi
fi

# Python 3.11安装逻辑
if [[ "$ha_version" == "2023.6.0" ]]; then
  if [ "$(python -c '...')" = "3.11" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
      echo 'Using dual-fork solution for macOS ARM64 lru-dict compatibility...'
      echo 'Step 1: Installing lru-dict==1.3.0 (compatible version)...'
      pip install -q lru-dict==1.3.0 &&
      echo 'Step 2: Installing forked HA 2023.6.0 (lru-dict dependencies removed)...'
      timeout 600 pip install git+https://github.com/MapleEve/homeassistant-lru-dict-macos-fix.git@macos-fix-branch &&
      echo 'Step 3: Installing forked pytest plugin (compatible with our HA fork)...'
      timeout 600 pip install git+https://github.com/MapleEve/pytest-homeassistant-custom-component-fixed.git@macos-fix-branch
    fi
  fi
fi
```

## 关键技术决策

### 为什么需要双fork？

1. **pytest插件依赖**: pytest-homeassistant-custom-component需要对应版本的HA
2. **依赖链问题**: HA在多个文件中硬编码lru-dict==1.1.8
3. **版本隔离**: 不同Python版本需要不同的HA版本支持
4. **兼容性要求**: 保持完整的功能兼容性，只修改依赖版本

### 安装顺序的重要性

1. **先装lru-dict==1.3.0**: 确保有兼容版本的lru-dict
2. **再装fork的HA**: 不会尝试安装lru-dict==1.1.8
3. **最后装pytest插件**: 使用已有的lru-dict和fork的HA

### 流程统一的优势

1. **维护简化**: 两个版本使用相同的安装模式
2. **故障排除**: 统一的错误处理和调试方法
3. **文档一致**: 减少文档维护负担

## 部署状态

### ✅ 已完成

#### Python 3.11 (2023.6.0)

- [x] 创建 pytest-homeassistant-custom-component macos-fix-branch
- [x] 创建 homeassistant-lru-dict-macos-fix macos-fix-branch
- [x] CI 脚本集成和测试验证

#### Python 3.10 (2022.10.0)

- [x] 创建 pytest-homeassistant-custom-component py310-fix-branch
- [x] 创建 homeassistant-lru-dict-macos-fix py310-fix-branch
- [x] 修复setup.py目录结构问题
- [x] 修复lru-dict依赖清理问题
- [x] CI 脚本集成和测试验证

#### 通用改进

- [x] 统一两个版本的安装流程
- [x] 更新交互菜单支持2022.10.0环境
- [x] 更新版本映射配置
- [x] 修复代码风格问题

## 仓库信息

### GitHub仓库

- `MapleEve/pytest-homeassistant-custom-component-fixed@macos-fix-branch` (Python 3.11)
- `MapleEve/pytest-homeassistant-custom-component-fixed@py310-fix-branch` (Python 3.10)
- `MapleEve/homeassistant-lru-dict-macos-fix@macos-fix-branch` (Python 3.11)
- `MapleEve/homeassistant-lru-dict-macos-fix@py310-fix-branch` (Python 3.10)

## 测试验证

### 环境要求

- macOS ARM64
- Python 3.10 或 3.11
- conda环境: `ci-test-ha2022.10.0-py3.10` 或 `ci-test-ha2023.6.0-py3.11`

### 测试命令

```bash
# 测试Python 3.10环境
.testing/test_ci_locally.sh --env ci-test-ha2022.10.0-py3.10

# 测试Python 3.11环境  
.testing/test_ci_locally.sh --env ci-test-ha2023.6.0-py3.11

# 交互式选择
.testing/test_ci_locally.sh
```

### 验证结果

#### ✅ 成功指标

- lru-dict==1.3.0 安装成功（无编译错误）
- Home Assistant fork安装成功（无lru-dict依赖冲突）
- pytest-homeassistant-custom-component 兼容版本安装成功
- 依赖验证通过，显示正确的版本信息

#### 🔧 已解决的问题

- ❌ ~~lru-dict==1.1.8 ARM64编译错误~~ → ✅ 使用lru-dict==1.3.0
- ❌ ~~setup.py 'src' directory not found~~ → ✅ 修复目录结构配置
- ❌ ~~版本规格化警告~~ → ✅ 使用PEP 440兼容版本
- ❌ ~~依赖冲突错误~~ → ✅ 彻底移除lru-dict硬编码依赖

## 维护说明

### 版本同步

1. 当原始仓库更新时，需要手动同步重要的安全修复
2. 避免重新引入lru-dict依赖
3. 保持fork版本的功能与原版本一致

### 文档更新

1. 及时更新CI脚本和版本映射配置
2. 记录新发现的兼容性问题和解决方案
3. 保持两个Python版本文档的同步

### 监控策略

1. **定期测试**: 每月运行完整的双fork测试矩阵
2. **兼容性监控**: 关注lru-dict新版本发布和ARM64支持
3. **清理策略**: 当upstream修复问题时可以移除fork方案

## 相关链接

- [pytest-homeassistant-custom-component 原始仓库](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component)
- [Home Assistant Core 原始仓库](https://github.com/home-assistant/core)
- [lru-dict 兼容性问题追踪](https://github.com/amitdev/lru-dict/issues)

---

**创建时间**: 2025-08-05  
**最后更新**: 2025-08-05  
**状态**: 完成，双版本支持已验证