from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pdf2image import convert_from_bytes
from io import BytesIO
from typing import List
import google.generativeai as genai
import os
import base64

from database import SessionLocal, engine
from models import PDFDocument, Base

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBw3pirY46jDJL5VztoSKZBdpeR1xbe6lY")
genai.configure(api_key=GEMINI_API_KEY)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Helper: Convert PDF to HTML using Gemini
def pdf_to_html_with_gemini(pdf_bytes: bytes) -> str:
    """
    Convert PDF to images and use Gemini to extract HTML with layout preservation
    """
    try:
        # Convert PDF pages to images
        images = convert_from_bytes(pdf_bytes, dpi=300)
        
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        html_pages = ['<div class="pdf-content">']
        
        for page_num, image in enumerate(images, 1):
            # Convert PIL Image to bytes
            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Prepare prompt for Gemini
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
            
            # Generate content with Gemini
            response = model.generate_content([prompt, image])
            page_html = response.text
            
            # Clean up response (remove markdown code blocks if present)
            page_html = page_html.replace('```html', '').replace('```', '').strip()
            
            html_pages.append(page_html)
        
        html_pages.append('</div>')
        return "\n".join(html_pages)
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing PDF with Gemini: {str(e)}"
        )

# Health check
@app.get("/health")
async def health():
    return {"status": "ok"}

# Upload PDF
@app.post("/api/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF allowed")

    contents = await file.read()
    
    # Use Gemini to convert PDF to HTML
    html_output = pdf_to_html_with_gemini(contents)

    doc = PDFDocument(
        filename=file.filename,
        original_html=html_output,
        edited_html=html_output
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "id": doc.id,
        "filename": doc.filename,
        "original_html": doc.original_html,
        "edited_html": doc.edited_html,
        "created_at": doc.created_at,
        "updated_at": doc.updated_at
    }

from schemas import PDFDocumentSchema

# List all PDFs
@app.get("/api/documents", response_model=List[PDFDocumentSchema])
def get_documents(db: Session = Depends(get_db)):
    docs = db.query(PDFDocument).order_by(PDFDocument.created_at.desc()).all()
    return docs

# Get single PDF by id
@app.get("/api/documents/{doc_id}", response_model=PDFDocumentSchema)
def get_document(doc_id: int, db: Session = Depends(get_db)):
    doc = db.query(PDFDocument).filter(PDFDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

# Update edited HTML
@app.put("/api/documents/{doc_id}", response_model=PDFDocumentSchema)
def update_document(doc_id: int, payload: dict, db: Session = Depends(get_db)):
    doc = db.query(PDFDocument).filter(PDFDocument.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    edited_html = payload.get("edited_html")
    if edited_html is None:
        raise HTTPException(status_code=400, detail="edited_html is required")

    doc.edited_html = edited_html
    db.commit()
    db.refresh(doc)

    return doc