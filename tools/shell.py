import subprocess

def run(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=180)
        output = result.stdout
        error = result.stderr
        return {
            "stdout": output,
            "stderr": error,
            "return_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out after 3 minutes (180s) of no output."}
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
