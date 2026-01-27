from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from schemas.schemas import PDFDocumentSchema
from config.database import get_db
from repositories.pdf_repository import PDFRepository
from services.pdf_service import process_pdf

router = APIRouter(prefix="/api")

@router.post("/upload-pdf", response_model=PDFDocumentSchema)
async def upload_pdf(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF allowed")

    contents = await file.read()
    doc = PDFRepository.create(db, file.filename)

    try:
        html = process_pdf(contents, doc, db)
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


@router.get("/documents", response_model=list[PDFDocumentSchema])
def list_docs(db: Session = Depends(get_db)):
    return PDFRepository.get_all(db)


@router.get("/documents/{doc_id}", response_model=PDFDocumentSchema)
def get_doc(doc_id: int, db: Session = Depends(get_db)):
    doc = PDFRepository.get(db, doc_id)
    if not doc:
        raise HTTPException(404, "Not found")
    return doc
