#!/bin/bash
set -e

# Verify XSC packages are compliant
# Checks for: no syscalls, XSC_ABI notes, libxsc-rt linking

PACKAGES_DIR="${1:-$HOME/xsc-test-packages}"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║  XSC Package Verification                                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo
echo "Checking packages in: $PACKAGES_DIR"
echo

if [[ ! -d "$PACKAGES_DIR" ]]; then
    echo "❌ Package directory not found: $PACKAGES_DIR"
    exit 1
fi

# Counters
TOTAL_PACKAGES=0
TOTAL_BINARIES=0
SYSCALL_VIOLATIONS=0
MISSING_ABI_NOTES=0
MISSING_LIBXSC=0

# Temp extraction directory
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

# Find all .deb files
DEB_FILES=$(find "$PACKAGES_DIR" -name "*.deb" | sort)

if [[ -z "$DEB_FILES" ]]; then
    echo "❌ No .deb files found in $PACKAGES_DIR"
    exit 1
fi

echo "Found $(echo "$DEB_FILES" | wc -l) .deb files"
echo

# Function to check a binary
check_binary() {
    local binary="$1"
    local pkg_name="$2"

    ((TOTAL_BINARIES++))

    local has_violation=0

    # Check for syscall instructions
    if objdump -d "$binary" 2>/dev/null | grep -qE '(syscall|int.*0x80|sysenter|svc)'; then
        echo "  ❌ SYSCALL VIOLATION: $binary"
        echo "     Contains traditional syscall instructions!"
        ((SYSCALL_VIOLATIONS++))
        has_violation=1
    fi

    # Check for XSC_ABI note
    if ! readelf -n "$binary" 2>/dev/null | grep -q "XSC_ABI"; then
        echo "  ⚠️  MISSING XSC_ABI: $binary"
        echo "     No XSC_ABI ELF note found!"
        ((MISSING_ABI_NOTES++))
        has_violation=1
    fi

    # Check for libxsc-rt linkage
    if ldd "$binary" 2>/dev/null | grep -v "not a dynamic executable" >/dev/null; then
        if ! ldd "$binary" 2>/dev/null | grep -q "libxsc-rt"; then
            echo "  ⚠️  NOT LINKED TO libxsc-rt: $binary"
            ((MISSING_LIBXSC++))
            has_violation=1
        fi
    fi

    # If no violations, show success
    if [[ $has_violation -eq 0 ]]; then
        echo "  ✅ $binary"
    fi
}

# Check each package
while IFS= read -r deb_file; do
    ((TOTAL_PACKAGES++))

    pkg_name=$(basename "$deb_file" .deb)
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📦 Checking: $pkg_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Extract package
    extract_dir="$TEMP_DIR/$pkg_name"
    mkdir -p "$extract_dir"
    dpkg-deb -x "$deb_file" "$extract_dir" 2>/dev/null

    # Find all ELF binaries
    binaries=$(find "$extract_dir" -type f -executable -exec file {} \; | \
               grep -i "elf" | cut -d: -f1 || true)

    if [[ -z "$binaries" ]]; then
        echo "  ℹ️  No binaries found (may be data-only package)"
    else
        while IFS= read -r binary; do
            check_binary "$binary" "$pkg_name"
        done <<< "$binaries"
    fi

    echo
done <<< "$DEB_FILES"

# Summary
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  Verification Summary                                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo
echo "Packages checked:        $TOTAL_PACKAGES"
echo "Binaries checked:        $TOTAL_BINARIES"
echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Violations:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

if [[ $SYSCALL_VIOLATIONS -eq 0 ]]; then
    echo "✅ Syscall instructions:  0 (PASS)"
else
    echo "❌ Syscall instructions:  $SYSCALL_VIOLATIONS (FAIL - CRITICAL!)"
fi

if [[ $MISSING_ABI_NOTES -eq 0 ]]; then
    echo "✅ Missing XSC_ABI notes: 0 (PASS)"
else
    echo "⚠️  Missing XSC_ABI notes: $MISSING_ABI_NOTES (WARNING)"
fi

if [[ $MISSING_LIBXSC -eq 0 ]]; then
    echo "✅ Missing libxsc-rt:     0 (PASS)"
else
    echo "⚠️  Missing libxsc-rt:     $MISSING_LIBXSC (WARNING)"
fi

echo

# Overall result
if [[ $SYSCALL_VIOLATIONS -eq 0 ]] && \
   [[ $MISSING_ABI_NOTES -eq 0 ]] && \
   [[ $MISSING_LIBXSC -eq 0 ]]; then
    echo "🎉 ALL PACKAGES ARE XSC COMPLIANT!"
    echo
    echo "Next steps:"
    echo "  1. Create test repository"
    echo "  2. Bootstrap minimal test system"
    echo "  3. Boot and functional test"
    echo "  4. If all pass -> scale to 400 packages"
    exit 0
else
    echo "⚠️  SOME PACKAGES HAVE ISSUES"
    echo
    echo "Action required:"
    if [[ $SYSCALL_VIOLATIONS -gt 0 ]]; then
        echo "  🔴 CRITICAL: Binaries contain syscall instructions!"
        echo "     These MUST be fixed - packages won't work on XSC"
        echo "     Check toolchain configuration and rebuild"
    fi
    if [[ $MISSING_ABI_NOTES -gt 0 ]]; then
        echo "  🟡 WARNING: Missing XSC_ABI notes"
        echo "     Add XSC_ABI section to linker scripts"
    fi
    if [[ $MISSING_LIBXSC -gt 0 ]]; then
        echo "  🟡 WARNING: Not linked to libxsc-rt"
        echo "     Add -lxsc-rt to LDFLAGS"
    fi
    exit 1
fi
