import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from core.config import load_config, save_config, setup_wizard

console = Console()

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
            "model_mode": "Auto-selection logic: manual, auto-offline, auto-online, or auto-mixed",
            "self_repair": "Autonomous system healing: Enable/disable automatic repair on errors",
            "dropbox_token": "Token for Dropbox cloud storage access",
            "gdrive_token": "Token for Google Drive cloud storage access"
        }
        
        for k, v in config_data.items():
            val = v if "api_key" not in k and "token" not in k or not v else "****" + v[-4:]
            desc = descriptions.get(k, "General system parameter")
            table.add_row(k, str(val), desc)
        
        console.print(table)
        console.print("\n[w] Launch Setup Wizard | [e] Edit Single Key | [r] Toggle Self-Repair | [b] Back")
        choice = Prompt.ask("Choice", choices=["w", "e", "r", "b"], default="b")
        if choice == "w":
            setup_wizard()
        elif choice == "r":
            current = config_data.get("self_repair", False)
            config_data["self_repair"] = not current
            save_config(config_data)
            status = "ENABLED" if not current else "DISABLED"
            console.print(f"[green]Self-Repair {status}[/green]")
        elif choice == "e":
            key = Prompt.ask("Enter the key name to edit")
            if key in config_data:
                val = Prompt.ask(f"Enter new value for {key}", default=str(config_data[key]))
                config_data[key] = val
                save_config(config_data)
                console.print(f"[green]Updated {key}[/green]")
            else:
                console.print(f"[red]Key '{key}' not found.[/red]")
        else:
            break

def network_menu():
    from tools.network import scan_network, scan_ports
    while True:
        console.print(Panel("Network Tools:\n[1] Scan Local Subnet (Fing-style) | [2] Scan Ports on IP | [b] Back", title="Networking"))
        choice = Prompt.ask("Choice", choices=["1", "2", "b"], default="b")
        if choice == "1":
            console.print(scan_network())
        elif choice == "2":
            ip = Prompt.ask("Target IP")
            ports = scan_ports(ip)
            console.print(f"[green]Open Ports on {ip}:[/green] {ports}")
        else: break

def server_menu():
    from tools.server import list_listening_ports, get_process_stats, kill_process
    while True:
        stats = get_process_stats()
        status = f"CPU: {stats['cpu_usage']}% | RAM: {stats['memory_usage']}% | PIDs: {stats['process_count']}"
        console.print(Panel(status, title="System Health"))
        console.print("\n[1] List Listening Ports | [2] Kill Process | [b] Back")
        choice = Prompt.ask("Choice", choices=["1", "2", "b"], default="b")
        if choice == "1":
            console.print(list_listening_ports())
        elif choice == "2":
            pid = int(Prompt.ask("Enter PID to terminate"))
            console.print(kill_process(pid))
        else: break

def memory_menu():
    from memory.vector import get_stats, search, clear
    from rich.prompt import Confirm
    while True:
        stats = get_stats()
        console.print(Panel(f"Stored Memories: [bold cyan]{stats['count']}[/bold cyan]", title="Memory Management"))
        console.print("\n[1] Search | [2] Clear All | [b] Back")
        choice = Prompt.ask("Choice", choices=["1", "2", "b"], default="b")
        if choice == "1":
            q = Prompt.ask("Search query")
            results = search(q)
            if results: console.print(Panel("\n".join([f"- {r}" for r in results]), title=f"Search: {q}"))
            else: console.print("[yellow]No relevant memories found.[/yellow]")
            input("\nPress Enter to continue...")
        elif choice == "2":
            if Confirm.ask("Are you sure you want to wipe all JARVIS memories?"):
                console.print(f"[green]{clear()}[/green]")
        else: break

def personality_menu():
    config = load_config()
    current = config.get("personality", "professional")
    console.print(Panel(f"Current Personality: [bold cyan]{current.capitalize()}[/bold cyan]", title="Personality Settings"))
    console.print("\n[1] Professional | [2] Sarcastic (Grok) | [3] Concise | [4] Mentor | [5] Nave AI (Beta) | [b] Back")
    choice = Prompt.ask("Select personality", choices=["1", "2", "3", "4", "5", "b"], default="b")
    mapping = {"1": "professional", "2": "sarcastic", "3": "concise", "4": "mentor", "5": "nave_ai"}
    if choice in mapping:
        config["personality"] = mapping[choice]
        save_config(config)
        console.print(f"[green]Personality updated to {mapping[choice].capitalize()}[/green]")

def models_menu():
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

def prompts_menu():
    from core.prompts import load_prompts, save_prompt, delete_prompt, list_prompts
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

def ssh_command(args):
    from tools.ssh import run_remote
    if not args:
        host = Prompt.ask("Host"); user = Prompt.ask("Username"); cmd = Prompt.ask("Command")
    else:
        parts = args.split(" ", 2)
        if len(parts) < 3:
            console.print("[red]Usage: /ssh <host> <user> <command>[/red]")
            return
        host, user, cmd = parts
    
    console.print(f"[bold cyan]Connecting to {host} as {user}...[/bold cyan]")
    res = run_remote(host, user, cmd)
    console.print(Panel(str(res), title=f"SSH Result: {host}"))

def robust_help():
    from rich.markdown import Markdown
    from core.ui import get_main_menu_table
    help_md = """
    # JARVIS Engineering Suite Documentation
    
    ### 💬 /chat [query]
    Connects to the active model to provide advice, code explanations, or project brainstorming.
    
    ### 🔧 /fix [issue]
    Autonomous agent mode. Research, strategy, execution, and verification—all in one loop.
    
    ### 🛠 /troubleshoot [command]
    Warp-inspired Agent Mode. Runs a command, captures error output, and enters a debug loop to fix the code causing the crash.

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
    from rich.align import Align
    console.print(Align.center(get_main_menu_table()))

def cloud_menu():
    from cli import cloud
    console.print(Panel("Select Cloud Platform:\n[1] Google Drive | [2] Dropbox | [3] iCloud Drive | [b] Back", title="Cloud Integration"))
    choice = Prompt.ask("Choice", choices=["1", "2", "3", "b"], default="b")
    if choice == "1": cloud("gdrive")
    elif choice == "2": cloud("dropbox")
    elif choice == "3": cloud("icloud")
