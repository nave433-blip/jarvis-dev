import subprocess

SAFE = ["ls", "cat", "echo", "git", "python", "cargo", "mkdir", "touch", "mv", "cp", "grep", "find", "rm", "cd", "brew", "curl"]

def run(cmd):
    if not any(cmd.startswith(x) for x in SAFE):
        return "BLOCKED: unsafe command"

    return subprocess.getoutput(cmd)