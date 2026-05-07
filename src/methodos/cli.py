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

from pathlib import Path

import typer
from rich.console import Console

from methodos import __version__
from methodos.config import Settings
from methodos.providers import make_embedding

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
