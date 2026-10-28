package com.cxmlo.miku.android.connection

import android.app.Notification
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import com.cxmlo.miku.android.data.MikuClient
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

class MikuNotificationListenerService : NotificationListenerService() {
    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        val notification = sbn?.notification ?: return
        val pkg = sbn.packageName ?: return
        if (pkg == packageName || pkg == "android" || pkg == "com.android.systemui") return
        if ((notification.flags and Notification.FLAG_ONGOING_EVENT) != 0) return

        val extras = notification.extras ?: return
        val title = extras.getCharSequence(Notification.EXTRA_TITLE)?.toString()?.trim().orEmpty()
        val text = extras.getCharSequence(Notification.EXTRA_BIG_TEXT)?.toString()?.trim()
            ?: extras.getCharSequence(Notification.EXTRA_TEXT)?.toString()?.trim()
            .orEmpty()
        if (title.isBlank() && text.isBlank()) return

        val appLabel = runCatching {
            val info = packageManager.getApplicationInfo(pkg, 0)
            packageManager.getApplicationLabel(info).toString()
        }.getOrDefault(pkg)

        val timeStr = SimpleDateFormat("HH:mm", Locale.getDefault()).format(Date(sbn.postTime))
        MikuClient.forwardPhoneNotification(
            id = sbn.key ?: "${pkg}_${sbn.id}",
            app = appLabel,
            title = title.ifBlank { appLabel },
            body = text,
            time = timeStr,
        )
    }
}
