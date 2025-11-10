[app]

title = Email Alert
package.name = emailalert
package.domain = com.emailmonitor
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

# 简化依赖
requirements = python3,kivy,requests

# 基本权限
android.permissions = INTERNET,VIBRATE,WAKE_LOCK

# 降低API level以提高兼容性
android.api = 29
android.minapi = 21

# 只构建arm64（减少构建时间）
android.archs = arm64-v8a

# 屏幕方向
orientation = portrait
fullscreen = 0

# 使用默认entry point
android.entrypoint = org.kivy.android.PythonActivity

# 基本gradle依赖
android.gradle_dependencies = androidx.core:core:1.6.0

[buildozer]
log_level = 2
warn_on_root = 1
