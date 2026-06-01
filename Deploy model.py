"""
PIPE_VISION_AI — Step 3: Model Deployment
Loads trained ResNet-50 and adds classification endpoint to FastAPI.
Replaces the placeholder cosine distance with real model predictions.

Usage:
  python3 deploy_model.py --model ~/Desktop/OKW\ FieldSync/PipeVisionModels/pipe_vision_XXXX.pt

Then update backend/main.py to use the new /api/classify_pipe endpoint.
"""

import os
import sys
import json
import base64
import argparse
import io
from pathlib import Path

# ── Inference Engine ───────────────────────────────────────────────────────────
class PipeVisionClassifier:
    """
    Wraps the trained ResNet-50 model for inference.
    Used by FastAPI to classify pipe photos in real-time.
    """

    CLASSES   = ["LEAD", "NON_LEAD", "GRR", "UNKNOWN"]
    IMG_SIZE  = 224

    def __init__(self, model_path):
        self.model_path = model_path
        self.model      = None
        self.device     = None
        self._load()

    def _load(self):
        try:
            import torch
            import torchvision.models as models
            import torchvision.transforms as transforms

            checkpoint = torch.load(self.model_path, map_location="cpu")

            self.device = torch.device(
                "mps"  if torch.backends.mps.is_available() else
                "cuda" if torch.cuda.is_available() else "cpu"
            )

            model = models.resnet50(weights=None)
            in_features = model.fc.in_features
            model.fc = torch.nn.Sequential(
                torch.nn.Dropout(0.3),
                torch.nn.Linear(in_features, 256),
                torch.nn.ReLU(),
                torch.nn.Dropout(0.2),
                torch.nn.Linear(256, len(self.CLASSES))
            )
            model.load_state_dict(checkpoint["model_state"])
            model.eval()
            model.to(self.device)
            self.model = model

            self.transform = transforms.Compose([
                transforms.Resize((self.IMG_SIZE, self.IMG_SIZE)),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406],
                                     [0.229, 0.224, 0.225]),
            ])

            val_acc = checkpoint.get("val_acc", 0)
            print(f"PIPE_VISION_AI loaded — val accuracy: {val_acc:.1%}")
            print(f"Device: {self.device}")

        except ImportError:
            print("[WARN] PyTorch not installed — running in stub mode.")
            self.model = None
        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")
            self.model = None

    def classify(self, image_base64):
        """
        Classify a pipe photo from Base64 string.
        Returns dict with class, confidence, probabilities, and recommendation.
        """
        if self.model is None:
            return self._stub_response()

        try:
            import torch
            from PIL import Image

            # Decode Base64 image
            clean = image_base64.strip()
            if "," in clean and clean.startswith("data:"):
                clean = clean.split(",", 1)[1]
            padding = len(clean) % 4
            if padding:
                clean += "=" * (4 - padding)
            img_bytes = base64.b64decode(clean)
            img = Image.open(io.BytesIO(img_bytes)).convert("RGB")

            # Run inference
            tensor = self.transform(img).unsqueeze(0).to(self.device)
            with torch.no_grad():
                logits = self.model(tensor)
                probs  = torch.softmax(logits, dim=1)[0]

            probs_list = probs.cpu().numpy().tolist()
            pred_idx   = int(probs.argmax())
            pred_class = self.CLASSES[pred_idx]
            confidence = float(probs[pred_idx])

            return {
                "material_class":   pred_class,
                "confidence":       round(confidence, 4),
                "probabilities":    {c: round(float(p), 4)
                                     for c, p in zip(self.CLASSES, probs_list)},
                "lead_probability": round(float(probs[0]), 4),
                "requires_inspection": confidence < 0.85 or pred_class in ["LEAD", "GRR", "UNKNOWN"],
                "priority_score":   self._priority_score(pred_class, confidence),
                "recommendation":   self._recommendation(pred_class, confidence),
                "model_version":    os.path.basename(self.model_path),
            }

        except Exception as e:
            return {"error": str(e), "material_class": "UNKNOWN",
                    "confidence": 0, "requires_inspection": True,
                    "lead_probability": 0, "priority_score": 50,
                    "recommendation": "Manual inspection required — classification failed."}

    def _priority_score(self, cls, confidence):
        """0-100 score — higher = inspect sooner."""
        base = {"LEAD": 90, "GRR": 75, "UNKNOWN": 60, "NON_LEAD": 20}[cls]
        # Low confidence bumps up priority regardless of class
        confidence_penalty = int((1 - confidence) * 30)
        return min(100, base + confidence_penalty)

    def _recommendation(self, cls, confidence):
        if cls == "LEAD" and confidence > 0.85:
            return "HIGH PRIORITY — Confirmed lead material. Schedule replacement immediately per ODEQ LCRI deadline."
        if cls == "LEAD":
            return "PRIORITY — Likely lead material. Field verification required before scheduling replacement."
        if cls == "GRR":
            return "ELEVATED — Galvanized pipe downstream of potential lead source. Inspector review needed."
        if cls == "UNKNOWN" or confidence < 0.7:
            return "REVIEW — Cannot determine material from photo. Field inspector visit required."
        return "LOW PRIORITY — Likely non-lead material. Standard reverification schedule."

    def _stub_response(self):
        """Returns when model not loaded — for testing without PyTorch."""
        return {
            "material_class":     "UNKNOWN",
            "confidence":         0.0,
            "probabilities":      {c: 0.25 for c in self.CLASSES},
            "lead_probability":   0.25,
            "requires_inspection": True,
            "priority_score":     50,
            "recommendation":     "Model not loaded — manual inspection required.",
            "model_version":      "stub",
        }


# ── FastAPI integration snippet ────────────────────────────────────────────────
FASTAPI_SNIPPET = '''
# ── Add this to backend/main.py ───────────────────────────────────────────────
# Place AFTER the existing imports

import sys
sys.path.append("{scripts_dir}")
from deploy_model import PipeVisionClassifier

# Load model at startup (replace with your actual model path)
MODEL_PATH = "{model_path}"
pipe_vision = PipeVisionClassifier(MODEL_PATH) if os.path.exists(MODEL_PATH) else None

class ClassifyRequest(BaseModel):
    photo_base64: str
    evidence_id:  int

@app.post("/api/classify_pipe")
def classify_pipe(body: ClassifyRequest):
    """
    Classify a pipe photo using PIPE_VISION_AI.
    Returns material class, confidence, and inspection priority.
    """
    if pipe_vision is None:
        raise HTTPException(status_code=503,
                            detail="PIPE_VISION_AI model not loaded.")
    result = pipe_vision.classify(body.photo_base64)

    # Optionally update Oracle with AI classification
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE EVIDENCE
            SET AI_MATERIAL_CLASS    = :1,
                AI_CONFIDENCE        = :2,
                AI_PRIORITY_SCORE    = :3,
                AI_REQUIRES_INSPECT  = :4
            WHERE EVIDENCE_ID = :5
        """, (
            result["material_class"],
            result["confidence"],
            result["priority_score"],
            1 if result["requires_inspection"] else 0,
            body.evidence_id
        ))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception:
        pass  # Classification still returns even if DB update fails

    return result


@app.get("/api/priority_list")
def get_priority_list():
    """
    Returns all service lines ranked by AI inspection priority.
    Highest priority (most likely lead) first.
    """
    try:
        conn   = get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT EVIDENCE_ID, SERVICE_LINE_ID,
                   GPS_LATITUDE, GPS_LONGITUDE,
                   NVL(USER_VERIFIED_STATUS, 'UNVERIFIED') AS STATUS,
                   NVL(AI_MATERIAL_CLASS, 'UNCLASSIFIED') AS AI_CLASS,
                   NVL(AI_PRIORITY_SCORE, 50) AS PRIORITY,
                   NVL(AI_CONFIDENCE, 0) AS CONFIDENCE
            FROM EVIDENCE
            WHERE USER_VERIFIED_STATUS IS NULL
               OR USER_VERIFIED_STATUS = 'UNVERIFIED'
            ORDER BY AI_PRIORITY_SCORE DESC NULLS LAST
        """)
        cols = [d[0].lower() for d in cursor.description]
        rows = [dict(zip(cols, row)) for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return {"priority_list": rows, "total": len(rows)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
'''


def print_integration_guide(model_path):
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    snippet = FASTAPI_SNIPPET.format(
        scripts_dir=scripts_dir,
        model_path=model_path
    )
    print("\n" + "="*60)
    print("PIPE_VISION_AI — FastAPI Integration")
    print("="*60)
    print(snippet)

    # Save snippet to file
    out_path = os.path.join(os.path.dirname(model_path), "fastapi_integration.py")
    with open(out_path, "w") as f:
        f.write(snippet)
    print(f"\nSnippet saved to: {out_path}")


def test_classifier(model_path, test_image_path=None):
    """Quick smoke test of the classifier."""
    print(f"\nTesting classifier: {model_path}")
    clf = PipeVisionClassifier(model_path)

    if test_image_path and os.path.exists(test_image_path):
        with open(test_image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        result = clf.classify(b64)
        print("\nClassification result:")
        print(json.dumps(result, indent=2))
    else:
        print("No test image provided — running stub test.")
        result = clf._stub_response()
        print(json.dumps(result, indent=2))

    return clf


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model",  required=True, help="Path to trained .pt model file")
    parser.add_argument("--test",   default=None,  help="Path to test image (optional)")
    parser.add_argument("--integrate", action="store_true",
                        help="Print FastAPI integration code")
    args = parser.parse_args()

    if not os.path.exists(args.model):
        print(f"[ERROR] Model not found: {args.model}")
        sys.exit(1)

    test_classifier(args.model, args.test)

    if args.integrate:
        print_integration_guide(args.model)