# Commercial Invoice Processor - Web Service

A web application for processing commercial invoices and matching HTS codes for customs documentation.

## Features

- **File Upload**: Upload tab-delimited invoice data files (.txt or .csv)
- **HTS Code Matching**: Automatically matches part numbers with HTS codes
- **Invoice Filtering**: Process specific invoices or all invoices in a file
- **Data Preview**: Preview uploaded data before processing
- **Export**: Download processed data as CSV with proper formatting
- **Summary Statistics**: View invoice totals, HTS breakdowns, and country statistics

## Technology Stack

- **Backend**: Python Flask
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Data Processing**: Pandas
- **Styling**: Modern CSS with custom design system

## Installation

### Local Development

1. **Clone or extract the project**
   ```bash
   cd invoice_processor
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the development server**
   ```bash
   python app.py
   ```

5. **Access the application**
   Open your browser and navigate to: `http://localhost:5000`

### Production Deployment

#### Option 1: Using Gunicorn (Linux/Unix)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run with Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

#### Option 2: Docker Deployment

1. **Create Dockerfile**
   ```dockerfile
   FROM python:3.11-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .

   RUN mkdir -p uploads outputs

   EXPOSE 5000

   CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
   ```

2. **Build and run**
   ```bash
   docker build -t invoice-processor .
   docker run -p 5000:5000 -v $(pwd)/uploads:/app/uploads -v $(pwd)/outputs:/app/outputs invoice-processor
   ```

#### Option 3: Deploy to Cloud Platform

**AWS Elastic Beanstalk:**
```bash
eb init -p python-3.11 invoice-processor
eb create invoice-processor-env
eb deploy
```

**Google Cloud Run:**
```bash
gcloud run deploy invoice-processor --source . --platform managed --region us-central1
```

**Azure App Service:**
```bash
az webapp up --name invoice-processor --runtime PYTHON:3.11
```

## Project Structure

```
invoice_processor/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/
│   └── index.html        # Main HTML page
├── static/
│   ├── css/
│   │   └── styles.css    # Application styles
│   └── js/
│       └── app.js        # Frontend JavaScript
├── uploads/              # Temporary upload storage
└── outputs/              # Processed file storage
```

## API Endpoints

### Health Check
- **GET** `/api/health`
- Returns API status

### Process Invoice
- **POST** `/api/process`
- **Body**: FormData with `data_file` and optional `invoice_number`
- **Returns**: Processing summary and download filename

### Preview Data
- **POST** `/api/preview`
- **Body**: FormData with `data_file`
- **Returns**: Column names and sample data

### Download File
- **GET** `/api/download/<filename>`
- **Returns**: CSV file download

## Input File Format

The application expects a tab-delimited text file with the following columns:

```
HTTS	C/N	PART	PART_DESC	DATE	MASTER_INVOICE	invoice_nbr	line	quantity	AMT	WEIGHT	...
```

Required columns:
- **HTTS**: HTS code
- **C/N**: Country of origin
- **PART**: Part/SKU number
- **PART_DESC**: Part description
- **quantity**: Quantity
- **AMT**: Unit price
- **WEIGHT**: Weight in kg

## Output Format

The processed CSV file contains:

```
SKU, DESCRIPTION, HTS, COUNTRY OF ORIGIN, NO. OF PACKAGE, 
QUANTITY, NET WEIGHT, GROSS WEIGHT, UNIT PRICE, VALUE, QTY UNIT
```

## Configuration

### Environment Variables

Create a `.env` file for configuration:

```env
FLASK_ENV=production
FLASK_SECRET_KEY=your-secret-key-here
MAX_CONTENT_LENGTH=16777216  # 16MB
UPLOAD_FOLDER=uploads
OUTPUT_FOLDER=outputs
```

### Security Considerations

For production deployment:

1. **Set a strong secret key**
   ```python
   app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
   ```

2. **Enable HTTPS** - Use a reverse proxy (Nginx) with SSL certificates

3. **Add authentication** - Implement user authentication for internal teams

4. **Rate limiting** - Add Flask-Limiter to prevent abuse

5. **File validation** - The app already validates file types and sizes

## Usage

1. **Upload File**: Select or drag & drop your invoice data file
2. **Enter Invoice Number** (optional): Filter to a specific invoice
3. **Preview**: Click "Preview Data" to see column structure
4. **Process**: Click "Process Invoice" to generate the formatted output
5. **Download**: Download the processed CSV file
6. **Process Another**: Reset the form to process another file

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Use a different port
python app.py --port 5001
```

**Module not found:**
```bash
# Ensure virtual environment is activated and dependencies installed
pip install -r requirements.txt
```

**File upload fails:**
- Check file size (max 16MB)
- Verify file format (.txt or .csv)
- Ensure proper tab-delimitation

## Support

For internal support, contact your IT team or the application administrator.

## License

Internal use only - Proprietary
