from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class PDFDocumentSchema(BaseModel):
    id: int
    filename: str
    edited_html: Optional[str] = None
    original_html: Optional[str] = None

    status: str
    processed_pages: int
    total_pages: int

    total_tokens: int
    tokens_per_page: Optional[Dict[int, int]]

    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
