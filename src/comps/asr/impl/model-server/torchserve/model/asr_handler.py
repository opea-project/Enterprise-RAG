# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
ASRHandler is a custom handler for processing ASR models using TorchServe.

Attributes:
    batch_size (int): The batch size for processing requests.
    initialized (bool): Flag indicating if the handler has been initialized.
    hf_hub (bool): Flag indicating if the input is from Hugging Face Hub.
    device_type (str): The type of device to run the model on (e.g., 'cpu', 'cuda').
    amp_dtype (torch.dtype): The data type for automatic mixed precision (AMP).
    amp_enabled (bool): Flag indicating if AMP is enabled.
    model (transformers.Wav2Vec2ForCTC): The ASR model.

Methods:
    __init__():
        Initializes the ASRHandler instance.

    initialize(ctx: Context):
        Initializes the model and sets up the environment based on context.

    preprocess(requests):
        Preprocesses the incoming requests to extract input audio.

    inference(input_batch):
        Performs inference on the preprocessed input batch to generate transcriptions.

    postprocess(inference_output):
        Postprocesses the inference output to return the final result.
"""
import logging
import os
import io
from abc import ABC

import torch
import torchaudio
from transformers import WhisperForConditionalGeneration, WhisperProcessor
from pydub import AudioSegment
import numpy as np

from ts.context import Context
from ts.torch_handler.base_handler import BaseHandler

import intel_extension_for_pytorch as ipex

logger = logging.getLogger(__name__)

class ASRHandler(BaseHandler, ABC):
    def __init__(self):
        super(ASRHandler, self).__init__()
        self.batch_size = None
        self.initialized = False

    def initialize(self, ctx: Context):
        model_name = str(os.getenv('TORCHSERVE_MODEL_NAME')) 
        if not model_name:
            raise ValueError("The 'TORCHSERVE_MODEL_NAME' cannot be empty.")
        self.device_type = str(os.getenv('TORCHSERVE_DEVICE_TYPE', "cpu")).lower()
        self.batch_size = int(os.getenv('TORCHSERVE_BATCH_SIZE'))
        self.amp_dtype = str(os.getenv('TORCHSERVE_AMP_DTYPE'))
        self.language = 'english'
        if self.amp_dtype == "BF16":
            self.amp_enabled = True
            self.amp_dtype = torch.bfloat16
        elif self.amp_dtype == "FP32":
            self.amp_enabled = False
            self.amp_dtype = torch.float32
        else:
            error_message = f"Invalid AMP_DTYPE value '{self.amp_dtype}'. Expected 'BF16' or 'FP32'."
            logger.error(error_message)
            raise ValueError(error_message)
        logger.info(f"TORCHSERVE_MODEL_LANGUAGE is set to {self.language}.")
        logger.info(f"TORCHSERVE_MODEL_NAME is set to {model_name}.")
        logger.info(f"TORCHSERVE_DEVICE_TYPE is set to {self.device_type}.")
        logger.info(f"TORCHSERVE_BATCH_SIZE is set to {self.batch_size}.")
        logger.info(f"TORCHSERVE_AMP_DTYPE is set to {self.amp_dtype}.")

        try:
            ipex._C.disable_jit_linear_repack()
            torch._C._jit_set_texpr_fuser_enabled(False)
        except Exception:
            logger.warning("Failed to disable certain optimizations, proceeding without them.")

        try:
            self.processor = WhisperProcessor.from_pretrained(model_name)
            self.model = WhisperForConditionalGeneration.from_pretrained(model_name).to(self.device_type)
            self.model.eval()

            self.model = ipex.llm.optimize(
                self.model,
                dtype=self.amp_dtype,
                inplace=True,
                deployment_mode=True,
            )
            self.initialized = True
            logger.info(f"Model '{model_name}' loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model '{model_name}': {str(e)}")
            raise

    def _audiosegment_to_librosawav(self, audiosegment):
        # https://github.com/jiaaro/pydub/blob/master/API.markdown#audiosegmentget_array_of_samples
        # This way is faster than librosa.load or HuggingFace Dataset wrapper
        channel_sounds = audiosegment.split_to_mono()[:1]  # only select the first channel
        samples = [s.get_array_of_samples() for s in channel_sounds]

        fp_arr = np.array(samples).T.astype(np.float32)
        fp_arr /= np.iinfo(samples[0].typecode).max
        fp_arr = fp_arr.reshape(-1)

        return fp_arr

    def preprocess(self, requests):
        audio_inputs = []
        logger.debug(f"Received requests: {requests}")

        for data in requests:
            body = data.get("data") or data.get("body")

        logger.info(f"Received body type: {type(body)}, Length: {len(body) if isinstance(body, bytes) else 'N/A'}")
        
        if isinstance(body, (bytes, bytearray)):  # Handle raw audio bytes
            audio_stream = io.BytesIO(body)

            try:
                # Convert audio to WAV using pydub
                audio = AudioSegment.from_file(audio_stream).set_frame_rate(16000)  # Ensure 16kHz, mono
                waveform = self._audiosegment_to_librosawav(audio)
                sample_rate = 16000
                #waveform, sample_rate = torchaudio.load(wav_stream)
            except Exception as e:
                logger.error(f"Failed to process audio: {e}")
                raise ValueError("Invalid audio format. Ensure the file is a valid audio file.")
        elif isinstance(body, dict) and "inputs" in body:  # Handle JSON format
            audio = body["inputs"]
            if isinstance(audio, list):
                audio = audio[0]  # Extract first input
            waveform, sample_rate = torchaudio.load(audio)
        else:
            raise ValueError("Invalid input format. Expected raw audio bytes or JSON with 'inputs'.")

        audio_inputs.append((waveform, sample_rate))

        logger.debug(f"Processed audio inputs: {audio_inputs}")
        return audio_inputs

    def inference(self, input_batch):
        logger.debug(f"Received input_batch: {input_batch}")
        transcriptions = []
        with torch.inference_mode(), torch.no_grad(), torch.autocast(
            device_type=self.device_type,
            enabled=self.amp_enabled,
            dtype=self.amp_dtype,
        ):
            for waveform, sample_rate in input_batch:
                try:
                    processed_inputs = self.processor(
                        waveform,
                        return_tensors="pt",
                        truncation=False,
                        padding="longest",
                        return_attention_mask=True,
                        sampling_rate=16000,
                    )
                except RuntimeError as e:
                    if "Padding size should be less than" in str(e):
                        # short-form
                        processed_inputs = self.processor(
                            waveform,
                            return_tensors="pt",
                            sampling_rate=16000,
                        )
                    else:
                        raise e
                if processed_inputs.input_features.shape[-1] < 3000:
                    # short-form
                    processed_inputs = self.processor(
                        waveform,
                        return_tensors="pt",
                        sampling_rate=16000,
                    )
                elif self.device_type == "hpu" and processed_inputs.input_features.shape[-1] > 3000:
                    processed_inputs["input_features"] = torch.nn.functional.pad(
                        processed_inputs.input_features,
                        (0, self.hpu_max_len - processed_inputs.input_features.size(-1)),
                        value=-1.5,
                    )
                    processed_inputs["attention_mask"] = torch.nn.functional.pad(
                        processed_inputs.attention_mask,
                        (0, self.hpu_max_len + 1 - processed_inputs.attention_mask.size(-1)),
                        value=0,
                    )

                predicted_ids = self.model.generate(
                    **(
                        processed_inputs.to(
                            self.device_type,
                        )
                    ),
                    language=self.language,
                    return_timestamps=False,
                )
                # pylint: disable=E1101
                result = self.processor.tokenizer.batch_decode(predicted_ids, skip_special_tokens=True, normalize=True)[0]
                if self.language in ["chinese", "mandarin"]:
                    from zhconv import convert

                    result = convert(result, "zh-cn")
                print(f"the result is: {result}")
                return [result]

        #return transcriptions

    def postprocess(self, inference_output):
        if len(inference_output) > 1:
            return inference_output
        return [inference_output]
