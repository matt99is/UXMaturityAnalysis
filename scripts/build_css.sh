#!/bin/bash
# CSS Build Script for UX Analysis Reports
# Compiles Sass modular stylesheets into a single optimized CSS file

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CSS_DIR="$PROJECT_ROOT/css"
OUTPUT_DIR="$PROJECT_ROOT/output/css"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "Building CSS..."

# Check if sass is installed
if ! command -v sass &> /dev/null; then
    echo -e "${YELLOW}Sass not found. Installing...${NC}"
    if command -v npm &> /dev/null; then
        npm install -g sass
    else
        echo -e "${RED}Error: npm not found. Please install Node.js or sass manually.${NC}"
        echo "  npm install -g sass"
        echo "  Or: sudo apt-get install sass-cli (Debian/Ubuntu)"
        exit 1
    fi
fi

# Build CSS
sass "$CSS_DIR/main.scss" "$OUTPUT_DIR/main.css" --style=compressed --no-source-map

if [ $? -eq 0 ]; then
    file_size=$(wc -c < "$OUTPUT_DIR/main.css")
    file_size_formatted=$(numfmt --to=iec-i --suffix=B $file_size 2>/dev/null || echo "$file_size bytes")
    echo -e "${GREEN}✓ CSS built: output/css/main.css ($file_size_formatted)${NC}"
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi
