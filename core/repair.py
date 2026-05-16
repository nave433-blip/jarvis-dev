import sys
import traceback
import os
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()

def self_repair_hook(exctype, value, tb):
    """Global exception hook for JARVIS self-repair and reporting."""
    # To avoid recursion if the repair engine itself fails
    sys.excepthook = sys.__excepthook__
    
    error_msg = "".join(traceback.format_exception(exctype, value, tb))
    console.print("\n[bold red]⚠️ JARVIS CRITICAL FAILURE DETECTED[/bold red]")
    console.print(Panel(error_msg, title="Traceback", border_style="red"))
    
    # Extract the failing file path
    last_trace = traceback.extract_tb(tb)[-1]
    failing_file = last_trace.filename
    line_no = last_trace.lineno
    
    console.print(f"\n[bold yellow]Failing Component:[/bold yellow] {failing_file} (Line {line_no})")
    
    if Confirm.ask("\nWould you like JARVIS to attempt an autonomous self-repair?"):
        from core.brain import think
        from tools.editor import replace_in_file
        
        with open(failing_file, 'r') as f:
            source_code = f.read()
            
        repair_prompt = f"""
        I have crashed with the following error:
        {error_msg}
        
        The failing file is: {failing_file}
        
        Here is the source code of that file:
        {source_code}
        
        Your task is to provide a fix using the EDIT tool.
        """
        
        console.print("[bold blue]Analyzing crash and generating patch...[/bold blue]")
        response = think("", repair_prompt)
        
        # Look for TOOL: EDIT in response
        if "TOOL: EDIT" in response:
            console.print("[green]Self-repair patch generated! Applying...[/green]")
            # Simplified tool parsing for emergency repair
            lines = response.split("\n")
            for i, line in enumerate(lines):
                if "TOOL: EDIT" in line and i+1 < len(lines):
                    import json
                    args = json.loads(lines[i+1].replace("ARGS:", "").strip())
                    res = replace_in_file(args["path"], args["old"], args["new"])
                    console.print(f"[bold green]{res}[/bold green]")
                    console.print("\n[bold blue]Please restart JARVIS to verify the fix.[/bold blue]")
                    return
        else:
            console.print("[red]Could not determine an automated fix.[/red]")

    if Confirm.ask("\nWould you like to report this error log to the GitHub repository?"):
        from tools.github import github_tool
        from core.update import CURRENT_VERSION
        
        title = f"Crash Report: {exctype.__name__} in {os.path.basename(failing_file)}"
        body = f"""
        ### System Info
        - OS: {sys.platform}
        - Version: {CURRENT_VERSION}
        - File: {failing_file}
        
        ### Traceback
        ```python
        {error_msg}
        ```
        """
        console.print("[bold blue]Opening GitHub issue...[/bold blue]")
        res = github_tool.create_issue("nave433-blip/jarvis-dev", title, body)
        if "Error" not in str(res):
            console.print(f"[green]Issue successfully created: {res.get('html_url')}[/green]")
        else:
            console.print(f"[red]Failed to report issue: {res}[/red]")

def init_repair_engine():
    sys.excepthook = self_repair_hook
