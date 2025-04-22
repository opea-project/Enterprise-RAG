from typing import List

from comps import (
    get_opea_logger,
    PrevQuestionDetails
)

logger = get_opea_logger(f"{__file__.split('comps/')[1].split('/', 1)[0]}_microservice")

class ConversationHistoryHandler:
    def parse_conversation_history(self, con_history: List[PrevQuestionDetails], type: str, params: dict = {}) -> str:
        logger.info(params)
        if type.lower() == "naive":
            return self._get_history_naive(con_history, **params)
        else:
            raise ValueError(f"Incorrect ConversationHistoryHandler parsing type. Got: {type}. Expected: [naive, ]")

    def _get_history_naive(self, con_history: List[PrevQuestionDetails], top_k: int = 3) -> str:
        if len(con_history) < top_k:
            last_k_answers = con_history
        else:
            last_k_answers = con_history[-top_k:]

        formatted_output = ""
        for conv in last_k_answers:
            formatted_output += f"previous_question: {conv.question} previous_answer: {conv.answer} "

        logger.info(formatted_output)
        return formatted_output.strip()
