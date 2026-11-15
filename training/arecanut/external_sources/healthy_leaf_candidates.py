
from pathlib import Path
from PIL import Image, ImageDraw
import csv
import math

ROOT = Path("training/arecanut/external_sources/ARECANUT-DATASET")
REPORT = Path("training/arecanut/external_sources/external_duplicate_candidates.csv")
OUTPUT = Path("training/arecanut/external_sources/healthy_leaf_candidates.jpg")

with open(REPORT, newline="", encoding="utf-8") as f:
    pairs = [
        row for row in csv.DictReader(f)
        if row["class"] == "HEALTHY LEAF"
    ]

cell_w, cell_h = 440, 210
cols = 2
rows = math.ceil(len(pairs) / cols)

sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
draw = ImageDraw.Draw(sheet)

for i, pair in enumerate(pairs):
    x = (i % cols) * cell_w
    y = (i // cols) * cell_h

    for j, key in enumerate(["image_1", "image_2"]):
        path = ROOT / "HEALTHY LEAF" / pair[key]

        with Image.open(path) as img:
            img.thumbnail((200, 155))
            px = x + j * 220 + 10
            sheet.paste(img.convert("RGB"), (px, y + 5))
            draw.text((px, y + 165), pair[key][:27], fill="black")

    draw.text(
        (x + 10, y + 190),
        f"Pair {i + 1} | pHash distance: {pair['phash_distance']}",
        fill="blue"
    )

sheet.save(OUTPUT)
print("Created:", OUTPUT)
print("Candidate pairs displayed:", len(pairs))
