import requests
import os
import json
from memory.vector import add, search
from core.config import get_env_with_config
from core.prompts import load_prompts

def is_connected():
    """Check if the user is online."""
    try:
        requests.get("https://8.8.8.8", timeout=1)
        return True
    except:
        return False

class LLMProvider:
    def __init__(self, model=None):
        self.model = model
    def ask(self, prompt, context=""):
        raise NotImplementedError

class OllamaProvider(LLMProvider):
    def __init__(self, model=None):
        super().__init__(model or get_env_with_config("jarvis_model") or "llama3")
        self.host = get_env_with_config("ollama_host") or "http://localhost:11434"
        self.url = f"{self.host}/api/generate"

    def ask(self, prompt, context=""):
        import time
        max_retries = 3
        timeout = 120 # Increased to 2 minutes
        
        for attempt in range(max_retries):
            try:
                r = requests.post(self.url, json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                }, timeout=timeout)
                r.raise_for_status()
                return r.json()["response"]
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                if attempt == max_retries - 1:
                    return f"Ollama Error (Final Attempt): {e}"
                console.print(f"[yellow]⚠️ Ollama timeout/error (Attempt {attempt+1}/{max_retries}). Retrying in 5s...[/yellow]")
                time.sleep(5)
            except Exception as e:
                return f"Ollama Error: {e}"
        return "Ollama Error: Max retries exceeded."

class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, api_key, url, model):
        super().__init__(model)
        self.api_key = api_key
        self.url = url

    def ask(self, prompt, context=""):
        if not self.api_key:
            # Autonomous Key Recovery
            console.print(f"[dim]⚠️ API Key missing for {self.url}. Attempting autonomous recovery...[/dim]")
            from tools.search import system_find
            # Look for common key containers
            results = system_find(".env")
            if results and "/" in results:
                # If a .env exists, the agent can potentially read it later
                # For now, we'll inform the brain to suggest /config or /free
                return f"Error: API Key missing. JARVIS found potential keys in local .env files. Please use '/config' to set them or '/free' for help."
            return f"Error: API Key missing for {self.url}. Use '/free' to get one or '/config' to set it."
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}]
            }
            r = requests.post(self.url, headers=headers, json=data, timeout=60)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"API Error ({self.url}): {e}"

class GeminiProvider(LLMProvider):
    def __init__(self, model=None):
        super().__init__(model or get_env_with_config("gemini_model") or "gemini-1.5-pro")
        self.api_key = get_env_with_config("gemini_api_key")

    def ask(self, prompt, context=""):
        if not self.api_key: return "Gemini API Key missing."
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        try:
            headers = {'Content-Type': 'application/json'}
            data = {"contents": [{"parts": [{"text": prompt}]}]}
            r = requests.post(url, headers=headers, json=data, timeout=60)
            r.raise_for_status()
            return r.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            return f"Gemini Error: {e}"

class ClaudeProvider(LLMProvider):
    def __init__(self, model=None):
        super().__init__(model or get_env_with_config("claude_model") or "claude-3-5-sonnet-20240620")
        self.api_key = get_env_with_config("anthropic_api_key")

    def ask(self, prompt, context=""):
        if not self.api_key: return "Claude API Key missing."
        try:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            data = {
                "model": self.model,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": prompt}]
            }
            r = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data, timeout=60)
            r.raise_for_status()
            return r.json()["content"][0]["text"]
        except Exception as e:
            return f"Claude Error: {e}"

def get_best_offline():
    """Auto-detect and return the best available offline provider."""
    # Check Ollama
    try:
        host = get_env_with_config("ollama_host") or "http://localhost:11434"
        requests.get(f"{host}/api/tags", timeout=0.5)
        return OllamaProvider()
    except: pass
    
    # Check LM Studio
    try:
        host = get_env_with_config("lm_studio_host") or "http://localhost:1234"
        requests.get(f"{host}/v1/models", timeout=0.5)
        return OpenAICompatibleProvider(api_key="lm-studio", url=f"{host}/v1/chat/completions", model="local-model")
    except: pass
    
    # Fallback to Ollama even if it fails (standard default)
    return OllamaProvider()

def get_best_online():
    """Auto-detect and return the best available online provider."""
    # Prioritize Gemini Free Tier
    if get_env_with_config("gemini_api_key"):
        return GeminiProvider(model="gemini-1.5-flash")
    # Then OpenAI
    if get_env_with_config("openai_api_key"):
        return OpenAICompatibleProvider(
            api_key=get_env_with_config("openai_api_key"),
            url="https://api.openai.com/v1/chat/completions",
            model="gpt-4o-mini"
        )
    # Then Grok
    if get_env_with_config("xai_api_key"):
        return OpenAICompatibleProvider(
            api_key=get_env_with_config("xai_api_key"),
            url="https://api.x.ai/v1/chat/completions",
            model="grok-beta"
        )
    return None

def get_provider(model_override=None):
    mode = get_env_with_config("model_mode") or "manual"
    p = get_env_with_config("provider") or "ollama"
    p = p.lower()
    
    # List of all potential providers in order of fallback priority
    # Local First -> Cloud Free -> Cloud Paid
    providers = []
    
    # 1. Primary choice
    if p == "ollama": providers.append(OllamaProvider(model=model_override))
    elif p == "gemini": providers.append(GeminiProvider(model=model_override))
    elif p == "claude": providers.append(ClaudeProvider(model=model_override))
    # ... (other cases handled by manual selection below)

    # 2. Local Fallbacks
    providers.append(OllamaProvider())
    providers.append(OpenAICompatibleProvider(
        api_key="lm-studio", 
        url=f"{get_env_with_config('lm_studio_host')}/v1/chat/completions", 
        model="local-model"
    ))
    providers.append(OpenAICompatibleProvider(
        api_key="not-needed", 
        url=f"{get_env_with_config('gpt4all_host')}/v1/chat/completions", 
        model="local-model"
    ))

    # 3. Cloud Fallbacks (only if key exists)
    if get_env_with_config("gemini_api_key"):
        providers.append(GeminiProvider(model="gemini-1.5-flash"))
    if get_env_with_config("openai_api_key"):
        providers.append(OpenAICompatibleProvider(
            api_key=get_env_with_config("openai_api_key"),
            url="https://api.openai.com/v1/chat/completions",
            model="gpt-4o-mini"
        ))

    # Autonomous "Indestructible" Brain Selection
    # If mode is not manual, we try to find the FIRST working one
    for provider in providers:
        try:
            # Quick health check for local providers
            if isinstance(provider, OllamaProvider):
                requests.get(provider.url.replace("/api/generate", "/api/tags"), timeout=0.2)
                return provider
            if "localhost" in getattr(provider, 'url', ''):
                # Generic check for other local servers
                requests.get(provider.url.replace("/v1/chat/completions", "/v1/models"), timeout=0.2)
                return provider
            
            # For cloud, we check if key exists and internet is on
            if is_connected():
                if getattr(provider, 'api_key', None):
                    return provider
        except:
            continue

    # Final fallback if everything else fails
    return OllamaProvider(model=model_override)

PERSONALITIES = {
    "professional": "You are a professional senior software engineer. Be precise, accurate, and helpful.",
    "sarcastic": "You are a witty, sarcastic, and slightly rebellious AI assistant (Grok-style). Use humor, be edgy, but still solve the technical problem.",
    "concise": "You are a minimalist assistant. Provide the shortest possible correct answer. No fluff.",
    "mentor": "You are a patient engineering mentor. Explain the 'why' behind your solutions and encourage best practices.",
    "nave_ai": "You are the NAVE-AI Integrator. Focus on multi-model refinement and technical redundancy for maximum precision."
}

def get_project_instructions():
    if os.path.exists("JARVIS.md"):
        with open("JARVIS.md", "r") as f:
            return f.read()
    return ""

def think(context, task, model=None, prompt_name=None):
    provider = get_provider(model_override=model)
    relevant_memories = search(task, k=3)
    memory_context = "\n".join([f"- {m}" for m in relevant_memories])
    project_rules = get_project_instructions()
    
    prompts = load_prompts()
    active_prompt_name = prompt_name or get_env_with_config("active_prompt") or "default"
    system_instruction = prompts.get(active_prompt_name, prompts["default"])
    
    personality_type = get_env_with_config("personality") or "professional"
    personality_prompt = PERSONALITIES.get(personality_type, PERSONALITIES["professional"])

    prompt = f"""
{system_instruction}
{personality_prompt}

Context: {context}
Task: {task}

Tools:
- SEARCH: grep(pattern), glob(pattern)
- SYSTEM_SEARCH: name, root (System-wide find)
- READ: read_file(path, start, end)
- EDIT: replace(path, old, new)
- SHELL: run(command)
- CLOUD: platform, action, path
- NETWORK/SSH/SERVER/HARDWARE/GITHUB/ANALYTICS

Format:
TOOL: <NAME>
ARGS: <JSON>
"""
    response = provider.ask(prompt)
    if not isinstance(response, str) or response.startswith("Error") or response.endswith("Error"):
        return str(response)
        
    add(f"Task: {task}\nResult: {response}", metadata="Conversation")
    return response
