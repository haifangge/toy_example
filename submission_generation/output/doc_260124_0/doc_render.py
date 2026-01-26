import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle, Frame, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import io
import random

# ==========================================
# 1. GENERATE EXCEL (SUMS INSURED)
# ==========================================

excel_filename = "Apex_Precision_Sums_Insured.xlsx"

data = {
    "Location": [
        "Loc 1: Apex Main Plant", "Loc 1: Apex Main Plant", "Loc 1: Apex Main Plant", "Loc 1: Apex Main Plant", "Loc 1: Apex Main Plant",
        "Loc 2: Coventry Distribution", "Loc 2: Coventry Distribution", "Loc 2: Coventry Distribution", "Loc 2: Coventry Distribution",
        "Loc 3: Solihull Sales Office", "Loc 3: Solihull Sales Office", "Loc 3: Solihull Sales Office"
    ],
    "Address": [
        "14-18 Industrial Parkway, Birmingham, B24 9QZ", "", "", "", "",
        "Unit 5, Logistics Way, Coventry, CV6 4BX", "", "", "",
        "Apex House, 22 Business Park, Solihull, B90 8AG", "", ""
    ],
    "Category": [
        "Buildings (Declared Value)", "Machinery & Plant", "Stock (Raw Materials)", "Stock (Finished Goods)", "Business Interruption (12m)",
        "Buildings (Declared Value)", "Machinery & Plant (Forklifts/Racking)", "Stock (Finished Goods)", "Business Interruption (Increased Cost of Working)",
        "Tenants Improvements", "Office Contents / Computers", "Business Interruption (ICOW)"
    ],
    "Sum Insured (£)": [
        3200000, 1500000, 400000, 600000, 2000000,
        1800000, 250000, 1200000, 500000,
        0, 150000, 250000
    ],
    "Notes": [
        "Day One Uplift 15%", "Indemnity Basis", "Floating limit across site", "Floating limit across site", "Gross Profit basis",
        "Day One Uplift 15%", "Indemnity Basis", "", "ICOW only",
        "Leased premises", "Reinstatement basis", "ICOW only"
    ]
}

df = pd.DataFrame(data)

# Create Excel file
with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
    df.to_excel(writer, index=False, sheet_name='Sums Insured Schedule')
    
    # Auto-adjust column widths (basic estimation)
    worksheet = writer.sheets['Sums Insured Schedule']
    for idx, col in enumerate(df.columns):
        max_len = max(df[col].astype(str).map(len).max(), len(col)) + 2
        worksheet.column_dimensions[chr(65 + idx)].width = max_len

# ==========================================
# 2. GENERATE PDF (BROKING SUBMISSION)
# ==========================================

pdf_filename = "Broking_Submission_Apex_Precision.pdf"

def create_scanned_pdf(filename):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    styles = getSampleStyleSheet()
    
    # Custom Styles
    styles.add(ParagraphStyle(name='MainTitle', parent=styles['Heading1'], fontSize=24, alignment=TA_CENTER, spaceAfter=20, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='SectionHeader', parent=styles['Heading2'], fontSize=16, spaceBefore=15, spaceAfter=10, fontName='Helvetica-Bold', textColor=colors.darkblue))
    styles.add(ParagraphStyle(name='NormalText', parent=styles['Normal'], fontSize=10, spaceAfter=6, fontName='Helvetica', leading=14))
    styles.add(ParagraphStyle(name='BulletItem', parent=styles['Normal'], fontSize=10, leftIndent=20, spaceAfter=4, bulletIndent=10))

    def draw_background(c):
        # Simulate "Off-white" paper
        c.setFillColorRGB(0.98, 0.97, 0.95) # Very light beige
        c.rect(0, 0, width, height, fill=1, stroke=0)
        
        # Simulate slight rotation/skew for "scanned" look
        # We rotate the coordinate system slightly for the text
        c.saveState()
        angle = random.uniform(-0.3, 0.3) # Slight rotation between -0.3 and 0.3 degrees
        c.rotate(angle)

    def restore_background(c):
        c.restoreState() # Restore from rotation

    # --- PAGE 1: INTRO ---
    draw_background(c)
    
    # Logo Placeholder
    c.setFont("Helvetica-Bold", 30)
    c.setFillColor(colors.darkslategrey)
    c.drawString(2 * inch, height - 3 * inch, "SUMMIT RISK SOLUTIONS")
    c.setFont("Helvetica", 10)
    c.drawString(2 * inch, height - 3.3 * inch, "Commercial Insurance Brokers | London, UK")
    
    # Submission Title
    text = []
    text.append(Paragraph("<b>BROKING SUBMISSION</b>", styles['MainTitle']))
    text.append(Spacer(1, 30))
    text.append(Paragraph("<b>Client:</b> Apex Precision Engineering Ltd", styles['Heading2']))
    text.append(Paragraph("<b>Submission Date:</b> 24th January 2026", styles['NormalText']))
    text.append(Paragraph("<b>Renewal Date:</b> 28th February 2026", styles['NormalText']))
    text.append(Spacer(1, 40))
    text.append(Paragraph("<b>Broker Contact:</b>", styles['Heading2']))
    text.append(Paragraph("Sarah Jenkins (Account Director)", styles['NormalText']))
    text.append(Paragraph("Email: s.jenkins@summit-risk.com", styles['NormalText']))
    text.append(Paragraph("Phone: +44 (0)20 7946 0123", styles['NormalText']))

    f = Frame(inch, inch, width - 2*inch, height - 5*inch, showBoundary=0)
    f.addFromList(text, c)
    restore_background(c)
    c.showPage()

    # --- PAGE 2: RISK OVERVIEW ---
    draw_background(c)
    
    story = []
    story.append(Paragraph("Risk Overview", styles['SectionHeader']))
    story.append(Paragraph("Apex Precision Engineering Ltd is a premier mid-market engineering firm specializing in CNC machining and precision components for the automotive and aerospace sectors. Established in 1998, they have been a client of Summit Risk Solutions for 8 years. This is a well-managed risk with a strong emphasis on quality control and health & safety.", styles['NormalText']))
    story.append(Paragraph("The risk is being marketed to benchmark pricing and ensure coverage aligns with their recent expansion into the EV (Electric Vehicle) supply chain.", styles['NormalText']))
    
    # Key Data
    story.append(Spacer(1, 10))
    data_list = [
        "<b>Business Activity:</b> Precision Engineering & Manufacturing",
        "<b>Established:</b> 1998",
        "<b>ERN:</b> 123/AB45678",
        "<b>Holding Insurer:</b> Aviva",
        "<b>Target Premium:</b> £65,000 + IPT",
        "<b>Renewal Date:</b> 28th February 2026"
    ]
    for item in data_list:
        story.append(Paragraph(f"• {item}", styles['BulletItem']))

    # Products and Covers
    story.append(Paragraph("Products and Covers Required", styles['SectionHeader']))
    covers = [
        "<b>Property Damage (All Risks):</b> See attached schedule for Sums Insured",
        "<b>Business Interruption:</b> £2m Gross Profit (12 months indemnity)",
        "<b>Employers Liability:</b> £10m Limit of Indemnity",
        "<b>Public/Products Liability:</b> £5m Limit of Indemnity",
        "<b>Goods in Transit:</b> £50,000 limit",
        "<b>Terrorism:</b> Required (All Locations)",
        "<b>Directors & Officers:</b> £1m Limit (Entity cover included)"
    ]
    for cover in covers:
        story.append(Paragraph(f"• {cover}", styles['BulletItem']))

    # Risk Management
    story.append(Paragraph("Risk Management", styles['SectionHeader']))
    rm_points = [
        "Dedicated full-time Risk Manager (James Thorne, NEBOSH qualified).",
        "ISO 9001 (Quality), ISO 14001 (Environmental), and ISO 45001 (Health & Safety) certified.",
        "Internal Health & Safety committee meets monthly.",
        "Strict permit-to-work system for all hot work and contractors.",
        "Waste metal stored externally in locked skips, min 10m from buildings.",
        "Thermographic imaging of electrical systems conducted annually (Last: Oct 2025)."
    ]
    for p in rm_points:
        story.append(Paragraph(f"• {p}", styles['BulletItem']))

    f = Frame(0.8*inch, 0.8*inch, width - 1.6*inch, height - 1.6*inch, showBoundary=0)
    f.addFromList(story, c)
    restore_background(c)
    c.showPage()

    # --- PAGE 3: PROPERTY DETAILS ---
    draw_background(c)
    story = []
    
    story.append(Paragraph("Property Damage Details", styles['SectionHeader']))
    story.append(Paragraph("The client operates from three locations. The Sums Insured are detailed in the attached Excel schedule. Below are the risk features for the main location.", styles['NormalText']))
    
    story.append(Paragraph("<b>Location 1: Main Manufacturing Plant (Birmingham)</b>", styles['Heading3']))
    
    loc_details = [
        "<b>Address:</b> 14-18 Industrial Parkway, Birmingham, B24 9QZ",
        "<b>Construction:</b> Steel portal frame, non-combustible composite cladding (LPCB approved), concrete floors, pitched steel roof. Built 2005.",
        "<b>Floor Area:</b> 3,500 sq meters.",
        "<b>Occupancy:</b> 80% Manufacturing (CNC, Lathes, Milling), 20% Finished Goods Storage.",
        "<b>Heating:</b> Gas fired warm air blowers (serviced annually)."
    ]
    for item in loc_details:
        story.append(Paragraph(f"• {item}", styles['BulletItem']))

    story.append(Paragraph("<b>Fire Protection & Security (Main Site)</b>", styles['Heading3']))
    prot_details = [
        "<b>Sprinklers:</b> Full automatic sprinkler system (BS EN 12845 compliant). Weekly bell tests, annual pump service.",
        "<b>Fire Alarm:</b> L1 Addressable system, connected to ARC (Redcare).",
        "<b>Extinguishers:</b> UKAS accredited annual maintenance.",
        "<b>Intruder Alarm:</b> NSI Gold certified, dual path signaling.",
        "<b>CCTV:</b> HD system covering perimeter and internal production areas, 30-day recording.",
        "<b>Perimeter:</b> 2.4m palisade fencing with gated access (locked overnight)."
    ]
    for item in prot_details:
        story.append(Paragraph(f"• {item}", styles['BulletItem']))

    story.append(Paragraph("Loss History (Past 5 Years)", styles['SectionHeader']))
    
    # Loss Table
    loss_data = [
        ["Year", "Type", "Amount", "Status", "Details"],
        ["2024", "Nil", "-", "-", "-"],
        ["2023", "Nil", "-", "-", "-"],
        ["2022", "Storm", "£4,200", "Closed", "Minor roof leak. Repaired. No recurrence."],
        ["2021", "Nil", "-", "-", "-"],
        ["2020", "Nil", "-", "-", "-"]
    ]
    
    t = Table(loss_data, colWidths=[40, 60, 60, 60, 250])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.black),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story.append(t)

    f = Frame(0.8*inch, 0.8*inch, width - 1.6*inch, height - 1.6*inch, showBoundary=0)
    f.addFromList(story, c)
    restore_background(c)
    c.showPage()
    
    # --- PAGE 4: LIABILITY ---
    draw_background(c)
    story = []
    
    story.append(Paragraph("Liability Covers", styles['SectionHeader']))
    
    story.append(Paragraph("<b>Employers Liability (£10m Limit)</b>", styles['Heading3']))
    story.append(Paragraph("Employees undertake precision machining, assembly, and warehouse duties. All machinery is guarded to PUWER standards. PPE (safety boots, glasses, hearing protection) is mandatory in production areas.", styles['NormalText']))
    
    # Wage Roll Table
    wage_data = [
        ["Category", "Headcount", "Wageroll (£)"],
        ["Clerical / Management / Sales", "12", "£650,000"],
        ["Manual - Premises (Machining)", "45", "£1,800,000"],
        ["Manual - Premises (Assembly/Warehouse)", "20", "£600,000"],
        ["Manual - Work Away (Install/Service)", "4", "£150,000"],
        ["Drivers", "3", "£90,000"],
        ["<b>TOTAL</b>", "<b>84</b>", "<b>£3,290,000</b>"]
    ]
    t_wage = Table(wage_data, colWidths=[250, 80, 100])
    t_wage.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ]))
    story.append(t_wage)
    
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Public & Products Liability (£5m Limit)</b>", styles['Heading3']))
    story.append(Paragraph("<b>Products:</b> Precision metal components (gears, shafts, brackets).", styles['NormalText']))
    story.append(Paragraph("<b>Sectors Served:</b> Automotive (Tier 2/3) - 60%, Aerospace (non-critical) - 30%, General Engineering - 10%.", styles['NormalText']))
    story.append(Paragraph("<b>Quality:</b> ISO 9001 certified. Full traceability of raw materials (steel/aluminum) back to source.", styles['NormalText']))

    # Turnover Table
    turnover_data = [
        ["Territory", "Turnover (£)"],
        ["United Kingdom", "£11,500,000"],
        ["EEA (Europe)", "£2,000,000"],
        ["USA / Canada", "£1,000,000"],
        ["Rest of World", "£0"],
        ["<b>TOTAL</b>", "<b>£14,500,000</b>"]
    ]
    t_to = Table(turnover_data, colWidths=[250, 100])
    t_to.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
    ]))
    story.append(t_to)
    
    story.append(Spacer(1, 10))
    story.append(Paragraph("Note regarding USA Exports: Indirect exports only (via UK Tier 1 suppliers). No direct sales offices or assets in North America.", styles['NormalText']))
    
    story.append(Paragraph("<b>Liability Claims History</b>", styles['Heading3']))
    story.append(Paragraph("2024: Nil", styles['BulletItem']))
    story.append(Paragraph("2023: Nil", styles['BulletItem']))
    story.append(Paragraph("2022: EL Claim - Cut finger on lathe. Claimant returned to work after 2 weeks. Reserves: £3,500. Status: Open (awaiting medical report).", styles['BulletItem']))
    story.append(Paragraph("2021: Nil", styles['BulletItem']))
    story.append(Paragraph("2020: Nil", styles['BulletItem']))

    f = Frame(0.8*inch, 0.8*inch, width - 1.6*inch, height - 1.6*inch, showBoundary=0)
    f.addFromList(story, c)
    restore_background(c)
    c.showPage()
    
    c.save()


if __name__ == "__main__":
    create_scanned_pdf(pdf_filename)
