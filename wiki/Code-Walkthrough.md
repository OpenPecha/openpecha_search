# Code Walkthrough

A detailed explanation of the OpenPecha Search API codebase.

---

## Project Structure

```
openpecha_search/
├── api.py              # FastAPI application (main API)
├── main.py             # Test/demo script
├── requirements.txt    # Python dependencies
├── .env               # Environment variables (not in git)
└── README.md          # Project documentation
```

---

## api.py - The FastAPI Application

This is the main API file. Let's walk through each section.

### 1. Imports

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
import os
from dotenv import load_dotenv
from google import genai
from google.genai.types import EmbedContentConfig
from pymilvus import MilvusClient, AnnSearchRequest, RRFRanker
```

| Import | Purpose |
|--------|---------|
| `FastAPI` | Web framework for building the API |
| `HTTPException` | Raise HTTP error responses |
| `CORSMiddleware` | Handle Cross-Origin Resource Sharing |
| `BaseModel`, `Field` | Data validation with Pydantic |
| `dotenv` | Load environment variables from `.env` |
| `genai` | Google Gemini AI for embeddings |
| `pymilvus` | Milvus vector database client |

---

### 2. Environment Configuration

```python
# Load environment variables from .env file
load_dotenv()

# Get credentials from environment variables
MILVUS_URI = os.getenv("MILVUS_URI")
MILVUS_TOKEN = os.getenv("MILVUS_TOKEN")
MILVUS_COLLECTION_NAME = os.getenv("MILVUS_COLLECTION_NAME", "production")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Validate required environment variables
if not MILVUS_URI:
    raise ValueError("MILVUS_URI environment variable is not set")
if not MILVUS_TOKEN:
    raise ValueError("MILVUS_TOKEN environment variable is not set")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")
```

**What this does:**
1. Loads variables from `.env` file
2. Retrieves each required credential
3. Validates that all required variables exist
4. Raises an error at startup if anything is missing

---

### 3. FastAPI Application Setup

```python
# Initialize FastAPI app
app = FastAPI(
    title="OpenPecha Search API",
    description="API for searching Tibetan texts using hybrid, BM25, and semantic search",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**FastAPI Configuration:**
- `title`: Appears in documentation
- `description`: API description for docs
- `version`: API version number

**CORS Middleware:**
- Allows cross-origin requests (needed for web frontends)
- `allow_origins=["*"]` allows all origins (restrict in production)

---

### 4. Client Initialization

```python
# Initialize Milvus client
milvus_client = MilvusClient(
    uri=MILVUS_URI,
    token=MILVUS_TOKEN
)

# Initialize Gemini client
genai_client = genai.Client(api_key=GEMINI_API_KEY)
doc_cfg = EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT", output_dimensionality=768)
```

**Milvus Client:**
- Connects to Milvus/Zilliz Cloud
- Uses URI and token for authentication

**Gemini Client:**
- Initializes Google's Gemini AI
- `doc_cfg` configures embeddings:
  - `task_type="RETRIEVAL_DOCUMENT"`: Optimized for document retrieval
  - `output_dimensionality=768`: 768-dimensional vectors

---

### 5. Pydantic Models

#### SearchFilter Model

```python
class SearchFilter(BaseModel):
    title: Optional[Union[str, List[str]]] = Field(
        None, 
        description="Filter results by title or list of titles"
    )
    language: Optional[Union[str, List[str]]] = Field(
        None, 
        description="Filter results by language or list of languages"
    )
```

**Purpose:** Defines filter options for search queries
- `title`: Can be a single string or list of strings
- `language`: Can be a single string or list of strings
- Both are optional (`None` default)

#### SearchRequest Model

```python
class SearchRequest(BaseModel):
    query: str = Field(
        ...,  # ... means required
        description="The search query text",
        min_length=1,
        examples=["དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད། །"]
    )
    search_type: str = Field(
        "hybrid",
        description="Type of search: 'hybrid', 'bm25', 'semantic', or 'exact'",
        examples=["hybrid"]
    )
    limit: int = Field(
        10,
        description="Maximum number of results to return",
        ge=1, le=100,  # Between 1 and 100
        examples=[10]
    )
    return_text: bool = Field(
        True,
        description="If True, return full text in results"
    )
    hierarchical: bool = Field(
        False,
        description="If true, perform parent->children two-stage search"
    )
    parent_limit: Optional[int] = Field(
        None,
        description="Max parents to retrieve when hierarchical=true",
        ge=1, le=200
    )
    filter: Optional[SearchFilter] = Field(
        None,
        description="Optional filters to apply"
    )
```

**Key Features:**
- `query` is required (`...`)
- `limit` is constrained (`ge=1, le=100`)
- `examples` appear in documentation
- Nested `SearchFilter` for filtering

#### Response Models

```python
class SearchResult(BaseModel):
    id: Any
    distance: float
    entity: Dict[str, Any]

class SearchResponse(BaseModel):
    query: str
    search_type: str
    results: List[SearchResult]
    count: int
```

---

### 6. Helper Functions

#### Embedding Generation

```python
def get_embedding(text: str) -> List[float]:
    """Generate embedding for the given text using Gemini."""
    try:
        resp = genai_client.models.embed_content(
            model="gemini-embedding-001",
            contents=text,
            config=doc_cfg,
        )
        return [i.values for i in resp.embeddings][0]
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating embedding: {str(e)}"
        )
```

**What it does:**
1. Calls Gemini's embedding API
2. Uses `gemini-embedding-001` model
3. Returns first embedding's values
4. Raises HTTP 500 on failure

#### Filter Expression Builder

```python
def build_filter_expression(filter_obj: Optional[SearchFilter]) -> Optional[str]:
    """Build Milvus filter expression from filter object."""
    if not filter_obj:
        return None
    
    conditions = []
    if filter_obj.title:
        if isinstance(filter_obj.title, list):
            titles = [_escape_milvus_string(str(title)) 
                     for title in filter_obj.title if str(title).strip() != ""]
            if titles:
                conditions.append(f'title in ["{"\", \"".join(titles)}"]')
        else:
            conditions.append(f'title == "{_escape_milvus_string(str(filter_obj.title))}"')
    
    # Similar for language...
    
    return " && ".join(conditions) if conditions else None
```

**What it does:**
1. Returns `None` if no filter
2. Builds conditions for each field
3. Handles single value vs list
4. Escapes strings for Milvus
5. Joins with `&&` (AND)

**Generated expressions:**
- Single: `title == "Dorjee"`
- List: `title in ["Dorjee", "Kangyur"]`
- Combined: `title == "Dorjee" && language == "bo"`

#### String Escaping

```python
def _escape_milvus_string(value: str) -> str:
    """Escape characters for use inside Milvus string literals."""
    return value.replace("\\", "\\\\").replace('"', '\\"')
```

Escapes backslashes and quotes to prevent injection.

#### Filter Combination

```python
def combine_filters(*filters: Optional[str]) -> Optional[str]:
    """Combine multiple filter expressions using logical AND."""
    parts = [f for f in filters if f]
    return " && ".join(parts) if parts else None
```

Combines multiple filter strings with AND logic.

#### Results Formatting

```python
def format_results(results: List, query: str, search_type: str) -> SearchResponse:
    """Format raw Milvus results into SearchResponse."""
    formatted_results = []
    
    for result_list in results:
        for hit in result_list:
            formatted_results.append(SearchResult(
                id=hit.get('id'),
                distance=hit.get('distance', 0.0),
                entity=hit.get('entity', {})
            ))
    
    return SearchResponse(
        query=query,
        search_type=search_type,
        results=formatted_results,
        count=len(formatted_results)
    )
```

Converts raw Milvus results to structured `SearchResponse`.

---

### 7. API Endpoints

#### Root Endpoint

```python
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "OpenPecha Search API",
        "version": "1.0.0",
        "endpoints": {"search": "/search"},
        "search_types": {
            "hybrid": "Combined BM25 + semantic search (default)",
            "bm25": "Keyword-based search",
            "semantic": "Meaning-based search",
            "exact": "Exact phrase matching"
        },
        "docs": "/docs"
    }
```

Returns API information and available search types.

#### Main Search Endpoint

```python
@app.post("/search", response_model=SearchResponse)
async def unified_search_post(req: SearchRequest):
    """Unified search endpoint (POST) accepting JSON body."""
    try:
        search_type_lower = req.search_type.lower()
        
        # Validate search type
        valid_types = ["hybrid", "bm25", "semantic", "exact"]
        if search_type_lower not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid search_type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Build filter expression
        base_filter_expr = build_filter_expression(req.filter)
        
        # Non-hierarchical search
        if not req.hierarchical:
            if search_type_lower == "hybrid":
                return await perform_hybrid_search(...)
            elif search_type_lower == "bm25":
                return await perform_bm25_search(...)
            # ... etc
        
        # Hierarchical search (two-stage)
        # Stage 1: Find parents
        parent_filter = combine_filters(base_filter_expr, 'parent_id == ""')
        parent_resp = await perform_search(query, parent_filter)
        
        # Stage 2: Find children of matched parents
        parent_ids = [r.id for r in parent_resp.results]
        children_filter = build_children_filter_from_parents(parent_ids)
        return await perform_search(query, children_filter)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
```

**Flow:**
1. Validate search type
2. Build filter expression
3. If hierarchical: two-stage search
4. Otherwise: single-stage search
5. Handle errors appropriately

---

### 8. Search Implementation Functions

#### Hybrid Search

```python
async def perform_hybrid_search(query, limit, filter_expr, return_text=True):
    """Perform hybrid search combining BM25 and semantic search."""
    # Get embedding for semantic search
    embedding = get_embedding(query)
    
    # BM25 search parameters
    search_param_1 = {
        "data": [query],
        "anns_field": "sparce_vector",
        "param": {},
        "limit": limit
    }
    if filter_expr:
        search_param_1["expr"] = filter_expr
    request_1 = AnnSearchRequest(**search_param_1)
    
    # Semantic search parameters
    search_param_2 = {
        "data": [embedding],
        "anns_field": "dense_vector",
        "param": {"drop_ratio_search": 0.2},
        "limit": limit
    }
    if filter_expr:
        search_param_2["expr"] = filter_expr
    request_2 = AnnSearchRequest(**search_param_2)
    
    # Combine with RRF ranker
    output_fields = ['text', 'language'] if return_text else []
    ranker = RRFRanker()
    
    results = milvus_client.hybrid_search(
        collection_name=MILVUS_COLLECTION_NAME,
        reqs=[request_1, request_2],
        ranker=ranker,
        limit=limit,
        output_fields=output_fields
    )
    
    return format_results(results, query, "hybrid")
```

**Key points:**
- Creates two `AnnSearchRequest` objects (BM25 + Semantic)
- Uses `RRFRanker()` to combine results
- `drop_ratio_search: 0.2` = speed/accuracy tradeoff for dense vectors

#### BM25 Search

```python
async def perform_bm25_search(query, limit, filter_expr, return_text=True):
    """Perform BM25 (sparse vector) search."""
    output_fields = ['text', 'language'] if return_text else []
    
    search_params = {
        "collection_name": MILVUS_COLLECTION_NAME,
        "data": [query],
        "anns_field": "sparce_vector",  # Note: typo in original
        "limit": limit,
        "output_fields": output_fields
    }
    
    if filter_expr:
        search_params["filter"] = filter_expr
    
    results = milvus_client.search(**search_params)
    return format_results(results, query, "bm25")
```

**Key points:**
- Searches on `sparce_vector` field (BM25 index)
- Passes raw query text (Milvus handles tokenization)

#### Semantic Search

```python
async def perform_semantic_search(query, limit, filter_expr, return_text=True):
    """Perform semantic (dense vector) search."""
    embedding = get_embedding(query)  # Generate embedding first
    
    search_params = {
        "collection_name": MILVUS_COLLECTION_NAME,
        "data": [embedding],  # Use embedding, not text
        "anns_field": "dense_vector",
        "limit": limit,
        "output_fields": output_fields
    }
    
    results = milvus_client.search(**search_params)
    return format_results(results, query, "semantic")
```

**Key difference:** Uses embedding vector, not raw text.

#### Exact Match Search

```python
async def perform_exact_search(query, limit, filter_expr, return_text=True):
    """Perform exact phrase match search."""
    # Escape single quotes
    escaped_query = query.replace("'", "\\'")
    
    # Build PHRASE_MATCH filter
    phrase_filter = f"PHRASE_MATCH(text, '{escaped_query}')"
    
    # Combine filters
    if filter_expr:
        final_filter = f"{phrase_filter} && {filter_expr}"
    else:
        final_filter = phrase_filter
    
    search_params = {
        "collection_name": MILVUS_COLLECTION_NAME,
        "data": [query],
        "anns_field": "sparce_vector",
        "limit": limit,
        "output_fields": output_fields,
        "filter": final_filter  # PHRASE_MATCH as filter
    }
    
    results = milvus_client.search(**search_params)
    return format_results(results, query, "exact")
```

**Key points:**
- Uses `PHRASE_MATCH()` in filter expression
- Escapes quotes to prevent syntax errors
- Still uses BM25 index as base search

---

### 9. Health & Debug Endpoints

```python
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "milvus_connected": True,
        "gemini_configured": True
    }

@app.get("/debug/search")
async def debug_search():
    """Debug endpoint to test basic search functionality."""
    try:
        results = milvus_client.search(
            collection_name=MILVUS_COLLECTION_NAME,
            data=["how to worry less?"],
            anns_field="sparce_vector",
            limit=5,
            output_fields=["text"]
        )
        return {"status": "success", "raw_results": str(results), ...}
    except Exception as e:
        return {"status": "error", "error": str(e), ...}
```

---

### 10. Application Entry Point

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

Runs the server on port 8001 when executed directly.

---

## main.py - Test/Demo Script

This file demonstrates the search capabilities without the API layer.

### Key Sections

#### Client Setup

```python
from google import genai
from pymilvus import MilvusClient, AnnSearchRequest, RRFRanker

client = MilvusClient(
    uri=MILVUS_URI,
    token=MILVUS_TOKEN,
    collection_name=MILVUS_COLLECTION_NAME
)

genai_client = genai.Client(api_key=GEMINI_API_KEY)
```

#### Embedding Generation

```python
doc_cfg = EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT", output_dimensionality=768)
query = "how to worry less?"
resp = genai_client.models.embed_content(
    model="gemini-embedding-001",
    contents=query,
    config=doc_cfg,
)
embd = [i.values for i in resp.embeddings]
```

#### Hybrid Search Demo

```python
# BM25 request
search_param_1 = {
    "data": ["how to worry less ?"],
    "anns_field": "sparce_vector",
    "param": {},
    "limit": 2
}
request_1 = AnnSearchRequest(**search_param_1)

# Dense vector request
search_param_2 = {
    "data": embd,
    "anns_field": "dense_vector",
    "param": {"drop_ratio_search": 0.2},
    "limit": 2
}
request_2 = AnnSearchRequest(**search_param_2)

# Hybrid search with RRF
ranker = RRFRanker()
results = client.hybrid_search(
    collection_name=MILVUS_COLLECTION_NAME,
    reqs=[request_1, request_2],
    ranker=ranker,
    limit=2
)
```

#### BM25 Search with PHRASE_MATCH

```python
results2 = client.search(
    collection_name=MILVUS_COLLECTION_NAME,
    data=["དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད། །"],
    anns_field='sparce_vector',
    output_fields=['text'],
    filter="PHRASE_MATCH(text, 'དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད། །')",
    limit=10,
)
```

#### Filtered Search

```python
expr = "title == 'Dorjee'"
results4 = client.search(
    collection_name='test_kangyur_tengyur',
    data=embd,
    anns_field='dense_vector',
    output_fields=['title'],
    limit=10,
    filter=expr
)
```

---

## Summary

| File | Purpose | Key Components |
|------|---------|----------------|
| `api.py` | Production API | FastAPI endpoints, Pydantic models, search functions |
| `main.py` | Demo/testing | Direct Milvus usage, search examples |

---

*Next: [Architecture](Architecture) for system design overview.*
