import requests
import os
import json
from memory.vector import add, search
from core.config import get_env_with_config

class LLMProvider:
    def ask(self, prompt, context=""):
        raise NotImplementedError

class OllamaProvider(LLMProvider):
    def __init__(self):
        self.host = get_env_with_config("ollama_host") or "http://localhost:11434"
        self.url = f"{self.host}/api/generate"
        self.model = get_env_with_config("jarvis_model") or "llama3"

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

class GeminiProvider(LLMProvider):
    def __init__(self):
        self.api_key = get_env_with_config("gemini_api_key")
        self.model = get_env_with_config("gemini_model") or "gemini-1.5-pro"
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

    def ask(self, prompt, context=""):
        if not self.api_key: return "Gemini API Key missing."
        try:
            headers = {'Content-Type': 'application/json'}
            data = {"contents": [{"parts": [{"text": prompt}]}]}
            r = requests.post(self.url, headers=headers, json=data)
            r.raise_for_status()
            return r.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            return f"Gemini Error: {e}"

class ClaudeProvider(LLMProvider):
    def __init__(self):
        self.api_key = get_env_with_config("anthropic_api_key")
        self.model = get_env_with_config("claude_model") or "claude-3-5-sonnet-20240620"

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

class GrokProvider(LLMProvider):
    def __init__(self):
        self.api_key = get_env_with_config("xai_api_key")
        self.model = "grok-beta" 

    def ask(self, prompt, context=""):
        if not self.api_key: return "Grok API Key missing."
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}]
            }
            r = requests.post("https://api.x.ai/v1/chat/completions", headers=headers, json=data)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Grok Error: {e}"

def get_provider(model_override=None):
    p = get_env_with_config("provider") or "ollama"
    p = p.lower()
    
    if p == "gemini": provider = GeminiProvider()
    elif p == "claude": provider = ClaudeProvider()
    elif p == "grok": provider = GrokProvider()
    else: provider = OllamaProvider()

    if model_override:
        provider.model = model_override
        if p == "gemini":
            provider.url = f"https://generativelanguage.googleapis.com/v1beta/models/{provider.model}:generateContent?key={provider.api_key}"
    return provider

def get_project_instructions():
    if os.path.exists("JARVIS.md"):
        with open("JARVIS.md", "r") as f:
            return f.read()
    return ""

def think(context, task, model=None):
    provider = get_provider(model_override=model)
    relevant_memories = search(task, k=3)
    memory_context = "\n".join([f"- {m}" for m in relevant_memories])
    project_rules = get_project_instructions()

    prompt = f"""
You are JARVIS, a senior software engineering assistant.

Core workflow: Research -> Strategy -> Execution.

Available Tools:
- SEARCH: grep(pattern) or glob(pattern)
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
        # Fallback or Error reporting
        return str(response)
        
    add(f"Task: {task} | Response: {response[:200]}...")
    return response
