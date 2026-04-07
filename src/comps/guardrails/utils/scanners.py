import re

from collections.abc import Iterable
from llm_guard.input_scanners import BanSubstrings, Code, Regex
from llm_guard.input_scanners.regex import MatchType
from llm_guard.util import calculate_risk_score
from presidio_anonymizer.core.text_replace_builder import TextReplaceBuilder

from comps import get_opea_logger

logger = get_opea_logger("opea_llm_guard_utils_scanners")

# The bug is reported here: https://github.com/protectai/llm-guard/issues/210
class OPEABanSubstrings(BanSubstrings):
    def _redact_text(self, text: str, substrings: list[str]) -> str:
        redacted_text = text
        flags = 0
        if not self._case_sensitive:
            flags = re.IGNORECASE
        for s in substrings:
            regex_redacted = re.compile(re.escape(s), flags)
            redacted_text = regex_redacted.sub("[REDACTED]", redacted_text)
        return redacted_text

    def scan(self, prompt: str, output: str = None) -> tuple[str, bool, float]:
        if output is not None:
            return super().scan(output)
        return super().scan(prompt)

# LLM Guard's Regex Scanner doesn't replace all occurrences of found patterns.
# The bug is reported here: https://github.com/protectai/llm-guard/issues/229
class OPEARegexScanner(Regex):
    def scan(self, prompt: str, output: str = None) -> tuple[str, bool, float]:
        text_to_scan = ""
        if output is not None:
            text_to_scan = output
        else:
            text_to_scan = prompt

        text_replace_builder = TextReplaceBuilder(original_text=text_to_scan)
        for pattern in self._patterns:
            if self._match_type == MatchType.SEARCH:
                matches = re.finditer(pattern, text_to_scan)
            else:
                matches = self._match_type.match(pattern, text_to_scan)

            if matches is None:
                continue
            elif isinstance(matches, Iterable):
                matches = list(matches)
                if len(matches) == 0:
                    continue
            else:
                matches = [matches]

            if self._is_blocked:
                logger.warning(f"Pattern was detected in the text: {pattern}")

                if self._redact:
                    for match in reversed(matches):
                        text_replace_builder.replace_text_get_insertion_index(
                            "[REDACTED]",
                            match.start(),
                            match.end(),
                        )

                return text_replace_builder.output_text, False, 1.0

            logger.debug(f"Pattern matched the text: {pattern}")
            return text_replace_builder.output_text, True, 0.0

        if self._is_blocked:
            logger.debug("None of the patterns were found in the text")
            return text_replace_builder.output_text, True, 0.0

        logger.warning("None of the patterns matched the text")
        return text_replace_builder.output_text, False, 1.0


# LLM Guard's Code scanner processes the entire prompt as a single block when no markdown
# fencing is found. This causes the ML classifier to dilute confidence across mixed-language
# inputs (e.g. Python + Scala in one prompt), failing to detect either language above the threshold.
# OPEACode works around this by also splitting on blank-line boundaries.
class OPEACode(Code):
    _CHUNK_SEPARATOR = re.compile(r'\n\s*\n')

    def scan(self, prompt: str, output: str = None) -> tuple[str, bool, float]:
        text = output if output is not None else prompt

        if text.strip() == "":
            return text, True, 0.0

        # Extract markdown code blocks (same as parent)
        code_blocks = self._extract_code_blocks(text)
        if len(code_blocks) == 0:
            code_blocks = [text]

            chunks = [c.strip() for c in self._CHUNK_SEPARATOR.split(text) if c.strip()]
            if len(chunks) > 1:
                code_blocks.extend(chunks)

        results = self._pipeline(code_blocks)
        logger.info(code_blocks)
        for languages in results:
            for language in languages:
                score = round(language["score"], 2)

                if score < self._threshold or language["label"] not in self._languages:
                    continue

                if self._is_blocked:
                    logger.warning(f"Language is not allowed: {language['label']} (score={score})")
                    return text, False, calculate_risk_score(score, self._threshold)

                if not self._is_blocked:
                    return text, True, 0.0

        if self._is_blocked:
            return text, True, 0.0

        logger.warning("No allowed languages detected")
        return text, False, 1.0