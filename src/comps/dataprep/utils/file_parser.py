# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import magic
import os
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class FileParser:
    def __init__(self, file_path):
        self._mappings = self.default_mappings()

        self.file_path = file_path
        self.file_type = file_path.split('.')[-1]
        self.mime_type = self.get_mime_type()

        if os.path.islink(self.file_path):
            raise ValueError(f"The file {self.file_path} is a symbolic link, which is not allowed.")
        if self.file_type not in self.supported_types():
            raise ValueError(f"Unsupported file type: {self.file_type}. Supported files types: {', '.join(self.supported_types())}")
        if self.mime_type not in self.supported_mime_types():
            raise ValueError(f"Unsupported mime type: {self.mime_type}. Supported mime types: {', '.join(self.supported_mime_types())}")
        file_types_via_mime = [m['file_type'] for m in self.supported_file(self.mime_type)]
        if self.file_type not in file_types_via_mime:
            raise ValueError(f"File type and mime type mismatch. File type: {self.file_type}, Mime type: {self.mime_type}. Expected file type: {', '.join(file_types_via_mime)}")

    def get_mime_type(self):
        return magic.from_file(self.file_path, mime=True)

    def parse(self):
        supported_mappings = self.supported_file(self.mime_type)
        file_loader = next(m for m in supported_mappings if m['file_type'] == self.file_type)

        loader = getattr(
            __import__(f"comps.dataprep.utils.file_loaders.{file_loader['loader_file_name']}", fromlist=['comps']),
            file_loader['loader_class']
        )

        logger.info(f"Started processing file {self.file_path} with loader {file_loader['loader_class']}")

        data = None
        try:
            data = loader(self.file_path).extract_text()
        except Exception as e:
            logger.exception(f"Error while processing file {self.file_path} with loader {file_loader['loader_class']}. {e}")
            raise

        logger.info(f"Finished processing file {self.file_path} with loader {file_loader['loader_class']}")

        return data

    def default_mappings(self):
        return [
            {'file_type': 'doc',   'loader_file_name': 'load_doc',   'loader_class': 'LoadDoc',    'mime_type': 'application/msword'},
            {'file_type': 'docx',  'loader_file_name': 'load_doc',   'loader_class': 'LoadDoc',    'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'},
            {'file_type': 'txt',   'loader_file_name': 'load_txt',   'loader_class': 'LoadTxt',    'mime_type': 'text/plain'},
            {'file_type': 'json',  'loader_file_name': 'load_json',  'loader_class': 'LoadJson',   'mime_type': 'application/json'},
            {'file_type': 'jsonl', 'loader_file_name': 'load_json',  'loader_class': 'LoadJson',   'mime_type': 'application/x-ndjson'},
            {'file_type': 'csv',   'loader_file_name': 'load_csv',   'loader_class': 'LoadCsv',    'mime_type': 'text/csv'},
            {'file_type': 'xlsx',  'loader_file_name': 'load_xls',   'loader_class': 'LoadXls',    'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'},
            {'file_type': 'xls',   'loader_file_name': 'load_xls',   'loader_class': 'LoadXls',    'mime_type': 'application/vnd.ms-excel'},
            {'file_type': 'pdf',   'loader_file_name': 'load_pdf',   'loader_class': 'LoadPdf',    'mime_type': 'application/pdf'},
            {'file_type': 'html',  'loader_file_name': 'load_html',  'loader_class': 'LoadHtml',   'mime_type': 'text/html'},
            {'file_type': 'md',    'loader_file_name': 'load_md',    'loader_class': 'LoadMd',     'mime_type': 'text/plain'},
            {'file_type': 'xml',   'loader_file_name': 'load_xml',   'loader_class': 'LoadXml',    'mime_type': 'text/xml'},
            {'file_type': 'yaml',  'loader_file_name': 'load_yaml',  'loader_class': 'LoadYaml',   'mime_type': 'application/yaml'},
            {'file_type': 'ppt',   'loader_file_name': 'load_ppt',   'loader_class': 'LoadPpt',    'mime_type': 'application/vnd.ms-powerpoint'},
            {'file_type': 'pptx',  'loader_file_name': 'load_ppt',   'loader_class': 'LoadPpt',    'mime_type': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'},
            {'file_type': 'tiff',  'loader_file_name': 'load_image', 'loader_class': 'LoadImage',  'mime_type': 'image/tiff'},
            {'file_type': 'jpg',   'loader_file_name': 'load_image', 'loader_class': 'LoadImage',  'mime_type': 'image/jpeg'},
            {'file_type': 'jpeg',  'loader_file_name': 'load_image', 'loader_class': 'LoadImage',  'mime_type': 'image/jpeg'},
            {'file_type': 'png',   'loader_file_name': 'load_image', 'loader_class': 'LoadImage',  'mime_type': 'image/png'},
            {'file_type': 'svg',   'loader_file_name': 'load_image', 'loader_class': 'LoadImage',  'mime_type': 'image/svg+xml'},
        ]

    def supported_mime_types(self):
        return [mapping['mime_type'] for mapping in self._mappings]

    def supported_types(self):
        return [mapping['file_type'] for mapping in self._mappings]

    def supported_file(self, mime_type):
        mappings = []
        for mapping in self._mappings:
            if mapping['mime_type'] == mime_type:
                mappings.append(mapping)
        return mappings
