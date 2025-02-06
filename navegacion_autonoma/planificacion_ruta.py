# import libraries
import googlemaps
import folium
import csv

# prepare API
gmaps = googlemaps.Client(key="API-key")
# eps 3 entrada eps 2
# (38.38717735745423, -0.5122577483285744)
# eps 3 entrada eps 1
# (38.38669284754157, -0.5118640102682578)

origin = (38.38717735745423, -0.5122577483285744)
destiny = (38.38669284754157, -0.5118640102682578)

# get route
route = gmaps.directions(origin, destiny, mode="walking")

coordenadas = []

if route:
    # draw map
    map = folium.Map(location=origin, zoom_start=25)

    coordenadas.append(origin)

    # add the origin marker to the map
    marker = folium.Marker(location=origin).add_to(map)

    # get steps of the route
    steps = route[0]["legs"][0]["steps"]

    # for each step...
    for step in steps:
        # add the marker for current step into the map
        marker = folium.Marker(location=(step["end_location"]["lat"], step["end_location"]["lng"])).add_to(map)
        # add the line for the route segment connecting current to next step into the map
        line = folium.PolyLine(locations=[(step["start_location"]["lat"], step["start_location"]["lng"]), (step["end_location"]["lat"], step["end_location"]["lng"])]).add_to(map)
        coordenadas.append((step["end_location"]["lat"], step["end_location"]["lng"]))

    # save the coordinates
    with open("ruta_eps3_corta.csv", "w", newline="") as file:
        writer = csv.writer(file)
        for coord in coordenadas:
            writer.writerow(coord)
    # save the map
    map.save("ruta_eps3_corta.html")
