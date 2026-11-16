
from pathlib import Path
import csv
import random
import shutil
from collections import defaultdict

# Project paths
ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = ROOT / "dataset" / "Arecanut"
TRAINING_DIR = ROOT / "training" / "arecanut"

GROUPS_CSV = TRAINING_DIR / "arecanut_candidate_groups.csv"
OUTPUT_DIR = TRAINING_DIR / "split"

SEED = 42
random.seed(SEED)

CLASSES = {
    "BUD ROT": DATASET_DIR / "Disease" / "BUD ROT",
    "RING SPOT": DATASET_DIR / "Disease" / "RING SPOT",
    "YELLOW LEAF": DATASET_DIR / "Disease" / "YELLOW LEAF",
    "HEALTHY LEAF": DATASET_DIR / "Healthy" / "HEALTHY LEAF",
}

# Split proportions
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

# Read candidate groups
image_to_group = {}

with GROUPS_CSV.open("r", newline="", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)

    for row in reader:
        image_path = row["image_path"].replace("/", "\\")
        group_id = row["group_id"]

        image_to_group[image_path.lower()] = group_id

# Collect images by class
class_images = {}

for class_name, folder in CLASSES.items():
    if not folder.exists():
        raise FileNotFoundError(f"Class folder not found: {folder}")

    images = sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in {
            ".jpg", ".jpeg", ".png", ".bmp", ".webp"
        }
    )

    if len(images) != 50:
        raise ValueError(
            f"{class_name}: expected 50 images, found {len(images)}"
        )

    class_images[class_name] = images

# Build indivisible groups for each class.
# Images without candidate matches become individual groups.
split_records = []

for class_name, images in class_images.items():
    groups = defaultdict(list)

    for image in images:
        relative_path = str(image.relative_to(ROOT)).replace("/", "\\")
        group_id = image_to_group.get(relative_path.lower())

        if group_id is None:
            group_id = f"UNIQUE_{class_name}_{image.name}"

        groups[group_id].append(image)

    group_items = list(groups.items())
    random.shuffle(group_items)

    total = len(images)
    target_train = round(total * TRAIN_RATIO)
    target_val = round(total * VAL_RATIO)

    assigned = {
        "train": [],
        "validation": [],
        "test": [],
    }

    counts = {
        "train": 0,
        "validation": 0,
        "test": 0,
    }

    # Greedily assign whole groups to the split
    for group_id, members in group_items:
        remaining_train = target_train - counts["train"]
        remaining_val = target_val - counts["validation"]

        if counts["train"] < target_train and (
            remaining_train >= len(members) or
            remaining_train >= remaining_val
        ):
            split_name = "train"

        elif counts["validation"] < target_val:
            split_name = "validation"

        else:
            split_name = "test"

        assigned[split_name].append((group_id, members))
        counts[split_name] += len(members)

    # Create manifest records
    for split_name, group_list in assigned.items():
        for group_id, members in group_list:
            for image in members:
                relative_path = str(image.relative_to(ROOT)).replace("/", "\\")

                split_records.append({
                    "class_name": class_name,
                    "split": split_name,
                    "group_id": group_id,
                    "image_path": relative_path,
                })

    print(f"\n{class_name}")
    print(f"  Total images: {total}")
    print(f"  Train: {counts['train']}")
    print(f"  Validation: {counts['validation']}")
    print(f"  Test: {counts['test']}")
    print(f"  Groups: {len(group_items)}")

# Verify no candidate group crosses splits
group_splits = defaultdict(set)

for record in split_records:
    group_splits[
        (record["class_name"], record["group_id"])
    ].add(record["split"])

leaking_groups = {
    key: splits
    for key, splits in group_splits.items()
    if len(splits) > 1
}

if leaking_groups:
    raise RuntimeError(
        f"Data leakage detected across splits: {leaking_groups}"
    )

# Write reproducible CSV manifest
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

manifest_path = OUTPUT_DIR / "arecanut_split_manifest.csv"

with manifest_path.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=["class_name", "split", "group_id", "image_path"]
    )
    writer.writeheader()
    writer.writerows(split_records)

print("\nSplit manifest created:")
print(manifest_path)
print(f"Total images assigned: {len(split_records)}")
print("Cross-split candidate-group leakage: NONE")
print("\nOriginal dataset images were not modified or copied.")
