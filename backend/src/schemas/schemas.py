from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class TokenUsage(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
class PDFDocumentSchema(BaseModel):
    id: int
    filename: str
    edited_html: Optional[str] = None
    original_html: Optional[str] = None

    status: str
    total_pages: Optional[int] = None
    processed_pages: Optional[int] = None

    total_tokens: int
    tokens_per_page: Dict[str, TokenUsage]

    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


from pydantic import BaseModel
from typing import List

class PaginatedPDFResponse(BaseModel):
    items: List[PDFDocumentSchema]
    total: int
    page: int
    page_size: int
