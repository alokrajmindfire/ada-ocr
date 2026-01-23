# PDF to HTML Converter

A minimal web application that converts PDF files to HTML, stores them in a database, and allows users to edit the converted HTML.

## Features

- Upload PDF files
- Automatic PDF to HTML conversion using Python (pdfplumber)
- Store original and edited HTML in Supabase database
- Edit HTML in a text editor
- Preview both original and edited HTML
- Minimal, functional design

## Tech Stack

### Frontend
- React with TypeScript
- Tailwind CSS
- shadcn/ui components
- Vite

### Backend
- Python FastAPI
- pdfplumber for PDF extraction
- httpx for API calls

### Database
- Supabase (PostgreSQL)

### Infrastructure
- Docker & Docker Compose

## Setup Instructions

### Prerequisites
- Docker and Docker Compose installed
- Supabase account (free tier)

### 1. Get Supabase Credentials

1. Go to [supabase.com](https://supabase.com) and create a project
2. Go to Settings > API
3. Copy your Project URL and anon/public key

### 2. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
VITE_SUPABASE_URL=your_supabase_project_url
VITE_SUPABASE_ANON_KEY=your_supabase_anon_key
```

Create a `.env` file in the `backend` directory:

```bash
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

### 3. Database Setup

The database table is automatically created via the Supabase migration. If you need to create it manually, run this SQL in your Supabase SQL editor:

```sql
CREATE TABLE IF NOT EXISTS pdf_documents (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  filename text NOT NULL,
  original_html text NOT NULL,
  edited_html text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE pdf_documents ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access"
  ON pdf_documents FOR SELECT TO anon, authenticated USING (true);

CREATE POLICY "Allow public insert access"
  ON pdf_documents FOR INSERT TO anon, authenticated WITH CHECK (true);

CREATE POLICY "Allow public update access"
  ON pdf_documents FOR UPDATE TO anon, authenticated USING (true) WITH CHECK (true);
```

### 4. Run with Docker Compose

```bash
docker-compose up --build
```

The application will be available at:
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 5. Development Setup (without Docker)

#### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python main.py
```

#### Frontend Setup

```bash
npm install
npm run dev
```

## Usage

1. Open the application in your browser
2. Click "Upload PDF" and select a PDF file
3. The PDF will be automatically converted to HTML
4. Select the document from the list on the left
5. Edit the HTML in the editor
6. Switch between "Edit HTML", "Preview", and "Original" tabs
7. Click "Save Changes" to save your edits

## API Endpoints

### Backend API

- `POST /api/upload-pdf` - Upload and convert PDF file
  - Body: multipart/form-data with file
  - Returns: Created document object

- `GET /health` - Health check endpoint

## Database Schema

### pdf_documents Table

| Column | Type | Description |
|--------|------|-------------|
| id | uuid | Primary key |
| filename | text | Original PDF filename |
| original_html | text | Converted HTML from PDF |
| edited_html | text | User-edited HTML |
| created_at | timestamptz | Creation timestamp |
| updated_at | timestamptz | Last update timestamp |

## Notes

- This is a minimal implementation focused on functionality
- PDF conversion is basic and preserves text content
- For better PDF to HTML conversion, consider using libraries like pdf2htmlEX or implementing more sophisticated parsing
- For production use, add proper authentication and authorization
- Consider adding file size limits and virus scanning for uploads

## Stopping the Application

```bash
docker-compose down
```

To remove volumes:

```bash
docker-compose down -v
```
