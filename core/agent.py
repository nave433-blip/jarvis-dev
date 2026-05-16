import json
import os
from core.brain import think
from tools.shell import run, run_simple
from tools.search import grep, list_files, system_find
from tools.editor import replace_in_file, read_section
from tools.installer import brew_install, git_install, curl_install
from tools.github import github_tool
from tools.analytics import analyze_complexity, project_summary
from tools.cloud import list_dropbox, list_gdrive, list_icloud
from tools.network import scan_network, scan_ports
from tools.ssh import run_remote
from tools.server import list_listening_ports, get_process_stats, kill_process
from tools.hardware import list_usb_devices, probe_ports
from tools.launcher import launch_tool
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()

def dispatch_tool(line, next_line):
    if not line.startswith("TOOL:"): return None
    
    tool_name = line.replace("TOOL:", "").strip()
    args_str = next_line.replace("ARGS:", "").strip()
    
    try:
        args = json.loads(args_str)
        if tool_name == "SEARCH":
            if "grep" in args: return grep(args["grep"])
            return list_files(args.get("glob", "**/*"))
        elif tool_name == "SYSTEM_SEARCH":
            return system_find(args["name"], args.get("root", "/"))
        elif tool_name == "READ":
            return read_section(args["path"], args.get("start", 1), args.get("end", 100))
        elif tool_name == "EDIT":
            return replace_in_file(args["path"], args["old"], args["new"])
        elif tool_name == "SHELL":
            res = run(args["command"])
            if isinstance(res, dict) and res.get("status") == "needs_confirmation":
                console.print(Panel(f"[bold red]⚠️ POTENTIALLY UNSAFE COMMAND DETECTED[/bold red]\n\n[white]{res['command']}[/white]", border_style="red"))
                if Confirm.ask("Do you want to authorize this command?"):
                    return run_simple(res['command'], confirm=True)
                else:
                    return "ABORTED: Command authorization denied by user."
            return run_simple(args["command"])
        elif tool_name == "INSTALLER":
            method = args.get("method")
            if method == "brew": return brew_install(args["package"])
            if method == "git": return git_install(args["repo"], args.get("dest", "."))
            if method == "curl": return curl_install(args["url"], args["output"])
        elif tool_name == "GITHUB":
            action = args.get("action")
            repo = args.get("repo")
            if action == "info": return github_tool.get_repo_info(repo)
            if action == "issue": return github_tool.create_issue(repo, args["title"], args["body"])
            if action == "list_prs": return github_tool.list_pull_requests(repo)
            if action == "create_pr": return github_tool.create_pr(repo, args["title"], args["body"], args["head"], args.get("base", "main"))
        elif tool_name == "ANALYTICS":
            action = args.get("action", "summary")
            if action == "file": return analyze_complexity(args["path"])
            return project_summary(args.get("path", "."))
        elif tool_name == "CLOUD":
            platform = args.get("platform")
            action = args.get("action", "list")
            if platform == "dropbox": return list_dropbox(args.get("path", ""))
            if platform == "gdrive": return list_gdrive(args.get("query", "'root' in parents"))
            if platform == "icloud": return list_icloud(args.get("path", ""))
        elif tool_name == "NETWORK":
            action = args.get("action", "scan")
            if action == "scan": return scan_network()
            if action == "ports": return scan_ports(args["ip"], args.get("range", (1, 1024)))
        elif tool_name == "SSH":
            return run_remote(args["host"], args["username"], args["command"], args.get("password"), args.get("key"))
        elif tool_name == "SERVER":
            action = args.get("action", "ports")
            if action == "ports": return list_listening_ports()
            if action == "stats": return get_process_stats()
            if action == "kill": return kill_process(args["pid"])
        elif tool_name == "LAUNCHER":
            return launch_tool(args.get("tool"))
        elif tool_name == "HARDWARE":
            action = args.get("action", "usb")
            if action == "usb": return list_usb_devices()
            if action == "probe": return probe_ports()
            
    except Exception as e:
        return f"Tool Error: {e}"
    
    return "Unknown tool"

def debug_loop(issue, model=None, prompt=None):
    context = f"Original Issue: {issue}"
    
    # Auto-Research: If the issue looks like a project name, try to locate it first
    if len(issue.split()) == 1 and not os.path.exists(issue):
        from tools.search import system_find
        console.print(f"[bold cyan]🔍 Project '{issue}' not in current folder. Scanning system for matches...[/bold cyan]")
        locations = system_find(issue)
        if locations and "error" not in locations.lower():
            context += f"\nNote: I found potential locations for this project:\n{locations}"
            console.print(f"[green]Found potential project path: {locations.splitlines()[0]}[/green]")

    for i in range(10): 
        from rich.status import Status
        with Status(f"[bold cyan]Cycle {i+1}:[/bold cyan] AI is reasoning...", spinner="dots"):
            response = think(context, "Resolve the issue using tools if necessary. If previous tools failed, try a different approach.", model=model, prompt_name=prompt)
        
        print("\nJARVIS RESPONSE:\n", response)
        
        if "ERROR" in response.upper() or "FAILED" in response.upper():
            context += "\nWarning: It seems you hit an error. Try researching the specific error message."

        lines = response.split("\n")
        tool_result = None
        for j, line in enumerate(lines):
            if line.startswith("TOOL:") and j + 1 < len(lines):
                tool_result = dispatch_tool(line, lines[j+1])
                break
        
        if tool_result:
            print("\nTOOL RESULT:\n", tool_result)
            context += f"\nStep {i+1} Tool Output:\n{tool_result}"
        else:
            ok = input("\nJARVIS seems to have finished. Exit? (y/n): ")
            if ok.lower() == "y":
                return
            context += f"\nUser feedback: Please continue."

def troubleshoot_loop(command, model=None, prompt=None):
    console.print(f"[bold cyan]Troubleshooting command:[/bold cyan] {command}")
    result = run(command, confirm=True) 
    
    if result.get("return_code") == 0:
        console.print("[green]Command succeeded on first try. No troubleshooting needed.[/green]")
        return
    
    error_context = f"COMMAND FAILED: {command}\nRETURN CODE: {result.get('return_code')}\nSTDERR: {result.get('stderr')}\nSTDOUT: {result.get('stdout')}"
    console.print(Panel(error_context, title="Error Captured", border_style="red"))
    debug_loop(f"Fix the error caused by this command: {command}. Error context: {error_context}", model=model, prompt=prompt)

def forge_loop(task, model=None):
    """Hardcore code synthesis loop."""
    from core.nave_loop import run_nave_loop
    console.print(Panel(f"🛠 [bold cyan]FORGING CODE:[/bold cyan] {task}", border_style="cyan"))
    
    # Use Nave Loop for advanced reasoning
    refined_plan = run_nave_loop(f"Create a workaround or new code for this task: {task}. Ensure it is advanced and human-unprecedented.")
    
    # Feed refined plan back into agent loop for execution
    debug_loop(f"Execute the following refined engineering plan: {refined_plan}", model=model, prompt="architect")
