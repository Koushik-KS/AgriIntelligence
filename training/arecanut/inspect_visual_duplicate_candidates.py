
from pathlib import Path
import csv
import math
from PIL import Image, ImageOps, ImageDraw

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = Path(__file__).resolve().parent / "arecanut_visual_duplicate_candidates.csv"
OUTPUT_DIR = Path(__file__).resolve().parent / "duplicate_review"

OUTPUT_DIR.mkdir(exist_ok=True)

with CSV_PATH.open("r", newline="", encoding="utf-8") as file:
    pairs = list(csv.DictReader(file))

if not pairs:
    print("No candidate pairs to inspect.")
    raise SystemExit

PAGE_SIZE = 4
IMAGE_WIDTH = 320
IMAGE_HEIGHT = 220

for page_index in range(math.ceil(len(pairs) / PAGE_SIZE)):
    page_pairs = pairs[
        page_index * PAGE_SIZE:(page_index + 1) * PAGE_SIZE
    ]

    sheet = Image.new(
        "RGB",
        (IMAGE_WIDTH * 2, (IMAGE_HEIGHT + 65) * len(page_pairs)),
        "white"
    )
    draw = ImageDraw.Draw(sheet)

    for row_index, pair in enumerate(page_pairs):
        y = row_index * (IMAGE_HEIGHT + 65)

        for column, key in enumerate(["path_1", "path_2"]):
            image_path = PROJECT_ROOT / pair[key]
            x = column * IMAGE_WIDTH

            try:
                with Image.open(image_path) as image:
                    image = ImageOps.exif_transpose(image).convert("RGB")
                    image.thumbnail((IMAGE_WIDTH - 20, IMAGE_HEIGHT - 35))
                    sheet.paste(image, (x + 10, y + 10))

                draw.text(
                    (x + 10, y + IMAGE_HEIGHT - 20),
                    Path(pair[key]).name[:42],
                    fill="black"
                )

            except Exception as error:
                draw.text(
                    (x + 10, y + 20),
                    f"Cannot open: {error}",
                    fill="red"
                )

        draw.text(
            (10, y + IMAGE_HEIGHT + 5),
            f"Pair {page_index * PAGE_SIZE + row_index + 1} | "
            f"Class: {pair['class_1']} | "
            f"Distance: {pair['hash_distance']}",
            fill="blue"
        )

    output_path = OUTPUT_DIR / f"duplicate_review_{page_index + 1}.jpg"
    sheet.save(output_path, quality=90)
    print(f"Saved: {output_path}")

print(f"\nTotal candidate pairs: {len(pairs)}")
print("Open the generated comparison sheets and inspect the images.")
