export interface PdfDocument {
  id: number;
  filename: string;
  original_html: string;
  edited_html: string | null;
  created_at: string;
  updated_at: string;
}
