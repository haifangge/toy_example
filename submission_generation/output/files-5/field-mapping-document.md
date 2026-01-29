# PDF Form Field Mapping Document

## Property Owners Insurance Application Form - Field Mapping

This document shows how data from the JSON submission file was mapped to the PDF form fields.

---

### Field 1: Name of Applicant(s)
**PDF Field Label:** "Name of Applicant(s) - Please clearly define all parties to be insured identifying any holding/subsidiary company relationships."

**Value Filled:** Titan Automotive Components Ltd

**JSON Source:** 
- Path: `submission_header.insured_details.company_name`
- Original Value: "Titan Automotive Components Ltd"

**Mapping Explanation:** The company name was extracted from the insured details section of the submission header.

---

### Field 2: Owners'/Directors'/Partners' full names
**PDF Field Label:** "Owners'/Directors'/Partners' full names (if not shown above)"

**Value Filled:** [Left Blank]

**JSON Source:** Not available in submission data

**Mapping Explanation:** The submission JSON does not contain information about individual owners, directors, or partners. This field was left blank as no corresponding data exists.

---

### Field 3: Postal address
**PDF Field Label:** "Postal address"

**Value Filled:** Unit 5-7, Stafford Park, Telford, TF3 3BQ

**JSON Source:** 
- Path: `property_damage_cover.locations[0].address`
- Original Value: "Unit 5-7, Stafford Park, Telford, TF3 3BQ"

**Mapping Explanation:** Used the address of the primary location (Location ID 1 - "Headquarters & Primary Manufacturing"). This is the main business address for the insured party.

---

### Field 4: Postcode
**PDF Field Label:** "Postcode"

**Value Filled:** TF3 3BQ

**JSON Source:** 
- Path: `property_damage_cover.locations[0].address` (extracted)
- Original Value: "Unit 5-7, Stafford Park, Telford, TF3 3BQ"

**Mapping Explanation:** The postcode was extracted from the end of the primary location address string.

---

### Field 5: Telephone
**PDF Field Label:** "Telephone"

**Value Filled:** +44 (0) 20 7946 0123

**JSON Source:** 
- Path: `submission_header.broker_details.contact_phone`
- Original Value: "+44 (0) 20 7946 0123"

**Mapping Explanation:** Used the broker's contact phone number. Since the submission is prepared by Summit Risk Partners on behalf of Titan Automotive, the broker contact information is used as the primary contact point.

---

### Field 6: Email
**PDF Field Label:** "Email"

**Value Filled:** s.jenkins@summitrisk.co.uk

**JSON Source:** 
- Path: `submission_header.broker_details.contact_email`
- Original Value: "s.jenkins@summitrisk.co.uk"

**Mapping Explanation:** Used the broker's contact email address (Sarah Jenkins, Senior Corporate Broker at Summit Risk Partners). This is the primary contact for the insurance application.

---

### Field 7: Website
**PDF Field Label:** "Website"

**Value Filled:** [Left Blank]

**JSON Source:** Not available in submission data

**Mapping Explanation:** The submission JSON does not contain a website field for either the broker or the insured company. This field was left blank.

---

### Field 8: Date upon which the insurance is to commence
**PDF Field Label:** "Date upon which the insurance is to commence"

**Value Filled:** 2025-10-30

**JSON Source:** 
- Path: `submission_header.dates.renewal_date`
- Original Value: "2025-10-30"
- Also referenced at: `risk_overview.business_details.renewal_date`

**Mapping Explanation:** Used the renewal date from the submission, which represents the date when the new insurance coverage should commence.

---

## Summary Statistics

- **Total PDF Fields:** 8
- **Fields Filled:** 6
- **Fields Left Blank:** 2 (Fields 2 and 7 - no corresponding data in JSON)
- **Primary Data Sources:**
  - Submission Header: 4 fields
  - Property Damage Cover (Location 1): 2 fields
  - No data available: 2 fields

## Notes on Semantic Mapping

1. **Company Name:** Straightforward mapping from insured details to applicant name
2. **Address Selection:** Chose the headquarters/primary manufacturing location as the main business address rather than the warehouse or R&D facility
3. **Contact Information:** Used broker contact details as they are the primary point of contact for the insurance application
4. **Date Format:** Preserved the ISO date format (YYYY-MM-DD) from the JSON
5. **Missing Data:** Left fields blank where no corresponding information exists rather than making assumptions
