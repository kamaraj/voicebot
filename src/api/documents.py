"""
Document upload and processing API endpoints
Supports PDF, TXT, and MD file uploads for RAG knowledge base
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any
import structlog
from pathlib import Path
import tempfile
import os

# PDF processing
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

from src.rag.chromadb_retriever import get_rag_retriever

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file"""
    if not PDF_AVAILABLE:
        raise ImportError("PyPDF2 is required for PDF processing. Install with: pip install PyPDF2")
    
    text = ""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                text += f"\n\n--- Page {page_num + 1} ---\n\n{page_text}"
        
        logger.info("pdf_text_extracted", pages=len(pdf_reader.pages))
        return text.strip()
    except Exception as e:
        logger.error("pdf_extraction_error", error=str(e))
        raise


def extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        logger.info("txt_text_extracted", length=len(text))
        return text.strip()
    except Exception as e:
        logger.error("txt_extraction_error", error=str(e))
        raise


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks for better retrieval.
    
    Args:
        text: Full text to chunk
        chunk_size: Maximum size of each chunk
        overlap: Number of characters to overlap between chunks
        
    Returns:
        List of text chunks
    """
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < text_length:
            # Look for sentence ending within last 100 chars
            last_period = text.rfind('.', end - 100, end)
            if last_period != -1:
                end = last_period + 1
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap if end < text_length else end
    
    logger.info("text_chunked", chunks=len(chunks))
    return chunks


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> Dict[str, Any]:
    """
    Upload a document (PDF, TXT, MD) and add it to the knowledge base.
    
    Args:
        file: Uploaded file
        chunk_size: Size of text chunks (default: 1000)
        chunk_overlap: Overlap between chunks (default: 200)
        
    Returns:
        Upload status and statistics
    """
    logger.info("document_upload_started", filename=file.filename)
    
    # Validate file type
    allowed_extensions = {'.pdf', '.txt', '.md'}
    file_ext = Path(file.filename).suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as tmp_file:
        tmp_path = tmp_file.name
        contents = await file.read()
        tmp_file.write(contents)
    
    try:
        # Extract text based on file type
        if file_ext == '.pdf':
            if not PDF_AVAILABLE:
                raise HTTPException(
                    status_code=500,
                    detail="PDF processing not available. Install PyPDF2: pip install PyPDF2"
                )
            text = extract_text_from_pdf(tmp_path)
        else:  # .txt or .md
            text = extract_text_from_txt(tmp_path)
        
        if not text:
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from the file"
            )
        
        # Chunk the text
        chunks = chunk_text(text, chunk_size=chunk_size, overlap=chunk_overlap)
        
        # Create metadata for each chunk
        metadatas = [
            {
                "source": file.filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "file_type": file_ext
            }
            for i in range(len(chunks))
        ]
        
        # Add to knowledge base
        rag = get_rag_retriever()
        rag.add_documents(chunks, metadatas)
        
        logger.info("document_uploaded_successfully",
                   filename=file.filename,
                   chunks_added=len(chunks))
        
        return {
            "status": "success",
            "filename": file.filename,
            "file_type": file_ext,
            "text_length": len(text),
            "chunks_created": len(chunks),
            "chunks_added": len(chunks),
            "total_documents_in_kb": rag.get_stats()["total_documents"]
        }
        
    except Exception as e:
        logger.error("document_upload_error",
                    filename=file.filename,
                    error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except:
            pass


@router.post("/upload-multiple")
async def upload_multiple_documents(
    files: List[UploadFile] = File(...),
    chunk_size: int = 1000,
    chunk_overlap: int = 200
) -> Dict[str, Any]:
    """
    Upload multiple documents at once.
    
    Args:
        files: List of uploaded files
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks
        
    Returns:
        Upload status for all files
    """
    results = []
    total_chunks = 0
    
    for file in files:
        try:
            result = await upload_document(file, chunk_size, chunk_overlap)
            results.append({
                "filename": file.filename,
                "status": "success",
                "chunks_added": result["chunks_created"]
            })
            total_chunks += result["chunks_created"]
        except Exception as e:
            results.append({
                "filename": file.filename,
                "status": "error",
                "error": str(e)
            })
    
    rag = get_rag_retriever()
    
    return {
        "total_files": len(files),
        "successful": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] == "error"),
        "total_chunks_added": total_chunks,
        "total_documents_in_kb": rag.get_stats()["total_documents"],
        "results": results
    }


@router.get("/stats")
async def get_knowledge_base_stats() -> Dict[str, Any]:
    """Get knowledge base statistics"""
    rag = get_rag_retriever()
    stats = rag.get_stats()
    
    return {
        "status": "ok",
        "knowledge_base": stats
    }


@router.post("/search")
async def search_knowledge_base(
    query: str,
    top_k: int = 5,
    score_threshold: float = 0.0
) -> Dict[str, Any]:
    """
    Search the knowledge base.
    
    Args:
        query: Search query
        top_k: Number of results
        score_threshold: Minimum similarity score
        
    Returns:
        Search results
    """
    rag = get_rag_retriever()
    results = rag.search(query, top_k=top_k, score_threshold=score_threshold)
    
    return {
        "query": query,
        "results_count": len(results),
        "results": results
    }


@router.get("/list")
async def list_documents() -> Dict[str, Any]:
    """
    List all documents in the knowledge base.
    
    Returns:
        List of documents with metadata grouped by source file
    """
    rag = get_rag_retriever()
    
    # Get all documents from the collection
    try:
        all_docs = rag.collection.get(
            include=["metadatas", "documents"]
        )
        
        # Group by source filename
        documents_by_source = {}
        
        for i, metadata in enumerate(all_docs['metadatas']):
            source = metadata.get('source', 'sample_knowledge')
            
            if source not in documents_by_source:
                documents_by_source[source] = {
                    "source": source,
                    "file_type": metadata.get('file_type', 'built-in'),
                    "chunks": [],
                    "total_chunks": 0
                }
            
            documents_by_source[source]["chunks"].append({
                "chunk_index": metadata.get('chunk_index', 0),
                "text_preview": all_docs['documents'][i][:200] + "..." if len(all_docs['documents'][i]) > 200 else all_docs['documents'][i],
                "text_length": len(all_docs['documents'][i])
            })
            documents_by_source[source]["total_chunks"] = metadata.get('total_chunks', len(documents_by_source[source]["chunks"]))
        
        # Convert to list and sort
        documents_list = sorted(documents_by_source.values(), key=lambda x: x['source'])
        
        logger.info("documents_listed", total_sources=len(documents_list))
        
        return {
            "status": "success",
            "total_sources": len(documents_list),
            "total_chunks": sum(d["total_chunks"] for d in documents_list),
            "documents": documents_list
        }
        
    except Exception as e:
        logger.error("list_documents_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error listing documents: {str(e)}"
        )


@router.get("/view/{source_name}")
async def view_document(source_name: str) -> Dict[str, Any]:
    """
    Get all content for a specific document.
    
    Args:
        source_name: The source filename (e.g., "1_System_Usage_FAQ.pdf")
        
    Returns:
        Full document content reconstructed from chunks
    """
    rag = get_rag_retriever()
    
    try:
        all_docs = rag.collection.get(
            include=["metadatas", "documents"]
        )
        
        # Find chunks for this source
        chunks = []
        for i, metadata in enumerate(all_docs['metadatas']):
            if metadata.get('source') == source_name:
                chunks.append({
                    "index": metadata.get('chunk_index', 0),
                    "text": all_docs['documents'][i]
                })
        
        if not chunks:
            raise HTTPException(
                status_code=404,
                detail=f"Document '{source_name}' not found"
            )
        
        # Sort by chunk index and combine
        chunks.sort(key=lambda x: x['index'])
        full_content = "\n\n".join([c['text'] for c in chunks])
        
        logger.info("document_viewed", source=source_name, chunks=len(chunks))
        
        return {
            "status": "success",
            "source": source_name,
            "total_chunks": len(chunks),
            "content": full_content
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("view_document_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Error viewing document: {str(e)}"
        )


@router.delete("/clear")
async def clear_knowledge_base() -> Dict[str, str]:
    """Clear all documents from knowledge base (use with caution!)"""
    rag = get_rag_retriever()
    rag.clear()
    
    logger.warning("knowledge_base_cleared")
    
    return {
        "status": "success",
        "message": "Knowledge base cleared"
    }
