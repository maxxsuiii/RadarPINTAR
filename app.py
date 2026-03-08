"""
Student Performance Radar (Spider Web) Chart App
=================================================
Reads an Excel file matching the Perintis Pintar format:
  Columns A–F  → Student identity info displayed on each chart
  Columns I–P  → Subject/skill scores used as radar chart axes
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from io import BytesIO

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Student Analytics Portal", layout="wide")
st.title("🎓 Student Performance Radar")
st.write("Upload your Excel file to generate interactive spider web charts.")

# ── Column definitions (0-indexed) ───────────────────────────────────────────
# Identity columns A–F (indices 0–5) shown as student info
IDENTITY_COLS = {
    "Sekolah":        0,   # A – School name
    "Email":          1,   # B – Student email
    "Score":          2,   # C – Total/composite score
    "Nama Pelajar":   3,   # D – Full name
    "Kad Pengenalan": 4,   # E – IC number
    "Kelas":          5,   # F – Class
}

# Mark columns I–P (indices 8–15) used as radar axes
MARK_COL_START = 8   # Column I
MARK_COL_END   = 16  # Up to but not including index 16 (column P inclusive)

# ── Sidebar: file upload ──────────────────────────────────────────────────────
uploaded_file = st.sidebar.file_uploader("Upload Student Excel (XLSX)", type=["xlsx"])

if uploaded_file:

    # ── Load data ─────────────────────────────────────────────────────────────
    df = pd.read_excel(uploaded_file, header=0)

    # Basic column-count guard: need at least 16 columns (A=0 … P=15)
    if df.shape[1] < 16:
        st.error(
            f"Expected at least 16 columns (A–P) but found {df.shape[1]}. "
            "Please check your Excel file."
        )
        st.stop()

    # ── Derive name column and mark columns ───────────────────────────────────
    name_col   = df.columns[IDENTITY_COLS["Nama Pelajar"]]   # Column D
    mark_cols  = df.columns[MARK_COL_START:MARK_COL_END]     # Columns I–P

    # Friendly short labels for identity fields shown on the chart
    identity_labels = {
        df.columns[IDENTITY_COLS["Sekolah"]]:        "School",
        df.columns[IDENTITY_COLS["Email"]]:          "Email",
        df.columns[IDENTITY_COLS["Score"]]:          "Total Score",
        df.columns[IDENTITY_COLS["Nama Pelajar"]]:   "Name",
        df.columns[IDENTITY_COLS["Kad Pengenalan"]]: "IC Number",
        df.columns[IDENTITY_COLS["Kelas"]]:          "Class",
    }

    # ── Radar axis range: 0 → max mark value across whole dataset ─────────────
    max_mark = df[mark_cols].max(numeric_only=True).max()
    radar_max = max_mark * 1.1  # 10 % headroom so values don't touch the edge

    # ── Individual Student View ───────────────────────────────────────────────
    st.subheader("Individual Student Analysis")

    # Dropdown: list unique student names
    student_names = df[name_col].dropna().unique().tolist()
    selected_name = st.selectbox("Select a Student", student_names)

    # Retrieve the selected student's row (first match)
    student_row = df[df[name_col] == selected_name].iloc[0]

    # ── Build radar chart ─────────────────────────────────────────────────────
    # Plotly requires the polygon to be closed: repeat first value/category
    categories   = mark_cols.tolist()
    values       = student_row[mark_cols].tolist()
    plot_cats    = categories + [categories[0]]
    plot_values  = values + [values[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=plot_values,
        theta=plot_cats,
        fill="toself",
        name=selected_name,
        line_color="#1f77b4",
        fillcolor="rgba(31,119,180,0.2)",   # translucent fill
        hovertemplate="<b>%{theta}</b><br>Score: %{r}<extra></extra>",
    ))

    fig.update_layout(
        title=dict(
            text=f"Performance Radar — {selected_name}",
            font=dict(size=18),
            x=0.5,
            xanchor="center",
        ),
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, radar_max],
                tickfont=dict(size=10),
            )
        ),
        showlegend=False,
        margin=dict(b=40),
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── Student info card: 3 columns × 2 rows so nothing overlaps ────────────
    # Split 6 identity fields into two rows of 3
    id_items = [
        (identity_labels[col], student_row[col])
        for col in identity_labels
    ]
    st.markdown(
        """
        <style>
        .info-card {
            background: #f0f4fa;
            border-radius: 10px;
            padding: 14px 20px;
            margin-bottom: 12px;
        }
        .info-label { font-size: 12px; color: #555; margin-bottom: 2px; }
        .info-value { font-size: 15px; font-weight: 600; color: #1a1a2e; word-break: break-word; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Render two rows of three metric-style boxes
    for row_items in [id_items[:3], id_items[3:]]:
        cols = st.columns(3)
        for col_ui, (label, value) in zip(cols, row_items):
            col_ui.markdown(
                f"""
                <div class="info-card">
                    <div class="info-label">{label}</div>
                    <div class="info-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Optional: show the raw mark scores as a small table ──────────────────
    with st.expander("📊 View raw scores for this student"):
        score_df = pd.DataFrame({
            "Subject / Skill": categories,
            "Score": values,
        })
        st.dataframe(score_df, use_container_width=True, hide_index=True)

    # ── Download section ──────────────────────────────────────────────────────
    st.divider()
    st.subheader("Reports & Exports")

    col1, col2 = st.columns(2)

    with col1:
        # Export the current student's interactive chart as a self-contained HTML file
        html_buffer = BytesIO()
        fig.write_html(html_buffer)
        st.download_button(
            label=f"⬇️ Download {selected_name}'s Interactive Chart (HTML)",
            data=html_buffer.getvalue(),
            file_name=f"{selected_name}_radar.html",
            mime="text/html",
        )

    with col2:
        # Export the full dataset (all students, all columns) as CSV
        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download Full Student Data (CSV)",
            data=csv_data,
            file_name="full_student_report.csv",
            mime="text/csv",
        )

    # ── Class-wide comparison (bonus view) ───────────────────────────────────
    st.divider()
    st.subheader("📈 Class-Wide Average Comparison")

    # Compute per-subject averages across all students
    avg_values      = df[mark_cols].mean().tolist()
    avg_plot_vals   = avg_values + [avg_values[0]]
    student_plot    = plot_values   # already closed from individual chart above

    fig_class = go.Figure()

    # Trace 1: class average
    fig_class.add_trace(go.Scatterpolar(
        r=avg_plot_vals,
        theta=plot_cats,
        fill="toself",
        name="Class Average",
        line_color="#ff7f0e",
        fillcolor="rgba(255,127,14,0.15)",
    ))

    # Trace 2: selected student overlay
    fig_class.add_trace(go.Scatterpolar(
        r=student_plot,
        theta=plot_cats,
        fill="toself",
        name=selected_name,
        line_color="#1f77b4",
        fillcolor="rgba(31,119,180,0.2)",
    ))

    fig_class.update_layout(
        title=dict(
            text=f"Class Average vs {selected_name}",
            font=dict(size=16),
            x=0.5,
            xanchor="center",
        ),
        polar=dict(radialaxis=dict(visible=True, range=[0, radar_max])),
        showlegend=True,
    )

    st.plotly_chart(fig_class, use_container_width=True)

else:
    # Shown when no file has been uploaded yet
    st.info(
        "💡 Please upload your Excel file to begin.\n\n"
        "**Expected format:**\n"
        "- Columns A–F: Student identity info (school, email, score, name, IC, class)\n"
        "- Columns I–P: Subject/skill marks used as spider web axes"
    )