from logsentry.clustering import cluster_records
from logsentry.generator import generate_report, render_offline_report
from logsentry.parser import parse_lines


def _sample_clusters():
    lines = [
        "ERROR: Connection refused to db-primary:5432",
        "ERROR: Connection refused to db-primary:5432",
        "WARN: retry attempt 1",
    ]
    return cluster_records(parse_lines(lines))


def test_render_offline_report_includes_counts_and_templates():
    clusters = _sample_clusters()
    report = render_offline_report(clusters)

    assert "Log Cluster Report" in report
    assert "× 2" in report
    assert "Connection refused" in report


def test_generate_report_falls_back_without_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    clusters = _sample_clusters()
    report = generate_report(clusters, use_ai=True)

    assert "Root Cause Summary" not in report
    assert "Log Cluster Report" in report


def test_generate_report_respects_no_ai_flag(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "fake-key-not-used")

    clusters = _sample_clusters()
    report = generate_report(clusters, use_ai=False)

    assert "Root Cause Summary" not in report
