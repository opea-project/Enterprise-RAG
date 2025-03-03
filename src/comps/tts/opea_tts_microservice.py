import os
import time
import ast
import requests
from typing import Union
from fastapi import HTTPException
from dotenv import load_dotenv
from utils import sanitize_env, get_opea_logger, change_opea_logger_level
from comps.tts.utils.opea_tts import OPEATTS
from models import TextDoc, TextDocList, EmbedDoc, EmbedDocList
from services import register_microservice, register_statistics, ServiceType, MegaServiceEndpoint, statistics_dict, opea_microservices

# Define the unique service name for the microservice
USVC_NAME='opea_service@opea_tts'

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "impl/microservice/.env"))

# Initialize the logger for the microservice
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

# Initialize an instance of the OPEATTS class with environment variables.
opea_tts = OPEATTS(
    model_name=sanitize_env(os.getenv("TTS_MODEL_NAME")),
    model_server=sanitize_env(os.getenv("TTS_MODEL_SERVER")),
    endpoint=sanitize_env(os.getenv("TTS_MODEL_SERVER_ENDPOINT")),
    connector=sanitize_env(os.getenv("TTS_CONNECTOR")),
)

# Register the microservice with the specified configuration.
@register_microservice(
    name=USVC_NAME,
    service_type=ServiceType.TTS,
    endpoint=str(MegaServiceEndpoint.TTS),
    host="0.0.0.0",
    port=int(os.getenv('TTS_USVC_PORT', default=7000)),
    input_datatype=Union[TextDoc, TextDocList],
    output_datatype=Union[EmbedDoc, EmbedDocList],
    validate_methods=[opea_tts.validate_method]
)
@register_statistics(names=[USVC_NAME])
# Define a function to handle processing of input for the microservice.
# Its input and output data types must comply with the registered ones above.
async def process(input: Union[TextDoc, TextDocList]) -> Union[EmbedDoc, EmbedDocList]:
    """
    Process the input document using the OPEATTS.

    Args:
        input (Union[TextDoc, TextDocList]): The input document to be processed.
    """
    start = time.time()
    logger.debug(f"Received input: {input}")

    try:
        # Pass the input to the 'run' method of the microservice instance
        res = await opea_tts.run(input)

    except ValueError as e:
        logger.exception(f"ValueError occured while validating the input: {str(e)}")
        raise HTTPException(status_code=400,
                            detail=f"ValueError occured while validating the input: {str(e)}"
        )
    except requests.exceptions.HTTPError as e:
        if hasattr(e.response, "status_code") and e.response.status_code == 413:
            raise HTTPException(status_code=413, detail=f"Input text is too long. Provide a valid input text. Error: {ast.literal_eval(e.response.text)['error']}")
        else:
            raise HTTPException(status_code=e.response.status_code, detail=ast.literal_eval(e.response.text)['error'])
    except NotImplementedError as e:
        logger.exception(f"NotImplementedError occured: {str(e)}")
        raise HTTPException(status_code=501,
                            detail=f"NotImplementedError occured: {str(e)}"
        )
    except Exception as e:
         logger.exception(f"An error occurred while processing: {str(e)}")
         raise HTTPException(status_code=500,
                             detail=f"An error occurred while processing: {str(e)}"
    )
    statistics_dict[USVC_NAME].append_latency(time.time() - start, None)
    return res


if __name__ == "__main__":
    # Start the microservice
    opea_microservices[USVC_NAME].start()
    logger.info(f"Started OPEA Microservice: {USVC_NAME}")
