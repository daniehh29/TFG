import speech_recognition as sr
from googletrans import Translator
from groundingdino.util.inference import load_model, load_image, predict, annotate
import cv2
import googlemaps
import folium
import webbrowser

# Configurar la API Key de Google
gmaps = googlemaps.Client(key="AIzaSyBEZvL3tGskyLHol63YZ4-z39AxAZuPgBI")

# load the model
model = load_model("groundingdino/config/GroundingDINO_SwinT_OGC.py", "weights/groundingdino_swint_ogc.pth")

# parameters
IMAGE_PATH = "images/test-4.jpg"
OUTPUT_PATH = "images/result.jpg"
BOX_TRESHOLD = 0.40
TEXT_TRESHOLD = 0.35

# load the image
image_source, image = load_image(IMAGE_PATH)

# Coordenadas actuales
origen = (38.632786091443634, -0.8661588316334603)

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

def listen(l):
	r = sr.Recognizer()
	mic = sr.Microphone()

	with mic as source:
		r.adjust_for_ambient_noise(source)
		print("Escuchando...")
		audio = r.listen(source)
		
		try:
			text = r.recognize_google(audio, language=l)
			print(text)
			print("Has dicho: ", text)
			return text
		except sr.UnknownValueError:
			print("No te he entendido")
			return ""
		except sr.RequestError as e:
			print("No he podido realizar la petición: ", e)
			return ""

def translate(text, l_o, l_d):
	t = Translator()

	trans = t.translate(text, src=l_o, dest=l_d)
	print(trans)
	print("Has dicho: ", trans.text)
	return trans.text

if __name__ == "__main__":
	command = "tormes"
	
	# se lee la imagen original
	annotated_frame = cv2.imread(IMAGE_PATH)
    
	while True:
		cv2.imshow("Imagen Original", annotated_frame)
		cv2.waitKey(1)  # Para que se vea la imagen
		
		text = listen('es-ES')
		if command in text.lower():
			print("Guau Guau")
			note = listen('es-ES')
			if note:
				if "busca" in note.lower():
					print("BUSCO")
					
					note_translated = translate(note, 'es', 'en')

					boxes, logits, phrases = predict(
					    model=model,
					    image=image,
					    caption=note_translated,
					    box_threshold=BOX_TRESHOLD,
					    text_threshold=TEXT_TRESHOLD
					)
					
					# se muestran los resultados
					annotated_frame = annotate(image_source=image_source, boxes=boxes, logits=logits, phrases=phrases)
					
					print("HECHO")
				if "llévame a" in note.lower():
					print("TE LLEVO")
					consulta = note.replace("llévame a ", "")
					resultado = buscar_lugar(consulta, origen[0], origen[1])

					if resultado:
						destino = (resultado["latitud"], resultado["longitud"])
						print(destino)
						# get route
						route = gmaps.directions(origen, destino, mode="walking")

						if route:
							# draw map
							map = folium.Map(location=origen, zoom_start=25)

							# get steps of the route
							steps = route[0]["legs"][0]["steps"]

							# for each step...
							for step in steps:
								# add the marker for current step into the map
								marker = folium.Marker(location=(step["end_location"]["lat"], step["end_location"]["lng"])).add_to(map)
								# add the line for the route segment connecting current to next step into the map
								line = folium.PolyLine(locations=[(step["start_location"]["lat"], step["start_location"]["lng"]), (step["end_location"]["lat"], step["end_location"]["lng"])]).add_to(map)

							# save the map
							path = "maps/" + consulta + ".html"
							map.save(path)
							webbrowser.open(path)
					else:
						print("No se encontró ningun lugar")
					
		# Presiona 'q' para cerrar la ventana de OpenCV
		if cv2.waitKey(1) & 0xFF == ord('q'):
		    break

	cv2.destroyAllWindows()  # Cerrar todas las ventanas de OpenCV