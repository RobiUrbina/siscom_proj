import serial
from statistics import mode

# === CONFIGURACIÓN SERIAL ===
PORT = "COM5"           # Puerto del PSoC
BAUD = 115200           # Velocidad del USBUART
TIMEOUT = 1.0           # Timeout de lectura

# === PARÁMETROS DE TRAMA ===
SYNC_PATTERN = "10101010"   # Byte de sincronización (0xAA)
MIN_SYNC_MATCH = 5          # Coincidencias mínimas para detectar sync
SAMPLES_PER_BIT = 4         # Número de muestras del PSoC por bit del Arduino

# === CORRECCIONES ===
INVERTIR = False             # Invierte bits 0↔1 (True o False)
DESPLAZAMIENTO = 2          # Corre bits a la derecha (0, 1, 2 o 3)

# === FUNCIONES AUXILIARES ===
def bits_to_byte(bits: str) -> int:
    """Convierte 8 bits (string) en un entero."""
    return int(bits, 2)

def buscar_sync(bits: str) -> int:
    """Busca el patrón de sincronización dentro del flujo binario."""
    for i in range(len(bits) - 8):
        ventana = bits[i:i+8]
        coincidencias = sum(a == b for a, b in zip(ventana, SYNC_PATTERN))
        if coincidencias >= MIN_SYNC_MATCH:
            return i
    return -1

def compactar(bits: str, n: int) -> str:
    """Compacta las muestras por moda (reduce ruido y repeticiones)."""
    bloques = [bits[i:i+n] for i in range(0, len(bits), n)]
    return ''.join(mode(b) for b in bloques if len(b) == n)

# === INICIO DE SESIÓN SERIAL ===
print(f"📡 Conectando al PSoC en {PORT}...\n")
try:
    ser = serial.Serial(PORT, BAUD, timeout=TIMEOUT)
    print("✅ Conectado correctamente.\n")
except serial.SerialException:
    print("❌ No se pudo abrir el puerto serial.")
    exit()

# === LOOP PRINCIPAL ===
print("⏳ Esperando trama...\n(Detén con Ctrl+C)\n")

bit_buffer = ""
state = "search_sync"
expected_len = 0

try:
    while True:
        data = ser.read(512)
        if not data:
            continue

        # Convertir ASCII '0'/'1' a bits válidos
        raw_bits = ''.join(c for c in data.decode(errors='ignore') if c in '01')
        if not raw_bits:
            continue

        # Compactar por moda (reduce redundancia)
        bits = compactar(raw_bits, SAMPLES_PER_BIT)

        # === Corrección de polaridad / desplazamiento ===
        if INVERTIR:
            bits = ''.join('1' if b == '0' else '0' for b in bits)
        if DESPLAZAMIENTO > 0:
            bits = bits[DESPLAZAMIENTO:]

        # Añadir al buffer
        bit_buffer += bits
        if len(bit_buffer) > 8000:
            bit_buffer = bit_buffer[-4000:]

        # === ESTADO 1: BUSCAR SINCRONIZACIÓN ===
        if state == "search_sync":
            idx = buscar_sync(bit_buffer)
            if idx != -1:
                print(f"\n🔄 Sincronización detectada (pos {idx})")
                bit_buffer = bit_buffer[idx + len(SYNC_PATTERN):]
                state = "read_len"
            continue

        # === ESTADO 2: LEER LONGITUD ===
        if state == "read_len" and len(bit_buffer) >= 8:
            len_bits = bit_buffer[:8]
            bit_buffer = bit_buffer[8:]
            expected_len = bits_to_byte(len_bits)
            print(f"📏 Longitud detectada: {expected_len} caracteres")
            state = "read_data"
            continue

        # === ESTADO 3: LEER DATOS ===
        if state == "read_data" and len(bit_buffer) >= expected_len * 8:
            data_bits = bit_buffer[:expected_len * 8]
            bit_buffer = bit_buffer[expected_len * 8:]

            # Reconstruir texto ASCII
            texto = ''.join(
                chr(bits_to_byte(data_bits[i:i+8]))
                for i in range(0, len(data_bits), 8)
                if len(data_bits[i:i+8]) == 8
            )

            if texto.strip():
                print(f"\n✅ Mensaje completo recibido:\n➡️ {texto}\n")
            else:
                print("⚠️ Bits recibidos pero no decodificables.\n")

            state = "search_sync"

except KeyboardInterrupt:
    print("\n🛑 Lectura detenida manualmente.")
finally:
    ser.close()
    print("🔌 Puerto serial cerrado.")
