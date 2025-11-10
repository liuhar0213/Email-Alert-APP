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
from kivy.core.window import Window

import requests
import json
import threading
import time
from datetime import datetime

# Android specific imports
if platform == 'android':
    try:
        from android.permissions import request_permissions, Permission
        from jnius import autoclass

        # Request basic permissions only
        request_permissions([
            Permission.INTERNET,
            Permission.VIBRATE,
            Permission.WAKE_LOCK
        ])

        # Android classes
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        Vibrator = autoclass('android.os.Vibrator')
        RingtoneManager = autoclass('android.media.RingtoneManager')
        PowerManager = autoclass('android.os.PowerManager')

        ANDROID_AVAILABLE = True
    except Exception as e:
        print(f"[Android] Import failed: {e}")
        ANDROID_AVAILABLE = False
else:
    ANDROID_AVAILABLE = False


class EmailAlertApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.server_url = ""
        self.connected = False
        self.alert_count = 0
        self.running = False
        self.vibrator = None
        self.ringtone = None
        self.wake_lock = None

    def build(self):
        """Build the UI"""
        Window.clearcolor = (0.1, 0.1, 0.15, 1)

        # Main layout
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        # Title
        title = Label(
            text='Email Monitor',
            font_size='28sp',
            size_hint_y=0.1,
            bold=True,
            color=(1, 1, 1, 1)
        )
        layout.add_widget(title)

        # Status
        self.status_label = Label(
            text='Disconnected',
            font_size='18sp',
            size_hint_y=0.08,
            color=(1, 0.5, 0, 1)
        )
        layout.add_widget(self.status_label)

        # Server URL input
        url_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10)
        url_layout.add_widget(Label(text='Server:', size_hint_x=0.25, color=(1, 1, 1, 1)))
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
            text='Connect',
            background_color=(0.2, 0.6, 0.2, 1),
            background_normal=''
        )
        self.connect_btn.bind(on_press=self.toggle_connection)
        btn_layout.add_widget(self.connect_btn)

        test_btn = Button(
            text='Test Alert',
            background_color=(0.6, 0.4, 0, 1),
            background_normal=''
        )
        test_btn.bind(on_press=self.test_alert)
        btn_layout.add_widget(test_btn)

        layout.add_widget(btn_layout)

        # Alert count
        self.count_label = Label(
            text='Alerts: 0',
            font_size='20sp',
            size_hint_y=0.08,
            color=(1, 1, 1, 1)
        )
        layout.add_widget(self.count_label)

        # Alert log
        log_label = Label(
            text='Alert Log:',
            font_size='16sp',
            size_hint_y=0.06,
            color=(0.8, 0.8, 0.8, 1)
        )
        layout.add_widget(log_label)

        scroll = ScrollView(size_hint_y=0.46)
        self.log_label = Label(
            text='No alerts yet',
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
        if ANDROID_AVAILABLE:
            self.init_android()

        return layout

    def init_android(self):
        """Initialize Android specific components"""
        try:
            activity = PythonActivity.mActivity
            context = activity.getApplicationContext()

            # Get Vibrator
            self.vibrator = context.getSystemService(Context.VIBRATOR_SERVICE)

            # Get default alarm ringtone
            alarm_uri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
            self.ringtone = RingtoneManager.getRingtone(activity, alarm_uri)

            # Get PowerManager and create WakeLock
            power_manager = context.getSystemService(Context.POWER_SERVICE)
            self.wake_lock = power_manager.newWakeLock(
                PowerManager.PARTIAL_WAKE_LOCK,
                "EmailAlert::AlertWakeLock"
            )

            print("[Android] Initialized successfully")
        except Exception as e:
            print(f"[Android] Init failed: {e}")

    def toggle_connection(self, instance):
        """Toggle connection to server"""
        if not self.connected:
            self.server_url = self.url_input.text.strip()
            if not self.server_url:
                self.update_status("Please enter server URL", (1, 0, 0, 1))
                return

            self.running = True
            self.connected = True
            self.connect_btn.text = 'Disconnect'
            self.connect_btn.background_color = (0.8, 0.2, 0.2, 1)
            self.update_status("Connecting...", (1, 0.8, 0, 1))

            # Start monitoring thread
            thread = threading.Thread(target=self.monitor_loop, daemon=True)
            thread.start()
        else:
            self.running = False
            self.connected = False
            self.connect_btn.text = 'Connect'
            self.connect_btn.background_color = (0.2, 0.6, 0.2, 1)
            self.update_status("Disconnected", (1, 0.5, 0, 1))

    def monitor_loop(self):
        """Monitor server for alerts using SSE"""
        try:
            url = f"{self.server_url}/events"

            # Use SSE to receive real-time alerts
            response = requests.get(url, stream=True, timeout=30)

            if response.status_code == 200:
                Clock.schedule_once(lambda dt: self.update_status("Connected", (0, 1, 0, 1)))

                for line in response.iter_lines():
                    if not self.running:
                        break

                    if line:
                        line = line.decode('utf-8')

                        # Parse SSE event
                        if line.startswith('data: '):
                            try:
                                data = json.loads(line[6:])
                                Clock.schedule_once(lambda dt, d=data: self.handle_alert(d))
                            except:
                                pass
            else:
                Clock.schedule_once(lambda dt: self.update_status(f"Failed: {response.status_code}", (1, 0, 0, 1)))

        except requests.exceptions.Timeout:
            Clock.schedule_once(lambda dt: self.update_status("Timeout", (1, 0, 0, 1)))
        except requests.exceptions.ConnectionError:
            Clock.schedule_once(lambda dt: self.update_status("Cannot connect", (1, 0, 0, 1)))
        except Exception as e:
            Clock.schedule_once(lambda dt: self.update_status(f"Error: {str(e)}", (1, 0, 0, 1)))
        finally:
            if self.connected:
                self.connected = False
                Clock.schedule_once(lambda dt: self.reset_connection())

    def handle_alert(self, data):
        """Handle incoming alert"""
        self.alert_count += 1
        self.count_label.text = f'Alerts: {self.alert_count}'

        subject = data.get('subject', 'Unknown')
        sender = data.get('from', 'Unknown')

        # Add to log
        log_entry = f"\n[{datetime.now().strftime('%H:%M:%S')}]\n{subject}\n{sender}\n"
        current_log = self.log_label.text
        if current_log == 'No alerts yet':
            self.log_label.text = log_entry
        else:
            self.log_label.text = log_entry + current_log

        # Trigger alert
        self.trigger_alert(subject, sender)

    def trigger_alert(self, title, message):
        """Trigger sound and vibration"""
        print(f"[Alert] {title}")

        if ANDROID_AVAILABLE:
            # Acquire wake lock to keep device awake during alert
            if self.wake_lock and not self.wake_lock.isHeld():
                self.wake_lock.acquire(75000)  # 75 seconds (70s alert + 5s buffer)
                print("[Wake] Lock acquired")

            # Vibrate for 70 seconds in background thread
            threading.Thread(target=self.vibrate_long, daemon=True).start()

            # Play alarm sound for 70 seconds in background thread
            threading.Thread(target=self.play_alarm_long, daemon=True).start()
        else:
            print(f"[Desktop Alert] {title}: {message}")

    def vibrate_long(self):
        """Vibrate for 70 seconds"""
        if not self.vibrator:
            return

        try:
            # Vibrate pattern: 500ms on, 300ms off, repeat for 70 seconds
            pattern = [0, 500, 300] * 87  # 87 cycles ≈ 70 seconds
            if hasattr(self.vibrator, 'vibrate'):
                # Try new API (array)
                try:
                    from jnius import cast
                    from array import array
                    long_array = array('l', pattern)
                    self.vibrator.vibrate(long_array, -1)
                except:
                    # Fallback: simple vibration
                    for _ in range(87):
                        if not self.running:
                            break
                        try:
                            self.vibrator.vibrate(500)
                            time.sleep(0.8)
                        except:
                            break
        except Exception as e:
            print(f"[Vibrate Error] {e}")

    def play_alarm_long(self):
        """Play alarm sound for 70 seconds"""
        if not self.ringtone:
            return

        try:
            # Play for 70 seconds
            end_time = time.time() + 70
            while time.time() < end_time and self.running:
                if hasattr(self.ringtone, 'play'):
                    self.ringtone.play()
                time.sleep(5)  # Ringtone duration

            if hasattr(self.ringtone, 'stop'):
                self.ringtone.stop()
        except Exception as e:
            print(f"[Sound Error] {e}")

    def test_alert(self, instance):
        """Test alert functionality"""
        self.trigger_alert("Test Alert", "This is a test")
        self.alert_count += 1
        self.count_label.text = f'Alerts: {self.alert_count}'

        log_entry = f"\n[{datetime.now().strftime('%H:%M:%S')}]\nTest Alert\nSystem Test\n"
        if self.log_label.text == 'No alerts yet':
            self.log_label.text = log_entry
        else:
            self.log_label.text = log_entry + self.log_label.text

    def update_status(self, text, color):
        """Update status label"""
        self.status_label.text = text
        self.status_label.color = color

    def reset_connection(self):
        """Reset connection UI"""
        self.connect_btn.text = 'Connect'
        self.connect_btn.background_color = (0.2, 0.6, 0.2, 1)
        self.connected = False


if __name__ == '__main__':
    EmailAlertApp().run()
