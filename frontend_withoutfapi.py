import streamlit as st
from PIL import Image
import io
import logging

from app.detector import PPEDetector
from app.alert import alert_system
from app.config import MODEL_PATH, MAX_FILE_SIZE
ALLOWED_TYPES = ["jpg", "jpeg", "png"]

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="SafeGuard — PPE Detection",
    page_icon="🦺",
    layout="wide"
)

# ── Load model once using Streamlit cache ─────────────────────
# @st.cache_resource runs only ONCE even if user re-uploads
# This is the key — model loads in ~3 seconds, not on every image
@st.cache_resource
def load_detector():
    return PPEDetector(model_path=MODEL_PATH)

try:
    detector = load_detector()
    model_loaded = True
except FileNotFoundError as e:
    model_loaded = False
    st.error(f"Model not found: {e}")
    st.stop()

# ── Header ────────────────────────────────────────────────────
st.title("🦺 SafeGuard — PPE Compliance Detection")
st.caption(
    "Real-time helmet, vest, and mask violation detection "
    "for construction sites · Powered by YOLOv8n"
)

# ── Sidebar ───────────────────────────────────────────────────
with st.sidebar:
    st.header("About SafeGuard")
    st.write("""
    Detects PPE violations in construction site images
    using a fine-tuned YOLOv8n model.

    **Violations (red boxes):**
    - ❌ No Hardhat
    - ❌ No Safety Vest
    - ❌ No Mask

    **Compliant (green boxes):**
    - ✅ Hardhat
    - ✅ Safety Vest
    - ✅ Mask
    """)

    st.divider()
    st.caption(f"Model: YOLOv8n fine-tuned")
    st.caption(f"Status: {'✅ Loaded' if model_loaded else '❌ Not loaded'}")
    st.caption("Max upload: 10MB")

# ── Tabs ──────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📷 Detect PPE", "📊 Violation Log"])

# ════════════════════════════════════════════════════════════
# TAB 1 — DETECTION
# ════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Upload a Construction Site Image")
    st.caption(f"Supported formats: {', '.join(ALLOWED_TYPES)} · Max 10MB")

    uploaded_file = st.file_uploader(
        "Choose an image",
        type=ALLOWED_TYPES
    )

    if uploaded_file is not None:

        # Validate size
        if uploaded_file.size > MAX_FILE_SIZE:
            st.error("File too large. Please upload an image under 10MB.")
            st.stop()

        # Load image
        image = Image.open(uploaded_file).convert("RGB")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Original Image**")
            st.image(image, use_column_width=True)

        # Run detection
        with st.spinner("Running PPE detection..."):
            try:
                buf = io.BytesIO()
                image.save(buf, format="JPEG")
                image_bytes = buf.getvalue()

                annotated_bytes, summary = detector.detect_image(image_bytes)
                alert = alert_system.check_and_log(summary, source="upload")
            except Exception as e:
                st.error(f"Detection failed: {str(e)}")
                st.stop()

        with col2:
            st.write("**Detection Result**")
            st.image(annotated_bytes, use_column_width=True)

        st.divider()

        # Status banner
        if summary["safety_status"] == "VIOLATION":
            st.error(
                f"⚠️ SAFETY VIOLATION — "
                f"{summary['total_violations']} violation(s) detected"
            )
        else:
            st.success("✅ SAFE — No PPE violations detected")

        # Metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Detections", summary["total_detections"])
        m2.metric("Persons Detected", summary["total_persons"])
        m3.metric("Violations", summary["total_violations"])
        m4.metric("Status", summary["safety_status"])

        # Violation breakdown
        if summary["total_violations"] > 0:
            st.subheader("Violation Breakdown")
            v = summary["violations"]
            vc1, vc2, vc3 = st.columns(3)
            vc1.metric("No Hardhat", v.get("NO-Hardhat", 0))
            vc2.metric("No Safety Vest", v.get("NO-Safety Vest", 0))
            vc3.metric("No Mask", v.get("NO-Mask", 0))

        # Alert info
        if alert:
            st.warning(
                f"🚨 Alert {alert['alert_id']} logged | "
                f"Severity: {alert['severity']}"
            )

        # All detections table
        with st.expander("All Detections Detail"):
            if summary["all_detections"]:
                st.dataframe(
                    summary["all_detections"],
                    use_container_width=True
                )
            else:
                st.write("No objects detected in this image.")

# ════════════════════════════════════════════════════════════
# TAB 2 — VIOLATION LOG
# ════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Violation Log & Statistics")

    if st.button("🔄 Refresh"):
        st.rerun()

    # Statistics
    stats = alert_system.get_statistics()

    st.subheader("Overall Statistics")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Total Alerts", stats["total_alerts"])
    s2.metric("No Hardhat", stats["no_hardhat"])
    s3.metric("No Vest", stats["no_vest"])
    s4.metric("No Mask", stats["no_mask"])

    if stats["total_alerts"] > 0:
        st.info(f"Most common violation: **{stats['most_common']}**")

    st.divider()
    st.subheader("Recent Violations")

    log = alert_system.get_violation_log(limit=20)

    if not log:
        st.info("No violations yet. Upload an image to start.")
    else:
        for v in log:
            severity_icon = {
                "CRITICAL": "🔴",
                "HIGH":     "🟠",
                "MEDIUM":   "🟡"
            }.get(v.get("severity", ""), "⚪")

            with st.expander(
                f"{severity_icon} {v['alert_id']} | "
                f"{v['timestamp'][:19]} | "
                f"{v['total_violations']} violation(s)"
            ):
                c1, c2, c3 = st.columns(3)
                c1.metric("No Hardhat",
                          v["violations"].get("NO-Hardhat", 0))
                c2.metric("No Vest",
                          v["violations"].get("NO-Safety Vest", 0))
                c3.metric("No Mask",
                          v["violations"].get("NO-Mask", 0))
                st.caption(
                    f"Severity: {v['severity']} | "
                    f"Source: {v['source']}"
                )