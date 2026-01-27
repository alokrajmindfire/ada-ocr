from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from config.database import Base

class PDFDocument(Base):
    __tablename__ = "pdf_documents"

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    original_html = Column(Text)
    edited_html = Column(Text)
    
    
    # progress
    status = Column(String, default="processing")   # processing | completed | failed
    processed_pages = Column(Integer, default=0)
    total_pages = Column(Integer, default=0)
    
    total_tokens = Column(Integer, default=0)
    tokens_per_page = Column(JSON)   # {1: 450, 2: 380}

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
