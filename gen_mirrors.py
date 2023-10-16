import json
from colorama import Fore, Style, init

STRING_TO_REPLACE = "labhub.eu.org/api/raw/?path=/UNETLAB%20I/"
STRING_TO_REPLACE_WITH = "drive.labhub.eu.org/0:/"
STRING_TO_REPLACE_2 = "labhub.eu.org/api/raw/?path=/UNETLAB%20II/"
STRING_TO_REPLACE_WITH_2 = "drive.labhub.eu.org/1:/"

INDEXES = ["index.od.bin.json", "index.od.qemu.json", "index.od.dynamips.json", "index.od.json"]

# Function to replace strings in the links
def replace_strings(link):
    link = link.replace(STRING_TO_REPLACE, STRING_TO_REPLACE_WITH)
    link = link.replace(STRING_TO_REPLACE_2, STRING_TO_REPLACE_WITH_2)
    return link

# Iterate through the INDEXES
for index_filename in INDEXES:
    print(Fore.GREEN + f"Processing {index_filename}..." + Style.RESET_ALL)

    # Load the JSON data from the current INDEX file
    with open(index_filename, "r") as f:
        data = json.load(f)

    if isinstance(data, list):
        # Handle the structure where data is a list of dictionaries
        for item in data:
            if "download_links" in item:
                item["download_links"] = [replace_strings(link) for link in item["download_links"]]
    else:
        # Handle the structure where data is a dictionary with keys for different types
        for key, items in data.items():
            for item in items:
                if "download_links" in item:
                    item["download_links"] = [replace_strings(link) for link in item["download_links"]]

    # Save the modified JSON to a new file
    new_index_filename = index_filename.replace("index.od", "index.gd")
    with open(new_index_filename, "w") as f:
        json.dump(data, f, indent=4)

    print(Fore.GREEN + f"--- Strings replaced. New index file created at: {new_index_filename} ---" + Style.RESET_ALL)
