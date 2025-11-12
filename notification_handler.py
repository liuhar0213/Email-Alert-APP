# -*- coding: utf-8 -*-
"""
Notification Handler for Email Alert App
Handles notifications from NotificationListenerService
"""

from kivy.utils import platform

if platform == 'android':
    try:
        from jnius import autoclass, PythonJavaClass, java_method

        Context = autoclass('android.content.Context')
        BroadcastReceiver = autoclass('android.content.BroadcastReceiver')
        IntentFilter = autoclass('android.content.IntentFilter')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Intent = autoclass('android.content.Intent')

        ANDROID_AVAILABLE = True
    except Exception as e:
        print(f"[NotificationHandler] Android import failed: {e}")
        ANDROID_AVAILABLE = False
else:
    ANDROID_AVAILABLE = False


class NotificationBroadcastReceiver:
    """Receives broadcasts from NotificationListenerService"""

    def __init__(self, callback):
        self.callback = callback
        self.receiver = None

        if not ANDROID_AVAILABLE:
            print("[NotificationHandler] Android not available")
            return

        try:
            # Register broadcast receiver
            self._register_receiver()
            print("[NotificationHandler] Broadcast receiver registered")
        except Exception as e:
            print(f"[NotificationHandler] Failed to register receiver: {e}")

    def _register_receiver(self):
        """Register the broadcast receiver for notification alerts"""
        try:
            # Create intent filter
            intent_filter = IntentFilter()
            intent_filter.addAction("com.emailmonitor.emailalert.NOTIFICATION_ALERT")

            # Create Java broadcast receiver class
            class JavaBroadcastReceiver(PythonJavaClass):
                __javainterfaces__ = ['android/content/BroadcastReceiver']

                def __init__(self, python_callback):
                    super().__init__()
                    self.python_callback = python_callback

                @java_method('(Landroid/content/Context;Landroid/content/Intent;)V')
                def onReceive(self, context, intent):
                    try:
                        # Extract notification data
                        package = intent.getStringExtra("package")
                        title = intent.getStringExtra("title")
                        text = intent.getStringExtra("text")

                        print(f"[NotificationHandler] Received alert from {package}")
                        print(f"[NotificationHandler] Title: {title}")
                        print(f"[NotificationHandler] Text: {text}")

                        # Call Python callback
                        if self.python_callback:
                            self.python_callback(package, title, text)
                    except Exception as e:
                        print(f"[NotificationHandler] Error in onReceive: {e}")

            # Create receiver instance
            self.receiver = JavaBroadcastReceiver(self.callback)

            # Register receiver
            activity = PythonActivity.mActivity
            activity.registerReceiver(self.receiver, intent_filter)

        except Exception as e:
            print(f"[NotificationHandler] Error registering receiver: {e}")
            raise

    def unregister(self):
        """Unregister the broadcast receiver"""
        if self.receiver and ANDROID_AVAILABLE:
            try:
                activity = PythonActivity.mActivity
                activity.unregisterReceiver(self.receiver)
                print("[NotificationHandler] Broadcast receiver unregistered")
            except Exception as e:
                print(f"[NotificationHandler] Error unregistering receiver: {e}")


def start_notification_listener_service():
    """
    Prompts user to enable notification access for the app.
    Returns True if notification access is granted, False otherwise.
    """
    if not ANDROID_AVAILABLE:
        return False

    try:
        # Check if notification listener permission is granted
        Settings = autoclass('android.provider.Settings$Secure')
        activity = PythonActivity.mActivity
        content_resolver = activity.getContentResolver()

        enabled_listeners = Settings.getString(
            content_resolver,
            "enabled_notification_listeners"
        )

        package_name = activity.getPackageName()

        if enabled_listeners and package_name in enabled_listeners:
            print("[NotificationHandler] Notification access already granted")
            return True

        # Open notification access settings
        print("[NotificationHandler] Opening notification access settings...")
        intent = Intent("android.settings.ACTION_NOTIFICATION_LISTENER_SETTINGS")
        activity.startActivity(intent)

        return False

    except Exception as e:
        print(f"[NotificationHandler] Error checking notification access: {e}")
        return False
