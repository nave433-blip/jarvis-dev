import json
from core.brain import think
from tools.shell import run
from tools.search import grep, list_files
from tools.editor import replace_in_file, read_section

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
            return run(args["command"])
    except Exception as e:
        return f"Tool Error: {e}"
    
    return "Unknown tool"

def debug_loop(issue):
    context = f"Original Issue: {issue}"

    for i in range(10): # More steps for complex reasoning
        print(f"\n--- STEP {i+1} ---")
        response = think(context, "Resolve the issue using tools if necessary.")
        
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
