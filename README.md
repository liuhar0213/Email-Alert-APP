# 📱 Email Alert App - 独立Android应用

邮件监控提醒的独立Android App，支持锁屏响铃和振动。

## ✨ 功能特点

- ✅ **锁屏完美支持** - 后台运行，锁屏也能收到提醒
- ✅ **系统警报音** - 使用Android系统铃声，持续70秒
- ✅ **持续振动** - 70秒连续振动模式
- ✅ **系统通知** - 显示在通知栏，不会消失
- ✅ **实时连接** - SSE实时接收服务器推送
- ✅ **界面简洁** - 深色主题，一键连接
- ✅ **完全独立** - 不依赖任何第三方服务

---

## 📦 方案1：直接下载APK（最简单）

由于打包Android APK在Windows上比较复杂，我提供了更简单的方案：

### 使用在线打包服务（推荐）

1. **访问** https://www.python-for-android.org/ 或使用Google Colab
2. **上传** `main.py` 和 `buildozer.spec`
3. **点击构建** - 等待10-20分钟
4. **下载APK** 到手机安装

---

## 📦 方案2：在线Colab打包（免费）

### 步骤：

1. **打开Google Colab**
   - 访问 https://colab.research.google.com/

2. **新建笔记本，运行以下代码**：

```python
# 安装依赖
!pip install buildozer
!pip install cython

# 克隆仓库或上传文件
# 将 main.py 和 buildozer.spec 上传到Colab

# 安装Android SDK和NDK
!buildozer android debug

# 下载APK
from google.colab import files
files.download('bin/emailalert-1.0-arm64-v8a-debug.apk')
```

3. **等待构建完成**（约15-20分钟）

4. **下载APK**到手机

---

## 📦 方案3：本地Linux/WSL打包（高级）

### 在WSL (Ubuntu)中：

```bash
# 1. 安装依赖
sudo apt update
sudo apt install -y git zip unzip openjdk-17-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# 2. 安装buildozer
pip3 install buildozer cython

# 3. 复制App文件到WSL
# (将 C:\Users\27654\Desktop\交易\project\email_alert_app 复制到WSL)

# 4. 进入目录
cd ~/email_alert_app

# 5. 初始化buildozer（首次）
buildozer init

# 6. 构建APK
buildozer -v android debug

# 7. APK位置
# bin/emailalert-1.0-arm64-v8a-debug.apk
```

**注意**：首次构建需要下载Android SDK/NDK，可能需要30分钟-1小时。

---

## 📦 方案4：使用Docker打包（推荐给开发者）

```bash
# 运行buildozer Docker容器
docker run --rm -v "$(pwd)":/app kivy/buildozer android debug

# APK会生成在 bin/ 目录
```

---

## 📱 安装和使用

### 1. 安装APK

1. 将生成的APK传到手机
2. 允许"未知来源安装"
3. 点击APK安装

### 2. 设置权限

安装后，需要授予以下权限：
- ✅ 网络访问
- ✅ 振动
- ✅ 保持唤醒
- ✅ 通知

**重要**：允许后台运行

1. 手机设置 → 应用管理 → Email Alert
2. 电池 → 允许后台活动
3. 自启动 → 允许

### 3. 使用App

1. **打开App**
2. **输入服务器地址**
   - 格式：`http://10.0.0.170:8080`
   - 确保手机和电脑在同一WiFi
3. **点击"连接"**
4. **状态显示"已连接 ✓"**

### 4. 测试

1. 点击 **"测试提醒"** 按钮
2. 应该：
   - 播放系统警报音（70秒）
   - 持续振动（70秒）
   - 显示通知

### 5. 锁屏测试

1. 连接成功后
2. **锁定手机屏幕**
3. 在电脑上触发一个TradingView邮件提醒
4. 手机应该：
   - 屏幕亮起
   - 播放警报音
   - 持续振动
   - 显示通知

---

## ⚙️ 修改铃声

### 方法1：修改代码使用自定义铃声

编辑 `main.py` 第231行：

```python
# 使用通知铃声而不是警报铃声
alarm_uri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)

# 或使用自定义音频文件
# alarm_uri = Uri.parse("file:///sdcard/your_sound.mp3")
```

### 方法2：使用手机设置

1. 手机设置 → 声音和振动
2. 默认警报音 → 选择你喜欢的铃声
3. App会使用你设置的铃声

---

## 🔧 电脑端配置

### 确保email_watcher服务正常运行

```bash
cd C:\Users\27654\Desktop\交易\project\email_watcher
python email_watcher.py
```

应该看到：
```
[EmailWatcher] Started. Poll seconds = 5
[WebServer] Started on port 8080
[WebServer] Open http://10.0.0.170:8080 on your phone
```

---

## 🐛 故障排查

### 问题1：App连接失败

**检查**：
1. 手机和电脑是否在同一WiFi？
2. IP地址是否正确？
   - 在电脑上运行 `ipconfig`
   - 找到无线网卡的IPv4地址
3. 防火墙是否拦截了8080端口？
4. email_watcher程序是否正在运行？

**测试**：
手机浏览器访问 `http://10.0.0.170:8080`，如果能打开说明网络正常。

### 问题2：锁屏没有声音

**检查**：
1. App是否允许后台运行？
2. 手机是否开启勿扰模式？
3. 音量是否调到最大？（通知音量，不是媒体音量）
4. 是否允许App发送通知？

### 问题3：振动不工作

**检查**：
1. 手机是否开启振动？
2. 手机设置 → 声音和振动 → 振动强度
3. 某些省电模式会禁用振动

### 问题4：App被系统杀掉

**解决**：
- 小米：安全中心 → 授权管理 → 自启动管理 → Email Alert → 允许
- 华为：设置 → 应用 → 应用启动管理 → Email Alert → 手动管理 → 全部允许
- OPPO：设置 → 电池 → 应用耗电管理 → Email Alert → 允许后台运行
- vivo：设置 → 电池 → 后台高耗电 → Email Alert → 允许

---

## 📊 App与其他方案对比

| 方案 | 锁屏支持 | 自定义铃声 | 稳定性 | 安装难度 |
|------|---------|-----------|--------|---------|
| **独立App** | ✅ 完美 | ✅ 完全控制 | ✅ 最稳定 | ⚠️ 需要打包APK |
| 企业微信 | ✅ 完美 | ⚠️ 部分支持 | ✅ 稳定 | ✅ 简单 |
| 钉钉 | ✅ 完美 | ❌ 不支持 | ✅ 稳定 | ✅ 简单 |
| Web/PWA | ❌ 受限 | ❌ 不支持 | ⚠️ 易被杀 | ✅ 最简单 |

---

## 🎨 自定义App

### 修改界面颜色

编辑 `main.py` 第49行：

```python
Window.clearcolor = (0.1, 0.1, 0.15, 1)  # 深蓝色
# 改为其他颜色，例如：
Window.clearcolor = (0.1, 0.15, 0.1, 1)  # 深绿色
```

### 修改振动时长

编辑 `main.py` 第182行：

```python
pattern = [0, 500, 300] * 87  # 70秒
# 改为2分钟：
pattern = [0, 500, 300] * 150  # 120秒
```

### 修改铃声时长

编辑 `main.py` 第197行：

```python
end_time = time.time() + 70  # 70秒
# 改为2分钟：
end_time = time.time() + 120  # 120秒
```

---

## 📝 技术说明

- **框架**: Kivy (Python跨平台GUI框架)
- **打包工具**: Buildozer
- **Android API**: 21+ (Android 5.0+)
- **架构支持**: ARM64, ARMv7
- **网络协议**: SSE (Server-Sent Events)
- **权限**: 网络、振动、唤醒、通知

---

## 💡 未来改进

- [ ] 添加App图标和启动画面
- [ ] 支持多个服务器
- [ ] 历史记录本地存储
- [ ] 自定义铃声文件上传
- [ ] 铃声和振动强度调节
- [ ] 定时静音功能

---

## 📄 许可证

MIT License

---

## 🙋 需要帮助？

如果遇到任何问题：
1. 检查"故障排查"部分
2. 确认所有权限已授予
3. 查看App日志（如果可以）

---

**推荐方案排序**：
1. **最简单**：使用企业微信/钉钉（如果能用的话）
2. **最稳定**：独立App（需要打包APK）
3. **最快速**：Web/PWA（受限制）

如果你愿意花15-30分钟打包APK，独立App是最完美的解决方案！
