"""
Startup connector and validator for JARVIS.

- Validates configured providers at startup.
- For missing/unhealthy providers, offers interactive connect flows:
    - OpenAI / Anthropic / Deepseek / Kimi: prompt for API key
    - Ollama / nemotron / qwen / host-based: prompt for host URL
    - Gemini (Google): offer OAuth flow if google client secrets present (uses core.google_auth.GoogleAuth)
- Persists credentials with core.services helper functions or core.config.save_config
- Optionally runs silently when auto=True (non-interactive)
- Starts periodic config maintenance thread via core.config.start_periodic_config_maintenance()
"""

from typing import Optional, Dict, Any, List
import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from core import services as svc
from core.config import load_config, save_config, start_periodic_config_maintenance
from core.google_auth import GoogleAuth

console = Console()

# Which providers to check by default at startup (standardized names)
DEFAULT_PROVIDERS = [
    "ollama", "openai", "gemini", "anthropic", "mistral", "deepseek", 
    "qwen", "kimi", "perplexity", "granite", "nemotron", "groq"
]

def _interactive_connect(provider: str) -> Dict[str, Any]:
    """
    Interactive connect helper. Prompts user for key or host depending on provider.
    Returns dict with status and message.
    """
    provider = provider.lower()
    result = {"provider": provider, "connected": False, "message": ""}

    try:
        if provider == "ollama":
            host = Prompt.ask("Enter Ollama host URL", default=load_config().get("ollama_host", "http://localhost:11434"))
            if host:
                cfg = load_config()
                cfg["ollama_host"] = host
                save_config(cfg)
                v = svc.validate_provider_connection("ollama", extra={"host": host})
                if v.get("ok"):
                    result.update({"connected": True, "message": f"Ollama reachable at {host}"})
                else:
                    result.update({"connected": False, "message": f"Ollama validation: {v.get('error')}"})
            return result

        if provider in ("nemotron", "qwen", "gpt4all", "llama_cpp", "vllm", "sglang", "laguna"):
            host = Prompt.ask(f"Enter host URL for {provider}", default=load_config().get(f"{provider}_host", ""))
            if host:
                cfg = load_config()
                cfg[f"{provider}_host"] = host
                save_config(cfg)
                v = svc.validate_provider_connection(provider, extra={"host": host})
                if v.get("ok"):
                    result.update({"connected": True, "message": f"{provider} reachable at {host}"})
                else:
                    result.update({"connected": False, "message": f"{provider} validation: {v.get('error')}"})
            return result

        # Cloud API key providers
        if provider in ("openai", "anthropic", "deepseek", "kimi", "mistral", "perplexity", "granite", "groq", "replit"):
            key = Prompt.ask(f"Enter API key for {provider} (leave blank to skip)", default="", password=True)
            if key:
                svc.set_api_key(provider, key)
                v = svc.validate_provider_connection(provider, extra={"key": key})
                if v.get("ok"):
                    result.update({"connected": True, "message": f"{provider} validated"})
                else:
                    result.update({"connected": False, "message": f"Validation failed: {v.get('error')}"})
            else:
                result.update({"connected": False, "message": "No key entered"})
            return result

        if provider == "gemini":
            # Offer OAuth flow if google client secrets present
            console.print(Panel("To connect Gemini (Google), JARVIS can run the Google OAuth flow (Installed App).", title="Gemini Connect"))
            client_file = os.path.expanduser("~/.jarvis/google_client.json")
            if os.path.exists(client_file):
                if Confirm.ask("Run Google OAuth flow now to link Gemini?"):
                    creds = GoogleAuth.run_flow()
                    if creds:
                        result.update({"connected": True, "message": "Google OAuth successful"})
                    else:
                        result.update({"connected": False, "message": "OAuth flow failed or cancelled"})
                else:
                    result.update({"connected": False, "message": "User declined OAuth flow"})
            else:
                console.print("[yellow]No google_client.json found in ~/.jarvis.[/yellow]")
                key = Prompt.ask("Paste Gemini API key (if you have one), leave blank to skip", default="", password=True)
                if key:
                    svc.set_api_key("gemini", key)
                    v = svc.validate_provider_connection("gemini", extra={"key": key})
                    if v.get("ok"):
                        result.update({"connected": True, "message": "Gemini key saved and validated"})
                    else:
                        result.update({"connected": False, "message": f"Validation failed: {v.get('error')}"})
            return result

        # Unknown provider fallback
        key = Prompt.ask(f"Enter API key for {provider} (or leave blank to skip)", default="", password=True)
        if key:
            svc.set_api_key(provider, key)
            v = svc.validate_provider_connection(provider, extra={"key": key})
            result.update({"connected": v.get("ok", False), "message": v.get("error") or "validated"})
        
        return result
    except Exception as e:
        return {"provider": provider, "connected": False, "message": f"Exception during connect: {e}"}


def check_provider(provider: str, auto: bool = False) -> Dict[str, Any]:
    """
    Validate a single provider. If interactive and not valid, ask user to connect.
    Returns structured status dict: {'provider', 'ok', 'validated', 'action_taken', 'message'}
    """
    status = {"provider": provider, "ok": False, "validated": False, "action_taken": None, "message": None}
    try:
        cfg = load_config()
        extra = {}
        if provider == "ollama":
            extra["host"] = cfg.get("ollama_host")
        elif provider in ("nemotron", "qwen", "gpt4all", "llama_cpp", "vllm", "sglang", "laguna"):
            extra["host"] = cfg.get(f"{provider}_host")
        else:
            # try Keychain via svc
            api_key = svc.get_api_key(provider)
            if api_key:
                extra["key"] = api_key

        v = svc.validate_provider_connection(provider, extra=extra)
        status["ok"] = v.get("ok", False)
        status["validated"] = v.get("ok", False)
        status["message"] = v.get("error") or v.get("note") or "Connected" if v.get("ok") else "Missing credentials"

        if not v.get("ok") and not auto:
            # Check if this is a "Core" provider worth bothering the user about
            CORE_PROVIDERS = ["ollama", "openai", "gemini"]
            if provider in CORE_PROVIDERS:
                if Confirm.ask(f"[bold yellow]⚠️ Provider '{provider.upper()}' is not ready.[/bold yellow] Configure it now?"):
                    conn = _interactive_connect(provider)
                    status["action_taken"] = conn
                    status["ok"] = conn.get("connected", False)
                    status["message"] = conn.get("message")
    except Exception as e:
        status["ok"] = False
        status["message"] = f"Exception: {e}"
    return status


def startup_check_and_login(auto: bool = False, providers: Optional[List[str]] = None, start_maintenance: bool = True) -> Dict[str, Any]:
    """
    Main entry to call at application startup.
    """
    report = {"auto": bool(auto), "results": [], "maintenance_started": False}
    provs = providers or DEFAULT_PROVIDERS
    
    console.print(Panel(f"JARVIS System Initialization: Verifying connectivity to {len(provs)} providers...", title="Startup", border_style="cyan"))

    for p in provs:
        res = check_provider(p, auto=auto)
        report["results"].append(res)
        if res.get("ok"):
            console.print(f"  [green]✓[/green] {p.upper()}: [dim]{res.get('message')}[/dim]")

    if start_maintenance:
        try:
            start_periodic_config_maintenance(interval_hours=24)
            report["maintenance_started"] = True
        except Exception:
            pass

    console.print(Panel("Intelligence core online. Systems nominal.", title="Status", border_style="green"))
    return report
