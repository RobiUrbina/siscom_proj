# === graficar_csv_labview.py ===
import pandas as pd
import matplotlib.pyplot as plt

# === 1. Ruta del archivo CSV ===
# 👇 Cambia esta ruta por la ubicación de tu archivo
archivo_csv = r"test.csv"

# === 2. Leer el archivo CSV ===
# Usa encoding='latin-1' si el archivo tiene caracteres extraños
try:
    datos = pd.read_csv(archivo_csv)
except UnicodeDecodeError:
    datos = pd.read_csv(archivo_csv, encoding='latin-1')

print("✅ Archivo leído correctamente.")
print("Primeras filas del archivo:")
print(datos.head(), "\n")

# === 3. Detectar las columnas automáticamente ===
columnas = datos.columns.tolist()
print("Columnas detectadas:", columnas)

# Si hay una columna de tiempo, úsala
if 'Time' in columnas or 'time' in columnas:
    tiempo = datos[columnas[0]]
    señal = datos[columnas[-1]]
    eje_x = "Tiempo [s]"
else:
    tiempo = range(len(datos))
    señal = datos[columnas[-1]]
    eje_x = "Muestras"

# === 4. Graficar ===
plt.figure(figsize=(10, 5))
plt.plot(tiempo, señal, label='Señal adquirida', linewidth=1.2)
plt.title("Datos adquiridos desde LabVIEW o DAQ")
plt.xlabel(eje_x)
plt.ylabel("Voltaje [V]")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
