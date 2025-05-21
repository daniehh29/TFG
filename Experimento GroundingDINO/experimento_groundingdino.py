import os
import csv
import cv2
from groundingdino.util.inference import load_model, load_image, predict, annotate
from pathlib import Path

# Cargar el modelo
model = load_model("groundingdino/config/GroundingDINO_SwinT_OGC.py", "weights/groundingdino_swint_ogc.pth")

# Directorios
IMAGE_DIR = "images_eval"
OUTPUT_DIR = "outputs_eval"
CSV_PATH = "resultados_experimento.csv"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configuración de prompts y thresholds
prompts = {
    "general": ["vehicle, crosswalk, green pedestrian traffic light, red pedestrian traffic light"]
    #"especifico": ["person crossing the street", "cyclist on the road", "dog walking on a crosswalk", "red pedestrian traffic light", "group of people waiting at the traffic light", "person holding a dog's leash"]
}

thresholds = [0.2, 0.25, 0.3, 0.35, 0.4]

# Obtener lista de imágenes
imagenes = [f for f in os.listdir(IMAGE_DIR) if f.endswith(".jpg") or f.endswith(".png")]

# Preparar CSV
with open(CSV_PATH, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["imagen", "nivel_prompt", "prompt", "box_threshold", "text_threshold", "detecciones", "archivo_salida"])

    # Iterar sobre imágenes, prompts y thresholds
    for imagen in imagenes:
        image_path = os.path.join(IMAGE_DIR, imagen)
        image_source, image = load_image(image_path)

        for nivel, prompts_lista in prompts.items():
            for prompt in prompts_lista:
                for threshold in thresholds:
                    boxes, logits, phrases = predict(
                        model=model,
                        image=image,
                        caption=prompt,
                        box_threshold=threshold,
                        text_threshold=0.2
                    )

                    output_name = f"{Path(imagen).stem}_{nivel}_{prompt[:15].replace(' ', '_')}_thr{threshold}.jpg"
                    output_path = os.path.join(OUTPUT_DIR, output_name)

                    annotated_frame = annotate(image_source=image_source, boxes=boxes, logits=logits, phrases=phrases)
                    cv2.imwrite(output_path, annotated_frame)

                    writer.writerow([imagen, nivel, prompt, threshold, 0.2, len(boxes), output_name])
