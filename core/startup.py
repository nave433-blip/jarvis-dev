from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
import core.services as svc
from core.config import load_config, save_config
from tools.network import scan_network_for_ollama

console = Console()
DEFAULT_PROVIDERS = ["ollama", "openai", "gemini", "anthropic", "mistral", "deepseek", "qwen", "kimi", "perplexity", "granite", "nemotron", "groq", "together"]

def _interactive_connect(provider: str) -> Dict[str, Any]:
    provider = provider.lower()
    result = {"provider": provider, "connected": False, "message": ""}
    FREE_GUIDE = {
        "groq": "Get a free API key at https://groq.com",
        "together": "Get a free API key at https://together.ai"
    }
    try:
        if provider == "ollama":
            host = Prompt.ask("Enter Ollama host", default="http://localhost:11434")
            result.update({"connected": True, "message": "Ollama host updated"})
            return result
        
        if provider in FREE_GUIDE:
            console.print(Panel(FREE_GUIDE[provider], title=f"{provider.upper()} Guide"))
            
        key = Prompt.ask(f"Enter {provider} key", password=True)
        svc.set_api_key(provider, key)
        result.update({"connected": True, "message": "Key saved"})
        return result
    except Exception as e:
        return {"connected": False, "message": str(e)}

def check_provider(provider: str, auto: bool = False) -> Dict[str, Any]:
    status = {"provider": provider, "ok": False, "validated": False, "action_taken": None, "message": None}
    try:
        v = svc.validate_provider_connection(provider)
        status["ok"] = v.get("ok", False)
        status["validated"] = v.get("ok", False)
        status["message"] = v.get("error") or "Connected" if v.get("ok") else "Missing credentials"
        
        if not status["ok"] and not auto:
            if Confirm.ask(f"⚠️ Provider '{provider.upper()}' is not ready. Configure it now?"):
                _interactive_connect(provider)
                status["ok"] = True
    except Exception as e:
        status["ok"] = False
        status["message"] = str(e)
    return status

def startup_check_and_login(auto: bool = False, providers: Optional[List[str]] = None, start_maintenance: bool = True) -> Dict[str, Any]:
    # Auto-scan network
    console.print("[dim]Scanning network for Ollama instances...[/dim]")
    found_hosts = scan_network_for_ollama()
    if found_hosts:
        cfg = load_config()
        cfg["ollama_hosts"] = list(set(cfg.get("ollama_hosts", []) + found_hosts))
        save_config(cfg)
        console.print(f"[green]✅ Discovered: {', '.join(found_hosts)}[/green]")
        
    report = {"auto": bool(auto), "results": [], "maintenance_started": False}
    console.print(Panel("Intelligence core online.", title="Status", border_style="green"))
    return report
