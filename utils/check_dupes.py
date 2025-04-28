#!/usr/bin/env python3
import json
import argparse
from collections import defaultdict
from rich.console import Console
from rich.progress import Progress
from rich.panel import Panel
from rich.table import Table
from rich import box

# Initialize rich console
console = Console()

def print_header():
    """Print beautiful header"""
    console.print(Panel.fit("🔍 Duplicate Checker", 
                          style="bold cyan",
                          subtitle="⚡ Powered by LabHub Indexing System"))

def check_duplicates(json_data, verbose=False):
    """Check for duplicate names and hashes with progress tracking"""
    results = {}
    
    with Progress(transient=True) as progress:
        # Setup progress tasks
        main_task = progress.add_task("[cyan]Processing device types...", total=3)
        type_tasks = {
            "IOL": progress.add_task("[yellow]Checking IOL...", total=3, visible=False),
            "QEMU": progress.add_task("[magenta]Checking QEMU...", total=3, visible=False),
            "DYNAMIPS": progress.add_task("[green]Checking DYNAMIPS...", total=3, visible=False)
        }
        
        for device_type in ["IOL", "QEMU", "DYNAMIPS"]:
            progress.update(main_task, advance=1, description=f"Processing {device_type}")
            
            if device_type not in json_data:
                continue
                
            entries = json_data[device_type]
            type_results = {
                "duplicate_names": defaultdict(int),
                "duplicate_md5": defaultdict(int),
                "duplicate_sha1": defaultdict(int)
            }
            
            # Make current type task visible
            progress.update(type_tasks[device_type], visible=True)
            
            # Track names and hashes
            name_counts = defaultdict(int)
            md5_counts = defaultdict(int)
            sha1_counts = defaultdict(int)
            
            # Update progress for current type
            progress.update(type_tasks[device_type], description=f"Scanning {device_type} names")
            for entry in entries:
                name_counts[entry["name"]] += 1
                if verbose:
                    console.print(f"  🔸 Found {entry['name']}")
            
            progress.update(type_tasks[device_type], advance=1, description=f"Checking {device_type} MD5")
            for entry in entries:
                for file_entry in entry["files"]:
                    md5 = file_entry["checksum"]["md5"]
                    md5_counts[md5] += 1
                    if verbose:
                        console.print(f"  🔹 MD5: {md5[:8]}... for {entry['name']}")
            
            progress.update(type_tasks[device_type], advance=1, description=f"Checking {device_type} SHA1")
            for entry in entries:
                for file_entry in entry["files"]:
                    sha1 = file_entry["checksum"]["sha1"]
                    sha1_counts[sha1] += 1
                    if verbose:
                        console.print(f"  🔸 SHA1: {sha1[:8]}... for {entry['name']}")
            
            # Collect duplicates
            progress.update(type_tasks[device_type], description=f"Compiling {device_type} results")
            for name, count in name_counts.items():
                if count > 1:
                    type_results["duplicate_names"][name] = count
                    
            for md5, count in md5_counts.items():
                if count > 1:
                    type_results["duplicate_md5"][md5] = count
                    
            for sha1, count in sha1_counts.items():
                if count > 1:
                    type_results["duplicate_sha1"][sha1] = count
                    
            results[device_type] = type_results
            progress.update(type_tasks[device_type], advance=1, visible=False)
    
    return results

def print_report(results):
    """Print formatted duplicate report with tables"""
    for device_type, data in results.items():
        # Create main table for each device type
        type_table = Table(
            title=f"📊 {device_type} Duplicates",
            box=box.ROUNDED,
            border_style="blue",
            show_header=True,
            header_style="bold"
        )
        type_table.add_column("Duplicate Type", style="cyan")
        type_table.add_column("Count", justify="right")
        type_table.add_column("Examples", style="magenta")
        
        # Add name duplicates
        name_count = len(data["duplicate_names"])
        name_examples = ", ".join(list(data["duplicate_names"].keys())[:3])
        if len(data["duplicate_names"]) > 3:
            name_examples += ", ..."
        type_table.add_row(
            "🔤 Names",
            str(name_count),
            name_examples if name_count else "✅ None"
        )
        
        # Add MD5 duplicates
        md5_count = len(data["duplicate_md5"])
        md5_examples = ", ".join([f"{k[:8]}..." for k in list(data["duplicate_md5"].keys())[:3]])
        if len(data["duplicate_md5"]) > 3:
            md5_examples += ", ..."
        type_table.add_row(
            "🆔 MD5",
            str(md5_count),
            md5_examples if md5_count else "✅ None"
        )
        
        # Add SHA1 duplicates
        sha1_count = len(data["duplicate_sha1"])
        sha1_examples = ", ".join([f"{k[:8]}..." for k in list(data["duplicate_sha1"].keys())[:3]])
        if len(data["duplicate_sha1"]) > 3:
            sha1_examples += ", ..."
        type_table.add_row(
            "🔒 SHA1",
            str(sha1_count),
            sha1_examples if sha1_count else "✅ None"
        )
        
        console.print(Panel(type_table, border_style="green"))
        
        # Show detailed tables if duplicates found
        if any([data["duplicate_names"], data["duplicate_md5"], data["duplicate_sha1"]]):
            details_table = Table(
                title=f"🔍 {device_type} Detailed Findings",
                box=box.SIMPLE,
                show_header=True,
                header_style="bold magenta"
            )
            details_table.add_column("Type")
            details_table.add_column("Value")
            details_table.add_column("Occurrences", justify="right")
            
            for name, count in data["duplicate_names"].items():
                details_table.add_row("📝 Name", name, str(count))
                
            for md5, count in data["duplicate_md5"].items():
                details_table.add_row("🆔 MD5", f"{md5[:8]}...", str(count))
                
            for sha1, count in data["duplicate_sha1"].items():
                details_table.add_row("🔒 SHA1", f"{sha1[:8]}...", str(count))
                
            console.print(details_table)
        else:
            console.print(f"🎉 [bold green]No duplicates found in {device_type}[/]")
        
        console.print()  # Add spacing between sections

def main():
    print_header()
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Check for duplicate entries in LabHub index files")
    parser.add_argument("json_file", help="Path to the merged JSON file to check")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    args = parser.parse_args()
    
    # Load JSON file with progress
    with console.status("[bold green]Loading JSON file...", spinner="dots") as status:
        try:
            with open(args.json_file, "r") as f:
                data = json.load(f)
            console.print(f"✅ [green]Loaded {args.json_file}[/]")
        except FileNotFoundError:
            console.print(f"❌ [red]Error: File {args.json_file} not found[/]")
            return
        except json.JSONDecodeError:
            console.print(f"❌ [red]Error: Invalid JSON format in {args.json_file}[/]")
            return
    
    # Check for duplicates
    with console.status("[bold green]Analyzing for duplicates...", spinner="dots") as status:
        duplicate_report = check_duplicates(data, verbose=args.verbose)
    
    # Print results
    console.print(Panel.fit("[bold]📋 Duplicate Check Results[/]", 
                          border_style="yellow",
                          padding=(1, 4)))
    print_report(duplicate_report)

if __name__ == "__main__":
    main()