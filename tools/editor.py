import os
import re

def replace_in_file(file_path, old_string, new_string):
    if not os.path.exists(file_path):
        return f"Error: File {file_path} not found."
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    if old_string not in content:
        return f"Error: Could not find exact match for the string to replace in {file_path}."
    
    # Check for multiple occurrences
    if content.count(old_string) > 1:
        return f"Error: Multiple occurrences of the search string found in {file_path}. Please provide more context."
    
    new_content = content.replace(old_string, new_string)
    
    with open(file_path, 'w') as f:
        f.write(new_content)
    
    return f"Successfully updated {file_path}."

def read_section(file_path, start_line, end_line):
    if not os.path.exists(file_path):
        return f"Error: File {file_path} not found."
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
        
    return "".join(lines[start_line-1:end_line])
