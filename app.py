import io
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

# Step 3: Labor Hours per Department
st.header("3. Labor Hours")
hourly_rate = 75.0  # Default shop hourly rate

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
labor_cost = total_hours * hourly_rate

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
    "Profit Markup (%)", min_value=0, max_value=50, value=20, step=5
)

# Calculations
subtotal = material_cost + labor_cost + outside_services
total_quote = subtotal * (1 + (markup_pct / 100))
per_unit_price = total_quote / part_qty

st.divider()

# Final Summary Display
st.header("📋 Quote Summary")
st.write(f"**Job:** {job_name} ({part_qty} units)")
st.write(f"**Total Labor Time:** {total_hours:.1f} Hours")
st.write(f"**Estimated Delivery:** {lead_time_days} business days")

st.subheader(f"Total Quote: **${total_quote:,.2f}**")
st.caption(f"(${per_unit_price:,.2f} per part)")

# Prepare downloadable file
quote_data = {
    "Field": [
        "Job Name",
        "Quantity",
        "Material Cost ($)",
        "Setup Hours",
        "CNC Hours",
        "Manual Hours",
        "Inspection Hours",
        "Total Labor Hours",
        "Labor Cost ($)",
        "Outside Services ($)",
        "Markup (%)",
        "Estimated Lead Time (Days)",
        "Price Per Unit ($)",
        "TOTAL QUOTE ($)",
    ],
    "Value": [
        job_name,
        part_qty,
        f"{material_cost:.2f}",
        f"{setup_hrs:.1f}",
        f"{cnc_hrs:.1f}",
        f"{manual_hrs:.1f}",
        f"{inspection_hrs:.1f}",
        f"{total_hours:.1f}",
        f"{labor_cost:.2f}",
        f"{outside_services:.2f}",
        f"{markup_pct}%",
        lead_time_days,
        f"{per_unit_price:.2f}",
        f"{total_quote:.2f}",
    ],
}

df_quote = pd.DataFrame(quote_data)
csv_buffer = df_quote.to_csv(index=False)

st.divider()

# Download Button
st.download_button(
    label="📥 Download Quote File",
    data=csv_buffer,
    file_name=f"Quote_{job_name.replace(' ', '_')}.csv",
    mime="text/csv",
)
