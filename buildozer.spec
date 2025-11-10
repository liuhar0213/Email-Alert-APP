[app]

# App名称
title = Email Alert

# 包名（必须唯一）
package.name = emailalert

# 包域名
package.domain = com.emailmonitor

# 源代码目录
source.dir = .

# 源文件
source.include_exts = py,png,jpg,kv,atlas

# 版本号
version = 1.0

# 需要的Python包
requirements = python3,kivy,requests

# Android权限
android.permissions = INTERNET,VIBRATE,WAKE_LOCK,ACCESS_NETWORK_STATE,FOREGROUND_SERVICE,POST_NOTIFICATIONS

# Android API level
android.api = 31

# 最小API level
android.minapi = 21

# Android NDK版本
android.ndk = 25b

# 屏幕方向
orientation = portrait

# 全屏模式
fullscreen = 0

# Android arch
android.archs = arm64-v8a,armeabi-v7a

# App图标（如果有的话）
#icon.filename = %(source.dir)s/data/icon.png

# 启动画面
#presplash.filename = %(source.dir)s/data/presplash.png

# Android entry point
android.entrypoint = org.kivy.android.PythonActivity

# Android app theme
android.apptheme = "@android:style/Theme.NoTitleBar"

# 使用AndroidX
android.gradle_dependencies = androidx.core:core:1.6.0,androidx.appcompat:appcompat:1.3.1

# 允许备份
android.allow_backup = True

[buildozer]

# 日志级别
log_level = 2

# 警告错误
warn_on_root = 1
