
from pathlib import Path
from PIL import Image
from skimage.metrics import structural_similarity as ssim
import numpy as np
import csv

ROOT = Path(
    "training/arecanut/external_sources/ARECANUT-DATASET/HEALTHY LEAF"
)
REPORT = Path(
    "training/arecanut/external_sources/external_duplicate_candidates.csv"
)

with open(REPORT, newline="", encoding="utf-8") as f:
    pairs = [
        row for row in csv.DictReader(f)
        if row["class"] == "HEALTHY LEAF"
    ]

def load_image(path):
    with Image.open(path) as img:
        img = img.convert("RGB")
        img = img.resize((256, 256))
        return np.asarray(img)

print("HEALTHY LEAF SSIM VERIFICATION")
print("-" * 65)

for i, pair in enumerate(pairs, 1):
    p1 = ROOT / pair["image_1"]
    p2 = ROOT / pair["image_2"]

    a = load_image(p1)
    b = load_image(p2)

    score = ssim(a, b, channel_axis=2, data_range=255)

    print(
        f"Pair {i}: SSIM={score:.4f} | "
        f"{p1.name} vs {p2.name}"
    )
