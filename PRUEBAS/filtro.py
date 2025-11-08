# === filtro_seguro.py ===
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import butter, filtfilt, medfilt

# === 1. Leer el archivo CSV ===
archivo_csv = r"test.csv"
datos = pd.read_csv(archivo_csv)

# Extraer los valores como lista o arreglo
valores = datos["Voltage"].values
rango = 0.01
for i in range(len(valores)):
    if i <= rango:
        valores[i] = 0
    elif i > rango:
        valores[i] = 2

tiempo = np.arange(len(valores))

plt.plot(tiempo, valores)
plt.show()
