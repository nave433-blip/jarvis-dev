import shlex
import subprocess
import difflib
import logging
import json
import os
import sys
from typing import Callable, Dict, List, Optional, Any
from core.brain import think

logger = logging.getLogger("jarvis.command_handler")

class CommandError(Exception):
    pass

class CommandHandler:
    def __init__(self, shell_timeout: int = 180):
        self._registry: Dict[str, Dict[str, Any]] = {}
        self.shell_timeout = shell_timeout
        self.allowed_shell = None # No whitelist by default, but we use JARVIS safety checks

    def register(self, name: str, func: Callable[..., Any], aliases: Optional[List[str]] = None, help: str = ""):
        entry = {"func": func, "aliases": set(aliases or []), "help": help}
        # Names are registered with slash for consistency with JARVIS
        name_slash = name if name.startswith("/") else "/" + name
        self._registry[name_slash] = entry
        for a in aliases or []:
            a_slash = a if a.startswith("/") else "/" + a
            self._registry[a_slash] = entry

    def list_commands(self):
        seen = set()
        out = []
        for name, meta in self._registry.items():
            if id(meta["func"]) in seen: continue
            seen.add(id(meta["func"]))
            out.append((name, meta["help"]))
        return out

    def _tokenize(self, text: str) -> List[str]:
        try:
            return shlex.split(text)
        except:
            return text.split()

    def _match_known(self, tokens: List[str]):
        if not tokens: return None, None
        candidate = tokens[0]
        # Add slash if missing for matching
        if not candidate.startswith("/"): candidate = "/" + candidate
        
        if candidate in self._registry:
            return candidate, tokens[1:]
            
        # Fuzzy match
        keys = list(self._registry.keys())
        close = difflib.get_close_matches(candidate, keys, n=1, cutoff=0.6)
        if close:
            return close[0], tokens[1:]
        return None, None

    def _call_llm_parse(self, text: str) -> Dict[str, Any]:
        """Use JARVIS brain to parse natural language into structured intent."""
        prompt = f"""
Analyze the user's request and map it to a command or intent.
User Request: "{text}"

Available Command Types:
- fix: For debugging, repairing, or patching code.
- chat: For general questions or technical advice.
- forge: For creating new code, features, or systems.
- locate: For finding files or projects.
- plan: For designing a strategy.
- shell: For direct terminal commands.

Return a JSON object exactly like this:
{{
  "type": "internal" | "shell" | "chat",
  "target": "command_name_without_slash",
  "args": "string of arguments",
  "confirm": boolean
}}
"""
        response = think("", prompt, prompt_name="nave_sovereign")
        try:
            # Attempt to extract JSON from markdown or raw response
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "{" in response:
                response = response[response.find("{"):response.rfind("}")+1]
            return json.loads(response)
        except:
            # Fallback to simple routing
            text_low = text.lower()
            if any(k in text_low for k in ["fix", "broken", "bug"]): return {"type": "internal", "target": "fix", "args": text}
            if any(k in text_low for k in ["find", "locate", "search"]): return {"type": "internal", "target": "locate", "args": text.split()[-1]}
            return {"type": "chat", "args": text}

    def handle(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        if not text: return {"ok": False, "error": "empty"}

        # If it looks like a slash command, try direct match first
        tokens = self._tokenize(text)
        matched, args = self._match_known(tokens)

        if matched:
            return {"ok": True, "type": "internal", "command": matched, "args": " ".join(args)}

        # Complex or messy natural language -> LLM
        parsed = self._call_llm_parse(text)
        t = parsed.get("type")
        
        if t == "internal":
            target = parsed.get("target")
            cmd = target if target.startswith("/") else "/" + target
            return {"ok": True, "type": "internal", "command": cmd, "args": parsed.get("args", "")}
        elif t == "shell":
            return {"ok": True, "type": "shell", "command": parsed.get("target"), "confirm": parsed.get("confirm", True)}
        
        return {"ok": True, "type": "chat", "args": text}
