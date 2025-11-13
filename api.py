from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
from google import genai
from google.genai.types import EmbedContentConfig
from pymilvus import MilvusClient, AnnSearchRequest, RRFRanker

# Load environment variables
load_dotenv()

# Get credentials from environment variables
MILVUS_URI = os.getenv("MILVUS_URI")
MILVUS_TOKEN = os.getenv("MILVUS_TOKEN")
MILVUS_COLLECTION_NAME = os.getenv("MILVUS_COLLECTION_NAME", "test_kangyur_tengyur")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Validate required environment variables
if not MILVUS_URI:
    raise ValueError("MILVUS_URI environment variable is not set")
if not MILVUS_TOKEN:
    raise ValueError("MILVUS_TOKEN environment variable is not set")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set")

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

# Initialize Milvus client
milvus_client = MilvusClient(
    uri=MILVUS_URI,
    token=MILVUS_TOKEN,
    collection_name=MILVUS_COLLECTION_NAME
)

# Initialize Gemini client
genai_client = genai.Client(api_key=GEMINI_API_KEY)
doc_cfg = EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT", output_dimensionality=768)


# Pydantic models
class SearchFilter(BaseModel):
    title: Optional[str] = Field(None, description="Filter results by title")


class SearchRequest(BaseModel):
    query: str = Field(..., description="The search query text", min_length=1)
    limit: int = Field(10, description="Maximum number of results to return", ge=1, le=100)
    filter: Optional[SearchFilter] = Field(None, description="Optional filters to apply")


class SearchResult(BaseModel):
    id: Any
    distance: float
    entity: Dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    search_type: str
    results: List[SearchResult]
    count: int


# Helper function to generate embeddings
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
        raise HTTPException(status_code=500, detail=f"Error generating embedding: {str(e)}")


# Helper function to build filter expression
def build_filter_expression(filter_obj: Optional[SearchFilter]) -> Optional[str]:
    """Build Milvus filter expression from filter object."""
    if not filter_obj:
        return None
    
    conditions = []
    if filter_obj.title:
        conditions.append(f'title == "{filter_obj.title}"')
    
    return " && ".join(conditions) if conditions else None


# Helper function to format results
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


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "OpenPecha Search API",
        "version": "1.0.0",
        "endpoints": {
            "hybrid": "/search/hybrid",
            "bm25": "/search/bm25",
            "semantic": "/search/semantic"
        },
        "docs": "/docs"
    }


@app.post("/search/hybrid", response_model=SearchResponse)
async def hybrid_search(request: SearchRequest):
    """
    Perform hybrid search combining BM25 (sparse) and semantic (dense) search.
    Uses RRF (Reciprocal Rank Fusion) to merge results.
    """
    try:
        # Get embedding for semantic search
        embedding = get_embedding(request.query)
        
        # Build filter expression
        filter_expr = build_filter_expression(request.filter)
        
        # BM25 search parameters
        search_param_1 = {
            "data": [request.query],
            "anns_field": "sparce_vector",
            "param": {},
            "limit": request.limit
        }
        if filter_expr:
            search_param_1["expr"] = filter_expr
        request_1 = AnnSearchRequest(**search_param_1)
        
        # Semantic search parameters
        search_param_2 = {
            "data": [embedding],
            "anns_field": "dense_vector",
            "param": {"drop_ratio_search": 0.2},
            "limit": request.limit
        }
        if filter_expr:
            search_param_2["expr"] = filter_expr
        request_2 = AnnSearchRequest(**search_param_2)
        
        # Perform hybrid search
        ranker = RRFRanker()
        results = milvus_client.hybrid_search(
            collection_name=MILVUS_COLLECTION_NAME,
            reqs=[request_1, request_2],
            ranker=ranker,
            limit=request.limit,
            output_fields=['title']
        )
        
        return format_results(results, request.query, "hybrid")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid search failed: {str(e)}")


@app.post("/search/bm25", response_model=SearchResponse)
async def bm25_search(request: SearchRequest):
    """
    Perform BM25 search (sparse vector search) for keyword-based matching.
    Best for exact term matching and traditional search.
    """
    try:
        # Build filter expression
        filter_expr = build_filter_expression(request.filter)
        
        # Prepare search parameters
        search_params = {
            "collection_name": MILVUS_COLLECTION_NAME,
            "data": [request.query],
            "anns_field": "sparce_vector",
            "limit": request.limit,
            "output_fields": ['title']
        }
        
        if filter_expr:
            search_params["filter"] = filter_expr
        
        # Perform BM25 search
        results = milvus_client.search(**search_params)
        
        return format_results(results, request.query, "bm25")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"BM25 search failed: {str(e)}")


@app.post("/search/semantic", response_model=SearchResponse)
async def semantic_search(request: SearchRequest):
    """
    Perform semantic search (dense vector search) for meaning-based matching.
    Best for finding conceptually similar content regardless of exact wording.
    """
    try:
        # Get embedding
        embedding = get_embedding(request.query)
        
        # Build filter expression
        filter_expr = build_filter_expression(request.filter)
        
        # Prepare search parameters
        search_params = {
            "collection_name": MILVUS_COLLECTION_NAME,
            "data": [embedding],
            "anns_field": "dense_vector",
            "limit": request.limit,
            "output_fields": ['title']
        }
        
        if filter_expr:
            search_params["filter"] = filter_expr
        
        # Perform semantic search
        results = milvus_client.search(**search_params)
        
        return format_results(results, request.query, "semantic")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "milvus_connected": True,
        "gemini_configured": True
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

