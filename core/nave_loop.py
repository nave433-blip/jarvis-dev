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
        "A": {"name": "mistral", "role": "Expander", "instr": "Take the idea below and expand it with more technical detail and possibilities. Identify missing components. Do not remove anything; only add and clarify."},
        "B": {"name": "llama3", "role": "Engineer/Critic", "instr": "You are an OS and AI engineer. Identify weaknesses or contradictions in the text below. Propose better architectures or algorithms. Rewrite into a more coherent technical proposal."},
        "C": {"name": "gemini-1.5-flash", "role": "Integrator/Editor", "instr": "You are the final integrator. Merge all good ideas from the text below. Remove repetition. Output a single, clear, step-by-step specification or plan."}
    }

    with Live(display_loop_status(history), refresh_per_second=4) as live:
        for i in range(cycles):
            for step, info in models.items():
                live.update(display_loop_status(history, current_step=f"Cycle {i+1}: {info['role']} ({info['name']})"))
                
                # Call brain.think with specific model
                response = think(
                    context=f"Cycle: {i+1}\nRole: {info['role']}\nInstructions: {info['instr']}",
                    query=current_text,
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
