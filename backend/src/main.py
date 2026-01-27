from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pdf2image import convert_from_bytes
from io import BytesIO
from typing import List
import google.generativeai as genai
import os
import base64
import time

from config.logger import get_logger
logger = get_logger("pdf_processor")

from config.database import SessionLocal, engine
from models.models import PDFDocument, Base
from schemas.schemas import PDFDocumentSchema


logger.info("🚀 Starting PDF Processor Service")

Base.metadata.create_all(bind=engine)
logger.info("📦 Database tables ensured")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
# GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "*****")
# if GEMINI_API_KEY == "*****":
#     logger.warning("⚠️ GEMINI_API_KEY not set, using placeholder")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyC0zhIUx33-mZSmMLZGxyjvIHteiCEfMmc")


genai.configure(api_key=GEMINI_API_KEY)
logger.info("Gemini configured")

# Dependency
def get_db():
    logger.debug("Opening DB session")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        logger.debug("Closed DB session")


def extract_text_from_response(response) -> str:
    logger.debug("Extracting text from Gemini response")
    parts = response.candidates[0].content.parts
    texts = []
    for part in parts:
        if hasattr(part, "text"):
            texts.append(part.text)
    final_text = "".join(texts)
    logger.debug(f"Extracted {len(final_text)} characters from Gemini")
    return final_text


# Helper: Convert PDF to HTML using Gemini
def pdf_to_html_with_gemini(pdf_bytes: bytes) -> str:
    logger.info("📄 Starting PDF → HTML conversion")
    start_time = time.time()

    try:
        # Convert PDF pages to images
        images = convert_from_bytes(pdf_bytes, dpi=300)
        logger.info(f"🖼️ Converted PDF into {len(images)} images")

        model = genai.GenerativeModel('gemini-2.5-flash')
        logger.info("Gemini model initialized")

        html_pages = ['<div class="pdf-content">']

        for page_num, image in enumerate(images, 1):
            logger.info(f"➡️ Processing page {page_num}")

            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            prompt = f"""
            Analyze this PDF page image (Page {page_num}) and convert it to clean, semantic HTML.
            
            Requirements:
            1. Preserve the exact visual layout and design
            2. Identify headers, paragraphs, lists, tables, and other elements
            3. Maintain font sizes, spacing, and alignment as closely as possible
            4. Use appropriate HTML5 semantic tags (header, section, article, etc.)
            5. Add CSS classes for styling (use Tailwind-like class names)
            6. Preserve text hierarchy (h1, h2, h3, p, etc.)
            7. For tables, create proper HTML table structure
            8. For images, use placeholder <img> tags with descriptions
            
            Return ONLY the HTML code for this page content, wrapped in:
            <div class="page" data-page="{page_num}">
                <!-- page content here -->
            </div>
            
            Do not include <!DOCTYPE>, <html>, <head>, or <body> tags.
            Focus on semantic, well-structured HTML that matches the visual layout.
            """

            logger.debug(f"Sending page {page_num} to Gemini")
            response = model.generate_content([prompt, image])

            page_html = extract_text_from_response(response)
            page_html = page_html.replace('```html', '').replace('```', '').strip()

            logger.info(f"✅ Page {page_num} converted, length={len(page_html)}")
            html_pages.append(page_html)

        html_pages.append('</div>')
        total_time = round(time.time() - start_time, 2)

        logger.info(f"🎉 PDF conversion finished in {total_time}s")
        return "\n".join(html_pages)

    except Exception as e:
        logger.exception("❌ Error during PDF processing")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF with Gemini: {str(e)}"
        )


# Health check
@app.get("/health")
async def health():
    logger.info("Health check called")
    return {"status": "ok"}


# Upload PDF
@app.post("/api/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    logger.info(f"📤 Upload request received: {file.filename}")

    if not file.filename.endswith(".pdf"):
        logger.warning("Non-PDF upload attempt")
        raise HTTPException(status_code=400, detail="Only PDF allowed")

    contents = await file.read()
    logger.info(f"File size: {len(contents)} bytes")

    html_output = pdf_to_html_with_gemini(contents)
    logger.info("HTML generated from PDF")

    doc = PDFDocument(
        filename=file.filename,
        original_html=html_output,
        edited_html=html_output
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)

    logger.info(f"📄 Document saved with ID={doc.id}")

    return {
        "id": doc.id,
        "filename": doc.filename,
        "original_html": doc.original_html,
        "edited_html": doc.edited_html,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at
    }


# List all PDFs
@app.get("/api/documents", response_model=List[PDFDocumentSchema])
def get_documents(db: Session = Depends(get_db)):
    logger.info("Fetching all documents")
    docs = db.query(PDFDocument).order_by(PDFDocument.created_at.desc()).all()
    logger.info(f"Returned {len(docs)} documents")
    return docs


# Get single PDF by id
@app.get("/api/documents/{doc_id}", response_model=PDFDocumentSchema)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    logger.info(f"Fetching document ID={doc_id}")
    doc = db.query(PDFDocument).filter(PDFDocument.id == doc_id).first()

    if not doc:
        logger.warning(f"Document not found ID={doc_id}")
        raise HTTPException(status_code=404, detail="Document not found")

    logger.info(f"Document found ID={doc_id}")
    return doc


# Update edited HTML
@app.put("/api/documents/{doc_id}", response_model=PDFDocumentSchema)
def update_document(doc_id: int, payload: dict, db: Session = Depends(get_db)):
    logger.info(f"Updating document ID={doc_id}")

    doc = db.query(PDFDocument).filter(PDFDocument.id == doc_id).first()
    if not doc:
        logger.warning(f"Update failed, document not found ID={doc_id}")
        raise HTTPException(status_code=404, detail="Document not found")

    edited_html = payload.get("edited_html")
    if edited_html is None:
        logger.warning("Update payload missing edited_html")
        raise HTTPException(status_code=400, detail="edited_html is required")

    doc.edited_html = edited_html
    db.commit()
    db.refresh(doc)

    logger.info(f"Document ID={doc_id} updated successfully")
    return doc
