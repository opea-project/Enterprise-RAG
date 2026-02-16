#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
import io
import logging
import os
from pydub import AudioSegment
import requests
import secrets
import sherpa_onnx
import struct
import tarfile
import time
import wave
from dataclasses import dataclass
from pathlib import Path

from tests.e2e.helpers.api_request_helper import ApiRequestHelper, ApiResponse
from tests.e2e.validation.buildcfg import cfg
from tests.e2e.validation.constants import AUDIO_OUTPUT_FILES_DIR, TEST_AUDIO_DIR

logger = logging.getLogger(__name__)

MODELS_DIR = Path(AUDIO_OUTPUT_FILES_DIR)
MODELS_BASE_URL = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models"


@dataclass
class VoiceModel:
    """Voice model configuration."""
    name: str
    language: str
    gender: str
    description: str

    @property
    def tar_url(self) -> str:
        return f"{MODELS_BASE_URL}/{self.name}.tar.bz2"


@dataclass
class AudioData:
    """Generated audio container."""
    audio_bytes: bytes
    voice: str
    sample_rate: int = 22050
    format: str = "wav"
    _filename: str = None

    @property
    def filename(self):
        if self._filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            self._filename = f"sherpa_{self.voice}_{timestamp}.{self.format}"
        return self._filename

    @property
    def filepath(self):
        return os.path.join(AUDIO_OUTPUT_FILES_DIR, self.filename)


VOICES: dict[str, VoiceModel] = {
    # https://huggingface.co/csukuangfj/vits-piper-en_US-joe-medium/blob/main/MODEL_CARD
    "en_male_joe": VoiceModel("vits-piper-en_US-joe-medium", "en", "male", "Joe - US male"),
    # https://huggingface.co/csukuangfj/vits-piper-en_US-ljspeech-medium/blob/main/MODEL_CARD
    "en_female": VoiceModel("vits-piper-en_US-ljspeech-medium", "en", "female", "US female"),
    # https://huggingface.co/csukuangfj/vits-piper-en_US-kusal-medium/blob/main/MODEL_CARD
    "en_male_kusal": VoiceModel("vits-piper-en_US-kusal-medium", "en", "female", "US male"),
    #https://huggingface.co/csukuangfj/vits-piper-en_US-bryce-medium/blob/main/MODEL_CARD
    "en_male_bryce": VoiceModel("vits-piper-en_US-bryce-medium", "en", "male", "US male Bryce"),
}


class SherpaTTS:
    """
    Text-to-Speech provider using sherpa-onnx.
    """

    def __init__(self,):
        self.models_dir = MODELS_DIR
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._engines = {}

    def generate(self, text: str, voice_key: str = "en_male_joe", speed: float = 1.0, format="wav") -> AudioData:
        """Generate audio from text."""
        engine = self._get_engine(voice_key)

        audio = engine.generate(text, speed=speed)
        if format == "wav":
            audio_bytes = self._to_wav(audio.samples, audio.sample_rate)
        elif format == "mp3":
            audio_bytes = self._to_mp3(audio.samples, audio.sample_rate)
        else:
            raise ValueError(f"Unsupported audio format: {format}")

        return AudioData(
            audio_bytes=audio_bytes,
            voice=voice_key,
            sample_rate=audio.sample_rate,
            format=format
        )

    def save(self, audio_data: AudioData) -> Path:
        """
        Save the generated AudioData to a physical file.

        Returns:
            Path: The path to the saved .wav file.
        """
        directory = Path(AUDIO_OUTPUT_FILES_DIR)
        directory.mkdir(parents=True, exist_ok=True)

        file_path = directory / audio_data.filename

        try:
            file_path.write_bytes(audio_data.audio_bytes)
            logger.info(f"Audio file saved successfully: {file_path}")
        except Exception as e:
            logger.error(f"Failed to save audio file {file_path}: {e}")
            raise

        return file_path

    def _get_engine(self, voice_key: str):
        """Get or create TTS engine for voice."""
        if voice_key in self._engines:
            return self._engines[voice_key]

        model = VOICES.get(voice_key)
        if not model:
            raise ValueError(f"Unknown voice: {voice_key}. Available: {list(VOICES.keys())}")

        model_dir = self.models_dir / model.name
        if not model_dir.exists():
            self._download(voice_key)

        onnx_file = next(model_dir.glob("*.onnx"), None)
        if not onnx_file:
            raise FileNotFoundError(f"No .onnx file in {model_dir}")

        config = sherpa_onnx.OfflineTtsConfig(
            model=sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                    model=str(onnx_file),
                    tokens=str(model_dir / "tokens.txt"),
                    data_dir=str(model_dir / "espeak-ng-data"),
                ),
                provider="cpu",
                num_threads=4,
            ),
        )

        self._engines[voice_key] = sherpa_onnx.OfflineTts(config)
        return self._engines[voice_key]

    def _download(self, voice_key: str):
        """Download voice model"""
        model = VOICES[voice_key]
        tar_path = self.models_dir / f"{model.name}.tar.bz2"

        logger.info(f"Downloading {model.name} from {model.tar_url}...")
        try:
            with requests.get(model.tar_url, stream=True, verify=False) as r:
                r.raise_for_status()
                with open(tar_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            with tarfile.open(tar_path, "r:bz2") as tar:
                tar.extractall(self.models_dir)
        except Exception as e:
            logger.error(f"Failed to download or extract model: {e}")
            raise
        finally:
            if tar_path.exists():
                tar_path.unlink()

    @staticmethod
    def _to_wav(samples: list, sample_rate: int) -> bytes:
        """Convert samples to WAV bytes."""
        int_samples = [max(-32768, min(32767, int(s * 32767))) for s in samples]

        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(struct.pack(f'{len(int_samples)}h', *int_samples))

        return buffer.getvalue()

    @staticmethod
    def _to_mp3(samples: list, sample_rate: int) -> bytes:
        """Convert samples to MP3 bytes"""
        int_samples = [max(-32768, min(32767, int(s * 32767))) for s in samples]
        pcm_data = struct.pack(f'{len(int_samples)}h', *int_samples)

        audio = AudioSegment(
            data=pcm_data,
            sample_width=2,
            frame_rate=sample_rate,
            channels=1
        )

        buffer = io.BytesIO()

        # Temporarily disable pydub logging to avoid cluttering test output with ffmpeg logs
        logging.disable(logging.INFO)
        try:
            audio.export(buffer, format="mp3", bitrate="128k")
        finally:
            logging.disable(logging.NOTSET)

        return buffer.getvalue()


class AudioApiHelper(ApiRequestHelper):

    def __init__(self, keycloak_helper):
        super().__init__(keycloak_helper=keycloak_helper)
        self.asr_api_path = f"https://{cfg.get('FQDN')}/v1/audio/transcriptions"
        self.tts_api_path = f"https://{cfg.get('FQDN')}/v1/audio/speech"
        self.tts = SherpaTTS()

    def generate_audio(self, text: str, voice_key: str = "en_male_joe", speed: float = 1.0, format="wav") -> AudioData:
        """Generate audio bytes from text using SherpaTTS."""
        audio_data = self.tts.generate(text, voice_key=voice_key, speed=speed, format=format)
        self.tts.save(audio_data)
        return audio_data

    def transcribe_audio(self, audio_data, language="en", response_format="json", model=None, as_user=False):
        """Send AudioData container to ASR service for transcription"""
        files = {
            "file": (audio_data.filename, audio_data.audio_bytes, "audio/wav")
        }

        data = {
            "language": language,
            "response_format": response_format,
            "model": model
        }

        headers = self.get_headers(as_user).copy()
        headers.pop("Content-Type", None)

        logger.debug("Requesting to make a transcription API call")
        start_time = time.time()
        response = requests.post(
            url=self.asr_api_path,
            headers=headers,
            files=files,
            data=data,
            verify=False
        )

        api_call_duration = round(time.time() - start_time, 2)
        logger.info(f"ASR API call duration: {api_call_duration}s")

        return ApiResponse(response, api_call_duration)

    def get_transcription_text(self, response: ApiResponse) -> str:
        """Extract transcription text from ASR response."""
        if response.status_code != 200:
            raise ValueError(f"Invalid response status: {response.status_code}")

        try:
            return response.json().get("text", "")
        except Exception as e:
            raise ValueError(f"Failed to parse transcription response: {e}")

    def generate_real_words(self, count: int) -> str:
        """Helper to fetch a specific number of real words from the Linux dictionary"""
        dict_path = Path("/usr/share/dict/words")

        if not dict_path.exists():
            logger.warning("Linux dictionary not found, using fallback word list.")
            fallback_words = ["composite", "joist", "plank", "drill", "garden", "frame", "timber", "measurement"]
            return " ".join(secrets.choice(fallback_words) for _ in range(count))

        all_words = dict_path.read_text().splitlines()
        all_words = [w for w in all_words if len(w) > 1]

        selected_words = []
        for _ in range(count):
            selected_words.append(secrets.choice(all_words))

        return " ".join(selected_words)

    def load_audio_from_file(self, file_path: str) -> AudioData:
        """Load audio bytes from a file into an AudioData container."""
        audio_dir = Path(TEST_AUDIO_DIR)
        file_path = audio_dir / file_path

        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        audio_bytes = file_path.read_bytes()
        return AudioData(
            audio_bytes=audio_bytes,
            voice="unknown",
            sample_rate=22050,
            format=file_path.suffix[1:],
            _filename=file_path.name
        )

    def text_to_speech(self, text: str, as_user=False):
        """
        Call the text-to-speech API with the given text.

        Args:
            text: The input text to convert to speech
            as_user: Whether to make the request as a user

        Returns:
            ApiResponse containing the MP3 audio data
        """
        headers = self.get_headers(as_user)

        payload = {
            "input": text
        }

        logger.debug(f"Requesting text-to-speech API call with text: '{text}'")
        start_time = time.time()
        response = requests.post(
            url=self.tts_api_path,
            headers=headers,
            json=payload,
            verify=False
        )

        api_call_duration = round(time.time() - start_time, 2)
        logger.info(f"TTS API call duration: {api_call_duration}s")

        return ApiResponse(response, api_call_duration)

    def text_to_speech_audio(self, input_text: str, filename: str, as_user: bool = False) -> AudioData:
        """
        Call TTS API and return the audio as AudioData container.

        Args:
            input_text: The text to convert to speech
            filename: The filename to save the MP3 as
            as_user: If True, call TTS API as a regular user instead of admin

        Returns:
            AudioData container with the MP3 audio
        """
        logger.info(f"Calling TTS with input (length: {len(input_text)} chars){' as user' if as_user else ''}")
        tts_response = self.text_to_speech(input_text, as_user=as_user)
        assert tts_response.status_code == 200, f"TTS API call failed: {tts_response.text}"

        # Get the MP3 audio data from response
        mp3_audio_bytes = tts_response.content
        assert len(mp3_audio_bytes) > 0, "TTS API returned empty audio data"
        size_in_mb = len(mp3_audio_bytes) / (1024 * 1024)
        logger.info(f"TTS API returned {size_in_mb:.2f} MB of MP3 audio")

        audio_data = AudioData(
            audio_bytes=mp3_audio_bytes,
            voice="tts_api",
            format="mp3",
            _filename=filename
        )

        # Save the MP3 file to disk
        saved_path = self.tts.save(audio_data)
        logger.info(f"Saved TTS output to: {saved_path}")

        return audio_data

    def transcribe_to_text(self, audio_data: AudioData, original_text: str = None) -> str:
        """
        Transcribe audio to text using ASR API.

        Args:
            audio_data: The audio data to transcribe
            original_text: Optional original text for comparison logging

        Returns:
            The transcribed text
        """
        logger.info("Transcribing audio using ASR API")
        asr_response = self.transcribe_audio(audio_data)
        assert asr_response.status_code == 200, f"ASR transcription failed: {asr_response.text}"

        transcription = self.get_transcription_text(asr_response).strip()

        if original_text is not None:
            logger.info(f"Original text: '{original_text}' | Transcribed text: '{transcription}'")
        else:
            logger.info(f"Transcribed text: '{transcription}'")

        return transcription
