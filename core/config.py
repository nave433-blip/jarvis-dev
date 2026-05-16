import json
import os
import requests
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()

CONFIG_DIR = Path.home() / ".jarvis"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "provider": "ollama",
    "ollama_host": "http://localhost:11434",
    "lm_studio_host": "http://localhost:1234",
    "llama_cpp_host": "http://localhost:8080",
    "gpt4all_host": "http://localhost:4891",
    "jarvis_model": "llama3",
    "gemini_api_key": "",
    "anthropic_api_key": "",
    "xai_api_key": "",
    "openai_api_key": "",
    "mistral_api_key": "",
    "nvidia_api_key": "",
    "dropbox_token": "",
    "gdrive_token": "",
    "github_token": "",
    "personality": "professional",
    "active_prompt": "default",
    "model_mode": "manual",
    "self_repair": False
}

def load_config():
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, "r") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    except Exception:
        return DEFAULT_CONFIG

def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def detect_ollama():
    hosts = ["http://localhost:11434", "http://127.0.0.1:11434"]
    for host in hosts:
        try:
            r = requests.get(f"{host}/api/tags", timeout=1)
            if r.status_code == 200: return host
        except: continue
    return None

def smart_input(label, default_val, auto_detect_func=None):
    """Smarter input that offers auto-detection if the user is unsure."""
    if Confirm.ask(f"Do you have the specific {label} details (e.g. URL or Key)?"):
        return Prompt.ask(f"Enter {label}", default=default_val)
    
    if auto_detect_func:
        console.print(f"[dim]Attempting to auto-configure {label}...[/dim]")
        detected = auto_detect_func()
        if detected:
            console.print(f"[green]✅ Auto-detected: {detected}[/green]")
            return detected
            
    console.print(f"[yellow]⚠️ No specific {label} details provided. Using default/empty.[/yellow]")
    return default_val

def setup_wizard():
    console.print("[bold cyan]Welcome to JARVIS Setup Wizard[/bold cyan]\n")
    config = load_config()
    
    config["provider"] = Prompt.ask(
        "Select your primary LLM provider",
        choices=["ollama", "gemini", "claude", "openai", "grok", "mistral", "nvidia"],
        default=config["provider"]
    )

    if config["provider"] == "ollama":
        config["ollama_host"] = smart_input("Ollama Host URL", config["ollama_host"], auto_detect_func=detect_ollama)
        config["jarvis_model"] = Prompt.ask("Ollama Model Name", default=config["jarvis_model"])
    
    if Confirm.ask("Would you like to configure Cloud API Keys now?"):
        for key in ["gemini_api_key", "openai_api_key", "anthropic_api_key", "xai_api_key", "mistral_api_key", "nvidia_api_key"]:
            name = key.replace("_", " ").title()
            if Confirm.ask(f"Configure {name}?"):
                config[key] = Prompt.ask(f"Enter {name}", default=config.get(key, ""), password=True)

    if Confirm.ask("Configure external integrations (GitHub, Cloud Storage)?"):
        config["github_token"] = Prompt.ask("GitHub Personal Access Token", default=config.get("github_token", ""), password=True)
        config["dropbox_token"] = Prompt.ask("Dropbox API Token", default=config.get("dropbox_token", ""), password=True)
        config["gdrive_token"] = Prompt.ask("Google Drive API Token", default=config.get("gdrive_token", ""), password=True)

    config["self_repair"] = Confirm.ask("Enable autonomous self-repair?", default=config.get("self_repair", False))

    save_config(config)
    console.print("\n[green]Configuration saved successfully.[/green]")

def get_env_with_config(key):
    config = load_config()
    env_val = os.getenv(key.upper())
    if env_val: return env_val
    return config.get(key.lower(), "")
