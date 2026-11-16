
import os
import json
import numpy as np
import pandas as pd
import tensorflow as tf

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)

# --------------------------------------------------
# PATHS AND SETTINGS
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

MANIFEST_PATH = os.path.join(
    BASE_DIR, "split", "cardamom_split_manifest.csv"
)

RESULTS_DIR = os.path.join(BASE_DIR, "results")

ORIGINAL_MODEL_PATH = os.path.join(
    RESULTS_DIR, "cardamom_mobilenetv2.keras"
)

FINETUNED_MODEL_PATH = os.path.join(
    RESULTS_DIR, "cardamom_mobilenetv2_finetuned.keras"
)

OUTPUT_PATH = os.path.join(
    RESULTS_DIR, "model_comparison_results.json"
)

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 16

CLASS_NAMES = ["HEALTHY", "BLIGHT", "PHYLOSTICTA"]

CLASS_TO_INDEX = {
    name: index for index, name in enumerate(CLASS_NAMES)
}


# --------------------------------------------------
# LOAD TEST DATA ONLY
# --------------------------------------------------

def load_test_data():

    df = pd.read_csv(MANIFEST_PATH)

    test_df = df[df["split"] == "test"].copy()

    test_df = test_df[
        test_df["class_name"].isin(CLASS_NAMES)
    ].reset_index(drop=True)

    if len(test_df) != 258:
        raise ValueError(
            f"Expected 258 test images, found {len(test_df)}"
        )

    images = []
    labels = []

    for _, row in test_df.iterrows():

        image_path = os.path.normpath(
            os.path.join(
                os.path.dirname(os.path.dirname(BASE_DIR)),
                row["image_path"]
            )
        )

        if not os.path.exists(image_path):
            raise FileNotFoundError(
                f"Test image not found: {image_path}"
            )

        image = tf.keras.utils.load_img(
            image_path,
            target_size=IMAGE_SIZE
        )

        image = tf.keras.utils.img_to_array(image)

        # MobileNetV2 preprocessing
        image = tf.keras.applications.mobilenet_v2.preprocess_input(
            image
        )

        images.append(image)
        labels.append(CLASS_TO_INDEX[row["class_name"]])

    x_test = np.asarray(images, dtype=np.float32)
    y_test = np.asarray(labels, dtype=np.int32)

    print("\nTest dataset loaded successfully.")
    print(f"Total test images: {len(x_test)}")

    for class_name in CLASS_NAMES:
        count = int(np.sum(y_test == CLASS_TO_INDEX[class_name]))
        print(f"{class_name}: {count}")

    return x_test, y_test


# --------------------------------------------------
# EVALUATE ONE MODEL
# --------------------------------------------------

def evaluate_model(model_path, model_name, x_test, y_test):

    print(f"\n{'=' * 55}")
    print(f"Evaluating: {model_name}")
    print(f"{'=' * 55}")

    model = tf.keras.models.load_model(
        model_path,
        compile=False
    )

    probabilities = model.predict(
        x_test,
        batch_size=BATCH_SIZE,
        verbose=1
    )

    predictions = np.argmax(probabilities, axis=1)

    accuracy = accuracy_score(y_test, predictions)

    report = classification_report(
        y_test,
        predictions,
        labels=[0, 1, 2],
        target_names=CLASS_NAMES,
        output_dict=True,
        zero_division=0
    )

    matrix = confusion_matrix(
        y_test,
        predictions,
        labels=[0, 1, 2]
    )

    print(f"\nAccuracy: {accuracy * 100:.2f}%")

    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            predictions,
            labels=[0, 1, 2],
            target_names=CLASS_NAMES,
            zero_division=0
        )
    )

    print("Confusion Matrix:")
    print(matrix)

    results = {
        "model_name": model_name,
        "accuracy": float(accuracy),
        "accuracy_percent": float(accuracy * 100),
        "classification_report": report,
        "confusion_matrix": matrix.tolist()
    }

    del model
    tf.keras.backend.clear_session()

    return results


# --------------------------------------------------
# MAIN COMPARISON
# --------------------------------------------------

def main():

    if not os.path.exists(ORIGINAL_MODEL_PATH):
        raise FileNotFoundError(ORIGINAL_MODEL_PATH)

    if not os.path.exists(FINETUNED_MODEL_PATH):
        raise FileNotFoundError(FINETUNED_MODEL_PATH)

    x_test, y_test = load_test_data()

    original_results = evaluate_model(
        ORIGINAL_MODEL_PATH,
        "Original Model",
        x_test,
        y_test
    )

    finetuned_results = evaluate_model(
        FINETUNED_MODEL_PATH,
        "Fine-Tuned Model",
        x_test,
        y_test
    )

    comparison = {
        "test_image_count": int(len(y_test)),
        "class_names": CLASS_NAMES,
        "original_model": original_results,
        "finetuned_model": finetuned_results
    }

    os.makedirs(RESULTS_DIR, exist_ok=True)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(comparison, file, indent=4)

    print("\n" + "=" * 55)
    print("FINAL MODEL COMPARISON")
    print("=" * 55)

    print(
        f"Original Model: "
        f"{original_results['accuracy_percent']:.2f}%"
    )

    print(
        f"Fine-Tuned Model: "
        f"{finetuned_results['accuracy_percent']:.2f}%"
    )

    difference = (
        finetuned_results["accuracy_percent"]
        - original_results["accuracy_percent"]
    )

    print(f"Accuracy difference: {difference:+.2f} percentage points")

    print(f"\nResults saved to:\n{OUTPUT_PATH}")

    print(
        "\nComparison complete. No model or API files were modified."
    )


if __name__ == "__main__":
    main()
