#!/bin/bash
# Downloads, patches, and builds CBSH2-RTC for reference solution verification.
# CBSH2-RTC is not included in this repo (USC Research License).
# This script clones it from the authors' GitHub and applies our CLI11 patch.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="$SCRIPT_DIR/build"
COMMIT="a834df1e16c1668a677b68fef6699371c4233d33"
CLI11_URL="https://github.com/CLIUtils/CLI11/releases/download/v2.4.1/CLI11.hpp"
BOOST_URL="https://archives.boost.io/release/1.86.0/source/boost_1_86_0.tar.gz"

echo "=== CBSH2-RTC Setup ==="

# Step 1: Clone
if [ -d "$BUILD_DIR/CBSH2-RTC" ]; then
    echo "CBSH2-RTC already cloned, skipping."
else
    echo "Cloning CBSH2-RTC..."
    mkdir -p "$BUILD_DIR"
    git clone https://github.com/Jiaoyang-Li/CBSH2-RTC.git "$BUILD_DIR/CBSH2-RTC"
    cd "$BUILD_DIR/CBSH2-RTC"
    git checkout "$COMMIT"
fi

# Step 2: Download Boost headers (header-only, no compilation needed)
if [ -d "$BUILD_DIR/boost" ]; then
    echo "Boost headers already present, skipping."
else
    echo "Downloading Boost 1.86.0 headers..."
    cd "$BUILD_DIR"
    curl -L -o boost.tar.gz "$BOOST_URL"
    tar xzf boost.tar.gz
    mv boost_1_86_0 boost
    rm boost.tar.gz
fi

# Step 3: Download CLI11 header and apply patch
cd "$BUILD_DIR/CBSH2-RTC"
if [ ! -f inc/CLI11.hpp ]; then
    echo "Downloading CLI11..."
    curl -L -o inc/CLI11.hpp "$CLI11_URL"
fi

if git diff --quiet; then
    echo "Applying CLI11 patch..."
    git apply "$SCRIPT_DIR/cli11_patch.diff"
else
    echo "Patch already applied, skipping."
fi

# Step 4: Build
echo "Building..."
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DBOOST_ROOT="$BUILD_DIR/boost"
cmake --build . --config Release

echo ""
echo "=== Done ==="
echo "Binary: $BUILD_DIR/CBSH2-RTC/build/Release/cbs"
echo ""
echo "Example usage:"
echo "  ./cbs -m <map.map> -a <scenario.scen> -k <agent_count> -t 60"
