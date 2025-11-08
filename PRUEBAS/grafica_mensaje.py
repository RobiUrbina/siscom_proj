# === Graficar datos de un archivo CSV ===
# Autor: Roberto Urbina Loaiza
# Descripción: Lee un archivo .csv con columnas "tiempo" y "voltaje" y grafica los datos.

import pandas as pd
import matplotlib.pyplot as plt

# === 1. Leer el archivo CSV ===
# Asegúrate de cambiar el nombre del archivo por el tuyo, por ejemplo: "datos.csv"
archivo = "datos_pcom_1.csv"

# Si el archivo tiene encabezados "tiempo" y "voltaje"
data = pd.read_csv(archivo)

# === 2. Extraer columnas ===
tiempo = data["tiempo"]
voltaje = data["voltaje"]

# === 3. Graficar ===
plt.figure(figsize=(8, 5))
plt.plot(tiempo, voltaje, label="Voltaje (V)", linewidth=1.5)
plt.xlabel("Tiempo (s)")
plt.ylabel("Voltaje (V)")
plt.title("Gráfica de Voltaje vs Tiempo")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()
