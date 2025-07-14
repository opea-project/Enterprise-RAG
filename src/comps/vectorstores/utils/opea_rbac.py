import os
import requests
import json
from comps.cores.mega.logger import change_opea_logger_level, get_opea_logger

# Initialize the logger for the microservice
logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}")
change_opea_logger_level(logger, log_level=os.getenv("OPEA_LOGGER_LEVEL", "INFO"))

def retrieve_bucket_list(auth_header: str) -> list:
    edp_backend = os.getenv("EDP_BACKEND_ENDPOINT", "http://edp-backend.edp.svc:5000")
    if not auth_header or auth_header == "":
        raise ValueError("Authorization header is missing or empty while retrieving RBAC bucket list")

    r = requests.get(f"{edp_backend}/api/list_bucket_with_permissions", headers={ "Authorization": auth_header })
    if r.status_code != 200:
        logger.error(f"Failed to retrieve bucket list: {r.status_code} - {r.text}.")
        return []

    try:
        bucket_names = r.json()
        logger.debug(f"List of buckets with permissions: {bucket_names}")
        return bucket_names
    except json.JSONDecodeError:
        logger.error(f"Error decoding json response: {r.text}")
        return []
