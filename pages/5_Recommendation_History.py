"""
KROP - Recommendation History and Historical Comparison
Persistent audit trail of previously generated crop recommendations using SQLite.
"""

import pandas as pd
import plotly.express as px
import streamlit as st

from src.ui_components import esc, flash, get_plotly_theme, show_flash

db = st.session_state["db_manager"]

st.title("📜 Recommendation History & Analysis")
st.write(
    "Review previously generated agricultural advisory records stored persistently in the local SQLite database. "
    "Compare suitability trends and audit evidence-based decisions across seasons."
)

show_flash()
records = db.get_recommendation_history(limit=50)
total_records = db.count_recommendations()

if not records:
    st.info("No recommendation history found yet. Head over to **Crop Recommendations** to generate and save your first advisory.")
    if st.button("Generate Recommendations", type="primary"):
        st.switch_page("pages/3_Crop_Recommendations.py")
    st.stop()

st.metric(
    "Total Stored Advisory Records", total_records,
    delta=f"Showing latest {len(records)} | oldest shown: {records[-1]['created_at'][:10]}", delta_color="off",
)

st.markdown("<br>", unsafe_allow_html=True)

# Historical Comparison Visualization
st.markdown("### 📊 Cross-Advisory Crop Score Trends")

comparison_data = []
for r in records[:10]:
    date_label = r["created_at"][:16].replace("T", " ")
    loc_label = f"{r.get('district') or 'Farm'} ({date_label})"
    crops = r.get("recommended_crops", [])
    for c in crops[:3]:
        comparison_data.append({
            "Advisory": loc_label,
            "Crop": c.get("crop_name"),
            "Composite Score (%)": c.get("composite_score", 0),
            "Rank": f"#{c.get('rank', 1)}"
        })

if comparison_data:
    df_comp = pd.DataFrame(comparison_data)
    fig_comp = px.bar(
        df_comp,
        x="Advisory",
        y="Composite Score (%)",
        color="Crop",
        barmode="group",
        title="Top Recommended Crops & Scores Across Recent Advisory Sessions",
        color_discrete_sequence=["#2d6a4f", "#52b788", "#74c69d", "#95d5b2", "#d8f3dc", "#b7e4c7"]
    )
    fig_comp.update_layout(
        height=280,
        margin=dict(l=20, r=20, t=35, b=20),
        **get_plotly_theme()
    )
    fig_comp.update_xaxes(tickangle=-15)
    st.plotly_chart(fig_comp, width="stretch")

st.divider()

# Individual Record Cards with Delete & Expand
st.markdown("### 🗂️ Stored Advisory Records")

for rec in records:
    r_id = rec["id"]
    created = rec["created_at"][:19].replace("T", " ")
    dist = rec.get("district") or "Unlinked profile"
    state = rec.get("state") or ""
    village = rec.get("village") or ""
    area = rec.get("land_area") or "-"
    unit = rec.get("land_unit") or ""
    soil = rec.get("soil_type") or "Unknown"
    rec_crops = rec.get("recommended_crops", [])
    w_sum = rec.get("weather_summary", {})

    top_crop_names = [f"#{c.get('rank', 1)} {c.get('crop_name')} ({c.get('composite_score', 0)}%)" for c in rec_crops[:3]]

    with st.expander(f"📍 #{r_id} · {village} {dist}, {state} · {created} · {', '.join(top_crop_names)}", expanded=False):
        c_det1, c_det2 = st.columns([2, 1.2])

        with c_det1:
            st.markdown(f"**Field Parameters:** {area} {unit} | Soil: {soil} | Recorded at: {created}")
            st.markdown("##### Recommended Candidates:")
            for c in rec_crops:
                reasons = c.get("explanation_points") or ["Verified regional suitability"]
                st.markdown(
                    f"""
                    <div style="background: #ffffff; padding: 0.6rem 0.8rem; border-radius: 6px; border: 1px solid #e0e5e2; margin-bottom: 0.4rem; font-size: 0.88rem;">
                        <strong>#{esc(c.get('rank', 1))} {esc(c.get('crop_name'))}</strong> &mdash;
                        Suitability: <strong style="color: #2d6a4f;">{esc(c.get('composite_score'))}%</strong> |
                        Water: {esc(c.get('water_requirement', 'N/A'))} | Soil: {esc(c.get('suitable_soil', 'N/A'))} |
                        Duration: {esc(c.get('growing_duration', 'N/A'))}
                        <div style="margin-top: 0.3rem; color: #555b6e; font-size: 0.83rem;"><em>{esc(reasons[0])}</em></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with c_det2:
            st.markdown("##### Environmental Snapshot:")
            if w_sum:
                st.markdown(f"- **Temp:** {w_sum.get('temperature_c', 'N/A')}°C")
                st.markdown(f"- **Humidity:** {w_sum.get('humidity_pct', 'N/A')}%")
                st.markdown(f"- **Rainfall:** {w_sum.get('precipitation_mm', 0.0)} mm")
                st.markdown(f"- **Condition:** {w_sum.get('condition', 'Seasonal')}")
            else:
                st.markdown("_No live weather logged for this run._")

            st.markdown(f"- **ML Model Version:** {rec.get('model_version', 'n/a')}")

            # Delete Record Action with confirmation checkbox
            st.markdown("---")
            confirm_del = st.checkbox(f"Confirm deletion of Record #{r_id}", key=f"del_chk_{r_id}")
            if st.button(f"🗑️ Delete Record #{r_id}", key=f"btn_del_{r_id}", disabled=not confirm_del):
                db.delete_recommendation(r_id)
                flash(f"Record #{r_id} permanently deleted.")
                st.rerun()
