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
    "/cloud", "/network", "/ssh", "/server", "/troubleshoot", "/free", "/model", "/doctor",
    "/git", "/nave", "/sync", "/upgrade", "/update", "/exit"
]

def get_bottom_toolbar():
    try:
        cwd = os.getcwd()
        config = load_config()
        model = config.get("jarvis_model", "unknown")
        provider = config.get("provider", "ollama")
        return f" [cyan]📁 {cwd}[/cyan] | [magenta]🧠 {provider.upper()} ({model})[/magenta]"
    except:
        return " [red]System Initializing...[/red]"

@app.command()
def menu():
    """Launch the interactive Gemini-style slash command menu."""
    display_welcome()
    auto_check_on_launch()

    completer = WordCompleter(COMMANDS, ignore_case=True)
    kb = KeyBindings()
    @kb.add('escape')
    def _(event): event.app.exit(result="/exit")

    session = PromptSession(
        completer=completer, 
        key_bindings=kb,
        bottom_toolbar=get_bottom_toolbar
    )
    style = Style.from_dict({
        'prompt': 'ansicyan bold',
        'bottom-toolbar': 'bg:#1e1e1e #888888',
    })
    last_ctrl_c = 0

    while True:
        try:
            text = session.prompt('JARVIS > ', style=style).strip()
            last_ctrl_c = 0 
            if not text: continue
            if text in ["/exit", "exit", "quit"]:
                console.print("[yellow]Goodbye, Sir.[/yellow]"); break
            
            # --- Smart Intent Router ---
            text_low = text.lower()
            tokens = text.split()
            first_word = tokens[0].lower() if tokens else ""
            
            # 1. Alias & Verb Mapping
            verb_map = {
                "fix": "/fix", "repair": "/fix", "patch": "/fix",
                "forge": "/forge", "create": "/forge", "build": "/forge",
                "chat": "/chat", "ask": "/chat", "tell": "/chat",
                "analyze": "/analyze", "audit": "/analyze", "check": "/analyze",
                "decode": "/decode", "translate": "/decode",
                "lookup": "/lookup", "search": "/lookup",
                "locate": "/locate", "find": "/locate",
                "update": "/upgrade", "upgrade": "/upgrade",
                "sync": "/sync", "doctor": "/doctor",
                "cloud": "/cloud", "ssh": "/ssh", "server": "/server",
                "memory": "/memory", "personality": "/personality", "models": "/models"
            }

            if not text.startswith("/"):
                if first_word in verb_map:
                    # Rewrite text as a slash command
                    args = " ".join(tokens[1:])
                    text = verb_map[first_word] + " " + args
                elif any(kw in text_low for kw in ["fix this", "bug in", "repair my"]):
                    text = "/fix " + text
                else:
                    # Default to Chat or Nave Loop
                    config = load_config()
                    if config.get("personality") == "nave_ai": 
                        run_nave_loop(text)
                    else: 
                        chat(text)
                    continue

            # --- Standard Command Processing ---
            parts = text.split(" ", 2)
            cmd = parts[0].lower()
            
            # Final command sanitization
            if cmd == "/update": cmd = "/upgrade"

            # Parse prompt override (@persona)
            prompt_name = None
            args = ""
            if len(parts) > 1:
                if parts[1].startswith("@"):
                    prompt_name = parts[1][1:]
                    args = parts[2] if len(parts) > 2 else ""
                else:
                    args = " ".join(parts[1:])

            # --- Routing Table ---
            if cmd == "/chat": chat(args or Prompt.ask("Question"), prompt=prompt_name)
            elif cmd == "/fix": fix(args or Prompt.ask("Issue to fix"), prompt=prompt_name)
            elif cmd == "/forge": forge(args or Prompt.ask("Task to forge"))
            elif cmd == "/decode": decode(args or Prompt.ask("Content to decode"))
            elif cmd == "/lookup": lookup(args or Prompt.ask("What are you looking for?"))
            elif cmd == "/hardware": hardware_menu()
            elif cmd == "/voice": voice()
            elif cmd == "/watch": watch()
            elif cmd == "/config": menus.config_menu()
            elif cmd == "/init": init()
            elif cmd == "/analyze": analyze(args or ".")
            elif cmd == "/analyze-file": analyze_file(args or Prompt.ask("Path to file"), prompt=prompt_name)
            elif cmd == "/locate": locate(args or Prompt.ask("Name to search for"))
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
            elif cmd == "/git": ai_git(args or Prompt.ask("Git task?"))
            elif cmd == "/nave":
                q = args or Prompt.ask("Technical idea to refine?")
                res = run_nave_loop(q); console.print(Markdown(res))
            elif cmd == "/search":
                q = args or Prompt.ask("Search term")
                results = session.history.get_strings()
                matches = [s for s in results if q.lower() in s.lower()]
                console.print(Panel("\n".join(matches[-10:]), title=f"History: {q}"))
            elif cmd == "/clear": console.clear()
            elif cmd == "/help": menus.robust_help()
            elif cmd == "/health":
                results = check_system_health()
                display_health_report(results)
            elif cmd == "/upgrade":
                from core.update import manual_upgrade
                manual_upgrade()
            elif cmd == "/sync": update_all_repos()
            elif cmd == "/exit": break
            else:
                console.print(f"[red]Unknown command: {cmd}. Try /help.[/red]")

        except KeyboardInterrupt:
            now = time.time()
            if now - last_ctrl_c < 2: 
                console.print("\n[yellow]Shutdown complete. Goodbye.[/yellow]"); break
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
def chat(q: str, model: Annotated[Optional[str], typer.Option("--model", "-m")] = None, prompt: Annotated[Optional[str], typer.Option("--prompt", "-p")] = None):
    """Chat with JARVIS."""
    provider = get_env_with_config("provider") or "ollama"
    console.print(Panel(f"JARVIS [bold cyan]({provider})[/bold cyan] [dim]prompt: {prompt or 'default'}[/dim]", border_style="cyan"))
    response = think("", q, model=model, prompt_name=prompt)
    console.print(Markdown(response))

@app.command()
def fix(issue: str, model: Annotated[Optional[str], typer.Option("--model", "-m")] = None, prompt: Annotated[Optional[str], typer.Option("--prompt", "-p")] = None):
    """Autonomous debug loop."""
    debug_loop(issue, model=model, prompt=prompt)

@app.command()
def forge(task: str, model: Annotated[Optional[str], typer.Option("--model", "-m")] = None):
    """Hardcore code synthesis for creating unprecedented solutions."""
    forge_loop(task, model=model)

@app.command()
def decode(content: str):
    """Universal decoder for technical content."""
    prompt = f"Decode and explain with maximum depth: {content}"
    response = think("", prompt, prompt_name="nave_sovereign")
    console.print(Markdown(response))

@app.command()
def lookup(request: str):
    """Smart command discovery."""
    prompt = f"Suggest best command for: {request}"
    response = think("", prompt)
    console.print(Panel(Markdown(response), title="Lookup"))

@app.command()
def hardware_menu():
    """Physical port and USB diagnostics."""
    from tools.hardware import get_hardware_summary, list_usb_devices, probe_ports
    while True:
        console.print(get_hardware_summary())
        console.print("\n[1] USB | [2] All Ports | [b] Back")
        c = Prompt.ask("Choice", choices=["1", "2", "b"], default="b")
        if c == "1": console.print(Panel(list_usb_devices()))
        elif c == "2": console.print(Panel(probe_ports()))
        else: break

@app.command()
def analyze_file(path: str, model: Annotated[Optional[str], typer.Option("--model", "-m")] = None, prompt: Annotated[Optional[str], typer.Option("--prompt", "-p")] = None):
    """Deep audit of a single file."""
    if not os.path.exists(path):
        console.print(f"[red]Error: Not found:[/red] {path}"); return
    with open(path, 'r') as f: content = f.read()
    console.print(f"[bold cyan]Auditing:[/bold cyan] {path}...")
    res = think(f"Path: {path}\nContent:\n{content}", "Perform deep security and performance audit.", model=model, prompt_name=prompt)
    console.print(Markdown(res))

@app.command()
def locate(name: str, root: str = "/"):
    """Global system search."""
    from tools.search import system_find
    console.print(f"[bold cyan]Searching for '{name}'...[/bold cyan]")
    res = system_find(name, root); console.print(Panel(res, title="Locate"))

@app.command()
def troubleshoot(command: str, model: Annotated[Optional[str], typer.Option("--model", "-m")] = None, prompt: Annotated[Optional[str], typer.Option("--prompt", "-p")] = None):
    """Autonomous troubleshooting."""
    troubleshoot_loop(command, model=model, prompt=prompt)

@app.command()
def undo(path: str):
    """Safety rollback."""
    from tools.editor import undo_last_edit
    console.print(f"[green]{undo_last_edit(path)}[/green]")

@app.command()
def dashboard():
    """System monitor TUI."""
    from core.dashboard import Dashboard; Dashboard().run()

@app.command()
def focus(path: str):
    """Set context path."""
    if os.path.exists(path): console.print(Panel(f"[green]Focus set:[/green] {os.path.abspath(path)}", border_style="green"))
    else: console.print(f"[red]Error: Missing path:[/red] {path}")

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
    s = project_summary(path)
    t = Table(title="Health", border_style="cyan")
    t.add_row("Files", str(s["total_files"])); t.add_row("Lines", str(s["total_lines"]))
    console.print(t)

@app.command()
def github(action: str, repo: str, title: str = "", body: str = ""):
    from tools.github import github_tool
    if action == "info": res = github_tool.get_repo_info(repo)
    elif action == "issue": res = github_tool.create_issue(repo, title, body)
    else: res = "Unknown."
    console.print(Panel(str(res), title="GitHub"))

@app.command()
def run_doctor():
    from core.deps import ensure_all; ensure_all()
    results = check_system_health(); display_health_report(results)

@app.command()
def ai_git(task: str):
    res = think("", f"Git task: {task}"); console.print(Markdown(res))

@app.command()
def nave(q: str):
    """Refine a technical problem or idea using the multi-model Nave AI Redundancy Loop."""
    from core.nave_loop import run_nave_loop
    console.print(Panel(f"🚀 [bold cyan]Nave AI Redundancy Loop[/bold cyan]\nRefining: [dim]{q}[/dim]", border_style="cyan"))
    result = run_nave_loop(q)
    console.print(Markdown(result))

@app.command()
def init():
    if os.path.exists("JARVIS.md"): console.print("[yellow]Exists.[/yellow]")
    else:
        with open("JARVIS.md", "w") as f: f.write("# JARVIS Rules")
        console.print("[green]Created.[/green]")

def show_model_status():
    p_obj = get_provider(); p_name = get_env_with_config("provider") or "ollama"
    status = f"Brain: {p_name.upper()}\nModel: {p_obj.model}"
    console.print(Panel(status, title="Status", border_style="magenta"))

if __name__ == "__main__": app()
