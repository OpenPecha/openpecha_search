from fastapi import FastAPI, HTTPException, Query
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
    token=MILVUS_TOKEN
)

# Initialize Gemini client
genai_client = genai.Client(api_key=GEMINI_API_KEY)
doc_cfg = EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT", output_dimensionality=768)


# Pydantic models
class SearchFilter(BaseModel):
    title: Optional[str] = Field(None, description="Filter results by title")


class SearchRequest(BaseModel):
    query: str = Field(..., description="The search query text", min_length=1, examples=["དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད། །"])
    search_type: str = Field("hybrid", description="Type of search: 'hybrid', 'bm25', 'semantic', or 'exact'", examples=["hybrid"])
    limit: int = Field(10, description="Maximum number of results to return", ge=1, le=100, examples=[10])
    return_text: bool = Field(True, description="If True, return full text in results. If False, return only ID and distance", examples=[True])
    filter: Optional[SearchFilter] = Field(None, description="Optional filters to apply")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད། །",
                    "search_type": "hybrid",
                    "limit": 10,
                    "return_text": True,
                    "filter": None
                },
                {
                    "query": "how to worry less?",
                    "search_type": "semantic",
                    "limit": 5,
                    "return_text": True,
                    "filter": None
                },
                {
                    "query": "དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད། །",
                    "search_type": "exact",
                    "limit": 10,
                    "return_text": True,
                    "filter": None
                },
                {
                    "query": "ཕམ་པར་གྱུར་བའི་ཆོས་དུན་པ",
                    "search_type": "bm25",
                    "limit": 10,
                    "return_text": False,
                    "filter": None
                }
            ]
        }
    }


class SearchResult(BaseModel):
    id: Any
    distance: float
    entity: Dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    search_type: str
    results: List[SearchResult]
    count: int
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query": "དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད། །",
                    "search_type": "hybrid",
                    "results": [
                        {
                            "id": "449691587532670411",
                            "distance": 0.95,
                            "entity": {
                                "text": "དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད། །གང་ཕྱིར་འདི་དག་རང་བཞིན་མེད།"
                            }
                        },
                        {
                            "id": "449691587532670412",
                            "distance": 0.87,
                            "entity": {
                                "text": "སངས་རྒྱས་ཀྱི་བསྟན་པ་ལ་གུས་པར་བྱོས།"
                            }
                        }
                    ],
                    "count": 2
                },
                {
                    "query": "how to worry less?",
                    "search_type": "semantic",
                    "results": [
                        {
                            "id": "449691587532670413",
                            "distance": 0.82,
                            "entity": {
                                "text": "སེམས་ཅན་ཐམས་ཅད་བདེ་བར་གྱུར་ཅིག"
                            }
                        }
                    ],
                    "count": 1
                }
            ]
        }
    }


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


@app.get("/search", response_model=SearchResponse)
async def unified_search(
    query: str = Query(..., description="The search query text", example="དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད། །"),
    search_type: str = Query("hybrid", description="Type of search: 'hybrid', 'bm25', 'semantic', or 'exact'", example="hybrid"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of results to return (1-100)", example=10),
    return_text: bool = Query(True, description="If True, return full text in results. If False, return only ID and distance", example=True),
    title_filter: Optional[str] = Query(None, description="Optional filter by title", example=None)
):
    """
    Unified search endpoint supporting multiple search types.
    
    **Search Types:**
    - `hybrid`: Combines BM25 (sparse) and semantic (dense) search using RRF ranking (default)
    - `bm25`: Keyword-based matching, best for exact term matching
    - `semantic`: Meaning-based matching, best for conceptually similar content
    - `exact`: Exact phrase matching using PHRASE_MATCH, best for finding exact quotes
    
    **Parameters:**
    - `query`: The search query text (required)
    - `search_type`: Type of search (default: "hybrid")
    - `limit`: Maximum results to return (default: 10, max: 100)
    - `return_text`: Return full text or just IDs (default: true)
    - `title_filter`: Optional filter by title field
    
    **Examples:**
    - Hybrid: `/search?query=དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད།&search_type=hybrid&limit=10`
    - BM25: `/search?query=ཕམ་པར་གྱུར་བའི་ཆོས་དུན་པ&search_type=bm25&limit=5`
    - Semantic: `/search?query=how to worry less?&search_type=semantic&limit=10`
    - Exact: `/search?query=དེ་ལ་མི་དགར་ཅི་ཞིག་ཡོད།&search_type=exact&limit=10`
    - IDs Only: `/search?query=test&search_type=hybrid&return_text=false`
    """
    try:
        search_type_lower = search_type.lower()
        
        # Validate search type
        valid_types = ["hybrid", "bm25", "semantic", "exact"]
        if search_type_lower not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid search_type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Build filter expression from title_filter
        filter_expr = None
        if title_filter:
            filter_expr = f'title == "{title_filter}"'
        
        # Route to appropriate search logic
        if search_type_lower == "hybrid":
            return await perform_hybrid_search(query, limit, filter_expr, return_text)
        elif search_type_lower == "bm25":
            return await perform_bm25_search(query, limit, filter_expr, return_text)
        elif search_type_lower == "semantic":
            return await perform_semantic_search(query, limit, filter_expr, return_text)
        elif search_type_lower == "exact":
            return await perform_exact_search(query, limit, filter_expr, return_text)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/search", response_model=SearchResponse)
async def unified_search_post(req: SearchRequest):
    """
    Unified search endpoint (POST) accepting JSON body.
    Mirrors the GET /search behavior using the SearchRequest schema.
    """
    try:
        search_type_lower = req.search_type.lower()
        
        # Validate search type
        valid_types = ["hybrid", "bm25", "semantic", "exact"]
        if search_type_lower not in valid_types:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid search_type. Must be one of: {', '.join(valid_types)}"
            )
        
        # Build filter expression from structured filter
        filter_expr = build_filter_expression(req.filter)
        
        # Route to appropriate search logic
        if search_type_lower == "hybrid":
            return await perform_hybrid_search(req.query, req.limit, filter_expr, req.return_text)
        elif search_type_lower == "bm25":
            return await perform_bm25_search(req.query, req.limit, filter_expr, req.return_text)
        elif search_type_lower == "semantic":
            return await perform_semantic_search(req.query, req.limit, filter_expr, req.return_text)
        elif search_type_lower == "exact":
            return await perform_exact_search(req.query, req.limit, filter_expr, req.return_text)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


# Internal search functions
async def perform_hybrid_search(query: str, limit: int, filter_expr: Optional[str], return_text: bool = True) -> SearchResponse:
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
    
    # Determine output fields based on return_text parameter
    output_fields = ['text'] if return_text else []
    
    # Perform hybrid search
    ranker = RRFRanker()
    results = milvus_client.hybrid_search(
        collection_name=MILVUS_COLLECTION_NAME,
        reqs=[request_1, request_2],
        ranker=ranker,
        limit=limit,
        output_fields=output_fields
    )
    
    return format_results(results, query, "hybrid")


async def perform_bm25_search(query: str, limit: int, filter_expr: Optional[str], return_text: bool = True) -> SearchResponse:
    """Perform BM25 (sparse vector) search."""
    # Determine output fields based on return_text parameter
    output_fields = ['text'] if return_text else []
    
    # Prepare search parameters
    search_params = {
        "collection_name": MILVUS_COLLECTION_NAME,
        "data": [query],
        "anns_field": "sparce_vector",
        "limit": limit,
        "output_fields": output_fields
    }
    
    if filter_expr:
        search_params["filter"] = filter_expr
    
    # Perform BM25 search
    results = milvus_client.search(**search_params)
    
    return format_results(results, query, "bm25")


async def perform_semantic_search(query: str, limit: int, filter_expr: Optional[str], return_text: bool = True) -> SearchResponse:
    """Perform semantic (dense vector) search."""
    # Get embedding
    embedding = get_embedding(query)
    
    # Determine output fields based on return_text parameter
    output_fields = ['text'] if return_text else []
    
    # Prepare search parameters
    search_params = {
        "collection_name": MILVUS_COLLECTION_NAME,
        "data": [embedding],
        "anns_field": "dense_vector",
        "limit": limit,
        "output_fields": output_fields
    }
    
    if filter_expr:
        search_params["filter"] = filter_expr
    
    # Perform semantic search
    results = milvus_client.search(**search_params)
    
    return format_results(results, query, "semantic")


async def perform_exact_search(query: str, limit: int, filter_expr: Optional[str], return_text: bool = True) -> SearchResponse:
    """Perform exact phrase match search."""
    # Escape single quotes in query to prevent filter syntax errors
    escaped_query = query.replace("'", "\\'")
    
    # Build filter expression for exact phrase match
    phrase_filter = f"PHRASE_MATCH(text, '{escaped_query}')"
    
    # Combine filters if additional filter exists
    if filter_expr:
        final_filter = f"{phrase_filter} && {filter_expr}"
    else:
        final_filter = phrase_filter
    
    # Determine output fields based on return_text parameter
    output_fields = ['text'] if return_text else []
    
    # Prepare search parameters
    search_params = {
        "collection_name": MILVUS_COLLECTION_NAME,
        "data": [query],
        "anns_field": "sparce_vector",
        "limit": limit,
        "output_fields": output_fields,
        "filter": final_filter
    }
    
    # Perform exact match search
    results = milvus_client.search(**search_params)
    
    return format_results(results, query, "exact")


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
        # Test basic BM25 search without any fancy options
        results = milvus_client.search(
            collection_name=MILVUS_COLLECTION_NAME,
            data=["how to worry less?"],
            anns_field="sparce_vector",
            limit=5,
            output_fields=["text"]
        )
        
        return {
            "status": "success",
            "raw_results": str(results),
            "results_type": str(type(results)),
            "results_length": len(results),
            "first_result": str(results[0]) if results else None
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "error_type": str(type(e))
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

