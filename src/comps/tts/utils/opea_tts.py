from comps.tts.utils.connectors import connector_microsoft

class OPEATTS:
    """
    Singleton class for managing TTS with different frameworks as a connector and model servers.
    This class ensures that only one instance is created and reused across the application.
    """

    _instance = None

    def __new__(cls, model_name: str, model_server: str, endpoint: str, connector: str):

        if cls._instance is None:
            cls._instance = super(OPEATTS, cls).__new__(cls)
            cls._instance._initialize(model_name, model_server, endpoint, connector)
        else:
            if (cls._instance._model_name != model_name or
                cls._instance._model_server != model_server or
                cls._instance._connector != connector):
                logger.warning(f"Existing OPEATTS instance has different parameters: "
                              f"{cls._instance._model_name} != {model_name}, "
                              f"{cls._instance._model_server} != {model_server}, "
                              f"{cls._instance._connector} != {connector}. "
                              "Proceeding with the existing instance.")
        return cls._instance

    def _initialize(self, model_name: str, model_server: str, endpoint: str, connector: str) -> None:
        """
        Initializes the OPEATTS instance.

        Args:
            model_name (str): The full name of the model, which may include the repository ID (e.g., 'microsoft/speecht5_tts'). 
                      Internally, only the short name (the last part after the final '/') will be used. For instance, 
                      'speecht5_tts' will be extracted from 'microsoft/speecht5_tts'.

            model_server (str): The URL of the model server.
            endpoint (str): The endpoint for the model server.
            connector (str): The name of the connector framework to be used.
        """
        self._model_name = model_name.split('/')[-1].lower()    # Extract the last part of the model name
        self._model_server = model_server.lower()
        self._endpoint = endpoint
        self._connector = connector.lower()
        self._APIs = []

        self._api_config = None
        if self._is_api_based():
            self._api_config = self._get_api_config()

        self._SUPPORTED_FRAMEWORKS = {
            "microsoft": self._import_microsoft
        }

        if self._connector not in self._SUPPORTED_FRAMEWORKS:
            logger.error(f"Unsupported framework: {self._connector}. "
                          f"Supported frameworks: {list(self._SUPPORTED_FRAMEWORKS.keys())}")
            raise NotImplementedError(f"Unsupported framework: {self._connector}.")
        else:
            self._SUPPORTED_FRAMEWORKS[self._connector]()

    async def run(self, input: Union[TextDoc, TextDocList]) -> Union[EmbedDoc, EmbedDocList]:
        """
        Processes the input document using the OPEATTS.

        Args:
            input (Union[TextDoc, TextDocList]): The input document to be processed.

        Returns:
            Union[EmbedDoc, EmbedDocList]: The processed document.
        """

        docs = []
        if isinstance(input, TextDoc):
            if input.text.strip() == "":
                raise ValueError("Input text is empty. Provide a valid input text.")

            audio = await self.tts_documents([input.text])
            if len(audio) == 1 and isinstance(audio[0], list):
                audio = audio[0]
            res = EmbedDoc(text=input.text, embedding=audio, metadata=input.metadata)
            return res # return EmbedDoc
        else:
            docs_to_parse = input.docs

            docs_to_parse = [s for s in docs_to_parse if s.text.strip()]
            if len(docs_to_parse) == 0:
                raise ValueError("Input text is empty. Provide a valid input text.")

            # Multithreaded executor is needed to enabled batching in the model server
            async def multithreaded_tts_query(doc):
                # TODO: Process a batch of documents instead of handling them one by one
                res_audio = await self.tts_documents([doc.text])

                if len(res_audio) == 1:
                    # For documents of 1 KB or smaller, TorchServe returns the result audio wrapped in an additional list,
                    # extract the inner list to ensure compatibility with the next steps
                    res_audio = res_audio[0]

                return EmbedDoc(text=doc.text, embedding=res_audio, metadata=doc.metadata)


            # Create tasks for each document
            tasks = [multithreaded_tts_query(doc) for doc in docs_to_parse]

            # Run all tasks concurrently
            docs = await asyncio.gather(*tasks)

            return EmbedDocList(docs=docs) # return EmbedDocList


    def _import_microsoft(self) -> None:
        try:
            self.tts_query = connector_microsoft.MicrosoftTTS(self._model_name, self._model_server, self._endpoint, self._api_config).tts_query
            self.tts_documents = connector_microsoft.MicrosoftTTS(self._model_name, self._model_server, self._endpoint, self._api_config).tts_documents
            self.validate_method = connector_microsoft.MicrosoftTTS(self._model_name, self._model_server, self._endpoint, self._api_config)._validate
        except ModuleNotFoundError:
            logger.exception("microsoft module not found. Ensure it is installed if you need its functionality.")
            raise
        except Exception as e:
            logger.exception(f"An unexpected error occurred while initializing the connector_microsoft module {e}")
            raise

    def _get_api_config(self) -> dict:
        try:
            api_config_path = os.environ.get("API_CONFIG_PATH", os.path.join(os.getcwd(), "utils", "api_config", "api_config.yaml"))
            with open(api_config_path, "r") as config:
                return yaml.safe_load(config)
        except FileNotFoundError as e:
            logger.exception(f"API configuration file not found: {e}")
            raise
        except yaml.YAMLError as e:
            logger.exception(f"Error parsing the API configuration file: {e}")
            raise
        except Exception as e:
            logger.exception(f"An unexpected error occurred while loading API configuration: {e}")
            raise

    def _is_api_based(self) -> bool:
        """
        Checks if the model server is API-based.

        Returns:
            bool: True if the model server is API-based, False otherwise.
        """
        if self._model_server in self._APIs:
            return True
        else:
            return False
