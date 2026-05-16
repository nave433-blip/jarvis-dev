# JARVIS: Local AI Coding Assistant

JARVIS is a senior software engineering assistant that runs locally on macOS, powered by Ollama. It combines voice commands, vector memory, and proactive file monitoring with a Gemini-inspired structured agent workflow.

## Features

- **Gemini-Like Agent:** Structured Research -> Strategy -> Execution loop.
- **Surgical Editing:** Precise file modifications without rewriting entire files.
- **Vector Memory:** Remembers past tasks and analyses using Ollama-powered embeddings.
- **Voice Commands:** Control Jarvis using your voice (Speech-to-Text).
- **Proactive Monitoring:** Automatically analyzes file changes in the background.
- **Safe Shell:** Integrated shell tool with built-in safety checks.

## 📦 Installation Alternatives

JARVIS is designed to be accessible from any environment. Choose the method that best fits your workflow:

### 1. Homebrew (macOS GUI)
Install the standalone Jarvis Term application via Cask:
```bash
brew install --cask https://raw.githubusercontent.com/nave433-blip/jarvis-term/master/jarvis-term.rb
```

### 2. Global Pip Install (Assistant CLI)
Install the JARVIS CLI globally on any machine with Python 3.9+:
```bash
pip install git+https://github.com/nave433-blip/jarvis-dev.git
```
*Note: This will add the `jarvis` command to your system PATH.*

### 3. One-Liner (Self-Repairing Setup)
Best for fresh macOS systems:
```bash
curl -fsSL https://raw.githubusercontent.com/nave433-blip/jarvis-dev/main/install.sh | bash
```

### 4. Linux AppImage
Download the `.AppImage` from the [Releases](https://github.com/nave433-blip/jarvis-term/releases) tab, make it executable, and run.

## Usage

Once installed, just type `jarvis` to open the interactive menu or use specific commands:

```bash
jarvis chat "How do I use vector memory?"
jarvis fix "The bug in memory/vector.py"
jarvis setup  # Reconfigure LLM providers/keys
```

## Project Rules

Custom instructions can be added to `JARVIS.md` to guide the AI's behavior.
