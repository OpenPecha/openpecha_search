# Architecture

System design and data flow for the OpenPecha Search API.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              OpenPecha Search System                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────────────┐    ┌───────────────────────┐  │
│  │   Client     │    │    FastAPI Server    │    │    External Services  │  │
│  │              │    │                      │    │                       │  │
│  │  • Web App   │───▶│  • api.py            │───▶│  • Milvus (Vector DB) │  │
│  │  • CLI       │    │  • Endpoints         │    │  • Gemini (Embeddings)│  │
│  │  • Mobile    │◀───│  • Search Logic      │◀───│                       │  │
│  │              │    │                      │    │                       │  │
│  └──────────────┘    └──────────────────────┘    └───────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### 1. API Layer (FastAPI)

```
┌─────────────────────────────────────────────────────────┐
│                     FastAPI Application                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │                   Middleware                     │    │
│  │  • CORS (Cross-Origin Resource Sharing)         │    │
│  │  • Request/Response logging                     │    │
│  └─────────────────────────────────────────────────┘    │
│                          │                               │
│                          ▼                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │                    Endpoints                     │    │
│  │  • GET  /           (API info)                  │    │
│  │  • POST /search     (main search)               │    │
│  │  • GET  /health     (health check)              │    │
│  │  • GET  /debug/search (debug)                   │    │
│  └─────────────────────────────────────────────────┘    │
│                          │                               │
│                          ▼                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │                 Request Validation               │    │
│  │  • Pydantic Models (SearchRequest, SearchFilter)│    │
│  │  • Type checking & constraints                  │    │
│  └─────────────────────────────────────────────────┘    │
│                          │                               │
│                          ▼                               │
│  ┌─────────────────────────────────────────────────┐    │
│  │                  Search Logic                    │    │
│  │  • perform_hybrid_search()                      │    │
│  │  • perform_bm25_search()                        │    │
│  │  • perform_semantic_search()                    │    │
│  │  • perform_exact_search()                       │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 2. Vector Database Layer (Milvus)

```
┌─────────────────────────────────────────────────────────┐
│                  Milvus Vector Database                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │                   Collection                     │    │
│  │              (MILVUS_COLLECTION_NAME)           │    │
│  ├─────────────────────────────────────────────────┤    │
│  │                                                  │    │
│  │  Schema:                                         │    │
│  │  ┌───────────────┬──────────┬─────────────────┐ │    │
│  │  │ Field         │ Type     │ Description     │ │    │
│  │  ├───────────────┼──────────┼─────────────────┤ │    │
│  │  │ id            │ VARCHAR  │ Primary key     │ │    │
│  │  │ text          │ VARCHAR  │ Document text   │ │    │
│  │  │ title         │ VARCHAR  │ Document title  │ │    │
│  │  │ language      │ VARCHAR  │ Language code   │ │    │
│  │  │ parent_id     │ VARCHAR  │ Parent doc ID   │ │    │
│  │  │ dense_vector  │ FLOAT[768]│ Semantic emb.  │ │    │
│  │  │ sparce_vector │ SPARSE   │ BM25 vector     │ │    │
│  │  └───────────────┴──────────┴─────────────────┘ │    │
│  │                                                  │    │
│  │  Indexes:                                        │    │
│  │  • dense_vector: HNSW (for semantic search)     │    │
│  │  • sparce_vector: SPARSE_INVERTED_INDEX (BM25)  │    │
│  │                                                  │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 3. Embedding Layer (Google Gemini)

```
┌─────────────────────────────────────────────────────────┐
│                  Google Gemini AI                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Model: gemini-embedding-001                             │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │                Configuration                     │    │
│  │                                                  │    │
│  │  • task_type: RETRIEVAL_DOCUMENT                │    │
│  │  • output_dimensionality: 768                   │    │
│  │                                                  │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  Input:  "How to find inner peace?"                      │
│            │                                             │
│            ▼                                             │
│  Output: [0.023, -0.156, 0.892, ..., 0.445]             │
│          (768 floating-point numbers)                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Data Flow Diagrams

### Standard Search Flow

```
┌──────────┐     ┌───────────────────────────────────────────────────────────┐
│  Client  │     │                      API Server                           │
└────┬─────┘     └───────────────────────────────────────────────────────────┘
     │                                    │
     │  POST /search                      │
     │  {query, search_type, ...}         │
     │ ──────────────────────────────────▶│
     │                                    │
     │                          ┌─────────┴─────────┐
     │                          │ Validate Request  │
     │                          │ (Pydantic)        │
     │                          └─────────┬─────────┘
     │                                    │
     │                          ┌─────────┴─────────┐
     │                          │ Build Filter      │
     │                          │ Expression        │
     │                          └─────────┬─────────┘
     │                                    │
     │                          ┌─────────┴─────────┐
     │                          │ Route to Search   │
     │                          │ Function          │
     │                          └─────────┬─────────┘
     │                                    │
     │                    ┌───────────────┼───────────────┐
     │                    ▼               ▼               ▼
     │               ┌────────┐     ┌────────┐     ┌────────┐
     │               │ Hybrid │     │  BM25  │     │Semantic│
     │               └────┬───┘     └────┬───┘     └────┬───┘
     │                    │              │              │
     │                    │              │         ┌────┴────┐
     │                    │              │         │ Gemini  │
     │                    │              │         │Embedding│
     │                    │              │         └────┬────┘
     │                    │              │              │
     │                    └───────────┬──┴──────────────┘
     │                                │
     │                       ┌────────┴────────┐
     │                       │     Milvus      │
     │                       │  Vector Search  │
     │                       └────────┬────────┘
     │                                │
     │                       ┌────────┴────────┐
     │                       │ Format Results  │
     │                       └────────┬────────┘
     │                                │
     │  SearchResponse                │
     │  {query, results, count}       │
     │ ◀──────────────────────────────│
     │                                │
```

### Hybrid Search Internal Flow

```
                         Query
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
    ┌─────────────────┐      ┌─────────────────┐
    │   Raw Query     │      │  Generate       │
    │   (BM25)        │      │  Embedding      │
    └────────┬────────┘      └────────┬────────┘
             │                        │
             │                        │ Gemini API
             │                        ▼
             │               ┌─────────────────┐
             │               │ 768-dim Vector  │
             │               └────────┬────────┘
             │                        │
             ▼                        ▼
    ┌─────────────────┐      ┌─────────────────┐
    │ AnnSearchRequest│      │ AnnSearchRequest│
    │ sparce_vector   │      │ dense_vector    │
    └────────┬────────┘      └────────┬────────┘
             │                        │
             └──────────┬─────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │  Milvus         │
              │  hybrid_search  │
              │                 │
              │  reqs=[req1,    │
              │        req2]    │
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   RRF Ranker    │
              │                 │
              │ Score = Σ 1/(k+r)│
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Combined &      │
              │ Ranked Results  │
              └─────────────────┘
```

### Hierarchical Search Flow

```
                         Query + hierarchical=true
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │       Stage 1            │
                    │   Find Parent Documents  │
                    │                          │
                    │   Filter: parent_id==""  │
                    │   Limit: parent_limit    │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │   Search Milvus          │
                    │                          │
                    │   Returns: Parent IDs    │
                    │   [P1, P2, P3, ...]      │
                    └────────────┬─────────────┘
                                 │
                                 │ Extract parent_ids
                                 ▼
                    ┌──────────────────────────┐
                    │       Stage 2            │
                    │  Find Children of Parents│
                    │                          │
                    │  Filter: parent_id       │
                    │  in [P1, P2, P3...]      │
                    │  Limit: limit            │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │   Search Milvus          │
                    │                          │
                    │   Returns: Child docs    │
                    │   that match query       │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │   Final Results          │
                    │                          │
                    │   Children documents     │
                    │   with context           │
                    └──────────────────────────┘
```

---

## Technology Stack

### Runtime Environment

```
┌─────────────────────────────────────────────────────────┐
│                    Runtime Stack                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Application Layer:                                      │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Python 3.8+                                    │    │
│  │  ├── FastAPI (async web framework)             │    │
│  │  ├── Pydantic (data validation)                │    │
│  │  └── Uvicorn (ASGI server)                     │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  Client Libraries:                                       │
│  ┌─────────────────────────────────────────────────┐    │
│  │  pymilvus (Milvus Python SDK)                   │    │
│  │  google-genai (Google AI Python SDK)            │    │
│  │  python-dotenv (Environment management)         │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  External Services:                                      │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Milvus / Zilliz Cloud (Vector Database)        │    │
│  │  Google Gemini (Embedding Generation)           │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Dependency Graph

```
                    ┌─────────────┐
                    │   api.py    │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
         ▼                 ▼                 ▼
   ┌───────────┐    ┌───────────┐    ┌───────────┐
   │  fastapi  │    │  pymilvus │    │google-genai│
   └─────┬─────┘    └───────────┘    └───────────┘
         │
         ▼
   ┌───────────┐
   │  pydantic │
   └───────────┘
```

---

## Security Architecture

### Environment Variables

```
┌─────────────────────────────────────────────────────────┐
│                 Credential Management                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  .env file (NOT in version control):                    │
│  ┌─────────────────────────────────────────────────┐    │
│  │  MILVUS_URI=https://...                         │    │
│  │  MILVUS_TOKEN=<token>                           │    │
│  │  MILVUS_COLLECTION_NAME=production              │    │
│  │  GEMINI_API_KEY=<api_key>                       │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  Loaded at startup via python-dotenv                     │
│  Validated before server starts                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### API Security Considerations

```
┌─────────────────────────────────────────────────────────┐
│                  Security Layers                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Input Validation (Pydantic):                        │
│     • Type checking                                     │
│     • Value constraints (ge, le, min_length)            │
│     • Required field enforcement                        │
│                                                          │
│  2. String Escaping:                                    │
│     • _escape_milvus_string() for filter injection      │
│     • Quote escaping for PHRASE_MATCH                   │
│                                                          │
│  3. CORS Configuration:                                 │
│     • Currently: allow_origins=["*"] (open)             │
│     • Production: Should restrict to specific origins   │
│                                                          │
│  4. Error Handling:                                     │
│     • HTTPException for controlled errors               │
│     • Generic 500 for unexpected errors                 │
│     • No credential leakage in error messages           │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

### Local Development

```
┌─────────────────────────────────────────┐
│           Local Development             │
├─────────────────────────────────────────┤
│                                         │
│  Terminal:                              │
│  $ python api.py                        │
│                                         │
│  ┌─────────────────────────────┐        │
│  │     Uvicorn Server          │        │
│  │     localhost:8001          │        │
│  └─────────────────────────────┘        │
│              │                          │
│              ▼                          │
│  ┌─────────────────────────────┐        │
│  │  External Services          │        │
│  │  (Milvus Cloud, Gemini)     │        │
│  └─────────────────────────────┘        │
│                                         │
└─────────────────────────────────────────┘
```

### Production Deployment Options

```
┌─────────────────────────────────────────────────────────┐
│              Production Options                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Option 1: Cloud Run / Lambda                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │  • Serverless deployment                        │    │
│  │  • Auto-scaling                                 │    │
│  │  • Environment variables via secrets            │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  Option 2: Container (Docker)                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │  • Dockerfile with Python + dependencies        │    │
│  │  • Kubernetes / ECS deployment                  │    │
│  │  • Load balancer for high availability          │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  Option 3: VM / VPS                                     │
│  ┌─────────────────────────────────────────────────┐    │
│  │  • Gunicorn + Uvicorn workers                   │    │
│  │  • Nginx reverse proxy                          │    │
│  │  • Systemd service management                   │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Performance Considerations

### Bottlenecks & Optimizations

```
┌─────────────────────────────────────────────────────────┐
│              Performance Analysis                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Potential Bottlenecks:                                 │
│  ┌─────────────────────────────────────────────────┐    │
│  │  1. Embedding Generation (Gemini API call)      │    │
│  │     • ~100-500ms per request                    │    │
│  │     • Solution: Caching, batching               │    │
│  │                                                  │    │
│  │  2. Vector Search (Milvus)                      │    │
│  │     • ~10-100ms depending on limit              │    │
│  │     • Solution: Proper indexing, limit tuning   │    │
│  │                                                  │    │
│  │  3. Network Latency                             │    │
│  │     • API ↔ Milvus Cloud                        │    │
│  │     • API ↔ Gemini                              │    │
│  │     • Solution: Regional deployment             │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  Optimizations Applied:                                 │
│  ┌─────────────────────────────────────────────────┐    │
│  │  • drop_ratio_search: 0.2 (speed/accuracy)     │    │
│  │  • Optional return_text (reduce payload)        │    │
│  │  • Configurable limits                          │    │
│  │  • Async endpoints (non-blocking)               │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

*Next: [Setup Guide](Setup-Guide) for installation instructions.*
