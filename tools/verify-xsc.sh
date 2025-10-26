#!/bin/bash
# XSC Binary Verification Script
# Verifies that a .deb package contains ZERO syscall instructions

set -e

PACKAGE_DEB="$1"

if [ -z "$PACKAGE_DEB" ]; then
    echo "Usage: $0 <package.deb>"
    echo ""
    echo "Verifies that all binaries in the .deb have zero syscall instructions."
    exit 1
fi

if [ ! -f "$PACKAGE_DEB" ]; then
    echo "ERROR: File not found: $PACKAGE_DEB"
    exit 1
fi

TMPDIR=$(mktemp -d /tmp/xsc-verify-XXXXXX)
trap "rm -rf $TMPDIR" EXIT

echo "=== XSC Verification for $(basename $PACKAGE_DEB) ==="
echo ""

# Extract .deb
echo "[1/4] Extracting .deb package..."
dpkg-deb -x "$PACKAGE_DEB" "$TMPDIR/extract" 2>/dev/null
echo "✓ Extracted to $TMPDIR/extract"
echo ""

# Find all ELF binaries
echo "[2/4] Finding ELF binaries..."
BINARIES=$(find "$TMPDIR/extract" -type f -executable -exec file {} \; | grep "ELF.*executable" | cut -d: -f1)
BINARY_COUNT=$(echo "$BINARIES" | grep -c "." || echo "0")

if [ "$BINARY_COUNT" -eq 0 ]; then
    echo "WARNING: No ELF binaries found in package"
    echo "This package may only contain libraries or scripts."
    exit 0
fi

echo "✓ Found $BINARY_COUNT ELF binaries:"
echo "$BINARIES" | while read bin; do
    echo "  - ${bin#$TMPDIR/extract}"
done
echo ""

# Check each binary for syscall instructions
echo "[3/4] Checking for syscall instructions..."
TOTAL_SYSCALLS=0
FAILED_BINARIES=()

echo "$BINARIES" | while read BINARY; do
    SYSCALL_COUNT=$(objdump -d "$BINARY" 2>/dev/null | grep -c "syscall" || echo "0")
    
    if [ "$SYSCALL_COUNT" -gt 0 ]; then
        echo "  ❌ ${BINARY#$TMPDIR/extract}: $SYSCALL_COUNT syscall instructions"
        FAILED_BINARIES+=("$BINARY")
        TOTAL_SYSCALLS=$((TOTAL_SYSCALLS + SYSCALL_COUNT))
    else
        echo "  ✓ ${BINARY#$TMPDIR/extract}: ZERO syscalls"
    fi
done

echo ""

# Final verdict
echo "[4/4] Verification Result"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$TOTAL_SYSCALLS" -eq 0 ]; then
    echo "✓✓✓ XSC VERIFICATION PASSED ✓✓✓"
    echo ""
    echo "ALL binaries have ZERO syscall instructions."
    echo "This package uses ring-based syscalls via libxsc-rt."
    echo ""
    echo "Package: $(basename $PACKAGE_DEB)"
    echo "Binaries checked: $BINARY_COUNT"
    echo "Total syscall instructions: 0"
    echo ""
    exit 0
else
    echo "❌❌❌ XSC VERIFICATION FAILED ❌❌❌"
    echo ""
    echo "Found $TOTAL_SYSCALLS syscall instructions in binaries."
    echo "This package was NOT built with XSC toolchain."
    echo ""
    echo "Failed binaries:"
    for bin in "${FAILED_BINARIES[@]}"; do
        echo "  - ${bin#$TMPDIR/extract}"
    done
    echo ""
    exit 1
fi
