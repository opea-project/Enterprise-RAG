# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from abc import ABC
from beanie import Document, init_beanie
import motor.motor_asyncio as motor
from typing import List, Union

from comps import get_opea_logger


logger = get_opea_logger("OPEAMongoConnector")


class OPEAMongoConnector(ABC):
    def __init__(self, host: str, port: int, documents: Union[Document, List[Document]], db_name: str = "OPEA"):
        self.host = host
        self.port = port
        self.db_name = db_name
        self.documents = documents

        if not isinstance(documents, List):
            self.documents = [self.documents]

        conn_url = f"mongodb://{self.host}:{self.port}/{self.db_name}"

        self.client = motor.AsyncIOMotorClient(conn_url)

    async def init_async(self) -> None:
        await init_beanie(database=self.client.get_database(), document_models=self.documents)
        await self.validate()

    def close(self):
        self.client.close()
        logger.info("Connection to database cluster closed.")

    async def validate(self):
        df_database = self.client.get_default_database()
        ping_response = await df_database.command("ping")
        if int(ping_response["ok"]) != 1:
            logger.error("Problem connecting to database cluster.")
            raise Exception("Problem connecting to database cluster.")
        else:
            logger.info("Connected to database cluster.")

    async def insert(self, document: Document):
        if type(document) not in self.documents:
            logger.error(f"Document {document} not found in the list of documents {self.documents}.")
            raise ValueError(f"Document {document} not found in the list of documents {self.documents}.")

        await document.insert()
        return document.id

    async def delete(self, document: Document, id: str):
        if document not in self.documents:
            logger.error(f"Document {document} not found in the list of documents {self.documents}.")
            raise ValueError(f"Document {document} not found in the list of documents {self.documents}.")

        d = await document.get(id)
        if d is None:
            logger.error(f"Document with id: {id} not found.")
            raise Exception(f"Document with id: {id} not found.")

        logger.info(f"Deleting document: {d}")
        return await d.delete()

    async def get_all(self, document: Document):
        if document not in self.documents:
            logger.error(f"Document {document} not found in the list of documents {self.documents}.")
            raise ValueError(f"Document {document} not found in the list of documents {self.documents}.")

        output = await document.find_all().to_list()
        return output

    async def get_by_id(self, document: Document, id: str):
        if document not in self.documents:
            logger.error(f"Document {document} not found in the list of documents {self.documents}.")
            raise ValueError(f"Document {document} not found in the list of documents {self.documents}.")

        output = await document.get(id)
        return output
