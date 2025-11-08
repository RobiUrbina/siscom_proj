import serial
import matplotlib.pyplot as plt
import numpy as np

# === Configura el puerto ===
ser = serial.Serial('COM7', 115200, timeout=1)

THRESHOLD = 4000       # Nivel de detección (en counts)
below_limit = 20
samples = []
trigger_active = False
below_count = 0

print(f"Esperando cruce por {THRESHOLD}...\n")

# === Captura de datos ===
try:
    while True:
        line = ser.readline().decode('utf-8').strip()
        if not line:
            continue

        try:
            voltage = float(line)
        except ValueError:
            continue  # ignora líneas corruptas o vacías

        if not trigger_active:
            if voltage >= THRESHOLD:
                trigger_active = True
                samples = [voltage]
                below_count = 0
                print(f"Se detectó cruce por {THRESHOLD}. Iniciando captura...")
        else:
            samples.append(voltage)
            if voltage < THRESHOLD:
                below_count += 1
            else:
                below_count = 0

            if below_count >= below_limit:
                print("Fin de la señal. Captura detenida.")
                break

except KeyboardInterrupt:
    print("\nLectura detenida manualmente.")
finally:
    ser.close()

# === Procesamiento de datos ===
if not samples:
    print("No se capturaron datos.")
    exit()

samples = np.array(samples)

# === Señal analógica ===
plt.figure(figsize=(10, 4))
plt.plot(samples, linewidth=1)
plt.axhline(THRESHOLD, color='r', linestyle='--', label='Umbral')
plt.title("Señal capturada desde PSoC")
plt.xlabel("Muestras")
plt.ylabel("Amplitud [counts]")
plt.legend()
plt.grid(True)
plt.show()

# === Señal lógica binarizada ===
logic = (samples > THRESHOLD).astype(int)

plt.figure(figsize=(10, 3))
plt.step(range(len(logic)), logic, where='post', linewidth=1)
plt.title("Señal lógica (umbral aplicado)")
plt.xlabel("Muestra")
plt.ylabel("Nivel lógico")
plt.grid(True)

# === Medir el primer periodo que dura en alto ===
start_index = None
end_index = None

# Buscar el primer punto alto
for i in range(len(logic)):
    if logic[i] == 1:
        start_index = i
        break

# Buscar el primer punto donde baja (1 -> 0)
if start_index is not None:
    for j in range(start_index + 1, len(logic)):
        if logic[j - 1] == 1 and logic[j] == 0:
            end_index = j
            break

if start_index is not None and end_index is not None:
    pulse_width_samples = end_index - start_index

    # Ajusta según tu frecuencia de muestreo real
    Fs = 10000  # Hz
    pulse_width_time = pulse_width_samples / Fs

    print("\n=== RESULTADO DE MEDICIÓN ===")
    print(f"Inicio del primer pulso alto: muestra {start_index}")
    print(f"Fin del primer pulso alto: muestra {end_index}")
    print(f"Duración del primer pulso alto: {pulse_width_samples} muestras")
    print(f"Duración aproximada: {pulse_width_time*1000:.3f} ms")

    # === Dibujar líneas verticales ===
    start_ref = end_index + pulse_width_samples
    period_2x = 2 * pulse_width_samples
    max_index = len(logic)

    for k in range(start_ref, max_index, period_2x):
        plt.axvline(k, color='g', linestyle='--', alpha=0.7)

    plt.axvline(start_index, color='b', linestyle='--', alpha=0.8, label='Inicio primer pulso alto')
    plt.axvline(end_index, color='r', linestyle='--', alpha=0.8, label='Fin primer pulso alto')
    plt.axvline(start_ref, color='orange', linestyle='--', alpha=0.7, label='Inicio referencias (T)')
    plt.legend(loc='upper right')

    # === Decodificación Manchester desde el eje naranja (con descarte de flancos cercanos) ===
    decoded_bits = []
    ref_index = start_ref
    last_state = logic[ref_index] if ref_index < len(logic) else 0

    # Buscar flancos en toda la señal
    flancos = []
    for i in range(ref_index + 1, len(logic)):
        if logic[i] != logic[i - 1]:
            flancos.append(i)

    # Procesar flancos dentro de cada periodo 2T
    for k in range(start_ref, max_index, period_2x):
        next_k = k + period_2x
        if next_k >= len(logic):
            break

        # Filtrar flancos dentro del periodo actual
        flancos_periodo = [f for f in flancos if k <= f < next_k]
        if not flancos_periodo:
            continue

        # Si hay más de un flanco, mantener el más central (más alejado de los bordes)
        centro = (k + next_k) / 2
        flanco_central = min(flancos_periodo, key=lambda f: abs(f - centro))

        # Validar si está suficientemente alejado de los bordes (margen = 20% del periodo)
        margen = 0.2 * period_2x
        if abs(flanco_central - k) < margen or abs(next_k - flanco_central) < margen:
            continue  # demasiado cerca del borde → ignorar

        # Decodificar dirección del flanco central
        if logic[flanco_central - 1] == 1 and logic[flanco_central] == 0:
            decoded_bits.append(1)  # alta → baja → 0
        elif logic[flanco_central - 1] == 0 and logic[flanco_central] == 1:
            decoded_bits.append(0)  # baja → alta → 1

        # Dibujar el flanco central detectado
        plt.axvline(flanco_central, color='magenta', linestyle=':', alpha=0.8)

    # === Mostrar resultado ===
    print("\n=== DECODIFICACIÓN MANCHESTER (flanco más central por periodo) ===")
    print(f"Bits detectados: {len(decoded_bits)}")
    print("Secuencia:", ''.join(map(str, decoded_bits)))

        # === Conversión de binario a texto ASCII ===
    if decoded_bits:
        # Asegurar que el número de bits sea múltiplo de 8
        while len(decoded_bits) % 8 != 0:
            decoded_bits.append(0)  # relleno con ceros si falta

        # Agrupar en bytes y convertir a texto
        decoded_text = ''
        for i in range(0, len(decoded_bits), 8):
            byte = decoded_bits[i:i+8]
            valor = int(''.join(map(str, byte)), 2)
            if 32 <= valor <= 126:  # solo caracteres imprimibles
                decoded_text += chr(valor)
            else:
                decoded_text += '?' 

        print("\n=== TEXTO DECODIFICADO ===")
        print(decoded_text)
    else:
        print("\n⚠️ No se decodificaron bits suficientes para texto.")


else:
    print("\n⚠️ No se detectó un pulso alto inicial completo (inicio y fin).")

plt.show()
