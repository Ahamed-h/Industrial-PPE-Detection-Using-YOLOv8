# SafeGuard — Technical Decisions

## Why YOLOv8n over YOLOv8s/m/l?
YOLOv8 comes in 5 sizes: nano, small, medium, large, xlarge.
For this project, nano was chosen because:
- Deployment target is CPU (no GPU in production)
- YOLOv8n runs at ~45ms per frame on CPU vs ~180ms for YOLOv8s
- mAP50 difference is only ~3% between n and s
- Real-time usability matters more than marginal accuracy gain

## Why Ultralytics over raw PyTorch?
Ultralytics wraps all YOLO complexity into a clean API.
Training, evaluation, and inference are 5 lines of code.
This is what production teams actually use — not raw PyTorch YOLO implementations.

## Why this dataset?
Construction Site Safety dataset (Roboflow) has:
- 2801 images pre-labelled in YOLOv8 format
- 10 classes covering all major PPE scenarios
- Real construction site images (not synthetic)
- Zero custom labelling needed

## Why in-memory violation log instead of database?
For a portfolio project demonstrating CV skills, PostgreSQL adds
complexity without changing the core demonstration.
In production: PostgreSQL with TimescaleDB for time-series violation data.

## Why FastAPI over Flask?
- Auto-generated docs at /docs
- Native async support
- Pydantic validation built in
- Type hints throughout
- Industry standard for ML serving APIs