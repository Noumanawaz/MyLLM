from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv
import json
import asyncio
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import hashlib
import uuid
from collections import OrderedDict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Global variables for memory and caching
class ConversationMemory:
    def __init__(self, max_conversations: int = 1000, max_messages_per_conversation: int = 50):
        self.conversations: Dict[str, Dict] = {}
        self.max_conversations = max_conversations
        self.max_messages_per_conversation = max_messages_per_conversation
        self.last_cleanup = time.time()
        self.cleanup_interval = 3600  # 1 hour
    
    def add_message(self, session_id: str, role: str, content: str, metadata: Dict = None):
        """Add a message to conversation memory"""
        if session_id not in self.conversations:
            self.conversations[session_id] = {
                'messages': [],
                'created_at': time.time(),
                'last_activity': time.time(),
                'metadata': metadata or {},
                'order_context': {
                    'customer_name': None,
                    'phone_number': None,
                    'delivery_address': None,
                    'current_order': [],
                    'order_total': 0.0,
                    'payment_method': None,
                    'delivery_preference': None,
                    'special_instructions': None
                }
            }
        
        conversation = self.conversations[session_id]
        conversation['last_activity'] = time.time()
        
        message = {
            'role': role,
            'content': content,
            'timestamp': time.time()
        }
        
        conversation['messages'].append(message)
        
        # Limit messages per conversation
        if len(conversation['messages']) > self.max_messages_per_conversation:
            conversation['messages'] = conversation['messages'][-self.max_messages_per_conversation:]
        
        # Cleanup old conversations periodically
        self._cleanup_old_conversations()
    
    def get_conversation(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session"""
        if session_id in self.conversations:
            self.conversations[session_id]['last_activity'] = time.time()
            return self.conversations[session_id]['messages']
        return []
    
    def get_order_context(self, session_id: str) -> Dict:
        """Get order context for a session"""
        if session_id in self.conversations:
            return self.conversations[session_id].get('order_context', {})
        return {}
    
    def update_order_context(self, session_id: str, updates: Dict):
        """Update order context for a session"""
        if session_id in self.conversations:
            order_context = self.conversations[session_id].get('order_context', {})
            order_context.update(updates)
            self.conversations[session_id]['order_context'] = order_context
            self.conversations[session_id]['last_activity'] = time.time()
    
    def add_to_order(self, session_id: str, item: Dict):
        """Add an item to the current order"""
        if session_id in self.conversations:
            order_context = self.conversations[session_id].get('order_context', {})
            current_order = order_context.get('current_order', [])
            current_order.append(item)
            order_context['current_order'] = current_order
            # Update total
            order_context['order_total'] = sum(item.get('price', 0) for item in current_order)
            self.conversations[session_id]['order_context'] = order_context
            self.conversations[session_id]['last_activity'] = time.time()
    
    def remove_from_order(self, session_id: str, item_index: int):
        """Remove an item from the current order"""
        if session_id in self.conversations:
            order_context = self.conversations[session_id].get('order_context', {})
            current_order = order_context.get('current_order', [])
            if 0 <= item_index < len(current_order):
                removed_item = current_order.pop(item_index)
                order_context['current_order'] = current_order
                # Update total
                order_context['order_total'] = sum(item.get('price', 0) for item in current_order)
                self.conversations[session_id]['order_context'] = order_context
                self.conversations[session_id]['last_activity'] = time.time()
                return removed_item
        return None
    
    def clear_order(self, session_id: str):
        """Clear the current order"""
        if session_id in self.conversations:
            order_context = self.conversations[session_id].get('order_context', {})
            order_context['current_order'] = []
            order_context['order_total'] = 0.0
            self.conversations[session_id]['order_context'] = order_context
            self.conversations[session_id]['last_activity'] = time.time()
    
    def get_session_summary(self, session_id: str) -> Dict:
        """Get a summary of the session including order context"""
        if session_id in self.conversations:
            conversation = self.conversations[session_id]
            return {
                'session_id': session_id,
                'created_at': conversation['created_at'],
                'last_activity': conversation['last_activity'],
                'message_count': len(conversation['messages']),
                'order_context': conversation.get('order_context', {}),
                'metadata': conversation.get('metadata', {})
            }
        return {}
    
    def clear_conversation(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in self.conversations:
            del self.conversations[session_id]
    
    def _cleanup_old_conversations(self):
        """Remove old conversations to prevent memory bloat"""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        self.last_cleanup = current_time
        cutoff_time = current_time - (24 * 3600)  # 24 hours
        
        sessions_to_remove = []
        for session_id, conversation in self.conversations.items():
            if conversation['last_activity'] < cutoff_time:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.conversations[session_id]
        
        logger.info(f"Cleaned up {len(sessions_to_remove)} old conversations")

class ResponseCache:
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.cache: OrderedDict = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl
    
    def _generate_key(self, prompt: str, model: str, max_tokens: int, temperature: float) -> str:
        """Generate cache key for a request"""
        key_data = f"{prompt}:{model}:{max_tokens}:{temperature}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
        """Get cached response if available and not expired"""
        key = self._generate_key(prompt, model, max_tokens, temperature)
        
        if key in self.cache:
            cached_item = self.cache[key]
            if time.time() - cached_item['timestamp'] < self.ttl:
                # Move to end (most recently used)
                self.cache.move_to_end(key)
                return cached_item['response']
            else:
                # Remove expired item
                del self.cache[key]
        
        return None
    
    def set(self, prompt: str, model: str, max_tokens: int, temperature: float, response: str):
        """Cache a response"""
        key = self._generate_key(prompt, model, max_tokens, temperature)
        
        # Remove if key already exists
        if key in self.cache:
            del self.cache[key]
        
        # Add new item
        self.cache[key] = {
            'response': response,
            'timestamp': time.time()
        }
        
        # Remove oldest item if cache is full
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)

# Initialize global memory and cache
conversation_memory = ConversationMemory()
response_cache = ResponseCache()

# Load menu data from data.json
def load_menu_data():
    try:
        with open('data.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
            # Extract all menu items from the selection1 array
            menu_items = data.get('selection1', [])
            return menu_items
    except FileNotFoundError:
        logger.warning("data.json not found. Menu items will not be available.")
        return []
    except json.JSONDecodeError:
        logger.warning("Invalid JSON in data.json. Menu items will not be available.")
        return []

# Load menu items
MENU_ITEMS = load_menu_data()

# Create menu context string (cached)
_menu_context = None
_menu_context_timestamp = 0
MENU_CONTEXT_TTL = 300  # 5 minutes

def create_menu_context():
    """Create menu context with caching"""
    global _menu_context, _menu_context_timestamp
    
    current_time = time.time()
    if _menu_context is None or (current_time - _menu_context_timestamp) > MENU_CONTEXT_TTL:
        if not MENU_ITEMS:
            _menu_context = "Menu items are currently unavailable."
        else:
            menu_text = "Here's our current menu:\n\n"
            for item in MENU_ITEMS:
                menu_text += f"• {item['name']} - {item['description']} - {item['price']}\n"
            _menu_context = menu_text
        
        _menu_context_timestamp = current_time
    
    return _menu_context

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    global http_client
    if http_client:
        await http_client.aclose()

app = FastAPI(
    title="Saad's Restaurant Conversational LLM API",
    description="A FastAPI application that provides restaurant-related conversational responses using OpenRouter's free models with memory and caching for faster responses.",
    version="2.0.0",
    lifespan=lifespan
)

class ChatRequest(BaseModel):
    prompt: str
    max_tokens: int = 80
    temperature: float = 0.7
    model: str = "qwen/qwen3-coder:free"  # Default FREE model (262K context)
    session_id: Optional[str] = None
    use_cache: bool = True
    clear_memory: bool = False

class ChatResponse(BaseModel):
    model_config = {"protected_namespaces": ()}
    
    response: str
    model_used: str
    tokens_used: int = 0
    session_id: str
    cached: bool = False
    conversation_length: int = 0

class SessionRequest(BaseModel):
    session_id: str

# OpenRouter configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", None)

# Free models available on OpenRouter
FREE_MODELS = {
    "qwen/qwen3-coder:free": "Qwen3 Coder (FREE - 262K context)",
    "meta-llama/llama-2-7b-chat": "Llama 2 7B Chat (FREE)",
    "google/palm-2-chat-bison": "PaLM 2 Chat (FREE)",
    "anthropic/claude-instant-v1": "Claude Instant (FREE)"
}

# Optimized HTTP client with connection pooling
http_client = None

async def get_http_client():
    """Get or create optimized HTTP client"""
    global http_client
    if http_client is None:
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
        http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            limits=limits
        )
    return http_client



@app.get("/")
async def root():
    return {
        "message": "Saad's Restaurant Conversational LLM API v2.0",
        "restaurant": "Saad's Restaurant",
        "features": {
            "memory": "Conversation memory with session management",
            "caching": "Response caching for faster responses",
            "optimization": "Connection pooling and async optimizations"
        },
        "endpoints": {
            "POST /chat": "Send a restaurant-related prompt and get LLM response with memory",
            "POST /chat/new": "Start a new conversation session",
            "DELETE /chat/session/{session_id}": "Clear conversation memory for a session",
            "GET /chat/session/{session_id}": "Get conversation history for a session",
            "GET /health": "Check API health status",
            "GET /models": "List available free models",
            "GET /menu": "Get current menu items",
            "GET /stats": "Get API usage statistics"
        },
        "free_models": FREE_MODELS,
        "menu_items_count": len(MENU_ITEMS),
        "active_sessions": len(conversation_memory.conversations),
        "cache_size": len(response_cache.cache)
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "provider": "OpenRouter",
        "models_available": len(FREE_MODELS),
        "restaurant": "Saad's Restaurant",
        "menu_loaded": len(MENU_ITEMS) > 0,
        "memory_stats": {
            "active_conversations": len(conversation_memory.conversations),
            "cache_size": len(response_cache.cache),
            "memory_usage": "optimized"
        }
    }

@app.get("/stats")
async def get_stats():
    """Get API usage statistics"""
    total_messages = sum(len(conv['messages']) for conv in conversation_memory.conversations.values())
    return {
        "active_sessions": len(conversation_memory.conversations),
        "total_messages": total_messages,
        "cache_size": len(response_cache.cache),
        "cache_hit_rate": "tracked_per_session",
        "uptime": "optimized"
    }

@app.get("/models")
async def list_models():
    """List available free models"""
    return {
        "models": FREE_MODELS,
        "note": "These are free tier models available on OpenRouter"
    }

@app.get("/menu")
async def get_menu():
    """Get current menu items"""
    return {
        "restaurant": "Saad's Restaurant",
        "menu_items": MENU_ITEMS,
        "total_items": len(MENU_ITEMS)
    }

@app.post("/chat/new")
async def start_new_session():
    """Start a new conversation session"""
    session_id = str(uuid.uuid4())
    return {
        "session_id": session_id,
        "message": "New conversation session created",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/chat/session/{session_id}")
async def get_session_history(session_id: str):
    """Get conversation history for a session"""
    messages = conversation_memory.get_conversation(session_id)
    return {
        "session_id": session_id,
        "messages": messages,
        "message_count": len(messages)
    }

@app.delete("/chat/session/{session_id}")
async def clear_session(session_id: str):
    """Clear conversation memory for a session"""
    conversation_memory.clear_conversation(session_id)
    return {
        "session_id": session_id,
        "message": "Conversation memory cleared",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/chat/session/{session_id}/summary")
async def get_session_summary(session_id: str):
    """Get comprehensive session summary including order context"""
    summary = conversation_memory.get_session_summary(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Session not found")
    return summary

@app.get("/chat/session/{session_id}/order")
async def get_order_context(session_id: str):
    """Get order context for a session"""
    order_context = conversation_memory.get_order_context(session_id)
    if not order_context:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "order_context": order_context
    }

@app.post("/chat/session/{session_id}/order/update")
async def update_order_context(session_id: str, updates: Dict[str, Any]):
    """Update order context for a session"""
    conversation_memory.update_order_context(session_id, updates)
    return {
        "session_id": session_id,
        "message": "Order context updated",
        "order_context": conversation_memory.get_order_context(session_id)
    }

@app.post("/chat/session/{session_id}/order/add")
async def add_order_item(session_id: str, item: Dict[str, Any]):
    """Add an item to the current order"""
    conversation_memory.add_to_order(session_id, item)
    return {
        "session_id": session_id,
        "message": "Item added to order",
        "order_context": conversation_memory.get_order_context(session_id)
    }

@app.delete("/chat/session/{session_id}/order/remove/{item_index}")
async def remove_order_item(session_id: str, item_index: int):
    """Remove an item from the current order"""
    removed_item = conversation_memory.remove_from_order(session_id, item_index)
    if removed_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return {
        "session_id": session_id,
        "message": "Item removed from order",
        "removed_item": removed_item,
        "order_context": conversation_memory.get_order_context(session_id)
    }

@app.delete("/chat/session/{session_id}/order/clear")
async def clear_order(session_id: str):
    """Clear the current order"""
    conversation_memory.clear_order(session_id)
    return {
        "session_id": session_id,
        "message": "Order cleared",
        "order_context": conversation_memory.get_order_context(session_id)
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_with_llm(request: ChatRequest):
    """
    Send a restaurant-related prompt and get a conversational response from the LLM with memory.
    
    Example prompts:
    - "What's your most popular pizza?"
    - "Can you recommend a vegetarian dish?"
    - "What's the price of your wings?"
    - "Tell me about your deals"
    """
    
    if not OPENROUTER_API_KEY:
        raise HTTPException(
            status_code=400, 
            detail="OpenRouter API key required. Get a free key from https://openrouter.ai/keys"
        )
    
    if request.model not in FREE_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Model {request.model} not available. Use one of: {list(FREE_MODELS.keys())}"
        )
    
    # Generate session ID if not provided
    session_id = request.session_id or str(uuid.uuid4())
    
    # Clear memory if requested
    if request.clear_memory:
        conversation_memory.clear_conversation(session_id)
    
    # Check cache first
    cached_response = None
    if request.use_cache:
        cached_response = response_cache.get(
            request.prompt, request.model, request.max_tokens, request.temperature
        )
    
    if cached_response:
        # Add to conversation memory
        conversation_memory.add_message(session_id, "user", request.prompt)
        conversation_memory.add_message(session_id, "assistant", cached_response)
        
        return ChatResponse(
            response=cached_response,
            model_used=request.model,
            tokens_used=0,
            session_id=session_id,
            cached=True,
            conversation_length=len(conversation_memory.get_conversation(session_id))
        )
    
    try:
        # Get conversation history
        conversation_history = conversation_memory.get_conversation(session_id)
        
        # Prepare headers for OpenRouter API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:8000",
            "X-Title": "Saad's Restaurant LLM API v2.0"
        }
        
        # Create the system prompt with Saad's Restaurant context and menu
        menu_context = create_menu_context()
        system_prompt = f"""You are a friendly restaurant assistant at Saad's Restaurant. Keep responses SHORT and CONCISE (1-2 sentences max).

{menu_context}

IMPORTANT: Be brief and direct. No lengthy explanations. Focus on:
- Quick answers to menu questions
- Simple order confirmations
- Brief price quotes
- Short recommendations

Remember conversation context but keep responses minimal."""

        # Build messages array with conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history (limit to last 10 messages to prevent token overflow)
        for msg in conversation_history[-10:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": request.prompt
        })

        # Prepare the payload for OpenRouter
        payload = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature
        }
        
        # Use optimized HTTP client
        client = await get_http_client()
        
        start_time = time.time()
        response = await client.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload
        )
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            
            # Extract the generated text from the response
            if "choices" in result and len(result["choices"]) > 0:
                generated_text = result["choices"][0]["message"]["content"]
                tokens_used = result.get("usage", {}).get("total_tokens", 0)
            else:
                generated_text = "I'm sorry, I couldn't generate a response. Please try again."
                tokens_used = 0
            
            # Add to conversation memory
            conversation_memory.add_message(session_id, "user", request.prompt)
            conversation_memory.add_message(session_id, "assistant", generated_text)
            
            # Cache the response for future use
            if request.use_cache:
                response_cache.set(
                    request.prompt, request.model, request.max_tokens, 
                    request.temperature, generated_text
                )
            
            logger.info(f"Response generated in {response_time:.2f}s for session {session_id}")
            
            return ChatResponse(
                response=generated_text,
                model_used=request.model,
                tokens_used=tokens_used,
                session_id=session_id,
                cached=False,
                conversation_length=len(conversation_memory.get_conversation(session_id))
            )
        else:
            error_detail = f"OpenRouter API error: {response.status_code}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_detail += f" - {error_data['error'].get('message', 'Unknown error')}"
            except:
                error_detail += f" - {response.text}"
            
            raise HTTPException(
                status_code=response.status_code,
                detail=error_detail
            )
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=408, detail="Request timeout")
    except Exception as e:
        logger.error(f"Error in chat_with_llm: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/chat/restaurant", response_model=ChatResponse)
async def restaurant_specific_chat(request: ChatRequest):
    """
    Specialized endpoint for Saad's Restaurant conversations.
    Automatically adds restaurant context to the prompt.
    """
    # Add restaurant context to the prompt
    restaurant_prompt = f"Saad's Restaurant context: {request.prompt}"
    
    # Create a new request with the enhanced prompt
    enhanced_request = ChatRequest(
        prompt=restaurant_prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        model=request.model,
        session_id=request.session_id,
        use_cache=request.use_cache,
        clear_memory=request.clear_memory
    )
    
    return await chat_with_llm(enhanced_request)

@app.post("/chat/quick")
async def quick_chat(prompt: str, session_id: Optional[str] = None):
    """
    Quick chat endpoint with default settings for simple testing
    """
    request = ChatRequest(
        prompt=prompt,
        max_tokens=60,
        temperature=0.7,
        model="qwen/qwen3-coder:free",
        session_id=session_id,
        use_cache=True
    )
    
    return await chat_with_llm(request)

if __name__ == "__main__":
    import os
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port) 