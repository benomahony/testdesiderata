from collections import defaultdict
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from testdesiderata.linter import Linter
from testdesiderata.models import Rule, Violation
from testdesiderata.rules import ALL_RULES

app = typer.Typer(
    help="Lint Python test files for Test Desiderata compliance.",
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()


def _build_rules(
    base: list[Rule],
    select: str | None,
    ignore: str | None,
    junit: Path | None,
    slow: float,
) -> list[Rule]:
    assert base, "Base rules must not be empty"
    assert slow > 0, "Slow threshold must be positive"
    rules: list[Rule] = list(base)
    if select:
        prefixes = {p.strip().upper() for p in select.split(",")}
        rules = [r for r in rules if r.rule_id in prefixes]
    if ignore:
        prefixes = {p.strip().upper() for p in ignore.split(",")}
        rules = [r for r in rules if r.rule_id not in prefixes]
    from testdesiderata.timing import SlowTestRule, find_junit_xml, load_junit_timings

    timing_path = junit or find_junit_xml()
    if timing_path and timing_path.exists():
        rules.append(SlowTestRule(load_junit_timings(timing_path), slow))
        console.print(f"[dim]Loaded timing data from {timing_path}[/dim]")
    return rules


def _collect_ai_violations(paths: list[Path]) -> list[Violation]:
    assert paths, "Paths must not be empty"
    assert isinstance(paths, list), "Paths must be a list"
    import asyncio

    try:
        from testdesiderata.agent import review_file as _ai_review
    except ImportError as e:
        raise ImportError("Install AI deps: pip install 'testdesiderata[ai]'") from e
    all_files = [
        p
        for root in paths
        for p in (
            [root]
            if root.is_file()
            else sorted(root.rglob("test_*.py")) + sorted(root.rglob("*_test.py"))
        )
    ]

    async def _run() -> list[Violation]:
        assert all_files is not None, "File list must not be None"
        assert isinstance(all_files, list), "File list must be a list"
        results = await asyncio.gather(
            *[_ai_review(p) for p in all_files], return_exceptions=True
        )
        return [v for r in results if isinstance(r, list) for v in r]

    with console.status("[bold cyan]Running AI review…[/bold cyan]"):
        return asyncio.run(_run())


def _display_violations(violations: list[Violation]) -> None:
    assert violations is not None, "Violations must not be None"
    assert isinstance(violations, list), "Violations must be a list"
    by_file: dict[str, list[Violation]] = defaultdict(list)
    for v in violations:
        by_file[v.filename].append(v)
    for filename, file_violations in by_file.items():
        console.print(f"\n[bold]{filename}[/bold]")
        for v in file_violations:
            loc = f"[dim]{v.line}:{v.col}[/dim]"
            rule = f"[bold yellow]{v.rule_id}[/bold yellow]"
            desid = f"[dim cyan][{v.desideratum}][/dim cyan]"
            console.print(f"  {loc}  {rule}  {desid}  {v.message}")
    console.print()
    if not violations:
        console.print("[bold green]✓ No violations found[/bold green]")
        return
    n_files = len(by_file)
    total = len(violations)
    console.rule(style="dim")
    console.print(
        f"[bold red]{total} violation{'s' if total != 1 else ''}[/bold red] in [bold]{n_files} file{'s' if n_files != 1 else ''}[/bold]\n"
    )
    by_desid: dict[str, list[str]] = defaultdict(list)
    for v in violations:
        by_desid[v.desideratum].append(v.rule_id)
    table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
    table.add_column("Desideratum", style="cyan")
    table.add_column("Count", justify="right", style="yellow")
    table.add_column("Rules triggered", style="dim")
    for desid, rule_ids in sorted(by_desid.items()):
        table.add_row(desid, str(len(rule_ids)), ", ".join(sorted(set(rule_ids))))
    console.print(table)
    console.print()


@app.command()
def main(
    paths: Annotated[list[Path], typer.Argument(help="Files or directories to lint")],
    select: Annotated[
        str | None,
        typer.Option(
            "--select", "-s", help="Comma-separated rule prefixes to run (e.g. DET,FST)"
        ),
    ] = None,
    ignore: Annotated[
        str | None,
        typer.Option(
            "--ignore", "-i", help="Comma-separated rule prefixes to skip (e.g. BHV)"
        ),
    ] = None,
    junit: Annotated[
        Path | None,
        typer.Option("--junit", help="JUnit XML for timing (auto-detected if absent)"),
    ] = None,
    slow: Annotated[
        float, typer.Option("--slow", help="Slow test threshold in seconds")
    ] = 1.0,
    ai: Annotated[
        bool,
        typer.Option("--ai", help="Run AI reviewer for Writable/Inspiring desiderata"),
    ] = False,
) -> None:
    assert paths, "At least one path must be provided"
    assert ALL_RULES, "Rule registry must not be empty"
    rules = _build_rules(ALL_RULES, select, ignore, junit, slow)
    linter = Linter(rules=rules)
    violations: list[Violation] = []
    for path in paths:
        violations.extend(linter.lint_path(path))
    if ai:
        try:
            violations.extend(_collect_ai_violations(paths))
        except ImportError as e:
            console.print(f"[red]{e}[/red]")
            raise typer.Exit(1)
    _display_violations(violations)
    if violations:
        raise typer.Exit(1)
