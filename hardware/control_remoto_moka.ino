#include <Arduino.h>
#include <Wire.h>
#include <U8g2lib.h>
#include <ESP32Servo.h> 
#include <WiFi.h>
#include <WebServer.h>

// ==========================================
// CONFIGURACIÓN DE RED WIFI (Conexión a tu router)
// ==========================================
const char* ssid = "NOMBRE_DE_TU_WIFI"; // Reemplaza con el nombre de tu red
const char* password = "CONTRASEÑA_DE_TU_WIFI"; // Reemplaza con tu contraseña

// ==========================================
// CONFIGURACIÓN DE LA PANTALLA LCD (1.3")
// ==========================================
// Usa SH1106. Si no enciende, cambia "SH1106" por "SSD1306"
U8G2_SH1106_128X64_NONAME_F_HW_I2C u8g2(U8G2_R0, /* reset=*/ U8X8_PIN_NONE);

// ==========================================
// CONFIGURACIÓN DE LOS SERVOMOTORES
// ==========================================
#define PIN_SERVO1 16 // Pin físico IO16 (Libre de luces)
#define PIN_SERVO2 12 // Pin físico IO12

Servo servoPan;
Servo servoTilt;

// ==========================================
// SERVIDOR WEB Y VARIABLES GLOBALES
// ==========================================
WebServer server(80);

int panPos = 90;
int tiltPos = 90;
String lcdMessage = "¡Hola! :)";
int currentExpression = 0; // 0=Normal, 1=Blink, 2=Yawn, 3=Happy

// --- INTERFAZ WEB (HTML, CSS y JS) ---
const char* htmlPage = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Control ESP32</title>
  <style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; margin: 0; padding: 20px; background-color: #f4f4f9; color: #333; }
    .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0px 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px; max-width: 400px; margin-left: auto; margin-right: auto; }
    h2 { margin-top: 0; color: #444; font-size: 1.2rem; }
    label { display: block; margin-top: 10px; font-weight: 500; font-size: 0.9rem; }
    input[type=range] { width: 100%; margin: 15px 0 25px 0; }
    input[type=text] { width: calc(100% - 22px); padding: 10px; margin-top: 10px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 6px; font-size: 1rem; }
    button { background-color: #007BFF; color: white; border: none; padding: 12px 20px; font-size: 1rem; border-radius: 6px; cursor: pointer; width: 100%; transition: background 0.3s; }
    button:hover { background-color: #0056b3; }
    .btn-row { display: flex; gap: 8px; justify-content: center; margin-bottom: 15px; flex-wrap: wrap; }
    .btn-row button { background-color: #28a745; width: auto; flex: 1; padding: 10px; font-size: 0.9rem; }
    .btn-row button:hover { background-color: #218838; }
  </style>
</head>
<body>
  <div class="card">
    <h2>Control de Servos</h2>
    <label>Servo Pan (Rotación): <span id="panVal">90</span>&deg;</label>
    <input type="range" id="panSlider" min="0" max="180" value="90" oninput="updatePan(this.value)">
    
    <label>Servo Tilt (Inclinación): <span id="tiltVal">90</span>&deg;</label>
    <input type="range" id="tiltSlider" min="0" max="180" value="90" oninput="updateTilt(this.value)">
  </div>

  <div class="card">
    <h2>Pantalla OLED</h2>
    <div class="btn-row">
      <button onclick="setFace('blink')">Parpadear</button>
      <button onclick="setFace('yawn')">Bostezar</button>
      <button onclick="setFace('happy')">Feliz</button>
    </div>
    <input type="text" id="lcdMsg" placeholder="Escribe un mensaje..." maxlength="30">
    <button onclick="sendMessage()">Enviar Mensaje</button>
  </div>

  <script>
    let isSending = false;
    let pendingReq = false;

    // Enviar peticiones de forma continua pero ordenada (0% Lag)
    function sendServoReq() {
      if (isSending) return; // Esperar a que el ESP32 termine de procesar la anterior
      isSending = true;
      const pan = document.getElementById('panSlider').value;
      const tilt = document.getElementById('tiltSlider').value;
      pendingReq = false;
      
      fetch(`/setServos?pan=${pan}&tilt=${tilt}`)
        .then(() => {
          isSending = false;
          // Si moviste el slider mientras se enviaba la anterior, envíalo ahora de inmediato
          if (pendingReq) sendServoReq(); 
        })
        .catch(e => {
          console.error(e);
          isSending = false;
        });
    }

    function updatePan(val) {
      document.getElementById('panVal').innerText = val;
      pendingReq = true;
      sendServoReq();
    }
    
    function updateTilt(val) {
      document.getElementById('tiltVal').innerText = val;
      pendingReq = true;
      sendServoReq();
    }

    function setFace(type) {
      fetch(`/setFace?type=${type}`).catch(e => console.error(e));
    }

    function sendMessage() {
      const msg = document.getElementById('lcdMsg').value;
      if(msg) {
        fetch(`/setMessage?msg=${encodeURIComponent(msg)}`).then(() => {
          document.getElementById('lcdMsg').value = ''; // Limpiar input
        }).catch(e => console.error(e));
      }
    }
  </script>
</body>
</html>
)rawliteral";

// ==========================================
// FUNCIÓN PARA DIBUJAR PANTALLA
// ==========================================
void drawOLED() {
  u8g2.clearBuffer();          
  
  // 1. DIBUJAR ICONO DE WIFI (Barras de señal)
  u8g2.drawBox(0, 7, 2, 3);
  u8g2.drawBox(3, 5, 2, 5);
  u8g2.drawBox(6, 3, 2, 7);
  u8g2.drawBox(9, 1, 2, 9);

  // 2. ESCRIBIR IP EN PEQUEÑO ARRIBA
  u8g2.setFont(u8g2_font_5x7_tr); // Fuente muy pequeña
  u8g2.setCursor(15, 9);
  u8g2.print(WiFi.localIP().toString());

  // 3. DIBUJAR CARITA DE MIKU (Según la animación)
  if (currentExpression == 0) {
    // Normal
    u8g2.drawRBox(22, 18, 34, 34, 8); // Ojo izq
    for (int i = 0; i < 3; i++) u8g2.drawLine(30, 14 + i, 44, 12 + i); // Ceja izq
    u8g2.drawRBox(72, 18, 34, 34, 8); // Ojo der
    for (int i = 0; i < 3; i++) u8g2.drawLine(84, 12 + i, 98, 14 + i); // Ceja der
    u8g2.drawRBox(59, 53, 10, 5, 1); // Boquita
  } 
  else if (currentExpression == 1) {
    // Parpadeo (ojos cerrados = lineas gruesas)
    u8g2.drawRBox(22, 33, 34, 4, 1); // Ojo izq cerrado
    for (int i = 0; i < 3; i++) u8g2.drawLine(30, 24 + i, 44, 22 + i); // Ceja izq más baja
    u8g2.drawRBox(72, 33, 34, 4, 1); // Ojo der cerrado
    for (int i = 0; i < 3; i++) u8g2.drawLine(84, 22 + i, 98, 24 + i); // Ceja der más baja
    u8g2.drawRBox(59, 53, 10, 5, 1); // Boquita normal
  }
  else if (currentExpression == 2) {
    // Bostezando
    u8g2.drawRBox(22, 33, 34, 6, 2); // Ojo izq cerrado/apretado
    for (int i = 0; i < 3; i++) u8g2.drawLine(30, 24 + i, 44, 26 + i); // Ceja izq invertida
    u8g2.drawRBox(72, 33, 34, 6, 2); // Ojo der cerrado/apretado
    for (int i = 0; i < 3; i++) u8g2.drawLine(84, 26 + i, 98, 24 + i); // Ceja der invertida
    u8g2.drawEllipse(64, 48, 8, 12); // Boca muuuuy grande
    
    // Burbuja Zzz
    u8g2.setFont(u8g2_font_5x7_tr);
    u8g2.drawStr(105, 20, "Z");
    u8g2.drawStr(112, 15, "z");
    u8g2.drawStr(118, 10, "z");
  }
  else if (currentExpression == 3) {
    // Feliz (Ojos ^ ^)
    for(int j=0; j<4; j++) {
      u8g2.drawLine(22, 35+j, 39, 18+j); 
      u8g2.drawLine(39, 18+j, 56, 35+j); 
      u8g2.drawLine(72, 35+j, 89, 18+j); 
      u8g2.drawLine(89, 18+j, 106, 35+j); 
    }
    u8g2.drawRBox(54, 45, 20, 10, 4); // Gran sonrisa
  }

  // 4. MOSTRAR MENSAJE DE LA WEB (Centrado abajo, solo si hay)
  if (lcdMessage.length() > 0) {
    u8g2.setFont(u8g2_font_6x10_tr); // Fuente un poco más grande para el mensaje
    int textWidth = u8g2.getStrWidth(lcdMessage.c_str());
    int xPos = (128 - textWidth) / 2; // Centrar el texto
    if (xPos < 0) xPos = 0;
    u8g2.setCursor(xPos, 60);
    u8g2.print(lcdMessage.c_str());
  }

  u8g2.sendBuffer();  
}

// ==========================================
// RUTAS DEL SERVIDOR WEB
// ==========================================
void handleRoot() {
  server.send(200, "text/html", htmlPage);
}

void handleSetServos() {
  if (server.hasArg("pan")) {
    panPos = server.arg("pan").toInt();
    servoPan.write(panPos);
  }
  if (server.hasArg("tilt")) {
    tiltPos = server.arg("tilt").toInt();
    servoTilt.write(tiltPos);
  }
  server.send(200, "text/plain", "OK");
}

void handleSetMessage() {
  if (server.hasArg("msg")) {
    lcdMessage = server.arg("msg");
    Serial.println("Nuevo mensaje: " + lcdMessage);
    drawOLED(); // Actualizamos la pantalla SOLO cuando llega un mensaje nuevo
  }
  server.send(200, "text/plain", "OK");
}

void handleSetFace() {
  if (server.hasArg("type")) {
    String t = server.arg("type");
    if (t == "normal") { 
      currentExpression = 0; 
      drawOLED(); 
    }
    else if (t == "blink") { 
      currentExpression = 1; drawOLED(); 
      delay(200); // Mantiene los ojos cerrados un instante
      currentExpression = 0; drawOLED(); 
    }
    else if (t == "yawn") { 
      currentExpression = 2; drawOLED(); 
      delay(1500); // Bosteza largo
      currentExpression = 0; drawOLED(); 
    }
    else if (t == "happy") { 
      currentExpression = 3; drawOLED(); 
      delay(1500); // Sonríe un buen rato
      currentExpression = 0; drawOLED(); 
    }
  }
  server.send(200, "text/plain", "OK");
}

// ==========================================
// FUNCIÓN SETUP
// ==========================================
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n=== INICIANDO SISTEMA ===");

  // Apagar la luz del Flash (Pin 4)
  pinMode(4, OUTPUT);
  digitalWrite(4, LOW);

  // 1. Inicializar Pantalla LCD (Pines I2C: 14=SDA, 15=SCL)
  Wire.begin(14, 15);
  u8g2.begin();  
  Serial.println("-> Pantalla LCD lista");

  // Mostrar mensaje inicial para comprobar que la pantalla sirve
  u8g2.clearBuffer();
  u8g2.setFont(u8g2_font_ncenB08_tr); 
  u8g2.drawStr(0, 30, "Iniciando Pantalla...");
  u8g2.sendBuffer();
  delay(1000);

  // 2. Inicializar Servos
  u8g2.clearBuffer();
  u8g2.drawStr(0, 30, "Iniciando Servos...");
  u8g2.sendBuffer();
  
  servoPan.attach(PIN_SERVO1);
  servoTilt.attach(PIN_SERVO2);
  servoPan.write(panPos);
  servoTilt.write(tiltPos);
  Serial.println("-> Servos configurados");
  delay(1000);

  // 3. Inicializar WiFi
  u8g2.clearBuffer();
  u8g2.drawStr(0, 30, "Conectando WiFi...");
  u8g2.sendBuffer();

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  Serial.print("-> Conectando a WiFi ");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("\n-> WiFi Conectado!");
  
  // 4. Configurar Servidor Web
  server.on("/", handleRoot);
  server.on("/setServos", handleSetServos);
  server.on("/setMessage", handleSetMessage);
  server.on("/setFace", handleSetFace);
  server.begin();
  Serial.println("-> Servidor HTTP iniciado");

  // Al finalizar el setup, dibujamos la carita por primera vez
  drawOLED();
}

// ==========================================
// FUNCIÓN LOOP
// ==========================================
void loop() {
  // Ahora el loop corre miles de veces por segundo porque no se queda
  // dibujando la pantalla repetitivamente. Así lee los servos en tiempo real.
  server.handleClient();
}
