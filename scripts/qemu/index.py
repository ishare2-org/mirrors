#!/usr/bin/env python3
import os
import json
import urllib.parse
from collections import OrderedDict

# Get the absolute path of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Configuration
image_type = os.path.abspath(script_dir).split('/')[-1]
hostname = "labhub.eu.org"
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir)).split('/')[-1]
remote_path = f"/api/raw/?path=/addons/{image_type}"
download_path = f"/opt/unetlab/addons/{image_type}/"

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)

def encode_url_component(component):
    return urllib.parse.quote(component, safe='/,=?')

def generate_file_entry(filename, relative_path, root):
    encoded_hostname = encode_url_component(hostname)
    encoded_remote_path = encode_url_component(remote_path)
    encoded_relative_path = encode_url_component(relative_path)
    encoded_filename = encode_url_component(filename)

    link = f"https://{encoded_hostname}{encoded_remote_path}/{encoded_relative_path}/{encoded_filename}"

    size = os.path.getsize(os.path.join(root, filename))  # get size in bytes
    human_readable_size = sizeof_fmt(size)  # convert size to human-readable format

    entry = OrderedDict([
        ("format", os.path.splitext(filename)[1]),
        ("name", filename),
        ("download_links", [link]),
        ("download_path", download_path),
        ("type", image_type),
        ("size", size),  # add size to the entry
        ("human_readable_size", human_readable_size)  # add human-readable size to the entry
    ])

    return entry, link

def generate_index(directory):
    index_data = []
    for root, dirs, files in os.walk(directory):
        all_files = []
        qcow2_present = False
        for filename in files:
            full_path = os.path.relpath(os.path.join(root, filename), script_dir)
            relative_path = os.path.dirname(full_path)
            file_entry, link = generate_file_entry(filename, relative_path, root)
            all_files.append((file_entry, link))
            if filename.endswith('.qcow2'):
                qcow2_present = True

        if qcow2_present:
            folder_name = os.path.basename(root)
            links = [file_entry_link[1] for file_entry_link in all_files]

            total_size_qcow2_files = sum(os.path.getsize(os.path.join(root, file)) for file in files if file.endswith('.qcow2'))
            human_readable_total_size_qcow2_files = sizeof_fmt(total_size_qcow2_files)

            entry = {
                "format": ".qcow2",
                "name": folder_name,
                "download_links": links,
                "download_path": download_path + folder_name,
                "type": image_type,
                "size": total_size_qcow2_files,  # add total size of .qcow2 files to the entry
                "human_readable_size": human_readable_total_size_qcow2_files  # add human-readable total size of .qcow2 files to the entry
            }

            index_data.append(entry)
        else:
            for file_entry, link in all_files:
                if file_entry["format"] in [".tgz", ".zip"]:
                    file_entry["format"] = file_entry["format"]
                    file_entry["name"] = os.path.splitext(file_entry["name"])[0]
                    file_entry["download_links"] = [link]
                    file_entry["download_path"] += file_entry["name"]

                    index_data.append(file_entry)

    return index_data

def save_to_json(index_data, output_file):
    with open(output_file, 'w') as json_file:
        json.dump(index_data, json_file, indent=4)

def print_summary(index_data):
    file_formats = [".qcow2", ".tgz", ".zip"]
    num_entries = len(index_data)
    num_entries_by_format = {format: sum(1 for entry in index_data if entry["format"] == format) for format in file_formats}

    print("Summary of indexed data:")
    print(f"Total number of entries: {num_entries}")
    for format in file_formats:
        print(f"Number of {format} entries: {num_entries_by_format[format]}")

if __name__ == "__main__":
    output_file_path = os.path.join(script_dir, "index.main.qemu.json")  # Output JSON file path

    index_data = generate_index(script_dir)
    save_to_json(index_data, output_file_path)

    print("Indexing completed. JSON file created at:", output_file_path)