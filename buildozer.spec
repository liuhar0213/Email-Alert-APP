[app]

title = Email Alert
package.name = emailalert
package.domain = com.emailmonitor
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,mp3,java
version = 4.0

requirements = python3,kivy,requests

android.permissions = INTERNET,ACCESS_NETWORK_STATE,VIBRATE,WAKE_LOCK,FOREGROUND_SERVICE,POST_NOTIFICATIONS,USE_FULL_SCREEN_INTENT,SCHEDULE_EXACT_ALARM,REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,RECEIVE_BOOT_COMPLETED
android.api = 29
android.minapi = 21
android.archs = arm64-v8a

# 个推 SDK Gradle 依赖
android.gradle_dependencies = com.getui:gtsdk:3.2.13.0,com.getui:gtc:3.1.10.0

# 个推 Maven 仓库
android.add_gradle_repositories = maven { url 'https://mvn.getui.com/nexus/content/repositories/releases/' }

# Java 源代码路径
android.add_src = src

# AndroidManifest.xml 配置 (个推元数据)
android.manifest.application_meta_data = com.igexin.sdk.appid:mQM6bHMbLlAQzfy53obHVB,com.igexin.sdk.appkey:tldyUidqkC9KDQQ1tZ9SK8,com.igexin.sdk.appsecret:hFE42eKXNN7rabpB9LKsH4

# 使用自定义 AndroidManifest.xml 模板 (在 templates/ 目录)
# p4a 会自动合并 templates/AndroidManifest.xml 中的 service 和 receiver 声明
p4a.bootstrap = sdl2

orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
