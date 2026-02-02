#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime
import io
import logging
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
from tests.e2e.validation.constants import AUDIO_FILES_DIR

logger = logging.getLogger(__name__)

MODELS_DIR = Path(AUDIO_FILES_DIR)
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
    text: str
    voice: str
    sample_rate: int = 22050

    @property
    def filename(self) -> str:
        # Format: sherpa_en_male_joe_20260127_093056_123.wav
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        return f"sherpa_{self.voice}_{timestamp}.wav"


VOICES: dict[str, VoiceModel] = {
    # English US
    "en_male_joe": VoiceModel("vits-piper-en_US-joe-medium", "en", "male", "Joe - US male")
}


class SherpaTTS:
    """
    Text-to-Speech provider using sherpa-onnx.
    """

    def __init__(self,):
        self.models_dir = MODELS_DIR
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self._engines = {}

    def generate(self, text: str, voice_key: str = "en_male_joe", speed: float = 1.0) -> AudioData:
        """Generate audio from text."""
        engine = self._get_engine(voice_key)

        audio = engine.generate(text, speed=speed)
        wav_bytes = self._to_wav(audio.samples, audio.sample_rate)

        return AudioData(
            audio_bytes=wav_bytes,
            text=text,
            voice=voice_key,
            sample_rate=audio.sample_rate,
        )

    def save(self, audio_data: AudioData) -> Path:
        """
        Save the generated AudioData to a physical file.

        Returns:
            Path: The path to the saved .wav file.
        """
        directory = Path(AUDIO_FILES_DIR)
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


class AudioApiHelper(ApiRequestHelper):

    def __init__(self, keycloak_helper):
        super().__init__(keycloak_helper=keycloak_helper)
        self.asr_api_path = f"https://{cfg.get('FQDN')}/v1/audio/transcriptions"
        self.tts = SherpaTTS()

    def generate_audio(self, text: str,  speed: float = 1.0) -> AudioData:
        """Generate audio bytes from text using SherpaTTS."""
        audio_data = self.tts.generate(text, speed=speed)
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
