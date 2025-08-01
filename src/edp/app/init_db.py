# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from dotenv import load_dotenv
import os
from comps.cores.mega.logger import change_opea_logger_level, get_opea_logger
from app.models import Base
from sqlalchemy import create_engine
from app.database import DATABASE_URL

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(__file__), "./.env"))

# Initialize the logger for the microservice
logger = get_opea_logger("edp_microservice")
logger_level = os.getenv("OPEA_LOGGER_LEVEL", "INFO")
change_opea_logger_level(logger, log_level=logger_level)

engine = create_engine(DATABASE_URL, echo=True if logger_level == "DEBUG" else False)
Base.metadata.create_all(bind=engine, checkfirst=True)
