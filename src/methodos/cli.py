"""Methodos CLI — Typer + Rich.

Subcommands:
    ingest                     Build the vector store from /methods
    query "<problem>"          Recommend methods (with LLM explanation)
    list                       Browse the catalog
    show ID                    Print a method's full Markdown
    feedback ID --rating N     Record outcome
    stats                      Aggregated ratings table
    --version                  Show version + active providers
"""

from __future__ import annotations

import json as _json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from methodos import __version__
from methodos.config import Settings
from methodos.providers import make_embedding, make_llm

if TYPE_CHECKING:
    from methodos.models import Method
    from methodos.search import Candidate

# On Windows, default stdout encoding is cp1252, which can't render the unicode
# characters we use in tables (●, ○, en-dash, ellipsis). Reconfigure to UTF-8 so
# the CLI works in regular cmd / PowerShell windows without manual env tweaks.
if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")

app = typer.Typer(
    name="methodos",
    help="An expert-level RAG catalog of management methods.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        s = Settings()
        console.print(
            f"methodos {__version__}\n"
            f"  model:     {s.model}\n"
            f"  embedding: {s.embedding_provider}:{s.embedding_model}\n"
            f"  chroma:    {s.chroma_path}"
        )
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool | None = typer.Option(
        None,
        "--version",
        help="Show version + active providers",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Methodos AI: pick the right management method for your problem."""


@app.command()
def ingest(
    methods_dir: Path = typer.Option(  # noqa: B008
        Path("methods"), "--methods-dir", help="Directory of method JSON files"
    ),
) -> None:
    """Rebuild the local vector store from /methods/*.json."""
    from methodos.ingest import IngestError
    from methodos.ingest import ingest as do_ingest

    settings = Settings()
    try:
        embedding = make_embedding(settings)
    except Exception as e:
        console.print(f"[red]Failed to construct embedding provider:[/] {e}")
        raise typer.Exit(code=2) from e

    try:
        summary = do_ingest(
            methods_dir=methods_dir,
            chroma_path=settings.chroma_path,
            embedding=embedding,
        )
    except IngestError as e:
        console.print(f"[red]Ingest failed:[/]\n{e}")
        raise typer.Exit(code=1) from e

    if summary.count == 0:
        console.print("[yellow]No methods found — nothing ingested.[/]")
        return
    console.print(
        f"[green]Ingested {summary.count} method(s)[/] "
        f"(provider: {summary.provider_name}, {summary.dimensions}d)"
    )


def _complexity_dots(score: int) -> str:
    return "●" * score + "○" * (5 - score)


def _render_candidates(candidates: list[Candidate]) -> None:
    for i, c in enumerate(candidates, 1):
        header = (
            f"#{i}  {c.name}  (sim {c.similarity:.2f})  "
            f"complexity {_complexity_dots(c.complexity_score)}"
        )
        body_lines = [
            "[bold]Strengths:[/] " + " · ".join(c.strengths[:3]),
            f"[bold]Duration:[/] {c.duration_min}–{c.duration_max} min",  # noqa: RUF001
            f"[bold]Category:[/] {c.category}",
            f"→ [link=file://{c.doc_path}]{c.doc_path}[/link]",
        ]
        console.print(Panel("\n".join(body_lines), title=header, expand=False))


@app.command()
def query(
    text: str = typer.Argument(..., help="Natural-language problem statement"),
    top_k: int | None = typer.Option(None, "--top-k", "-k", help="Number of methods to recommend"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Skip LLM explanation"),
    model: str | None = typer.Option(None, "--model", help="Override LLM model string"),
) -> None:
    """Recommend methods for a problem."""
    from methodos.search import StaleIndexError, search

    settings = Settings()
    if model is not None:
        settings = settings.model_copy(update={"model": model})
    if top_k is None:
        top_k = settings.top_k

    embedding = make_embedding(settings)
    llm = None if no_llm else make_llm(settings)

    try:
        result = search(
            query=text,
            embedding=embedding,
            llm=llm,
            chroma_path=settings.chroma_path,
            top_k=top_k,
        )
    except StaleIndexError as e:
        console.print(f"[red]Stale index:[/] {e}")
        raise typer.Exit(code=1) from e

    if not result.candidates:
        console.print("[yellow]No matches.[/]")
        return

    _render_candidates(result.candidates)

    from methodos.feedback import log_recommendation

    qid = log_recommendation(
        query=text,
        method_ids=[c.id for c in result.candidates],
        model=settings.model,
        path=settings.feedback_path,
    )

    if result.explanation:
        console.print()
        console.print(Markdown(result.explanation))

    if sys.stdout.isatty() and result.candidates:
        top = result.candidates[0]
        console.print(
            f"\n[dim]─────[/]\n[dim]Logged as {qid} · rate with: methodos feedback {top.id} -r 4[/]"
        )


def _load_all_methods(methods_dir: Path) -> list[Method]:
    from methodos.models import Method

    methods = []
    for f in sorted(methods_dir.glob("*.json")):
        methods.append(Method.model_validate(_json.loads(f.read_text(encoding="utf-8"))))
    return methods


@app.command("list")
def list_methods(
    category: str | None = typer.Option(None, "--category", "-c"),
    max_complexity: int | None = typer.Option(None, "--max-complexity"),
    methods_dir: Path = typer.Option(Path("methods"), "--methods-dir"),  # noqa: B008
) -> None:
    """Browse the catalog."""
    methods = _load_all_methods(methods_dir)
    if category:
        methods = [m for m in methods if m.category.value == category]
    if max_complexity is not None:
        methods = [m for m in methods if m.complexity_score <= max_complexity]

    if not methods:
        console.print("[yellow]No methods match.[/]")
        return

    table = Table(title="Methods")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Category", style="magenta")
    table.add_column("Complexity", justify="center")
    table.add_column("Duration (min)", justify="right")
    for m in methods:
        table.add_row(
            m.id,
            m.name,
            m.category.value,
            _complexity_dots(m.complexity_score),
            f"{m.estimated_duration.min_minutes}–{m.estimated_duration.max_minutes}",  # noqa: RUF001
        )
    console.print(table)


@app.command()
def show(
    id: str = typer.Argument(..., help="Method id (e.g. SWOT)"),
    methods_dir: Path = typer.Option(Path("methods"), "--methods-dir"),  # noqa: B008
) -> None:
    """Print a method's full Markdown documentation."""
    md = methods_dir / f"{id}.md"
    if not md.exists():
        console.print(f"[red]No method with id '{id}'[/]")
        raise typer.Exit(code=1)
    console.print(Markdown(md.read_text(encoding="utf-8")))


@app.command()
def feedback(
    method_id: str = typer.Argument(..., help="Method id (e.g. SWOT)"),
    rating: int = typer.Option(..., "--rating", "-r", min=1, max=5),
    note: str | None = typer.Option(None, "--note", "-n"),
    query_id: str | None = typer.Option(None, "--query-id", "-q"),
) -> None:
    """Record an outcome rating for a previously-recommended method."""
    from methodos.feedback import log_rating

    settings = Settings()
    log_rating(
        method_id=method_id,
        rating=rating,
        note=note,
        query_id=query_id,
        path=settings.feedback_path,
    )
    console.print(f"[green]Recorded:[/] {method_id} rated {rating}/5")


@app.command("stats")
def stats_cmd() -> None:
    """Show aggregated method ratings."""
    from methodos.feedback import stats

    settings = Settings()
    s = stats(settings.feedback_path)
    if not s:
        console.print("[yellow]No feedback yet.[/]")
        return
    table = Table(title="Method ratings")
    table.add_column("Method", style="cyan")
    table.add_column("Recommended", justify="right")
    table.add_column("Rated", justify="right")
    table.add_column("Avg rating", justify="right")
    for mid, stat in sorted(s.items()):
        table.add_row(
            mid,
            str(stat.recommendation_count),
            str(stat.rating_count),
            f"{stat.avg_rating:.2f}" if stat.rating_count else "—",
        )
    console.print(table)
