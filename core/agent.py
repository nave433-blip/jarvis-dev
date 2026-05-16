import json
from core.brain import think
from tools.shell import run, run_simple
from tools.search import grep, list_files
from tools.editor import replace_in_file, read_section
from tools.installer import brew_install, git_install, curl_install
from tools.github import github_tool
from tools.analytics import analyze_complexity, project_summary
from rich.console import Console
from rich.panel import Panel

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
        elif tool_name == "READ":
            return read_section(args["path"], args.get("start", 1), args.get("end", 100))
        elif tool_name == "EDIT":
            return replace_in_file(args["path"], args["old"], args["new"])
        elif tool_name == "SHELL":
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
            
    except Exception as e:
        return f"Tool Error: {e}"
    
    return "Unknown tool"

def debug_loop(issue, model=None):
    context = f"Original Issue: {issue}"

    for i in range(10): # More steps for complex reasoning
        print(f"\n--- STEP {i+1} ---")
        response = think(context, "Resolve the issue using tools if necessary.", model=model)
        
        print("\nJARVIS RESPONSE:\n", response)
        
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
            # If no tool was used, assume JARVIS is done or giving final answer
            ok = input("\nJARVIS seems to have finished. Exit? (y/n): ")
            if ok.lower() == "y":
                return
            context += f"\nUser feedback: Please continue."

def troubleshoot_loop(command, model=None):
    console.print(f"[bold blue]Troubleshooting command:[/bold blue] {command}")
    
    # Execute the failing command
    result = run(command)
    
    if result.get("return_code") == 0:
        console.print("[green]Command succeeded on first try. No troubleshooting needed.[/green]")
        return
    
    error_context = f"""
    COMMAND FAILED: {command}
    RETURN CODE: {result.get('return_code')}
    STDERR: {result.get('stderr')}
    STDOUT: {result.get('stdout')}
    """
    
    console.print(Panel(error_context, title="Error Captured", border_style="red"))
    
    # Pass to the debug loop for fixing
    debug_loop(f"Fix the error caused by this command: {command}. Error context: {error_context}", model=model)
