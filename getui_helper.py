#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
个推推送辅助模块
处理个推 SDK 的初始化和消息监听
"""

import time
import threading
from kivy.utils import platform

if platform == 'android':
    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        Context = autoclass('android.content.Context')
        PushManager = autoclass('com.igexin.sdk.PushManager')
        ANDROID_AVAILABLE = True
    except:
        ANDROID_AVAILABLE = False
else:
    ANDROID_AVAILABLE = False


def init_getui(app_instance):
    """
    初始化个推 SDK

    Args:
        app_instance: EmailAlertApp 实例
    """
    if not ANDROID_AVAILABLE:
        print("[Getui] Not on Android, skipping initialization")
        return None

    try:
        activity = PythonActivity.mActivity
        context = activity.getApplicationContext()

        # 初始化个推 SDK
        PushManager.getInstance().initialize(context)
        print("[Getui] ✓ SDK initialized")

        # 获取 ClientID
        client_id = get_client_id()
        if client_id:
            print(f"[Getui] ✓ Client ID: {client_id}")
            app_instance.getui_client_id = client_id
        else:
            print("[Getui] Client ID not ready yet, will retrieve later")

        return True
    except Exception as e:
        print(f"[Getui] ✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_client_id():
    """
    获取个推 Client ID

    Returns:
        str: Client ID 或 None
    """
    if not ANDROID_AVAILABLE:
        return None

    try:
        activity = PythonActivity.mActivity
        context = activity.getApplicationContext()

        # 方案1: 从 SharedPreferences 读取（由 Java Service 保存）
        prefs = context.getSharedPreferences("getui", Context.MODE_PRIVATE)
        client_id = prefs.getString("client_id", None)

        if client_id:
            return client_id

        # 方案2: 从个推 SDK 获取
        client_id = PushManager.getInstance().getClientid(context)
        return client_id
    except Exception as e:
        print(f"[Getui] Failed to get client ID: {e}")
        return None


def start_push_listener(app_instance):
    """
    启动推送监听线程
    监听 SharedPreferences 中的待处理推送

    Args:
        app_instance: EmailAlertApp 实例
    """
    if not ANDROID_AVAILABLE:
        print("[Getui] Not on Android, skipping listener")
        return

    def listener_loop():
        print("[Getui] Push listener thread started")

        while app_instance.running:
            try:
                activity = PythonActivity.mActivity
                context = activity.getApplicationContext()

                # 读取待处理的推送
                prefs = context.getSharedPreferences("email_alert", Context.MODE_PRIVATE)
                subject = prefs.getString("pending_subject", None)
                sender = prefs.getString("pending_from", None)
                timestamp = prefs.getLong("pending_timestamp", 0)

                # 如果有新的推送且未处理过
                if subject and timestamp > app_instance.last_processed_timestamp:
                    print(f"[Getui] ⚡ New push received: {subject} from {sender}")

                    # 更新最后处理时间
                    app_instance.last_processed_timestamp = timestamp

                    # 清除已处理的推送
                    prefs.edit().remove("pending_subject").remove("pending_from").remove("pending_timestamp").apply()

                    # 触发警报（调用现有的 trigger_alert 方法）
                    app_instance.trigger_alert(subject, sender)

                # 每 1 秒检查一次
                time.sleep(1)

            except Exception as e:
                print(f"[Getui] Listener error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(5)  # 出错后等待 5 秒再试

        print("[Getui] Push listener thread stopped")

    # 启动监听线程
    listener_thread = threading.Thread(target=listener_loop, daemon=True)
    listener_thread.start()
    app_instance.getui_listener_thread = listener_thread

    print("[Getui] ✓ Push listener started")


def stop_push_listener(app_instance):
    """
    停止推送监听线程

    Args:
        app_instance: EmailAlertApp 实例
    """
    # running 设为 False 会自动停止线程
    if app_instance.getui_listener_thread and app_instance.getui_listener_thread.is_alive():
        print("[Getui] Stopping push listener...")
        # 线程会在下一次循环检查时自动退出
