
from pathlib import Path
from collections import defaultdict
import hashlib

ORIGINAL = Path("dataset/Arecanut")
EXTERNAL = Path(
    "training/arecanut/external_sources/ARECANUT-DATASET"
)

CLASSES = ["HEALTHY LEAF", "RING SPOT", "YELLOW LEAF"]

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def image_files(folder):
    return [
        p for p in folder.rglob("*")
        if p.is_file()
        and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}
    ]

original_hashes = defaultdict(list)

for path in image_files(ORIGINAL):
    original_hashes[sha256(path)].append(path)

print("Original images indexed:", sum(map(len, original_hashes.values())))

total_external = 0
total_matches = 0

for class_name in CLASSES:
    folder = EXTERNAL / class_name
    matches = []

    files = image_files(folder)
    total_external += len(files)

    for path in files:
        digest = sha256(path)

        if digest in original_hashes:
            total_matches += 1
            matches.append((path, original_hashes[digest]))

    print(f"\n{class_name}")
    print("External images:", len(files))
    print("Exact matches with original dataset:", len(matches))

    for external_path, original_paths in matches:
        for original_path in original_paths:
            print("MATCH:", external_path.name, "<->", original_path)

print("\nTOTAL EXTERNAL IMAGES:", total_external)
print("TOTAL EXACT OVERLAPS:", total_matches)
