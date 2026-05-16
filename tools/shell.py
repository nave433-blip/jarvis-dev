import subprocess

SAFE = ["ls", "cat", "echo", "git", "python", "cargo", "mkdir", "touch", "mv", "cp", "grep", "find", "rm", "cd", "brew", "curl", "make", "pip", "npm", "node"]

def run(cmd):
    if not any(cmd.startswith(x) for x in SAFE):
        return "BLOCKED: unsafe command"

    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        output = result.stdout
        error = result.stderr
        return {
            "stdout": output,
            "stderr": error,
            "return_code": result.returncode
        }
    except Exception as e:
        return {"error": str(e)}

def run_simple(cmd):
    """Legacy wrapper for simple output."""
    res = run(cmd)
    if isinstance(res, dict):
        if res.get("return_code") == 0:
            return res.get("stdout") or "Success (No output)"
        return f"Error ({res.get('return_code')}): {res.get('stderr')}"
    return res
