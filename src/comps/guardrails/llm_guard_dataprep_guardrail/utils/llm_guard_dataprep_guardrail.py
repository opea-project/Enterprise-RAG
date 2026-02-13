# Copyright (C) 2024-2026 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from llm_guard import scan_prompt
from fastapi import HTTPException

from comps.guardrails.llm_guard_dataprep_guardrail.utils.llm_guard_dataprep_scanners import DataprepScannersConfig
from comps import get_opea_logger, TextDocList

logger = get_opea_logger("opea_llm_guard_dataprep_guardrail_microservice")


class OPEALLMGuardDataprepGuardrail:

    def __init__(self, usv_config: dict):

        try:
            self._scanners_config = DataprepScannersConfig(usv_config)
            self._scanners = self._scanners_config.create_enabled_dataprep_scanners()
        except ValueError as e:
            logger.exception(f"Value Error occured while initializing LLM Guard Dataprep Guardrail scanners: {e}")
            raise
        except Exception as e:
            logger.exception(
                f"An unexpected error occured during initializing \
                    LLM Guard Dataprep Guardrail scanners: {e}"
            )
            raise

    
    def scan_dataprep_docs(self, dataprep_docs: TextDocList) -> TextDocList:
        try:
            if dataprep_docs.dataprep_guardrail_params is not None:
                if self._scanners_config.changed(dataprep_docs.dataprep_guardrail_params.dict()):
                    self._scanners = self._scanners_config.create_enabled_dataprep_scanners()
            else:
                logger.warning("Input guardrail params not found in dataprep request.")
            if self._scanners:
                for doc in dataprep_docs.docs:
                    sanitized_text, results_valid, results_score = scan_prompt(self._scanners, doc.text)

                    if False in results_valid.values():
                        msg = f"Ingested doc is not valid, scores: {results_score}"
                        logger.error(f"{msg}")
                        usr_msg = "I'm sorry, I cannot ingest this document, becasue it does not comply with our standards."
                        raise HTTPException(status_code=466, detail=f"{usr_msg}")
                    doc.text = sanitized_text
                return dataprep_docs
            else:
                logger.info("No input scanners enabled. Skipping scanning.")
                return dataprep_docs
        except HTTPException as e:
            raise e
        except ValueError as e:
            error_msg = f"Validation Error occured while initializing LLM Guard Dataprep Guardrail scanners: {e}"
            logger.exception(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        except Exception as e:
            error_msg = f"An unexpected error occured during scanning prompt with LLM Guard Dataprep Guardrail: {e}"
            logger.exception(error_msg)
            raise HTTPException(status_code=500, detail=error_msg)
