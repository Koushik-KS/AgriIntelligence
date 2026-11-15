
from pathlib import Path
from PIL import Image
import hashlib
from collections import defaultdict

folders = {
    "Bud Rot": Path("dataset/Arecanut/Disease/BUD ROT"),
    "Ring Spot": Path("dataset/Arecanut/Disease/RING SPOT"),
    "Yellow Leaf": Path("dataset/Arecanut/Disease/YELLOW LEAF"),
    "Healthy Leaf": Path("dataset/Arecanut/Healthy/HEALTHY LEAF")
}

extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
hash_groups = defaultdict(list)

total = 0
readable = 0
unreadable = []

for class_name, folder in folders.items():
    count = 0

    for path in folder.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue

        total += 1
        count += 1

        try:
            with Image.open(path) as img:
                img.verify()

            readable += 1
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            hash_groups[digest].append((class_name, str(path)))

        except Exception as error:
            unreadable.append((str(path), str(error)))

    print(f"{class_name}: {count} images")

duplicates = {
    digest: files
    for digest, files in hash_groups.items()
    if len(files) > 1
}

print("\n========== VALIDATION REPORT ==========")
print("Total images:", total)
print("Readable images:", readable)
print("Unreadable images:", len(unreadable))
print("Exact duplicate groups:", len(duplicates))

if unreadable:
    print("\nUnreadable files:")
    for path, error in unreadable:
        print(path, "->", error)

if duplicates:
    print("\nDuplicate files:")
    for files in duplicates.values():
        for class_name, path in files:
            print(class_name, "->", path)
        print("---")
