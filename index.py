#!/usr/bin/env python3
import json
import shutil
import subprocess
from colorama import Fore, Style, init

# Initialize colorama
init()

# Base directory
base_dir = "../UNETLAB/"

# Copy index.py to corresponding directories from ./scripts to UNETLAB I and UNETLAB II
print(Fore.GREEN + "- Copying index.py to UNETLAB I and UNETLAB II..." + Style.RESET_ALL)
# scripts/dynamips/index.py, scripts/iol/bin/index.py, scripts/qemu/index.py
shutil.copyfile("scripts/dynamips/index.py", f"{base_dir}UNETLAB I/addons/dynamips/index.py")
# shutil.copyfile("scripts/dynamips/index.py", f"{base_dir}UNETLAB II/addons/dynamips/index.py") # Dynamips is not supported in UNETLAB II
shutil.copyfile("scripts/iol/index.py", f"{base_dir}UNETLAB I/addons/iol/bin/index.py")
shutil.copyfile("scripts/iol/index.py", f"{base_dir}UNETLAB II/addons/iol/bin/index.py")
shutil.copyfile("scripts/qemu/index.py", f"{base_dir}UNETLAB I/addons/qemu/index.py")
shutil.copyfile("scripts/qemu/index.py", f"{base_dir}UNETLAB II/addons/qemu/index.py")

# Run indexing scripts
print(Fore.GREEN + "- Indexing UNETLAB I IOL images..." + Style.RESET_ALL)
subprocess.run(["python3", f"{base_dir}UNETLAB I/addons/iol/bin/index.py"])
print(Fore.GREEN + "- Indexing UNETLAB II IOL images..." + Style.RESET_ALL)
subprocess.run(["python3", f"{base_dir}UNETLAB II/addons/iol/bin/index.py"])
print(Fore.GREEN + "- Indexing UNETLAB I QEMU images..." + Style.RESET_ALL)
subprocess.run(["python3", f"{base_dir}UNETLAB I/addons/qemu/index.py"])
print(Fore.GREEN + "- Indexing UNETLAB II QEMU images..." + Style.RESET_ALL)
subprocess.run(["python3", f"{base_dir}UNETLAB II/addons/qemu/index.py"])
print(Fore.GREEN + "- Indexing UNETLAB I DYNAMIPS images..." + Style.RESET_ALL)
subprocess.run(["python3", f"{base_dir}UNETLAB I/addons/dynamips/index.py"])

# IOL
UNETLABI_IOL_INDEX = f"{base_dir}UNETLAB I/addons/iol/bin/index_bin.json"
UNETLABII_IOL_INDEX = f"{base_dir}UNETLAB II/addons/iol/bin/index_bin.json"
# QEMU
UNETLABI_QEMU_INDEX = f"{base_dir}UNETLAB I/addons/qemu/index_qemu.json"
UNETLABII_QEMU_INDEX = f"{base_dir}UNETLAB II/addons/qemu/index_qemu.json"
# DYNAMIPS
UNETLABI_DYNAMIPS_INDEX = f"{base_dir}UNETLAB I/addons/dynamips/index_dynamips.json"

# Join IOL index files
print(Fore.GREEN + "- Joining IOL index files..." + Style.RESET_ALL)
with open(UNETLABI_IOL_INDEX, "r") as f:
    iol_i = json.load(f)
with open(UNETLABII_IOL_INDEX, "r") as f:
    iol_ii = json.load(f)
iol_i.extend(iol_ii)
with open("index.od.bin.json", "w") as f:
    json.dump(iol_i, f)

# Join QEMU index files
print(Fore.GREEN + "- Joining QEMU index files..." + Style.RESET_ALL)
with open(UNETLABI_QEMU_INDEX, "r") as f:
    qemu_i = json.load(f)
with open(UNETLABII_QEMU_INDEX, "r") as f:
    qemu_ii = json.load(f)
qemu_i.extend(qemu_ii)
with open("index.od.qemu.json", "w") as f:
    json.dump(qemu_i, f)

# Copy Dynamips index file
print(Fore.GREEN + "Copying DYNAMIPS index file..." + Style.RESET_ALL)
shutil.copyfile(UNETLABI_DYNAMIPS_INDEX, "index.od.dynamips.json")

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