"""
Example usage scenarios for PDF table extraction
"""
from extract_pdf_tables import PDFTableExtractor
import pandas as pd


def example_basic_extraction():
    """Example 1: Basic extraction - all methods"""
    print("Example 1: Basic Extraction")
    print("-" * 60)
    
    extractor = PDFTableExtractor("your_document.pdf", "output")
    
    # Run all methods and compare
    extractor.extract_all_methods()
    
    print("\nCheck the 'output' folder for results!")


def example_standard_tables_only():
    """Example 2: Extract only tables with borders"""
    print("\nExample 2: Standard Tables Only")
    print("-" * 60)
    
    extractor = PDFTableExtractor("your_document.pdf", "standard_output")
    
    # Get tables as DataFrames
    tables = extractor.extract_tables_standard(save_csv=True)
    
    print(f"Found {len(tables)} standard tables")
    
    # Preview first table
    if tables:
        print("\nFirst table preview:")
        print(tables[0].head())


def example_borderless_tables():
    """Example 3: Extract borderless tables"""
    print("\nExample 3: Borderless Tables")
    print("-" * 60)
    
    extractor = PDFTableExtractor("your_document.pdf", "borderless_output")
    
    # Extract borderless tables
    tables = extractor.extract_tables_borderless(save_csv=True)
    
    print(f"Found {len(tables)} borderless tables")


def example_merge_spanning_tables():
    """Example 4: Merge multi-page tables"""
    print("\nExample 4: Merge Spanning Tables")
    print("-" * 60)
    
    extractor = PDFTableExtractor("your_document.pdf", "merged_output")
    
    # Extract and merge tables across pages
    tables = extractor.extract_and_merge_spanning_tables(save_csv=True)
    
    print(f"Found {len(tables)} merged tables")
    
    # Show size of merged tables
    for i, df in enumerate(tables, 1):
        print(f"Table {i}: {df.shape[0]} rows × {df.shape[1]} columns")


def example_process_extracted_data():
    """Example 5: Process extracted data"""
    print("\nExample 5: Process Extracted Data")
    print("-" * 60)
    
    extractor = PDFTableExtractor("your_document.pdf")
    
    # Get tables without saving
    tables = extractor.extract_tables_standard(save_csv=False)
    
    for i, df in enumerate(tables, 1):
        print(f"\nProcessing table {i}...")
        
        # Clean data
        df = df.fillna('')
        df = df.replace('', pd.NA).dropna(how='all')
        
        # Remove empty columns
        df = df.dropna(axis=1, how='all')
        
        # Example: Filter specific rows
        # df = df[df['Status'] == 'Active']
        
        # Example: Convert types
        # df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
        
        # Save with custom name
        df.to_csv(f'processed_table_{i}.csv', index=False)
        
        print(f"  Saved: processed_table_{i}.csv")
        print(f"  Shape: {df.shape}")


def example_custom_settings():
    """Example 6: Use custom extraction settings"""
    print("\nExample 6: Custom Settings")
    print("-" * 60)
    
    import pdfplumber
    
    # Custom settings for challenging borderless tables
    custom_settings = {
        "vertical_strategy": "text",
        "horizontal_strategy": "text",
        "snap_tolerance": 5,  # Wider tolerance for spacing
        "join_tolerance": 5,
        "min_words_vertical": 2,  # Fewer words required per column
        "min_words_horizontal": 1,
    }
    
    with pdfplumber.open("your_document.pdf") as pdf:
        for i, page in enumerate(pdf.pages, 1):
            print(f"Processing page {i}...")
            
            tables = page.extract_tables(table_settings=custom_settings)
            
            for j, table in enumerate(tables, 1):
                if table and len(table) > 1:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
                    
                    if not df.empty:
                        filename = f'custom_page{i}_table{j}.csv'
                        df.to_csv(filename, index=False)
                        print(f"  Saved: {filename}")


def example_specific_pages():
    """Example 7: Extract from specific pages only"""
    print("\nExample 7: Specific Pages Only")
    print("-" * 60)
    
    import pdfplumber
    
    # Extract tables only from pages 3, 4, 5, and 11
    target_pages = [3, 4, 5, 11]
    
    with pdfplumber.open("your_document.pdf") as pdf:
        for page_num in target_pages:
            if page_num <= len(pdf.pages):
                page = pdf.pages[page_num - 1]  # 0-indexed
                print(f"\nProcessing page {page_num}...")
                
                tables = page.extract_tables()
                
                for j, table in enumerate(tables, 1):
                    if table and len(table) > 1:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
                        
                        if not df.empty:
                            filename = f'page{page_num}_table{j}.csv'
                            df.to_csv(filename, index=False)
                            print(f"  Found table: {df.shape}")


def main():
    """Run examples"""
    print("PDF Table Extraction Examples")
    print("=" * 60)
    print("\nChoose an example to run:")
    print("1. Basic extraction (all methods)")
    print("2. Standard tables only")
    print("3. Borderless tables")
    print("4. Merge spanning tables")
    print("5. Process extracted data")
    print("6. Custom settings")
    print("7. Specific pages")
    print("0. Run all examples")
    
    choice = input("\nEnter choice (0-7): ").strip()
    
    examples = {
        '0': lambda: [example_basic_extraction(), example_standard_tables_only(),
                     example_borderless_tables(), example_merge_spanning_tables(),
                     example_process_extracted_data(), example_custom_settings(),
                     example_specific_pages()],
        '1': example_basic_extraction,
        '2': example_standard_tables_only,
        '3': example_borderless_tables,
        '4': example_merge_spanning_tables,
        '5': example_process_extracted_data,
        '6': example_custom_settings,
        '7': example_specific_pages,
    }
    
    if choice in examples:
        try:
            examples[choice]()
        except FileNotFoundError:
            print("\nError: Please replace 'your_document.pdf' with your actual PDF file path")
        except Exception as e:
            print(f"\nError: {e}")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
