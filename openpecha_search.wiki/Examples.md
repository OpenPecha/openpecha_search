# Examples

Usage examples for the OpenPecha Search API in multiple programming languages.

---

## Table of Contents

- [cURL Examples](#curl-examples)
- [Python Examples](#python-examples)
- [JavaScript Examples](#javascript-examples)
- [TypeScript Examples](#typescript-examples)

---

## cURL Examples

### Basic Hybrid Search

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད། །",
    "search_type": "hybrid",
    "limit": 10
  }'
```

### BM25 Keyword Search

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "སངས་རྒྱས་ཀྱི་བསྟན་པ",
    "search_type": "bm25",
    "limit": 10
  }'
```

### Semantic Search (English Query)

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "how to achieve enlightenment",
    "search_type": "semantic",
    "limit": 5
  }'
```

### Exact Phrase Match

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད། །",
    "search_type": "exact",
    "limit": 10
  }'
```

### Search with Title Filter

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "བདེ་བ་ཐོབ་པའི་ཐབས",
    "search_type": "hybrid",
    "limit": 10,
    "filter": {
      "title": "Kangyur"
    }
  }'
```

### Search with Multiple Filters

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "བདེ་བ་ཐོབ་པའི་ཐབས",
    "search_type": "hybrid",
    "limit": 20,
    "filter": {
      "title": ["Kangyur", "Tengyur"],
      "language": "bo"
    }
  }'
```

### Hierarchical Search

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "བདེ་བ་ཐོབ་པའི་ཐབས",
    "search_type": "hybrid",
    "hierarchical": true,
    "parent_limit": 20,
    "limit": 50
  }'
```

### Search Without Text in Response

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "test query",
    "search_type": "bm25",
    "limit": 100,
    "return_text": false
  }'
```

### Health Check

```bash
curl http://localhost:8001/health
```

### API Info

```bash
curl http://localhost:8001/
```

---

## Python Examples

### Basic Setup

```python
import requests

BASE_URL = "http://localhost:8001"

def search(query, search_type="hybrid", limit=10, **kwargs):
    """Perform a search request."""
    payload = {
        "query": query,
        "search_type": search_type,
        "limit": limit,
        **kwargs
    }
    
    response = requests.post(f"{BASE_URL}/search", json=payload)
    response.raise_for_status()
    return response.json()
```

### Hybrid Search

```python
# Simple hybrid search
results = search("དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད། །", "hybrid", 10)

print(f"Found {results['count']} results")
for result in results['results']:
    print(f"ID: {result['id']}, Score: {result['distance']}")
    if 'text' in result['entity']:
        print(f"Text: {result['entity']['text'][:100]}...")
    print("---")
```

### Semantic Search with English Query

```python
# Cross-language semantic search
results = search(
    query="how to overcome suffering and find peace",
    search_type="semantic",
    limit=5
)

for result in results['results']:
    print(f"Score: {result['distance']:.4f}")
    print(f"Text: {result['entity'].get('text', 'N/A')[:200]}")
    print("---")
```

### BM25 Search for Tibetan Keywords

```python
# Keyword-based search
results = search(
    query="སངས་རྒྱས་ཀྱི་བསྟན་པ",
    search_type="bm25",
    limit=10
)

for result in results['results']:
    print(f"ID: {result['id']}")
```

### Exact Match Search

```python
# Find exact phrase
results = search(
    query="དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད། །",
    search_type="exact",
    limit=10
)

print(f"Found {results['count']} exact matches")
```

### Search with Filters

```python
# Single filter
results = search(
    query="བདེ་བ",
    search_type="hybrid",
    limit=10,
    filter={"title": "Kangyur"}
)

# Multiple titles
results = search(
    query="བདེ་བ",
    search_type="hybrid",
    limit=10,
    filter={"title": ["Kangyur", "Tengyur"]}
)

# Combined filters
results = search(
    query="བདེ་བ",
    search_type="hybrid",
    limit=10,
    filter={
        "title": "Kangyur",
        "language": "bo"
    }
)
```

### Hierarchical Search

```python
# Two-stage parent->children search
results = search(
    query="བདེ་བ་ཐོབ་པའི་ཐབས",
    search_type="hybrid",
    hierarchical=True,
    parent_limit=20,
    limit=50
)

print(f"Found {results['count']} child documents")
```

### Complete Python Client

```python
import requests
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass

@dataclass
class SearchResult:
    id: str
    distance: float
    text: Optional[str] = None
    language: Optional[str] = None

class OpenPechaSearchClient:
    """Client for OpenPecha Search API."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def search(
        self,
        query: str,
        search_type: str = "hybrid",
        limit: int = 10,
        return_text: bool = True,
        hierarchical: bool = False,
        parent_limit: Optional[int] = None,
        title: Optional[Union[str, List[str]]] = None,
        language: Optional[Union[str, List[str]]] = None
    ) -> List[SearchResult]:
        """
        Perform a search.
        
        Args:
            query: Search query text
            search_type: 'hybrid', 'bm25', 'semantic', or 'exact'
            limit: Maximum results to return
            return_text: Include text in results
            hierarchical: Enable parent->children search
            parent_limit: Max parents for hierarchical search
            title: Filter by title(s)
            language: Filter by language(s)
        
        Returns:
            List of SearchResult objects
        """
        payload = {
            "query": query,
            "search_type": search_type,
            "limit": limit,
            "return_text": return_text,
            "hierarchical": hierarchical
        }
        
        if parent_limit:
            payload["parent_limit"] = parent_limit
        
        # Build filter
        filter_obj = {}
        if title:
            filter_obj["title"] = title
        if language:
            filter_obj["language"] = language
        if filter_obj:
            payload["filter"] = filter_obj
        
        response = self.session.post(
            f"{self.base_url}/search",
            json=payload
        )
        response.raise_for_status()
        
        data = response.json()
        results = []
        for r in data["results"]:
            results.append(SearchResult(
                id=r["id"],
                distance=r["distance"],
                text=r["entity"].get("text"),
                language=r["entity"].get("language")
            ))
        
        return results


# Usage
if __name__ == "__main__":
    client = OpenPechaSearchClient()
    
    # Check health
    print(client.health_check())
    
    # Perform search
    results = client.search(
        query="how to find peace",
        search_type="semantic",
        limit=5,
        title="Kangyur"
    )
    
    for r in results:
        print(f"ID: {r.id}, Score: {r.distance:.4f}")
        if r.text:
            print(f"Text: {r.text[:100]}...")
```

### Async Python Client

```python
import asyncio
import aiohttp
from typing import Optional, List, Dict, Any

async def async_search(
    query: str,
    search_type: str = "hybrid",
    limit: int = 10,
    base_url: str = "http://localhost:8001"
) -> Dict[str, Any]:
    """Async search function."""
    async with aiohttp.ClientSession() as session:
        payload = {
            "query": query,
            "search_type": search_type,
            "limit": limit
        }
        async with session.post(f"{base_url}/search", json=payload) as response:
            return await response.json()

async def batch_search(queries: List[str], search_type: str = "hybrid"):
    """Run multiple searches concurrently."""
    tasks = [async_search(q, search_type) for q in queries]
    return await asyncio.gather(*tasks)

# Usage
async def main():
    # Single search
    result = await async_search("བདེ་བ", "hybrid", 10)
    print(f"Found {result['count']} results")
    
    # Batch search
    queries = [
        "སངས་རྒྱས",
        "བྱང་ཆུབ",
        "ཆོས"
    ]
    results = await batch_search(queries)
    for q, r in zip(queries, results):
        print(f"Query: {q} -> {r['count']} results")

asyncio.run(main())
```

---

## JavaScript Examples

### Fetch API

```javascript
const BASE_URL = "http://localhost:8001";

async function search(query, searchType = "hybrid", limit = 10, options = {}) {
  const payload = {
    query,
    search_type: searchType,
    limit,
    ...options
  };

  const response = await fetch(`${BASE_URL}/search`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// Usage examples
async function main() {
  // Hybrid search
  const hybridResults = await search("དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད། །", "hybrid", 10);
  console.log(`Found ${hybridResults.count} results`);

  // Semantic search
  const semanticResults = await search("how to find peace", "semantic", 5);
  semanticResults.results.forEach(result => {
    console.log(`Score: ${result.distance}, ID: ${result.id}`);
  });

  // With filters
  const filteredResults = await search("བདེ་བ", "hybrid", 10, {
    filter: {
      title: "Kangyur"
    }
  });
}

main();
```

### Axios

```javascript
const axios = require("axios");

const api = axios.create({
  baseURL: "http://localhost:8001",
  headers: {
    "Content-Type": "application/json"
  }
});

async function search(query, searchType = "hybrid", limit = 10, filter = null) {
  const payload = {
    query,
    search_type: searchType,
    limit
  };

  if (filter) {
    payload.filter = filter;
  }

  const response = await api.post("/search", payload);
  return response.data;
}

// Usage
async function main() {
  try {
    const results = await search("བདེ་བ", "hybrid", 10, {
      title: ["Kangyur", "Tengyur"]
    });
    
    console.log(`Query: ${results.query}`);
    console.log(`Search Type: ${results.search_type}`);
    console.log(`Results: ${results.count}`);
    
    results.results.forEach((result, i) => {
      console.log(`${i + 1}. ID: ${result.id}, Score: ${result.distance.toFixed(4)}`);
    });
  } catch (error) {
    console.error("Search failed:", error.message);
  }
}

main();
```

### Complete JavaScript Client

```javascript
class OpenPechaSearchClient {
  constructor(baseUrl = "http://localhost:8001") {
    this.baseUrl = baseUrl;
  }

  async healthCheck() {
    const response = await fetch(`${this.baseUrl}/health`);
    return response.json();
  }

  async search({
    query,
    searchType = "hybrid",
    limit = 10,
    returnText = true,
    hierarchical = false,
    parentLimit = null,
    filter = null
  }) {
    const payload = {
      query,
      search_type: searchType,
      limit,
      return_text: returnText,
      hierarchical
    };

    if (parentLimit) {
      payload.parent_limit = parentLimit;
    }

    if (filter) {
      payload.filter = filter;
    }

    const response = await fetch(`${this.baseUrl}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Search failed");
    }

    return response.json();
  }

  // Convenience methods
  async hybridSearch(query, limit = 10, filter = null) {
    return this.search({ query, searchType: "hybrid", limit, filter });
  }

  async bm25Search(query, limit = 10, filter = null) {
    return this.search({ query, searchType: "bm25", limit, filter });
  }

  async semanticSearch(query, limit = 10, filter = null) {
    return this.search({ query, searchType: "semantic", limit, filter });
  }

  async exactSearch(query, limit = 10, filter = null) {
    return this.search({ query, searchType: "exact", limit, filter });
  }

  async hierarchicalSearch(query, parentLimit = 20, limit = 50, filter = null) {
    return this.search({
      query,
      searchType: "hybrid",
      hierarchical: true,
      parentLimit,
      limit,
      filter
    });
  }
}

// Usage
const client = new OpenPechaSearchClient();

// Health check
client.healthCheck().then(console.log);

// Hybrid search
client.hybridSearch("བདེ་བ", 10).then(results => {
  console.log(`Found ${results.count} results`);
});

// With filters
client.semanticSearch("enlightenment", 5, { title: "Kangyur" }).then(results => {
  results.results.forEach(r => {
    console.log(`${r.id}: ${r.distance}`);
  });
});
```

---

## TypeScript Examples

### Type Definitions

```typescript
interface SearchFilter {
  title?: string | string[];
  language?: string | string[];
}

interface SearchRequest {
  query: string;
  search_type?: "hybrid" | "bm25" | "semantic" | "exact";
  limit?: number;
  return_text?: boolean;
  hierarchical?: boolean;
  parent_limit?: number;
  filter?: SearchFilter;
}

interface SearchResult {
  id: string;
  distance: number;
  entity: {
    text?: string;
    language?: string;
    [key: string]: any;
  };
}

interface SearchResponse {
  query: string;
  search_type: string;
  results: SearchResult[];
  count: number;
}

interface HealthResponse {
  status: string;
  milvus_connected: boolean;
  gemini_configured: boolean;
}
```

### TypeScript Client

```typescript
class OpenPechaSearchClient {
  private baseUrl: string;

  constructor(baseUrl: string = "http://localhost:8001") {
    this.baseUrl = baseUrl;
  }

  async healthCheck(): Promise<HealthResponse> {
    const response = await fetch(`${this.baseUrl}/health`);
    return response.json();
  }

  async search(request: SearchRequest): Promise<SearchResponse> {
    const payload = {
      query: request.query,
      search_type: request.search_type ?? "hybrid",
      limit: request.limit ?? 10,
      return_text: request.return_text ?? true,
      hierarchical: request.hierarchical ?? false,
      ...(request.parent_limit && { parent_limit: request.parent_limit }),
      ...(request.filter && { filter: request.filter })
    };

    const response = await fetch(`${this.baseUrl}/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || "Search failed");
    }

    return response.json();
  }

  // Type-safe convenience methods
  async hybridSearch(
    query: string,
    limit: number = 10,
    filter?: SearchFilter
  ): Promise<SearchResponse> {
    return this.search({ query, search_type: "hybrid", limit, filter });
  }

  async semanticSearch(
    query: string,
    limit: number = 10,
    filter?: SearchFilter
  ): Promise<SearchResponse> {
    return this.search({ query, search_type: "semantic", limit, filter });
  }

  async bm25Search(
    query: string,
    limit: number = 10,
    filter?: SearchFilter
  ): Promise<SearchResponse> {
    return this.search({ query, search_type: "bm25", limit, filter });
  }

  async exactSearch(
    query: string,
    limit: number = 10,
    filter?: SearchFilter
  ): Promise<SearchResponse> {
    return this.search({ query, search_type: "exact", limit, filter });
  }
}

// Usage with full type safety
async function main() {
  const client = new OpenPechaSearchClient();

  // Health check
  const health = await client.healthCheck();
  console.log(`Status: ${health.status}`);

  // Hybrid search
  const results = await client.hybridSearch("བདེ་བ", 10, {
    title: ["Kangyur", "Tengyur"]
  });

  // Type-safe result handling
  results.results.forEach((result: SearchResult) => {
    console.log(`ID: ${result.id}`);
    console.log(`Score: ${result.distance.toFixed(4)}`);
    if (result.entity.text) {
      console.log(`Text: ${result.entity.text.substring(0, 100)}...`);
    }
  });
}

main();
```

---

## React Hook Example

```typescript
import { useState, useCallback } from 'react';

interface UseSearchResult {
  results: SearchResult[];
  loading: boolean;
  error: string | null;
  search: (query: string, type?: string) => Promise<void>;
}

function useSearch(baseUrl: string = "http://localhost:8001"): UseSearchResult {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const search = useCallback(async (query: string, type: string = "hybrid") => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`${baseUrl}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          search_type: type,
          limit: 10
        })
      });

      if (!response.ok) {
        throw new Error("Search failed");
      }

      const data: SearchResponse = await response.json();
      setResults(data.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [baseUrl]);

  return { results, loading, error, search };
}

// Usage in React component
function SearchComponent() {
  const { results, loading, error, search } = useSearch();
  const [query, setQuery] = useState("");

  const handleSearch = () => {
    if (query.trim()) {
      search(query);
    }
  };

  return (
    <div>
      <input 
        value={query} 
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search..."
      />
      <button onClick={handleSearch} disabled={loading}>
        {loading ? "Searching..." : "Search"}
      </button>
      
      {error && <div className="error">{error}</div>}
      
      <ul>
        {results.map((result) => (
          <li key={result.id}>
            <strong>{result.id}</strong>: {result.distance.toFixed(4)}
            {result.entity.text && <p>{result.entity.text}</p>}
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## Error Handling Examples

### Python

```python
import requests

def safe_search(query, **kwargs):
    """Search with comprehensive error handling."""
    try:
        response = requests.post(
            "http://localhost:8001/search",
            json={"query": query, **kwargs},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to API server")
        return None
    
    except requests.exceptions.Timeout:
        print("Error: Request timed out")
        return None
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            print(f"Bad request: {e.response.json().get('detail')}")
        elif e.response.status_code == 422:
            print(f"Validation error: {e.response.json()}")
        elif e.response.status_code == 500:
            print(f"Server error: {e.response.json().get('detail')}")
        else:
            print(f"HTTP error: {e}")
        return None
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None
```

### JavaScript

```javascript
async function safeSearch(query, options = {}) {
  try {
    const response = await fetch("http://localhost:8001/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, ...options })
    });

    if (!response.ok) {
      const error = await response.json();
      
      switch (response.status) {
        case 400:
          console.error("Bad request:", error.detail);
          break;
        case 422:
          console.error("Validation error:", error.detail);
          break;
        case 500:
          console.error("Server error:", error.detail);
          break;
        default:
          console.error("HTTP error:", response.status);
      }
      return null;
    }

    return await response.json();

  } catch (error) {
    if (error.name === "TypeError") {
      console.error("Network error: Cannot connect to API");
    } else {
      console.error("Unexpected error:", error);
    }
    return null;
  }
}
```

---

*Back to [Home](Home)*
