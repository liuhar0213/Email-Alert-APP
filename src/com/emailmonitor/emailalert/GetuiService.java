package com.emailmonitor.emailalert;

import android.content.Context;
import com.igexin.sdk.GTIntentService;
import com.igexin.sdk.message.GTCmdMessage;
import com.igexin.sdk.message.GTTransmitMessage;
import org.kivy.android.PythonActivity;
import org.json.JSONObject;

/**
 * 个推推送服务 - 最小化实现
 * 接收推送后调用 Python 的 trigger_alert 方法
 */
public class GetuiService extends GTIntentService {

    @Override
    public void onReceiveServicePid(Context context, int pid) {
        System.out.println("[Getui] Service started with pid: " + pid);
    }

    @Override
    public void onReceiveClientId(Context context, String clientId) {
        System.out.println("[Getui] Client ID: " + clientId);
        // 保存 clientId 供 Python 使用
        context.getSharedPreferences("getui", Context.MODE_PRIVATE)
               .edit()
               .putString("client_id", clientId)
               .apply();
    }

    @Override
    public void onReceiveMessageData(Context context, GTTransmitMessage message) {
        try {
            // 获取推送消息内容
            byte[] payload = message.getPayload();
            if (payload != null) {
                String jsonStr = new String(payload);
                System.out.println("[Getui] Received message: " + jsonStr);

                // 解析 JSON
                JSONObject json = new JSONObject(jsonStr);
                String subject = json.optString("subject", "Email Alert");
                String from = json.optString("from", "Unknown");

                // 调用 Python 的静态方法触发警报
                PythonActivity activity = (PythonActivity) PythonActivity.mActivity;
                if (activity != null) {
                    activity.runOnUiThread(new Runnable() {
                        @Override
                        public void run() {
                            try {
                                // 通过 Kivy 的事件系统触发警报
                                // Python 端会监听这个事件
                                System.out.println("[Getui] Triggering alert: " + subject);
                                // 触发自定义事件（Python 端监听）
                                triggerPythonAlert(subject, from);
                            } catch (Exception e) {
                                System.err.println("[Getui] Error triggering alert: " + e);
                                e.printStackTrace();
                            }
                        }
                    });
                }
            }
        } catch (Exception e) {
            System.err.println("[Getui] Error processing message: " + e);
            e.printStackTrace();
        }
    }

    @Override
    public void onReceiveOnlineState(Context context, boolean online) {
        System.out.println("[Getui] Online state: " + online);
    }

    @Override
    public void onReceiveCommandResult(Context context, GTCmdMessage cmdMessage) {
        System.out.println("[Getui] Command result: " + cmdMessage);
    }

    /**
     * 触发 Python 警报的辅助方法
     * 通过文件或共享内存传递消息给 Python
     */
    private void triggerPythonAlert(String subject, String from) {
        try {
            // 方案1: 使用 SharedPreferences 传递数据
            Context context = PythonActivity.mActivity.getApplicationContext();
            context.getSharedPreferences("email_alert", Context.MODE_PRIVATE)
                   .edit()
                   .putString("pending_subject", subject)
                   .putString("pending_from", from)
                   .putLong("pending_timestamp", System.currentTimeMillis())
                   .apply();

            // 方案2: 发送广播给 Python
            android.content.Intent intent = new android.content.Intent("com.emailmonitor.emailalert.ALERT");
            intent.putExtra("subject", subject);
            intent.putExtra("from", from);
            context.sendBroadcast(intent);

            System.out.println("[Getui] Alert data saved and broadcast sent");
        } catch (Exception e) {
            System.err.println("[Getui] Error in triggerPythonAlert: " + e);
            e.printStackTrace();
        }
    }
}
