import folium

# Crear el mapa centrado en la posicion 1
mapa = folium.Map(location=[38.6509072, -0.8848098], zoom_start=20)

# Lista de posiciones con sus coordenadas (latitud, longitud)
lugares = [
    ("Posición 1", 38.6509072, -0.8848098),
    ("Posición 2", 38.6507737, -0.8849808),
    ("Posición 3", 38.6510224, -0.8850861),
    ("Posición 4", 38.6510710, -0.8848389),
    ("Posición 5", 38.6509726, -0.8845701)
]

# Añadir marcadores al mapa
for nombre, lat, lon in lugares:
    folium.Marker(
        location=[lat, lon],
        popup=nombre,
        icon=folium.Icon(color="blue", icon="info-sign")
    ).add_to(mapa)

# Guardar el mapa en un archivo HTML
mapa.save("mapa_con_marcadores.html")
