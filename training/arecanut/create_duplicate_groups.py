
import csv
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "training" / "arecanut" / "arecanut_visual_duplicate_candidates.csv"
OUTPUT = ROOT / "training" / "arecanut" / "arecanut_candidate_groups.csv"

parent = {}

def find(x):
    parent.setdefault(x, x)
    if parent[x] != x:
        parent[x] = find(parent[x])
    return parent[x]

def union(a, b):
    parent[find(a)] = find(b)

with INPUT.open("r", newline="", encoding="utf-8-sig") as file:
    reader = csv.DictReader(file)

    for row in reader:
        a = row["path_1"]
        b = row["path_2"]
        union(a, b)

groups = defaultdict(list)

for image in parent:
    groups[find(image)].append(image)

with OUTPUT.open("w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["group_id", "image_path", "group_size"])

    for number, images in enumerate(groups.values(), start=1):
        group_id = f"CANDIDATE_GROUP_{number:03d}"

        for image in sorted(images):
            writer.writerow([group_id, image, len(images)])

print(f"Candidate groups created: {len(groups)}")
print(f"Images included in groups: {len(parent)}")
print(f"Report saved to: {OUTPUT}")
