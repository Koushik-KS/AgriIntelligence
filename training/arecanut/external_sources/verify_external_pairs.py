
from pathlib import Path
from PIL import Image
from skimage.metrics import structural_similarity as ssim
import numpy as np
import hashlib
import csv

BASE = Path("training/arecanut/external_sources")
DATASET = BASE / "ARECANUT-DATASET"
INPUT_CSV = BASE / "external_duplicate_candidates.csv"
OUTPUT_CSV = BASE / "external_ssim_results.csv"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def sha256_file(path):
    digest = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def load_image(path):
    with Image.open(path) as img:
        img = img.convert("RGB")
        img = img.resize((256, 256))
        return np.asarray(img)


with open(INPUT_CSV, newline="", encoding="utf-8") as f:
    candidates = list(csv.DictReader(f))

results = []

print("EXTERNAL DATASET SSIM VERIFICATION")
print("=" * 65)

for index, pair in enumerate(candidates, 1):
    class_name = pair["class"]
    image_1 = pair["image_1"]
    image_2 = pair["image_2"]

    path_1 = DATASET / class_name / image_1
    path_2 = DATASET / class_name / image_2

    if not path_1.exists() or not path_2.exists():
        print(f"Skipping pair {index}: image file missing")
        continue

    try:
        hash_1 = sha256_file(path_1)
        hash_2 = sha256_file(path_2)

        pixels_1 = load_image(path_1)
        pixels_2 = load_image(path_2)

        pixel_identical = np.array_equal(pixels_1, pixels_2)
        score = ssim(
            pixels_1,
            pixels_2,
            channel_axis=2,
            data_range=255
        )

        sha_identical = hash_1 == hash_2

        phash_distance = pair.get(
            "phash_distance",
            pair.get("distance", "")
        )

        results.append({
            "class": class_name,
            "image_1": image_1,
            "image_2": image_2,
            "phash_distance": phash_distance,
            "ssim": round(float(score), 4),
            "sha256_identical": sha_identical,
            "resized_pixels_identical": pixel_identical
        })

        print(
            f"{index:02d} | {class_name:12s} | "
            f"SSIM={score:.4f} | "
            f"SHA256={sha_identical} | "
            f"Pixels={pixel_identical}"
        )

    except Exception as error:
        print(f"Error in pair {index}: {error}")


fieldnames = [
    "class",
    "image_1",
    "image_2",
    "phash_distance",
    "ssim",
    "sha256_identical",
    "resized_pixels_identical"
]

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)


print("\nVERIFICATION SUMMARY")
print("=" * 65)
print("Candidate pairs:", len(candidates))
print("Successfully checked:", len(results))
print(
    "Identical SHA-256 pairs:",
    sum(r["sha256_identical"] for r in results)
)
print(
    "Identical resized pixel pairs:",
    sum(r["resized_pixels_identical"] for r in results)
)
print(
    "High SSIM pairs (>= 0.90):",
    sum(r["ssim"] >= 0.90 for r in results)
)
print("Report saved:", OUTPUT_CSV)
