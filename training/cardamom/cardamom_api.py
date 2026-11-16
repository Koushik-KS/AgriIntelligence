
from pathlib import Path
import io

import numpy as np
import tensorflow as tf
from PIL import Image, UnidentifiedImageError
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware


# ---------------- PATHS ----------------
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "results" / "cardamom_mobilenetv2_finetuned.keras"


# ---------------- SETTINGS ----------------
IMAGE_SIZE = (224, 224)
MAX_FILE_SIZE = 5 * 1024 * 1024

CLASS_NAMES = [
    "HEALTHY",
    "BLIGHT",
    "PHYLOSTICTA",
]

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

ALLOWED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP"}


# ---------------- FASTAPI APP ----------------
app = FastAPI(title="KisanVision AI - Cardamom Prediction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


model = None


# ---------------- LOAD MODEL ----------------
@app.on_event("startup")
def load_model():
    global model

    if not MODEL_PATH.is_file():
        raise RuntimeError(f"Cardamom model is missing: {MODEL_PATH}")

    loaded_model = tf.keras.models.load_model(MODEL_PATH)

    output_shape = loaded_model.output_shape

    if (
        not isinstance(output_shape, tuple)
        or output_shape[-1] != len(CLASS_NAMES)
    ):
        raise RuntimeError(
            "Cardamom model output does not match the three classes."
        )

    model = loaded_model

    print("Cardamom model loaded successfully.")
    print(f"Model: {MODEL_PATH.name}")
    print(f"Classes: {CLASS_NAMES}")


# ---------------- HEALTH CHECK ----------------
@app.get("/health")
def health():
    return {
        "success": True,
        "service": "KisanVision AI Cardamom API",
        "model_loaded": model is not None,
        "model_name": MODEL_PATH.name,
        "classes": CLASS_NAMES,
    }


# ---------------- CARDAMOM PREDICTION ----------------
@app.post("/predict/cardamom")
async def predict_cardamom(file: UploadFile = File(...)):

    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Cardamom model is not loaded.",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Upload a JPG, PNG, or WebP image.",
        )

    try:
        image_bytes = await file.read(MAX_FILE_SIZE + 1)

        if not image_bytes:
            raise HTTPException(
                status_code=400,
                detail="The uploaded image is empty.",
            )

        if len(image_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail="Image exceeds the 5 MB limit.",
            )

        try:
            with Image.open(io.BytesIO(image_bytes)) as source:

                if source.format not in ALLOWED_IMAGE_FORMATS:
                    raise HTTPException(
                        status_code=400,
                        detail="Unsupported image format.",
                    )

                source.load()

                image_array = np.asarray(
                    source.convert("RGB"),
                    dtype=np.uint8,
                )

                image_array = tf.image.resize(
                    image_array,
                    IMAGE_SIZE,
                    method="bilinear",
                )

                image_array = image_array.numpy().astype(np.float32)

        except UnidentifiedImageError:
            raise HTTPException(
                status_code=400,
                detail="The uploaded file is not a valid image.",
            )

        except OSError:
            raise HTTPException(
                status_code=400,
                detail="The uploaded image could not be read.",
            )

        # MobileNetV2 preprocessing
        image_array = preprocess_input(image_array)

        image_array = np.expand_dims(image_array, axis=0)

        predictions = model.predict(
            image_array,
            verbose=0,
        )[0]

        if (
            len(predictions) != len(CLASS_NAMES)
            or not np.all(np.isfinite(predictions))
        ):
            raise HTTPException(
                status_code=500,
                detail="The model returned invalid prediction output.",
            )

        best_index = int(np.argmax(predictions))

        return {
            "success": True,
            "crop": "Cardamom",
            "predicted_class": CLASS_NAMES[best_index],
            "confidence": round(
                float(predictions[best_index]) * 100, 2
            ),
            "probabilities": {
                name: round(float(predictions[index]) * 100, 4)
                for index, name in enumerate(CLASS_NAMES)
            },
            "warning": (
                "Prediction is experimental and must be verified. "
                "Confidence is not a confirmed diagnosis."
            ),
        }

    finally:
        await file.close()
