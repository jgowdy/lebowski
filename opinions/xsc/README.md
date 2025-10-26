# XSC Architecture Opinions

These opinions build packages for the XSC architecture (x86_64-xsc-linux-gnu).

## What is XSC?

**eXtended SysCall** - Ring-based syscalls with hardware CFI enforcement.

Instead of traditional `syscall` instructions, XSC uses submission/completion ring buffers:
- No CPU traps for system calls
- Hardware control-flow integrity (Intel CET, ARM PAC)
- Significantly improved security and performance

## XSC Variants

### base
- Works on all x86-64 and ARM64 CPUs
- Ring-based syscalls
- Standard hardening

### cfi-compat
- **Requires hardware CFI support**
  - x86-64: Intel CET (Tiger Lake+, Zen 3+)
  - ARM64: PAC (ARMv8.3-A+, M1+, Graviton3+)
- Mandatory control-flow integrity
- Hard CFI enforcement (no allowlist)

## Using XSC Opinions

```bash
# Build package for XSC base variant
lebowski build nginx --opinion xsc-base

# Build for CFI-compat variant (requires CET/PAC hardware)
lebowski build nginx --opinion xsc-cfi-compat
```

## Requirements

XSC toolchain must be installed:
- x86_64-xsc-linux-gnu-gcc
- x86_64-xsc-linux-gnu-binutils
- glibc with --enable-xsc
- libxsc-rt

## Opinion Structure

All XSC opinions:
- Use x86_64-xsc-linux-gnu toolchain
- Link against libxsc-rt
- Include XSC_ABI ELF note
- Contain NO traditional syscall instructions

## Verification

After building, verify:

```bash
# No syscall instructions
objdump -d package | grep syscall
# Should be empty!

# XSC_ABI note present
readelf -n package | grep XSC_ABI
# Should show: XSC_ABI   version: 1
```

## Package List

See `/xsc-minimal-server-packages.txt` for complete list of ~400 packages needed for minimal server ISO.
