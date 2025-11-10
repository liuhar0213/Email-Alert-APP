# 📧 Email Alert - TradingView邮件监控Android App

> 独立Android应用，实现TradingView邮件警报的锁屏提醒（铃声+振动）

---

## ✨ 核心功能

- ✅ **锁屏完美支持** - 后台运行，锁屏也能收到提醒
- ✅ **70秒连续警报** - 系统铃声 + 持续振动
- ✅ **系统通知** - 通知栏显示，不会消失
- ✅ **实时连接** - SSE实时接收服务器推送
- ✅ **完全独立** - 不依赖任何第三方推送服务

---

## 🚀 快速开始

### 方案1：GitHub Actions自动打包（推荐）

**总耗时**：30分钟 | **难度**：⭐⭐

详见：**[GitHub打包步骤.md](GitHub打包步骤.md)**

**简要步骤**：
1. 创建GitHub仓库
2. 上传代码文件
3. 触发自动构建
4. 下载APK安装

---

### 方案2：在线Colab打包

**总耗时**：20分钟 | **难度**：⭐⭐

详见：**[打包APK教程.md](打包APK教程.md)** - "方案4：在线服务"

---

### 方案3：本地打包（高级）

使用Docker或WSL进行本地构建

详见：**[打包APK教程.md](打包APK教程.md)** - 方案2和方案3

---

## 📁 项目文件

```
email_alert_app/
├── main.py                 # ⭐ App主程序（Kivy框架）
├── buildozer.spec          # ⭐ APK打包配置
├── requirements.txt        # Python依赖
├── .gitignore             # Git忽略文件
├── .github/
│   └── workflows/
│       └── build.yml       # ⭐ GitHub Actions自动构建脚本
├── README.md              # 完整技术文档
├── 项目README.md          # 本文件（项目概览）
├── GitHub打包步骤.md      # ⭐ 详细操作指南（推荐阅读）
├── 打包APK教程.md         # 多种打包方案
└── 快速开始.md            # 30分钟上手指南
```

**标注⭐的文件需要上传到GitHub仓库**

---

## 📱 使用流程

### 1. 打包APK
选择上述任一方案打包APK（推荐GitHub Actions）

### 2. 安装到手机
- 通过微信/QQ传输，或使用数据线复制
- 允许"未知来源安装"
- 授予所有权限

### 3. 配置后台运行
- 设置 → 应用 → Email Alert
- 电池 → 不限制后台活动
- 自启动 → 允许

### 4. 连接服务器
- 启动电脑端：`python email_watcher.py`
- App输入：`http://10.0.0.170:8080`
- 点击"连接"

### 5. 测试
- 点击"测试提醒"
- 确认声音和振动正常
- 锁屏测试

---

## 🎯 与其他方案对比

| 方案 | 锁屏 | 自定义 | 稳定性 | 难度 |
|------|------|--------|--------|------|
| **独立App** | ✅ 完美 | ✅ 完全控制 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 企业微信 | ✅ 完美 | ⚠️ 部分 | ⭐⭐⭐⭐ | ⭐ |
| Web/PWA | ❌ 受限 | ⚠️ 有限 | ⭐⭐ | ⭐ |

---

## 🔧 技术栈

- **框架**: Kivy (Python跨平台GUI)
- **打包**: Buildozer + GitHub Actions
- **协议**: SSE (Server-Sent Events)
- **Android API**: 21+ (Android 5.0+)
- **架构**: ARM64-v8a, ARMv7a

---

## 📞 故障排查

### 连接失败
- 检查手机和电脑是否同一WiFi
- 验证IP地址（电脑运行`ipconfig`）
- 关闭防火墙
- 确认email_watcher服务运行中

### 锁屏无声音
- 开启后台运行权限
- 关闭勿扰模式
- 调高通知音量
- 检查电池优化设置

### App被杀掉
- 小米：安全中心 → 自启动管理
- 华为：应用启动管理 → 手动管理
- OPPO：应用耗电管理 → 允许后台
- vivo：后台高耗电 → 允许

---

## 📊 配套项目

本App需要配合电脑端邮件监控服务使用：

**位置**：`C:\Users\27654\Desktop\交易\project\email_watcher\`

**启动**：
```bash
cd C:\Users\27654\Desktop\交易\project\email_watcher
python email_watcher.py
```

---

## 🎉 开始使用

**推荐路径**：

1. 阅读 **[GitHub打包步骤.md](GitHub打包步骤.md)**
2. 创建GitHub仓库并上传代码
3. 等待自动构建完成（15-20分钟）
4. 下载APK安装到手机
5. 完成配置并测试

**预计总时间**：30-40分钟
**难度等级**：⭐⭐ (简单-中等)

---

## 📄 许可证

MIT License

---

**祝您使用愉快！再也不会错过TradingView的重要警报了！** 🚀
