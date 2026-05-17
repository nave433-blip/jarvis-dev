import os
import sys
import time
from typing import Optional, Dict
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
from core.handler import CommandHandler
import core.menus as menus

# Prompt Toolkit for slash commands
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.styles import Style
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import HTML

app = typer.Typer(help="🚀 JARVIS: The Ultimate Local AI Coding Assistant")
console = Console()

# Initialize Advanced Handler
handler = CommandHandler()

COMMANDS = [
    "/chat", "/fix", "/forge", "/decode", "/lookup", "/hardware", "/voice", "/watch", "/config", "/init", "/analyze", "/analyze-file",
    "/locate", "/undo", "/dashboard", "/memory", "/personality", "/models", "/focus", 
    "/cloud", "/network", "/ssh", "/server", "/troubleshoot", "/free", "/model", "/doctor",
    "/git", "/nave", "/sync", "/upgrade", "/update", "/connect", "/launch", "/plan", "/restart", "/reinstall", "/menu", "/exit"
]

# Register commands for fuzzy matching
for cmd in COMMANDS:
    if cmd != "/exit":
        handler.register(cmd, lambda x: None, help="System command")

def get_bottom_toolbar():
    try:
        cwd = os.getcwd()
        config = load_config()
        model = config.get("jarvis_model", "unknown")
        provider = config.get("provider", "ollama")
        return HTML(f'<style fg="cyan">📁 {cwd}</style> | <style fg="magenta">🧠 {provider.upper()} ({model})</style>')
    except:
        return HTML('<style fg="red">System Initializing...</style>')

@app.command()
def menu():
    """Launch the high-fidelity JARVIS Dashboard Menu."""
    console.clear()
    header = Panel(Markdown(f"# JARVIS SYSTEM INTERFACE\nVersion: `{CURRENT_VERSION}` | Role: `Engineering Sovereign`"), style="bold cyan", border_style="cyan")
    console.print(header)

    grid = Table.grid(expand=True)
    grid.add_column(justify="center"); grid.add_column(justify="center")
    
    core_table = Table(title="[bold magenta]Core AI Agents[/bold magenta]", show_header=True, header_style="bold magenta", border_style="magenta")
    core_table.add_column("Command", style="white"); core_table.add_column("Function", style="dim")
    core_table.add_row("/fix", "Autonomous repair & debugging"); core_table.add_row("/forge", "Hardcore code synthesis & creation"); core_table.add_row("/plan", "Strategic engineering roadmaps"); core_table.add_row("/nave", "Multi-model reasoning & refinement"); core_table.add_row("/copilot", "GitHub Copilot technical advice"); core_table.add_row("/chat", "Direct technical consultation")

    dev_table = Table(title="[bold green]DevOps & Utilities[/bold green]", show_header=True, header_style="bold green", border_style="green")
    dev_table.add_column("Command", style="white"); dev_table.add_column("Function", style="dim")
    dev_table.add_row("/doctor", "System health & self-repair"); dev_table.add_row("/cloud", "Bridge to G-Drive/Dropbox"); dev_table.add_row("/network", "Network discovery & security"); dev_table.add_row("/hardware", "USB & Physical port probing"); dev_table.add_row("/server", "Process & service management")
    
    grid.add_row(core_table, dev_table)
    console.print(grid)

    footer = Panel("[bold white]Settings:[/bold white] /config | [bold white]Accounts:[/bold white] /connect | [bold yellow]RESTART[/bold yellow] | [bold red]REINSTALL[/bold red]", border_style="dim")
    console.print(footer)
    console.print("\n[dim]*Type any command or natural language request below.*[/dim]")

@app.command()
def interactive():
    """Launch the main interactive Gemini-style prompt."""
    from core.config import verify_and_fix_local_llm
    display_welcome()
    verify_and_fix_local_llm()
    auto_check_on_launch()

    completer = WordCompleter(COMMANDS, ignore_case=True)
    kb = KeyBindings()
    @kb.add('escape')
    def _(event): event.app.exit(result="/exit")

    session = PromptSession(completer=completer, key_bindings=kb, bottom_toolbar=get_bottom_toolbar)
    style = Style.from_dict({'prompt': 'ansicyan bold', 'bottom-toolbar': 'bg:#1e1e1e #888888'})
    last_ctrl_c = 0

    while True:
        try:
            text = session.prompt('JARVIS > ', style=style).strip()
            last_ctrl_c = 0 
            if not text: continue
            if text in ["/exit", "exit", "quit"]:
                console.print("[yellow]Goodbye, Sir.[/yellow]"); break
            
            # --- Use Advanced Handler ---
            res = handler.handle(text)
            ui_hint = res.get("ui")
            
            if res.get("type") == "internal":
                cmd = res["command"]
                args = res.get("args", "")
                
                # Check for prompt override (@persona) in args if not already parsed
                prompt_name = None
                if "@" in args:
                    parts = args.split("@", 1)
                    args = parts[0].strip()
                    prompt_name = parts[1].split()[0]
                
                # --- Routing Table ---
                if cmd == "/chat": chat(args or Prompt.ask("Question"), prompt=prompt_name)
                elif cmd == "/fix": fix(args or Prompt.ask("Issue to fix"), prompt=prompt_name, ui_hint=ui_hint)
                elif cmd == "/plan": plan(args or Prompt.ask("Task for strategy"))
                elif cmd == "/forge": forge(args or Prompt.ask("Task to forge"))
                elif cmd == "/decode": decode(args or Prompt.ask("Content to decode"))
                elif cmd == "/lookup": lookup(args or Prompt.ask("What to find?"))
                elif cmd == "/hardware": hardware_menu()
                elif cmd == "/voice": voice()
                elif cmd == "/watch": watch()
                elif cmd == "/config": menus.config_menu()
                elif cmd == "/init": init()
                elif cmd == "/analyze": analyze(args or ".")
                elif cmd == "/analyze-file": analyze_file(args or Prompt.ask("Path to file"), prompt=prompt_name)
                elif cmd == "/locate": locate(args or Prompt.ask("Search name"))
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
                elif cmd == "/connect": menus.connect_menu()
                elif cmd == "/menu": menu()
                elif cmd == "/reinstall": reinstall()
                elif cmd == "/launch":
                    t = args or Prompt.ask("AI tool", choices=["claude-desktop", "claude", "openclaw", "hermes", "opencode", "codex", "copilot", "droid", "pi"])
                    launch(tool=t)
                elif cmd == "/model": show_model_status()
                elif cmd == "/focus": focus(args or Prompt.ask("Path"))
                elif cmd in ["/troubleshoot", "/t"]: troubleshoot(args or Prompt.ask("Command"), prompt=prompt_name)
                elif cmd == "/free": free_keys()
                elif cmd == "/doctor": run_doctor()
                elif cmd == "/git": ai_git(args or Prompt.ask("Git task?"))
                elif cmd == "/restart": restart()
                elif cmd == "/search":
                    q = args or Prompt.ask("Search history")
                    results = session.history.get_strings()
                    matches = [s for s in results if q.lower() in s.lower()]
                    console.print(Panel("\n".join(matches[-10:]), title=f"History: {q}"))
                elif cmd == "/clear": console.clear()
                elif cmd == "/help": menus.robust_help()
                elif cmd == "/health": display_health_report(check_system_health())
                elif cmd == "/upgrade":
                    from core.update import manual_upgrade
                    manual_upgrade()
                elif cmd == "/sync": update_all_repos()
                else: console.print(f"[red]Routing error for: {cmd}[/red]")
            
            elif res.get("type") == "shell":
                cmd = res["command"]
                if res.get("confirm", True):
                    console.print(Panel(f"[bold red]⚠️ EXECUTE SHELL COMMAND?[/bold red]\n\n[white]{cmd}[/white]", border_style="red"))
                    if Confirm.ask("Authorize?"):
                        from tools.shell import run_simple
                        console.print(run_simple(cmd))
                else:
                    from tools.shell import run_simple
                    console.print(run_simple(cmd))
            
            else:
                # Type is 'chat'
                chat(res.get("args", text))

        except KeyboardInterrupt:
            now = time.time()
            if now - last_ctrl_c < 2: 
                console.print("\n[yellow]Shutdown complete.[/yellow]"); break
            else:
                console.print("\n[bold red]Press Ctrl+C again to exit.[/bold red]")
                last_ctrl_c = now
        except EOFError: break

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """JARVIS: Your local AI engineer."""
    if ctx.invoked_subcommand is None:
        if not CONFIG_FILE.exists():
            console.print("[yellow]No configuration found. Starting setup...[/yellow]")
            setup_wizard()
        interactive()

@app.command()
def setup(): setup_wizard()

@app.command()
def restart():
    console.print("[yellow]🔄 Restarting JARVIS...[/yellow]")
    os.execv(sys.executable, ['python3'] + sys.argv)

@app.command()
def reinstall():
    """Perform a clean sovereign reinstallation of the JARVIS ecosystem."""
    if Confirm.ask("[bold red]⚠️ DANGER: This will wipe your local installation and start fresh. Proceed?[/bold red]"):
        console.print("[bold yellow]🚀 Initiating Sovereign Reinstallation...[/bold yellow]")
        # 1. Get base dir
        base_dir = os.path.dirname(os.path.abspath(__file__))
        # 2. Run install.sh from source
        os.system(f"cd {base_dir} && bash install.sh")
        console.print("[bold green]✅ Reinstallation complete. Please restart JARVIS.[/bold green]")
        sys.exit(0)

@app.command()
def chat(q: str, model: Annotated[Optional[str], typer.Option("--model", "-m")] = None, prompt: Annotated[Optional[str], typer.Option("--prompt", "-p")] = None):
    provider = get_env_with_config("provider") or "ollama"
    console.print(Panel(f"JARVIS [bold cyan]({provider})[/bold cyan] [dim]prompt: {prompt or 'default'}[/dim]", border_style="cyan"))
    console.print(Markdown(think("", q, model=model, prompt_name=prompt)))

@app.command()
def fix(issue: str, model: Annotated[Optional[str], typer.Option("--model", "-m")] = None, prompt: Annotated[Optional[str], typer.Option("--prompt", "-p")] = None):
    debug_loop(issue, model=model, prompt=prompt)

@app.command()
def plan(task: str, model: Annotated[Optional[str], typer.Option("--model", "-m")] = None):
    from core.agent import generate_plan
    console.print(Panel(f"📋 [bold cyan]STRATEGY PHASE:[/bold cyan] {task}", border_style="cyan"))
    console.print(Panel(Markdown(generate_plan(task, model=model)), title="Strategic Plan", border_style="green"))

@app.command()
def forge(task: str, model: Annotated[Optional[str], typer.Option("--model", "-m")] = None):
    forge_loop(task, model=model)

@app.command()
def decode(content: str):
    console.print(Markdown(think("", f"Decode and explain with maximum depth: {content}", prompt_name="nave_sovereign")))

@app.command()
def lookup(request: str):
    console.print(Panel(Markdown(think("", f"Suggest best command for: {request}")), title="Lookup"))

@app.command()
def hardware_menu():
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
    if not os.path.exists(path): console.print(f"[red]Error: Not found:[/red] {path}"); return
    with open(path, 'r') as f: content = f.read()
    console.print(f"[bold cyan]Auditing:[/bold cyan] {path}...")
    console.print(Markdown(think(f"Path: {path}\nContent:\n{content}", "Deep security and performance audit.", model=model, prompt_name=prompt)))

@app.command()
def locate(name: str, root: str = "/"):
    from tools.search import system_find
    console.print(f"[bold cyan]Searching for '{name}'...[/bold cyan]")
    console.print(Panel(system_find(name, root), title="Locate"))

@app.command()
def launch(tool: str):
    from tools.launcher import launch_tool
    console.print(f"[bold cyan]Launching:[/bold cyan] {tool}")
    console.print(f"[green]{launch_tool(tool)}[/green]")

@app.command()
def troubleshoot(command: str, model: Annotated[Optional[str], typer.Option("--model", "-m")] = None, prompt: Annotated[Optional[str], typer.Option("--prompt", "-p")] = None):
    troubleshoot_loop(command, model=model, prompt=prompt)

@app.command()
def undo(path: str):
    from tools.editor import undo_last_edit
    console.print(f"[green]{undo_last_edit(path)}[/green]")

@app.command()
def dashboard():
    from core.dashboard import Dashboard; Dashboard().run()

@app.command()
def focus(path: str):
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
    s = project_summary(path); t = Table(title="Health", border_style="cyan")
    t.add_row("Files", str(s["total_files"])); t.add_row("Lines", str(s["total_lines"]))
    console.print(t)

@app.command()
def run_doctor():
    from core.deps import ensure_all; ensure_all()
    display_health_report(check_system_health())

@app.command()
def ai_git(task: str):
    console.print(Markdown(think("", f"Git task: {task}")))

@app.command()
def copilot(query: str, action: Annotated[str, typer.Option("--action", "-a")] = "suggest"):
    """Get technical suggestions or command explanations from GitHub Copilot CLI."""
    from tools.copilot import copilot_suggest, copilot_explain
    if action == "suggest":
        res = copilot_suggest(query)
    else:
        res = copilot_explain(query)
    console.print(Panel(res, title=f"GitHub Copilot ({action.capitalize()})", border_style="cyan"))

@app.command()
def init():
    if os.path.exists("JARVIS.md"): console.print("[yellow]Exists.[/yellow]")
    else:
        with open("JARVIS.md", "w") as f: f.write("# JARVIS Rules")
        console.print("[green]Created.[/green]")

def show_model_status():
    p_obj = get_provider(); p_name = get_env_with_config("provider") or "ollama"
    console.print(Panel(f"Brain: {p_name.upper()}\nModel: {p_obj.model}", title="Status", border_style="magenta"))

if __name__ == "__main__": app()
