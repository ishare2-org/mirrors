#!/usr/bin/bash

# Color codes and formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Configuration
SOURCE_DIRS=(
    "addons/iol/bin/"
    "addons/qemu/"
    "addons/dynamips/"
)
DEST_FILES=(
    "iol_hashes"
    "qemu_hashes"
    "dynamips_hashes"
)
# Check if script was run from the directory where the script is located
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ "$PWD" != "$script_dir" ]]; then
    echo -e "${RED}Error: Please run this script from the directory where it is located.${NC}"
    echo -e "Current directory: ${RED}$PWD${NC}"
    echo -e "Script directory: ${RED}$script_dir${NC}"
    echo -e "Please change to the script directory and try again."
    exit 1
fi

OUTPUT_DIR="../data/labhub_hashes"

# Print usage information
usage() {
    echo -e "${BOLD}Usage:${NC} $0 [-v] <rclone_remote_name>"
    echo -e "  -v  Enable verbose output"
    exit 1
}

# Pretty print functions
print_success() {
    echo -e "${GREEN}✅ Success:${NC} $1"
}

print_error() {
    echo -e "${RED}❌ Error:${NC} $1"
}

print_info() {
    echo -e "${CYAN}ℹ️  Info:${NC} $1"
}

print_header() {
    echo -e "${BOLD}${CYAN}"
    echo "╔════════════════════════════════════════╗"
    echo "║      LabHub Hash Generator             ║"
    echo "╚════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Initialize variables
VERBOSE=0
REMOTE_NAME=""

# Parse arguments
while getopts "v" opt; do
    case $opt in
    v) VERBOSE=1 ;;
    *) usage ;;
    esac
done
shift $((OPTIND - 1))

[ -z "$1" ] && usage
REMOTE_NAME="$1"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Main function
generate_hashes() {
    print_header
    print_info "Starting hash generation for remote: ${BOLD}$REMOTE_NAME${NC}"
    echo -e "${YELLOW}────────────────────────────────────────────${NC}"

    for i in "${!SOURCE_DIRS[@]}"; do
        local source_dir="${SOURCE_DIRS[i]}"
        local dest_file="${OUTPUT_DIR}/${DEST_FILES[i]}"

        [ $VERBOSE -eq 1 ] && print_info "Processing directory: ${source_dir}"

        echo -e "${CYAN}⏳ Generating hashes SHA1 for ${BOLD}${source_dir}${NC}..."

        if rclone sha1sum "$REMOTE_NAME:$source_dir" --output-file "$dest_file.sha1sum.txt"; then
            [ $VERBOSE -eq 1 ] && print_info "Saved hashes to: ${dest_file}.sha1sum.txt"
            print_success "Completed ${source_dir}"

            # Show quick stats
            file_count=$(wc -l <"$dest_file.sha1sum.txt")
            echo -e "   ${CYAN}📊 Hashes generated: ${BOLD}${file_count}${NC}"
        else
            print_error "Failed to generate sha1 hashes for ${source_dir}"
            exit 1
        fi

        echo -e "${CYAN}⏳ Generating hashes MD5 for ${BOLD}${source_dir}${NC}..."
        if rclone md5sum "$REMOTE_NAME:$source_dir" --output-file "$dest_file.md5sum.txt"; then
            [ $VERBOSE -eq 1 ] && print_info "Saved hashes to: ${dest_file}.md5sum.txt"
            print_success "Completed ${source_dir}"

            # Show quick stats
            file_count=$(wc -l <"$dest_file.md5sum.txt")
            echo -e "   ${CYAN}📊 Hashes generated: ${BOLD}${file_count}${NC}"
        else
            print_error "Failed to generate md5 hashes for ${source_dir}"
            exit 1
        fi

        echo -e "${YELLOW}────────────────────────────────────────────${NC}"
    done

    print_success "All hashes generated successfully!"
    echo -e "\n${BOLD}Output files:${NC}"
    ls -lh "${OUTPUT_DIR}" | tail -n +2
}

# Run main function
generate_hashes
