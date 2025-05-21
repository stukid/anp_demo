import os
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from asyncio import CancelledError
import logging
import asyncio
from urllib.parse import urlparse

from .log_base import setup_logging
from .anp_tool import ANPTool
from .models import (
    QueryRequest,
    QueryResponse,
    AgentDocTreeRequest,
    AgentDocTreeResponse,
    GetDocumentRequest,
    GetDocumentResponse,
)
from .simple_example import simple_crawl

# Set up logging
setup_logging(logging.INFO)

# Get project root directory
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = Path(__file__).resolve().parent.parent.parent

# Initialize FastAPI application
app = FastAPI(
    title="ANP Network Explorer",
    description="Agent Network Explorer application based on ANP protocol",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)
   
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static"), html=True), name="static")    

# Get DID paths
did_document_path = str(ROOT_DIR / "use_did_test_public/did.json")
private_key_path = str(ROOT_DIR / "use_did_test_public/key-1_private.pem")

event_queue = []

# @app.get("/api/health")
# async def health_check():
#     """Health check endpoint"""
#     return {"status": "ok", "service": "ANP Network Explorer API"}

@app.get("/", response_class=HTMLResponse)
async def root():
    return FileResponse(BASE_DIR / "static" / "index.html")

# @app.get("/agent-doc-tree.html", response_class=HTMLResponse)
# async def read_agent_doc_tree():
#     return FileResponse(BASE_DIR / "frontend" / "agent-doc-tree.html")

# @app.get("/", response_class=HTMLResponse)
# async def read_root():
#     """Serve frontend page"""
#     print(f"---BASE_DIR: {BASE_DIR}")
#     try:
#         with open(BASE_DIR / "frontend" / "index.html", "r", encoding="utf-8") as f:
#             content = f.read()
#         return content
#     except Exception as e:
#         logging.error(f"Error reading frontend page: {str(e)}")
#         raise HTTPException(
#             status_code=500, detail=f"Error reading frontend page: {str(e)}"
#         )


@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """Process query request"""
    try:
        # Use agent URL provided by user or default URL
        initial_url = (
            request.agent_url
            if request.agent_url
            else "https://agent-search.ai/ad.json"
        )

        event_queue.append(f"query: {request.query}, begin to crawl: {initial_url}")
        # Call simple_crawl function
        result = await simple_crawl(
            user_input=request.query,
            task_type="general",
            did_document_path=did_document_path,
            private_key_path=private_key_path,
            max_documents=20,  # Crawl up to 10 documents
            initial_url=initial_url,  # Pass in user provided URL
            event_queue=event_queue
        )

        event_queue.append(f"query: {request.query}, crawl finished")

        return result
    except Exception as e:
        logging.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")


@app.post("/api/agent-doc-tree", response_model=AgentDocTreeResponse)
async def agent_doc_tree(request: AgentDocTreeRequest):
    """Parse agent URL and its child documents, build document tree"""
    try:
        # Use agent URL provided by user or default URL
        initial_url = (
            request.agent_url
            if request.agent_url
            else "https://agent-search.ai/ad.json"
        )

        # Initialize ANPTool
        anp_tool = ANPTool(
            did_document_path=did_document_path, private_key_path=private_key_path
        )

        # Initialize sets of visited URLs and list of crawled documents
        visited_urls = set()
        crawled_documents = []

        # Recursively get documents
        await crawl_doc_tree(
            initial_url, anp_tool, visited_urls, crawled_documents, level=0, max_level=5
        )

        # Process document tree structure
        doc_tree = process_doc_tree(crawled_documents)

        return {
            "doc_tree": doc_tree,
            "visited_urls": list(visited_urls),
            "crawled_documents": crawled_documents,
        }
    except Exception as e:
        logging.error(f"Error building document tree: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error building document tree: {str(e)}")


async def crawl_doc_tree(
    url, anp_tool, visited_urls, crawled_documents, level=0, max_level=5, max_docs=30
):
    """Function to recursively get documents and their linked content"""
    # Return if already visited URL or reached max depth or document count limit
    if url in visited_urls or level >= max_level or len(crawled_documents) >= max_docs:
        return

    try:
        # Use ANPTool to get URL content
        result = await anp_tool.execute(url=url)

        # Record visited URL and obtained content
        visited_urls.add(url)
        crawled_documents.append({"url": url, "method": "GET", "content": result})

        logging.info(f"Successfully obtained document: {url}, current depth: {level}")

        # Extract links from document
        links = extract_links(result)

        # Recursively get linked documents
        for link in links:
            if len(crawled_documents) >= max_docs:
                break

            # Skip already visited URLs
            if link in visited_urls:
                continue

            await crawl_doc_tree(
                link,
                anp_tool,
                visited_urls,
                crawled_documents,
                level + 1,
                max_level,
                max_docs,
            )

    except Exception as e:
        logging.error(f"Failed to get document: {url}, error: {str(e)}")


def extract_links(data):
    """Extract links from JSON-LD document"""
    links = set()

    def traverse(obj):
        if not obj or not isinstance(obj, dict):
            return

        # Process links in specific fields
        for key in ["@id", "url", "serviceEndpoint"]:
            if key in obj and isinstance(obj[key], str) and is_valid_url(obj[key]):
                links.add(obj[key])

        # Check if other properties are objects or arrays
        for key, value in obj.items():
            if key == "@context":
                continue  # Skip @context

            if isinstance(value, dict):
                traverse(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        traverse(item)

    traverse(data)
    return links


def is_valid_url(url):
    """Validate if URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def process_doc_tree(documents):
    """Process documents, build tree structure"""
    doc_tree = {"name": "Root Node", "children": []}
    url_map = {}

    # First add all document nodes
    for doc in documents:
        url = doc["url"]
        node = {"name": url.split("/")[-1], "url": url, "children": [], "doc": doc}
        url_map[url] = node

        # If it's the root node
        if doc == documents[0]:
            doc_tree["children"].append(node)

    # Then establish connection relationships
    for doc in documents[1:]:  # Skip the first (root) document
        url = doc["url"]
        node = url_map[url]

        # Find parent node
        found_parent = False
        for parent_doc in documents:
            parent_url = parent_doc["url"]
            if parent_url == url:
                continue

            # Check if parent document content contains current URL
            try:
                content_str = str(parent_doc["content"])
                if url in content_str:
                    # Found a possible parent node
                    parent_node = url_map[parent_url]
                    parent_node["children"].append(node)
                    found_parent = True
                    break
            except:
                pass

        # If no parent node found, add to root node
        if not found_parent:
            doc_tree["children"].append(node)

    return doc_tree


@app.post("/api/get-document", response_model=GetDocumentResponse)
async def get_document(request: GetDocumentRequest):
    """Get document content by URL"""
    try:
        # Get URL
        url = request.url
        if not url:
            raise HTTPException(status_code=400, detail="URL parameter cannot be empty")

        # Initialize ANPTool
        anp_tool = ANPTool(
            did_document_path=did_document_path, private_key_path=private_key_path
        )

        # Use ANPTool to get URL content
        try:
            result = await anp_tool.execute(url=url)

            return {
                "url": url,
                "content": result,
                "success": True,
                "message": "Successfully retrieved document",
            }
        except Exception as e:
            logging.error(f"Failed to get document via ANPTool: {url}, error: {str(e)}")
            return {
                "url": url,
                "content": None,
                "success": False,
                "message": f"Failed to get document: {str(e)}",
            }

    except Exception as e:
        logging.error(f"Failed to get document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@app.get("/api/events")
async def stream_events(request: Request):
    print("transferring events")
    async def event_generator():
        last_index = 0
        try:
            while True:
                if await request.is_disconnected():
                    break
                if last_index < len(event_queue):
                    yield {
                        "event": "event",
                        "data": event_queue[last_index]
                    }
                    last_index += 1
                await asyncio.sleep(0.5)
        except CancelledError:
            print("server shutdown")
            return
    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    # Startup port
    port = int(os.environ.get("PORT", 5000))

    # Start uvicorn server
    uvicorn.run(
        "src.anp_demo.backend.anp_examples_backend:app",
        host="127.0.0.1",
        port=port,
        reload=True,
    )
