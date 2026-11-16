
import pandas as pd
from PIL import Image, ImageDraw
from pathlib import Path
import math

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "training/arecanut/results/misclassified_images.csv"
OUTPUT = ROOT / "training/arecanut/results/misclassified_contact_sheet.jpg"

df = pd.read_csv(REPORT)

thumb_width = 320
thumb_height = 240
label_height = 65
columns = 2
rows = math.ceil(len(df) / columns)

sheet = Image.new(
    "RGB",
    (columns * thumb_width, rows * (thumb_height + label_height)),
    "white"
)
draw = ImageDraw.Draw(sheet)

for index, row in df.iterrows():
    image_path = ROOT / row["image_path"]
    image = Image.open(image_path).convert("RGB")
    image.thumbnail((thumb_width - 10, thumb_height - 10))

    x = (index % columns) * thumb_width
    y = (index // columns) * (thumb_height + label_height)

    image_x = x + (thumb_width - image.width) // 2
    image_y = y + (thumb_height - image.height) // 2

    sheet.paste(image, (image_x, image_y))

    text = (
        f"Actual: {row['actual_class']}\n"
        f"Predicted: {row['predicted_class']} "
        f"({row['confidence']:.2f})"
    )
    draw.text((x + 5, y + thumb_height), text, fill="black")

sheet.save(OUTPUT, quality=95)

print(f"Contact sheet saved: {OUTPUT}")
