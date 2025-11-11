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

        # Request all needed permissions
        request_permissions([
            Permission.INTERNET,
            Permission.VIBRATE,
            Permission.WAKE_LOCK,
            Permission.FOREGROUND_SERVICE
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
        NotificationChannel = autoclass('android.app.NotificationChannel')
        NotificationManager = autoclass('android.app.NotificationManager')
        Notification = autoclass('android.app.Notification')
        NotificationBuilder = autoclass('android.app.Notification$Builder')
        PendingIntent = autoclass('android.app.PendingIntent')
        Intent = autoclass('android.content.Intent')
        Service = autoclass('android.app.Service')

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

        # Configuration
        self.alert_duration = 70  # seconds
        self.custom_ringtone_path = None

        # Foreground service
        self.notification_id = 1
        self.foreground_running = False

        # Thread tracking for auto-restart
        self.sse_thread = None
        self.poll_thread = None
        self.watchdog_event = None

    def build(self):
        """Build the UI"""
        Window.clearcolor = (0.1, 0.1, 0.15, 1)

        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Title
        title = Label(
            text='Email Monitor',
            font_size='24sp',
            size_hint_y=0.08,
            bold=True,
            color=(1, 1, 1, 1)
        )
        main_layout.add_widget(title)

        # Create scrollable content area
        scroll = ScrollView(size_hint_y=0.92)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=15, size_hint_y=None)
        layout.bind(minimum_height=layout.setter('height'))
        scroll.add_widget(layout)

        # Status
        self.status_label = Label(
            text='Disconnected',
            font_size='20sp',
            size_hint_y=None,
            height=45,
            color=(1, 0.5, 0, 1)
        )
        layout.add_widget(self.status_label)

        # Server URL input
        url_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=55, spacing=10)
        url_layout.add_widget(Label(text='Server:', size_hint_x=0.25, color=(1, 1, 1, 1)))
        self.url_input = TextInput(
            text='http://10.0.0.170:8080',
            multiline=False,
            size_hint_x=0.75
        )
        url_layout.add_widget(self.url_input)
        layout.add_widget(url_layout)

        # Settings section
        settings_label = Label(
            text='Settings',
            font_size='20sp',
            size_hint_y=None,
            height=40,
            color=(0.8, 0.8, 1, 1),
            bold=True
        )
        layout.add_widget(settings_label)

        # Foreground service toggle
        foreground_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        foreground_layout.add_widget(Label(text='Background Service:', size_hint_x=0.6, color=(1, 1, 1, 1), font_size='16sp'))
        self.foreground_btn = Button(
            text='OFF',
            size_hint_x=0.4,
            background_color=(0.5, 0.5, 0.5, 1),
            background_normal=''
        )
        self.foreground_btn.bind(on_press=self.toggle_foreground_service)
        foreground_layout.add_widget(self.foreground_btn)
        layout.add_widget(foreground_layout)

        # Alert duration slider
        duration_label_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=35)
        duration_label_layout.add_widget(Label(text='Alert Duration:', size_hint_x=0.6, color=(1, 1, 1, 1), font_size='16sp'))
        self.duration_value_label = Label(text=f'{self.alert_duration}s', size_hint_x=0.4, color=(1, 1, 1, 1), font_size='16sp')
        duration_label_layout.add_widget(self.duration_value_label)
        layout.add_widget(duration_label_layout)

        from kivy.uix.slider import Slider
        self.duration_slider = Slider(
            min=10,
            max=300,
            value=self.alert_duration,
            step=5,
            size_hint_y=None,
            height=50
        )
        self.duration_slider.bind(value=self.on_duration_change)
        layout.add_widget(self.duration_slider)

        # Custom ringtone button
        ringtone_btn = Button(
            text='Select Custom Ringtone',
            size_hint_y=None,
            height=55,
            background_color=(0.3, 0.5, 0.7, 1),
            background_normal=''
        )
        ringtone_btn.bind(on_press=self.select_ringtone)
        layout.add_widget(ringtone_btn)

        self.ringtone_label = Label(
            text='Using: Default Beep',
            font_size='14sp',
            size_hint_y=None,
            height=30,
            color=(0.7, 0.7, 0.7, 1)
        )
        layout.add_widget(self.ringtone_label)

        # Separator
        layout.add_widget(Label(text='', size_hint_y=None, height=15))

        # Buttons
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=65, spacing=10)

        self.connect_btn = Button(
            text='Connect',
            background_color=(0.2, 0.6, 0.2, 1),
            background_normal='',
            font_size='16sp'
        )
        self.connect_btn.bind(on_press=self.toggle_connection)
        btn_layout.add_widget(self.connect_btn)

        test_btn = Button(
            text='Test Alert',
            background_color=(0.6, 0.4, 0, 1),
            background_normal='',
            font_size='16sp'
        )
        test_btn.bind(on_press=self.test_alert)
        btn_layout.add_widget(test_btn)

        layout.add_widget(btn_layout)

        # Alert count
        self.count_label = Label(
            text='Alerts: 0',
            font_size='20sp',
            size_hint_y=None,
            height=45,
            color=(1, 1, 1, 1)
        )
        layout.add_widget(self.count_label)

        # Alert log
        log_label = Label(
            text='Alert Log:',
            font_size='18sp',
            size_hint_y=None,
            height=35,
            color=(0.8, 0.8, 0.8, 1)
        )
        layout.add_widget(log_label)

        log_scroll = ScrollView(size_hint_y=None, height=250)
        self.log_label = Label(
            text='No alerts yet',
            font_size='15sp',
            size_hint_y=None,
            color=(0.7, 0.7, 0.7, 1),
            text_size=(Window.width - 80, None),
            halign='left',
            valign='top'
        )
        self.log_label.bind(texture_size=self.log_label.setter('size'))
        log_scroll.add_widget(self.log_label)
        layout.add_widget(log_scroll)

        # Add content to main layout
        main_layout.add_widget(scroll)

        # Initialize Android components
        if ANDROID_AVAILABLE:
            self.init_android()

        return main_layout

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

            # Initialize MediaPlayer
            self.init_media_player()

            print("[Android] ===== ALL INITIALIZED SUCCESSFULLY =====")
        except Exception as e:
            print(f"[Android] Init FAILED: {e}")
            import traceback
            traceback.print_exc()

    def toggle_foreground_service(self, instance):
        """Toggle foreground service for background persistence"""
        if not ANDROID_AVAILABLE:
            print("[Foreground] Not available on this platform")
            return

        if not self.foreground_running:
            self.start_foreground_service()
            self.foreground_btn.text = 'ON'
            self.foreground_btn.background_color = (0.2, 0.6, 0.2, 1)
        else:
            self.stop_foreground_service()
            self.foreground_btn.text = 'OFF'
            self.foreground_btn.background_color = (0.5, 0.5, 0.5, 1)

    def start_foreground_service(self):
        """Show HIGH-PRIORITY persistent notification for background monitoring"""
        try:
            activity = PythonActivity.mActivity
            context = activity.getApplicationContext()

            # Create HIGH-PRIORITY notification channel for foreground service
            channel_id = "foreground_monitor_channel"
            notification_manager = context.getSystemService(Context.NOTIFICATION_SERVICE)

            try:
                channel = NotificationChannel(
                    channel_id,
                    "Background Monitoring",
                    NotificationManager.IMPORTANCE_LOW  # LOW = minimal disturbance but keeps alive
                )
                channel.setDescription("Keeps app running to monitor email alerts")
                channel.setSound(None, None)  # No sound for this notification
                notification_manager.createNotificationChannel(channel)
                print("[ForegroundService] Channel created")
            except Exception as e:
                print(f"[ForegroundService] Channel error: {e}")

            # Create notification builder
            try:
                notification_builder = NotificationBuilder(context, channel_id)
            except:
                notification_builder = NotificationBuilder(context)

            notification_builder.setContentTitle("📧 Email Monitor Active")
            notification_builder.setContentText(f"Connected to {self.server_url} - Monitoring alerts")
            notification_builder.setSmallIcon(context.getApplicationInfo().icon)
            notification_builder.setOngoing(True)  # Cannot be dismissed - CRITICAL
            notification_builder.setAutoCancel(False)
            notification_builder.setPriority(1)  # PRIORITY_LOW
            notification_builder.setCategory("service")

            notification = notification_builder.build()
            notification.flags |= 0x00000020  # FLAG_NO_CLEAR - prevents swipe-to-dismiss

            # Show persistent notification
            notification_manager.notify(self.notification_id, notification)
            self.foreground_running = True
            print("[ForegroundService] ✓ HIGH-PRIORITY persistent notification shown")
            print("[ForegroundService] This keeps app alive in background on vivo!")

        except Exception as e:
            print(f"[ForegroundService] FAILED: {e}")
            import traceback
            traceback.print_exc()
            self.foreground_running = False

    def stop_foreground_service(self):
        """Remove persistent notification"""
        try:
            activity = PythonActivity.mActivity
            context = activity.getApplicationContext()

            notification_manager = context.getSystemService(Context.NOTIFICATION_SERVICE)
            notification_manager.cancel(self.notification_id)
            self.foreground_running = False
            print("[Notification] ✓ Notification cancelled")

        except Exception as e:
            print(f"[Notification] Stop FAILED: {e}")

    def on_duration_change(self, instance, value):
        """Handle alert duration slider change"""
        self.alert_duration = int(value)
        self.duration_value_label.text = f'{self.alert_duration}s'
        print(f"[Config] Alert duration set to {self.alert_duration}s")

    def select_ringtone(self, instance):
        """Open file picker for custom ringtone"""
        if platform == 'android':
            try:
                # Use Android file picker
                from android import activity
                from jnius import autoclass, cast

                Intent = autoclass('android.content.Intent')
                Uri = autoclass('android.net.Uri')

                intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
                intent.addCategory(Intent.CATEGORY_OPENABLE)
                intent.setType("audio/*")

                activity.bind(on_activity_result=self.on_ringtone_selected)
                PythonActivity.mActivity.startActivityForResult(intent, 1001)
                print("[Ringtone] File picker opened")

            except Exception as e:
                print(f"[Ringtone] Picker error: {e}")
                self.ringtone_label.text = "Error: Could not open file picker"
        else:
            # Desktop: just show info
            self.ringtone_label.text = "Custom ringtone only works on Android"
            print("[Ringtone] Not available on desktop")

    def on_ringtone_selected(self, request_code, result_code, data):
        """Handle ringtone file selection result"""
        if request_code == 1001 and result_code == -1:  # RESULT_OK
            try:
                uri = data.getData()

                # Get real path from URI
                from jnius import autoclass, cast
                ContentResolver = autoclass('android.content.ContentResolver')
                ParcelFileDescriptor = autoclass('android.os.ParcelFileDescriptor')

                activity = PythonActivity.mActivity
                context = activity.getApplicationContext()
                content_resolver = context.getContentResolver()

                # Copy file to app's internal storage
                import os
                import shutil

                ringtone_path = os.path.join(os.path.dirname(__file__), 'custom_ringtone.mp3')

                # Open input stream
                input_stream = content_resolver.openInputStream(uri)
                input_stream_reader = autoclass('java.io.InputStream')

                # Save to file
                with open(ringtone_path, 'wb') as f:
                    buffer = bytearray(8192)
                    while True:
                        bytes_read = input_stream.read(buffer)
                        if bytes_read == -1:
                            break
                        f.write(buffer[:bytes_read])

                input_stream.close()

                self.custom_ringtone_path = ringtone_path
                self.ringtone_label.text = 'Using: Custom Ringtone'
                print(f"[Ringtone] ✓ Custom ringtone saved: {ringtone_path}")

                # Reinitialize MediaPlayer with new file
                self.init_media_player()

            except Exception as e:
                print(f"[Ringtone] Selection error: {e}")
                import traceback
                traceback.print_exc()
                self.ringtone_label.text = "Error: Could not load ringtone"

    def init_media_player(self):
        """Initialize or reinitialize MediaPlayer with current ringtone"""
        if not ANDROID_AVAILABLE:
            return

        try:
            # Stop and release old player if exists
            if self.media_player:
                try:
                    if self.media_player.isPlaying():
                        self.media_player.stop()
                    self.media_player.release()
                except:
                    pass

            activity = PythonActivity.mActivity
            context = activity.getApplicationContext()

            # Create new player
            self.media_player = MediaPlayer()

            # Set AudioAttributes for ALARM stream
            audio_attrs = AudioAttributesBuilder() \
                .setUsage(AudioAttributes.USAGE_ALARM) \
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION) \
                .build()

            self.media_player.setAudioAttributes(audio_attrs)

            # Set data source
            import os
            if self.custom_ringtone_path and os.path.exists(self.custom_ringtone_path):
                audio_file = self.custom_ringtone_path
            else:
                audio_file = os.path.join(os.path.dirname(__file__), 'alarm.wav')

            self.media_player.setDataSource(audio_file)
            self.media_player.prepare()
            self.media_player.setLooping(True)
            self.media_player.setVolume(1.0, 1.0)

            print(f"[MediaPlayer] ✓ Initialized with: {audio_file}")

        except Exception as e:
            print(f"[MediaPlayer] Init error: {e}")
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

            # CRITICAL: Start foreground service to prevent vivo from killing app
            if ANDROID_AVAILABLE:
                self.start_foreground_service()

            # Start BOTH SSE monitoring and polling threads for vivo reliability
            self.sse_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.sse_thread.start()

            self.poll_thread = threading.Thread(target=self.poll_loop, daemon=True)
            self.poll_thread.start()
            print("[Init] Started SSE + Polling hybrid mode for vivo")

            # Start watchdog to auto-restart dead threads (check every 30 seconds)
            if self.watchdog_event:
                self.watchdog_event.cancel()
            self.watchdog_event = Clock.schedule_interval(self.check_threads, 30)
            print("[Watchdog] Started thread monitor (30s interval)")
        else:
            self.running = False
            self.connected = False
            self.connect_btn.text = 'Connect'
            self.connect_btn.background_color = (0.2, 0.6, 0.2, 1)
            self.update_status("Disconnected", (1, 0.5, 0, 1))

            # Stop watchdog
            if self.watchdog_event:
                self.watchdog_event.cancel()
                self.watchdog_event = None
                print("[Watchdog] Stopped")

            # Stop foreground service when disconnecting
            if ANDROID_AVAILABLE and self.foreground_running:
                self.stop_foreground_service()

    def monitor_loop(self):
        """Monitor server for alerts using SSE with auto-reconnect"""
        retry_count = 0
        max_retries = 999  # Essentially unlimited retries

        while self.running and retry_count < max_retries:
            try:
                url = f"{self.server_url}/events"

                if retry_count > 0:
                    wait_time = min(5, retry_count)  # Wait up to 5 seconds between retries
                    print(f"[SSE] Reconnecting in {wait_time}s (attempt {retry_count + 1})...")
                    Clock.schedule_once(lambda dt: self.update_status(f"Reconnecting... ({retry_count + 1})", (1, 0.8, 0, 1)))
                    time.sleep(wait_time)

                print(f"[SSE] Connecting to {url}")
                # Use SSE to receive real-time alerts
                response = requests.get(url, stream=True, timeout=30)

                if response.status_code == 200:
                    retry_count = 0  # Reset retry counter on successful connection
                    Clock.schedule_once(lambda dt: self.update_status("Connected", (0, 1, 0, 1)))
                    print("[SSE] ✓ Connected successfully")

                    for line in response.iter_lines():
                        if not self.running:
                            print("[SSE] Disconnecting (user requested)")
                            break

                        if line:
                            line = line.decode('utf-8')
                            print(f"[SSE] Received line: {line}")

                            # Parse SSE event
                            if line.startswith('data: '):
                                try:
                                    json_str = line[6:]
                                    print(f"[SSE] Parsing JSON: {json_str}")
                                    data = json.loads(json_str)
                                    print(f"[SSE] ✓ Parsed data: {data}")
                                    Clock.schedule_once(lambda dt, d=data: self.handle_alert(d))
                                except Exception as e:
                                    print(f"[SSE] ✗ JSON parse error: {e}")
                                    print(f"[SSE] Raw line was: {repr(line)}")

                    # Connection ended normally
                    if self.running:
                        print("[SSE] Connection closed by server, will retry")
                        retry_count += 1
                    else:
                        print("[SSE] Connection closed by user")
                        break
                else:
                    print(f"[SSE] ✗ HTTP {response.status_code}")
                    Clock.schedule_once(lambda dt: self.update_status(f"Failed: {response.status_code}", (1, 0, 0, 1)))
                    retry_count += 1

            except requests.exceptions.Timeout:
                print("[SSE] ✗ Timeout")
                Clock.schedule_once(lambda dt: self.update_status("Timeout, retrying...", (1, 0.5, 0, 1)))
                retry_count += 1
            except requests.exceptions.ConnectionError as e:
                print(f"[SSE] ✗ Connection error: {e}")
                Clock.schedule_once(lambda dt: self.update_status("Connection lost, retrying...", (1, 0.5, 0, 1)))
                retry_count += 1
            except Exception as e:
                print(f"[SSE] ✗ Unexpected error: {e}")
                Clock.schedule_once(lambda dt: self.update_status(f"Error: {str(e)}", (1, 0, 0, 1)))
                retry_count += 1
                import traceback
                traceback.print_exc()

        # Final cleanup
        if self.connected:
            self.connected = False
            Clock.schedule_once(lambda dt: self.reset_connection())
            print("[SSE] Monitor loop ended")

    def poll_loop(self):
        """Polling fallback for vivo phones - checks every 5 seconds"""
        print("[Poll] Starting polling thread (5s interval)")
        processed_timestamps = set()  # Track processed alerts to avoid duplicates

        while self.running:
            try:
                time.sleep(5)  # Poll every 5 seconds

                if not self.running:
                    break

                url = f"{self.server_url}/poll"
                print(f"[Poll] Checking {url}")

                response = requests.get(url, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    alerts = data.get('alerts', [])

                    if alerts:
                        print(f"[Poll] ✓ Received {len(alerts)} alert(s)")

                        for alert in alerts:
                            # Use timestamp to avoid duplicate processing
                            timestamp = alert.get('timestamp', time.time())

                            if timestamp not in processed_timestamps:
                                processed_timestamps.add(timestamp)
                                print(f"[Poll] Processing alert: {alert.get('subject')}")
                                Clock.schedule_once(lambda dt, a=alert: self.handle_alert(a))

                                # Keep processed set size limited
                                if len(processed_timestamps) > 100:
                                    oldest = min(processed_timestamps)
                                    processed_timestamps.remove(oldest)
                    else:
                        print("[Poll] No new alerts")
                else:
                    print(f"[Poll] ✗ HTTP {response.status_code}")

            except requests.exceptions.Timeout:
                print("[Poll] Timeout (will retry)")
            except requests.exceptions.ConnectionError as e:
                print(f"[Poll] Connection error: {e}")
            except Exception as e:
                print(f"[Poll] Error: {e}")
                import traceback
                traceback.print_exc()

        print("[Poll] Polling loop ended")

    def check_threads(self, dt):
        """Watchdog: Check if threads are alive and restart if dead"""
        if not self.running:
            return

        sse_alive = self.sse_thread and self.sse_thread.is_alive()
        poll_alive = self.poll_thread and self.poll_thread.is_alive()

        if not sse_alive:
            print("[Watchdog] ⚠ SSE thread died! Restarting...")
            self.sse_thread = threading.Thread(target=self.monitor_loop, daemon=True)
            self.sse_thread.start()
            Clock.schedule_once(lambda dt: self.update_status("Auto-restarted SSE", (1, 0.8, 0, 1)))

        if not poll_alive:
            print("[Watchdog] ⚠ Poll thread died! Restarting...")
            self.poll_thread = threading.Thread(target=self.poll_loop, daemon=True)
            self.poll_thread.start()
            Clock.schedule_once(lambda dt: self.update_status("Auto-restarted Polling", (1, 0.8, 0, 1)))

        if not sse_alive or not poll_alive:
            print(f"[Watchdog] Status - SSE: {'✓' if sse_alive else '✗'}, Poll: {'✓' if poll_alive else '✗'}")
        else:
            print(f"[Watchdog] ✓ All threads healthy")

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
                        wake_duration = (self.alert_duration + 5) * 1000  # Alert duration + 5s buffer, in milliseconds
                        self.wake_lock.acquire(wake_duration)
                        print(f"[Wake] ✓ WAKE LOCK ACQUIRED ({self.alert_duration + 5}s)")
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

            print(f"\n[Alert] Starting vibration and sound threads ({self.alert_duration}s)...")

            # MULTI-METHOD VIBRATION STRATEGY:
            # 1. Direct Vibrator calls (works when unlocked)
            threading.Thread(target=self.vibrate_long, daemon=True, name="VibrateThread").start()

            # 2. Full-Screen Intent notification (system-level)
            threading.Thread(target=self.vibrate_via_notification, daemon=True, name="NotificationVibrateThread").start()

            # 3. AlarmManager system alarm
            threading.Thread(target=self.vibrate_via_alarm, daemon=True, name="AlarmVibrateThread").start()

            # 4. WEARABLE DEVICE NOTIFICATIONS (for smartwatch/band)
            threading.Thread(target=self.vibrate_via_wearable, daemon=True, name="WearableVibrateThread").start()

            # 5. Play alarm sound for configured duration in background thread
            threading.Thread(target=self.play_alarm_long, daemon=True, name="SoundThread").start()

            print(f"[Alert] All 5 threads started (Direct + Notification + Alarm + Wearable + Sound)!\n")
        else:
            print(f"[Desktop Alert] {title}: {message}")

    def vibrate_long(self):
        """Vibrate for configured duration - ULTRA aggressive method for vivo lockscreen"""
        if not self.vibrator:
            return

        try:
            print(f"[Vibrate] Starting {self.alert_duration}s ULTRA AGGRESSIVE vibration")
            print(f"[Vibrate] Strategy: 200ms vibrate + 200ms sleep, wake lock EVERY cycle")

            # ULTRA aggressive: vibrate every 200ms (not 500ms)
            # This gives vivo NO time to suspend the vibration
            cycle_duration = 0.2  # 200ms cycles
            vibrate_duration = 180  # 180ms vibrate (leave 20ms gap)
            cycles = int(self.alert_duration / cycle_duration)

            # Get PowerManager for creating fresh wake locks
            try:
                activity = PythonActivity.mActivity
                context = activity.getApplicationContext()
                power_manager = context.getSystemService(Context.POWER_SERVICE)
                print("[Vibrate] PowerManager obtained for per-cycle wake locks")
            except Exception as e:
                print(f"[Vibrate] PowerManager error: {e}")
                power_manager = None

            for i in range(cycles):
                if not self.alert_active:
                    print("[Vibrate] Stopped by alert_active flag")
                    break

                try:
                    # CRITICAL: Acquire NEW wake lock EVERY cycle to fight vivo
                    if power_manager and i % 2 == 0:  # Every other cycle (every 400ms)
                        try:
                            # Release old wake lock if held
                            if self.wake_lock and self.wake_lock.isHeld():
                                try:
                                    self.wake_lock.release()
                                except:
                                    pass

                            # Create FRESH wake lock with PARTIAL_WAKE_LOCK for lockscreen
                            self.wake_lock = power_manager.newWakeLock(
                                PowerManager.PARTIAL_WAKE_LOCK | PowerManager.ACQUIRE_CAUSES_WAKEUP,
                                f"EmailAlert::Cycle{i}"
                            )
                            self.wake_lock.acquire(10000)  # 10 second timeout per lock
                        except Exception as we:
                            pass  # Continue anyway

                    # Vibrate with AudioAttributes every cycle
                    try:
                        AudioAttributes = autoclass('android.media.AudioAttributes')
                        attrs = AudioAttributes.Builder() \
                            .setUsage(AudioAttributes.USAGE_ALARM) \
                            .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION) \
                            .build()
                        self.vibrator.vibrate(vibrate_duration, attrs)
                    except:
                        self.vibrator.vibrate(vibrate_duration)

                    # Very short sleep
                    time.sleep(cycle_duration)

                    if i % 25 == 0:  # Log every 5 seconds
                        elapsed = i * cycle_duration
                        remaining = self.alert_duration - elapsed
                        print(f"[Vibrate] {elapsed:.1f}s / {self.alert_duration}s (remaining: {remaining:.1f}s)")

                except Exception as ve:
                    print(f"[Vibrate] Cycle {i} error: {ve}")
                    # Don't break - try to continue vibrating
                    time.sleep(0.5)

            print(f"[Vibrate] ✓ Completed {cycles} cycles")

        except Exception as e:
            print(f"[Vibrate Error] {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                self.vibrator.cancel()
            except:
                pass
            self.alert_active = False
            print("[Vibrate] Cleanup complete")

    def play_alarm_long(self):
        """Play alarm sound for configured duration using MediaPlayer"""
        if not self.media_player:
            print("[Sound] MediaPlayer not available!")
            return

        try:
            print("[Sound] ===== STARTING ALARM =====")

            # Start playing (already set to loop in init)
            self.media_player.start()
            print("[Sound] MediaPlayer.start() called - SHOULD BE PLAYING NOW")

            # Keep playing for configured duration
            checks = int(self.alert_duration / 5)  # Check every 5 seconds
            for i in range(checks):
                time.sleep(5)
                is_playing = self.media_player.isPlaying()
                print(f"[Sound] Check {i+1}/{checks}: isPlaying={is_playing}, alert_active={self.alert_active}")
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

    def vibrate_via_notification(self):
        """Use Full-Screen Intent notification for lockscreen - ULTIMATE method"""
        if not ANDROID_AVAILABLE:
            return

        try:
            print("[FullScreenVibrate] Starting FULL-SCREEN INTENT vibration (like incoming call)")

            activity = PythonActivity.mActivity
            context = activity.getApplicationContext()
            notification_manager = context.getSystemService(Context.NOTIFICATION_SERVICE)

            # Create ALARM-level notification channel
            channel_id = "fullscreen_alert_channel"
            try:
                NotificationChannel = autoclass('android.app.NotificationChannel')
                NotificationManager = autoclass('android.app.NotificationManager')

                # Use IMPORTANCE_HIGH for full-screen intents
                channel = NotificationChannel(
                    channel_id,
                    "Critical Alerts",
                    NotificationManager.IMPORTANCE_HIGH
                )
                channel.setDescription("Critical email alerts with full-screen notification")
                channel.enableVibration(True)
                channel.setBypassDnd(True)
                channel.setLockscreenVisibility(1)  # Show on lockscreen

                # Aggressive vibration pattern
                pattern_cycles = int(self.alert_duration / 0.4)
                vibration_pattern = []
                for i in range(pattern_cycles):
                    vibration_pattern.extend([0, 300, 100])
                channel.setVibrationPattern(vibration_pattern)

                notification_manager.createNotificationChannel(channel)
                print("[FullScreenVibrate] Full-screen channel created")

            except Exception as e:
                print(f"[FullScreenVibrate] Channel error: {e}")

            # Create Full-Screen Intent (launches app when locked)
            try:
                Intent = autoclass('android.content.Intent')
                PendingIntent = autoclass('android.app.PendingIntent')

                # Create intent to launch main activity
                full_screen_intent = Intent(context, PythonActivity)
                full_screen_intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP)
                full_screen_intent.putExtra("TRIGGERED_BY_ALERT", True)

                # Create PendingIntent with FLAG_IMMUTABLE for Android 12+
                try:
                    pending_intent = PendingIntent.getActivity(
                        context,
                        0,
                        full_screen_intent,
                        PendingIntent.FLAG_UPDATE_CURRENT | 0x04000000  # FLAG_IMMUTABLE
                    )
                except:
                    # Fallback for older Android
                    pending_intent = PendingIntent.getActivity(
                        context,
                        0,
                        full_screen_intent,
                        PendingIntent.FLAG_UPDATE_CURRENT
                    )

                print("[FullScreenVibrate] PendingIntent created")

                # Build notification with Full-Screen Intent
                NotificationBuilder = autoclass('android.app.Notification$Builder')
                try:
                    builder = NotificationBuilder(context, channel_id)
                except:
                    builder = NotificationBuilder(context)

                builder.setContentTitle("🚨 CRITICAL EMAIL ALERT")
                builder.setContentText("Urgent: Check your email immediately")
                builder.setSmallIcon(context.getApplicationInfo().icon)
                builder.setPriority(2)  # PRIORITY_MAX
                builder.setCategory("alarm")
                builder.setVisibility(1)  # VISIBILITY_PUBLIC
                builder.setAutoCancel(True)

                # Set vibration pattern on notification
                pattern_cycles = int(self.alert_duration / 0.4)
                vibration_pattern = []
                for i in range(pattern_cycles):
                    vibration_pattern.extend([0, 300, 100])
                builder.setVibrate(vibration_pattern)

                # THE KEY: Set Full-Screen Intent (like incoming call)
                builder.setFullScreenIntent(pending_intent, True)

                # Build and post notification
                notification = builder.build()
                notification.flags |= 0x00000080  # FLAG_INSISTENT (repeating sound/vibration)

                notification_id = 8888
                notification_manager.notify(notification_id, notification)
                print(f"[FullScreenVibrate] ✓ FULL-SCREEN notification posted!")
                print(f"[FullScreenVibrate] This should wake screen and vibrate on lockscreen!")

                # Keep notification for duration
                time.sleep(self.alert_duration)

                # Cancel notification
                notification_manager.cancel(notification_id)
                print("[FullScreenVibrate] ✓ Notification cancelled")

            except Exception as e:
                print(f"[FullScreenVibrate] Intent/Notification error: {e}")
                import traceback
                traceback.print_exc()

        except Exception as e:
            print(f"[FullScreenVibrate] ERROR: {e}")
            import traceback
            traceback.print_exc()

    def vibrate_via_alarm(self):
        """Use AlarmManager to schedule system alarm with vibration - TRUE system service"""
        if not ANDROID_AVAILABLE:
            return

        try:
            print("[AlarmVibrate] Starting ALARMMANAGER-BASED vibration (system service)")

            activity = PythonActivity.mActivity
            context = activity.getApplicationContext()

            # Get AlarmManager system service
            AlarmManager = autoclass('android.app.AlarmManager')
            alarm_service = context.getSystemService(Context.ALARM_SERVICE)

            # Create multiple rapid-fire alarms for continuous vibration effect
            Intent = autoclass('android.content.Intent')
            PendingIntent = autoclass('android.app.PendingIntent')

            # Calculate number of alarms needed (one every 500ms)
            num_alarms = int(self.alert_duration / 0.5)
            print(f"[AlarmVibrate] Scheduling {num_alarms} alarms over {self.alert_duration}s")

            import time as time_module
            current_time_ms = int(time_module.time() * 1000)

            for i in range(num_alarms):
                try:
                    # Create broadcast intent for alarm
                    alarm_intent = Intent(context, PythonActivity)
                    alarm_intent.setAction(f"com.emailmonitor.VIBRATE_ALARM_{i}")
                    alarm_intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                    alarm_intent.addFlags(Intent.FLAG_RECEIVER_FOREGROUND)

                    # Create PendingIntent
                    try:
                        pending_intent = PendingIntent.getBroadcast(
                            context,
                            10000 + i,  # Unique request code
                            alarm_intent,
                            PendingIntent.FLAG_UPDATE_CURRENT | 0x04000000  # FLAG_IMMUTABLE
                        )
                    except:
                        pending_intent = PendingIntent.getBroadcast(
                            context,
                            10000 + i,
                            alarm_intent,
                            PendingIntent.FLAG_UPDATE_CURRENT
                        )

                    # Schedule alarm to fire at specific time
                    trigger_time_ms = current_time_ms + (i * 500)  # Every 500ms

                    # Use setAlarmClock for highest priority (shows alarm icon)
                    try:
                        AlarmClockInfo = autoclass('android.app.AlarmManager$AlarmClockInfo')
                        clock_info = AlarmClockInfo(trigger_time_ms, pending_intent)
                        alarm_service.setAlarmClock(clock_info, pending_intent)
                    except:
                        # Fallback: use setExactAndAllowWhileIdle
                        try:
                            alarm_service.setExactAndAllowWhileIdle(
                                AlarmManager.RTC_WAKEUP,
                                trigger_time_ms,
                                pending_intent
                            )
                        except:
                            # Final fallback: regular setExact
                            alarm_service.setExact(
                                AlarmManager.RTC_WAKEUP,
                                trigger_time_ms,
                                pending_intent
                            )

                    # Vibrate immediately when alarm fires (in this thread)
                    if i == 0:
                        time.sleep(0.5)  # Wait for first alarm
                    else:
                        time.sleep(0.5)  # Wait between alarms

                    # Trigger vibration manually as alarms fire
                    if self.vibrator and self.alert_active:
                        try:
                            AudioAttributes = autoclass('android.media.AudioAttributes')
                            attrs = AudioAttributes.Builder() \
                                .setUsage(AudioAttributes.USAGE_ALARM) \
                                .build()
                            self.vibrator.vibrate(400, attrs)
                        except:
                            self.vibrator.vibrate(400)

                except Exception as alarm_error:
                    print(f"[AlarmVibrate] Alarm {i} error: {alarm_error}")

            print(f"[AlarmVibrate] ✓ Scheduled {num_alarms} system alarms")
            print("[AlarmVibrate] AlarmManager vibration complete")

        except Exception as e:
            print(f"[AlarmVibrate] ERROR: {e}")
            import traceback
            traceback.print_exc()

    def vibrate_via_wearable(self):
        """Send continuous notifications for smartwatch/band vibration"""
        if not ANDROID_AVAILABLE:
            return

        try:
            print("[WearableVibrate] Starting WEARABLE DEVICE notification sequence")
            print("[WearableVibrate] This will vibrate your smartwatch/band continuously!")

            activity = PythonActivity.mActivity
            context = activity.getApplicationContext()
            notification_manager = context.getSystemService(Context.NOTIFICATION_SERVICE)

            # Create wearable-optimized notification channel
            channel_id = "wearable_vibration_channel"
            try:
                NotificationChannel = autoclass('android.app.NotificationChannel')
                NotificationManager = autoclass('android.app.NotificationManager')

                channel = NotificationChannel(
                    channel_id,
                    "Wearable Alerts",
                    NotificationManager.IMPORTANCE_HIGH  # HIGH ensures sync to wearable
                )
                channel.setDescription("Continuous alerts for smartwatch/band")
                channel.enableVibration(True)
                channel.setBypassDnd(True)
                channel.setLockscreenVisibility(1)

                # Simple vibration pattern that wearables will repeat
                channel.setVibrationPattern([0, 500, 200, 500, 200, 500])

                notification_manager.createNotificationChannel(channel)
                print("[WearableVibrate] Wearable channel created")

            except Exception as e:
                print(f"[WearableVibrate] Channel error: {e}")

            # Send MULTIPLE notifications over the alert duration
            # Each notification will vibrate the wearable device
            # Interval: every 3 seconds (typical wearable vibration is ~2s)
            num_notifications = int(self.alert_duration / 3) + 1
            print(f"[WearableVibrate] Sending {num_notifications} notifications over {self.alert_duration}s")

            NotificationBuilder = autoclass('android.app.Notification$Builder')

            for i in range(num_notifications):
                if not self.alert_active:
                    print("[WearableVibrate] Stopped by alert_active flag")
                    break

                try:
                    # Create notification builder
                    try:
                        builder = NotificationBuilder(context, channel_id)
                    except:
                        builder = NotificationBuilder(context)

                    # Set notification content - changes slightly each time to ensure delivery
                    alert_num = i + 1
                    builder.setContentTitle(f"🚨 EMAIL ALERT #{alert_num}")
                    builder.setContentText(f"Critical email notification - Check immediately!")
                    builder.setSmallIcon(context.getApplicationInfo().icon)
                    builder.setPriority(2)  # PRIORITY_MAX
                    builder.setCategory("alarm")
                    builder.setVisibility(1)  # VISIBILITY_PUBLIC

                    # CRITICAL for wearables: Set to auto-cancel after a short time
                    # This ensures each notification is "new" and triggers vibration
                    builder.setAutoCancel(True)
                    builder.setTimeoutAfter(2500)  # Auto-dismiss after 2.5s

                    # Vibration pattern for wearable
                    builder.setVibrate([0, 500, 200, 500, 200, 500])

                    # Set as ongoing for first notification only (shows in notification shade)
                    if i == 0:
                        builder.setOngoing(False)  # Allow dismissal

                    # Build notification
                    notification = builder.build()

                    # Use unique notification ID for each (ensures wearable vibrates for each)
                    notification_id = 5000 + i
                    notification_manager.notify(notification_id, notification)

                    print(f"[WearableVibrate] ✓ Notification {alert_num}/{num_notifications} sent (ID: {notification_id})")

                    # Wait 3 seconds before next notification
                    if i < num_notifications - 1:  # Don't sleep after last one
                        time.sleep(3)

                except Exception as notif_error:
                    print(f"[WearableVibrate] Notification {i} error: {notif_error}")

            print(f"[WearableVibrate] ✓ Sent {num_notifications} wearable notifications")
            print("[WearableVibrate] Your smartwatch/band should have vibrated continuously!")

            # Clean up: cancel all wearable notifications after completion
            time.sleep(2)
            for i in range(num_notifications):
                try:
                    notification_manager.cancel(5000 + i)
                except:
                    pass

        except Exception as e:
            print(f"[WearableVibrate] ERROR: {e}")
            import traceback
            traceback.print_exc()

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
