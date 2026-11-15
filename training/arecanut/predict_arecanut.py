
import sys
from pathlib import Path

import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.utils import load_img, img_to_array

# Model path
MODEL_PATH = Path(
    "training/arecanut/results/arecanut_mobilenetv2_finetuned.keras"
)

# Keep exactly the same order used during training
CLASS_NAMES = [
    "BUD ROT",
    "RING SPOT",
    "YELLOW LEAF",
    "HEALTHY LEAF"
]

IMAGE_SIZE = (224, 224)


def main():
    if len(sys.argv) != 2:
        print("Usage:")
        print(
            "python training/arecanut/predict_arecanut.py "
            '"path/to/image.jpg"'
        )
        return

    image_path = Path(sys.argv[1])

    if not image_path.is_file():
        print(f"Image not found: {image_path}")
        return

    if not MODEL_PATH.is_file():
        print(f"Model not found: {MODEL_PATH}")
        return

    print("Loading Arecanut model...")
    model = tf.keras.models.load_model(MODEL_PATH)

    # Load and preprocess image exactly as during training
    image = load_img(
        image_path,
        target_size=IMAGE_SIZE,
        color_mode="rgb"
    )

    image_array = img_to_array(image)
    image_array = preprocess_input(image_array)
    image_array = np.expand_dims(image_array, axis=0)

    # Predict
    predictions = model.predict(image_array, verbose=0)[0]

    predicted_index = int(np.argmax(predictions))
    predicted_class = CLASS_NAMES[predicted_index]
    confidence = float(predictions[predicted_index]) * 100

    print("\nARECANUT DISEASE PREDICTION")
    print("--------------------------")
    print(f"Image: {image_path.name}")
    print(f"Predicted class: {predicted_class}")
    print(f"Confidence: {confidence:.2f}%")

    print("\nAll class probabilities:")
    for name, score in zip(CLASS_NAMES, predictions):
        print(f"{name}: {score * 100:.2f}%")


if __name__ == "__main__":
    main()
