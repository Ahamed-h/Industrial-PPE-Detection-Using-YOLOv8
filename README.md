# 🦺 SafeGuard — Industrial PPE Detection

> Real-time PPE compliance detection for construction sites  
> using a fine-tuned YOLOv8n model — detects helmet, vest,  
> and mask violations instantly from any image.

🔴 **Live Demo:** [Add Streamlit Cloud URL here]  
📁 **Dataset:** [Construction Site Safety — Roboflow](https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety)

---

## The Problem

Construction site accidents are largely preventable.  
Manual PPE checks are slow, inconsistent, and impossible  
to scale across large sites. SafeGuard automates compliance  
monitoring — flag violations instantly, log them, and act.

---

## What It Detects

| Class | Status |
|-------|--------|
| Hardhat | ✅ Compliant |
| Safety Vest | ✅ Compliant |
| Mask | ✅ Compliant |
| NO-Hardhat | ❌ Violation |
| NO-Safety Vest | ❌ Violation |
| NO-Mask | ❌ Violation |
| Person | 🔵 Tracked |
| Safety Cone | 🔵 Tracked |

---

## Model Performance

Trained on [Construction Site Safety dataset](https://universe.roboflow.com/roboflow-universe-projects/construction-site-safety)  
— 2,801 images, 10 classes, YOLOv8 format.  
Evaluated on held-out test set (82 images).

| Metric | Score |
|--------|-------|
| mAP50 | **0.702** |
| mAP50-95 | **0.415** |
| Precision | **0.877** |
| Recall | **0.625** |
| Inference speed (CPU) | ~45ms/image |
| Model size | ~6MB |

**On precision vs recall tradeoff:**  
Precision (0.877) is intentionally higher than recall (0.625).  
A false alarm on a compliant worker is less costly than  
incorrectly flagging the system as safe. Recall can be  
improved with more epochs and augmentation.

---

## Architecture
User uploads image
↓
Streamlit UI (frontend_withoutfapi.py)
↓
core/detector.py — PPEDetector.run()
↓
YOLOv8n inference (models/best.pt)
↓
Annotated image + detection summary
↓
core/alert.py — AlertSystem.check_and_log()
↓
Violation logged + displayed in UI

---

## Features

- Upload any construction site image
- Colour-coded bounding boxes — red for violations, green for compliant
- Violation banner overlay on detected images
- Per-image detection summary with confidence scores
- Violation log with severity classification (Medium / High / Critical)
- Session statistics — total alerts, per-class counts, most common violation
- Input validation — file type check, 10MB size limit
- Graceful error handling — never crashes on bad input

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Model | YOLOv8n (Ultralytics) |
| Computer Vision | OpenCV |
| Frontend | Streamlit |
| Language | Python 3.11 |
| Training | Google Colab T4 GPU |
| Dataset | Roboflow Construction Site Safety |

---

## Run Locally

```bash
# Clone
git clone https://github.com/Ahamed-h/Industrial-PPE-Detection-Using-YOLOv8
cd Industrial-PPE-Detection-Using-YOLOv8

# Install
pip install -r requirements.txt

# Run
streamlit run streamlit_app.py
```

> Model (`best.pt`) is included in `model/` folder.  
> No additional setup required.

---

## Project Structure
safeguard/
├── app/
│   ├── detector.py      # YOLO inference + annotation logic
│   ├── alert.py         # Violation logging + severity classification
│   └── config.py        # Environment config
├── model/
│   └── best.pt          # Fine-tuned YOLOv8n weights
├── model_result/        # Training metrics and plots
├── streamlit_app.py     # Main Streamlit application
├── DECISIONS.md         # Technical decisions log
└── requirements.txt

---

## What Broke and How I Fixed It

**1. data.yaml paths breaking on Colab**  
Relative paths in data.yaml failed when Colab's working  
directory didn't match. Fixed by rewriting paths to absolute  
paths before training.

**2. Docker image downloading CUDA packages unnecessarily**  
Default torch installs GPU packages (2GB+) even on CPU-only  
deployment. Fixed by switching to `torch+cpu` with  
`--extra-index-url https://download.pytorch.org/whl/cpu`.

**3. Low recall on NO-Mask class**  
Masks are small objects and often partially occluded. Model  
struggled here. Partial fix: trained with `imgsz=640` instead  
of 416 to preserve small object detail. Full fix would require  
more labelled mask data.

---

## What I'd Improve With More Time

- **PostgreSQL** for persistent violation log across sessions
- **Real-time webcam stream** via WebSocket
- **DeepSORT tracking** to assign IDs to individual workers
- **More training epochs** (100+) to improve recall
- **Data augmentation** — mosaic, mixup to handle occlusion better
- **Email/SMS alerts** when violation threshold exceeded

---

## DECISIONS.md Summary

See [DECISIONS.md](./DECISIONS.md) for full reasoning.  
Key decisions: why YOLOv8n over larger variants,  
why Streamlit over FastAPI + React, why this dataset.
