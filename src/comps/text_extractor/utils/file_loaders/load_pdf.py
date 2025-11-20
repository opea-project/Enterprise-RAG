# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import pymupdf
import nltk
import time
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from comps.text_extractor.utils.file_loaders.abstract_loader import AbstractLoader
from comps.text_extractor.utils.file_loaders.load_image import LoadImage
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


def _process_single_page(file_path, page_num):
    """
    Process a single PDF page. This function is designed to be run in parallel.
    
    Args:
        file_path: Path to the PDF file
        page_num: Page number to process (0-indexed)
        
    Returns:
        dict: Dictionary containing extracted text and metadata
    """
    try:
        doc = pymupdf.open(file_path)
        page = doc.load_page(page_num)
        page.clean_contents()
        
        result = ""
        
        # https://pymupdf.readthedocs.io/en/latest/page.html#description-of-get-links-entries
        for link in page.links(): 
            if link.get("uri"):
                result = result + f" {link.get('uri')}"
        
        # https://pymupdf.readthedocs.io/en/latest/recipes-text.html#how-to-extract-table-content-from-documents
        finder = page.find_tables()
        for table in finder.tables:
            logger.info(f"[{file_path}] Extracting table from page {page_num + 1}")
            table_data = table.extract()
            if len(table_data) > 0:
                flattened_table_data = [str(item) for sublist in table_data for item in sublist]
                result += " ".join(flattened_table_data)
        
        # https://pymupdf.readthedocs.io/en/latest/recipes-text.html#how-to-extract-text-from-pdf-documents
        # simple page.get_text() does extact text, but it includes text from tables. skip table bounding boxes from the text extraction
        try:
            non_table_text = []
            text_dict = page.get_text("dict")
            table_rects = [pymupdf.Rect(table.bbox) for table in finder.tables]
            for block in text_dict["blocks"]:
                block_rect = pymupdf.Rect(block["bbox"])
                if not any(block_rect.intersects(table_rect) for table_rect in table_rects):
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                non_table_text.append(span["text"])
            result += " ".join(non_table_text)
        except Exception:
            result += page.get_text().strip()
        
        # https://pymupdf.readthedocs.io/en/latest/recipes-images.html#how-to-extract-images-pdf-documents
        images = doc.get_page_images(page_num, full=False)
        for img in images:
            img_data = doc.extract_image(img[0])
            img_path = ""
            try:
                img_path = _save_image(img_data)
                logger.debug(f"[{file_path}] Extracted {img_path} for processing")
                img_loader = LoadImage(img_path)
                result += img_loader.extract_text()
                logger.info(f"[{file_path}] Processed image {img_path} for page {page_num + 1}")
            except Exception as e:
                logger.error(f"[{file_path}] Error parsing image on page {page_num + 1}: {e}. Ignoring...")
            finally:
                if img_path and img_path != "" and os.path.exists(img_path) and not os.path.isdir(img_path):
                    logger.debug(f"[{file_path}] Removed {img_path} after processing")
                    os.remove(img_path)
        
        doc.close()
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
        
        Environment variables:
        - PDF_PARALLEL_PROCESSING: Enable/disable parallel processing (default: true)
        - PDF_MAX_WORKERS: Maximum number of parallel workers (default: auto-detect)
        """
        doc = pymupdf.open(self.file_path)
        page_count = doc.page_count
        doc.close()
        
        logger.info(f"[{self.file_path}] Processing {page_count} pages")
        
        # Configuration from environment variables
        enable_parallel = os.getenv('PDF_PARALLEL_PROCESSING', 'true').lower() == 'true'
        max_workers = os.getenv('PDF_MAX_WORKERS', None)
        
        if max_workers:
            max_workers = int(max_workers)
        else:
            # Auto-detect: use min of (page_count, cpu_count, 8)
            # Cap at 8 to avoid excessive memory usage
            max_workers = min(page_count, os.cpu_count() or 4, 8)
        
        start_time = time.time()
        
        if enable_parallel and page_count > 1:
            # Parallel processing
            logger.info(f"[{self.file_path}] Using parallel processing with {max_workers} workers")
            results = {}
            
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                # Submit all pages for processing
                future_to_page = {
                    executor.submit(_process_single_page, self.file_path, i): i 
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
            
            result = ""
            doc = pymupdf.open(self.file_path)
            
            for i in range(page_count):
                page_start = time.time()
                page_result = self._extract_page_sequential(doc, i)
                result += " " + page_result if result else page_result
                page_end = time.time()
                logger.info(f"[{self.file_path}] Page {i+1}/{page_count} processed in {page_end - page_start:.2f} seconds")
            
            doc.close()
        
        end_time = time.time()
        logger.info(f"[{self.file_path}] Total processing time: {end_time - start_time:.2f} seconds for {page_count} pages")
        
        return result

    def _extract_page_sequential(self, doc, page_num):
        """Extract text from a single page (sequential processing)."""
        result = ""
        page = doc.load_page(page_num)
        page.clean_contents()
        
        # https://pymupdf.readthedocs.io/en/latest/page.html#description-of-get-links-entries
        for link in page.links(): 
            if link.get("uri"):
                result = result + f" {link.get('uri')}"
        
        # https://pymupdf.readthedocs.io/en/latest/recipes-text.html#how-to-extract-table-content-from-documents
        finder = page.find_tables()
        for table in finder.tables:
            logger.info(f"[{self.file_path}] Extracting table from page {page_num + 1}")
            table_data = table.extract()
            if len(table_data) > 0:
                flattened_table_data = [str(item) for sublist in table_data for item in sublist]
                result += " ".join(flattened_table_data)
        
        # https://pymupdf.readthedocs.io/en/latest/recipes-text.html#how-to-extract-text-from-pdf-documents
        # simple page.get_text() does extact text, but it includes text from tables. skip table bounding boxes from the text extraction
        try:
            non_table_text = []
            text_dict = page.get_text("dict")
            table_rects = [pymupdf.Rect(table.bbox) for table in finder.tables]
            for block in text_dict["blocks"]:
                block_rect = pymupdf.Rect(block["bbox"])
                if not any(block_rect.intersects(table_rect) for table_rect in table_rects):
                    if "lines" in block:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                non_table_text.append(span["text"])
            result += " ".join(non_table_text)
        except Exception:
            result += page.get_text().strip()
        
        # https://pymupdf.readthedocs.io/en/latest/recipes-images.html#how-to-extract-images-pdf-documents
        images = doc.get_page_images(page_num, full=False)
        for img in images:
            img_data = doc.extract_image(img[0])
            img_path = ""
            try:
                img_path = _save_image(img_data)
                logger.debug(f"[{self.file_path}] Extracted {img_path} for processing")
                img_loader = LoadImage(img_path)
                result += img_loader.extract_text()
                logger.info(f"[{self.file_path}] Processed image {img_path}")
            except Exception as e:
                logger.error(f"[{self.file_path}] Error parsing image {img_path}: {e}. Ignoring...")
            finally:
                if img_path and img_path != "" and os.path.exists(img_path) and not os.path.isdir(img_path):
                    logger.debug(f"[{self.file_path}] Removed {img_path} after processing")
                    os.remove(img_path)
        
        return result
