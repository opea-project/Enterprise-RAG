import requests

from typing import List
from json import JSONDecodeError

from comps import (
    get_opea_logger,
    PrevQuestionDetails
)

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

USER_PREFIXES = {
    "en": "User",
    "pl": "Użytkownik"
}

ASSISTANT_PREFIXES = {
    "en": "Assistant",
    "pl": "Asystent"
}

class ChatHistoryHandler:
    def __init__(self, chat_history_endpoint: str = None, prompt_template_language: str = "en") -> None:
        """
        Initializes the ChatHistoryHandler instance.
        """
        self.chat_history_endpoint = chat_history_endpoint
        self.prompt_template_language = prompt_template_language

        if self.chat_history_endpoint is not None and self.chat_history_endpoint.strip() != "":
            r = requests.get(f"{self.chat_history_endpoint}/v1/health_check", headers={"Content-Type": "application/json"})
            if r.status_code != 200 and "chat_history" not in r.text:
                err_msg = f"Chat history service is not available at {self.chat_history_endpoint}. Please check the endpoint. Response: {r.status_code} - {r.text}"
                logger.error(err_msg)
                raise ValueError(err_msg)
            logger.info(f"Chat history service is available at {self.chat_history_endpoint}")
        else:
            logger.info("Chat history endpoint is not set. No chat history will be retrieved.")


    def validate_chat_history(self, con_history: List[PrevQuestionDetails]) -> bool:
        if con_history is None:
            return False

        if len(con_history) == 0:
            return False

        if_not_empty_history = False
        for h in con_history:
            if h.question.strip() != "" or h.answer.strip() != "":
                if_not_empty_history = True
        return if_not_empty_history


    def remove_history_blocked_by_guardrails(self, con_history: List[PrevQuestionDetails]) -> List[PrevQuestionDetails]:
        """
        Removes any history entries that are blocked by guardrails.
        """
        history_without_blocked_answers = []
        for h in con_history:
            if h.answer == "I'm sorry, I cannot assist you with your prompt.":
                continue
            history_without_blocked_answers.append(h)
        return history_without_blocked_answers

    def retrieve_chat_history(self, history_id: str, access_token: str) -> List[PrevQuestionDetails]:
        """
        Retrieves the conversation history by its ID.
        """
        if history_id is None:
            return []

        if self.chat_history_endpoint is None or self.chat_history_endpoint.strip() == "":
            logger.warning("Chat history endpoint is not set. No conversation history will be retrieved.")
            return []

        logger.info(f"Retrieving conversation history for ID: {history_id}")

        if not access_token or access_token == "":
            logger.warning("Authorization header is missing or empty while retrieving conversation history. Conversation history won't be retrieved.")
            return []

        r = requests.get(f"{self.chat_history_endpoint}/v1/chat_history/get?history_id={history_id}", headers={"Authorization": f"Bearer {access_token}",
                                                                                                               "Content-Type": "application/json"})
        if r.status_code == 400:
            err_msg = f"Bad request while retrieving conversation history: {r.text}"
            logger.error(err_msg)
            raise ValueError(err_msg)
        elif r.status_code != 200 and r.status_code != 400:
            err_msg = f"Failed to retrieve conversation history: {r.status_code} - {r.text}."
            logger.error(err_msg)
            raise Exception(err_msg)

        try:
            con_history = r.json()
            logger.debug(f"Received history: {con_history}")
            con_history = [PrevQuestionDetails(question=h["question"], answer=h["answer"]) for h in con_history["history"]]
            return con_history
        except JSONDecodeError as e:
            err_msg = f"Error decoding JSON response while retrieving conversation history: {str(e)}"
            logger.error(err_msg)
            raise JSONDecodeError(err_msg) from e
        except Exception as e:
            err_msg = f"Error retrieving conversation history: {str(e)}"
            logger.error(err_msg)
            raise Exception(err_msg) from e


    def parse_chat_history(self, history_id: str, type: str, access_token: str, params: dict = {}) -> str:
        """
        Parses the conversation history for a given ID and type.
        """
        if history_id is None:
            logger.warning("History ID is None. No conversation history will be parsed.")
            return ""

        con_history = self.retrieve_chat_history(history_id, access_token)

        if self.validate_chat_history(con_history) is False:
            return ""

        con_history = self.remove_history_blocked_by_guardrails(con_history)

        if type.lower() == "naive":
            return self._get_history_naive(con_history, **params)
        else:
            raise ValueError(f"Incorrect ChatHistoryHandler parsing type. Got: {type}. Expected: [naive, ]")

    def _get_history_naive(self, con_history: List[PrevQuestionDetails], top_k: int = 3) -> str:
        """
        Formats the conversation history in a naive way.
        """
        if len(con_history) < top_k:
            last_k_answers = con_history
        else:
            last_k_answers = con_history[-top_k:]

        formatted_output = ""
        for conv in last_k_answers:
            formatted_output += f"{USER_PREFIXES[self.prompt_template_language]}: {conv.question}\n\
{ASSISTANT_PREFIXES[self.prompt_template_language]}: {conv.answer}\n"

        logger.info(formatted_output)
        return formatted_output.strip()
