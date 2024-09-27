# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps import get_opea_logger
from comps.cores.utils.mongodb import OPEAMongoConnector

from .documents import PromptDocument

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")


class OPEAPromptRegistryConnector(OPEAMongoConnector):
    def __init__(self, mongodb_host, mongodb_port) -> None:
        """
        Initializes the OPEAPromptRegistry instance.
        """
        super().__init__(host=mongodb_host,
                         port=mongodb_port,
                         documents=[PromptDocument],
                        )

    async def insert_prompt(self, prompt_text: str, filename: str) -> str:
        """
        Inserts a prompt into the database.
        """
        try:
            p = PromptDocument(prompt_text=prompt_text, filename=filename)
            id = await self.insert(p)
        except Exception as e:
            err_name = f"Error inserting prompt: {prompt_text} for filename: {filename}"
            logger.error(err_name)
            raise Exception(f"{err_name}: {e}")
        logger.info(f"Prompt inserted: {p}")
        return str(id)

    async def delete_prompt(self, prompt_id: str) -> None:
        """
        Deletes a prompt from the database.
        """
        try:
            await self.delete(PromptDocument, prompt_id)
        except Exception as e:
            err_name = f"Error deleting prompt with id: {prompt_id}"
            logger.exception(err_name)
            raise Exception(f"{err_name}: {e}")
        logger.info(f"Prompt with id: {prompt_id} deleted")

    async def get_all_prompts(self) -> list:
        """
        Retrieves all prompts from the database.
        """
        try:
            prompts = await self.get_all(PromptDocument)
        except Exception as e:
            err_name = "Error retrieving prompts"
            logger.exception(err_name)
            raise Exception(f"{err_name}: {e}")
        return prompts

    async def get_prompt_by_id(self, prompt_id: str) -> PromptDocument:
        """
        Retrieves a prompt from the database by id.
        """
        try:
            prompt = await self.get_by_id(PromptDocument, prompt_id)
        except Exception as e:
            err_name = f"Error retrieving prompt with id: {prompt_id}"
            logger.exception(err_name)
            raise Exception(f"{err_name}: {e}")
        return prompt

    async def get_prompts_by_filename(self, filename: str) -> list:
        """
        Retrieves prompts from the database by filename.
        """
        try:
            prompts = await PromptDocument.find(PromptDocument.filename == filename).to_list()
        except Exception as e:
            err_name = f"Error retrieving prompts for filename: {filename}"
            logger.exception(err_name)
            raise Exception(f"{err_name}: {e}")
        return prompts

    # TODO: implement more sophisticated search, e.g. based on keywords
    async def get_prompts_by_text(self, text: str) -> list:
        """
        Retrieves prompts from the database by text.
        """
        try:
            prompts = await self.get_all_prompts()
            output = [p for p in prompts if text in p.prompt_text]
        except Exception as e:
            err_name = f"Error retrieving prompts for text: {text}"
            logger.exception(err_name)
            raise Exception(f"{err_name}: {e}")
        return output

    async def get_prompts_by_filename_and_text(self, filename: str, text: str) -> list:
        """
        Retrieves prompts from the database by filename and text.
        """
        try:
            prompts = await PromptDocument.find(PromptDocument.filename == filename).to_list()
            output = [p for p in prompts if text in p.prompt_text]
        except Exception as e:
            err_name = f"Error retrieving prompts for text: {text}"
            logger.exception(err_name)
            raise Exception(f"{err_name}: {e}")
        return output
