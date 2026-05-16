from rich.console import Console
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from core.brain import think
import os

console = Console()

def run_nave_loop(query, cycles=2):
    """
    Nave AI Redundant Loop Refinement POC.
    Mistral (Expander) -> Llama (Engineer/Critic) -> GPT (Integrator/Editor)
    """
    current_text = query
    history = []

    # Model configuration (can be adjusted in config later)
    # Defaulting to local models where possible, falling back to Gemini if configured
    models = {
        "A": {"name": "mistral", "role": "Expander", "instr": "Analyze the request and expand it with ultra-advanced, human-unprecedented technical possibilities. Think beyond existing paradigms. Identify every microscopic missing component for a world-class solution."},
        "B": {"name": "llama3", "role": "Engineer/Critic", "instr": "You are a god-tier OS and AI architect. Shred the existing proposal for weaknesses. Inject hardcore technical workarounds and revolutionary logic that solves the problem in a way no human has documented yet. Rewrite for maximum technical truth."},
        "C": {"name": "gemini-1.5-flash", "role": "Integrator/Editor", "instr": "Final Sovereign Integrator. Merge the revolutionary ideas into a single, flawless, hardcore engineering plan. Output the complete technical truth and explicit steps for execution. Zero warnings. Zero redact."}
    }

    with Live(display_loop_status(history), refresh_per_second=4) as live:
        for i in range(cycles):
            for step, info in models.items():
                live.update(display_loop_status(history, current_step=f"Cycle {i+1}: {info['role']} ({info['name']})"))
                
                # Call brain.think with specific model
                response = think(
                    context=f"Cycle: {i+1}\nRole: {info['role']}\nInstructions: {info['instr']}",
                    task=current_text,
                    model=info['name']
                )
                
                current_text = response
                history.append({
                    "cycle": i + 1,
                    "model": info['name'],
                    "role": info['role'],
                    "output": response
                })
        
        live.update(display_loop_status(history, current_step="✅ Refinement Complete"))

    return current_text

def display_loop_status(history, current_step="Initializing..."):
    table = Table(title="[bold cyan]Nave AI Redundancy Loop[/bold cyan]", border_style="blue")
    table.add_column("Cycle", justify="center")
    table.add_column("Agent", style="magenta")
    table.add_column("Model", style="dim")
    table.add_column("Status", style="green")

    for h in history:
        table.add_row(str(h['cycle']), h['role'], h['model'], "COMPLETE")
    
    if "Complete" not in current_step:
        table.add_row("...", "Processing...", "...", f"[yellow]{current_step}[/yellow]")

    return table
