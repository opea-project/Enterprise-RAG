# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import docx
from comps.dataprep.utils.file_loaders.abstract_loader import AbstractLoader
from comps.dataprep.utils.file_loaders.load_image import LoadImage
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class LoadDoc(AbstractLoader):
    """ Load and parse doc/docx files. """
    def extract_text(self):
        if self.file_type == "doc":
            self.convert_to_docx(self.file_path)

        doc = docx.Document(self.file_path)
        parsed_text = ""

        logger.info(f"[{self.file_path}] Processing {len(doc.element.body)} elements")

        for child in doc.element.body.iterchildren():
            # {http://schemas.openxmlformats.org/wordprocessingml/2006/main}tbl
            if child.tag.endswith('tbl'):
                table = docx.table.Table(child, doc)
                parsed_text += self.extract_text_from_table(table)
            # {http://schemas.openxmlformats.org/wordprocessingml/2006/main}p
            if child.tag.endswith('p'):
                paragraph = docx.text.paragraph.Paragraph(child, doc)
                parsed_text += self.extract_text_from_paragraph(paragraph)

        return parsed_text

    def extract_text_from_paragraph(self, paragraph):
        parsed_text = ""
        para_text = []
        for paragraph_content in paragraph.iter_inner_content():
            if isinstance(paragraph_content, docx.text.run.Run):
                for int_cont in paragraph_content.iter_inner_content():
                    if isinstance(int_cont, docx.text.run.Drawing):
                        img_path = ""
                        try:
                            img_path = self.save_image(int_cont, os.getenv("UPLOAD_PATH", "/tmp/opea_upload"))
                            logger.debug(f"[{self.file_path}] Extracted {img_path} for processing")
                            img_loader = LoadImage(img_path)
                            para_text.append(img_loader.extract_text())
                            logger.info(f"[{self.file_path}] Processed image {img_path}")
                        except Exception as e:
                            logger.error(f"[{self.file_path}] Error parsing image: {e}. Ignoring...")
                        finally:
                            if img_path and img_path != "" and os.path.exists(img_path) and not os.path.isdir(img_path):
                                logger.debug(f"[{self.file_path}] Removed {img_path} after processing")
                                os.remove(img_path)
                    if isinstance(int_cont, str):
                        para_text.append(int_cont.strip())
            if isinstance(paragraph_content, docx.text.hyperlink.Hyperlink):
                para_text.append(f"{paragraph_content.text.strip()} ({paragraph_content.url})")
        
        cleaned = [str(item).strip() for item in para_text if item not in (None, "")]
        if len(cleaned) > 0:
            parsed_text += " ".join(cleaned)
            parsed_text += "\n"
        
        return parsed_text

    def extract_text_from_table(self, table):
        parsed_text = ""
        for row in table.rows:
            for cell in row.cells:
                cell_text = []
                for paragraph in cell.paragraphs:
                    cell_text.append(self.extract_text_from_paragraph(paragraph))
                cleaned = [str(item).strip() for item in cell_text if item not in (None, "")]
                if len(cleaned) > 0:
                    parsed_text += " ".join(cell_text)
                    parsed_text += "\n"
        return parsed_text

    def save_image(self, drawing, save_path="/tmp/opea_upload"):
        import uuid
        import os
        blip = drawing._element.xpath('.//a:blip')
        if blip:
            r_embed = blip[0].get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed')
            image_part = drawing._parent.part.related_parts[r_embed]
            image_data = image_part.blob
            image_ext = image_part.content_type.split('/')[-1]
            image_filename = os.path.join(save_path, f"{uuid.uuid4()}.{image_ext}")
            with open(image_filename, 'wb') as f:
                f.write(image_data)
            print(f"Saved: {image_filename}")
            return image_filename
        return None

    def convert_to_docx(self, doc_path):
        """Convert doc file to docx file."""
        docx_path = doc_path + "x"
        os.system(f"libreoffice --headless --invisible --convert-to docx --outdir {os.path.dirname(docx_path)} {doc_path}")
        self.file_path = docx_path
        self._file_type = "docx"
