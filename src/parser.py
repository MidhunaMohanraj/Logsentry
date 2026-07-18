"""Parses raw log lines into structured records.

Handles a handful of common formats without requiring the caller to
specify one:

    2026-07-18 10:22:31 ERROR Connection refused to db-primary:5432
    [2026-07-18T10:22:31Z] [ERROR] Connection refused to db-primary:5432
    ERROR: Connection refused to db-primary:5432

Anything that doesn't match a recognized pattern is kept as a line with
level "UNKNOWN" rather than dropped, so nothing silently disappears.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

LEVELS = ("CRITICAL", "FATAL", "ERROR", "WARN", "WARNING", "INFO", "DEBUG", "TRACE")
LEVEL_PATTERN = "|".join(LEVELS)

# Try a few layouts, most specific first.
PATTERNS = [
    # 2026-07-18 10:22:31 ERROR message   OR   2026-07-18T10:22:31Z ERROR message
    re.compile(
        rf"^\s*\[?(?P<timestamp>\d{{4}}-\d{{2}}-\d{{2}}[T ]\d{{2}}:\d{{2}}:\d{{2}}[^\]\s]*)\]?\s*"
        rf"\[?(?P<level>{LEVEL_PATTERN})\]?:?\s*(?P<message>.*)$"
    ),
    # ERROR: message   OR   [ERROR] message
    re.compile(rf"^\s*\[?(?P<level>{LEVEL_PATTERN})\]?:?\s+(?P<message>.*)$"),
]


@dataclass
class LogRecord:
    raw: str
    level: str
    message: str
    timestamp: str | None = None


def parse_line(line: str) -> LogRecord:
    stripped = line.rstrip("\n")
    for pattern in PATTERNS:
        match = pattern.match(stripped)
        if match:
            groups = match.groupdict()
            return LogRecord(
                raw=stripped,
                level=groups.get("level", "UNKNOWN").upper(),
                message=groups["message"].strip(),
                timestamp=groups.get("timestamp"),
            )
    return LogRecord(raw=stripped, level="UNKNOWN", message=stripped.strip())


def parse_lines(lines: list[str]) -> list[LogRecord]:
    return [parse_line(line) for line in lines if line.strip()]
