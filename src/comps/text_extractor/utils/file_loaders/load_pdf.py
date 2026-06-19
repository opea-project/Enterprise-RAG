# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

# activate PyMuPDF-Layout in pymupdf
import pymupdf.layout
import pymupdf
import tabulate

import io
import nltk
import time
import os
import re
import multiprocessing
from typing import Any


import pymupdf4llm.helpers.document_layout as pymupdf4llm_dl
from docling.datamodel.base_models import DocumentStream, InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions, TableFormerMode

from docling.document_converter import DocumentConverter, PdfFormatOption, ImageFormatOption


from concurrent.futures import ProcessPoolExecutor, as_completed
from comps.text_extractor.utils.file_loaders.abstract_loader import AbstractLoader
from comps.text_extractor.utils.file_loaders.load_image import LoadImage
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


AVAILABLE_LANGUAGES = ["eng", "pol"]  # expects 3-letter ISO 639-2 code

# Maximum safe dimension in pixels at any DPI - prevents pymupdf OCR crashes on very tall/wide pages
# Set to 8000 based on practical pymupdf/tesseract limits (crashes occur around 10000px)
MAX_OCR_DIMENSION = 8000
# Minimum DPI for acceptable OCR quality - below this, text becomes too degraded for accurate recognition
# (industry standard for document scanning is 300 DPI; 150 is half, minimum for readable text)
MIN_QUALITY_DPI = 150
# Default OCR resolution - standard DPI for document processing that balances quality and performance
DEFAULT_OCR_DPI = 300
# Minimum DPI for pymupdf OCR - values below 70 trigger a warning and are automatically
# adjusted to 70 by the pdfocr_tobytes() function (enforced by tesseract OCR layer)
PYMUPDF_MIN_DPI = 70

# Pre-resolve the pymupdf4llm OCR function once to avoid repeated
# prints that the selection outputs.
_PYMUPDF_OCR_FUNCTION = pymupdf4llm_dl.select_ocr_function()
pymupdf4llm_dl.INFO_MESSAGES.truncate(0)
pymupdf4llm_dl.INFO_MESSAGES.seek(0)

# Markers added by pymupdf4llm for OCR text
PICTURE_TEXT_START_MARKER = "---- Start of picture text ----"
PICTURE_TEXT_END_MARKER = "---- End of picture text -----"

# Placeholder marker for pictures in pymupdf4llm output
PICTURE_PLACEHOLDER_MARKER = re.compile(r"==> picture \[\d+ x \d+\] <==")

def _remove_pymupdf4llm_markers(text):
    """Remove markers added by pymupdf4llm during OCR text extraction."""
    text = text.replace(PICTURE_TEXT_START_MARKER, "")
    text = text.replace(PICTURE_TEXT_END_MARKER, "")
    text = PICTURE_PLACEHOLDER_MARKER.sub("", text)
    return text


def _process_single_page_from_file(file_path, page_num):
    """
    Process a single PDF page. This function is designed to be run in parallel.

    Opens the PDF file, extracts text. Each call opens and closes its own document instance, making it safe for parallel execution.
    Args:
        file_path: Path to the PDF file
        page_num: Page number to process (0-indexed)

    Returns:
        dict: Dictionary containing extracted text and metadata
    """

    doc = None

    try:
        doc = pymupdf.open(file_path)

        result = _extract_page(doc, page_num, log_identifier=file_path)

        return {
            'page_num': page_num,
            'text': result,
            'success': True
        }
    except Exception as e:
        logger.error(f"[{file_path}] Error processing page {page_num + 1}: {e}")
        return {
            'page_num': page_num,
            'text': "",
            'success': False,
            'error': str(e)
        }
    finally:
        if doc is not None:
            doc.close()


def _build_docling_converter():
    """Build a DocumentConverter instance with the appropriate pipeline options for table extraction."""

    ocr_options = TesseractCliOcrOptions(lang=AVAILABLE_LANGUAGES)
    pipeline_options = PdfPipelineOptions(do_ocr=True, ocr_options=ocr_options)
    pipeline_options.table_structure_options.mode = TableFormerMode.ACCURATE
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
            InputFormat.IMAGE: ImageFormatOption(pipeline_options=pipeline_options),
        }
    )

    return converter

def _extract_table_with_docling(doc: Any, page_num: int, clip=None, mode: InputFormat = InputFormat.PDF, dpi: int = 150) -> str:
    """Extract a table region from a PDF page using Docling.

    Args:
        doc: An open pymupdf Document object.
        page_num: Zero-indexed page number to extract the table from.
        clip: Optional pymupdf.IRect defining the bounding box of the table region.
              If None, the entire page is used.
        dpi: Resolution used when mode=InputFormat.IMAGE to rasterize the region (default: 150).
        mode: InputFormat.PDF  — crop and pass a single-page PDF stream (TesseractCli, no rasterization).
              InputFormat.IMAGE — rasterize to PNG and pass as image stream (ImageFormatOption + TesseractCli).

    Returns:
        A Markdown-formatted string representing the extracted table(s).
    """
    result = ""
    mode_label = "cropped PDF stream" if mode == InputFormat.PDF else "rasterized PNG"
    logger.debug(f"Extracting table from page {page_num + 1} using Docling with mode: {mode_label}")

    if mode == InputFormat.PDF:
        cropped_doc = pymupdf.open()
        cropped_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
        if clip is not None:
            cropped_page = cropped_doc.load_page(0)
            cropped_page.set_cropbox(pymupdf.Rect(clip))
        data = cropped_doc.tobytes()
        cropped_doc.close()
        stream = DocumentStream(name="table_region.pdf", stream=io.BytesIO(data))
    elif mode == InputFormat.IMAGE:
        page = doc.load_page(page_num)
        clip_pix = page.get_pixmap(dpi=dpi, clip=clip)
        stream = DocumentStream(name="table_region.png", stream=io.BytesIO(clip_pix.tobytes("png")))
    else:
        raise ValueError(f"Unsupported mode '{mode}'. Expected InputFormat.PDF (cropped PDF stream, no rasterization) or InputFormat.IMAGE (rasterized PNG via pixmap).")

    converter = _build_docling_converter()
    conv_result = converter.convert(stream)

    if not conv_result.document or not conv_result.document.tables:
        raise ValueError(f"Docling found no tables in the clipped region (mode: {mode_label})")

    for tbl in conv_result.document.tables:
        # Direct grid export: first row → header, remaining rows → data.
        # Stub/row-header cells appear as regular values in the first column.
        grid = tbl.data.grid
        if not grid or not grid[0]:
            continue
        num_cols = len(grid[0])
        lines = ["| " + " | ".join(cell.text.replace("\n", " ") for cell in row) + " |"
                 for row in grid]
        lines.insert(1, "| " + " | ".join(["---"] * num_cols) + " |")
        result += "\n".join(lines) + "\n\n"

    result = result.strip()
    if not result:
        raise ValueError(f"Table extracted but markdown output is empty (mode: {mode_label})")

    return result


def _parse_to_text(
    doc: Any,
    page_num: int,
    header: bool = True,
    footer: bool = True,
    force_text: bool = True,
    ignore_code: bool = False,
    show_progress: bool = False,
    ocr_dpi: int = 300,
    use_ocr: bool = True,
    force_ocr: bool = False,
    ocr_language: str = "eng",
    ocr_function=None,
) -> str:
    """
    Extract text from a single page. First, obtain full layout information.
    Then iterate over the document blocks and apply the appropriate text extraction method for each block type.
    """

    # Create a temporary single-page Document because pymupdf4llm expects a Document, not a Page.
    single_page_doc = pymupdf.open()
    single_page_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

    parsed = pymupdf4llm_dl.parse_document(
        single_page_doc,
        ocr_dpi=ocr_dpi,
        force_text=force_text,
        use_ocr=use_ocr,
        force_ocr=force_ocr,
        ocr_language=ocr_language,
        ocr_function=ocr_function,
        show_progress=show_progress,
        image_dpi=150,
    )

    output_buffer = ""
    for page in parsed.pages:
        list_item_levels = pymupdf4llm_dl.create_list_item_levels(page.boxes)
        for i, box in enumerate(page.boxes):
            bclass = box.boxclass
            if bclass == "page-header" and header is False:
                continue
            if bclass == "page-footer" and footer is False:
                continue
            
            clip = pymupdf.IRect(box.x0, box.y0, box.x1, box.y1)

            if bclass == "picture":
                if box.textlines:
                    output_buffer += pymupdf4llm_dl.picture_text_to_text(
                            box.textlines, ignore_code=ignore_code or page.full_ocred, clip=clip)
                else:
                    logger.debug(f"Picture block on page {page_num + 1} has no textlines, skipping OCR text extraction for this block.")

            elif bclass in ("table", "table-fallback"):
                # Attempt table extraction with cascading fallbacks:
                #   1. Docling via cropped PDF stream (no rasterization, native Tesseract)
                #   2. Docling via rasterized PNG image (ImageFormatOption + Tesseract)
                #   3. pymupdf4llm wrap_table_for_tabulate (grid text fallback)

                # Note:
                # Docling should operate on the original `doc`, not parsed.pages, to preserve full PDF fidelity;
                # the clip only narrows the table region while the source remains the original document for best results.

                table_text = None

                try:
                    table_text = _extract_table_with_docling(doc, page_num, clip=clip, mode=InputFormat.PDF)
                    logger.info(f"Table on page {page_num + 1} successfully extracted by Docling via cropped PDF stream")
                except Exception as e:
                    logger.warning(f"Docling via cropped PDF stream failed for table on page {page_num + 1}: {e}. Trying rasterized PNG.")

                if table_text is None:
                    try:
                        table_text = _extract_table_with_docling(doc, page_num, clip=clip, mode=InputFormat.IMAGE)
                        logger.info(f"Table on page {page_num + 1} successfully extracted by Docling via rasterized PNG")
                    except Exception as e:
                        logger.warning(f"Docling via rasterized PNG failed for table on page {page_num + 1}: {e}. Entering fallback options.")

                if table_text is None:
                    # fallback options if docling extraction fails (can still produce something, just less structured and accurate)
                    try:
                        wrapped_table = pymupdf4llm_dl.wrap_table_for_tabulate(
                            box.table["extract"],
                            max_width=100,
                            min_col_width=10,
                        )
                        table_text = tabulate.tabulate(wrapped_table, tablefmt="github")
                        logger.info("Fallback table extraction successful.")

                    except Exception as e:
                        logger.warning(f"Fallback table extraction failed for table on page {page_num + 1}: {e}. Trying textline fallback.")

                        # fallback 2: use textline fallback
                        if box.textlines:
                            try:
                                table_text = pymupdf4llm_dl.fallback_text_to_text(
                                    box.textlines, ignore_code=ignore_code or page.full_ocred, clip=clip)
                            except (AttributeError, TypeError) as te:
                                # fallback_text_to_text can fail with non-string values in span["text"]
                                # Use plain text extraction as fallback
                                logger.warning(f"fallback_text_to_text failed for table on page {page_num + 1}: {te}. Using plain text fallback.")
                                text_parts = []
                                for tl in box.textlines:
                                    line_text = " ".join(str(span.get("text", "")) for span in tl.get("spans", []))
                                    if line_text.strip():
                                        text_parts.append(line_text.strip())
                                table_text = "\n".join(text_parts) + "\n\n" if text_parts else ""


                # to avoid None concatenation
                if table_text:
                    output_buffer += table_text + "\n\n"
                else:
                    logger.error(f"All extraction methods failed for table on page {page_num + 1}. No text extracted for this block.")

            elif bclass == "list-item":
                output_buffer += pymupdf4llm_dl.list_item_to_text(box.textlines, list_item_levels[i])
            elif bclass == "footnote":
                output_buffer += pymupdf4llm_dl.footnote_to_text(box.textlines)
            else:
                output_buffer += pymupdf4llm_dl.text_to_text(
                    box.textlines, ignore_code=ignore_code or page.full_ocred)

    return _remove_pymupdf4llm_markers(output_buffer)


def _calculate_ocr_params(page, page_num, log_identifier=""):
    """
    Calculate optimal OCR parameters based on page dimensions.

    pymupdf OCR has practical limits on image dimensions (~10000 pixels per side).
    For very tall or wide pages, reduce DPI or disable parse_document OCR entirely
    to prevent crashes or poor quality output.

    Args:
        page: pymupdf Page object
        page_num: Page number (0-indexed) for logging
        log_identifier: Optional log prefix for messages

    Returns:
        tuple: (ocr_dpi, use_ocr) - adjusted DPI and whether to enable OCR
    """
    page_rect = page.rect

    # Calculate dimensions at default DPI
    # Divide by 72 to convert from points (PDF coordinate system at 72 points per inch) to inches
    # then multiply by DPI to get pixel dimensions
    width_at_dpi = int(page_rect.width * DEFAULT_OCR_DPI / 72)
    height_at_dpi = int(page_rect.height * DEFAULT_OCR_DPI / 72)
    max_dimension = max(width_at_dpi, height_at_dpi)

    if max_dimension <= MAX_OCR_DIMENSION:
        return (DEFAULT_OCR_DPI, True)

    # Scale down DPI proportionally
    adjusted_dpi = int((MAX_OCR_DIMENSION / max_dimension) * DEFAULT_OCR_DPI)
    adjusted_dpi = max(PYMUPDF_MIN_DPI, adjusted_dpi)

    # If DPI too low, disable parse_document OCR - rely on image extraction instead
    if adjusted_dpi < MIN_QUALITY_DPI:
        logger.info(
            f"[{log_identifier}] Page {page_num + 1} dimensions {width_at_dpi}x{height_at_dpi} "
            f"at {DEFAULT_OCR_DPI} DPI exceed limits. DPI {adjusted_dpi} too low for quality - "
            f"disabling parse_document OCR, using image extraction OCR instead."
        )
        return (adjusted_dpi, False)

    logger.info(
        f"[{log_identifier}] Page {page_num + 1} dimensions {width_at_dpi}x{height_at_dpi} "
        f"at {DEFAULT_OCR_DPI} DPI exceed limits. Reducing OCR DPI to {adjusted_dpi}."
    )
    return (adjusted_dpi, True)


def _extract_page(doc, page_num, log_identifier=""):
    """
    Extract text from a single page using an already opened document.

    Args:
        doc: Opened pymupdf Document object
        page_num: Page number to process (0-indexed)
        log_identifier: Optional log identifier (file_path) for logging purposes only

    Returns:
        dict: Dictionary containing extracted text and metadata
    """

    page = doc.load_page(page_num)
    result = ""

    # Calculate optimal OCR parameters based on page dimensions
    ocr_dpi, use_ocr = _calculate_ocr_params(page, page_num, log_identifier)

    result = _parse_to_text(
        doc, page_num,
        header=False,
        footer=False,
        use_ocr=use_ocr,
        force_text=True,
        ocr_dpi=ocr_dpi,
        ocr_language="+".join(AVAILABLE_LANGUAGES),
        ocr_function=_PYMUPDF_OCR_FUNCTION
    )

    # https://pymupdf.readthedocs.io/en/latest/page.html#description-of-get-links-entries
    for link in page.links():
        if link.get("uri"):
            result = result + f" {link.get('uri')}"


    # https://pymupdf.readthedocs.io/en/latest/recipes-images.html#how-to-extract-images-pdf-documents
    images = page.get_images(full=False)
    debug_cnt = 0
    for img in images:
        img_data = doc.extract_image(img[0])
        img_path = ""

        debug_cnt += 1
        logger.info(f"Extracting image {debug_cnt}/{len(images)}")
        try:
            img_path = _save_image(img_data)
            logger.debug(f"[{log_identifier}] Extracted {img_path} for processing")
            img_loader = LoadImage(img_path)
            image_text = img_loader.extract_text()
            image_text = image_text.strip()
            if image_text:
                result += "\n" + image_text
            logger.info(f"[{log_identifier}] Processed image {img_path} for page {page_num + 1}")
        except Exception as e:
            logger.error(f"[{log_identifier}] Error parsing image on page {page_num + 1}: {e}. Ignoring...")
        finally:
            if img_path and img_path != "" and os.path.exists(img_path) and not os.path.isdir(img_path):
                    logger.debug(f"[{log_identifier}] Removed {img_path} after processing")
                    os.remove(img_path)

    return result


def _save_image(data, save_path="/tmp/opea_upload"):
    """Save image data to a file."""

    import uuid
    if not os.path.exists(save_path):
        os.makedirs(save_path, mode=0o700, exist_ok=True)
    image_ext = data["ext"]
    image_filename = os.path.join(save_path, f"{uuid.uuid4()}.{image_ext}")
    with open(image_filename, "wb") as f:
        f.write(data["image"])
    return image_filename


class LoadPdf(AbstractLoader):
    def __init__(self, file_path):
        super().__init__(file_path)
        nltk.download('punkt_tab', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        nltk.download('averaged_perceptron_tagger_eng', quiet=True)

    def extract_text(self):
        """
        Load the pdf file with parallel page processing.

        NOTE: This method is NOT called by the production microservice.
        opea_text_extractor_microservice.py bypasses LoadPdf entirely and calls
        _process_single_page_from_file() directly via a shared ProcessPoolExecutor,
        dispatching one pool task per page. This avoids nested process pools
        (which would OOM the pod) and keeps the asyncio event loop free for
        health checks and concurrent requests.
        This method exists for standalone use and unit tests only.
        Any debug code or logging added here will NOT appear in pod logs.
        To instrument production behaviour, modify _process_single_page_from_file()
        or _extract_page() instead.

        Environment variables:
        - PDF_PARALLEL_PROCESSING: Enable/disable parallel processing (default: true)
        - TEXT_EXTRACTOR_MAX_WORKERS: Maximum number of parallel workers (default: 12; injected automatically from pod CPU limit via Kubernetes Downward API)
        """

        doc = pymupdf.open(self.file_path)
        page_count = doc.page_count
        doc.close()
        
        logger.info(f"[{self.file_path}] Processing {page_count} pages")
        
        # Configuration from environment variables
        enable_parallel = os.getenv('PDF_PARALLEL_PROCESSING', 'true').lower() == 'true'

        # Never create a nested pool: if this code is already running inside a worker
        # process (spawned by the microservice's ProcessPoolExecutor), creating another
        # pool here would multiply process count by max_workers, causing OOM.
        if multiprocessing.current_process().name != 'MainProcess':
            enable_parallel = False
            logger.info(f"[{self.file_path}] Running inside worker process, using sequential processing to avoid nested pool")

        # PDF_MAX_WORKERS is injected by the Kubernetes Downward API (limits.cpu)
        # in the pod spec, so this always reflects the actual pod CPU limit.
        max_workers = min(page_count, int(os.getenv('PDF_MAX_WORKERS', 12)))
        
        start_time = time.time()
        
        if enable_parallel and page_count > 1:
            # Parallel processing
            logger.info(f"[{self.file_path}] Using parallel processing with {max_workers} workers")
            results = {}
            
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                # Submit all pages for processing
                future_to_page = {
                    executor.submit(_process_single_page_from_file, self.file_path, i): i
                    for i in range(page_count)
                }

                # Collect results as they complete
                for future in as_completed(future_to_page):
                    page_num = future_to_page[future]
                    try:
                        page_result = future.result()
                        results[page_result['page_num']] = page_result['text']
                        
                        if page_result['success']:
                            logger.info(f"[{self.file_path}] Page {page_num + 1}/{page_count} completed")
                        else:
                            err_msg = f"[{self.file_path}] Page {page_num + 1}/{page_count} failed: {page_result.get('error', 'Unknown error')}"
                            logger.error(err_msg)
                            raise Exception(err_msg)
                    except Exception as e:
                        logger.error(f"[{self.file_path}] Error retrieving result for page {page_num + 1}: {e}")
                        raise e
            
            # Combine results in page order
            result = " ".join(results[i] for i in range(page_count))

        else:
            # Sequential processing (fallback or single page)
            if page_count == 1:
                logger.info(f"[{self.file_path}] Using sequential processing for single page")
            else:
                logger.info(f"[{self.file_path}] Using sequential processing (parallel disabled)")
            
            doc = None
            try:
                result = ""
                doc = pymupdf.open(self.file_path)

                for i in range(page_count):
                    page_start = time.time()
                    page_result = _extract_page(doc, i, log_identifier=self.file_path)
                    result += " " + page_result if result else page_result
                    page_end = time.time()
                    logger.info(f"[{self.file_path}] Page {i+1}/{page_count} processed in {page_end - page_start:.2f} seconds")

            except Exception as e:
                logger.error(f"[{self.file_path}] Error processing document: {e}")
                raise e
            finally:
                if doc is not None:
                    doc.close()
        
        end_time = time.time()
        logger.info(f"[{self.file_path}] Total processing time: {end_time - start_time:.2f} seconds for {page_count} pages")

        return result

    def extract_metadata(self):
        """Extract rich metadata from PDF document properties."""
        metadata = super().extract_metadata()
        
        try:
            doc = pymupdf.open(self.file_path)
            meta = doc.metadata or {}
            doc.close()
            
            if meta.get('title'):
                metadata['file_title'] = meta['title']
            if meta.get('author'):
                metadata['author'] = meta['author']
            
            # Parse PDF dates (D:YYYYMMDDHHmmSS format)
            from datetime import datetime
            for pdf_key, out_key in [('creationDate', 'creation_date'), ('modDate', 'last_update_date')]:
                if date_str := meta.get(pdf_key):
                    clean = (date_str[2:16] if date_str.startswith('D:') else date_str[:14]).ljust(14, '0')
                    metadata[out_key] = int(datetime.strptime(clean, '%Y%m%d%H%M%S').timestamp())
        except Exception as e:
            logger.error(f"[{self.file_path}] PDF metadata extraction failed: {e}")
        
        return metadata
