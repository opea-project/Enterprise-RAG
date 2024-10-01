# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0


class FileParser:
    def __init__(self, file_path):
        self._mappings = self.default_mappings()

        self.file_path = file_path
        self.file_type = file_path.split('.')[-1]

        if self.file_type not in self.supported_types():
            raise ValueError(f"Unsupported file type: {self.file_type}. Supported files types: {', '.join(self.supported_types())}")

    def parse(self):
        file_type = self.file_path.split('.')[-1]
        file_loader = self.supported_file(file_type)
        loader = getattr(
            __import__(f"comps.dataprep.utils.file_loaders.{file_loader['loader_file_name']}", fromlist=['comps']),
            file_loader['loader_class']
        )
        return loader(self.file_path).extract_text()

    def default_mappings(self):
        # file type, and loader class file name without extension
        return [
            {'file_type': 'doc',   'loader_file_name': 'load_doc',   'loader_class': 'LoadDoc'},
            {'file_type': 'docx',  'loader_file_name': 'load_doc',   'loader_class': 'LoadDoc'},
            {'file_type': 'txt',   'loader_file_name': 'load_txt',   'loader_class': 'LoadTxt'},
            {'file_type': 'json',  'loader_file_name': 'load_json',  'loader_class': 'LoadJson'},
            {'file_type': 'jsonl', 'loader_file_name': 'load_json',  'loader_class': 'LoadJson'},
            {'file_type': 'csv',   'loader_file_name': 'load_csv',   'loader_class': 'LoadCsv'},
            {'file_type': 'xlsx',  'loader_file_name': 'load_xls',   'loader_class': 'LoadXls'},
            {'file_type': 'xls',   'loader_file_name': 'load_xls',   'loader_class': 'LoadXls'},
            {'file_type': 'pdf',   'loader_file_name': 'load_pdf',   'loader_class': 'LoadPdf'},
            {'file_type': 'html',  'loader_file_name': 'load_html',  'loader_class': 'LoadHtml'},
            {'file_type': 'md',    'loader_file_name': 'load_md',    'loader_class': 'LoadMd'},
            {'file_type': 'xml',   'loader_file_name': 'load_xml',   'loader_class': 'LoadXml'},
            {'file_type': 'yaml',  'loader_file_name': 'load_yaml',  'loader_class': 'LoadYaml'},
            {'file_type': 'ppt',   'loader_file_name': 'load_ppt',   'loader_class': 'LoadPpt'},
            {'file_type': 'pptx',  'loader_file_name': 'load_ppt',   'loader_class': 'LoadPpt'},
            {'file_type': 'tiff',  'loader_file_name': 'load_image', 'loader_class': 'LoadImage'},
            {'file_type': 'jpg',   'loader_file_name': 'load_image', 'loader_class': 'LoadImage'},
            {'file_type': 'jpeg',  'loader_file_name': 'load_image', 'loader_class': 'LoadImage'},
            {'file_type': 'png',   'loader_file_name': 'load_image', 'loader_class': 'LoadImage'},
            {'file_type': 'svg',   'loader_file_name': 'load_image', 'loader_class': 'LoadImage'},
        ]

    def supported_types(self):
        return [mapping['file_type'] for mapping in self._mappings]

    def supported_file(self, file_type):
        for mapping in self._mappings:
            if mapping['file_type'] == file_type:
                return mapping
