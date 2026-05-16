import typer
from core.brain import think, get_provider
from core.agent import debug_loop, troubleshoot_loop
from voice.voice import run_voice
from watcher.monitor import start_monitor
from core.config import setup_wizard, get_env_with_config, CONFIG_FILE, load_config
import os
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
    "/troubleshoot", "/free", "/model", "/help", "/exit"
]

def display_welcome():
    welcome_text = """
    # JARVIS v1.0
    The Senior Software Engineering Assistant
    
    *Type [bold cyan]/[/bold cyan] to see available commands or [bold yellow]Ctrl+C[/bold yellow] twice to exit.*
    """
    console.print(Panel(Markdown(welcome_text), style="bold blue", border_style="cyan"))

def get_main_menu_table():
    table = Table(show_header=False, box=None)
    table.add_column("Command", style="cyan", justify="right")
    table.add_column("Description", style="white")
    
    table.add_row("/chat", "Ask technical questions or get code explanations")
    table.add_row("/fix", "Launch autonomous agent to research and repair bugs")
    table.add_row("/analyze", "Run project-wide health, complexity, and hotspot analytics")
    table.add_row("/analyze-file", "Perform deep security and quality audit on a single file")
    table.add_row("/locate", "Search for any file or directory across your entire computer")
    table.add_row("/troubleshoot", "Execute a failing command and auto-fix its errors (Warp Mode)")
    table.add_row("/undo", "Instantly rollback the last file modification made by JARVIS")
    table.add_row("/dashboard", "Open the live multi-window system status TUI")
    table.add_row("/memory", "Search, view stats, or clear JARVIS's long-term vector brain")
    table.add_row("/personality", "Switch between Professional, Sarcastic, Concise, or Mentor personas")
    table.add_row("/models", "Browse and switch between LLM providers (NVIDIA, OpenAI, etc.)")
    table.add_row("/model", "Show active model status, provider info, and current quota")
    table.add_row("/focus", "Set a specific directory or file as the primary work context")
    table.add_row("/help", "Open robust system documentation and command guide")
    table.add_row("/exit", "Securely shutdown and exit the JARVIS interface")
    
    return Panel(table, title="[bold white]Slash Commands & Capabilities[/bold white]", border_style="blue", expand=False)

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
            last_ctrl_c = 0 # Reset on successful input
            
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
            if now - last_ctrl_c < 2: # 2 seconds threshold
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
    
    # Quota logic (simplified placeholder as most APIs don't expose this via simple GET)
    quota = "N/A"
    if p_name.lower() in ["gemini"]:
        quota = "1,500 requests/day (Free Tier)"
    elif p_name.lower() in ["ollama", "lm_studio", "llama_cpp"]:
        quota = "N/A (Local)"
    
    status_info = f"""
    [bold]Active Provider:[/bold] {p_name.upper()}
    [bold]Active Model:[/bold] {model_name}
    [bold]Current Quota:[/bold] {quota}
    """
    console.print(Panel(status_info, title="Model Indicator", border_style="magenta"))

def config_menu():
    """Manage global JARVIS settings and API keys."""
    while True:
        config_data = load_config()
        table = Table(title="System Configuration", show_header=True, header_style="bold magenta")
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="white")
        table.add_column("Description", style="dim")
        
        descriptions = {
            "provider": "The current LLM service (Ollama, Gemini, OpenAI, etc.)",
            "jarvis_model": "The specific AI model name being used",
            "personality": "Behavioral profile (Professional, Sarcastic, etc.)",
            "active_prompt": "Persistent system role from your Prompt Library",
            "github_token": "Token used for autonomous PR and Issue management",
            "gemini_api_key": "API Key for Google Gemini services",
            "openai_api_key": "API Key for OpenAI services",
            "anthropic_api_key": "API Key for Anthropic Claude services",
            "nvidia_api_key": "API Key for NVIDIA NIM services",
            "xai_api_key": "API Key for xAI Grok services",
            "mistral_api_key": "API Key for Mistral AI services",
            "ollama_host": "Local host URL for Ollama server",
            "lm_studio_host": "Local host URL for LM Studio server",
            "llama_cpp_host": "Local host URL for Llama.cpp server"
        }
        
        for k, v in config_data.items():
            val = v if "api_key" not in k or not v else "****" + v[-4:]
            desc = descriptions.get(k, "System setting")
            table.add_row(k, str(val), desc)
        
        console.print(table)
        console.print("\n[1] Launch Setup Wizard | [b] Back")
        choice = Prompt.ask("Choice", choices=["1", "b"], default="b")
        if choice == "1":
            setup_wizard()
        else:
            break

def robust_help():
    """Detailed documentation for all JARVIS systems."""
    help_md = """
    # JARVIS System Documentation
    
    ### 💬 /chat [query]
    Connects to your active LLM to provide architectural advice, code explanations, or general technical help.
    
    ### 🔧 /fix [issue]
    The heart of JARVIS's agentic power. It will:
    1. **Research:** Use `SEARCH` and `READ` tools to understand your project.
    2. **Strategy:** Formulate a step-by-step plan.
    3. **Execute:** Apply changes with the `EDIT` tool.
    4. **Verify:** Ensure the fix works and suggest further improvements.

    ### 🧪 /analyze-file [path]
    A specialized audit tool. JARVIS will scan the provided file for security vulnerabilities (like SQL injection or hardcoded keys), performance bottlenecks, and style inconsistencies.

    ### 🔍 /locate [name]
    Uses low-level system commands to find files or directories anywhere on your computer or linked volumes.

    ### 🛠 /troubleshoot [command]
    Warp-inspired Agent Mode. It executes your command, captures any failures (stderr), and automatically attempts to fix the underlying code responsible for the crash.

    ### 🧠 /memory
    JARVIS uses a FAISS vector database to store "long-term" insights from your conversations. This menu lets you query that database or clear it to reset JARVIS's memory.

    ### 🎭 /personality
    Choose the "vibe" of your assistant. Personalities influence the tone and detail level of responses.
    
    ### 📝 /prompts
    Your Prompt Library. Save complex system instructions or specialized "Engineer Personas" to use across different projects. Use `@name` in chat to trigger them.
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
    console.print(Panel(f"Provider: [bold cyan]{current_p.upper()}[/bold cyan]\nModel: [bold yellow]{current_m}[/bold yellow]", title="LLM Selection"))
    console.print("\n[1] Ollama | [2] OpenAI | [3] Gemini | [4] Claude | [5] Grok | [6] Mistral | [7] NVIDIA | [8] LM Studio | [9] Llama.cpp | [b] Back")
    choice = Prompt.ask("Select provider", choices=["1", "2", "3", "4", "5", "6", "7", "8", "9", "b"], default="b")
    p_mapping = {"1": "ollama", "2": "openai", "3": "gemini", "4": "claude", "5": "grok", "6": "mistral", "7": "nvidia", "8": "lm_studio", "9": "llama_cpp"}
    if choice in p_mapping:
        provider = p_mapping[choice]
        config["provider"] = provider
        models = {"ollama": ["llama3", "mistral", "codellama", "phi3"], "openai": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"], "gemini": ["gemini-1.5-pro", "gemini-1.5-flash"], "claude": ["claude-3-5-sonnet-20240620", "claude-3-opus-20240229"], "grok": ["grok-beta"], "mistral": ["mistral-large-latest", "open-mixtral-8x22b"], "nvidia": ["nvidia/llama-3.1-405b-instruct", "nvidia/nemotron-4-340b-instruct"], "lm_studio": ["local-model"], "llama_cpp": ["local-model"]}
        console.print(f"\n[bold]Common Models for {provider.upper()}:[/bold]")
        for m in models[provider]: console.print(f"- {m}")
        new_model = Prompt.ask("Enter model name", default=models[provider][0])
        config["jarvis_model"] = new_model
        if provider == "gemini": config["gemini_model"] = new_model
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
def init():
    """Initialize project."""
    if os.path.exists("JARVIS.md"): console.print("[yellow]Already exists.[/yellow]")
    else:
        with open("JARVIS.md", "w") as f: f.write("# JARVIS Project Instructions\n\n- Define rules here.")
        console.print("[green]Created JARVIS.md[/green]")

if __name__ == "__main__": app()
