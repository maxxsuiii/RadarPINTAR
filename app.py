import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF
import tempfile
import os

st.set_page_config(page_title="RadarPINTAR Explorer", layout="wide")


def create_radar_chart(name, stats, categories):
    """Helper function to generate a Plotly radar figure."""
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=list(stats) + [stats[0]],
        theta=categories + [categories[0]],
        fill='toself',
        name=name
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),  # Adjust range as needed
        title=f"Performance: {name}"
    )
    return fig


st.title("🎓 RadarPINTAR: Student Analytics")

uploaded_file = st.file_uploader("Upload Student Excel", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    categories = df.columns[1:].tolist()

    st.sidebar.header("Report Settings")
    if st.sidebar.button("🔨 Generate Full PDF Report"):
        with st.spinner("Preparing PDF... this may take a moment."):
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)

            # Create a temporary directory for chart images
            with tempfile.TemporaryDirectory() as tmpdir:
                for index, row in df.iterrows():
                    name = row['Name']
                    stats = row[1:].values

                    # 1. Create Chart
                    fig = create_radar_chart(name, stats, categories)

                    # 2. Save Chart as Image
                    img_path = os.path.join(tmpdir, f"{name}.png")
                    fig.write_image(img_path, engine="kaleido")

                    # 3. Add to PDF
                    pdf.add_page()
                    pdf.set_font("Arial", 'B', 16)
                    pdf.cell(0, 10, f"Student Report: {name}", ln=True, align='C')
                    pdf.image(img_path, x=10, y=30, w=190)

                # Output PDF to bytes
                pdf_output = pdf.output(dest='S').encode('latin-1')

                st.sidebar.success("✅ Report Ready!")
                st.sidebar.download_button(
                    label="📥 Download Full PDF",
                    data=pdf_output,
                    file_name="Full_Student_Report.pdf",
                    mime="application/pdf"
                )

    # Display the interactive table for quick viewing
    st.subheader("Data Preview")
    st.dataframe(df, use_container_width=True)
