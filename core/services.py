"""
Service manager: API keys, provider validation, model listing, routing, adapters.

Adds support for 'nemotron' and 'qwen', robust Ollama repair helper, and normalized error types.
"""

from typing import Dict, Optional, List, Any
import requests
import json
import os
import time
import webbrowser
import keyring
import shutil
import subprocess
from core.config import load_config, save_config
from rich.console import Console

console = Console()

API_KEYS_KEY = "api_keys"
KEYRING_SERVICE_NAME = "jarvis_cli"
DEFAULT_MODELS_KEY = "default_models"
KNOWN_PROVIDERS = [
    "openai", "ollama", "anthropic", "gemini", "mistral", "gpt4all", "llama_cpp", "vllm", "sglang", 
<<<<<<< HEAD
    "nemotron", "qwen", "deepseek", "kimi", "perplexity", "granite", "laguna", "gemma", "together", 
=======
    "nemotron", "qwen", "deepseek", "kimi", "perplexity", "granite", "laguna", "gemma", 
>>>>>>> 9e66ec40d76fc19c950679b2764e4723752540ae
    "glm", "minimax", "lfm", "essential", "olmo", "cogito", "meta", "microsoft", "minicpm", 
    "smollm", "tii", "nous", "lg", "cohere", "yi", "upstage", "groq", "internlm", 
    "athene", "stability", "reflection", "z_ai", "midjourney", "flux", "sora", "kling", "whisper",
    "wolfram", "polly", "heygen", "veo", "mindsdb", "xiaomi", "tencent", "kwaipilot", "replit", "local"
]

# Key/model utilities (unchanged)
def _load_keys() -> Dict[str, str]:
    cfg = load_config()
    return cfg.get(API_KEYS_KEY, {})

def _save_keys(keys: Dict[str, str]):
    cfg = load_config()
    cfg[API_KEYS_KEY] = keys
    save_config(cfg)

def set_api_key(provider: str, key: str):
    try:
        keyring.set_password(KEYRING_SERVICE_NAME, provider.lower(), key)
    except Exception as e:
        console.print(f"[red]Failed to save key in keyring: {e}[/red]")
        # Fallback to config if keyring fails
        keys = _load_keys()
        keys[provider.lower()] = key
        _save_keys(keys)
    return {"ok": True, "provider": provider.lower()}

def get_api_key(provider: str) -> Optional[str]:
    # First try keyring
    try:
        key = keyring.get_password(KEYRING_SERVICE_NAME, provider.lower())
        if key: return key
    except Exception:
        pass

    # Fallback to config file
    key = _load_keys().get(provider.lower())
    if key:
        return key

    # Fallback to environment variables
    env_keys = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "nemotron": "NEMOTRON_API_KEY",
        "qwen": "DASHSCOPE_API_KEY",
        "vllm": "VLLM_API_KEY",
        "sglang": "SGLANG_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "kimi": "MOONSHOT_API_KEY",
        "perplexity": "PERPLEXITY_API_KEY",
        "granite": "WATSONX_API_KEY",
        "laguna": "LAGUNA_API_KEY",
        "gemma": "GEMMA_API_KEY",
        "glm": "GLM_API_KEY",
        "minimax": "MINIMAX_API_KEY",
        "lfm": "LIQUID_API_KEY",
        "essential": "ESSENTIAL_API_KEY",
        "olmo": "OLMO_API_KEY",
        "cogito": "COGITO_API_KEY",
        "meta": "META_API_KEY",
        "microsoft": "AZURE_API_KEY",
        "cohere": "COHERE_API_KEY",
        "yi": "YI_API_KEY",
        "upstage": "UPSTAGE_API_KEY",
        "groq": "GROQ_API_KEY",
<<<<<<< HEAD
        "together": "TOGETHER_API_KEY",
        "qwen": "DASHSCOPE_API_KEY",
=======
>>>>>>> 9e66ec40d76fc19c950679b2764e4723752540ae
        "internlm": "INTERNLM_API_KEY",
        "stability": "STABILITY_API_KEY",
        "midjourney": "MIDJOURNEY_API_KEY",
        "flux": "FLUX_API_KEY",
        "sora": "OPENAI_API_KEY",
        "kling": "KLING_API_KEY",
        "whisper": "OPENAI_API_KEY",
        "wolfram": "WOLFRAM_APP_ID",
        "polly": "AWS_SECRET_KEY",
        "heygen": "HEYGEN_API_KEY",
        "veo": "GEMINI_API_KEY",
        "mindsdb": "MINDSDB_API_KEY",
        "xiaomi": "XIAOMI_API_KEY",
        "tencent": "TENCENT_API_KEY",
        "kwaipilot": "KWAIPILOT_API_KEY",
        "replit": "REPLIT_API_KEY"
    }
    env_var = env_keys.get(provider.lower())
    if env_var:
        return os.getenv(env_var)
    return None

def unset_api_key(provider: str):
    try:
        keyring.delete_password(KEYRING_SERVICE_NAME, provider.lower())
    except Exception:
        pass

    keys = _load_keys()
    if provider.lower() in keys:
        del keys[provider.lower()]
        _save_keys(keys)
    return {"ok": True, "provider": provider.lower()}

def _load_default_models() -> Dict[str, str]:
    cfg = load_config()
    return cfg.get(DEFAULT_MODELS_KEY, {})

def _save_default_models(d: Dict[str, str]):
    cfg = load_config()
    cfg[DEFAULT_MODELS_KEY] = d
    save_config(cfg)

def set_default_model(provider: str, model_name: str):
    d = _load_default_models()
    d[provider.lower()] = model_name
    _save_default_models(d)
    return {"ok": True, "provider": provider.lower(), "model": model_name}

def get_default_model(provider: str) -> Optional[str]:
    return _load_default_models().get(provider.lower())

<<<<<<< HEAD
def get_connected_providers() -> List[str]:
    """Return a list of all providers that have an API key or host configured."""
    connected = []
    cfg = load_config()
    for p in KNOWN_PROVIDERS:
        if p == "ollama":
            if cfg.get("ollama_host"): connected.append(p)
            continue
        
        # Check for host-based providers
        if f"{p}_host" in cfg and cfg.get(f"{p}_host"):
            connected.append(p)
            continue
            
        # Check for key-based providers
        if get_api_key(p):
            connected.append(p)
            
    return connected

def validate_gemini(key: str, timeout: float = 5.0) -> Dict:
    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
        r = requests.get(url, timeout=timeout)
        if r.status_code == 200:
            return {"ok": True, "provider": "gemini", "note": "Gemini key validated"}
        if r.status_code == 400:
            return {"ok": False, "error": "Gemini key invalid", "error_type": "unauthorized"}
        return {"ok": False, "error": f"Gemini error {r.status_code}", "error_type": "other"}
    except Exception as e:
        return {"ok": False, "error": str(e), "error_type": "unreachable"}

=======
>>>>>>> 9e66ec40d76fc19c950679b2764e4723752540ae
# --------------------
# Validation helpers (enhanced)
# --------------------
def validate_openai(key: str, timeout: float = 5.0) -> Dict:
    url = "https://api.openai.com/v1/models"
    headers = {"Authorization": f"Bearer {key}"}
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        if r.status_code == 200:
            return {"ok": True, "provider": "openai", "models_count": len(r.json().get("data", []))}
        if r.status_code == 401:
            return {"ok": False, "error": "Unauthorized: invalid OpenAI key", "error_type": "unauthorized"}
        return {"ok": False, "error": f"OpenAI returned HTTP {r.status_code}", "error_type": "other"}
    except Exception as e:
        return {"ok": False, "error": str(e), "error_type": "unreachable"}

def validate_ollama(host: str, timeout: float = 2.0) -> Dict:
    """
    Probes common Ollama endpoints and returns a helpful status.
    If 401 is seen, marks as auth-required.
    """
    host = host.rstrip("/")
<<<<<<< HEAD
    # /api/tags is the most reliable endpoint for checking health and models
    endpoints = ["/api/tags", "/api/models", "/api/health", "/api/completions", ""]
    last_exc = None
    for p in endpoints:
        url = host + p if p else host
=======
    endpoints = ["/api/models", "/api/tags", "/api/health", "/api/completions"]
    for p in endpoints:
        url = host + p
>>>>>>> 9e66ec40d76fc19c950679b2764e4723752540ae
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code == 200:
                return {"ok": True, "provider": "ollama", "endpoint": url}
            if r.status_code == 401:
                return {"ok": False, "error": "Ollama requires authentication (401)", "error_type": "auth", "endpoint": url}
<<<<<<< HEAD
            # If we get a 404, we continue to the next endpoint
            if r.status_code == 404:
                continue
            # Other 4xx codes might be auth or configuration issues
            if 400 <= r.status_code < 500:
                return {"ok": False, "error": f"Ollama returned HTTP {r.status_code}", "error_type": "auth", "endpoint": url}
        except requests.exceptions.RequestException as e:
            last_exc = e
            continue
    # none responded 200/401
    return {"ok": False, "error": f"Could not reach Ollama at {host}. Error: {last_exc}", "error_type": "unreachable"}
=======
            # 403 and 4xx other codes -> auth/permission
            if 400 <= r.status_code < 500:
                return {"ok": False, "error": f"Ollama returned HTTP {r.status_code}", "error_type": "auth", "endpoint": url}
        except requests.exceptions.RequestException as e:
            # continue to try other endpoints
            last_exc = e
            continue
    # none responded 200/401
    return {"ok": False, "error": f"Could not reach Ollama at {host} (checked {len(endpoints)} endpoints)", "error_type": "unreachable"}
>>>>>>> 9e66ec40d76fc19c950679b2764e4723752540ae

def validate_generic_host(host: str, timeout: float = 2.0) -> Dict:
    try:
        r = requests.get(host, timeout=timeout)
        return {"ok": True, "status": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e), "error_type": "unreachable"}

def validate_provider_connection(provider: str, extra: Optional[Dict[str, Any]] = None) -> Dict:
    provider = provider.lower()
    extra = extra or {}
    if provider == "openai":
        key = extra.get("key") or get_api_key("openai")
        if not key:
            return {"ok": False, "error": "OpenAI key not configured", "error_type": "unauthorized"}
        return validate_openai(key)
    if provider == "ollama":
        cfg = load_config()
        host = extra.get("host") or cfg.get("ollama_host")
        if not host:
            return {"ok": False, "error": "Ollama host not configured (config.ollama_host)", "error_type": "unreachable"}
        return validate_ollama(host)
    if provider in ("gpt4all", "llama_cpp", "vllm", "sglang", "nemotron", "qwen", "local"):
        cfg = load_config()
        host = extra.get("host") or cfg.get(f"{provider}_host")
        if not host:
            return {"ok": False, "error": f"No host configured for {provider} (e.g. {provider}_host in config)", "error_type": "unreachable"}
        return validate_generic_host(host)
    if provider == "anthropic":
        key = extra.get("key") or get_api_key("anthropic")
        if not key:
            return {"ok": False, "error": "Anthropic key not configured", "error_type": "unauthorized"}
        return {"ok": True, "provider": "anthropic", "note": "Key present (no network check performed)"}
    if provider == "gemini":
        key = extra.get("key") or get_api_key("gemini")
        if not key:
            return {"ok": False, "error": "Gemini key not configured", "error_type": "unauthorized"}
<<<<<<< HEAD
        return validate_gemini(key)
=======
        return {"ok": True, "provider": "gemini", "note": "Key present (OAuth flows not validated)"}
>>>>>>> 9e66ec40d76fc19c950679b2764e4723752540ae
    return {"ok": False, "error": f"Provider '{provider}' not supported for validation.", "error_type": "other"}

# --------------------
# Model listing (unchanged core behavior; extended for nemotron/qwen host lists)
# --------------------
def list_models_for_provider(provider: str, extra: Optional[Dict[str, Any]] = None) -> Dict:
    provider = provider.lower()
    extra = extra or {}
    if provider == "openai":
        key = extra.get("key") or get_api_key("openai")
        if not key:
            return {"ok": False, "error": "OpenAI key required", "error_type": "unauthorized"}
        try:
            r = requests.get("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {key}"}, timeout=5)
            if r.status_code == 200:
                models = [m.get("id") for m in r.json().get("data", []) if m.get("id")]
                return {"ok": True, "models": models}
            return {"ok": False, "error": f"OpenAI error {r.status_code}", "error_type": "other"}
        except Exception as e:
            return {"ok": False, "error": str(e), "error_type": "unreachable"}
    if provider == "ollama":
        cfg = load_config()
        host = extra.get("host") or cfg.get("ollama_host")
        if not host:
            return {"ok": False, "error": "Ollama host not configured", "error_type": "unreachable"}
        for p in ("/api/models", "/api/tags"):
            try:
                r = requests.get(host.rstrip("/") + p, timeout=4)
                if r.status_code == 200:
                    try:
                        data = r.json()
                        if isinstance(data, dict) and "models" in data:
                            models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                        else:
                            models = list(data) if isinstance(data, list) else []
                        return {"ok": True, "models": models}
                    except Exception:
                        return {"ok": True, "models": []}
            except Exception:
                continue
        return {"ok": False, "error": "Could not fetch models from Ollama", "error_type": "unreachable"}
    # For nemotron/qwen assume host-based listing (config.<provider>_host)
    if provider in ("nemotron", "qwen"):
        cfg = load_config()
        host = extra.get("host") or cfg.get(f"{provider}_host")
        if not host:
            return {"ok": False, "error": f"No host configured for {provider}", "error_type": "unreachable"}
        return validate_generic_host(host)
    fallback = {
        "openai": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        "anthropic": ["claude-2.1", "claude-instant"],
        "gemini": ["gemini-1.5-pro", "gemini-1.0-base"],
    }
    return {"ok": True, "models": fallback.get(provider, [])}

# --------------------
# Call adapters (OpenAI/Ollama + host-based adapters for nemotron/qwen), normalized errors
# --------------------
def _call_openai_chat(api_key: str, model: str, messages: List[Dict[str,str]], temperature: float = 0.2, timeout: float = 20.0) -> Dict:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {"model": model, "messages": messages, "temperature": temperature}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if r.status_code == 200:
            j = r.json()
            if "choices" in j and len(j["choices"]) > 0:
                content = j["choices"][0].get("message", {}).get("content") or j["choices"][0].get("text", "")
                return {"ok": True, "text": content, "raw": j}
            return {"ok": False, "error": "No choices in OpenAI response", "raw": j, "error_type": "other"}
        if r.status_code == 401:
            return {"ok": False, "error": "Unauthorized (OpenAI key invalid)", "error_type": "unauthorized"}
        if r.status_code == 429:
            return {"ok": False, "error": "Rate limited", "error_type": "rate_limited"}
        return {"ok": False, "error": f"OpenAI HTTP {r.status_code}: {r.text[:400]}", "error_type": "other"}
    except requests.exceptions.RequestException as e:
        return {"ok": False, "error": str(e), "error_type": "unreachable"}
    except Exception as e:
        return {"ok": False, "error": str(e), "error_type": "other"}

def _call_ollama(host: str, model: str, prompt: str, timeout: float = 20.0) -> Dict:
    host = host.rstrip("/")
    # Try /api/chat first (modern standard) then fallback to /api/generate
    endpoints = [
        (f"{host}/api/chat", {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False}),
        (f"{host}/api/generate", {"model": model, "prompt": prompt, "stream": False}),
        (f"{host}/api/completions", {"model": model, "prompt": prompt})
    ]
    headers = {"Content-Type": "application/json"}
    
    for url, body in endpoints:
        try:
            r = requests.post(url, headers=headers, json=body, timeout=timeout)
            if r.status_code == 200:
                try:
                    j = r.json()
                    # Extract from /api/chat
                    if "message" in j and "content" in j["message"]:
                        return {"ok": True, "text": j["message"]["content"], "raw": j}
                    # Extract from /api/generate
                    if "response" in j:
                        return {"ok": True, "text": j["response"], "raw": j}
                    # Generic fallback
                    return {"ok": True, "text": json.dumps(j)[:2000], "raw": j}
                except Exception:
                    return {"ok": True, "text": r.text, "raw": r.text}
            if r.status_code == 401:
                return {"ok": False, "error": "Ollama returned 401 - auth required", "error_type": "auth"}
        except requests.exceptions.RequestException:
            continue
            
    return {"ok": False, "error": f"Ollama call failed to {host}", "error_type": "unreachable"}

def _call_host_adapter(host: str, model: Optional[str], prompt: str, timeout: float = 20.0) -> Dict:
    """
    Generic host adapter for nemotron/qwen/gpt4all/llama_cpp: do a POST to host + /api or /v1 endpoints if present.
    If the host isn't a simple REST LLM endpoint, fallback to failure for safety.
    """
    host = host.rstrip("/")
    candidate_paths = ["/api/completions", "/v1/completions", "/v1/generate", "/generate"]
    headers = {"Content-Type": "application/json"}
    body = {"model": model, "prompt": prompt} if model else {"prompt": prompt}
    for p in candidate_paths:
        url = host + p
        try:
            r = requests.post(url, headers=headers, json=body, timeout=timeout)
            if r.status_code == 200:
                try:
                    j = r.json()
                    # best-effort extract
                    text = ""
                    if isinstance(j, dict):
                        text = j.get("text") or j.get("output") or json.dumps(j)
                    else:
                        text = str(j)
                    return {"ok": True, "text": text, "raw": j}
                except Exception:
                    return {"ok": True, "text": r.text, "raw": r.text}
            if r.status_code == 401:
                return {"ok": False, "error": "Unauthorized", "error_type": "auth"}
        except requests.exceptions.RequestException as e:
            continue
    return {"ok": False, "error": f"Host adapter could not reach {host}", "error_type": "unreachable"}

# --------------------
# Public call entrypoint (normalized, extended)
# --------------------
def call_model(provider: str, model: Optional[str], messages_or_text: Any, temperature: float = 0.2, timeout: float = 20.0) -> Dict:
    provider = provider.lower()
    if isinstance(messages_or_text, str):
        messages = [{"role": "user", "content": messages_or_text}]
    else:
        messages = messages_or_text

    def _wrap_net_error(e):
        return {"ok": False, "error": str(e), "error_type": "unreachable"}

    if provider == "openai":
        key = get_api_key("openai")
        if not key:
            return {"ok": False, "error": "OpenAI key not configured", "error_type": "unauthorized"}
        model = model or get_default_model("openai") or load_config().get("jarvis_model")
        try:
            return _call_openai_chat(key, model, messages, temperature=temperature, timeout=timeout)
        except requests.exceptions.RequestException as e:
            return _wrap_net_error(e)
        except Exception as e:
            return {"ok": False, "error": str(e), "error_type": "other"}

    if provider == "ollama":
        cfg = load_config()
        host = cfg.get("ollama_host")
        if not host:
            return {"ok": False, "error": "Ollama host not configured (config.ollama_host)", "error_type": "unreachable"}
        prompt = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in messages]) if isinstance(messages, list) else str(messages)
        model = model or get_default_model("ollama") or load_config().get("jarvis_model")
        try:
            res = _call_ollama(host, model, prompt, timeout=timeout)
            if not res.get("ok"):
                return {"ok": False, "error": res.get("error"), "error_type": res.get("error_type", "unreachable")}
            return res
        except requests.exceptions.RequestException as e:
            return _wrap_net_error(e)
        except Exception as e:
            return {"ok": False, "error": str(e), "error_type": "other"}

    if provider in ("nemotron", "qwen", "gpt4all", "llama_cpp", "vllm", "sglang"):
        cfg = load_config()
        host = cfg.get(f"{provider}_host")
        if not host:
            return {"ok": False, "error": f"No host configured for {provider}", "error_type": "unreachable"}
        prompt = "\n".join([m.get("content","") for m in messages]) if isinstance(messages, list) else str(messages)
        return _call_host_adapter(host, model, prompt, timeout=timeout)

    # Fallback removed to avoid infinite loops with core.brain.think
    return {"ok": False, "error": f"Provider '{provider}' not handled in call_model.", "error_type": "other"}

# --------------------
# Ollama repair helper and detection utilities
# --------------------
def detect_ollama_candidates() -> List[str]:
    """
    Return a list of common Ollama host candidates to try probing.
    """
    candidates = [
        "http://localhost:11434",
        "http://127.0.0.1:11434",
        "http://0.0.0.0:11434",
        "http://localhost:5000",
    ]
    # include configured host if present
    cfg = load_config()
    ch = cfg.get("ollama_host")
    if ch and ch not in candidates:
        candidates.insert(0, ch)
    return candidates

<<<<<<< HEAD
def ensure_ollama() -> Dict:
    """
    High-level utility to ensure Ollama is installed, running, and reachable.
    Used by startup and repair flows.
    """
    cfg = load_config()
    host = cfg.get("ollama_host", "http://localhost:11434")
    
    # 1. Quick probe
    v = validate_ollama(host, timeout=1.0)
    if v.get("ok"):
        return {"ok": True, "message": f"Ollama is running and reachable at {host}", "host": host}
    
    # 2. If not reachable, attempt repair
    console.print(f"[yellow]Ollama not reachable at {host}. Attempting auto-repair...[/yellow]")
    rep = repair_ollama(host)
    if rep.get("fixed"):
        # Re-probe
        new_host = cfg.get("ollama_host", host)
        v = validate_ollama(new_host, timeout=1.5)
        if v.get("ok"):
            return {"ok": True, "message": "Ollama repaired and verified.", "host": new_host}
    
    # 3. Check if binary exists but server is down
    import shutil
    if shutil.which("ollama"):
        return {"ok": False, "error": "Ollama is installed but the server is not responding. Try running 'ollama serve' manually.", "error_type": "down"}
    
    # 4. Check for Ollama.app on Mac
    if sys.platform == "darwin" and os.path.exists("/Applications/Ollama.app"):
        return {"ok": False, "error": "Ollama.app found but not running. Please open it.", "error_type": "app_closed"}
        
    return {"ok": False, "error": "Ollama is not installed. Download it from https://ollama.com", "error_type": "missing"}

=======
>>>>>>> 9e66ec40d76fc19c950679b2764e4723752540ae
def repair_ollama(host: Optional[str] = None, open_app_if_mac: bool = True, prompt_for_host: bool = True) -> Dict:
    """
    Improved repair helper that:
    - probes candidate hosts
    - attempts to open Ollama.app on macOS
    - attempts 'brew services restart ollama' if Homebrew-managed service present
    - attempts ollama CLI checks if available
    - attempts to restart Docker container if one named/containing 'ollama' found
    - persists successful host to config
    Returns a structured report.
    """
    cfg = load_config()
    report = {"attempts": [], "fixed": False, "details": []}
    # candidate hosts
    candidates = []
    if host:
        candidates.append(host)
    # include configured host first if present
    ch = cfg.get("ollama_host")
    if ch and ch not in candidates:
        candidates.append(ch)
    # common defaults
    for c in ("http://localhost:11434", "http://127.0.0.1:11434", "http://0.0.0.0:11434", "http://localhost:5000"):
        if c not in candidates:
            candidates.append(c)

    # function to probe a host quickly
    def probe(h):
        result = validate_ollama(h, timeout=2)
        result.setdefault("host", h)
        return result

    # 1) probe candidates
    for h in candidates:
        p = probe(h)
        report["attempts"].append(p)
        if p.get("ok"):
            cfg["ollama_host"] = h
            save_config(cfg)
            report["fixed"] = True
            report["details"].append(f"Detected Ollama at {h} and saved to config.")
            return report
        if p.get("error_type") == "auth":
            cfg["ollama_host"] = h
            save_config(cfg)
            report["details"].append(f"Host {h} requires authentication (saved host). Please open the Ollama app or web UI to authenticate.")
            return report

    # 2) Try to start/open app on macOS
    try:
        if open_app_if_mac and os.name == "posix" and "darwin" in os.uname().sysname.lower():
            report["details"].append("Attempting to open Ollama.app on macOS...")
            os.system("open -a Ollama")
            time.sleep(4)
            for h in candidates:
                p = probe(h)
                report["attempts"].append({"after_open": p})
                if p.get("ok"):
                    cfg["ollama_host"] = h
                    save_config(cfg)
                    report["fixed"] = True
                    report["details"].append(f"Detected Ollama at {h} after launching app.")
                    return report
    except Exception as e:
        report["details"].append(f"mac open attempt error: {e}")

    # 3) Try Homebrew service restart if brew present
    try:
        if shutil.which("brew"): 
            res = subprocess.run(["brew", "services", "list"], capture_output=True, text=True, timeout=8)
            if "ollama" in res.stdout.lower():
                report["details"].append("Found Homebrew-managed Ollama service; attempting restart via brew services restart ollama")
                try:
                    rr = subprocess.run(["brew", "services", "restart", "ollama"], capture_output=True, text=True, timeout=60)
                    report["attempts"].append({"brew_restart": rr.returncode, "stdout": rr.stdout, "stderr": rr.stderr})
                    time.sleep(3)
                    for h in candidates:
                        p = probe(h)
                        report["attempts"].append({"after_brew_restart": p})
                        if p.get("ok"):
                            cfg["ollama_host"] = h
                            save_config(cfg)
                            report["fixed"] = True
                            report["details"].append(f"Detected Ollama at {h} after brew restart.")
                            return report
                except Exception as e:
                    report["details"].append(f"brew restart error: {e}")
    except Exception:
        pass

    # 4) Try ollama CLI if present
    try:
        if shutil.which("ollama"):
            report["details"].append("ollama CLI found; checking status/version.")
            try:
                rr = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=6)
                report["attempts"].append({"ollama_cli_version": rr.stdout.strip()})
            except Exception as e:
                report["details"].append(f"ollama --version error: {e}")
            for cmd in (["ollama", "start"], ["ollama", "daemon"], ["ollama", "serve"]):
                try:
                    # Run in background via subprocess.Popen since these commands block
                    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    report["attempts"].append({ "cmd": " ".join(cmd), "started": True })
                    time.sleep(3)
                    for h in candidates:
                        p = probe(h)
                        report["attempts"].append({"after_cli_start": p})
                        if p.get("ok"):
                            cfg["ollama_host"] = h
                            save_config(cfg)
                            report["fixed"] = True
                            report["details"].append(f"Detected Ollama at {h} after CLI start attempt.")
                            return report
                except Exception:
                    continue
    except Exception:
        pass

    # 5) Try docker container restart if present
    try:
        if shutil.which("docker"):
            dp = subprocess.run(["docker", "ps", "--format", "{{.ID}} {{.Image}} {{.Names}}"], capture_output=True, text=True)
            lines = dp.stdout.splitlines()
            found = []
            for L in lines:
                if "ollama" in L.lower() or "ollama" in (L.split()[1].lower() if len(L.split())>1 else ""):
                    cid = L.split()[0]
                    found.append(cid)
            if found:
                for cid in found:
                    report["details"].append(f"Found Ollama Docker container {cid}; attempting restart")
                    subprocess.run(["docker", "restart", cid], timeout=30)
                    time.sleep(3)
                    for h in candidates:
                        p = probe(h)
                        report["attempts"].append({"after_docker_restart": p})
                        if p.get("ok"):
                            cfg["ollama_host"] = h
                            save_config(cfg)
                            report["fixed"] = True
                            report["details"].append(f"Detected Ollama at {h} after docker restart.")
                            return report
    except Exception as e:
        report["details"].append(f"docker attempts error: {e}")

    # 6) Prompt user to input host
    if prompt_for_host:
        try:
            from rich.prompt import Prompt
            candidate = Prompt.ask("Enter Ollama host URL (or leave blank to skip)", default="")
            if candidate:
                p = probe(candidate)
                report["attempts"].append({"host_user": candidate, "probe": p})
                if p.get("ok"):
                    cfg["ollama_host"] = candidate
                    save_config(cfg)
                    report["fixed"] = True
                    report["details"].append(f"User-provided host {candidate} validated and saved.")
                    return report
                if p.get("error_type") == "auth":
                    cfg["ollama_host"] = candidate
                    save_config(cfg)
                    report["details"].append(f"Saved Ollama host {candidate} (requires auth). Please authenticate via the Ollama app or web.")
                    return report
                report["details"].append(f"Provided host {candidate} failed: {p.get('error')}")
        except Exception:
            pass

    report["details"].append(
        "Unable to auto-detect or start Ollama. Please ensure Ollama is installed and running, "
        "or set 'ollama_host' in your ~/.jarvis/config.json. If you need to login, open the Ollama app or visit https://ollama.com"
    )
    return report
