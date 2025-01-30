# import libraries
import googlemaps
import folium

# prepare API
gmaps = googlemaps.Client(key="AIzaSyBEZvL3tGskyLHol63YZ4-z39AxAZuPgBI")

# eps 1
origin = (38.386884064791204, -0.511243216267247)
# club social 1
destiny = (38.384541941033376, -0.5162267605152372)

# get route
route = gmaps.directions(origin, destiny, mode="walking")


if route:
    # draw map
    map = folium.Map(location=origin, zoom_start=13)

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

    # save the map
    map.save("map.html")