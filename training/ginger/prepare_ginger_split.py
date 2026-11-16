
import hashlib
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


# ---------------- PATHS ----------------

BASE_DIR = Path(__file__).resolve().parents[2]
DATASET_DIR = BASE_DIR / "dataset" / "Ginger"
SPLIT_DIR = Path(__file__).resolve().parent / "split"

RANDOM_SEED = 42

CLASS_FOLDERS = {
    "HEALTHY": DATASET_DIR / "Healthy",
    "DAMAGE-PEST": DATASET_DIR / "Disease" / "Damage-Pest",
    "DEHYDRATED": DATASET_DIR / "Disease" / "Dehydrated",
    "LEAF-BLIGHT": DATASET_DIR / "Disease" / "Leaf-blight",
}


# ---------------- IMAGE HASH ----------------

def calculate_hash(path):
    sha = hashlib.sha256()

    with open(path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            sha.update(chunk)

    return sha.hexdigest()


# ---------------- COLLECT IMAGES ----------------

def collect_images():

    records = []

    for class_name, folder in CLASS_FOLDERS.items():

        if not folder.exists():
            raise FileNotFoundError(f"Folder not found: {folder}")

        images = sorted(folder.glob("*.jpg"))

        if not images:
            raise ValueError(f"No JPG images found: {folder}")

        for image in images:
            records.append({
                "class_name": class_name,
                "image_path": image.relative_to(BASE_DIR).as_posix(),
                "hash": calculate_hash(image)
            })

        print(f"{class_name}: {len(images)} images")

    return pd.DataFrame(records)


# ---------------- DUPLICATE CHECK ----------------

def check_duplicates(data):

    duplicates = data[data.duplicated("hash", keep=False)]

    if not duplicates.empty:
        print("\nDuplicate images detected:")
        print(duplicates[["class_name", "image_path"]].to_string(index=False))
        raise ValueError("Resolve duplicate images before splitting.")

    print("\nNo exact duplicate images found.")


# ---------------- STRATIFIED SPLIT ----------------

def create_split(data):

    train, temporary = train_test_split(
        data,
        test_size=0.30,
        random_state=RANDOM_SEED,
        stratify=data["class_name"]
    )

    validation, test = train_test_split(
        temporary,
        test_size=0.50,
        random_state=RANDOM_SEED,
        stratify=temporary["class_name"]
    )

    train = train.copy()
    validation = validation.copy()
    test = test.copy()

    train["split"] = "train"
    validation["split"] = "validation"
    test["split"] = "test"

    result = pd.concat(
        [train, validation, test],
        ignore_index=True
    )

    return result.sample(
        frac=1,
        random_state=RANDOM_SEED
    ).reset_index(drop=True)


# ---------------- VERIFY ----------------

def verify_split(data):

    print("\nCLASS-WISE SPLIT COUNTS")

    print(pd.crosstab(data["class_name"], data["split"]))

    split_hashes = {
        name: set(data[data["split"] == name]["hash"])
        for name in ["train", "validation", "test"]
    }

    assert split_hashes["train"].isdisjoint(
        split_hashes["validation"]
    )

    assert split_hashes["train"].isdisjoint(
        split_hashes["test"]
    )

    assert split_hashes["validation"].isdisjoint(
        split_hashes["test"]
    )

    print("\nNo exact hash leakage between splits.")
    print("Total images:", len(data))


# ---------------- MAIN ----------------

def main():

    SPLIT_DIR.mkdir(parents=True, exist_ok=True)

    print("Preparing Ginger dataset...\n")

    data = collect_images()

    print("\nChecking duplicates...")
    check_duplicates(data)

    print("\nCreating 70:15:15 stratified split...")

    result = create_split(data)

    verify_split(result)

    output = SPLIT_DIR / "ginger_split_manifest.csv"

    result[
        ["class_name", "split", "image_path", "hash"]
    ].to_csv(output, index=False)

    print("\nManifest saved:")
    print(output)


if __name__ == "__main__":
    main()
