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
1. Preserve the exact visual layout and design as closely as possible.
2. Identify and correctly structure headers, paragraphs, lists, tables, figures, and sections.
3. Maintain font sizes, spacing, alignment, and reading order.
4. Use appropriate HTML5 semantic tags (header, nav, main, section, article, aside, footer).
5. Add meaningful CSS classes for styling (use Tailwind-like utility names).
6. Preserve text hierarchy (h1–h6, p, blockquote, etc.).
7. For tables:
   - Use <table>, <thead>, <tbody>, <th>, <td>
   - Add scope attributes for headers.
   - Ensure logical reading order.
8. For images:
   - DO NOT embed real images.
   - Instead, insert <figure> with a detailed textual description.
   - Use <figcaption> and alt-like descriptive text explaining what the image conveys.

ADA / WCAG Compliance (Mandatory):
9. Ensure the HTML is 100% accessible:
   - Proper heading hierarchy (no skipped levels).
   - Use ARIA roles only when semantic HTML is insufficient.
   - Add aria-label / aria-labelledby where needed.
   - Ensure all interactive elements are keyboard accessible.
   - No visual-only meaning; everything must be understandable via screen reader.
10. Provide descriptive text for:
    - Charts, diagrams, icons, and infographics.
    - Any visual cues (colors, arrows, highlights).
11. Use:
    - <main> for main content.
    - <nav> for navigation blocks.
    - <section> for logical grouping.
    - <article> for independent content.
12. Reading order must match visual order (top-to-bottom, left-to-right).

Output Format:
Return ONLY the HTML code for this page content, wrapped in:

<div class="page" data-page="{page_num}">
    <!-- page content here -->
</div>

Rules:
- Do NOT include <!DOCTYPE>, <html>, <head>, or <body>.
- Do NOT include markdown.
- No explanations, no commentary.
- The HTML must be ready for screen readers like NVDA, JAWS, VoiceOver.
- The result should pass WCAG 2.1 AA standards.
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

        page_html = llm.generate_html(
            PROMPT.format(page_num=page_num),
            image
        )

        tokens = len(page_html.split())
        tokens_per_page[page_num] = tokens
        total_tokens += tokens

        html_pages.append(page_html)

        doc.processed_pages = page_num
        doc.tokens_per_page = tokens_per_page
        doc.total_tokens = total_tokens
        db.commit()

        logger.info(
            f"Page {page_num} done | tokens={tokens} | total_tokens={total_tokens}"
        )

    html_pages.append("</div>")

    duration = round(time.time() - start_time, 2)
    logger.info(
        f"Finished PDF processing for doc_id={doc.id} in {duration}s"
    )

    return "\n".join(html_pages)
