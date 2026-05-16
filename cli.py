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
from core.agent import debug_loop, troubleshoot_loop, forge_loop
from core.config import setup_wizard, get_env_with_config, CONFIG_FILE, load_config, save_config
from core.ui import display_welcome, get_main_menu_table
from core.health import check_system_health, display_health_report, auto_repair_workspace, update_all_repos
from core.repair import auto_check_on_launch
from core.nave_loop import run_nave_loop
import core.menus as menus

# Prompt Toolkit for slash commands
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings

app = typer.Typer(help="🚀 JARVIS: The Ultimate Local AI Coding Assistant")
console = Console()

COMMANDS = [
    "/chat", "/fix", "/forge", "/decode", "/lookup", "/hardware", "/voice", "/watch", "/config", "/init", "/analyze", "/analyze-file",
    "/locate", "/undo", "/dashboard", "/memory", "/personality", "/models", "/focus", 
    "/cloud", "/network", "/ssh", "/server", "/troubleshoot", "/free", "/model", "/help", "/health", "/upgrade", "/nave", "/sync", "/doctor", "/git", "/search", "/clear", "/exit"
]

@app.command()
def menu():
    """Launch the interactive Gemini-style slash command menu."""
    display_welcome()
    auto_check_on_launch()

    completer = WordCompleter(COMMANDS, ignore_case=True)
    kb = KeyBindings()
    @kb.add('escape')
    def _(event): event.app.exit(result="/exit")

    session = PromptSession(completer=completer, key_bindings=kb)
    style = Style.from_dict({'prompt': 'ansicyan bold'})
    last_ctrl_c = 0

    while True:
        try:
            cwd = os.getcwd()
            console.print(Panel(f"📁 [bold white]Workspace:[/bold white] [cyan]{cwd}[/cyan]", border_style="dim", expand=False))
            
            text = session.prompt('JARVIS > ', style=style).strip()
            last_ctrl_c = 0 
            if not text: continue
            if text == "/exit":
                console.print("[yellow]Goodbye, Sir.[/yellow]"); break
            
            if not text.startswith("/"):
                config = load_config()
                if config.get("personality") == "nave_ai": run_nave_loop(text)
                else: chat(text)
                continue

            parts = text.split(" ", 2)
            cmd = parts[0].lower()
            prompt_name = parts[1][1:] if len(parts) > 1 and parts[1].startswith("@") else None
            args = parts[2] if prompt_name and len(parts) > 2 else (" ".join(parts[1:]) if len(parts) > 1 else "")

            if cmd == "/chat": chat(args or Prompt.ask("Question"), prompt=prompt_name)
            elif cmd == "/fix": fix(args or Prompt.ask("Issue to fix"), prompt=prompt_name)
            elif cmd == "/forge": forge(args or Prompt.ask("Task to forge"))
            elif cmd == "/decode": decode(args or Prompt.ask("Text/Script to decode"))
            elif cmd == "/lookup": lookup(args or Prompt.ask("Command to find"))
            elif cmd == "/hardware": hardware_menu()
            elif cmd == "/voice": voice()
            elif cmd == "/watch": watch()
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
            elif cmd == "/doctor": run_doctor()
            elif cmd == "/git": ai_git(args or Prompt.ask("What git operation?"))
            elif cmd == "/search":
                q = args or Prompt.ask("Search session history")
                results = session.history.get_strings()
                matches = [s for s in results if q.lower() in s.lower()]
                console.print(Panel("\n".join(matches[-10:]), title=f"History Search: {q}"))
            elif cmd == "/clear": console.clear()
            elif cmd in ["/help", "/h"]: menus.robust_help()
            elif cmd == "/exit": break
            else: console.print(f"[red]Unknown command: {cmd}. Type /help for options.[/red]")

        except KeyboardInterrupt:
            now = time.time()
            if now - last_ctrl_c < 2: 
                console.print("\n[yellow]Secure shutdown initiated. Goodbye.[/yellow]"); break
            else:
                console.print("\n[bold red]Press Ctrl+C again to exit JARVIS.[/bold red]")
                last_ctrl_c = now
        except EOFError: break

@app.command()
def chat(q: str, model: Annotated[Optional[str], typer.Option("--model", "-m")] = None, prompt: Annotated[Optional[str], typer.Option("--prompt", "-p")] = None):
    """Chat with JARVIS."""
    provider = get_env_with_config("provider") or "ollama"
    console.print(Panel(f"JARVIS [bold cyan]({provider})[/bold cyan] [dim]prompt: {prompt or 'default'}[/dim]", border_style="cyan"))
    response = think("", q, model=model, prompt_name=prompt)
    console.print(Markdown(response))

@app.command()
def forge(task: str, model: Annotated[Optional[str], typer.Option("--model", "-m")] = None):
    """Hardcore code synthesis for creating unprecedented solutions."""
    forge_loop(task, model=model)

@app.command()
def decode(content: str):
    """Universal decoder for scripts, languages, and coding paradigms."""
    console.print(f"[bold cyan]Decoding:[/bold cyan] {content[:50]}...")
    prompt = f"Decode and explain the following content. If it's a script, explain logic. If it's a language/font, translate. Provide maximum technical depth: {content}"
    response = think("", prompt, prompt_name="nave_sovereign")
    console.print(Markdown(response))

@app.command()
def lookup(request: str):
    """Smart command discovery (Gemini-style)."""
    prompt = f"The user wants to perform this action: {request}. Suggest the best shell command or JARVIS command to use."
    response = think("", prompt)
    console.print(Panel(Markdown(response), title="Command Discovery"))

@app.command()
def hardware_menu():
    """Manage and probe physical ports and USB devices."""
    from tools.hardware import get_hardware_summary, list_usb_devices, probe_ports
    while True:
        console.print(get_hardware_summary())
        console.print("\n[1] List USB Details | [2] Full System Probe | [b] Back")
        choice = Prompt.ask("Choice", choices=["1", "2", "b"], default="b")
        if choice == "1": console.print(Panel(list_usb_devices(), title="USB Diagnostics"))
        elif choice == "2": console.print(Panel(probe_ports(), title="System Port Probe"))
        else: break

@app.command()
def fix(issue: str, model: Annotated[Optional[str], typer.Option("--model", "-m")] = None, prompt: Annotated[Optional[str], typer.Option("--prompt", "-p")] = None):
    """Autonomous debug loop."""
    debug_loop(issue, model=model, prompt=prompt)

@app.command()
def analyze_file(path: str, model: Annotated[Optional[str], typer.Option("--model", "-m")] = None, prompt: Annotated[Optional[str], typer.Option("--prompt", "-p")] = None):
    """Deeply analyze a single file."""
    if not os.path.exists(path):
        console.print(f"[red]Error: File not found:[/red] {path}"); return
    with open(path, 'r') as f: content = f.read()
    console.print(f"[bold cyan]Analyzing file:[/bold cyan] {path}...")
    response = think(f"File Path: {path}\nFile Content:\n{content}", "Analyze for bugs and improvements.", model=model, prompt_name=prompt)
    console.print(Markdown(response))

@app.command()
def locate(name: str, root: str = "/"):
    """Search for a file/directory across the computer."""
    from tools.search import system_find
    console.print(f"[bold cyan]Searching for '{name}' starting from {root}...[/bold cyan]")
    results = system_find(name, root)
    console.print(Panel(results, title=f"Locate Results: {name}"))

@app.command()
def troubleshoot(command: str, model: Annotated[Optional[str], typer.Option("--model", "-m")] = None, prompt: Annotated[Optional[str], typer.Option("--prompt", "-p")] = None):
    """Autonomous troubleshooting."""
    troubleshoot_loop(command, model=model, prompt=prompt)

@app.command()
def undo(path: str):
    """Rollback last edit."""
    from tools.editor import undo_last_edit
    res = undo_last_edit(path); console.print(f"[green]{res}[/green]")

@app.command()
def dashboard():
    """Launch multi-window live dashboard."""
    from core.dashboard import Dashboard; Dashboard().run()

@app.command()
def focus(path: str):
    """Set working context."""
    if os.path.exists(path): console.print(Panel(f"[green]Focus set to:[/green] {os.path.abspath(path)}", border_style="green"))
    else: console.print(f"[red]Error: Path does not exist:[/red] {path}")

@app.command()
def voice():
    from voice.voice import run_voice; run_voice()

@app.command()
def watch():
    from watcher.monitor import start_monitor; start_monitor()

@app.command()
def config(): menus.config_menu()

@app.command()
def analyze(path: str = "."):
    from tools.analytics import project_summary
    summary = project_summary(path)
    table = Table(title="Health Stats", border_style="cyan")
    table.add_row("Files", str(summary["total_files"])); table.add_row("Lines", str(summary["total_lines"]))
    console.print(table)

@app.command()
def github(action: str, repo: str, title: str = "", body: str = "", head: str = "", base: str = "main"):
    from tools.github import github_tool
    if action == "info": res = github_tool.get_repo_info(repo)
    elif action == "issue": res = github_tool.create_issue(repo, title, body)
    else: res = "Unknown action."
    console.print(Panel(str(res), title=f"GitHub Result: {action}"))

@app.command()
def memory(action: str = "stats", q: str = ""):
    from memory.vector import get_stats, search, clear
    if action == "stats": console.print(Panel(f"Total Memories: {get_stats()['count']}"))
    elif action == "search":
        res = search(q)
        if res: console.print(Panel("\n".join(res)))
    elif action == "clear":
        if Confirm.ask("Clear all?"): console.print(f"[green]{clear()}[/green]")

@app.command()
def run_doctor():
    from core.deps import ensure_all
    ensure_all()
    results = check_system_health()
    display_health_report(results)

@app.command()
def ai_git(task: str):
    prompt = f"Perform git task: {task}"
    response = think("", prompt); console.print(Markdown(response))

@app.command()
def init():
    if os.path.exists("JARVIS.md"): console.print("[yellow]Already exists.[/yellow]")
    else:
        with open("JARVIS.md", "w") as f: f.write("# JARVIS Rules")
        console.print("[green]Created JARVIS.md[/green]")

def show_model_status():
    provider_obj = get_provider()
    p_name = get_env_with_config("provider") or "ollama"
    status_info = f"Provider: {p_name.upper()}\nModel: {provider_obj.model}"
    console.print(Panel(status_info, title="Model Status", border_style="magenta"))

if __name__ == "__main__": app()
