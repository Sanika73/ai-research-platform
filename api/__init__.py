# Python configuration for Vercel deployment
import sys
import os

# Add the root directory to Python path for proper imports
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# Ensure services directory is accessible
SERVICES_DIR = os.path.join(ROOT_DIR, 'services')
if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)
