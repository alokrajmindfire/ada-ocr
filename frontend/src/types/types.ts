export interface PdfDocument {
  id: number;
  filename: string;
  status: string;
  original_html: string;
  edited_html: string | null;
  created_at: string;
  updated_at: string;
}

export interface PaginatedDocuments {
  items: PdfDocument[];
  total: number;
  page: number;
  page_size: number;
}
