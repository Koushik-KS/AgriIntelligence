
from pathlib import Path
from PIL import Image
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "dataset" / "Arecanut"
OUTPUT = ROOT / "training" / "arecanut" / "arecanut_source_audit.csv"

records = []

for path in sorted(DATASET.rglob("*")):
    if not path.is_file():
        continue

    try:
        with Image.open(path) as img:
            exif = img.getexif()

            records.append({
                "image_path": str(path.relative_to(ROOT)),
                "class_folder": path.parent.name,
                "filename": path.name,
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "camera_make": exif.get(271, ""),
                "camera_model": exif.get(272, ""),
                "date_taken": exif.get(36867, ""),
                "software": exif.get(305, ""),
                "file_size_kb": round(path.stat().st_size / 1024, 2)
            })

    except Exception as error:
        print(f"Could not inspect {path.name}: {error}")

df = pd.DataFrame(records)
df.to_csv(OUTPUT, index=False)

print("\nARECANUT SOURCE AUDIT")
print("---------------------")
print(f"Images inspected: {len(df)}")
print(f"Images with camera metadata: {(df['camera_make'].astype(str).str.len() > 0).sum()}")
print(f"Images with capture dates: {(df['date_taken'].astype(str).str.len() > 0).sum()}")
print(f"Images with software metadata: {(df['software'].astype(str).str.len() > 0).sum()}")
print(f"\nReport saved: {OUTPUT}")
