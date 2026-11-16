
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
from sklearn.utils.class_weight import compute_class_weight


# =====================================================
# 1. CONFIGURATION
# =====================================================

SEED = 42
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 16

STAGE1_EPOCHS = 10
STAGE2_EPOCHS = 20

LEARNING_RATE = 0.0001
FINE_TUNE_LEARNING_RATE = 0.00001

random.seed(SEED)
np.random.seed(SEED)
tf.random.set_seed(SEED)

ROOT = Path(__file__).resolve().parents[2]

MANIFEST = (
    ROOT / "training" / "ginger" /
    "split" / "ginger_split_manifest.csv"
)

OUTPUT_DIR = ROOT / "training" / "ginger" / "results"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = OUTPUT_DIR / "ginger_mobilenetv2.keras"

CLASS_NAMES = [
    "HEALTHY",
    "DAMAGE-PEST",
    "DEHYDRATED",
    "LEAF-BLIGHT"
]

CLASS_TO_INDEX = {
    name: index for index, name in enumerate(CLASS_NAMES)
}


# =====================================================
# 2. LOAD AND VALIDATE MANIFEST
# =====================================================

if not MANIFEST.exists():
    raise FileNotFoundError(f"Manifest not found: {MANIFEST}")

df = pd.read_csv(MANIFEST)

required_columns = {
    "class_name", "split", "image_path", "hash"
}

if not required_columns.issubset(df.columns):
    raise ValueError("Manifest is missing required columns.")

if len(df) != 10910:
    raise ValueError(f"Expected 10910 images, found {len(df)}.")

if df["image_path"].duplicated().any():
    raise ValueError("Duplicate image paths found.")

if df["hash"].duplicated().any():
    raise ValueError("Duplicate image hashes found.")

if set(df["class_name"]) != set(CLASS_NAMES):
    raise ValueError("Unexpected or missing Ginger class.")

if set(df["split"]) != {"train", "validation", "test"}:
    raise ValueError("Unexpected or missing dataset split.")

df["label"] = df["class_name"].map(CLASS_TO_INDEX)

df["absolute_path"] = df["image_path"].apply(
    lambda p: str(ROOT / Path(str(p).replace("\\", "/")))
)

for image_path in df["absolute_path"]:
    if not Path(image_path).is_file():
        raise FileNotFoundError(f"Image missing: {image_path}")

train_df = df[df["split"] == "train"].copy()
val_df = df[df["split"] == "validation"].copy()
test_df = df[df["split"] == "test"].copy()

if min(len(train_df), len(val_df), len(test_df)) == 0:
    raise ValueError("One or more dataset splits are empty.")

# Verify no exact hash leakage between splits.
train_hashes = set(train_df["hash"])
val_hashes = set(val_df["hash"])
test_hashes = set(test_df["hash"])

if (
    not train_hashes.isdisjoint(val_hashes)
    or not train_hashes.isdisjoint(test_hashes)
    or not val_hashes.isdisjoint(test_hashes)
):
    raise ValueError("Exact duplicate leakage detected.")

print("\nGinger dataset summary")
print("----------------------")

for split_name, split_df in [
    ("Train", train_df),
    ("Validation", val_df),
    ("Test", test_df)
]:
    print(f"\n{split_name}: {len(split_df)} images")
    print(split_df["class_name"].value_counts().to_string())


# =====================================================
# 3. CLASS WEIGHTS
# =====================================================

class_weights = compute_class_weight(
    class_weight="balanced",
    classes=np.arange(len(CLASS_NAMES)),
    y=train_df["label"].values
)

CLASS_WEIGHTS = {
    index: float(weight)
    for index, weight in enumerate(class_weights)
}

print("\nClass weights")

for index, class_name in enumerate(CLASS_NAMES):
    print(class_name, ":", round(CLASS_WEIGHTS[index], 4))


# =====================================================
# 4. IMAGE PREPROCESSING
# =====================================================

def load_image(path, label, sample_weight=None):

    image = tf.io.read_file(path)

    image = tf.io.decode_jpeg(
        image,
        channels=3
    )

    image = tf.image.resize(
        image,
        IMAGE_SIZE,
        method="bilinear"
    )

    image = tf.cast(image, tf.float32)

    image = tf.keras.applications.mobilenet_v2.preprocess_input(
        image
    )

    if sample_weight is not None:
        return image, label, sample_weight

    return image, label


def create_dataset(dataframe, training=False):

    paths = dataframe["absolute_path"].values
    labels = dataframe["label"].values.astype(np.int32)

    if training:

        weights = np.array([
            CLASS_WEIGHTS[int(label)]
            for label in labels
        ], dtype=np.float32)

        dataset = tf.data.Dataset.from_tensor_slices(
            (paths, labels, weights)
        )

        dataset = dataset.shuffle(
            buffer_size=len(dataframe),
            seed=SEED,
            reshuffle_each_iteration=True
        )

        dataset = dataset.map(
            load_image,
            num_parallel_calls=1
        )

    else:

        dataset = tf.data.Dataset.from_tensor_slices(
            (paths, labels)
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
# 5. DATA AUGMENTATION
# =====================================================

augmentation = tf.keras.Sequential([
    tf.keras.layers.RandomFlip("horizontal"),
    tf.keras.layers.RandomRotation(0.08),
    tf.keras.layers.RandomZoom(0.10),
    tf.keras.layers.RandomContrast(0.10),
], name="ginger_data_augmentation")


# =====================================================
# 6. BUILD MOBILENETV2 MODEL
# =====================================================

base_model = tf.keras.applications.MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights="imagenet"
)

base_model.trainable = False

inputs = tf.keras.Input(shape=(224, 224, 3))

x = augmentation(inputs)

x = base_model(x, training=False)

x = tf.keras.layers.GlobalAveragePooling2D()(x)

x = tf.keras.layers.Dropout(0.30)(x)

outputs = tf.keras.layers.Dense(
    len(CLASS_NAMES),
    activation="softmax"
)(x)

model = tf.keras.Model(inputs, outputs)

model.compile(
    optimizer=tf.keras.optimizers.Adam(
        learning_rate=LEARNING_RATE
    ),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

model.summary()


# =====================================================
# 7. STAGE 1 CALLBACKS
# =====================================================

stage1_callbacks = [

    tf.keras.callbacks.ModelCheckpoint(
        filepath=str(MODEL_PATH),
        monitor="val_loss",
        save_best_only=True,
        verbose=1
    ),

    tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=6,
        restore_best_weights=True,
        verbose=1
    ),

    tf.keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.2,
        patience=3,
        min_lr=1e-7,
        verbose=1
    )
]


# =====================================================
# 8. STAGE 1 - TRAIN CLASSIFICATION HEAD
# =====================================================

print("\n======================================")
print("STAGE 1: TRAINING CLASSIFICATION HEAD")
print("======================================")

history_stage1 = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=STAGE1_EPOCHS,
    callbacks=stage1_callbacks,
    verbose=1
)

# Load the best Stage 1 checkpoint.
model = tf.keras.models.load_model(MODEL_PATH)


# =====================================================
# 9. STAGE 2 - FINE-TUNE MOBILENETV2
# =====================================================

print("\n======================================")
print("STAGE 2: FINE-TUNING MOBILENETV2")
print("======================================")

# Unfreeze the MobileNetV2 base model.
base_model = model.get_layer("mobilenetv2_1.00_224")
base_model.trainable = True

# Freeze all but the final 30 layers.
for layer in base_model.layers[:-30]:
    layer.trainable = False

# Keep Batch Normalization layers frozen.
for layer in base_model.layers:
    if isinstance(layer, tf.keras.layers.BatchNormalization):
        layer.trainable = False

print(
    "\nTrainable MobileNetV2 layers:",
    sum(1 for layer in base_model.layers if layer.trainable)
)

# Recompile with a lower learning rate.
model.compile(
    optimizer=tf.keras.optimizers.Adam(
        learning_rate=FINE_TUNE_LEARNING_RATE
    ),
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

stage2_callbacks = [

    tf.keras.callbacks.ModelCheckpoint(
        filepath=str(MODEL_PATH),
        monitor="val_loss",
        save_best_only=True,
        verbose=1
    ),

    tf.keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=6,
        restore_best_weights=True,
        verbose=1
    ),

    tf.keras.callbacks.ReduceLROnPlateau(
        monitor="val_loss",
        factor=0.2,
        patience=3,
        min_lr=1e-7,
        verbose=1
    )
]

history_stage2 = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=STAGE2_EPOCHS,
    callbacks=stage2_callbacks,
    verbose=1
)

# Load the best fine-tuned checkpoint.
model = tf.keras.models.load_model(MODEL_PATH)


# =====================================================
# 10. COMBINE TRAINING HISTORIES
# =====================================================

history_df = pd.concat(
    [
        pd.DataFrame(history_stage1.history).assign(
            stage="initial"
        ),

        pd.DataFrame(history_stage2.history).assign(
            stage="fine_tuning"
        )
    ],
    ignore_index=True
)


# =====================================================
# 11. TEST EVALUATION
# =====================================================

print("\nEvaluating on untouched test set...")

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

print("\nTest accuracy:", round(accuracy, 4))

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
# 12. SAVE RESULTS
# =====================================================

results = {
    "model": "MobileNetV2",
    "training_method": "Two-stage fine-tuning",
    "image_size": list(IMAGE_SIZE),
    "batch_size": BATCH_SIZE,
    "stage1_epochs": STAGE1_EPOCHS,
    "stage2_epochs": STAGE2_EPOCHS,
    "test_loss": float(test_loss),
    "test_accuracy": float(test_accuracy),
    "accuracy_score": float(accuracy),
    "classes": CLASS_NAMES,
    "class_weights": CLASS_WEIGHTS,
    "classification_report": report,
    "confusion_matrix": matrix.tolist(),
    "test_image_count": len(test_df),
    "seed": SEED
}

with (OUTPUT_DIR / "evaluation_results.json").open(
    "w",
    encoding="utf-8"
) as file:
    json.dump(results, file, indent=4)

history_df.to_csv(
    OUTPUT_DIR / "training_history.csv",
    index=False
)

print("\nGinger training completed.")
print("Model saved:", MODEL_PATH)
print("Evaluation saved:", OUTPUT_DIR / "evaluation_results.json")
print("Training history saved:", OUTPUT_DIR / "training_history.csv")
