import sys
import subprocess
import importlib.util
import shutil
from rich.console import Console

console = Console()

PYTHON_DEPS = {
    "typer": "typer",
    "rich": "rich",
    "requests": "requests",
    "watchdog": "watchdog",
    "sounddevice": "sounddevice",
    "scipy": "scipy",
    "numpy": "numpy",
    "sentence-transformers": "sentence_transformers",
    "faiss-cpu": "faiss",
    "SpeechRecognition": "speech_recognition",
    "prompt_toolkit": "prompt_toolkit",
    "Pillow": "PIL"
}

def check_python_deps():
    missing = []
    for pkg, imp in PYTHON_DEPS.items():
        if importlib.util.find_spec(imp) is None:
            missing.append(pkg)
    
    if missing:
        console.print(f"[yellow]Missing Python dependencies: {', '.join(missing)}[/yellow]")
        console.print("[bold blue]Installing missing packages automatically...[/bold blue]")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            console.print("[green]All Python dependencies installed successfully![/green]")
            return True
        except Exception as e:
            console.print(f"[red]Failed to install dependencies: {e}[/red]")
            return False
    return True

def check_system_deps():
    # Check for portaudio on macOS (required for sounddevice/voice)
    if sys.platform == "darwin":
        if not shutil.which("brew"):
            console.print("[yellow]Warning: Homebrew not found. System dependency checks skipped.[/yellow]")
            return True
        
        # Check for portaudio
        res = subprocess.run(["brew", "list", "portaudio"], capture_output=True)
        if res.returncode != 0:
            console.print("[yellow]System dependency 'portaudio' is missing (required for voice).[/yellow]")
            if console.input("Would you like to install it via Homebrew now? (y/n): ").lower() == 'y':
                console.print("[bold blue]Installing portaudio...[/bold blue]")
                subprocess.run(["brew", "install", "portaudio"])
                console.print("[green]portaudio installed![/green]")
    return True

def ensure_all():
    """Run all dependency checks."""
    p_ok = check_python_deps()
    s_ok = check_system_deps()
    return p_ok and s_ok
