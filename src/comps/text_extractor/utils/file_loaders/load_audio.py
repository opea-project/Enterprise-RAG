# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import requests
from comps.text_extractor.utils.file_loaders.abstract_loader import AbstractLoader
from comps.cores.mega.logger import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class LoadAudio(AbstractLoader):
    def __init__(self, file_path, asr_endpoint=None):
        super().__init__(file_path)
        self.asr_endpoint = asr_endpoint

    def extract_text(self):
        """Load and process audio file using ASR microservice."""
        if not self.asr_endpoint or self.asr_endpoint.strip() == "":
            raise ValueError("ASR_MODEL_SERVER_ENDPOINT is not configured. Cannot process audio files.")

        # Construct the full URL for the ASR transcription endpoint
        url = f"{self.asr_endpoint.rstrip('/')}/v1/audio/transcriptions"

        logger.info(f"Sending audio file {self.file_path} to ASR endpoint: {url}")

        try:
            with open(self.file_path, 'rb') as audio_file:
                files = {
                    'file': (os.path.basename(self.file_path), audio_file, self._get_content_type())
                }
                data = {
                    'language': 'auto',
                    'response_format': 'json'
                }

                response = requests.post(url, files=files, data=data, timeout=300)
                response.raise_for_status()

                result = response.json()

                if 'text' not in result:
                    raise ValueError(f"ASR response does not contain 'text' field: {result}")

                transcribed_text = result['text']
                logger.info(f"Successfully transcribed audio file {self.file_path}")

                return transcribed_text

        except requests.exceptions.Timeout as e:
            error_msg = f"Timeout error while transcribing audio file {self.file_path}: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Connection error while transcribing audio file {self.file_path}. Is ASR microservice running at {self.asr_endpoint}? Error: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error while transcribing audio file {self.file_path}: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        except Exception as e:
            error_msg = f"Error while transcribing audio file {self.file_path}: {str(e)}"
            logger.error(error_msg)
            raise

    def _get_content_type(self):
        """Get the content type based on file extension."""
        extension = self.file_type.lower()
        content_types = {
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav'
        }
        return content_types.get(extension, 'application/octet-stream')
