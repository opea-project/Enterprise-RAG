# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import aiohttp
import asyncio
import json
import requests

from typing import AsyncIterator, List, Union, Optional
from fastapi import Request
from fastapi.responses import Response, StreamingResponse

from comps import get_opea_logger
from comps.cores.proto.api_protocol import AudioSpeechRequest
from comps.cores.mega.cancellation_wrapper import maybe_cancel_on_disconnect
from comps.tts.utils.sentence_splitter import SentenceAwareTextSplitter

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

SUPPORTED_MEDIA_FORMATS = ["mp3", "wav"]
CHUNK_SIZE = 128
PARALLEL_BATCH_SIZE = 4

class OPEATTS:
    def __init__(
        self,
        model_server: str,
        model_server_endpoint: str
    ):
        """
        Initialize the OPEATTS instance with the given parameters.

        :param model_server: Server hosting the TTS model (e.g., "fastapi").
        :param model_server_endpoint: Endpoint for the TTS model server.

        Raises:
            ValueError: If any of the required parameters are missing or empty.
        """
        self._model_server = model_server
        self._model_server_endpoint = model_server_endpoint
        if not self._model_server_endpoint.endswith("/v1"):
            self._model_server_endpoint = self._model_server_endpoint.rstrip("/") + "/v1"

        self._validate_config()
        self._validate_model_server()

        logger.info(
            f"OPEA TTS Microservice is configured to send requests to service {self._model_server_endpoint}"
        )

    def _validate_config(self) -> None:
        """Validate the configuration values."""
        try:
            if not self._model_server_endpoint:
                raise ValueError("The 'TTS_MODEL_SERVER_ENDPOINT' cannot be empty.")
            if not self._model_server:
                raise ValueError("The 'TTS_MODEL_SERVER' cannot be empty.")

            if self._model_server.lower() != "fastapi":
                raise ValueError(f"Unsupported TTS model server '{self._model_server}'. Currently only 'fastapi' is supported.")
        except Exception as e:
            logger.exception(f"Configuration validation error: {e}")
            raise

    def _validate_model_server(self, timeout_sec: int = 30) -> None:
        """
        Validate that the TTS model server is reachable and functional by
        sending a test request to /v1/audio/speech.
        """
        try:
            payload = {
                "input": "test",
                "voice": "default",
                "response_format": "mp3"
            }

            resp = requests.post(
                f"{self._model_server_endpoint}/audio/speech",
                json=payload,
                timeout=timeout_sec
            )
            resp.raise_for_status()

            if len(resp.content) == 0:
                raise ValueError("TTS server returned empty response")

        except requests.RequestException as e:
            logger.error(f"Failed to connect to TTS model server at {self._model_server_endpoint}: {e}. " \
                "Check if the TTS model server is running and accessible.")
            raise ConnectionError(f"Failed to connect to TTS model server at {self._model_server_endpoint}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during TTS endpoint validation: {e}")
            raise

        logger.info("OPEATTS model server connection validated successfully.")

    def _merge_wav_files(self, wav_chunks: List[bytes]) -> bytes:
        """
        Properly merge multiple WAV files by combining their audio data.
        This removes intermediate headers and creates a single valid WAV file.

        WAV file structure:
        - RIFF header (12 bytes): 'RIFF' + file_size + 'WAVE'
        - fmt chunk: format information
        - data chunk: 'data' + data_size + actual audio data

        Args:
            wav_chunks: List of WAV file bytes to merge

        Returns:
            Merged WAV file as bytes
        """
        if not wav_chunks:
            return b''

        if len(wav_chunks) == 1:
            return wav_chunks[0]

        logger.debug(f"Merging {len(wav_chunks)} WAV files")

        # Parse the first WAV file to get format info
        first_wav = wav_chunks[0]

        if first_wav[:4] != b'RIFF' or first_wav[8:12] != b'WAVE':
            logger.error("Invalid WAV file format detected, falling back to simple concatenation")
            return b''.join(wav_chunks)

        # Find the 'data' chunk in the first file
        data_start = first_wav.find(b'data')
        if data_start == -1:
            logger.error("Could not find data chunk in WAV file, falling back to simple concatenation")
            return b''.join(wav_chunks)

        # Get the header (everything before audio data)
        # data_start + 4 bytes for 'data' + 4 bytes for size
        header = first_wav[:data_start + 8]

        # Extract audio data from all chunks (skip headers)
        all_audio_data = b''
        for i, wav_chunk in enumerate(wav_chunks):
            chunk_data_start = wav_chunk.find(b'data')
            if chunk_data_start == -1:
                logger.warning(f"Could not find data chunk in WAV chunk {i+1}, skipping")
                continue
            # Skip 'data' (4 bytes) and size (4 bytes)
            audio_data_start = chunk_data_start + 8
            chunk_audio = wav_chunk[audio_data_start:]
            all_audio_data += chunk_audio
            logger.debug(f"Extracted {len(chunk_audio)} bytes from chunk {i+1}")

        # Update the size fields in the header
        total_size = len(all_audio_data) + len(header) - 8  # -8 for RIFF header
        data_size = len(all_audio_data)

        # Build the new WAV file
        merged_wav = bytearray(header)

        # Update RIFF chunk size (bytes 4-7)
        merged_wav[4:8] = total_size.to_bytes(4, byteorder='little')

        # Update data chunk size (at data_start + 4)
        data_size_pos = data_start + 4
        merged_wav[data_size_pos:data_size_pos + 4] = data_size.to_bytes(4, byteorder='little')

        merged_wav += all_audio_data

        logger.debug(f"Successfully merged WAV files: {len(merged_wav)} total bytes")

        return bytes(merged_wav)

    async def generate_speech(
        self,
        text: str,
        voice: str = "default",
        instructions: str = None,
        response_format: str = "mp3"
    ) -> bytes:
        """
        Generate speech from text using the TTS model server.

        :param text: The text to convert to speech
        :param voice: Voice to use for synthesis
        :param instructions: Optional instructions for voice style
        :param response_format: Audio format (mp3, wav)
        :return: Audio bytes
        """
        logger.info(f"Generating speech for text (length={len(text)}), voice={voice}, format={response_format}")

        payload = {
            "input": text,
            "voice": voice,
            "response_format": response_format
        }

        if instructions:
            payload["instructions"] = instructions

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self._model_server_endpoint}/audio/speech",
                    data=json.dumps(payload),
                    headers={"Content-Type": "application/json"},
                    timeout=120
                ) as response:
                    if response.status >= 400:
                        error_text = await response.text()

                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=json.loads(error_text)["detail"],
                            headers=response.headers
                        )

                    response_content = await response.read()

            logger.info(f"Successfully generated speech, size={len(response_content)} bytes")
            return response_content

        except aiohttp.ClientResponseError as e:
            logger.error(f"ClientResponseError with status code {e.status} occurred while generating speech: {e.message}")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Connection error while generating speech: {e}")
            raise
        except Exception as e:
            logger.error(f"Unknown error occurred while generating speech: {e}")
            raise

    async def generate_speech_for_chunks(
        self,
        text_chunks: List[str],
        voice: str = "default",
        instructions: str = None,
        response_format: str = "mp3"
    ) -> AsyncIterator[bytes]:
        """
        Generate speech for multiple text chunks and yield audio bytes in order.
        Processes chunks in parallel batches of PARALLEL_BATCH_SIZE to improve performance
        while maintaining correct order.

        :param text_chunks: List of text chunks to convert to speech
        :param voice: Voice to use for synthesis
        :param instructions: Optional instructions for voice style
        :param response_format: Audio format (mp3, wav, etc.)
        :yield: Audio bytes for each chunk in the original order
        """
        logger.info(f"Generating speech for {len(text_chunks)} chunks with batch size {PARALLEL_BATCH_SIZE}")

        # Process chunks in batches
        for batch_start in range(0, len(text_chunks), PARALLEL_BATCH_SIZE):
            batch_end = min(batch_start + PARALLEL_BATCH_SIZE, len(text_chunks))
            batch_chunks = text_chunks[batch_start:batch_end]

            logger.info(f"Processing batch {batch_start//PARALLEL_BATCH_SIZE + 1}: chunks {batch_start+1} to {batch_end}")

            # Create tasks for parallel processing - all start immediately
            tasks = []
            for i, chunk in enumerate(batch_chunks):
                chunk_idx = batch_start + i
                logger.debug(f"Creating task for chunk {chunk_idx+1}/{len(text_chunks)} (length={len(chunk)})")

                task = asyncio.create_task(self.generate_speech(
                    text=chunk,
                    voice=voice,
                    instructions=instructions,
                    response_format=response_format
                ))
                tasks.append(task)

            # Await and yield results in order (tasks run in parallel, but we yield sequentially)
            for i, task in enumerate(tasks):
                chunk_idx = batch_start + i
                audio_bytes = await task
                logger.debug(f"Yielding audio for chunk {chunk_idx+1}/{len(text_chunks)} (size={len(audio_bytes)} bytes)")
                yield audio_bytes

    async def run(self, request: AudioSpeechRequest, raw_request: Optional[Request] = None) -> Union[Response, StreamingResponse]:
        """
        Main entry point for TTS processing. Handles the complete TTS workflow including
        text splitting, audio generation, and streaming.

        Args:
            request: AudioSpeechRequest
            raw_request: Optional FastAPI Request for cancellation monitoring

        Returns:
            Response or StreamingResponse: Complete audio when streaming=False, streamed audio when streaming=True.
        """
        input_text = request.input
        voice = request.voice.lower() or "default"
        response_format = request.response_format.lower() or "mp3"
        streaming = request.streaming or False
        instructions = request.instructions or None

        logger.info(f"Received TTS request: text_length={len(input_text)}, voice={voice}, format={response_format}, streaming={streaming}")
        logger.info(input_text)

        if response_format not in SUPPORTED_MEDIA_FORMATS:
            raise ValueError(f"Unsupported media format '{response_format}'. Supported formats are: {', '.join(SUPPORTED_MEDIA_FORMATS)}")
        media_type = f"audio/{response_format}" if response_format != "mp3" else "audio/mpeg"

        if len(input_text) <= CHUNK_SIZE:
            audio_bytes = await self.generate_speech(
                text=input_text,
                voice=voice,
                instructions=instructions,
                response_format=response_format
            )

            if streaming:
                return StreamingResponse(
                    iter([audio_bytes]),
                    media_type=media_type,
                    headers={
                        "Content-Disposition": f"inline; filename=speech.{response_format}"
                    }
                )
            else:
                return Response(
                    content=audio_bytes,
                    media_type=media_type,
                    headers={
                        "Content-Disposition": f"inline; filename=speech.{response_format}"
                    }
                )

        else:
            text_splitter = SentenceAwareTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=0)
            text_chunks = text_splitter.split_text(input_text)
            logger.info(f"Split text into {len(text_chunks)} chunks")
            logger.info(f"Chunks: {text_chunks}")

            if not streaming:
                async with maybe_cancel_on_disconnect(raw_request):
                    audio_chunks = []
                    async for audio_bytes in self.generate_speech_for_chunks(
                        text_chunks=text_chunks,
                        voice=voice,
                        instructions=instructions,
                        response_format=response_format
                    ):
                        audio_chunks.append(audio_bytes)

                # For WAV files, we need to properly merge them to avoid header issues
                if response_format == "wav":
                    combined_audio = self._merge_wav_files(audio_chunks)
                else:
                    combined_audio = b''.join(audio_chunks)

                return Response(
                    content=combined_audio,
                    media_type=media_type,
                    headers={
                        "Content-Disposition": f"inline; filename=speech.{response_format}"
                    }
                )
            else:
                async def audio_stream():
                    async with maybe_cancel_on_disconnect(raw_request):
                        async for audio_bytes in self.generate_speech_for_chunks(
                            text_chunks=text_chunks,
                            voice=voice,
                            instructions=instructions,
                            response_format=response_format
                        ):
                            yield audio_bytes
                        yield b''

                return StreamingResponse(
                    audio_stream(),
                    media_type=media_type,
                    headers={
                        "Content-Disposition": f"inline; filename=speech.{response_format}"
                    }
                )
