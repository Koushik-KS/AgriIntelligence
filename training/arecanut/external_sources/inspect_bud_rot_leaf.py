from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import math

ROOT = Path(
    "training/arecanut/external_sources/ARECANUT-DATASET/BUD ROT"
)

OUTPUT = Path(
    "training/arecanut/external_sources/bud_rot_leaf_review.jpg"
)

files = sorted(
    p for p in ROOT.iterdir()
    if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
)

thumb_w, thumb_h = 220, 190
label_h = 35
columns = 4
rows = math.ceil(len(files) / columns)

sheet = Image.new(
    "RGB",
    (columns * thumb_w, rows * (thumb_h + label_h)),
    "white"
)

draw = ImageDraw.Draw(sheet)

for index, path in enumerate(files):
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((thumb_w - 10, thumb_h - 10))

    x = (index % columns) * thumb_w
    y = (index // columns) * (thumb_h + label_h)

    sheet.paste(img, (x + (thumb_w - img.width) // 2, y + 5))
    draw.text(
        (x + 5, y + thumb_h),
        f"{index + 1}. {path.name[:28]}",
        fill="black"
    )

sheet.save(OUTPUT, quality=90)

print("Images:", len(files))
print("Contact sheet saved:", OUTPUT)