#!/usr/bin/env python3
"""
Example usage of the Restaurant LLM API from other projects
"""

import requests
import json

# API Configuration
API_BASE_URL = "http://localhost:8000"

def test_api_health():
    """Test if the API is running"""
    try:
        response = requests.get(f"{API_BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is healthy!")
            return response.json()
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return None

def chat_with_restaurant_ai(prompt, max_tokens=100, temperature=0.7, model="openai/gpt-3.5-turbo"):
    """
    Send a prompt to the restaurant AI and get a response
    
    Args:
        prompt (str): Your question about food/restaurants
        max_tokens (int): Maximum response length
        temperature (float): Creativity level (0.0-1.0)
        model (str): Which model to use
    
    Returns:
        dict: API response with 'response', 'model_used', 'tokens_used'
    """
    try:
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "model": model
        }
        
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def restaurant_specific_chat(prompt, max_tokens=150, temperature=0.8):
    """Use the restaurant-specific endpoint"""
    try:
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        response = requests.post(
            f"{API_BASE_URL}/chat/restaurant",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def quick_chat(prompt):
    """Quick chat with default settings"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat/quick",
            json={"prompt": prompt},
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

def get_available_models():
    """Get list of available models"""
    try:
        response = requests.get(f"{API_BASE_URL}/models")
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get models: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None

# Example usage functions
def example_restaurant_recommendations():
    """Example: Get restaurant recommendations"""
    print("\n🍽️ Restaurant Recommendations Example:")
    
    questions = [
        "What are some good Italian restaurants in downtown?",
        "Can you recommend vegetarian-friendly restaurants?",
        "What's the best way to cook pasta al dente?"
    ]
    
    for question in questions:
        print(f"\nQ: {question}")
        result = chat_with_restaurant_ai(question, max_tokens=150)
        if result:
            print(f"A: {result['response']}")
            print(f"Model: {result['model_used']} | Tokens: {result['tokens_used']}")

def example_recipe_help():
    """Example: Get cooking help"""
    print("\n👨‍🍳 Recipe Help Example:")
    
    cooking_questions = [
        "How do I make authentic carbonara?",
        "What's the secret to fluffy rice?",
        "How do I properly season a steak?"
    ]
    
    for question in cooking_questions:
        print(f"\nQ: {question}")
        result = restaurant_specific_chat(question, max_tokens=200)
        if result:
            print(f"A: {result['response']}")
            print(f"Model: {result['model_used']} | Tokens: {result['tokens_used']}")

def example_quick_questions():
    """Example: Quick questions"""
    print("\n⚡ Quick Questions Example:")
    
    quick_questions = [
        "What is sushi?",
        "How do I make coffee?",
        "What's the difference between baking and frying?"
    ]
    
    for question in quick_questions:
        print(f"\nQ: {question}")
        result = quick_chat(question)
        if result:
            print(f"A: {result['response']}")

# Main execution
if __name__ == "__main__":
    print("🚀 Restaurant LLM API Usage Examples")
    print("=" * 50)
    
    # Check API health
    health = test_api_health()
    if not health:
        print("❌ API is not available. Make sure it's running on localhost:8000")
        exit(1)
    
    # Show available models
    models = get_available_models()
    if models:
        print(f"📋 Available models: {list(models['models'].keys())}")
    
    # Run examples
    example_restaurant_recommendations()
    example_recipe_help()
    example_quick_questions()
    
    print("\n✅ All examples completed!") 