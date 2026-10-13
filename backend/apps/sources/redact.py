"""Strip secrets from text before it is stored or logged.

Example:
    redact("GET ...?access_token=EAAB123&limit=25")
    # "GET ...?access_token=[redacted]&limit=25"
"""

from __future__ import annotations

import logging
import re

from django.conf import settings

_PARAM = re.compile(r"(access_token|token|key|secret|password)=([^&\s\"']+)", re.IGNORECASE)
_BEARER = re.compile(r"(Bearer|OAuth)\s+[A-Za-z0-9._\-]+", re.IGNORECASE)


def redact(text: str) -> str:
    """Hide query-string secrets, bearer tokens and the configured Meta token."""
    if not text:
        return text
    cleaned = _PARAM.sub(r"\1=[redacted]", text)
    cleaned = _BEARER.sub(r"\1 [redacted]", cleaned)
    token = (getattr(settings, "META_ADS_ACCESS_TOKEN", "") or "").strip()
    if token:
        cleaned = cleaned.replace(token, "[redacted]")
    return cleaned


class RedactingFilter(logging.Filter):
    """Logging filter: redact the final message and any traceback text.

    Example (settings.LOGGING):
        "filters": {"redact": {"()": "apps.sources.redact.RedactingFilter"}}
    """

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.msg = redact(record.getMessage())
            record.args = ()
            if record.exc_info and not record.exc_text:
                record.exc_text = redact(logging.Formatter().formatException(record.exc_info))
            elif record.exc_text:
                record.exc_text = redact(record.exc_text)
        except Exception:  # noqa: BLE001 - never break logging itself
            pass
        return True
