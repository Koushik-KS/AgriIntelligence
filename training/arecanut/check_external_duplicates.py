
from pathlib import Path
from PIL import Image
import imagehash
from itertools import combinations
import csv

ROOT = Path("training/arecanut/external_sources/ARECANUT-DATASET")
OUTPUT = Path("training/arecanut/external_sources")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

HASH_THRESHOLD = 8

results = []

for class_folder in sorted(ROOT.iterdir()):
    if not class_folder.is_dir() or class_folder.name == ".git":
        continue

    images = []

    for path in class_folder.iterdir():
        if path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        try:
            with Image.open(path) as img:
                phash = imagehash.phash(img.convert("RGB"))
                images.append((path, phash))
        except Exception as error:
            print("Could not process:", path, error)

    candidates = []

    for (path1, hash1), (path2, hash2) in combinations(images, 2):
        distance = hash1 - hash2

        if distance <= HASH_THRESHOLD:
            candidates.append((path1.name, path2.name, distance))

    print(f"\n{class_folder.name}:")
    print("Images checked:", len(images))
    print("Similar-image candidates:", len(candidates))

    for name1, name2, distance in candidates:
        results.append({
            "class": class_folder.name,
            "image_1": name1,
            "image_2": name2,
            "phash_distance": distance
        })

csv_path = OUTPUT / "external_duplicate_candidates.csv"

with open(csv_path, "w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=["class", "image_1", "image_2", "phash_distance"]
    )
    writer.writeheader()
    writer.writerows(results)

print("\nTotal candidate pairs:", len(results))
print("Report saved:", csv_path)
