import streamlit as st
import requests
from PIL import Image
import io
import json
import time

# ── Page config ──────────────────────────────────────────────
st.set_page_config(
    page_title="SafeGuard — PPE Detection",
    page_icon="🦺",
    layout="wide"
)

API_URL = "http://localhost:8000"

# ── Header ───────────────────────────────────────────────────
st.title("🦺 SafeGuard — PPE Compliance Detection")
st.caption("Real-time helmet, vest, and mask violation detection for construction sites")

# ── Sidebar ──────────────────────────────────────────────────
with st.sidebar:
    st.header("About SafeGuard")
    st.write("""
    SafeGuard detects PPE violations in real time using YOLOv8.

    **Detects:**
    - ✅ Hardhat (compliant)
    - ✅ Safety Vest (compliant)
    - ✅ Mask (compliant)
    - ❌ NO-Hardhat (violation)
    - ❌ NO-Safety Vest (violation)
    - ❌ NO-Mask (violation)
    """)

    st.divider()

    # API health check
    try:
        health = requests.get(f"{API_URL}/health", timeout=3)
        if health.status_code == 200:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Error")
    except:
        st.error("❌ API Offline — start with: uvicorn app.main:app")

# ── Tabs ─────────────────────────────────────────────────────
tab1, tab2 = st.tabs(["📷 Image Detection", "📊 Violation Log"])

# ════════════════════════════════════════════════════════════
# TAB 1 — IMAGE DETECTION
# ════════════════════════════════════════════════════════════
with tab1:
    st.subheader("Upload an Image for PPE Analysis")

    uploaded_file = st.file_uploader(
        "Choose an image",
        type=["jpg", "jpeg", "png"],
        help="Upload a construction site image to detect PPE violations"
    )

    if uploaded_file is not None:
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Original Image**")
            original_image = Image.open(uploaded_file)
            st.image(original_image, use_column_width=True)

        # Send to API
        uploaded_file.seek(0)
        files = {"file": (uploaded_file.name,
                          uploaded_file.read(),
                          uploaded_file.type)}

        with st.spinner("Analysing image..."):
            try:
                # Get annotated image
                response = requests.post(
                    f"{API_URL}/detect/image",
                    files=files,
                    timeout=30
                )

                if response.status_code == 200:
                    # Show annotated image
                    with col2:
                        st.write("**Detection Result**")
                        annotated_image = Image.open(
                            io.BytesIO(response.content)
                        )
                        st.image(annotated_image, use_column_width=True)

                    # Get JSON summary separately
                    uploaded_file.seek(0)
                    json_response = requests.post(
                        f"{API_URL}/detect/image/json",
                        files={"file": (uploaded_file.name,
                                        uploaded_file.read(),
                                        uploaded_file.type)},
                        timeout=30
                    )

                    if json_response.status_code == 200:
                        data = json_response.json()
                        summary = data["summary"]
                        alert = data["alert"]

                        st.divider()

                        # Status banner
                        if summary["safety_status"] == "VIOLATION":
                            st.error(
                                f"⚠️ SAFETY VIOLATION DETECTED — "
                                f"{summary['total_violations']} violation(s) found"
                            )
                        else:
                            st.success("✅ No violations detected — Site is compliant")

                        # Metrics row
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("Total Detections",
                                  summary["total_detections"])
                        m2.metric("Persons Detected",
                                  summary["total_persons"])
                        m3.metric("Violations",
                                  summary["total_violations"],
                                  delta=None)
                        m4.metric("Status",
                                  summary["safety_status"])

                        # Violation breakdown
                        if summary["total_violations"] > 0:
                            st.subheader("Violation Breakdown")
                            v = summary["violations"]
                            vc1, vc2, vc3 = st.columns(3)
                            vc1.metric("No Hardhat",
                                       v.get("NO-Hardhat", 0))
                            vc2.metric("No Safety Vest",
                                       v.get("NO-Safety Vest", 0))
                            vc3.metric("No Mask",
                                       v.get("NO-Mask", 0))

                        # All detections table
                        with st.expander("All Detections Detail"):
                            detections = summary["all_detections"]
                            if detections:
                                st.dataframe(
                                    detections,
                                    use_container_width=True
                                )
                            else:
                                st.write("No objects detected")

                else:
                    st.error(f"API Error: {response.status_code}")

            except requests.exceptions.ConnectionError:
                st.error(
                    "Cannot connect to API. "
                    "Start it with: uvicorn app.main:app --reload"
                )
            except Exception as e:
                st.error(f"Error: {str(e)}")

# ════════════════════════════════════════════════════════════
# TAB 2 — VIOLATION LOG
# ════════════════════════════════════════════════════════════
with tab2:
    st.subheader("Violation Log & Statistics")

    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

    # Statistics
    try:
        stats_response = requests.get(
            f"{API_URL}/violations/stats", timeout=5
        )
        if stats_response.status_code == 200:
            stats = stats_response.json()

            st.subheader("Overall Statistics")
            s1, s2, s3, s4 = st.columns(4)
            s1.metric("Total Alerts", stats.get("total_alerts", 0))
            s2.metric("No Hardhat", stats.get("no_hardhat", 0))
            s3.metric("No Vest", stats.get("no_vest", 0))
            s4.metric("No Mask", stats.get("no_mask", 0))

            if stats.get("total_alerts", 0) > 0:
                st.info(
                    f"Most common violation: "
                    f"**{stats.get('most_common', 'N/A')}**"
                )

    except Exception as e:
        st.warning("Could not load statistics")

    st.divider()

    # Violation log
    st.subheader("Recent Violations")
    try:
        log_response = requests.get(
            f"{API_URL}/violations/log?limit=20", timeout=5
        )
        if log_response.status_code == 200:
            log_data = log_response.json()
            violations = log_data["violations"]

            if not violations:
                st.info("No violations logged yet. Upload an image to start.")
            else:
                for v in violations:
                    severity_color = {
                        "CRITICAL": "🔴",
                        "HIGH": "🟠",
                        "MEDIUM": "🟡",
                        "NONE": "🟢"
                    }.get(v.get("severity", "NONE"), "⚪")

                    with st.expander(
                        f"{severity_color} {v['alert_id']} — "
                        f"{v['timestamp'][:19]} — "
                        f"{v['total_violations']} violation(s)"
                    ):
                        c1, c2, c3 = st.columns(3)
                        c1.metric("No Hardhat",
                                  v["violations"].get("NO-Hardhat", 0))
                        c2.metric("No Vest",
                                  v["violations"].get("NO-Safety Vest", 0))
                        c3.metric("No Mask",
                                  v["violations"].get("NO-Mask", 0))
                        st.caption(f"Severity: {v.get('severity')} | Source: {v.get('source')}")

    except Exception as e:
        st.warning(f"Could not load violation log: {str(e)}")