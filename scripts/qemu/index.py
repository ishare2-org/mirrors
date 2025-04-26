#!/usr/bin/env python3
import os
import json
import argparse
import urllib.parse
from collections import OrderedDict
from tqdm import tqdm

# Get absolute path of current script file
script_directory = os.path.dirname(os.path.abspath(__file__))

# Configuration parameters
image_category = os.path.abspath(script_directory).split('/')[-1]
api_hostname = "labhub.eu.org"
unused_parent_dir = os.path.abspath(os.path.join(script_directory, os.pardir, os.pardir)).split('/')[-1]
remote_api_path = f"/api/raw/?path=/addons/{image_category}"
local_install_path = f"/opt/unetlab/addons/{image_category}/"


# File type mapping configuration
FILE_TYPE_MAPPING = {
    '.qcow2': 'disk',
    '.img': 'disk',
    '.vmdk': 'disk',
    '.iso': 'disk',
    '.yml': 'template',
    '.yaml': 'template',
    '.txt': 'document',
    '.md': 'document',
    '.tar.gz': 'archive',
    '.tgz': 'archive',
    '.zip': 'archive',
    '.py': 'script',
    '.sh': 'script',
    '.png': 'image',
}

def get_file_type(file_format: str):
    """Determine file type based on file extension"""
    return FILE_TYPE_MAPPING.get(file_format.lower(), 'other')

def convert_size_human_readable(num_bytes, suffix='B'):
    """Convert byte size to human-readable format"""
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num_bytes) < 1024.0:
            return "%3.1f %s%s" % (num_bytes, unit, suffix)
        num_bytes /= 1024.0
    return "%.1f %s%s" % (num_bytes, 'Yi', suffix)

def url_encode_component(component):
    """URL-encode path components"""
    return urllib.parse.quote(component, safe='/,=?')

def create_file_object(file_path, relative_dir, verbose=False):
    """Create a detailed file object with metadata"""
    file_name = os.path.basename(file_path)
    if verbose:
        tqdm.write(f" Processing file: {file_name}")

    # URL components encoding
    encoded_host = url_encode_component(api_hostname)
    encoded_api_path = url_encode_component(remote_api_path)
    encoded_relative_dir = url_encode_component(relative_dir)
    encoded_filename = url_encode_component(file_name)

    # File metadata
    file_format = os.path.splitext(file_name)[1]
    file_size = os.path.getsize(file_path)
    
    return OrderedDict([
        ("url", f"https://{encoded_host}{encoded_api_path}/{encoded_relative_dir}/{encoded_filename}"),
        ("size", file_size),
        ("human_readable_size", convert_size_human_readable(file_size)),
        ("format", file_format),
        ("type", get_file_type(file_format))
    ])

def process_directory_entry(current_dir, files, verbose=False):
    """Process a directory containing QCOW2 files and create entry"""
    folder_name = os.path.basename(current_dir)
    if verbose:
        tqdm.write(f" Creating directory entry: {folder_name}")

    # Calculate relative path from script directory
    relative_dir = os.path.relpath(current_dir, script_directory)
    
    # Process all files in directory
    file_objects = []
    total_size = 0
    
    for filename in files:
        file_path = os.path.join(current_dir, filename)
        file_obj = create_file_object(file_path, relative_dir, verbose)
        file_objects.append(file_obj)
        total_size += file_obj['size']

    return OrderedDict([
        ("format", ".qcow2"),
        ("name", folder_name),
        ("files", file_objects),
        ("download_path", f"{local_install_path}{folder_name}"),
        ("type", image_category),
        ("total_size", total_size),
        ("total_human_readable_size", convert_size_human_readable(total_size))
    ])

def process_single_file_entry(file_path, verbose=False):
    """Process a single file entry (TGZ/ZIP) and create metadata"""
    file_name = os.path.basename(file_path)
    if verbose:
        tqdm.write(f" Creating archive entry: {file_name}")

    # Calculate relative path from script directory
    relative_dir = os.path.relpath(os.path.dirname(file_path), script_directory)
    
    # Create file object
    file_obj = create_file_object(file_path, relative_dir, verbose)
    
    # Base name without extension
    base_name = os.path.splitext(file_name)[0]
    
    return OrderedDict([
        ("format", file_obj['format']),
        ("name", base_name),
        ("files", [file_obj]),
        ("download_path", f"{local_install_path}{base_name}"),
        ("type", image_category),
        ("total_size", file_obj['size']),
        ("total_human_readable_size", file_obj['human_readable_size'])
    ])

def generate_directory_index(start_path, truncate=None, verbose=False):
    """Generate index data with restructured format"""
    index_entries = []
    entry_count = 0

    # First pass to count potential entries for accurate progress
    total_entries = 0
    for current_dir, _, files in os.walk(start_path):
        if any(f.endswith('.qcow2') for f in files):
            total_entries += 1
        else:
            total_entries += sum(1 for f in files if f.endswith(('.tgz', '.tar.gz', '.zip')))

    # Apply truncate if specified
    if truncate is not None:
        total_entries = min(total_entries, truncate)

    with tqdm(
        desc="Indexing files",
        total=total_entries,
        unit="entry",
        colour="#00ff00",
        bar_format="{l_bar}{bar:40}{r_bar}",
        disable=verbose  # Disable bar in verbose mode to avoid conflict with logs
    ) as progress_bar:
        for current_dir, subdirs, files in os.walk(start_path):
            if entry_count >= total_entries:
                break

            # Process directories with QCOW2 files
            qcow2_files = [f for f in files if f.endswith('.qcow2')]
            if qcow2_files:
                dir_entry = process_directory_entry(current_dir, files, verbose)
                index_entries.append(dir_entry)
                entry_count += 1
                progress_bar.update(1)
                progress_bar.set_postfix_str(f"📁 {dir_entry['name'][:15]}...")

                if entry_count >= total_entries:
                    break

            # Process individual archive files
            else:
                for filename in files:
                    if entry_count >= total_entries:
                        break
                    if filename.endswith(('.tgz', '.tar.gz', '.zip')):
                        file_path = os.path.join(current_dir, filename)
                        file_entry = process_single_file_entry(file_path, verbose)
                        index_entries.append(file_entry)
                        entry_count += 1
                        progress_bar.update(1)
                        progress_bar.set_postfix_str(f"📦 {file_entry['name'][:15]}...")

    return index_entries

def write_json_output(data, output_path):
    """Write index data to JSON file"""
    with open(output_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def display_index_summary(index_data):
    """Print statistics about the generated index"""
    target_formats = [".qcow2", ".tgz", ".tar.gz", ".zip"]
    print("\nIndex generation summary:")
    print(f"Total indexed items: {len(index_data)}")
    for fmt in target_formats:
        count = sum(1 for e in index_data if e["format"] == fmt)
        print(f"{fmt} files/directories: {count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate file index with optional truncation and verbose output")
    parser.add_argument("--truncate", type=int, help="Stop after generating specified number of entries")
    parser.add_argument("--verbose", action="store_true", help="Enable detailed logging")
    args = parser.parse_args()

    output_json_path = os.path.join(script_directory, "index.main.qemu.json")
    
    index_data = generate_directory_index(
        script_directory,
        truncate=args.truncate,
        verbose=args.verbose
    )
    
    write_json_output(index_data, output_json_path)
    display_index_summary(index_data)
    print(f"\nOutput file: {output_json_path}")