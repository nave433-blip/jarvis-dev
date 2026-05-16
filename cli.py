import typer
from core.brain import think
from core.agent import debug_loop, troubleshoot_loop
from voice.voice import run_voice
from watcher.monitor import start_monitor
from core.config import setup_wizard, get_env_with_config, CONFIG_FILE, load_config
import os
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.prompt import Prompt
from rich.align import Align

# Prompt Toolkit for slash commands
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

app = typer.Typer(help="🚀 JARVIS: The Ultimate Local AI Coding Assistant")
console = Console()

COMMANDS = [
    "/chat", "/fix", "/voice", "/watch", "/config", "/init", "/analyze", 
    "/undo", "/dashboard", "/memory", "/personality", "/models", "/focus", 
    "/troubleshoot", "/help", "/exit"
]

def display_welcome():
    welcome_text = """
    # JARVIS v1.0
    The Senior Software Engineering Assistant
    
    *Type [bold cyan]/[/bold cyan] to see available commands.*
    """
    console.print(Panel(Markdown(welcome_text), style="bold blue", border_style="cyan"))

def get_main_menu_table():
    table = Table(show_header=False, box=None)
    table.add_column("Command", style="cyan", justify="right")
    table.add_column("Description", style="white")
    
    table.add_row("/chat", "Ask JARVIS anything")
    table.add_row("/fix", "Autonomous debugging loop")
    table.add_row("/voice", "Voice control")
    table.add_row("/watch", "Proactive monitoring")
    table.add_row("/config", "Settings")
    table.add_row("/analyze", "Project analytics")
    table.add_row("/undo", "Rollback last edit")
    table.add_row("/dashboard", "Live multi-window TUI")
    table.add_row("/memory", "Manage vector memory")
    table.add_row("/personality", "Switch behavior profiles")
    table.add_row("/models", "Switch AI models")
    table.add_row("/focus", "Set context path")
    table.add_row("/troubleshoot", "Auto-fix terminal errors")
    table.add_row("/help", "Show documentation")
    table.add_row("/exit", "Quit JARVIS")
    
    return Panel(table, title="[bold white]Slash Commands[/bold white]", border_style="blue", expand=False)

@app.command()
def menu():
    """Launch the interactive Gemini-style slash command menu."""
    display_welcome()
    
    completer = WordCompleter(COMMANDS, ignore_case=True)
    session = PromptSession(completer=completer)
    
    style = Style.from_dict({
        'prompt': 'ansicyan bold',
    })

    while True:
        try:
            text = session.prompt('JARVIS > ', style=style).strip()
            if not text: continue
            
            if not text.startswith("/"):
                # Default to chat if no slash
                chat(text)
                continue

            parts = text.split(" ", 1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""

            if cmd == "/chat":
                chat(args or Prompt.ask("Question"))
            elif cmd == "/fix":
                fix(args or Prompt.ask("Issue to fix"))
            elif cmd in ["/voice", "/v"]:
                voice()
            elif cmd in ["/watch", "/w"]:
                watch()
            elif cmd == "/config":
                config_menu()
            elif cmd == "/init":
                init()
            elif cmd == "/analyze":
                analyze(args or ".")
            elif cmd == "/undo":
                undo(args or Prompt.ask("Path to undo"))
            elif cmd == "/dashboard":
                dashboard()
            elif cmd == "/memory":
                memory_menu()
            elif cmd == "/personality":
                personality_menu()
            elif cmd == "/models":
                models_menu()
            elif cmd == "/focus":
                focus(args or Prompt.ask("Path to focus on"))
            elif cmd in ["/troubleshoot", "/t"]:
                troubleshoot(args or Prompt.ask("Failing command"))
            elif cmd in ["/help", "/h"]:
                robust_help()
                console.print(Align.center(get_main_menu_table()))
            elif cmd in ["/exit", "/quit", "/q"]:
                console.print("[yellow]Goodbye, Sir.[/yellow]")
                break
            else:
                console.print(f"[red]Unknown command: {cmd}. Type /help for options.[/red]")

        except KeyboardInterrupt:
            continue
        except EOFError:
            break

def config_menu():
    while True:
        config_data = load_config()
        table = Table(title="Current Configuration", show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")
        
        for k, v in config_data.items():
            val = v if "api_key" not in k or not v else "****" + v[-4:]
            table.add_row(k, str(val))
        
        console.print(table)
        console.print("\n[1] Edit Config (Wizard) | [b] Back")
        choice = Prompt.ask("Choice", choices=["1", "b"], default="b")
        if choice == "1":
            setup_wizard()
        else:
            break

def robust_help():
    help_md = """
    # JARVIS Robust Help System
    
    ### 💬 /chat
    Uses the configured LLM to answer technical questions.
    
    ### 🔧 /fix
    Autonomous agent loop to repair bugs.
    
    ### 🎙 /voice
    Hands-free control via speech.
    
    ### 👁 /watch
    Real-time file monitoring.

    ### 🖥 /dashboard
    Live multi-window TUI.

    ### 🎯 /focus
    Narrow context to a specific path.

    ### 🧠 /memory
    Search or clear persistent history.

    ### 🎭 /personality
    Switch between Professional, Sarcastic, etc.

    ### ⚙️ /config
    Manage LLM providers and API keys.
    """
    console.print(Panel(Markdown(help_md), title="[bold green]System Documentation[/bold green]", border_style="green"))

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """JARVIS: Your local AI engineer."""
    if ctx.invoked_subcommand is None:
        if not CONFIG_FILE.exists():
            console.print("[yellow]No configuration found. Starting setup...[/yellow]")
            setup_wizard()
        menu()

@app.command()
def setup():
    """Run the interactive setup wizard."""
    setup_wizard()

from typing import Optional

@app.command()
def chat(q: str, model: Optional[str] = typer.Option(None, "--model", "-m", help="Override default LLM model")):
    """Chat with JARVIS."""
    provider = get_env_with_config("provider") or "ollama"
    console.print(Panel(f"JARVIS [bold blue]({provider})[/bold blue] [dim]model: {model or 'default'}[/dim]", border_style="blue"))
    response = think("", q, model=model)
    console.print(Markdown(response))

@app.command()
def fix(issue: str, model: Optional[str] = typer.Option(None, "--model", "-m", help="Override default LLM model")):
    """Autonomous debug loop."""
    debug_loop(issue, model=model)

@app.command()
def undo(path: str):
    """Rollback the last edit to a specific file."""
    from tools.editor import undo_last_edit
    res = undo_last_edit(path)
    if "Error" in res:
        console.print(f"[red]{res}[/red]")
    else:
        console.print(f"[green]{res}[/green]")

@app.command()
def dashboard():
    """Launch the multi-window live dashboard."""
    from core.dashboard import Dashboard
    db = Dashboard()
    db.run()

@app.command()
def focus(path: str):
    """Set the working directory/file focus for JARVIS."""
    if os.path.exists(path):
        console.print(Panel(f"[green]Focus successfully set to:[/green]\n{os.path.abspath(path)}", border_style="green"))
    else:
        console.print(f"[red]Error: Path does not exist:[/red] {path}")

@app.command()
def troubleshoot(command: str, model: Optional[str] = typer.Option(None, "--model", "-m", help="Override default LLM model")):
    """Run a command and automatically troubleshoot and fix any errors."""
    troubleshoot_loop(command, model=model)

@app.command()
def voice():
    """Voice control."""
    run_voice()

@app.command()
def watch():
    """Proactive monitoring."""
    start_monitor()

@app.command()
def config():
    """Show configuration."""
    config_menu()

@app.command()
def analyze(path: str = "."):
    """Perform deep project complexity and health analytics."""
    from tools.analytics import project_summary
    console.print(f"[bold blue]Analyzing project at {path}...[/bold blue]")
    summary = project_summary(path)
    
    table = Table(title="Project Health Analytics", border_style="cyan")
    table.add_column("Metric", style="white")
    table.add_column("Value", style="green")
    
    table.add_row("Total Files", str(summary["total_files"]))
    table.add_row("Total Lines (Python)", str(summary["total_lines"]))
    
    for lang, count in summary["languages"].items():
        table.add_row(f"Language ({lang})", str(count))
    
    console.print(table)
    
    if summary["hotspots"]:
        console.print("\n[bold red]Complexity Hotspots (Refactor Recommended):[/bold red]")
        for hs in summary["hotspots"]:
            console.print(f"- {hs['path']} (Score: {hs['score']})")
    else:
        console.print("\n[green]No complexity hotspots detected. Great job![/green]")

@app.command()
def github(action: str, repo: str, title: str = "", body: str = "", head: str = "", base: str = "main"):
    """Perform GitHub actions."""
    from tools.github import github_tool
    if action == "info":
        res = github_tool.get_repo_info(repo)
    elif action == "issue":
        res = github_tool.create_issue(repo, title, body)
    elif action == "create_pr":
        res = github_tool.create_pr(repo, title, body, head, base)
    elif action == "list_prs":
        res = github_tool.list_pull_requests(repo)
    else:
        res = "Unknown GitHub action."
    
    console.print(Panel(str(res), title=f"GitHub Result: {action}"))

@app.command()
def memory(action: str = "stats", q: str = ""):
    """Manage vector memory."""
    from memory.vector import get_stats, search, clear
    if action == "stats":
        stats = get_stats()
        console.print(Panel(f"Total Memories: [bold green]{stats['count']}[/bold green]", title="Memory Stats"))
    elif action == "search":
        results = search(q)
        if results:
            console.print(Panel("\n".join([f"- {r}" for r in results]), title=f"Search Results: {q}"))
        else:
            console.print("[yellow]No relevant memories found.[/yellow]")
    elif action == "clear":
        from rich.prompt import Confirm
        if Confirm.ask("Are you sure you want to wipe all JARVIS memories?"):
            res = clear()
            console.print(f"[green]{res}[/green]")

def memory_menu():
    from memory.vector import get_stats
    while True:
        stats = get_stats()
        console.print(Panel(f"Stored Memories: [bold cyan]{stats['count']}[/bold cyan]", title="Memory Management"))
        console.print("\n[1] Search | [2] Clear All | [b] Back")
        choice = Prompt.ask("Choice", choices=["1", "2", "b"], default="b")
        if choice == "1":
            q = Prompt.ask("Search query")
            memory(action="search", q=q)
            input("\nPress Enter to continue...")
        elif choice == "2":
            memory(action="clear")
        else:
            break

def personality_menu():
    from core.config import load_config, save_config
    config = load_config()
    current = config.get("personality", "professional")
    
    console.print(Panel(f"Current Personality: [bold cyan]{current.capitalize()}[/bold cyan]", title="Personality Settings"))
    console.print("\n[1] Professional | [2] Sarcastic (Grok) | [3] Concise | [4] Mentor | [b] Back")
    
    choice = Prompt.ask("Select personality", choices=["1", "2", "3", "4", "b"], default="b")
    
    mapping = {"1": "professional", "2": "sarcastic", "3": "concise", "4": "mentor"}
    if choice in mapping:
        config["personality"] = mapping[choice]
        save_config(config)
        console.print(f"[green]Personality updated to {mapping[choice].capitalize()}[/green]")

@app.command()
def personality(type: str):
    """Set behavior profile."""
    from core.config import load_config, save_config
    config = load_config()
    if type in ["professional", "sarcastic", "concise", "mentor"]:
        config["personality"] = type
        save_config(config)
        console.print(f"[green]Personality set to {type.capitalize()}[/green]")
    else:
        console.print("[red]Invalid personality type.[/red]")

def models_menu():
    from core.config import load_config, save_config
    config = load_config()
    current_p = config.get("provider", "ollama")
    current_m = config.get("jarvis_model", "llama3")
    
    console.print(Panel(f"Current Provider: [bold cyan]{current_p.upper()}[/bold cyan]\nCurrent Model: [bold yellow]{current_m}[/bold yellow]", title="LLM Model Selection"))
    
    console.print("\n[1] Ollama (Local) | [2] OpenAI | [3] Gemini | [4] Claude | [5] Grok | [6] Mistral | [7] NVIDIA NIM | [b] Back")
    
    choice = Prompt.ask("Select provider", choices=["1", "2", "3", "4", "5", "6", "7", "b"], default="b")
    
    p_mapping = {
        "1": "ollama", "2": "openai", "3": "gemini", "4": "claude", 
        "5": "grok", "6": "mistral", "7": "nvidia"
    }
    
    if choice in p_mapping:
        provider = p_mapping[choice]
        config["provider"] = provider
        
        models = {
            "ollama": ["llama3", "mistral", "codellama", "phi3"],
            "openai": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            "gemini": ["gemini-1.5-pro", "gemini-1.5-flash"],
            "claude": ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229"],
            "grok": ["grok-beta"],
            "mistral": ["mistral-large-latest", "open-mixtral-8x22b"],
            "nvidia": ["nvidia/llama-3.1-405b-instruct", "nvidia/nemotron-4-340b-instruct"]
        }
        
        console.print(f"\n[bold]Common Models for {provider.upper()}:[/bold]")
        for m in models[provider]:
            console.print(f"- {m}")
        
        new_model = Prompt.ask("Enter model name", default=models[provider][0])
        config["jarvis_model"] = new_model
        if provider == "gemini":
            config["gemini_model"] = new_model
        save_config(config)
        console.print(f"[green]Switched to {provider.upper()} ({new_model})[/green]")

@app.command()
def models(provider: str, model: str):
    """Directly set LLM."""
    from core.config import load_config, save_config
    config = load_config()
    config["provider"] = provider.lower()
    config["jarvis_model"] = model
    save_config(config)
    console.print(f"[green]Provider set to {provider.upper()}, Model to {model}[/green]")

@app.command()
def init():
    """Initialize project JARVIS.md."""
    if os.path.exists("JARVIS.md"):
        console.print("[yellow]JARVIS.md already exists.[/yellow]")
    else:
        with open("JARVIS.md", "w") as f:
            f.write("# JARVIS Project Instructions\n\n- Define project rules here.")
        console.print("[green]Created JARVIS.md[/green]")

if __name__ == "__main__":
    app()
