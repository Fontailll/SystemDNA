from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

from systemdna.cli.dependencies import get_history_engine
from systemdna.scoring.engine import ScoringEngine

score_cmd = typer.Typer(help="Calculate health score from a snapshot")
console = Console()

_SEVERITY_STYLES = {
    "critical": "red",
    "warning": "yellow",
    "info": "blue",
}

_SEVERITY_LABELS = {
    "critical": "CRITICAL",
    "warning": "WARNING",
    "info": "INFO",
}


def _score_color(score: int) -> str:
    if score >= 80:
        return "green"
    if score >= 50:
        return "yellow"
    return "red"


@score_cmd.command()
def check(
    snapshot_id: str | None = typer.Argument(
        None, help="Snapshot ID to score (defaults to latest)",
    ),
) -> None:
    history = get_history_engine()

    if snapshot_id is None:
        snapshot = history.get_latest_snapshot()
        if snapshot is None:
            console.print("[yellow]No snapshots found[/]")
            raise typer.Exit(code=1)
    else:
        snapshot = history.show_snapshot(snapshot_id)

    engine = ScoringEngine()
    health = engine.score(snapshot)

    color = _score_color(health.overall_score)
    score_text = Text(f"{health.overall_score}", style=f"bold {color}", justify="center")
    label_text = Text("HEALTH SCORE", style="dim", justify="center")

    console.print()
    console.print(Panel.fit(
        f"{score_text}\n{label_text}",
        title="SystemDNA Health Score",
        border_style=color,
        padding=(1, 4),
    ))

    cat_table = Table(show_header=True, border_style="dim")
    cat_table.add_column("Category", style="bold", min_width=18)
    cat_table.add_column("Score", justify="center", min_width=10)
    cat_table.add_column("Progress", min_width=30)
    cat_table.add_column("Findings", justify="center", min_width=8)

    for cat in health.categories:
        cat_color = _score_color(int(cat.score / cat.max_score * 100))
        cat.score / cat.max_score if cat.max_score > 0 else 0
        bar = ProgressBar(total=cat.max_score, completed=cat.score, width=28)
        cat_table.add_row(
            cat.category.value.capitalize(),
            f"[{cat_color}]{cat.score}/{cat.max_score}[/]",
            bar,
            str(len(cat.findings)),
        )

    console.print()
    console.print(Panel(cat_table, title="Category Breakdown", border_style="cyan"))

    if health.findings_count > 0:
        findings_table = Table(show_header=True, border_style="dim")
        findings_table.add_column("Severity", style="bold", min_width=12)
        findings_table.add_column("Finding", min_width=30)
        findings_table.add_column("Description", min_width=40)
        findings_table.add_column("Impact", justify="center", min_width=8)

        for cat in health.categories:
            for finding in cat.findings:
                sev_color = _SEVERITY_STYLES.get(finding.severity, "white")
                sev_label = _SEVERITY_LABELS.get(finding.severity, finding.severity.upper())
                findings_table.add_row(
                    f"[{sev_color}]{sev_label}[/]",
                    f"{finding.title}",
                    f"{finding.description}",
                    f"-{finding.impact}",
                )

        console.print()
        console.print(Panel(findings_table, title="Findings", border_style="red"))

    summary_parts = []
    if health.critical_count > 0:
        summary_parts.append(f"[red]{health.critical_count} critical[/]")
    if health.warning_count > 0:
        summary_parts.append(f"[yellow]{health.warning_count} warning(s)[/]")
    if health.info_count > 0:
        summary_parts.append(f"[blue]{health.info_count} info[/]")

    if summary_parts:
        console.print()
        console.print(
            Panel(
                " | ".join(summary_parts),
                title="Summary",
                border_style="cyan",
            )
        )
    console.print()
