# Deployment Guide - Commercial Invoice Processor

## Quick Start Deployment Options

### Option 1: Local Development (Fastest)

```bash
# Navigate to project directory
cd invoice_processor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py

# Access at http://localhost:5000
```

### Option 2: Docker (Recommended for Internal Server)

```bash
# Build and run with Docker Compose
docker-compose up -d

# Access at http://localhost:5000

# View logs
docker-compose logs -f

# Stop application
docker-compose down
```

### Option 3: Production Server with Nginx

#### Step 1: Install Dependencies
```bash
# On Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx

# Create application directory
sudo mkdir -p /var/www/invoice-processor
cd /var/www/invoice-processor

# Copy application files
sudo cp -r /path/to/invoice_processor/* .

# Set permissions
sudo chown -R www-data:www-data /var/www/invoice-processor
```

#### Step 2: Setup Python Environment
```bash
sudo -u www-data python3 -m venv venv
sudo -u www-data venv/bin/pip install -r requirements.txt
```

#### Step 3: Create Systemd Service
```bash
sudo nano /etc/systemd/system/invoice-processor.service
```

Add this content:
```ini
[Unit]
Description=Invoice Processor Web Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/invoice-processor
Environment="PATH=/var/www/invoice-processor/venv/bin"
ExecStart=/var/www/invoice-processor/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
```

#### Step 4: Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/invoice-processor
```

Add this content:
```nginx
server {
    listen 80;
    server_name your-domain.com;  # Change this

    client_max_body_size 16M;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/invoice-processor/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### Step 5: Enable and Start Services
```bash
# Enable Nginx site
sudo ln -s /etc/nginx/sites-available/invoice-processor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Start application service
sudo systemctl enable invoice-processor
sudo systemctl start invoice-processor
sudo systemctl status invoice-processor
```

### Option 4: Cloud Platform Deployment

#### AWS Elastic Beanstalk

1. **Install EB CLI**
   ```bash
   pip install awsebcli
   ```

2. **Initialize and Deploy**
   ```bash
   eb init -p python-3.11 invoice-processor --region us-east-1
   eb create invoice-processor-prod
   eb open
   ```

3. **Configure Environment**
   ```bash
   eb setenv FLASK_SECRET_KEY=your-secret-key
   ```

#### Google Cloud Run

1. **Create cloudbuild.yaml**
   ```yaml
   steps:
     - name: 'gcr.io/cloud-builders/docker'
       args: ['build', '-t', 'gcr.io/$PROJECT_ID/invoice-processor', '.']
     - name: 'gcr.io/cloud-builders/docker'
       args: ['push', 'gcr.io/$PROJECT_ID/invoice-processor']
   images:
     - 'gcr.io/$PROJECT_ID/invoice-processor'
   ```

2. **Deploy**
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   gcloud run deploy invoice-processor \
     --image gcr.io/PROJECT_ID/invoice-processor \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated
   ```

#### Azure App Service

```bash
# Login to Azure
az login

# Create resource group
az group create --name invoice-processor-rg --location eastus

# Deploy
az webapp up \
  --name invoice-processor \
  --runtime "PYTHON:3.11" \
  --sku B1
```

## Security Configuration

### 1. Set Secret Key
Create `.env` file:
```env
FLASK_SECRET_KEY=your-very-long-random-secret-key-here
```

Generate secure key:
```python
import secrets
print(secrets.token_hex(32))
```

### 2. Enable HTTPS
For production, always use HTTPS. With Nginx:
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

### 3. Add Authentication (Optional)
For basic auth, add to Nginx config:
```nginx
location / {
    auth_basic "Invoice Processor";
    auth_basic_user_file /etc/nginx/.htpasswd;
    # ... rest of config
}
```

Create password file:
```bash
sudo apt install apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd admin
```

## Monitoring and Maintenance

### Check Application Status
```bash
# Systemd service
sudo systemctl status invoice-processor

# Docker
docker-compose ps
docker-compose logs -f

# Check if port is listening
sudo netstat -tulpn | grep 5000
```

### View Logs
```bash
# Systemd
sudo journalctl -u invoice-processor -f

# Docker
docker-compose logs -f web

# Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Backup Data
```bash
# Backup uploads and outputs
tar -czf backup-$(date +%Y%m%d).tar.gz uploads/ outputs/

# Restore
tar -xzf backup-20250101.tar.gz
```

### Update Application
```bash
# Pull latest code
git pull origin main

# Restart service
sudo systemctl restart invoice-processor

# Or with Docker
docker-compose down
docker-compose up -d --build
```

## Performance Optimization

### 1. Increase Workers
Edit systemd service or docker-compose:
```
--workers 8  # Adjust based on CPU cores
```

### 2. Add Caching
Install Redis and configure Flask-Caching for better performance.

### 3. Database for File Tracking
For tracking processing history, add PostgreSQL or MySQL.

## Troubleshooting

### Application Won't Start
```bash
# Check Python version
python3 --version  # Should be 3.9+

# Check dependencies
pip list

# Test application directly
python app.py
```

### File Upload Issues
```bash
# Check directory permissions
ls -la uploads/ outputs/

# Fix permissions
sudo chown -R www-data:www-data uploads/ outputs/
sudo chmod -R 755 uploads/ outputs/
```

### Port Already in Use
```bash
# Find process using port
sudo lsof -i :5000

# Kill process
sudo kill -9 <PID>
```

## Support Contacts

- **Technical Issues**: IT Support Team
- **Application Questions**: Data Processing Team
- **Deployment Help**: DevOps Team

## Change Log

- **v1.0.0** (2025-01-16): Initial release
  - File upload and processing
  - HTS code matching
  - CSV export functionality
