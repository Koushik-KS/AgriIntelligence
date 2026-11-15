
import pandas as pd
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]

CSV_PATH = ROOT / "training/arecanut/results/misclassified_images.csv"
REVIEW_DIR = ROOT / "training/arecanut/results/manual_review"

df = pd.read_csv(CSV_PATH)

REVIEW_DIR.mkdir(parents=True, exist_ok=True)

for index, row in df.iterrows():
    source = ROOT / row["image_path"]

    filename = (
        f"{index + 1:02d}_"
        f"Actual-{row['actual_class'].replace(' ', '_')}_"
        f"Predicted-{row['predicted_class'].replace(' ', '_')}_"
        f"{source.name}"
    )

    destination = REVIEW_DIR / filename
    shutil.copy2(source, destination)

    print(f"Copied: {filename}")

print(f"\nReview images saved in: {REVIEW_DIR}")
print(f"Total images copied: {len(df)}")
