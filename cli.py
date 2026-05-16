import os
import sys

# 1. Self-Repairing Dependency Check
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core.deps import ensure_all
ensure_all()

# 2. Auto-Update Check
from core.update import auto_update_check, CURRENT_VERSION
auto_update_check()

import typer
from core.brain import think, get_provider
from core.agent import debug_loop, troubleshoot_loop
from voice.voice import run_voice
from watcher.monitor import start_monitor
from core.config import setup_wizard, get_env_with_config, CONFIG_FILE, load_config
import time
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
    "/chat", "/fix", "/voice", "/watch", "/config", "/init", "/analyze", "/analyze-file",
    "/locate", "/undo", "/dashboard", "/memory", "/personality", "/models", "/focus", 
    "/cloud", "/troubleshoot", "/free", "/model", "/help", "/exit"
]

def display_welcome():
    # Load icon if possible (ASCII art or just a box)
    logo = """
    [bold white]      _______[/bold white]
    [bold white]     |__   __|[/bold white]
    [bold white]        | |[/bold white]
    [bold white]        | |[/bold white]
    [bold white]      __| |[/bold white]
    [bold white]     |____/ [/bold white]
    """
    
    splash_text = f"""
    [bold cyan]JARVIS[/bold cyan] [white]v{CURRENT_VERSION}[/white]
    [dim]The Advanced AI Engineering Suite[/dim]
    
    [bold white]Created by Nave433 (Evan Shipley)[/bold white]
    
    *Type [bold cyan]/[/bold cyan] to see commands | [bold yellow]Ctrl+C[/bold yellow] twice to exit*
    """
    
    console.print(Align.center(Panel(
        Markdown(f"# JARVIS\nCreated by **Nave433 (Evan Shipley)**\n\nVersion: `{CURRENT_VERSION}`"),
        style="bold blue",
        border_style="cyan",
        subtitle="Initializing Systems...",
        expand=False
    )))

def get_main_menu_table():
    table = Table(show_header=False, box=None)
    table.add_column("Command", style="cyan", justify="right")
    table.add_column("Description", style="white")
    
    table.add_row("/chat", "Consult JARVIS for technical advice or code explanation")
    table.add_row("/fix", "Autonomous research & repair loop for project bugs")
    table.add_row("/analyze", "Deep health audit: lines, complexity, and file hotspots")
    table.add_row("/analyze-file", "Focused security and performance audit on a single file")
    table.add_row("/locate", "Global system search for files and directories")
    table.add_row("/troubleshoot", "Warp-style Agent Mode: Run command and auto-fix errors")
    table.add_row("/undo", "Safety rollback: Revert the last file change made by JARVIS")
    table.add_row("/dashboard", "Launch live multi-window system monitoring interface")
    table.add_row("/memory", "Search or manage the persistent vector knowledge base")
    table.add_row("/personality", "Switch between Professional, Sarcastic, Concise, or Mentor vibes")
    table.add_row("/models", "Intelligent provider switcher (Ollama, NVIDIA, OpenAI, etc.)")
    table.add_row("/model", "Detailed status of active model, provider, and current quota")
    table.add_row("/cloud", "Bridge to Google Drive, Dropbox, and iCloud storage")
    table.add_row("/focus", "Set a specific path as the primary work context for the agent")
    table.add_row("/help", "Access detailed system documentation and role guide")
    table.add_row("/exit", "Secure shutdown of all background threads and exit")
    
    return Panel(table, title="[bold white]System Commands[/bold white]", border_style="blue", expand=False)

@app.command()
def menu():
    """Launch the interactive Gemini-style slash command menu."""
    display_welcome()
    
    completer = WordCompleter(COMMANDS, ignore_case=True)
    session = PromptSession(completer=completer)
    
    style = Style.from_dict({
        'prompt': 'ansicyan bold',
    })

    last_ctrl_c = 0

    while True:
        try:
            text = session.prompt('JARVIS > ', style=style).strip()
            last_ctrl_c = 0 # Reset
            
            if not text: continue
            
            if not text.startswith("/"):
                chat(text)
                continue

            parts = text.split(" ", 2)
            cmd = parts[0].lower()
            
            prompt_name = None
            args = ""
            
            if len(parts) > 1:
                if parts[1].startswith("@"):
                    prompt_name = parts[1][1:]
                    args = parts[2] if len(parts) > 2 else ""
                else:
                    args = " ".join(parts[1:])

            if cmd == "/chat":
                chat(args or Prompt.ask("Question"), prompt=prompt_name)
            elif cmd == "/fix":
                fix(args or Prompt.ask("Issue to fix"), prompt=prompt_name)
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
            elif cmd == "/analyze-file":
                analyze_file(args or Prompt.ask("Path to file"), prompt=prompt_name)
            elif cmd == "/locate":
                locate(args or Prompt.ask("Filename to search for"))
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
            elif cmd == "/model":
                show_model_status()
            elif cmd == "/cloud":
                cloud_menu()
            elif cmd == "/focus":
                focus(args or Prompt.ask("Path to focus on"))
            elif cmd in ["/troubleshoot", "/t"]:
                troubleshoot(args or Prompt.ask("Failing command"), prompt=prompt_name)
            elif cmd == "/free":
                free_keys()
            elif cmd in ["/help", "/h"]:
                robust_help()
                console.print(Align.center(get_main_menu_table()))
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
            continue
        except EOFError:
            break

def show_model_status():
    provider_obj = get_provider()
    p_name = get_env_with_config("provider") or "ollama"
    model_name = provider_obj.model
    
    quota = "N/A (Unlimited Local)"
    if p_name.lower() in ["gemini"]:
        quota = "1,500 requests/day (Google AI Studio Free Tier)"
    elif p_name.lower() in ["openai", "claude", "mistral", "nvidia", "grok"]:
        quota = "Managed by Provider Billing/Tokens"
    
    status_info = f"""
    [bold]Active Provider:[/bold] {p_name.upper()}
    [bold]Active Model:[/bold] {model_name}
    [bold]Current Quota:[/bold] {quota}
    
    [dim]Tip: Use '/models' to switch providers or '/free' to see free tier options.[/dim]
    """
    console.print(Panel(status_info, title="[bold magenta]Active Model Indicator[/bold magenta]", border_style="magenta"))

def config_menu():
    """Manage global JARVIS settings, identities, and API keys."""
    while True:
        config_data = load_config()
        table = Table(title="Global System Configuration", show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")
        table.add_column("Functional Description", style="dim")
        
        descriptions = {
            "provider": "Primary LLM engine (Ollama, Gemini, OpenAI, Claude, Grok, Mistral, NVIDIA)",
            "jarvis_model": "The specific AI model version (e.g., llama3, gpt-4o, claude-3-5-sonnet)",
            "personality": "Tone and detail level of responses (Professional, Sarcastic, Concise, Mentor)",
            "active_prompt": "Persistent system instructions from your Prompt Library",
            "github_token": "Allows JARVIS to autonomously manage PRs, Issues, and repo data",
            "gemini_api_key": "Token for Google Gemini (recommended for high-quality free tier)",
            "openai_api_key": "Token for OpenAI GPT-4o and GPT-3.5 services",
            "anthropic_api_key": "Token for Claude 3.5 Sonnet and Opus services",
            "nvidia_api_key": "Token for NVIDIA NIM GPU-accelerated model hosting",
            "xai_api_key": "Token for xAI Grok-Beta services",
            "mistral_api_key": "Token for Mistral Large and Pixtral services",
            "ollama_host": "Host URL for your local Ollama server (Default: localhost:11434)",
            "lm_studio_host": "Host URL for LM Studio local API (Default: localhost:1234)",
            "llama_cpp_host": "Host URL for Llama.cpp local server (Default: localhost:8080)",
            "gpt4all_host": "Host URL for GPT4All local API (Default: localhost:4891)",
            "model_mode": "Auto-selection logic: manual, auto-offline, auto-online, or auto-mixed"
        }
        
        for k, v in config_data.items():
            val = v if "api_key" not in k or not v else "****" + v[-4:]
            desc = descriptions.get(k, "General system parameter")
            table.add_row(k, str(val), desc)
        
        console.print(table)
        console.print("\n[1] Launch Setup Wizard | [b] Back")
        choice = Prompt.ask("Choice", choices=["1", "b"], default="b")
        if choice == "1":
            setup_wizard()
        else:
            break

def robust_help():
    """Exhaustive guide for all JARVIS engineering systems."""
    help_md = """
    # JARVIS Engineering Suite Documentation
    
    ### 💬 /chat [query]
    Connects to the active model to provide advice, code explanations, or project brainstorming.
    
    ### 🔧 /fix [issue]
    Autonomous agent mode. JARVIS will research the issue, create a strategy, apply code changes, and verify the result.
    
    ### 🛠 /troubleshoot [command]
    Warp-style Agent Mode. Runs a command, captures error output, and enters a debug loop to fix the code causing the crash.

    ### 🧪 /analyze-file [path]
    Deep security and quality audit of a single file. Useful for pre-PR checks and identifying vulnerabilities.

    ### 🧠 /memory
    Manages the FAISS vector database. This allows JARVIS to have a 'long-term' memory of your past projects and conversations.

    ### 🎭 /personality
    Sets the behavioral persona.
    - **Professional:** Direct and formal.
    - **Sarcastic:** Grok-style wit and humor.
    - **Mentor:** Patient and detailed educational responses.
    - **Concise:** Minimalist answers only.

    ### 📝 /prompts
    Manage your custom role library. Add @name in your chat to apply a specific persona on the fly.
    """
    console.print(Panel(Markdown(help_md), title="[bold green]Robust Documentation[/bold green]", border_style="green"))

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
def chat(q: str, model: Optional[str] = typer.Option(None, "--model", "-m"), prompt: Optional[str] = typer.Option(None, "--prompt", "-p")):
    """Chat with JARVIS."""
    provider = get_env_with_config("provider") or "ollama"
    console.print(Panel(f"JARVIS [bold blue]({provider})[/bold blue] [dim]prompt: {prompt or 'default'}[/dim]", border_style="blue"))
    response = think("", q, model=model, prompt_name=prompt)
    console.print(Markdown(response))

@app.command()
def fix(issue: str, model: Optional[str] = typer.Option(None, "--model", "-m"), prompt: Optional[str] = typer.Option(None, "--prompt", "-p")):
    """Autonomous debug loop."""
    debug_loop(issue, model=model, prompt=prompt)

@app.command()
def analyze_file(path: str, model: Optional[str] = typer.Option(None, "--model", "-m"), prompt: Optional[str] = typer.Option(None, "--prompt", "-p")):
    """Deeply analyze a single file."""
    if not os.path.exists(path):
        console.print(f"[red]Error: File not found:[/red] {path}")
        return
    with open(path, 'r') as f:
        content = f.read()
    console.print(f"[bold blue]Analyzing file:[/bold blue] {path}...")
    response = think(f"File Path: {path}\nFile Content:\n{content}", "Analyze this file for bugs, security issues, and performance improvements.", model=model, prompt_name=prompt)
    console.print(Markdown(response))

@app.command()
def locate(name: str, root: str = "/"):
    """Search for a file/directory across the computer."""
    from tools.search import system_find
    console.print(f"[bold blue]Searching for '{name}' starting from {root}...[/bold blue]")
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
    db = Dashboard()
    db.run()

@app.command()
def focus(path: str):
    """Set working context."""
    if os.path.exists(path):
        console.print(Panel(f"[green]Focus successfully set to:[/green]\n{os.path.abspath(path)}", border_style="green"))
    else:
        console.print(f"[red]Error: Path does not exist:[/red] {path}")

@app.command()
def troubleshoot(command: str, model: Optional[str] = typer.Option(None, "--model", "-m"), prompt: Optional[str] = typer.Option(None, "--prompt", "-p")):
    """Autonomous troubleshooting."""
    troubleshoot_loop(command, model=model, prompt=prompt)

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
    """Project health analytics."""
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
        from rich.prompt import Confirm
        if Confirm.ask("Are you sure you want to wipe all JARVIS memories?"):
            console.print(f"[green]{clear()}[/green]")

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
        elif choice == "2": memory(action="clear")
        else: break

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
    else: console.print("[red]Invalid type.[/red]")

def models_menu():
    from core.config import load_config, save_config
    config = load_config()
    current_p = config.get("provider", "ollama")
    current_m = config.get("jarvis_model", "llama3")
    current_mode = config.get("model_mode", "manual")
    
    console.print(Panel(
        f"Mode: [bold green]{current_mode.upper()}[/bold green]\n"
        f"Provider: [bold cyan]{current_p.upper()}[/bold cyan]\n"
        f"Model: [bold yellow]{current_m}[/bold yellow]", 
        title="LLM Model & Mode Selection"
    ))
    
    console.print("\n[bold]Select Operation Mode:[/bold]")
    console.print("[a] Auto-Offline | [s] Auto-Online | [x] Auto-Mixed | [m] Manual Select")
    console.print("\n[bold]Manual Providers:[/bold]")
    console.print("[1] Ollama | [2] OpenAI | [3] Gemini | [4] Claude | [5] Grok | [6] Mistral | [7] NVIDIA")
    console.print("[8] LM Studio | [9] Llama.cpp | [g] GPT4All | [b] Back")
    
    choice = Prompt.ask("Select choice", choices=["a", "s", "x", "m", "1", "2", "3", "4", "5", "6", "7", "8", "9", "g", "b"], default="b")
    
    if choice == "a":
        config["model_mode"] = "auto-offline"
        save_config(config)
        console.print("[green]Switched to Auto-Offline mode (Local only).[/green]")
        return
    elif choice == "s":
        config["model_mode"] = "auto-online"
        save_config(config)
        console.print("[green]Switched to Auto-Online mode (Prioritize cloud).[/green]")
        return
    elif choice == "x":
        config["model_mode"] = "auto-mixed"
        save_config(config)
        console.print("[green]Switched to Auto-Mixed mode (Dynamic local/cloud).[/green]")
        return
    elif choice == "m":
        config["model_mode"] = "manual"
        save_config(config)
        console.print("[green]Switched to Manual mode.[/green]")
        return

    p_mapping = {"1": "ollama", "2": "openai", "3": "gemini", "4": "claude", "5": "grok", "6": "mistral", "7": "nvidia", "8": "lm_studio", "9": "llama_cpp", "g": "gpt4all"}
    if choice in p_mapping:
        config["model_mode"] = "manual"
        provider = p_mapping[choice]
        config["provider"] = provider
        models = {"ollama": ["llama3", "mistral", "codellama", "phi3"], "openai": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"], "gemini": ["gemini-1.5-pro", "gemini-1.5-flash"], "claude": ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229"], "grok": ["grok-beta"], "mistral": ["mistral-large-latest", "open-mixtral-8x22b"], "nvidia": ["nvidia/llama-3.1-405b-instruct", "nvidia/nemotron-4-340b-instruct"], "lm_studio": ["local-model"], "llama_cpp": ["local-model"], "gpt4all": ["Mistral-7B-Instruct", "Llama-3-8B-Instruct"]}
        console.print(f"\n[bold]Common Models for {provider.upper()}:[/bold]")
        for m in models[provider]: console.print(f"- {m}")
        new_model = Prompt.ask("Enter model name", default=models[provider][0])
        config["jarvis_model"] = new_model
        if provider == "gemini": config["gemini_model"] = new_model
        save_config(config)
        console.print(f"[green]Manual Setup: Switched to {provider.upper()} ({new_model})[/green]")

@app.command()
def models(provider: str, model: str):
    """Directly set LLM."""
    from core.config import load_config, save_config
    config = load_config()
    config["provider"] = provider.lower()
    config["jarvis_model"] = model
    save_config(config)
    console.print(f"[green]Set to {provider.upper()} ({model})[/green]")

def prompts_menu():
    from core.prompts import load_prompts, save_prompt, delete_prompt, list_prompts
    from core.config import load_config, save_config
    while True:
        console.print(list_prompts())
        config = load_config()
        current = config.get("active_prompt", "default")
        console.print(f"Active Prompt: [bold cyan]{current}[/bold cyan]")
        console.print("\n[1] Select Active | [2] Add New | [3] Delete | [b] Back")
        choice = Prompt.ask("Choice", choices=["1", "2", "3", "b"], default="b")
        if choice == "1":
            name = Prompt.ask("Prompt name")
            prompts = load_prompts()
            if name in prompts:
                config["active_prompt"] = name
                save_config(config)
                console.print(f"[green]Active set to '{name}'[/green]")
            else: console.print(f"[red]'{name}' not found.[/red]")
        elif choice == "2":
            name = Prompt.ask("Name"); text = Prompt.ask("Text")
            console.print(f"[green]{save_prompt(name, text)}[/green]")
        elif choice == "3":
            name = Prompt.ask("Name"); res = delete_prompt(name)
            if "Error" in res: console.print(f"[red]{res}[/red]")
            else: console.print(f"[green]{res}[/green]")
        else: break

@app.command()
def prompts(action: str = "list", name: str = "", text: str = ""):
    """Manage prompts."""
    from core.prompts import list_prompts, save_prompt, delete_prompt, load_prompts
    from core.config import load_config, save_config
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
    info = """
    # 🎁 Get Started for Free
    1. **Gemini Flash:** [https://aistudio.google.com/](https://aistudio.google.com/)
    2. **Mistral:** [https://console.mistral.ai/](https://console.mistral.ai/)
    3. **NVIDIA:** [https://build.nvidia.com/](https://build.nvidia.com/)
    4. **Ollama:** [https://ollama.com/](https://ollama.com/)
    """
    console.print(Panel(Markdown(info), title="Free Tier Automation"))

@app.command()
def cloud(platform: str, action: str = "list", path: str = ""):
    """Manage cloud storage."""
    from tools.cloud import list_dropbox, list_gdrive, list_icloud
    console.print(f"[bold blue]Accessing {platform.upper()}...[/bold blue]")
    if platform == "dropbox": res = list_dropbox(path)
    elif platform == "gdrive": res = list_gdrive()
    elif platform == "icloud": res = list_icloud(path)
    else: res = "Unknown platform."
    console.print(Panel(str(res), title=f"Cloud Result: {platform}"))

def cloud_menu():
    console.print(Panel("Select Cloud Platform:\n[1] Google Drive | [2] Dropbox | [3] iCloud Drive | [b] Back", title="Cloud Integration"))
    choice = Prompt.ask("Choice", choices=["1", "2", "3", "b"], default="b")
    if choice == "1": cloud("gdrive")
    elif choice == "2": cloud("dropbox")
    elif choice == "3": cloud("icloud")

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
    quota = "N/A (Unlimited Local)"
    if p_name.lower() in ["gemini"]: quota = "1,500 requests/day (Free Tier)"
    elif p_name.lower() in ["openai", "claude", "mistral", "nvidia", "grok"]: quota = "Managed by Provider"
    status_info = f"[bold]Provider:[/bold] {p_name.upper()}\n[bold]Model:[/bold] {model_name}\n[bold]Quota:[/bold] {quota}"
    console.print(Panel(status_info, title="[bold magenta]Model Indicator[/bold magenta]", border_style="magenta"))

if __name__ == "__main__": app()
