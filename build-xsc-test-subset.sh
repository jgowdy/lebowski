#!/bin/bash
set -e

# Build XSC Test Subset using Lebowski
# Proves Lebowski + XSC integration works before scaling to 400 packages

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$HOME/xsc-test-packages"
XSC_TOOLCHAIN_DIR="$HOME/flexsc/build/toolchain"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Building XSC Test Subset (15 packages)                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo

# Check XSC toolchain exists
if [[ ! -d "$XSC_TOOLCHAIN_DIR" ]]; then
    echo "❌ XSC toolchain not found at: $XSC_TOOLCHAIN_DIR"
    echo "   Run: cd ~/flexsc && ./build-xsc-toolchain.sh"
    exit 1
fi

# Add XSC toolchain to PATH
export PATH="$XSC_TOOLCHAIN_DIR/bin:$PATH"

# Verify XSC compiler works
if ! which x86_64-xsc-linux-gnu-gcc >/dev/null 2>&1; then
    echo "❌ x86_64-xsc-linux-gnu-gcc not in PATH"
    echo "   XSC toolchain may not be built correctly"
    exit 1
fi

echo "✓ XSC toolchain found: $(x86_64-xsc-linux-gnu-gcc --version | head -1)"
echo

# Create output directory
mkdir -p "$OUTPUT_DIR"/{essential,services,devtools}

# Package lists
ESSENTIAL_PKGS=(bash coreutils util-linux openssh-server systemd)
PACKAGE_MGMT=(apt dpkg gnupg)
SERVICES=(nginx postgresql-15 python3 redis-server)
DEVTOOLS=(gcc gdb strace)

# Function to build a package
build_package() {
    local pkg="$1"
    local category="$2"
    local opinion="${3:-xsc-base}"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📦 Building: $pkg (opinion: $opinion)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Check if opinion exists
    local opinion_file="$SCRIPT_DIR/opinions/${pkg}/${opinion}.yaml"

    if [[ ! -f "$opinion_file" ]]; then
        # Try creating from template
        echo "⚠️  Opinion not found: $opinion_file"
        echo "   Creating from template..."

        mkdir -p "$SCRIPT_DIR/opinions/$pkg"
        sed "s/PACKAGE_NAME/$pkg/g" "$SCRIPT_DIR/opinions/xsc/TEMPLATE.yaml" \
            > "$opinion_file"

        echo "✓ Created template opinion"
    fi

    # Build with Lebowski
    cd "$SCRIPT_DIR/build-tool"

    if python3 -m lebowski build "$pkg" \
        --opinion-file "$opinion_file" \
        --output-dir "$OUTPUT_DIR/$category" \
        --keep-sources; then
        echo "✅ $pkg built successfully"
        return 0
    else
        echo "❌ $pkg build failed"
        return 1
    fi
}

# Track successes and failures
SUCCESS_COUNT=0
FAIL_COUNT=0
FAILED_PACKAGES=()

# Build essential packages
echo "═══════════════════════════════════════════════════════════"
echo "TIER 1: Essential Packages"
echo "═══════════════════════════════════════════════════════════"
for pkg in "${ESSENTIAL_PKGS[@]}"; do
    if build_package "$pkg" "essential"; then
        ((SUCCESS_COUNT++))
    else
        ((FAIL_COUNT++))
        FAILED_PACKAGES+=("$pkg")
    fi
    echo
done

# Build package management
echo "═══════════════════════════════════════════════════════════"
echo "TIER 2: Package Management"
echo "═══════════════════════════════════════════════════════════"
for pkg in "${PACKAGE_MGMT[@]}"; do
    if build_package "$pkg" "essential"; then
        ((SUCCESS_COUNT++))
    else
        ((FAIL_COUNT++))
        FAILED_PACKAGES+=("$pkg")
    fi
    echo
done

# Build services
echo "═══════════════════════════════════════════════════════════"
echo "TIER 3: Key Services"
echo "═══════════════════════════════════════════════════════════"
for pkg in "${SERVICES[@]}"; do
    # Use xsc-optimized for python3
    local opinion="xsc-base"
    [[ "$pkg" == "python3" ]] && opinion="xsc-optimized"

    if build_package "$pkg" "services" "$opinion"; then
        ((SUCCESS_COUNT++))
    else
        ((FAIL_COUNT++))
        FAILED_PACKAGES+=("$pkg")
    fi
    echo
done

# Build devtools
echo "═══════════════════════════════════════════════════════════"
echo "TIER 4: Development Tools"
echo "═══════════════════════════════════════════════════════════"
for pkg in "${DEVTOOLS[@]}"; do
    if build_package "$pkg" "devtools"; then
        ((SUCCESS_COUNT++))
    else
        ((FAIL_COUNT++))
        FAILED_PACKAGES+=("$pkg")
    fi
    echo
done

# Summary
echo
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Build Summary                                             ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo
echo "✅ Successful: $SUCCESS_COUNT"
echo "❌ Failed:     $FAIL_COUNT"
echo

if [[ $FAIL_COUNT -gt 0 ]]; then
    echo "Failed packages:"
    for pkg in "${FAILED_PACKAGES[@]}"; do
        echo "  - $pkg"
    done
    echo
    echo "⚠️  Some packages failed to build"
    echo "   Fix failures before proceeding to full 400-package build"
    exit 1
else
    echo "🎉 All test packages built successfully!"
    echo
    echo "Next steps:"
    echo "  1. Run verification: ./verify-xsc-packages.sh"
    echo "  2. Test packages in minimal system"
    echo "  3. If all pass, scale to full 400-package build"
fi

echo
echo "Packages saved to: $OUTPUT_DIR"
