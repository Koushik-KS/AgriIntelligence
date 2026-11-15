
from pathlib import Path
from PIL import Image
from skimage.metrics import structural_similarity as ssim
import numpy as np
import imagehash
import csv
from itertools import combinations

ROOT = Path("training/arecanut/external_sources/ARECANUT-DATASET")
OUTPUT = Path("training/arecanut/external_sources/external_ssim_audit.csv")

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

def load_image(path):
    with Image.open(path) as img:
        img = img.convert("RGB")
        img = img.resize((256, 256))
        return np.asarray(img)

results = []

for folder in sorted(ROOT.iterdir()):
    if not folder.is_dir() or folder.name == ".git":
        continue

    images = [
        p for p in folder.iterdir()
        if p.suffix.lower() in EXTENSIONS
    ]

    print(f"\nChecking: {folder.name}")
    print("Images:", len(images))

    loaded = []

    for path in images:
        try:
            array = load_image(path)
            phash = imagehash.phash(Image.fromarray(array))
            loaded.append((path, array, phash))
        except Exception as error:
            print("Skipped:", path.name, error)

    count = 0

    for (p1, a, h1), (p2, b, h2) in combinations(loaded, 2):
        phash_distance = h1 - h2

        # Keep candidate pairs for SSIM analysis
        if phash_distance <= 8:
            score = ssim(a, b, channel_axis=2, data_range=255)
            count += 1

            results.append({
                "class": folder.name,
                "image_1": p1.name,
                "image_2": p2.name,
                "phash_distance": phash_distance,
                "ssim_score": round(float(score), 4)
            })

    print("Candidate pairs checked:", count)

with open(OUTPUT, "w", newline="", encoding="utf-8") as file:
    fields = [
        "class", "image_1", "image_2",
        "phash_distance", "ssim_score"
    ]

    writer = csv.DictWriter(file, fieldnames=fields)
    writer.writeheader()
    writer.writerows(results)

print("\nTOTAL CANDIDATE PAIRS:", len(results))
print("Report saved:", OUTPUT)
