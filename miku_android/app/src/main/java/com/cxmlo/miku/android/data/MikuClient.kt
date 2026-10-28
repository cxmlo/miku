package com.cxmlo.miku.android.data

import android.Manifest
import android.app.NotificationManager
import android.app.WallpaperManager
import android.content.ContentResolver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.content.pm.ApplicationInfo
import android.content.pm.PackageManager
import android.media.RingtoneManager
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.net.Uri
import android.os.BatteryManager
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.provider.CallLog
import android.provider.OpenableColumns
import android.provider.Telephony
import android.telephony.SmsManager
import androidx.core.content.ContextCompat
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.HttpUrl
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import okio.BufferedSink
import okio.source
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.UUID
import java.util.concurrent.TimeUnit
import kotlin.math.min

data class ChatMessage(
    val id: String,
    val text: String,
    val sender: String,
)

data class AgentOption(
    val id: String,
    val name: String,
)

data class AgentNotice(
    val id: String,
    val agent: String,
    val event: String,
    val detail: String,
)

data class PhoneCommand(
    val action: String,
    val extras: JSONObject,
)

data class MikuState(
    val serverIp: String = "",
    val tunnelUrl: String = "",
    val usingTunnel: Boolean = false,
    val pcName: String = "",
    val connected: Boolean = false,
    val status: String = "Desconectado",
    val error: String? = null,
    val messages: List<ChatMessage> = emptyList(),
    val agents: List<AgentOption> = listOf(AgentOption("miku", "Miku")),
    val notices: List<AgentNotice> = emptyList(),
    val clipboardText: String? = null,
    val pendingDownload: String? = null,
    val pendingPhoneCommand: PhoneCommand? = null,
)

object MikuClient {
    private val http = OkHttpClient.Builder()
        .connectTimeout(6, TimeUnit.SECONDS)
        .readTimeout(45, TimeUnit.SECONDS)
        .pingInterval(20, TimeUnit.SECONDS)
        .build()
    private val _state = MutableStateFlow(MikuState())
    val state: StateFlow<MikuState> = _state.asStateFlow()
    private var webSocket: WebSocket? = null
    private var credentials: DeviceCredentials? = null
    private var activeEndpoint: String = ""
    private var appContext: Context? = null
    private var reconnectAttempt = 0
    private var reconnectRunnable: Runnable? = null
    private val mainHandler = android.os.Handler(android.os.Looper.getMainLooper())

    private fun resolveBestEndpoint(ip: String, tunnelUrl: String): Pair<String, Boolean> {
        val candidates = buildList {
            if (ip.isNotBlank() && !ip.startsWith("http")) add(baseUrl(ip) to false)
            if (tunnelUrl.isNotBlank()) add(baseUrl(tunnelUrl) to true)
            if (ip.startsWith("http")) add(baseUrl(ip) to ip.contains("trycloudflare.com"))
        }.distinctBy { it.first }

        for ((candidate, isTunnel) in candidates) {
            try {
                val req = Request.Builder().url("$candidate/api/desktop/info").get().build()
                http.newCall(req).execute().use { resp ->
                    if (resp.isSuccessful) {
                        return candidate to isTunnel
                    }
                }
            } catch (_: Exception) {
                // Probar siguiente candidato (ej. caer a Cloudflare Tunnel en 4G/5G)
            }
        }
        return if (tunnelUrl.isNotBlank()) baseUrl(tunnelUrl) to true else baseUrl(ip) to false
    }

    suspend fun pair(context: Context, link: PairingLink): DeviceCredentials = withContext(Dispatchers.IO) {
        appContext = context.applicationContext
        val (resolvedBase, usingTunnel) = resolveBestEndpoint(link.host, link.tunnelUrl)
        activeEndpoint = resolvedBase
        val info = request(resolvedBase, "/api/desktop/info")
        val deviceId = UUID.randomUUID().toString()
        val publicKey = java.security.MessageDigest.getInstance("SHA-256")
            .digest("$deviceId${System.currentTimeMillis()}".toByteArray())
            .joinToString("") { "%02x".format(it) }
        val payload = JSONObject()
            .put("session_id", link.sessionId)
            .put("device_id", deviceId)
            .put("name", android.os.Build.MODEL.ifBlank { "Miku Android" })
            .put("public_key", publicKey)
        val response = request(resolvedBase, "/api/pair/confirm", "POST", payload)
        check(response.optString("status") == "ok") {
            response.optString("detail", "No se pudo completar la vinculación.")
        }

        val effectiveTunnel = link.tunnelUrl.ifBlank { info.optString("tunnel_url", "") }
        val credentials = DeviceCredentials(
            serverIp = link.host,
            deviceId = deviceId,
            pcName = info.optString("hostname", link.host),
            tunnelUrl = effectiveTunnel,
        )
        DeviceStore(context).save(
            credentials.serverIp,
            credentials.deviceId,
            credentials.pcName,
            credentials.tunnelUrl,
        )
        this@MikuClient.credentials = credentials
        _state.update {
            it.copy(
                serverIp = credentials.serverIp,
                tunnelUrl = credentials.tunnelUrl,
                usingTunnel = usingTunnel,
                pcName = credentials.pcName,
                error = null,
                status = "Vinculado; conectando…",
            )
        }
        credentials
    }

    fun connect(context: Context) {
        appContext = context.applicationContext
        val saved = DeviceStore(context).read() ?: return
        credentials = saved
        _state.update {
            it.copy(
                serverIp = saved.serverIp,
                tunnelUrl = saved.tunnelUrl,
                pcName = saved.pcName,
                status = "Conectando…",
                error = null,
            )
        }
        reconnectRunnable?.let {
            mainHandler.removeCallbacks(it)
            reconnectRunnable = null
        }
        webSocket?.cancel()
        ioScope.launch {
            val (bestBase, usingTunnel) = resolveBestEndpoint(saved.serverIp, saved.tunnelUrl)
            activeEndpoint = bestBase
            _state.update { it.copy(usingTunnel = usingTunnel) }
            webSocket = http.newWebSocket(webSocketRequest(saved, bestBase), listener(saved))
        }
    }

    fun disconnect() {
        reconnectRunnable?.let(mainHandler::removeCallbacks)
        reconnectRunnable = null
        reconnectAttempt = 0
        webSocket?.close(1000, "Miku disconnected")
        webSocket = null
        credentials = null
        _state.update { it.copy(connected = false, status = "Desconectado") }
    }

    fun unpair(context: Context) {
        disconnect()
        DeviceStore(context).clear()
        _state.value = MikuState()
    }

    private fun currentBaseUrl(saved: DeviceCredentials): String =
        activeEndpoint.takeIf(String::isNotBlank) ?: baseUrl(saved.serverIp)

    suspend fun sendChat(text: String, agent: AgentOption) = withContext(Dispatchers.IO) {
        val saved = requireCredentials()
        val payload = JSONObject()
            .put("message", text)
            .put("source", "mobile")
            .put("agent_id", agent.id)
            .put("agent_name", agent.name)
        request(currentBaseUrl(saved), "/chat", "POST", payload, saved.deviceId)
    }

    suspend fun uploadFile(context: Context, uri: Uri) = withContext(Dispatchers.IO) {
        val saved = requireCredentials()
        val resolver = context.contentResolver
        val fileName = displayName(resolver, uri)
        val mimeType = resolver.getType(uri)?.toMediaTypeOrNull()
            ?: "application/octet-stream".toMediaTypeOrNull()
        val body = object : RequestBody() {
            override fun contentType() = mimeType

            override fun contentLength(): Long =
                resolver.openAssetFileDescriptor(uri, "r")?.use { it.length } ?: -1L

            override fun writeTo(sink: BufferedSink) {
                val input = resolver.openInputStream(uri)
                    ?: throw IOException("No se pudo leer el archivo seleccionado.")
                input.use { sink.writeAll(it.source()) }
            }
        }
        val multipart = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("file", fileName, body)
            .build()
        val request = Request.Builder()
            .url(currentBaseUrl(saved) + "/api/device/upload")
            .header("X-Device-Id", saved.deviceId)
            .post(multipart)
            .build()
        execute(request)
    }

    suspend fun lockPc() = withContext(Dispatchers.IO) {
        val saved = requireCredentials()
        val request = Request.Builder()
            .url(currentBaseUrl(saved) + "/api/device/lock")
            .header("X-Device-Id", saved.deviceId)
            .post(JSONObject().toString().toRequestBody(JSON))
            .build()
        execute(request)
    }

    suspend fun sendClipboard(text: String) = withContext(Dispatchers.IO) {
        val saved = requireCredentials()
        request(
            currentBaseUrl(saved),
            "/api/device/clipboard",
            "POST",
            JSONObject().put("text", text),
            saved.deviceId,
        )
    }

    suspend fun downloadFile(context: Context, fileName: String, destination: Uri) =
        withContext(Dispatchers.IO) {
            val saved = requireCredentials()
            val url = currentBaseUrl(saved) + "/api/temp_media/${Uri.encode(fileName)}"
            val request = Request.Builder().url(url).get().build()
            val response = executeRaw(request)
            val input = response.body?.byteStream()
                ?: throw IOException("El servidor no devolvió el archivo.")
            val output = context.contentResolver.openOutputStream(destination)
                ?: throw IOException("No se pudo guardar el archivo en el destino elegido.")
            input.use { source -> output.use { target -> source.copyTo(target) } }
            _state.update { it.copy(pendingDownload = null) }
        }

    fun forwardPhoneNotification(id: String, app: String, title: String, body: String, time: String) {
        val saved = credentials ?: return
        ioScope.launch {
            runCatching {
                val notifObj = JSONObject()
                    .put("id", id)
                    .put("app", app)
                    .put("title", title)
                    .put("body", body)
                    .put("time", time)
                val payload = JSONObject().put("notification", notifObj)
                request(currentBaseUrl(saved), "/api/device/telemetry", "POST", payload, saved.deviceId)
            }
        }
    }

    suspend fun pushDeviceTelemetry(context: Context) = withContext(Dispatchers.IO) {
        val saved = credentials ?: return@withContext
        val payload = JSONObject()

        // 1. Batería y carga
        runCatching {
            val bm = context.getSystemService(Context.BATTERY_SERVICE) as? BatteryManager
            val pct = bm?.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
            val sticky = context.registerReceiver(null, IntentFilter(Intent.ACTION_BATTERY_CHANGED))
            val status = sticky?.getIntExtra(BatteryManager.EXTRA_STATUS, -1) ?: -1
            val charging = status == BatteryManager.BATTERY_STATUS_CHARGING || status == BatteryManager.BATTERY_STATUS_FULL
            if (pct != null && pct in 0..100) payload.put("battery", pct)
            payload.put("charging", charging)
        }

        // 2. Señal (Wi-Fi vs Datos Móviles 4G/5G)
        runCatching {
            val cm = context.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager
            val caps = cm?.getNetworkCapabilities(cm.activeNetwork)
            val sig = when {
                caps == null -> "Sin red"
                caps.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) -> "Wi-Fi"
                caps.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) -> "Datos Móviles (4G/5G)"
                else -> "En línea"
            }
            payload.put("signal", sig)
        }

        // 3. Mensajes SMS recientes (si tiene permiso READ_SMS)
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.READ_SMS) == PackageManager.PERMISSION_GRANTED) {
            runCatching {
                val threadsMap = linkedMapOf<String, JSONObject>()
                context.contentResolver.query(
                    Telephony.Sms.CONTENT_URI,
                    arrayOf(Telephony.Sms._ID, Telephony.Sms.THREAD_ID, Telephony.Sms.ADDRESS, Telephony.Sms.BODY, Telephony.Sms.DATE, Telephony.Sms.TYPE),
                    null,
                    null,
                    "${Telephony.Sms.DATE} DESC LIMIT 40"
                )?.use { cursor ->
                    val idIdx = cursor.getColumnIndex(Telephony.Sms._ID)
                    val thIdx = cursor.getColumnIndex(Telephony.Sms.THREAD_ID)
                    val addrIdx = cursor.getColumnIndex(Telephony.Sms.ADDRESS)
                    val bodyIdx = cursor.getColumnIndex(Telephony.Sms.BODY)
                    val dateIdx = cursor.getColumnIndex(Telephony.Sms.DATE)
                    val typeIdx = cursor.getColumnIndex(Telephony.Sms.TYPE)
                    val fmt = SimpleDateFormat("HH:mm", Locale.getDefault())
                    while (cursor.moveToNext()) {
                        val threadId = cursor.getString(thIdx) ?: continue
                        val address = cursor.getString(addrIdx) ?: "Desconocido"
                        val body = cursor.getString(bodyIdx) ?: ""
                        val dateMs = cursor.getLong(dateIdx)
                        val type = cursor.getInt(typeIdx)
                        val threadObj = threadsMap.getOrPut(threadId) {
                            JSONObject()
                                .put("id", threadId)
                                .put("name", address)
                                .put("unread", 0)
                                .put("messages", JSONArray())
                        }
                        threadObj.getJSONArray("messages").put(
                            JSONObject()
                                .put("id", cursor.getString(idIdx) ?: UUID.randomUUID().toString())
                                .put("dir", if (type == Telephony.Sms.MESSAGE_TYPE_INBOX) "in" else "out")
                                .put("text", body)
                                .put("time", fmt.format(Date(dateMs)))
                        )
                    }
                }
                val threadsArray = JSONArray()
                threadsMap.values.forEach { threadsArray.put(it) }
                payload.put("messages", threadsArray)
            }
        }

        // 4. Historial de llamadas (si tiene permiso READ_CALL_LOG)
        if (ContextCompat.checkSelfPermission(context, Manifest.permission.READ_CALL_LOG) == PackageManager.PERMISSION_GRANTED) {
            runCatching {
                val callsArr = JSONArray()
                context.contentResolver.query(
                    CallLog.Calls.CONTENT_URI,
                    arrayOf(CallLog.Calls._ID, CallLog.Calls.NUMBER, CallLog.Calls.CACHED_NAME, CallLog.Calls.TYPE, CallLog.Calls.DATE),
                    null,
                    null,
                    "${CallLog.Calls.DATE} DESC LIMIT 25"
                )?.use { cursor ->
                    val idIdx = cursor.getColumnIndex(CallLog.Calls._ID)
                    val numIdx = cursor.getColumnIndex(CallLog.Calls.NUMBER)
                    val nameIdx = cursor.getColumnIndex(CallLog.Calls.CACHED_NAME)
                    val typeIdx = cursor.getColumnIndex(CallLog.Calls.TYPE)
                    val dateIdx = cursor.getColumnIndex(CallLog.Calls.DATE)
                    val fmt = SimpleDateFormat("HH:mm", Locale.getDefault())
                    while (cursor.moveToNext()) {
                        val num = cursor.getString(numIdx) ?: "Desconocido"
                        val name = cursor.getString(nameIdx)?.takeIf(String::isNotBlank) ?: num
                        val type = cursor.getInt(typeIdx)
                        val dir = when (type) {
                            CallLog.Calls.MISSED_TYPE -> "missed"
                            CallLog.Calls.OUTGOING_TYPE -> "out"
                            else -> "in"
                        }
                        callsArr.put(
                            JSONObject()
                                .put("id", cursor.getString(idIdx) ?: UUID.randomUUID().toString())
                                .put("name", name)
                                .put("number", num)
                                .put("dir", dir)
                                .put("time", fmt.format(Date(cursor.getLong(dateIdx))))
                        )
                    }
                }
                payload.put("calls", callsArr)
            }
        }

        // 5. Aplicaciones instaladas del usuario
        runCatching {
            val pm = context.packageManager
            val appsArr = JSONArray()
            val installed = pm.getInstalledApplications(PackageManager.GET_META_DATA)
                .filter { (it.flags and ApplicationInfo.FLAG_SYSTEM) == 0 && pm.getLaunchIntentForPackage(it.packageName) != null }
                .take(40)
            for (appInfo in installed) {
                val label = pm.getApplicationLabel(appInfo).toString()
                appsArr.put(
                    JSONObject()
                        .put("id", appInfo.packageName)
                        .put("name", label)
                        .put("category", "Android App")
                )
            }
            payload.put("apps", appsArr)
        }

        runCatching {
            request(currentBaseUrl(saved), "/api/device/telemetry", "POST", payload, saved.deviceId)
        }
    }

    fun clearPendingDownload() {
        _state.update { it.copy(pendingDownload = null) }
    }

    fun clearPhoneCommand() {
        _state.update { it.copy(pendingPhoneCommand = null) }
    }

    fun clearClipboardText() {
        _state.update { it.copy(clipboardText = null) }
    }

    private fun listener(saved: DeviceCredentials) = object : WebSocketListener() {
        override fun onOpen(webSocket: WebSocket, response: Response) {
            reconnectAttempt = 0
            this@MikuClient.webSocket = webSocket
            val modeTag = if (_state.value.usingTunnel) " (Túnel 4G/5G)" else " (Wi-Fi Local)"
            _state.update {
                it.copy(connected = true, status = "Conectado a ${saved.pcName}$modeTag", error = null)
            }
            ioScope.launch {
                runCatching { loadHistory(saved) }
                    .onFailure { _state.update { state -> state.copy(error = it.message) } }
                runCatching { loadAgents(saved) }
                    .onFailure { _state.update { state -> state.copy(error = it.message) } }
                appContext?.let { ctx ->
                    runCatching { pushDeviceTelemetry(ctx) }
                }
            }
        }

        override fun onMessage(webSocket: WebSocket, text: String) {
            runCatching { JSONObject(text) }
                .onSuccess(::handleMessage)
                .onFailure {
                    _state.update { state -> state.copy(error = "Se recibió un mensaje no válido del escritorio.") }
                }
        }

        override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
            if (this@MikuClient.webSocket !== webSocket) return
            markDisconnected(saved)
            scheduleReconnect(saved)
        }

        override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
            if (this@MikuClient.webSocket !== webSocket) return
            if (response?.code == 403) {
                appContext?.let { unpair(it) } ?: disconnect()
                markDisconnected(
                    saved,
                    "Dispositivo desvinculado por Miku Desktop.",
                )
            } else {
                markDisconnected(saved, t.message ?: "No se pudo conectar con el escritorio.")
                scheduleReconnect(saved)
            }
        }
    }

    private fun markDisconnected(saved: DeviceCredentials, error: String? = null) {
        if (credentials?.deviceId != saved.deviceId) return
        _state.update {
            it.copy(
                connected = false,
                status = "Sin conexión; reintentando…",
                error = error,
            )
        }
    }

    private fun scheduleReconnect(saved: DeviceCredentials) {
        if (credentials?.deviceId != saved.deviceId || reconnectRunnable != null) return
        val delay = min(3_000L * (1L shl reconnectAttempt.coerceAtMost(4)), 30_000L)
        reconnectAttempt += 1
        reconnectRunnable = Runnable {
            reconnectRunnable = null
            if (credentials?.deviceId == saved.deviceId) {
                ioScope.launch {
                    val (bestBase, usingTunnel) = resolveBestEndpoint(saved.serverIp, saved.tunnelUrl)
                    activeEndpoint = bestBase
                    _state.update { it.copy(usingTunnel = usingTunnel) }
                    webSocket = http.newWebSocket(webSocketRequest(saved, bestBase), listener(saved))
                }
            }
        }.also { mainHandler.postDelayed(it, delay) }
    }

    private fun handleMessage(message: JSONObject) {
        when {
            message.has("id") && message.has("text") && message.has("sender") -> {
                val chatMessage = ChatMessage(
                    id = message.optString("id", UUID.randomUUID().toString()),
                    text = message.optString("text"),
                    sender = message.optString("sender"),
                )
                _state.update { state ->
                    if (state.messages.any { it.id == chatMessage.id }) state
                    else state.copy(messages = state.messages + chatMessage)
                }
            }
            message.optString("type") == "agent_hook" -> {
                val notice = AgentNotice(
                    id = UUID.randomUUID().toString(),
                    agent = message.optString("agent", "Agente"),
                    event = message.optString("event", "Notificación"),
                    detail = message.optString("tool").ifBlank { message.optString("prompt") },
                )
                _state.update { it.copy(notices = (listOf(notice) + it.notices).take(50)) }
            }
            message.optString("type") == "miku_link_unpaired" || (message.optString("type") == "ui_command" && message.optString("action") == "unpair") -> {
                appContext?.let { unpair(it) } ?: disconnect()
            }
            message.optString("type") == "ui_command" -> handleUiCommand(message)
        }
    }

    private fun handleUiCommand(message: JSONObject) {
        val ctx = appContext
        when (message.optString("action")) {
            "status_update" -> {
                val text = message.optString("text", "En línea")
                _state.update { it.copy(status = text) }
            }
            "download_file" -> {
                val filename = message.optString("filename").takeIf(String::isNotBlank) ?: return
                _state.update { it.copy(pendingDownload = filename) }
            }
            "ejecutar_intent_android" -> {
                val action = message.optString("intent_action").takeIf(String::isNotBlank) ?: return
                val extras = message.optJSONObject("extras") ?: JSONObject()
                _state.update { it.copy(pendingPhoneCommand = PhoneCommand(action, extras)) }
            }
            "sync_clipboard" -> {
                val text = message.optString("text").takeIf(String::isNotBlank) ?: return
                _state.update { it.copy(clipboardText = text) }
            }
            "ring_phone" -> {
                if (ctx != null) {
                    runCatching {
                        val ringUri = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
                            ?: RingtoneManager.getDefaultUri(RingtoneManager.TYPE_RINGTONE)
                        RingtoneManager.getRingtone(ctx, ringUri)?.play()
                        val vib = ctx.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
                        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                            vib?.vibrate(VibrationEffect.createOneShot(1800, VibrationEffect.DEFAULT_AMPLITUDE))
                        } else {
                            @Suppress("DEPRECATION")
                            vib?.vibrate(1800)
                        }
                    }
                }
            }
            "set_dnd" -> {
                if (ctx != null) {
                    val enabled = message.optBoolean("enabled", false)
                    runCatching {
                        val nm = ctx.getSystemService(Context.NOTIFICATION_SERVICE) as? NotificationManager
                        if (nm != null && nm.isNotificationPolicyAccessGranted) {
                            nm.setInterruptionFilter(
                                if (enabled) NotificationManager.INTERRUPTION_FILTER_NONE
                                else NotificationManager.INTERRUPTION_FILTER_ALL
                            )
                        }
                    }
                }
            }
            "dial_call" -> {
                if (ctx != null) {
                    val number = message.optString("number").trim()
                    if (number.isNotEmpty()) {
                        runCatching {
                            val hasCallPerm = ContextCompat.checkSelfPermission(ctx, Manifest.permission.CALL_PHONE) == PackageManager.PERMISSION_GRANTED
                            val act = if (hasCallPerm) Intent.ACTION_CALL else Intent.ACTION_DIAL
                            val dialIntent = Intent(act, Uri.parse("tel:${Uri.encode(number)}")).apply {
                                addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                            }
                            ctx.startActivity(dialIntent)
                        }
                    }
                }
            }
            "send_sms" -> {
                if (ctx != null) {
                    val recipient = message.optString("recipient").ifBlank { message.optString("thread_id") }.trim()
                    val text = message.optString("text").trim()
                    if (recipient.isNotEmpty() && text.isNotEmpty()) {
                        runCatching {
                            if (ContextCompat.checkSelfPermission(ctx, Manifest.permission.SEND_SMS) == PackageManager.PERMISSION_GRANTED) {
                                @Suppress("DEPRECATION")
                                val sms = SmsManager.getDefault()
                                sms.sendTextMessage(recipient, null, text, null, null)
                            } else {
                                val smsIntent = Intent(Intent.ACTION_SENDTO, Uri.parse("smsto:${Uri.encode(recipient)}")).apply {
                                    putExtra("sms_body", text)
                                    addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                                }
                                ctx.startActivity(smsIntent)
                            }
                        }
                    }
                }
            }
            "open_mobile_app" -> {
                if (ctx != null) {
                    val pkg = message.optString("app_id").trim()
                    if (pkg.isNotEmpty()) {
                        runCatching {
                            val launch = ctx.packageManager.getLaunchIntentForPackage(pkg)
                            if (launch != null) {
                                launch.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                                ctx.startActivity(launch)
                            }
                        }
                    }
                }
            }
            "sync_phone_wallpaper" -> {
                if (ctx != null) {
                    val saved = credentials ?: return
                    val relUrl = message.optString("url", "/api/link/phone_wallpaper")
                    ioScope.launch {
                        runCatching {
                            val fullUrl = currentBaseUrl(saved) + relUrl
                            val req = Request.Builder().url(fullUrl).header("X-Device-Id", saved.deviceId).get().build()
                            val resp = executeRaw(req)
                            resp.body?.byteStream()?.use { stream ->
                                WallpaperManager.getInstance(ctx).setStream(stream)
                            }
                        }
                    }
                }
            }
            "agent_reply" -> addMessage(message)
        }
    }

    private fun addMessage(message: JSONObject) {
        val chatMessage = ChatMessage(
            id = message.optString("id", UUID.randomUUID().toString()),
            text = message.optString("text"),
            sender = message.optString("sender", "Miku"),
        )
        _state.update { state ->
            if (state.messages.any { it.id == chatMessage.id }) state
            else state.copy(messages = state.messages + chatMessage)
        }
    }

    private suspend fun loadHistory(saved: DeviceCredentials) {
        val result = request(currentBaseUrl(saved), "/history", deviceId = saved.deviceId)
        val items = result.optJSONArray("messages") ?: JSONArray()
        val history = buildList {
            for (index in 0 until items.length()) {
                val message = items.optJSONObject(index) ?: continue
                val text = message.optString("text").takeIf(String::isNotBlank) ?: continue
                add(
                    ChatMessage(
                        id = message.optString("id", index.toString()),
                        text = text,
                        sender = message.optString("sender", "Miku"),
                    ),
                )
            }
        }
        _state.update { current ->
            current.copy(messages = (history + current.messages).distinctBy(ChatMessage::id))
        }
    }

    private suspend fun loadAgents(saved: DeviceCredentials) {
        val result = request(currentBaseUrl(saved), "/api/agents", deviceId = saved.deviceId)
        val items = result.optJSONArray("agents") ?: JSONArray()
        val agents = buildList {
            add(AgentOption("miku", "Miku"))
            for (index in 0 until items.length()) {
                val item = items.optJSONObject(index) ?: continue
                val id = item.optString("id").takeIf(String::isNotBlank) ?: continue
                if (id != "miku") add(AgentOption(id, item.optString("name", id)))
            }
        }.distinctBy(AgentOption::id)
        _state.update { it.copy(agents = agents) }
    }

    private fun webSocketRequest(saved: DeviceCredentials, resolvedBase: String = currentBaseUrl(saved)): Request {
        val httpUrl = resolvedBase.toHttpUrl()
        val httpEndpoint: HttpUrl = httpUrl.newBuilder()
            .addPathSegment("ws")
            .addQueryParameter("device_id", saved.deviceId)
            .build()
        val wsUrl = httpEndpoint.toString().replaceFirst(
            if (httpUrl.isHttps) "https://" else "http://",
            if (httpUrl.isHttps) "wss://" else "ws://",
        )
        return Request.Builder()
            .url(wsUrl)
            .header("X-Device-Id", saved.deviceId)
            .build()
    }

    private suspend fun request(
        base: String,
        path: String,
        method: String = "GET",
        payload: JSONObject? = null,
        deviceId: String? = credentials?.deviceId,
    ): JSONObject {
        val url = base + path
        val builder = Request.Builder().url(url)
        if (deviceId != null) builder.header("X-Device-Id", deviceId)
        when (method) {
            "POST" -> builder.post((payload ?: JSONObject()).toString().toRequestBody(JSON))
            else -> builder.get()
        }
        return execute(builder.build())
    }

    private suspend fun execute(request: Request): JSONObject {
        val response = executeRaw(request)
        val text = response.body?.string().orEmpty()
        val json = runCatching { JSONObject(text) }.getOrElse { JSONObject() }
        if (!response.isSuccessful) {
            throw IOException(json.optString("detail").ifBlank { "Error HTTP ${response.code}" })
        }
        return json
    }

    private suspend fun executeRaw(request: Request): Response = withContext(Dispatchers.IO) {
        val response = http.newCall(request).execute()
        if (!response.isSuccessful) {
            val body = response.body?.string().orEmpty()
            val detail = runCatching { JSONObject(body).optString("detail") }.getOrNull()
            response.close()
            throw IOException(detail?.takeIf(String::isNotBlank) ?: "Error HTTP ${response.code}")
        }
        response
    }

    private fun requireCredentials(): DeviceCredentials =
        credentials ?: throw IllegalStateException("Vincula primero la app con Miku Desktop.")

    private fun displayName(resolver: ContentResolver, uri: Uri): String {
        resolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { cursor ->
            if (cursor.moveToFirst()) {
                val column = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                if (column >= 0) return cursor.getString(column)
            }
        }
        return uri.lastPathSegment?.substringAfterLast('/') ?: "miku-upload"
    }

    private fun baseUrl(ip: String): String {
        val normalized = ip.trim().removeSuffix("/")
        return when {
            normalized.startsWith("https://") || normalized.startsWith("http://") -> normalized
            normalized.endsWith(".trycloudflare.com") -> "https://$normalized"
            normalized.contains(':') && !normalized.startsWith("[") && normalized.count { it == ':' } > 1 ->
                "http://[$normalized]:8000"
            normalized.substringAfterLast(':').toIntOrNull() != null -> "http://$normalized"
            else -> "http://$normalized:8000"
        }
    }

    private val ioScope = kotlinx.coroutines.CoroutineScope(
        kotlinx.coroutines.SupervisorJob() + Dispatchers.IO,
    )
    private val JSON = "application/json; charset=utf-8".toMediaTypeOrNull()

}
