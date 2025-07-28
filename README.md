# Restaurant Conversational LLM API

A FastAPI application that provides restaurant-related conversational responses using a free LLM from Hugging Face.

## Features

- 🍽️ Restaurant-focused conversational AI
- 🆓 Uses free Hugging Face models (no cost)
- ⚡ FastAPI for high performance
- 🔧 Easy to configure and extend
- 📝 RESTful API endpoints
- 🎯 Specialized restaurant conversation endpoint

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration (Optional)

Create a `.env` file in the root directory:

```bash
# Copy the example file
cp env_example.txt .env

# Edit .env and add your Hugging Face token (optional)
HF_TOKEN=your_huggingface_token_here
```

**Note**: You can use the API without a Hugging Face token, but you'll have rate limits. Get a free token from [Hugging Face Settings](https://huggingface.co/settings/tokens).

### 3. Run the Application

```bash
# Run with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or run directly
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### 1. Health Check

```http
GET /health
```

### 2. General Chat

```http
POST /chat
Content-Type: application/json

{
  "prompt": "What's the best way to cook pasta?",
  "max_length": 150,
  "temperature": 0.7
}
```

### 3. Restaurant-Specific Chat

```http
POST /chat/restaurant
Content-Type: application/json

{
  "prompt": "How do I make a good pizza dough?",
  "max_length": 200,
  "temperature": 0.8
}
```

## Usage Examples

### Using curl

```bash
# General chat
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What are some popular Italian dishes?",
    "max_length": 150,
    "temperature": 0.7
  }'

# Restaurant-specific chat
curl -X POST "http://localhost:8000/chat/restaurant" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "How do I make authentic carbonara?",
    "max_length": 200,
    "temperature": 0.8
  }'
```

### Using Python requests

```python
import requests

# General chat
response = requests.post(
    "http://localhost:8000/chat",
    json={
        "prompt": "What's the best way to cook pasta?",
        "max_length": 150,
        "temperature": 0.7
    }
)
print(response.json())

# Restaurant-specific chat
response = requests.post(
    "http://localhost:8000/chat/restaurant",
    json={
        "prompt": "Can you recommend a vegetarian dish?",
        "max_length": 200,
        "temperature": 0.8
    }
)
print(response.json())
```

## API Documentation

Once the server is running, you can access:

- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc

## Model Information

The API currently uses:

- **Model**: `microsoft/DialoGPT-medium`
- **Provider**: Hugging Face (free tier)
- **Type**: Conversational AI

You can easily change the model by modifying the `MODEL_ID` variable in `main.py`.

## Alternative Models

You can switch to other free models by changing the `MODEL_ID` in `main.py`:

```python
# Some alternative free models:
MODEL_ID = "microsoft/DialoGPT-small"  # Smaller, faster
MODEL_ID = "microsoft/DialoGPT-large"  # Larger, more capable
MODEL_ID = "EleutherAI/gpt-neo-125M"   # Different architecture
```

## Error Handling

The API includes comprehensive error handling for:

- Network timeouts
- Model API errors
- Invalid requests
- Server errors

## Rate Limits

- **Without token**: Limited requests per hour
- **With token**: Higher rate limits
- **Free tier**: Suitable for development and small-scale use

## Contributing

Feel free to contribute by:

1. Adding new endpoints
2. Improving error handling
3. Adding more model options
4. Enhancing documentation

## License

This project is open source and available under the MIT License.
