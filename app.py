import io
from datetime import date

import docx
import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# --------------------------------------------------------------------------- #
# Page setup
# --------------------------------------------------------------------------- #
st.set_page_config(page_title="Quick Quote Builder", page_icon="🛠️", layout="centered")

# Scoped, lighter-touch styling instead of a blanket font-size override on
# every Streamlit internal class (which can break widget layout).
st.markdown(
    """
    <style>
    .block-container { padding-top: 2rem; max-width: 780px; }
    h1 { font-size: 2rem !important; }
    .stButton>button, .stDownloadButton>button {
        width: 100%;
        height: 3em;
        font-size: 18px !important;
        border-radius: 8px;
        font-weight: 600;
    }
    .stButton>button { background-color: #2e7d32; color: white; }
    .stDownloadButton>button { background-color: #1976d2; color: white; }
    [data-testid="stMetricValue"] { font-size: 1.6rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🛠️ Machine Shop Quote Builder")
st.caption("Fill in the job details, generate a quote, and download it in the format you need.")

# Hours fields: (label, session key, default)
HOUR_FIELDS = [
    ("Setup Hours", "setup_hrs", 1.0),
    ("CNC Machining Hours", "cnc_hrs", 2.0),
    ("Fabrication (Laser, Punch, Brake, Saw) Hours", "fab_hrs", 0.0),
    ("Weld Hours", "weld_hrs", 0.0),
    ("Manual / Finishing Hours", "manual_hrs", 0.5),
    ("Inspection / QC Hours", "inspection_hrs", 0.5),
    ("Paint Hours", "paint_hrs", 0.0),
]

# --------------------------------------------------------------------------- #
# Input form — nothing recalculates until "Generate Quote" is pressed
# --------------------------------------------------------------------------- #
with st.form("quote_form"):
    st.subheader("1. Job Info")
    c1, c2 = st.columns(2)
    with c1:
        job_name = st.text_input("Job / Part Name", value="Custom Part")
    with c2:
        part_qty = st.number_input("Number of Parts Needed", min_value=1, value=1, step=1)

    st.subheader("2. Raw Material")
    material_cost = st.number_input("Total Material Cost ($)", min_value=0.0, value=50.0, step=5.0)

    st.subheader("3. Labor Hours & Rate")
    hourly_rate = st.slider("Hourly Labor Rate ($/hr)", min_value=40, max_value=200, value=120, step=5)

    hours = {}
    hc1, hc2 = st.columns(2)
    for i, (label, key, default) in enumerate(HOUR_FIELDS):
        col = hc1 if i % 2 == 0 else hc2
        hours[key] = col.number_input(label, min_value=0.0, value=default, step=0.5, key=f"in_{key}")

    st.subheader("4. Lead Time, Shipping & Extras")
    lt1, lt2 = st.columns(2)
    with lt1:
        lead_time_days = st.slider("Shop Lead Time (Production Days)", min_value=1, max_value=30, value=5)
        outside_services = st.number_input(
            "Outside Services ($) — Heat Treat, Anodize, etc.", min_value=0.0, value=0.0, step=10.0
        )
    with lt2:
        shipping_days = st.slider("Shipping Transit Time (Days)", min_value=1, max_value=14, value=3)
        shipping_cost = st.number_input("Shipping Cost ($)", min_value=0.0, value=25.0, step=5.0)

    markup_pct = st.slider("Material & Services Markup (%)", min_value=0, max_value=60, value=20, step=5)

    submitted = st.form_submit_button("Generate Quote")

# --------------------------------------------------------------------------- #
# Calculation
# --------------------------------------------------------------------------- #
def build_quote(job_name, part_qty, material_cost, hourly_rate, hours,
                 lead_time_days, outside_services, markup_pct,
                 shipping_days, shipping_cost):
    total_hours = sum(hours.values())
    labor_cost = total_hours * hourly_rate

    mats_and_services = material_cost + outside_services
    mats_services_markup = mats_and_services * (markup_pct / 100.0)
    mats_and_services_marked_up = mats_and_services + mats_services_markup

    total_quote = mats_and_services_marked_up + labor_cost + shipping_cost
    per_unit_price = total_quote / part_qty
    total_delivery_days = lead_time_days + shipping_days

    rows = [
        ("Job Name", job_name),
        ("Quantity", part_qty),
        ("Material Cost ($)", f"{material_cost:.2f}"),
        ("Outside Services ($)", f"{outside_services:.2f}"),
        ("Material & Services Markup (%)", f"{markup_pct}%"),
        ("Materials & Services Total incl. Markup ($)", f"{mats_and_services_marked_up:.2f}"),
        ("Hourly Labor Rate ($/hr)", f"{hourly_rate:.2f}"),
        ("Setup Hours", f"{hours['setup_hrs']:.1f}"),
        ("CNC Hours", f"{hours['cnc_hrs']:.1f}"),
        ("Fabrication Hours (Laser/Punch/Brake/Saw)", f"{hours['fab_hrs']:.1f}"),
        ("Weld Hours", f"{hours['weld_hrs']:.1f}"),
        ("Manual Hours", f"{hours['manual_hrs']:.1f}"),
        ("Paint Hours", f"{hours['paint_hrs']:.1f}"),
        ("Inspection Hours", f"{hours['inspection_hrs']:.1f}"),
        ("Total Labor Hours", f"{total_hours:.1f}"),
        ("Total Labor Cost ($)", f"{labor_cost:.2f}"),
        ("Shipping Cost ($)", f"{shipping_cost:.2f}"),
        ("Shop Lead Time (Days)", lead_time_days),
        ("Shipping Transit Time (Days)", shipping_days),
        ("Total Estimated Delivery (Days)", total_delivery_days),
        ("Price Per Unit ($)", f"{per_unit_price:.2f}"),
        ("TOTAL QUOTE ($)", f"{total_quote:.2f}"),
        ("Quote Date", date.today().isoformat()),
    ]

    return {
        "job_name": job_name,
        "part_qty": part_qty,
        "total_hours": total_hours,
        "labor_cost": labor_cost,
        "mats_and_services": mats_and_services,
        "mats_and_services_marked_up": mats_and_services_marked_up,
        "markup_pct": markup_pct,
        "shipping_cost": shipping_cost,
        "lead_time_days": lead_time_days,
        "shipping_days": shipping_days,
        "total_delivery_days": total_delivery_days,
        "total_quote": total_quote,
        "per_unit_price": per_unit_price,
        "rows": rows,
    }


if submitted:
    if not job_name.strip():
        st.error("Please enter a Job / Part Name before generating a quote.")
    else:
        st.session_state["quote"] = build_quote(
            job_name.strip(), part_qty, material_cost, hourly_rate, hours,
            lead_time_days, outside_services, markup_pct, shipping_days, shipping_cost,
        )

# --------------------------------------------------------------------------- #
# Export builders
# --------------------------------------------------------------------------- #
def build_pdf(rows, job_name):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleStyle", parent=styles["Heading1"], fontSize=22, leading=26,
                                  textColor=colors.HexColor("#1B365D"), spaceAfter=15)
    cell_style = ParagraphStyle("CellStyle", parent=styles["Normal"], fontSize=10, leading=13)
    header_style = ParagraphStyle("HeaderCellStyle", parent=styles["Normal"], fontSize=11, leading=14,
                                   textColor=colors.white, fontName="Helvetica-Bold")

    story = [Paragraph(f"Machine Shop Quote: {job_name}", title_style), Spacer(1, 10)]
    table_data = [[Paragraph("Field", header_style), Paragraph("Value", header_style)]]
    for field, val in rows:
        table_data.append([Paragraph(str(field), cell_style), Paragraph(str(val), cell_style)])

    table = Table(table_data, colWidths=[320, 220])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B365D")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8F9FA")]),
    ]))
    story.append(table)
    doc.build(story)
    return buf.getvalue()


def build_excel(rows):
    df = pd.DataFrame(rows, columns=["Field", "Value"])
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Quote Summary")
    return buf.getvalue()


def build_docx(rows, job_name):
    doc = docx.Document()
    doc.add_heading(f"Machine Shop Quote: {job_name}", level=1)
    table = doc.add_table(rows=1, cols=2)
    table.style = "Light Grid Accent 1"
    hdr = table.rows[0].cells
    hdr[0].text, hdr[1].text = "Field", "Value"
    for field, val in rows:
        cells = table.add_row().cells
        cells[0].text, cells[1].text = str(field), str(val)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def build_csv(rows):
    df = pd.DataFrame(rows, columns=["Field", "Value"])
    return df.to_csv(index=False)


# --------------------------------------------------------------------------- #
# Summary + download
# --------------------------------------------------------------------------- #
quote = st.session_state.get("quote")

if quote:
    st.divider()
    st.header("📋 Quote Summary")
    st.write(f"**Job:** {quote['job_name']} ({quote['part_qty']} units)")

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Quote", f"${quote['total_quote']:,.2f}")
    m2.metric("Per Unit", f"${quote['per_unit_price']:,.2f}")
    m3.metric("Delivery", f"{quote['total_delivery_days']} days")

    st.write(
        f"**Labor:** {quote['total_hours']:.1f} hrs @ ${quote['labor_cost'] / max(quote['total_hours'], 1):,.2f}/hr "
        f"(actual rate) = **${quote['labor_cost']:,.2f}**"
    )
    st.write(
        f"**Materials & Outside Services:** ${quote['mats_and_services']:,.2f} "
        f"(+{quote['markup_pct']}% markup = **${quote['mats_and_services_marked_up']:,.2f}**). "
        f"*Markup applies to materials/services only, not labor.*"
    )
    st.write(f"**Shipping:** **${quote['shipping_cost']:,.2f}** "
             f"({quote['lead_time_days']} production days + {quote['shipping_days']} shipping days)")

    st.divider()
    st.header("💾 Download Quote")
    file_format = st.radio(
        "Select File Format:",
        options=["PDF (.pdf)", "Excel (.xlsx)", "Word Document (.docx)", "CSV (.csv)"],
        horizontal=True,
    )

    safe_job_name = quote["job_name"].replace(" ", "_")
    rows = quote["rows"]

    try:
        if file_format == "PDF (.pdf)":
            st.download_button("📥 Download PDF", build_pdf(rows, quote["job_name"]),
                                file_name=f"Quote_{safe_job_name}.pdf", mime="application/pdf")
        elif file_format == "Excel (.xlsx)":
            st.download_button("📥 Download Excel", build_excel(rows),
                                file_name=f"Quote_{safe_job_name}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        elif file_format == "Word Document (.docx)":
            st.download_button("📥 Download Word", build_docx(rows, quote["job_name"]),
                                file_name=f"Quote_{safe_job_name}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        else:
            st.download_button("📥 Download CSV", build_csv(rows),
                                file_name=f"Quote_{safe_job_name}.csv", mime="text/csv")
    except Exception as e:
        st.error(f"Couldn't generate the file: {e}")
else:
    st.info("Fill out the form above and click **Generate Quote** to see a summary and download options.")
