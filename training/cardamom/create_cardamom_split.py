
from pathlib import Path
import csv
import random
from collections import defaultdict

# =====================================================
# 1. CONFIGURATION
# =====================================================

SEED = 42
random.seed(SEED)

ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = ROOT / "dataset" / "Cardamom"
OUTPUT_DIR = ROOT / "training" / "cardamom" / "split"

CLASSES = {
    "HEALTHY": DATASET_DIR / "Healthy" / "Healthy_1000",
    "BLIGHT": DATASET_DIR / "Disease" / "Blight1000",
    "PHYLOSTICTA": DATASET_DIR / "Disease" / "Phylosticta_LS_1000",
}

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# Visually similar pairs identified during the audit.
NEAR_DUPLICATE_PAIRS = [
    ("Healthy (298).jpg", "Healthy (299).jpg"),
    ("Healthy (571).jpg", "Healthy (572).jpg"),
    ("Healthy (431).jpg", "Healthy (432).jpg"),
    ("Healthy (446).jpg", "Healthy (447).jpg"),
    ("Healthy (610).jpg", "Healthy (611).jpg"),
]

# =====================================================
# 2. COLLECT IMAGES
# =====================================================

class_images = {}

for class_name, folder in CLASSES.items():

    if not folder.exists():
        raise FileNotFoundError(f"Missing class folder: {folder}")

    images = sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    )

    if not images:
        raise ValueError(f"No images found in {folder}")

    class_images[class_name] = images

    print(f"{class_name}: {len(images)} images")

# =====================================================
# 3. CREATE NEAR-DUPLICATE GROUPS
# =====================================================

image_to_group = {}

for index, pair in enumerate(NEAR_DUPLICATE_PAIRS, start=1):

    group_id = f"HEALTHY_PAIR_{index}"

    for filename in pair:

        image_path = CLASSES["HEALTHY"] / filename

        if not image_path.is_file():
            raise FileNotFoundError(
                f"Near-duplicate image missing: {image_path}"
            )

        image_to_group[image_path.resolve()] = group_id

# =====================================================
# 4. GROUP-AWARE SPLITTING
# =====================================================

split_records = []

ratios = {
    "train": TRAIN_RATIO,
    "validation": VAL_RATIO,
    "test": TEST_RATIO,
}

for class_name, images in class_images.items():

    groups = defaultdict(list)

    for image in images:

        resolved_path = image.resolve()

        group_id = image_to_group.get(
            resolved_path,
            f"UNIQUE_{class_name}_{image.name}"
        )

        groups[group_id].append(image)

    group_items = list(groups.items())
    random.shuffle(group_items)

    # Process larger groups first.
    group_items.sort(
        key=lambda item: len(item[1]),
        reverse=True
    )

    total = len(images)

    targets = {
        split: total * ratio
        for split, ratio in ratios.items()
    }

    counts = {
        "train": 0,
        "validation": 0,
        "test": 0,
    }

    assigned = {
        "train": [],
        "validation": [],
        "test": [],
    }

    for group_id, members in group_items:

        best_split = min(
            ratios,
            key=lambda split: (
                (counts[split] + len(members) - targets[split]) ** 2
                - (counts[split] - targets[split]) ** 2
            )
        )

        assigned[best_split].append((group_id, members))
        counts[best_split] += len(members)

    for split_name, group_list in assigned.items():

        for group_id, members in group_list:

            for image in members:

                relative_path = str(
                    image.relative_to(ROOT)
                ).replace("/", "\\")

                split_records.append({
                    "class_name": class_name,
                    "split": split_name,
                    "group_id": group_id,
                    "image_path": relative_path,
                })

    print(f"\n{class_name}")
    print("Total:", total)
    print("Train:", counts["train"])
    print("Validation:", counts["validation"])
    print("Test:", counts["test"])
    print("Groups:", len(group_items))

# =====================================================
# 5. VERIFY NO GROUP LEAKAGE
# =====================================================

group_splits = defaultdict(set)

for record in split_records:

    key = (
        record["class_name"],
        record["group_id"]
    )

    group_splits[key].add(record["split"])

leaking_groups = {
    key: splits
    for key, splits in group_splits.items()
    if len(splits) > 1
}

if leaking_groups:
    raise RuntimeError(
        f"Group leakage detected: {leaking_groups}"
    )

# Verify all images are included exactly once.
manifest_paths = [
    record["image_path"]
    for record in split_records
]

if len(manifest_paths) != len(set(manifest_paths)):
    raise RuntimeError("Duplicate image paths in manifest.")

expected_total = sum(
    len(images) for images in class_images.values()
)

if len(split_records) != expected_total:
    raise RuntimeError("Some images are missing from the split.")

# =====================================================
# 6. SAVE MANIFEST
# =====================================================

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

manifest_path = OUTPUT_DIR / "cardamom_split_manifest.csv"

with manifest_path.open(
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=[
            "class_name",
            "split",
            "group_id",
            "image_path",
        ]
    )

    writer.writeheader()
    writer.writerows(split_records)

print("\n================================")
print("CARDAMOM SPLIT COMPLETED")
print("================================")
print("Total images:", len(split_records))
print("Manifest:", manifest_path)
print("Near-duplicate group leakage: NONE")
print("Original images modified: NO")
