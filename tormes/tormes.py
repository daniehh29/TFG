import speech_recognition as sr
from googletrans import Translator
from groundingdino.util.inference import load_model, load_image, predict, annotate
import cv2

# load the model
model = load_model("groundingdino/config/GroundingDINO_SwinT_OGC.py", "weights/groundingdino_swint_ogc.pth")

# parameters
IMAGE_PATH = "images/test-4.jpg"
OUTPUT_PATH = "images/result.jpg"
BOX_TRESHOLD = 0.40
TEXT_TRESHOLD = 0.35

# load the image
image_source, image = load_image(IMAGE_PATH)

def listen(l):
	r = sr.Recognizer()
	t = Translator()
	
	mic = sr.Microphone()

	with mic as source:
		r.adjust_for_ambient_noise(source)
		print("Escuchando...")
		audio = r.listen(source)
		
		try:
			text = r.recognize_google(audio, language=l)
			trans = t.translate(text, src="es", dest="en")
			print(trans)
			print("Has dicho: ", trans.text)
			return trans.text
			
		except sr.UnknownValueError:
			print("No te he entendido")
			return ""
		except sr.RequestError as e:
			print("No he podido realizar la petición: ", e)
			return ""
			
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
				if "find" in note.lower():
					print("BUSCO")
					# make predictions
					boxes, logits, phrases = predict(
					    model=model,
					    image=image,
					    caption=note,
					    box_threshold=BOX_TRESHOLD,
					    text_threshold=TEXT_TRESHOLD
					)
					
					# show the results
					annotated_frame = annotate(image_source=image_source, boxes=boxes, logits=logits, phrases=phrases)
					
					print("HECHO")
		# Presiona 'q' para cerrar la ventana de OpenCV
		if cv2.waitKey(1) & 0xFF == ord('q'):
		    break

	cv2.destroyAllWindows()  # Cerrar todas las ventanas de OpenCV
