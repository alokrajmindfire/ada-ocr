# PDF to HTML Converter (ADA OCR)

A minimal web application that converts PDF files to semantic HTML using Google Gemini, stores them in a MySQL database, and allows users to edit and preview the converted HTML.

Repository:
[https://github.com/alokrajmindfire/ada-ocr.git](https://github.com/alokrajmindfire/ada-ocr.git)

---

## Features

* Upload PDF files
* Convert each PDF page to HTML using **Gemini Vision**
* Preserve layout with semantic HTML
* Store original and edited HTML in **MySQL**
* Track processing progress:

  * status
  * processed pages
  * total pages
  * token usage
* Edit HTML in a text editor
* Preview original and edited HTML
* Minimal, functional design

---

## Tech Stack

### Frontend

* React with TypeScript
* Tailwind CSS
* shadcn/ui
* Vite

### Backend

* Python FastAPI
* pdf2image (PDF → images)
* Google Gemini (`gemini-2.5-flash`)
* SQLAlchemy ORM

### Database

* MySQL

### Infrastructure

* Docker & Docker Compose

---

## Backend Data Model

### `PDFDocument` (SQLAlchemy)

```python
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

    # tokens
    total_tokens = Column(Integer, default=0)
    tokens_per_page = Column(JSON)   # {1: 450, 2: 380}

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
```

---

## Database Schema (MySQL)

```sql
CREATE TABLE pdf_documents (
  id INT AUTO_INCREMENT PRIMARY KEY,
  filename VARCHAR(255),
  original_html LONGTEXT,
  edited_html LONGTEXT,

  status VARCHAR(50) DEFAULT 'processing',
  processed_pages INT DEFAULT 0,
  total_pages INT DEFAULT 0,

  total_tokens INT DEFAULT 0,
  tokens_per_page JSON,

  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

---

## Setup Instructions

### Prerequisites

* Docker & Docker Compose
* Google Gemini API Key

---

### 1. Clone Repository

```bash
git clone https://github.com/alokrajmindfire/ada-ocr.git
cd ada-ocr
```

---

### 2. Environment Variables

Create `.env` inside `backend/`:

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/ada_ocr
GEMINI_API_KEY=YOUR_GEMINI_KEY
```

---

### 3. Run with Docker

```bash
docker-compose up --build
```

Services:

* Frontend: [http://localhost:5173](http://localhost:5173)
* Backend: [http://localhost:8000](http://localhost:8000)
* Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Development (Without Docker)

### Backend

```bash
cd backend
pip install -r requirements.txt
python main.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## API Endpoints

### Health Check

```
GET /health
```

Response:

```json
{ "status": "ok" }
```

---

### Upload PDF

```
POST /api/upload-pdf
```

Body:

* multipart/form-data
* key: `file` (PDF)

Response:

```json
{
  "id": 1,
  "filename": "sample.pdf",
  "original_html": "...",
  "edited_html": "...",
  "created_at": "...",
  "updated_at": "..."
}
```

---

### List All Documents

```
GET /api/documents
```

---

### Get Single Document

```
GET /api/documents/{id}
```

---

### Update Edited HTML

```
PUT /api/documents/{id}
```

Body:

```json
{
  "edited_html": "<h1>Updated</h1>"
}
```

---

## How PDF Conversion Works

1. PDF is converted into images using `pdf2image`
2. Each page is sent to Gemini with a structured prompt
3. Gemini returns semantic HTML:

   * headers
   * tables
   * lists
   * layout-preserving divs
4. Pages are wrapped like:

```html
<div class="pdf-content">
  <div class="page" data-page="1">
    ...
  </div>
</div>
```

---

## Token & Progress Tracking

The system is designed to support:

* Per-page token tracking
* Total token usage
* Processing status:

  * `processing`
  * `completed`
  * `failed`

(Ready for future async/background workers.)

---

## Notes

* This uses **Gemini Vision**, not basic text extraction.
* Layout accuracy is much higher than `pdfplumber`.
* No authentication (open API).
* For production:

  * Add auth (JWT / OAuth)
  * Add file size limits
  * Run PDF conversion in background queue (Celery / RQ)
  * Store images in S3 / GCS

---

## Stop Application

```bash
docker-compose down
```

Remove volumes:

```bash
docker-compose down -v
```

---

## Future Enhancements

* Async processing with progress polling
* Page-wise streaming
* HTML diff viewer
* OCR fallback for scanned PDFs
* Export to DOCX / Markdown
