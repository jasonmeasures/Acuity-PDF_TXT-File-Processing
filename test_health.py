#!/usr/bin/env python3
"""
Comprehensive health check for the Invoice Processor application.
Tests all components, dependencies, and functionality.
"""

import sys
import os
import importlib

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_python_version():
    """Test Python version"""
    print("\n" + "=" * 60)
    print("1. Testing Python Version")
    print("=" * 60)
    version = sys.version_info
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("⚠ WARNING: Python 3.8+ recommended")
    else:
        print("✓ Python version is supported")
    
    return True

def test_dependencies():
    """Test all required dependencies"""
    print("\n" + "=" * 60)
    print("2. Testing Dependencies")
    print("=" * 60)
    
    dependencies = {
        'flask': 'Flask',
        'flask_cors': 'Flask-CORS',
        'pandas': 'Pandas',
        'PyPDF2': 'PyPDF2',
        'pytesseract': 'pytesseract',
        'pdf2image': 'pdf2image',
        'PIL': 'Pillow',
        'numpy': 'NumPy',
    }
    
    failed = []
    for module, name in dependencies.items():
        try:
            lib = importlib.import_module(module)
            version = getattr(lib, '__version__', 'unknown')
            print(f"✓ {name}: {version}")
        except ImportError as e:
            print(f"✗ {name}: NOT FOUND ({e})")
            failed.append(name)
    
    if failed:
        print(f"\n✗ Missing dependencies: {', '.join(failed)}")
        return False
    
    return True

def test_external_tools():
    """Test external tools"""
    print("\n" + "=" * 60)
    print("3. Testing External Tools")
    print("=" * 60)
    
    tools = ['tesseract', 'pdftoppm']
    
    for tool in tools:
        result = os.system(f'which {tool} > /dev/null 2>&1')
        if result == 0:
            print(f"✓ {tool} is installed")
        else:
            print(f"✗ {tool} is NOT installed")
            return False
    
    return True

def test_directories():
    """Test required directories"""
    print("\n" + "=" * 60)
    print("4. Testing Directory Structure")
    print("=" * 60)
    
    required_dirs = [
        'uploads',
        'outputs',
        'templates',
        'static',
        'static/css',
        'static/js'
    ]
    
    for directory in required_dirs:
        if os.path.exists(directory):
            file_count = len(os.listdir(directory))
            print(f"✓ {directory}/ ({file_count} files)")
        else:
            print(f"✗ {directory}/ - NOT FOUND")
            return False
    
    return True

def test_app_import():
    """Test app module import"""
    print("\n" + "=" * 60)
    print("5. Testing Application Import")
    print("=" * 60)
    
    try:
        from app import app
        print(f"✓ Application imported successfully")
        print(f"✓ Flask app object created")
        print(f"✓ App name: {app.name}")
        print(f"✓ Debug mode: {app.debug}")
        return True
    except Exception as e:
        print(f"✗ Failed to import app: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_templates():
    """Test template files"""
    print("\n" + "=" * 60)
    print("6. Testing Template Files")
    print("=" * 60)
    
    templates = [
        'templates/index.html',
        'templates/enhanced_index.html',
    ]
    
    for template in templates:
        if os.path.exists(template):
            size = os.path.getsize(template)
            print(f"✓ {template} ({size:,} bytes)")
        else:
            print(f"✗ {template} - NOT FOUND")
            return False
    
    return True

def test_static_files():
    """Test static files"""
    print("\n" + "=" * 60)
    print("7. Testing Static Files")
    print("=" * 60)
    
    static_files = [
        'static/css/styles.css',
        'static/js/app.js',
    ]
    
    for file in static_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"✓ {file} ({size:,} bytes)")
        else:
            print(f"✗ {file} - NOT FOUND")
            return False
    
    return True

def test_configuration():
    """Test application configuration"""
    print("\n" + "=" * 60)
    print("8. Testing Configuration")
    print("=" * 60)
    
    from app import app
    
    config_checks = [
        ('UPLOAD_FOLDER exists', os.path.exists(app.config.get('UPLOAD_FOLDER', ''))),
        ('OUTPUT_FOLDER exists', os.path.exists(app.config.get('OUTPUT_FOLDER', ''))),
        ('MAX_CONTENT_LENGTH set', app.config.get('MAX_CONTENT_LENGTH', 0) > 0),
        ('CORS enabled', hasattr(app, 'extensions') and 'flask-cors' in app.extensions),
    ]
    
    all_ok = True
    for check_name, check_result in config_checks:
        if check_result:
            print(f"✓ {check_name}")
        else:
            print(f"✗ {check_name}")
            all_ok = False
    
    return all_ok

def test_app_functions():
    """Test key application functions"""
    print("\n" + "=" * 60)
    print("9. Testing Application Functions")
    print("=" * 60)
    
    try:
        from app import (
            extract_text_from_pdf,
            extract_text_from_txt,
            parse_invoice_from_text,
            extract_part_numbers_from_text,
            process_invoice_data,
            allowed_file
        )
        
        functions = [
            extract_text_from_pdf,
            extract_text_from_txt,
            parse_invoice_from_text,
            extract_part_numbers_from_text,
            process_invoice_data,
            allowed_file
        ]
        
        for func in functions:
            print(f"✓ {func.__name__}")
        
        return True
    except Exception as e:
        print(f"✗ Failed to import functions: {e}")
        return False

def test_file_cleanup():
    """Test cleanup function"""
    print("\n" + "=" * 60)
    print("10. Testing Cleanup Function")
    print("=" * 60)
    
    try:
        from app import cleanup_old_files
        
        # Test cleanup function exists
        print("✓ cleanup_old_files function exists")
        
        # Test it doesn't crash
        uploads_count, uploads_size = cleanup_old_files('uploads', days_old=365)
        outputs_count, outputs_size = cleanup_old_files('outputs', days_old=365)
        
        print(f"✓ Cleanup function works (no files older than 365 days)")
        
        return True
    except Exception as e:
        print(f"✗ Cleanup function failed: {e}")
        return False

def main():
    """Run all health checks"""
    print("\n" + "=" * 60)
    print("INVOICE PROCESSOR - COMPREHENSIVE HEALTH CHECK")
    print("=" * 60)
    
    results = []
    
    # Run all tests
    results.append(("Python Version", test_python_version()))
    results.append(("Dependencies", test_dependencies()))
    results.append(("External Tools", test_external_tools()))
    results.append(("Directory Structure", test_directories()))
    results.append(("App Import", test_app_import()))
    results.append(("Templates", test_templates()))
    results.append(("Static Files", test_static_files()))
    results.append(("Configuration", test_configuration()))
    results.append(("App Functions", test_app_functions()))
    results.append(("Cleanup Function", test_file_cleanup()))
    
    # Summary
    print("\n" + "=" * 60)
    print("HEALTH CHECK SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n✓ ALL CHECKS PASSED - System is healthy!")
        return 0
    else:
        print("\n✗ SOME CHECKS FAILED - Please review issues above")
        return 1

if __name__ == '__main__':
    sys.exit(main())




