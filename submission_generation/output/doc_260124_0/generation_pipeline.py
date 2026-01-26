import json
import pandas as pd
import os
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle, Frame, Spacer
from reportlab.lib.enums import TA_CENTER


# ==========================================
# 1. THE LLM GENERATION LAYER
# ==========================================

def get_data_from_llm(template_text):
    """
    In a real scenario, this function sends the 'template_text' to 
    GPT-4 or Gemini with a system prompt asking for JSON output.
    """
    
    # --- REAL API CODE (COMMENTED OUT) ---
    from openai import OpenAI

    openai = OpenAI()

    prompt = f"Read this template: {template_text}. Generate a realistic insurance submission for a UK manufacturer. OUTPUT AS VALID JSON."
    response = openai.chat.completions.create(model="gpt-5.2", messages=[{"role": "user", "content": prompt}])
    
    # print(response.choices[0].message.content)  # For debugging
    # Replace and assign back to original content
    json_result = response.choices[0].message.content
    json_result = json_result.replace("```json", "")
    json_result = json_result.replace("```", "")

    return json.loads(json_result)
    # -------------------------------------

    print("🔄 Step 2: Calling (Simulated) LLM to generate synthetic data...")
    
    # --- SIMULATED RESPONSE (HARDCODED JSON) ---
    # This represents exactly what the LLM would return in JSON format
    mock_json_response = {
        "broker": {
            "name": "Summit Risk Solutions",
            "contact": "Sarah Jenkins",
            "email": "s.jenkins@summit-risk.com",
            "phone": "+44 (0)20 7946 0123"
        },
        "client": {
            "name": "Apex Precision Engineering Ltd",
            "activity": "Precision CNC manufacturing for automotive/aerospace",
            "est": "1998",
            "renewal_date": "28/02/2026",
            "target_premium": "£65,000 + IPT",
            "holding_insurer": "Aviva"
        },
        "email_text": "Please find attached the submission for Apex Precision. Target premium is £65k. Risk is well managed with full ISO accreditation.",
        "risk_highlights": [
            "ISO 9001, 14001, 45001 accredited",
            "Full sprinkler protection (EN 12845)",
            "NSI Gold Intruder Alarm",
            "Dedicated Risk Manager on site"
        ],
        "locations": [
            {
                "name": "Main Plant (Birmingham)",
                "address": "14-18 Industrial Parkway, B24 9QZ",
                "details": "Steel portal frame, built 2005. 3,500 sqm.",
                "sums_insured": {
                    "Buildings": 3200000,
                    "Machinery": 1500000,
                    "Stock": 1000000,
                    "BI": 2000000
                }
            },
            {
                "name": "Distribution Hub (Coventry)",
                "address": "Unit 5, Logistics Way, CV6 4BX",
                "details": "Modern warehouse, built 2015.",
                "sums_insured": {
                    "Buildings": 1800000,
                    "Machinery": 250000,
                    "Stock": 1200000,
                    "BI": 500000
                }
            }
        ],
        "liability": {
            "wageroll": [
                ["Clerical", "£650,000"],
                ["Manual (Premises)", "£2,400,000"],
                ["Drivers", "£90,000"]
            ],
            "turnover": [
                ["UK", "£11,500,000"],
                ["Europe", "£2,000,000"],
                ["USA", "£1,000,000"]
            ]
        },
        "claims": [
            ["2022", "Storm", "£4,200", "Closed - Roof leak repaired"],
            ["2024", "Nil", "-", "-"]
        ]
    }
    
    return mock_json_response

# ==========================================
# 3. OUTPUT GENERATORS
# ==========================================

def generate_excel(data, filename="Output_SumsInsured.xlsx"):
    print(f"📊 Step 3a: Generating Excel file: {filename}")
    
    # Flatten JSON 'locations' into a list suitable for Excel
    rows = []
    for loc in data['locations']:
        # Header for location
        for category, amount in loc['sums_insured'].items():
            rows.append({
                "Location": loc['name'],
                "Address": loc['address'],
                "Category": category,
                "Sum Insured (£)": amount,
                "Notes": "Day One Uplift" if category == "Buildings" else "Indemnity"
            })
            
    df = pd.DataFrame(rows)
    df.to_excel(filename, index=False)

def generate_pdf(data, filename="Output_Submission.pdf"):
    print(f"📄 Step 3b: Generating PDF file: {filename}")
    
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, alignment=TA_CENTER)
    h2_style = ParagraphStyle('H2', parent=styles['Heading2'], spaceBefore=15, textColor=colors.darkblue)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], spaceAfter=6)

    story = []

    # -- Intro --
    story.append(Paragraph("BROKING SUBMISSION", title_style))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"<b>Client:</b> {data['client']['name']}", normal_style))
    story.append(Paragraph(f"<b>Broker:</b> {data['broker']['name']}", normal_style))
    story.append(Spacer(1, 20))

    # -- Risk Overview --
    story.append(Paragraph("Risk Overview", h2_style))
    story.append(Paragraph(data['client']['activity'], normal_style))
    story.append(Paragraph(f"Target Premium: {data['client']['target_premium']}", normal_style))
    
    for highlight in data['risk_highlights']:
        story.append(Paragraph(f"• {highlight}", normal_style))

    # -- Locations (Narrative only, nums are in Excel) --
    story.append(Paragraph("Location Details", h2_style))
    story.append(Paragraph("<i>(See attached Excel for full Sums Insured)</i>", normal_style))
    
    for loc in data['locations']:
        story.append(Paragraph(f"<b>{loc['name']}</b>", styles['Heading3']))
        story.append(Paragraph(f"Address: {loc['address']}", normal_style))
        story.append(Paragraph(f"Details: {loc['details']}", normal_style))
        story.append(Spacer(1, 5))

    # -- Liability Tables --
    story.append(Paragraph("Liability Information", h2_style))
    
    # Wageroll Table
    story.append(Paragraph("<b>Wageroll Split</b>", styles['Normal']))
    wage_data = [["Category", "Amount"]] + data['liability']['wageroll']
    t = Table(wage_data, colWidths=[200, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story.append(t)

    # -- Claims --
    story.append(Paragraph("Claims History", h2_style))
    claims_data = [["Year", "Type", "Amount", "Details"]] + data['claims']
    t2 = Table(claims_data, colWidths=[50, 80, 60, 200])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('FONTSIZE', (0,0), (-1,-1), 8),
    ]))
    story.append(Spacer(1, 10))
    story.append(t2)

    # Build PDF
    f = Frame(inch, inch, width - 2*inch, height - 2*inch)
    f.addFromList(story, c)
    c.showPage()
    c.save()

def generate_email(data, filename="Output_Email.txt"):
    print(f"📧 Step 3c: Generating Text Email: {filename}")
    
    email_body = f"""
Subject: New Submission - {data['client']['name']}

Hi Underwriting Team,

{data['email_text']}

Please see attached:
1. PDF Submission (Qualitative data)
2. Excel Schedule (Sums Insured)

Broker: {data['broker']['name']}
Contact: {data['broker']['contact']}
    """
    
    with open(filename, "w") as f:
        f.write(email_body)

# ==========================================
# 4. MAIN EXECUTION FLOW
# ==========================================

if __name__ == "__main__":
    # A. Read the markdown template
    with open("../../data/manufacturing_template.md", "r") as f:
        md_content = f.read()

    # B. Call the (simulated) LLM to get structured JSON
    submission_data = get_data_from_llm(md_content)

    # Save the JSON for reference
    with open("Output_Submission.json", "w") as f:
        json.dump(submission_data, f, indent=4)

    # C. Generate the files based on that JSON
    # generate_excel(submission_data)
    # generate_pdf(submission_data)
    # generate_email(submission_data)

    # print("\n✅ PROCESS COMPLETE. Created 3 files:")
    # print("   1. Output_Submission.pdf")
    # print("   2. Output_SumsInsured.xlsx")
    # print("   3. Output_Email.txt")
