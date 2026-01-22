"""
PDF Table Extractor - Handles borderless tables and tables spanning multiple pages
"""
import pdfplumber
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any


class PDFTableExtractor:
    def __init__(self, pdf_path: str, output_dir: str = "extracted_tables"):
        self.pdf_path = pdf_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def extract_tables_standard(self, save_csv: bool = True) -> List[pd.DataFrame]:
        """
        Extract tables using standard pdfplumber method.
        Works well for tables with borders.
        """
        all_tables = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            print(f"Processing {len(pdf.pages)} pages...")
            
            for page_num, page in enumerate(pdf.pages, start=1):
                print(f"Page {page_num}...")
                tables = page.extract_tables()
                
                for table_num, table in enumerate(tables):
                    if table and len(table) > 1:  # Has headers and data
                        # Convert to DataFrame
                        df = pd.DataFrame(table[1:], columns=table[0])
                        # Clean empty columns/rows
                        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
                        
                        if not df.empty:
                            all_tables.append({
                                'page': page_num,
                                'table_num': table_num + 1,
                                'dataframe': df
                            })
                            print(f"  - Found table {table_num + 1}: {df.shape[0]} rows x {df.shape[1]} cols")
        
        if save_csv:
            self._save_tables_to_csv(all_tables)
        
        return [t['dataframe'] for t in all_tables]
    
    def extract_tables_borderless(self, save_csv: bool = True) -> List[pd.DataFrame]:
        """
        Extract tables including borderless tables using custom table settings.
        More aggressive at finding tables without clear borders.
        """
        all_tables = []
        
        # Custom table extraction settings for borderless tables
        table_settings = {
            "vertical_strategy": "text",  # Use text alignment instead of lines
            "horizontal_strategy": "text",
            "explicit_vertical_lines": [],
            "explicit_horizontal_lines": [],
            "snap_tolerance": 3,
            "join_tolerance": 3,
            "edge_min_length": 3,
            "min_words_vertical": 3,
            "min_words_horizontal": 1,
            "intersection_tolerance": 3,
        }
        
        with pdfplumber.open(self.pdf_path) as pdf:
            print(f"Processing {len(pdf.pages)} pages with borderless table detection...")
            
            for page_num, page in enumerate(pdf.pages, start=1):
                print(f"Page {page_num}...")
                
                # Try with custom settings
                tables = page.extract_tables(table_settings=table_settings)
                
                for table_num, table in enumerate(tables):
                    if table and len(table) > 1:
                        df = pd.DataFrame(table[1:], columns=table[0])
                        df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
                        
                        if not df.empty:
                            all_tables.append({
                                'page': page_num,
                                'table_num': table_num + 1,
                                'dataframe': df
                            })
                            print(f"  - Found table {table_num + 1}: {df.shape[0]} rows x {df.shape[1]} cols")
        
        if save_csv:
            self._save_tables_to_csv(all_tables, prefix="borderless")
        
        return [t['dataframe'] for t in all_tables]
    
    def extract_and_merge_spanning_tables(self, save_csv: bool = True) -> List[pd.DataFrame]:
        """
        Extract tables and attempt to merge tables that span multiple pages.
        Uses heuristics to detect table continuations.
        """
        all_tables = []
        page_tables = []
        
        with pdfplumber.open(self.pdf_path) as pdf:
            print(f"Processing {len(pdf.pages)} pages and merging spanning tables...")
            
            # First pass: extract all tables with page info
            for page_num, page in enumerate(pdf.pages, start=1):
                tables = page.extract_tables()
                
                for table_num, table in enumerate(tables):
                    if table and len(table) > 0:
                        page_tables.append({
                            'page': page_num,
                            'table_num': table_num,
                            'raw_table': table
                        })
        
        # Second pass: merge tables that likely span pages
        merged_tables = []
        skip_indices = set()
        
        for i, current in enumerate(page_tables):
            if i in skip_indices:
                continue
                
            current_table = current['raw_table']
            current_page = current['page']
            
            # Check if next table(s) might be continuation
            merged_table = current_table.copy()
            
            for j in range(i + 1, len(page_tables)):
                if j in skip_indices:
                    continue
                    
                next_table = page_tables[j]
                
                # Heuristic: tables on consecutive pages with same column count
                # might be continuations
                if (next_table['page'] == current_page + (j - i) and
                    len(next_table['raw_table'][0]) == len(current_table[0])):
                    
                    # Check if first row of next table looks like a header
                    # (if it matches current header, it's likely continuation)
                    if self._is_table_continuation(merged_table, next_table['raw_table']):
                        print(f"Merging table from page {current_page} with page {next_table['page']}")
                        # Skip the header row if it's a repeat
                        merged_table.extend(next_table['raw_table'][1:])
                        skip_indices.add(j)
                    else:
                        break
                else:
                    break
            
            # Convert merged table to DataFrame
            if len(merged_table) > 1:
                df = pd.DataFrame(merged_table[1:], columns=merged_table[0])
                df = df.dropna(axis=1, how='all').dropna(axis=0, how='all')
                
                if not df.empty:
                    merged_tables.append({
                        'start_page': current_page,
                        'dataframe': df
                    })
                    print(f"Final merged table from page {current_page}: {df.shape[0]} rows x {df.shape[1]} cols")
        
        if save_csv:
            self._save_merged_tables_to_csv(merged_tables)
        
        return [t['dataframe'] for t in merged_tables]
    
    def _is_table_continuation(self, table1: List[List], table2: List[List]) -> bool:
        """
        Check if table2 is likely a continuation of table1.
        Returns True if headers match or if table2's first row looks like data.
        """
        if not table1 or not table2:
            return False
        
        header1 = table1[0]
        first_row_table2 = table2[0]
        
        # If headers match exactly, it's a continuation
        if header1 == first_row_table2:
            return True
        
        # If headers are similar (allowing for minor differences)
        if len(header1) == len(first_row_table2):
            matches = sum(1 for h1, h2 in zip(header1, first_row_table2) 
                         if h1 and h2 and h1.strip().lower() == h2.strip().lower())
            if matches / len(header1) > 0.7:  # 70% similarity
                return True
        
        return False
    
    def _save_tables_to_csv(self, tables: List[Dict], prefix: str = "table"):
        """Save extracted tables to CSV files."""
        for idx, table_info in enumerate(tables, start=1):
            df = table_info['dataframe']
            page = table_info['page']
            table_num = table_info['table_num']
            
            filename = f"{prefix}_page{page}_table{table_num}.csv"
            filepath = self.output_dir / filename
            df.to_csv(filepath, index=False)
            print(f"Saved: {filename}")
    
    def _save_merged_tables_to_csv(self, tables: List[Dict]):
        """Save merged tables to CSV files."""
        for idx, table_info in enumerate(tables, start=1):
            df = table_info['dataframe']
            start_page = table_info['start_page']
            
            filename = f"merged_table_{idx}_from_page{start_page}.csv"
            filepath = self.output_dir / filename
            df.to_csv(filepath, index=False)
            print(f"Saved: {filename}")
    
    def extract_all_methods(self):
        """
        Run all extraction methods and save results in separate subdirectories.
        Useful for comparing different approaches.
        """
        print("\n" + "="*60)
        print("METHOD 1: Standard Table Extraction")
        print("="*60)
        standard_dir = self.output_dir / "standard"
        standard_dir.mkdir(exist_ok=True)
        original_output_dir = self.output_dir
        self.output_dir = standard_dir
        tables_standard = self.extract_tables_standard()
        
        print("\n" + "="*60)
        print("METHOD 2: Borderless Table Extraction")
        print("="*60)
        borderless_dir = original_output_dir / "borderless"
        borderless_dir.mkdir(exist_ok=True)
        self.output_dir = borderless_dir
        tables_borderless = self.extract_tables_borderless()
        
        print("\n" + "="*60)
        print("METHOD 3: Multi-page Table Merging")
        print("="*60)
        merged_dir = original_output_dir / "merged"
        merged_dir.mkdir(exist_ok=True)
        self.output_dir = merged_dir
        tables_merged = self.extract_and_merge_spanning_tables()
        
        self.output_dir = original_output_dir
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Standard extraction: {len(tables_standard)} tables")
        print(f"Borderless extraction: {len(tables_borderless)} tables")
        print(f"Merged extraction: {len(tables_merged)} tables")
        print(f"\nAll results saved in: {self.output_dir}")


def main():
    """
    Example usage
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python extract_pdf_tables.py <pdf_file_path> [output_directory]")
        print("\nExample: python extract_pdf_tables.py document.pdf extracted_tables")
        sys.exit(1)
    
    pdf_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "extracted_tables"
    
    extractor = PDFTableExtractor(pdf_file, output_dir)
    
    print(f"Extracting tables from: {pdf_file}")
    print(f"Output directory: {output_dir}\n")
    
    # Run all methods to compare results
    extractor.extract_all_methods()


if __name__ == "__main__":
    main()
