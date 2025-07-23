"""
Ollama Engine Service for AI Email Assistant
"""
import requests
import json
import time
from typing import Dict, List, Optional, Generator
from flask import current_app

class OllamaService:
    """Service for interacting with Ollama local AI models"""
    
    def __init__(self):
        self.base_url = current_app.config['OLLAMA_BASE_URL']
        self.model = current_app.config['OLLAMA_MODEL']
        self.timeout = current_app.config['OLLAMA_TIMEOUT']
        self.stream = current_app.config['OLLAMA_STREAM']
    
    def check_health(self) -> bool:
        """Check if Ollama service is running"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            current_app.logger.error(f"Ollama health check failed: {e}")
            return False
    
    def list_models(self) -> Optional[List[Dict]]:
        """List available models"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('models', [])
            else:
                current_app.logger.error(f"List models failed: {response.text}")
                return None
        except Exception as e:
            current_app.logger.error(f"List models error: {e}")
            return None
    
    def pull_model(self, model_name: str) -> bool:
        """Pull/download a model"""
        try:
            data = {'name': model_name}
            
            response = requests.post(
                f"{self.base_url}/api/pull",
                json=data,
                timeout=300,  # 5 minutes for model download
                stream=True
            )
            
            if response.status_code == 200:
                # Process streaming response
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            if chunk.get('status') == 'success':
                                return True
                        except json.JSONDecodeError:
                            continue
                return True
            else:
                current_app.logger.error(f"Pull model failed: {response.text}")
                return False
        except Exception as e:
            current_app.logger.error(f"Pull model error: {e}")
            return False
    
    def generate_response(self, prompt: str, context: Optional[str] = None, system_prompt: Optional[str] = None) -> Dict:
        """Generate response from Ollama model"""
        try:
            # Build the full prompt
            full_prompt = self._build_prompt(prompt, context, system_prompt)
            
            data = {
                'model': self.model,
                'prompt': full_prompt,
                'stream': False,  # Non-streaming for API responses
                'options': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'top_k': 40,
                    'num_predict': 2048
                }
            }
            
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=self.timeout
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'text': result.get('response', '').strip(),
                    'model_used': self.model,
                    'response_time_ms': response_time,
                    'token_count': self._estimate_tokens(result.get('response', '')),
                    'context': result.get('context'),
                    'done': result.get('done', True)
                }
            else:
                current_app.logger.error(f"Generate response failed: {response.text}")
                return {
                    'text': "I'm sorry, I'm having trouble processing your request right now.",
                    'error': response.text,
                    'response_time_ms': response_time
                }
        
        except requests.exceptions.Timeout:
            current_app.logger.error("Ollama request timeout")
            return {
                'text': "I'm sorry, the response took too long to generate. Please try again.",
                'error': 'timeout'
            }
        except Exception as e:
            current_app.logger.error(f"Generate response error: {e}")
            return {
                'text': "I'm sorry, I encountered an error while processing your request.",
                'error': str(e)
            }
    
    def generate_streaming_response(self, prompt: str, context: Optional[str] = None, system_prompt: Optional[str] = None) -> Generator[Dict, None, None]:
        """Generate streaming response from Ollama model"""
        try:
            full_prompt = self._build_prompt(prompt, context, system_prompt)
            
            data = {
                'model': self.model,
                'prompt': full_prompt,
                'stream': True,
                'options': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'top_k': 40,
                    'num_predict': 2048
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=self.timeout,
                stream=True
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        try:
                            chunk = json.loads(line)
                            if 'response' in chunk:
                                yield {
                                    'text': chunk['response'],
                                    'done': chunk.get('done', False),
                                    'context': chunk.get('context')
                                }
                        except json.JSONDecodeError:
                            continue
            else:
                yield {
                    'text': "Error generating response",
                    'error': response.text,
                    'done': True
                }
        
        except Exception as e:
            current_app.logger.error(f"Streaming response error: {e}")
            yield {
                'text': "Error generating streaming response",
                'error': str(e),
                'done': True
            }
    
    def chat_completion(self, messages: List[Dict], system_prompt: Optional[str] = None) -> Dict:
        """Chat completion with conversation history"""
        try:
            # Convert messages to Ollama format
            prompt = self._format_chat_messages(messages, system_prompt)
            
            data = {
                'model': self.model,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'top_k': 40,
                    'num_predict': 2048
                }
            }
            
            start_time = time.time()
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=self.timeout
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'text': result.get('response', '').strip(),
                    'model_used': self.model,
                    'response_time_ms': response_time,
                    'token_count': self._estimate_tokens(result.get('response', '')),
                    'done': result.get('done', True)
                }
            else:
                return {
                    'text': "I'm sorry, I'm having trouble processing your request.",
                    'error': response.text,
                    'response_time_ms': response_time
                }
        
        except Exception as e:
            current_app.logger.error(f"Chat completion error: {e}")
            return {
                'text': "I'm sorry, I encountered an error while processing your request.",
                'error': str(e)
            }
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embeddings for text (if model supports it)"""
        try:
            data = {
                'model': self.model,
                'prompt': text
            }
            
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('embedding')
            else:
                current_app.logger.warning(f"Embedding generation failed: {response.text}")
                return None
        
        except Exception as e:
            current_app.logger.error(f"Generate embedding error: {e}")
            return None
    
    def _build_prompt(self, prompt: str, context: Optional[str] = None, system_prompt: Optional[str] = None) -> str:
        """Build complete prompt with context and system instructions"""
        parts = []
        
        # Add system prompt
        if system_prompt:
            parts.append(f"SYSTEM: {system_prompt}")
        else:
            parts.append("SYSTEM: You are an AI assistant helping with email management. Be helpful, concise, and professional.")
        
        # Add context if provided
        if context:
            parts.append(f"CONTEXT: {context}")
        
        # Add user prompt
        parts.append(f"USER: {prompt}")
        parts.append("ASSISTANT:")
        
        return "\n\n".join(parts)
    
    def _format_chat_messages(self, messages: List[Dict], system_prompt: Optional[str] = None) -> str:
        """Format chat messages for prompt"""
        formatted_parts = []
        
        if system_prompt:
            formatted_parts.append(f"SYSTEM: {system_prompt}")
        
        for message in messages:
            role = message.get('role', 'user').upper()
            content = message.get('content', '')
            formatted_parts.append(f"{role}: {content}")
        
        formatted_parts.append("ASSISTANT:")
        return "\n\n".join(formatted_parts)
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Very rough estimation: ~4 characters per token
        return len(text) // 4
    
    def get_model_info(self, model_name: Optional[str] = None) -> Optional[Dict]:
        """Get information about a specific model"""
        try:
            model_to_check = model_name or self.model
            
            response = requests.post(
                f"{self.base_url}/api/show",
                json={'name': model_to_check},
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                current_app.logger.error(f"Get model info failed: {response.text}")
                return None
        
        except Exception as e:
            current_app.logger.error(f"Get model info error: {e}")
            return None