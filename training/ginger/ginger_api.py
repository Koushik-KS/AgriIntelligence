
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

MODEL_PATH = BASE_DIR / "results" / "ginger_mobilenetv2.keras"


# ---------------- SETTINGS ----------------

IMAGE_SIZE = (224, 224)
MAX_FILE_SIZE = 5 * 1024 * 1024

# Must match the exact class order used during training.
CLASS_NAMES = [
    "HEALTHY",
    "DAMAGE-PEST",
    "DEHYDRATED",
    "LEAF-BLIGHT",
]

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

ALLOWED_IMAGE_FORMATS = {
    "JPEG",
    "PNG",
    "WEBP",
}


# ---------------- FASTAPI APP ----------------

app = FastAPI(
    title="KisanVision AI - Ginger Prediction API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://miniproject1-eta-one.vercel.app",
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
        raise RuntimeError(
            f"Ginger model is missing: {MODEL_PATH}"
        )

    loaded_model = tf.keras.models.load_model(
        MODEL_PATH
    )

    output_shape = loaded_model.output_shape

    if (
        not isinstance(output_shape, tuple)
        or output_shape[-1] != len(CLASS_NAMES)
    ):
        raise RuntimeError(
            "Ginger model output does not match "
            "the four Ginger classes."
        )

    model = loaded_model

    print("\nGinger model loaded successfully.")
    print(f"Model: {MODEL_PATH.name}")
    print(f"Classes: {CLASS_NAMES}")


# ---------------- HEALTH CHECK ----------------

@app.get("/health")
def health():

    return {
        "success": True,
        "service": "KisanVision AI Ginger API",
        "model_loaded": model is not None,
        "model_name": MODEL_PATH.name,
        "classes": CLASS_NAMES,
    }


# ---------------- GINGER PREDICTION ----------------

@app.post("/predict/ginger")
async def predict_ginger(
    file: UploadFile = File(...)
):

    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Ginger model is not loaded.",
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Upload a JPG, PNG, or WebP image.",
        )

    try:

        image_bytes = await file.read(
            MAX_FILE_SIZE + 1
        )

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

            with Image.open(
                io.BytesIO(image_bytes)
            ) as source:

                if source.format not in ALLOWED_IMAGE_FORMATS:
                    raise HTTPException(
                        status_code=400,
                        detail="Unsupported image format.",
                    )

                source.load()

                # Convert image to RGB.
                image_array = np.asarray(
                    source.convert("RGB"),
                    dtype=np.uint8,
                )

                # Resize exactly as in training.
                image_array = tf.image.resize(
                    image_array,
                    IMAGE_SIZE,
                    method="bilinear",
                )

                image_array = image_array.numpy().astype(
                    np.float32
                )

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

        # MobileNetV2 preprocessing.
        image_array = preprocess_input(image_array)

        image_array = np.expand_dims(
            image_array,
            axis=0,
        )

        # Model prediction.
        predictions = model.predict(
            image_array,
            verbose=0,
        )[0]

        predictions = np.asarray(
            predictions,
            dtype=np.float64,
        )

        # Validate model output.
        if (
            predictions.ndim != 1
            or len(predictions) != len(CLASS_NAMES)
            or not np.all(np.isfinite(predictions))
        ):
            raise HTTPException(
                status_code=500,
                detail="The model returned invalid prediction output.",
            )

        # Softmax probabilities must be between 0 and 1.
        if np.any(predictions < 0) or np.any(predictions > 1):
            raise HTTPException(
                status_code=500,
                detail="Model probabilities are outside the valid range.",
            )

        probability_sum = float(np.sum(predictions))

        if (
            not np.isfinite(probability_sum)
            or probability_sum <= 0
            or not np.isclose(
                probability_sum,
                1.0,
                atol=0.01,
            )
        ):
            raise HTTPException(
                status_code=500,
                detail="Model probabilities do not sum to approximately 1.",
            )

        # Normalize minor floating-point differences.
        predictions = predictions / probability_sum

        best_index = int(np.argmax(predictions))

        # Convert probabilities to percentages.
        percentage_values = predictions * 100

        probabilities = {
            name: round(
                float(percentage_values[index]),
                4
            )
            for index, name in enumerate(CLASS_NAMES)
        }

        confidence = round(
            float(percentage_values[best_index]),
            2
        )

        return {
            "success": True,
            "crop": "Ginger",
            "predicted_class": CLASS_NAMES[best_index],
            "confidence": confidence,
            "probabilities": probabilities,
            "warning": (
                "Prediction is experimental and must be verified. "
                "Confidence is not a confirmed diagnosis."
            ),
        }

    finally:
        await file.close()
