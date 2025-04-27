#!/usr/bin/env python3
import json
from rich.console import Console
from rich.progress import Progress
from rich.panel import Panel
from rich import box

console = Console()

# Configuration
OLD_BASE_URL = "labhub.eu.org/api/raw/?path=/"
NEW_BASE_URL = "drive.labhub.eu.org/0:/"
INDEX_FILES = ["index.od.iol.json", "index.od.qemu.json", 
              "index.od.dynamips.json", "index.od.json"]

def print_header():
    """Display styled header"""
    console.print(Panel.fit("🛠️  URL Mirror Generation Tool",
                        style="bold cyan",
                        subtitle="⚡ Powered by LabHub"))

def print_step(message, emoji="🔧"):
    """Print processing step"""
    console.print(f"{emoji} [bold]{message}[/]")

def print_success(message):
    """Print success message"""
    console.print(f"✅ [bold green]{message}[/]")

def print_error(message):
    """Print error message"""
    console.print(f"❌ [bold red]{message}[/]")

def verify_index_files():
    """Validate JSON index files with progress"""
    print_step("Validating index files...", "🔍")
    
    with Progress(transient=True) as progress:
        task = progress.add_task("[cyan]Checking files...", total=len(INDEX_FILES))
        
        for index_file in INDEX_FILES:
            progress.update(task, advance=1, description=f"Checking {index_file}")
            
            try:
                with open(index_file, "r") as f:
                    json.load(f)
                progress.console.print(f"📄 [green]Validated[/] {index_file}")
            except FileNotFoundError:
                print_error(f"File {index_file} not found")
                return False
            except json.JSONDecodeError as e:
                print_error(f"Invalid JSON in {index_file}: {str(e)}")
                return False
                
    print_success("All index files validated!")
    return True

def update_urls_in_data(data):
    """Recursively update URLs in data structure"""
    if isinstance(data, dict):
        for key, value in data.items():
            if key == "url" and isinstance(value, str):
                data[key] = value.replace(OLD_BASE_URL, NEW_BASE_URL)
            else:
                update_urls_in_data(value)
    elif isinstance(data, list):
        for item in data:
            update_urls_in_data(item)

def migrate_urls():
    """Main mirror url generation function"""
    print_step("Starting mirror URL generation...", "🔄")
    
    with Progress() as progress:
        task = progress.add_task("[cyan]Processing files...", total=len(INDEX_FILES))
        
        for index_file in INDEX_FILES:
            progress.update(task, advance=1, description=f"Processing {index_file}")
            
            try:
                # Load and process data
                with open(index_file, "r") as f:
                    data = json.load(f)
                
                progress.console.print(f"🔗 Updating URLs in {index_file}")
                update_urls_in_data(data)
                
                # Save new file
                new_filename = index_file.replace("index.od", "index.gd")
                with open(new_filename, "w") as f:
                    json.dump(data, f, indent=4)
                
                progress.console.print(f"💾 Saved mirror file: [bold]{new_filename}[/]")
                
            except Exception as e:
                print_error(f"Failed processing {index_file}: {str(e)}")
                return False
    
    print_success("URL mirror generation completed!")

    return True

def main():
    print_header()
    
    if not verify_index_files():
        return
    
    if not migrate_urls():
        print_error("Mirror URL generation failed. Check the logs.")
        return
    
    console.print(Panel.fit("[bold green]🎉 All operations completed successfully![/]", 
                        border_style="green"))

if __name__ == "__main__":
    main()