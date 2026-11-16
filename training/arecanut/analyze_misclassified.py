
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf

ROOT = Path(__file__).resolve().parents[2]

MANIFEST = (
    ROOT / "training" / "arecanut" /
    "split" / "arecanut_split_manifest.csv"
)

MODEL_PATH = (
    ROOT / "training" / "arecanut" /
    "results" / "arecanut_mobilenetv2.keras"
)

OUTPUT_DIR = (
    ROOT / "training" / "arecanut" /
    "results"
)

IMAGE_SIZE = (224, 224)

CLASS_NAMES = [
    "BUD ROT",
    "RING SPOT",
    "YELLOW LEAF",
    "HEALTHY LEAF"
]

df = pd.read_csv(MANIFEST)
test_df = df[df["split"] == "test"].copy()

model = tf.keras.models.load_model(MODEL_PATH)

misclassified = []

for _, row in test_df.iterrows():
    image_path = ROOT / Path(
        str(row["image_path"]).replace("\\", "/")
    )

    image = tf.io.read_file(str(image_path))
    image = tf.io.decode_image(
        image,
        channels=3,
        expand_animations=False
    )
    image.set_shape([None, None, 3])

    image = tf.image.resize(image, IMAGE_SIZE)

    image = tf.keras.applications.mobilenet_v2.preprocess_input(
        tf.cast(image, tf.float32)
    )

    image = tf.expand_dims(image, axis=0)

    probabilities = model.predict(image, verbose=0)[0]

    predicted_index = int(np.argmax(probabilities))
    actual_class = row["class_name"]
    predicted_class = CLASS_NAMES[predicted_index]

    if actual_class != predicted_class:
        misclassified.append({
            "image_path": row["image_path"],
            "actual_class": actual_class,
            "predicted_class": predicted_class,
            "confidence": round(
                float(probabilities[predicted_index]), 4
            )
        })

report = pd.DataFrame(misclassified)

output_file = OUTPUT_DIR / "misclassified_images.csv"
report.to_csv(output_file, index=False)

print("\nMisclassified images:", len(report))
print("\nMisclassification details:")

if report.empty:
    print("No misclassified images.")
else:
    print(report.to_string(index=False))

print("\nReport saved:", output_file)
