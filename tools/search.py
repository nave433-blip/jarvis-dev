import subprocess
import glob as python_glob
import os

def grep(pattern, path="."):
    try:
        # Simple grep-like search
        results = []
        for root, dirs, files in os.walk(path):
            if ".git" in root or "venv" in root: continue
            for file in files:
                if file.endswith(('.py', '.md', '.txt', '.cfg', '.toml')):
                    full_path = os.path.join(root, file)
                    with open(full_path, 'r', errors='ignore') as f:
                        for i, line in enumerate(f, 1):
                            if pattern in line:
                                results.append(f"{full_path}:{i}: {line.strip()}")
        return "\n".join(results[:50]) or "No matches found."
    except Exception as e:
        return f"Grep error: {e}"

def list_files(pattern="**/*"):
    files = python_glob.glob(pattern, recursive=True)
    return "\n".join([f for f in files if "venv" not in f and ".git" not in f][:100])

def system_find(name, root="/"):
    """Search for a file/directory by name across the system."""
    try:
        # We use a safe find command limited to a depth or result count to prevent hanging
        cmd = f"find {root} -name '*{name}*' -not -path '*/.*' 2>/dev/null | head -n 20"
        return subprocess.getoutput(cmd)
    except Exception as e:
        return f"System search error: {e}"
