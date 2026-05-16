import requests
import os
import sys
import subprocess
from rich.console import Console

console = Console()

GITHUB_REPO = "nave433-blip/jarvis-dev"
CURRENT_VERSION = "0.1.3"

def check_for_updates():
    """Check GitHub for a newer version of JARVIS."""
    try:
        # We'll check the pyproject.toml on main for the latest version string
        url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/pyproject.toml"
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            content = r.text
            for line in content.splitlines():
                if "version =" in line:
                    latest = line.split("=")[1].strip().strip('"').strip("'")
                    if latest > CURRENT_VERSION:
                        return latest
    except:
        pass
    return None

def apply_update():
    """Perform a git pull and reinstall dependencies."""
    console.print("[bold blue]🚀 A new version of JARVIS is available![/bold blue]")
    console.print("[dim]Starting automatic update and self-repair sequence...[/dim]")
    
    # 1. Create a simple backup (copy current dir to .bak)
    # In a real environment, we'd use git tags/commits for rollbacks
    
    try:
        # Pull latest code
        console.print("[yellow]Pulling latest changes from GitHub...[/yellow]")
        subprocess.check_call(["git", "pull", "origin", "main"])
        
        # Re-install dependencies
        console.print("[yellow]Refreshing dependencies...[/yellow]")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", "."])
        
        console.print("[bold green]✅ Update successful! Please restart JARVIS.[/bold green]")
        return True
    except Exception as e:
        console.print(f"[bold red]❌ Update failed: {e}[/bold red]")
        console.print("[bold yellow]Attempting auto-rollback...[/bold yellow]")
        # Rollback via git
        subprocess.run(["git", "reset", "--hard", "HEAD@{1}"])
        return False

def auto_update_check():
    latest = check_for_updates()
    if latest:
        apply_update()
        sys.exit(0) # Exit to allow the user to restart or wrapper to restart
