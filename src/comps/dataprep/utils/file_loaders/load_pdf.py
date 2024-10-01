# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import easyocr
import fitz
import io
import nltk
import numpy
from PIL import Image
from comps.dataprep.utils.file_loaders.abstract_loader import AbstractLoader


class LoadPdf(AbstractLoader):
    def __init__(self, file_path):
        super().__init__(file_path)
        nltk.download('punkt_tab')
        nltk.download('averaged_perceptron_tagger')
        nltk.download('averaged_perceptron_tagger_eng')

    def extract_text(self):
        """Load the pdf file."""
        doc = fitz.open(self.file_path)
        reader = easyocr.Reader(["en"], gpu=False)
        result = ""
        for i in range(doc.page_count):
            page = doc.load_page(i)
            pagetext = page.get_text().strip()
            if pagetext:
                if pagetext.endswith("!") or pagetext.endswith("?") or pagetext.endswith("."):
                    result = result + pagetext
                else:
                    result = result + pagetext + "."
            if len(doc.get_page_images(i)) > 0:
                for img in doc.get_page_images(i):
                    if img:
                        pageimg = ""
                        xref = img[0]
                        img_data = doc.extract_image(xref)
                        img_bytes = img_data["image"]
                        pil_image = Image.open(io.BytesIO(img_bytes))
                        img = numpy.array(pil_image)
                        img_result = reader.readtext(img, paragraph=True, detail=0)
                        pageimg = pageimg + ", ".join(img_result).strip()
                        if pageimg.endswith("!") or pageimg.endswith("?") or pageimg.endswith("."):
                            pass
                        else:
                            pageimg = pageimg + "."
                    result = result + pageimg
        return result

    def get_tables_result(self, table_strategy):
        """Extract tables information from pdf file."""
        if table_strategy == "fast":
            return None

        from unstructured.documents.elements import FigureCaption
        from unstructured.partition.pdf import partition_pdf

        tables_result = []
        raw_pdf_elements = partition_pdf(
            filename=self.file_path,
            infer_table_structure=True,
        )
        tables = [el for el in raw_pdf_elements if el.category == "Table"]
        for table in tables:
            table_coords = table.metadata.coordinates.points
            content = table.metadata.text_as_html
            table_page_number = table.metadata.page_number
            min_distance = float("inf")
            table_summary = None
            if table_strategy == "hq":
                for element in raw_pdf_elements:
                    if isinstance(element, FigureCaption) or element.text.startswith("Tab"):
                        caption_page_number = element.metadata.page_number
                        caption_coords = element.metadata.coordinates.points
                        related, y_distance = self.get_relation(
                            table_coords, caption_coords, table_page_number, caption_page_number
                        )
                        if related:
                            if y_distance < min_distance:
                                min_distance = y_distance
                                table_summary = element.text
                if table_summary is None:
                    parent_id = table.metadata.parent_id
                    for element in raw_pdf_elements:
                        if element.id == parent_id:
                            table_summary = element.text
                            break
            elif table_strategy is None:
                table_summary = None
            if table_summary is None:
                text = f"[Table: {content}]"
            else:
                text = f"|Table: [Summary: {table_summary}], [Content: {content}]|"
            tables_result.append(text)
        return tables_result

    def get_relation(self, table_coords, caption_coords, table_page_number, caption_page_number, threshold=100):
        """Get the relation of a pair of table and caption."""
        same_page = table_page_number == caption_page_number
        x_overlap = (min(table_coords[2][0], caption_coords[2][0]) - max(table_coords[0][0], caption_coords[0][0])) > 0
        if table_coords[0][1] - caption_coords[1][1] >= 0:
            y_distance = table_coords[0][1] - caption_coords[1][1]
        elif caption_coords[0][1] - table_coords[1][1] >= 0:
            y_distance = caption_coords[0][1] - table_coords[1][1]
        else:
            y_distance = 0
        y_close = y_distance < threshold
        return same_page and x_overlap and y_close, y_distance
