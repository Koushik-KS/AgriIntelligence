
from pathlib import Path
from PIL import Image, ImageDraw
import csv
import math

ROOT = Path(
    "training/arecanut/external_sources/ARECANUT-DATASET/HEALTHY LEAF"
)

REPORT = Path(
    "training/arecanut/external_sources/external_ssim_audit.csv"
)

OUTPUT_DIR = Path(
    "training/arecanut/external_sources/healthy_leaf_reviews"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

with open(REPORT, newline="", encoding="utf-8") as f:
    rows = [
        row for row in csv.DictReader(f)
        if row["class"] == "HEALTHY LEAF"
    ]

rows.sort(
    key=lambda row: float(row["ssim_score"]),
    reverse=True
)

cell_w = 500
image_h = 260
label_h = 55
pair_h = image_h + label_h
pairs_per_sheet = 5

total_sheets = math.ceil(len(rows) / pairs_per_sheet)

for sheet_index in range(total_sheets):
    start = sheet_index * pairs_per_sheet
    batch = rows[start:start + pairs_per_sheet]

    sheet = Image.new(
        "RGB",
        (cell_w * 2, pair_h * len(batch)),
        "white"
    )

    draw = ImageDraw.Draw(sheet)

    for i, row in enumerate(batch):
        y = i * pair_h

        for j, key in enumerate(["image_1", "image_2"]):
            path = ROOT / row[key]

            with Image.open(path) as img:
                img = img.convert("RGB")
                img.thumbnail((cell_w - 20, image_h - 15))

                x = j * cell_w + (cell_w - img.width) // 2
                image_y = y + (image_h - img.height) // 2

                sheet.paste(img, (x, image_y))

            draw.text(
                (j * cell_w + 8, y + image_h + 3),
                row[key][:65],
                fill="black"
            )

        draw.text(
            (8, y + image_h + 28),
            f'Pair {start + i + 1} | SSIM: {row["ssim_score"]}',
            fill="blue"
        )

    output = OUTPUT_DIR / f"healthy_leaf_part_{sheet_index + 1}.jpg"
    sheet.save(output, quality=95)

    print("Saved:", output)

print("\nTotal candidate pairs:", len(rows))
print("Contact sheets generated:", total_sheets)
