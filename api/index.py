import os
import sys

# Add the project root to the system path
root_dir = os.path.dirname(os.path.dirname(__file__))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, 'backend'))

from backend.app import app

# Vercel expects the WSGI application to be available as 'app'
# This is already provided by the import
