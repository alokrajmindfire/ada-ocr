import { useState, useEffect } from 'react';
import type { PdfDocument } from './types/types';
import { UploadPdf } from './components/UploadPdf';
import { DocumentList } from './components/DocumentList';
import { HtmlEditor } from './components/HtmlEditor';
import { Toaster } from "./components/ui/sonner"

const API_BASE = 'http://localhost:8000';

function App() {
  const [documents, setDocuments] = useState<PdfDocument[]>([]);
  const [selectedDocument, setSelectedDocument] = useState<PdfDocument | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/documents`);
      if (!res.ok) throw new Error('Failed to fetch documents');
      const data: PdfDocument[] = await res.json();
      setDocuments(data);
    } catch (err) {
      console.error('Error fetching documents:', err);
    } finally {
      setLoading(false);
    }
  };


  const fetchDocumentById = async (id: number) => {
    const res = await fetch(`${API_BASE}/api/documents/${id}`);
    if (!res.ok) throw new Error('Failed to fetch document');
    return (await res.json()) as PdfDocument;
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleUploadSuccess = async () => {
    await fetchDocuments();
  };

  const handleSaveSuccess = async () => {
    if (!selectedDocument) return;

    // refresh selected document after save
    const updatedDoc = await fetchDocumentById(selectedDocument.id);
    setSelectedDocument(updatedDoc);
    await fetchDocuments();
  };

  const handleSelectDocument = async (doc: PdfDocument) => {
    // always load fresh data from backend
    const freshDoc = await fetchDocumentById(doc.id);
    setSelectedDocument(freshDoc);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        Loading...
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold mb-4">PDF to HTML Converter</h1>
        <UploadPdf onUploadSuccess={handleUploadSuccess} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1">
          <DocumentList
            documents={documents}
            onSelectDocument={handleSelectDocument}
            selectedDocId={selectedDocument?.id}
          />
        </div>

        <div className="md:col-span-2">
          {selectedDocument ? (
            <HtmlEditor
              document={selectedDocument}
              onSaveSuccess={handleSaveSuccess}
            />
          ) : (
            <div className="flex items-center justify-center h-64 border rounded-md bg-muted/10">
              <p className="text-muted-foreground">
                Select a document to edit
              </p>
            </div>
          )}
        </div>
      </div>

      <Toaster />
    </div>
  );
}

export default App;
