"""
Vercel serverless handler for FastAPI backend
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from mangum import Mangum

# Create handler for Vercel serverless
lambda_handler = Mangum(app, lifespan="off")

# Vercel expects a handler function
def handler(event, context):
    """AWS Lambda / Vercel serverless handler"""
    return lambda_handler(event, context)
