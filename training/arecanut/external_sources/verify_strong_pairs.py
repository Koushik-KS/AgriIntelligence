
from pathlib import Path
from PIL import Image, ImageOps, ImageChops
import hashlib
import csv

ROOT = Path(
    "training/arecanut/external_sources/ARECANUT-DATASET"
)

REPORT = Path(
    "training/arecanut/external_sources/external_ssim_audit.csv"
)

OUTPUT = Path(
    "training/arecanut/external_sources/strong_pair_verification.csv"
)

def sha256_file(path):
    digest = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()

def image_info(path):
    with Image.open(path) as img:
        original_dimensions = img.size
        corrected = ImageOps.exif_transpose(img).convert("RGB")
        pixels = corrected.copy()

    return original_dimensions, pixels

with open(REPORT, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

selected = []

for class_name in ["KOLEROGA", "RING SPOT"]:
    candidates = [
        row for row in rows
        if row["class"] == class_name
    ]

    candidates.sort(
        key=lambda row: float(row["ssim_score"]),
        reverse=True
    )

    selected.extend(candidates[:2])

results = []

for index, row in enumerate(selected, 1):
    path1 = ROOT / row["class"] / row["image_1"]
    path2 = ROOT / row["class"] / row["image_2"]

    dim1, image1 = image_info(path1)
    dim2, image2 = image_info(path2)

    hash1 = sha256_file(path1)
    hash2 = sha256_file(path2)

    same_file_hash = hash1 == hash2

    same_dimensions = image1.size == image2.size

    same_pixels = (
        same_dimensions
        and ImageChops.difference(image1, image2).getbbox() is None
    )

    result = {
        "class": row["class"],
        "image_1": row["image_1"],
        "image_2": row["image_2"],
        "ssim": row["ssim_score"],
        "dimensions_1": str(dim1),
        "dimensions_2": str(dim2),
        "file_size_1": path1.stat().st_size,
        "file_size_2": path2.stat().st_size,
        "same_sha256": same_file_hash,
        "same_dimensions": same_dimensions,
        "same_pixels": same_pixels,
    }

    results.append(result)

    print(f"\nPAIR {index}: {row['class']}")
    print("Image 1:", row["image_1"])
    print("Image 2:", row["image_2"])
    print("Dimensions 1:", dim1)
    print("Dimensions 2:", dim2)
    print("Same SHA-256:", same_file_hash)
    print("Same decoded pixels:", same_pixels)

with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    fields = list(results[0].keys())
    writer = csv.DictWriter(f, fieldnames=fields)
    writer.writeheader()
    writer.writerows(results)

print("\nVERIFICATION COMPLETED")
print("Report saved:", OUTPUT)
