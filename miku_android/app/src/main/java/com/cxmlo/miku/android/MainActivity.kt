package com.cxmlo.miku.android

import android.Manifest
import android.content.ClipData
import android.content.ClipboardManager
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.AlarmClock
import android.provider.Settings
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.ExposedDropdownMenuAnchorType
import androidx.compose.material3.ExposedDropdownMenuBox
import androidx.compose.material3.ExposedDropdownMenuDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.cxmlo.miku.android.connection.MikuConnectionService
import com.cxmlo.miku.android.data.AgentOption
import com.cxmlo.miku.android.data.ChatMessage
import com.cxmlo.miku.android.data.DeviceStore
import com.cxmlo.miku.android.data.MikuClient
import com.cxmlo.miku.android.data.PairingLink
import com.cxmlo.miku.android.ui.theme.MikuPalette
import com.cxmlo.miku.android.ui.theme.MikuTheme
import com.journeyapps.barcodescanner.ScanContract
import com.journeyapps.barcodescanner.ScanOptions
import kotlinx.coroutines.launch
import org.json.JSONObject

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (DeviceStore(this).read() != null) startConnection()
        setContent {
            MikuTheme {
                MikuApp(
                    onPair = ::pair,
                    onStartConnection = ::startConnection,
                    onStopConnection = { MikuConnectionService.stop(this) },
                )
            }
        }
        requestNotificationPermission()
        handlePairingIntent(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handlePairingIntent(intent)
    }

    private fun handlePairingIntent(intent: Intent?) {
        val uri = intent?.data ?: return
        if (intent.action != Intent.ACTION_VIEW || uri.scheme != "miku" || uri.host != "pair") return
        pair(uri.toString()) { error ->
            Toast.makeText(
                this,
                error ?: "Teléfono vinculado con Miku Desktop.",
                Toast.LENGTH_LONG,
            ).show()
        }
    }

    private fun startConnection() {
        ContextCompat.startForegroundService(
            this,
            Intent(this, MikuConnectionService::class.java),
        )
    }

    private fun pair(raw: String, onComplete: (String?) -> Unit) {
        lifecycleScope.launch {
            runCatching {
                MikuClient.pair(this@MainActivity, PairingLink.parse(raw))
                startConnection()
            }.onSuccess {
                onComplete(null)
            }.onFailure {
                onComplete(it.message ?: "No se pudo vincular el dispositivo.")
            }
        }
    }

    private fun requestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) !=
            android.content.pm.PackageManager.PERMISSION_GRANTED
        ) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 4102)
        }
    }
}

@Composable
private fun MikuApp(
    onPair: (String, (String?) -> Unit) -> Unit,
    onStartConnection: () -> Unit,
    onStopConnection: () -> Unit,
) {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val state by MikuClient.state.collectAsState()
    var selectedTab by remember { mutableStateOf(0) }
    var pairUrl by remember { mutableStateOf("") }
    var selectedAgent by remember { mutableStateOf(AgentOption("miku", "Miku")) }
    var message by remember { mutableStateOf("") }
    var busy by remember { mutableStateOf(false) }
    var feedback by remember { mutableStateOf<String?>(null) }
    var pendingFileName by remember { mutableStateOf<String?>(null) }

    val scanner = rememberLauncherForActivityResult(ScanContract()) { result ->
        val contents = result.contents
        if (contents.isNullOrBlank()) {
            feedback = "Escaneo cancelado o no se detectó ningún QR."
        } else {
            pairUrl = contents
            feedback = "QR leído. Vinculando con Miku Desktop..."
            onPair(contents) { error ->
                feedback = error ?: "Teléfono vinculado con Miku Desktop."
            }
        }
    }
    val scanOptions = remember {
        ScanOptions().apply {
            setDesiredBarcodeFormats(ScanOptions.QR_CODE)
            setPrompt("Escanea el QR de Miku Desktop")
            setBeepEnabled(false)
            setOrientationLocked(false)
        }
    }
    val requestCameraPermission = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission(),
    ) { granted ->
        if (granted) {
            scanner.launch(scanOptions)
        } else {
            feedback = "Permite el acceso a la cámara para escanear el QR, o pega el enlace manualmente."
        }
    }
    val pickFile = rememberLauncherForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) {
            busy = true
            scope.launch {
                runCatching { MikuClient.uploadFile(context, uri) }
                    .onSuccess { feedback = "Archivo enviado a la PC." }
                    .onFailure { feedback = it.message }
                busy = false
            }
        }
    }
    val saveFile = rememberLauncherForActivityResult(
        ActivityResultContracts.CreateDocument("*/*"),
    ) { uri ->
        val name = pendingFileName
        if (uri != null && name != null) {
            busy = true
            scope.launch {
                runCatching { MikuClient.downloadFile(context, name, uri) }
                    .onSuccess { feedback = "Archivo guardado en el teléfono." }
                    .onFailure { feedback = it.message }
                busy = false
            }
        }
    }

    LaunchedEffect(state.clipboardText) {
        state.clipboardText?.let { text ->
            val manager = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
            manager.setPrimaryClip(ClipData.newPlainText("Miku", text))
            MikuClient.clearClipboardText()
            feedback = "Texto copiado desde el PC."
        }
    }

    Scaffold(
        containerColor = MikuPalette.Background,
        bottomBar = {
            NavigationBar(containerColor = MikuPalette.Surface) {
                listOf("Chat", "Control", "Eventos", "Ajustes").forEachIndexed { index, label ->
                    NavigationBarItem(
                        selected = selectedTab == index,
                        onClick = { selectedTab = index },
                        icon = { Text(listOf("✦", "⌘", "◉", "⚙")[index]) },
                        label = { Text(label) },
                    )
                }
            }
        },
    ) { padding ->
        Column(
            modifier = Modifier.fillMaxSize().background(MikuPalette.Background).padding(padding).padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Column {
                    Text("MIKU MOBILE", style = MaterialTheme.typography.titleLarge, color = Color.White)
                    Text(
                        state.pcName.ifBlank { "Conecta con tu Miku Desktop" },
                        style = MaterialTheme.typography.bodySmall,
                        color = Color.LightGray,
                    )
                }
                Text(
                    if (state.connected) "● EN LÍNEA" else "● SIN CONEXIÓN",
                    color = if (state.connected) MikuPalette.Accent else MikuPalette.Error,
                )
            }
            state.error?.let { Text(it, color = MikuPalette.Error) }
            feedback?.let {
                Card(colors = CardDefaults.cardColors(containerColor = MikuPalette.Surface)) {
                    Row(
                        modifier = Modifier.fillMaxWidth().padding(12.dp),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(it, modifier = Modifier.weight(1f), color = Color.White)
                        TextButton(onClick = { feedback = null }) { Text("Cerrar") }
                    }
                }
            }

            when (selectedTab) {
                0 -> ChatPanel(
                    messages = state.messages,
                    agents = state.agents,
                    selectedAgent = selectedAgent,
                    onAgentChange = { selectedAgent = it },
                    message = message,
                    onMessageChange = { message = it },
                    enabled = state.connected && !busy,
                    onSend = {
                        val text = message.trim()
                        if (text.isNotEmpty()) {
                            message = ""
                            busy = true
                            scope.launch {
                                runCatching { MikuClient.sendChat(text, selectedAgent) }
                                    .onFailure { feedback = it.message }
                                busy = false
                            }
                        }
                    },
                )
                1 -> ControlPanel(
                    connected = state.connected,
                    busy = busy,
                    pendingCommand = state.pendingPhoneCommand,
                    pendingDownload = state.pendingDownload,
                    onLock = {
                        busy = true
                        scope.launch {
                            runCatching { MikuClient.lockPc() }
                                .onSuccess { feedback = "La PC recibió la orden de bloqueo." }
                                .onFailure { feedback = it.message }
                            busy = false
                        }
                    },
                    onPickFile = { pickFile.launch(arrayOf("*/*")) },
                    onSaveDownload = {
                        state.pendingDownload?.let { name ->
                            pendingFileName = name
                            saveFile.launch(name)
                        }
                    },
                    onSyncClipboard = {
                        val manager = context.getSystemService(Context.CLIPBOARD_SERVICE) as ClipboardManager
                        val text = manager.primaryClip?.getItemAt(0)?.coerceToText(context)?.toString().orEmpty()
                        if (text.isBlank()) {
                            feedback = "No hay texto en el portapapeles."
                        } else {
                            busy = true
                            scope.launch {
                                runCatching { MikuClient.sendClipboard(text) }
                                    .onSuccess { feedback = "Portapapeles enviado a la PC." }
                                    .onFailure { feedback = it.message }
                                busy = false
                            }
                        }
                    },
                    onRunCommand = { command ->
                        runCatching { runPhoneCommand(context, command.action, command.extras) }
                            .onSuccess { feedback = "Se abrió la acción solicitada en Android." }
                            .onFailure { feedback = it.message ?: "Android no pudo abrir esta acción." }
                        MikuClient.clearPhoneCommand()
                    },
                    onDismissCommand = MikuClient::clearPhoneCommand,
                )
                2 -> EventsPanel(state.notices)
                else -> SettingsPanel(
                    serverIp = state.serverIp,
                    status = state.status,
                    onReconnect = onStartConnection,
                    onUnpair = {
                        MikuClient.unpair(context)
                        onStopConnection()
                        feedback = "Dispositivo desvinculado."
                    },
                    pairUrl = pairUrl,
                    onPairUrlChange = { pairUrl = it },
                    onScan = { requestCameraPermission.launch(Manifest.permission.CAMERA) },
                    onPair = { onPair(pairUrl) { error -> feedback = error ?: "Teléfono vinculado." } },
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun ChatPanel(
    messages: List<com.cxmlo.miku.android.data.ChatMessage>,
    agents: List<AgentOption>,
    selectedAgent: AgentOption,
    onAgentChange: (AgentOption) -> Unit,
    message: String,
    onMessageChange: (String) -> Unit,
    enabled: Boolean,
    onSend: () -> Unit,
) {
    var expanded by remember { mutableStateOf(false) }
    Column(modifier = Modifier.fillMaxSize(), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        ExposedDropdownMenuBox(expanded = expanded, onExpandedChange = { expanded = it }) {
            OutlinedTextField(
                value = selectedAgent.name,
                onValueChange = {},
                readOnly = true,
                label = { Text("Agente") },
                trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded) },
                modifier = Modifier.menuAnchor(ExposedDropdownMenuAnchorType.PrimaryNotEditable).fillMaxWidth(),
            )
            ExposedDropdownMenu(expanded = expanded, onDismissRequest = { expanded = false }) {
                agents.forEach { agent ->
                    DropdownMenuItem(
                        text = { Text(agent.name) },
                        onClick = {
                            onAgentChange(agent)
                            expanded = false
                        },
                    )
                }
            }
        }
        LazyColumn(
            modifier = Modifier.weight(1f).fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(8.dp),
        ) {
            items(messages, key = ChatMessage::id) { item ->
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = if (item.sender == "user") MikuPalette.AccentSurface else MikuPalette.Surface,
                    ),
                ) {
                    Column(Modifier.padding(12.dp)) {
                        Text(item.sender, color = MikuPalette.Accent, style = MaterialTheme.typography.labelSmall)
                        Spacer(Modifier.height(3.dp))
                        Text(item.text, color = Color.White)
                    }
                }
            }
        }
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
            OutlinedTextField(
                value = message,
                onValueChange = onMessageChange,
                modifier = Modifier.weight(1f),
                label = { Text("Escribe a Miku") },
                keyboardOptions = KeyboardOptions(imeAction = ImeAction.Send),
                enabled = enabled,
            )
            Button(onClick = onSend, enabled = enabled && message.isNotBlank()) { Text("Enviar") }
        }
    }
}

@Composable
private fun ControlPanel(
    connected: Boolean,
    busy: Boolean,
    pendingCommand: com.cxmlo.miku.android.data.PhoneCommand?,
    pendingDownload: String?,
    onLock: () -> Unit,
    onPickFile: () -> Unit,
    onSaveDownload: () -> Unit,
    onSyncClipboard: () -> Unit,
    onRunCommand: (com.cxmlo.miku.android.data.PhoneCommand) -> Unit,
    onDismissCommand: () -> Unit,
) {
    Column(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.spacedBy(12.dp),
    ) {
        Text("CONTROL DEL ESCRITORIO", color = MikuPalette.Accent, style = MaterialTheme.typography.titleMedium)
        ActionCard("Bloquear PC", "Bloquea la sesión de Windows vinculada.", connected && !busy, onLock)
        ActionCard("Enviar archivo a la PC", "Elige un archivo y Miku lo abrirá en el escritorio.", connected && !busy, onPickFile)
        ActionCard("Sincronizar portapapeles", "Copia el texto actual del teléfono al PC.", connected && !busy, onSyncClipboard)
        pendingDownload?.let { name ->
            ActionCard("Guardar archivo del PC", "Archivo recibido: $name", !busy, onSaveDownload)
        }
        pendingCommand?.let { command ->
            Card(colors = CardDefaults.cardColors(containerColor = MikuPalette.Surface)) {
                Column(
                    modifier = Modifier.fillMaxWidth().padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp),
                ) {
                    Text("ACCIÓN SOLICITADA PARA EL TELÉFONO", color = MikuPalette.Accent)
                    Text(command.action, color = Color.White)
                    Text(
                        "Android abrirá la pantalla correspondiente; Miku no puede ejecutar acciones del sistema en silencio.",
                        color = Color.LightGray,
                    )
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(onClick = { onRunCommand(command) }) { Text("Abrir en Android") }
                        TextButton(onClick = onDismissCommand) { Text("Rechazar") }
                    }
                }
            }
        }
        Text(
            "Las acciones recibidas desde el Island requieren confirmación en el teléfono.",
            color = Color.LightGray,
            style = MaterialTheme.typography.bodySmall,
        )
    }
}

@Composable
private fun EventsPanel(notices: List<com.cxmlo.miku.android.data.AgentNotice>) {
    Column(modifier = Modifier.fillMaxSize(), verticalArrangement = Arrangement.spacedBy(10.dp)) {
        Text("EVENTOS DE AGENTES", color = MikuPalette.Accent, style = MaterialTheme.typography.titleMedium)
        if (notices.isEmpty()) {
            Text("Las notificaciones de agentes del Island aparecerán aquí.", color = Color.LightGray)
        } else {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(notices, key = com.cxmlo.miku.android.data.AgentNotice::id) { notice ->
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(containerColor = MikuPalette.Surface),
                    ) {
                        Column(Modifier.padding(12.dp)) {
                            Text("${notice.agent} · ${notice.event}", color = MikuPalette.Accent)
                            Text(notice.detail, color = Color.White)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun SettingsPanel(
    serverIp: String,
    status: String,
    onReconnect: () -> Unit,
    onUnpair: () -> Unit,
    pairUrl: String,
    onPairUrlChange: (String) -> Unit,
    onScan: () -> Unit,
    onPair: () -> Unit,
) {
    Column(modifier = Modifier.fillMaxSize(), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("VINCULACIÓN Y CONEXIÓN", color = MikuPalette.Accent, style = MaterialTheme.typography.titleMedium)
        Text(if (serverIp.isBlank()) "Aún no hay un PC vinculado." else "PC: $serverIp", color = Color.White)
        Text(status, color = Color.LightGray)
        OutlinedTextField(
            value = pairUrl,
            onValueChange = onPairUrlChange,
            modifier = Modifier.fillMaxWidth(),
            label = { Text("Enlace miku://pair del QR") },
            singleLine = true,
        )
        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(onClick = onScan) { Text("Escanear QR") }
            Button(onClick = onPair, enabled = pairUrl.isNotBlank()) { Text("Vincular") }
        }
        Button(onClick = onReconnect, enabled = serverIp.isNotBlank()) { Text("Reconectar") }
        if (serverIp.isNotBlank()) {
            TextButton(onClick = onUnpair) { Text("Desvincular este teléfono", color = MikuPalette.Error) }
        }
    }
}

@Composable
private fun ActionCard(title: String, detail: String, enabled: Boolean, action: () -> Unit) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(containerColor = MikuPalette.Surface),
        onClick = action,
        enabled = enabled,
    ) {
        Column(Modifier.padding(14.dp)) {
            Text(title, color = Color.White, style = MaterialTheme.typography.titleSmall)
            Text(detail, color = Color.LightGray, style = MaterialTheme.typography.bodySmall)
        }
    }
}

private fun runPhoneCommand(context: Context, action: String, extras: JSONObject) {
    val intent = when (action) {
        AlarmClock.ACTION_SET_ALARM -> Intent(AlarmClock.ACTION_SET_ALARM).apply {
            putExtra(AlarmClock.EXTRA_MESSAGE, extras.optString(AlarmClock.EXTRA_MESSAGE, "Miku"))
            if (extras.has(AlarmClock.EXTRA_HOUR)) putExtra(AlarmClock.EXTRA_HOUR, extras.optInt(AlarmClock.EXTRA_HOUR))
            if (extras.has(AlarmClock.EXTRA_MINUTES)) putExtra(AlarmClock.EXTRA_MINUTES, extras.optInt(AlarmClock.EXTRA_MINUTES))
            putExtra(AlarmClock.EXTRA_SKIP_UI, false)
        }
        AlarmClock.ACTION_SET_TIMER -> Intent(AlarmClock.ACTION_SET_TIMER).apply {
            putExtra(AlarmClock.EXTRA_LENGTH, extras.optInt(AlarmClock.EXTRA_LENGTH).coerceIn(1, 86_400))
            putExtra(AlarmClock.EXTRA_MESSAGE, extras.optString(AlarmClock.EXTRA_MESSAGE, "Miku"))
            putExtra(AlarmClock.EXTRA_SKIP_UI, false)
        }
        AlarmClock.ACTION_SHOW_ALARMS -> Intent(AlarmClock.ACTION_SHOW_ALARMS)
        Settings.ACTION_SETTINGS -> Intent(Settings.ACTION_SETTINGS)
        Settings.ACTION_WIFI_SETTINGS -> Intent(Settings.ACTION_WIFI_SETTINGS)
        Settings.ACTION_BLUETOOTH_SETTINGS -> Intent(Settings.ACTION_BLUETOOTH_SETTINGS)
        else -> throw IllegalArgumentException("Miku no tiene permitido ejecutar esta acción de Android: $action")
    }
    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    context.startActivity(intent)
}
