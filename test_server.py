#!/usr/bin/env python3
"""
Simple test script to check if the server can start
"""
import os
import sys
import asyncio

# Set environment variables
os.environ['GOOGLE_API_KEY'] = 'AIzaSyBZUMvf1QN_6Hv-JRL31-ay1oVm1RhvPdc'
os.environ['SECRET_KEY'] = 'dev-secret-key-change-in-production-12345'
os.environ['DATABASE_URL'] = 'sqlite:///./assignment_agent.db'

# Add backend to path
sys.path.insert(0, '/Users/apple/Desktop/rahul_project/backend')

try:
    print("Testing imports...")
    from app.core.config import settings
    print(f"✓ Config loaded: {settings.database_url}")
    
    from app.core.database import init_db
    print("✓ Database module imported")
    
    from app.main import app
    print("✓ FastAPI app created")
    
    print("✓ All imports successful!")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
