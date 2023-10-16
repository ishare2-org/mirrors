import json
import os

def add_ids_and_sort(json_data):
    for key in json_data:
        entries = json_data[key] # Get the list of entries
        entries.sort(key=lambda x: x['name'])  # Sort entries by name
        for i, entry in enumerate(entries, start=1):
            entry_with_id_first = {"id": i, **entry}
            entries[i-1] = entry_with_id_first

def add_ids_and_sort_individual_structure(json_data):
    entries = json_data # The entries are the top-level elements
    entries.sort(key=lambda x: x['name'])  # Sort entries by name
    for i, entry in enumerate(entries, start=1):
        entry_with_id_first = {"id": i, **entry}
        entries[i-1] = entry_with_id_first

# List of JSON files to process
files = ["index.gd.json", "index.od.json"]
types = ["bin", "dynamips", "qemu"]
# Add files to the list of files
for type in types:
    files.append(f"index.gd.{type}.json")
    files.append(f"index.od.{type}.json")

print("Files to process:")
print(files)

for file_name in files:
    print(f"\nProcessing file: {file_name}")

    # Check if the file exists and is not empty
    if os.path.exists(file_name) and os.path.getsize(file_name) > 0:
        with open(file_name, 'r') as f:
            data = json.load(f)

            if "QEMU" in data or "IOL" in data or "DYNAMIPS" in data:
                # Handle all images in one structure
                add_ids_and_sort(data)
            else:
                # Handle each image in its own structure
                add_ids_and_sort_individual_structure(data)

        with open(file_name, 'w') as f:
            json.dump(data, f, indent=4)  # Write modified data back to the file
    else:
        print(f"File {file_name} does not exist or is empty.")
