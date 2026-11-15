
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import random
import math

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_ROOT = PROJECT_ROOT / "dataset" / "Arecanut"
OUTPUT = PROJECT_ROOT / "training" / "arecanut" / "arecanut_class_samples.jpg"

random.seed(42)

classes = {
    "BUD ROT": DATASET_ROOT / "Disease" / "BUD ROT",
    "RING SPOT": DATASET_ROOT / "Disease" / "RING SPOT",
    "YELLOW LEAF": DATASET_ROOT / "Disease" / "YELLOW LEAF",
    "HEALTHY LEAF": DATASET_ROOT / "Healthy" / "HEALTHY LEAF",
}

samples_per_class = 6
thumb_width = 220
thumb_height = 170
label_height = 28

columns = 4
rows = samples_per_class

sheet = Image.new(
    "RGB",
    (columns * thumb_width, rows * (thumb_height + label_height)),
    "white"
)

draw = ImageDraw.Draw(sheet)

for col, (class_name, folder) in enumerate(classes.items()):
    paths = [
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in
        {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    ]

    selected = random.sample(paths, min(samples_per_class, len(paths)))

    for row, path in enumerate(selected):
        try:
            with Image.open(path) as image:
                image = ImageOps.exif_transpose(image).convert("RGB")
                image.thumbnail((thumb_width - 10, thumb_height - 10))

            x = col * thumb_width
            y = row * (thumb_height + label_height)

            sheet.paste(image, (x + 5, y + 5))
            draw.text(
                (x + 5, y + thumb_height + 3),
                f"{class_name}: {path.name[:20]}",
                fill="black"
            )

        except Exception as error:
            print("Skipped:", path, error)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
sheet.save(OUTPUT, quality=92)

print("Sample sheet saved to:", OUTPUT)
