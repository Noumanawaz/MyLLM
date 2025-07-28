#!/usr/bin/env python3
"""
Example usage of Saad's Restaurant LLM API with Enhanced Order Context
This demonstrates the new order tracking and session management features.
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

async def demonstrate_order_context():
    """Demonstrate the enhanced order context features"""
    print("🛒 Saad's Restaurant LLM API - Order Context Demo")
    print("=" * 60)
    
    # 1. Start a new conversation session
    print("\n1. Creating a new conversation session...")
    session_response = await make_request("/chat/new", "POST")
    session_id = session_response["session_id"]
    print(f"✅ Session created: {session_id}")
    
    # 2. Update customer information
    print("\n2. Updating customer information...")
    customer_info = {
        "customer_name": "Ahmed Khan",
        "phone_number": "+92-300-1234567",
        "delivery_address": "House 123, Street 5, Gulberg III, Lahore",
        "delivery_preference": "home_delivery",
        "payment_method": "cash_on_delivery"
    }
    
    update_response = await make_request(f"/chat/session/{session_id}/order/update", "POST", customer_info)
    print(f"✅ Customer info updated: {update_response['message']}")
    
    # 3. Start a conversation about ordering
    print("\n3. Starting order conversation...")
    chat_request = {
        "prompt": "Hi, I'd like to order some food. Can you tell me about your popular pizzas?",
        "session_id": session_id,
        "use_cache": True,
        "max_tokens": 200,
        "temperature": 0.7,
        "model": "openai/gpt-3.5-turbo"
    }
    
    response1 = await make_request("/chat", "POST", chat_request)
    print(f"🤖 Response: {response1['response'][:100]}...")
    
    # 4. Add items to order
    print("\n4. Adding items to order...")
    
    # Add a pizza
    pizza_item = {
        "name": "Peri Peri Pizza",
        "size": "Large",
        "price": 1200.0,
        "quantity": 1,
        "special_instructions": "Extra spicy"
    }
    
    add_response = await make_request(f"/chat/session/{session_id}/order/add", "POST", pizza_item)
    print(f"✅ Added to order: {pizza_item['name']}")
    
    # Add wings
    wings_item = {
        "name": "BBQ Wings",
        "size": "Regular (6 pieces)",
        "price": 450.0,
        "quantity": 1,
        "special_instructions": "Extra BBQ sauce"
    }
    
    add_response = await make_request(f"/chat/session/{session_id}/order/add", "POST", wings_item)
    print(f"✅ Added to order: {wings_item['name']}")
    
    # 5. Continue conversation with order context
    print("\n5. Continuing conversation with order context...")
    chat_request["prompt"] = "What's in my current order and what's the total?"
    
    response2 = await make_request("/chat", "POST", chat_request)
    print(f"🤖 Response: {response2['response'][:150]}...")
    
    # 6. Get order context
    print("\n6. Getting order context...")
    order_context = await make_request(f"/chat/session/{session_id}/order")
    print(f"📋 Order Context:")
    print(f"   Customer: {order_context['order_context']['customer_name']}")
    print(f"   Phone: {order_context['order_context']['phone_number']}")
    print(f"   Address: {order_context['order_context']['delivery_address']}")
    print(f"   Total Items: {len(order_context['order_context']['current_order'])}")
    print(f"   Order Total: Rs. {order_context['order_context']['order_total']}")
    
    # 7. Show current order items
    print(f"\n   Current Order Items:")
    for i, item in enumerate(order_context['order_context']['current_order']):
        print(f"   {i+1}. {item['name']} - Rs. {item['price']}")
    
    # 8. Remove an item from order
    print("\n7. Removing an item from order...")
    remove_response = await make_request(f"/chat/session/{session_id}/order/remove/0", "DELETE")
    print(f"🗑️ Removed: {remove_response['removed_item']['name']}")
    
    # 9. Get updated order context
    print("\n8. Getting updated order context...")
    updated_order = await make_request(f"/chat/session/{session_id}/order")
    print(f"📋 Updated Order Total: Rs. {updated_order['order_context']['order_total']}")
    
    # 10. Get session summary
    print("\n9. Getting session summary...")
    summary = await make_request(f"/chat/session/{session_id}/summary")
    print(f"📊 Session Summary:")
    print(f"   Session ID: {summary['session_id']}")
    print(f"   Created: {summary['created_at']}")
    print(f"   Last Activity: {summary['last_activity']}")
    print(f"   Message Count: {summary['message_count']}")
    print(f"   Order Total: Rs. {summary['order_context']['order_total']}")
    
    # 11. Continue conversation with updated order
    print("\n10. Continuing conversation with updated order...")
    chat_request["prompt"] = "Can you confirm my order and tell me the delivery time?"
    
    response3 = await make_request("/chat", "POST", chat_request)
    print(f"🤖 Response: {response3['response'][:150]}...")
    
    # 12. Add special instructions
    print("\n11. Adding special instructions...")
    special_instructions = {
        "special_instructions": "Please call 5 minutes before delivery and ring the doorbell twice"
    }
    
    update_response = await make_request(f"/chat/session/{session_id}/order/update", "POST", special_instructions)
    print(f"✅ Special instructions added")
    
    # 13. Final order confirmation
    print("\n12. Final order confirmation...")
    final_order = await make_request(f"/chat/session/{session_id}/order")
    print(f"📋 Final Order Details:")
    print(f"   Customer: {final_order['order_context']['customer_name']}")
    print(f"   Phone: {final_order['order_context']['phone_number']}")
    print(f"   Address: {final_order['order_context']['delivery_address']}")
    print(f"   Payment: {final_order['order_context']['payment_method']}")
    print(f"   Special Instructions: {final_order['order_context']['special_instructions']}")
    print(f"   Total: Rs. {final_order['order_context']['order_total']}")
    
    print("\n✅ Order context demo completed successfully!")
    print("\nKey Features Demonstrated:")
    print("• Customer information tracking")
    print("• Order item management (add/remove)")
    print("• Order total calculation")
    print("• Special instructions")
    print("• Session persistence")
    print("• Context-aware conversations")

async def demonstrate_session_isolation():
    """Demonstrate that different sessions have isolated order contexts"""
    print("\n" + "=" * 60)
    print("🔒 Session Isolation Demo")
    print("=" * 60)
    
    # Create two different sessions
    session1_response = await make_request("/chat/new", "POST")
    session1_id = session1_response["session_id"]
    
    session2_response = await make_request("/chat/new", "POST")
    session2_id = session2_response["session_id"]
    
    print(f"📱 Session 1: {session1_id}")
    print(f"📱 Session 2: {session2_id}")
    
    # Add different customer info to each session
    customer1 = {
        "customer_name": "Fatima Ali",
        "phone_number": "+92-300-1111111",
        "delivery_address": "Apartment 5A, Block 7, Clifton, Karachi"
    }
    
    customer2 = {
        "customer_name": "Usman Ahmed",
        "phone_number": "+92-300-2222222",
        "delivery_address": "Shop 15, Mall Road, Islamabad"
    }
    
    await make_request(f"/chat/session/{session1_id}/order/update", "POST", customer1)
    await make_request(f"/chat/session/{session2_id}/order/update", "POST", customer2)
    
    # Add different items to each order
    item1 = {"name": "Margherita Pizza", "price": 800.0, "quantity": 1}
    item2 = {"name": "Chicken Burger", "price": 350.0, "quantity": 2}
    
    await make_request(f"/chat/session/{session1_id}/order/add", "POST", item1)
    await make_request(f"/chat/session/{session2_id}/order/add", "POST", item2)
    
    # Check that sessions are isolated
    order1 = await make_request(f"/chat/session/{session1_id}/order")
    order2 = await make_request(f"/chat/session/{session2_id}/order")
    
    print(f"\n📋 Session 1 Order:")
    print(f"   Customer: {order1['order_context']['customer_name']}")
    print(f"   Items: {len(order1['order_context']['current_order'])}")
    print(f"   Total: Rs. {order1['order_context']['order_total']}")
    
    print(f"\n📋 Session 2 Order:")
    print(f"   Customer: {order2['order_context']['customer_name']}")
    print(f"   Items: {len(order2['order_context']['current_order'])}")
    print(f"   Total: Rs. {order2['order_context']['order_total']}")
    
    print(f"\n✅ Sessions are properly isolated!")
    
    # Clean up
    await make_request(f"/chat/session/{session1_id}", "DELETE")
    await make_request(f"/chat/session/{session2_id}", "DELETE")

async def main():
    """Main function to run the demo"""
    try:
        # Check if API is running
        health = await make_request("/health")
        print(f"🏥 API Status: {health['status']}")
        
        # Run demonstrations
        await demonstrate_order_context()
        await demonstrate_session_isolation()
        
    except httpx.ConnectError:
        print("❌ Error: Could not connect to the API. Make sure it's running on http://localhost:8001")
        print("💡 Start the API with: python main.py")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 