# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import os
import time
from comps.cores.utils.utils import get_boolean_env_var
from utils import opea_dataprep
from comps.cores.mega.constants import MegaServiceEndpoint, ServiceType
from comps.cores.proto.docarray import DataPrepInput, TextDocList
from comps.cores.mega.micro_service import opea_microservices, register_microservice
from comps.cores.mega.base_statistics import register_statistics, statistics_dict
import logging

def start_ingestion_service(opea_dataprep: opea_dataprep.OPEADataprep, opea_microservice_name: str):
    @register_microservice(
        name=opea_microservice_name,
        service_type=ServiceType.DATAPREP,
        endpoint=str(MegaServiceEndpoint.DATAPREP),
        host="0.0.0.0",
        port=9399,
        input_datatype=DataPrepInput,
        output_datatype=TextDocList,
    )
    @register_statistics(names=[opea_microservice_name])
    async def dataprep(input: DataPrepInput) -> TextDocList:

        start = time.time()
        textdocs = await opea_dataprep.dataprep(input=input)
        statistics_dict[opea_microservice_name].append_latency(time.time() - start, None)

        return TextDocList(docs=textdocs)

    opea_microservices[opea_microservice_name].start()

if __name__ == "__main__":
    try:
        dataprep = opea_dataprep.OPEADataprep(
            chunk_size=int(os.getenv("CHUNK_SIZE", 1500)),
            chunk_overlap=int(os.getenv("CHUNK_OVERLAP", 100)),
            process_table=get_boolean_env_var("PROCESS_TABLE", False),
            table_strategy=os.getenv("PROCESS_TABLE_STRATEGY", "fast")
        )

        opea_microservice_name = "opea_service@opea_dataprep"
        start_ingestion_service(dataprep, opea_microservice_name)
    except Exception as e:
        logging.exception(f"Error initializing OPEADataprep: {e}")
