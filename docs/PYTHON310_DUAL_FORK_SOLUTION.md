# Python 3.10 双Fork解决方案技术文档

## 概述

本文档记录了为解决 macOS ARM64 Python 3.10 环境下 lru-dict==1.1.8 编译问题而实施的双fork解决方案。

## 问题背景

- **目标**: 支持 pytest-homeassistant-custom-component 0.12.5 (对应 Home Assistant 2022.10.0) 在 Python 3.10 环境下的测试
- **核心问题**: lru-dict==1.1.8 在 macOS ARM64 Python 3.10 环境下编译失败
- **错误信息**: `lru.c:629:17: error: incompatible function pointer types initializing 'PyCFunction'`

## 解决方案架构

### 双Fork策略

类似现有的 Python 3.11 解决方案，为 Python 3.10 创建独立的双fork：

1. **pytest插件fork**: `MapleEve/pytest-homeassistant-custom-component-fixed@py310-fix-branch`
2. **Home Assistant fork**: `MapleEve/homeassistant-2022.10.0-py310-fix@py310-fix-branch`

### 版本对应关系

```
原始版本                          Fork版本
├── pytest-ha-plugin 0.12.5  →  py310-fix-branch (基于0.12.5)
├── Home Assistant 2022.10.0  →  py310-fix-branch (移除lru-dict)
└── Python 3.10               →  使用lru-dict==1.3.0兼容版本
```

## 技术实现细节

### 1. pytest-homeassistant-custom-component Fork修改

**分支**: `py310-fix-branch` (基于tag 0.12.5)

**关键修改**:

```python
# setup.py - 改进的需求解析
requirements = ["sqlalchemy"]

# Parse requirements_test.txt more carefully
with open("requirements_test.txt", "r") as f:
    for line in f:
        line = line.strip()
        if (line and 
            not line.startswith("#") and 
            not line.startswith("-r") and 
            not line.startswith("-c") and
            not line.startswith("--") and
            not line.startswith("EOF") and
            "requirements" not in line.lower() and
            "constraints" not in line.lower() and
            "< /dev/null" not in line.lower()):
            
            if not line.startswith("git+"):
                requirements.append(line)

# 支持Python 3.10
python_requires=">=3.10"
packages=find_packages(where="src"),
package_dir={"": "src"},
```

**requirements_test.txt修改**:

```txt
# 原有内容保持不变，末尾添加：
# Fix for macOS ARM64 lru-dict compilation issue
lru-dict==1.3.0
EOF < /dev/null
```

### 2. Home Assistant 2022.10.0 Fork修改

**分支**: `py310-fix-branch` (基于tag 2022.10.0)

**关键修改**:

- `requirements.txt`: 移除 `lru-dict==1.1.8` 行
- `pyproject.toml`: 从dependencies数组中移除 `"lru-dict==1.1.8",`

### 3. CI脚本集成

**test_ci_locally.sh修改**:

```bash
# 测试矩阵添加
test_matrix["2022.10.0"]="3.10"

# 安装逻辑
if [[ "$ha_version" == "2022.10.0" ]]; then
  if [ "$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" = "3.10" ]; then
    if [[ "$OSTYPE" == "darwin"* ]]; then
      # macOS Python 3.10: 使用双fork解决方案
      echo 'Using dual-fork solution for macOS ARM64 lru-dict compatibility (2022.10.0)...'
      echo 'Step 1: Installing lru-dict==1.3.0 (compatible version)...'
      pip install -q lru-dict==1.3.0 &&
      echo 'Step 2: Installing forked HA 2022.10.0 (lru-dict dependencies removed)...'
      timeout 600 pip install -q git+https://github.com/MapleEve/homeassistant-2022.10.0-py310-fix.git@py310-fix-branch &&
      echo 'Step 3: Installing forked pytest plugin (compatible with our HA fork)...'
      timeout 600 pip install -q git+https://github.com/MapleEve/pytest-homeassistant-custom-component-fixed.git@py310-fix-branch
    else
      pip install --force-reinstall -q 'pytest-homeassistant-custom-component==0.12.5'
    fi
  else
    pip install --force-reinstall -q 'pytest-homeassistant-custom-component==0.12.5'
  fi
fi
```

**版本映射更新**:

```bash
# version_mapping.sh
show_version_mapping() {
  echo "| 2022.10.0   | 3.10   | ==0.12.5            | 2022.10.0     |"
  # ... 其他版本
}
```

## 部署状态

### ✅ 已完成

- [x] 创建 pytest-homeassistant-custom-component py310-fix-branch
- [x] 创建 homeassistant-2022.10.0-py310-fix py310-fix-branch
- [x] 更新 CI 脚本集成双fork逻辑
- [x] 更新交互菜单支持2022.10.0环境
- [x] 更新版本映射配置

### 🔄 待完成

- [ ] 推送 pytest-homeassistant-custom-component fork到GitHub
- [ ] 创建并推送 homeassistant-2022.10.0-py310-fix 仓库到GitHub
- [ ] 测试完整的双fork解决方案

## 仓库信息

### 本地仓库路径

```
/Volumes/LocalRAW/lifesmart-HACS-for-hass/temp_forks/
├── pytest-homeassistant-custom-component-fixed/  # py310-fix-branch
└── homeassistant-2022.10.0-py310-fix/           # py310-fix-branch
```

### 目标GitHub仓库

- `MapleEve/pytest-homeassistant-custom-component-fixed@py310-fix-branch`
- `MapleEve/homeassistant-2022.10.0-py310-fix@py310-fix-branch` (需创建)

## 推送命令

```bash
# 1. 推送pytest插件fork
cd temp_forks/pytest-homeassistant-custom-component-fixed
git remote add origin https://github.com/MapleEve/pytest-homeassistant-custom-component-fixed.git
git push origin py310-fix-branch

# 2. 创建并推送HA fork (需要先在GitHub创建仓库)
cd temp_forks/homeassistant-2022.10.0-py310-fix  
git remote add origin https://github.com/MapleEve/homeassistant-2022.10.0-py310-fix.git
git push origin py310-fix-branch
```

## 测试验证

### 环境要求

- macOS ARM64
- Python 3.10
- conda环境: `ci-test-ha2022.10.0-py3.10`

### 测试命令

```bash
# 测试新环境
.testing/test_ci_locally.sh --env ci-test-ha2022.10.0-py3.10

# 或交互式选择 1) ci-test-ha2022.10.0-py3.10
.testing/test_ci_locally.sh
```

### 预期结果

- lru-dict==1.3.0 安装成功（无编译错误）
- Home Assistant 2022.10.0 安装成功（无lru-dict依赖冲突）
- pytest-homeassistant-custom-component 0.12.5 兼容版本安装成功
- 所有测试通过

## 维护说明

1. **版本同步**: 当原始仓库更新时，需要手动同步重要的安全修复
2. **依赖更新**: 避免重新引入lru-dict依赖
3. **测试覆盖**: 确保fork版本的功能与原版本保持一致
4. **文档更新**: 及时更新CI脚本和版本映射配置

## 相关链接

- [Python 3.11 双Fork解决方案](./DUAL_FORK_SOLUTION.md)
- [pytest-homeassistant-custom-component 原始仓库](https://github.com/MatthewFlamm/pytest-homeassistant-custom-component)
- [Home Assistant Core 原始仓库](https://github.com/home-assistant/core)
- [lru-dict 兼容性问题追踪](https://github.com/amitdev/lru-dict/issues)

---

**创建时间**: 2025-08-05  
**最后更新**: 2025-08-05
**状态**: 开发完成，待推送到GitHub