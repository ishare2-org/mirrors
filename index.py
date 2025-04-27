#!/usr/bin/env python3
import json
import shutil
import subprocess
import os
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn
from rich.table import Table
from rich import box

# Initialize rich console
console = Console()

# Configuration
BASE_DIR = "./labhub-mock/"
SCRIPTS_DIR = "./scripts/"
IMAGE_TYPES = ["IOL", "QEMU", "DYNAMIPS"]
INDEX_SUFFIXES = {
    "IOL": "bin",
    "QEMU": "",
    "DYNAMIPS": ""
}

def print_header():
    """Print beautiful header"""
    console.print(Panel.fit("🚀 LabHub Repository Indexer",
                        style="bold cyan on black", 
                        subtitle="⚡ Powered by LabHub"))

def print_step(message, emoji="🔷", style="bold blue"):
    """Print a processing step with emoji"""
    console.print(f"{emoji} [bold]{message}[/]", style=style)

def print_success(message):
    """Print success message with emoji"""
    console.print(f"✅ [bold green]{message}[/]")

def print_error(message):
    """Print error message with emoji"""
    console.print(f"❌ [bold red]{message}[/]")

def print_directory_tree():
    """Display directory structure with ASCII art"""
    tree = Table.grid(padding=1)
    tree.add_column("Structure", style="cyan")
    tree.add_row("📂 labhub-repo/")
    tree.add_row("└── 📂 addons/")
    for img_type in IMAGE_TYPES:
        branch = "    ├── 📂 " if img_type != IMAGE_TYPES[-1] else "    └── 📂 "
        tree.add_row(f"{branch}{img_type.lower()}/")
        if img_type == "IOL":
            tree.add_row("    │   └── 📂 bin/")
    console.print(Panel(tree, title="📁 Expected Directory Structure", border_style="yellow"))

def validate_directory_structure():
    """Validate the required directory structure"""
    print_step("Validating directory structure...", "🔍")
    
    if not os.path.exists(BASE_DIR):
        print_error(f"Base directory {BASE_DIR} not found!")
        console.print("\n💡 [italic]Did you forget to mount the repository?[/]")
        exit(1)

    missing_dirs = []
    for img_type in IMAGE_TYPES:
        path = os.path.join(BASE_DIR, "addons", img_type.lower(), INDEX_SUFFIXES[img_type])
        if not os.path.exists(path):
            missing_dirs.append(path)

    if missing_dirs:
        print_error("Directory structure mismatch!")
        console.print("\n🔥 [bold]Missing directories:[/]")
        for d in missing_dirs:
            console.print(f"  • [red]{d}[/]")
        print_directory_tree()
        exit(1)

    print_success("Directory structure validated!")

def copy_index_scripts():
    """Copy index scripts with progress tracking"""
    print_step("Deploying indexing scripts...", "📂")
    
    with Progress(SpinnerColumn(), transient=True) as progress:
        task = progress.add_task("[cyan]Copying files...", total=len(IMAGE_TYPES))
        
        for img_type in IMAGE_TYPES:
            progress.update(task, advance=1, description=f"Copying {img_type} script")
            src = os.path.join(SCRIPTS_DIR, img_type.lower(), "index.py")
            dest_dir = os.path.join(BASE_DIR, "addons", img_type.lower(), INDEX_SUFFIXES[img_type])
            dest = os.path.join(dest_dir, "index.py")
            
            try:
                shutil.copyfile(src, dest)
                progress.console.print(f"📄 Copied [bold]{img_type}[/] script to {dest}")
            except Exception as e:
                print_error(f"Failed to copy {img_type} script: {str(e)}")
                exit(1)
    
    print_success("All scripts deployed successfully!")

def run_indexing_scripts():
    """Run indexing scripts with pretty output"""
    print_step("Starting indexing process...", "📊")
    
    results = {}
    with console.status("[bold green]Indexing in progress...", spinner="dots") as status:
        for img_type in IMAGE_TYPES:
            status.update(f"🔍 Indexing {img_type} images...")
            script_path = os.path.join(BASE_DIR, "addons", img_type.lower(), INDEX_SUFFIXES[img_type], "index.py")
            
            result = subprocess.run(["python3", script_path], capture_output=True)
            results[img_type] = result.returncode
            
            if result.returncode != 0:
                print_error(f"{img_type} indexing failed!")
                console.print(f"[red]{result.stderr.decode()}[/]")
                exit(1)
    
    return results

def get_indexed_counts():
    """Count indexed images from JSON files and return totals"""
    print_step("Calculating indexing results...", "🧮")
    
    total_images = {}
    total_sizes = {}
    
    with Progress(transient=True) as progress:
        task = progress.add_task("[cyan]Processing index files...", total=len(IMAGE_TYPES))
        
        for img_type in IMAGE_TYPES:
            progress.update(task, advance=1, description=f"Processing {img_type}")
            
            json_path = os.path.join(
                BASE_DIR, "addons", img_type.lower(), 
                INDEX_SUFFIXES[img_type], f"index.main.{img_type.lower()}.json"
            )
            
            try:
                with open(json_path, "r") as f:
                    data = json.load(f)
                    total_images[img_type] = len(data)
                    
                    # Calculate total size in GB
                    total_bytes = sum(item.get('total_size', 0) for item in data)
                    size_gb = total_bytes / (1024 ** 3)
                    total_sizes[img_type] = f"{size_gb:.2f} GB"
                    
                    progress.console.print(
                        f"📊 Found [bold]{total_images[img_type]}[/] {img_type} images "
                        f"([green]{total_sizes[img_type]}[/])"
                    )
                    
            except Exception as e:
                print_error(f"Failed to process {img_type} index: {str(e)}")
                total_images[img_type] = 0
                total_sizes[img_type] = "0.00 GB"
    
    return total_images, total_sizes

def show_results_table(results, total_images, total_sizes):
    """Display beautiful results table with statistics"""
    table = Table(
        title="📊 Indexing Results Summary",
        show_header=True,
        header_style="bold magenta",
        box=box.ROUNDED,
        border_style="blue",
        show_footer=True
    )
    
    # Configure columns
    table.add_column("Type", style="cyan", footer="Total")
    table.add_column("Status", justify="center")
    table.add_column("Images", justify="right")
    table.add_column("Total Size", justify="right")
    table.add_column("Details", style="italic")
    
    # Add rows
    total_all_images = 0
    total_all_size = 0.0
    
    for img_type in IMAGE_TYPES:
        code = results.get(img_type, 1)
        status = "✅ [green]Success[/]" if code == 0 else "❌ [red]Failed[/]"
        images_count = total_images.get(img_type, 0)
        size_str = total_sizes.get(img_type, "0.00 GB")
        
        # Calculate totals
        total_all_images += images_count
        try:
            total_all_size += float(size_str.split()[0])
        except:
            pass
        
        table.add_row(
            f"📁 {img_type}",
            status,
            str(images_count),
            size_str,
            "Ready for deployment" if code == 0 else "Check logs for errors"
        )
    
    # Add footer with totals
    table.columns[2].footer = str(total_all_images)
    table.columns[3].footer = f"{total_all_size:.2f} GB"
    
    console.print(Panel(
        table,
        title="[bold]📦 Repository Status Report[/]",
        subtitle=f"Generated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        border_style="green"
    ))

def process_index_files():
    """Process and merge generated index files with rich output"""
    print_step("Compiling final indexes...", "📦")
    
    merged_data = {}
    
    with Progress(transient=True) as progress:
        task = progress.add_task("[cyan]Merging indexes...", total=len(IMAGE_TYPES))
        
        for img_type in IMAGE_TYPES:
            progress.update(task, advance=1, description=f"Processing {img_type}")
            src_filename = f"index.main.{img_type.lower()}.json"
            dest_filename = src_filename.replace("main", "od")
            src_path = os.path.join(
                BASE_DIR, "addons", img_type.lower(), 
                INDEX_SUFFIXES[img_type], src_filename
            )
            
            try:
                progress.console.print(f"📄 Copying [bold]{img_type}[/] index...")
                shutil.copyfile(src_path, dest_filename)
                
                with open(dest_filename, "r") as f:
                    merged_data[img_type] = json.load(f)
                    
                progress.console.print(f"🔗 Merged {len(merged_data[img_type])} {img_type} entries")
                
            except Exception as e:
                print_error(f"Failed to process {img_type} index: {str(e)}")
                exit(1)
    
    console.print(f"💾 Saving merged index...")
    with open("index.od.json", "w") as f:
        json.dump(merged_data, f, indent=4)
    
    print_success(f"Merged {sum(len(v) for v in merged_data.values())} total entries")

def post_processing():
    """Handle additional processing steps with rich output"""
    print_step("Running post-processing...", "🔁")
    
    steps = [
        ("🪞 Generating mirror indexes", "gen_mirrors.py"),
        ("🔢 Sorting entries", "sort.py")
    ]
    
    for description, script in steps:
        with console.status(f"[bold]{description}...") as status:
            try:
                result = subprocess.run(["python3", script], capture_output=True, text=True)
                if result.returncode != 0:
                    console.print(f"[red]Error in {script}:[/]\n{result.stderr}")
                    exit(1)
                print_success(f"{description} completed")
            except Exception as e:
                print_error(f"Failed to run {script}: {str(e)}")
                exit(1)

def main():
    print_header()
    validate_directory_structure()
    copy_index_scripts()
    
    # Run indexing and get results
    results = run_indexing_scripts()
    
    # Process results

    process_index_files()
    post_processing()
    
    # Show summary
    total_images, total_sizes = get_indexed_counts()
    show_results_table(results, total_images, total_sizes)
    
    console.print("\n🎉 [bold green]Repository indexing completed successfully![/]\n")

if __name__ == "__main__":
    main()
