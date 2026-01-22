#!/usr/bin/env python3
"""
Test script for the enhanced invoice processor functionality
"""

import os
import sys
import requests
import json
import time

def test_server():
    """Test if the server is running"""
    try:
        response = requests.get('http://localhost:5000/api/health')
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print("❌ Server returned status:", response.status_code)
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Server is not running. Please start it with: python app.py")
        return False

def test_multiple_file_upload():
    """Test multiple file upload functionality"""
    print("\n🧪 Testing multiple file upload...")
    
    # Test files
    test_files = [
        ('sample_invoice.txt', 'sample_invoice.txt'),
        ('sample_structured_data.txt', 'sample_structured_data.txt')
    ]
    
    # Prepare files for upload
    files = []
    for local_path, filename in test_files:
        if os.path.exists(local_path):
            files.append(('files', (filename, open(local_path, 'rb'), 'text/plain')))
        else:
            print(f"⚠️ Test file not found: {local_path}")
    
    if not files:
        print("❌ No test files found")
        return False
    
    try:
        response = requests.post('http://localhost:5000/api/upload-files', files=files)
        
        # Close file handles
        for _, file_tuple in files:
            file_tuple[1].close()
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload successful: {result['message']}")
            return result['files']
        else:
            print(f"❌ Upload failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return False

def test_combined_processing(uploaded_files):
    """Test combined file processing functionality"""
    print("\n🧪 Testing combined file processing...")
    
    if not uploaded_files:
        print("❌ No uploaded files to process")
        return False
    
    # Create file pairs (simplified for testing)
    file_pairs = []
    for file_info in uploaded_files:
        if file_info['type'] == 'txt':
            # For testing, we'll use TXT files as both PDF and TXT
            # In real usage, you'd have actual PDF files
            file_pairs.append({
                'pdf': file_info,  # In real scenario, this would be a PDF
                'txt': file_info   # This is the TXT file
            })
    
    try:
        response = requests.post('http://localhost:5000/api/process-combined', 
                               json={'file_pairs': file_pairs})
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Combined processing successful!")
            print(f"   - Files processed: {result['summary']['total_files_processed']}")
            print(f"   - Line items: {result['summary']['total_line_items']}")
            print(f"   - Total value: ${result['summary']['total_value']:,.2f}")
            print(f"   - File types: {result['summary']['file_types']}")
            print(f"   - CSV file: {result['download_filename']}")
            return result
        else:
            print(f"❌ Combined processing failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Combined processing error: {e}")
        return False

def test_single_file_processing():
    """Test single file processing (legacy functionality)"""
    print("\n🧪 Testing single file processing...")
    
    if not os.path.exists('sample_structured_data.txt'):
        print("⚠️ Sample file not found for single file test")
        return False
    
    try:
        with open('sample_structured_data.txt', 'rb') as f:
            files = {'data_file': f}
            data = {'invoice_number': 'INV-2024-001'}
            
            response = requests.post('http://localhost:5000/api/process', 
                                   files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Single file processing successful!")
            print(f"   - Line items: {result['summary']['total_lines']}")
            print(f"   - Total value: ${result['summary']['total_value']:,.2f}")
            print(f"   - HTS codes: {result['summary']['unique_hts_codes']}")
            return result
        else:
            print(f"❌ Single file processing failed: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Single file processing error: {e}")
        return False

def test_csv_download(csv_filename):
    """Test CSV download functionality"""
    print("\n🧪 Testing CSV download...")
    
    if not csv_filename:
        print("❌ No CSV file to download")
        return False
    
    try:
        response = requests.get(f'http://localhost:5000/api/download/{csv_filename}')
        
        if response.status_code == 200:
            print(f"✅ CSV download successful")
            print(f"   - File size: {len(response.content)} bytes")
            return True
        else:
            print(f"❌ CSV download failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ CSV download error: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Enhanced Invoice Processor")
    print("=" * 50)
    
    # Test 1: Server status
    if not test_server():
        return
    
    # Test 2: Multiple file upload
    uploaded_files = test_multiple_file_upload()
    if not uploaded_files:
        return
    
    # Test 3: Combined file processing
    combined_result = test_combined_processing(uploaded_files)
    if not combined_result:
        return
    
    # Test 4: Single file processing
    single_result = test_single_file_processing()
    
    # Test 5: CSV download
    csv_filename = combined_result.get('download_filename')
    test_csv_download(csv_filename)
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")
    print("\nEnhanced features available:")
    print("1. Multiple file upload (PDF + TXT)")
    print("2. Intelligent data combination")
    print("3. Enhanced CSV output")
    print("4. Legacy single file processing")
    print("\nTo use the enhanced interface:")
    print("1. Open http://localhost:5000 in your browser")
    print("2. Choose between 'Single File' or 'Combined PDF + TXT' modes")
    print("3. Upload files and process them")
    print("4. Download the generated CSV files")

if __name__ == "__main__":
    main()

