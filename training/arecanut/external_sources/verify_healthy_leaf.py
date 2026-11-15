
from pathlib import Path
from PIL import Image, ImageOps, ImageChops
import hashlib
import csv

ROOT = Path(
    "training/arecanut/external_sources/ARECANUT-DATASET/HEALTHY LEAF"
)

REPORT = Path(
    "training/arecanut/external_sources/external_ssim_audit.csv"
)

OUTPUT = Path(
    "training/arecanut/external_sources/healthy_leaf_verification.csv"
)

def sha256_file(path):
    digest = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()

def load_pixels(path):
    with Image.open(path) as img:
        dimensions = img.size
        pixels = ImageOps.exif_transpose(img).convert("RGB").copy()

    return dimensions, pixels

with open(REPORT, newline="", encoding="utf-8") as f:
    pairs = [
        row for row in csv.DictReader(f)
        if row["class"] == "HEALTHY LEAF"
    ]

results = []

for index, pair in enumerate(pairs, 1):
    path1 = ROOT / pair["image_1"]
    path2 = ROOT / pair["image_2"]

    dim1, image1 = load_pixels(path1)
    dim2, image2 = load_pixels(path2)

    hash1 = sha256_file(path1)
    hash2 = sha256_file(path2)

    same_sha256 = hash1 == hash2
    same_dimensions = image1.size == image2.size

    same_pixels = (
        same_dimensions
        and ImageChops.difference(image1, image2).getbbox() is None
    )

    result = {
        "pair": index,
        "image_1": pair["image_1"],
        "image_2": pair["image_2"],
        "ssim": pair["ssim_score"],
        "dimensions_1": str(dim1),
        "dimensions_2": str(dim2),
        "same_sha256": same_sha256,
        "same_dimensions": same_dimensions,
        "same_pixels": same_pixels
    }

    results.append(result)

    print(
        f"Pair {index:02d} | "
        f"SSIM={pair['ssim_score']} | "
        f"SHA256={same_sha256} | "
        f"Pixels={same_pixels}"
    )

with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=list(results[0].keys())
    )
    writer.writeheader()
    writer.writerows(results)

exact_hash = sum(r["same_sha256"] for r in results)
exact_pixels = sum(r["same_pixels"] for r in results)

print("\nHEALTHY LEAF VERIFICATION SUMMARY")
print("Total candidate pairs:", len(results))
print("Identical SHA-256 pairs:", exact_hash)
print("Identical pixel pairs:", exact_pixels)
print("Report saved:", OUTPUT)
