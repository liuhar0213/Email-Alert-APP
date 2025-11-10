#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Alert App - Android版
独立运行的邮件提醒App，支持锁屏响铃和振动
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.utils import platform
from kivy.core.audio import SoundLoader
from kivy.core.window import Window

import requests
import json
import threading
import time
from datetime import datetime

# Android specific imports
if platform == 'android':
    from android.permissions import request_permissions, Permission
    from jnius import autoclass, cast

    # Android classes
    PythonActivity = autoclass('org.kivy.android.PythonActivity')
    Context = autoclass('android.content.Context')
    NotificationManager = autoclass('android.app.NotificationManager')
    NotificationCompat = autoclass('androidx.core.app.NotificationCompat')
    NotificationChannel = autoclass('android.app.NotificationChannel')
    PendingIntent = autoclass('android.app.PendingIntent')
    Intent = autoclass('android.content.Intent')
    Vibrator = autoclass('android.os.Vibrator')
    AudioManager = autoclass('android.media.AudioManager')
    RingtoneManager = autoclass('android.media.RingtoneManager')
    Uri = autoclass('android.net.Uri')

    # Request necessary permissions
    request_permissions([
        Permission.VIBRATE,
        Permission.WAKE_LOCK,
        Permission.INTERNET,
        Permission.ACCESS_NETWORK_STATE,
        Permission.FOREGROUND_SERVICE
    ])


class EmailAlertApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.server_url = ""
        self.connected = False
        self.alert_count = 0
        self.running = False
        self.vibrator = None
        self.notification_manager = None
        self.alarm_sound = None

    def build(self):
        """Build the UI"""
        Window.clearcolor = (0.1, 0.1, 0.15, 1)

        # Main layout
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Title
        title = Label(
            text='📧 邮件监控',
            font_size='28sp',
            size_hint_y=0.1,
            bold=True,
            color=(1, 1, 1, 1)
        )
        layout.add_widget(title)

        # Status
        self.status_label = Label(
            text='未连接',
            font_size='18sp',
            size_hint_y=0.08,
            color=(1, 0.5, 0, 1)
        )
        layout.add_widget(self.status_label)

        # Server URL input
        url_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10)
        url_layout.add_widget(Label(text='服务器:', size_hint_x=0.25, color=(1, 1, 1, 1)))
        self.url_input = TextInput(
            text='http://10.0.0.170:8080',
            multiline=False,
            size_hint_x=0.75
        )
        url_layout.add_widget(self.url_input)
        layout.add_widget(url_layout)

        # Buttons
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=0.12, spacing=10)

        self.connect_btn = Button(
            text='连接',
            background_color=(0.2, 0.6, 0.2, 1),
            background_normal=''
        )
        self.connect_btn.bind(on_press=self.toggle_connection)
        btn_layout.add_widget(self.connect_btn)

        test_btn = Button(
            text='测试提醒',
            background_color=(0.6, 0.4, 0, 1),
            background_normal=''
        )
        test_btn.bind(on_press=self.test_alert)
        btn_layout.add_widget(test_btn)

        layout.add_widget(btn_layout)

        # Alert count
        self.count_label = Label(
            text='提醒次数: 0',
            font_size='20sp',
            size_hint_y=0.08,
            color=(1, 1, 1, 1)
        )
        layout.add_widget(self.count_label)

        # Alert log
        log_label = Label(
            text='提醒记录:',
            font_size='16sp',
            size_hint_y=0.06,
            color=(0.8, 0.8, 0.8, 1)
        )
        layout.add_widget(log_label)

        scroll = ScrollView(size_hint_y=0.46)
        self.log_label = Label(
            text='暂无记录',
            font_size='14sp',
            size_hint_y=None,
            color=(0.7, 0.7, 0.7, 1),
            text_size=(Window.width - 60, None),
            halign='left',
            valign='top'
        )
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        scroll.add_widget(self.log_label)
        layout.add_widget(scroll)

        # Initialize Android components
        if platform == 'android':
            self.init_android()

        return layout

    def init_android(self):
        """Initialize Android specific components"""
        try:
            activity = PythonActivity.mActivity
            context = activity.getApplicationContext()

            # Get Vibrator
            self.vibrator = cast(Vibrator, context.getSystemService(Context.VIBRATOR_SERVICE))

            # Get NotificationManager
            self.notification_manager = cast(NotificationManager,
                context.getSystemService(Context.NOTIFICATION_SERVICE))

            # Create notification channel (Android 8.0+)
            channel_id = "email_alerts"
            channel = NotificationChannel(
                channel_id,
                "邮件提醒",
                NotificationManager.IMPORTANCE_HIGH
            )
            channel.setDescription("TradingView邮件警报通知")
            channel.enableVibration(True)
            channel.setVibrationPattern([0, 500, 200, 500, 200, 500])

            if self.notification_manager:
                self.notification_manager.createNotificationChannel(channel)

            print("[Android] 初始化完成")
        except Exception as e:
            print(f"[Android] 初始化失败: {e}")

    def toggle_connection(self, instance):
        """Toggle connection to server"""
        if not self.connected:
            self.server_url = self.url_input.text.strip()
            if not self.server_url:
                self.update_status("请输入服务器地址", (1, 0, 0, 1))
                return

            self.running = True
            self.connected = True
            self.connect_btn.text = '断开'
            self.connect_btn.background_color = (0.8, 0.2, 0.2, 1)
            self.update_status("正在连接...", (1, 0.8, 0, 1))

            # Start monitoring thread
            thread = threading.Thread(target=self.monitor_loop, daemon=True)
            thread.start()
        else:
            self.running = False
            self.connected = False
            self.connect_btn.text = '连接'
            self.connect_btn.background_color = (0.2, 0.6, 0.2, 1)
            self.update_status("已断开", (1, 0.5, 0, 1))

    def monitor_loop(self):
        """Monitor server for alerts using SSE"""
        try:
            url = f"{self.server_url}/events"

            # Use SSE to receive real-time alerts
            response = requests.get(url, stream=True, timeout=10)

            if response.status_code == 200:
                Clock.schedule_once(lambda dt: self.update_status("已连接 ✓", (0, 1, 0, 1)))

                for line in response.iter_lines():
                    if not self.running:
                        break

                    if line:
                        line = line.decode('utf-8')

                        # Parse SSE event
                        if line.startswith('event: alert'):
                            # Next line should be data
                            continue
                        elif line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                Clock.schedule_once(lambda dt, d=data: self.handle_alert(d))
                            except:
                                pass
            else:
                Clock.schedule_once(lambda dt: self.update_status(f"连接失败: {response.status_code}", (1, 0, 0, 1)))

        except requests.exceptions.Timeout:
            Clock.schedule_once(lambda dt: self.update_status("连接超时", (1, 0, 0, 1)))
        except requests.exceptions.ConnectionError:
            Clock.schedule_once(lambda dt: self.update_status("无法连接到服务器", (1, 0, 0, 1)))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_status(f"错误: {str(e)}", (1, 0, 0, 1)))
        finally:
            if self.connected:
                self.connected = False
                Clock.schedule_once(lambda dt: self.reset_connection())

    def handle_alert(self, data):
        """Handle incoming alert"""
        self.alert_count += 1
        self.count_label.text = f'提醒次数: {self.alert_count}'

        subject = data.get('subject', '未知主题')
        sender = data.get('from', '未知发件人')
        timestamp = data.get('timestamp', '')

        # Add to log
        log_entry = f"\n[{datetime.now().strftime('%H:%M:%S')}]\n{subject}\n{sender}\n"
        current_log = self.log_label.text
        if current_log == '暂无记录':
            self.log_label.text = log_entry
        else:
            self.log_label.text = log_entry + current_log

        # Trigger alert
        self.trigger_alert(subject, sender)

    def trigger_alert(self, title, message):
        """Trigger sound, vibration and notification"""
        print(f"[Alert] {title}")

        if platform == 'android':
            # Vibrate for 70 seconds
            threading.Thread(target=self.vibrate_long, daemon=True).start()

            # Play alarm sound for 70 seconds
            threading.Thread(target=self.play_alarm_long, daemon=True).start()

            # Show notification
            self.show_notification(title, message)
        else:
            # Desktop: just print
            print(f"[Desktop Alert] {title}: {message}")

    def vibrate_long(self):
        """Vibrate for 70 seconds"""
        if not self.vibrator:
            return

        try:
            # Vibrate pattern: 500ms on, 300ms off, repeat for 70 seconds
            pattern = [0, 500, 300] * 87  # 87 cycles ≈ 70 seconds
            self.vibrator.vibrate(pattern, -1)  # -1 means don't repeat
        except Exception as e:
            print(f"[Vibrate Error] {e}")

    def play_alarm_long(self):
        """Play alarm sound for 70 seconds"""
        try:
            if platform == 'android':
                # Use system alarm sound
                activity = PythonActivity.mActivity
                alarm_uri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
                ringtone = RingtoneManager.getRingtone(activity, alarm_uri)

                # Play for 70 seconds
                end_time = time.time() + 70
                while time.time() < end_time and self.running:
                    ringtone.play()
                    time.sleep(5)  # Ringtone duration

                ringtone.stop()
        except Exception as e:
            print(f"[Sound Error] {e}")

    def show_notification(self, title, message):
        """Show Android notification"""
        if not self.notification_manager:
            return

        try:
            activity = PythonActivity.mActivity

            # Create intent
            intent = Intent(activity, PythonActivity)
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK)

            pending_intent = PendingIntent.getActivity(
                activity, 0, intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
            )

            # Build notification
            builder = NotificationCompat.Builder(activity, "email_alerts")
            builder.setContentTitle("📧 " + title)
            builder.setContentText(message)
            builder.setSmallIcon(activity.getApplicationInfo().icon)
            builder.setPriority(NotificationCompat.PRIORITY_HIGH)
            builder.setCategory(NotificationCompat.CATEGORY_ALARM)
            builder.setVibrate([0, 500, 200, 500, 200, 500])
            builder.setAutoCancel(False)
            builder.setOngoing(True)
            builder.setContentIntent(pending_intent)

            notification = builder.build()
            self.notification_manager.notify(self.alert_count, notification)

        except Exception as e:
            print(f"[Notification Error] {e}")

    def test_alert(self, instance):
        """Test alert functionality"""
        self.trigger_alert("测试提醒", "这是一条测试邮件")
        self.alert_count += 1
        self.count_label.text = f'提醒次数: {self.alert_count}'

        log_entry = f"\n[{datetime.now().strftime('%H:%M:%S')}]\n测试提醒\n系统测试\n"
        if self.log_label.text == '暂无记录':
            self.log_label.text = log_entry
        else:
            self.log_label.text = log_entry + self.log_label.text

    def update_status(self, text, color):
        """Update status label"""
        self.status_label.text = text
        self.status_label.color = color

    def reset_connection(self):
        """Reset connection UI"""
        self.connect_btn.text = '连接'
        self.connect_btn.background_color = (0.2, 0.6, 0.2, 1)
        self.connected = False


if __name__ == '__main__':
    EmailAlertApp().run()
