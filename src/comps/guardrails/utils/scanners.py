import re

from llm_guard.input_scanners import BanSubstrings

from comps import get_opea_logger

logger = get_opea_logger("opea_llm_guard_utils_scanners")

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