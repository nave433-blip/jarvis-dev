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

app = typer.Typer(help="🚀 JARVIS: The Ultimate Local AI Coding Assistant")
console = Console()

def display_welcome():
    welcome_text = """
    # JARVIS v1.0
    The Senior Software Engineering Assistant
    """
    console.print(Panel(Markdown(welcome_text), style="bold blue", border_style="cyan"))

def get_main_menu_table():
    table = Table(show_header=False, box=None)
    table.add_column("Command", style="cyan", justify="right")
    table.add_column("Description", style="white")
    
    table.add_row("[1] Chat", "Ask JARVIS anything about your code")
    table.add_row("[2] Fix", "Autonomous debugging and repair loop")
    table.add_row("[3] Voice", "Control JARVIS with voice commands")
    table.add_row("[4] Watch", "Proactive background file monitoring")
    table.add_row("[5] Config", "View and edit settings")
    table.add_row("[6] Init", "Setup JARVIS.md for the current project")
    table.add_row("[7] Analyze", "Deep project complexity and health analytics")
    table.add_row("[8] Undo", "Rollback the last file edit")
    table.add_row("[9] Dashboard", "Multi-window live dashboard")
    table.add_row("[m] Memory", "Manage and clear vector memory")
    table.add_row("[p] Personality", "Switch between Professional, Sarcastic, etc.")
    table.add_row("[f] Focus", "Set the working context for JARVIS")
    table.add_row("[t] Troubleshoot", "Run a command and automatically fix any errors")
    table.add_row("[h] Help", "Robust command documentation")
    table.add_row("[q] Quit", "Exit the JARVIS CLI")
    
    return Panel(table, title="[bold white]Main Menu[/bold white]", border_style="blue", expand=False)

@app.command()
def menu():
    """Launch the interactive graphical CLI menu."""
    display_welcome()
    while True:
        console.print(Align.center(get_main_menu_table()))
        choice = Prompt.ask("\n[bold]Select an option[/bold]", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "m", "p", "f", "t", "h", "q"], default="1")
        
        if choice == "1":
            q = Prompt.ask("What is your question?")
            chat(q)
        elif choice == "2":
            issue = Prompt.ask("Describe the issue to fix")
            fix(issue)
        elif choice == "3":
            voice()
        elif choice == "4":
            watch()
        elif choice == "5":
            config_menu()
        elif choice == "6":
            init()
        elif choice == "7":
            analyze()
        elif choice == "8":
            path = Prompt.ask("Path to file to undo")
            undo(path)
        elif choice == "9":
            dashboard()
        elif choice == "m":
            memory_menu()
        elif choice == "p":
            personality_menu()
        elif choice == "f":
            path = Prompt.ask("Enter path to focus on", default=".")
            focus(path)
        elif choice == "t":
            cmd = Prompt.ask("Enter the command that is failing")
            troubleshoot(cmd)
        elif choice == "h":
            robust_help()
        elif choice == "q":
            console.print("[yellow]Goodbye, Sir.[/yellow]")
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
    
    ### 💬 Chat
    Uses the configured LLM (Ollama, Gemini, Claude, or Grok) to answer technical questions. 
    It has access to your project context if `SEARCH` and `READ` tools are invoked by the brain.
    
    ### 🔧 Fix
    An autonomous agent loop. JARVIS will:
    1. Research the issue using search tools.
    2. Propose a strategy.
    3. Execute changes using the `EDIT` tool.
    4. Validate and repeat until resolved.
    
    ### 🎙 Voice
    Hands-free control. JARVIS transcribes your speech and pipes it directly into the `Fix` or `Chat` engine.
    
    ### 👁 Watch
    Monitors `.py` files in real-time. When a file is saved, JARVIS automatically analyzes the changes 
    and stores the insights in its vector memory for future context.

    ### 🖥 Dashboard
    A live, multi-window TUI (Terminal User Interface) that displays your recent chat history, 
    system logs, project statistics, and the current focus context in a single layout.

    ### 🎯 Focus
    Narrow JARVIS's scope to a specific file or directory. This ensures the agent prioritizes 
    the relevant context when performing analytics or debugging.

    ### 🧠 Memory
    Manage your vector memory. View how many insights JARVIS has stored, search through them, 
    or wipe the slate clean if you want to start fresh.

    ### 🎭 Personality
    Switch JARVIS's behavioral profile. Choose from:
    - **Professional:** Standard senior engineer.
    - **Sarcastic:** Witty and edgy (Grok-style).
    - **Concise:** Minimalist and direct.
    - **Mentor:** Patient and educational.

    ### 🛠 Troubleshoot
    Inspired by Warp's Agent Mode. Provide a command that is failing; JARVIS will run it, 
    capture the error, and automatically enter a debug loop to fix the root cause.
    
    ### ⚙️ Config
    Manage your LLM providers and API keys. Supports local Ollama and cloud-based giants.
    """
    console.print(Panel(Markdown(help_md), title="[bold green]System Documentation[/bold green]", border_style="green"))
    input("\nPress Enter to return to menu...")

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
        # Persistent focus could be added to config later
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
    
    input("\nPress Enter to return...")

@app.command()
def github(action: str, repo: str, title: str = "", body: str = "", head: str = "", base: str = "main"):
    """Perform GitHub actions (info, issue, create_pr, list_prs)."""
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
    """Manage JARVIS's vector memory (stats, search, clear)."""
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
    """Set JARVIS's personality (professional, sarcastic, concise, mentor)."""
    from core.config import load_config, save_config
    config = load_config()
    if type in ["professional", "sarcastic", "concise", "mentor"]:
        config["personality"] = type
        save_config(config)
        console.print(f"[green]Personality set to {type.capitalize()}[/green]")
    else:
        console.print("[red]Invalid personality type.[/red]")

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
