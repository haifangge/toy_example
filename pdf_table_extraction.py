import pdfplumber
import pandas as pd


def extract_and_save_tables(pdf_path):
    # This list will hold all our final, stitched tables
    all_tables = []
    
    # We keep track of the "current" table being built across pages
    current_table_data = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            print(f"Processing page {i+1}...")
            
            # Extract table with a strategy that handles both bordered and borderless
            # vertical_strategy="text" helps detect columns by whitespace (borderless)
            # horizontal_strategy="text" helps detect rows by text alignment
            tables_on_page = page.extract_tables(table_settings={
                "vertical_strategy": "text", 
                "horizontal_strategy": "text",
                "snap_tolerance": 3,
            })
            
            # If no table is found on this page, and we were building a table, 
            # assume the previous table has ended.
            if not tables_on_page:
                if current_table_data:
                    all_tables.append(current_table_data)
                    current_table_data = []
                continue

            for table in tables_on_page:
                # Clean the table data (remove None or empty strings if needed)
                cleaned_table = [[cell.strip() if cell else "" for cell in row] for row in table]
                
                # LOGIC: Deciding if this is a new table or a continuation
                if not current_table_data:
                    # Case 1: No current table is being built. Start a new one.
                    current_table_data = cleaned_table
                else:
                    # Case 2: We have a table in progress. Check if columns match.
                    # We compare the number of columns in the new chunk vs the current table
                    prev_col_count = len(current_table_data[0])
                    curr_col_count = len(cleaned_table[0])
                    
                    if prev_col_count == curr_col_count:
                        # Columns match! It's likely a continuation.
                        
                        # OPTIONAL: Check for repeated headers.
                        # If the first row of the new chunk is identical to the header of the 
                        # current table, skip it (don't add the header twice).
                        if cleaned_table[0] == current_table_data[0]:
                            current_table_data.extend(cleaned_table[1:])
                        else:
                            current_table_data.extend(cleaned_table)
                    else:
                        # Columns don't match. The previous table is done.
                        all_tables.append(current_table_data)
                        # Start this new table as the "current" one
                        current_table_data = cleaned_table

    # End of loop: Append the final table if one is still in progress
    if current_table_data:
        all_tables.append(current_table_data)

    # Save to CSV
    print(f"\nFound {len(all_tables)} total tables.")
    for idx, table_data in enumerate(all_tables):
        df = pd.DataFrame(table_data)
        
        # Use the first row as header if it looks like a header
        # (This is a simple heuristic; you might need to adjust based on your data)
        new_header = df.iloc[0] 
        df = df[1:] 
        df.columns = new_header
        
        filename = f"extracted_table_{idx+1}.csv"
        df.to_csv(filename, index=False)
        print(f"Saved: {filename}")

# Run the function
extract_and_save_tables("your_file.pdf")
