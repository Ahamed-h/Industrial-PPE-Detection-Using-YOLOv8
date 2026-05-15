from ultralytics import YOLO
import cv2
import numpy as np
from PIL import Image
import io
import os
from datetime import datetime
from app.config import MODEL_PATH
from app.logging_config import logger

# Class names from the dataset
CLASS_NAMES = [
    'Hardhat', 'Mask', 'NO-Hardhat', 'NO-Mask',
    'NO-Safety Vest', 'Person', 'Safety Cone',
    'Safety Vest', 'machinery', 'vehicle'
]

# Which classes are violations
VIOLATION_CLASSES = ['NO-Hardhat', 'NO-Mask', 'NO-Safety Vest']

# Which classes are compliant PPE
COMPLIANT_CLASSES = ['Hardhat', 'Mask', 'Safety Vest']

# Colors: violations = red, compliant = green, others = blue
CLASS_COLORS = {
    'NO-Hardhat':      (0, 0, 255),    # red (BGR)
    'NO-Mask':         (0, 0, 255),    # red
    'NO-Safety Vest':  (0, 0, 255),    # red
    'Hardhat':         (0, 255, 0),    # green
    'Mask':            (0, 255, 0),    # green
    'Safety Vest':     (0, 255, 0),    # green
    'Person':          (255, 165, 0),  # orange
    'Safety Cone':     (255, 255, 0),  # yellow
    'machinery':       (128, 0, 128),  # purple
    'vehicle':         (255, 165, 0),  # orange
}


class PPEDetector:

    def __init__(self, model_path: str = MODEL_PATH):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Model not found at {model_path}. "
                f"Download best.pt from Colab and place it in models/"
            )
        self.model = YOLO(model_path)
        self.model_path = model_path
        logger.info("Model loaded from %s", model_path)

    def detect_image(self, image_bytes: bytes):
        """
        Takes raw image bytes.
        Returns: annotated image bytes, detection summary dict
        """
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if frame is None:
            raise ValueError("Could not decode image")

        # Run inference
        results = self.model(frame, verbose=False)

        # Annotate frame
        annotated_frame = self._annotate_frame(frame, results[0])

        # Build summary
        summary = self._build_summary(results[0])

        # Convert annotated frame to bytes
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        annotated_bytes = buffer.tobytes()

        return annotated_bytes, summary

    def detect_frame(self, frame: np.ndarray):
        """
        Takes a numpy frame (from webcam).
        Returns: annotated frame, summary dict
        Fast path — no bytes conversion overhead.
        """
        results = self.model(frame, verbose=False)
        annotated_frame = self._annotate_frame(frame, results[0])
        summary = self._build_summary(results[0])
        return annotated_frame, summary

    def _annotate_frame(self, frame: np.ndarray, result) -> np.ndarray:
        """
        Draw bounding boxes and labels on frame.
        Red for violations, green for compliant.
        """
        annotated = frame.copy()

        if result.boxes is None or len(result.boxes) == 0:
            return annotated

        for box in result.boxes:
            # Get coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Get class info
            class_id = int(box.cls[0])
            class_name = CLASS_NAMES[class_id]
            confidence = float(box.conf[0])

            # Get color
            color = CLASS_COLORS.get(class_name, (255, 255, 255))

            # Draw bounding box
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

            # Draw label background
            label = f"{class_name} {confidence:.2f}"
            (label_w, label_h), _ = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            cv2.rectangle(
                annotated,
                (x1, y1 - label_h - 8),
                (x1 + label_w, y1),
                color, -1
            )

            # Draw label text
            cv2.putText(
                annotated, label,
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (255, 255, 255), 1
            )

        # Draw violation warning banner if any violations
        violations = self._count_violations(result)
        if sum(violations.values()) > 0:
            cv2.rectangle(annotated, (0, 0), (frame.shape[1], 40),
                         (0, 0, 200), -1)
            total = sum(violations.values())
            cv2.putText(
                annotated,
                f"⚠ SAFETY VIOLATION DETECTED — {total} violation(s)",
                (10, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (255, 255, 255), 2
            )

        return annotated

    def _count_violations(self, result) -> dict:
        """Count violations per class."""
        counts = {v: 0 for v in VIOLATION_CLASSES}

        if result.boxes is None:
            return counts

        for box in result.boxes:
            class_id = int(box.cls[0])
            class_name = CLASS_NAMES[class_id]
            if class_name in VIOLATION_CLASSES:
                counts[class_name] += 1

        return counts

    def _build_summary(self, result) -> dict:
        """Build detection summary dict."""
        all_detections = []
        violations = {v: 0 for v in VIOLATION_CLASSES}
        compliant = {c: 0 for c in COMPLIANT_CLASSES}
        total_persons = 0

        if result.boxes is not None:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = CLASS_NAMES[class_id]
                confidence = float(box.conf[0])

                all_detections.append({
                    "class": class_name,
                    "confidence": round(confidence, 3),
                    "is_violation": class_name in VIOLATION_CLASSES
                })

                if class_name in VIOLATION_CLASSES:
                    violations[class_name] += 1
                elif class_name in COMPLIANT_CLASSES:
                    compliant[class_name] += 1
                elif class_name == 'Person':
                    total_persons += 1

        total_violations = sum(violations.values())

        return {
            "timestamp": datetime.now().isoformat(),
            "total_detections": len(all_detections),
            "total_persons": total_persons,
            "violations": violations,
            "compliant": compliant,
            "total_violations": total_violations,
            "safety_status": "VIOLATION" if total_violations > 0 else "SAFE",
            "all_detections": all_detections
        }
    

#sanity check  
import pathlib, random, os

if __name__ == "__main__":
    root = pathlib.Path(__file__).resolve().parents[1]
    val_dir = root / "model/dataset/sample_images"

    img_name = random.choice([f for f in os.listdir(val_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))])
    test_image_path = val_dir / img_name

    detector = PPEDetector(model_path=MODEL_PATH)
    annotated_bytes, summary = detector.detect_image(test_image_path.read_bytes())

    out_path = root / f"debug_detector_output_{img_name}"
    out_path.write_bytes(annotated_bytes)

    logger.info("Input: %s\nSaved: %s\n%s", test_image_path, out_path, summary)
