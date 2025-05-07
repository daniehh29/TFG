import tkinter as tk
from tkinter import Label, Frame, Text, Scrollbar
from PIL import Image, ImageTk
from googletrans import Translator
from groundingdino.util.inference import load_model, load_image, predict, annotate
import cv2
import threading
import tkintermapview
import speech_recognition as sr
import googlemaps
from geopy.distance import geodesic
import numpy as np
from shapely.geometry import Point, LineString
from math import atan2, degrees
from geopy.distance import distance as geopy_distance

# El índice actual en la lista de checkpoints
waypoint_index = 1

# Configurar la API de Google Maps
API_KEY = "AIzaSyBEZvL3tGskyLHol63YZ4-z39AxAZuPgBI"
gmaps = googlemaps.Client(key=API_KEY)

# Cargar el modelo de GroundingDINO
model = load_model("groundingdino/config/GroundingDINO_SwinT_OGC.py", "weights/groundingdino_swint_ogc.pth")

# Coordenadas iniciales de muestra
lat_actual, lon_actual = 38.632786091443634, -0.8661588316334603
marker_actual = None  # Se definirá después en la interfaz

# Ruta de la imagen de muestra
IMAGE_PATH = "images/test-4.jpg"

# Cargar la imagen para GroundingDINO
image_source, image = load_image(IMAGE_PATH)

# Crear vector de checkpoints global
checkpoints = []

# Crear ventana principal
root = tk.Tk()
root.title("Tormes UI")
root.geometry("900x500")

# Dividir en tres partes la interfaz usando frames
frame1 = Frame(root, bg="black")  # Imagen
frame2 = Frame(root, bg="white")  # Mapa
frame4 = Frame(root, bg="white")  # Indicaciones

frame1.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
frame2.grid(row=0, column=1, rowspan=2, padx=5, pady=5, sticky="nsew")  # Ocupa ambas filas de la columna 1
frame4.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

# Configurar las columnas y filas para que se ajusten al tamaño de la ventana
root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

# Cargar y mostrar la imagen
img = Image.open(IMAGE_PATH)
img_tk = ImageTk.PhotoImage(img)

image_label = Label(frame1, image=img_tk)
image_label.img_tk = img_tk 
image_label.pack(fill=tk.BOTH, expand=True)

# Mapa que muestra coordenadas actuales
map_widget = tkintermapview.TkinterMapView(frame2)
map_widget.pack(fill=tk.BOTH, expand=True)
map_widget.set_position(lat_actual, lon_actual)
marker_actual = map_widget.set_marker(lat_actual, lon_actual, text="Ubicación Actual")

# Cuadro de texto para mostrar las indicaciones en frame4
text_widget = Text(frame4, height=10, wrap="word")
text_widget.pack(side="left", fill="both", expand=True)

# Añadir una scrollbar al cuadro de texto
scrollbar = Scrollbar(frame4, command=text_widget.yview)
scrollbar.pack(side="right", fill="y")
text_widget.config(yscrollcommand=scrollbar.set)

def calcular_correccion(coord_actual, segmento):
    punto = Point(coord_actual[1], coord_actual[0])
    linea = LineString([(segmento[0][1], segmento[0][0]), (segmento[1][1], segmento[1][0])])
    punto_proyectado = linea.interpolate(linea.project(punto))

    # Coordenadas del punto más cercano sobre la ruta
    lat_corr = punto_proyectado.y
    lon_corr = punto_proyectado.x

    # Vector de corrección
    delta_lat = lat_corr - coord_actual[0]
    delta_lon = lon_corr - coord_actual[1]

    # Dirección de corrección (en grados)
    angulo_rad = atan2(delta_lat, delta_lon)
    angulo_deg = degrees(angulo_rad)

    # Distancia a corregir
    distancia = geopy_distance(coord_actual, (lat_corr, lon_corr)).meters

    return (lat_corr, lon_corr), distancia, angulo_deg

def seguimiento_ruta():
    global waypoint_index, lat_actual, lon_actual, checkpoints

    while True:
        if len(checkpoints) >= 2 and waypoint_index < len(checkpoints) - 1:
            actual = (lat_actual, lon_actual)
            siguiente = checkpoints[waypoint_index + 1]

            # Si estás cerca del siguiente waypoint, avanzar
            if geopy_distance(actual, siguiente).meters < 5:
                print(f"✅ Waypoint {waypoint_index + 1} alcanzado.")
                waypoint_index += 1
                continue

            # Calcular corrección
            (lat_corr, lon_corr), desviacion, angulo = calcular_correccion(actual, (checkpoints[waypoint_index], siguiente))

            print(f"📐 Desviación: {desviacion:.2f} m | Corrección: {angulo:.1f}° hacia ({lat_corr:.6f}, {lon_corr:.6f})")
        
        time.sleep(1.5)

def actualizar_gps_en_tiempo_real(puerto="/dev/ttyUSB0", baudrate=4800):
    import serial
    import pynmea2

    global lat_actual, lon_actual, marker_actual

    ser = None
    try:
        ser = serial.Serial(puerto, baudrate, timeout=1)
        print(f"📡 Escuchando GPS en {puerto}...")

        while True:
            linea = ser.readline().decode('ascii', errors='replace').strip()
            if any(linea.startswith(prefix) for prefix in ('$GPGGA', '$GNGGA', '$GPRMC', '$GNRMC')):
                try:
                    msg = pynmea2.parse(linea)
                    nueva_lat = msg.latitude
                    nueva_lon = msg.longitude

                    if nueva_lat and nueva_lon:
                        lat_actual = nueva_lat
                        lon_actual = nueva_lon

                        # Actualizar el marcador en el hilo de Tkinter
                        root.after(0, actualizar_marcador_en_mapa, nueva_lat, nueva_lon)
                except pynmea2.ParseError:
                    print("❌ Error al analizar NMEA.")
    except serial.SerialException as e:
        print(f"❌ Error en el puerto serial: {e}")
    finally:
        if ser:
            ser.close()
            print("🔌 Puerto serial cerrado.")

def actualizar_marcador_en_mapa(lat, lon):
    global marker_actual
    map_widget.set_position(lat, lon)

    if marker_actual:
        marker_actual.set_position(lat, lon)
    else:
        marker_actual = map_widget.set_marker(lat, lon, text="Ubicación Actual")

def buscar_lugar(query, lat, lon, radio=5000):
    """Busca un lugar usando Google Places API."""
    results = gmaps.places(query=query, location=(lat, lon), radius=radio)

    if "results" in results and len(results["results"]) > 0:
        lugar = results["results"][0]
        return {
            "nombre": lugar["name"],
            "direccion": lugar.get("formatted_address", "Dirección no disponible"),
            "latitud": lugar["geometry"]["location"]["lat"],
            "longitud": lugar["geometry"]["location"]["lng"]
        }
    return None

def obtener_ruta(destino_lat, destino_lon):
    """Calcula la ruta y muestra las indicaciones en la interfaz."""

    # Se limpia la ruta anteriormente mostrada
    map_widget.delete_all_path()

    ruta = gmaps.directions((lat_actual, lon_actual), (destino_lat, destino_lon), mode="walking")

    if ruta:
        steps = ruta[0]["legs"][0]["steps"]

        # Se muestra la ruta en el mapa
        waypoints = [(lat_actual, lon_actual)]
        for step in steps:
            end_location = step["end_location"]
            waypoints.append((end_location["lat"], end_location["lng"]))

        global checkpoints
        # Se guardan los puntos de la ruta
        checkpoints = waypoints.copy()

        map_widget.set_path(waypoints)

        # Se muestran las indicaciones en el cuadro de texto
        text_widget.delete(1.0, tk.END)

        for i, step in enumerate(steps):
            instruction = step["html_instructions"].replace("<b>", "").replace("</b>", "").replace("<div>", "").replace("</div>", "")
            # Se traduce la instruccion a español
            instruccion = translate(instruction, 'en', 'es')
            distance = step["distance"]["text"]
            text_widget.insert(tk.END, f"{i+1}. {instruccion} ({distance})\n\n")

def escuchar_comando():
    """Reconoce comandos de voz y ejecuta acciones según el mensaje."""
    r = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        r.adjust_for_ambient_noise(source)
        print("🎤 Escuchando...")

        try:
            audio = r.listen(source, timeout=20)
            text = r.recognize_google(audio, language="es-ES")
            print(f"🔊 Has dicho: {text}")
            return text.lower()

        except sr.UnknownValueError:
            print("❌ No te entendí.")
            return ""
        
        except sr.RequestError as e:
            print(f"❌ Error en la petición: {e}")
            return ""

def translate(text, l_o, l_d):
	t = Translator()
	trans = t.translate(text, src=l_o, dest=l_d)
	return trans.text

def procesar_voz():
    """Espera comandos de voz y busca rutas si se solicita."""
    comando = "tormes"

    while True:
        texto = escuchar_comando()
        
        if comando in texto:
            print("🐶 ¡Activado!")
            orden = escuchar_comando()
            
            if "llévame a" in orden:
                print("📍 Buscando destino...")
                consulta = orden.replace("llévame a ", "")
                resultado = buscar_lugar(consulta, lat_actual, lon_actual)

                if resultado:
                    print(f"🗺️ Destino encontrado: {resultado['nombre']} ({resultado['direccion']})")
                    obtener_ruta(resultado["latitud"], resultado["longitud"])
                else:
                    print("❌ No se encontró ningún lugar con ese nombre.")

            if "busca" in orden:
                print("🔍 Buscando...")

                busqueda = orden.replace("busca ", "")

                prompt = translate(busqueda, 'es', 'en')

                boxes, logits, phrases = predict(
				    model=model,
				    image=image,
				    caption=prompt,
				    box_threshold=0.4,
					text_threshold=0.35
				)
					
				# Se muestran los resultados
                annotated_image = annotate(image_source=image_source, boxes=boxes, logits=logits, phrases=phrases)

                # Se convierte la imagen anotada a formato compatible con Tkinter
                annotated_image_pil = Image.fromarray(cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB))
                annotated_image_tk = ImageTk.PhotoImage(annotated_image_pil)

                # Se muestra la imagen anotada en la interfaz
                image_label.config(image=annotated_image_tk)
                image_label.img_tk = annotated_image_tk

# Se inician hilos paralelos para voz, GPS y seguimiento de ruta
threading.Thread(target=procesar_voz, daemon=True).start()
threading.Thread(target=actualizar_gps_en_tiempo_real, daemon=True).start()
threading.Thread(target=seguimiento_ruta, daemon=True).start()

# Se ejecuta el bucle principal de la interfaz
root.mainloop()
