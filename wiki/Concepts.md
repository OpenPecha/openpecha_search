# Key Concepts

This page explains the fundamental concepts and terminology used in the OpenPecha Search API.

---

## Table of Contents

- [Vector Embeddings](#vector-embeddings)
- [Dense Vectors](#dense-vectors)
- [Sparse Vectors (BM25)](#sparse-vectors-bm25)
- [Hybrid Search](#hybrid-search)
- [RRF Ranker](#rrf-ranker-reciprocal-rank-fusion)
- [Milvus Vector Database](#milvus-vector-database)
- [Semantic Search](#semantic-search)
- [PHRASE_MATCH](#phrase_match)
- [Hierarchical Search](#hierarchical-search)
- [ANN (Approximate Nearest Neighbor)](#ann-approximate-nearest-neighbor)

---

## Vector Embeddings

### What are Embeddings?

**Embeddings** are numerical representations of text (or other data) in a high-dimensional space. They convert human-readable text into arrays of numbers that machines can process and compare.

```
Text: "How to find peace of mind?"
     ↓ Embedding Model
Embedding: [0.023, -0.156, 0.892, ..., 0.445]  (768 dimensions)
```

### Why Use Embeddings?

1. **Semantic Understanding**: Similar meanings → similar vectors
2. **Mathematical Operations**: Can calculate distances between texts
3. **Language Agnostic**: Works across different languages
4. **Efficient Search**: Fast comparison of millions of documents

### In This Project

We use **Google Gemini's `gemini-embedding-001`** model to generate 768-dimensional embeddings:

```python
from google.genai.types import EmbedContentConfig

doc_cfg = EmbedContentConfig(
    task_type="RETRIEVAL_DOCUMENT",
    output_dimensionality=768
)
```

---

## Dense Vectors

### Definition

**Dense vectors** are embedding vectors where most or all values are non-zero. They capture the semantic meaning of text in a continuous numerical space.

### Characteristics

| Property | Description |
|----------|-------------|
| Dimensionality | Typically 768-1536 dimensions |
| Values | Floating-point numbers (e.g., 0.234, -0.567) |
| Sparsity | Low (most values are non-zero) |
| Captures | Semantic meaning, context, relationships |

### Example

```python
# Dense vector (768 dimensions, showing first 10)
dense_vector = [0.023, -0.156, 0.892, 0.034, -0.567, 
                0.123, 0.445, -0.234, 0.678, -0.089, ...]
```

### Use Case in OpenPecha

Dense vectors power **semantic search** - finding texts with similar meanings even if they use different words:

```
Query: "How to overcome suffering?"
Match: "བདེ་བ་ཐོབ་པའི་ཐབས།" (Methods to attain happiness)
```

---

## Sparse Vectors (BM25)

### Definition

**Sparse vectors** are vectors where most values are zero. Only dimensions corresponding to words present in the text have non-zero values.

### BM25 Algorithm

**BM25 (Best Matching 25)** is a ranking function used in information retrieval. It considers:

1. **Term Frequency (TF)**: How often a word appears in a document
2. **Inverse Document Frequency (IDF)**: How rare a word is across all documents
3. **Document Length**: Normalizes for document size

### Formula

```
BM25(D, Q) = Σ IDF(qi) × (f(qi, D) × (k1 + 1)) / (f(qi, D) + k1 × (1 - b + b × |D|/avgdl))
```

Where:
- `f(qi, D)` = frequency of term qi in document D
- `|D|` = document length
- `avgdl` = average document length
- `k1`, `b` = tuning parameters

### Characteristics

| Property | Description |
|----------|-------------|
| Dimensionality | Size of vocabulary |
| Values | Term weights (mostly zeros) |
| Sparsity | High (most values are zero) |
| Captures | Keyword presence, term importance |

### Example

```python
# Sparse vector representation (conceptual)
# Vocabulary: ["dharma", "buddha", "peace", "mind", ...]
sparse_vector = {
    "dharma": 2.3,
    "peace": 1.8,
    "mind": 1.5
    # All other terms: 0
}
```

### Use Case in OpenPecha

Sparse vectors power **BM25 search** - exact keyword matching:

```
Query: "སངས་རྒྱས" (Buddha)
Match: Documents containing the exact term "སངས་རྒྱས"
```

---

## Hybrid Search

### Definition

**Hybrid search** combines multiple search methods to get the best of both worlds. In OpenPecha, it combines:

1. **BM25 (Sparse)**: Keyword matching
2. **Semantic (Dense)**: Meaning-based matching

### Why Hybrid?

| Search Type | Strength | Weakness |
|-------------|----------|----------|
| BM25 | Exact keyword matches | Misses synonyms |
| Semantic | Understands meaning | May miss specific terms |
| **Hybrid** | **Both strengths** | **Minimized weaknesses** |

### How It Works

```
Query: "How to achieve enlightenment?"
            ↓
    ┌───────┴───────┐
    ↓               ↓
  BM25           Semantic
 Search          Search
    ↓               ↓
 Results A      Results B
    ↓               ↓
    └───────┬───────┘
            ↓
       RRF Ranker
            ↓
    Combined Results
```

### Implementation

```python
# BM25 search request
request_1 = AnnSearchRequest(
    data=[query],
    anns_field="sparce_vector",
    limit=limit
)

# Semantic search request
request_2 = AnnSearchRequest(
    data=[embedding],
    anns_field="dense_vector",
    limit=limit
)

# Combine with RRF
results = client.hybrid_search(
    reqs=[request_1, request_2],
    ranker=RRFRanker()
)
```

---

## RRF Ranker (Reciprocal Rank Fusion)

### Definition

**Reciprocal Rank Fusion (RRF)** is an algorithm for combining ranked lists from multiple search methods into a single, unified ranking.

### Formula

```
RRF_score(d) = Σ 1 / (k + rank_i(d))
```

Where:
- `d` = document
- `k` = constant (typically 60)
- `rank_i(d)` = rank of document d in list i

### Example

```
Document X:
  - Rank in BM25: 3
  - Rank in Semantic: 1
  
RRF_score(X) = 1/(60+3) + 1/(60+1) = 0.0159 + 0.0164 = 0.0323

Document Y:
  - Rank in BM25: 1
  - Rank in Semantic: 10

RRF_score(Y) = 1/(60+1) + 1/(60+10) = 0.0164 + 0.0143 = 0.0307

Result: X ranks higher (0.0323 > 0.0307)
```

### Why RRF?

1. **Score-agnostic**: Works regardless of score scales
2. **Fair combination**: Doesn't favor one method over another
3. **Robust**: Handles missing results gracefully

### Usage in OpenPecha

```python
from pymilvus import RRFRanker

ranker = RRFRanker()
results = milvus_client.hybrid_search(
    collection_name=COLLECTION_NAME,
    reqs=[bm25_request, semantic_request],
    ranker=ranker,
    limit=10
)
```

---

## Milvus Vector Database

### What is Milvus?

**Milvus** is an open-source vector database designed for scalable similarity search. It's optimized for storing and querying high-dimensional vectors.

### Key Features

| Feature | Description |
|---------|-------------|
| Scalability | Handles billions of vectors |
| Speed | Millisecond search latency |
| Hybrid Search | Supports dense + sparse vectors |
| Filtering | Combine vector search with metadata filters |

### Architecture

```
┌─────────────────────────────────────┐
│           Milvus Cluster            │
├─────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐          │
│  │ Dense   │  │ Sparse  │          │
│  │ Index   │  │ Index   │  Metadata│
│  │ (HNSW)  │  │ (BM25)  │  Storage │
│  └─────────┘  └─────────┘          │
├─────────────────────────────────────┤
│         Query Coordinator           │
└─────────────────────────────────────┘
```

### Collections & Fields

In OpenPecha, the collection schema includes:

```python
# Fields in the collection
- id: Primary key
- text: Original Tibetan text
- title: Document title
- language: Language code
- dense_vector: 768-dim embedding
- sparce_vector: BM25 sparse vector
- parent_id: For hierarchical documents
```

### Connection

```python
from pymilvus import MilvusClient

client = MilvusClient(
    uri="your_milvus_uri",
    token="your_token"
)
```

---

## Semantic Search

### Definition

**Semantic search** understands the meaning and intent behind a query, rather than just matching keywords.

### How It Works

1. **Query Embedding**: Convert query to vector
2. **Vector Search**: Find nearest neighbors in vector space
3. **Distance Calculation**: Measure similarity (cosine, L2, etc.)
4. **Ranking**: Return most similar documents

### Distance Metrics

| Metric | Formula | Use Case |
|--------|---------|----------|
| Cosine | 1 - cos(θ) | Normalized vectors |
| L2 (Euclidean) | √Σ(a-b)² | General purpose |
| IP (Inner Product) | Σ(a×b) | Normalized vectors |

### Example

```python
# Generate embedding for query
embedding = get_embedding("How to find inner peace?")

# Search for similar vectors
results = milvus_client.search(
    collection_name=COLLECTION_NAME,
    data=[embedding],
    anns_field="dense_vector",
    limit=10
)
```

### Benefits

- Finds conceptually similar content
- Works across languages
- Understands synonyms and paraphrases

---

## PHRASE_MATCH

### Definition

**PHRASE_MATCH** is a Milvus filter function that finds exact phrase occurrences within text fields.

### Syntax

```python
filter = "PHRASE_MATCH(text, 'exact phrase to find')"
```

### How It Differs from BM25

| Aspect | BM25 | PHRASE_MATCH |
|--------|------|--------------|
| Matching | Token-based | Exact sequence |
| Word Order | Ignored | Preserved |
| Partial Match | Yes | No |

### Example

```python
# Find exact Tibetan phrase
results = milvus_client.search(
    collection_name=COLLECTION_NAME,
    data=[query],
    anns_field="sparce_vector",
    filter="PHRASE_MATCH(text, 'དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད། །')",
    limit=10
)
```

### Use Cases

- Finding exact quotes
- Locating specific verses
- Citation lookup

---

## Hierarchical Search

### Definition

**Hierarchical search** is a two-stage search pattern that first finds parent documents, then retrieves their children.

### Structure

```
Parent Document (e.g., Chapter)
├── Child 1 (e.g., Verse 1)
├── Child 2 (e.g., Verse 2)
└── Child 3 (e.g., Verse 3)
```

### How It Works

```
Stage 1: Search Parents
Query → Find matching parent documents
         (filter: parent_id == "")

Stage 2: Search Children
Parent IDs → Find children of matched parents
             (filter: parent_id in [parent_ids])
```

### Implementation

```python
# Stage 1: Find parents
parent_filter = 'parent_id == ""'
parent_results = await perform_search(query, parent_filter)

# Stage 2: Find children
parent_ids = [r.id for r in parent_results]
children_filter = f'parent_id in ["{"\", \"".join(parent_ids)}"]'
final_results = await perform_search(query, children_filter)
```

### Benefits

1. **Context Preservation**: Results include surrounding content
2. **Efficient Retrieval**: Two-stage filtering reduces search space
3. **Structured Results**: Maintains document hierarchy

---

## ANN (Approximate Nearest Neighbor)

### Definition

**Approximate Nearest Neighbor (ANN)** algorithms find vectors that are "close enough" to the query vector, trading perfect accuracy for speed.

### Why Approximate?

| Approach | Accuracy | Speed | Scalability |
|----------|----------|-------|-------------|
| Exact KNN | 100% | Slow | Poor |
| ANN | 95-99% | Fast | Excellent |

### Index Types in Milvus

| Index | Description | Use Case |
|-------|-------------|----------|
| HNSW | Hierarchical Navigable Small World | High accuracy |
| IVF_FLAT | Inverted File with Flat | Balanced |
| IVF_SQ8 | Quantized IVF | Memory efficient |

### Parameters

```python
search_params = {
    "data": [embedding],
    "anns_field": "dense_vector",
    "param": {
        "drop_ratio_search": 0.2  # Speed/accuracy tradeoff
    },
    "limit": 10
}
```

### In OpenPecha

The `anns_field` parameter specifies which vector field to search:
- `"dense_vector"` for semantic search
- `"sparce_vector"` for BM25 search

---

## Summary

| Concept | Purpose |
|---------|---------|
| Dense Vectors | Capture semantic meaning |
| Sparse Vectors | Enable keyword matching |
| Hybrid Search | Combine both approaches |
| RRF Ranker | Merge ranked results |
| Milvus | Store and search vectors |
| PHRASE_MATCH | Find exact phrases |
| Hierarchical | Two-stage parent-child search |
| ANN | Fast approximate search |

---

*Next: [Search Types](Search-Types) for detailed search method explanations.*
