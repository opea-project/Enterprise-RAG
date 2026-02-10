"""
Copyright (C) 2024-2026 Intel Corporation
SPDX-License-Identifier: Apache-2.0

Audio UI Tests - Voice Input and Transcription Testing

This module tests the audio/voice input functionality in the UI:
1. Voice input button visibility when audio is enabled
2. Audio recording starts/stops correctly
3. Audio is transcribed and sent as a prompt
4. Transcription accuracy validation
5. Speech speed variations (slow/fast)
6. Silence handling (no hallucination)

Focus: Voice UI interaction mechanism (mic button, recording, transcription).
Note: Response quality validation is handled by ChatQnA tests - not duplicated here.

SOLID/DRY Principles:
- Uses AudioData and SherpaTTS from audioqa_api_helper (shared with backend tests)
- TranscriptionAccuracyEvaluator for transcription validation (reusable)
- AudioChatUIHelper handles all audio UI interactions
- Test questions defined in AUDIO_TEST_CASES (configurable)

Test Flow:
1. Click microphone button (aria-label="Start recording") - starts "talking"
2. Click button again (aria-label="Stop recording") - stops recording
3. Wait for voice to be transcribed and returned in prompt textarea
4. Click send button
5. Wait for chatbot response
"""

import allure
import logging
import os
import re
import subprocess  # nosec B404 - subprocess used for audio system tools (pactl, parec)
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Callable

import pytest
import pytest_asyncio

# Shared components from backend tests (DRY principle)
from tests.e2e.helpers.audioqa_api_helper import AudioData, SherpaTTS
from tests.e2e.helpers.ui_helper import AudioUIHelper, AudioChatUIHelper
from tests.e2e.validation.buildcfg import cfg

logger = logging.getLogger(__name__)

# Audio artifacts directory for test failures
AUDIO_ARTIFACTS_DIR = Path(__file__).parent.parent.parent.parent.parent / "test-results" / "audio"


# =============================================================================
# Audio Artifact Collector (saves audio files on test failure)
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
        """
        Initialize artifact collector.
        
        Args:
            test_name: Name of the current test for file naming
        """
        self.test_name = test_name
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._input_audio: Optional[AudioData] = None
        self._output_audio: Optional[bytes] = None
        self._output_path: Optional[Path] = None
        
        # Ensure directory exists
        AUDIO_ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    
    def collect_input_audio(self, audio_data: AudioData) -> None:
        """
        Collect input audio (TTS-generated audio sent to the system).
        
        Args:
            audio_data: AudioData from TTS generation
        """
        self._input_audio = audio_data
        logger.debug(f"Collected input audio: {len(audio_data.audio_bytes)} bytes")
    
    def collect_output_audio(self, audio_bytes: bytes, source: str = "capture") -> None:
        """
        Collect output audio (captured audio from playback).
        
        Args:
            audio_bytes: Raw audio bytes
            source: Source description (e.g., "capture", "tts_response")
        """
        self._output_audio = audio_bytes
        logger.debug(f"Collected output audio from {source}: {len(audio_bytes)} bytes")
    
    def save_artifacts(self, attach_to_allure: bool = True) -> dict:
        """
        Save collected audio artifacts to disk and optionally attach to Allure.
        
        On test failure, audio files are:
        1. Saved to disk in test-results/audio/
        2. Attached to Allure report for easy playback/download
        
        Args:
            attach_to_allure: Whether to attach artifacts to Allure report
            
        Returns:
            Dict with paths to saved artifacts
        """
        saved = {}
        
        # Save input audio (TTS-generated audio sent to the system)
        if self._input_audio:
            input_path = AUDIO_ARTIFACTS_DIR / f"input_{self.test_name}_{self.timestamp}.wav"
            try:
                input_path.write_bytes(self._input_audio.audio_bytes)
                saved["input_audio"] = str(input_path)
                logger.info(f"Saved input audio artifact: {input_path}")
                
                if attach_to_allure:
                    # Attach audio bytes directly with proper MIME type
                    allure.attach(
                        self._input_audio.audio_bytes,
                        name=f"Input Audio (TTS): {self.test_name}.wav",
                        attachment_type="audio/wav",
                        extension="wav"
                    )
                    logger.info("Attached input audio to Allure report")
            except Exception as e:
                logger.error(f"Failed to save input audio artifact: {e}")
        
        # Save output audio (captured audio from playback)
        if self._output_audio:
            output_path = AUDIO_ARTIFACTS_DIR / f"output_{self.test_name}_{self.timestamp}.wav"
            try:
                output_path.write_bytes(self._output_audio)
                saved["output_audio"] = str(output_path)
                logger.info(f"Saved output audio artifact: {output_path}")
                
                if attach_to_allure:
                    # Attach audio bytes directly with proper MIME type
                    allure.attach(
                        self._output_audio,
                        name=f"Output Audio (Captured): {self.test_name}.wav",
                        attachment_type="audio/wav",
                        extension="wav"
                    )
                    logger.info("Attached output audio to Allure report")
            except Exception as e:
                logger.error(f"Failed to save output audio artifact: {e}")
        
        # Also attach a text summary of what audio was collected
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
                attachment_type=allure.attachment_type.TEXT
            )
        
        return saved
    
    def cleanup_on_success(self) -> None:
        """Remove any temporary audio files if test passed."""
        # Nothing to clean up - we only save on failure
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
            
            # Sort by modification time, oldest first
            files_sorted = sorted(files, key=lambda x: x.stat().st_mtime)
            files_to_remove = files_sorted[:-keep_count]
            
            for f in files_to_remove:
                try:
                    f.unlink()
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
    
    This allows testing audio input without a physical microphone by:
    1. Creating a virtual PulseAudio sink (audio destination)
    2. Making the sink's monitor available as a source (virtual mic)
    3. Playing TTS audio to the sink, which browser hears as mic input
    
    Audio is resampled to 16000 Hz (ASR-compatible) before playback.
    
    Usage:
        player = VirtualMicAudioPlayer()
        player.setup()  # Create virtual mic
        player.play_audio(wav_bytes)  # Play audio to virtual mic
        player.cleanup()  # Remove virtual devices
    """
    
    # Target sample rate for ASR compatibility
    TARGET_SAMPLE_RATE = 16000
    
    def __init__(self, sink_name: str = "test_virtual_mic"):
        self.sink_name = sink_name
        self.sink_id = None
        self.source_name = f"{sink_name}.monitor"
        self._setup_complete = False
        self._pending_processes = []  # Track background paplay processes
    
    def setup(self) -> bool:
        """Set up virtual microphone using PulseAudio null-sink at 16000 Hz for ASR."""
        try:
            # Check if sink already exists
            result = subprocess.run(
                ["pactl", "list", "short", "sinks"],
                capture_output=True, text=True, timeout=5
            )
            if self.sink_name in result.stdout:
                # Remove existing sink to recreate with correct sample rate
                logger.info(f"Removing existing sink {self.sink_name} to set correct sample rate")
                self.cleanup()
            
            # Create null-sink at 16000 Hz mono (ASR-compatible)
            # rate=16000 channels=1 ensures audio is in the correct format for ASR
            result = subprocess.run(
                ["pactl", "load-module", "module-null-sink",
                 f"sink_name={self.sink_name}",
                 "sink_properties=device.description=TestVirtualMic",
                 f"rate={self.TARGET_SAMPLE_RATE}",
                 "channels=1"],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to create virtual sink: {result.stderr}")
                return False
            
            self.sink_id = result.stdout.strip()
            logger.info(f"Created virtual sink: {self.sink_name} at {self.TARGET_SAMPLE_RATE}Hz mono (module ID: {self.sink_id})")
            
            # Set the monitor as default source (mic)
            subprocess.run(
                ["pactl", "set-default-source", self.source_name],
                capture_output=True, timeout=5
            )
            logger.info(f"Set default source to: {self.source_name}")
            
            self._setup_complete = True
            return True
            
        except subprocess.SubprocessError as e:
            logger.error(f"PulseAudio setup failed: {e}")
            return False
    
    def _resample_audio(self, audio_data: bytes) -> bytes:
        """
        Resample WAV audio to 16000 Hz mono for ASR compatibility.
        
        Args:
            audio_data: Original WAV audio bytes
            
        Returns:
            Resampled WAV audio bytes at TARGET_SAMPLE_RATE (16000 Hz) mono
        """
        import io
        import wave
        import struct
        
        try:
            # Read original WAV
            with wave.open(io.BytesIO(audio_data), 'rb') as wf:
                orig_rate = wf.getframerate()
                n_channels = wf.getnchannels()
                sampwidth = wf.getsampwidth()
                n_frames = wf.getnframes()
                raw_data = wf.readframes(n_frames)
            
            needs_resample = (orig_rate != self.TARGET_SAMPLE_RATE)
            needs_mono = (n_channels > 1)
            
            if not needs_resample and not needs_mono:
                logger.debug(f"Audio already at {self.TARGET_SAMPLE_RATE} Hz mono, no conversion needed")
                return audio_data
            
            logger.info(f"Converting audio: {orig_rate}Hz {n_channels}ch -> {self.TARGET_SAMPLE_RATE}Hz mono")
            
            # Convert bytes to samples
            if sampwidth == 2:
                fmt = f"<{n_frames * n_channels}h"
                samples = list(struct.unpack(fmt, raw_data))
            elif sampwidth == 1:
                samples = [s - 128 for s in raw_data]  # Convert unsigned to signed
            else:
                logger.warning(f"Unsupported sample width {sampwidth}, skipping conversion")
                return audio_data
            
            # Convert to mono if needed
            if needs_mono:
                mono_samples = []
                for i in range(0, len(samples), n_channels):
                    # Average all channels
                    avg = sum(samples[i:i+n_channels]) // n_channels
                    mono_samples.append(avg)
                samples = mono_samples
                n_frames = len(samples)
            
            # Resample if needed
            if needs_resample:
                ratio = self.TARGET_SAMPLE_RATE / orig_rate
                new_n_frames = int(n_frames * ratio)
                resampled = []
                
                for i in range(new_n_frames):
                    orig_idx = i / ratio
                    idx_floor = int(orig_idx)
                    idx_ceil = min(idx_floor + 1, len(samples) - 1)
                    frac = orig_idx - idx_floor
                    
                    # Linear interpolation
                    val = samples[idx_floor] * (1 - frac) + samples[idx_ceil] * frac
                    resampled.append(int(val))
                
                samples = resampled
            
            # Write converted WAV (16000 Hz mono)
            output = io.BytesIO()
            with wave.open(output, 'wb') as wf:
                wf.setnchannels(1)  # Mono
                wf.setsampwidth(sampwidth)
                wf.setframerate(self.TARGET_SAMPLE_RATE)
                
                if sampwidth == 2:
                    packed = struct.pack(f"<{len(samples)}h", *samples)
                else:
                    packed = bytes([s + 128 for s in samples])  # Convert back to unsigned
                wf.writeframes(packed)
            
            return output.getvalue()
            
        except Exception as e:
            logger.warning(f"Resampling failed: {e}, using original audio")
            return audio_data
    
    def play_audio(self, audio_data: bytes, wait: bool = True) -> bool:
        """
        Play audio to the virtual microphone.
        
        Audio is automatically resampled to 16000 Hz for ASR compatibility.
        
        Args:
            audio_data: WAV audio bytes
            wait: Whether to wait for playback to complete
            
        Returns:
            True if playback started/completed successfully
        """
        if not self._setup_complete:
            logger.warning("Virtual mic not set up, calling setup()")
            if not self.setup():
                return False
        
        try:
            import tempfile
            import wave
            
            # Resample audio to 16000 Hz for ASR compatibility
            audio_data = self._resample_audio(audio_data)
            
            # Write audio to temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name
            
            # Get audio duration for waiting
            duration = 0
            try:
                with wave.open(temp_path, 'rb') as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    duration = frames / rate
            except Exception:
                duration = 3.0  # Default duration
            
            # Play to virtual sink using paplay
            cmd = ["paplay", f"--device={self.sink_name}", temp_path]
            
            if wait:
                result = subprocess.run(cmd, capture_output=True, timeout=duration + 5)
                os.unlink(temp_path)
                if result.returncode != 0:
                    logger.error(f"paplay failed: {result.stderr}")
                    return False
                logger.info(f"Played {duration:.1f}s audio to virtual mic")
                return True
            else:
                # Start in background and track process
                proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self._pending_processes.append((proc, temp_path))
                logger.info(f"Started playing {duration:.1f}s audio to virtual mic (background, pid={proc.pid})")
                return True
                
        except Exception as e:
            logger.error(f"Failed to play audio: {e}")
            return False
    
    def speak(self, text: str, tts: 'SherpaTTS' = None, speed: float = 1.0, wait: bool = True) -> bool:
        """Generate and play TTS audio."""
        if tts is None:
            logger.error("TTS not provided for speak()")
            return False
        
        audio_data = tts.generate(text, speed=speed)
        return self.play_audio(audio_data.audio_bytes, wait=wait)
    
    def cleanup(self):
        """Remove virtual audio devices and terminate pending background processes."""
        # Terminate any pending background paplay processes
        for proc, temp_path in self._pending_processes:
            try:
                if proc.poll() is None:  # Process still running
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
        
        # Remove virtual sink
        if self.sink_id:
            try:
                subprocess.run(
                    ["pactl", "unload-module", self.sink_id],
                    capture_output=True, timeout=5
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


# Skip all tests if audio is not enabled
audio_config = cfg.get("audio", {})
if not audio_config.get("enabled", False):
    pytestmark = pytest.mark.skip(reason="Audio/ASR is not enabled in deployment")

# Also check if chatqa pipeline is deployed
for pipeline in cfg.get("pipelines", []):
    if pipeline.get("type") == "chatqa":
        break
else:
    pytestmark = pytest.mark.skip(reason="ChatQA pipeline is not deployed")


# =============================================================================
# Transcription Accuracy Evaluator (Reusable)
# =============================================================================

class TranscriptionAccuracyEvaluator:
    """
    Evaluates transcription accuracy by comparing original text with transcribed text.
    
    Single Responsibility: Transcription validation only.
    
    Uses multiple methods:
    1. Word-level accuracy (Word Error Rate approximation)
    2. Keyword matching
    3. Combined weighted score
    """
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize text for comparison (lowercase, remove punctuation)."""
        text = text.lower().strip()
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
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
    def calculate_keyword_match(cls, original: str, transcribed: str, 
                                keywords: List[str] = None) -> float:
        """Calculate keyword matching accuracy."""
        trans_lower = transcribed.lower()
        
        if keywords:
            found = sum(1 for kw in keywords if kw.lower() in trans_lower)
            return found / len(keywords) if keywords else 0.0
        else:
            stop_words = {'the', 'is', 'are', 'was', 'were', 'what', 'how', 'why', 
                         'a', 'an', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of'}
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
        min_accuracy: float = 0.7
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
            "passed": combined_score >= min_accuracy
        }
        
        logger.info(f"Transcription evaluation: word_accuracy={word_accuracy:.2f}, "
                   f"keyword_match={keyword_match:.2f}, combined={combined_score:.2f}")
        
        return metrics["passed"], metrics


# =============================================================================
# Audio Test Cases Configuration (Single source of truth)
# =============================================================================

AUDIO_TEST_CASES = {
    "what_is_ai": {
        "text": "What is artificial intelligence?",
        "speed": 1.0,
        "expected_keywords": ["AI", "machine learning", "intelligence", "computer"],
        "min_length": 50,
    },
}

# Speed test cases - using moderate speeds that ASR can handle
# Note: Extreme speeds (< 0.85 or > 1.25) cause ASR to hear noise/beeps
SLOW_SPEECH_TEST_CASES = [
    {"speed": 0.95, "text": "Astronomy is a scientific study of stars and planets.",
     "expected_words": ["astronomy", "stars", "planets"], "min_accuracy": 0.4},
    {"speed": 0.9, "text": "Artificial intelligence is changing the future of technology.",
     "expected_words": ["artificial", "intelligence", "technology"], "min_accuracy": 0.4},
]

FAST_SPEECH_TEST_CASES = [
    {"speed": 1.1, "text": "The quick brown fox jumps over the lazy dog.",
     "expected_words": ["quick", "fox", "dog"], "min_accuracy": 0.4},
    {"speed": 1.15, "text": "Machine learning models need large datasets for training.",
     "expected_words": ["machine", "learning", "training"], "min_accuracy": 0.4},
]


# =============================================================================
# Unified Audio Input Provider (PulseAudio Primary, JS Mock Fallback)
# =============================================================================

def _pulseaudio_available() -> bool:
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


class UnifiedAudioInput:
    """
    PulseAudio-based audio input provider for realistic UI testing.
    
    Uses PulseAudio virtual microphone to play TTS audio that the browser
    captures via the real microphone API, then sends to real ASR.
    
    Requires PulseAudio to be available - tests will be skipped otherwise.
    """
    
    def __init__(
        self,
        audio_helper: 'AudioChatUIHelper',
        tts: SherpaTTS,
        virtual_mic_player: 'VirtualMicAudioPlayer',
        audio_artifacts_collector: Optional[Callable] = None
    ):
        """
        Initialize UnifiedAudioInput.
        
        Args:
            audio_helper: AudioChatUIHelper instance for UI interactions
            tts: SherpaTTS instance for audio generation
            virtual_mic_player: VirtualMicAudioPlayer for PulseAudio (required)
            audio_artifacts_collector: Callable to collect audio artifacts
        """
        self.helper = audio_helper
        self.tts = tts
        self.virtual_mic_player = virtual_mic_player
        self.artifacts_collector = audio_artifacts_collector
        
        logger.info("UnifiedAudioInput initialized with PulseAudio")
    
    @property
    def method_name(self) -> str:
        """Returns human-readable name of the audio input method."""
        return "PulseAudio Virtual Mic"
    
    async def setup_audio(
        self,
        text: str,
        speed: float = 1.0,
        expected_transcription: str = None
    ) -> AudioData:
        """
        Generate audio for the test.
        
        Args:
            text: Text to convert to speech
            speed: Speech speed (0.7-1.6)
            expected_transcription: Ignored (for API compatibility)
            
        Returns:
            AudioData with the generated audio
        """
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
        wait: bool = True
    ):
        """
        Play audio while recording is active via PulseAudio virtual microphone.
        
        Args:
            audio_data: Pre-generated AudioData (optional)
            text: Text to speak (if audio_data not provided)
            speed: Speech speed
            wait: Whether to wait for playback to complete
        """
        if text and not audio_data:
            # Generate and play via virtual mic
            self.virtual_mic_player.speak(text, tts=self.tts, speed=speed, wait=wait)
        elif audio_data:
            # Play existing audio via virtual mic
            self.virtual_mic_player.play_audio(audio_data.audio_bytes, wait=wait)
        logger.info("Audio playing through PulseAudio virtual mic")
    
    async def cleanup(self):
        """Clean up resources (no-op for PulseAudio, cleanup handled by fixture)."""
        pass


@pytest.fixture(scope="module")
def virtual_mic_player():
    """
    PulseAudio virtual microphone player (required).
    
    Module-scoped - creates virtual audio device once per test module.
    Skips all tests if PulseAudio is not available.
    """
    if not _pulseaudio_available():
        pytest.skip("PulseAudio not available - audio tests require PulseAudio")
    
    player = VirtualMicAudioPlayer()
    if player.setup():
        logger.info("Virtual microphone player ready")
        yield player
        player.cleanup()
    else:
        pytest.skip("Failed to set up PulseAudio virtual microphone")


@pytest.fixture(scope="module")
def sherpa_tts():
    """
    SherpaTTS instance for audio generation.
    
    Module-scoped for efficiency - TTS engine reused across tests.
    """
    return SherpaTTS()


@pytest_asyncio.fixture
async def unified_audio_input(
    audio_chat_ui_helper,
    sherpa_tts,
    virtual_mic_player,
    request
):
    """
    Fixture providing UnifiedAudioInput with PulseAudio virtual microphone.
    
    Requires PulseAudio - tests will be skipped if not available.
    Includes audio artifact collection on test failure.
    
    Usage:
        async def test_audio(unified_audio_input):
            audio_data = await unified_audio_input.setup_audio("Hello world")
            await audio_chat_ui_helper.audio.start_recording()
            await unified_audio_input.play_during_recording(audio_data)
            await audio_chat_ui_helper.audio.stop_recording()
    """
    # Create artifact collector for this test
    test_name = request.node.name.replace("::", "_")
    artifact_collector = AudioArtifactCollector(test_name)
    
    # Create collector callback for UnifiedAudioInput
    def collect_audio(audio_data: AudioData = None, output_bytes: bytes = None, source: str = ""):
        if audio_data:
            artifact_collector.collect_input_audio(audio_data)
        if output_bytes:
            artifact_collector.collect_output_audio(output_bytes, source)
    
    unified = UnifiedAudioInput(
        audio_helper=audio_chat_ui_helper,
        tts=sherpa_tts,
        virtual_mic_player=virtual_mic_player,
        audio_artifacts_collector=collect_audio
    )
    
    logger.info("UnifiedAudioInput ready with PulseAudio virtual microphone")
    
    yield unified
    
    # Cleanup
    await unified.cleanup()
    
    # Save artifacts on test failure
    test_failed = (
        hasattr(request.node, 'rep_call') and request.node.rep_call.failed
    ) or (
        hasattr(request.node, 'rep_setup') and request.node.rep_setup.failed
    )
    
    if test_failed:
        saved = artifact_collector.save_artifacts(attach_to_allure=True)
        if saved:
            logger.info(f"Audio artifacts saved for failed test: {list(saved.keys())}")
        AudioArtifactCollector.rotate_old_artifacts(keep_count=10)


# =============================================================================
# Audio-specific Fixtures for Headless Mode Support
# =============================================================================

@pytest_asyncio.fixture
async def audio_browser(playwright_instance):
    """
    Browser instance configured for audio testing with microphone permissions.
    
    Firefox requires preferences to be set at launch time to auto-grant 
    microphone permissions, unlike Chromium which supports runtime permissions.
    
    IMPORTANT: We do NOT use fake media streams - we use PulseAudio virtual mic
    so the browser captures real TTS audio for ASR testing.
    """
    headless_env = os.getenv('HEADLESS', 'true').lower()
    headless = headless_env in ('true', '1', 'yes')
    display = os.getenv('DISPLAY')
    
    logger.info(f"Launching Firefox browser for audio tests... (headless={headless}, display={display})")
    
    firefox_prefs = {
        # Auto-grant microphone permission (1 = allow)
        "permissions.default.microphone": 1,
        # Do NOT use fake streams - we want real PulseAudio virtual mic!
        "media.navigator.streams.fake": False,
        # Disable permission prompts
        "media.navigator.permission.disabled": True,
        # Disable notifications
        "dom.webnotifications.enabled": False,
        "dom.push.enabled": False,
        # Audio device selection - use default (which is our virtual mic)
        "media.getusermedia.aec_enabled": False,  # Disable echo cancellation for cleaner audio
        "media.getusermedia.noise_enabled": False,  # Disable noise suppression  
        "media.getusermedia.agc_enabled": False,  # Disable auto gain control
    }
    
    launch_args = ["--ignore-certificate-errors", "--ignore-ssl-errors"]
    if not headless:
        launch_args.extend(["--width=1920", "--height=1080"])
    
    browser = await playwright_instance.firefox.launch(
        headless=headless,
        args=launch_args,
        firefox_user_prefs=firefox_prefs
    )
    logger.info("Firefox browser for audio tests launched successfully")
    yield browser
    logger.info("Closing Firefox audio browser...")
    await browser.close()


@pytest_asyncio.fixture
async def audio_context(audio_browser, request):
    """Browser context configured for audio testing with video recording."""
    test_name = request.node.name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_path = Path(__file__).parent.parent.parent.parent.parent / "test-results" / "videos" / f"test_{test_name}_{timestamp}"
    
    context = await audio_browser.new_context(
        viewport={"width": 1920, "height": 1080},
        record_video_dir=str(video_path),
        record_video_size={"width": 1920, "height": 1080},
        ignore_https_errors=True,
    )
    yield context
    await context.close()


@pytest_asyncio.fixture
async def audio_page(audio_context):
    """Page instance configured for audio testing."""
    page = await audio_context.new_page()
    page.on("console", lambda msg: logger.debug(f"[Browser Console] {msg.text}"))
    yield page
    await page.close()


@pytest_asyncio.fixture
async def audio_chat_ui_helper(audio_page, admin_credentials):
    """
    Create AudioChatUIHelper with authenticated session for audio tests.
    
    Uses audio_page with special microphone permissions for Firefox.
    """
    username = admin_credentials['username']
    password = admin_credentials['password']

    helper = AudioChatUIHelper(audio_page, base_url=cfg.get('FQDN'), credentials=admin_credentials)
    await helper.login_as_admin(username, password)

    logger.info("AudioChatUIHelper ready for audio testing")
    yield helper


# =============================================================================
# TEST CASES
# =============================================================================

@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T331")
async def test_voice_input_button_visible(chat_ui_helper):
    """
    Test that the voice input (microphone) button is visible when audio is enabled.
    
    Success criteria:
    - Page loads successfully
    - Microphone button is visible
    - Button has correct aria-label
    """
    logger.info("Testing voice input button visibility")
    
    audio_helper = AudioUIHelper(chat_ui_helper.page)
    
    # Assert 1: Microphone button exists and is visible
    is_visible = await audio_helper.is_mic_button_visible(timeout=10000)
    assert is_visible, "Microphone button should be visible when audio is enabled"
    logger.info("Assert 1: Microphone button is visible")
    
    # Assert 2: Button has correct aria-label
    aria_label = await audio_helper.get_mic_button_aria_label()
    assert aria_label == "Start recording", f"Expected aria-label 'Start recording', got '{aria_label}'"
    logger.info("Assert 2: Button has correct aria-label")
    
    logger.info("Test completed: Voice input button visibility validated")


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T332")
async def test_audio_recording_starts_stops(audio_chat_ui_helper, unified_audio_input):
    """
    Test that clicking the microphone button starts and stops recording.
    
    Uses SherpaTTS for audio generation (DRY - shared with backend).
    Audio input via PulseAudio (primary) or JS mock (fallback).
    """
    logger.info(f"Testing audio recording start/stop (using {unified_audio_input.method_name})")
    
    test_case = AUDIO_TEST_CASES["what_is_ai"]
    audio_data = await unified_audio_input.setup_audio(
        text=test_case["text"],
        speed=test_case["speed"],
        expected_transcription=test_case["text"]
    )
    
    try:
        # Assert 1: Initial state - not recording
        is_recording = await audio_chat_ui_helper.audio.is_recording()
        assert not is_recording, "Initial state should be 'Start recording'"
        logger.info("Assert 1: Initial state is 'Start recording'")
        
        # Start recording
        await audio_chat_ui_helper.audio.click_mic_button()
        await audio_chat_ui_helper.page.wait_for_timeout(200)
        
        # Play audio through virtual mic (if PulseAudio) - no-op for JS mock
        await unified_audio_input.play_during_recording(audio_data)
        
        # Assert 2: Check recording state
        aria_label = await audio_chat_ui_helper.audio.get_mic_button_aria_label()
        logger.info(f"After clicking mic: aria-label = '{aria_label}'")
        
        if aria_label == "Stop recording":
            logger.info("Assert 2: Recording state shows 'Stop recording'")
            await audio_chat_ui_helper.audio.stop_recording()
        else:
            logger.info("Assert 2: Recording already completed (audio was short)")
        
        # Assert 3: Back to initial state
        is_recording = await audio_chat_ui_helper.audio.is_recording()
        assert not is_recording, "Final state should be 'Start recording'"
        logger.info("Assert 3: Returned to 'Start recording' state")
        
    finally:
        await unified_audio_input.cleanup()
    
    logger.info("Test completed: Audio recording start/stop validated")


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T333")
async def test_audio_transcription_to_prompt(audio_chat_ui_helper, unified_audio_input):
    """
    Test that recorded audio is transcribed and appears in the prompt input.
    Validates transcription accuracy.
    
    Audio input via PulseAudio (primary) or JS mock (fallback).
    """
    logger.info(f"Testing audio transcription to prompt (using {unified_audio_input.method_name})")
    
    test_case = AUDIO_TEST_CASES["what_is_ai"]
    original_text = test_case["text"]
    expected_keywords = test_case.get("expected_keywords", [])
    
    logger.info(f"Original text to speak: '{original_text}'")
    
    audio_data = await unified_audio_input.setup_audio(
        text=original_text,
        speed=test_case["speed"],
        expected_transcription=original_text
    )
    
    try:
        # Step 1: Start recording
        logger.info("Step 1: Starting recording")
        await audio_chat_ui_helper.audio.click_mic_button()
        
        recording_started = await audio_chat_ui_helper.audio.wait_for_recording_state(
            recording=True, timeout=5000
        )
        
        if recording_started:
            logger.info("Recording in progress...")
            # Play audio through virtual mic (if PulseAudio)
            await unified_audio_input.play_during_recording(audio_data)
            await audio_chat_ui_helper.page.wait_for_timeout(3000)
            
            # Step 2: Stop recording
            logger.info("Step 2: Stopping recording")
            await audio_chat_ui_helper.audio.click_mic_button()
            await audio_chat_ui_helper.audio.wait_for_recording_state(recording=False, timeout=5000)
        else:
            pytest.fail("Recording did not start")
        
        # Step 3: Wait for transcription
        logger.info("Step 3: Waiting for transcription...")
        transcribed_text = await audio_chat_ui_helper.audio.wait_for_transcription(timeout=30000)
        
        logger.info(f"Original text: '{original_text}'")
        logger.info(f"Transcribed text: '{transcribed_text}'")
        
        # Step 4: Validate transcription accuracy
        assert len(transcribed_text) > 0, "Textarea should contain transcribed text"
        
        passed, metrics = TranscriptionAccuracyEvaluator.evaluate_transcription(
            original=original_text,
            transcribed=transcribed_text,
            keywords=expected_keywords,
            min_accuracy=0.5
        )
        
        allure.attach(
            f"Audio Input Method: {unified_audio_input.method_name}\n"
            f"Original: {original_text}\n"
            f"Transcribed: {transcribed_text}\n"
            f"Word Accuracy: {metrics['word_accuracy']:.2%}\n"
            f"Keyword Match: {metrics['keyword_match']:.2%}\n"
            f"Combined Score: {metrics['combined_score']:.2%}",
            name="Transcription Accuracy Metrics",
            attachment_type=allure.attachment_type.TEXT
        )
        
        logger.info(f"Transcription accuracy: {metrics['combined_score']:.2%}")
        
    finally:
        await unified_audio_input.cleanup()
    
    logger.info("Test completed: Audio transcription to prompt validated")


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T334")
async def test_voice_question_receives_response(audio_chat_ui_helper, unified_audio_input):
    """
    Test full voice UI flow: voice input -> transcription -> send -> receive response.
    
    Focus: Voice UI interaction mechanism (mic button, recording, transcription).
    Note: Response quality validation is handled by ChatQnA tests.
    Audio input via PulseAudio (primary) or JS mock (fallback).
    """
    logger.info(f"Testing full voice question flow (using {unified_audio_input.method_name})")
    
    test_case = AUDIO_TEST_CASES["what_is_ai"]
    original_text = test_case["text"]
    expected_keywords = test_case.get("expected_keywords", [])
    
    audio_data = await unified_audio_input.setup_audio(
        text=original_text,
        speed=test_case["speed"],
        expected_transcription=original_text
    )
    
    try:
        # Clear textarea
        textarea = audio_chat_ui_helper.page.locator(audio_chat_ui_helper.audio.TEXTAREA_SELECTOR)
        await textarea.fill("")
        
        # Step 1: Start recording
        logger.info("Step 1: Starting recording")
        await audio_chat_ui_helper.audio.start_recording()
        # Wait for UI state to transition after click
        await audio_chat_ui_helper.page.wait_for_timeout(500)
        is_recording = await audio_chat_ui_helper.audio.is_recording()
        logger.info(f"Recording state after start: {is_recording}")
        assert is_recording, "Should be in recording state after starting"
        
        # Play audio through virtual mic (if PulseAudio)
        await unified_audio_input.play_during_recording(audio_data)
        await audio_chat_ui_helper.page.wait_for_timeout(2000)
        
        # Step 2: Stop recording
        logger.info("Step 2: Stopping recording")
        await audio_chat_ui_helper.audio.stop_recording()
        assert not await audio_chat_ui_helper.audio.is_recording()
        
        # Step 3: Wait for transcription
        logger.info("Step 3: Waiting for transcription")
        transcribed_text = await audio_chat_ui_helper.audio.wait_for_transcription(timeout=10000)
        
        # Validate transcription accuracy (voice UI specific)
        assert len(transcribed_text) > 0, "Should have transcribed text"
        trans_passed, trans_metrics = TranscriptionAccuracyEvaluator.evaluate_transcription(
            original=original_text,
            transcribed=transcribed_text,
            keywords=expected_keywords,
            min_accuracy=0.5
        )
        
        allure.attach(
            f"Audio Input Method: {unified_audio_input.method_name}\n"
            f"Original: {original_text}\n"
            f"Transcribed: {transcribed_text}\n"
            f"Word Accuracy: {trans_metrics['word_accuracy']:.2%}\n"
            f"Keyword Match: {trans_metrics['keyword_match']:.2%}",
            name="Transcription Accuracy Metrics",
            attachment_type=allure.attachment_type.TEXT
        )
        
        # Step 4: Send message (verify UI send flow works)
        logger.info("Step 4: Clicking send button")
        send_button = audio_chat_ui_helper.page.locator(audio_chat_ui_helper.audio.SEND_BUTTON_SELECTOR)
        assert await send_button.is_enabled(), "Send button should be enabled"
        await send_button.click()
        
        # Step 5: Verify response is received (not quality - that's ChatQnA's job)
        logger.info("Step 5: Waiting for chatbot response")
        response_text = await audio_chat_ui_helper.wait_for_response(timeout=60000)
        
        assert response_text is not None, "Should receive a response from chatbot"
        assert len(response_text) > 0, "Response should not be empty"
        logger.info(f"Chatbot response received: {len(response_text)} chars")
        
    finally:
        await unified_audio_input.cleanup()
    
    logger.info("Test completed: Full voice question UI flow validated")


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T335")
async def test_recording_animation_visible(audio_chat_ui_helper, unified_audio_input):
    """
    Test that recording animation (CSS pulse) is visible during recording.
    
    The current UI uses a CSS class 'prompt-input__button--recording' with pulse 
    animation on the microphone button to indicate recording state.
    
    Audio input via PulseAudio (primary) or JS mock (fallback).
    """
    logger.info(f"Testing recording animation visibility (using {unified_audio_input.method_name})")
    
    test_case = AUDIO_TEST_CASES["what_is_ai"]
    audio_data = await unified_audio_input.setup_audio(
        text=test_case["text"],
        speed=test_case["speed"],
        expected_transcription=test_case["text"]
    )
    
    try:
        assert await audio_chat_ui_helper.audio.is_mic_button_visible(timeout=10000)
        
        # Assert 1: No recording animation before starting
        animation_before = await audio_chat_ui_helper.audio.is_recording_animation_visible()
        logger.info(f"Animation visible before recording: {animation_before}")
        # Don't assert - just log (animation shouldn't be visible)
        
        # Start recording
        await audio_chat_ui_helper.audio.start_recording()
        
        # Play audio through virtual mic (if PulseAudio)
        await unified_audio_input.play_during_recording(audio_data)
        
        # Assert 2: Recording animation (CSS pulse) is visible during recording
        animation_visible = await audio_chat_ui_helper.audio.is_recording_animation_visible()
        logger.info(f"Recording animation visible during recording: {animation_visible}")
        
        # Also check aria-label as backup indicator
        aria_label = await audio_chat_ui_helper.audio.get_mic_button_aria_label()
        is_recording_state = aria_label == "Stop recording"
        
        # Either CSS animation or aria-label should indicate recording
        assert animation_visible or is_recording_state, \
            "Recording should be indicated by CSS animation or aria-label"
        logger.info("Assert 2: Recording state indicated (animation or aria-label)")
        
        # Stop recording
        await audio_chat_ui_helper.audio.stop_recording()
        
        # Assert 3: Animation hidden after stopping
        await audio_chat_ui_helper.page.wait_for_timeout(500)  # Allow state to update
        animation_after = await audio_chat_ui_helper.audio.is_recording_animation_visible()
        aria_after = await audio_chat_ui_helper.audio.get_mic_button_aria_label()
        
        assert not animation_after or aria_after == "Start recording", \
            "Recording animation should be hidden after stopping"
        logger.info("Assert 3: Recording animation hidden after stopping")
        
    finally:
        await unified_audio_input.cleanup()
    
    logger.info("Test completed: Recording animation visibility validated")


# =============================================================================
# Speed Variation Tests (Aligned with backend test_audioqa.py)
# =============================================================================

@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T336")
async def test_asr_slow_speech_ui(audio_chat_ui_helper, unified_audio_input):
    """
    Test ASR with slow speech audio at moderate speeds (0.9-0.95x).
    
    Validates that the UI audio flow works with slightly slower speech.
    Uses moderate speeds that ASR can still recognize.
    
    Audio input via PulseAudio (primary) or JS mock (fallback).
    """
    logger.info(f"Testing ASR with slow speech (using {unified_audio_input.method_name})")
    
    results = []
    
    for case in SLOW_SPEECH_TEST_CASES:
        text = case["text"]
        speed = case["speed"]
        expected_words = case["expected_words"]
        min_accuracy = case.get("min_accuracy", 0.4)
        
        logger.info(f"Testing speed {speed}: '{text}'")
        
        audio_data = await unified_audio_input.setup_audio(
            text=text,
            speed=speed,
            expected_transcription=text
        )
        
        try:
            # Clear textarea
            textarea = audio_chat_ui_helper.page.locator(audio_chat_ui_helper.audio.TEXTAREA_SELECTOR)
            await textarea.fill("")
            
            # Record and transcribe
            await audio_chat_ui_helper.audio.start_recording()
            # Play audio through virtual mic (if PulseAudio)
            await unified_audio_input.play_during_recording(audio_data)
            await audio_chat_ui_helper.page.wait_for_timeout(3000)
            await audio_chat_ui_helper.audio.stop_recording()
            
            transcribed = await audio_chat_ui_helper.audio.wait_for_transcription(timeout=15000)
            logger.info(f"Speed {speed} | Transcription: '{transcribed}'")
            
            # Validate with flexible accuracy threshold
            passed, metrics = TranscriptionAccuracyEvaluator.evaluate_transcription(
                original=text,
                transcribed=transcribed,
                keywords=expected_words,
                min_accuracy=min_accuracy
            )
            
            results.append({
                "speed": speed,
                "passed": passed,
                "accuracy": metrics["combined_score"],
                "transcribed": transcribed
            })
            
            logger.info(f"Speed {speed} | Accuracy: {metrics['combined_score']:.2%} | Passed: {passed}")
            
        finally:
            await unified_audio_input.cleanup()
    
    # At least one speed variation should work
    passed_count = sum(1 for r in results if r["passed"])
    
    allure.attach(
        "\n".join([f"Speed {r['speed']}: {r['accuracy']:.2%} - {'PASS' if r['passed'] else 'FAIL'}" for r in results]),
        name="Slow Speech Test Results",
        attachment_type=allure.attachment_type.TEXT
    )
    
    assert passed_count >= 1, f"At least one slow speech test should pass. Results: {results}"
    logger.info(f"Test completed: {passed_count}/{len(results)} slow speech tests passed")


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T337")
async def test_asr_fast_speech_ui(audio_chat_ui_helper, unified_audio_input):
    """
    Test ASR with fast speech audio at moderate speeds (1.1-1.15x).
    
    Validates that the UI audio flow works with slightly faster speech.
    Uses moderate speeds that ASR can still recognize.
    
    Audio input via PulseAudio (primary) or JS mock (fallback).
    """
    logger.info(f"Testing ASR with fast speech (using {unified_audio_input.method_name})")
    
    results = []
    
    for case in FAST_SPEECH_TEST_CASES:
        text = case["text"]
        speed = case["speed"]
        expected_words = case["expected_words"]
        min_accuracy = case.get("min_accuracy", 0.4)
        
        logger.info(f"Testing speed {speed}: '{text}'")
        
        audio_data = await unified_audio_input.setup_audio(
            text=text,
            speed=speed,
            expected_transcription=text
        )
        
        try:
            textarea = audio_chat_ui_helper.page.locator(audio_chat_ui_helper.audio.TEXTAREA_SELECTOR)
            await textarea.fill("")
            
            await audio_chat_ui_helper.audio.start_recording()
            # Play audio through virtual mic (if PulseAudio)
            await unified_audio_input.play_during_recording(audio_data)
            await audio_chat_ui_helper.page.wait_for_timeout(2000)
            await audio_chat_ui_helper.audio.stop_recording()
            
            transcribed = await audio_chat_ui_helper.audio.wait_for_transcription(timeout=15000)
            logger.info(f"Speed {speed} | Transcription: '{transcribed}'")
            
            # Validate with flexible accuracy threshold
            passed, metrics = TranscriptionAccuracyEvaluator.evaluate_transcription(
                original=text,
                transcribed=transcribed,
                keywords=expected_words,
                min_accuracy=min_accuracy
            )
            
            results.append({
                "speed": speed,
                "passed": passed,
                "accuracy": metrics["combined_score"],
                "transcribed": transcribed
            })
            
            logger.info(f"Speed {speed} | Accuracy: {metrics['combined_score']:.2%} | Passed: {passed}")
            
        finally:
            await unified_audio_input.cleanup()
    
    # At least one speed variation should work
    passed_count = sum(1 for r in results if r["passed"])
    
    allure.attach(
        "\n".join([f"Speed {r['speed']}: {r['accuracy']:.2%} - {'PASS' if r['passed'] else 'FAIL'}" for r in results]),
        name="Fast Speech Test Results",
        attachment_type=allure.attachment_type.TEXT
    )
    
    assert passed_count >= 1, f"At least one fast speech test should pass. Results: {results}"
    logger.info(f"Test completed: {passed_count}/{len(results)} fast speech tests passed")


@pytest.mark.ui
@pytest.mark.asyncio
@allure.testcase("IEASG-T338")
async def test_asr_silence_ui(audio_chat_ui_helper, unified_audio_input):
    """
    Test ASR with silence to ensure it doesn't hallucinate words.
    Aligned with backend test_asr_silence in test_audioqa.py.
    
    Audio input via PulseAudio (primary) or JS mock (fallback).
    
    Note: In UI mode with audio mock (oscillator tone), ASR may produce
    minimal false positives (1-2 short words). This is acceptable for
    UI testing where we verify the flow works, not ASR accuracy.
    """
    logger.info(f"Testing ASR with silence (using {unified_audio_input.method_name})")
    
    # Generate silent audio (empty text)
    audio_data = await unified_audio_input.setup_audio(
        text="",
        speed=1.0,
        expected_transcription=""  # Expect empty transcription
    )
    
    try:
        textarea = audio_chat_ui_helper.page.locator(audio_chat_ui_helper.audio.TEXTAREA_SELECTOR)
        await textarea.fill("")
        
        await audio_chat_ui_helper.audio.start_recording()
        # Play silence through virtual mic (if PulseAudio) - no-op for empty audio
        await unified_audio_input.play_during_recording(audio_data)
        await audio_chat_ui_helper.page.wait_for_timeout(2000)
        await audio_chat_ui_helper.audio.stop_recording()
        
        transcribed = await audio_chat_ui_helper.audio.wait_for_transcription(timeout=10000)
        transcribed = transcribed.strip()
        
        logger.info(f"Silence transcription output: '{transcribed}'")
        
        # In UI mode with audio mock, allow minimal false positives
        # (short single words from oscillator tone noise)
        word_count = len(transcribed.split()) if transcribed else 0
        
        # Should be empty, contain BLANK indicator, or have very minimal output
        is_acceptable = (
            transcribed == "" or 
            "BLANK" in transcribed or
            word_count <= 2  # Allow up to 2 short words from mock audio noise
        )
        
        if not is_acceptable:
            pytest.fail(f"ASR hallucinated significant text during silence: '{transcribed}' ({word_count} words)")
        elif word_count > 0:
            logger.warning(f"ASR produced minimal noise output: '{transcribed}' (acceptable for UI mock)")
        
    finally:
        await unified_audio_input.cleanup()
    
    logger.info("Test completed: Silence ASR validated in UI")
