import { useEffect, useState } from 'react';
import { UploadPdf } from '@/components/UploadPdf';
import { DocumentTable } from '@/components/DocumentTable';
import type { PaginatedDocuments } from '@/types/types';

const API_BASE = 'http://localhost:8000';

export default function Home() {
  const [data, setData] = useState<PaginatedDocuments | null>(null);
  const [page, setPage] = useState(1);

  const fetchDocuments = async () => {
    try {
      const res = await fetch(
        `${API_BASE}/api/documents?page=${page}&page_size=5`
      );
      if (!res.ok) throw new Error('Failed to fetch documents');
      const json: PaginatedDocuments = await res.json();
      setData(json);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, [page]);

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">PDF to HTML Converter</h1>

      <UploadPdf onUploadSuccess={fetchDocuments} />

      <DocumentTable
        documents={data?.items ?? []}
        page={data?.page ?? 1}
        pageSize={data?.page_size ?? 10}
        total={data?.total ?? 0}
        onPageChange={setPage}
      />
    </div>
  );
}
