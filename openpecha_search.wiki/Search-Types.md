# Search Types

The OpenPecha Search API supports four distinct search methods, each optimized for different use cases.

---

## Overview

| Search Type | Method | Best For | Speed |
|-------------|--------|----------|-------|
| [Hybrid](#hybrid-search) | BM25 + Semantic | General purpose | Medium |
| [BM25](#bm25-search) | Sparse vectors | Keyword matching | Fast |
| [Semantic](#semantic-search) | Dense vectors | Meaning-based | Medium |
| [Exact](#exact-match-search) | PHRASE_MATCH | Exact phrases | Fast |

---

## Hybrid Search

### Description

Hybrid search combines **BM25 (keyword-based)** and **Semantic (meaning-based)** search using **Reciprocal Rank Fusion (RRF)** to provide the most comprehensive results.

### When to Use

- ✅ General-purpose searching
- ✅ When you're unsure which method is best
- ✅ When you want both keyword and semantic matches
- ✅ Searching multilingual content

### How It Works

```
                    Query
                      │
           ┌─────────┴─────────┐
           ↓                   ↓
    ┌─────────────┐    ┌─────────────┐
    │    BM25     │    │  Semantic   │
    │   Search    │    │   Search    │
    │             │    │             │
    │ sparse_vec  │    │ dense_vec   │
    └──────┬──────┘    └──────┬──────┘
           │                   │
           │    Results A      │    Results B
           │                   │
           └─────────┬─────────┘
                     ↓
              ┌─────────────┐
              │ RRF Ranker  │
              │             │
              │ Combines &  │
              │ Re-ranks    │
              └──────┬──────┘
                     ↓
              Final Results
```

### API Usage

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to find peace of mind?",
    "search_type": "hybrid",
    "limit": 10
  }'
```

### Code Implementation

```python
async def perform_hybrid_search(query, limit, filter_expr, return_text):
    # Get embedding for semantic search
    embedding = get_embedding(query)
    
    # BM25 search parameters
    search_param_1 = {
        "data": [query],
        "anns_field": "sparce_vector",
        "param": {},
        "limit": limit
    }
    request_1 = AnnSearchRequest(**search_param_1)
    
    # Semantic search parameters
    search_param_2 = {
        "data": [embedding],
        "anns_field": "dense_vector",
        "param": {"drop_ratio_search": 0.2},
        "limit": limit
    }
    request_2 = AnnSearchRequest(**search_param_2)
    
    # Combine with RRF ranker
    ranker = RRFRanker()
    results = milvus_client.hybrid_search(
        collection_name=COLLECTION_NAME,
        reqs=[request_1, request_2],
        ranker=ranker,
        limit=limit
    )
    
    return format_results(results, query, "hybrid")
```

### Pros & Cons

| Pros | Cons |
|------|------|
| Best overall coverage | Slower than single methods |
| Handles diverse queries | Requires both indexes |
| Balanced results | More complex ranking |

---

## BM25 Search

### Description

BM25 (Best Matching 25) is a **keyword-based** search algorithm that uses sparse vectors. It excels at finding documents containing specific terms.

### When to Use

- ✅ Searching for specific Tibetan terms
- ✅ When exact terminology matters
- ✅ Fast keyword lookups
- ✅ When you know the exact words used

### How It Works

```
Query: "སངས་རྒྱས་ཀྱི་བསྟན་པ"
              │
              ↓
     ┌─────────────────┐
     │   Tokenization  │
     │                 │
     │ སངས་རྒྱས → token1 │
     │ བསྟན་པ → token2  │
     └────────┬────────┘
              │
              ↓
     ┌─────────────────┐
     │  BM25 Scoring   │
     │                 │
     │ TF × IDF × norm │
     └────────┬────────┘
              │
              ↓
     ┌─────────────────┐
     │ Sparse Vector   │
     │ Search (ANN)    │
     └────────┬────────┘
              │
              ↓
         Results
```

### API Usage

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "སངས་རྒྱས་ཀྱི་བསྟན་པ",
    "search_type": "bm25",
    "limit": 10
  }'
```

### Code Implementation

```python
async def perform_bm25_search(query, limit, filter_expr, return_text):
    output_fields = ['text', 'language'] if return_text else []
    
    search_params = {
        "collection_name": MILVUS_COLLECTION_NAME,
        "data": [query],
        "anns_field": "sparce_vector",
        "limit": limit,
        "output_fields": output_fields
    }
    
    if filter_expr:
        search_params["filter"] = filter_expr
    
    results = milvus_client.search(**search_params)
    
    return format_results(results, query, "bm25")
```

### Pros & Cons

| Pros | Cons |
|------|------|
| Fast execution | Misses synonyms |
| Exact term matching | No semantic understanding |
| Predictable results | Word order ignored |
| Good for Tibetan script | Language-dependent |

---

## Semantic Search

### Description

Semantic search uses **dense vector embeddings** to find documents based on meaning, not just keywords. It understands context and can match conceptually similar content.

### When to Use

- ✅ Conceptual/meaning-based queries
- ✅ Cross-language searching
- ✅ Finding related content
- ✅ When exact terms are unknown
- ✅ English queries on Tibetan texts

### How It Works

```
Query: "How to overcome suffering?"
              │
              ↓
     ┌─────────────────┐
     │ Gemini Embedding│
     │                 │
     │ gemini-embed-001│
     │ 768 dimensions  │
     └────────┬────────┘
              │
              ↓
     [0.023, -0.156, 0.892, ...]
              │
              ↓
     ┌─────────────────┐
     │ Vector Search   │
     │                 │
     │ Find nearest    │
     │ neighbors       │
     └────────┬────────┘
              │
              ↓
     Documents with similar
     semantic meaning
```

### API Usage

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to overcome suffering?",
    "search_type": "semantic",
    "limit": 10
  }'
```

### Code Implementation

```python
def get_embedding(text: str) -> List[float]:
    """Generate embedding using Gemini."""
    resp = genai_client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config=doc_cfg,
    )
    return [i.values for i in resp.embeddings][0]


async def perform_semantic_search(query, limit, filter_expr, return_text):
    # Get embedding
    embedding = get_embedding(query)
    
    output_fields = ['text', 'language'] if return_text else []
    
    search_params = {
        "collection_name": MILVUS_COLLECTION_NAME,
        "data": [embedding],
        "anns_field": "dense_vector",
        "limit": limit,
        "output_fields": output_fields
    }
    
    if filter_expr:
        search_params["filter"] = filter_expr
    
    results = milvus_client.search(**search_params)
    
    return format_results(results, query, "semantic")
```

### Pros & Cons

| Pros | Cons |
|------|------|
| Understands meaning | Slower (embedding generation) |
| Cross-language capable | May miss exact terms |
| Finds related content | Requires embedding model |
| Works with paraphrases | Less predictable |

---

## Exact Match Search

### Description

Exact match search uses **PHRASE_MATCH** to find documents containing the exact query phrase in the specified order.

### When to Use

- ✅ Finding exact quotes
- ✅ Citation lookup
- ✅ Locating specific verses
- ✅ When word order matters
- ✅ Precise text retrieval

### How It Works

```
Query: "དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད། །"
              │
              ↓
     ┌─────────────────┐
     │  PHRASE_MATCH   │
     │                 │
     │ Exact sequence  │
     │ matching        │
     └────────┬────────┘
              │
              ↓
     ┌─────────────────┐
     │ Filter + BM25   │
     │                 │
     │ Combined search │
     └────────┬────────┘
              │
              ↓
     Documents with exact
     phrase match
```

### API Usage

```bash
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད། །",
    "search_type": "exact",
    "limit": 10
  }'
```

### Code Implementation

```python
async def perform_exact_search(query, limit, filter_expr, return_text):
    # Escape single quotes
    escaped_query = query.replace("'", "\\'")
    
    # Build PHRASE_MATCH filter
    phrase_filter = f"PHRASE_MATCH(text, '{escaped_query}')"
    
    # Combine with additional filters
    if filter_expr:
        final_filter = f"{phrase_filter} && {filter_expr}"
    else:
        final_filter = phrase_filter
    
    output_fields = ['text'] if return_text else []
    
    search_params = {
        "collection_name": MILVUS_COLLECTION_NAME,
        "data": [query],
        "anns_field": "sparce_vector",
        "limit": limit,
        "output_fields": output_fields,
        "filter": final_filter
    }
    
    results = milvus_client.search(**search_params)
    
    return format_results(results, query, "exact")
```

### Pros & Cons

| Pros | Cons |
|------|------|
| 100% precision | May miss variations |
| Preserves word order | No fuzzy matching |
| Fast filtering | Exact text required |
| Perfect for citations | Case/format sensitive |

---

## Comparison Matrix

### By Feature

| Feature | Hybrid | BM25 | Semantic | Exact |
|---------|--------|------|----------|-------|
| Keyword matching | ✅ | ✅ | ❌ | ✅ |
| Semantic understanding | ✅ | ❌ | ✅ | ❌ |
| Cross-language | ✅ | ❌ | ✅ | ❌ |
| Word order preserved | Partial | ❌ | ❌ | ✅ |
| Synonym matching | ✅ | ❌ | ✅ | ❌ |
| Exact phrase | Partial | ❌ | ❌ | ✅ |

### By Use Case

| Use Case | Recommended |
|----------|-------------|
| General search | Hybrid |
| Specific Tibetan terms | BM25 |
| English query on Tibetan text | Semantic |
| Finding exact quotes | Exact |
| Related content discovery | Semantic |
| Fast keyword lookup | BM25 |
| Unknown exact wording | Hybrid or Semantic |
| Citation verification | Exact |

### Performance

| Metric | Hybrid | BM25 | Semantic | Exact |
|--------|--------|------|----------|-------|
| Speed | Medium | Fast | Medium | Fast |
| Accuracy | High | Good | High | Perfect* |
| Coverage | Best | Limited | Good | Limited |
| Resources | High | Low | Medium | Low |

*Perfect accuracy for exact matches only

---

## Hierarchical Search Mode

All search types support **hierarchical mode**, which performs a two-stage search:

1. **Stage 1**: Find matching parent documents
2. **Stage 2**: Retrieve children of matched parents

### Usage

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

### Parameters

| Parameter | Description |
|-----------|-------------|
| `hierarchical` | Enable two-stage search |
| `parent_limit` | Max parents to retrieve (stage 1) |
| `limit` | Max children to return (stage 2) |

---

## Choosing the Right Search Type

```
                    Start
                      │
                      ▼
              ┌───────────────┐
              │ Need exact    │
              │ phrase match? │
              └───────┬───────┘
                      │
           ┌──────────┴──────────┐
           │ Yes                 │ No
           ▼                     ▼
       ┌───────┐         ┌───────────────┐
       │ Exact │         │ Know specific │
       │       │         │ keywords?     │
       └───────┘         └───────┬───────┘
                                 │
                    ┌────────────┴────────────┐
                    │ Yes                     │ No
                    ▼                         ▼
            ┌───────────────┐         ┌───────────────┐
            │ Keywords only │         │ Meaning-based │
            │ or speed?     │         │ query?        │
            └───────┬───────┘         └───────┬───────┘
                    │                         │
           ┌────────┴────────┐       ┌────────┴────────┐
           │ Yes             │ No    │ Yes             │ No
           ▼                 ▼       ▼                 ▼
       ┌───────┐         ┌──────┐ ┌──────────┐    ┌──────┐
       │ BM25  │         │Hybrid│ │ Semantic │    │Hybrid│
       └───────┘         └──────┘ └──────────┘    └──────┘
```

---

*Next: [API Reference](API-Reference) for complete endpoint documentation.*
