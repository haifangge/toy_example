# PDF Table Extractor

A Python tool for extracting tables from PDFs, including support for:
- Tables with borders
- Borderless tables
- Tables spanning multiple pages
- Mixed content (text and tables)

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Command Line Usage

```bash
# Basic usage - extracts all tables using all three methods
python extract_pdf_tables.py your_document.pdf

# Specify output directory
python extract_pdf_tables.py your_document.pdf my_output_folder
```

### Python API Usage

```python
from extract_pdf_tables import PDFTableExtractor

# Initialize extractor
extractor = PDFTableExtractor("document.pdf", "output_folder")

# Method 1: Standard extraction (works best for tables with borders)
tables = extractor.extract_tables_standard()

# Method 2: Borderless table extraction (more aggressive)
tables = extractor.extract_tables_borderless()

# Method 3: Multi-page table merging (handles spanning tables)
tables = extractor.extract_and_merge_spanning_tables()

# Run all methods and compare results
extractor.extract_all_methods()
```

## Extraction Methods

The tool provides three extraction approaches:

### 1. Standard Table Extraction (`extract_tables_standard`)

Best for: Tables with clear borders and structure

- Uses pdfplumber's default table detection
- Works well with formatted tables that have visible gridlines
- Fast and reliable for standard tables

Output: `table_pageX_tableY.csv`

### 2. Borderless Table Extraction (`extract_tables_borderless`)

Best for: Tables without borders that rely on text alignment

- Uses text-based detection strategies
- Identifies tables based on column alignment and spacing
- More aggressive at finding tables without visual borders

Configuration:
```python
table_settings = {
    "vertical_strategy": "text",
    "horizontal_strategy": "text",
    "snap_tolerance": 3,
    "join_tolerance": 3,
}
```

Output: `borderless_pageX_tableY.csv`

### 3. Multi-page Table Merging (`extract_and_merge_spanning_tables`)

Best for: Tables that span multiple consecutive pages

- Detects tables across pages with matching column structures
- Automatically merges table continuations
- Handles repeated headers intelligently

Merging logic:
- Checks if tables on consecutive pages have the same column count
- Compares headers for similarity (>70% match)
- Merges data rows while removing duplicate headers

Output: `merged_table_X_from_pageY.csv`

## Output Structure

When running all methods (`extract_all_methods()`), results are organized as:

```
extracted_tables/
├── standard/
│   ├── table_page3_table1.csv
│   ├── table_page4_table1.csv
│   └── ...
├── borderless/
│   ├── borderless_page11_table1.csv
│   └── ...
└── merged/
    ├── merged_table_1_from_page3.csv
    └── ...
```

## Advanced Usage

### Custom Table Settings

For fine-tuning borderless table detection:

```python
extractor = PDFTableExtractor("document.pdf")

custom_settings = {
    "vertical_strategy": "text",
    "horizontal_strategy": "text",
    "snap_tolerance": 5,  # Increase for wider spacing
    "min_words_vertical": 2,  # Minimum words to form a column
}

# Manually extract with custom settings
import pdfplumber
with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        tables = page.extract_tables(table_settings=custom_settings)
        # Process tables...
```

### Working with Extracted DataFrames

```python
# Get tables as DataFrames (without saving)
tables = extractor.extract_tables_standard(save_csv=False)

# Process each DataFrame
for df in tables:
    # Clean data
    df = df.fillna('')
    
    # Filter rows
    df = df[df['Column1'] != '']
    
    # Data analysis
    print(df.describe())
    
    # Save with custom format
    df.to_excel('output.xlsx', index=False)
```

### Handling Specific Page Ranges

```python
import pdfplumber
import pandas as pd

# Extract only from specific pages
with pdfplumber.open("document.pdf") as pdf:
    # Pages 3-5 only
    for page_num in range(2, 5):  # 0-indexed
        page = pdf.pages[page_num]
        tables = page.extract_tables()
        
        for table in tables:
            if table:
                df = pd.DataFrame(table[1:], columns=table[0])
                df.to_csv(f'table_page{page_num+1}.csv', index=False)
```

## Troubleshooting

### Problem: Tables not detected

**Solution 1**: Try borderless extraction method
```python
extractor.extract_tables_borderless()
```

**Solution 2**: Adjust table settings
- Increase `snap_tolerance` for tables with irregular spacing
- Decrease `min_words_vertical` to detect smaller tables
- Use `"lines"` strategy if tables have partial borders

### Problem: Multi-page tables not merging correctly

**Solution**: Check column structure consistency
```python
# Verify column counts match across pages
with pdfplumber.open("document.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        tables = page.extract_tables()
        for table in tables:
            if table:
                print(f"Page {i+1}: {len(table[0])} columns")
```

### Problem: Too many false positives

**Solution**: Increase minimum thresholds
```python
table_settings = {
    "min_words_vertical": 5,  # Require more words per column
    "edge_min_length": 10,    # Require longer edges
}
```

### Problem: Headers repeated in merged tables

The tool automatically handles this, but if issues persist:
```python
# Manual cleanup
df = df[df['Column1'] != 'Column1']  # Remove header rows in data
df = df.reset_index(drop=True)
```

## Performance Tips

1. **Large PDFs**: Process in chunks
```python
# Process pages in batches
batch_size = 10
for start in range(0, total_pages, batch_size):
    # Process pages start to start+batch_size
    pass
```

2. **Many tables**: Use parallel processing
```python
from concurrent.futures import ProcessPoolExecutor

def process_page(page_num):
    # Extract tables from single page
    pass

with ProcessPoolExecutor() as executor:
    results = executor.map(process_page, range(total_pages))
```

## Common Use Cases

### Insurance Documents
Your scenario with mixed text/tables and spanning tables:
```python
extractor = PDFTableExtractor("insurance_doc.pdf")
# Use merged extraction to handle multi-page tables
tables = extractor.extract_and_merge_spanning_tables()
```

### Financial Reports
Tables with consistent formatting:
```python
extractor = PDFTableExtractor("financial_report.pdf")
tables = extractor.extract_tables_standard()
```

### Forms and Surveys
Borderless tables with text alignment:
```python
extractor = PDFTableExtractor("survey.pdf")
tables = extractor.extract_tables_borderless()
```

## Additional Resources

- [pdfplumber documentation](https://github.com/jsvine/pdfplumber)
- [Pandas documentation](https://pandas.pydata.org/docs/)

## Limitations

- Scanned PDFs require OCR preprocessing (use pytesseract)
- Complex nested tables may need manual review
- Very irregular table layouts might require custom parsing logic
- Rotated tables may not be detected correctly
