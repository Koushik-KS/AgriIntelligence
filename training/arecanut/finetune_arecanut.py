
from pathlib import Path
import json
import random

import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score
)

# =====================================================
# 1. CONFIGURATION
# =====================================================

SEED = 42
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 16
EPOCHS = 15
LEARNING_RATE = 0.00001
UNFREEZE_LAST_LAYERS = 30

random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

ROOT = Path(__file__).resolve().parents[2]

MANIFEST = (
    ROOT / "training" / "arecanut" /
    "split" / "arecanut_split_manifest.csv"
)

OUTPUT_DIR = ROOT / "training" / "arecanut" / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASELINE_MODEL = OUTPUT_DIR / "arecanut_mobilenetv2.keras"

FINETUNED_MODEL = (
    OUTPUT_DIR / "arecanut_mobilenetv2_finetuned.keras"
)

CLASS_NAMES = [
    "BUD ROT",
    "RING SPOT",
    "YELLOW LEAF",
    "HEALTHY LEAF"
]

CLASS_TO_INDEX = {
    name: index for index, name in enumerate(CLASS_NAMES)
}

# =====================================================
# 2. LOAD AND VALIDATE MANIFEST
# =====================================================

if not MANIFEST.exists():
    raise FileNotFoundError(f"Manifest not found: {MANIFEST}")

if not BASELINE_MODEL.exists():
    raise FileNotFoundError(
        f"Baseline model not found: {BASELINE_MODEL}"
    )

df = pd.read_csv(MANIFEST)

required_columns = {
    "class_name", "split", "group_id", "image_path"
}

if not required_columns.issubset(df.columns):
    raise ValueError("Manifest is missing required columns.")

if len(df) != 200:
    raise ValueError(f"Expected 200 images, found {len(df)}.")

if df["image_path"].duplicated().any():
    raise ValueError("Duplicate image paths found.")

if not set(df["class_name"]).issubset(CLASS_TO_INDEX):
    raise ValueError("Unexpected class name.")

if not set(df["split"]).issubset(
    {"train", "validation", "test"}
):
    raise ValueError("Unexpected split name.")

group_split_counts = (
    df.groupby(["class_name", "group_id"])["split"].nunique()
)

if (group_split_counts > 1).any():
    raise ValueError("Candidate group leakage detected.")

df["label"] = df["class_name"].map(CLASS_TO_INDEX)

df["absolute_path"] = df["image_path"].apply(
    lambda p: str(
        ROOT / Path(str(p).replace("\\", "/"))
    )
)

for image_path in df["absolute_path"]:
    if not Path(image_path).is_file():
        raise FileNotFoundError(f"Image missing: {image_path}")

train_df = df[df["split"] == "train"].copy()
val_df = df[df["split"] == "validation"].copy()
test_df = df[df["split"] == "test"].copy()

if train_df.empty or val_df.empty or test_df.empty:
    raise ValueError("One or more dataset splits are empty.")

print("\nDataset summary")
print("----------------")

for name, split_df in [
    ("Train", train_df),
    ("Validation", val_df),
    ("Test", test_df)
]:
    print(f"\n{name}: {len(split_df)} images")
    print(split_df["class_name"].value_counts().to_string())

# =====================================================
# 3. IMAGE PREPROCESSING
# =====================================================

def load_image(path, label):
    image = tf.io.read_file(path)

    image = tf.io.decode_image(
        image,
        channels=3,
        expand_animations=False
    )

    image.set_shape([None, None, 3])

    image = tf.image.resize(
        image,
        IMAGE_SIZE,
        method="bilinear"
    )

    image = tf.cast(image, tf.float32)

    image = tf.keras.applications.mobilenet_v2.preprocess_input(
        image
    )

    return image, label


def create_dataset(dataframe, training=False):
    paths = dataframe["absolute_path"].values
    labels = dataframe["label"].values.astype(np.int32)

    dataset = tf.data.Dataset.from_tensor_slices(
        (paths, labels)
    )

    if training:
        dataset = dataset.shuffle(
            buffer_size=len(dataframe),
            seed=SEED,
            reshuffle_each_iteration=True
        )

    dataset = dataset.map(
        load_image,
        num_parallel_calls=1
    )

    dataset = dataset.batch(BATCH_SIZE)
    dataset = dataset.prefetch(1)

    return dataset


train_ds = create_dataset(train_df, training=True)
val_ds = create_dataset(val_df)
test_ds = create_dataset(test_df)

# =====================================================
# 4. LOAD EXISTING BASELINE MODEL
# =====================================================

print("\nLoading baseline model...")

model = tf.keras.models.load_model(
    BASELINE_MODEL,
    compile=False
)

base_model = model.get_layer("mobilenetv2_1.00_224")

print("Baseline model loaded successfully.")

# =====================================================
# 5. UNFREEZE FINAL 30 LAYERS
# =====================================================

base_model.trainable = True

# Freeze all layers first.
for layer in base_model.layers:
    layer.trainable = False

# Unfreeze only the final 30 layers.
start_index = max(
    0,
    len(base_model.layers) - UNFREEZE_LAST_LAYERS
)

for layer in base_model.layers[start_index:]:
    if isinstance(
        layer,
        tf.keras.layers.BatchNormalization
    ):
        layer.trainable = False
    else:
        layer.trainable = True

print("\nFine-tuning configuration")
print("-------------------------")
print("Total backbone layers:", len(base_model.layers))
print("Unfreezing from layer:", start_index)

trainable_count = sum(
    layer.trainable
    for layer in base_model.layers
)

print("Trainable backbone layers:", trainable_count)

print("\nTrainable layer names:")
for layer in base_model.layers:
    if layer.trainable:
        print(layer.name)

# =====================================================
# 6. COMPILE MODEL
# =====================================================

model.compile(
    optimizer=tf.keras.optimizers.Adam(
        learning_rate=LEARNING_RATE
    ),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

# =====================================================
# 7. CALLBACKS
# =====================================================

callbacks = [
    tf.keras.callbacks.ModelCheckpoint(
        filepath=str(FINETUNED_MODEL),
        monitor="val_loss",
        save_best_only=True,
        verbose=1
    ),

    tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=4,
        restore_best_weights=True,
        verbose=1
    ),

    tf.keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.2,
        patience=2,
        min_lr=1e-7,
        verbose=1
    )
]

# =====================================================
# 8. FINE-TUNE MODEL
# =====================================================

print("\nStarting MobileNetV2 fine-tuning...")

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
    callbacks=callbacks,
    shuffle=False,
    verbose=1
)

# Load best validation checkpoint.
model = tf.keras.models.load_model(
    FINETUNED_MODEL,
    compile=False
)

# =====================================================
# 9. FINAL TEST EVALUATION
# =====================================================

print("\nEvaluating fine-tuned model on test set...")

model.compile(
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

test_loss, test_accuracy = model.evaluate(
    test_ds,
    verbose=1
)

all_true = []
all_predictions = []

for images, labels in test_ds:
    probabilities = model.predict(
        images,
        verbose=0
    )

    predictions = np.argmax(
        probabilities,
        axis=1
    )

    all_true.extend(labels.numpy().tolist())
    all_predictions.extend(predictions.tolist())

accuracy = accuracy_score(
    all_true,
    all_predictions
)

report = classification_report(
    all_true,
    all_predictions,
    labels=list(range(len(CLASS_NAMES))),
    target_names=CLASS_NAMES,
    output_dict=True,
    zero_division=0
)

matrix = confusion_matrix(
    all_true,
    all_predictions,
    labels=list(range(len(CLASS_NAMES)))
)

print("\nFine-tuned test accuracy:", round(accuracy, 4))

print("\nClassification report:")
print(
    classification_report(
        all_true,
        all_predictions,
        labels=list(range(len(CLASS_NAMES))),
        target_names=CLASS_NAMES,
        zero_division=0
    )
)

print("\nConfusion matrix:")
print(matrix)

# =====================================================
# 10. SAVE RESULTS
# =====================================================

results = {
    "experiment": "MobileNetV2 fine-tuning",
    "baseline_model": str(BASELINE_MODEL),
    "fine_tuned_model": str(FINETUNED_MODEL),
    "image_size": list(IMAGE_SIZE),
    "batch_size": BATCH_SIZE,
    "epochs_requested": EPOCHS,
    "learning_rate": LEARNING_RATE,
    "unfrozen_layers": UNFREEZE_LAST_LAYERS,
    "test_loss": float(test_loss),
    "test_accuracy": float(test_accuracy),
    "accuracy_score": float(accuracy),
    "classes": CLASS_NAMES,
    "classification_report": report,
    "confusion_matrix": matrix.tolist(),
    "test_image_count": len(test_df),
    "seed": SEED
}

results_path = OUTPUT_DIR / "finetuned_evaluation_results.json"

with results_path.open("w", encoding="utf-8") as file:
    json.dump(results, file, indent=4)

history_path = OUTPUT_DIR / "finetuned_training_history.csv"

pd.DataFrame(history.history).to_csv(
    history_path,
    index=False
)

print("\nFine-tuning completed.")
print("Fine-tuned model:", FINETUNED_MODEL)
print("Evaluation:", results_path)
print("Training history:", history_path)
