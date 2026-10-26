package com.cxmlo.miku.android.data

import android.content.ContentResolver
import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.update
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
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(45, TimeUnit.SECONDS)
        .pingInterval(20, TimeUnit.SECONDS)
        .build()
    private val _state = MutableStateFlow(MikuState())
    val state: StateFlow<MikuState> = _state.asStateFlow()
    private var webSocket: WebSocket? = null
    private var credentials: DeviceCredentials? = null
    private var appContext: Context? = null
    private var reconnectAttempt = 0
    private var reconnectRunnable: Runnable? = null
    private val mainHandler = android.os.Handler(android.os.Looper.getMainLooper())

    suspend fun pair(context: Context, link: PairingLink): DeviceCredentials = withContext(Dispatchers.IO) {
        val baseUrl = baseUrl(link.host)
        val info = request(baseUrl, "/api/desktop/info")
        val deviceId = UUID.randomUUID().toString()
        val publicKey = java.security.MessageDigest.getInstance("SHA-256")
            .digest("$deviceId${System.currentTimeMillis()}".toByteArray())
            .joinToString("") { "%02x".format(it) }
        val payload = JSONObject()
            .put("session_id", link.sessionId)
            .put("device_id", deviceId)
            .put("name", android.os.Build.MODEL.ifBlank { "Miku Android" })
            .put("public_key", publicKey)
        val response = request(baseUrl, "/api/pair/confirm", "POST", payload)
        check(response.optString("status") == "ok") {
            response.optString("detail", "No se pudo completar la vinculación.")
        }

        val credentials = DeviceCredentials(
            serverIp = link.host,
            deviceId = deviceId,
            pcName = info.optString("hostname", link.host),
        )
        DeviceStore(context).save(credentials.serverIp, credentials.deviceId, credentials.pcName)
        this@MikuClient.credentials = credentials
        _state.update {
            it.copy(
                serverIp = credentials.serverIp,
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
        webSocket = http.newWebSocket(webSocketRequest(saved), listener(saved))
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

    suspend fun sendChat(text: String, agent: AgentOption) = withContext(Dispatchers.IO) {
        val saved = requireCredentials()
        val payload = JSONObject()
            .put("message", text)
            .put("source", "mobile")
            .put("agent_id", agent.id)
            .put("agent_name", agent.name)
        request(baseUrl(saved.serverIp), "/chat", "POST", payload, saved.deviceId)
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
            .url(baseUrl(saved.serverIp) + "/api/device/upload")
            .header("X-Device-Id", saved.deviceId)
            .post(multipart)
            .build()
        execute(request)
    }

    suspend fun lockPc() = withContext(Dispatchers.IO) {
        val saved = requireCredentials()
        val request = Request.Builder()
            .url(baseUrl(saved.serverIp) + "/api/device/lock")
            .header("X-Device-Id", saved.deviceId)
            .post(JSONObject().toString().toRequestBody(JSON))
            .build()
        execute(request)
    }

    suspend fun sendClipboard(text: String) = withContext(Dispatchers.IO) {
        val saved = requireCredentials()
        request(
            baseUrl(saved.serverIp),
            "/api/device/clipboard",
            "POST",
            JSONObject().put("text", text),
            saved.deviceId,
        )
    }

    suspend fun downloadFile(context: Context, fileName: String, destination: Uri) =
        withContext(Dispatchers.IO) {
            val saved = requireCredentials()
            val url = baseUrl(saved.serverIp) + "/api/temp_media/${Uri.encode(fileName)}"
            val request = Request.Builder().url(url).get().build()
            val response = executeRaw(request)
            val input = response.body?.byteStream()
                ?: throw IOException("El servidor no devolvió el archivo.")
            val output = context.contentResolver.openOutputStream(destination)
                ?: throw IOException("No se pudo guardar el archivo en el destino elegido.")
            input.use { source -> output.use { target -> source.copyTo(target) } }
            _state.update { it.copy(pendingDownload = null) }
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
            _state.update {
                it.copy(connected = true, status = "Conectado a ${saved.pcName}", error = null)
            }
            ioScope.launch {
                runCatching { loadHistory(saved) }
                    .onFailure { _state.update { state -> state.copy(error = it.message) } }
                runCatching { loadAgents(saved) }
                    .onFailure { _state.update { state -> state.copy(error = it.message) } }
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
                webSocket = http.newWebSocket(webSocketRequest(saved), listener(saved))
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
        val result = request(baseUrl(saved.serverIp), "/history", deviceId = saved.deviceId)
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
        val result = request(baseUrl(saved.serverIp), "/api/agents", deviceId = saved.deviceId)
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

    private fun webSocketRequest(saved: DeviceCredentials): Request {
        val httpUrl = baseUrl(saved.serverIp).toHttpUrl()
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
