import sys
import os

# Add root and backend to python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(root_dir, 'backend')

sys.path.append(root_dir)
sys.path.append(backend_dir)

from backend.app import app

print(f"Active DB URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

if "sqlite" in app.config['SQLALCHEMY_DATABASE_URI']:
    print("STATUS: USING SQLITE (Local Default)")
    print("ACTION REQUIRED: Add DATABASE_URL to backend/.env")
else:
    print("STATUS: USING REMOTE DATABASE (likely Supabase)")
