# Enhanced Invoice Processor - PDF & TXT Support

## Overview

The Enhanced Invoice Processor is a comprehensive web application that extends the original Commercial Invoice Processor with advanced capabilities for handling PDF and TXT files, intelligent data combination, and enhanced CSV output generation.

## 🚀 New Features

### 1. **Dual Processing Modes**
- **Single File Processing**: Legacy functionality for individual file processing
- **Combined PDF + TXT Processing**: New mode for processing multiple files with data combination

### 2. **Multi-Format File Support**
- **PDF Files**: Extract text and parse invoice data using PyPDF2
- **TXT Files**: Support both structured (tab-delimited) and unstructured text files
- **CSV Files**: Enhanced processing with better error handling

### 3. **Intelligent Data Combination**
- Automatically pairs PDF and TXT files based on filename similarity
- Merges data from multiple sources intelligently
- Prioritizes structured data from TXT files over PDF-extracted data
- Handles missing or incomplete data gracefully

### 4. **Enhanced User Interface**
- Modern, responsive design with dual-mode interface
- Drag & drop file upload support
- Real-time file pairing visualization
- Enhanced processing statistics and summaries
- Tabbed interface for different processing modes

### 5. **Advanced CSV Output**
- Combined data from multiple sources
- Standardized field mapping
- Enhanced error handling and data validation
- Timestamped output files

## 📁 Project Structure

```
invoice_processor/
├── app.py                          # Enhanced Flask application
├── requirements.txt                # Python dependencies
├── templates/
│   ├── enhanced_index.html        # New enhanced interface
│   └── index.html                 # Legacy interface
├── static/
│   ├── css/styles.css             # Styling
│   └── js/app.js                  # JavaScript functionality
├── uploads/                       # File upload directory
├── outputs/                       # Generated CSV files
├── sample_invoice.txt             # Sample unstructured invoice
├── sample_structured_data.txt     # Sample structured data
├── test_enhanced_functionality.py # Test script
└── README_ENHANCED.md             # This documentation
```

## 🛠 Installation & Setup

### Prerequisites
- Python 3.7+
- pip (Python package manager)

### Installation Steps

1. **Navigate to the project directory:**
   ```bash
   cd "/Users/jasonmeasures/Library/CloudStorage/OneDrive-KlearNow/VS Scripts/invoice_processor"
   ```

2. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install requests  # For testing
   ```

4. **Start the server:**
   ```bash
   python app.py
   ```

5. **Access the application:**
   - Enhanced Interface: http://localhost:5000
   - Legacy Interface: http://localhost:5000/legacy

## 📖 Usage Guide

### Mode 1: Single File Processing (Legacy)

1. Select "Single File Processing" mode
2. Upload a single file (TXT, CSV, or PDF)
3. Optionally specify an invoice number for filtering
4. Click "Process Invoice" to generate CSV output

### Mode 2: Combined PDF + TXT Processing (New)

1. Select "Combined PDF + TXT Processing" mode
2. Upload PDF files in the PDF section
3. Upload TXT files in the TXT section
4. The system will automatically pair matching files
5. Review the file pairs before processing
6. Click "Process Combined Files" to generate combined CSV

### File Pairing Logic

The system automatically pairs PDF and TXT files based on:
- Filename similarity (e.g., `invoice.pdf` pairs with `invoice.txt`)
- Partial name matching
- Case-insensitive comparison

## 🔧 API Endpoints

### New Enhanced Endpoints

#### Upload Multiple Files
```
POST /api/upload-files
Content-Type: multipart/form-data
Body: files (multiple PDF/TXT files)
```

#### Process Combined Files
```
POST /api/process-combined
Content-Type: application/json
Body: {
  "file_pairs": [
    {
      "pdf": {"filename": "doc.pdf", "filepath": "/path/to/doc.pdf", "type": "pdf"},
      "txt": {"filename": "doc.txt", "filepath": "/path/to/doc.txt", "type": "txt"}
    }
  ],
  "invoice_number": "optional_invoice_number"
}
```

### Legacy Endpoints (Still Available)

#### Single File Processing
```
POST /api/process
Content-Type: multipart/form-data
Body: data_file + invoice_number (optional)
```

#### Health Check
```
GET /api/health
```

#### Download CSV
```
GET /api/download/<filename>
```

## 📊 Data Processing Logic

### PDF Processing
1. Extract text using PyPDF2
2. Parse using regex patterns for common invoice fields
3. Convert to standardized DataFrame format

### TXT Processing
1. Attempt structured parsing (tab-delimited)
2. Fall back to unstructured text parsing if needed
3. Apply same regex patterns as PDF processing

### Data Combination
1. Start with PDF-extracted data as base
2. Override/merge with TXT data where available
3. Handle missing fields gracefully
4. Combine all file pairs into single output

### Output Format
Standard CSV with columns:
- SKU
- DESCRIPTION
- HTS
- COUNTRY OF ORIGIN
- NO. OF PACKAGE
- QUANTITY
- NET WEIGHT
- GROSS WEIGHT
- UNIT PRICE
- VALUE
- QTY UNIT

## 🧪 Testing

Run the comprehensive test suite:

```bash
python test_enhanced_functionality.py
```

This tests:
- Server connectivity
- Multiple file upload
- Combined file processing
- Single file processing (legacy)
- CSV generation and download
- Data combination logic

## 📈 Performance & Statistics

### Processing Summary
The enhanced system provides detailed statistics:
- Total files processed
- Total line items generated
- Total value calculated
- File type breakdown
- Processing timestamps

### Error Handling
- Comprehensive error messages
- Graceful handling of malformed files
- Validation of file types and sizes
- Recovery from processing failures

## 🔒 Security Features

- File type validation
- Secure filename handling
- File size limits (16MB per file)
- Input sanitization
- CORS protection

## 🚀 Future Enhancements

Potential improvements for future versions:
- Batch processing capabilities
- Advanced PDF parsing with OCR
- Custom field mapping
- Database integration
- User authentication
- Processing history tracking
- Real-time collaboration features

## 🐛 Troubleshooting

### Common Issues

1. **Server won't start:**
   - Check if port 5000 is available
   - Verify virtual environment is activated
   - Ensure all dependencies are installed

2. **File upload fails:**
   - Verify file size is under 16MB
   - Check file format (PDF/TXT only)
   - Ensure uploads directory exists

3. **Processing errors:**
   - Check file content format
   - Verify file pairing
   - Review server logs for detailed errors

### Debug Mode

Enable debug mode for detailed logging:
```bash
export FLASK_DEBUG=1
python app.py
```

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the test script for expected behavior
3. Check server logs for detailed error messages
4. Verify file formats and content structure

## 📄 License

This project is proprietary software developed for internal invoice processing requirements.

---

## 🎉 Success Metrics

The enhanced system successfully demonstrates:
- ✅ Multiple file format support (PDF, TXT, CSV)
- ✅ Intelligent data combination
- ✅ Enhanced CSV output generation
- ✅ Modern, responsive user interface
- ✅ Comprehensive error handling
- ✅ Full backward compatibility with legacy functionality

