from pdf2image import convert_from_bytes
from io import BytesIO
import time
from repositories.pdf_repository import PDFRepository
from services.llm_factory import get_llm
from config.logger import get_logger
import fitz  
from bs4 import BeautifulSoup
import re
from difflib import SequenceMatcher
import json
from pypdf import PdfReader, PdfWriter
from io import BytesIO

logger = get_logger("pdf_service")

llm = get_llm()

def extract_pdf_links_with_positions(pdf_bytes: bytes):
    """
    Extract links from PDF with detailed position information.
    
    Returns:
    {
      page_number: [
        {
          "uri": "https://example.com",
          "rect": {
            "x0": float,
            "y0": float,
            "x1": float,
            "y1": float
          },
          "text": "Read More",
          "center_x": float,
          "center_y": float
        }
      ]
    }
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_links = {}

        for page_index, page in enumerate(doc):
            links = []
            page_height = page.rect.height
            page_width = page.rect.width
            
            for link in page.get_links():
                if link.get("uri"):
                    rect = fitz.Rect(link["from"])
                    text = page.get_textbox(rect).strip()
                    
                    # Calculate center point for easier matching
                    center_x = (rect.x0 + rect.x1) / 2
                    center_y = (rect.y0 + rect.y1) / 2
                    
                    links.append({
                        "uri": link["uri"],
                        "rect": {
                            "x0": rect.x0,
                            "y0": rect.y0,
                            "x1": rect.x1,
                            "y1": rect.y1
                        },
                        "text": text,
                        "center_x": center_x,
                        "center_y": center_y,
                        "page_width": page_width,
                        "page_height": page_height
                    })
            
            if links:
                page_links[page_index + 1] = links
                logger.info(f"Page {page_index + 1}: Extracted {len(links)} links with positions")

        return page_links
    except Exception as e:
        logger.error(f"Error extracting links from PDF: {e}")
        return {}


def normalize_text(text):
    """Normalize text for comparison by removing extra whitespace and lowercasing"""
    return re.sub(r'\s+', ' ', text.strip().lower())


def text_similarity(text1, text2):
    """Calculate similarity ratio between two texts"""
    return SequenceMatcher(None, normalize_text(text1), normalize_text(text2)).ratio()


def calculate_position_overlap(link_rect, html_bbox):
    """
    Calculate overlap ratio between PDF link rectangle and HTML element bounding box.
    
    Args:
        link_rect: dict with x0, y0, x1, y1 (PDF coordinates)
        html_bbox: dict with x, y, width, height (normalized 0-1 coordinates from LLM)
    
    Returns:
        float: overlap ratio (0.0 to 1.0)
    """
    # Convert HTML bbox to same format as link_rect
    # Assuming html_bbox is in normalized coordinates (0-1)
    html_x0 = html_bbox.get('x', 0)
    html_y0 = html_bbox.get('y', 0)
    html_x1 = html_x0 + html_bbox.get('width', 0)
    html_y1 = html_y0 + html_bbox.get('height', 0)
    
    # Calculate intersection
    x_overlap = max(0, min(link_rect['x1'], html_x1) - max(link_rect['x0'], html_x0))
    y_overlap = max(0, min(link_rect['y1'], html_y1) - max(link_rect['y0'], html_y0))
    
    intersection_area = x_overlap * y_overlap
    
    # Calculate areas
    link_area = (link_rect['x1'] - link_rect['x0']) * (link_rect['y1'] - link_rect['y0'])
    html_area = html_bbox.get('width', 0) * html_bbox.get('height', 0)
    
    if link_area == 0 or html_area == 0:
        return 0.0
    
    # Return intersection over minimum area (IoU variant)
    return intersection_area / min(link_area, html_area)


def fix_placeholder_links_with_positions(html: str, pdf_links: dict, link_positions: dict = None):
    """
    Fix placeholder links in HTML using position-based matching.
    
    Args:
        html: HTML string to process
        pdf_links: Links extracted from PDF with positions
        link_positions: Optional - position data from LLM for each link
    
    Returns:
        Fixed HTML string
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
        pages = soup.select("div.page")
        
        total_links_fixed = 0
        total_anchors_processed = 0

        for page_div in pages:
            page_num = int(page_div.get("data-page", "0"))
            
            if page_num not in pdf_links:
                logger.debug(f"No PDF links found for page {page_num}")
                continue

            page_link_data = pdf_links[page_num].copy()
            logger.info(f"Processing page {page_num} with {len(page_link_data)} PDF links")

            # Track which PDF links have been used
            used_link_indices = set()

            # Find all anchors on this page
            anchors = page_div.find_all("a", href=True)
            logger.info(f"Found {len(anchors)} anchor tags on page {page_num}")
            
            # Sort PDF links by position (top to bottom, left to right)
            sorted_pdf_links = sorted(
                enumerate(page_link_data),
                key=lambda x: (x[1]['center_y'], x[1]['center_x'])
            )
            
            for idx, a in enumerate(anchors):
                total_anchors_processed += 1
                href = a["href"].strip()
                anchor_text = a.get_text(strip=True)
                anchor_text_normalized = normalize_text(anchor_text)
                
                # Get position data if available
                anchor_position = None
                if link_positions and page_num in link_positions:
                    anchor_position = link_positions[page_num].get(idx)
                
                logger.debug(f"Anchor {idx + 1}: href='{href}', text='{anchor_text}'")
                
                # Only process placeholder links (href="#")
                if href != "#":
                    logger.debug(f"  Skipping - href is not '#': {href}")
                    continue

                matched_url = None
                matched_link_idx = None
                best_match_score = 0
                best_match_link = None
                best_match_idx = None
                best_match_method = None

                # Try different matching strategies in order of reliability
                for link_idx, link in sorted_pdf_links:
                    if link_idx in used_link_indices:
                        continue
                    
                    link_text = link["text"]
                    link_text_normalized = normalize_text(link_text)
                    
                    # Strategy 1: Position-based matching (if position data available)
                    if anchor_position:
                        position_overlap = calculate_position_overlap(link["rect"], anchor_position)
                        if position_overlap > 0.7:  # 70% overlap threshold
                            text_sim = text_similarity(anchor_text, link_text)
                            combined_score = position_overlap * 0.7 + text_sim * 0.3
                            
                            if combined_score > best_match_score:
                                best_match_score = combined_score
                                best_match_link = link
                                best_match_idx = link_idx
                                best_match_method = f"position+text({position_overlap:.2f}+{text_sim:.2f})"
                                
                                # If very high confidence, break early
                                if combined_score > 0.9:
                                    matched_url = link["uri"]
                                    matched_link_idx = link_idx
                                    logger.info(f"  ✓ Position match: '{anchor_text}' -> {matched_url} (score: {combined_score:.2f})")
                                    break
                    
                    # Strategy 2: Exact text match
                    if anchor_text_normalized and anchor_text_normalized == link_text_normalized:
                        text_sim = 1.0
                        if text_sim > best_match_score:
                            best_match_score = text_sim
                            best_match_link = link
                            best_match_idx = link_idx
                            best_match_method = "exact_text"
                            
                            # Exact match is very reliable
                            if not anchor_position:
                                matched_url = link["uri"]
                                matched_link_idx = link_idx
                                logger.info(f"  ✓ Exact text match: '{anchor_text}' -> {matched_url}")
                                break
                    
                    # Strategy 3: Substring matching
                    if anchor_text_normalized and link_text_normalized:
                        if anchor_text_normalized in link_text_normalized or link_text_normalized in anchor_text_normalized:
                            text_sim = text_similarity(anchor_text, link_text)
                            if text_sim > best_match_score and text_sim > 0.6:
                                best_match_score = text_sim
                                best_match_link = link
                                best_match_idx = link_idx
                                best_match_method = f"substring({text_sim:.2f})"
                    
                    # Strategy 4: Fuzzy text similarity
                    text_sim = text_similarity(anchor_text, link_text)
                    if text_sim > 0.6 and text_sim > best_match_score:
                        best_match_score = text_sim
                        best_match_link = link
                        best_match_idx = link_idx
                        best_match_method = f"fuzzy({text_sim:.2f})"

                # Use best match if no definitive match found
                if not matched_url and best_match_link and best_match_score > 0.5:
                    matched_url = best_match_link["uri"]
                    matched_link_idx = best_match_idx
                    logger.info(f"  ✓ Best match ({best_match_method}): '{anchor_text}' -> {matched_url} (score: {best_match_score:.2f})")

                if matched_url:
                    a["href"] = matched_url
                    if matched_link_idx is not None:
                        used_link_indices.add(matched_link_idx)
                    total_links_fixed += 1
                else:
                    # No reliable match found - convert to span
                    logger.warning(f"  ✗ No match found for: '{anchor_text}' - converting to span")
                    
                    span = soup.new_tag("span")
                    span.string = a.get_text()
                    span["class"] = a.get("class", []) + ["link-unresolved"]
                    span["aria-label"] = "Link destination not available in source PDF"
                    a.replace_with(span)

        logger.info(f"Link fixing complete: {total_links_fixed}/{total_anchors_processed} anchors fixed")
        return str(soup)
        
    except Exception as e:
        logger.error(f"Error fixing placeholder links: {e}", exc_info=True)
        return html
    
def extract_link_positions_from_html(html: str):
    """
    Extract position data from data-position attributes in HTML.
    
    Returns:
    {
      page_number: {
        anchor_index: {
          "x": float,
          "y": float,
          "width": float,
          "height": float
        }
      }
    }
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
        pages = soup.select("div.page")
        
        link_positions = {}
        
        for page_div in pages:
            page_num = int(page_div.get("data-page", "0"))
            anchors = page_div.find_all("a", href=True)
            
            page_positions = {}
            
            for idx, a in enumerate(anchors):
                position_str = a.get("data-position")
                if position_str:
                    try:
                        position_data = json.loads(position_str)
                        page_positions[idx] = position_data
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid position data for anchor {idx} on page {page_num}: {position_str}")
            
            if page_positions:
                link_positions[page_num] = page_positions
                logger.info(f"Extracted position data for {len(page_positions)} links on page {page_num}")
        
        return link_positions
        
    except Exception as e:
        logger.error(f"Error extracting link positions: {e}")
        return {}

def contains_placeholder_links(html: str) -> bool:
    """
    Check if the HTML contains any anchor tags with href='#'.
    
    Args:
        html: HTML string to check
        
    Returns:
        bool: True if at least one anchor with href='#' exists, False otherwise
    """
    try:
        soup = BeautifulSoup(html, "html.parser")
        placeholder_anchors = soup.find_all("a", href="#")
        return len(placeholder_anchors) > 0
    except Exception as e:
        logger.error(f"Error checking for placeholder links: {e}")
        return False

PROMPT = """
Analyze this PDF page image (Page {page_num}) and convert it to clean, semantic, fully ADA-compliant, and WCAG 2.1 AA-ready HTML.

Goal:
This output will be used in an **accessibility-first document reader**. 
All content must be screen-reader friendly, maintain correct reading order, and prioritize accessibility over visual fidelity. 
Ensure compliance with ADA and WCAG 2.1 AA standards.  

Core Requirements:
1. Preserve the visual layout and design as closely as possible, prioritizing **semantic structure and accessibility** over pixel-perfect accuracy.
2. Correctly structure headers, paragraphs, lists, tables, figures, sections, and navigation links.
3. Maintain relative fonts, font sizes, spacing, vertical spacing between lines, alignment, and reading order.
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
    - Try to mimic the exact spacing as closely as possible using margin and padding utility classes (e.g., mt-4, mb-2, leading-tight, leading-relaxed).
    - Try to retain the alignment of text as in the PDF.

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
IMPORTANT: For images or any coloured divs, try to retain the space occupied by the image and try to retain and have a background colour similar to the image background where text description of images are shown. Try to retain colour of the divs.

23. Provide descriptive text ONLY for:
    - Actual charts, diagrams, icons, infographics.
    - Actual visual cues (colors, arrows, highlights) if present.
    - try to retain the space occupied by the image and try to retain and have a background colour similar to the chart background where text description of images are shown

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
33. For multiple page PDFs, wrap each page in a container and provide boundary separation border between pages.

Extracting All Links (Navigation, Buttons, Inline Links) (Critical):
33. Include links inside their logical content flow.
34. Detect all clickable links in the page, including:
    - Use <a href="URL">link text</a>.
    - Maintain link text as shown in PDF.
    - Navigation menus and section links
    - Buttons that act as links (e.g., 'View All News', 'Read More')
    - Any inline links within text or content blocks
35. **Important** - Preserve links in clckable graphical elements like logs, Buttons, etc

Links (CRITICAL - POSITION TRACKING):
36. **MANDATORY**: Preserve ALL links from the PDF exactly as they appear.
37. For every clickable text or button in the PDF, create an anchor tag with:
    - The EXACT link text visible in the PDF as the anchor text
    - href="#" as a placeholder (this will be fixed by post-processing)
    - A data-position attribute with normalized coordinates (0-1 range):
      data-position='{"x": 0.15, "y": 0.32, "width": 0.10, "height": 0.02}'
      where:
      - x: horizontal position (0=left, 1=right) of left edge
      - y: vertical position (0=top, 1=bottom) of top edge  
      - width: width as fraction of page width
      - height: height as fraction of page height
    - Example: <a href="#" data-position='{"x": 0.15, "y": 0.32, "width": 0.10, "height": 0.02}'>Read More</a>
38. DO NOT omit links. If you see clickable text like "Read More", "View All", phone numbers, email addresses, or any underlined/colored text that appears to be a link, you MUST include it as an anchor tag with href="#" and position data.
39. The link text in your HTML must match the PDF link text as closely as possible for automated link fixing to work.
40. Position coordinates should be as accurate as possible based on the visual layout of the page.


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
- Do NOT wrap the entire documents inside ```html... ``` .
- **CRITICAL**: Include ALL links as <a href="#" data-position='...'>link text</a> - they will be fixed automatically using position matching.
"""



def extract_pdf_page_range(
    pdf_bytes: bytes,
    start_page: int,
    end_page: int,
) -> bytes:
    """
    start_page / end_page are 1-based and inclusive
    """
    reader = PdfReader(BytesIO(pdf_bytes))
    writer = PdfWriter()

    for i in range(start_page - 1, end_page):
        writer.add_page(reader.pages[i])

    output = BytesIO()
    writer.write(output)
    return output.getvalue()

def page_ranges(total_pages: int, chunk_size: int = 5):
    for start in range(1, total_pages + 1, chunk_size):
        end = min(start + chunk_size - 1, total_pages)
        yield start, end
def process_pdf(pdf_bytes: bytes, doc, db, chunk_size: int = 5):
    start_time = time.time()
    logger.info(f"[PDF:{doc.id}] Starting PDF-native chunked processing")

    reader = PdfReader(BytesIO(pdf_bytes))
    total_pages = len(reader.pages)

    doc.total_pages = total_pages
    doc.processed_pages = 0
    db.commit()

    full_html = []
    tokens_per_page = {}
    total_tokens = 0

    for start_page, end_page in page_ranges(total_pages, chunk_size):
        logger.info(
            f"[PDF:{doc.id}] Processing pages {start_page}–{end_page}"
        )

        chunk_pdf_bytes = extract_pdf_page_range(
            pdf_bytes,
            start_page,
            end_page
        )

        html_chunk, usage = llm.generate_html_from_pdf(
            prompt=PROMPT,
            pdf_bytes=chunk_pdf_bytes,
            # start_page=start_page,   # IMPORTANT
            # end_page=end_page
        )

        # Optional: Fix placeholder links per chunk
        if contains_placeholder_links(html_chunk):
            logger.info(f"[PDF:{doc.id}] Fixing placeholder links")
            pdf_links = extract_pdf_links_with_positions(pdf_bytes)
            link_positions = extract_link_positions_from_html(html_chunk)
            html_chunk = fix_placeholder_links_with_positions(
                html_chunk,
                pdf_links,
                link_positions
            )

        # Token accounting
        chunk_tokens = usage.get("tokens_per_page", {})
        for page, tokens in chunk_tokens.items():
            tokens_per_page[str(page)] = tokens
            total_tokens += tokens

        # Update progress
        pages_done = end_page - start_page + 1
        doc.processed_pages += pages_done
        doc.tokens_per_page = tokens_per_page
        doc.total_tokens = total_tokens
        db.commit()

        full_html.append(html_chunk)

    duration = round(time.time() - start_time, 2)
    logger.info(f"[PDF:{doc.id}] Finished in {duration}s")

    return f'<div class="pdf-content">\n{"".join(full_html)}\n</div>'
