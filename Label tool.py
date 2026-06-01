"""
PIPE_VISION_AI — Manual Labeling Tool
Use this to label pipe photos collected from field partners.
Run at label parties with certified inspectors.

Run: python3 label_tool.py --folder /path/to/field/photos
"""

import os
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime

DATASET_DIR   = os.path.expanduser("~/Desktop/OKW FieldSync/PipeVisionDataset")
MANIFEST_PATH = os.path.join(DATASET_DIR, "manifest.json")

CLASSES = {
    "1": ("LEAD",     "Confirmed lead pipe — visible lead joints, grey soft metal"),
    "2": ("NON_LEAD", "Confirmed non-lead — copper, plastic, iron, brass"),
    "3": ("GRR",      "Galvanized Requiring Replacement — downstream of lead"),
    "4": ("UNKNOWN",  "Cannot determine from photo — too dark, blurry, or obscured"),
    "s": ("SKIP",     "Skip this image — not a pipe photo"),
}

CONFIDENCE = {
    "1": "high",
    "2": "medium",
    "3": "low",
}

def load_manifest():
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH) as f:
            return json.load(f)
    return {"version": "1.0", "created": datetime.now().isoformat(), "images": []}

def save_manifest(manifest):
    os.makedirs(DATASET_DIR, exist_ok=True)
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)

def get_already_labeled(manifest):
    return {img["source_path"] for img in manifest["images"] if img.get("source_path")}

def label_folder(folder_path, inspector_name, manifest):
    folder = Path(folder_path)
    extensions = {".jpg", ".jpeg", ".png", ".heic", ".heif"}
    photos = [p for p in folder.iterdir()
              if p.suffix.lower() in extensions and p.is_file()]

    already_labeled = get_already_labeled(manifest)
    photos = [p for p in photos if str(p) not in already_labeled]

    if not photos:
        print("No new photos to label in this folder.")
        return 0

    print(f"\nFound {len(photos)} unlabeled photos.")
    print(f"Inspector: {inspector_name}")
    print("\nLABEL GUIDE:")
    for key, (cls, desc) in CLASSES.items():
        print(f"  {key} → {cls}: {desc}")

    labeled = 0
    for i, photo_path in enumerate(sorted(photos), 1):
        print(f"\n{'='*50}")
        print(f"Photo {i}/{len(photos)}: {photo_path.name}")
        print(f"Full path: {photo_path}")

        # Try to open image for preview (terminal only shows path)
        try:
            os.system(f"open '{photo_path}'")  # Opens in Preview on Mac
        except Exception:
            pass

        print("\nLabel:")
        for key, (cls, desc) in CLASSES.items():
            print(f"  [{key}] {cls} — {desc}")

        while True:
            choice = input("\nEnter label (1-4, s=skip, q=quit): ").strip().lower()
            if choice == "q":
                save_manifest(manifest)
                print(f"\nSaved. Labeled {labeled} photos.")
                return labeled
            if choice in CLASSES:
                break
            print("Invalid. Enter 1, 2, 3, 4, s, or q.")

        cls_name = CLASSES[choice][0]
        if cls_name == "SKIP":
            print("Skipped.")
            continue

        # Confidence
        print("\nConfidence:")
        print("  [1] High   — clearly visible, certain")
        print("  [2] Medium — likely correct")
        print("  [3] Low    — best guess, poor visibility")

        while True:
            conf_choice = input("Enter confidence (1-3): ").strip()
            if conf_choice in CONFIDENCE:
                break
            print("Invalid. Enter 1, 2, or 3.")
        confidence = CONFIDENCE[conf_choice]

        # Notes
        notes = input("Notes (press Enter to skip): ").strip()

        # Copy to dataset
        os.makedirs(os.path.join(DATASET_DIR, "images", cls_name), exist_ok=True)
        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_name = f"field_{ts}_{photo_path.stem}_{cls_name}{photo_path.suffix.lower()}"
        dest_path = os.path.join(DATASET_DIR, "images", cls_name, dest_name)
        shutil.copy2(photo_path, dest_path)

        manifest["images"].append({
            "filename":    dest_name,
            "label":       cls_name,
            "class_path":  f"images/{cls_name}/{dest_name}",
            "confidence":  confidence,
            "source_path": str(photo_path),
            "labeled_by":  inspector_name,
            "notes":       notes,
            "source":      "field_partner",
            "added_at":    datetime.now().isoformat(),
        })

        print(f"✓ Labeled as {cls_name} ({confidence} confidence)")
        labeled += 1

        # Save after each label so nothing is lost
        if labeled % 10 == 0:
            save_manifest(manifest)
            print(f"  [Auto-saved at {labeled} labels]")

    save_manifest(manifest)

    # Print session summary
    session_counts = {}
    for img in manifest["images"][-labeled:]:
        cls = img["label"]
        session_counts[cls] = session_counts.get(cls, 0) + 1

    print(f"\n{'='*50}")
    print(f"Session complete — {labeled} photos labeled")
    for cls, count in session_counts.items():
        print(f"  {cls}: {count}")

    # Print total dataset stats
    all_counts = {}
    for img in manifest["images"]:
        cls = img["label"]
        all_counts[cls] = all_counts.get(cls, 0) + 1

    total = sum(all_counts.values())
    print(f"\nTotal dataset: {total} labeled images")
    for cls in ["LEAD", "NON_LEAD", "GRR", "UNKNOWN"]:
        count = all_counts.get(cls, 0)
        needed = max(0, 200 - count)
        print(f"  {cls:<10}: {count:>4}  {'✅' if count >= 200 else f'(need {needed} more)'}")

    if total >= 500:
        print("\n✅ Ready for full model training!")
        print("   Run: python3 train_model.py --mode full")
    elif total >= 100:
        print("\n⚡ Enough for pilot model.")
        print("   Run: python3 train_model.py --mode pilot")
    else:
        print(f"\n⚠ Need {500-total} more labeled images for training.")

    return labeled


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PIPE_VISION_AI Labeling Tool")
    parser.add_argument("--folder",    required=True, help="Folder of pipe photos to label")
    parser.add_argument("--inspector", default="",    help="Inspector name/badge")
    args = parser.parse_args()

    if not args.inspector:
        args.inspector = input("Inspector name or badge number: ").strip()

    manifest = load_manifest()
    label_folder(args.folder, args.inspector, manifest)