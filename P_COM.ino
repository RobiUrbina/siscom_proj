const int manchesterPin = 9;
const int syncPin = 8;
const unsigned long bitRate = 1;                  // bits por segundo
const unsigned long bitPeriod = 1000000 / bitRate; // 500000 µs (0.5 s por bit)
const unsigned long halfPeriod = bitPeriod / 2;    // 250000 µs (0.25 s por medio bit)

void setup() {
  pinMode(manchesterPin, OUTPUT);
  pinMode(syncPin, OUTPUT);
  digitalWrite(manchesterPin, LOW);
  digitalWrite(syncPin, LOW);

  Serial.begin(9600);
  Serial.println("=== Generador Manchester 2 bit/s (con bit de sincronización) ===");
  Serial.println("Escribe un texto y presiona Enter para transmitirlo.\n");
}

void loop() {
  if (Serial.available() > 0) {
    String msg = Serial.readStringUntil('\n');
    msg.trim();

    if (msg.length() > 0) {
      Serial.print("Mensaje: ");
      Serial.println(msg);
      Serial.println("Binario transmitido:");

      // Pulso de sincronización general (inicio)
      digitalWrite(syncPin, HIGH);
      delay(100); // 100 ms para indicar inicio
      digitalWrite(syncPin, LOW);

      // === Nuevo: Bit de sincronización previo ===
      Serial.println("Enviando bit de sincronización (1)...");
      sendManchesterBit(1);  // Puede ser 1 o 0 según convenga para tu decodificador

      // === Enviar mensaje ===
      for (unsigned int i = 0; i < msg.length(); i++) {
        byte c = msg[i];

        // Mostrar byte en binario
        for (int b = 7; b >= 0; b--) {
          Serial.print(bitRead(c, b));
        }
        Serial.print(" ");

        // Transmitir el byte en Manchester
        sendManchesterByte(c);
      }

      // Pulso de sincronización final
      digitalWrite(syncPin, HIGH);
      delay(100); // 100 ms para indicar fin
      digitalWrite(syncPin, LOW);

      Serial.println("\nTransmisión completada.\n");
    }
  }
}

// === Función para enviar un solo bit en Manchester ===
void sendManchesterBit(bool bitVal) {
  if (bitVal) {
    // Manchester '1' → HIGH luego LOW
    digitalWrite(manchesterPin, HIGH);
    delayMicroseconds(halfPeriod);
    digitalWrite(manchesterPin, LOW);
    delayMicroseconds(halfPeriod);
  } else {
    // Manchester '0' → LOW luego HIGH
    digitalWrite(manchesterPin, LOW);
    delayMicroseconds(halfPeriod);
    digitalWrite(manchesterPin, HIGH);
    delayMicroseconds(halfPeriod);
  }
}

// === Función para enviar un byte completo en Manchester ===
void sendManchesterByte(byte data) {
  for (int i = 7; i >= 0; i--) {
    bool bitVal = bitRead(data, i);
    sendManchesterBit(bitVal);
  }

  // Pausa mínima entre bytes
  digitalWrite(manchesterPin, LOW);
  delayMicroseconds(bitPeriod);
}
