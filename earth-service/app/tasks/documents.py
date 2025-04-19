"""Tasks for processing uploaded documents: extraction, chunking, embedding, and vector storage."""

import os
from pathlib import Path

from app.core.logging import get_logger
from app.db.session import get_session_context
from app.models.documents import Document, DocumentChunk
from app.services.embedder import get_embedder
from app.services.markdown_extractor import extract_markdown
from app.services.text_chunker import chunk_text
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)
UPLOAD_DIR = "uploaded_documents"

@celery_app.task(bind=True, name="process_document")
def process_document(self, document_id: str) -> dict:
    """
    Celery task to process a document:
    - Extract markdown from file using markitdown
    - Chunk the markdown text
    - Generate embeddings for each chunk
    - Store DocumentChunk records and vectors in the vector store
    """
    with get_session_context() as session:
        try:
            document = session.get(Document, document_id)
            if not document:
                return {"status": "error", "error": "Document not found", "document_id": document_id}

            # Find the uploaded file
            file_path = None
            for fname in os.listdir(UPLOAD_DIR):
                if document.original_filename and fname.endswith(document.original_filename):
                    file_path = os.path.join(UPLOAD_DIR, fname)
                    break
            if not file_path or not Path(file_path).exists():
                return {"status": "error", "error": "File not found", "document_id": document_id}

            # Extract markdown
            markdown = extract_markdown(file_path)
            document.text = markdown
            session.add(document)
            session.flush()

            # Chunk text
            chunks = chunk_text(markdown)
            if not chunks:
                return {"status": "error", "error": "No chunks found", "document_id": document_id}
            # Embed chunks
            embedder = get_embedder()

            chunk_objs = []
            for idx, chunk in enumerate(chunks):
                if not chunk:
                    continue
                doc_chunk = DocumentChunk(
                    document_id=document.id,
                    chunk_index=idx,
                    text=chunk,
                    embedding=embedder.embed_text(chunk),
                )
                session.add(doc_chunk)
                session.flush()  # get chunk.id
                # Store vector in vector store
                chunk_objs.append(doc_chunk)


            try:
                Path(file_path).unlink()
            except OSError as e:
                # Log the error but don't fail the task
                logger.warning(f"Error removing file {file_path}: {e}")

            return {"status": "success", "document_id": document_id, "chunks": [str(c.id) for c in chunk_objs]}
        except Exception as e:
            session.rollback()
            return {"status": "error", "error": str(e), "document_id": document_id}
