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
        PowerManager = autoclass('android.os.PowerManager')
        AudioManager = autoclass('android.media.AudioManager')
        MediaPlayer = autoclass('android.media.MediaPlayer')
        AudioAttributes = autoclass('android.media.AudioAttributes')
        AudioAttributesBuilder = autoclass('android.media.AudioAttributes$Builder')

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
        self.media_player = None
        self.wake_lock = None
        self.audio_manager = None
        self.alert_active = False

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
            print("[Init] Vibrator obtained")

            # Get PowerManager and create STRONGEST WakeLock
            power_manager = context.getSystemService(Context.POWER_SERVICE)
            # Use FULL_WAKE_LOCK for maximum power - deprecated but most reliable
            try:
                from jnius import cast
                self.wake_lock = power_manager.newWakeLock(
                    PowerManager.SCREEN_BRIGHT_WAKE_LOCK | PowerManager.ACQUIRE_CAUSES_WAKEUP | PowerManager.ON_AFTER_RELEASE,
                    "EmailAlert::FullWakeLock"
                )
                print("[Init] FULL WakeLock created")
            except Exception as e:
                print(f"[Init] WakeLock error: {e}")

            # Get AudioManager and set volume to MAX
            self.audio_manager = context.getSystemService(Context.AUDIO_SERVICE)
            max_volume = self.audio_manager.getStreamMaxVolume(AudioManager.STREAM_ALARM)
            self.audio_manager.setStreamVolume(AudioManager.STREAM_ALARM, max_volume, 0)
            print(f"[Init] Alarm volume set to MAX: {max_volume}")

            # Initialize MediaPlayer with alarm.wav
            try:
                self.media_player = MediaPlayer()

                # Set AudioAttributes for ALARM stream
                audio_attrs = AudioAttributesBuilder() \
                    .setUsage(AudioAttributes.USAGE_ALARM) \
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION) \
                    .build()

                self.media_player.setAudioAttributes(audio_attrs)

                # Set data source to alarm.wav in app directory
                import os
                audio_file = os.path.join(os.path.dirname(__file__), 'alarm.wav')
                self.media_player.setDataSource(audio_file)
                self.media_player.prepare()
                self.media_player.setLooping(True)
                self.media_player.setVolume(1.0, 1.0)  # Max volume

                print(f"[Init] MediaPlayer ready with {audio_file}")
            except Exception as e:
                print(f"[Init] MediaPlayer error: {e}")
                self.media_player = None

            print("[Android] ===== ALL INITIALIZED SUCCESSFULLY =====")
        except Exception as e:
            print(f"[Android] Init FAILED: {e}")
            import traceback
            traceback.print_exc()

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
        print(f"\n{'='*50}")
        print(f"[Alert] ===== ALERT TRIGGERED: {title} =====")
        print(f"{'='*50}\n")

        if ANDROID_AVAILABLE:
            self.alert_active = True
            print(f"[Alert] alert_active set to True")

            # Acquire STRONGEST wake lock
            if self.wake_lock:
                try:
                    if not self.wake_lock.isHeld():
                        self.wake_lock.acquire(75000)  # 75 seconds
                        print("[Wake] ✓ WAKE LOCK ACQUIRED (75s)")
                    else:
                        print("[Wake] Wake lock already held")
                except Exception as e:
                    print(f"[Wake] ERROR: {e}")
            else:
                print("[Wake] ✗ Wake lock not available!")

            # Request audio focus (CRITICAL for vivo)
            if self.audio_manager:
                try:
                    result = self.audio_manager.requestAudioFocus(
                        None,
                        AudioManager.STREAM_ALARM,
                        AudioManager.AUDIOFOCUS_GAIN
                    )
                    print(f"[Audio] ✓ AUDIO FOCUS acquired (result={result})")
                except Exception as e:
                    print(f"[Audio] ✗ Focus failed: {e}")
            else:
                print("[Audio] ✗ AudioManager not available!")

            # Check MediaPlayer status
            if self.media_player:
                print(f"[Media] ✓ MediaPlayer available")
            else:
                print(f"[Media] ✗ MediaPlayer NOT available!")

            # Check Vibrator status
            if self.vibrator:
                print(f"[Vibrate] ✓ Vibrator available")
            else:
                print(f"[Vibrate] ✗ Vibrator NOT available!")

            print(f"\n[Alert] Starting vibration and sound threads...")

            # Vibrate for 70 seconds in background thread
            threading.Thread(target=self.vibrate_long, daemon=True, name="VibrateThread").start()

            # Play alarm sound for 70 seconds in background thread
            threading.Thread(target=self.play_alarm_long, daemon=True, name="SoundThread").start()

            print(f"[Alert] Both threads started!\n")
        else:
            print(f"[Desktop Alert] {title}: {message}")

    def vibrate_long(self):
        """Vibrate for 70 seconds - keep checking alert_active"""
        if not self.vibrator:
            return

        try:
            print("[Vibrate] Starting 70-second vibration")
            # Simple loop - more reliable on vivo
            for i in range(87):  # 87 cycles ≈ 70 seconds
                if not self.alert_active:
                    print("[Vibrate] Stopped by alert_active flag")
                    break
                try:
                    self.vibrator.vibrate(500)  # Vibrate for 500ms
                    time.sleep(0.8)  # Total cycle: 0.8s (500ms vibrate + 300ms pause)
                except Exception as e:
                    print(f"[Vibrate] Cycle error: {e}")
                    break
            print("[Vibrate] Completed")
        except Exception as e:
            print(f"[Vibrate Error] {e}")
        finally:
            self.alert_active = False

    def play_alarm_long(self):
        """Play alarm sound for 70 seconds using MediaPlayer"""
        if not self.media_player:
            print("[Sound] MediaPlayer not available!")
            return

        try:
            print("[Sound] ===== STARTING ALARM =====")

            # Start playing (already set to loop in init)
            self.media_player.start()
            print("[Sound] MediaPlayer.start() called - SHOULD BE PLAYING NOW")

            # Keep playing for 70 seconds
            for i in range(14):  # Check every 5 seconds, 14 times = 70 seconds
                time.sleep(5)
                is_playing = self.media_player.isPlaying()
                print(f"[Sound] Check {i+1}/14: isPlaying={is_playing}, alert_active={self.alert_active}")
                if not self.alert_active:
                    print("[Sound] alert_active is False, stopping")
                    break

            # Stop
            if self.media_player.isPlaying():
                self.media_player.pause()
                self.media_player.seekTo(0)  # Reset to beginning
            print("[Sound] ===== ALARM STOPPED =====")

        except Exception as e:
            print(f"[Sound ERROR] {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Release audio focus
            if self.audio_manager:
                try:
                    self.audio_manager.abandonAudioFocus(None)
                    print("[Audio] Focus released")
                except:
                    pass

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
