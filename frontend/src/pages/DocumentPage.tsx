import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import type { PdfDocument } from '@/types/types';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

const API_BASE = 'http://localhost:8000';

const DocumentPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [document, setDocument] = useState<PdfDocument | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;

    const fetchDocument = async () => {
      try {
        const res = await fetch(`${API_BASE}/api/documents/${id}`);
        if (!res.ok) throw new Error('Failed to fetch document');
        const data: PdfDocument = await res.json();
        setDocument(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchDocument();
  }, [id]);

  if (loading) {
    return <div className="p-6">Loading document...</div>;
  }

  if (!document) {
    return <div className="p-6">Document not found</div>;
  }

  return (
    <div className="min-h-screen bg-muted/20 p-6">
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => navigate(-1)}
          className="flex items-center gap-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to documents
        </Button>
      </div>

      {/* Content Card */}
      <Card className="p-6">
        <div className="border-b pb-4 mb-6">
          <h1 className="text-xl font-semibold">{document.filename}</h1>
          <p className="text-sm text-muted-foreground">
            Uploaded on {new Date(document.created_at).toLocaleDateString()}
          </p>
        </div>

        {/* HTML Content */}
        <div
          className="prose prose-neutral max-w-none overflow-x-auto"
          dangerouslySetInnerHTML={{
            __html: document.edited_html || document.original_html,
          }}
        />
      </Card>
    </div>
  );
};

export default DocumentPage;
