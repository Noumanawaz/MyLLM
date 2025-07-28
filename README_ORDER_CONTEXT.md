# Saad's Restaurant LLM API - Enhanced Order Context System

## 🛒 Overview

The Enhanced Order Context System provides comprehensive session-based memory for tracking customer orders, preferences, and conversation history. This system allows the LLM to maintain context across multiple interactions and provide personalized, order-aware responses.

## 🧠 Key Features

### 1. **Session-Based Memory**

- Each conversation gets a unique session ID
- All context is isolated between different sessions
- Automatic cleanup of old sessions (24 hours)
- Configurable memory limits

### 2. **Order Context Tracking**

- Customer information (name, phone, address)
- Current order items with prices and quantities
- Order total calculation
- Payment method and delivery preferences
- Special instructions

### 3. **Conversation History**

- Complete message history with timestamps
- Context-aware responses using previous messages
- Automatic context management to prevent token overflow

### 4. **Order Management**

- Add/remove items from orders
- Update customer information
- Clear entire orders
- Track order modifications

## 🔧 API Endpoints

### Core Session Management

#### `POST /chat/new`

Create a new conversation session.

```bash
curl -X POST http://localhost:8001/chat/new
```

**Response:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "New conversation session created",
  "timestamp": "2024-01-01T12:00:00"
}
```

#### `GET /chat/session/{session_id}`

Get conversation history for a session.

```bash
curl http://localhost:8001/chat/session/550e8400-e29b-41d4-a716-446655440000
```

**Response:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "messages": [
    {
      "role": "user",
      "content": "Hi, I'd like to order a pizza",
      "timestamp": 1704110400.0
    },
    {
      "role": "assistant",
      "content": "Great! I'd be happy to help you order a pizza...",
      "timestamp": 1704110400.5
    }
  ],
  "message_count": 2
}
```

### Order Context Management

#### `GET /chat/session/{session_id}/order`

Get order context for a session.

```bash
curl http://localhost:8001/chat/session/550e8400-e29b-41d4-a716-446655440000/order
```

**Response:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "order_context": {
    "customer_name": "Ahmed Khan",
    "phone_number": "+92-300-1234567",
    "delivery_address": "House 123, Street 5, Gulberg III, Lahore",
    "current_order": [
      {
        "name": "Peri Peri Pizza",
        "size": "Large",
        "price": 1200.0,
        "quantity": 1,
        "special_instructions": "Extra spicy"
      }
    ],
    "order_total": 1200.0,
    "payment_method": "cash_on_delivery",
    "delivery_preference": "home_delivery",
    "special_instructions": "Call 5 minutes before delivery"
  }
}
```

#### `POST /chat/session/{session_id}/order/update`

Update order context (customer info, preferences, etc.).

```bash
curl -X POST http://localhost:8001/chat/session/550e8400-e29b-41d4-a716-446655440000/order/update \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "Ahmed Khan",
    "phone_number": "+92-300-1234567",
    "delivery_address": "House 123, Street 5, Gulberg III, Lahore",
    "payment_method": "cash_on_delivery"
  }'
```

#### `POST /chat/session/{session_id}/order/add`

Add an item to the current order.

```bash
curl -X POST http://localhost:8001/chat/session/550e8400-e29b-41d4-a716-446655440000/order/add \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Peri Peri Pizza",
    "size": "Large",
    "price": 1200.0,
    "quantity": 1,
    "special_instructions": "Extra spicy"
  }'
```

#### `DELETE /chat/session/{session_id}/order/remove/{item_index}`

Remove an item from the current order.

```bash
curl -X DELETE http://localhost:8001/chat/session/550e8400-e29b-41d4-a716-446655440000/order/remove/0
```

#### `DELETE /chat/session/{session_id}/order/clear`

Clear the entire order.

```bash
curl -X DELETE http://localhost:8001/chat/session/550e8400-e29b-41d4-a716-446655440000/order/clear
```

### Session Information

#### `GET /chat/session/{session_id}/summary`

Get comprehensive session summary including order context.

```bash
curl http://localhost:8001/chat/session/550e8400-e29b-41d4-a716-446655440000/summary
```

**Response:**

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": 1704110400.0,
  "last_activity": 1704110500.0,
  "message_count": 5,
  "order_context": {
    "customer_name": "Ahmed Khan",
    "phone_number": "+92-300-1234567",
    "delivery_address": "House 123, Street 5, Gulberg III, Lahore",
    "current_order": [...],
    "order_total": 1200.0,
    "payment_method": "cash_on_delivery",
    "delivery_preference": "home_delivery",
    "special_instructions": "Call 5 minutes before delivery"
  },
  "metadata": {}
}
```

## 💡 Usage Examples

### Basic Order Flow

```python
import httpx
import asyncio

async def basic_order_flow():
    async with httpx.AsyncClient() as client:
        # 1. Create new session
        session_response = await client.post("http://localhost:8001/chat/new")
        session_id = session_response.json()["session_id"]

        # 2. Update customer information
        customer_info = {
            "customer_name": "Ahmed Khan",
            "phone_number": "+92-300-1234567",
            "delivery_address": "House 123, Street 5, Gulberg III, Lahore",
            "payment_method": "cash_on_delivery"
        }
        await client.post(f"http://localhost:8001/chat/session/{session_id}/order/update",
                         json=customer_info)

        # 3. Start conversation
        chat_response = await client.post("http://localhost:8001/chat", json={
            "prompt": "Hi, I'd like to order a pizza",
            "session_id": session_id
        })

        # 4. Add items to order
        pizza_item = {
            "name": "Peri Peri Pizza",
            "size": "Large",
            "price": 1200.0,
            "quantity": 1
        }
        await client.post(f"http://localhost:8001/chat/session/{session_id}/order/add",
                         json=pizza_item)

        # 5. Continue conversation with context
        follow_up = await client.post("http://localhost:8001/chat", json={
            "prompt": "What's in my order and when will it be delivered?",
            "session_id": session_id
        })

        print(f"Response: {follow_up.json()['response']}")

asyncio.run(basic_order_flow())
```

### Order Management

```python
async def order_management():
    async with httpx.AsyncClient() as client:
        # Create session
        session_response = await client.post("http://localhost:8001/chat/new")
        session_id = session_response.json()["session_id"]

        # Add multiple items
        items = [
            {"name": "Peri Peri Pizza", "price": 1200.0, "quantity": 1},
            {"name": "BBQ Wings", "price": 450.0, "quantity": 1},
            {"name": "Coke", "price": 100.0, "quantity": 2}
        ]

        for item in items:
            await client.post(f"http://localhost:8001/chat/session/{session_id}/order/add",
                             json=item)

        # Get order context
        order_context = await client.get(f"http://localhost:8001/chat/session/{session_id}/order")
        print(f"Order total: Rs. {order_context.json()['order_context']['order_total']}")

        # Remove an item
        await client.delete(f"http://localhost:8001/chat/session/{session_id}/order/remove/0")

        # Get updated context
        updated_order = await client.get(f"http://localhost:8001/chat/session/{session_id}/order")
        print(f"Updated total: Rs. {updated_order.json()['order_context']['order_total']}")

asyncio.run(order_management())
```

## 🔄 Integration with Chat

The order context is automatically integrated with the chat system. When you send a message with a session ID, the LLM:

1. **Retrieves conversation history** from the session
2. **Includes order context** in the system prompt
3. **Provides context-aware responses** based on the current order
4. **Updates conversation memory** with the new interaction

### Enhanced System Prompt

The LLM automatically receives order context in its system prompt:

```
You are a friendly and knowledgeable representative of Saad's Restaurant...

Current Order Context:
- Customer: Ahmed Khan
- Phone: +92-300-1234567
- Address: House 123, Street 5, Gulberg III, Lahore
- Current Order: Peri Peri Pizza (Large) - Rs. 1200
- Order Total: Rs. 1200
- Payment Method: Cash on Delivery
- Special Instructions: Call 5 minutes before delivery

Remember previous parts of the conversation to provide contextual responses.
```

## 📊 Monitoring and Analytics

### Session Statistics

```bash
# Get all active sessions
curl http://localhost:8001/stats

# Get specific session summary
curl http://localhost:8001/chat/session/{session_id}/summary
```

### Order Analytics

You can track:

- Number of active orders
- Average order value
- Popular items
- Customer preferences
- Session duration

## 🛡️ Security and Privacy

### Session Isolation

- Each session is completely isolated
- No cross-session data sharing
- Automatic session cleanup after 24 hours

### Data Protection

- All data stored in memory (not persistent)
- No external database dependencies
- Configurable data retention policies

## 🔧 Configuration

### Memory Settings

```python
# In main.py - ConversationMemory class
max_conversations = 1000  # Maximum active conversations
max_messages_per_conversation = 50  # Messages per conversation
cleanup_interval = 3600  # Cleanup every hour
conversation_ttl = 24 * 3600  # 24 hours
```

### Order Context Structure

```python
order_context = {
    'customer_name': None,
    'phone_number': None,
    'delivery_address': None,
    'current_order': [],
    'order_total': 0.0,
    'payment_method': None,
    'delivery_preference': None,
    'special_instructions': None
}
```

## 🚀 Running the Enhanced System

1. **Start the API:**

```bash
python main.py
```

2. **Run the order context demo:**

```bash
python example_order_context.py
```

3. **Test with curl:**

```bash
# Create session
SESSION_ID=$(curl -s -X POST http://localhost:8001/chat/new | jq -r '.session_id')

# Update customer info
curl -X POST "http://localhost:8001/chat/session/$SESSION_ID/order/update" \
  -H "Content-Type: application/json" \
  -d '{"customer_name": "Test Customer", "phone_number": "+92-300-1234567"}'

# Add item to order
curl -X POST "http://localhost:8001/chat/session/$SESSION_ID/order/add" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Pizza", "price": 1000.0, "quantity": 1}'

# Get order context
curl "http://localhost:8001/chat/session/$SESSION_ID/order"
```

## 📈 Benefits

### For Customers

- **Personalized experience** with order history
- **Context-aware responses** that remember preferences
- **Seamless ordering** without repeating information
- **Order tracking** throughout the conversation

### For Restaurant

- **Better customer service** with full context
- **Order accuracy** with detailed tracking
- **Customer insights** from session data
- **Operational efficiency** with automated order management

### For Developers

- **Simple API** for order management
- **Session isolation** for security
- **Automatic cleanup** for resource management
- **Extensible design** for future enhancements

## 🔮 Future Enhancements

- **Persistent storage** for order history
- **Payment integration** with order context
- **Delivery tracking** integration
- **Customer analytics** dashboard
- **Multi-language support** for order context
- **Advanced order validation** rules
