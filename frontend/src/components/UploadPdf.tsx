import { useState } from 'react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Upload } from 'lucide-react';
import { toast } from "sonner";

interface UploadPdfProps {
  onUploadSuccess: () => void;
}

export function UploadPdf({ onUploadSuccess }: UploadPdfProps) {
  const [uploading, setUploading] = useState(false);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.endsWith('.pdf')) {
      toast('Please upload a PDF file');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
      const response = await fetch(`${backendUrl}/api/upload-pdf`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      toast('PDF uploaded and converted successfully');

      onUploadSuccess();
      e.target.value = '';
    } catch (error) {
      toast('Failed to upload PDF');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex items-center gap-4">
      <Input
        type="file"
        accept=".pdf"
        onChange={handleFileUpload}
        disabled={uploading}
        className="max-w-xs"
      />
      <Button disabled={uploading}>
        <Upload className="mr-2 h-4 w-4" />
        {uploading ? 'Uploading...' : 'Upload PDF'}
      </Button>
    </div>
  );
}
