import time
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.markdown import Markdown
from core.config import get_env_with_config
from tools.analytics import project_summary
import os

console = Console()

def make_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )
    layout["main"].split_row(
        Layout(name="left"),
        Layout(name="right"),
    )
    layout["left"].split_column(
        Layout(name="chat", ratio=2),
        Layout(name="logs", ratio=1),
    )
    layout["right"].split_column(
        Layout(name="stats"),
        Layout(name="focus"),
    )
    return layout

class Dashboard:
    def __init__(self):
        self.layout = make_layout()
        self.chat_history = []
        self.logs = ["System Initialized..."]
        self.focus_path = "."

    def update_header(self):
        provider = get_env_with_config("provider") or "ollama"
        self.layout["header"].update(Panel(f"JARVIS DASHBOARD | Provider: [bold cyan]{provider}[/bold cyan] | Focus: [bold yellow]{self.focus_path}[/bold yellow]", style="cyan"))

    def update_stats(self):
        summary = project_summary(self.focus_path)
        table = Table(title="Project Stats", expand=True)
        table.add_column("Metric")
        table.add_column("Value")
        table.add_row("Total Files", str(summary["total_files"]))
        table.add_row("Python Lines", str(summary["total_lines"]))
        self.layout["stats"].update(Panel(table, border_style="green"))

    def update_chat(self):
        chat_md = "\n".join([f"**User:** {q}\n**JARVIS:** {a}" for q, a in self.chat_history[-3:]])
        self.layout["chat"].update(Panel(Markdown(chat_md or "No active chat."), title="Recent Chat"))

    def update_logs(self):
        log_text = "\n".join(self.logs[-10:])
        self.layout["logs"].update(Panel(log_text, title="System Logs"))

    def update_focus(self):
        files = os.listdir(self.focus_path)[:10]
        file_list = "\n".join([f"📄 {f}" for f in files])
        self.layout["focus"].update(Panel(file_list, title="Focus Context"))

    def run(self):
        with Live(self.layout, refresh_per_second=1, screen=True):
            while True:
                self.update_header()
                self.update_stats()
                self.update_chat()
                self.update_logs()
                self.update_focus()
                time.sleep(2)
                # In a real app, this would be non-blocking and respond to events
                # For this CLI version, we'll exit on Ctrl+C (handled by Live)
