# OpenPecha Search API

A powerful search API for Tibetan texts using hybrid, BM25, and semantic search powered by Milvus vector database and Google Gemini embeddings.

## Features

- 🔍 **Three Search Methods**:
  - **Hybrid Search**: Combines BM25 and semantic search using RRF (Reciprocal Rank Fusion)
  - **BM25 Search**: Traditional keyword-based search (sparse vector)
  - **Semantic Search**: AI-powered meaning-based search (dense vector)

- 🎯 **Filtering**: Filter results by title field
- ⚡ **Fast & Scalable**: Built with FastAPI and Milvus
- 🔒 **Secure**: Environment-based credential management
- 📚 **Auto Documentation**: Interactive API docs at `/docs`

## Prerequisites

- Python 3.8+
- Milvus/Zilliz Cloud account
- Google Gemini API key

## Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd openpecha_search
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Create `.env` file** in the project root:
```bash
# Milvus/Zilliz Cloud Configuration
MILVUS_URI=your_milvus_uri_here
MILVUS_TOKEN=your_milvus_token_here
MILVUS_COLLECTION_NAME=test_kangyur_tengyur

# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
```

## Running the API

### Development Mode
```bash
python api.py
```

Or using uvicorn directly:
```bash
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode
```bash
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

The API will be available at: `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- **Interactive Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### 1. Hybrid Search
**POST** `/search/hybrid`

Combines BM25 and semantic search for best results.

**Request Body**:
```json
{
  "query": "ཕམ་པར་གྱུར་བའི་ཆོས་དུན་པ",
  "limit": 10,
  "filter": {
    "title": "Dorjee"
  }
}
```

**Response**:
```json
{
  "query": "ཕམ་པར་གྱུར་བའི་ཆོས་དུན་པ",
  "search_type": "hybrid",
  "results": [
    {
      "id": "123",
      "distance": 0.85,
      "entity": {
        "title": "Dorjee",
        "text": "..."
      }
    }
  ],
  "count": 10
}
```

### 2. BM25 Search
**POST** `/search/bm25`

Traditional keyword-based search. Best for exact term matching.

**Request Body**:
```json
{
  "query": "ཕམ་པར་གྱུར་བའི་ཆོས་དུན་པ",
  "limit": 10,
  "filter": {
    "title": "Dorjee"
  }
}
```

### 3. Semantic Search
**POST** `/search/semantic`

AI-powered semantic search. Best for finding conceptually similar content.

**Request Body**:
```json
{
  "query": "ཕམ་པར་གྱུར་བའི་ཆོས་དུན་པ",
  "limit": 10,
  "filter": {
    "title": "Dorjee"
  }
}
```

### 4. Health Check
**GET** `/health`

Check API health status.

**Response**:
```json
{
  "status": "healthy",
  "milvus_connected": true,
  "gemini_configured": true
}
```

## Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | The search query text |
| `limit` | integer | No | 10 | Maximum results to return (1-100) |
| `filter.title` | string | No | - | Filter results by title |

## Example Usage

### Using cURL

**Hybrid Search**:
```bash
curl -X POST "http://localhost:8000/search/hybrid" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ཕམ་པར་གྱུར་བའི་ཆོས་དུན་པ",
    "limit": 5
  }'
```

**With Filter**:
```bash
curl -X POST "http://localhost:8000/search/bm25" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ཕམ་པར་གྱུར་བའི་ཆོས་དུན་པ",
    "limit": 10,
    "filter": {
      "title": "Dorjee"
    }
  }'
```

### Using Python

```python
import requests

url = "http://localhost:8000/search/hybrid"
payload = {
    "query": "ཕམ་པར་གྱུར་བའི་ཆོས་དུན་པ",
    "limit": 10,
    "filter": {
        "title": "Dorjee"
    }
}

response = requests.post(url, json=payload)
results = response.json()

print(f"Found {results['count']} results")
for result in results['results']:
    print(f"ID: {result['id']}, Distance: {result['distance']}")
    print(f"Title: {result['entity']['title']}")
```

### Using JavaScript

```javascript
const searchData = {
  query: "ཕམ་པར་གྱུར་བའི་ཆོས་དུན་པ",
  limit: 10,
  filter: {
    title: "Dorjee"
  }
};

fetch('http://localhost:8000/search/semantic', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(searchData),
})
  .then(response => response.json())
  .then(data => {
    console.log('Search Results:', data);
    console.log(`Found ${data.count} results`);
  });
```

## Search Method Comparison

| Method | Best For | Speed | Accuracy |
|--------|----------|-------|----------|
| **Hybrid** | General purpose, balanced results | Medium | High |
| **BM25** | Exact keyword matching, term frequency | Fast | Good for keywords |
| **Semantic** | Conceptual similarity, meaning-based | Medium | High for context |

## Project Structure

```
openpecha_search/
├── api.py              # FastAPI application with endpoints
├── main.py             # Original test script
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (not in git)
├── .env.example       # Example environment variables
├── README.md          # This file
└── LICENSE            # License file
```

## Environment Variables

Create a `.env` file with the following variables:

```bash
# Required
MILVUS_URI=your_milvus_uri
MILVUS_TOKEN=your_milvus_token
GEMINI_API_KEY=your_gemini_api_key

# Optional
MILVUS_COLLECTION_NAME=test_kangyur_tengyur  # Default collection name
```

## Error Handling

The API returns appropriate HTTP status codes:

- `200`: Success
- `400`: Bad request (invalid parameters)
- `422`: Validation error (missing required fields)
- `500`: Server error (search failed, connection issues)

Error response format:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Development

### Running Tests
```bash
# Add your test commands here
pytest
```

### Code Formatting
```bash
black api.py
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the terms specified in the LICENSE file.

## Troubleshooting

### Common Issues

1. **"MILVUS_URI environment variable is not set"**
   - Make sure `.env` file exists and contains all required variables
   - Check that `python-dotenv` is installed

2. **"Error generating embedding"**
   - Verify your Gemini API key is valid
   - Check your internet connection

3. **"Connection refused"**
   - Ensure Milvus/Zilliz Cloud is accessible
   - Verify URI and token are correct

## Support

For issues and questions:
- Open an issue on GitHub
- Contact the maintainers

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Vector search powered by [Milvus](https://milvus.io/)
- Embeddings by [Google Gemini](https://ai.google.dev/)
