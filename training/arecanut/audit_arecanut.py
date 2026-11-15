
from pathlib import Path
from collections import Counter
from PIL import Image, ImageOps
import csv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_ROOT = PROJECT_ROOT / "dataset" / "Arecanut"
OUTPUT = Path(__file__).resolve().parent / "arecanut_image_audit.csv"

EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

records = []
class_counts = Counter()
size_counts = Counter()
mode_counts = Counter()
aspect_ratios = Counter()
errors = []

for path in DATASET_ROOT.rglob("*"):
    if not path.is_file() or path.suffix.lower() not in EXTENSIONS:
        continue

    parts = path.relative_to(DATASET_ROOT).parts

    if len(parts) >= 2:
        class_name = parts[1]
    else:
        class_name = "UNKNOWN"

    try:
        with Image.open(path) as image:
            image = ImageOps.exif_transpose(image)
            width, height = image.size
            mode = image.mode

            ratio = round(width / height, 2) if height else 0

            records.append({
                "path": str(path.relative_to(PROJECT_ROOT)),
                "class": class_name,
                "width": width,
                "height": height,
                "mode": mode,
                "aspect_ratio": ratio,
            })

            class_counts[class_name] += 1
            size_counts[(width, height)] += 1
            mode_counts[mode] += 1
            aspect_ratios[ratio] += 1

    except Exception as error:
        errors.append((str(path), str(error)))

with OUTPUT.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "path", "class", "width", "height",
            "mode", "aspect_ratio"
        ]
    )
    writer.writeheader()
    writer.writerows(records)

print("\n===== ARECANUT IMAGE AUDIT =====")
print("Total readable images:", len(records))
print("Unreadable images:", len(errors))

print("\nClass counts:")
for name, count in class_counts.items():
    print(name, ":", count)

print("\nImage modes:")
for name, count in mode_counts.items():
    print(name, ":", count)

print("\nMost common dimensions:")
for dimensions, count in size_counts.most_common(10):
    print(dimensions, ":", count)

print("\nAspect ratios:")
for ratio, count in sorted(aspect_ratios.items()):
    print(ratio, ":", count)

print("\nAudit report saved to:", OUTPUT)
