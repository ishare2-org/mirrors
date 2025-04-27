#!/usr/bin/env python3
import json
import os
from rich.console import Console
from rich.progress import Progress
from rich.panel import Panel
from rich.table import Table
from rich import box

console = Console()

# Configuration
FILES = ["index.gd.json", "index.od.json"]
IMAGE_TYPES = ["iol", "dynamips", "qemu"]

def print_header():
    """Display styled header"""
    console.print(Panel.fit("🔢 ID Generation & Sorting", 
                          style="bold cyan",
                          subtitle="⚡ Powered by LabHub"))

def print_step(message, emoji="🔧"):
    """Print processing step"""
    console.print(f"{emoji} [bold]{message}[/]")

def print_success(message):
    """Print success message"""
    console.print(f"✅ [bold green]{message}[/]")

def print_warning(message):
    """Print warning message"""
    console.print(f"⚠️  [bold yellow]{message}[/]")

def print_error(message):
    """Print error message"""
    console.print(f"❌ [bold red]{message}[/]")

def generate_file_list():
    """Generate complete file list with rich display"""
    print_step("Generating file list...", "📂")
    file_table = Table(show_header=False, box=box.SIMPLE)
    file_table.add_column("Files to Process", style="cyan")
    
    for file in FILES:
        file_table.add_row(f"• {file}")
    
    for img_type in IMAGE_TYPES:
        file_table.add_row(f"• index.gd.{img_type}.json")
        file_table.add_row(f"• index.od.{img_type}.json")
    
    console.print(Panel(file_table, title="📄 File List", border_style="blue"))

def process_file(file_path):
    """Process a single JSON file with error handling"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        with console.status(f"[bold]Processing {os.path.basename(file_path)}...", spinner="dots"):
            if any(key in data for key in ["QEMU", "IOL", "DYNAMIPS"]):
                process_structured_data(data)
            else:
                process_flat_data(data)
                
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
            
        return True
        
    except json.JSONDecodeError:
        print_error(f"Invalid JSON format in {file_path}")
        return False
    except Exception as e:
        print_error(f"Error processing {file_path}: {str(e)}")
        return False

def process_structured_data(data):
    """Process nested JSON structure"""
    for key in data:
        entries = data[key]
        entries.sort(key=lambda x: x['name'])
        for i, entry in enumerate(entries, start=1):
            entries[i-1] = {"id": i, **entry}

def process_flat_data(data):
    """Process flat JSON structure"""
    data.sort(key=lambda x: x['name'])
    for i, entry in enumerate(data, start=1):
        data[i-1] = {"id": i, **entry}

def main():
    print_header()
    generate_file_list()
    
    # Generate complete file list
    full_list = FILES.copy()
    for img_type in IMAGE_TYPES:
        full_list.extend([
            f"index.gd.{img_type}.json",
            f"index.od.{img_type}.json"
        ])
    
    processed_count = 0
    with Progress() as progress:
        task = progress.add_task("[cyan]Processing files...", total=len(full_list))
        
        for file_path in full_list:
            progress.update(task, advance=1, description=f"Checking {file_path}")
            
            if not os.path.exists(file_path):
                print_warning(f"Skipping missing file: {file_path}")
                continue
                
            if os.path.getsize(file_path) == 0:
                print_warning(f"Skipping empty file: {file_path}")
                continue
                
            if process_file(file_path):
                processed_count += 1
                progress.console.print(f"✨ Processed [bold]{file_path}[/]")
    
    console.print(Panel.fit(
        f"[bold green]🎉 Successfully processed {processed_count}/{len(full_list)} files![/]",
        border_style="green"
    ))

if __name__ == "__main__":
    main()