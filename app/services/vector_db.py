"""
Vector Database Service for AI Email Assistant
"""
import os
import json
import uuid
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import numpy as np
from flask import current_app

class VectorDBService:
    """Service for managing vector database operations"""
    
    def __init__(self):
        self.db_path = current_app.config['VECTOR_DB_PATH']
        self.collection_name = current_app.config['VECTOR_COLLECTION_NAME']
        self.embedding_model_name = current_app.config['EMBEDDING_MODEL']
        
        self.client = None
        self.collection = None
        self.embedding_model = None
    
    def initialize(self):
        """Initialize vector database and embedding model"""
        try:
            # Ensure database directory exists
            os.makedirs(self.db_path, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(
                    name=self.collection_name,
                    embedding_function=self._get_embedding_function()
                )
                current_app.logger.info(f"Loaded existing collection: {self.collection_name}")
            except Exception:
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=self._get_embedding_function(),
                    metadata={"description": "Email embeddings for AI assistant"}
                )
                current_app.logger.info(f"Created new collection: {self.collection_name}")
            
            # Initialize embedding model
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            
            current_app.logger.info("Vector database service initialized successfully")
            return True
        
        except Exception as e:
            current_app.logger.error(f"Vector database initialization failed: {e}")
            return False
    
    def _get_embedding_function(self):
        """Get ChromaDB embedding function"""
        from chromadb.utils import embedding_functions
        
        # Use sentence transformer embedding function
        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model_name
        )
    
    def add_email(self, email_id: int, email_data: Dict, user_id: int) -> bool:
        """Add email to vector database"""
        try:
            if not self.collection:
                current_app.logger.error("Vector database not initialized")
                return False
            
            # Create document text from email data
            document_text = self._create_email_document(email_data)
            
            # Create unique document ID
            doc_id = f"email_{user_id}_{email_id}_{uuid.uuid4().hex[:8]}"
            
            # Prepare metadata
            metadata = {
                "email_id": email_id,
                "user_id": user_id,
                "subject": email_data.get('subject', '')[:500],  # Limit length
                "sender_email": email_data.get('sender_email', ''),
                "sender_name": email_data.get('sender_name', ''),
                "received_date": email_data.get('received_date', ''),
                "is_sent_item": email_data.get('is_sent_item', False),
                "folder_name": email_data.get('folder_name', ''),
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Add to collection
            self.collection.add(
                documents=[document_text],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            current_app.logger.debug(f"Added email {email_id} to vector database")
            return True
        
        except Exception as e:
            current_app.logger.error(f"Error adding email to vector database: {e}")
            return False
    
    def search_emails(self, user_id: int, query: str, limit: int = 10) -> List[Dict]:
        """Search emails using vector similarity"""
        try:
            if not self.collection:
                current_app.logger.error("Vector database not initialized")
                return []
            
            # Search in collection with user filter
            results = self.collection.query(
                query_texts=[query],
                n_results=min(limit, 100),
                where={"user_id": user_id}
            )
            
            # Format results
            search_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i]
                    distance = results['distances'][0][i] if results.get('distances') else None
                    
                    search_results.append({
                        'email_id': metadata.get('email_id'),
                        'subject': metadata.get('subject'),
                        'sender_email': metadata.get('sender_email'),
                        'sender_name': metadata.get('sender_name'),
                        'received_date': metadata.get('received_date'),
                        'folder_name': metadata.get('folder_name'),
                        'similarity_score': 1 - distance if distance else None,
                        'document_preview': doc[:200] + "..." if len(doc) > 200 else doc
                    })
            
            return search_results
        
        except Exception as e:
            current_app.logger.error(f"Error searching emails in vector database: {e}")
            return []
    
    def get_similar_emails(self, email_id: int, user_id: int, limit: int = 5) -> List[Dict]:
        """Find similar emails to a given email"""
        try:
            if not self.collection:
                return []
            
            # First, get the document for the given email
            results = self.collection.get(
                where={"$and": [{"email_id": email_id}, {"user_id": user_id}]}
            )
            
            if not results['documents']:
                return []
            
            # Use the document text to find similar emails
            document_text = results['documents'][0]
            
            # Search for similar emails (excluding the original)
            similar_results = self.collection.query(
                query_texts=[document_text],
                n_results=limit + 1,  # +1 to account for the original email
                where={"$and": [{"user_id": user_id}, {"email_id": {"$ne": email_id}}]}
            )
            
            # Format results
            similar_emails = []
            if similar_results['documents'] and similar_results['documents'][0]:
                for i, doc in enumerate(similar_results['documents'][0]):
                    metadata = similar_results['metadatas'][0][i]
                    distance = similar_results['distances'][0][i] if similar_results.get('distances') else None
                    
                    similar_emails.append({
                        'email_id': metadata.get('email_id'),
                        'subject': metadata.get('subject'),
                        'sender_email': metadata.get('sender_email'),
                        'sender_name': metadata.get('sender_name'),
                        'received_date': metadata.get('received_date'),
                        'similarity_score': 1 - distance if distance else None
                    })
            
            return similar_emails[:limit]
        
        except Exception as e:
            current_app.logger.error(f"Error finding similar emails: {e}")
            return []
    
    def get_user_email_context(self, user_id: int, query: str, limit: int = 5) -> str:
        """Get relevant email context for a user query"""
        try:
            search_results = self.search_emails(user_id, query, limit)
            
            if not search_results:
                return ""
            
            # Build context from search results
            context_parts = []
            for result in search_results:
                context_part = f"Email from {result.get('sender_name', 'Unknown')} ({result.get('sender_email', '')}):\n"
                context_part += f"Subject: {result.get('subject', 'No subject')}\n"
                context_part += f"Date: {result.get('received_date', 'Unknown date')}\n"
                context_part += f"Preview: {result.get('document_preview', '')}\n"
                context_parts.append(context_part)
            
            return "\n\n---\n\n".join(context_parts)
        
        except Exception as e:
            current_app.logger.error(f"Error getting email context: {e}")
            return ""
    
    def delete_user_emails(self, user_id: int) -> bool:
        """Delete all emails for a user from vector database"""
        try:
            if not self.collection:
                return False
            
            # Get all documents for the user
            results = self.collection.get(where={"user_id": user_id})
            
            if results['ids']:
                # Delete all documents
                self.collection.delete(ids=results['ids'])
                current_app.logger.info(f"Deleted {len(results['ids'])} email documents for user {user_id}")
            
            return True
        
        except Exception as e:
            current_app.logger.error(f"Error deleting user emails from vector database: {e}")
            return False
    
    def delete_email(self, email_id: int, user_id: int) -> bool:
        """Delete specific email from vector database"""
        try:
            if not self.collection:
                return False
            
            # Delete documents matching email_id and user_id
            self.collection.delete(
                where={"$and": [{"email_id": email_id}, {"user_id": user_id}]}
            )
            
            current_app.logger.debug(f"Deleted email {email_id} from vector database")
            return True
        
        except Exception as e:
            current_app.logger.error(f"Error deleting email from vector database: {e}")
            return False
    
    def get_collection_info(self) -> Dict:
        """Get information about the vector collection"""
        try:
            if not self.collection:
                return {"error": "Collection not initialized"}
            
            count = self.collection.count()
            
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "embedding_model": self.embedding_model_name,
                "database_path": self.db_path
            }
        
        except Exception as e:
            current_app.logger.error(f"Error getting collection info: {e}")
            return {"error": str(e)}
    
    def _create_email_document(self, email_data: Dict) -> str:
        """Create document text from email data for embedding"""
        parts = []
        
        # Add subject
        if email_data.get('subject'):
            parts.append(f"Subject: {email_data['subject']}")
        
        # Add sender info
        if email_data.get('sender_name'):
            parts.append(f"From: {email_data['sender_name']}")
        if email_data.get('sender_email'):
            parts.append(f"Email: {email_data['sender_email']}")
        
        # Add recipients
        if email_data.get('to_recipients'):
            recipients = []
            for recipient in email_data['to_recipients']:
                if isinstance(recipient, dict):
                    email_addr = recipient.get('emailAddress', {}).get('address', '')
                    name = recipient.get('emailAddress', {}).get('name', '')
                    recipients.append(name or email_addr)
                else:
                    recipients.append(str(recipient))
            if recipients:
                parts.append(f"To: {', '.join(recipients)}")
        
        # Add body content
        if email_data.get('body_preview'):
            parts.append(f"Content: {email_data['body_preview']}")
        elif email_data.get('body_content'):
            # Use body content but limit length
            body = email_data['body_content'][:2000]  # Limit to avoid embedding size issues
            parts.append(f"Content: {body}")
        
        # Add metadata
        if email_data.get('received_date'):
            parts.append(f"Date: {email_data['received_date']}")
        
        if email_data.get('folder_name'):
            parts.append(f"Folder: {email_data['folder_name']}")
        
        return "\n".join(parts)
    
    def batch_add_emails(self, email_data_list: List[Tuple[int, Dict, int]]) -> int:
        """Batch add multiple emails to vector database"""
        try:
            if not self.collection or not email_data_list:
                return 0
            
            documents = []
            metadatas = []
            ids = []
            
            for email_id, email_data, user_id in email_data_list:
                # Create document text
                document_text = self._create_email_document(email_data)
                
                # Create unique document ID
                doc_id = f"email_{user_id}_{email_id}_{uuid.uuid4().hex[:8]}"
                
                # Prepare metadata
                metadata = {
                    "email_id": email_id,
                    "user_id": user_id,
                    "subject": email_data.get('subject', '')[:500],
                    "sender_email": email_data.get('sender_email', ''),
                    "sender_name": email_data.get('sender_name', ''),
                    "received_date": email_data.get('received_date', ''),
                    "is_sent_item": email_data.get('is_sent_item', False),
                    "folder_name": email_data.get('folder_name', ''),
                    "created_at": datetime.utcnow().isoformat()
                }
                
                documents.append(document_text)
                metadatas.append(metadata)
                ids.append(doc_id)
            
            # Batch add to collection
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            current_app.logger.info(f"Batch added {len(email_data_list)} emails to vector database")
            return len(email_data_list)
        
        except Exception as e:
            current_app.logger.error(f"Error batch adding emails to vector database: {e}")
            return 0