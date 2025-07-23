"""
Models package for AI Email Assistant
"""
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

# Import models without relationships to avoid circular references
from .user import User
from .email import Email
from .chat import ChatMessage

__all__ = ['db', 'User', 'Email', 'ChatMessage']
