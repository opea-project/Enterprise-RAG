import asyncio
from typing import Optional

from comps import get_opea_logger
from comps.tts.utils.connectors.connector import TTSConnector

SUPPORTED_INTEGRATIONS = {
    "tei": TextEmbeddingsInference,  # Update this to the appropriate TTS model class
}

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class LlamaIndexTTS(TTSConnector):
    """
    A class representing a TTS model using LlamaIndex.

    Args:
        model_name (str): The name of the model.
        model_server (str): The server hosting the model.
        endpoint (str): The endpoint for accessing the model.
        **kwargs: Additional keyword arguments for configuring the TTS model.

    Attributes:
        _model_name (str): The name of the model.
        _endpoint (str): The endpoint for accessing the model.
        _model_server (str): The server hosting the model.
        _tts_model (BaseTTSModel): The TTS model object for performing TTS operations.

    Methods:
        synthesize_speech(text: str) -> bytes: Synthesizes speech from text.
        change_configuration(**kwargs): Changes the configuration of the TTS model.

    Raises:
        Exception: If there is an error initializing the TTS model.

    """
    _instance = None

    def __new__(cls, model_name: str, model_server: str, endpoint: str, api_config: Optional[dict] = None):
        if cls._instance is None:
            cls._instance = super(LlamaIndexTTS, cls).__new__(cls)
            cls._instance._initialize(model_name, model_server, endpoint, api_config)
        else:
            if (cls._instance._model_name != model_name or
                cls._instance._model_server != model_server):
                logger.warning(f"Existing LlamaIndexTTS instance has different parameters: "
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

    def _select_tts_model(self, **kwargs) -> BaseTTSModel:
        """
        Selects the appropriate TTS model based on the model server.

        Returns:
            BaseTTSModel: An instance of the selected TTS model.

        """
        if self._model_server not in SUPPORTED_INTEGRATIONS:
            error_message = f"Invalid model server: {self._model_server}. Available servers: {list(SUPPORTED_INTEGRATIONS.keys())}"
            logger.error(error_message)
            raise ValueError(error_message)

        return SUPPORTED_INTEGRATIONS[self._model_server](model_name=self._model_name, base_url=self._endpoint, **kwargs)

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
            **kwargs: Additional keyword arguments for configuring the TTS model.

        """
        self._tts_model = self._select_tts_model(**kwargs)
