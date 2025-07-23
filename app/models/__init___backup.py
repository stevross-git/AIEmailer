"""
Models package for AI Email Assistant
"""
from .user import User
from .email import Email, EmailThread
from .chat import ChatMessage

__all__ = ['User', 'Email', 'EmailThread', 'ChatMessage']
from .chat import ChatSession, ChatMessage
