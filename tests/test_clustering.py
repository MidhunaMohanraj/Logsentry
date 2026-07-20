from logsentry.clustering import cluster_records, normalize
from logsentry.parser import parse_lines


def test_normalize_replaces_numbers():
    assert normalize("Retry attempt 1 for request") == "Retry attempt <num> for request"


def test_normalize_replaces_ip():
    assert normalize("Connect to 192.168.0.1 failed") == "Connect to <ip> failed"


def test_normalize_replaces_uuid():
    text = "Job 123e4567-e89b-12d3-a456-426614174000 failed"
    assert normalize(text) == "Job <uuid> failed"


def test_normalize_replaces_quoted_strings():
    assert normalize("Retry for request id 'a1b2c3'") == "Retry for request id <str>"


def test_normalize_replaces_paths():
    # The path itself becomes <path>; the trailing line number is a
    # separate numeric token normalized to <num>.
    assert normalize("Error at /app/src/handlers/order.py:88") == "Error at <path>:<num>"


def test_cluster_records_groups_similar_messages():
    lines = [
        "2026-07-18 09:14:22 ERROR Connection refused to db-primary:5432",
        "2026-07-18 09:14:25 ERROR Connection refused to db-primary:5432",
        "2026-07-18 09:14:29 ERROR Connection refused to db-primary:5433",
        "2026-07-18 09:17:00 INFO Health check passed",
    ]
    records = parse_lines(lines)
    clusters = cluster_records(records)

    # All three "Connection refused to db-primary:<port>" lines should
    # merge into a single cluster since only the port number differs.
    # Hostnames are intentionally left as-is (no safe generic pattern for
    # arbitrary hostnames), so a differing host would NOT merge.
    error_clusters = [c for c in clusters if c.level == "ERROR"]
    assert len(error_clusters) == 1
    assert error_clusters[0].count == 3


def test_cluster_records_keeps_different_hosts_separate():
    lines = [
        "ERROR Connection refused to db-primary:5432",
        "ERROR Connection refused to db-replica:5432",
    ]
    records = parse_lines(lines)
    clusters = cluster_records(records)

    assert len(clusters) == 2


def test_cluster_records_sorted_by_count_descending():
    lines = [
        "ERROR: a",
        "ERROR: a",
        "ERROR: a",
        "WARN: b",
    ]
    records = parse_lines(lines)
    clusters = cluster_records(records)

    assert clusters[0].count == 3
    assert clusters[0].count >= clusters[-1].count


def test_cluster_samples_capped():
    lines = ["ERROR: repeated issue"] * 10
    records = parse_lines(lines)
    clusters = cluster_records(records)

    assert clusters[0].count == 10
    assert len(clusters[0].samples) == 3
