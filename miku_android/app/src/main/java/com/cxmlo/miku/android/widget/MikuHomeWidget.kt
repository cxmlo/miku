package com.cxmlo.miku.android.widget

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.widget.RemoteViews
import com.cxmlo.miku.android.MainActivity
import com.cxmlo.miku.android.R
import com.cxmlo.miku.android.data.MikuClient
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch

/**
 * MikuHomeWidget (2x2 and 4x2 Native Android Home Screen Widgets)
 * Displays live PC connection status, active agent, and quick actions (Lock PC, Sync Clipboard, Open Chat).
 */
open class BaseMikuWidgetProvider(private val layoutResId: Int) : AppWidgetProvider() {

    override fun onUpdate(
        context: Context,
        appWidgetManager: AppWidgetManager,
        appWidgetIds: IntArray
    ) {
        for (appWidgetId in appWidgetIds) {
            updateWidget(context, appWidgetManager, appWidgetId, layoutResId)
        }
    }

    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)
        if (intent.action == ACTION_WIDGET_CMD) {
            val cmd = intent.getStringExtra(EXTRA_CMD).orEmpty()
            CoroutineScope(Dispatchers.IO).launch {
                runCatching {
                    when (cmd) {
                        "lock_pc" -> MikuClient.lockPc()
                        "telemetry" -> MikuClient.pushDeviceTelemetry(context)
                    }
                }
                refreshAllWidgets(context)
            }
        }
    }

    companion object {
        const val ACTION_WIDGET_CMD = "com.cxmlo.miku.android.WIDGET_ACTION"
        const val EXTRA_CMD = "cmd"

        fun updateWidget(
            context: Context,
            manager: AppWidgetManager,
            widgetId: Int,
            layoutId: Int
        ) {
            val state = MikuClient.state.value
            val views = RemoteViews(context.packageName, layoutId)
            val statusLabel = if (state.connected) "● EN LÍNEA · ${state.pcName}" else "● DESCONECTADO"
            views.setTextViewText(R.id.widget_status_text, statusLabel)

            val openAppIntent = Intent(context, MainActivity::class.java)
            val openPending = PendingIntent.getActivity(
                context,
                0,
                openAppIntent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            views.setOnClickPendingIntent(R.id.widget_btn_open, openPending)

            val lockIntent = Intent(context, MikuWidget4x2Receiver::class.java).apply {
                action = ACTION_WIDGET_CMD
                putExtra(EXTRA_CMD, "lock_pc")
            }
            val lockPending = PendingIntent.getBroadcast(
                context,
                1,
                lockIntent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            views.setOnClickPendingIntent(R.id.widget_btn_lock, lockPending)

            manager.updateAppWidget(widgetId, views)
        }

        fun refreshAllWidgets(context: Context) {
            val manager = AppWidgetManager.getInstance(context)
            val ids2x2 = manager.getAppWidgetIds(ComponentName(context, MikuWidget2x2Receiver::class.java))
            ids2x2.forEach { updateWidget(context, manager, it, R.layout.miku_widget_2x2) }
            val ids4x2 = manager.getAppWidgetIds(ComponentName(context, MikuWidget4x2Receiver::class.java))
            ids4x2.forEach { updateWidget(context, manager, it, R.layout.miku_widget_4x2) }
        }
    }
}

class MikuWidget2x2Receiver : BaseMikuWidgetProvider(R.layout.miku_widget_2x2)
class MikuWidget4x2Receiver : BaseMikuWidgetProvider(R.layout.miku_widget_4x2)
