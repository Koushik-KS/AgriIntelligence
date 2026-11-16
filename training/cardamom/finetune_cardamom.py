from pathlib import Path
import json
import random

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.utils.class_weight import compute_class_weight

# Small Cardamom fine-tuning experiment.
# Preserves the original model and does not use the held-out test split.

SEED = 42
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 16
FINE_TUNE_EPOCHS = 5
LEARNING_RATE = 1e-5
UNFREEZE_LAST_LAYERS = 20

random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "training" / "cardamom" / "split" / "cardamom_split_manifest.csv"
RESULTS_DIR = ROOT / "training" / "cardamom" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

ORIGINAL_MODEL = RESULTS_DIR / "cardamom_mobilenetv2.keras"
OUTPUT_MODEL = RESULTS_DIR / "cardamom_mobilenetv2_finetuned.keras"
OUTPUT_METRICS = RESULTS_DIR / "finetuning_validation_results.json"

CLASS_NAMES = ["HEALTHY", "BLIGHT", "PHYLOSTICTA"]
CLASS_TO_INDEX = {name: i for i, name in enumerate(CLASS_NAMES)}

if not ORIGINAL_MODEL.is_file():
    raise FileNotFoundError(f"Original model not found: {ORIGINAL_MODEL}")
if not MANIFEST.is_file():
    raise FileNotFoundError(f"Manifest not found: {MANIFEST}")
if OUTPUT_MODEL.exists():
    raise FileExistsError(
        f"{OUTPUT_MODEL.name} already exists. Back it up or rename it first; "
        "this script will not overwrite an earlier experiment."
    )

df = pd.read_csv(MANIFEST)
required = {"class_name", "split", "group_id", "image_path"}
if not required.issubset(df.columns):
    raise ValueError(f"Manifest must contain columns: {sorted(required)}")
if set(df["class_name"]) != set(CLASS_NAMES):
    raise ValueError("Manifest classes do not match the model class order.")
if not set(df["split"]).issubset({"train", "validation", "test"}):
    raise ValueError("Unexpected split name.")

group_split_counts = df.groupby(["class_name", "group_id"])["split"].nunique()
if (group_split_counts > 1).any():
    raise ValueError("Near-duplicate group leakage detected.")

df["label"] = df["class_name"].map(CLASS_TO_INDEX)
df["absolute_path"] = df["image_path"].apply(
    lambda p: str(ROOT / Path(str(p).replace("\\", "/")))
)
for path in df["absolute_path"]:
    if not Path(path).is_file():
        raise FileNotFoundError(f"Image missing: {path}")

train_df = df[df["split"] == "train"].copy()
val_df = df[df["split"] == "validation"].copy()
if train_df.empty or val_df.empty:
    raise ValueError("Training or validation split is empty.")

weights = compute_class_weight(
    class_weight="balanced",
    classes=np.arange(len(CLASS_NAMES)),
    y=train_df["label"].values,
)
class_weights = {i: float(w) for i, w in enumerate(weights)}

def load_image(path, label, sample_weight=None):
    image = tf.io.read_file(path)
    image = tf.io.decode_image(image, channels=3, expand_animations=False)
    image.set_shape([None, None, 3])
    image = tf.image.resize(image, IMAGE_SIZE, method="bilinear")
    image = tf.cast(image, tf.float32)
    image = tf.keras.applications.mobilenet_v2.preprocess_input(image)
    if sample_weight is not None:
        return image, label, sample_weight
    return image, label

def make_dataset(dataframe, training=False):
    paths = dataframe["absolute_path"].values
    labels = dataframe["label"].values.astype(np.int32)
    if training:
        sample_weights = np.asarray(
            [class_weights[int(label)] for label in labels], dtype=np.float32
        )
        ds = tf.data.Dataset.from_tensor_slices((paths, labels, sample_weights))
        ds = ds.shuffle(len(dataframe), seed=SEED, reshuffle_each_iteration=True)
        ds = ds.map(load_image, num_parallel_calls=1)
    else:
        ds = tf.data.Dataset.from_tensor_slices((paths, labels))
        ds = ds.map(load_image, num_parallel_calls=1)
    return ds.batch(BATCH_SIZE).prefetch(1)

train_ds = make_dataset(train_df, training=True)
val_ds = make_dataset(val_df)

print("Loading original model:", ORIGINAL_MODEL)
model = tf.keras.models.load_model(ORIGINAL_MODEL)

base_model = next(
    (
        layer for layer in model.layers
        if isinstance(layer, tf.keras.Model)
        and layer.name.startswith("mobilenetv2")
    ),
    None,
)
if base_model is None:
    raise RuntimeError("Could not locate MobileNetV2 inside the saved model.")

base_model.trainable = True
for layer in base_model.layers[:-UNFREEZE_LAST_LAYERS]:
    layer.trainable = False
for layer in base_model.layers:
    if isinstance(layer, tf.keras.layers.BatchNormalization):
        layer.trainable = False

print("MobileNetV2 total layers:", len(base_model.layers))
print("Trainable MobileNetV2 layers:", sum(int(x.trainable) for x in base_model.layers))
print("Training images:", len(train_df))
print("Validation images:", len(val_df))
print("Held-out test split will NOT be used.")

model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=LEARNING_RATE),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

callbacks = [
    tf.keras.callbacks.ModelCheckpoint(
        filepath=str(OUTPUT_MODEL), monitor="val_loss",
        save_best_only=True, verbose=1
    ),
    tf.keras.callbacks.EarlyStopping(
        monitor="val_loss", patience=2,
        restore_best_weights=True, verbose=1
    ),
    tf.keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss", factor=0.2,
        patience=1, min_lr=1e-7, verbose=1
    ),
]

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=FINE_TUNE_EPOCHS,
    callbacks=callbacks,
    verbose=1,
)

best_model = tf.keras.models.load_model(OUTPUT_MODEL)
val_loss, val_accuracy = best_model.evaluate(val_ds, verbose=1)

summary = {
    "experiment": "MobileNetV2 small fine-tuning",
    "original_model": str(ORIGINAL_MODEL),
    "fine_tuned_model": str(OUTPUT_MODEL),
    "epochs_requested": FINE_TUNE_EPOCHS,
    "learning_rate": LEARNING_RATE,
    "unfreeze_last_layers": UNFREEZE_LAST_LAYERS,
    "batch_normalization_frozen": True,
    "training_image_count": int(len(train_df)),
    "validation_image_count": int(len(val_df)),
    "validation_loss": float(val_loss),
    "validation_accuracy": float(val_accuracy),
    "validation_accuracy_percent": round(float(val_accuracy) * 100, 2),
    "class_weights": class_weights,
    "test_split_used": False,
    "history": {
        key: [float(value) for value in values]
        for key, values in history.history.items()
    },
}

with OUTPUT_METRICS.open("w", encoding="utf-8") as f:
    json.dump(summary, f, indent=4)

print("\nFine-tuning experiment completed.")
print("Original model preserved:", ORIGINAL_MODEL)
print("Experimental model:", OUTPUT_MODEL)
print("Validation accuracy:", round(float(val_accuracy) * 100, 2), "%")
print("Validation results:", OUTPUT_METRICS)
print("Do not switch the API to the fine-tuned model until comparison is complete.")
