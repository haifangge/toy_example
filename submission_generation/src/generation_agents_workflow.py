import os
import json
import pandas as pd
from typing import List
from pydantic import BaseModel, Field
from openai import OpenAI

# ReportLab Imports (Updated for Multi-page support)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, ListFlowable, ListItem, PageBreak
from reportlab.lib.enums import TA_CENTER

# ==========================================
# 0. CONFIGURATION
# ==========================================
client = OpenAI() # Ensure OPENAI_API_KEY is set
TEMPLATE_FILE = "../../data/manufacturing_template.md"

if not os.path.exists(TEMPLATE_FILE):
    # Raise error if template missing
    raise FileNotFoundError(f"Template file '{TEMPLATE_FILE}' not found. Please create it.")

# ==========================================
# 1. PYDANTIC SCHEMA
# ==========================================
class SumsInsured(BaseModel):
    buildings: float
    machinery: float
    stock: float
    bi: float

class Location(BaseModel):
    name: str
    address: str
    description: str
    security_details: str
    sums_insured: SumsInsured

class WagerollCategory(BaseModel):
    category: str
    count: int
    amount: float

class TurnoverCategory(BaseModel):
    territory: str
    amount: float

class Claim(BaseModel):
    year: str
    type: str
    status: str
    amount: str
    details: str

class SubmissionPackage(BaseModel):
    broker_name: str
    broker_contact: str
    client_name: str
    business_description: str
    risk_management_narrative: str
    risk_management_points: List[str]
    locations: List[Location]
    wageroll_split: List[WagerollCategory]
    turnover_split: List[TurnoverCategory]
    claims_history: List[Claim]
    # FIX: Ensure this field is populated by the agents
    email_body: str = Field(..., description="The text of the email to the underwriter.")

# ==========================================
# 2. THE AGENTS (FIXED)
# ==========================================

def agent_creative_writer(template_content: str) -> str:
    print("✍️  Agent 1: Writing narrative AND email draft...")
    
    # FIX: Explicitly ask for the email draft in the prompt
    system_prompt = (
        "You are a Senior Insurance Broker. "
        "1. Write a realistic submission for a UK Manufacturing client based on the template. "
        "2. enerate synthetic but credible data "
        "3. AT THE VERY END, write a short, professional email to an underwriter (Subject: New Submission) summarizing the risk."
    )
    
    response = client.chat.completions.create(
        model="gpt-5.2-2025-12-11",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Template:\n{template_content}"}
        ]
    )
    return response.choices[0].message.content


def agent_data_extractor(narrative_text: str) -> SubmissionPackage:
    print("🤖 Agent 2: Extracting data and email text...")
    
    # FIX: Explicitly ask Agent 2 to extract the email section
    system_prompt = (
        "You are a Data Extractor. "
        "Read the submission text provided. "
        "Extract all fields into the JSON schema. "
        "Find the email draft at the end of the text and put it into 'email_body'. "
        "Ensure all numeric tables are captured perfectly."
    )
    
    completion = client.beta.chat.completions.parse(
        model="gpt-5.2-2025-12-11",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": narrative_text},
        ],
        response_format=SubmissionPackage,
    )
    return completion.choices[0].message.parsed


# ==========================================
# 3. PDF GENERATOR
# ==========================================
def generate_formatted_pdf(data: SubmissionPackage, filename="Submission_Formatted.pdf"):
    print(f"📄 Generating Formatted PDF (Fixed Layout): {filename}")
    
    # FIX 1: Reduce margins from 1 inch to 0.5 inch to give the table more room
    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        rightMargin=0.5*inch, leftMargin=0.5*inch,
        topMargin=0.5*inch, bottomMargin=0.5*inch
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    style_title = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=22, spaceAfter=20, alignment=TA_CENTER, textColor=colors.darkslategrey)
    style_h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=14, spaceBefore=15, textColor=colors.navy)
    style_h3 = ParagraphStyle('H3', parent=styles['Heading3'], fontSize=11, spaceBefore=10)
    style_body = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=8)
    
    # FIX 2: Create a specific style for Table formatting (smaller font, tight leading)
    style_table_text = ParagraphStyle('TableText', parent=styles['Normal'], fontSize=9, leading=11)
    
    story = []

    # --- CONTENT ---

    # 1. Header
    story.append(Paragraph(f"BROKING SUBMISSION", style_title))
    story.append(Paragraph(f"<b>Client:</b> {data.client_name}", style_body))
    story.append(Paragraph(f"<b>Broker:</b> {data.broker_name}", style_body))
    story.append(Spacer(1, 20))

    # 2. Risk Overview
    story.append(Paragraph("Risk Overview", style_h2))
    story.append(Paragraph(data.business_description, style_body))

    # 3. Risk Management
    story.append(Paragraph("Risk Management", style_h2))
    story.append(Paragraph(data.risk_management_narrative, style_body))
    
    if data.risk_management_points:
        bullets = [ListItem(Paragraph(pt, style_body)) for pt in data.risk_management_points]
        story.append(ListFlowable(bullets, bulletType='bullet', start='circle', leftIndent=20))

    # 4. Property
    story.append(Paragraph("Property Summary", style_h2))
    story.append(Paragraph("<i>(See attached Excel for full Sums Insured Schedule)</i>", style_body))
    
    for loc in data.locations:
        story.append(Paragraph(f"<b>{loc.name}</b>: {loc.address}", style_h3))
        story.append(Paragraph(loc.description, style_body))
        story.append(Paragraph(f"<i>Security:</i> {loc.security_details}", style_body))

    # 5. Liability
    story.append(Paragraph("Liability & Turnover", style_h2))
    
    # Wageroll Table
    story.append(Paragraph("<b>Wageroll Split</b>", style_h3))
    wage_data = [["Category", "Headcount", "Wageroll"]]
    for w in data.wageroll_split:
        wage_data.append([
            Paragraph(w.category, style_table_text), # Wrap category text if long
            str(w.count), 
            f"£{w.amount:,.2f}"
        ])
    
    # Adjusted widths for wider page
    t_wage = Table(wage_data, colWidths=[300, 80, 120], hAlign='LEFT')
    t_wage.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.aliceblue),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_wage)
    story.append(Spacer(1, 12))

    # Turnover Table
    story.append(Paragraph("<b>Turnover Split</b>", style_h3))
    turnover_data = [["Territory", "Amount"]]
    for t in data.turnover_split:
        turnover_data.append([t.territory, f"£{t.amount:,.2f}"])
        
    t_to = Table(turnover_data, colWidths=[300, 120], hAlign='LEFT')
    t_to.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.aliceblue),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_to)

    # 6. Claims History (FIXED)
    story.append(Paragraph("Claims History", style_h2))
    claims_data = [["Year", "Type", "Status", "Amount", "Details"]]
    
    for c in data.claims_history:
        # FIX 3: Wrap *every* text field in a Paragraph.
        # This prevents overlap if "Type" or "Status" happens to be long.
        c_year = Paragraph(c.year, style_table_text)
        c_type = Paragraph(c.type, style_table_text)
        c_status = Paragraph(c.status, style_table_text)
        c_amt = Paragraph(c.amount, style_table_text)
        c_details = Paragraph(c.details, style_table_text)
        
        claims_data.append([c_year, c_type, c_status, c_amt, c_details])

    # FIX 4: Updated Column Widths (Total ~515pts, fits within 0.5" margins)
    # Give 'Details' the most space (275)
    t_claims = Table(claims_data, colWidths=[45, 75, 60, 60, 275], hAlign='LEFT')
    
    t_claims.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'), # Aligns text to top of cell
        ('PADDING', (0,0), (-1,-1), 4),    # Adds breathing room inside cells
    ]))
    story.append(t_claims)

    # Build the PDF
    doc.build(story)
    
# ==========================================
# 4. EXCEL & EMAIL GENERATORS
# ==========================================
def generate_excel(data: SubmissionPackage, filename="Submission_SumsInsured.xlsx"):
    print(f"📊 Generating Excel: {filename}")
    rows = []
    for loc in data.locations:
        si = loc.sums_insured
        items = [("Buildings", si.buildings), ("Machinery", si.machinery), ("Stock", si.stock), ("BI", si.bi)]
        for cat, amt in items:
            rows.append({"Location": loc.name, "Address": loc.address, "Category": cat, "Sum Insured": amt})
    
    df = pd.DataFrame(rows)
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

def generate_email_file(data: SubmissionPackage, filename="Submission_Email.txt"):
    print(f"📧 Generating Email: {filename}")
    with open(filename, "w") as f:
        # Now uses the extracted email_body
        f.write(data.email_body)

# ==========================================
# 5. MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    with open(TEMPLATE_FILE, "r") as f: template_content = f.read()

    # Pipeline
    raw_narrative = agent_creative_writer(template_content)
    structured_data = agent_data_extractor(raw_narrative)

    # File Creation
    generate_excel(structured_data)
    generate_formatted_pdf(structured_data)
    generate_email_file(structured_data)
    
    print("\n✅ SUCCESS: All files generated. Email body is now populated.")
