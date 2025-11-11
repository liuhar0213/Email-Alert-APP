[app]

title = Email Alert
package.name = emailalert
package.domain = com.emailmonitor
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,mp3
version = 2.0

requirements = python3,kivy,requests

android.permissions = INTERNET,VIBRATE,WAKE_LOCK,FOREGROUND_SERVICE,POST_NOTIFICATIONS,USE_FULL_SCREEN_INTENT,SCHEDULE_EXACT_ALARM
android.api = 29
android.minapi = 21
android.archs = arm64-v8a

orientation = portrait
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1
