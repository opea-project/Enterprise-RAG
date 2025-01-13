# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import List, Tuple
from datetime import datetime
from beanie import Document, PydanticObjectId
from comps import get_opea_logger
from comps.cores.utils.mongodb import OPEAMongoConnector

from comps.system_fingerprint.utils.object_document_mapper import (
    RerankerParams,
    LLMParams,
    ComponentDetails,
    Fingerprint,
    Argument,
    ComponentConfiguration,
    ComponentTopology,
    LLMGuardInputGuardrailParams,
    LLMGuardOutputGuardrailParams,
    PackedParams,
    AnonymizeModel,
    BanCodeModel,
    BanCompetitorsModel,
    BanSubstringsModel,
    BanTopicsModel,
    CodeModel,
    GibberishModel,
    InvisibleText,
    LanguageModel,
    PromptInjectionModel,
    RegexModel,
    SecretsModel,
    SentimentModel,
    TokenLimitModel,
    ToxicityModel,
    BiasModel,
    JSONModel,
    LanguageSameModel,
    MaliciousURLsModel,
    NoRefusalModel,
    NoRefusalLightModel,
    ReadingTimeModel,
    FactualConsistencyModel,
    RelevanceModel,
    SensitiveModel,
    URLReachabilityModel,
    DeanonymizeModel
)

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

document_models = [
    RerankerParams, ComponentDetails, Fingerprint, Argument,
    ComponentConfiguration, ComponentTopology, LLMGuardInputGuardrailParams,
    LLMGuardOutputGuardrailParams, PackedParams, LLMParams, AnonymizeModel,
    BanCodeModel, BanCompetitorsModel, BanSubstringsModel, BanTopicsModel,
    CodeModel, GibberishModel, InvisibleText, LanguageModel,
    PromptInjectionModel, RegexModel, SecretsModel, SentimentModel,
    TokenLimitModel, ToxicityModel, BiasModel, JSONModel, LanguageSameModel,
    MaliciousURLsModel, NoRefusalModel, NoRefusalLightModel, ReadingTimeModel,
    FactualConsistencyModel, RelevanceModel, SensitiveModel,
    URLReachabilityModel, DeanonymizeModel
]


class OPEASystemFingerprintController(OPEAMongoConnector):
    def __init__(self, db_name, mongodb_host, mongodb_port):
        super().__init__(host=mongodb_host,
                         port=mongodb_port,
                         documents=document_models,
                         db_name=db_name)

        self.database = self.client[db_name]
        self.current_arguments = None
        self.current_component_info = None
        self.current_fingerprint = None
        self.existing_collections = None

    async def init_async(self) -> None:
        """
        Initializes the MongoDB and sets up the system fingerprint.

        Raises:
            Exception: If failed to initialize MongoDB.
        """
        try:
            await super().init_async()
            await self._setup()
        except Exception as e:
            err_msg = "Failed to initialize MongoDB"
            logger.exception(err_msg)
            raise Exception(f"{err_msg}: {e}")

    async def _setup(self) -> None:
        """
        Sets up the system fingerprint by checking and ingesting defaults,
        and updating the current data.

        Raises:
            Exception: If failed to setup system fingerprint.

        """
        try:
            await self._check_and_ingest_defaults()
            await self._update_current_data()
        except Exception as e:
            err_msg = "Failed to setup system fingerprint"
            logger.exception(err_msg)
            raise Exception(f"{err_msg}: {e}")

    async def _get_existing_collections(self) -> None:
        """
        Retrieves the existing collections from the database.

        Raises:
            Exception: If there is an error retrieving the existing collections.
        """
        try:
            self.existing_collections = await self.database.list_collection_names()
        except Exception as e:
            err_msg = "Failed to get existing collections"
            logger.exception(err_msg)
            raise Exception(f"{err_msg}: {e}")

    async def _update_current_data(self) -> None:
        """
        Update the current data by retrieving the latest fingerprint, arguments, and component details.

        Raises:
            Exception: If there is an error while updating the current data.
        """
        try:
            fingerprints = await Fingerprint.find().sort("-timestamp").to_list()
            self.current_fingerprint = fingerprints[0]
            self.current_arguments = await Argument.get(self.current_fingerprint.fingerprint[Argument.__name__])
            self.current_component_info = await ComponentDetails.get(self.current_fingerprint.fingerprint[ComponentDetails.__name__])
        except Exception as e:
            err_msg = "Failed to update current data"
            logger.exception(err_msg)
            raise Exception(f"{err_msg}: {e}")

    async def _check_and_ingest_defaults(self) -> None:
        """
        Checks if the required collections exist and ingests default documents if they are missing.

        Raises:
            Exception: If there is an error while checking and ingesting defaults.
        """
        try:
            await self._get_existing_collections()
            required_collections = [
                Argument.__name__,
                ComponentDetails.__name__,
                Fingerprint.__name__
            ]
            missing_collections = [
                name for name in required_collections if name not in self.existing_collections]

            for collection_name in missing_collections:
                await self._create_default_documents(collection_name)
                await self._get_existing_collections()
        except Exception as e:
            err_msg = "Failed to check and ingest defaults"
            logger.exception(err_msg)
            raise Exception(f"{err_msg}: {e}")

    async def _create_default_documents(self, collection_name: str) -> None:
        """
        Creates default documents based on the given collection name.

        Args:
            collection_name (str): The name of the collection.

        Raises:
            Exception: If failed to create default documents.
        """
        try:
            if collection_name == Argument.__name__:
                default_arguments = await self._create_default_arguments()
                await default_arguments.insert()

            if collection_name == ComponentDetails.__name__:
                default_cfg = await self._create_default_cfg()
                await default_cfg.insert()
                self.current_component_info = default_cfg

            if collection_name == Fingerprint.__name__:
                await self._update_fingerprint()
                fingerprints = await Fingerprint.find().sort("-timestamp").to_list()
                if fingerprints:
                    self.current_fingerprint = fingerprints[0]
        except Exception as e:
            err_msg = "Failed to create default documents"
            logger.exception(err_msg)
            raise Exception(f"{err_msg}: {e}")

    async def _create_default_arguments(self) -> Argument:
        """
        Creates and returns the default arguments for the system fingerprint.

        Returns:
            Argument: The default arguments for the system fingerprint.

        Raises:
            Exception: If there is an error creating the default arguments.
        """
        try:
            default_arguments = Argument(
                timestamp=datetime.now(),
                parameters=PackedParams(
                    llm=LLMParams(),
                    reranker=RerankerParams(),
                    input_guard=LLMGuardInputGuardrailParams(
                        anonymize=AnonymizeModel(),
                        ban_code=BanCodeModel(),
                        ban_competitors=BanCompetitorsModel(),
                        ban_substrings=BanSubstringsModel(),
                        ban_topics=BanTopicsModel(),
                        code=CodeModel(),
                        gibberish=GibberishModel(),
                        invisible_text=InvisibleText(),
                        language=LanguageModel(),
                        prompt_injection=PromptInjectionModel(),
                        regex=RegexModel(),
                        secrets=SecretsModel(),
                        sentiment=SentimentModel(),
                        token_limit=TokenLimitModel(),
                        toxicity=ToxicityModel()
                    ),
                    output_guard=LLMGuardOutputGuardrailParams(
                        ban_competitors=BanCompetitorsModel(),
                        ban_substrings=BanSubstringsModel(),
                        ban_topics=BanTopicsModel(),
                        bias=BiasModel(),
                        code=CodeModel(),
                        deanonymize=DeanonymizeModel(),
                        json_scanner=JSONModel(),
                        language=LanguageModel(),
                        language_same=LanguageSameModel(),
                        malicious_urls=MaliciousURLsModel(),
                        no_refusal=NoRefusalModel(),
                        no_refusal_light=NoRefusalLightModel(),
                        reading_time=ReadingTimeModel(),
                        factual_consistency=FactualConsistencyModel(),
                        gibberish=GibberishModel(),
                        regex=RegexModel(),
                        relevance=RelevanceModel(),
                        sensitive=SensitiveModel(),
                        sentiment=SentimentModel(),
                        toxicity=ToxicityModel(),
                        url_reachability=URLReachabilityModel(),
                        output_guard_streaming=True
                    )
                )
            )
            return default_arguments
        except Exception as e:
            err_msg = "Error creating default arguments"
            logger.exception(err_msg)
            raise Exception(f"{err_msg}: {e}")

    async def _update_fingerprint(self) -> None:
        """
        Updates the system fingerprint by retrieving the latest component details and arguments.
        If the fingerprint does not exist in the database, it is inserted.

        Raises:
            Exception: If there is an error updating the fingerprint.
        """
        try:
            latest_details = await ComponentDetails.find().sort("-timestamp").to_list()
            latest_arguments = await Argument.find().sort("-timestamp").to_list()

            argument_ids = [str(doc.id) for doc in latest_arguments]
            details_ids = [str(doc.id) for doc in latest_details]

            updated_fingerprint = {
                Argument.__name__: argument_ids[0],
                ComponentDetails.__name__: details_ids[0]
            }
            system_fingerprint = Fingerprint(
                timestamp=datetime.now(),
                fingerprint=updated_fingerprint
            )
            query = {"fingerprint": system_fingerprint.fingerprint}
            existing_doc = await ComponentDetails.find_one(query)

            if not existing_doc:
                await system_fingerprint.insert()
        except Exception as e:
            err_name = "Error updating fingerprint"
            logger.exception(err_name)
            raise Exception(f"{err_name}: {e}")

    async def _create_default_cfg(self) -> ComponentDetails:
        """
        Creates a default configuration for the system fingerprint component.

        Returns:
            ComponentDetails: The default component configuration.

        Raises:
            Exception: If there is an error constructing the default configuration.
        """
        # TODO: Add proper default configuration
        try:
            default_cfg = ("", ComponentConfiguration(
                settings={},
                topology=ComponentTopology(
                    namespace="",
                    previous="",
                    next="",
                    downstream=""
                ),
            ))
            default_components_cfg = ComponentDetails(
                timestamp=datetime.now(),
                components=[default_cfg]
            )
            return default_components_cfg
        except Exception as e:
            err_msg = "Failed to construct default configuration"
            logger.exception(err_msg)
            raise Exception(f"{err_msg}: {e}")

    async def _get_latest_documents(self) -> Tuple[List[Argument], List[ComponentDetails]]:
        """
        Retrieves the latest documents from the database.

        Returns:
            A tuple containing two lists:
            - The first list contains the latest argument documents.
            - The second list contains the latest component details documents.

        Raises:
            Exception: If there is an error retrieving the latest documents.
        """
        try:
            latest_fingerprint = await Fingerprint.find().sort("-timestamp").first_or_none()
            if latest_fingerprint:
                argument_ids = [
                    PydanticObjectId(id) for id in latest_fingerprint.arguments_ids]
                topology_ids = [
                    PydanticObjectId(id) for id in latest_fingerprint.topology_ids]

                arguments_docs = await Argument.find({"_id": {"$in": argument_ids}}).to_list()
                topology_docs = await ComponentDetails.find({"_id": {"$in": topology_ids}}).to_list()
                return arguments_docs, topology_docs
            return [], []
        except Exception as e:
            err_msg = "Failed to get latest documents"
            logger.exception(err_msg)
            raise Exception(f"{err_msg}: {e}")

    async def store_arguments(self, inputs: dict) -> None:
        """
        Stores the provided arguments in the database.

        Args:
            inputs (dict): A dictionary containing the arguments to be stored.

        Raises:
            Exception: If there is an error while storing the document.
        """

        arguments = await self._unpack_arguments(
            [(item.name, item.data) for item in inputs])

        try:
            is_duplicate = False

            if isinstance(arguments, Argument):
                latest_doc = await Argument.find_one(sort=[("timestamp", -1)])
                if latest_doc and latest_doc.parameters == arguments.parameters:
                    is_duplicate = True
            elif isinstance(arguments, ComponentDetails):
                latest_doc = await ComponentDetails.find_one(sort=[("timestamp", -1)])
                if latest_doc and latest_doc.components == arguments.components:
                    is_duplicate = True

            if is_duplicate:
                logger.warning(
                    f"Provided duplicate parameters. Skipping storage for {inputs}")
            else:
                await arguments.insert()
                await self._update_fingerprint()
                logger.info(f"Input {inputs} stored successfully.")
        except Exception as e:
            err_msg = "Failed to store document"
            logger.exception(err_msg)
            raise Exception(f"{err_msg}: {e}")

    async def print_all_arguments(self, collection: Document) -> None:
        """
        Prints all arguments in the given collection.

        Args:
            collection (Document): The collection to retrieve arguments from.

        Raises:
            Exception: If there is an error while printing the arguments.
        """
        try:
            all_arguments = await collection.find_all().to_list()
            for argument in all_arguments:
                logger.debug(argument.model_dump_json())
        except Exception as e:
            err_msg = "Failed to print all arguments"
            logger.exception(err_msg)
            raise Exception(f"{err_msg}: {e}")

    async def _unpack_arguments(self, params: List[Tuple[str, dict]]) -> Argument:
        """
        Unpacks the arguments from the given list of tuples and assigns them to the corresponding attributes of the `current_arguments` object.

        Args:
            params (List[Tuple[str, dict]]): A list of tuples containing the parameter name as the first element and the parameter v as the second element.

        Returns:
            Argument: An `Argument` object with the unpacked arguments.
        """
        for param in params:
            if param[0] == "reranker" and param[1] is not None:
                self.current_arguments.parameters.reranker = RerankerParams(
                    **param[1]
                )
            elif param[0] == "llm" and param[1] is not None:
                self.current_arguments.parameters.llm = LLMParams(
                    **param[1]
                )
            elif param[0] == "input_guard" and param[1] is not None:
                for k, v in param[1].items():
                    if k == "anonymize":
                        self.current_arguments.parameters.input_guard.anonymize = AnonymizeModel(
                            **v)
                    elif k == "ban_code":
                        self.current_arguments.parameters.input_guard.ban_code = BanCodeModel(
                            **v)
                    elif k == "ban_competitors":
                        self.current_arguments.parameters.input_guard.ban_competitors = BanCompetitorsModel(
                            **v)
                    elif k == "ban_substrings":
                        self.current_arguments.parameters.input_guard.ban_substrings = BanSubstringsModel(
                            **v)
                    elif k == "ban_topics":
                        self.current_arguments.parameters.input_guard.ban_topics = BanTopicsModel(
                            **v)
                    elif k == "code":
                        self.current_arguments.parameters.input_guard.code = CodeModel(
                            **v)
                    elif k == "gibberish":
                        self.current_arguments.parameters.input_guard.gibberish = GibberishModel(
                            **v)
                    elif k == "invisible_text":
                        self.current_arguments.parameters.input_guard.invisible_text = InvisibleText(
                            **v)
                    elif k == "language":
                        self.current_arguments.parameters.input_guard.language = LanguageModel(
                            **v)
                    elif k == "prompt_injection":
                        self.current_arguments.parameters.input_guard.prompt_injection = PromptInjectionModel(
                            **v)
                    elif k == "regex":
                        self.current_arguments.parameters.input_guard.regex = RegexModel(
                            **v)
                    elif k == "secrets":
                        self.current_arguments.parameters.input_guard.secrets = SecretsModel(
                            **v)
                    elif k == "sentiment":
                        self.current_arguments.parameters.input_guard.sentiment = SentimentModel(
                            **v)
                    elif k == "token_limit":
                        self.current_arguments.parameters.input_guard.token_limit = TokenLimitModel(
                            **v)
                    elif k == "toxicity":
                        self.current_arguments.parameters.input_guard.toxicity = ToxicityModel(
                            **v)
            elif param[0] == "output_guard" and param[1] is not None:
                for k, v in param[1].items():
                    if k == "ban_competitors":
                        self.current_arguments.parameters.output_guard.ban_competitors = BanCompetitorsModel(
                            **v)
                    elif k == "ban_substrings":
                        self.current_arguments.parameters.output_guard.ban_substrings = BanSubstringsModel(
                            **v)
                    elif k == "ban_topics":
                        self.current_arguments.parameters.output_guard.ban_substrings = BanTopicsModel(
                            **v)
                    elif k == "bias":
                        self.current_arguments.parameters.output_guard.bias = BiasModel(
                            **v)
                    elif k == "code":
                        self.current_arguments.parameters.output_guard.code = CodeModel(
                            **v)
                    elif k == "deanonymize":
                        self.current_arguments.parameters.output_guard.deanonymize = DeanonymizeModel(
                            **v)
                    elif k == "json_scanner":
                        self.current_arguments.parameters.output_guard.json_scanner = JSONModel(
                            **v)
                    elif k == "language":
                        self.current_arguments.parameters.output_guard.language = LanguageModel(
                            **v)
                    elif k == "language_same":
                        self.current_arguments.parameters.output_guard.language_same = LanguageSameModel(
                            **v)
                    elif k == "malicious_urls":
                        self.current_arguments.parameters.output_guard.malicious_urls = MaliciousURLsModel(
                            **v)
                    elif k == "no_refusal":
                        self.current_arguments.parameters.output_guard.no_refusal = NoRefusalModel(
                            **v)
                    elif k == "no_refusal_light":
                        self.current_arguments.parameters.output_guard.no_refusal_light = NoRefusalLightModel(
                            **v)
                    elif k == "reading_time":
                        self.current_arguments.parameters.output_guard.reading_time = ReadingTimeModel(
                            **v)
                    elif k == "factual_consistency":
                        self.current_arguments.parameters.output_guard.factual_consistency = FactualConsistencyModel(
                            **v)
                    elif k == "gibberish":
                        self.current_arguments.parameters.output_guard.gibberish = GibberishModel(
                            **v)
                    elif k == "regex":
                        self.current_arguments.parameters.output_guard.regex = RegexModel(
                            **v)
                    elif k == "relevance":
                        self.current_arguments.parameters.output_guard.relevance = RelevanceModel(
                            **v)
                    elif k == "sensitive":
                        self.current_arguments.parameters.output_guard.sensitive = SensitiveModel(
                            **v)
                    elif k == "sentiment":
                        self.current_arguments.parameters.output_guard.sentiment = SentimentModel(
                            **v)
                    elif k == "toxicity":
                        self.current_arguments.parameters.output_guard.toxicity = ToxicityModel(
                            **v)
                    elif k == "url_reachability":
                        self.current_arguments.parameters.output_guard.url_reachability = URLReachabilityModel(
                            **v)

        return Argument(
            timestamp=datetime.now(),
            parameters=self.current_arguments.parameters
        )

    async def pack_arguments(self) -> dict:
        """
        Packs the current arguments into a dictionary.

        Returns:
            dict: A dictionary containing the packed parameters.
        """
        await self._update_current_data()
        packed_parameters = {}

        def remove_id(d):
            if isinstance(d, dict):
                return {k: remove_id(v) for k, v in d.items() if k != 'id'}
            elif isinstance(d, list):
                return [remove_id(i) for i in d]
            else:
                return d

        packed_parameters.update(
            remove_id(
                self.current_arguments.parameters.llm.model_dump()))
        packed_parameters.update(
            remove_id(
                self.current_arguments.parameters.reranker.model_dump()))
        packed_parameters.update(
            {"input_guardrail_params":
                remove_id(
                    self.current_arguments.parameters.input_guard.model_dump())
             })
        packed_parameters.update({"output_guardrail_params": remove_id(
            self.current_arguments.parameters.output_guard.model_dump())})
        return {"parameters": packed_parameters}
