# Copyright (C) 2024-2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from typing import List

from comps import get_opea_logger
from comps.cores.proto.docarray import ChatMessage, ChatHistoryName
from comps.cores.utils.mongodb import OPEAMongoConnector

from .documents import ChatHistoryDocument

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

def generate_history_title(history: List[ChatMessage]) -> str:
	return history[0].question[:30] if len(history[0].question) > 30 else history[0].question

class OPEAChatHistoryConnector(OPEAMongoConnector):
    def __init__(self, mongodb_host, mongodb_port) -> None:
        """
        Initializes the OPEAChatHistory instance.
        """
        super().__init__(host=mongodb_host,
                         port=mongodb_port,
                         db_name="CHAT_HISTORY",
                         documents=[ChatHistoryDocument],
                        )

    async def create_new_history(self, chat_history: List[ChatMessage], user_id: str) -> ChatHistoryName:
        """
        Inserts a new chat history into the database.
        """
        try:
            h = ChatHistoryDocument(history=chat_history, user_id=user_id, history_name=f"{generate_history_title(chat_history)}")
            id = await self.insert(h)
        except Exception as e:
            err_msg = f"Error inserting history: {chat_history[0].question} for user_id: {user_id}: {e}"
            logger.error(err_msg)
            raise Exception(err_msg) from e
        logger.info(f"History inserted inserted: {h}")
        return ChatHistoryName(id=str(id), history_name=h.history_name)

    async def append_history(self, history_id: str, chat_history: List[ChatMessage], user_id: str) -> ChatHistoryName:
        """
        Updates an existing chat history in the database.
        """
        try:
            h = await self.get_by_id(ChatHistoryDocument, history_id)
            if not h:
                raise ValueError(f"Chat history with id {history_id} not found.")
            if h.user_id != user_id:
                raise ValueError(f"User ID {user_id} does not match the history's user ID {h.user_id}.")
            h.history.extend(chat_history)
            await h.save()
        except ValueError as e:
            err_msg = f"Error updating history with id: {history_id}: {e}"
            logger.error(err_msg)
            raise ValueError(err_msg) from e
        except Exception as e:
            err_msg = f"Error updating history with id: {history_id}: {e}"
            logger.error(err_msg)
            raise Exception(err_msg) from e
        logger.info(f"History with id: {history_id} updated")
        return ChatHistoryName(id=str(h.id), history_name=h.history_name)

    async def change_history_name(self, history_id: str, history_name: str, user_id: str) -> None:
        """
        Changes the name of an existing chat history in the database.
        """
        try:
            if history_name is None or history_name.strip() == "":
                raise ValueError("History name cannot be empty.")

            if len(history_name) > 250:
                raise ValueError("History name cannot be longer than 250 characters.")

            h = await self.get_by_id(ChatHistoryDocument, history_id)
            if not h:
                raise ValueError(f"Chat history with id {history_id} not found.")
            if h.user_id != user_id:
                raise ValueError(f"User ID {user_id} does not match the history's user ID {h.user_id}.")
            h.history_name = history_name
            await h.save()
        except ValueError as e:
            err_msg = f"Error changing history name with id: {history_id}: {e}"
            logger.error(err_msg)
            raise ValueError(err_msg) from e
        except Exception as e:
            err_msg = f"Error changing history name with id: {history_id}: {e}"
            logger.error(err_msg)
            raise Exception(err_msg) from e
        logger.info(f"History name with id: {history_id} changed to {h.history_name}")

    async def delete_history(self, history_id: str, user_id: str) -> None:
        """
        Deletes a history from the database.
        """
        try:
            h = await self.get_by_id(ChatHistoryDocument, history_id)
            if not h:
                raise ValueError(f"Chat history with id {history_id} not found.")
            if h.user_id != user_id:
                raise ValueError(f"User ID {user_id} does not match the history's user ID {h.user_id}.")
            await self.delete(ChatHistoryDocument, history_id)
        except Exception as e:
            err_name = f"Error deleting history with id: {history_id}: {e}"
            logger.error(err_name)
            raise Exception(err_name) from e
        logger.info(f"History with id: {history_id} deleted")

    async def get_all_histories_for_user(self, user_id: str) -> list[ChatHistoryName]:
        """
        Retrieves all histories for specific user from the database.
        """
        try:
            histories = await ChatHistoryDocument.find(ChatHistoryDocument.user_id == user_id).to_list()
            parsed_histories = [ChatHistoryName(id=str(h.id), history_name=h.history_name) for h in histories]
        except ValueError as e:
            err_msg = f"Error retrieving histories for user: {user_id}: {e}"
            logger.error(err_msg)
            raise ValueError(err_msg) from e
        except Exception as e:
            err_name = f"Error retrieving histories for user: {user_id}: {e}"
            logger.error(err_name)
            raise Exception(err_name) from e
        return parsed_histories

    async def get_history_by_id(self, history_id: str, user_id: str) -> ChatHistoryDocument:
        """
        Retrieves history from the database by its id.
        """
        try:
            h = await self.get_by_id(ChatHistoryDocument, history_id)
            if not h:
                raise ValueError(f"Chat history with id {history_id} not found.")
            if h.user_id != user_id:
                raise ValueError(f"User ID {user_id} does not match the history's user ID {h.user_id}.")
        except ValueError as e:
            err_msg = f"Error retrieving history for user: {user_id} with id: {history_id}: {e}"
            logger.error(err_msg)
            raise ValueError(err_msg) from e
        except Exception as e:
            err_name = f"Error retrieving history for user: {user_id} with id: {history_id}: {e}"
            logger.error(err_name)
            raise Exception(err_name) from e
        return h
