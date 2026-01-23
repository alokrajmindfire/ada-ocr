import { type PdfDocument } from './../types/types';
import { Card } from './../components/ui/card';
import { FileText } from 'lucide-react';

interface DocumentListProps {
  documents: PdfDocument[];
  onSelectDocument: (doc: PdfDocument) => void;
  selectedDocId?: number;
}

export function DocumentList({ documents, onSelectDocument, selectedDocId }: DocumentListProps) {
  return (
    <div className="space-y-2">
      <h2 className="text-lg font-semibold mb-4">Documents</h2>
      {documents.length === 0 ? (
        <p className="text-muted-foreground">No documents uploaded yet</p>
      ) : (
        documents.map((doc) => (
          <Card
            key={doc.id}
            className={`p-4 cursor-pointer hover:bg-accent transition-colors ${
              selectedDocId === doc.id ? 'bg-accent' : ''
            }`}
            onClick={() => onSelectDocument(doc)}
          >
            <div className="flex items-center gap-3">
              <FileText className="h-5 w-5" />
              <div className="flex-1 min-w-0">
                <p className="font-medium truncate">{doc.filename}</p>
                <p className="text-sm text-muted-foreground">
                  {new Date(doc.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
          </Card>
        ))
      )}
    </div>
  );
}
