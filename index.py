#!/usr/bin/env python3
import json
import shutil
import subprocess
from colorama import Fore, Style, init

# Initialize colorama
init()

# Base directory
base_dir = "./lh-gd/"

# Copy index.py to corresponding directories from ./scripts to UNETLAB I and UNETLAB II
print(Fore.GREEN + "- Copying index.py to images directories..." + Style.RESET_ALL)
# scripts/dynamips/index.py, scripts/iol/bin/index.py, scripts/qemu/index.py
shutil.copyfile("scripts/dynamips/index.py", f"{base_dir}/addons/dynamips/index.py")
# shutil.copyfile("scripts/dynamips/index.py", f"{base_dir}UNETLAB II/addons/dynamips/index.py") # Dynamips is not supported in UNETLAB II
shutil.copyfile("scripts/iol/index.py", f"{base_dir}/addons/iol/bin/index.py")
shutil.copyfile("scripts/qemu/index.py", f"{base_dir}/addons/qemu/index.py")

# Run indexing scripts
print(Fore.GREEN + "- Indexing IOL images..." + Style.RESET_ALL)
subprocess.run(["python3", f"{base_dir}/addons/iol/bin/index.py"])
print(Fore.GREEN + "- Indexing QEMU images..." + Style.RESET_ALL)
subprocess.run(["python3", f"{base_dir}/addons/qemu/index.py"])
print(Fore.GREEN + "- Indexing DYNAMIPS images..." + Style.RESET_ALL)
subprocess.run(["python3", f"{base_dir}/addons/dynamips/index.py"])

# IOL
IOL_INDEX = f"{base_dir}/addons/iol/bin/index.main.bin.json"

# QEMU
QEMU_INDEX = f"{base_dir}/addons/qemu/index.main.qemu.json"

# DYNAMIPS
DYNAMIPS_INDEX = f"{base_dir}/addons/dynamips/index.main.dynamips.json"

# Copy each index file to the current directory
for index_file in [IOL_INDEX, QEMU_INDEX, DYNAMIPS_INDEX]:
    print(Fore.GREEN + f"Copying {index_file}..." + Style.RESET_ALL)
    shutil.copyfile(index_file, f"index.od.{index_file.split('.')[-1]}") # Copy to current directory with new name: index.od.bin.json, index.od.qemu.json, index.od.dynamips.json

print(Fore.GREEN + "-- Indexing completed --" + Style.RESET_ALL)

# Merge index files
print(Fore.GREEN + "Merging index files..." + Style.RESET_ALL)
# File paths
IOL_INDEX = "index.od.bin.json"
QEMU_INDEX = "index.od.qemu.json"
DYNAMIPS_INDEX = "index.od.dynamips.json"

# Load IOL index data
with open(IOL_INDEX, "r") as f:
    iol_data = json.load(f)

# Load QEMU index data
with open(QEMU_INDEX, "r") as f:
    qemu_data = json.load(f)

# Load DYNAMIPS index data
with open(DYNAMIPS_INDEX, "r") as f:
    dynamips_data = json.load(f)

# Merge data into one dictionary
merged_data = {
    "QEMU": qemu_data,
    "IOL": iol_data,
    "DYNAMIPS": dynamips_data
}

# Save merged data to a new JSON file
with open("index.od.json", "w") as f:
    json.dump(merged_data, f, indent=4)

print(Fore.GREEN + "--- Merging completed. Merged index file created at: index.od.json ---" + Style.RESET_ALL)

# Create additional index files
print(Fore.GREEN + "Creating additional index files with alternative mirror links..." + Style.RESET_ALL)
subprocess.run(["python3", "gen_mirrors.py"])
print(Fore.GREEN + "--- Additional index files created ---" + Style.RESET_ALL)

# Sort index files by name and add IDs
print(Fore.GREEN + "Sorting index files by name and adding IDs..." + Style.RESET_ALL)
subprocess.run(["python3", "sort.py"])
print(Fore.GREEN + "--- Sorting completed ---" + Style.RESET_ALL)
