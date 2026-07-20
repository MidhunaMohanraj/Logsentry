from logsentry.parser import parse_line, parse_lines


def test_parse_timestamped_line():
    record = parse_line("2026-07-18 09:14:22 ERROR Connection refused to db-primary:5432")
    assert record.level == "ERROR"
    assert record.message == "Connection refused to db-primary:5432"
    assert record.timestamp == "2026-07-18 09:14:22"


def test_parse_bracketed_line():
    record = parse_line("[ERROR] Connection refused to db-primary:5432")
    assert record.level == "ERROR"
    assert record.message == "Connection refused to db-primary:5432"


def test_parse_prefix_line():
    record = parse_line("WARN: retry attempt 1")
    assert record.level == "WARN"
    assert record.message == "retry attempt 1"


def test_parse_unrecognized_line_kept_as_unknown():
    record = parse_line("just some free text with no level marker")
    assert record.level == "UNKNOWN"
    assert record.message == "just some free text with no level marker"


def test_parse_lines_skips_blank_lines():
    records = parse_lines(["ERROR: a\n", "\n", "   \n", "INFO: b\n"])
    assert len(records) == 2
