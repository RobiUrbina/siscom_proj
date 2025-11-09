import serial
import numpy as np
import time

# === CONFIGURACIÓN DEL PUERTO SERIAL ===
PORT = 'COM7'
BAUD = 115200
THRESHOLD = 2800       # Nivel de detección (en counts)
below_limit = 2200
Fs = 10000  # Frecuencia de muestreo estimada en Hz

ser = serial.Serial(PORT, BAUD, timeout=1)
print(f"\n📡 Escuchando en {PORT} a {BAUD} baudios...\n")

# === FUNCIÓN DE DECODIFICACIÓN MANCHESTER ===
def decodificar_manchester(samples, Fs, THRESHOLD):
    samples = np.array(samples)
    logic = (samples > THRESHOLD).astype(int)

    # --- Detectar primer pulso alto ---
    start_index = None
    end_index = None

    for i in range(len(logic)):
        if logic[i] == 1:
            start_index = i
            break

    if start_index is not None:
        for j in range(start_index + 1, len(logic)):
            if logic[j - 1] == 1 and logic[j] == 0:
                end_index = j
                break

    if start_index is None or end_index is None:
        return None, None

    pulse_width_samples = end_index - start_index
    pulse_width_time = pulse_width_samples / Fs

    start_ref = end_index + pulse_width_samples
    period_2x = 2 * pulse_width_samples
    max_index = len(logic)

    decoded_bits = []
    flancos = []

    for i in range(start_ref + 1, len(logic)):
        if logic[i] != logic[i - 1]:
            flancos.append(i)

    for k in range(start_ref, max_index, period_2x):
        next_k = k + period_2x
        if next_k >= len(logic):
            break

        flancos_periodo = [f for f in flancos if k <= f < next_k]
        if not flancos_periodo:
            continue

        centro = (k + next_k) / 2
        flanco_central = min(flancos_periodo, key=lambda f: abs(f - centro))
        margen = 0.2 * period_2x

        if abs(flanco_central - k) < margen or abs(next_k - flanco_central) < margen:
            continue

        if logic[flanco_central - 1] == 1 and logic[flanco_central] == 0:
            decoded_bits.append(1)  # alta → baja → 1
        elif logic[flanco_central - 1] == 0 and logic[flanco_central] == 1:
            decoded_bits.append(0)  # baja → alta → 0

    # --- Conversión binario → texto ---
    decoded_text = ''
    if decoded_bits:
        while len(decoded_bits) % 8 != 0:
            decoded_bits.append(0)
        for i in range(0, len(decoded_bits), 8):
            byte = decoded_bits[i:i+8]
            valor = int(''.join(map(str, byte)), 2)
            decoded_text += chr(valor) if 32 <= valor <= 126 else '?'

    return decoded_bits, decoded_text


# === BUCLE PRINCIPAL DE CAPTURA Y DECODIFICACIÓN ===
try:
    while True:
        samples = []
        trigger_active = False
        below_count = 0

        # Espera de trigger
        while True:
            line = ser.readline().decode('utf-8').strip()
            if not line:
                continue

            try:
                voltage = float(line)
            except ValueError:
                continue

            if not trigger_active:
                if voltage >= THRESHOLD:
                    trigger_active = True
                    samples = [voltage]
                    below_count = 0
                    print(f"\n⚡ Señal detectada. Capturando...")
            else:
                samples.append(voltage)
                if voltage < THRESHOLD:
                    below_count += 1
                else:
                    below_count = 0

                if below_count+2180 >= below_limit:
                    print("📩 Señal completa capturada. Decodificando...\n")
                    break

        # Decodificar mensaje capturado
        decoded_bits, decoded_text = decodificar_manchester(samples, Fs, THRESHOLD)

        if decoded_bits is None:
            print("⚠️ No se detectó pulso válido. Reintentando...\n")
            continue

        print("=== DECODIFICACIÓN MANCHESTER ===")
        print("Bits detectados:", len(decoded_bits))
        print("Secuencia:", ''.join(map(str, decoded_bits)))
        print("=== TEXTO DECODIFICADO ===")
        print(decoded_text if decoded_text else "(sin texto válido)")
        print("\nEsperando la siguiente transmisión...\n")

        time.sleep(0.5)  # pequeña pausa para limpiar buffer

except KeyboardInterrupt:
    print("\n🛑 Lectura detenida manualmente.")
finally:
    ser.close()
