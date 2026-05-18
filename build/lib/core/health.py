import os
import subprocess
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

REPOS = {
    "wikiproxy": {"path": "~/wikiproxy", "check": "python3.12 -m wikiproxy --help", "repair": "python3.12 -m pip install -e ."},
}

def check_system_health():
    """Check health of JARVIS, AI providers, and related engineering repos."""
    results = []
    
    from core.config import load_config
    from core.services import validate_provider_connection, get_api_key
    
    config = load_config()
    providers_to_check = ["ollama", "openai", "gemini"] # Core providers
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        # 1. Check AI Providers
        progress.add_task(description="Verifying AI Provider connectivity...", total=None)
        for p in providers_to_check:
            extra = {}
            if p == "ollama":
                extra["host"] = config.get("ollama_host")
            else:
                key = get_api_key(p)
                if key: extra["key"] = key
            
            v = validate_provider_connection(p, extra=extra)
            if v.get("ok"):
                results.append({"name": f"Provider: {p.upper()}", "status": "ONLINE", "type": "provider", "provider": p, "error": None})
            else:
                results.append({"name": f"Provider: {p.upper()}", "status": "ERROR", "type": "provider", "provider": p, "error": v.get("error") or "Not configured"})

        # 2. Check Repositories
        if REPOS:
            progress.add_task(description="Scanning workspace for repository issues...", total=None)
            for name, info in REPOS.items():
                path = os.path.expanduser(info["path"])
                if not os.path.exists(path):
                    results.append({"name": name, "status": "MISSING", "type": "repo", "error": "Path not found"})
                    continue
                
                try:
                    cmd = info["check"]
                    res = subprocess.run(cmd, shell=True, cwd=path, capture_output=True, text=True, timeout=30.0)
                    if res.returncode == 0:
                        results.append({"name": name, "status": "ONLINE", "type": "repo", "error": None})
                    else:
                        error_summary = res.stderr.splitlines()[-1] if res.stderr else "Unknown error"
                        results.append({"name": name, "status": "ERROR", "type": "repo", "error": error_summary})
                except Exception as e:
                    results.append({"name": name, "status": "CRITICAL", "type": "repo", "error": str(e)})

    return results

def display_health_report(results):
    if not results:
        return False

    table = Table(title="JARVIS System Health Report", show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Diagnostics / Action Required", style="dim")
    
    errors_found = False
    for res in results:
        status_style = "green" if res["status"] == "ONLINE" else "red"
        if res["status"] != "ONLINE":
            errors_found = True
        
        table.add_row(
            res["name"],
            f"[{status_style}]{res['status']}[/]",
            res["error"] or "[grey]Operational[/]"
        )
    
    console.print(table)
    return errors_found

def auto_repair_workspace(results):
    """Attempt to fix common issues in the workspace and providers."""
    from core.services import repair_ollama
    from core.startup import _interactive_connect

    for res in results:
        if res["status"] == "ERROR" or res["status"] == "MISSING":
            console.print(f"[yellow]Attempting to repair {res['name']}...[/yellow]")
            
            if res.get("type") == "provider":
                pname = res.get("provider")
                if pname == "ollama":
                    rep = repair_ollama()
                    if rep.get("fixed"):
                        console.print(f"[green]✅ {res['name']} repaired automatically.[/green]")
                    else:
                        console.print(f"[yellow]Could not auto-repair {res['name']}. Manual setup required.[/yellow]")
                        _interactive_connect(pname)
                else:
                    # For cloud providers, prompt for key
                    _interactive_connect(pname)
            
            elif res.get("type") == "repo":
                repo_name = res["name"]
                if repo_name in REPOS:
                    repair_cmd = REPOS[repo_name].get("repair")
                    if repair_cmd:
                        path = os.path.expanduser(REPOS[repo_name]["path"])
                        subprocess.run(repair_cmd, shell=True, cwd=path)
                    
                    # Re-verify
                    path = os.path.expanduser(REPOS[repo_name]["path"])
                    cmd = REPOS[repo_name]["check"]
                    final = subprocess.run(cmd, shell=True, cwd=path, capture_output=True)
                    if final.returncode == 0:
                        console.print(f"[green]✅ {res['name']} repaired successfully![/green]")
                    else:
                        console.print(f"[red]❌ Failed to repair {res['name']}.[/red]")

def update_all_repos():
    """Pull latest changes for all repos and reinstall."""
    for name, info in REPOS.items():
        path = os.path.expanduser(info["path"])
        if os.path.exists(os.path.join(path, ".git")):
            console.print(f"[bold cyan]Updating {name}...[/bold cyan]")
            subprocess.run(["git", "pull"], cwd=path)
        
        repair_cmd = info.get("repair")
        if repair_cmd:
            console.print(f"[dim]Reinstalling {name}...[/dim]")
            subprocess.run(repair_cmd, shell=True, cwd=path)
    console.print("[bold green]✅ All repositories synchronized and reinstalled.[/bold green]")
