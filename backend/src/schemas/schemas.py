from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PDFDocumentSchema(BaseModel):
    id: int
    filename: str
    original_html: str
    edited_html: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
