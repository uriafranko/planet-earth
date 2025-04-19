import shutil
from datetime import datetime
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlmodel import Session, col, select

from app.db.session import get_session
from app.models.documents import Document
from app.tasks.documents import process_document

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = "uploaded_documents"
Path.mkdir(Path(UPLOAD_DIR), parents=True, exist_ok=True)

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    title: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    session: Annotated[Session, Depends(get_session)]
):
    # Save file to disk
    if not file.filename or "." not in file.filename:
        raise HTTPException(status_code=400, detail="Invalid file name")
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in {"txt", "pdf", "docx"}:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    file_type = "plain" if file_ext == "txt" else file_ext
    created_at = datetime.utcnow()
    file_path = Path(UPLOAD_DIR) / f"{created_at.isoformat()}_{file.filename}"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Create Document record
    document = Document(
        title=title,
        created_at=created_at,
        original_filename=file.filename,
        file_type=file_type,
    )
    session.add(document)
    session.commit()
    session.refresh(document)
    process_document.delay(document.id)
    return {"message": "Document uploaded successfully", "document_id": str(document.id)}

class DocumentListResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    original_filename: str | None = None
    file_type: str
    text: str | None = None

@router.get("", response_model=list[DocumentListResponse])
def list_documents(session: Annotated[Session, Depends(get_session)]):
    documents = session.exec(
        select(Document).order_by(col(Document.created_at).desc())
    ).all()
    return [
        DocumentListResponse(
            id=str(doc.id),
            title=doc.title,
            created_at=doc.created_at,
            original_filename=doc.original_filename,
            file_type=doc.file_type,
            text=doc.text,
        )
        for doc in documents
    ]

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: str,
    session: Annotated[Session, Depends(get_session)]
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    session.delete(document)
    session.commit()
    return {"message": "Document deleted successfully"}


@router.get("/{document_id}", response_model=DocumentListResponse)
def get_document(
    document_id: str,
    session: Annotated[Session, Depends(get_session)]
):
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentListResponse(
        id=str(document.id),
        title=document.title,
        created_at=document.created_at,
        original_filename=document.original_filename,
        file_type=document.file_type,
        text=document.text,
    )
