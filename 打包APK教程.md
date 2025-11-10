# 📦 Android APK打包教程

## 🎯 推荐方案：使用GitHub Actions自动打包（最简单）

这是**最简单的方法**，完全免费，不需要配置本地环境。

### 步骤：

#### 1. 创建GitHub仓库

1. 访问 https://github.com/
2. 点击 **"New repository"**
3. 填写：
   - Repository name: `email-alert-app`
   - Public/Private: 选Public
4. 点击 **"Create repository"**

#### 2. 上传代码

将以下文件上传到GitHub：
- `main.py`
- `buildozer.spec`

**方法A：网页上传**
1. 在仓库页面点击 **"Add file"** → **"Upload files"**
2. 拖拽 `main.py` 和 `buildozer.spec`
3. 点击 **"Commit changes"**

**方法B：Git命令**
```bash
cd C:\Users\27654\Desktop\交易\project\email_alert_app
git init
git add main.py buildozer.spec
git commit -m "Initial commit"
git remote add origin https://github.com/你的用户名/email-alert-app.git
git push -u origin master
```

#### 3. 添加GitHub Actions工作流

在仓库中创建文件 `.github/workflows/build.yml`：

点击 **"Add file"** → **"Create new file"**

文件名：`.github/workflows/build.yml`

内容：

```yaml
name: Build APK

on:
  push:
    branches: [ master, main ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y git zip unzip openjdk-17-jdk wget libncurses5 libssl-dev
        pip install buildozer cython

    - name: Build APK
      run: |
        buildozer android debug

    - name: Upload APK
      uses: actions/upload-artifact@v3
      with:
        name: app-debug
        path: bin/*.apk
```

#### 4. 触发构建

1. 点击仓库的 **"Actions"** 标签
2. 点击左侧 **"Build APK"**
3. 点击右侧 **"Run workflow"** → **"Run workflow"**
4. 等待15-20分钟
5. 构建完成后，点击构建记录
6. 在 **"Artifacts"** 部分下载APK

---

## 🐳 方案2：使用Docker（推荐给有Docker的用户）

### 前提条件
- 安装Docker Desktop

### 步骤

```bash
# 1. 进入App目录
cd C:\Users\27654\Desktop\交易\project\email_alert_app

# 2. 使用Kivy官方Docker镜像打包
docker run --rm -v "%cd%":/app kivy/buildozer android debug

# 3. 等待完成，APK在 bin/ 目录
```

**首次运行会下载Docker镜像（约2GB）和Android SDK（约1.5GB），需要一些时间。**

---

## 💻 方案3：WSL (Windows Subsystem for Linux)

### 前提条件
- Windows 10/11
- 启用WSL 2

### 步骤

#### 1. 安装WSL

以管理员身份打开PowerShell：

```powershell
wsl --install -d Ubuntu
```

重启电脑。

#### 2. 启动Ubuntu，安装依赖

```bash
# 更新包管理器
sudo apt update
sudo apt upgrade -y

# 安装依赖
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# 安装buildozer
pip3 install --upgrade pip
pip3 install buildozer cython
```

#### 3. 复制文件到WSL

```bash
# 在WSL中创建目录
mkdir ~/email_alert_app
cd ~/email_alert_app

# 从Windows复制文件
cp /mnt/c/Users/27654/Desktop/交易/project/email_alert_app/main.py .
cp /mnt/c/Users/27654/Desktop/交易/project/email_alert_app/buildozer.spec .
```

#### 4. 构建APK

```bash
# 首次构建（会下载SDK/NDK，需要30分钟-1小时）
buildozer -v android debug

# APK生成位置
ls -lh bin/
```

#### 5. 复制APK到Windows

```bash
# 复制到Windows桌面
cp bin/*.apk /mnt/c/Users/27654/Desktop/
```

---

## ☁️ 方案4：在线服务（无需本地环境）

### 使用Google Colab

1. 访问 https://colab.research.google.com/
2. 新建笔记本
3. 上传 `main.py` 和 `buildozer.spec`
4. 运行以下代码单元：

```python
# 单元1：安装依赖
!sudo apt-get update
!sudo apt-get install -y git zip unzip openjdk-17-jdk wget libncurses5
!pip install buildozer cython

# 单元2：查看文件
!ls -la

# 单元3：构建APK（需要15-20分钟）
!buildozer -v android debug

# 单元4：下载APK
from google.colab import files
!ls -lh bin/
files.download('bin/emailalert-1.0-arm64-v8a-debug.apk')
```

---

## 🔧 常见问题

### Q1: buildozer首次运行很慢？

**正常**。首次会下载：
- Android SDK (~1.5GB)
- Android NDK (~1GB)
- Python-for-android (~500MB)

总计约3GB，根据网速需要30分钟到2小时。

**解决**：耐心等待，或使用国内镜像加速。

### Q2: 出现 "Command failed" 错误？

**常见原因**：
1. Java版本不对 - 确保使用OpenJDK 17
2. 权限不足 - 使用sudo
3. 磁盘空间不足 - 至少需要10GB空闲空间

**解决**：
```bash
# 检查Java版本
java -version

# 应该显示 openjdk version "17.x.x"
```

### Q3: APK安装后闪退？

**检查**：
1. Android版本是否 >= 5.0？
2. 是否允许安装未知来源？
3. 手机架构是否支持（ARM64或ARMv7）？

**调试**：
```bash
# 连接手机，查看日志
adb logcat | grep python
```

### Q4: GitHub Actions构建失败？

**常见原因**：
1. YAML文件缩进错误
2. 分支名称不对（master vs main）

**解决**：
- 检查YAML语法
- 查看Actions日志找具体错误

---

## 📊 方案对比

| 方案 | 难度 | 时间 | 环境要求 |
|------|------|------|----------|
| **GitHub Actions** | ⭐ 最简单 | 15-20分钟 | 只需GitHub账号 |
| **Docker** | ⭐⭐ 简单 | 首次1小时，后续10分钟 | 需要Docker |
| **WSL** | ⭐⭐⭐ 中等 | 首次1-2小时，后续10分钟 | Windows 10/11 |
| **Google Colab** | ⭐⭐ 简单 | 15-20分钟 | 只需Google账号 |
| **本地Linux** | ⭐⭐⭐⭐ 较难 | 首次2小时，后续5分钟 | Linux系统 |

**推荐顺序**：
1. GitHub Actions（最方便，自动化）
2. Google Colab（无需本地环境）
3. Docker（如果已安装）
4. WSL（Windows用户）

---

## ✅ 成功标志

打包成功后，你会得到：

```
bin/
└── emailalert-1.0-arm64-v8a-debug.apk  (约15-20MB)
```

这个APK可以直接安装到Android手机上！

---

## 🚀 快速开始（推荐路径）

### 使用GitHub Actions：

1. ✅ 在GitHub创建仓库
2. ✅ 上传 `main.py` 和 `buildozer.spec`
3. ✅ 创建 `.github/workflows/build.yml`
4. ✅ 触发工作流
5. ✅ 等待15分钟
6. ✅ 下载APK
7. ✅ 传到手机安装

**总耗时**：30分钟（包括GitHub注册和学习）

---

需要帮助？告诉我你选择哪个方案，我提供详细指导！
