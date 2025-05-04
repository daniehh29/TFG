import os
import re
import pandas as pd
import matplotlib.pyplot as plt
from geopy.distance import geodesic

# Coordenadas reales (referencia del móvil)
puntos_reales = [
    (38.6509072, -0.8848098),
    (38.6507737, -0.8849808),
    (38.6510224, -0.8850861),
    (38.6510710, -0.8848389),
    (38.6509726, -0.8845701)
]

# Inicializar resultados
resultados = []

# Procesar cada archivo
for i in range(1, 6):
    archivo = f'posicion{i}.txt'
    latitudes = []
    longitudes = []

    with open(archivo, 'r') as f:
        for linea in f:
            match = re.search(r'Latitud:\s*([-\d.]+),\s*Longitud:\s*([-\d.]+)', linea)
            if match:
                latitudes.append(float(match.group(1)))
                longitudes.append(float(match.group(2)))

    # Promedio de coordenadas GPS
    lat_prom = sum(latitudes) / len(latitudes)
    lon_prom = sum(longitudes) / len(longitudes)

    # Coordenadas reales
    lat_ref, lon_ref = puntos_reales[i - 1]

    # Error
    error_m = geodesic((lat_prom, lon_prom), (lat_ref, lon_ref)).meters

    # Guardar resultados
    resultados.append({
        'Punto': f'Posición {i}',
        'Latitud promedio': lat_prom,
        'Longitud promedio': lon_prom,
        'Latitud real': lat_ref,
        'Longitud real': lon_ref,
        'Error (m)': round(error_m, 2)
    })

# Crear DataFrame y guardar
df = pd.DataFrame(resultados)
df.to_csv('errores_gps.csv', index=False)
print(df)

# Graficar
plt.figure(figsize=(8, 5))
plt.bar(df['Punto'], df['Error (m)'], color='skyblue')
plt.ylabel('Error (metros)')
plt.title('Error de posición GPS por punto')
plt.grid(axis='y')
plt.tight_layout()
plt.savefig('error_gps_barras.png')
plt.show()
