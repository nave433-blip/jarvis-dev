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
    
    # Get the directory where the JARVIS source lives
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    try:
        # Pull latest code
        console.print(f"[yellow]Pulling latest changes from GitHub in {base_dir}...[/yellow]")
        subprocess.check_call(["git", "-C", base_dir, "pull", "origin", "main"])
        
        # Re-install dependencies
        console.print("[yellow]Refreshing dependencies...[/yellow]")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", base_dir])
        
        console.print("[bold green]✅ Update successful! Please restart JARVIS.[/bold green]")
        return True
    except Exception as e:
        console.print(f"[bold red]❌ Update failed: {e}[/bold red]")
        console.print("[bold yellow]Attempting auto-rollback...[/bold yellow]")
        # Rollback via git
        subprocess.run(["git", "-C", base_dir, "reset", "--hard", "HEAD@{1}"])
        return False

def auto_update_check():
    """Check for updates silently and only prompt if found."""
    latest = check_for_updates()
    if latest:
        console.print(f"[bold green]✨ A new version of JARVIS is available: {latest} (Current: {CURRENT_VERSION})[/bold green]")
        if console.input("Would you like to upgrade now? (y/n): ").lower() == 'y':
            if apply_update():
                console.print("[bold green]Upgrade complete! Please restart JARVIS.[/bold green]")
                sys.exit(0)

def manual_upgrade():
    """Manually trigger the upgrade sequence."""
    latest = check_for_updates()
    if not latest:
        console.print("[green]JARVIS is already up to date.[/green]")
        if not console.input("Force reinstall anyway? (y/n): ").lower() == 'y':
            return
    
    apply_update()
