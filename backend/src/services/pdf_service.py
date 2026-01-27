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
4. Ensure text alignment is preserved:
   - Left, right, center, or justified alignment of paragraphs, headings, and table content must reflect the PDF.
   - Maintain alignment consistency within sections and tables.
5. Use appropriate HTML5 semantic tags (header, nav, main, section, article, aside, footer).
6. Add meaningful CSS classes for styling (use Tailwind-like utility names, e.g., text-left, text-center, text-right, text-justify, mt-4, mb-2).
7. Preserve text hierarchy (h1–h6, p, blockquote, etc.).
8. For tables:
   - Use <table>, <thead>, <tbody>, <th>, <td>
   - Add scope attributes for headers.
   - Ensure logical reading order.
   - Preserve cell alignment.
9. For images:
   - Only if an actual image, chart, or diagram is present in the PDF.
   - DO NOT embed real images.
   - Instead, insert <figure> with a detailed textual description.
   - Use <figcaption> and alt-like descriptive text explaining what the image conveys.
   - If no image exists, do NOT generate <figure>.

ADA / WCAG Compliance (Mandatory):
10. Ensure the HTML is accessible:
    - Proper heading hierarchy (no skipped levels).
    - Use ARIA roles only when semantic HTML is insufficient.
    - Add aria-label / aria-labelledby where needed.
    - Ensure all interactive elements are keyboard accessible.
    - No visual-only meaning; everything must be understandable via screen reader.
11. Provide descriptive text only for:
    - Actual charts, diagrams, icons, and infographics present in the PDF.
    - Actual visual cues (colors, arrows, highlights) if they exist.
12. Use:
    - <main> for main content.
    - <nav> for navigation blocks.
    - <section> for logical grouping.
    - <article> for independent content.
13. Reading order must match visual order (top-to-bottom, left-to-right).

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
- Use CSS classes to indicate alignment where appropriate.
"""

def process_pdf(pdf_bytes, doc, db):
    start_time = time.time()
    logger.info(f"Starting PDF processing for doc_id={doc.id}")

    images = convert_from_bytes(pdf_bytes, dpi=300)
    total_pages = len(images)
    logger.info(f"PDF converted into {total_pages} images")

    doc.total_pages = total_pages
    db.commit()

    html_pages = ['<div class="pdf-content">']
    tokens_per_page = {}
    total_tokens = 0

    for page_num, image in enumerate(images, 1):
        logger.info(f"Processing page {page_num}/{total_pages}")

        page_html, usage = llm.generate_html(
            PROMPT.format(page_num=page_num),
            image
        )

        tokens_per_page[str(page_num)] = usage
        total_tokens += usage["total_tokens"]

        html_pages.append(page_html)

        doc.processed_pages = page_num
        doc.tokens_per_page = tokens_per_page
        doc.total_tokens = total_tokens
        db.commit()

        logger.info(
            f"Page {page_num} done | total_tokens={total_tokens}"
        )

    html_pages.append("</div>")

    duration = round(time.time() - start_time, 2)
    logger.info(
        f"Finished PDF processing for doc_id={doc.id} in {duration}s"
    )

    return "\n".join(html_pages)
