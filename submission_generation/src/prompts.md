## Version 1
You are an insurance broking assistant. Generate a realistic mid-market commercial property submission package based on the structure below. Generate **synthetic but credible** data for a UK manufacturing company. Follow these rules:

**Structure and contents**

As described in the attached markdown file. 

**Output files required**

1. PDF
- Full broking submission with example structure and contents as provided above. In the PDF file, do NOT include Sums Insured section, this section will be provided as a table in an Excel file.
- Add light to medium "scanned document" effect (off-white background, light rotation, faint watermark etc.)

2. Excel: This file will include the Sums Insured table for all locations as described in the above **structure and contents**.

3. Plain text: Submission email to an underwriter referencing the attachment(s), e.g., the PDF and Excel files. 



## Version 2
You are a Senior Insurance Broker. Read the attached template markdown file. Using the structure, contents and instructions as provided by the template, generate a realistic insurance submission for a UK manufacturer. OUTPUT AS VALID JSON.

### Filling out the form
You are an insurance broking assistant. I'm providing you with:
1. A JSON file containing business submission information
2. A commercial property insurance application form (multi-page PDF)

Your task: Create a filled-out version of this PDF form using ONLY the information from the JSON file.

RULES:

1. SEMANTIC FIELD MAPPING:
   - The JSON keys and PDF field labels won't match exactly - map them based on meaning and context
   - Explain your mapping decisions if any are ambiguous

2. TEXT PLACEMENT:
   - Fill information in the blank areas designated for each field (typically below or adjacent to field labels)
   - Ensure text is properly aligned and doesn't overlap with existing form elements
   - Use appropriate text sizing for the available space

3. CHECKBOX QUESTIONS:
   - Mark exactly ONE checkbox per question
   - Place checkmarks (☑) immediately to the right of Yes or No, on the same horizontal line
   - Example: "Is the building sprinklered?  Yes ☑  No ☐"

4. COMPLETENESS:
   - Fill all fields that have corresponding JSON data
   - Leave blank any fields without matching JSON information
   - Process all pages of the multi-page form

5. OUTPUT:
   - Provide the completed PDF ready for download
   - Provide a list of field label (from PDF) and value placed, explained using matching JSON information 

EXAMPLE MAPPING:
- PDF: "Please state name of the proposer including full trading name"
  JSON: "submission_title": "Broking Submission for ABC Company"
  → Fill "ABC Company" in the blank area below this label, and any alignment or formatting notes as necessary

Please proceed to fill out the form.


