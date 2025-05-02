#!/usr/bin/env python3
import os
import json
import argparse
import urllib.parse
from collections import OrderedDict
from tqdm import tqdm
from datetime import datetime, timezone

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

def lookup_hash(file_path, hash_type):
    """Look up file hash using full relative path from repository root"""
    hashes_dir = "data/labhub_hashes"
    hash_files = {
        "md5": "qemu_hashes.md5sum.txt",
        "sha1": "qemu_hashes.sha1sum.txt"
    }
    
    if hash_type not in hash_files:
        print(f"❌ Invalid hash type: {hash_type}. Use 'md5' or 'sha1'")
        return ""

    hash_path = os.path.join(hashes_dir, hash_files[hash_type])
    
    try:
        # Get relative path from repository root (POSIX format)
        relative_path = os.path.relpath(file_path, start=script_directory)
        relative_path = relative_path.replace(os.path.sep, '/')  # Normalize to POSIX
        
        with open(hash_path, 'r') as f, \
             tqdm(total=os.path.getsize(hash_path), 
                  desc=f"🔍 Searching {hash_type.upper()} hashes",
                  unit='B',
                  unit_scale=True,
                  bar_format="{l_bar}{bar:30}{r_bar}",
                  colour="#00ff00") as progress:

            for line in f:
                progress.update(len(line.encode('utf-8')))
                line = line.strip()
                if not line:
                    continue
                
                # Split hash and path, preserving spaces in path
                parts = line.split('  ', 1)
                if len(parts) != 2:
                    continue
                
                current_hash, hash_file_path = parts
                # Normalize hash file path to POSIX format
                normalized_hash_path = hash_file_path.replace('\\', '/')
                
                if normalized_hash_path == relative_path:
                    progress.close()
                    return current_hash
                    
    except FileNotFoundError:
        print(f"❌ Hash file not found: {hash_path}")
    except Exception as e:
        print(f"❌ Error reading hash file: {str(e)}")
    
    return ""

def create_file_object(file_path, relative_dir, verbose=False):
    """Create a detailed file object with metadata"""
    filename = os.path.basename(file_path)
    if verbose:
        tqdm.write(f" Processing file: {filename}")

    # URL components encoding
    encoded_host = url_encode_component(api_hostname)
    encoded_api_path = url_encode_component(remote_api_path)
    encoded_relative_dir = url_encode_component(relative_dir)
    encoded_filename = url_encode_component(filename)

    # File metadata
    file_format = os.path.splitext(filename)[1]
    file_size = os.path.getsize(file_path)
    
    return OrderedDict([
        ("filename", filename),
        ("path", f"/addons/qemu/{encoded_relative_dir}/{encoded_filename}"),
        ("size", file_size),
        ("human_size", convert_size_human_readable(file_size)),
        ("file_type", get_file_type(file_format)),
        ("extension", file_format),
        ("checksum", {
            "md5": lookup_hash(file_path, "md5"),
            "sha1": lookup_hash(file_path, "sha1")
            }
        )
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
        ("name", folder_name),
        ("type", image_category),
        ("files", file_objects),
        ("metadata", {
            "install_path": f"{local_install_path}{folder_name}/",
            "total_size": total_size,
            "total_human_size": convert_size_human_readable(total_size),
        }),
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
        ("name", base_name),
        ("type", image_category),
        ("files", [file_obj]),
        ("metadata", {
            "install_path": f"{local_install_path}{base_name}/",
            "total_size": file_obj['size'],
            "total_human_size": file_obj['human_size'],
        })
    ])

def generate_full_schema(index_data):
    """Wrap the existing data in the new schema format with sorted entries and IDs"""
    # Sort entries case-insensitively by name
    sorted_entries = sorted(index_data, key=lambda x: x['name'].lower())
    
    # Add sequential IDs while preserving OrderedDict structure
    ordered_entries = []
    for idx, entry in enumerate(sorted_entries, start=1):
        # Create new OrderedDict with ID as first key
        new_entry = OrderedDict()
        new_entry['id'] = idx
        for key in entry:
            new_entry[key] = entry[key]
        ordered_entries.append(new_entry)
    
    return OrderedDict([
        ("schema_version", "1.0"),
        ("description", "QEMU images index"),
        ("last_update", datetime.now(timezone.utc).isoformat()),
        ("url_properties", {
            "protocol": "https",
            "hostnames": {
                "main": "labhub.eu.org",
                "drive": "drive.labhub.eu.org"
            },
            "prefixes": {
                "main": "/api/raw/?path=/",
                "drive": "/0:/"
            }
        }),
        ("images", ordered_entries)
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
        desc="📁 Indexing files",
        total=total_entries,
        unit="entry",
        colour="#00ffff",  # Cyan color
        bar_format="{l_bar}{bar:30}{r_bar}",
        dynamic_ncols=True,
        disable=verbose
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
                progress_bar.set_postfix_str(f"📂 [cyan]{dir_entry['name'][:15]}...[/]")

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
                        progress_bar.set_postfix_str(f"📦 [yellow]{file_entry['name'][:15]}...[/]")

    return index_entries

def write_json_output(data, output_path):
    """Write index data to JSON file"""
    with open(output_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)

def display_index_summary(index_data):
    """Print statistics about the generated index"""
    target_formats = [".qcow2", ".tgz", ".tar.gz", ".zip", ".gz"]
    print("\nIndex generation summary:")
    print(f"Total indexed items: {len(index_data)}")
    for fmt in target_formats: # get from files[] > {extension}
        count = sum(1 for e in index_data if any(file["extension"] == fmt for file in e["files"]))
        print(f"{fmt} files/directories: {count}")

# Modified main execution block
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate QEMU images index")
    parser.add_argument("--truncate", type=int, help="Stop after generating specified number of entries")
    parser.add_argument("--verbose", action="store_true", help="Enable detailed logging")
    args = parser.parse_args()

    output_json_path = os.path.join(script_directory, "qemu.json")
    
    # Existing processing logic remains untouched
    index_data = generate_directory_index(
        script_directory,
        truncate=args.truncate,
        verbose=args.verbose
    )
    
    # Wrap in new schema format
    full_schema = generate_full_schema(index_data)
    
    # Save and display results
    write_json_output(full_schema, output_json_path)
    display_index_summary(index_data)
    print(f"\nOutput file: {output_json_path}")