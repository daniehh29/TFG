import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

thresholds = [0.2, 0.25, 0.3, 0.35, 0.4]
entidades = ["semáforo rojo", "semáforo verde", "paso de cebra", "vehículo"]

# Detecciones correctas
detecciones = {
    "semáforo rojo": [1,0,0,0,0],
    "semáforo verde": [0,0,0,0,0],
    "paso de cebra": [2,2,1,1,0],
    "vehículo": [1,0,0,0,0]
}

# Parámetros para posicionar barras agrupadas
x = np.arange(len(thresholds))  # posiciones base de los grupos
bar_width = 0.2

fig, ax = plt.subplots(figsize=(10, 6))

for i, entidad in enumerate(entidades):
    desplazamiento = i * bar_width - (bar_width * 1.5)  # centra las barras
    ax.bar(x + desplazamiento, detecciones[entidad], width=bar_width, label=entidad)

ax.set_xticks(x)
ax.set_xticklabels(thresholds)
ax.set_xlabel("Threshold")
ax.set_ylabel("Detecciones correctas")
ax.set_title("")
ax.legend()
ax.grid(True, axis='y')
plt.tight_layout()
plt.show()

# Datos
falsos_positivos = [2,1,0,0,0]
falsos_negativos = [0,1,1,1,1]
x = np.arange(len(thresholds))  # Posiciones en el eje x
bar_width = 0.35

# Gráfico combinado
plt.figure(figsize=(10, 5))
plt.bar(x - bar_width/2, falsos_positivos, width=bar_width, color='tomato', label='Falsos positivos')
plt.bar(x + bar_width/2, falsos_negativos, width=bar_width, color='blue', label='Falsos negativos')

# Configuración
plt.title("")
plt.xlabel("Threshold")
plt.ylabel("Cantidad")
plt.xticks(x, [str(t) for t in thresholds])
plt.legend()
plt.grid(axis='y')
plt.tight_layout()
plt.show()

# Filas = Fotos 1 a 5, Columnas = Thresholds
# Valores de ejemplo (0: mal, 3: excelente detección)
scores = np.array([
    [0, 0, 1, 2, 3],  # Foto 1
    [1, 2, 2, 3, 2],  # Foto 2
    [1, 1, 1, 3, 3],  # Foto 3
    [0, 0, 3, 1, 1],  # Foto 4
    [0, 1, 1, 1, 0],  # Foto 5
])

plt.figure(figsize=(10, 5))
sns.heatmap(scores, annot=True, cmap="YlGnBu", xticklabels=thresholds, yticklabels=[f"Foto {i}" for i in range(1, 6)])
plt.title("Calidad de detección por foto y threshold (0–3)")
plt.xlabel("Threshold")
plt.ylabel("Imagen")
plt.tight_layout()
plt.show()
