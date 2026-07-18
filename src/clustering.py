"""Groups structurally similar log messages together by replacing
variable substrings (numbers, UUIDs, IPs, hex blobs, quoted strings,
file paths) with placeholders, then bucketing on the resulting template.

This is the same basic idea used by tools like Drain/LogPai, simplified
down to regex substitution since we don't need streaming/online updates.
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field

from logsentry.parser import LogRecord

UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
IPV4_RE = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")
HEX_RE = re.compile(r"\b0x[0-9a-fA-F]+\b")
NUMBER_RE = re.compile(r"\b\d+(\.\d+)?\b")
QUOTED_RE = re.compile(r"'[^']*'|\"[^\"]*\"")
PATH_RE = re.compile(r"(?:/[\w.\-]+){2,}")


def normalize(message: str) -> str:
    text = message
    text = UUID_RE.sub("<uuid>", text)
    text = IPV4_RE.sub("<ip>", text)
    text = HEX_RE.sub("<hex>", text)
    text = PATH_RE.sub("<path>", text)
    text = QUOTED_RE.sub("<str>", text)
    text = NUMBER_RE.sub("<num>", text)
    return text.strip()


@dataclass
class Cluster:
    template: str
    level: str
    count: int = 0
    samples: list[str] = field(default_factory=list)

    def add(self, record: LogRecord, max_samples: int = 3) -> None:
        self.count += 1
        if len(self.samples) < max_samples:
            self.samples.append(record.raw)


def cluster_records(records: list[LogRecord]) -> list[Cluster]:
    """Group records by (level, normalized template) and return clusters
    sorted by descending count.
    """
    buckets: dict[tuple[str, str], Cluster] = {}

    for record in records:
        template = normalize(record.message)
        key = (record.level, template)
        if key not in buckets:
            buckets[key] = Cluster(template=template, level=record.level)
        buckets[key].add(record)

    return sorted(buckets.values(), key=lambda c: c.count, reverse=True)
