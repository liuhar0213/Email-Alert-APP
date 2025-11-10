# 🔧 GitHub Actions构建失败故障排查

## 📋 如何查看错误日志

1. **进入GitHub仓库的Actions页面**
   - 点击顶部"Actions"标签

2. **点击失败的构建记录**（红色×的那一行）

3. **点击"build"作业**

4. **展开失败的步骤**（有红色×的步骤）

5. **复制错误信息**
   - 通常在红色文字部分
   - 或者最后几行的错误消息

---

## 🛠️ 常见错误和解决方案

### 错误1: 构建超时（最常见）

**症状**:
```
Error: The operation was canceled.
```
或构建运行了一段时间后被取消

**原因**: 免费GitHub Actions默认6小时超时，但某些步骤可能更短

**解决方案**:
✅ 使用优化版配置文件 `build-optimized.yml`

**步骤**:
1. 在GitHub仓库中，删除旧的 `.github/workflows/build.yml`
2. 上传新的 `build-optimized.yml` 到 `.github/workflows/` 目录
3. 重新运行workflow

---

### 错误2: Android SDK License未接受

**症状**:
```
You have not accepted the license agreements
```

**解决方案**:
✅ 优化版配置已自动接受license

---

### 错误3: 依赖安装失败

**症状**:
```
ERROR: Could not find a version that satisfies the requirement
```
或
```
Failed building wheel for cython
```

**解决方案**:
✅ 使用简化版buildozer.spec

**步骤**:
1. 将 `buildozer-simple.spec` 重命名为 `buildozer.spec`
2. 提交并推送更改
3. 重新运行构建

---

### 错误4: NDK下载失败

**症状**:
```
Failed to download NDK
```

**解决方案**:
1. 检查网络连接
2. 重新运行workflow（有时是临时网络问题）

---

### 错误5: 编译Python模块失败

**症状**:
```
Compile failed: Cython.Compiler.Errors.CompileError
```

**解决方案**:
✅ 使用固定版本的Cython (0.29.33)，优化版已包含

---

### 错误6: 内存不足

**症状**:
```
MemoryError
```
或
```
Killed
```

**解决方案**:
1. 使用简化版buildozer.spec（只构建arm64）
2. 减少并行构建

---

## 🚀 推荐解决步骤

### 方案A: 使用优化配置（推荐）

1. **上传优化文件到GitHub**:
   ```
   .github/workflows/build-optimized.yml
   buildozer-simple.spec（重命名为buildozer.spec）
   ```

2. **删除旧的build.yml**

3. **在Actions页面运行新的workflow**

---

### 方案B: 使用Google Colab打包（如果GitHub一直失败）

如果GitHub Actions持续失败，可以改用Google Colab打包：

1. 访问 https://colab.research.google.com/

2. 新建笔记本，运行以下代码：

```python
# 单元1: 安装依赖
!sudo apt-get update
!sudo apt-get install -y git zip unzip openjdk-17-jdk wget libncurses5 libssl-dev
!pip install buildozer==1.5.0 cython==0.29.33

# 单元2: 上传文件
# 点击左侧文件图标，上传 main.py 和 buildozer.spec

# 单元3: 查看文件
!ls -la

# 单元4: 构建APK（需要20-30分钟）
!yes | buildozer -v android debug

# 单元5: 下载APK
from google.colab import files
!ls -lh bin/
files.download('bin/emailalert-1.0-arm64-v8a-debug.apk')
```

---

## 📝 获取详细帮助

如果上述方案都无法解决，请提供以下信息：

1. **失败的步骤名称**
   - 例如："Build APK with Buildozer"

2. **错误日志最后20行**
   - 展开失败步骤，复制最后的错误信息

3. **构建运行时间**
   - 是否超过20分钟？

---

## ✅ 快速修复清单

- [ ] 使用 `build-optimized.yml` 替换 `build.yml`
- [ ] 使用 `buildozer-simple.spec` 替换 `buildozer.spec`
- [ ] 确保仓库是 **Public**（免费版要求）
- [ ] 重新运行workflow
- [ ] 如果还是失败，考虑用Google Colab

---

## 💡 提示

1. **首次构建最慢**: 需要下载SDK/NDK（约3GB），后续构建会用缓存
2. **查看完整日志**: 展开所有步骤，找到第一个红色×
3. **多尝试几次**: 有时是GitHub服务器网络问题
4. **不要着急**: APK构建是复杂过程，多次尝试是正常的

---

**现在请告诉我具体的错误信息，我会快速帮您解决！** 🔍
