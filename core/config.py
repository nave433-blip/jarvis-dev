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
    "model_mode": "manual"
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
    """Attempt to auto-detect a local Ollama instance."""
    hosts = ["http://localhost:11434", "http://127.0.0.1:11434"]
    for host in hosts:
        try:
            r = requests.get(f"{host}/api/tags", timeout=1)
            if r.status_code == 200:
                return host
        except:
            continue
    return None

def setup_wizard():
    console.print("[bold cyan]Welcome to JARVIS Setup Wizard[/bold cyan]\n")
    
    config = load_config()
    
    provider = Prompt.ask(
        "Select your default LLM provider",
        choices=["ollama", "gemini", "claude", "grok", "openai"],
        default=config["provider"]
    )
    config["provider"] = provider

    if provider == "ollama":
        auto_host = detect_ollama()
        if auto_host:
            console.print(f"[green]Detected local Ollama instance at {auto_host}[/green]")
            config["ollama_host"] = auto_host
        else:
            config["ollama_host"] = Prompt.ask("Ollama Host URL", default=config["ollama_host"])
        config["jarvis_model"] = Prompt.ask("Ollama Model Name", default=config["jarvis_model"])
    
    if Confirm.ask("Would you like to configure API keys now?"):
        config["gemini_api_key"] = Prompt.ask("Gemini API Key", default=config["gemini_api_key"], password=True)
        config["anthropic_api_key"] = Prompt.ask("Anthropic API Key", default=config["anthropic_api_key"], password=True)
        config["openai_api_key"] = Prompt.ask("OpenAI API Key", default=config["openai_api_key"], password=True)
        config["mistral_api_key"] = Prompt.ask("Mistral API Key", default=config["mistral_api_key"], password=True)
        config["nvidia_api_key"] = Prompt.ask("NVIDIA NIM API Key", default=config["nvidia_api_key"], password=True)
        config["xai_api_key"] = Prompt.ask("XAI (Grok) API Key", default=config["xai_api_key"], password=True)
        config["github_token"] = Prompt.ask("GitHub Personal Access Token", default=config["github_token"], password=True)

    save_config(config)
    console.print("\n[green]Configuration saved to ~/.jarvis/config.json[/green]")

def get_env_with_config(key):
    """Get value from environment variable or fallback to config file."""
    config = load_config()
    env_val = os.getenv(key.upper())
    if env_val:
        return env_val
    
    config_key = key.lower()
    return config.get(config_key, "")
