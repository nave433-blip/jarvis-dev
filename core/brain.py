import requests
import os
from memory.vector import add, search

OLLAMA_URL = "http://localhost:11434/api/generate"

def get_project_instructions():
    if os.path.exists("JARVIS.md"):
        with open("JARVIS.md", "r") as f:
            return f.read()
    return ""

def ask(prompt):
    try:
        r = requests.post(OLLAMA_URL, json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        })
        r.raise_for_status()
        return r.json()["response"]
    except Exception as e:
        return f"Error connecting to Ollama: {e}"

def think(context, task):
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

Project Rules:
{project_rules}

Past relevant memories:
{memory_context}

Current Context:
{context}

Task:
{task}

To use a tool, return:
TOOL: <NAME>
ARGS: <JSON_ARGS>

Otherwise, return:
- diagnosis
- steps
- final thoughts
"""
    response = ask(prompt)
    if not response.startswith("Error"):
        add(f"Task: {task} | Response: {response[:200]}...")
    return response
