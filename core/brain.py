import requests
import os
import json
from memory.vector import add, search
from core.config import get_env_with_config

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
        try:
            r = requests.post(self.url, json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            })
            r.raise_for_status()
            return r.json()["response"]
        except Exception as e:
            return f"Ollama Error: {e}"

class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, api_key, url, model):
        super().__init__(model)
        self.api_key = api_key
        self.url = url

    def ask(self, prompt, context=""):
        if not self.api_key: return f"Error: API Key missing for {self.url}"
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}]
            }
            r = requests.post(self.url, headers=headers, json=data)
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
            r = requests.post(url, headers=headers, json=data)
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
            r = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
            r.raise_for_status()
            return r.json()["content"][0]["text"]
        except Exception as e:
            return f"Claude Error: {e}"

def get_provider(model_override=None):
    p = get_env_with_config("provider") or "ollama"
    p = p.lower()
    
    if p == "gemini": return GeminiProvider(model=model_override)
    if p == "claude": return ClaudeProvider(model=model_override)
    
    if p == "openai":
        return OpenAICompatibleProvider(
            api_key=get_env_with_config("openai_api_key"),
            url="https://api.openai.com/v1/chat/completions",
            model=model_override or "gpt-4o"
        )
    if p == "grok":
        return OpenAICompatibleProvider(
            api_key=get_env_with_config("xai_api_key"),
            url="https://api.x.ai/v1/chat/completions",
            model=model_override or "grok-beta"
        )
    if p == "mistral":
        return OpenAICompatibleProvider(
            api_key=get_env_with_config("mistral_api_key"),
            url="https://api.mistral.ai/v1/chat/completions",
            model=model_override or "mistral-large-latest"
        )
    if p == "nvidia":
        return OpenAICompatibleProvider(
            api_key=get_env_with_config("nvidia_api_key"),
            url="https://integrate.api.nvidia.com/v1/chat/completions",
            model=model_override or "nvidia/llama-3.1-405b-instruct"
        )
    
    if p == "lm_studio":
        return OpenAICompatibleProvider(
            api_key="lm-studio", # Usually not required
            url=f"{get_env_with_config('lm_studio_host')}/v1/chat/completions",
            model=model_override or "local-model"
        )

    if p == "llama_cpp":
        return OpenAICompatibleProvider(
            api_key="sk-no-key-required",
            url=f"{get_env_with_config('llama_cpp_host')}/v1/chat/completions",
            model=model_override or "local-model"
        )
    
    if p == "gpt4all":
        return OpenAICompatibleProvider(
            api_key="not-needed",
            url=f"{get_env_with_config('gpt4all_host')}/v1/chat/completions",
            model=model_override or "local-model"
        )
        
    if p == "free":
        # Auto-select the best available free tier
        gemini_key = get_env_with_config("gemini_api_key")
        if gemini_key:
            return GeminiProvider(model=model_override or "gemini-1.5-flash")
        return OllamaProvider(model=model_override)
        
    return OllamaProvider(model=model_override)

PERSONALITIES = {
    "professional": "You are a professional senior software engineer. Be precise, accurate, and helpful.",
    "sarcastic": "You are a witty, sarcastic, and slightly rebellious AI assistant (Grok-style). Use humor, be edgy, but still solve the technical problem.",
    "concise": "You are a minimalist assistant. Provide the shortest possible correct answer. No fluff.",
    "mentor": "You are a patient engineering mentor. Explain the 'why' behind your solutions and encourage best practices."
}

def get_project_instructions():
    if os.path.exists("JARVIS.md"):
        with open("JARVIS.md", "r") as f:
            return f.read()
    return ""

from core.prompts import load_prompts

def think(context, task, model=None, prompt_name=None):
    provider = get_provider(model_override=model)
    relevant_memories = search(task, k=3)
    memory_context = "\n".join([f"- {m}" for m in relevant_memories])
    project_rules = get_project_instructions()

    # Load custom prompt if specified, otherwise use active_prompt from config
    prompts = load_prompts()
    active_prompt_name = prompt_name or get_env_with_config("active_prompt") or "default"
    system_instruction = prompts.get(active_prompt_name, prompts["default"])

    personality_type = get_env_with_config("personality") or "professional"
    personality_prompt = PERSONALITIES.get(personality_type, PERSONALITIES["professional"])

    prompt = f"""
{system_instruction}
{personality_prompt}

Core workflow: Research -> Strategy -> Execution.
...

Available Tools:
- SEARCH: grep(pattern) or glob(pattern)
- SYSTEM_SEARCH: name, root (Search across the entire computer/storage)
- READ: read_file(path, start, end)
- EDIT: replace(path, old, new)
- SHELL: run(command)
- INSTALLER: brew(package), git(repo, dest), or curl(url, output)
- GITHUB: action(info, issue, list_prs, create_pr), repo, title, body, head, base
- ANALYTICS: action(file, summary), path

System Rules:
{project_rules}

Memories:
{memory_context}

Context:
{context}

Task:
{task}

Return your response in a structured format. If you need tools, use:
TOOL: <NAME>
ARGS: <JSON>
"""
    response = provider.ask(prompt)
    if not isinstance(response, str) or response.startswith("Error") or response.endswith("Error"):
        return str(response)
        
    add(f"Task: {task}\nResult: {response}", metadata="Conversation")
    return response
