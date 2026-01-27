from config.database import SessionLocal
from models.models import PDFDocument
from config.logger import get_logger
from sqlalchemy.orm import Session
logger = get_logger("pdf_migration")


def migrate_tokens():
    db = SessionLocal()
    try:
        docs = db.query(PDFDocument).all()
        logger.info(f"Migrating {len(docs)} documents")

        for doc in docs:
            if not doc.tokens_per_page:
                doc.tokens_per_page = {}
                continue

            new_map = {}
            for k, v in doc.tokens_per_page.items():
                if isinstance(v, int):
                    new_map[str(k)] = {
                        "input_tokens": 0,
                        "output_tokens": v,
                        "total_tokens": v
                    }
                else:
                    new_map[str(k)] = v

            doc.tokens_per_page = new_map

        db.commit()
        logger.info("Token migration completed successfully")

    finally:
        db.close()

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
