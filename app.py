import io
import docx
import openpyxl
import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

st.set_page_config(page_title="Quick Quote Builder", layout="centered")

# Custom styling for large text and high accessibility
st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-size: 20px;
    }
    .stButton>button {
        width: 100%;
        height: 3em;
        font-size: 24px !important;
        background-color: #2e7d32;
        color: white;
        border-radius: 10px;
    }
    .stDownloadButton>button {
        width: 100%;
        height: 3.5em;
        font-size: 24px !important;
        background-color: #1976d2;
        color: white;
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🛠️ Machine Shop Quote Builder")
st.write("Fill in the fields below to create and download a quick job quote.")

st.divider()

# Step 1: Basic Info
st.header("1. Job Info")
job_name = st.text_input("Job / Part Name", value="Custom Part")
part_qty = st.number_input("Number of Parts Needed", min_value=1, value=1, step=1)

# Step 2: Material Costs
st.header("2. Raw Material")
material_cost = st.number_input(
    "Total Material Cost ($)", min_value=0.0, value=50.0, step=5.0
)

# Step 3: Labor Hours & Rate
st.header("3. Labor Hours & Rate")
hourly_rate = st.slider(
    "Hourly Labor Rate ($/hr)", min_value=40, max_value=200, value=120, step=5
)

st.write("**Hours Per Department:**")
col1, col2 = st.columns(2)
with col1:
    setup_hrs = st.number_input("Setup Hours", min_value=0.0, value=1.0, step=0.5)
    cnc_hrs = st.number_input(
        "CNC Machining Hours", min_value=0.0, value=2.0, step=0.5
    )
    fab_hrs = st.number_input(
        "Fabrication (Laser, Punch, Brake, Saw) Hours",
        min_value=0.0,
        value=0.0,
        step=0.5,
    )
    weld_hrs = st.number_input(
        "Weld Hours", min_value=0.0, value=0.0, step=0.5
    )
with col2:
    manual_hrs = st.number_input(
        "Manual / Finishing Hours", min_value=0.0, value=0.5, step=0.5
    )
    inspection_hrs = st.number_input(
        "Inspection / QC Hours", min_value=0.0, value=0.5, step=0.5
    )
    paint_hrs = st.number_input(
        "Paint Hours", min_value=0.0, value=0.0, step=0.5
    )

total_hours = (
    setup_hrs
    + cnc_hrs
    + fab_hrs
    + weld_hrs
    + manual_hrs
    + inspection_hrs
    + paint_hrs
)
labor_cost = total_hours * hourly_rate  # Calculated across all 7 departments

# Step 4: Additional Factors, Shipping & Extras
st.header("4. Lead Time, Shipping & Extras")
lead_time_days = st.slider(
    "Shop Lead Time (Production Days)", min_value=1, max_value=30, value=5
)
outside_services = st.number_input(
    "Outside Services ($) (Heat Treat, Anodize, etc.)",
    min_value=0.0,
    value=0.0,
    step=10.0,
)
markup_pct = st.slider(
    "Material & Services Markup (%)", min_value=0, max_value=60, value=20, step=5
)

st.subheader("Shipping Details")
col_ship1, col_ship2 = st.columns(2)
with col_ship1:
    shipping_cost = st.number_input(
        "Shipping Cost ($)", min_value=0.0, value=25.0, step=5.0
    )
with col_ship2:
    shipping_days = st.slider(
        "Shipping Transit Time (Days)", min_value=1, max_value=14, value=3
    )

total_delivery_days = lead_time_days + shipping_days

# Calculations
mats_and_services = material_cost + outside_services
mats_services_markup = mats_and_services * (markup_pct / 100.0)
mats_and_services_marked_up = mats_and_services + mats_services_markup

# Total Quote = (Material + Outside Services marked up) + Dynamic Labor Cost + Shipping Cost
total_quote = mats_and_services_marked_up + labor_cost + shipping_cost
per_unit_price = total_quote / part_qty

st.divider()

# Final Summary Display
st.header("📋 Quote Summary")
st.write(f"**Job:** {job_name} ({part_qty} units)")
st.write(
    f"**Total Labor Time:** {total_hours:.1f} Hours @ ${hourly_rate}/hr ="
    f" **${labor_cost:,.2f}**"
)
st.write(
    f"**Materials & Outside Services:** ${mats_and_services:,.2f}"
    f" (+{markup_pct}% Markup = **${mats_and_services_marked_up:,.2f}**)"
)
st.write(f"**Shipping Cost:** **${shipping_cost:,.2f}**")
st.write(
    f"**Estimated Timeline:** {lead_time_days} days production +"
    f" {shipping_days} days shipping = **{total_delivery_days} total business days**"
)

st.subheader(f"Total Quote: **${total_quote:,.2f}**")
st.caption(f"(${per_unit_price:,.2f} per part)")

# Prepare downloadable file data structure
quote_data = [
    ("Job Name", job_name),
    ("Quantity", part_qty),
    ("Material Cost ($)", f"{material_cost:.2f}"),
    ("Outside Services ($)", f"{outside_services:.2f}"),
    ("Material & Services Markup (%)", f"{markup_pct}%"),
    (
        "Materials & Services Total (w/ Markup) ($)",
        f"{mats_and_services_marked_up:.2f}",
    ),
    ("Hourly Labor Rate ($/hr)", f"{hourly_rate:.2f}"),
    ("Setup Hours", f"{setup_hrs:.1f}"),
    ("CNC Hours", f"{cnc_hrs:.1f}"),
    ("Fabrication Hours (Laser/Punch/Brake/Saw)", f"{fab_hrs:.1f}"),
    ("Weld Hours", f"{weld_hrs:.1f}"),
    ("Manual Hours", f"{manual_hrs:.1f}"),
    ("Paint Hours", f"{paint_hrs:.1f}"),
    ("Inspection Hours", f"{inspection_hrs:.1f}"),
    ("Total Labor Hours", f"{total_hours:.1f}"),
    ("Total Labor Cost ($)", f"{labor_cost:.2f}"),
    ("Shipping Cost ($)", f"{shipping_cost:.2f}"),
    ("Shop Lead Time (Days)", lead_time_days),
    ("Shipping Transit Time (Days)", shipping_days),
    ("Total Estimated Delivery (Days)", total_delivery_days),
    ("Price Per Unit ($)", f"{per_unit_price:.2f}"),
    ("TOTAL QUOTE ($)", f"{total_quote:.2f}"),
]

st.divider()

# Select File Format
st.header("💾 Download Quote")
file_format = st.radio(
    "Select File Format:",
    options=["PDF (.pdf)", "Excel (.xlsx)", "Word Document (.docx)", "CSV (.csv)"],
    horizontal=True,
)

safe_job_name = job_name.replace(" ", "_")

if file_format == "PDF (.pdf)":
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Heading1"],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#1B365D"),
        alignment=0,
        spaceAfter=15,
    )

    cell_style = ParagraphStyle(
        "CellStyle",
        parent=styles["Normal"],
        fontSize=10,
        leading=13,
    )

    header_cell_style = ParagraphStyle(
        "HeaderCellStyle",
        parent=styles["Normal"],
        fontSize=11,
        leading=14,
        textColor=colors.white,
        fontName="Helvetica-Bold",
    )

    story = []
    story.append(Paragraph(f"🛠️ Machine Shop Quote: {job_name}", title_style))
    story.append(Spacer(1, 10))

    table_data = [[
        Paragraph("Field", header_cell_style),
        Paragraph("Value", header_cell_style),
    ]]

    for field, val in quote_data:
        table_data.append([
            Paragraph(str(field), cell_style),
            Paragraph(str(val), cell_style),
        ])

    pdf_table = Table(table_data, colWidths=[320, 220])
    pdf_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
    ]))

    story.append(pdf_table)
    doc.build(story)
    pdf_data = pdf_buffer.getvalue()

    st.download_button(
        label="📥 Download PDF Document (.pdf)",
        data=pdf_data,
        file_name=f"Quote_{safe_job_name}.pdf",
        mime="application/pdf",
    )

elif file_format == "Excel (.xlsx)":
    df_quote = pd.DataFrame(quote_data, columns=["Field", "Value"])
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df_quote.to_excel(writer, index=False, sheet_name="Quote Summary")
    excel_data = excel_buffer.getvalue()

    st.download_button(
        label="📥 Download Excel File (.xlsx)",
        data=excel_data,
        file_name=f"Quote_{safe_job_name}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

elif file_format == "Word Document (.docx)":
    doc = docx.Document()
    doc.add_heading(f"Machine Shop Quote: {job_name}", level=1)

    table = doc.add_table(rows=1, cols=2)
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = "Field"
    hdr_cells[1].text = "Value"

    for field, val in quote_data:
        row_cells = table.add_row().cells
        row_cells[0].text = str(field)
        row_cells[1].text = str(val)

    doc_buffer = io.BytesIO()
    doc.save(doc_buffer)
    doc_data = doc_buffer.getvalue()

    st.download_button(
        label="📥 Download Word File (.docx)",
        data=doc_data,
        file_name=f"Quote_{safe_job_name}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

else:  # CSV (.csv)
    df_quote = pd.DataFrame(quote_data, columns=["Field", "Value"])
    csv_buffer = df_quote.to_csv(index=False)

    st.download_button(
        label="📥 Download CSV File (.csv)",
        data=csv_buffer,
        file_name=f"Quote_{safe_job_name}.csv",
        mime="text/csv",
    )
