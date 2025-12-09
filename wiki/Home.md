# OpenPecha Search API Wiki

Welcome to the **OpenPecha Search API** wiki! This is a comprehensive guide to understanding and using the OpenPecha Search API for searching Tibetan texts.

## 🎯 What is OpenPecha Search?

OpenPecha Search is a powerful search API designed specifically for Tibetan Buddhist texts. It leverages modern vector search technology to provide multiple search methods:

- **Hybrid Search** - Best of both worlds (keyword + semantic)
- **BM25 Search** - Traditional keyword matching
- **Semantic Search** - AI-powered meaning-based search
- **Exact Match** - Find exact phrases

## 🚀 Quick Start

1. **Set up environment variables** (see [Setup Guide](Setup-Guide))
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Run the API**: `python api.py`
4. **Access the API**: `http://localhost:8001`
5. **View interactive docs**: `http://localhost:8001/docs`

## 📚 Wiki Pages

| Page | Description |
|------|-------------|
| [Concepts](Concepts) | Key definitions and terminology |
| [Search Types](Search-Types) | Detailed explanation of each search method |
| [API Reference](API-Reference) | Complete endpoint documentation |
| [Code Walkthrough](Code-Walkthrough) | Line-by-line code explanation |
| [Architecture](Architecture) | System design and data flow |
| [Setup Guide](Setup-Guide) | Installation and configuration |
| [Examples](Examples) | Usage examples in multiple languages |

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| Web Framework | FastAPI | High-performance async API |
| Vector Database | Milvus/Zilliz Cloud | Store and search vectors |
| Embeddings | Google Gemini | Generate semantic embeddings |
| Search Algorithm | BM25 + Dense Vectors | Hybrid search capability |

## 📖 Quick Example

```bash
# Perform a hybrid search
curl -X POST "http://localhost:8001/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད།", "search_type": "hybrid", "limit": 10}'
```

## 🔗 Useful Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Milvus Documentation](https://milvus.io/docs)
- [Google Gemini AI](https://ai.google.dev/)
- [OpenPecha](https://openpecha.org/)

## 📝 License

This project is open source. See the LICENSE file for details.

---

*For questions or issues, please open a GitHub issue.*
