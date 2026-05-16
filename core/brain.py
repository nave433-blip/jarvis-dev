import requests
import os
import json
from memory.vector import add, search

class LLMProvider:
    def ask(self, prompt, context=""):
        raise NotImplementedError

class OllamaProvider(LLMProvider):
    def __init__(self):
        self.host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.url = f"{self.host}/api/generate"
        self.model = os.getenv("JARVIS_MODEL", "llama3")

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
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")
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
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20240620")

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
        self.api_key = os.getenv("XAI_API_KEY")
        self.model = "grok-beta" # Placeholder

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

def get_provider():
    p = os.getenv("JARVIS_PROVIDER", "ollama").lower()
    if p == "gemini": return GeminiProvider()
    if p == "claude": return ClaudeProvider()
    if p == "grok": return GrokProvider()
    return OllamaProvider()

def get_project_instructions():
    if os.path.exists("JARVIS.md"):
        with open("JARVIS.md", "r") as f:
            return f.read()
    return ""

def think(context, task):
    provider = get_provider()
    relevant_memories = search(task, k=3)
    memory_context = "\n".join([f"- {m}" for m in relevant_memories])
    project_rules = get_project_instructions()

    prompt = f"""
You are JARVIS, a senior software engineering assistant.
System: {project_rules}
Memories: {memory_context}
Context: {context}
Task: {task}

Return your response in a structured format. If you need tools, use:
TOOL: <NAME>
ARGS: <JSON>
"""
    response = provider.ask(prompt)
    if not response.startswith("Error"):
        add(f"Task: {task} | Response: {response[:200]}...")
    return response
