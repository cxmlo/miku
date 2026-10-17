package com.cxmlo.miku.android.connection

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.core.content.ContextCompat
import com.cxmlo.miku.android.data.DeviceStore

class MikuBootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent?) {
        if (intent?.action != Intent.ACTION_BOOT_COMPLETED) return
        if (DeviceStore(context).read() == null) return

        ContextCompat.startForegroundService(
            context,
            Intent(context, MikuConnectionService::class.java),
        )
    }
}
