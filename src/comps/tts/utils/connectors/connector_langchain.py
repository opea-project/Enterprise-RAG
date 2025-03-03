import asyncio
import json

from typing import Optional

from comps import get_opea_logger
from comps.tts.utils.connectors.connector import TTSConnector

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class MosecTTS:
    async def synthesize(self, text: str) -> bytes:
        try:
            response = await self.async_client.post(
                json={"inputs": text}
            )
            return response.content

        except Exception as e:
            logger.exception(f"Error synthesizing speech: {e}")
            raise


class OVMSTTS:
    """
    Implementation of OVMSTTS with usage of HuggingFaceEndpointEmbeddings.
    Attributes:
        model_name (str): The name of the model.
        input_name (str): The name of the input. Defaults to None.
    Methods:
        get_input_name(url: str) -> str:
            Retrieves the input name from the model.
        synthesize(text: str) -> bytes:
            Synthesizes speech from text.
    """

    model_name: str
    input_name: str = None

    async def get_input_name(self, url: str) -> str:
        if self.input_name is None:
            import aiohttp
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        response_text = await response.text()
                        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)

                        self.input_name = json.loads(response_text)["inputs"][0]["name"]

            except aiohttp.ClientError as e:
                logger.error(f"Request failed: {e}")
                raise
            except json.JSONDecodeError as e:
                logger.error(f"JSON decoding failed: {e}")
                raise
            except KeyError as e:
                logger.error(f"Key error: {e}")
                raise
        return self.input_name

    async def synthesize(self, text: str) -> bytes:
        endpoint = f"v2/models/{self.model_name}"
        url = f"{self.model}/{endpoint}"

        try:
            from huggingface_hub import (
                    AsyncInferenceClient,
                )
            self.async_client = AsyncInferenceClient(
                    model=f"{url}/infer",
                )
        except ImportError as e:
            error_message =  "Could not import huggingface_hub python package.\n" \
                             "Please install it with `pip install huggingface_hub`.\n"  \
                             f"Error: {e}"
            logger.exception(error_message)
            raise

        try:
            input_name = await self.get_input_name(url)
        except Exception:
            raise

        input_data = {
            "name": input_name,
            "shape": [1],
            "datatype": "BYTES",
            "data": [text]
        }

        try:
            response = await self.async_client.post(
                json={"inputs": [input_data]}
            )
            response_data = json.loads(response.decode())
            if "outputs" in response_data and len(response_data["outputs"]) > 0:
                audio_data = response_data["outputs"][0]["data"]
                if audio_data:
                    return audio_data
        except Exception as e:
            logger.exception(f"Error synthesizing speech: {e}")
            raise

        return b''


SUPPORTED_INTEGRATIONS = {
    "tei": MosecTTS,  # Update this to the appropriate TTS model class
    "torchserve": MosecTTS,
    "mosec": MosecTTS,
    "ovms": OVMSTTS,
}

class LangchainTTS(TTSConnector):
    """
    Connector class for Text-to-Speech (TTS) models.

    Args:
        model_name (str): The name of the model.
        model_server (str): The model server to use.
        endpoint (str): The endpoint for the model server.
        api_config (Optional[dict]): Additional configuration for the API (default: None).

    Attributes:
        _endpoint (str): The endpoint for the model server.
        _model_server (str): The model server to use.
        _tts_model (TTSModel): The selected TTS model.
    """
    _instance = None

    def __new__(cls, model_name: str, model_server: str, endpoint: str, api_config: Optional[dict] = None):
        if cls._instance is None:
            cls._instance = super(LangchainTTS, cls).__new__(cls)
            cls._instance._initialize(model_name, model_server, endpoint, api_config)
        else:
            if (cls._instance._model_name != model_name or
                cls._instance._model_server != model_server):
                logger.warning(f"Existing LangchainTTS instance has different parameters: "
                              f"{cls._instance._model_name} != {model_name}, "
                              f"{cls._instance._model_server} != {model_server}, "
                              "Proceeding with the existing instance.")
        return cls._instance

    def _initialize(self, model_name: str, model_server: str, endpoint: str, api_config: Optional[dict] = None):
        super().__init__(model_name, model_server, endpoint)
        self._tts_model = self._select_tts_model()

        if api_config is not None:
            self._set_api_config(api_config)

        asyncio.run(self._validate())

    def _select_tts_model(self, **kwargs) -> TTSModel:
        """
        Selects the appropriate TTS model based on the model server.

        Returns:
            TTSModel: The selected TTS model.

        Raises:
            ValueError: If the model server is invalid.
        """
        if self._model_server not in SUPPORTED_INTEGRATIONS:
            error_message = f"Invalid model server: {self._model_server}. Available servers: {list(SUPPORTED_INTEGRATIONS.keys())}"
            logger.error(error_message)
            raise ValueError(error_message)

        if "model" not in kwargs:
            if self._model_server == "torchserve":
                self._endpoint = self._endpoint.rstrip('/')
                kwargs["model"] = self._endpoint + f"/predictions/{self._model_name.split('/')[-1]}"

            elif self._model_server == "mosec":
                kwargs["model"] = self._endpoint.rstrip('/') + "/synthesize"
            else:
                kwargs["model"] = self._endpoint

        if self._model_server == "ovms":
            kwargs["model_name"] = self._model_name

        return SUPPORTED_INTEGRATIONS[self._model_server](**kwargs)

    async def synthesize_speech(self, text: str) -> bytes:
        """
        Synthesizes speech from text.

        Args:
            text (str): The text to synthesize.

        Returns:
            bytes: The synthesized speech audio.
        """
        try:
            output = await self._tts_model.synthesize(text)
        except Exception as e:
            logger.exception(f"Error synthesizing speech: {e}")
            raise

        return output

    def change_configuration(self, **kwargs) -> None:
        """
        Changes the configuration of the TTS model.

        Args:
            **kwargs: The new configuration parameters.
        """
        self._tts_model = self._select_tts_model(**kwargs)
