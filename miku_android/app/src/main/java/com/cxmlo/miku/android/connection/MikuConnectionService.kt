package com.cxmlo.miku.android.connection

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.cxmlo.miku.android.MainActivity
import com.cxmlo.miku.android.data.AgentNotice
import com.cxmlo.miku.android.data.MikuClient
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.launch

class MikuConnectionService : Service() {
    private val serviceScope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private var notificationJob: Job? = null

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel(this)
        startForeground(NOTIFICATION_ID, connectionNotification(this, "Conectando con el escritorio…"))
        notificationJob = serviceScope.launch {
            var lastNoticeId = MikuClient.state.value.notices.firstOrNull()?.id
            var lastDownload = MikuClient.state.value.pendingDownload
            var lastPhoneCommand = MikuClient.state.value.pendingPhoneCommand
            MikuClient.state.collect { state ->
                val message = if (state.connected) "Conectado a ${state.pcName}" else state.status
                getSystemService(NotificationManager::class.java)
                    .notify(NOTIFICATION_ID, connectionNotification(this@MikuConnectionService, message))

                val newNotices = state.notices.takeWhile { it.id != lastNoticeId }.asReversed()
                newNotices.forEach { notifyAgentEvent(this@MikuConnectionService, it) }
                state.notices.firstOrNull()?.let { lastNoticeId = it.id }

                state.pendingDownload
                    ?.takeIf { it != lastDownload }
                    ?.let { notifyDownload(this@MikuConnectionService, it) }
                lastDownload = state.pendingDownload

                state.pendingPhoneCommand
                    ?.takeIf { it != lastPhoneCommand }
                    ?.let { notifyPhoneCommand(this@MikuConnectionService, it.action) }
                lastPhoneCommand = state.pendingPhoneCommand
            }
        }
        MikuClient.connect(this)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            MikuClient.disconnect()
            stopForeground(STOP_FOREGROUND_REMOVE)
            stopSelf()
            return START_NOT_STICKY
        }
        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        notificationJob?.cancel()
        serviceScope.cancel()
        super.onDestroy()
    }

    companion object {
        private const val CHANNEL_ID = "miku_connection"
        private const val NOTIFICATION_ID = 4101
        private const val ACTION_STOP = "com.cxmlo.miku.android.STOP_CONNECTION"

        fun stop(context: Context) {
            context.startService(Intent(context, MikuConnectionService::class.java).setAction(ACTION_STOP))
        }

        fun notifyAgentEvent(context: Context?, notice: AgentNotice) {
            if (context == null) return
            // Evitar spam de notificaciones automáticas de actividad de IDE / logs
            if (notice.agent.equals("antigravity", ignoreCase = true) || notice.event.contains("Active", ignoreCase = true)) {
                return
            }
            notify(
                context,
                notice.id.hashCode(),
                "${notice.agent}: ${notice.event}",
                notice.detail.ifBlank { "Hay una actualización del agente." },
            )
        }

        fun notifyDownload(context: Context?, fileName: String) {
            if (context == null) return
            notify(context, fileName.hashCode(), "Archivo listo en Miku", "Toca Control para guardarlo: $fileName")
        }

        fun notifyPhoneCommand(context: Context?, action: String) {
            if (context == null) return
            notify(context, action.hashCode(), "Miku solicita una acción", "Abre la app para revisar: $action")
        }

        private fun notify(context: Context, id: Int, title: String, detail: String) {
            createNotificationChannel(context)
            val notification = NotificationCompat.Builder(context, CHANNEL_ID)
                .setSmallIcon(android.R.drawable.stat_notify_chat)
                .setContentTitle(title)
                .setContentText(detail)
                .setStyle(NotificationCompat.BigTextStyle().bigText(detail))
                .setAutoCancel(true)
                .setContentIntent(mainPendingIntent(context))
                .build()
            runCatching {
                NotificationManagerCompat.from(context).notify(id, notification)
            }
        }

        private fun connectionNotification(context: Context, message: String): Notification =
            NotificationCompat.Builder(context, CHANNEL_ID)
                .setSmallIcon(android.R.drawable.stat_notify_sync)
                .setContentTitle("Miku Mobile")
                .setContentText(message)
                .setOngoing(true)
                .setContentIntent(mainPendingIntent(context))
                .build()

        private fun mainPendingIntent(context: Context): PendingIntent =
            PendingIntent.getActivity(
                context,
                0,
                Intent(context, MainActivity::class.java),
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
            )

        private fun createNotificationChannel(context: Context) {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                val channel = NotificationChannel(
                    CHANNEL_ID,
                    "Conexión con Miku",
                    NotificationManager.IMPORTANCE_DEFAULT,
                )
                context.getSystemService(NotificationManager::class.java).createNotificationChannel(channel)
            }
        }
    }
}
