import io
import docx
import openpyxl
import pandas as pd
import streamlit as st

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

# Step 3: Labor Hours per Department ($120/hr flat rate)
st.header("3. Labor Hours ($120/hr)")
hourly_rate = 120.0  # Shop hourly rate set to $120/hr

col1, col2 = st.columns(2)
with col1:
    setup_hrs = st.number_input("Setup Hours", min_value=0.0, value=1.0, step=0.5)
    cnc_hrs = st.number_input(
        "CNC Machining Hours", min_value=0.0, value=2.0, step=0.5
    )
with col2:
    manual_hrs = st.number_input(
        "Manual / Finishing Hours", min_value=0.0, value=0.5, step=0.5
    )
    inspection_hrs = st.number_input(
        "Inspection / QC Hours", min_value=0.0, value=0.5, step=0.5
    )

total_hours = setup_hrs + cnc_hrs + manual_hrs + inspection_hrs
labor_cost = total_hours * hourly_rate  # No markup applied to labor

# Step 4: Additional Factors
st.header("4. Lead Time & Extras")
lead_time_days = st.slider(
    "Estimated Lead Time (Days)", min_value=1, max_value=30, value=5
)
outside_services = st.number_input(
    "Outside Services ($) (Heat Treat, Anodize, etc.)",
    min_value=0.0,
    value=0.0,
    step=10.0,
)
markup_pct = st.slider(
    "Material & Services Markup (%)", min_value=0, max_value=50, value=20, step=5
)

# Calculations
mats_and_services = material_cost + outside_services
mats_services_markup = mats_and_services * (markup_pct / 100.0)
mats_and_services_marked_up = mats_and_services + mats_services_markup

# Total Quote = (Material + Outside Services marked up) + Flat Labor Cost
total_quote = mats_and_services_marked_up + labor_cost
per_unit_price = total_quote / part_qty

st.divider()

# Final Summary Display
st.header("📋 Quote Summary")
st.write(f"**Job:** {job_name} ({part_qty} units)")
st.write(f"**Total Labor Time:** {total_hours:.1f} Hours @ ${hourly_rate:.2f}/hr = **${labor_cost:,.2f}**")
st.write(f"**Materials & Outside Services:** ${mats_and_services:,.2f} (+{markup_pct}% Markup = **${mats_and_services_marked_up:,.2f}**)")
st.write(f"**Estimated Delivery:** {lead_time_days} business days")

st.subheader(f"Total Quote: **${total_quote:,.2f}**")
st.caption(f"(${per_unit_price:,.2f} per part)")

# Prepare downloadable file data structure
quote_data = [
    ("Job Name", job_name),
    ("Quantity", part_qty),
    ("Material Cost ($)", f"{material_cost:.2f}"),
    ("Outside Services ($)", f"{outside_services:.2f}"),
    ("Material & Services Markup (%)", f"{markup_pct}%"),
    ("Materials & Services Total (w/ Markup) ($)", f"{mats_and_services_marked_up:.2f}"),
    ("Hourly Labor Rate ($/hr)", f"{hourly_rate:.2f}"),
    ("Setup Hours", f"{setup_hrs:.1f}"),
    ("CNC Hours", f"{cnc_hrs:.1f}"),
    ("Manual Hours", f"{manual_hrs:.1f}"),
    ("Inspection Hours", f"{inspection_hrs:.1f}"),
    ("Total Labor Hours", f"{total_hours:.1f}"),
    ("Total Labor Cost ($)", f"{labor_cost:.2f}"),
    ("Estimated Lead Time (Days)", lead_time_days),
    ("Price Per Unit ($)", f"{per_unit_price:.2f}"),
    ("TOTAL QUOTE ($)", f"{total_quote:.2f}"),
]

st.divider()

# Select File Format
st.header("💾 Download Quote")
file_format = st.radio(
    "Select File Format:",
    options=["Excel (.xlsx)", "Word Document (.docx)", "CSV (.csv)"],
    horizontal=True,
)

safe_job_name = job_name.replace(" ", "_")

if file_format == "Excel (.xlsx)":
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
