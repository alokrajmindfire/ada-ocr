from pdf2image import convert_from_bytes
from io import BytesIO
import time
from repositories.pdf_repository import PDFRepository
from services.llm_factory import get_llm
from config.logger import get_logger

logger = get_logger("pdf_service")

llm = get_llm()

PROMPT = """
Analyze this PDF page image (Page {page_num}) and convert it to clean, semantic, fully ADA-compliant, and WCAG 2.1 AA-ready HTML.

Goal:
This output will be used in an **accessibility-first document reader**. 
All content must be screen-reader friendly, maintain correct reading order, and prioritize accessibility over visual fidelity. 
Ensure compliance with ADA and WCAG 2.1 AA standards.  

Core Requirements:
1. Preserve the visual layout and design as closely as possible, prioritizing **semantic structure and accessibility** over pixel-perfect accuracy.
2. Correctly structure headers, paragraphs, lists, tables, figures, sections, and navigation links.
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
9. Content must remain in **DOM order matching the visual grid order**.

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

Images and Visual Content (Critical – Text-Only Representation):
15. Detect all images, charts, diagrams, icons, or visual graphics.
16. Do NOT embed, reference, or simulate real images.
17. Do NOT use <figure>, <figcaption>, <img>, or image tags.
18. At the exact visual position where the image appears, insert:

    <p class="image-description">
        Image: [clear, detailed textual description of the visual content]
    </p>

19. Describe the visual meaning, data, or purpose in a screen-reader-friendly way.
20. If decorative and conveys no information, write:
    Image: Decorative image with no informational content.
21. If no image exists on the page, do NOT generate any image description.

ADA / WCAG Compliance (Mandatory):
22. Ensure the HTML is accessible:
    - Proper heading hierarchy (no skipped levels).
    - Use ARIA roles only when semantic HTML is insufficient.
    - Add aria-label / aria-labelledby where needed.
    - Ensure all interactive elements are keyboard accessible.
    - No visual-only meaning; all meaning must be screen-reader accessible.
23. Provide descriptive text ONLY for:
    - Actual charts, diagrams, icons, infographics.
    - Actual visual cues (colors, arrows, highlights) if present.

Styling Rules:
24. Do NOT use any **positioning styles** that could break reading order or accessibility:
    - No position: fixed, absolute, sticky, or similar.
    - No visual-only styles that interfere with natural DOM flow.
25. Only use CSS classes for semantic alignment and spacing (e.g., mt-4, text-center, gap-6, grid-cols-*).

Structural Rules:
26. Use:
    - <main> for main content
    - <nav> for navigation links or menus
    - <section> for logical grouping
    - <article> for independent content
27. Reading order must match visual order (top-to-bottom, left-to-right by grid column).

Handling Complex Visual Layouts (e.g., News Carousel, Overlapping Cards):
28. Detect visual cards, carousel items, or grid-based content blocks that may overlap or be layered (like news cards with images and titles).
29. Reconstruct the content **into a clean grid or column layout**:
    - Each card/item should be a separate <article> inside the proper <section> or <div class="grid">.
    - Preserve **reading order**: top-to-bottom, left-to-right in visual order.
    - Avoid any visual overlapping; all content must be accessible and sequential in DOM.
30. Extract all text content, dates, headings, and links from each card:
    - Dates should be in <time datetime="YYYY-MM-DD"> format.
    - Headings in h2/h3 based on hierarchy.
31. If cards contain background images or icons, do NOT embed images:
    - Instead, insert <p class="image-description"> with a clear textual description of the visual content.
32. Ensure the reconstructed layout:
    - Uses **semantic HTML only**.
    - Is fully **screen-reader accessible**.
    - Does **not use overlapping, position-fixed, or absolute styling**.
    - Maintains the logical content order for keyboard navigation.

Extracting All Links (Navigation, Buttons, Inline Links) (Critical):
33. Include links inside their logical content flow.
34. Detect all clickable links in the page, including:
    - Use <a href="URL">link text</a>.
    - Maintain link text as shown in PDF.
    - Navigation menus and section links
    - Buttons that act as links (e.g., 'View All News', 'Read More')
    - Any inline links within text or content blocks
35. **Important** - Preserve links in clckable graphical elements like logs, Buttons, etc

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
- The HTML must be ready for **screen readers** like NVDA, JAWS, VoiceOver.
- The result should pass **WCAG 2.1 AA standards**.
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
