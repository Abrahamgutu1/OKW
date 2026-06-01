"""
PIPE_VISION_AI — Step 2: Model Training Pipeline
Fine-tunes ResNet-50 on labeled pipe photos using transfer learning.
Outputs a trained model ready to deploy in FastAPI.

Run:
  python3 train_model.py --mode pilot   (< 500 images)
  python3 train_model.py --mode full    (500+ images)

Requirements:
  pip3 install torch torchvision pillow scikit-learn matplotlib --user
"""

import os
import json
import argparse
import time
from pathlib import Path
from datetime import datetime

# ── Config ─────────────────────────────────────────────────────────────────────
DATASET_DIR  = os.path.expanduser("~/Desktop/OKW FieldSync/PipeVisionDataset")
MODELS_DIR   = os.path.expanduser("~/Desktop/OKW FieldSync/PipeVisionModels")
MANIFEST_PATH = os.path.join(DATASET_DIR, "manifest.json")

CLASSES      = ["LEAD", "NON_LEAD", "GRR", "UNKNOWN"]
CLASS_TO_IDX = {c: i for i, c in enumerate(CLASSES)}
IDX_TO_CLASS = {i: c for i, c in enumerate(CLASSES)}

IMG_SIZE     = 224   # ResNet-50 input size
BATCH_SIZE   = 16
EPOCHS_PILOT = 10
EPOCHS_FULL  = 25
LEARNING_RATE = 0.0001

def check_dependencies():
    try:
        import torch
        import torchvision
        from PIL import Image
        from sklearn.model_selection import train_test_split
        return True
    except ImportError as e:
        print(f"\n[ERROR] Missing dependency: {e}")
        print("Install with:")
        print("  pip3 install torch torchvision pillow scikit-learn matplotlib --user")
        return False

def load_dataset(manifest_path):
    """Load image paths and labels from manifest."""
    with open(manifest_path) as f:
        manifest = json.load(f)

    images, labels = [], []
    for item in manifest["images"]:
        path = os.path.join(DATASET_DIR, item["class_path"])
        if os.path.exists(path) and item["label"] in CLASS_TO_IDX:
            images.append(path)
            labels.append(CLASS_TO_IDX[item["label"]])

    return images, labels

def train(mode="pilot"):
    if not check_dependencies():
        return

    import torch
    import torchvision
    import torchvision.transforms as transforms
    from torchvision import models
    from torch.utils.data import Dataset, DataLoader
    from PIL import Image
    from sklearn.model_selection import train_test_split
    import numpy as np

    print(f"\nPIPE_VISION_AI Training Pipeline")
    print(f"Mode: {mode.upper()}")
    print("=" * 50)

    # ── Load dataset ───────────────────────────────────────────────────────────
    if not os.path.exists(MANIFEST_PATH):
        print("[ERROR] No dataset found. Run collect_data.py first.")
        return

    images, labels = load_dataset(MANIFEST_PATH)
    total = len(images)
    print(f"Total labeled images: {total}")

    if total < 20:
        print("[ERROR] Need at least 20 labeled images to train.")
        print("Run collect_data.py and add more labeled photos.")
        return

    # Print class distribution
    for cls_idx, cls_name in IDX_TO_CLASS.items():
        count = labels.count(cls_idx)
        print(f"  {cls_name}: {count} images")

    # ── Train/val/test split ───────────────────────────────────────────────────
    train_imgs, test_imgs, train_lbls, test_lbls = train_test_split(
        images, labels, test_size=0.15, random_state=42, stratify=labels
    )
    train_imgs, val_imgs, train_lbls, val_lbls = train_test_split(
        train_imgs, train_lbls, test_size=0.15, random_state=42, stratify=train_lbls
    )

    print(f"\nSplit: {len(train_imgs)} train / {len(val_imgs)} val / {len(test_imgs)} test")

    # ── Data transforms ────────────────────────────────────────────────────────
    train_transform = transforms.Compose([
        transforms.Resize((IMG_SIZE + 32, IMG_SIZE + 32)),
        transforms.RandomCrop(IMG_SIZE),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225]),
    ])

    val_transform = transforms.Compose([
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406],
                             [0.229, 0.224, 0.225]),
    ])

    # ── Dataset class ──────────────────────────────────────────────────────────
    class PipeDataset(Dataset):
        def __init__(self, paths, labels, transform):
            self.paths     = paths
            self.labels    = labels
            self.transform = transform

        def __len__(self): return len(self.paths)

        def __getitem__(self, idx):
            try:
                img = Image.open(self.paths[idx]).convert("RGB")
                return self.transform(img), self.labels[idx]
            except Exception:
                # Return black image if file is corrupted
                img = Image.new("RGB", (IMG_SIZE, IMG_SIZE), (0, 0, 0))
                return self.transform(img), self.labels[idx]

    train_ds = PipeDataset(train_imgs, train_lbls, train_transform)
    val_ds   = PipeDataset(val_imgs,   val_lbls,   val_transform)
    test_ds  = PipeDataset(test_imgs,  test_lbls,  val_transform)

    train_loader = DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True,  num_workers=0)
    val_loader   = DataLoader(val_ds,   batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    test_loader  = DataLoader(test_ds,  batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    # ── Model — ResNet-50 with transfer learning ───────────────────────────────
    print("\nLoading ResNet-50 pretrained on ImageNet…")
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)

    # Freeze all layers except the final block and classifier
    for name, param in model.named_parameters():
        if "layer4" not in name and "fc" not in name:
            param.requires_grad = False

    # Replace final layer for 4-class output
    in_features = model.fc.in_features
    model.fc = torch.nn.Sequential(
        torch.nn.Dropout(0.3),
        torch.nn.Linear(in_features, 256),
        torch.nn.ReLU(),
        torch.nn.Dropout(0.2),
        torch.nn.Linear(256, len(CLASSES))
    )

    device = torch.device("mps" if torch.backends.mps.is_available()
                          else "cuda" if torch.cuda.is_available()
                          else "cpu")
    print(f"Training device: {device}")
    model = model.to(device)

    # ── Training setup ─────────────────────────────────────────────────────────
    # Use class weights to handle imbalanced dataset
    class_counts = [labels.count(i) for i in range(len(CLASSES))]
    total_samples = sum(class_counts)
    weights = torch.tensor(
        [total_samples / (len(CLASSES) * max(c, 1)) for c in class_counts],
        dtype=torch.float32
    ).to(device)

    criterion = torch.nn.CrossEntropyLoss(weight=weights)
    optimizer = torch.optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=LEARNING_RATE, weight_decay=0.01
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=EPOCHS_FULL
    )

    epochs    = EPOCHS_PILOT if mode == "pilot" else EPOCHS_FULL
    best_val  = 0.0
    best_path = None
    history   = {"train_loss": [], "val_acc": [], "val_loss": []}

    os.makedirs(MODELS_DIR, exist_ok=True)

    print(f"\nTraining for {epochs} epochs…\n")

    # ── Training loop ──────────────────────────────────────────────────────────
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        t0 = time.time()

        for batch_imgs, batch_labels in train_loader:
            batch_imgs   = batch_imgs.to(device)
            batch_labels = torch.tensor(batch_labels).to(device)

            optimizer.zero_grad()
            outputs = model(batch_imgs)
            loss    = criterion(outputs, batch_labels)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            total_loss += loss.item()

        scheduler.step()

        # Validation
        model.eval()
        val_correct = 0
        val_total   = 0
        val_loss    = 0

        with torch.no_grad():
            for batch_imgs, batch_labels in val_loader:
                batch_imgs   = batch_imgs.to(device)
                batch_labels = torch.tensor(batch_labels).to(device)
                outputs      = model(batch_imgs)
                val_loss    += criterion(outputs, batch_labels).item()
                _, predicted = outputs.max(1)
                val_total   += batch_labels.size(0)
                val_correct += predicted.eq(batch_labels).sum().item()

        val_acc = val_correct / max(val_total, 1)
        elapsed = time.time() - t0

        history["train_loss"].append(total_loss / max(len(train_loader), 1))
        history["val_acc"].append(val_acc)
        history["val_loss"].append(val_loss / max(len(val_loader), 1))

        print(f"Epoch {epoch+1:3d}/{epochs}  "
              f"loss: {total_loss/len(train_loader):.4f}  "
              f"val_acc: {val_acc:.3f}  "
              f"({elapsed:.1f}s)")

        # Save best model
        if val_acc > best_val:
            best_val  = val_acc
            ts        = datetime.now().strftime("%Y%m%d_%H%M")
            best_path = os.path.join(MODELS_DIR, f"pipe_vision_{ts}_acc{val_acc:.3f}.pt")
            torch.save({
                "epoch":      epoch,
                "model_state": model.state_dict(),
                "val_acc":    val_acc,
                "classes":    CLASSES,
                "img_size":   IMG_SIZE,
            }, best_path)
            print(f"  ✅ Saved best model: {os.path.basename(best_path)}")

    # ── Test set evaluation ────────────────────────────────────────────────────
    print("\n" + "="*50)
    print("Test Set Evaluation")
    print("="*50)

    model.eval()
    all_preds, all_labels = [], []

    with torch.no_grad():
        for batch_imgs, batch_labels in test_loader:
            batch_imgs = batch_imgs.to(device)
            outputs    = model(batch_imgs)
            _, preds   = outputs.max(1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(batch_labels)

    # Per-class accuracy
    for cls_idx, cls_name in IDX_TO_CLASS.items():
        cls_mask    = [l == cls_idx for l in all_labels]
        cls_correct = sum(p == l for p, l in zip(all_preds, all_labels) if l == cls_idx)
        cls_total   = sum(cls_mask)
        if cls_total > 0:
            print(f"  {cls_name:<12} {cls_correct}/{cls_total} = {cls_correct/cls_total:.1%}")

    overall = sum(p == l for p, l in zip(all_preds, all_labels)) / max(len(all_labels), 1)
    print(f"\n  Overall accuracy: {overall:.1%}")
    print(f"  Best val accuracy: {best_val:.1%}")
    print(f"  Model saved: {best_path}")

    # Save training history
    history_path = os.path.join(MODELS_DIR, "training_history.json")
    with open(history_path, "w") as f:
        json.dump({"history": history, "best_val_acc": best_val,
                   "test_acc": overall, "model_path": best_path,
                   "trained_at": datetime.now().isoformat()}, f, indent=2)

    print(f"\nDone. Deploy with: python3 deploy_model.py --model {best_path}")
    return best_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["pilot", "full"], default="pilot")
    args = parser.parse_args()
    train(mode=args.mode)