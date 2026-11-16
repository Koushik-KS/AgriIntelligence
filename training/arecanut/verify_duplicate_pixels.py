
from pathlib import Path
from PIL import Image, ImageOps, ImageChops
import csv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = Path(__file__).resolve().parent / "arecanut_visual_duplicate_candidates.csv"
OUTPUT = Path(__file__).resolve().parent / "arecanut_pixel_duplicate_report.csv"


def load_image(relative_path):
    path = PROJECT_ROOT / relative_path

    with Image.open(path) as image:
        return ImageOps.exif_transpose(image).convert("RGB").copy()


results = []

with CSV_PATH.open("r", newline="", encoding="utf-8") as file:
    pairs = list(csv.DictReader(file))

for index, pair in enumerate(pairs, start=1):
    try:
        image1 = load_image(pair["path_1"])
        image2 = load_image(pair["path_2"])

        same_size = image1.size == image2.size
        pixel_equal = False
        grayscale_equal = False

        if same_size:
            pixel_equal = ImageChops.difference(
                image1, image2
            ).getbbox() is None

            grayscale1 = image1.convert("L")
            grayscale2 = image2.convert("L")

            grayscale_equal = ImageChops.difference(
                grayscale1, grayscale2
            ).getbbox() is None

        result = {
            "pair": index,
            "path_1": pair["path_1"],
            "path_2": pair["path_2"],
            "class": pair["class_1"],
            "hash_distance": pair["hash_distance"],
            "size_1": str(image1.size),
            "size_2": str(image2.size),
            "same_size": same_size,
            "pixel_equal": pixel_equal,
            "grayscale_equal": grayscale_equal,
        }

    except Exception as error:
        result = {
            "pair": index,
            "path_1": pair["path_1"],
            "path_2": pair["path_2"],
            "class": pair["class_1"],
            "hash_distance": pair["hash_distance"],
            "error": str(error),
        }

    results.append(result)

    print(
        f"Pair {index}: "
        f"Same size={result.get('same_size', False)}, "
        f"Pixel equal={result.get('pixel_equal', False)}, "
        f"Grayscale equal={result.get('grayscale_equal', False)}"
    )

with OUTPUT.open("w", newline="", encoding="utf-8") as file:
    fieldnames = list(dict.fromkeys(
        key for result in results for key in result
    ))

    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

print("\n===== PIXEL COMPARISON REPORT =====")
print("Pairs checked:", len(results))
print("Exact pixel duplicates:", sum(
    r.get("pixel_equal", False) for r in results
))
print("Grayscale-equivalent pairs:", sum(
    r.get("grayscale_equal", False) for r in results
))
print("Report saved to:", OUTPUT)
print("Original images were not modified.")
