# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0
"""
TTSHandler is a custom handler for processing TTS models using TorchServe.

Attributes:
    batch_size (int): The batch size for processing requests.
    initialized (bool): Flag indicating if the handler has been initialized.
    hf_hub (bool): Flag indicating if the input is from Hugging Face Hub.
    device_type (str): The type of device to run the model on (e.g., 'cpu', 'cuda').
    amp_dtype (torch.dtype): The data type for automatic mixed precision (AMP).
    amp_enabled (bool): Flag indicating if AMP is enabled.
    model (transformers.T5ForConditionalGeneration): The TTS model.

Methods:
    __init__():
        Initializes the TTSHandler instance.

    initialize(ctx: Context):
        Initializes the model and sets up the environment based on context.

    preprocess(requests):
        Preprocesses the incoming requests to extract input texts.

    inference(input_batch):
        Performs inference on the preprocessed input batch to generate speech audio.

    postprocess(inference_output):
        Postprocesses the inference output to return the final result.
"""

import logging
import os
import subprocess
from abc import ABC
import json
import torch
import numpy as np
from transformers import SpeechT5ForTextToSpeech, SpeechT5Processor, SpeechT5HifiGan

from ts.context import Context
from ts.torch_handler.base_handler import BaseHandler

import intel_extension_for_pytorch as ipex

logger = logging.getLogger(__name__)

# The handler is responsible for defining how a model processes incoming requests during inference

class TTSHandler(BaseHandler, ABC):
    def __init__(self):
        super(TTSHandler, self).__init__()
        self.batch_size = None
        self.initialized = False
    def initialize(self, ctx : Context):
        model_name = str(os.getenv('TORCHSERVE_MODEL_NAME'))
        if not model_name:
                raise ValueError("The 'TORCHSERVE_MODEL_NAME' cannot be empty.")
        vocoder_model_name= str(os.getenv('TORCHSERVE_VOCODER_MODEL_NAME'))
        if not model_name:
                raise ValueError("The 'TORCHSERVE_VOCODER_MODEL_NAME' cannot be empty.")        
        self.device_type = str(os.getenv('TORCHSERVE_DEVICE_TYPE', "cpu")).lower()
        self.batch_size = int(os.getenv('TORCHSERVE_BATCH_SIZE'))
        self.amp_dtype = str(os.getenv('TORCHSERVE_AMP_DTYPE'))


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

        logger.info(f"TORCHSERVE_MODEL_NAME is set to {model_name}.")
        logger.info(f"TORCHSERVE_VOCODER_MODEL_NAME is set to {vocoder_model_name}.")
        logger.info(f"TORCHSERVE_DEVICE_TYPE is set to {self.device_type}.")
        logger.info(f"TORCHSERVE_BATCH_SIZE is set to {self.batch_size}.")
        logger.info(f"TORCHSERVE_AMP_DTYPE is set to {self.amp_dtype}.")

        try:
            ipex._C.disable_jit_linear_repack()
            torch._C._jit_set_texpr_fuser_enabled(False)
        except Exception:
            logger.warning("Failed to execute ipex._C.disable_jit_linear_repack() and torch._C._jit_set_texpr_fuser_enabled(False). Proceeding without it.")
            pass

        try:
            self.model = SpeechT5ForTextToSpeech.from_pretrained(model_name)
            self.processor = SpeechT5Processor.from_pretrained(model_name)
            self.vocoder = SpeechT5HifiGan.from_pretrained(vocoder_model_name)
            self.model = self.model.to(memory_format=torch.channels_last)
            self.model.eval()
            self.vocoder = self.vocoder.to(memory_format=torch.channels_last)
            self.vocoder.eval()            

            self.model = ipex.llm.optimize(
                self.model,
                dtype=self.amp_dtype,
                inplace=True,
                deployment_mode=True,
            )
            self.vocoder = ipex.llm.optimize(
                self.vocoder,
                dtype=self.amp_dtype,
                inplace=True,
                deployment_mode=True,
            )
            self.voice = "default"
            # Fetch default speaker embedding
            try:
                self.default_speaker_embedding = torch.load("/home/user/spk_embed_default.pt").to(self.device_type)
            except Exception as e:
                logger.error(f"Error loading default speaker embedding: {str(e)}")
                logger.warning("Warning! Need to prepare speaker_embeddings, will use the backup embedding.")
                self.default_speaker_embedding = torch.zeros((1, 512)).to(self.device_type)

            self.initialized = True
            logger.info(f"Model '{model_name}' loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model '{model_name}': {str(e)}")
            raise


    def split_long_text_into_batch(self, text, batch_length=128):
        """Batch the long text into sequences of shorter sentences."""
        res = []
        hitted_ends = [",", ".", "?", "!", "。", ";", " "]
        idx = 0
        cur_start = 0
        cur_end = -1
        while idx < len(text):
            if idx - cur_start > batch_length:
                if cur_end != -1 and cur_end > cur_start:
                    res.append(text[cur_start : cur_end + 1])
                else:
                    cur_end = cur_start + batch_length - 1
                    res.append(text[cur_start : cur_end + 1])
                idx = cur_end
                cur_start = cur_end + 1
            if text[idx] in hitted_ends:
                cur_end = idx
            idx += 1
        # deal with the last sequence
        if cur_start < len(text):
            last_chunk = text[cur_start:]
            last_punc_idx = max([last_chunk.rfind(punc) for punc in hitted_ends[:-1]])  # exclude " "
            if last_punc_idx != -1:
                last_chunk = last_chunk[: last_punc_idx + 1]
                res.append(last_chunk[: last_punc_idx + 1])
            else:
                res.append(last_chunk)
        res = [i + "." for i in res]  # avoid unexpected end of sequence
        return res

    def tts(self, text, voice="default"):
        if self.voice != voice:
            try:
                logger.info(f"Loading spk embedding with voice: {voice}.")
                self.default_speaker_embedding = torch.load("spk_embed_{voice}.pt")
                self.voice = voice
            except Exception as e:
                print(e)
        all_speech = np.array([])
        text = self.split_long_text_into_batch(text, batch_length=100)
        inputs = self.processor(text=text, padding=True, max_length=128, return_tensors="pt")
        logger.info(f"[SpeechT5] batch size: {inputs['input_ids'].size(0)}")
        with torch.no_grad(), torch.cpu.amp.autocast(enabled=True):
            waveforms, waveform_lengths = self.model.generate_speech(
                inputs["input_ids"].to(self.device),
                speaker_embeddings=self.default_speaker_embedding.to(self.device),
                attention_mask=inputs["attention_mask"].to(self.device),
                vocoder=self.vocoder,
                return_output_lengths=True,
            )
        for i in range(waveforms.size(0)):
            all_speech = np.concatenate([all_speech, waveforms[i][: waveform_lengths[i]].cpu().numpy()])
        return all_speech

    def preprocess(self, requests):
        texts = [] 
        bodies = [data.get("data") or data.get("body") for data in requests]
        for body in bodies:
            input_text = body['inputs']
            logger.debug(f"Received input_text: {input_text}")
            if isinstance(input_text, dict):
                input_text = body['inputs'][0]
            text = list(map(lambda x: x.replace("\n", " "), input_text))
            texts.append((text[0], body.get("voice", "default")))
        logger.debug(f"Received texts: {texts}")
        return texts


    def inference(self, input_batch):
        speeches =[]
        logger.debug(f"Received input_batch: {input_batch}")
        for input_data in input_batch:
            speech = self.tts(input_data[0], voice=input_data[1])
            speeches.append(speech)
        return speeches

    def postprocess(self, data):
        logger.debug(f"Received data: {data}")
        response = [chunk.tolist() for chunk in data] 
        return response