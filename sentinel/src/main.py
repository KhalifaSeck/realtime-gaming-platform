"""
CLI Sentinel AI — parle a ton platform.

Usage :
    python -m src.main "What are the top 5 trending games right now?"
    python -m src.main "Any review bombs in the last 24h?"
    python -m src.main "Show me publishers dominating specific genres"
"""
from __future__ import annotations

import argparse
import sys

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from src.agent import ask


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("question", nargs="*", help="Question a poser a l'agent")
    args = parser.parse_args()

    console = Console()

    question = " ".join(args.question) or console.input("[bold cyan]You: [/bold cyan]")

    if not question.strip():
        console.print("[yellow]Empty question, exit.[/yellow]")
        sys.exit(0)

    console.print(Panel(f"[cyan]{question}[/cyan]", title="Question", border_style="cyan"))

    with console.status("[bold green]Sentinel is thinking..."):
        answer = ask(question)

    console.print(Panel(Markdown(answer), title="Sentinel", border_style="magenta"))


if __name__ == "__main__":
    main()