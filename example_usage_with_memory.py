#!/usr/bin/env python3
"""
Example usage of Saad's Restaurant LLM API with Memory and Caching
This demonstrates the new features: conversation memory, session management, and response caching.
"""

import asyncio
import httpx
import json
from typing import Dict, Any

# API Configuration
API_BASE_URL = "http://localhost:8001"

async def make_request(endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
    """Helper function to make API requests"""
    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(f"{API_BASE_URL}{endpoint}")
        elif method == "POST":
            response = await client.post(f"{API_BASE_URL}{endpoint}", json=data)
        elif method == "DELETE":
            response = await client.delete(f"{API_BASE_URL}{endpoint}")
        
        return response.json()

async def demonstrate_memory_and_caching():
    """Demonstrate the memory and caching features"""
    print("🚀 Saad's Restaurant LLM API - Memory & Caching Demo")
    print("=" * 60)
    
    # 1. Start a new conversation session
    print("\n1. Creating a new conversation session...")
    session_response = await make_request("/chat/new", "POST")
    session_id = session_response["session_id"]
    print(f"✅ Session created: {session_id}")
    
    # 2. First conversation - asking about menu
    print("\n2. First conversation - asking about menu...")
    chat_request = {
        "prompt": "What's your most popular pizza?",
        "session_id": session_id,
        "use_cache": True,
        "max_tokens": 150,
        "temperature": 0.7,
        "model": "openai/gpt-3.5-turbo"
    }
    
    response1 = await make_request("/chat", "POST", chat_request)
    print(f"🤖 Response: {response1['response'][:100]}...")
    print(f"📊 Cached: {response1['cached']}, Tokens: {response1['tokens_used']}")
    
    # 3. Second conversation - follow-up question (should use memory)
    print("\n3. Second conversation - follow-up question...")
    chat_request["prompt"] = "What's the price of that pizza?"
    
    response2 = await make_request("/chat", "POST", chat_request)
    print(f"🤖 Response: {response2['response'][:100]}...")
    print(f"📊 Cached: {response2['cached']}, Tokens: {response2['tokens_used']}")
    print(f"💬 Conversation length: {response2['conversation_length']}")
    
    # 4. Third conversation - asking the same question (should use cache)
    print("\n4. Third conversation - asking the same question (should use cache)...")
    chat_request["prompt"] = "What's your most popular pizza?"
    
    response3 = await make_request("/chat", "POST", chat_request)
    print(f"🤖 Response: {response3['response'][:100]}...")
    print(f"📊 Cached: {response3['cached']}, Tokens: {response3['tokens_used']}")
    
    # 5. Get conversation history
    print("\n5. Getting conversation history...")
    history = await make_request(f"/chat/session/{session_id}")
    print(f"📝 Total messages in session: {history['message_count']}")
    for i, msg in enumerate(history['messages'][-3:], 1):  # Show last 3 messages
        print(f"   {i}. {msg['role']}: {msg['content'][:50]}...")
    
    # 6. Check API statistics
    print("\n6. Checking API statistics...")
    stats = await make_request("/stats")
    print(f"📈 Active sessions: {stats['active_sessions']}")
    print(f"📈 Total messages: {stats['total_messages']}")
    print(f"📈 Cache size: {stats['cache_size']}")
    
    # 7. Start a new session and demonstrate session isolation
    print("\n7. Starting a new session to demonstrate isolation...")
    new_session_response = await make_request("/chat/new", "POST")
    new_session_id = new_session_response["session_id"]
    
    chat_request["session_id"] = new_session_id
    chat_request["prompt"] = "What's your most popular pizza?"
    
    response4 = await make_request("/chat", "POST", chat_request)
    print(f"🤖 New session response: {response4['response'][:100]}...")
    print(f"📊 Cached: {response4['cached']}, Tokens: {response4['tokens_used']}")
    print(f"💬 Conversation length: {response4['conversation_length']}")
    
    # 8. Demonstrate quick chat endpoint
    print("\n8. Using quick chat endpoint...")
    quick_response = await make_request("/chat/quick", "POST", {"prompt": "Tell me about your deals"})
    print(f"⚡ Quick response: {quick_response['response'][:100]}...")
    print(f"📊 Cached: {quick_response['cached']}")
    
    # 9. Clear one of the sessions
    print("\n9. Clearing the first session...")
    clear_response = await make_request(f"/chat/session/{session_id}", "DELETE")
    print(f"🗑️ {clear_response['message']}")
    
    # 10. Final statistics
    print("\n10. Final statistics...")
    final_stats = await make_request("/stats")
    print(f"📈 Active sessions: {final_stats['active_sessions']}")
    print(f"📈 Total messages: {final_stats['total_messages']}")
    print(f"📈 Cache size: {final_stats['cache_size']}")
    
    print("\n✅ Demo completed successfully!")
    print("\nKey Features Demonstrated:")
    print("• Conversation memory with session management")
    print("• Response caching for faster repeated queries")
    print("• Session isolation (different sessions don't share memory)")
    print("• Conversation history tracking")
    print("• Automatic memory cleanup")
    print("• Performance optimization with connection pooling")

async def demonstrate_performance_comparison():
    """Demonstrate performance improvements with caching"""
    print("\n" + "=" * 60)
    print("🏃‍♂️ Performance Comparison Demo")
    print("=" * 60)
    
    # Create a new session
    session_response = await make_request("/chat/new", "POST")
    session_id = session_response["session_id"]
    
    # Test question
    test_prompt = "What are your vegetarian options?"
    
    # First request (no cache)
    print(f"\n1. First request (no cache): '{test_prompt}'")
    start_time = asyncio.get_event_loop().time()
    
    chat_request = {
        "prompt": test_prompt,
        "session_id": session_id,
        "use_cache": True,
        "max_tokens": 150,
        "temperature": 0.7,
        "model": "openai/gpt-3.5-turbo"
    }
    
    response1 = await make_request("/chat", "POST", chat_request)
    first_request_time = asyncio.get_event_loop().time() - start_time
    
    print(f"⏱️ Time: {first_request_time:.2f}s")
    print(f"📊 Cached: {response1['cached']}, Tokens: {response1['tokens_used']}")
    
    # Second request (should use cache)
    print(f"\n2. Second request (with cache): '{test_prompt}'")
    start_time = asyncio.get_event_loop().time()
    
    response2 = await make_request("/chat", "POST", chat_request)
    second_request_time = asyncio.get_event_loop().time() - start_time
    
    print(f"⏱️ Time: {second_request_time:.2f}s")
    print(f"📊 Cached: {response2['cached']}, Tokens: {response2['tokens_used']}")
    
    # Calculate improvement
    if first_request_time > 0:
        improvement = ((first_request_time - second_request_time) / first_request_time) * 100
        print(f"🚀 Performance improvement: {improvement:.1f}% faster with caching!")
    
    # Clean up
    await make_request(f"/chat/session/{session_id}", "DELETE")

async def main():
    """Main function to run the demo"""
    try:
        # Check if API is running
        health = await make_request("/health")
        print(f"🏥 API Status: {health['status']}")
        
        # Run demonstrations
        await demonstrate_memory_and_caching()
        await demonstrate_performance_comparison()
        
    except httpx.ConnectError:
        print("❌ Error: Could not connect to the API. Make sure it's running on http://localhost:8001")
        print("💡 Start the API with: python main.py")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 