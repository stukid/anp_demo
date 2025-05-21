from typing import List, Dict, Any, Optional
from pydantic import BaseModel, HttpUrl, Field


class QueryRequest(BaseModel):
    """Input query request model"""

    query: str = Field(..., description="User's natural language query")
    agent_url: Optional[str] = Field(None, description="URL of the agent description JSON document")


class CrawledDocument(BaseModel):
    """Information about a crawled document"""

    url: str = Field(..., description="URL that was crawled")
    method: str = Field(..., description="HTTP method")
    content: Dict[str, Any] = Field(..., description="Response content")


class QueryResponse(BaseModel):
    """Query response model"""

    content: str = Field(..., description="Answer content returned by the model")
    type: str = Field(..., description="Response type")
    visited_urls: List[str] = Field(..., description="List of visited URLs")
    crawled_documents: List[CrawledDocument] = Field(..., description="List of crawled documents")
    task_type: Optional[str] = Field(None, description="Task type")


class AgentDocTreeRequest(BaseModel):
    """Agent document tree request model"""

    agent_url: Optional[str] = Field(None, description="URL of the agent description JSON document")


class DocumentNode(BaseModel):
    """Document node model"""

    name: str = Field(..., description="Node name")
    url: str = Field(..., description="Node URL")
    children: List["DocumentNode"] = Field(default=[], description="List of child nodes")
    doc: Optional[Dict[str, Any]] = Field(None, description="Document content")


# Update recursive reference
DocumentNode.update_forward_refs()


class DocumentTree(BaseModel):
    """Document tree model"""

    name: str = Field(..., description="Root name")
    children: List[DocumentNode] = Field(default=[], description="List of child nodes")


class AgentDocTreeResponse(BaseModel):
    """Agent document tree response model"""

    doc_tree: DocumentTree = Field(..., description="Document tree structure")
    visited_urls: List[str] = Field(..., description="List of visited URLs")
    crawled_documents: List[CrawledDocument] = Field(..., description="List of crawled documents")


class GetDocumentRequest(BaseModel):
    """Get document request model"""

    url: str = Field(..., description="URL of the document to retrieve")


class GetDocumentResponse(BaseModel):
    """Get document response model"""

    url: str = Field(..., description="URL of the retrieved document")
    content: Optional[Dict[str, Any]] = Field(None, description="Document content")
    success: bool = Field(..., description="Whether the retrieval was successful")
    message: str = Field(..., description="Message describing the result")
