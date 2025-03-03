# TEST WITH IMAGES (CPU)
# https://github.com/IDEA-Research/GroundingDINO
# libraries
from groundingdino.util.inference import load_model, load_image, predict, annotate
import cv2

# load the model
model = load_model("groundingdino/config/GroundingDINO_SwinT_OGC.py", "weights/groundingdino_swint_ogc.pth")

# parameters
IMAGE_PATH = "images/test.jpg"
OUTPUT_PATH = "images/result.jpg"
TEXT_PROMPT = "traffic light"
BOX_TRESHOLD = 0.35
TEXT_TRESHOLD = 0.25

# load the image
image_source, image = load_image(IMAGE_PATH)

# make predictions
boxes, logits, phrases = predict(
    model=model,
    image=image,
    caption=TEXT_PROMPT,
    box_threshold=BOX_TRESHOLD,
    text_threshold=TEXT_TRESHOLD
)

# show the results
annotated_frame = annotate(image_source=image_source, boxes=boxes, logits=logits, phrases=phrases)
cv2.imwrite(OUTPUT_PATH, annotated_frame)
