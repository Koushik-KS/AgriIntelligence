
from pathlib import Path
from PIL import Image, ImageDraw
import csv

ROOT = Path(
    "training/arecanut/external_sources/ARECANUT-DATASET"
)

REPORT = Path(
    "training/arecanut/external_sources/external_ssim_audit.csv"
)

OUTPUT = Path(
    "training/arecanut/external_sources/strong_duplicate_review.jpg"
)

with open(REPORT, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

# Select the two strongest Koleroga and two strongest Ring Spot pairs
selected = []

for class_name in ["KOLEROGA", "RING SPOT"]:
    class_rows = [
        row for row in rows
        if row["class"] == class_name
    ]

    class_rows.sort(
        key=lambda row: float(row["ssim_score"]),
        reverse=True
    )

    selected.extend(class_rows[:2])

if len(selected) != 4:
    print("Expected 4 pairs, found:", len(selected))
    raise SystemExit(1)

cell_w = 420
image_h = 300
label_h = 65
pair_h = image_h + label_h

sheet = Image.new("RGB", (cell_w * 2, pair_h * 4), "white")
draw = ImageDraw.Draw(sheet)

for i, row in enumerate(selected):
    y = i * pair_h

    for j, key in enumerate(["image_1", "image_2"]):
        path = ROOT / row["class"] / row[key]

        with Image.open(path) as img:
            img = img.convert("RGB")
            img.thumbnail((cell_w - 20, image_h - 20))

            x = j * cell_w + (cell_w - img.width) // 2
            image_y = y + (image_h - img.height) // 2

            sheet.paste(img, (x, image_y))

        draw.text(
            (j * cell_w + 8, y + image_h + 5),
            row[key][:55],
            fill="black"
        )

    draw.text(
        (8, y + image_h + 35),
        f'{row["class"]} | SSIM: {row["ssim_score"]}',
        fill="blue"
    )

sheet.save(OUTPUT, quality=95)

print("Contact sheet saved:", OUTPUT)
print("Pairs included:", len(selected))
