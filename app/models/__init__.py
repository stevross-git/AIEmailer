"""
Models package initialization
Import models in the correct order to avoid circular dependencies
"""

# Import base models first
from app.models.user import User
from app.models.email import Email
from app.models.chat import ChatMessage

# Make all models available at package level
__all__ = ['User', 'Email', 'ChatMessage']