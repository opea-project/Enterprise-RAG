# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

"""
Audio test helper classes extracted from UI test files.

Provides reusable utilities for audio UI testing:
- AudioArtifactCollector: Saves audio files on test failure for debugging
- VirtualMicAudioPlayer: PulseAudio virtual microphone for voice input testing
- TranscriptionAccuracyEvaluator: Evaluates ASR transcription quality
- UnifiedAudioInput: Orchestrates audio input via PulseAudio virtual mic
- PulseAudioOutputCapture: Captures audio output for TTS verification
"""

import atexit
import io
import logging
import os
import re
import struct
import subprocess  # nosec B404 - subprocess used for audio system tools (pactl, parec, paplay)
import tempfile
import wave
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Callable, List, Optional, Tuple

import allure

if TYPE_CHECKING:
    from tests.e2e.helpers.ui_helper import AudioChatUIHelper

from tests.e2e.helpers.audioqa_api_helper import AudioData, SherpaTTS

logger = logging.getLogger(__name__)


def _find_project_root() -> Path:
    """Walk up from this file to find the project root (contains src/)."""
    current = Path(__file__).resolve().parent
    for _ in range(10):
        if (current / "src").is_dir():
            return current
        current = current.parent
    # Fallback to the traditional 5-level parent
    return Path(__file__).resolve().parent.parent.parent.parent.parent


AUDIO_ARTIFACTS_DIR = _find_project_root() / "test-results" / "audio"


# =============================================================================
# Audio Artifact Collector
# =============================================================================


class AudioArtifactCollector:
    """
    Collects and saves audio artifacts for test debugging.

    On test failure, saves:
    - Input audio (TTS-generated audio sent to the system)
    - Output audio (captured audio from playback, if available)

    Artifacts are attached to Allure reports and saved to disk.
    """

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._input_audio: Optional[AudioData] = None
        self._output_audio: Optional[bytes] = None
        self._output_path: Optional[Path] = None

        AUDIO_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    def collect_input_audio(self, audio_data: AudioData) -> None:
        self._input_audio = audio_data
        logger.debug(f"Collected input audio: {len(audio_data.audio_bytes)} bytes")

    def collect_output_audio(self, audio_bytes: bytes, source: str = "capture") -> None:
        self._output_audio = audio_bytes
        logger.debug(f"Collected output audio from {source}: {len(audio_bytes)} bytes")

    def save_artifacts(self, attach_to_allure: bool = True) -> dict:
        """Save collected audio artifacts to disk and optionally attach to Allure."""
        saved = {}

        if self._input_audio:
            input_path = AUDIO_ARTIFACTS_DIR / f"input_{self.test_name}_{self.timestamp}.wav"
            try:
                input_path.write_bytes(self._input_audio.audio_bytes)
                saved["input_audio"] = str(input_path)
                logger.info(f"Saved input audio artifact: {input_path}")

                if attach_to_allure:
                    allure.attach(
                        self._input_audio.audio_bytes,
                        name=f"Input Audio (TTS): {self.test_name}.wav",
                        attachment_type="audio/wav",
                        extension="wav",
                    )
            except Exception as e:
                logger.error(f"Failed to save input audio artifact: {e}")

        if self._output_audio:
            output_path = AUDIO_ARTIFACTS_DIR / f"output_{self.test_name}_{self.timestamp}.wav"
            try:
                output_path.write_bytes(self._output_audio)
                saved["output_audio"] = str(output_path)
                logger.info(f"Saved output audio artifact: {output_path}")

                if attach_to_allure:
                    allure.attach(
                        self._output_audio,
                        name=f"Output Audio (Captured): {self.test_name}.wav",
                        attachment_type="audio/wav",
                        extension="wav",
                    )
            except Exception as e:
                logger.error(f"Failed to save output audio artifact: {e}")

        if saved and attach_to_allure:
            summary = f"Audio Artifacts for Failed Test: {self.test_name}\n"
            summary += f"Timestamp: {self.timestamp}\n"
            summary += "-" * 50 + "\n"
            if "input_audio" in saved:
                summary += f"Input Audio (TTS sent to system): {saved['input_audio']}\n"
                if self._input_audio:
                    summary += f"  - Size: {len(self._input_audio.audio_bytes)} bytes\n"
                    summary += f"  - Text: {getattr(self._input_audio, 'text', 'N/A')}\n"
            if "output_audio" in saved:
                summary += f"Output Audio (Captured playback): {saved['output_audio']}\n"
                summary += f"  - Size: {len(self._output_audio)} bytes\n"

            allure.attach(
                summary,
                name="Audio Artifacts Summary",
                attachment_type=allure.attachment_type.TEXT,
            )

        return saved

    def cleanup_on_success(self) -> None:
        """Remove any temporary audio files if test passed."""
        pass

    @staticmethod
    def rotate_old_artifacts(keep_count: int = 10) -> None:
        """Remove old audio artifacts, keeping only the most recent ones."""
        try:
            if not AUDIO_ARTIFACTS_DIR.exists():
                return

            files = list(AUDIO_ARTIFACTS_DIR.glob("*.wav"))
            if len(files) <= keep_count:
                return

            files_sorted = sorted(files, key=lambda x: x.stat().st_mtime)
            files_to_remove = files_sorted[:-keep_count]

            for f in files_to_remove:
                try:
                    f.unlink(missing_ok=True)
                    logger.debug(f"Removed old audio artifact: {f.name}")
                except OSError:
                    pass

        except Exception as e:
            logger.warning(f"Failed to rotate audio artifacts: {e}")


# =============================================================================
# Virtual Microphone Audio Player (PulseAudio-based)
# =============================================================================


class VirtualMicAudioPlayer:
    """
    Plays audio to a PulseAudio virtual microphone source.

    Creates a virtual PulseAudio sink whose monitor acts as a mic source,
    then plays TTS audio to it. Audio is resampled to 16000 Hz for ASR.
    """

    TARGET_SAMPLE_RATE = 16000

    def __init__(self, sink_name: str = "test_virtual_mic"):
        self.sink_name = sink_name
        self.sink_id = None
        self.source_name = f"{sink_name}.monitor"
        self._setup_complete = False
        self._pending_processes = []

    def setup(self) -> bool:
        """Set up virtual microphone using PulseAudio null-sink at 16000 Hz for ASR."""
        try:
            result = subprocess.run(
                ["pactl", "list", "short", "sinks"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if self.sink_name in result.stdout:
                logger.info(f"Removing existing sink {self.sink_name} to set correct sample rate")
                self.cleanup()

            result = subprocess.run(
                [
                    "pactl",
                    "load-module",
                    "module-null-sink",
                    f"sink_name={self.sink_name}",
                    "sink_properties=device.description=TestVirtualMic",
                    f"rate={self.TARGET_SAMPLE_RATE}",
                    "channels=1",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode != 0:
                logger.error(f"Failed to create virtual sink: {result.stderr}")
                return False

            self.sink_id = result.stdout.strip()
            logger.info(
                f"Created virtual sink: {self.sink_name} at {self.TARGET_SAMPLE_RATE}Hz mono "
                f"(module ID: {self.sink_id})"
            )

            subprocess.run(
                ["pactl", "set-default-source", self.source_name],
                capture_output=True,
                timeout=5,
            )
            logger.info(f"Set default source to: {self.source_name}")

            self._setup_complete = True
            return True

        except subprocess.SubprocessError as e:
            logger.error(f"PulseAudio setup failed: {e}")
            return False

    def _resample_audio(self, audio_data: bytes) -> bytes:
        """Resample WAV audio to 16000 Hz mono for ASR compatibility."""
        try:
            with wave.open(io.BytesIO(audio_data), "rb") as wf:
                orig_rate = wf.getframerate()
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                n_frames = wf.getnframes()
                raw_data = wf.readframes(n_frames)

            needs_resample = orig_rate != self.TARGET_SAMPLE_RATE
            needs_mono = n_channels > 1

            if not needs_resample and not needs_mono:
                logger.debug(f"Audio already at {self.TARGET_SAMPLE_RATE} Hz mono, no conversion needed")
                return audio_data

            logger.info(f"Converting audio: {orig_rate}Hz {n_channels}ch -> {self.TARGET_SAMPLE_RATE}Hz mono")

            if sampwidth == 2:
                fmt = f"<{n_frames * n_channels}h"
                samples = list(struct.unpack(fmt, raw_data))
            elif sampwidth == 1:
                samples = [s - 128 for s in raw_data]
            else:
                logger.warning(f"Unsupported sample width {sampwidth}, skipping conversion")
                return audio_data

            if needs_mono:
                mono_samples = []
                for i in range(0, len(samples), n_channels):
                    avg = sum(samples[i : i + n_channels]) // n_channels
                    mono_samples.append(avg)
                samples = mono_samples
                n_frames = len(samples)

            if needs_resample:
                ratio = self.TARGET_SAMPLE_RATE / orig_rate
                new_n_frames = int(n_frames * ratio)
                resampled = []

                for i in range(new_n_frames):
                    orig_idx = i / ratio
                    idx_floor = int(orig_idx)
                    idx_ceil = min(idx_floor + 1, len(samples) - 1)
                    frac = orig_idx - idx_floor

                    val = samples[idx_floor] * (1 - frac) + samples[idx_ceil] * frac
                    # Clamp to int16 range to prevent overflow
                    resampled.append(max(-32768, min(32767, int(val))))

                samples = resampled

            output = io.BytesIO()
            with wave.open(output, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(sampwidth)
                wf.setframerate(self.TARGET_SAMPLE_RATE)

                if sampwidth == 2:
                    packed = struct.pack(f"<{len(samples)}h", *samples)
                else:
                    packed = bytes([s + 128 for s in samples])
                wf.writeframes(packed)

            return output.getvalue()

        except Exception as e:
            logger.warning(f"Resampling failed: {e}, using original audio")
            return audio_data

    def play_audio(self, audio_data: bytes, wait: bool = True) -> bool:
        """Play audio to the virtual microphone (resampled to 16000 Hz)."""
        if not self._setup_complete:
            logger.warning("Virtual mic not set up, calling setup()")
            if not self.setup():
                return False

        try:
            audio_data = self._resample_audio(audio_data)

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name

            duration = 0
            try:
                with wave.open(temp_path, "rb") as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    duration = frames / rate
            except Exception:
                duration = 3.0

            cmd = ["paplay", f"--device={self.sink_name}", temp_path]

            if wait:
                try:
                    result = subprocess.run(cmd, capture_output=True, timeout=duration + 5)
                    if result.returncode != 0:
                        logger.error(f"paplay failed: {result.stderr}")
                        return False
                    logger.info(f"Played {duration:.1f}s audio to virtual mic")
                    return True
                finally:
                    try:
                        os.unlink(temp_path)
                    except OSError:
                        pass
            else:
                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self._pending_processes.append((proc, temp_path))
                logger.info(f"Started playing {duration:.1f}s audio to virtual mic (background, pid={proc.pid})")
                return True

        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            return False

    def speak(self, text: str, tts: "SherpaTTS" = None, speed: float = 1.0, wait: bool = True) -> bool:
        """Generate and play TTS audio."""
        if tts is None:
            logger.error("TTS not provided for speak()")
            return False

        audio_data = tts.generate(text, speed=speed)
        return self.play_audio(audio_data.audio_bytes, wait=wait)

    def cleanup(self):
        """Remove virtual audio devices and terminate pending background processes."""
        for proc, temp_path in self._pending_processes:
            try:
                if proc.poll() is None:
                    proc.terminate()
                    proc.wait(timeout=2)
                    logger.debug(f"Terminated background paplay process (pid={proc.pid})")
            except Exception as e:
                logger.warning(f"Failed to terminate paplay process: {e}")
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except Exception:
                pass
        self._pending_processes.clear()

        if self.sink_id:
            try:
                subprocess.run(
                    ["pactl", "unload-module", self.sink_id],
                    capture_output=True,
                    timeout=5,
                )
                logger.info(f"Removed virtual sink module: {self.sink_id}")
            except subprocess.SubprocessError as e:
                logger.warning(f"Failed to cleanup virtual sink: {e}")
            self.sink_id = None
        self._setup_complete = False

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


# =============================================================================
# Transcription Accuracy Evaluator
# =============================================================================


class TranscriptionAccuracyEvaluator:
    """
    Evaluates transcription accuracy by comparing original text with transcribed text.

    Uses word-level accuracy, keyword matching, and a combined weighted score.
    """

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for comparison (lowercase, remove punctuation)."""
        text = text.lower().strip()
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text

    @staticmethod
    def get_words(text: str) -> List[str]:
        """Extract words from text."""
        return TranscriptionAccuracyEvaluator.normalize_text(text).split()

    @classmethod
    def calculate_word_accuracy(cls, original: str, transcribed: str) -> float:
        """Calculate word-level accuracy (1 - WER approximation)."""
        orig_words = cls.get_words(original)
        trans_words = cls.get_words(transcribed)

        if not orig_words:
            return 1.0 if not trans_words else 0.0
        if not trans_words:
            return 0.0

        orig_set = set(orig_words)
        trans_set = set(trans_words)
        correct = len(orig_set & trans_set)

        return correct / len(orig_set)

    @classmethod
    def calculate_keyword_match(cls, original: str, transcribed: str, keywords: List[str] = None) -> float:
        """Calculate keyword matching accuracy."""
        trans_lower = transcribed.lower()

        if keywords:
            found = sum(1 for kw in keywords if kw.lower() in trans_lower)
            return found / len(keywords) if keywords else 0.0
        else:
            stop_words = {
                "the",
                "is",
                "are",
                "was",
                "were",
                "what",
                "how",
                "why",
                "a",
                "an",
                "and",
                "or",
                "in",
                "on",
                "at",
                "to",
                "for",
                "of",
            }
            orig_words = cls.get_words(original)
            key_words = [w for w in orig_words if w not in stop_words and len(w) > 2]

            if not key_words:
                return 1.0

            found = sum(1 for w in key_words if w in trans_lower)
            return found / len(key_words)

    @classmethod
    def evaluate_transcription(
        cls,
        original: str,
        transcribed: str,
        keywords: List[str] = None,
        min_accuracy: float = 0.7,
    ) -> Tuple[bool, dict]:
        """
        Comprehensive transcription evaluation.

        Returns:
            Tuple of (passed: bool, metrics: dict)
        """
        word_accuracy = cls.calculate_word_accuracy(original, transcribed)
        keyword_match = cls.calculate_keyword_match(original, transcribed, keywords)
        combined_score = (word_accuracy * 0.6) + (keyword_match * 0.4)

        metrics = {
            "original_text": original,
            "transcribed_text": transcribed,
            "word_accuracy": word_accuracy,
            "keyword_match": keyword_match,
            "combined_score": combined_score,
            "min_accuracy": min_accuracy,
            "passed": combined_score >= min_accuracy,
        }

        logger.info(
            f"Transcription evaluation: word_accuracy={word_accuracy:.2f}, "
            f"keyword_match={keyword_match:.2f}, combined={combined_score:.2f}"
        )

        return metrics["passed"], metrics


# =============================================================================
# Unified Audio Input Provider
# =============================================================================


class UnifiedAudioInput:
    """
    PulseAudio-based audio input provider for realistic UI testing.

    Uses PulseAudio virtual microphone to play TTS audio that the browser
    captures via the real microphone API, then sends to real ASR.
    """

    def __init__(
        self,
        audio_helper: "AudioChatUIHelper",
        tts: SherpaTTS,
        virtual_mic_player: "VirtualMicAudioPlayer",
        audio_artifacts_collector: Optional[Callable] = None,
    ):
        self.helper = audio_helper
        self.tts = tts
        self.virtual_mic_player = virtual_mic_player
        self.artifacts_collector = audio_artifacts_collector

        logger.info("UnifiedAudioInput initialized with PulseAudio")

    @property
    def method_name(self) -> str:
        return "PulseAudio Virtual Mic"

    async def setup_audio(
        self,
        text: str,
        speed: float = 1.0,
        expected_transcription: str = None,
    ) -> AudioData:
        """Generate audio for the test."""
        audio_data = self.tts.generate(text, speed=speed)

        if self.artifacts_collector:
            self.artifacts_collector(audio_data=audio_data)

        logger.info(f"PulseAudio mode - audio ready: {text[:50]}...")
        return audio_data

    async def play_during_recording(
        self,
        audio_data: AudioData = None,
        text: str = None,
        speed: float = 1.0,
        wait: bool = True,
    ):
        """Play audio while recording is active via PulseAudio virtual microphone."""
        if text and not audio_data:
            self.virtual_mic_player.speak(text, tts=self.tts, speed=speed, wait=wait)
        elif audio_data:
            self.virtual_mic_player.play_audio(audio_data.audio_bytes, wait=wait)
        logger.info("Audio playing through PulseAudio virtual mic")

    async def cleanup(self):
        """Clean up resources (no-op for PulseAudio, cleanup handled by fixture)."""
        pass


# =============================================================================
# PulseAudio Output Capture (for TTS verification)
# =============================================================================

# Track all active capture processes for atexit cleanup
_active_captures: list = []


def _cleanup_captures():
    """Safety net: kill any orphaned parec processes at exit."""
    for capture in _active_captures:
        if capture._process and capture._process.poll() is None:
            try:
                capture._process.terminate()
                capture._process.wait(timeout=2)
            except Exception:
                pass


atexit.register(_cleanup_captures)


class PulseAudioOutputCapture:
    """
    Captures audio output from PulseAudio default sink.

    Uses parec to record audio playing through the system's audio output,
    allowing verification that TTS audio is actually played and audible.
    """

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self._process = None
        self._temp_file = None
        self._monitor_source = None

    def _get_default_sink_monitor(self) -> Optional[str]:
        """Get the monitor source for the default audio sink."""
        try:
            result = subprocess.run(
                ["pactl", "get-default-sink"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                logger.warning(f"Failed to get default sink: {result.stderr}")
                return None

            default_sink = result.stdout.strip()
            monitor_source = f"{default_sink}.monitor"
            logger.info(f"Using monitor source: {monitor_source}")
            return monitor_source

        except Exception as e:
            logger.error(f"Failed to get sink monitor: {e}")
            return None

    def start(self) -> bool:
        """Start capturing audio output."""
        try:
            self._monitor_source = self._get_default_sink_monitor()
            if not self._monitor_source:
                logger.error("Could not find audio monitor source")
                return False

            self._temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            self._temp_file.close()

            cmd = [
                "parec",
                f"--device={self._monitor_source}",
                "--file-format=wav",
                f"--rate={self.sample_rate}",
                f"--channels={self.channels}",
                self._temp_file.name,
            ]

            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            _active_captures.append(self)

            logger.info(f"Started audio capture to {self._temp_file.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}")
            return False

    def stop(self) -> Optional[bytes]:
        """Stop capturing and return audio bytes."""
        if not self._process:
            logger.warning("No capture process running")
            return None

        try:
            self._process.terminate()
            self._process.wait(timeout=5)

            if os.path.exists(self._temp_file.name):
                with open(self._temp_file.name, "rb") as f:
                    audio_bytes = f.read()

                try:
                    with wave.open(self._temp_file.name, "rb") as wf:
                        frames = wf.getnframes()
                        rate = wf.getframerate()
                        duration = frames / rate
                        logger.info(f"Captured {duration:.2f}s of audio ({len(audio_bytes)} bytes)")
                except Exception:
                    pass

                os.unlink(self._temp_file.name)

                return audio_bytes
            else:
                logger.error("Capture file not found")
                return None

        except Exception as e:
            logger.error(f"Failed to stop audio capture: {e}")
            return None
        finally:
            self._process = None
            self._temp_file = None
            if self in _active_captures:
                _active_captures.remove(self)

    def is_available(self) -> bool:
        """Check if PulseAudio capture is available."""
        try:
            result = subprocess.run(["pactl", "info"], capture_output=True, timeout=5)
            return result.returncode == 0
        except Exception:
            return False


def pulseaudio_available() -> bool:
    """Check if PulseAudio is available for testing."""
    try:
        result = subprocess.run(["pactl", "info"], capture_output=True, timeout=5)
        available = result.returncode == 0
        if not available:
            logger.warning(f"pactl returned non-zero: {result.returncode}, stderr: {result.stderr}")
        else:
            logger.info("PulseAudio is available")
        return available
    except (FileNotFoundError, subprocess.SubprocessError) as e:
        logger.warning(f"PulseAudio check failed: {e}")
        return False
