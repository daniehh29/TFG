import googlemaps

# Configurar la API Key de Google
gmaps = googlemaps.Client(key="")

def buscar_lugar(query, lat, lon, radio=5000):
    """
    Busca un lugar usando la API de Google Places con la librería googlemaps.
    
    query: (str) descripción del lugar (ejemplo: "restaurante más cercano", "Mercadona del centro").
    lat, lon: (float) coordenadas actuales del usuario.
    radio: (int) radio de búsqueda en metros, por defecto 5kms
    """
    # Realizar la búsqueda en Google Places
    results = gmaps.places(query=query, location=(lat, lon), radius=radio)

    if "results" in results and len(results["results"]) > 0:
        lugar = results["results"][0]  # Primer resultado
        nombre = lugar["name"]
        direccion = lugar.get("formatted_address", "Dirección no disponible")
        latitud = lugar["geometry"]["location"]["lat"]
        longitud = lugar["geometry"]["location"]["lng"]

        return {
            "nombre": nombre,
            "direccion": direccion,
            "latitud": latitud,
            "longitud": longitud
        }
    else:
        return None


# Coordenadas actuales
origen = (38.38717735745423, -0.5122577483285744)
consulta = "The nearest restaurant"

resultado = buscar_lugar(consulta, origen[0], origen[1])
print(resultado if resultado else "No se encontró ningún lugar.")
