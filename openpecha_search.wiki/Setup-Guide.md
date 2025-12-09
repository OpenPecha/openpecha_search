# Setup Guide

Complete instructions for setting up the OpenPecha Search API.

---

## Prerequisites

Before you begin, ensure you have:

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| Python | 3.8+ | `python --version` |
| pip | Latest | `pip --version` |
| Git | Any | `git --version` |

You'll also need accounts for:
- **Milvus/Zilliz Cloud** - Vector database service
- **Google AI (Gemini)** - Embedding generation

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/openpecha_search.git
cd openpecha_search

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env with your credentials

# 5. Run the API
python api.py
```

---

## Detailed Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/openpecha_search.git
cd openpecha_search
```

### Step 2: Create Virtual Environment

Using a virtual environment isolates project dependencies.

**macOS/Linux:**
```bash
python -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Verify activation:**
```bash
which python  # Should show venv path
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies installed:**

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | Latest | Web framework |
| uvicorn[standard] | Latest | ASGI server |
| python-dotenv | Latest | Environment variables |
| pymilvus | Latest | Milvus client |
| google-genai | Latest | Gemini AI SDK |
| tqdm | Latest | Progress bars |

**Verify installation:**
```bash
pip list | grep -E "fastapi|pymilvus|google-genai"
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
touch .env
```

Add the following variables:

```env
# Milvus/Zilliz Cloud Configuration
MILVUS_URI=https://your-cluster.zillizcloud.com
MILVUS_TOKEN=your_milvus_api_token
MILVUS_COLLECTION_NAME=your_collection_name

# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key
```

---

## Getting API Credentials

### Milvus/Zilliz Cloud

1. **Create Account**
   - Go to [Zilliz Cloud](https://cloud.zilliz.com/)
   - Sign up for a free account

2. **Create Cluster**
   - Click "Create Cluster"
   - Choose Free Tier (for development)
   - Select region closest to you

3. **Get Credentials**
   - Go to your cluster dashboard
   - Copy the **Public Endpoint** → `MILVUS_URI`
   - Generate API Key → `MILVUS_TOKEN`

4. **Create Collection**
   - Note your collection name → `MILVUS_COLLECTION_NAME`

### Google Gemini API

1. **Access Google AI Studio**
   - Go to [Google AI Studio](https://aistudio.google.com/)
   - Sign in with Google account

2. **Generate API Key**
   - Click "Get API Key"
   - Create new API key
   - Copy the key → `GEMINI_API_KEY`

---

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `MILVUS_URI` | ✅ Yes | Milvus cluster endpoint | `https://xxx.zillizcloud.com` |
| `MILVUS_TOKEN` | ✅ Yes | Milvus API token | `db_xxx...` |
| `MILVUS_COLLECTION_NAME` | No | Collection name (default: "production") | `openpecha_texts` |
| `GEMINI_API_KEY` | ✅ Yes | Google Gemini API key | `AIza...` |

---

## Running the API

### Development Mode

```bash
python api.py
```

Output:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001 (Press CTRL+C to quit)
```

### With Uvicorn Directly

```bash
uvicorn api:app --host 0.0.0.0 --port 8001 --reload
```

Options:
- `--reload`: Auto-restart on code changes (development only)
- `--host 0.0.0.0`: Accept external connections
- `--port 8001`: Custom port

### Production Mode

```bash
uvicorn api:app --host 0.0.0.0 --port 8001 --workers 4
```

---

## Verify Installation

### 1. Check API is Running

```bash
curl http://localhost:8001/
```

Expected response:
```json
{
  "message": "OpenPecha Search API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

### 2. Check Health

```bash
curl http://localhost:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "milvus_connected": true,
  "gemini_configured": true
}
```

### 3. Test Search

```bash
curl -X POST http://localhost:8001/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "search_type": "bm25", "limit": 5}'
```

### 4. Access Documentation

Open in browser: `http://localhost:8001/docs`

---

## Troubleshooting

### Common Issues

#### 1. "MILVUS_URI environment variable is not set"

**Problem:** Missing environment variables

**Solution:**
```bash
# Verify .env file exists
ls -la .env

# Check .env contents (don't share output!)
cat .env | head -1

# Ensure python-dotenv is installed
pip install python-dotenv
```

#### 2. "Connection refused" to Milvus

**Problem:** Can't connect to Milvus cluster

**Solutions:**
- Verify `MILVUS_URI` is correct
- Check Milvus cluster is running
- Verify network connectivity
- Check API token is valid

```bash
# Test connectivity
curl -v $MILVUS_URI
```

#### 3. "Error generating embedding"

**Problem:** Gemini API issues

**Solutions:**
- Verify `GEMINI_API_KEY` is correct
- Check API key has correct permissions
- Verify quota hasn't been exceeded

```bash
# Test Gemini API directly
curl -X POST \
  "https://generativelanguage.googleapis.com/v1/models/gemini-embedding-001:embedContent?key=$GEMINI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "models/gemini-embedding-001", "content": {"parts": [{"text": "test"}]}}'
```

#### 4. "ModuleNotFoundError: No module named 'xxx'"

**Problem:** Missing Python package

**Solution:**
```bash
# Reinstall all dependencies
pip install -r requirements.txt

# Or install specific package
pip install <package_name>
```

#### 5. Port already in use

**Problem:** Port 8001 is taken

**Solutions:**
```bash
# Option 1: Kill the process using the port
lsof -i :8001
kill -9 <PID>

# Option 2: Use different port
python -c "import uvicorn; uvicorn.run('api:app', host='0.0.0.0', port=8002)"
```

---

## Development Setup

### IDE Configuration

**VS Code Extensions:**
- Python
- Pylance
- REST Client (for testing APIs)

**settings.json:**
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.formatting.provider": "black"
}
```

### Running Tests

```bash
# Run the test/demo script
python main.py
```

### Code Formatting

```bash
# Install formatters
pip install black isort

# Format code
black api.py
isort api.py
```

---

## Docker Setup (Optional)

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Build and Run

```bash
# Build image
docker build -t openpecha-search .

# Run container
docker run -p 8001:8001 --env-file .env openpecha-search
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8001:8001"
    env_file:
      - .env
    restart: unless-stopped
```

```bash
docker-compose up -d
```

---

## Security Best Practices

### 1. Never Commit Credentials

```bash
# Add to .gitignore
echo ".env" >> .gitignore
```

### 2. Use Environment-Specific Configs

```
.env.development
.env.staging
.env.production
```

### 3. Restrict CORS in Production

```python
# In api.py, change:
allow_origins=["*"]  # Development

# To:
allow_origins=["https://yourdomain.com"]  # Production
```

### 4. Use HTTPS in Production

Always deploy behind HTTPS (use nginx, cloud load balancer, etc.)

---

## Next Steps

After setup is complete:

1. **Explore the API** - Visit `http://localhost:8001/docs`
2. **Read the Code** - See [Code Walkthrough](Code-Walkthrough)
3. **Try Examples** - See [Examples](Examples)

---

*Next: [Examples](Examples) for usage examples in multiple languages.*
