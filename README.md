# JARVIS: Local AI Coding Assistant

JARVIS is a senior software engineering assistant that runs locally on macOS, powered by Ollama. It combines voice commands, vector memory, and proactive file monitoring with a Gemini-inspired structured agent workflow.

## Features

- **Gemini-Like Agent:** Structured Research -> Strategy -> Execution loop.
- **Surgical Editing:** Precise file modifications without rewriting entire files.
- **Vector Memory:** Remembers past tasks and analyses using Ollama-powered embeddings.
- **Voice Commands:** Control Jarvis using your voice (Speech-to-Text).
- **Proactive Monitoring:** Automatically analyzes file changes in the background.
- **Safe Shell:** Integrated shell tool with built-in safety checks.

## Installation

### 🚀 Quick Install (Global)
Install JARVIS globally and launch it from anywhere by simply typing `jarvis`:

```bash
curl -fsSL https://raw.githubusercontent.com/nave433-blip/jarvis-dev/main/install.sh | bash
```

### 📦 Manual Install
1. **Requirements:** Python 3.9+, [Ollama](https://ollama.com/), PortAudio (`brew install portaudio`).
2. **Setup:**
   ```bash
   git clone https://github.com/nave433-blip/jarvis-dev.git
   cd jarvis-dev
   make install
   ```

## Usage

Once installed, just type `jarvis` to open the interactive menu or use specific commands:

```bash
jarvis chat "How do I use vector memory?"
jarvis fix "The bug in memory/vector.py"
jarvis setup  # Reconfigure LLM providers/keys
```

## Project Rules

Custom instructions can be added to `JARVIS.md` to guide the AI's behavior.
