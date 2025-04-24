# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


import os
from comps.dataprep.utils.file_loaders.load_html import LoadHtml
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class LoadAsciiDoc(LoadHtml):
    def __init__(self, file_path):
        super().__init__(file_path)

    def extract_text(self):
        """Load adoc file."""
        dir_path = os.path.dirname(self.file_path)
        adoc_html_output_file = os.path.join(dir_path, "temp_output.html")
        try:
            os.system(f"asciidoctor -b html5 -o {adoc_html_output_file} {self.file_path}")
            logger.info(f"Converted adoc to html. Created temporary file: {adoc_html_output_file}")

            original_file_path = self.file_path
            self.file_path = adoc_html_output_file
            output = super().extract_text()
            self.file_path = original_file_path
        except Exception as e:
            err_msg = f"Failed to parse adoc file. Exception: {e}"
            logger.error(err_msg)
            raise Exception(err_msg)
        finally:
            if os.path.exists(adoc_html_output_file):
                os.remove(adoc_html_output_file)
                logger.info(f"Removed temporary file: {adoc_html_output_file}")

        return output
