"""Command-line interface for logsentry."""

from __future__ import annotations

from pathlib import Path
import click
from logsentry.clustering import cluster_records  
from logsentry.generator import generate_report
from logsentry.parser import parse_lines
@click.command() 
@click.argument("logfile", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), default="log_report.md", help="Output Markdown file.")
@click.option("--no-ai", is_flag=True, help="Skip the AI-generated root-cause summary.")
@click.option("--top", default=20, show_default=True, help="Number of top clusters to include in the report.")
@click.option(
    "--level",
    "levels",
    multiple=True,
    help="Only include records at this level (repeatable, e.g. --level ERROR --level WARN).",
)
def main(logfile: Path, output: Path, no_ai: bool, top: int, levels: tuple[str, ...]) -> None:
    """Cluster LOGFILE's lines by message pattern and write a report to OUTPUT."""
    raw_lines = logfile.read_text(encoding="utf-8", errors="replace").splitlines()
    records = parse_lines(raw_lines)

    if levels:
        wanted = {lvl.upper() for lvl in levels}
        records = [r for r in records if r.level in wanted]

    if not records:
        click.echo("No matching log lines found.")
        raise SystemExit(1)

    clusters = cluster_records(records)
    click.echo(f"Parsed {len(records)} line(s) into {len(clusters)} cluster(s)")

    report = generate_report(clusters, use_ai=not no_ai, top_n=top)
    output.write_text(report, encoding="utf-8")

    click.echo(f"Wrote report to {output.resolve()}")


if __name__ == "__main__":
    main()
