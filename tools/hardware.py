import subprocess
import sys
from rich.console import Console
from rich.table import Table

console = Console()

def list_usb_devices():
    """List all USB devices currently connected to the computer."""
    if sys.platform == "darwin":
        # macOS specific
        try:
            cmd = "system_profiler SPUSBDataType"
            res = subprocess.getoutput(cmd)
            return res
        except Exception as e:
            return f"Error scanning USB: {e}"
    elif sys.platform == "linux":
        # Linux specific
        try:
            cmd = "lsusb"
            res = subprocess.getoutput(cmd)
            return res
        except Exception as e:
            return f"Error scanning USB: {e}"
    else:
        return "Unsupported platform for hardware probing."

def probe_ports():
    """General hardware port probe."""
    if sys.platform == "darwin":
        try:
            # Get a list of all hardware data types
            cmd = "system_profiler -listDataTypes"
            types = subprocess.getoutput(cmd)
            return types
        except Exception as e:
            return f"Error probing hardware: {e}"
    return "Unsupported platform for general probing."

def get_hardware_summary():
    table = Table(title="Hardware Port Summary", border_style="cyan")
    table.add_column("Type", style="cyan")
    table.add_column("Status", style="green")
    
    # Check USB
    usb = list_usb_devices()
    usb_count = usb.count("Product ID:") if "Product ID:" in usb else 0
    table.add_row("USB Devices", f"{usb_count} detected")
    
    # Other ports check could go here
    
    return table
