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
    "qwen", "kimi", "perplexity", "granite", "nemotron", "groq", "together"
]

def _interactive_connect(provider: str) -> Dict[str, Any]:
    """
    Interactive connect helper. Prompts user for key or host depending on provider.
    Returns dict with status and message.
    """
    provider = provider.lower()
    result = {"provider": provider, "connected": False, "message": ""}

    # Guide for free providers
    FREE_GUIDE = {
        "groq": "Get a free API key at https://groq.com (Fastest inference for Llama 3.3/Mixtral)",
        "together": "Get a free API key at https://together.ai (Supports almost every open model)",
        "deepseek": "Get an API key at https://api.deepseek.com (High-reasoning DeepSeek-V3/R1)",
        "qwen": "Get an API key at https://dashscope.aliyun.com (Strong coding models)"
    }

    try:
        if provider == "ollama":
            console.print(Panel("Ollama: Best for true local privacy. Download from https://ollama.com\nRecommended: `ollama run deepseek-r1` or `llama3.2`", title="Ollama Guide"))
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

        # Cloud API key providers
        if provider in ("openai", "anthropic", "deepseek", "kimi", "mistral", "perplexity", "granite", "groq", "together", "replit", "qwen"):
            if provider in FREE_GUIDE:
                console.print(Panel(FREE_GUIDE[provider], title=f"{provider.upper()} Guide", border_style="green"))
            
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
            # Proactive check
            ensure = svc.ensure_ollama()
            if ensure.get("ok"):
                status["ok"] = True
                status["validated"] = True
                status["message"] = ensure.get("message")
                return status
            else:
                status["message"] = ensure.get("error")
                v = {"ok": False, "error": ensure.get("error")}
        elif provider in ("nemotron", "qwen", "gpt4all", "llama_cpp", "vllm", "sglang", "laguna"):
            extra["host"] = cfg.get(f"{provider}_host")
            v = svc.validate_provider_connection(provider, extra=extra)
        else:
            # try Keychain via svc
            api_key = svc.get_api_key(provider)
            if api_key:
                extra["key"] = api_key
            v = svc.validate_provider_connection(provider, extra=extra)

        if provider != "ollama": # already handled above
            status["ok"] = v.get("ok", False)
            status["validated"] = v.get("ok", False)
            status["message"] = v.get("error") or v.get("note") or "Connected" if v.get("ok") else "Missing credentials"

        if not status["ok"] and not auto:
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
    # Auto-scan network for Ollama servers
    from tools.network import scan_network_for_ollama
    console.print("[dim]Scanning network for Ollama instances...[/dim]")
    found_hosts = scan_network_for_ollama()
    if found_hosts:
        cfg = load_config()
        existing = cfg.get("ollama_hosts", [])
        new_list = list(set(existing + found_hosts))
        if new_list != existing:
            cfg["ollama_hosts"] = new_list
            save_config(cfg)
            console.print(f"[green]✅ Auto-discovered Ollama hosts: {', '.join(found_hosts)}[/green]")
            
    # Proactively detect models
    try:
        from core.services import list_models_for_provider
        console.print("[dim]Detecting available Ollama models...[/dim]")
        res = list_models_for_provider("ollama")
        if res.get("ok"):
            models = res.get("models", [])
            console.print(f"[dim]Detected models: {', '.join(models)}[/dim]")
            if 'gemma4:latest' in models: console.print("[green]✅ Gemma4 Detected.[/green]")
            if 'qwen2.5:latest' in models or 'qwen' in ''.join(models).lower(): console.print("[green]✅ Qwen Detected.[/green]")
    except Exception as e:
        console.print(f"[dim]Could not auto-detect models: {e}[/dim]")

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
