#!/usr/bin/env python3
import sys
import os

print("\n" + "=" * 60)
print("INVOICE PROCESSOR - HEALTH CHECK")
print("=" * 60 + "\n")

# Test Python
print(f"✓ Python: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

# Test imports
modules = ['flask', 'pandas', 'PyPDF2', 'pytesseract', 'pdf2image', 'PIL.Image']
for m in modules:
    try:
        __import__(m)
        print(f"✓ Module: {m}")
    except Exception as e:
        print(f"✗ Module: {m} - {str(e)[:50]}")

# Test directories
print()
dirs = ['uploads', 'outputs', 'templates', 'static/css', 'static/js']
for d in dirs:
    if os.path.exists(d):
        print(f"✓ Directory: {d}/")
    else:
        print(f"✗ Directory: {d}/ - NOT FOUND")

# Test files
print()
files = ['app.py', 'templates/enhanced_index.html', 'static/css/styles.css']
for f in files:
    if os.path.exists(f):
        size = os.path.getsize(f)
        print(f"✓ File: {f} ({size:,} bytes)")
    else:
        print(f"✗ File: {f} - NOT FOUND")

print("\n" + "=" * 60)
print("Health check complete!")
print("=" * 60 + "\n")




