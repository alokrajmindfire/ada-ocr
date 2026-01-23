import { useState, useEffect } from 'react';
import { Save } from 'lucide-react';
import type { PdfDocument } from '../types/types';
import { toast } from "sonner";
import {
  Editor,
  EditorProvider,
  Toolbar,
  BtnBold,
  BtnItalic,
  BtnUnderline,
  BtnStrikeThrough,
  BtnBulletList,
  BtnNumberedList,
  BtnLink,
  BtnClearFormatting,
  BtnUndo,
  BtnRedo,
} from 'react-simple-wysiwyg';

interface HtmlEditorProps {
  document: PdfDocument;
  onSaveSuccess: () => void;
}

export function HtmlEditor({ document, onSaveSuccess }: HtmlEditorProps) {
  const [content, setContent] = useState(
    document.edited_html || document.original_html
  );
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setContent(document.edited_html || document.original_html);
  }, [document]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await fetch(
        `http://localhost:8000/api/documents/${document.id}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ edited_html: content }),
        }
      );
      if (!res.ok) throw new Error();
      toast('Changes saved successfully');
      onSaveSuccess();
    } catch {
      toast('Failed to save changes');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="border-b p-4 bg-white flex justify-between items-center">
        <h2 className="text-lg font-semibold">{document.filename}</h2>
        <button
          onClick={handleSave}
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded"
        >
          <Save className="h-4 w-4" />
          {saving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-hidden">
        <EditorProvider>
          <Toolbar>
            <BtnBold />
            <BtnItalic />
            <BtnUnderline />
            <BtnStrikeThrough />
            <BtnBulletList />
            <BtnNumberedList />
            <BtnLink />
            <BtnUndo />
            <BtnRedo />
            <BtnClearFormatting />
          </Toolbar>

          <Editor
            value={content}
            onChange={(e) => setContent(e.target.value)}
            className="h-full"
          />
        </EditorProvider>
      </div>
    </div>
  );
}
