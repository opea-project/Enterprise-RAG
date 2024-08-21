import os

from comps import (
    LLMParamsDoc,
    MegaServiceEndpoint,
    SearchedDoc,
    ServiceType,
    opea_microservices,
    register_microservice,
    register_statistics,
)
from comps.reranks.utils.opea_reranking import OPEAReranker
from langsmith import traceable

config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.ini")
opea_reranker = OPEAReranker(config_file=config_file)


@register_microservice(
    name=opea_reranker.name,
    service_type=ServiceType.RERANK,
    endpoint=str(MegaServiceEndpoint.RERANKING),
    host=opea_reranker.host,
    port=opea_reranker.port,
    input_datatype=SearchedDoc,
    output_datatype=LLMParamsDoc,
)
@traceable(run_type="llm")
@register_statistics(names=[opea_reranker.name])
def process(input: SearchedDoc) -> LLMParamsDoc:
    """
    Process the input document using the OPEAReranker.

    Args:
        input (SearchedDoc): The input document to be processed.

    Returns:
        LLMParamsDoc: The processed document with LLM parameters.
    """
    return opea_reranker.run(input)


if __name__ == "__main__":
    opea_microservices[opea_reranker.name].start()
