
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import math

ROOT = Path(
    "training/arecanut/external_sources/ARECANUT-DATASET/YELLOW LEAF"
)

OUTPUT = Path(
    "training/arecanut/external_sources/yellow_leaf_review.jpg"
)

files = sorted(
    p for p in ROOT.iterdir()
    if p.is_file()
    and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
)

CELL_W = 300
CELL_H = 260
COLUMNS = 3
ROWS = math.ceil(len(files) / COLUMNS)

sheet = Image.new("RGB", (COLUMNS * CELL_W, ROWS * CELL_H), "white")
draw = ImageDraw.Draw(sheet)

for index, path in enumerate(files):
    try:
        with Image.open(path) as original:
            img = ImageOps.exif_transpose(original).convert("RGB")
            img.thumbnail((CELL_W - 15, CELL_H - 45))

        x = (index % COLUMNS) * CELL_W
        y = (index // COLUMNS) * CELL_H

        sheet.paste(img, (x + (CELL_W - img.width) // 2, y + 5))
        draw.text(
            (x + 5, y + CELL_H - 30),
            f"{index + 1}. {path.name[:35]}",
            fill="black"
        )

    except Exception as error:
        print("Error:", path.name, error)

sheet.save(OUTPUT, quality=95)

print("Yellow Leaf images:", len(files))
print("Contact sheet saved:", OUTPUT)
