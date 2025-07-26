"""
Models package for AI Email Assistant
"""
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

# Note: Models are imported in __init__ methods to avoid circular imports
# Import only when needed, not at module level