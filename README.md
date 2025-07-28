# Restaurant LLM API

A FastAPI application that provides restaurant-related conversational responses using OpenRouter's free models with memory and caching.

## 🚀 Deploy to Hugging Face Spaces

### Step 1: Create Hugging Face Account

1. Go to [huggingface.co](https://huggingface.co)
2. Sign up for a free account
3. Verify your email

### Step 2: Create a New Space

1. Click **"New Space"** on your profile
2. Choose **"Docker"** as the SDK
3. Set **Space name**: `restaurant-llm-api`
4. Set **License**: `MIT`
5. Set **Visibility**: `Public` (or Private if you prefer)
6. Click **"Create Space"**

### Step 3: Configure Space Settings

1. In your Space, go to **"Settings"** tab
2. Set **Hardware**: `CPU Basic` (free tier)
3. Set **Docker SDK**: `Docker`
4. Set **Python version**: `3.12`

### Step 4: Add Required Files

#### Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 7860

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]
```

#### Create `.dockerignore`:

```
venv/
__pycache__/
*.pyc
.env
.git/
.gitignore
```

#### Update `requirements.txt` (if needed):

```
fastapi>=0.115.2
uvicorn[standard]==0.22.0
requests==2.31.0
python-dotenv==1.0.0
pydantic>=2.9.2
httpx==0.24.1
```

### Step 5: Set Environment Variables

1. In your Space settings, go to **"Repository secrets"**
2. Add these secrets:
   - `OPENROUTER_API_KEY`: Your OpenRouter API key
   - `PORT`: `7860`

### Step 6: Deploy

1. Commit and push your files to the Space
2. Hugging Face will automatically build and deploy
3. Your API will be available at: `https://your-username-restaurant-llm-api.hf.space`

## 🔧 Local Development

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Set Environment Variables

Create `.env` file:

```
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### Run Locally

```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

## 📡 API Endpoints

- `GET /` - API info and health
- `POST /chat` - Main chat endpoint
- `POST /chat/new` - Start new session
- `GET /models` - List available models
- `GET /menu` - Get restaurant menu

## 🆓 Free Models Available

- `qwen/qwen3-coder:free` - Qwen3 Coder (262K context)
- `google/palm-2-chat-bison` - PaLM 2 Chat
- `anthropic/claude-instant-v1` - Claude Instant

## 🔑 Get OpenRouter API Key

1. Go to [openrouter.ai](https://openrouter.ai)
2. Sign up for free account
3. Get your API key from dashboard
4. Add to environment variables

## 📊 Features

- ✅ Conversation memory
- ✅ Response caching
- ✅ Session management
- ✅ Order context tracking
- ✅ Free LLM models
- ✅ Optimized performance
