# 双fork解决方案详细记录 (Dual Fork Solution Details)

## 背景问题
macOS ARM64 Python 3.11环境下 lru-dict==1.1.8 编译失败，导致Home Assistant 2023.6.0测试环境无法正常运行。

## 解决方案架构
1. **Fork pytest-homeassistant-custom-component**
   - 仓库: `MapleEve/pytest-homeassistant-custom-component-fixed`
   - 分支: `macos-fix-branch`
   - 修改: 修复setup.py解析问题，版本改为PEP 440兼容的"0.13.36"
   - 依赖: 指向fork的HA版本

2. **Fork Home Assistant 2023.6.0**
   - 仓库: `MapleEve/homeassistant-2023.6.0-macos-fix` 
   - 分支: `macos-fix-branch`
   - 修改: 从requirements.txt, pyproject.toml, package_constraints.txt中移除lru-dict==1.1.8
   - 修复: fnv-hash-fast包名错误

3. **CI脚本集成**
   - 文件: `.testing/test_ci_locally.sh`
   - 逻辑: 检测macOS + Python 3.11环境，自动使用双fork方案
   - 超时: 600秒防止安装超时
   - 顺序: lru-dict==1.3.0 -> fork HA -> fork pytest plugin

## 技术细节

### 环境检测逻辑
```bash
# macOS Python 3.11环境检测和双fork安装逻辑
if [ "$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')" = "3.11" ]; then
  if [[ "$OSTYPE" == "darwin"* ]]; then
    echo 'Using dual-fork solution for macOS ARM64 lru-dict compatibility...'
    echo 'Step 1: Installing lru-dict==1.3.0 (compatible version)...'
    pip install -q lru-dict==1.3.0 &&
    echo 'Step 2: Installing forked HA 2023.6.0 (lru-dict dependencies removed)...'
    timeout 600 pip install -q git+https://github.com/MapleEve/homeassistant-2023.6.0-macos-fix.git@macos-fix-branch &&
    echo 'Step 3: Installing forked pytest plugin (compatible with our HA fork)...'
    timeout 600 pip install -q git+https://github.com/MapleEve/pytest-homeassistant-custom-component-fixed.git@macos-fix-branch
  fi
fi
```

### Fork 1: pytest-homeassistant-custom-component 修改详情

#### setup.py 修复
- **问题**: 原始setup.py无法正确解析git URL格式的依赖
- **解决**: 跳过git+开头的URL，避免install_requires验证错误
- **代码**:
```python
# Skip git URLs as they are not valid for install_requires
if not line.startswith("git+"):
    requirements.append(line)
```

#### version 文件修复
- **问题**: "0.13.36-macos-fix" 不符合PEP 440规范
- **解决**: 修改为 "0.13.36"

#### requirements_test.txt 更新
- **新增**: 指向fork的HA版本
```
git+https://github.com/MapleEve/homeassistant-2023.6.0-macos-fix.git@macos-fix-branch
lru-dict==1.3.0
```

### Fork 2: Home Assistant 2023.6.0 修改详情

#### requirements.txt
- **移除**: `# lru-dict==1.1.8` (注释掉)

#### pyproject.toml 
- **移除**: lru-dict==1.1.8 依赖

#### homeassistant/package_constraints.txt
- **移除**: `# lru-dict==1.1.8` (注释掉)
- **修复**: fnv-hanh-fast==0.3.1 -> fnv-hash-fast==0.3.1

## 关键技术决策

### 为什么fork两个仓库？
1. **pytest插件要求**: pytest-homeassistant-custom-component需要安装HA 2023.6.0
2. **依赖链问题**: HA 2023.6.0在多个文件中硬编码lru-dict==1.1.8
3. **兼容性要求**: 需要保持完整的功能兼容性，只修改依赖版本

### 安装顺序的重要性
1. **先装lru-dict==1.3.0**: 确保有兼容版本的lru-dict
2. **再装fork的HA**: 不会尝试安装lru-dict==1.1.8
3. **最后装pytest插件**: 使用已有的lru-dict和fork的HA

## 验证方法

### 本地测试
```bash
cd /Volumes/LocalRAW/lifesmart-HACS-for-hass && echo "1" | ./.testing/test_ci_locally.sh
```

### 手动验证步骤
1. 创建Python 3.11虚拟环境
2. 在macOS ARM64系统运行安装步骤
3. 验证pytest插件能正常导入HA模块
4. 运行完整测试套件

## 优势
1. **完全兼容**: 保持所有HA功能不变
2. **自动检测**: 只在需要时启用双fork方案
3. **性能优化**: 使用600秒超时防止卡死
4. **维护简单**: 清晰的分支命名和文档

## 风险控制
1. **版本锁定**: 使用特定的分支而非tag，便于后续修复
2. **超时机制**: 防止网络问题导致安装卡死
3. **条件安装**: 只在确实需要时才使用fork方案
4. **测试覆盖**: 保持原有测试覆盖率不变

## 后续维护
1. **定期更新**: 当原始仓库有重要更新时同步修改
2. **监控兼容性**: 关注lru-dict新版本发布
3. **清理策略**: 当upstream修复问题时可以移除fork方案