#!/usr/bin/env python3
"""Simple startup script for Flask application"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Start the Flask app
if __name__ == '__main__':
    from app import app
    print("=" * 60)
    print("Starting Invoice Processor on http://localhost:5001")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5001)




