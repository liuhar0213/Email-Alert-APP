package com.emailmonitor.emailalert;

import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;
import android.content.Intent;
import android.os.Bundle;
import android.util.Log;

public class NotificationListener extends NotificationListenerService {
    private static final String TAG = "NotificationListener";

    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        String packageName = sbn.getPackageName();
        Bundle extras = sbn.getNotification().extras;

        // Get notification title and text
        String title = extras.getString("android.title", "");
        String text = extras.getCharSequence("android.text", "").toString();

        Log.d(TAG, "Notification from: " + packageName);
        Log.d(TAG, "Title: " + title);
        Log.d(TAG, "Text: " + text);

        // Check if notification is from TradingView or email apps
        boolean isTradingView = packageName.contains("tradingview");
        boolean isEmail = packageName.contains("email") ||
                         packageName.contains("gmail") ||
                         packageName.contains("qq.reader");

        if (isTradingView || isEmail) {
            // Check if notification contains alert keywords
            String fullText = (title + " " + text).toLowerCase();
            boolean isAlert = fullText.contains("alert") ||
                            fullText.contains("警报") ||
                            fullText.contains("警報") ||
                            fullText.contains("提醒");

            if (isAlert) {
                Log.d(TAG, "Alert detected! Broadcasting to app...");

                // Broadcast to main app
                Intent intent = new Intent("com.emailmonitor.emailalert.NOTIFICATION_ALERT");
                intent.putExtra("package", packageName);
                intent.putExtra("title", title);
                intent.putExtra("text", text);
                sendBroadcast(intent);
            }
        }
    }

    @Override
    public void onNotificationRemoved(StatusBarNotification sbn) {
        // Not needed for our use case
    }
}
