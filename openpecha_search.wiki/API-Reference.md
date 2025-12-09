# API Reference

Complete documentation for all OpenPecha Search API endpoints.

---

## Base URL

```
http://localhost:8001
```

---

## Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API information |
| POST | `/search` | Unified search endpoint |
| GET | `/health` | Health check |
| GET | `/debug/search` | Debug search functionality |
| GET | `/docs` | Interactive API documentation |
| GET | `/redoc` | Alternative API documentation |

---

## Root Endpoint

### `GET /`

Returns basic API information and available endpoints.

#### Response

```json
{
  "message": "OpenPecha Search API",
  "version": "1.0.0",
  "endpoints": {
    "search": "/search"
  },
  "search_types": {
    "hybrid": "Combined BM25 + semantic search (default)",
    "bm25": "Keyword-based search",
    "semantic": "Meaning-based search",
    "exact": "Exact phrase matching"
  },
  "docs": "/docs"
}
```

---

## Search Endpoint

### `POST /search`

The main search endpoint supporting all search types.

#### Request Body

```json
{
  "query": "string (required)",
  "search_type": "string (optional, default: 'hybrid')",
  "limit": "integer (optional, default: 10)",
  "return_text": "boolean (optional, default: true)",
  "hierarchical": "boolean (optional, default: false)",
  "parent_limit": "integer (optional)",
  "filter": {
    "title": "string or array (optional)",
    "language": "string or array (optional)"
  }
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | ✅ Yes | - | The search query text (min 1 character) |
| `search_type` | string | No | `"hybrid"` | Search method: `"hybrid"`, `"bm25"`, `"semantic"`, `"exact"` |
| `limit` | integer | No | `10` | Max results to return (1-100) |
| `return_text` | boolean | No | `true` | Include full text in results |
| `hierarchical` | boolean | No | `false` | Enable two-stage parent→children search |
| `parent_limit` | integer | No | `limit` | Max parents in hierarchical mode (1-200) |
| `filter` | object | No | `null` | Filter criteria |
| `filter.title` | string \| array | No | - | Filter by title(s) |
| `filter.language` | string \| array | No | - | Filter by language(s) |

#### Response

```json
{
  "query": "string",
  "search_type": "string",
  "results": [
    {
      "id": "string",
      "distance": "float",
      "entity": {
        "text": "string (if return_text=true)",
        "language": "string (if return_text=true)"
      }
    }
  ],
  "count": "integer"
}
```

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `query` | string | The original query |
| `search_type` | string | Search method used |
| `results` | array | List of search results |
| `results[].id` | string | Document ID |
| `results[].distance` | float | Similarity/relevance score |
| `results[].entity` | object | Document data |
| `count` | integer | Total results returned |

---

### Search Examples

#### Basic Hybrid Search

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད། །",
    "search_type": "hybrid",
    "limit": 10
  }'
```

#### Semantic Search (English Query)

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how to worry less?",
    "search_type": "semantic",
    "limit": 5
  }'
```

#### BM25 Search (Tibetan Keywords)

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ཕམ་པར་གྱུར་བའི་ཆོས་དུན་པ",
    "search_type": "bm25",
    "limit": 10,
    "return_text": false
  }'
```

#### Exact Phrase Match

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད། །",
    "search_type": "exact",
    "limit": 10
  }'
```

#### With Title Filter

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "བདེ་བ་ཐོབ་པའི་ཐབས",
    "search_type": "hybrid",
    "limit": 10,
    "filter": {
      "title": "Dorjee"
    }
  }'
```

#### With Multiple Title Filters

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "བདེ་བ་ཐོབ་པའི་ཐབས",
    "search_type": "hybrid",
    "limit": 10,
    "filter": {
      "title": ["Dorjee", "Kangyur", "Tengyur"]
    }
  }'
```

#### Hierarchical Search

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "བདེ་བ་ཐོབ་པའི་ཐབས",
    "search_type": "hybrid",
    "hierarchical": true,
    "parent_limit": 20,
    "limit": 50,
    "filter": {
      "title": "Some Title"
    }
  }'
```

---

## Health Check

### `GET /health`

Check API health and service connectivity.

#### Response

```json
{
  "status": "healthy",
  "milvus_connected": true,
  "gemini_configured": true
}
```

#### Status Codes

| Code | Meaning |
|------|---------|
| 200 | API is healthy |
| 500 | Internal server error |

---

## Debug Endpoint

### `GET /debug/search`

Test basic search functionality for debugging purposes.

#### Response (Success)

```json
{
  "status": "success",
  "raw_results": "string",
  "results_type": "string",
  "results_length": "integer",
  "first_result": "string"
}
```

#### Response (Error)

```json
{
  "status": "error",
  "error": "string",
  "error_type": "string"
}
```

---

## Error Responses

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid search_type or parameters |
| 422 | Validation Error | Missing required fields, invalid types |
| 500 | Server Error | Search failed, connection issues |

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Errors

#### Invalid Search Type

```json
{
  "detail": "Invalid search_type. Must be one of: hybrid, bm25, semantic, exact"
}
```

#### Missing Query

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "query"],
      "msg": "Field required"
    }
  ]
}
```

#### Embedding Generation Failed

```json
{
  "detail": "Error generating embedding: API key invalid"
}
```

#### Search Failed

```json
{
  "detail": "Search failed: Connection timeout"
}
```

---

## Data Models

### SearchRequest

```python
class SearchRequest(BaseModel):
    query: str                    # Required, min_length=1
    search_type: str = "hybrid"   # hybrid|bm25|semantic|exact
    limit: int = 10               # 1-100
    return_text: bool = True
    hierarchical: bool = False
    parent_limit: Optional[int]   # 1-200
    filter: Optional[SearchFilter]
```

### SearchFilter

```python
class SearchFilter(BaseModel):
    title: Optional[Union[str, List[str]]]
    language: Optional[Union[str, List[str]]]
```

### SearchResult

```python
class SearchResult(BaseModel):
    id: Any
    distance: float
    entity: Dict[str, Any]
```

### SearchResponse

```python
class SearchResponse(BaseModel):
    query: str
    search_type: str
    results: List[SearchResult]
    count: int
```

---

## Filter Expressions

The API automatically builds Milvus filter expressions from the `filter` object.

### Single Value Filter

```json
{
  "filter": {
    "title": "Dorjee"
  }
}
```

Generates: `title == "Dorjee"`

### Multiple Values Filter

```json
{
  "filter": {
    "title": ["Dorjee", "Kangyur"]
  }
}
```

Generates: `title in ["Dorjee", "Kangyur"]`

### Combined Filters

```json
{
  "filter": {
    "title": "Dorjee",
    "language": "bo"
  }
}
```

Generates: `title == "Dorjee" && language == "bo"`

---

## Rate Limits & Best Practices

### Recommendations

1. **Limit Results**: Use reasonable `limit` values (10-50 for most cases)
2. **Return Text**: Set `return_text: false` when you only need IDs
3. **Use Filters**: Apply filters to narrow results and improve performance
4. **Choose Search Type**: Pick the appropriate search type for your use case

### Performance Tips

| Tip | Impact |
|-----|--------|
| Lower `limit` | Faster response |
| `return_text: false` | Less data transfer |
| Use filters | Fewer results to process |
| BM25 for keywords | Fastest for exact terms |

---

## Interactive Documentation

Access auto-generated interactive documentation at:

- **Swagger UI**: `http://localhost:8001/docs`
- **ReDoc**: `http://localhost:8001/redoc`

These provide:
- Try-it-out functionality
- Request/response schemas
- Example values
- Full API exploration

---

*Next: [Code Walkthrough](Code-Walkthrough) for detailed code explanation.*
