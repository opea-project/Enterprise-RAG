import os
import time
import torch

from datasets import load_dataset
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech
from transformers import SpeechT5HifiGan

from comps.cores.mega.logger import get_opea_logger

try:
    torch.jit.enable_onednn_fusion(True)
except Exception:
    pass

os.environ['TORCH_MKLDNN_ENABLE'] = '1'

logger = get_opea_logger("TTS FastAPI Model Server")

DEVICE = torch.device("cpu")
SUPPORTED_MODELS = {"microsoft/speecht5_tts",
                    "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
                    "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
                    "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"}

SPEECH_T5_SUPPORTED_VOICES = { "awb": 0, "bdl": 1138, "clb": 2271, "jmk": 3403, "ksp": 4535, "rms": 5667, "slt": 6799 }


class TTSModel:
    def __init__(self, model_name: str):
        if model_name not in SUPPORTED_MODELS:
            raise ValueError(f"Unsupported model provided: {model_name}")

        self.model_name = model_name
        if model_name == "microsoft/speecht5_tts":
            self._init_speecht5()
        elif "Qwen3-TTS" in model_name:
            self._init_qwen_tts(model_name)
        else:
            raise NotImplementedError(f"Model {model_name} is not yet implemented.")

        self.generate_audio("test")

        logger.info(f"TTS model {model_name} initialized successfully.")
        self.ready = True

    def _init_speecht5(self):
        self.processor = SpeechT5Processor.from_pretrained(
            "microsoft/speecht5_tts",
            normalize=True
        )

        self.model = SpeechT5ForTextToSpeech.from_pretrained(
            "microsoft/speecht5_tts"
        ).to(DEVICE)

        self.vocoder = SpeechT5HifiGan.from_pretrained(
            "microsoft/speecht5_hifigan"
        ).to(DEVICE)

        self.embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")

        self.speaker_embeddings_cache = {}
        for voice, idx in SPEECH_T5_SUPPORTED_VOICES.items():
            self.speaker_embeddings_cache[voice] = torch.tensor(self.embeddings_dataset[idx]["xvector"]).unsqueeze(0).to(DEVICE)

        self.model.eval()
        self.vocoder.eval()

        self.model = self.model.to(memory_format=torch.channels_last)
        self.vocoder = self.vocoder.to(memory_format=torch.channels_last)

    def _init_qwen_tts(self, model_name: str):
        from qwen_tts import Qwen3TTSModel

        self.model = Qwen3TTSModel.from_pretrained(
            model_name,
            device_map="cpu",
            dtype=torch.bfloat16,
        )
        logger.warning("Flash attention doesn't support Intel CPUs. It'll be enabled once support is added.")

    @torch.inference_mode()
    def generate_audio(self, text: str, voice: str = "default", instructions: str = None):
        start_time = time.time()
        if self.model_name == "microsoft/speecht5_tts":
            if voice == "default":
                voice = "awb"
            else:
                if voice.lower() not in SPEECH_T5_SUPPORTED_VOICES:
                    raise ValueError(f"Unsupported speaker {voice} for model {self.model_name}. " \
                        f"Supported speakers: {list(SPEECH_T5_SUPPORTED_VOICES.keys())}. " \
                        "Check https://huggingface.co/datasets/Matthijs/cmu-arctic-xvectors for more details.")

            if instructions is not None:
                logger.warning("Instructions parameter is not supported for microsoft/speecht5_tts model and will be ignored.")

            speaker_embedding = self.speaker_embeddings_cache.get(voice.lower())

            inputs = self.processor(text=text, return_tensors="pt").to(DEVICE)

            audio_output = self.model.generate_speech(
                inputs["input_ids"],
                speaker_embedding,
                vocoder=self.vocoder
            )

            end_time = time.time()
            logger.info(f"Speech generated in {end_time - start_time:.2f} seconds.")
            return audio_output.cpu(), 16000
        elif "Qwen3-TTS" in self.model_name:
            if voice == "default":
                voice = "ryan"
            else:
                if voice.lower() not in self.model.get_supported_speakers():
                    raise ValueError(f"Unsupported speaker {voice} for model {self.model_name}. " \
                        f"Supported speakers: {self.model.get_supported_speakers()}.")

            if "CustomVoice" in self.model_name:
                wavs, sr = self.model.generate_custom_voice(
                    text=text,
                    language="English",
                    speaker=voice,
                    instruct=instructions,
                )
            elif "VoiceDesign" in self.model_name:
                wavs, sr = self.model.generate_voice_design(
                    text=text,
                    language="English",
                    instruct=instructions,
                )
            else:
                raise NotImplementedError(f"Model {self.model_name} is not yet implemented.")

            end_time = time.time()
            logger.info(f"Speech generated in {end_time - start_time:.2f} seconds.")
            return wavs[0], sr
        else:
            raise NotImplementedError(f"Model {self.model_name} is not yet implemented.")
