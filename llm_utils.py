"""
Shared retry logic for Gemini API calls.

Gemini's API frequently returns 503 UNAVAILABLE ("model is currently
experiencing high demand") during busy periods — this is Google's
servers being overloaded, not a bug in this code, and it's common
enough that every module calling the LLM should retry automatically
instead of failing on the first hiccup.
"""

import logging

from google.genai import errors as genai_errors
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

logger = logging.getLogger("smarthire_genai")
logging.basicConfig(level=logging.INFO)


def _is_retryable(exc: BaseException) -> bool:
    """
    Retry on transient server-side errors (503 overloaded, 500 internal,
    429 rate-limited). Don't retry on 400s — a bad request will just
    fail the same way again.
    """
    if isinstance(exc, genai_errors.ServerError):
        return True
    if isinstance(exc, genai_errors.ClientError):
        return getattr(exc, "status_code", None) == 429
    return False


# Retries up to 5 times with exponential backoff (2s, 4s, 8s, 16s, 32s,
# capped at 60s) before finally letting the error propagate.
llm_retry = retry(
    retry=retry_if_exception(_is_retryable),
    wait=wait_exponential(multiplier=2, max=60),
    stop=stop_after_attempt(5),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
