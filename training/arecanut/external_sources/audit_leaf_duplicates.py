
from pathlib import Path
from collections import defaultdict
from PIL import Image
import hashlib
import csv

ROOT = Path("training/arecanut/external_sources/ARECANUT-DATASET")

CLASSES = ["HEALTHY LEAF", "RING SPOT", "YELLOW LEAF"]

OUTPUT = Path(
    "training/arecanut/external_sources/leaf_duplicate_audit.csv"
)

rows = []

for class_name in CLASSES:
    folder = ROOT / class_name
    hash_groups = defaultdict(list)
    image_count = 0
    unreadable = []

    for path in sorted(folder.iterdir()):
        if not path.is_file() or path.suffix.lower() not in {
            ".jpg", ".jpeg", ".png", ".webp"
        }:
            continue

        image_count += 1

        try:
            with Image.open(path) as img:
                img.verify()

            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            hash_groups[digest].append(path.name)

        except Exception as error:
            unreadable.append(path.name)
            print("Unreadable:", class_name, path.name, error)

    duplicate_groups = [
        names for names in hash_groups.values() if len(names) > 1
    ]

    print(f"\n{class_name}")
    print("Images:", image_count)
    print("Exact duplicate groups:", len(duplicate_groups))
    print("Unreadable images:", len(unreadable))

    for names in duplicate_groups:
        print("Duplicate:", " | ".join(names))
        rows.append({
            "class": class_name,
            "files": " | ".join(names),
            "sha256_exact_duplicate": True
        })

with OUTPUT.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=["class", "files", "sha256_exact_duplicate"]
    )
    writer.writeheader()
    writer.writerows(rows)

print("\nAudit complete.")
print("Report:", OUTPUT)
