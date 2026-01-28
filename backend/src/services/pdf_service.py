from pdf2image import convert_from_bytes
from io import BytesIO
import time
from repositories.pdf_repository import PDFRepository
from services.llm_factory import get_llm
from config.logger import get_logger

logger = get_logger("pdf_service")

llm = get_llm()


PROMPT = """
Analyze this PDF page image (Page {page_num}) and convert it to clean, semantic, and fully ADA-compliant HTML.

Goal:
This output will be used in an accessibility-first document reader similar to the DocAccess app.

Core Requirements:
1. Preserve the visual layout and design as closely as possible, while prioritizing correct structure over pixel-perfect accuracy.
2. Identify and correctly structure headers, paragraphs, lists, tables, figures, and sections.
3. Maintain relative font sizes, spacing, alignment, and reading order.

Multi-Column Layout (Critical):
4. Detect if the page uses multiple columns (two, three, etc.).
5. If multi-column:
   - Use a grid-based layout for columns.
   - Wrap all columns inside a grid container:
     <div class="columns grid grid-cols-2 gap-6"> or
     <div class="columns grid grid-cols-3 gap-6">
   - Each column must be explicitly represented as:
     <div class="column col-span-1 column-1">,
     <div class="column col-span-1 column-2">, etc.
6. Reading order MUST follow:
   - Top-to-bottom within column 1,
   - then top-to-bottom within column 2,
   - then subsequent columns.
7. Do NOT interleave text from different columns.
8. Preserve column-specific alignment, spacing, and structure.
9. Content must remain in DOM order matching the visual grid order.

Text Alignment:
10. Ensure text alignment is preserved:
    - Left, right, center, or justified alignment of paragraphs, headings, and table content must reflect the PDF.
    - Use alignment utility classes:
      text-left, text-center, text-right, text-justify
    - Maintain alignment consistency within each column.

Semantic HTML:
11. Use appropriate HTML5 semantic tags (header, nav, main, section, article, aside, footer).
12. Add meaningful CSS utility classes (Tailwind-like):
    - grid, grid-cols-*, gap-*
    - mt-4, mb-2, leading-tight, leading-relaxed
13. Preserve text hierarchy (h1–h6, p, blockquote, etc.).

Tables:
14. For tables:
    - Use <table>, <thead>, <tbody>, <th>, <td>
    - Add scope attributes for headers.
    - Ensure logical reading order.
    - Preserve cell alignment.
    - Tables must stay within their grid column unless they visually span all columns.
    - If spanning all columns, place table outside the grid container.

Images (Critical – Text-Only Representation):
15. Detect actual images, charts, diagrams, icons, or visual graphics present in the PDF.
16. Do NOT embed, reference, or simulate real images.
17. Do NOT use <figure>, <figcaption>, <img>, or any image-related HTML tags.
18. At the exact visual position where the image appears, insert a plain semantic block:

    <p class="image-description">
        Image: [clear, detailed textual description of the visual content]
    </p>

19. The description must explain the visual meaning, data, or purpose of the image in a screen-reader-friendly way.
20. If the image is decorative and conveys no information, write:
    Image: Decorative image with no informational content.
21. If no image exists on the page, do NOT generate any image description.


ADA / WCAG Compliance (Mandatory):
22. Ensure the HTML is accessible:
    - Proper heading hierarchy (no skipped levels).
    - Use ARIA roles only when semantic HTML is insufficient.
    - Add aria-label / aria-labelledby where needed.
    - Ensure all interactive elements are keyboard accessible.
    - No visual-only meaning; everything must be screen-reader friendly.
23. Provide descriptive text ONLY for:
    - Actual charts, diagrams, icons, and infographics present.
    - Actual visual cues (colors, arrows, highlights) if they exist.

Structural Rules:
24. Use:
    - <main> for main content.
    - <nav> for navigation blocks.
    - <section> for logical grouping.
    - <article> for independent content.
25. Reading order must match visual order (top-to-bottom, left-to-right by grid column).
Links:
26. If you find any links in the pdf , put the link text in anchor tag text and link in href of anchor tag in HTML.
Output Format:
Return ONLY the HTML code for this page content, wrapped in:

<div class="page" data-page="{page_num}">
    <!-- page content here -->
</div>

Rules:
- Do NOT include <!DOCTYPE>, <html>, <head>, or <body>.
- Do NOT include markdown.
- No explanations, no commentary.
- Do NOT hallucinate content that is not present.
- The HTML must be ready for screen readers like NVDA, JAWS, VoiceOver.
- The result should pass WCAG 2.1 AA standards.
- Use CSS classes to indicate alignment and grid-based column layout.
"""



def process_pdf(pdf_bytes: bytes, doc, db):
    start_time = time.time()
    logger.info(f"Starting PDF processing for doc_id={doc.id}")

    html, usage = llm.generate_html_from_pdf(
        prompt=PROMPT,
        pdf_bytes=pdf_bytes
    )

    doc.total_pages = usage.get("pages", None)
    doc.processed_pages = doc.total_pages
    doc.tokens_per_page = usage.get("tokens_per_page", {})
    doc.total_tokens = usage.get("total_tokens", 0)

    db.commit()

    duration = round(time.time() - start_time, 2)
    logger.info(f"Finished PDF processing in {duration}s")

    return f'<div class="pdf-content">\n{html}\n</div>'
