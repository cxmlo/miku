#include <WiFi.h>
#include <WebServer.h>
#include <ESP32Servo.h>

// --- CONFIGURACIÓN DE RED ---
const char* ssid = "TU_WIFI";
const char* password = "TU_PASSWORD";

// --- CONFIGURACIÓN DE SERVOS ---
Servo panServo;   // Motor de la base (Izquierda/Derecha)
Servo tiltServo;  // Motor de la cabeza (Arriba/Abajo)

// Pines para los servos (Ajustar según tu PCB de Blueprint)
const int PAN_PIN = 4;
const int TILT_PIN = 5;

// Servidor Web en el puerto 80
WebServer server(80);

void setup() {
  Serial.begin(115200);
  
  // 1. Iniciar los Servos
  // ESP32 requiere configurar los temporizadores de los servos
  ESP32PWM::allocateTimer(0);
  ESP32PWM::allocateTimer(1);
  
  panServo.setPeriodHertz(50); // Servos estándar de 50Hz
  tiltServo.setPeriodHertz(50);
  
  panServo.attach(PAN_PIN, 500, 2400); // Rango de pulso para SG90/MG90S
  tiltServo.attach(TILT_PIN, 500, 2400);
  
  // Centrar la cabeza al encender
  panServo.write(90);
  tiltServo.write(90);

  // 2. Conectar al WiFi
  Serial.println("Conectando a WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConectado!");
  Serial.print("Direccion IP del ESP32: ");
  Serial.println(WiFi.localIP());

  // 3. Configurar Rutas del Servidor HTTP
  // Esta ruta es exactamente la que llama tu script test_motores.py
  server.on("/servo", HTTP_GET, []() {
    if (server.hasArg("pan") && server.hasArg("tilt")) {
      int panVal = server.arg("pan").toInt();
      int tiltVal = server.arg("tilt").toInt();
      
      // Limitar los valores para no romper el mecanismo
      panVal = constrain(panVal, 0, 180);
      tiltVal = constrain(tiltVal, 0, 180);
      
      panServo.write(panVal);
      tiltServo.write(tiltVal);
      
      server.send(200, "text/plain", "Movimiento OK");
    } else {
      server.send(400, "text/plain", "Faltan parametros pan o tilt");
    }
  });

  // Iniciar servidor
  server.begin();
  Serial.println("Servidor HTTP iniciado.");
}

void loop() {
  // Escuchar a las peticiones HTTP que vienen de Miku (tu computadora)
  server.handleClient();
  
  // Aquí luego agregaremos el código para dibujar los Ojos y leer la Cámara
}
