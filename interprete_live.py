import serial
import matplotlib.pyplot as plt
import numpy as np
from collections import deque

# === Configuración de puerto y parámetros ===
PORT = 'COM7'
BAUD = 115200
THRESHOLD = 4000
below_limit = 20
Fs = 10000         # Frecuencia de muestreo (Hz) — estimada
WINDOW = 1000      # Número de muestras visibles en pantalla

ser = serial.Serial(PORT, BAUD, timeout=0.05)
print(f"\n⏳ Esperando datos desde {PORT}...\n")

# === Buffers circulares para graficar ===
samples = deque(maxlen=WINDOW)
logic = deque(maxlen=WINDOW)

# === Variables de control ===
trigger_active = False
below_count = 0
captured = []
paused = False

# === Configuración de gráfica ===
plt.ion()
fig, ax = plt.subplots(figsize=(10, 4))
line, = ax.plot([], [], lw=1, label="Señal [counts]")
ax.axhline(THRESHOLD, color='r', ls='--', label='Umbral')
ax.set_ylim(0, 8000)
ax.set_xlim(0, WINDOW)
ax.set_xlabel("Muestras recientes")
ax.set_ylabel("Amplitud [counts]")
ax.set_title("Lectura en tiempo real desde PSoC")
ax.grid(True)
ax.legend()

# === Bucle principal ===
try:
    while True:
        line_serial = ser.readline().decode(errors='ignore').strip()
        if not line_serial:
            continue

        try:
            value = float(line_serial)
        except ValueError:
            continue

        # --- Detección de trigger ---
        if not trigger_active:
            if value >= THRESHOLD:
                trigger_active = True
                below_count = 0
                captured = []
                print(f"🚀 Disparo detectado (>{THRESHOLD}). Comienza captura...")
        else:
            captured.append(value)
            if value < THRESHOLD:
                below_count += 1
            else:
                below_count = 0
            if below_count >= below_limit:
                print("✅ Señal terminada, deteniendo captura.")
                break

        # --- Actualiza buffers de gráfica ---
        samples.append(value)
        logic.append(1 if value > THRESHOLD else 0)

        # --- Actualiza la gráfica cada ~50 muestras ---
        if len(samples) % 50 == 0:
            line.set_data(range(len(samples)), samples)
            ax.set_xlim(max(0, len(samples) - WINDOW), len(samples))
            plt.pause(0.001)

except KeyboardInterrupt:
    print("\n⛔ Lectura detenida manualmente.")
finally:
    ser.close()
    plt.ioff()
    print("🔌 Puerto cerrado.")

# === Muestra la señal final ===
if captured:
    captured = np.array(captured)
    plt.figure(figsize=(10, 4))
    plt.plot(captured, lw=1)
    plt.axhline(THRESHOLD, color='r', ls='--')
    plt.title("Señal capturada completa")
    plt.xlabel("Muestras")
    plt.ylabel("Amplitud [counts]")
    plt.grid(True)
    plt.show()
else:
    print("⚠️ No se capturaron datos.")
