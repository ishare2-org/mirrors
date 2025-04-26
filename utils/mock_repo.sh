#!/bin/bash

# Script to copy directory structure and create empty files, without deleting originals

# Function to display usage instructions
usage() {
  echo "Usage: $0 -s <source_directory> -d <destination_directory>"
  echo "  -s, --source      Source directory to copy the structure from."
  echo "  -d, --destination Destination directory to create the new structure in."
  echo "  -h, --help        Display this help message."
  exit 1
}

# Initialize variables
source_dir=""
dest_dir=""

# Parse command-line options
while getopts "s:d:h" opt; do
  case "$opt" in
    s) source_dir="$OPTARG" ;;
    d) dest_dir="$OPTARG" ;;
    h) usage ;;
    *) usage ;;
  esac
done
shift $((OPTIND -1))

# Check if required options are provided
if [ -z "$source_dir" ] || [ -z "$dest_dir" ]; then
  echo "Error: Both source and destination directories are required."
  usage
fi

# Check if the source directory exists and is a directory
if [ ! -d "$source_dir" ]; then
  echo "Error: Source directory '$source_dir' does not exist or is not a directory."
  exit 1
fi

# Check if the destination directory exists.  If it doesn't, create it.
if [ ! -d "$dest_dir" ]; then
  echo "Destination directory '$dest_dir' does not exist. Creating it."
  mkdir -p "$dest_dir" || {
    echo "Error: Failed to create destination directory '$dest_dir'."
    exit 1
  }
fi

# Function to copy the directory structure and create empty files
copy_structure() {
  local source="$1"
  local dest="$2"

  # Use find to create the directory structure in the destination
  find "$source" -type d -print0 | xargs -0 mkdir -p "$dest"
  if [ $? -ne 0 ]; then
    echo "Error: Failed to create directories in '$dest'"
    return 1
  fi

  # Use find to create empty files in the destination, mirroring the source structure
  find "$source" -type f -print0 | while IFS= read -r -d $'\0' file; do
    # Reconstruct the destination path for each file.
    local relative_path=$(echo "$file" | sed "s#^$(echo "$source" | sed 's:/*$:/:')##") #remove source path
    local dest_file="$dest/$relative_path"
    # Create the empty file.  Use touch --no-create in case a file exists.
    # Create the directory if it does not exist
    local dest_dir_for_file=$(dirname "$dest_file")
    if [ ! -d "$dest_dir_for_file" ]; then
      echo "Creating directory: $dest_dir_for_file"
      mkdir -p "$dest_dir_for_file"
      if [ $? -ne 0 ]; then
        echo "Error: Failed to create directory: $dest_dir_for_file"
        return 1
      fi
    fi
    echo "Creating file: $dest_file"
    # Try creating the file with a different method
    > "$dest_file" # Use output redirection to create an empty file
    touch_result=$?
    if [ $touch_result -ne 0 ]; then
      echo "Error: Failed to create mock file: $dest_file.  Output redirection exit code: $touch_result"
      touch --no-create "$dest_file" #also try touch
      touch_result=$?
      if [ $touch_result -ne 0 ]; then
        echo "Error: Failed to create mock file: $dest_file.  touch exit code: $touch_result"
      fi
    elif [ ! -f "$dest_file" ]; then
      echo "Error: Failed to create mock file: $dest_file. File does not exist after redirection."
    fi
  done
  echo "Successfully copied directory structure from '$source' to '$dest' and created empty files."
}

# Call the function to do the work
copy_structure "$source_dir" "$dest_dir"

exit 0
