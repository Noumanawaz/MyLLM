from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Restaurant Conversational LLM API (OpenRouter)",
    description="A FastAPI application that provides restaurant-related conversational responses using OpenRouter's free models",
    version="1.0.0"
)

class ChatRequest(BaseModel):
    prompt: str
    max_tokens: int = 150
    temperature: float = 0.7
    model: str = "openai/gpt-3.5-turbo"  # Default free model

class ChatResponse(BaseModel):
    response: str
    model_used: str
    tokens_used: int = 0

# OpenRouter configuration
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", None)

# Free models available on OpenRouter
FREE_MODELS = {
    "qwen/qwen3-coder:free": "Qwen3 Coder (FREE - 262K context)",
}

@app.get("/")
async def root():
    return {
        "message": "Restaurant Conversational LLM API (OpenRouter)",
        "endpoints": {
            "POST /chat": "Send a restaurant-related prompt and get LLM response",
            "GET /health": "Check API health status",
            "GET /models": "List available free models"
        },
        "free_models": FREE_MODELS
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "provider": "OpenRouter",
        "models_available": len(FREE_MODELS)
    }

@app.get("/models")
async def list_models():
    """List available free models"""
    return {
        "models": FREE_MODELS,
        "note": "These are free tier models available on OpenRouter"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_with_llm(request: ChatRequest):
    """
    Send a restaurant-related prompt and get a conversational response from the LLM.
    
    Example prompts:
    - "What's the best way to cook pasta?"
    - "Can you recommend a vegetarian dish?"
    - "How do I make a good pizza dough?"
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
    
    try:
        # Prepare headers for OpenRouter API
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:8000",  # Required by OpenRouter
            "X-Title": "Restaurant LLM API"  # Optional: helps with analytics
        }
        
        # Prepare the payload for OpenRouter
        payload = {
            "model": request.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful restaurant and cooking assistant. Provide helpful, accurate, and engaging responses about food, cooking, and restaurant-related topics."
                },
                {
                    "role": "user",
                    "content": request.prompt
                }
            ],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                OPENROUTER_API_URL,
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract the generated text from the response
                if "choices" in result and len(result["choices"]) > 0:
                    generated_text = result["choices"][0]["message"]["content"]
                    tokens_used = result.get("usage", {}).get("total_tokens", 0)
                else:
                    generated_text = "I'm sorry, I couldn't generate a response. Please try again."
                    tokens_used = 0
                
                return ChatResponse(
                    response=generated_text,
                    model_used=request.model,
                    tokens_used=tokens_used
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
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/chat/restaurant", response_model=ChatResponse)
async def restaurant_specific_chat(request: ChatRequest):
    """
    Specialized endpoint for restaurant-related conversations.
    Automatically adds restaurant context to the prompt.
    """
    # Add restaurant context to the prompt
    restaurant_prompt = f"Restaurant context: {request.prompt}"
    
    # Create a new request with the enhanced prompt
    enhanced_request = ChatRequest(
        prompt=restaurant_prompt,
        max_tokens=request.max_tokens,
        temperature=request.temperature,
        model=request.model
    )
    
    return await chat_with_llm(enhanced_request)

@app.post("/chat/quick")
async def quick_chat(prompt: str):
    """
    Quick chat endpoint with default settings for simple testing
    """
    request = ChatRequest(
        prompt=prompt,
        max_tokens=100,
        temperature=0.7,
        model="openai/gpt-3.5-turbo"
    )
    
    return await chat_with_llm(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Different port to avoid conflicts 