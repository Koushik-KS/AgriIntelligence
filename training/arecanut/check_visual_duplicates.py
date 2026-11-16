
from pathlib import Path
from itertools import combinations
import csv
import imagehash
from PIL import Image, ImageOps

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASET_ROOT = PROJECT_ROOT / "dataset" / "Arecanut"
OUTPUT = Path(__file__).resolve().parent / "arecanut_visual_duplicate_candidates.csv"

EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
HAMMING_THRESHOLD = 4


def get_class(path):
    parts = path.relative_to(DATASET_ROOT).parts

    if len(parts) >= 2 and parts[0].lower() == "disease":
        return parts[1].strip()

    if len(parts) >= 2 and parts[0].lower() == "healthy":
        return parts[1].strip()

    return "UNKNOWN"


def main():
    if not DATASET_ROOT.is_dir():
        raise FileNotFoundError(DATASET_ROOT)

    image_paths = [
        path
        for path in DATASET_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in EXTENSIONS
    ]

    image_records = []
    unreadable = 0

    print(f"Found {len(image_paths)} images.")
    print("Calculating perceptual hashes...")

    for index, path in enumerate(image_paths, start=1):
        try:
            with Image.open(path) as image:
                image = ImageOps.exif_transpose(image).convert("RGB")
                fingerprint = imagehash.phash(image, hash_size=8)

            image_records.append({
                "path": str(path.relative_to(PROJECT_ROOT)),
                "class": get_class(path),
                "hash": fingerprint,
            })

        except (OSError, ValueError) as error:
            unreadable += 1
            print(f"Could not read: {path} -> {error}")

        if index % 50 == 0:
            print(f"Processed {index}/{len(image_paths)} images...")

    candidates = []

    for first, second in combinations(image_records, 2):
        distance = first["hash"] - second["hash"]

        if distance <= HAMMING_THRESHOLD:
            candidates.append({
                "path_1": first["path"],
                "class_1": first["class"],
                "path_2": second["path"],
                "class_2": second["class"],
                "hash_distance": distance,
            })

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "path_1",
        "class_1",
        "path_2",
        "class_2",
        "hash_distance",
    ]

    with OUTPUT.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(candidates)

    cross_class = sum(
        1 for pair in candidates
        if pair["class_1"] != pair["class_2"]
    )

    print("\n===== ARECANUT VISUAL DUPLICATE REPORT =====")
    print(f"Images found: {len(image_paths)}")
    print(f"Images successfully checked: {len(image_records)}")
    print(f"Unreadable images: {unreadable}")
    print(f"Candidate pairs: {len(candidates)}")
    print(f"Pairs across different classes: {cross_class}")
    print(f"Report saved to: {OUTPUT}")

    print("\nThese are possible visual matches, not confirmed duplicates.")
    print("No original dataset images were modified.")


if __name__ == "__main__":
    main()
