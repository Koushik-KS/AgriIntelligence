
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import math

ROOT = Path(
    "training/arecanut/external_sources/ARECANUT-DATASET/BUD ROT"
)

OUTPUT_DIR = Path(
    "training/arecanut/external_sources/bud_rot_reviews"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

extensions = {".jpg", ".jpeg", ".png", ".webp"}

files = sorted(
    p for p in ROOT.iterdir()
    if p.is_file() and p.suffix.lower() in extensions
)

GROUP_SIZE = 4
CELL_W = 500
CELL_H = 430

print("Total Bud Rot images:", len(files))

for start in range(0, len(files), GROUP_SIZE):
    group = files[start:start + GROUP_SIZE]

    sheet = Image.new(
        "RGB",
        (CELL_W * 2, CELL_H * 2),
        "white"
    )

    draw = ImageDraw.Draw(sheet)

    for index, path in enumerate(group):
        try:
            with Image.open(path) as original:
                img = ImageOps.exif_transpose(original).convert("RGB")
                img.thumbnail((CELL_W - 30, CELL_H - 65))

            x = (index % 2) * CELL_W
            y = (index // 2) * CELL_H

            paste_x = x + (CELL_W - img.width) // 2
            paste_y = y + 5

            sheet.paste(img, (paste_x, paste_y))

            label = f"{start + index + 1}. {path.name}"

            draw.text(
                (x + 10, y + CELL_H - 45),
                label[:75],
                fill="black"
            )

        except Exception as error:
            print("Could not inspect:", path.name, error)

    first = start + 1
    last = start + len(group)

    output = OUTPUT_DIR / f"bud_rot_images_{first}_to_{last}.jpg"

    sheet.save(output, quality=95)

    print("Saved:", output)

print("\nContact sheet generation completed.")
