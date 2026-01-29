# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
import io
import json
import requests
import struct
import wave

from openai import AsyncOpenAI

from comps.cores.proto.api_protocol import AudioTranscriptionResponse
from comps.cores.proto.docarray import Audio2TextDoc
from comps import get_opea_logger

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

VALIDATED_LANGUAGES = ["auto", "en", "pl"]
SUPPORTED_RESPONSE_FORMATS = ["json", "text", "verbose_json"]

class OPEAAsr:
    def __init__(
        self,
        model_name: str,
        model_server: str,
        model_server_endpoint: str
    ):
        """
        Initialize the OPEASR instance with the given parameters.

        :param model_name: Name of the ASR model.
        :param model_server: Server hosting the ASR model (e.g., "vllm").
        :param model_server_endpoint: Endpoint for the ASR model server.
        :param insecure_endpoint: Whether to skip TLS verification.
        :param headers: Optional headers for requests.

        Raises:
            ValueError: If any of the required parameters are missing or empty.
        """
        self._model_name = model_name
        self._model_server = model_server
        self._model_server_endpoint = model_server_endpoint
        if not self._model_server_endpoint.rstrip("/").endswith("/v1"):
            self._model_server_endpoint = self._model_server_endpoint.rstrip("/") + "/v1"

        self._validate_config()
        self._validate_model_server()

        logger.info(
            f"OPEA ASR Microservice is configured to send requests to service {self._model_server_endpoint}"
        )

    def _validate_config(self) -> None:
        """Validate the configuration values."""
        try:
            if not self._model_name:
                raise ValueError("The 'ASR_MODEL_NAME' cannot be empty.")
            if not self._model_server_endpoint:
                raise ValueError("The 'ASR_MODEL_SERVER_ENDPOINT' cannot be empty.")
            if not self._model_server:
                raise ValueError("The 'ASR_MODEL_SERVER' cannot be empty.")
            if self._model_server.lower() != "vllm":
                raise ValueError(f"Unsupported ASR model server '{self._model_server}'. Currently only 'vllm' is supported.")
        except Exception as e:
            logger.exception(f"Configuration validation error: {e}")
            raise

    def _make_silence_wav_bytes(self, duration_sec=0.5, sample_rate=16000) -> bytes:
        """
        Create a small mono WAV (PCM 16-bit) containing silence.
        """
        n_channels = 1
        sampwidth = 2
        n_frames = int(duration_sec * sample_rate)

        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(n_channels)
            wf.setsampwidth(sampwidth)
            wf.setframerate(sample_rate)
            # write silence (0 amplitude)
            silence_frame = struct.pack('<h', 0)  # little-endian 16-bit
            wf.writeframes(silence_frame * n_frames)
        buf.seek(0)
        return buf.getvalue()

    def _validate_model_server(self, timeout_sec: int = 30) -> None:
        """
        Validate that the ASR transcription endpoint is reachable and functional by
        sending a tiny in-memory WAV file.
        """
        wav_bytes = self._make_silence_wav_bytes(duration_sec=0.5, sample_rate=16000)

        files = {
            "file": ("silence.wav", wav_bytes, "audio/wav"),
        }

        data = {
            "model": self._model_name,
            "language": "en",
            "response_format": "json",
            "temperature": 0
        }

        try:
            resp = requests.post(f"{self._model_server_endpoint}/audio/transcriptions", files=files, data=data, timeout=timeout_sec)
            resp.raise_for_status()

        except requests.RequestException as e:
            logger.error(f"Failed to connect to ASR microservice at {self._model_server_endpoint}: {e}. " \
                "Check if the ASR model server is running and accessible and provided model name is correct.")
            raise ConnectionError(f"Failed to connect to ASR microservice at {self._model_server_endpoint}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during ASR endpoint validation: {e}")
            raise

        logger.info("OPEAAsr model server connection validated successfully.")

    async def run(self, input: Audio2TextDoc) -> AudioTranscriptionResponse:
        """
        Process audio transcription using the ASR model server.

        :param input: Audio2TextDoc containing audio data (base64 encoded) and parameters.
        :return: AudioTranscriptionResponse with transcription text.
        """

        logger.info(f"Processing audio file with language: {input.language}, response_format: {input.response_format}")

        if input.model is not None and input.model.strip() != self._model_name:
            raise ValueError(f"Model name mismatch: input model '{input.model}' does not match configured model '{self._model_name}'")

        language = None
        if input.language is not None:
            language = input.language.strip().lower()
        if language not in VALIDATED_LANGUAGES:
            raise ValueError(f"Unsupported language '{input.language}'. Supported languages are: {', '.join(VALIDATED_LANGUAGES)}")

        if language == "auto":
            language = "en"

        response_format = "json"
        if input.response_format is not None and \
            input.response_format.strip().lower() in SUPPORTED_RESPONSE_FORMATS:
            response_format = input.response_format.strip().lower()
        else:
            raise ValueError(f"Unsupported response format '{input.response_format}'. Supported formats are: {', '.join(SUPPORTED_RESPONSE_FORMATS)}")

        try:
            audio_file = io.BytesIO(input.file)

            client = AsyncOpenAI(
                api_key="dummy",
                base_url=self._model_server_endpoint,
                timeout=60,
                max_retries=1
            )

            response = await client.audio.transcriptions.create(
                model=self._model_name,
                file=audio_file,
                language=language,
                response_format=response_format,
                temperature=0
            )

            if response_format == "text":
                logger.info(f"Received ASR text response: {response}")

                response = json.loads(response)
                res = AudioTranscriptionResponse(text=response["text"])
            else:
                logger.info(f"Received ASR response: {response.text}")
                res = AudioTranscriptionResponse(text=response.text)
            return res
        except Exception as e:
            logger.exception(f"Error during ASR transcription: {e}")
            raise
