#!/usr/bin/env python3
import json
import shutil
import subprocess
import os
from datetime import datetime, timezone
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn
from rich.table import Table
from rich import box
from tqdm import tqdm
from collections import OrderedDict
from rich.progress import Progress, SpinnerColumn

# Initialize rich console
console = Console()

# Configuration
BASE_DIR = "./labhub-repo/"
SCRIPTS_DIR = "./scripts/"
IMAGE_TYPES = ["IOL", "QEMU", "DYNAMIPS"]
INDEX_SUFFIXES = {
    "IOL": "bin",
    "QEMU": "",
    "DYNAMIPS": ""
}

# Path to store generated index files
dist_dir = "./dist/"
if not os.path.exists(dist_dir):
    os.makedirs(dist_dir)

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
            else:
                print_success(f"{img_type} indexing completed successfully!")
                console.print(f"[green]{result.stdout.decode()}[/]")
                # Copy the generated JSON file to the dist directory
                json_src = os.path.join(BASE_DIR, "addons", img_type.lower(), INDEX_SUFFIXES[img_type], f"{img_type.lower()}.json")
                json_dest = os.path.join(dist_dir, f"{img_type.lower()}.json")
                try:
                    shutil.copyfile(json_src, json_dest)
                    console.print(f"📄 Copied [bold]{img_type}[/] JSON file to {json_dest}")
                except Exception as e:
                    print_error(f"Failed to copy {img_type} JSON file: {str(e)}")
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
                INDEX_SUFFIXES[img_type], f"{img_type.lower()}.json"
            )
            
            try:
                with open(json_path, "r") as f:
                    data = json.load(f)
                    # Access the image array using the 'images' key
                    entries = data.get('images', [])
                    total_images[img_type] = len(entries)
                    
                    # Calculate total size from metadata
                    total_bytes = sum(entry.get('metadata', {}).get('total_size', 0) for entry in entries)
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
    
    merged_data = OrderedDict()
    url_properties = None
    schema_version = "1.0"
    description = "LabHub Repository Index"

    # Get the most recent last_update from any index
    last_update = datetime.now(timezone.utc).isoformat()

    with Progress(transient=True) as progress:
        task = progress.add_task("[cyan]Merging indexes...", total=len(IMAGE_TYPES))
        
        for img_type in IMAGE_TYPES:
            progress.update(task, advance=1, description=f"Processing {img_type}")
            src_path = os.path.join(
                BASE_DIR, "addons", img_type.lower(), 
                INDEX_SUFFIXES[img_type], f"{img_type.lower()}.json"
            )
            
            try:
                with open(src_path, "r") as f:
                    type_data = json.load(f, object_pairs_hook=OrderedDict)
                    
                # Capture url_properties from first valid type
                if url_properties is None:
                    url_properties = type_data.get('url_properties', {})
                    
                # Store the image data under its type key
                merged_data[img_type] = type_data.get('images', [])
                
                progress.console.print(
                    f"🔗 Added {len(merged_data[img_type])} {img_type} entries "
                    f"({type_data.get('last_update', 'unknown date')})"
                )
                
            except Exception as e:
                print_error(f"Failed to process {img_type} index: {str(e)}")
                exit(1)

    # Create final unified schema
    final_schema = OrderedDict([
        ("schema_version", schema_version),
        ("description", description),
        ("last_update", last_update),
        ("url_properties", url_properties),
        *[(img_type, merged_data[img_type]) for img_type in IMAGE_TYPES]
    ])

    # Save the merged data
    merged_filename = os.path.join(dist_dir, "labhub.json")
    with open(merged_filename, "w") as f:
        json.dump(final_schema, f, indent=4, ensure_ascii=False)
    
    print_success(f"Created unified index with:")
    for img_type in IMAGE_TYPES:
        console.print(f"  • [bold cyan]{img_type}:[/] {len(merged_data[img_type])} entries")
    console.print(f"\n💾 Saved to [bold green]{merged_filename}[/]")


def cleanup_leftovers():
    """Cleanup index.py scripts and generated json files with progress tracking"""
    print_step("Cleaning up leftover files...", "🧹")
    
    # Collect all files to remove
    script_files = []
    json_files = []
    
    # First pass to find all existing files
    for img_type in IMAGE_TYPES:
        script_path = os.path.join(BASE_DIR, "addons", img_type.lower(), INDEX_SUFFIXES[img_type], "index.py")
        if os.path.exists(script_path):
            script_files.append(script_path)
            
        json_path = os.path.join(
            BASE_DIR, "addons", img_type.lower(), 
            INDEX_SUFFIXES[img_type], f"{img_type.lower()}.json"
        )
        if os.path.exists(json_path):
            json_files.append(json_path)
    
    # If no files to remove, exit
    if not script_files and not json_files:
        print_success("No leftover files to clean up")
        return

    # Custom progress bar style with emojis
    bar_format = "{l_bar}{bar:20}{r_bar}{bar:-10b}"
    
    # Create progress bars with emojis and styling
    with tqdm(total=len(script_files),
             desc="📜 Scripts", 
             bar_format=bar_format,
             colour='#00ff00',
             unit=' file',
             dynamic_ncols=True) as script_bar, \
         tqdm(total=len(json_files),
             desc="📊 JSONs",
             bar_format=bar_format,
             colour='#00ff00',
             unit=' file',
             dynamic_ncols=True) as json_bar:
        
        # Process script files
        for script_file in script_files:
            try:
                os.remove(script_file)
                script_bar.update(1)
            except Exception as e:
                print_error(f"Failed to remove {script_file}: {str(e)}")
                script_bar.update(1)
                
        # Process JSON files
        for json_file in json_files:
            try:
                os.remove(json_file)
                json_bar.update(1)
            except Exception as e:
                print_error(f"Failed to remove {json_file}: {str(e)}")
                json_bar.update(1)

def main():
    print_header()
    validate_directory_structure()
    copy_index_scripts()
    
    # Run indexing and get results
    results = run_indexing_scripts()
    
    # Process results
    process_index_files()    

    # Show summary
    total_images, total_sizes = get_indexed_counts()
    show_results_table(results, total_images, total_sizes)
    
    console.print("\n🎉 [bold green]Repository indexing completed successfully![/]\n")
    # Cleanup leftover scripts and files
    cleanup_leftovers()
    print_success("Cleaned up leftover scripts and files")

if __name__ == "__main__":
    # on keyboard interrupt, cleanup leftovers
    try:
        main()
    except KeyboardInterrupt:
        print_error("Process interrupted by user!")
        cleanup_leftovers()
        print_success("Cleaned up leftover scripts and files")
        exit(1)
    except Exception as e:
        print_error(f"An unexpected error occurred: {str(e)}")
        cleanup_leftovers()
        print_success("Cleaned up leftover scripts and files")
        exit(1)