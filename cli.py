import os
import sys
import time
from typing import Optional
from typing_extensions import Annotated

# 1. Self-Repairing Dependency Check
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.deps import ensure_all
ensure_all()

# 2. Global Self-Repair & Reporting Engine
from core.repair import init_repair_engine
init_repair_engine()

# 3. Auto-Update Check
from core.update import auto_update_check, CURRENT_VERSION
auto_update_check()

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.prompt import Prompt, Confirm

# Internal Modules
from core.brain import think, get_provider
from core.agent import debug_loop, troubleshoot_loop
from core.config import setup_wizard, get_env_with_config, CONFIG_FILE, load_config, save_config
from core.ui import display_welcome, get_main_menu_table
from core.health import check_system_health, display_health_report, auto_repair_workspace
from core.repair import auto_check_on_launch
from core.nave_loop import run_nave_loop
import core.menus as menus

# Prompt Toolkit for slash commands
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style

app = typer.Typer(help="🚀 JARVIS: The Ultimate Local AI Coding Assistant")
console = Console()

COMMANDS = [
    "/chat", "/fix", "/voice", "/watch", "/config", "/init", "/analyze", "/analyze-file",
    "/locate", "/undo", "/dashboard", "/memory", "/personality", "/models", "/focus", 
    "/cloud", "/network", "/ssh", "/server", "/troubleshoot", "/free", "/model", "/help", "/health", "/upgrade", "/nave", "/exit"
]

@app.command()
def menu():
    """Launch the interactive Gemini-style slash command menu."""
    display_welcome()
    
    # 1. System Health Check at Launch (Automatic if configured)
    auto_check_on_launch()

    completer = WordCompleter(COMMANDS, ignore_case=True)
    session = PromptSession(completer=completer)
    style = Style.from_dict({'prompt': 'ansicyan bold'})
    last_ctrl_c = 0

    while True:
        try:
            # Display Workspace Info Box before each prompt
            cwd = os.getcwd()
            console.print(Panel(f"📁 [bold white]Workspace:[/bold white] [cyan]{cwd}[/cyan]", border_style="dim", expand=False))
            
            text = session.prompt('JARVIS > ', style=style).strip()
            last_ctrl_c = 0 
            
            if not text: continue
            if not text.startswith("/"):
                # Use Nave AI loop if personality is set
                config = load_config()
                if config.get("personality") == "nave_ai":
                    nave(text)
                else:
                    chat(text)
                continue

            parts = text.split(" ", 2)
            cmd = parts[0].lower()
            prompt_name = parts[1][1:] if len(parts) > 1 and parts[1].startswith("@") else None
            args = parts[2] if prompt_name and len(parts) > 2 else (" ".join(parts[1:]) if len(parts) > 1 else "")

            if cmd == "/chat": 
                config = load_config()
                if config.get("personality") == "nave_ai":
                    nave(args or Prompt.ask("Idea to refine"))
                else:
                    chat(args or Prompt.ask("Question"), prompt=prompt_name)
            elif cmd == "/nave": nave(args or Prompt.ask("Idea to refine"))
            elif cmd == "/fix": fix(args or Prompt.ask("Issue to fix"), prompt=prompt_name)
            elif cmd in ["/voice", "/v"]: voice()
            elif cmd in ["/watch", "/w"]: watch()
            elif cmd == "/config": menus.config_menu()
            elif cmd == "/init": init()
            elif cmd == "/analyze": analyze(args or ".")
            elif cmd == "/analyze-file": analyze_file(args or Prompt.ask("Path to file"), prompt=prompt_name)
            elif cmd == "/locate": locate(args or Prompt.ask("Filename to search for"))
            elif cmd == "/network": menus.network_menu()
            elif cmd == "/ssh": menus.ssh_command(args)
            elif cmd == "/server": menus.server_menu()
            elif cmd == "/undo": undo(args or Prompt.ask("Path to undo"))
            elif cmd == "/dashboard": dashboard()
            elif cmd == "/memory": menus.memory_menu()
            elif cmd == "/personality": menus.personality_menu()
            elif cmd == "/models": menus.models_menu()
            elif cmd == "/prompts": menus.prompts_menu()
            elif cmd == "/cloud": menus.cloud_menu()
            elif cmd == "/model": show_model_status()
            elif cmd == "/focus": focus(args or Prompt.ask("Path to focus on"))
            elif cmd in ["/troubleshoot", "/t"]: troubleshoot(args or Prompt.ask("Failing command"), prompt=prompt_name)
            elif cmd == "/free": free_keys()
            elif cmd in ["/help", "/h"]: menus.robust_help()
            elif cmd == "/health":
                health_results = check_system_health()
                display_health_report(health_results)
            elif cmd == "/upgrade":
                from core.update import manual_upgrade
                manual_upgrade()
            elif cmd in ["/exit", "/quit", "/q"]:
                console.print("[yellow]Goodbye, Sir.[/yellow]")
                break
            else:
                console.print(f"[red]Unknown command: {cmd}. Type /help for options.[/red]")

        except KeyboardInterrupt:
            now = time.time()
            if now - last_ctrl_c < 2: 
                console.print("\n[yellow]Secure shutdown initiated. Goodbye.[/yellow]")
                break
            else:
                console.print("\n[bold red]Press Ctrl+C again to exit JARVIS.[/bold red]")
                last_ctrl_c = now
        except EOFError: break

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

@app.command()
def chat(
    q: str, 
    model: Annotated[Optional[str], typer.Option("--model", "-m")] = None, 
    prompt: Annotated[Optional[str], typer.Option("--prompt", "-p")] = None
):
    """Chat with JARVIS."""
    provider = get_env_with_config("provider") or "ollama"
    console.print(Panel(f"JARVIS [bold cyan]({provider})[/bold cyan] [dim]prompt: {prompt or 'default'}[/dim]", border_style="cyan"))
    response = think("", q, model=model, prompt_name=prompt)
    console.print(Markdown(response))

@app.command()
def fix(
    issue: str, 
    model: Annotated[Optional[str], typer.Option("--model", "-m")] = None, 
    prompt: Annotated[Optional[str], typer.Option("--prompt", "-p")] = None
):
    """Autonomous debug loop."""
    debug_loop(issue, model=model, prompt=prompt)

@app.command()
def analyze_file(
    path: str, 
    model: Annotated[Optional[str], typer.Option("--model", "-m")] = None, 
    prompt: Annotated[Optional[str], typer.Option("--prompt", "-p")] = None
):
    """Deeply analyze a single file."""
    if not os.path.exists(path):
        console.print(f"[red]Error: File not found:[/red] {path}"); return
    with open(path, 'r') as f: content = f.read()
    console.print(f"[bold cyan]Analyzing file:[/bold cyan] {path}...")
    response = think(f"File Path: {path}\nFile Content:\n{content}", "Analyze this file for bugs, security issues, and performance improvements.", model=model, prompt_name=prompt)
    console.print(Markdown(response))

@app.command()
def locate(name: str, root: str = "/"):
    """Search for a file/directory across the computer."""
    from tools.search import system_find
    console.print(f"[bold cyan]Searching for '{name}' starting from {root}...[/bold cyan]")
    results = system_find(name, root)
    console.print(Panel(results, title=f"Locate Results: {name}"))

@app.command()
def undo(path: str):
    """Rollback last edit."""
    from tools.editor import undo_last_edit
    res = undo_last_edit(path)
    if "Error" in res: console.print(f"[red]{res}[/red]")
    else: console.print(f"[green]{res}[/green]")

@app.command()
def dashboard():
    """Launch multi-window live dashboard."""
    from core.dashboard import Dashboard
    Dashboard().run()

@app.command()
def focus(path: str):
    """Set working context."""
    if os.path.exists(path): console.print(Panel(f"[green]Focus successfully set to:[/green]\n{os.path.abspath(path)}", border_style="green"))
    else: console.print(f"[red]Error: Path does not exist:[/red] {path}")

@app.command()
def troubleshoot(
    command: str, 
    model: Annotated[Optional[str], typer.Option("--model", "-m")] = None, 
    prompt: Annotated[Optional[str], typer.Option("--prompt", "-p")] = None
):
    """Autonomous troubleshooting."""
    troubleshoot_loop(command, model=model, prompt=prompt)

@app.command()
def voice():
    """Voice control."""
    from voice.voice import run_voice
    run_voice()

@app.command()
def watch():
    """Proactive monitoring."""
    from watcher.monitor import start_monitor
    start_monitor()

@app.command()
def config():
    """Show configuration."""
    menus.config_menu()

@app.command()
def analyze(path: str = "."):
    """Project health analytics."""
    from tools.analytics import project_summary
    console.print(f"[bold cyan]Analyzing project at {path}...[/bold cyan]")
    summary = project_summary(path)
    table = Table(title="Project Health Analytics", border_style="cyan")
    table.add_column("Metric", style="white"); table.add_column("Value", style="green")
    table.add_row("Total Files", str(summary["total_files"]))
    table.add_row("Total Lines (Python)", str(summary["total_lines"]))
    for lang, count in summary["languages"].items(): table.add_row(f"Language ({lang})", str(count))
    console.print(table)
    if summary["hotspots"]:
        console.print("\n[bold red]Complexity Hotspots (Refactor Recommended):[/bold red]")
        for hs in summary["hotspots"]: console.print(f"- {hs['path']} (Score: {hs['score']})")

@app.command()
def github(action: str, repo: str, title: str = "", body: str = "", head: str = "", base: str = "main"):
    """GitHub actions."""
    from tools.github import github_tool
    if action == "info": res = github_tool.get_repo_info(repo)
    elif action == "issue": res = github_tool.create_issue(repo, title, body)
    elif action == "create_pr": res = github_tool.create_pr(repo, title, body, head, base)
    elif action == "list_prs": res = github_tool.list_pull_requests(repo)
    else: res = "Unknown action."
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
        if results: console.print(Panel("\n".join([f"- {r}" for r in results]), title=f"Search: {q}"))
        else: console.print("[yellow]No relevant memories found.[/yellow]")
    elif action == "clear":
        if Confirm.ask("Are you sure you want to wipe all JARVIS memories?"):
            console.print(f"[green]{clear()}[/green]")

@app.command()
def personality(type: str):
    """Set behavior profile."""
    config = load_config()
    if type in ["professional", "sarcastic", "concise", "mentor"]:
        config["personality"] = type
        save_config(config)
        console.print(f"[green]Personality set to {type.capitalize()}[/green]")
    else: console.print("[red]Invalid type.[/red]")

@app.command()
def models(provider: str, model: str):
    """Directly set LLM."""
    config = load_config()
    config["provider"] = provider.lower()
    config["jarvis_model"] = model
    save_config(config)
    console.print(f"[green]Set to {provider.upper()} ({model})[/green]")

@app.command()
def prompts(action: str = "list", name: str = "", text: str = ""):
    """Manage prompts."""
    from core.prompts import list_prompts, save_prompt, delete_prompt
    if action == "list": console.print(list_prompts())
    elif action == "add": console.print(save_prompt(name, text))
    elif action == "delete": console.print(delete_prompt(name))
    elif action == "set":
        config = load_config()
        config["active_prompt"] = name
        save_config(config)
        console.print(f"Active set to {name}")

@app.command()
def free_keys():
    """Free API keys links."""
    info = "# 🎁 Get Started for Free\n1. [Gemini Flash](https://aistudio.google.com/)\n2. [Mistral](https://console.mistral.ai/)\n3. [NVIDIA](https://build.nvidia.com/)\n4. [Ollama](https://ollama.com/)"
    console.print(Panel(Markdown(info), title="Free Tier Automation"))

@app.command()
def cloud(platform: str, action: str = "list", path: str = ""):
    """Manage cloud storage."""
    from tools.cloud import list_dropbox, list_gdrive, list_icloud
    console.print(f"[bold cyan]Accessing {platform.upper()}...[/bold cyan]")
    if platform == "dropbox": res = list_dropbox(path)
    elif platform == "gdrive": res = list_gdrive()
    elif platform == "icloud": res = list_icloud(path)
    else: res = "Unknown platform."
    console.print(Panel(str(res), title=f"Cloud Result: {platform}"))

@app.command()
def init():
    """Initialize project."""
    if os.path.exists("JARVIS.md"): console.print("[yellow]Already exists.[/yellow]")
    else:
        with open("JARVIS.md", "w") as f: f.write("# JARVIS Project Instructions\n\n- Define rules here.")
        console.print("[green]Created JARVIS.md[/green]")

def show_model_status():
    provider_obj = get_provider()
    p_name = get_env_with_config("provider") or "ollama"
    model_name = provider_obj.model
    quota = "1,500 requests/day (Free Tier)" if p_name.lower() == "gemini" else "Managed by Provider"
    if p_name.lower() == "ollama": quota = "N/A (Unlimited Local)"
    status_info = f"[bold]Provider:[/bold] {p_name.upper()}\n[bold]Model:[/bold] {model_name}\n[bold]Quota:[/bold] {quota}"
    console.print(Panel(status_info, title="[bold magenta]Model Indicator[/bold magenta]", border_style="magenta"))

@app.command()
def health():
    """System health check."""
    results = check_system_health()
    errors_found = display_health_report(results)
    if errors_found:
        if Confirm.ask("[bold yellow]Issues detected in workspace. Attempt auto-repair?[/bold yellow]"):
            auto_repair_workspace(results)

@app.command()
def upgrade():
    """Upgrade JARVIS to the latest version."""
    from core.update import manual_upgrade
    manual_upgrade()

@app.command()
def nave(q: str):
    """Nave AI Redundancy Loop Refinement."""
    console.print(Panel(f"🚀 [bold cyan]Nave AI Redundancy Loop[/bold cyan]\nRefining: [dim]{q}[/dim]", border_style="cyan"))
    result = run_nave_loop(q)
    console.print(Markdown(result))

if __name__ == "__main__": app()
