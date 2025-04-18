#!/usr/bin/env python3
import os
import json
import urllib.parse

# Get the absolute path of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Configuration
image_type = os.path.abspath(os.path.join(script_dir)).split('/')[-1]
download_path = f"/opt/unetlab/addons/{image_type}/"
hostname = "labhub.eu.org"
parent_dir = os.path.abspath(os.path.join(script_dir, os.pardir, os.pardir)).split('/')[-1]
remote_path = f"/api/raw/?path=/addons/{image_type}"

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f %s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f %s%s" % (num, 'Yi', suffix)

def generate_index(directory):
    index_data = []
    absolute_directory_path = os.path.join(script_dir, directory)

    for filename in os.listdir(absolute_directory_path):
        if filename.endswith('.image'):
            # Construct the download link with URL encoding
            encoded_hostname = urllib.parse.quote(hostname, safe='')
            encoded_remote_path = urllib.parse.quote(remote_path, safe='/,?,=')
            encoded_filename = urllib.parse.quote(filename, safe='/')
            download_link = f"https://{encoded_hostname}{encoded_remote_path}/{encoded_filename}"

            size = os.path.getsize(os.path.join(absolute_directory_path, filename))  # get size in bytes
            human_readable_size = sizeof_fmt(size)  # convert size to human-readable format

            entry = {
                "format": ".image",
                "name": filename,
                "download_links": [download_link],
                "download_path": download_path,
                "type": image_type,
                "size": size,  # add size to the entry
                "human_readable_size": human_readable_size  # add human-readable size to the entry
            }
            index_data.append(entry)

    return index_data

def save_to_json(index_data, output_file):
    with open(output_file, 'w') as json_file:
        json.dump(index_data, json_file, indent=4)

if __name__ == "__main__":
    output_file_path = os.path.join(script_dir, "index.main.dynamips.json")  # Output JSON file path

    index_data = generate_index(".")
    save_to_json(index_data, output_file_path)

    print("Indexing completed. JSON file created at:", output_file_path)
