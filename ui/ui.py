import tkinter as tk
from tkinter import Label, Frame, Text, Scrollbar
from PIL import Image, ImageTk
import tkintermapview
import time
import threading
from geopy.distance import distance as geopy_distance
from shapely.geometry import Point, LineString
from math import atan2, degrees
import speech_recognition as sr
from googletrans import Translator
from groundingdino.util.inference import load_model, load_image, predict, annotate
import groundingdino.datasets.transforms as T
import cv2
import numpy as np
import serial
import pynmea2
import googlemaps

# Configurar la API de Google Maps
API_KEY = ""
gmaps = googlemaps.Client(key=API_KEY)

img_pil = None

cap = cv2.VideoCapture(0)  # cámara por defecto

# Crear vector de ruta global
ruta = []

def translate(text, l_o, l_d):
	t = Translator()
	trans = t.translate(text, src=l_o, dest=l_d)
	return trans.text

def video_loop():
    global img_pil
    while True:
        ret, frame = cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(frame_rgb)
            img_tk = ImageTk.PhotoImage(img_pil)

            def update_image():
                image_label.img_tk = img_tk
                image_label.config(image=img_tk)

            image_label.after(0, update_image)
        time.sleep(0.03)  # Aproximadamente 30 FPS

def on_closing():
    cap.release()
    root.destroy()

def escuchar_comando():
    global calculos_ruta, ruta
    
    recognizer = sr.Recognizer()
    mic = sr.Microphone()

    with mic as source:
        recognizer.adjust_for_ambient_noise(source)
        print("🎤 Escuchando...")
        
        try:
            audio = recognizer.listen(source)
            comando = recognizer.recognize_google(audio, language="es-ES").lower()
            print(f"🗣️ Comando detectado: {comando}")
            if "llévame a" in comando.lower():
                consulta = comando.replace("llévame a ", "")
                resultado = buscar_lugar(consulta, lat_actual, lon_actual)
                
                if resultado:
                    obtener_ruta(resultado["latitud"], resultado["longitud"])
                    map_widget.set_path(ruta)
                    map_widget.set_marker(ruta[-1][0], ruta[-1][1], text="Destino")
                    calculos_ruta = True
                else:
                    print("❌ No se encontró ningún lugar con ese nombre.")

            if "busca" in comando:
                transform = T.Compose(
                    [
                        T.RandomResize([800], max_size=1333),
                        T.ToTensor(),
                        T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
                    ]
                )
                image, _ = transform(img_pil, None)
                print("🔍 Buscando...")
                busqueda = comando.replace("busca ", "")
                prompt = translate(busqueda, 'es', 'en')
                boxes, logits, phrases = predict(
                    model=model,
                    image=image,
                    caption=prompt,
                    box_threshold=0.3,
                    text_threshold=0.2
                )  
                # Se muestran los resultados
                annotated_image = annotate(image_source=np.asarray(img_pil), boxes=boxes, logits=logits, phrases=phrases)
                # Se convierte la imagen anotada a formato compatible con Tkinter
                annotated_image_pil = Image.fromarray(cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB))
                annotated_image_tk = ImageTk.PhotoImage(annotated_image_pil)
                # Se muestra la imagen anotada en la interfaz
                annotated_label.config(image=annotated_image_tk)
                annotated_label.img_tk = annotated_image_tk
        except sr.UnknownValueError:
            print("❌ No se entendió el comando.")
        except sr.RequestError as e:
            print(f"🔌 Error con el servicio de reconocimiento: {e}")

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

# Cargar el modelo de GroundingDINO
model = load_model("groundingdino/config/GroundingDINO_SwinT_OGC.py", "weights/groundingdino_swint_ogc.pth")

# Coordenadas iniciales de muestra
lat_actual, lon_actual = 38.650911666666666, -0.8845533333333333
marker_actual = None  # Se definirá después en la interfaz

# Ventana principal
root = tk.Tk()
root.title("Interfaz Grafica")
root.geometry("1300x1100")

# Dividir en tres partes la interfaz usando frames
frame1 = Frame(root, bg="black", width=640, height=360)  # Imagen
frame2 = Frame(root, bg="white", width=640, height=360)  # Mapa
frame3 = Frame(root, bg="gray", width=640, height=360)  # Imagen anotada
frame4 = Frame(root, bg="white", width=640, height=360)  # Indicaciones

label1 = Label(root, text="Vídeo en tiempo real", bg="black", fg="white")
label2 = Label(root, text="Mapa en tiempo real", bg="white", fg="black")
label3 = Label(root, text="Resultados de la deteccion", bg="gray", fg="white")
label4 = Label(root, text="Alertas", bg="white", fg="black")

# Colocarlas sobre los frames correspondientes
label1.grid(row=0, column=0, sticky="nsew", padx=2)
label2.grid(row=0, column=1, sticky="nsew", padx=2)
label3.grid(row=2, column=0, sticky="nsew", padx=2)
label4.grid(row=2, column=1, sticky="nsew", padx=2)

# Mover los frames una fila hacia abajo
frame1.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
frame2.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")
frame3.grid(row=3, column=0, padx=5, pady=5, sticky="nsew")
frame4.grid(row=3, column=1, padx=5, pady=5, sticky="nsew")

# Evitar que los widgets se estiren
root.grid_rowconfigure(0, weight=0)
root.grid_rowconfigure(1, weight=0)
root.grid_columnconfigure(0, weight=0)
root.grid_columnconfigure(1, weight=0)

# Evitar que los frames se ajusten automáticamente a su contenido
frame1.grid_propagate(False)
frame2.grid_propagate(False)
frame3.grid_propagate(False)
frame4.grid_propagate(False)

image_label = Label(frame1)
image_label.pack(fill=tk.BOTH, expand=True)

annotated_label = Label(frame3)
annotated_label.pack(fill=tk.BOTH, expand=True)

# Mapa
map_widget = tkintermapview.TkinterMapView(frame2)
map_widget.pack(fill=tk.BOTH, expand=True)
map_widget.set_zoom(20)
map_widget.set_position(lat_actual, lon_actual)
# Mostrar ubicacion actual
marker_actual = map_widget.set_marker(lat_actual, lon_actual, text="Ubicación Actual")

# Variables de control
waypoint_index = 1
waypoints_alcanzados = set()
umbral_extra = 10.0  # metros adicionales al segmento

# Global
en_desvio = False
calculos_ruta = False

# Cuadro de texto para mostrar las indicaciones en frame4
text_widget = Text(frame4, height=10, wrap="word")
text_widget.pack(side="left", fill="both", expand=True)

def punto_mas_cercano_a_segmento(coord, segmento):
    """Distancia desde coord hasta un segmento de línea."""
    punto = Point(coord[1], coord[0])
    linea = LineString([(segmento[0][1], segmento[0][0]), (segmento[1][1], segmento[1][0])])
    punto_proyectado = linea.interpolate(linea.project(punto))
    return geopy_distance((punto.y, punto.x), (punto_proyectado.y, punto_proyectado.x)).meters

def navegacion_tiempo_real():
    global marker_actual, waypoint_index, lat_actual, lon_actual
    ser = None

    try:
        ser = serial.Serial("/dev/ttyUSB0", 4800, timeout=1)

        while True:
            linea = ser.readline().decode('ascii', errors='replace').strip()
            if any(linea.startswith(prefix) for prefix in ('$GPGGA', '$GNGGA', '$GPRMC', '$GNRMC')):
                try:
                    msg = pynmea2.parse(linea)
                    lat = msg.latitude
                    lon = msg.longitude

                    lat_actual = lat
                    lon_actual = lon

                    # Actualizar en mapa
                    map_widget.set_position(lat, lon)
                    marker_actual.set_position(lat, lon)

                    if calculos_ruta:
                        # Verificar si se ha alcanzado el siguiente waypoint
                        if waypoint_index < len(ruta):
                            wp_lat, wp_lon = ruta[waypoint_index]
                            distancia_wp = geopy_distance((lat, lon), (wp_lat, wp_lon)).meters

                            if distancia_wp < 5.0 and waypoint_index not in waypoints_alcanzados:
                                print(f"✅ Waypoint {waypoint_index} alcanzado")
                                waypoints_alcanzados.add(waypoint_index)
                                waypoint_index += 1

                        # Verificar desvío si vamos de ruta[i-1] -> ruta[i]
                        if waypoint_index > 0 and waypoint_index < len(ruta):
                            wp_lat_or, wp_lon_or = ruta[waypoint_index - 1]
                            wp_lat_des, wp_lon_des = ruta[waypoint_index]
                            
                            desviacion = geopy_distance((lat, lon), (wp_lat_des, wp_lon_des)).meters
                            
                            umbral = geopy_distance((wp_lat_or, wp_lon_or), (wp_lat_des, wp_lon_des)).meters + umbral_extra

                            global en_desvio

                            if desviacion > umbral:
                                (punto_corr, dist_corr, ang_corr) = calcular_correccion(
                                        (lat, lon),
                                        [(wp_lat_or, wp_lon_or), (wp_lat_des, wp_lon_des)]
                                )
                                print(f"Vuelve {dist_corr:.2f}m a {ang_corr:.2f}°")
                                if not en_desvio:
                                    en_desvio = True
                                    mensaje = ("⚠️ Desvío detectado.")
                                    text_widget.delete("1.0", tk.END)
                                    text_widget.insert(tk.END, mensaje)
                            else:
                                if en_desvio:
                                    en_desvio = False
                                    text_widget.delete("1.0", tk.END)
                except pynmea2.ParseError:
                    print("❌ Error al analizar NMEA.")
    except serial.SerialException as e:
        print(f"❌ Error en el puerto serial: {e}")
    finally:
        if ser:
            ser.close()
            print("🔌 Puerto serial cerrado.")

def on_space_pressed(event):
    # Lanzar hilo de escucha por voz
    threading.Thread(target=escuchar_comando, daemon=True).start()

# Lanzar el hilo de la lectura del gps
threading.Thread(target=navegacion_tiempo_real, daemon=True).start()
# Lanzar el hilo de la actualizacion de la camara en tiempo real
threading.Thread(target=video_loop, daemon=True).start()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Luego en la configuración inicial:
root.bind("<space>", on_space_pressed)

# Ejecutar interfaz
root.mainloop()
