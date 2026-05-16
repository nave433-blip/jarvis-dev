import typer
from core.brain import think
from core.agent import debug_loop
from voice.voice import run_voice
from watcher.monitor import start_monitor
from core.config import setup_wizard, get_env_with_config, CONFIG_FILE
import os
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

app = typer.Typer()
console = Console()

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """JARVIS: Your local AI engineer."""
    if ctx.invoked_subcommand is None:
        if not CONFIG_FILE.exists():
            console.print("[yellow]No configuration found. Starting setup...[/yellow]")
            setup_wizard()
        else:
            console.print(ctx.get_help())

@app.command()
def setup():
    """Run the interactive setup wizard to configure providers and API keys."""
    setup_wizard()

@app.command()
def chat(q: str):
    """Chat with JARVIS using the configured LLM provider."""
    provider = get_env_with_config("provider") or "ollama"
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
    provider = get_env_with_config("provider") or "ollama"
    model = get_env_with_config("jarvis_model") or "llama3"
    
    config_info = f"""
    [bold]Config File:[/bold] {CONFIG_FILE}
    
    [bold]Current Provider:[/bold] {provider}
    [bold]Model:[/bold] {model}
    
    [bold]API Key Status:[/bold]
    - GEMINI_API_KEY: {"[green]Set[/green]" if get_env_with_config("gemini_api_key") else "[red]Missing[/red]"}
    - ANTHROPIC_API_KEY: {"[green]Set[/green]" if get_env_with_config("anthropic_api_key") else "[red]Missing[/red]"}
    - XAI_API_KEY: {"[green]Set[/green]" if get_env_with_config("xai_api_key") else "[red]Missing[/red]"}
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
