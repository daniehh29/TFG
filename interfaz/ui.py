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

# 🔹 Configurar la API de Google Maps
API_KEY = "AIzaSyBEZvL3tGskyLHol63YZ4-z39AxAZuPgBI"
gmaps = googlemaps.Client(key=API_KEY)

# load the model
model = load_model("groundingdino/config/GroundingDINO_SwinT_OGC.py", "weights/groundingdino_swint_ogc.pth")

# 🔹 Coordenadas iniciales (simulación, puedes conectar con GPS real)
lat_actual, lon_actual = 38.632786091443634, -0.8661588316334603

# 🔹 Ruta de la imagen
IMAGE_PATH = "images/test-4.jpg"

# load the image
image_source, image = load_image(IMAGE_PATH)

# 🔹 Crear ventana principal
root = tk.Tk()
root.title("Tormes UI")
root.geometry("900x500")

# 🔹 Dividir en tres partes usando frames (eliminando frame3)
frame1 = Frame(root, bg="black")  # Imagen
frame2 = Frame(root, bg="white")  # Mapa con GPS
frame4 = Frame(root, bg="white")  # Instrucciones paso a paso

frame1.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
frame2.grid(row=0, column=1, rowspan=2, padx=5, pady=5, sticky="nsew")  # Ocupa ambas filas de la columna 1
frame4.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

# 🔹 Configurar las columnas y filas para que se ajusten al tamaño de la ventana
root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)

# 🔹 Cargar y mostrar la imagen
img = Image.open(IMAGE_PATH)
img_tk = ImageTk.PhotoImage(img)

image_label = Label(frame1, image=img_tk)
image_label.img_tk = img_tk  # Mantener referencia para evitar que se recoja por el garbage collector
image_label.pack(fill=tk.BOTH, expand=True)

# 🔹 Mapa con coordenadas actuales
map_widget = tkintermapview.TkinterMapView(frame2)
map_widget.pack(fill=tk.BOTH, expand=True)
map_widget.set_position(lat_actual, lon_actual)
marker_actual = map_widget.set_marker(lat_actual, lon_actual, text="Ubicación Actual")

# 🔹 Cuadro de texto para direcciones en frame4
text_widget = Text(frame4, height=10, wrap="word")
text_widget.pack(side="left", fill="both", expand=True)

# 🔹 Scrollbar
scrollbar = Scrollbar(frame4, command=text_widget.yview)
scrollbar.pack(side="right", fill="y")
text_widget.config(yscrollcommand=scrollbar.set)

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

    # 🔹 LIMPIAR RUTA ANTERIOR
    map_widget.delete_all_path()

    ruta = gmaps.directions((lat_actual, lon_actual), (destino_lat, destino_lon), mode="walking")

    if ruta:
        steps = ruta[0]["legs"][0]["steps"]

        # 🔹 Mostrar ruta en el mapa
        waypoints = [(lat_actual, lon_actual)]
        for step in steps:
            end_location = step["end_location"]
            waypoints.append((end_location["lat"], end_location["lng"]))

        map_widget.set_path(waypoints)

        # 🔹 Mostrar indicaciones en `frame4`
        text_widget.delete(1.0, tk.END)

        for i, step in enumerate(steps):
            instruction = step["html_instructions"].replace("<b>", "").replace("</b>", "").replace("<div>", "").replace("</div>", "")
            distance = step["distance"]["text"]
            text_widget.insert(tk.END, f"{i+1}. {instruction} ({distance})\n\n")

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
					
				# se muestran los resultados
                annotated_image = annotate(image_source=image_source, boxes=boxes, logits=logits, phrases=phrases)

                # Convertir la imagen anotada a formato compatible con Tkinter
                annotated_image_pil = Image.fromarray(cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB))
                annotated_image_tk = ImageTk.PhotoImage(annotated_image_pil)

                # Mostrar la imagen anotada en la interfaz
                image_label.config(image=annotated_image_tk)
                image_label.img_tk = annotated_image_tk  # Mantener referencia para evitar que se recoja por el garbage collector

# 🔹 Iniciar el reconocimiento de voz en un hilo aparte
threading.Thread(target=procesar_voz, daemon=True).start()

# 🔹 Ejecutar interfaz
root.mainloop()
