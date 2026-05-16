import typer
from core.brain import think
from core.agent import debug_loop
from voice.voice import run_voice
from watcher.monitor import start_monitor
import os
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

app = typer.Typer()
console = Console()

@app.command()
def chat(q: str):
    """Chat with JARVIS using the configured LLM provider."""
    provider = os.getenv("JARVIS_PROVIDER", "ollama")
    console.print(f"[bold blue]JARVIS ({provider}):[/bold blue]")
    response = think("", q)
    console.print(Markdown(response))

@app.command()
def fix(issue: str):
    """Start an autonomous debug loop to fix a reported issue."""
    debug_loop(issue)

@app.command()
def voice():
    """Control JARVIS using voice commands."""
    run_voice()

@app.command()
def watch():
    """Start proactive monitoring of file changes."""
    start_monitor()

@app.command()
def config():
    """Show current configuration and LLM provider."""
    provider = os.getenv("JARVIS_PROVIDER", "ollama")
    model = os.getenv("JARVIS_MODEL", "llama3")
    
    config_info = f"""
    [bold]Current Provider:[/bold] {provider}
    [bold]Model:[/bold] {model}
    
    [bold]Environment Variables:[/bold]
    - JARVIS_PROVIDER: {os.getenv("JARVIS_PROVIDER", "Not Set")}
    - GEMINI_API_KEY: {"[green]Set[/green]" if os.getenv("GEMINI_API_KEY") else "[red]Missing[/red]"}
    - ANTHROPIC_API_KEY: {"[green]Set[/green]" if os.getenv("ANTHROPIC_API_KEY") else "[red]Missing[/red]"}
    - XAI_API_KEY: {"[green]Set[/green]" if os.getenv("XAI_API_KEY") else "[red]Missing[/red]"}
    """
    console.print(Panel(config_info, title="JARVIS Configuration"))

@app.command()
def init():
    """Initialize a JARVIS.md file in the current directory."""
    if os.path.exists("JARVIS.md"):
        console.print("[yellow]JARVIS.md already exists.[/yellow]")
    else:
        with open("JARVIS.md", "w") as f:
            f.write("# JARVIS Project Instructions\n\n- Define project rules here.")
        console.print("[green]Created JARVIS.md[/green]")

if __name__ == "__main__":
    app()
