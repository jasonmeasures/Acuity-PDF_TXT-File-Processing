"""
Commercial Invoice Processor Web Service
Processes commercial invoices and matches HTS codes
"""

from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import pandas as pd
import os
import io
import time
import glob
from datetime import datetime
from werkzeug.utils import secure_filename
import PyPDF2
import re
import pytesseract
from pdf2image import convert_from_path
from PIL import Image

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'csv'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def cleanup_old_files(directory, days_old=7):
    """
    Remove files older than specified days from a directory
    
    Args:
        directory: Path to directory to clean
        days_old: Number of days old before file is deleted (default: 7)
    """
    if not os.path.exists(directory):
        return 0, 0
    
    current_time = time.time()
    cutoff_time = current_time - (days_old * 24 * 60 * 60)  # Convert days to seconds
    
    removed_count = 0
    total_size_removed = 0
    
    for file_path in glob.glob(os.path.join(directory, '*')):
        if os.path.isfile(file_path):
            file_stat = os.stat(file_path)
            
            # Check if file is older than cutoff
            if file_stat.st_mtime < cutoff_time:
                file_size = file_stat.st_size
                os.remove(file_path)
                removed_count += 1
                total_size_removed += file_size
    
    return removed_count, total_size_removed


def extract_text_from_pdf(file_path):
    """Extract text from PDF file using PyPDF2 first, then OCR if needed"""
    try:
        # First try PyPDF2 for text-based PDFs
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        
        # If no text was extracted, try OCR
        if not text.strip():
            print("No text found with PyPDF2, trying OCR...")
            try:
                # Convert PDF to images
                images = convert_from_path(file_path, dpi=300)
                ocr_text = ""
                
                for i, image in enumerate(images):
                    print(f"Processing page {i+1}/{len(images)} with OCR...")
                    # Use OCR to extract text from image
                    page_text = pytesseract.image_to_string(image, lang='eng')
                    ocr_text += page_text + "\n"
                
                text = ocr_text.strip()
                print(f"OCR extracted {len(text)} characters")
                
            except Exception as ocr_error:
                print(f"OCR failed: {ocr_error}")
                return ""
        
        return text.strip()
        
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""

def extract_text_from_txt(file_path):
    """Extract text from TXT file with robust encoding handling"""
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-16', 'utf-32']
    
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read().strip()
                print(f"Successfully read TXT file with {encoding} encoding")
                return content
        except (UnicodeDecodeError, UnicodeError) as e:
            print(f"Failed to read with {encoding}: {e}")
            continue
    
    # If all encodings fail, try with error handling
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
            content = file.read().strip()
            print("Read TXT file with UTF-8 and error replacement")
            return content
    except Exception as e:
        print(f"All encoding attempts failed: {e}")
        return ""

def parse_invoice_from_text(text):
    """Parse invoice data from unstructured text"""
    data = {}
    
    # Enhanced invoice patterns for your specific format
    patterns = {
        'invoice_number': [
            r'(\d{3,}[A-Z]-\d{8,})',  # Pattern like 074M-22005749
            r'(\d{3,}[A-Z]\d{8,})',   # Pattern like 074M22005749
            r'Invoice[:\s#]*([A-Z0-9-]+)',
        ],
        'invoice_date': [
            r'(\d{1,2}[A-Za-z]{3}/\d{2}/\d{4})',  # Pattern like 21Oct/2025
            r'Date[:\s]*([0-9/-]+)',
        ],
        'seller_name': [
            r'([A-Za-z\s&.,]+(?:S\.\s*de\s*RL\s*de\s*CV|INC|CORP|LLC|LTD))',  # Company names
            r'(?:Seller|From|Exporter)[:\s]*([^\n]+)',
        ],
        'buyer_name': [
            r'(?:Buyer|To|Importer)[:\s]*([^\n]+)',
        ],
        'total_amount': [
            r'Total[:\s]*\$?([0-9,]+\.?[0-9]*)',
            r'\$([0-9,]+\.?[0-9]*)',  # Any dollar amount
        ],
        'currency': [
            r'Currency[:\s]*([A-Z]{3})',
            r'\b(USD|MXN|CAD)\b',  # Common currencies
        ],
        'country_origin': [
            r'([A-Z]{2})\s+[A-Z]{3}\s+[A-Z]',  # Pattern like "MX NIO D"
            r'(?:Country of Origin|Origin)[:\s]*([^\n]+)',
        ],
        'country_destination': [
            r'(?:Country of Destination|Destination)[:\s]*([^\n]+)',
        ],
        'terms': [
            r'(?:Terms|Payment Terms|INCOTERM)[:\s]*([^\n]+)',
        ],
    }
    
    for field, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                data[field] = match.group(1).strip()
                break
    
    # Extract part numbers from PDF text, excluding the invoice number if found
    invoice_num = data.get('invoice_number')
    data['part_numbers'] = extract_part_numbers_from_text(text, invoice_number=invoice_num)
    
    return data

def extract_part_numbers_from_text(text, invoice_number=None):
    """
    Extract part numbers from text content with improved filtering
    
    Args:
        text: Text content to extract part numbers from
        invoice_number: Optional invoice number to exclude from results
    
    Returns:
        List of filtered part numbers
    """
    part_numbers = []
    
    # More specific part number patterns based on your actual data
    patterns = [
        r'\*([A-Z0-9]{6,7})\b',             # Pattern like *214N53, *183NK5
        r'\b([A-Z]{2,}\d{4,})\b',           # Pattern like COMP001, MEM002
        r'\b(\d{4,}[A-Z]{2,})\b',           # Pattern like 001COMP, 002MEM
        r'\b([A-Z]{1,3}\d{3,6})\b',         # Pattern like A123, AB1234
        r'\b(\d{3,6}[A-Z]{1,3})\b',         # Pattern like 123A, 1234AB
        # More specific patterns for actual part numbers
        r'\b([A-Z]{2,3}\d{3,4}[A-Z]{1,2})\b',  # Pattern like 214N53, 222A7C
        r'\b(\d{3,4}[A-Z]{2,3}\d{1,2})\b',     # Pattern like 253G2M, 2575L7
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text)
        part_numbers.extend(matches)
    
    # Build dynamic invoice number filter patterns
    invoice_patterns = []
    if invoice_number:
        # Add the exact invoice number and variations
        invoice_patterns.append(invoice_number.upper())
        # Remove dashes and add that variation
        invoice_patterns.append(invoice_number.replace('-', '').upper())
        # Extract just the numeric part if it has a pattern like 074M-22006670
        numeric_match = re.search(r'(\d{8,})', invoice_number)
        if numeric_match:
            invoice_patterns.append(numeric_match.group(1))
        # Extract prefix part (like 074M)
        prefix_match = re.search(r'^(\d{3,}[A-Z]+)', invoice_number)
        if prefix_match:
            invoice_patterns.append(prefix_match.group(1))
    
    # Remove duplicates and filter out common false positives
    filtered_numbers = []
    for num in set(part_numbers):
        # Skip if matches invoice number or its variations
        if invoice_number and any(
            inv_pattern in num.upper() or 
            num.upper() in inv_pattern or
            num.upper() == inv_pattern
            for inv_pattern in invoice_patterns
        ):
            continue
        # More comprehensive filtering (removed specific invoice numbers - now handled dynamically above)
        if not any(false_positive in num.upper() for false_positive in 
                  ['USD', 'FOB', 'NET', 'TOTAL', 'DATE', 'INVOICE', 'QUANTITY', 'MX', 'US', 
                   'PAGE', 'ENTRY', 'PORT', 'VALUE', 'RATE', 'DUTY', 'PACKING', 'WEIGHT',
                   'ORIGIN', 'DESTINATION', 'CURRENCY', 'TERMS', 'PAYMENT', 'FREIGHT',
                   'CARRIER', 'TRUCK', 'CHARGE', 'INCOTERM', 'RECORD', 'IMPORTER',
                   'SUMMARY', 'DESCRIPTION', 'CONTROLLERS', 'SENSOR', 'RELAY', 'FIXTURE',
                   'LIGHTING', 'LIGHT', 'WALL', 'CEILING', 'MOTION', 'OCCUPATION',
                   'PROGRAMMABLE', 'PALLETS', 'BUNDLES', 'PACK', 'UNIT', 'TYPE',
                   'NUMBER', 'PART', 'GROSS', 'LOCAL', 'ESTIMATED', 'PKGS', 'DUTIABLE',
                   'VENDOR', 'BRANDS', 'ACUITY', 'CALIFORNIA', 'TEXAS', 'GEORGIA',
                   'ATLANTA', 'LAREDO', 'GUADALUPE', 'LEON', 'NUEVO', 'ENLACE',
                   'PARQUE', 'PLANTA', 'SILLA', 'LASILLA', 'ARQUE', 'AARQUE',
                   'PEACHTREE', 'SUITE', 'STREET', 'BASE', 'METAL', 'PLASTIC',
                   'GLASS', 'BRASS', 'CHANNEL', 'FITTINGS', 'LUMINAIRES', 'PARTS',
                   'ONLY', 'ROAD', 'EXPRESS', 'GATEWAY', 'SOUTH', 'PLAINES',
                   'JUNO', 'WOLF', 'KALOS', 'KGGR', 'KGNT', '58PM', '36PM',
                   'ABL941020S81', '1C926', '1C22', 'NPP20', 'LSXR', 'J100',
                   'WRDC', 'ND98413', '2633371', '252829']):
            # Additional filtering for pure numbers (likely not part numbers)
            if not (num.isdigit() and len(num) <= 4):
                filtered_numbers.append(num)
    
    return filtered_numbers

def combine_document_data(pdf_data, txt_data):
    """Combine PDF and TXT data intelligently"""
    combined = {}
    
    # Start with PDF data
    if pdf_data:
        combined.update(pdf_data)
    
    # Override/merge with TXT data where available
    if txt_data:
        for key, value in txt_data.items():
            if value and value != 'N/A' and value.strip():
                combined[key] = value
    
    return combined

def extract_part_numbers_from_txt_file(file_path):
    """Extract part numbers from TXT file's PART column"""
    try:
        # Try to read as structured data first with different encodings
        df = None
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-16', 'utf-32']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, sep='\t', index_col=False, encoding=encoding)
                print(f"Successfully read TXT file for part numbers with {encoding} encoding")
                break
            except Exception as e:
                print(f"Failed to read TXT file with {encoding}: {e}")
                continue
        
        if df is not None and 'PART' in df.columns:
            part_numbers = df['PART'].dropna().astype(str).tolist()
            # Filter out empty strings and clean up
            part_numbers = [p.strip() for p in part_numbers if p.strip() and p.strip() != 'nan']
            print(f"Extracted {len(part_numbers)} part numbers from TXT file")
            return part_numbers
        else:
            print("No PART column found in TXT file")
    except Exception as e:
        print(f"Error reading TXT file for part numbers: {e}")
    
    # If structured parsing fails, try to extract from unstructured text
    try:
        content = extract_text_from_txt(file_path)
        part_numbers = extract_part_numbers_from_text(content)
        print(f"Extracted {len(part_numbers)} part numbers from unstructured text")
        return part_numbers
    except Exception as e:
        print(f"Error extracting part numbers from text: {e}")
        return []

def match_files_by_part_numbers(pdf_files, txt_files):
    """Match PDF and TXT files based on part numbers found in content"""
    matches = []
    
    for pdf_file in pdf_files:
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(pdf_file['filepath'])
        pdf_part_numbers = extract_part_numbers_from_text(pdf_text)
        
        best_match = None
        max_matches = 0
        
        # If PDF has no extractable text, match with any available TXT file
        if not pdf_part_numbers:
            # For PDFs without text, match with the first available TXT file
            if txt_files:
                best_match = txt_files[0]  # Take the first TXT file as default
                max_matches = 1  # Indicate it's a fallback match
        
        # Try to match based on part numbers if PDF has text
        if not best_match:
            for txt_file in txt_files:
                # Extract part numbers from TXT file
                txt_part_numbers = extract_part_numbers_from_txt_file(txt_file['filepath'])
                
                # Normalize part numbers for comparison (remove asterisks and convert to uppercase)
                pdf_normalized = {p.replace('*', '').upper() for p in pdf_part_numbers}
                txt_normalized = {p.replace('*', '').upper() for p in txt_part_numbers}
                
                # Count matching part numbers
                matches_count = len(pdf_normalized & txt_normalized)
                
                if matches_count > max_matches:
                    max_matches = matches_count
                    best_match = txt_file
        
        matches.append({
            'pdf': pdf_file,
            'txt': best_match,
            'match_score': max_matches,
            'pdf_parts': pdf_part_numbers,
            'txt_parts': extract_part_numbers_from_txt_file(best_match['filepath']) if best_match else [],
            'pdf_has_text': len(pdf_part_numbers) > 0
        })
    
    return matches

def process_invoice_data(file_path, file_type, invoice_number=None):
    """
    Process invoice data from various file types
    
    Args:
        file_path: Path to the file
        file_type: Type of file ('txt', 'pdf', 'csv')
        invoice_number: Optional invoice number for filtering
        
    Returns:
        DataFrame with formatted output
    """
    
    if file_type == 'pdf':
        # Extract text from PDF and parse metadata
        # NOTE: PDF files contain invoice metadata but not detailed line items
        # Line items should come from the paired TXT file
        # Return empty DataFrame - actual line items will come from TXT file
        text = extract_text_from_pdf(file_path)
        parsed_data = parse_invoice_from_text(text)
        
        # Log extracted invoice metadata for debugging
        print(f"PDF Invoice Number: {parsed_data.get('invoice_number', 'N/A')}")
        print(f"PDF Seller: {parsed_data.get('seller_name', 'Unknown')}")
        print(f"PDF Country: {parsed_data.get('country_origin', 'N/A')}")
        
        # Return empty DataFrame - do NOT create a line item from invoice metadata
        # The paired TXT file will provide the actual line items
        return pd.DataFrame(columns=[
            'SKU', 'DESCRIPTION', 'HTS', 'COUNTRY OF ORIGIN', 'NO. OF PACKAGE',
            'QUANTITY', 'NET WEIGHT', 'GROSS WEIGHT', 'UNIT PRICE', 'VALUE', 'QTY UNIT'
        ])
    
    elif file_type == 'txt':
        # Check if it's structured tab-delimited data or unstructured text
        try:
            # Try to read as tab-delimited first with different encodings
            txt_df = None
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-16', 'utf-32']
            
            for encoding in encodings:
                try:
                    txt_df = pd.read_csv(file_path, sep='\t', index_col=False, encoding=encoding)
                    print(f"Successfully read TXT file for processing with {encoding} encoding")
                    break
                except Exception as e:
                    print(f"Failed to read TXT file with {encoding}: {e}")
                    continue
            
            if txt_df is None:
                raise Exception("Could not read file with any encoding")
            
            # If successful, process as structured data
            if invoice_number:
                txt_df = txt_df[txt_df['invoice_nbr'] == invoice_number]
            
            output_data = []
            for idx, row in txt_df.iterrows():
                qty = float(row['quantity']) if pd.notna(row['quantity']) else 0.0
                unit_price = float(row['AMT']) if pd.notna(row['AMT']) else 0.0
                weight = float(row['WEIGHT']) if pd.notna(row['WEIGHT']) else 0.0
                
                output_data.append({
                    'SKU': str(row['PART']).strip(),
                    'DESCRIPTION': str(row['PART_DESC']).strip(),
                    'HTS': str(row['HTTS']).strip(),
                    'COUNTRY OF ORIGIN': str(row['C/N']).strip(),
                    'NO. OF PACKAGE': '',
                    'QUANTITY': qty,
                    'NET WEIGHT': weight,
                    'GROSS WEIGHT': weight,
                    'UNIT PRICE': unit_price,
                    'VALUE': qty * unit_price,
                    'QTY UNIT': 'EA'
                })
            
            return pd.DataFrame(output_data)
            
        except Exception:
            # If tab-delimited parsing fails, treat as unstructured text
            text = extract_text_from_txt(file_path)
            parsed_data = parse_invoice_from_text(text)
            
            output_data = [{
                'SKU': parsed_data.get('invoice_number', 'N/A'),
                'DESCRIPTION': f"Invoice from {parsed_data.get('seller_name', 'Unknown')}",
                'HTS': 'N/A',
                'COUNTRY OF ORIGIN': parsed_data.get('country_origin', 'N/A'),
                'NO. OF PACKAGE': '1',
                'QUANTITY': 1,
                'NET WEIGHT': 0.0,
                'GROSS WEIGHT': 0.0,
                'UNIT PRICE': float(parsed_data.get('total_amount', '0').replace(',', '')) if parsed_data.get('total_amount') else 0.0,
                'VALUE': float(parsed_data.get('total_amount', '0').replace(',', '')) if parsed_data.get('total_amount') else 0.0,
                'QTY UNIT': 'EA'
            }]
            
            return pd.DataFrame(output_data)
    
    elif file_type == 'csv':
        # Process CSV files
        csv_df = pd.read_csv(file_path, index_col=False)
        
        if invoice_number:
            csv_df = csv_df[csv_df['invoice_nbr'] == invoice_number]
        
        output_data = []
        for idx, row in csv_df.iterrows():
            qty = float(row.get('quantity', 0)) if pd.notna(row.get('quantity', 0)) else 0.0
            unit_price = float(row.get('AMT', 0)) if pd.notna(row.get('AMT', 0)) else 0.0
            weight = float(row.get('WEIGHT', 0)) if pd.notna(row.get('WEIGHT', 0)) else 0.0
            
            output_data.append({
                'SKU': str(row.get('PART', '')).strip(),
                'DESCRIPTION': str(row.get('PART_DESC', '')).strip(),
                'HTS': str(row.get('HTTS', '')).strip(),
                'COUNTRY OF ORIGIN': str(row.get('C/N', '')).strip(),
                'NO. OF PACKAGE': '',
                'QUANTITY': qty,
                'NET WEIGHT': weight,
                'GROSS WEIGHT': weight,
                'UNIT PRICE': unit_price,
                'VALUE': qty * unit_price,
                'QTY UNIT': 'EA'
            })
        
        return pd.DataFrame(output_data)
    
    else:
        raise ValueError(f"Unsupported file type: {file_type}")


def format_dataframe_for_csv(df):
    """
    Format DataFrame to ensure numeric columns are properly typed and formatted
    for CSV export without scientific notation or text formatting issues.
    
    Args:
        df: DataFrame to format
        
    Returns:
        Formatted DataFrame with proper numeric types
    """
    df_formatted = df.copy()
    
    # Define numeric columns that should be properly formatted
    numeric_columns = ['QUANTITY', 'NET WEIGHT', 'GROSS WEIGHT', 'UNIT PRICE', 'VALUE']
    
    # Ensure numeric columns are properly typed as float
    for col in numeric_columns:
        if col in df_formatted.columns:
            # Convert to numeric, coercing errors to NaN, then fill NaN with 0
            df_formatted[col] = pd.to_numeric(df_formatted[col], errors='coerce').fillna(0.0)
            # Ensure it's float type
            df_formatted[col] = df_formatted[col].astype(float)
    
    # Ensure 'NO. OF PACKAGE' is string (can be empty or number)
    if 'NO. OF PACKAGE' in df_formatted.columns:
        df_formatted['NO. OF PACKAGE'] = df_formatted['NO. OF PACKAGE'].astype(str)
    
    return df_formatted


def format_number_for_csv(value):
    """
    Format a number for CSV export, removing trailing zeros and ensuring no scientific notation.
    
    Args:
        value: Numeric value to format
        
    Returns:
        String representation of the number without trailing zeros
    """
    if pd.isna(value):
        return '0'
    
    # Convert to float to ensure proper handling
    try:
        num_value = float(value)
    except (ValueError, TypeError):
        return '0'
    
    # Handle zero case
    if num_value == 0:
        return '0'
    
    # Format with enough precision, then remove trailing zeros
    formatted = f'{num_value:.10f}'
    # Remove trailing zeros and decimal point if not needed
    formatted = formatted.rstrip('0').rstrip('.')
    return formatted if formatted else '0'


def write_csv_with_proper_formatting(df, output_path):
    """
    Write DataFrame to CSV with proper number formatting to avoid scientific notation.
    Formats numbers as plain decimals without scientific notation, ensuring they remain
    as numeric values (not text) in the CSV. Removes unnecessary trailing zeros.
    Ensures columns are in the correct order.
    
    Args:
        df: DataFrame to write
        output_path: Path where CSV file should be written
    """
    # Define the correct column order
    correct_column_order = [
        'SKU',
        'DESCRIPTION',
        'HTS',
        'COUNTRY OF ORIGIN',
        'NO. OF PACKAGE',
        'QUANTITY',
        'NET WEIGHT',
        'GROSS WEIGHT',
        'UNIT PRICE',
        'VALUE',
        'QTY UNIT'
    ]
    
    # Format the DataFrame first to ensure proper numeric types
    df_formatted = format_dataframe_for_csv(df)
    
    # Reorder columns to match the correct order (only include columns that exist)
    existing_columns = [col for col in correct_column_order if col in df_formatted.columns]
    # Add any remaining columns that weren't in the expected order
    remaining_columns = [col for col in df_formatted.columns if col not in correct_column_order]
    df_formatted = df_formatted[existing_columns + remaining_columns]
    
    # Format numeric columns to remove trailing zeros while keeping them as numbers
    numeric_cols = ['QUANTITY', 'NET WEIGHT', 'GROSS WEIGHT', 'UNIT PRICE', 'VALUE']
    df_to_write = df_formatted.copy()
    
    for col in numeric_cols:
        if col in df_to_write.columns:
            # Apply formatting to remove trailing zeros
            df_to_write[col] = df_to_write[col].apply(format_number_for_csv)
    
    # Write CSV - numbers will be written as plain decimals without scientific notation
    df_to_write.to_csv(output_path, index=False)


def aggregate_by_sku(df):
    """
    Aggregate data by SKU, summing quantities, weights, and values.
    
    Args:
        df: DataFrame with invoice data
        
    Returns:
        Aggregated DataFrame grouped by SKU with columns in correct order
    """
    if df.empty:
        return df
    
    # Define the correct column order
    correct_column_order = [
        'SKU',
        'DESCRIPTION',
        'HTS',
        'COUNTRY OF ORIGIN',
        'NO. OF PACKAGE',
        'QUANTITY',
        'NET WEIGHT',
        'GROSS WEIGHT',
        'UNIT PRICE',
        'VALUE',
        'QTY UNIT'
    ]
    
    # Group by SKU and aggregate numeric columns
    agg_dict = {
        'QUANTITY': 'sum',
        'NET WEIGHT': 'sum',
        'GROSS WEIGHT': 'sum',
        'UNIT PRICE': 'mean',  # Average unit price (will be recalculated)
        'VALUE': 'sum',
        'NO. OF PACKAGE': 'sum' if 'NO. OF PACKAGE' in df.columns else 'first'
    }
    
    # Keep first occurrence of non-numeric columns
    non_numeric_cols = ['DESCRIPTION', 'HTS', 'COUNTRY OF ORIGIN', 'QTY UNIT']
    for col in non_numeric_cols:
        if col in df.columns:
            agg_dict[col] = 'first'
    
    aggregated = df.groupby('SKU', as_index=False).agg(agg_dict)
    
    # Recalculate unit price based on aggregated values
    # Unit price = total value / total quantity
    mask = aggregated['QUANTITY'] > 0
    aggregated.loc[mask, 'UNIT PRICE'] = aggregated.loc[mask, 'VALUE'] / aggregated.loc[mask, 'QUANTITY']
    
    # Reorder columns to match the correct order (only include columns that exist)
    existing_columns = [col for col in correct_column_order if col in aggregated.columns]
    # Add any remaining columns that weren't in the expected order
    remaining_columns = [col for col in aggregated.columns if col not in correct_column_order]
    aggregated = aggregated[existing_columns + remaining_columns]
    
    return aggregated


def generate_summary(df, invoice_number, include_aggregated=False):
    """
    Generate processing summary statistics
    
    Args:
        df: DataFrame with invoice data
        invoice_number: Invoice number
        include_aggregated: If True, also return aggregated summary
        
    Returns:
        Dictionary with summary statistics
    """
    # Helper function to safely get top HTS codes
    def get_top_hts_codes(df):
        if 'HTS' not in df.columns or 'VALUE' not in df.columns:
            return {}
        try:
            # Ensure VALUE is numeric
            df_copy = df.copy()
            df_copy['VALUE'] = pd.to_numeric(df_copy['VALUE'], errors='coerce').fillna(0.0)
            # Group by HTS and sum values, then get top 5
            grouped = df_copy.groupby('HTS')['VALUE'].sum()
            # Ensure the result is numeric before using nlargest
            if grouped.dtype == 'object':
                grouped = pd.to_numeric(grouped, errors='coerce').fillna(0.0)
            return grouped.nlargest(5).to_dict()
        except Exception as e:
            print(f"Error getting top HTS codes: {e}")
            return {}
    
    # Helper function to safely get quantity by SKU
    def get_quantity_by_sku(df):
        if 'SKU' not in df.columns or 'QUANTITY' not in df.columns:
            return {}
        try:
            # Ensure QUANTITY is numeric
            df_copy = df.copy()
            df_copy['QUANTITY'] = pd.to_numeric(df_copy['QUANTITY'], errors='coerce').fillna(0.0)
            grouped = df_copy.groupby('SKU')['QUANTITY'].sum()
            # Ensure the result is numeric
            if grouped.dtype == 'object':
                grouped = pd.to_numeric(grouped, errors='coerce').fillna(0.0)
            return grouped.to_dict()
        except Exception as e:
            print(f"Error getting quantity by SKU: {e}")
            return {}
    
    summary = {
        'invoice_number': invoice_number,
        'timestamp': datetime.now().isoformat(),
        'total_lines': len(df),
        'total_quantity': float(pd.to_numeric(df['QUANTITY'], errors='coerce').fillna(0.0).sum()) if 'QUANTITY' in df.columns else 0.0,
        'total_net_weight': float(pd.to_numeric(df['NET WEIGHT'], errors='coerce').fillna(0.0).sum()) if 'NET WEIGHT' in df.columns else 0.0,
        'total_gross_weight': float(pd.to_numeric(df['GROSS WEIGHT'], errors='coerce').fillna(0.0).sum()) if 'GROSS WEIGHT' in df.columns else 0.0,
        'total_value': float(pd.to_numeric(df['VALUE'], errors='coerce').fillna(0.0).sum()) if 'VALUE' in df.columns else 0.0,
        'unique_hts_codes': int(df['HTS'].nunique()) if 'HTS' in df.columns else 0,
        'unique_skus': int(df['SKU'].nunique()) if 'SKU' in df.columns else 0,
        'countries': df['COUNTRY OF ORIGIN'].value_counts().to_dict() if 'COUNTRY OF ORIGIN' in df.columns else {},
        'top_hts_codes': get_top_hts_codes(df),
        'quantity_by_sku': get_quantity_by_sku(df)
    }
    
    if include_aggregated:
        aggregated_df = aggregate_by_sku(df)
        summary['aggregated'] = {
            'total_lines': len(aggregated_df),
            'total_quantity': float(aggregated_df['QUANTITY'].sum()) if 'QUANTITY' in aggregated_df.columns else 0.0,
            'total_value': float(aggregated_df['VALUE'].sum()) if 'VALUE' in aggregated_df.columns else 0.0,
            'unique_skus': int(aggregated_df['SKU'].nunique()) if 'SKU' in aggregated_df.columns else 0
        }
    
    return summary


@app.route('/')
def index():
    """Serve the enhanced main page"""
    return render_template('enhanced_index.html')

@app.route('/legacy')
def legacy_index():
    """Serve the legacy single file processing page"""
    return render_template('index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/cleanup', methods=['POST'])
def manual_cleanup():
    """Manually trigger cleanup of old files"""
    try:
        days = request.json.get('days', 7) if request.is_json else 7
        
        uploads_removed, uploads_size = cleanup_old_files(UPLOAD_FOLDER, days_old=days)
        outputs_removed, outputs_size = cleanup_old_files(OUTPUT_FOLDER, days_old=days)
        
        total_files = uploads_removed + outputs_removed
        total_size = uploads_size + outputs_size
        total_mb = total_size / (1024 * 1024)
        
        return jsonify({
            'success': True,
            'uploads_removed': uploads_removed,
            'outputs_removed': outputs_removed,
            'total_files_removed': total_files,
            'total_size_removed_mb': round(total_mb, 2),
            'message': f'Cleaned up {total_files} files ({total_mb:.2f} MB)'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/upload-files', methods=['POST'])
def upload_multiple_files():
    """Handle multiple file uploads for PDF and TXT files"""
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files or all(file.filename == '' for file in files):
            return jsonify({'error': 'No files selected'}), 400
        
        uploaded_files = []
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_type = filename.rsplit('.', 1)[1].lower()
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                saved_filename = f"{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
                file.save(filepath)
                
                uploaded_files.append({
                    'filename': filename,
                    'saved_filename': saved_filename,
                    'filepath': filepath,
                    'type': file_type
                })
        
        return jsonify({
            'message': f'Successfully uploaded {len(uploaded_files)} files',
            'files': uploaded_files
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/match-files-by-parts', methods=['POST'])
def match_files_by_parts():
    """Match PDF and TXT files based on part numbers found in content"""
    try:
        data = request.json
        pdf_files = data.get('pdf_files', [])
        txt_files = data.get('txt_files', [])
        
        if not pdf_files or not txt_files:
            return jsonify({'error': 'Both PDF and TXT files are required'}), 400
        
        matches = match_files_by_part_numbers(pdf_files, txt_files)
        
        return jsonify({
            'matches': matches,
            'message': f'Found {len([m for m in matches if m["txt"]])} file matches based on part numbers'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process-combined', methods=['POST'])
def process_combined_files():
    """Process multiple files and combine their data"""
    try:
        data = request.json
        file_pairs = data.get('file_pairs', [])
        invoice_number = data.get('invoice_number', None)
        
        if not file_pairs:
            return jsonify({'error': 'No file pairs provided'}), 400
        
        all_results = []
        combined_summary = {
            'total_files_processed': 0,
            'total_line_items': 0,
            'total_value': 0.0,
            'file_types': {},
            'processing_timestamp': datetime.now().isoformat()
        }
        
        for pair in file_pairs:
            pdf_file = pair.get('pdf')
            txt_file = pair.get('txt')
            
            if not pdf_file:
                return jsonify({'error': 'PDF file is required for each pair'}), 400
            
            # Process PDF file
            pdf_df = process_invoice_data(pdf_file['filepath'], pdf_file['type'], invoice_number)
            
            # Process TXT file if provided
            txt_df = pd.DataFrame()
            if txt_file:
                txt_df = process_invoice_data(txt_file['filepath'], txt_file['type'], invoice_number)
            
            # Combine data from both files
            if not txt_df.empty:
                # Merge DataFrames, preferring TXT data where available
                combined_df = pdf_df.copy()
                for idx, row in txt_df.iterrows():
                    # Add TXT data as additional rows or update existing
                    combined_df = pd.concat([combined_df, row.to_frame().T], ignore_index=True)
            else:
                combined_df = pdf_df
            
            if not combined_df.empty:
                all_results.append(combined_df)
                combined_summary['total_line_items'] += len(combined_df)
                combined_summary['total_value'] += combined_df['VALUE'].sum()
                
                # Track file types
                file_type = f"{pdf_file['type']}"
                if txt_file:
                    file_type += f"+{txt_file['type']}"
                combined_summary['file_types'][file_type] = combined_summary['file_types'].get(file_type, 0) + 1
        
        if not all_results:
            return jsonify({'error': 'No data found in any files'}), 404
        
        # Combine all results into single DataFrame
        final_df = pd.concat(all_results, ignore_index=True)
        combined_summary['total_files_processed'] = len(file_pairs)
        combined_summary['total_quantity'] = float(final_df['QUANTITY'].sum()) if 'QUANTITY' in final_df.columns else 0.0
        
        # Generate aggregated data
        aggregated_df = aggregate_by_sku(final_df)
        
        # Extract invoice number from first PDF if not provided
        if not invoice_number and file_pairs:
            try:
                first_pdf = file_pairs[0].get('pdf')
                if first_pdf:
                    text = extract_text_from_pdf(first_pdf['filepath'])
                    parsed_data = parse_invoice_from_text(text)
                    invoice_number = parsed_data.get('invoice_number', None)
                    print(f"Extracted invoice number from PDF: {invoice_number}")
            except Exception as e:
                print(f"Could not extract invoice number from PDF: {e}")
        
        # Generate summary with aggregated data
        summary = generate_summary(final_df, invoice_number or 'ALL', include_aggregated=True)
        combined_summary.update(summary)
        
        # Generate final output CSV with proper number formatting (save raw data)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Include invoice number in filename for easy identification
        safe_invoice = (invoice_number or 'ALL').replace('/', '-').replace('\\', '-').replace(' ', '_')
        output_filename = f"{timestamp}_{safe_invoice}_combined_processed.csv"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        # Use custom formatting function to ensure numbers are written as plain decimals
        write_csv_with_proper_formatting(final_df, output_path)
        
        # Also save aggregated CSV
        aggregated_filename = f"{timestamp}_{safe_invoice}_combined_aggregated.csv"
        aggregated_path = os.path.join(app.config['OUTPUT_FOLDER'], aggregated_filename)
        write_csv_with_proper_formatting(aggregated_df, aggregated_path)
        
        # Convert DataFrames to dict for JSON response (sample of data for display)
        raw_data_sample = final_df.head(100).to_dict('records') if len(final_df) > 0 else []
        aggregated_data_sample = aggregated_df.head(100).to_dict('records') if len(aggregated_df) > 0 else []
        
        return jsonify({
            'success': True,
            'summary': combined_summary,
            'raw_data': {
                'total_rows': len(final_df),
                'sample': raw_data_sample
            },
            'aggregated_data': {
                'total_rows': len(aggregated_df),
                'sample': aggregated_data_sample
            },
            'download_filename': output_filename,
            'aggregated_filename': aggregated_filename,
            'message': f'Successfully processed {len(file_pairs)} file pairs with {len(final_df)} total line items ({len(aggregated_df)} unique SKUs)'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/process', methods=['POST'])
def process_invoice():
    """
    Process uploaded invoice files (legacy single file processing)
    Expects: 
        - data_file: Tab-delimited text file with invoice data
        - invoice_number: Optional invoice number to filter
    """
    try:
        # Check if file was uploaded
        if 'data_file' not in request.files:
            return jsonify({'error': 'No data file provided'}), 400
        
        data_file = request.files['data_file']
        invoice_number = request.form.get('invoice_number', None)
        
        if data_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(data_file.filename):
            return jsonify({'error': 'Invalid file type. Please upload .txt, .csv, or .pdf'}), 400
        
        # Save uploaded file
        filename = secure_filename(data_file.filename)
        file_type = filename.rsplit('.', 1)[1].lower()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        saved_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
        data_file.save(filepath)
        
        # Process the data
        result_df = process_invoice_data(filepath, file_type, invoice_number)
        
        if len(result_df) == 0:
            return jsonify({'error': 'No data found for the specified invoice number'}), 404
        
        # Extract invoice number from file if not provided
        if not invoice_number:
            try:
                if file_type == 'pdf':
                    text = extract_text_from_pdf(filepath)
                    parsed_data = parse_invoice_from_text(text)
                    invoice_number = parsed_data.get('invoice_number', None)
                    print(f"Extracted invoice number from file: {invoice_number}")
            except Exception as e:
                print(f"Could not extract invoice number: {e}")
        
        # Generate aggregated data
        aggregated_df = aggregate_by_sku(result_df)
        
        # Generate summary with aggregated data
        summary = generate_summary(result_df, invoice_number or 'ALL', include_aggregated=True)
        
        # Save output CSV with proper number formatting (save raw data)
        # Include invoice number in filename for easy identification
        safe_invoice = (invoice_number or 'ALL').replace('/', '-').replace('\\', '-').replace(' ', '_')
        output_filename = f"{timestamp}_{safe_invoice}_processed.csv"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], output_filename)
        # Use custom formatting function to ensure numbers are written as plain decimals
        write_csv_with_proper_formatting(result_df, output_path)
        
        # Also save aggregated CSV
        aggregated_filename = f"{timestamp}_{safe_invoice}_aggregated.csv"
        aggregated_path = os.path.join(app.config['OUTPUT_FOLDER'], aggregated_filename)
        write_csv_with_proper_formatting(aggregated_df, aggregated_path)
        
        # Convert DataFrames to dict for JSON response (sample of data for display)
        raw_data_sample = result_df.head(100).to_dict('records') if len(result_df) > 0 else []
        aggregated_data_sample = aggregated_df.head(100).to_dict('records') if len(aggregated_df) > 0 else []
        
        # Return summary and download link
        return jsonify({
            'success': True,
            'summary': summary,
            'raw_data': {
                'total_rows': len(result_df),
                'sample': raw_data_sample
            },
            'aggregated_data': {
                'total_rows': len(aggregated_df),
                'sample': aggregated_data_sample
            },
            'download_filename': output_filename,
            'aggregated_filename': aggregated_filename,
            'message': f'Successfully processed {len(result_df)} line items ({len(aggregated_df)} unique SKUs)'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download processed CSV file"""
    try:
        filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(
            filepath,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/preview', methods=['POST'])
def preview_data():
    """Preview the first few rows of uploaded data"""
    try:
        if 'data_file' not in request.files:
            return jsonify({'error': 'No data file provided'}), 400
        
        data_file = request.files['data_file']
        
        # Read and preview
        df = pd.read_csv(data_file, sep='\t', nrows=10)
        
        preview = {
            'columns': list(df.columns),
            'row_count': len(df),
            'sample_data': df.head(5).to_dict('records')
        }
        
        return jsonify(preview)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Clean up old files on startup (remove files older than 7 days)
    print("\n" + "=" * 60)
    print("Invoice Processor - Starting up")
    print("=" * 60)
    uploads_removed, uploads_size = cleanup_old_files(UPLOAD_FOLDER, days_old=7)
    outputs_removed, outputs_size = cleanup_old_files(OUTPUT_FOLDER, days_old=7)
    
    if uploads_removed > 0 or outputs_removed > 0:
        total_mb = (uploads_size + outputs_size) / (1024 * 1024)
        print(f"Cleaned up {uploads_removed + outputs_removed} old files ({total_mb:.2f} MB)")
    
    print("=" * 60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
