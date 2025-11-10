# 🚀 GitHub Actions 一键打包APK

## 📋 准备工作

您需要：
- GitHub账号（免费注册：https://github.com/）
- 5分钟时间

---

## 🎯 完整步骤（30分钟）

### 第1步：创建GitHub仓库（2分钟）

1. **登录GitHub**
   - 访问 https://github.com/
   - 点击右上角头像 → Your repositories

2. **创建新仓库**
   - 点击绿色按钮 **"New"**
   - Repository name: `email-alert-app`
   - Description: `TradingView邮件监控Android App`
   - 选择 **Public**（免费用户必须选Public才能使用Actions）
   - ✅ 勾选 "Add a README file"
   - 点击 **"Create repository"**

---

### 第2步：上传代码（3分钟）

**方法A：网页上传（推荐，最简单）**

1. 在仓库页面，点击 **"Add file"** → **"Upload files"**

2. 将以下文件拖拽到上传区域：
   ```
   ✅ main.py
   ✅ buildozer.spec
   ✅ requirements.txt
   ✅ .gitignore
   ```

3. 在 "Commit changes" 框中：
   - 标题：`初始化项目文件`
   - 点击 **"Commit changes"**

4. 再次点击 **"Add file"** → **"Create new file"**

5. 文件名输入：`.github/workflows/build.yml`

6. 复制粘贴以下内容到编辑器：

```yaml
name: Build Android APK

on:
  push:
    branches: [ master, main ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout code
      uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'

    - name: Install system dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y \
          git zip unzip openjdk-17-jdk wget \
          libncurses5 libssl-dev autoconf libtool \
          pkg-config zlib1g-dev libffi-dev

    - name: Install Python dependencies
      run: |
        pip install --upgrade pip
        pip install buildozer cython==0.29.33

    - name: Build APK with Buildozer
      run: |
        buildozer -v android debug

    - name: Upload APK
      uses: actions/upload-artifact@v3
      with:
        name: email-alert-apk
        path: bin/*.apk
        if-no-files-found: error

    - name: Display build info
      run: |
        echo "✅ APK构建完成！"
        ls -lh bin/
```

7. 提交：标题 `添加GitHub Actions构建脚本`，点击 **"Commit changes"**

---

**方法B：使用Git命令（适合熟悉Git的用户）**

```bash
# 1. 进入项目目录
cd C:\Users\27654\Desktop\交易\project\email_alert_app

# 2. 初始化Git
git init

# 3. 添加所有文件
git add .

# 4. 提交
git commit -m "初始化项目"

# 5. 关联远程仓库（替换成你的用户名）
git remote add origin https://github.com/你的用户名/email-alert-app.git

# 6. 推送
git branch -M main
git push -u origin main
```

---

### 第3步：启动自动构建（1分钟）

1. 在GitHub仓库页面，点击顶部 **"Actions"** 标签

2. 如果看到提示 "Workflows found in this repository"：
   - 点击 **"I understand my workflows, go ahead and enable them"**

3. 左侧应该显示 **"Build Android APK"**

4. 点击右侧 **"Run workflow"** 下拉按钮
   - 选择分支：`main`
   - 点击绿色按钮 **"Run workflow"**

5. 页面会刷新，显示一个黄色圆圈 🟡（构建中）

---

### 第4步：等待构建完成（15-20分钟）

1. 点击正在运行的构建记录（标题是您的commit信息）

2. 查看构建进度：
   - 展开各个步骤查看日志
   - **"Build APK with Buildozer"** 是最耗时的步骤

3. 等待所有步骤变成绿色 ✅

4. 构建完成的标志：
   - 顶部显示绿色勾号 ✅
   - 时间约15-25分钟

---

### 第5步：下载APK（1分钟）

1. 构建完成后，页面向下滚动到 **"Artifacts"** 部分

2. 看到：
   ```
   📦 email-alert-apk
   ```

3. 点击名称下载ZIP文件

4. 解压ZIP，得到APK文件：
   ```
   emailalert-1.0-arm64-v8a-debug.apk
   ```

5. 文件大小约 **15-20MB**

---

## 📱 安装APK到手机

### 方法1：微信/QQ传输

1. 在电脑上，将APK文件通过微信或QQ发送给自己
2. 在手机上接收文件
3. 点击文件，选择"用其他应用打开" → "安装"
4. 允许"未知来源安装"
5. 完成安装

### 方法2：数据线传输

1. 用USB数据线连接手机和电脑
2. 将APK复制到手机存储
3. 在手机上用文件管理器找到APK
4. 点击安装

---

## ✅ 安装后配置

### 1. 授予权限

首次打开App时，允许以下权限：
- ✅ 网络访问
- ✅ 振动
- ✅ 通知

### 2. 允许后台运行（重要！）

不同手机设置方法：

**小米手机：**
1. 安全中心 → 授权管理 → 自启动管理
2. 找到 "Email Alert" → 开启

**华为手机：**
1. 设置 → 应用 → 应用启动管理
2. 找到 "Email Alert" → 手动管理
3. 允许自启动、允许关联启动、允许后台活动

**OPPO手机：**
1. 设置 → 电池 → 应用耗电管理
2. 找到 "Email Alert" → 允许后台运行

**vivo手机：**
1. 设置 → 电池 → 后台高耗电
2. 找到 "Email Alert" → 允许

**通用设置：**
- 设置 → 应用管理 → Email Alert
- 电池 → 不限制后台活动
- 通知 → 允许

### 3. 连接服务器

1. **确保电脑端邮件监控服务正在运行**：
   ```bash
   cd C:\Users\27654\Desktop\交易\project\email_watcher
   python email_watcher.py
   ```

2. **在App中输入服务器地址**：
   - 格式：`http://10.0.0.170:8080`
   - 确保手机和电脑在同一WiFi

3. **点击"连接"按钮**
   - 状态应显示：`已连接 ✓`

### 4. 测试

1. 点击"测试提醒"按钮
2. 应该：
   - 🔊 播放警报音（70秒）
   - 📳 持续振动（70秒）
   - 📲 显示系统通知

---

## 🔧 故障排查

### 问题1：构建失败

**检查**：
- Actions日志中的错误信息
- 是否是Public仓库（Private需要付费）
- YAML文件格式是否正确

**解决**：
- 查看具体错误步骤
- 修改代码后重新提交会自动触发构建

### 问题2：下载的ZIP中没有APK

**原因**：构建失败了

**解决**：
- 查看Actions日志
- 找到红色 ❌ 的步骤
- 根据错误信息修复

### 问题3：APK安装失败

**检查**：
- Android版本是否 >= 5.0
- 是否允许安装未知来源
- 手机架构（ARM64或ARMv7）

**解决**：
- 更新Android系统
- 开启"允许安装未知来源"

### 问题4：连接服务器失败

**检查**：
1. 手机和电脑在同一WiFi？
2. 电脑IP地址正确？（`ipconfig`查看）
3. 电脑防火墙关闭？
4. email_watcher程序运行中？

**测试**：
- 手机浏览器访问 `http://10.0.0.170:8080`
- 能打开说明网络正常

### 问题5：锁屏没声音

**检查**：
1. 后台运行权限是否开启？
2. 勿扰模式是否关闭？
3. 通知音量是否足够？
4. 电池优化是否关闭？

---

## 🎉 完成！

现在您有了一个**完全独立的Android App**，可以：

- ✅ 锁屏完美支持
- ✅ 70秒连续警报音
- ✅ 70秒连续振动
- ✅ 系统通知
- ✅ 后台稳定运行

**下次需要重新打包**（修改代码后）：
1. 上传修改的文件到GitHub
2. Actions会自动触发构建
3. 或手动运行workflow

---

## 📞 需要帮助？

如果遇到问题：
1. 检查本文档的"故障排查"部分
2. 查看GitHub Actions构建日志
3. 确认所有权限已授予

---

**预计总耗时**：30-40分钟
**难度等级**：⭐⭐ (简单-中等)
**推荐指数**：⭐⭐⭐⭐⭐ (最完美的方案)
