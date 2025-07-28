#!/usr/bin/env python3
"""
Test script for the Restaurant Conversational LLM API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the health endpoint"""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed!")
            print(f"   Status: {response.json()['status']}")
            print(f"   Model: {response.json()['model']}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

def test_chat(prompt, max_length=150, temperature=0.7):
    """Test the general chat endpoint"""
    print(f"\n🍽️ Testing chat with prompt: '{prompt}'")
    
    payload = {
        "prompt": prompt,
        "max_length": max_length,
        "temperature": temperature
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Chat response received!")
            print(f"   Response: {result['response']}")
            print(f"   Model: {result['model_used']}")
        else:
            print(f"❌ Chat failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Chat error: {e}")

def test_restaurant_chat(prompt, max_length=200, temperature=0.8):
    """Test the restaurant-specific chat endpoint"""
    print(f"\n🏪 Testing restaurant chat with prompt: '{prompt}'")
    
    payload = {
        "prompt": prompt,
        "max_length": max_length,
        "temperature": temperature
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/chat/restaurant",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Restaurant chat response received!")
            print(f"   Response: {result['response']}")
            print(f"   Model: {result['model_used']}")
        else:
            print(f"❌ Restaurant chat failed: {response.status_code}")
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Restaurant chat error: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting Restaurant LLM API Tests")
    print("=" * 50)
    
    # Test health endpoint
    test_health()
    
    # Wait a moment for the server to be ready
    time.sleep(1)
    
    # Test prompts
    test_prompts = [
        "What's the best way to cook pasta?",
        "Can you recommend a vegetarian dish?",
        "How do I make a good pizza dough?",
        "What are some popular Italian dishes?",
        "How do I make authentic carbonara?"
    ]
    
    # Test general chat
    for prompt in test_prompts[:3]:
        test_chat(prompt)
        time.sleep(1)  # Small delay between requests
    
    # Test restaurant-specific chat
    for prompt in test_prompts[3:]:
        test_restaurant_chat(prompt)
        time.sleep(1)  # Small delay between requests
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")

if __name__ == "__main__":
    main() 