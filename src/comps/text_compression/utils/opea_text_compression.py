import time

from typing import List, Optional
from docarray import DocList

from comps.cores.proto.docarray import TextDoc, TextCompressionTechnique
from comps.cores.mega.logger import get_opea_logger
from comps.text_compression.utils.compressors import header_footer_stripper_compressor, ranking_aware_deduplication

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class OPEATextCompressor:
    """Singleton class for handling token compression using various techniques."""
    _instance = None

    def __new__(cls, default_techniques: str = None):

        if cls._instance is None:
            cls._instance = super(OPEATextCompressor, cls).__new__(cls)
            cls._instance._initialize(default_techniques)
        else:
            if (cls._instance.default_techniques_str != default_techniques):
                logger.warning(f"Existing OPEATextCompressor instance has different parameters: "
                              f"{cls._instance.default_techniques_str} != {default_techniques}, "
                              "Proceeding with the existing instance.")
        return cls._instance

    def _initialize(self, default_techniques: str = None):
        """
        Initialize the token compressor.
        """
        self.default_techniques_str = default_techniques
        self.default_techniques = [item.strip() for item in default_techniques.split(',')] if default_techniques else []

        self._SUPPORTED_TECHNIQUES = {
            "header_footer_stripper": header_footer_stripper_compressor.HeaderFooterStripper,
            "ranking_aware_deduplication": ranking_aware_deduplication.RankedDeduplicator,
            # Add more compression techniques here as needed
        }

        for technique in self.default_techniques:
            if technique not in self._SUPPORTED_TECHNIQUES:
                raise ValueError(f"Unsupported compression technique: {technique}. "
                                 f"Available techniques: {list(self._SUPPORTED_TECHNIQUES.keys())}")

        self.initialized_techniques = self._init_compression_techniques()
        logger.info(f"Default compression techniques set to: {self.default_techniques}")

    def _init_compression_techniques(self):
        """Initialize all available compression techniques."""
        self.initialized_techniques = {}
        load_start_time = time.time()
        for name, compressor_class in self._SUPPORTED_TECHNIQUES.items():
            try:
                # Dynamically load the compressor class
                compressor = compressor_class()
                self.initialized_techniques[name] = compressor
                logger.debug(f"Loaded compression technique '{name}'")
            except Exception as e:
                logger.error(f"Failed to load compression technique '{name}': {e}")

        if not self.initialized_techniques:
            raise ValueError("No compression techniques loaded. Please check your configuration.")

        load_duration = time.time() - load_start_time
        logger.info(f"Loaded {len(self.initialized_techniques)} compression techniques. Compression techniques loaded in {load_duration:.2f} seconds.")
        return self.initialized_techniques

    async def compress_docs(self, docs: DocList[TextDoc], techniques: Optional[List[TextCompressionTechnique]] = None) -> DocList[TextDoc]:
        """
        Compress the text in each document using the specified technique.

        Args:
            docs (DocList[TextDoc]): The documents containing text to compress.
            techniques (List[TextCompressionTechnique], optional): Specify the compression techniques to apply.

        Returns:
            DocList[TextDoc]: The documents with compressed text.
        """
        compressed_docs = DocList[TextDoc]()

        for doc in docs:
            if doc.text.strip() == "":
                compressed_doc = TextDoc(text="", metadata=doc.metadata)
            else:
                # Apply compression technique
                compressed_text = await self.compress(doc.text, techniques)

                compressed_doc = TextDoc(
                    text=compressed_text,
                    metadata=doc.metadata.copy() if doc.metadata else {}
                )

                if compressed_doc.metadata is None:
                    compressed_doc.metadata = {}

            techniques_str = ", ".join(technique.name for technique in techniques) if techniques else self.default_techniques_str
            compressed_doc.metadata["compression_technique"] = techniques_str
            compressed_doc.metadata["original_length"] = len(doc.text)
            compressed_doc.metadata["compressed_length"] = len(compressed_text)
            compressed_doc.metadata["compression_ratio"] = len(compressed_text) / len(doc.text) if len(doc.text) > 0 else 1.0

            compressed_docs.append(compressed_doc)

        return compressed_docs

    async def compress(self, text: str, techniques: Optional[List[TextCompressionTechnique]] = None) -> str:
        """
        Compress the given text using the specified technique.

        Args:
            text (str): The text to compress.
            techniques (List[TextCompressionTechnique], optional): List of compression techniques to apply.
                If None, a default technique setup will be used.

        Returns:
            str: The compressed text.
        """
        if not text:
            return ""

        if techniques is not None:
            techniques_str = ", ".join(technique.name for technique in techniques)
            logger.info(f"Requested compression techniques: {techniques_str}")
            for technique in techniques:
                if technique.name not in self.initialized_techniques:
                    err_msg = f"Unknown compression technique: {technique.name}. Available techniques: {list(self._SUPPORTED_TECHNIQUES.keys())}"
                    logger.error(err_msg)
                    raise ValueError(err_msg)

                logger.info(f" - {technique.name}: {self.initialized_techniques[technique.name]}")
                try:
                    params = technique.parameters if technique.parameters else {}
                    text = self.initialized_techniques[technique.name].compress_text(text, **params)
                except Exception as e:
                    err_msg = f"Error applying compression technique {technique}: {e}"
                    logger.error(err_msg)
                    raise Exception(err_msg)
            return text
        else:
            logger.info(f"No specific compression technique requested. Using default: {self.default_techniques}.")

            if not self.default_techniques:
                war_msg = "No default compression techniques specified. Skipping."
                logger.warning(war_msg)
                return text

            for c_name in self.default_techniques:
                print(f" - {c_name}: {self.initialized_techniques[c_name]}")

                try:
                    logger.info(f"Applying compression technique: {c_name}")
                    text = self.initialized_techniques[c_name].compress_text(text)
                    logger.info(f"Applied compression technique: {c_name}")
                except Exception as e:
                    err_msg = f"Error applying compression techniques {self.default_techniques_str}: {e}"
                    logger.error(err_msg)
                    raise Exception(err_msg)
            return text
