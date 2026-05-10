import typer
from core.brain import think
from core.agent import debug_loop
from voice.voice import run_voice
from watcher.monitor import start_monitor

app = typer.Typer()

@app.command()
def chat(q: str):
    print("\nJARVIS:\n", think("", q))

@app.command()
def fix(issue: str):
    debug_loop(issue)

@app.command()
def voice():
    run_voice()

@app.command()
def watch():
    start_monitor()

if __name__ == "__main__":
    app()
