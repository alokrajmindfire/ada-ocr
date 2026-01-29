from fastapi import APIRouter, UploadFile, Query, File, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.schemas import PDFDocumentSchema,PaginatedPDFResponse
from config.database import get_db
from repositories.pdf_repository import PDFRepository
from services.pdf_service import process_pdf

router = APIRouter(prefix="/api")

@router.post("/upload-pdf", response_model=PDFDocumentSchema)
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF allowed")

    pdf_bytes = await file.read()
    doc = PDFRepository.create(db, file.filename)

    try:
        html = process_pdf(pdf_bytes, doc, db)
        doc.original_html = html
        doc.edited_html = html
        doc.status = "completed"
    except Exception as e:
        doc.status = "failed"
        db.commit()
        raise HTTPException(500, str(e))

    db.commit()
    db.refresh(doc)
    return doc

@router.get("/documents", response_model=PaginatedPDFResponse)
def list_docs(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    offset = (page - 1) * page_size

    items = PDFRepository.get_all(db, page_size, offset)
    total = PDFRepository.count(db)

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/documents/{doc_id}", response_model=PDFDocumentSchema)
def get_doc(doc_id: int, db: Session = Depends(get_db)):
    doc = PDFRepository.get(db, doc_id)
    if not doc:
        raise HTTPException(404, "Not found")
    return doc
