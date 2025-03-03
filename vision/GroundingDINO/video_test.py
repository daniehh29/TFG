# TEST WITH VIDEOS (CPU)
# https://github.com/IDEA-Research/GroundingDINO
# libraries
from groundingdino.util.inference import load_model, predict, annotate
import groundingdino.datasets.transforms as T
import cv2
import torch
import numpy as np
from PIL import Image

# Cargar el modelo en CPU
model = load_model("groundingdino/config/GroundingDINO_SwinT_OGC.py", "weights/groundingdino_swint_ogc.pth")

# Parámetros
VIDEO_PATH = "videos/test_1.mp4"
OUTPUT_PATH = "videos/result_1.mp4"
TEXT_PROMPT = "traffic light"
BOX_TRESHOLD = 0.35
TEXT_TRESHOLD = 0.25

# Abrir el video
cap = cv2.VideoCapture(VIDEO_PATH)

# Verificar si el video se abrió correctamente
if not cap.isOpened():
    print("Error al abrir el video")
    exit()

# Obtener propiedades del video
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
fps = cap.get(cv2.CAP_PROP_FPS)

# Definir el codec y crear el objeto VideoWriter
out = cv2.VideoWriter(OUTPUT_PATH, cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame_width, frame_height))

# Transformación para preprocesar cada frame
def preprocess_frame(frame):
    transform = T.Compose(
        [
            T.RandomResize([800], max_size=1333),
            T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ]
    )
    
    image_source = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    image = np.asarray(image_source)
    image_transformed, _ = transform(image_source, None)
    
    return image_transformed

while cap.isOpened():
    # Leer frame a frame
    ret, frame = cap.read()
    if not ret:
        break

    # Preprocesar el frame
    image_tensor = preprocess_frame(frame)

    # Hacer predicciones
    boxes, logits, phrases = predict(
        model=model,
        image=image_tensor,
        caption=TEXT_PROMPT,
        box_threshold=BOX_TRESHOLD,
        text_threshold=TEXT_TRESHOLD
    )

    # Anotar el frame
    annotated_frame = annotate(image_source=frame, boxes=boxes, logits=logits, phrases=phrases)

    # Escribir el frame en el video de salida
    out.write(annotated_frame)

# Liberar recursos
cap.release()
out.release()
cv2.destroyAllWindows()
