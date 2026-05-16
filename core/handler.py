import shlex
import subprocess
import difflib
import logging
import json
import os
import sys
from typing import Callable, Dict, List, Optional, Any
from core.brain import get_provider

logger = logging.getLogger("jarvis.command_handler")

class CommandError(Exception):
    pass

class CommandHandler:
    def __init__(self, shell_timeout: int = 180):
        self._registry: Dict[str, Dict[str, Any]] = {}
        self.shell_timeout = shell_timeout

    def register(self, name: str, func: Callable[..., Any], aliases: Optional[List[str]] = None, help: str = ""):
        entry = {"func": func, "aliases": set(aliases or []), "help": help}
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
        if not candidate.startswith("/"): candidate = "/" + candidate
        if candidate in self._registry:
            return candidate, tokens[1:]
        keys = list(self._registry.keys())
        close = difflib.get_close_matches(candidate, keys, n=1, cutoff=0.6)
        if close:
            return close[0], tokens[1:]
        return None, None

    def _call_llm_parse(self, text: str) -> Dict[str, Any]:
        """
        Deterministic intent parser using strict JSON schema and few-shot examples.
        """
        system_instruction = """
You are an intent parser for a command-line assistant. Your job is to parse a single user utterance into a strict JSON object only — no surrounding text, no markdown, no explanation. The JSON MUST exactly follow the schema below. If you cannot confidently parse, return the "noop" fallback form. Always use lowercase canonical command names.

JSON schema:
{
  "type": "object",
  "properties": {
    "type": { "type": "string", "enum": ["internal", "shell", "help", "noop"] },
    "target": { "type": "string" },
    "args": { "type": "array", "items": { "type": "string" } },
    "confirm": { "type": "boolean" }
  },
  "required": ["type", "target", "args", "confirm"],
  "additionalProperties": false
}

Interpretation rules:
- type: "internal" = invoke a registered internal command; "shell" = run a shell command; "help" = return CLI help/listing; "noop" = no-op.
- target: For "internal" this is the canonical command name (e.g., "fix", "forge", "locate"). For "shell" this is the exact shell string to run. For "help" and "noop", target is "".
- args: List of strings for internal commands. For shell, use [].
- confirm: true for potentially destructive operations (rm, sudo, etc.).

Few-shot examples:
User: "scan /etd drive for useful code"
Assistant: {"type":"internal","target":"locate","args":["/etd"],"confirm":false}

User: "fix broken code in n4v3r41n"
Assistant: {"type":"internal","target":"fix","args":["n4v3r41n"],"confirm":false}

User: "run git status"
Assistant: {"type":"shell","target":"git status","args":[],"confirm":false}

User: "what can you do?"
Assistant: {"type":"help","target":"","args":[],"confirm":false}
"""
        provider = get_provider()
        # Call model with deterministic settings
        response = provider.ask(f"{system_instruction}\n\nUser: \"{text}\"\nAssistant:", options={"temperature": 0, "top_p": 1})
        
        try:
            # Clean response
            res_clean = response.strip()
            if "```json" in res_clean:
                res_clean = res_clean.split("```json")[1].split("```")[0]
            elif "{" in res_clean:
                res_clean = res_clean[res_clean.find("{"):res_clean.rfind("}")+1]
            
            obj = json.loads(res_clean)
            # Basic validation
            if all(k in obj for k in ["type", "target", "args", "confirm"]):
                return obj
        except:
            pass
            
        return {"type": "noop", "target": "", "args": [], "confirm": False}

    def handle(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        if not text: return {"ok": False, "error": "empty"}

        # Try direct or fuzzy match for slash commands first
        tokens = self._tokenize(text)
        matched, args = self._match_known(tokens)
        if matched:
            return {"ok": True, "type": "internal", "command": matched, "args": " ".join(args)}

        # Deterministic LLM parse
        parsed = self._call_llm_parse(text)
        t = parsed.get("type")
        
        if t == "internal":
            target = parsed.get("target")
            cmd = target if target.startswith("/") else "/" + target
            return {"ok": True, "type": "internal", "command": cmd, "args": " ".join(parsed.get("args", []))}
        elif t == "shell":
            return {"ok": True, "type": "shell", "command": parsed.get("target"), "confirm": parsed.get("confirm", True)}
        elif t == "help":
            return {"ok": True, "type": "internal", "command": "/help", "args": ""}
        
        return {"ok": True, "type": "chat", "args": text}
