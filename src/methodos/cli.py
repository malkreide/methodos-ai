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

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from methodos import __version__
from methodos.config import Settings
from methodos.providers import make_embedding, make_llm

if TYPE_CHECKING:
    from methodos.search import Candidate

app = typer.Typer(
    name="methodos",
    help="An expert-level RAG catalog of management methods.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()


def _version_callback(value: bool) -> None:
    if value:
        s = Settings(_env_file=None)  # type: ignore[call-arg]
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
    if result.explanation:
        console.print()
        console.print(Markdown(result.explanation))

    if sys.stdout.isatty() and result.candidates:
        top = result.candidates[0]
        console.print(f"\n[dim]─────[/]\n[dim]Rate with: methodos feedback {top.id} -r 1..5[/]")
