from sqlalchemy.orm import Session
from models.models import PDFDocument
from config.logger import get_logger

logger = get_logger("pdf_repository")


class PDFRepository:

    @staticmethod
    def create(db: Session, filename: str):
        logger.info(f"Creating PDFDocument record for file: {filename}")

        doc = PDFDocument(
            filename=filename,
            status="processing",
            processed_pages=0,
            total_pages=0,
            total_tokens=0,
            tokens_per_page={}
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)

        logger.info(f"PDFDocument created with id={doc.id}")
        return doc

    @staticmethod
    def get_all(db: Session):
        logger.info("Fetching all PDFDocument records")
        docs = db.query(PDFDocument).order_by(PDFDocument.created_at.desc()).all()
        logger.info(f"Fetched {len(docs)} PDFDocument records")
        return docs

    @staticmethod
    def get(db: Session, doc_id: int):
        logger.info(f"Fetching PDFDocument with id={doc_id}")
        doc = db.query(PDFDocument).filter(PDFDocument.id == doc_id).first()

        if not doc:
            logger.warning(f"PDFDocument not found id={doc_id}")
        else:
            logger.info(f"PDFDocument found id={doc_id}")

        return doc
