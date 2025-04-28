#!/usr/bin/env python3
import os
import json
import argparse
import urllib.parse
from collections import OrderedDict
from tqdm import tqdm

# Get the absolute path of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Configuration
download_path = "/opt/unetlab/addons/dynamips/"
image_type = os.path.abspath(os.path.join(script_dir)).split('/')[-1]
hostname = "labhub.eu.org"
parent_dir = os.path.abspath(os.path.join(script_dir)).split('/')[-1]
remote_path = f"/api/raw/?path=/addons/{parent_dir}"

def sizeof_fmt(num, suffix='B'):
    """Convert bytes to human-readable format"""
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)

def url_encode_component(component):
    """URL-encode components while preserving needed characters"""
    return urllib.parse.quote(component, safe='/,=?')

def lookup_hash(image_name, hash_type):
    """Look up file hash from stored checksum files with progress tracking"""
    hashes_dir = "data/labhub_hashes"
    hash_files = {
        "md5": "dynamips_hashes.md5sum.txt",
        "sha1": "dynamips_hashes.sha1sum.txt"
    }
    
    if hash_type not in hash_files:
        print(f"❌ Invalid hash type: {hash_type}. Use 'md5' or 'sha1'")
        return ""

    hash_path = os.path.join(hashes_dir, hash_files[hash_type])
    
    try:
        # Get total lines for progress bar
        with open(hash_path, 'r') as f:
            total_lines = sum(1 for _ in f)
            
        with open(hash_path, 'r') as f, \
             tqdm(total=total_lines, 
                  desc=f"🔍 Searching {hash_type.upper()} hashes",
                  unit="file",
                  bar_format="{l_bar}{bar:30}{r_bar}",
                  colour="#00ff00") as progress:

            for line in f:
                progress.update(1)
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split('  ', 1)
                if len(parts) != 2:
                    continue
                
                current_hash, filename = parts
                if filename == image_name:
                    progress.close()
                    return current_hash
                    
    except FileNotFoundError:
        print(f"❌ Hash file not found: {hash_path}")
    except Exception as e:
        print(f"❌ Error reading hash file: {str(e)}")
    
    return ""

def generate_file_entry(file_path, filename):
    """Create detailed file entry with metadata"""
    size = os.path.getsize(file_path)
    return OrderedDict([
        ("filename", filename),
        ("url", f"https://{url_encode_component(hostname)}"
                f"{url_encode_component(remote_path)}/"
                f"{url_encode_component(filename)}"),
        ("size", size),
        ("human_size", sizeof_fmt(size)),
        ("file_type", "firmware"),
        ("extension", os.path.splitext(filename)[1]),
        ("checksum", {
            "md5": lookup_hash(filename, "md5"),
            "sha1": lookup_hash(filename, "sha1")
            }
        )
    ])

def generate_index(directory, truncate=None, verbose=False):
    """Generate structured index data for .image files"""
    index_data = []
    absolute_dir = os.path.join(script_dir, directory)
    
    # Get list of .image files
    image_files = [f for f in os.listdir(absolute_dir) if f.endswith('.image')]
    if not image_files:
        if verbose:
            tqdm.write("No .image files found in directory")
        return index_data

    # Set up progress bar
    total_files = len(image_files) if truncate is None else min(truncate, len(image_files))
    progress_desc = f"🔧 Processing {image_type} images"

    with tqdm(
        total=total_files,
        desc=progress_desc,
        unit="file",
        colour="#00ff00",
        disable=verbose  # Disable bar if verbose to avoid output conflict
    ) as pbar:
        processed = 0
        for filename in image_files:
            if truncate and processed >= truncate:
                if verbose:
                    tqdm.write(f"Stopped at truncation limit: {truncate} files")
                break

            file_path = os.path.join(absolute_dir, filename)
            
            if verbose:
                tqdm.write(f"\nProcessing file: {filename}")
                
            try:
                file_entry = generate_file_entry(file_path, filename)
                main_entry = OrderedDict([
                    ("name", filename),
                    ("type", image_type),
                    ("files", [file_entry]),
                    ("metadata", {
                        "install_path": download_path,
                        "total_size": file_entry["size"],
                        "total_human_size": file_entry["human_size"],
                    })
                ])
                index_data.append(main_entry)
                processed += 1
                
                if verbose:
                    tqdm.write(f"Added entry for {filename} ({file_entry['human_readable_size']})")
                    
                pbar.update(1)
                # Add emoji and truncate long filenames
                truncated_name = (filename[:15] + '...') if len(filename) > 15 else filename
                pbar.set_postfix_str(f"💾 {truncated_name}")

            except Exception as e:
                if verbose:
                    tqdm.write(f"Error processing {filename}: {str(e)}")
                continue

    return index_data

def save_to_json(index_data, output_file):
    """Save index data to JSON file with proper formatting"""
    with open(output_file, 'w') as json_file:
        json.dump(index_data, json_file, indent=4)

def display_summary(index_data):
    """Print summary statistics"""
    total_entries = len(index_data)
    total_size = sum(entry["metadata"]["total_size"] for entry in index_data) if index_data else 0
    
    print("\nIndexing summary:")
    print(f"Total entries created: {total_entries}")
    print(f"Total firmware size: {sizeof_fmt(total_size)}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate DYNAMIPS images index")
    parser.add_argument("--truncate", type=int, help="Limit number of entries processed")
    parser.add_argument("--verbose", action="store_true", help="Enable detailed processing output")
    args = parser.parse_args()

    output_file_path = os.path.join(script_dir, "index.main.dynamips.json")
    
    index_data = generate_index(
        script_dir,
        truncate=args.truncate,
        verbose=args.verbose
    )
    
    save_to_json(index_data, output_file_path)
    display_summary(index_data)
    print(f"\nOutput file created at: {output_file_path}")