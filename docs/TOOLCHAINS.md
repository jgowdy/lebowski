# Toolchains in Lebowski

## Overview

Lebowski supports multiple compiler toolchains for different build scenarios:

1. **Standard**: Default GCC/G++ from Debian
2. **XSC**: Custom zero-syscall toolchain
3. **LLVM/Clang**: Alternative compiler
4. **Custom**: User-defined toolchains

**Critical**: Not every GCC is XSC-aware! XSC builds require a special toolchain.

## The Problem

Consider these different scenarios:

### Standard Build (most packages)
```bash
CC=gcc
CXX=g++
# Uses system glibc
# Produces normal binaries with syscall instructions
```

### XSC Build (zero-syscall)
```bash
CC=gcc  # But with XSC sysroot!
CXX=g++
CFLAGS="--sysroot=/build/xsc/xsc-toolchain/sysroot ..."
LDFLAGS="-lxsc-rt ..."
# Uses xsc-glibc
# Produces binaries with ZERO syscall instructions
```

### Cross-Compilation
```bash
CC=aarch64-linux-gnu-gcc
CXX=aarch64-linux-gnu-g++
# Cross-compiling for ARM
```

**The key insight**: The toolchain determines the runtime environment, not just the compiler.

## Toolchain Specification in Opinions

### Method 1: Container Images (Recommended)

The **cleanest approach** is to use container images with pre-built toolchains:

```yaml
# opinions/bash/xsc.yaml
extends: ../_base/xsc-baseline.yaml
package: bash
opinion_name: xsc

# Use container with XSC toolchain pre-installed
container_image: "lebowski/builder:xsc"

modifications:
  # Toolchain-specific paths (relative to container)
  env:
    CC: gcc
    CXX: g++
    LD_LIBRARY_PATH: /toolchain/xsc/lib:/toolchain/xsc/sysroot/lib64

  cflags:
    - "--sysroot=/toolchain/xsc/sysroot"
    - "-O2"

  ldflags:
    - "--sysroot=/toolchain/xsc/sysroot"
    - "-L/toolchain/xsc/lib"
    - "-lxsc-rt"
```

**Container structure**:
```
lebowski/builder:xsc
├── /toolchain/xsc/
│   ├── bin/x86_64-xsc-linux-gnu-gcc  (optional cross-compiler)
│   ├── lib/libxsc-rt.so.1.0.0
│   ├── include/xsc/syscall.h
│   └── sysroot/
│       ├── lib64/libc.so.6  (xsc-glibc)
│       └── lib64/ld-linux-x86-64.so.2  (XSC dynamic linker)
└── /usr/bin/gcc  (host gcc, used with --sysroot)
```

### Method 2: Toolchain Field (Future Enhancement)

For clarity, we could add an explicit `toolchain` section:

```yaml
modifications:
  toolchain:
    type: xsc
    root: /toolchain/xsc
    sysroot: /toolchain/xsc/sysroot

    # Auto-set by toolchain type:
    # CC: gcc
    # CFLAGS: --sysroot={sysroot}
    # LDFLAGS: -L{root}/lib -lxsc-rt
    # LD_LIBRARY_PATH: {root}/lib:{sysroot}/lib64
```

**Not implemented yet**, but would make toolchain setup more declarative.

## Container Images for Different Toolchains

### 1. Standard Toolchain

**Image**: `lebowski/builder:bookworm` (default)

**Contents**:
- Standard Debian GCC 12
- System glibc
- Standard build tools

**Use case**: Normal package builds

### 2. XSC Toolchain

**Image**: `lebowski/builder:xsc`

**Contents**:
- Host GCC (for compiling with --sysroot)
- XSC toolchain at `/toolchain/xsc/`
  - libxsc-rt.so (ring syscall runtime)
  - xsc-glibc (glibc with syscall → xsc_syscall patch)
  - XSC dynamic linker
- All standard build tools

**Use case**: Zero-syscall builds

**How to build** (example Dockerfile):
```dockerfile
FROM debian:bookworm

# Install standard tools
RUN apt-get update && apt-get install -y \
    build-essential dpkg-dev debhelper \
    wget curl git

# Copy XSC toolchain
COPY xsc-toolchain/ /toolchain/xsc/

# Set up library paths
RUN echo "/toolchain/xsc/lib" > /etc/ld.so.conf.d/xsc.conf && \
    echo "/toolchain/xsc/sysroot/lib64" >> /etc/ld.so.conf.d/xsc.conf && \
    ldconfig

# Default to XSC-aware environment
ENV PATH="/toolchain/xsc/bin:${PATH}"
ENV LD_LIBRARY_PATH="/toolchain/xsc/lib:/toolchain/xsc/sysroot/lib64"
```

### 3. LLVM/Clang Toolchain

**Image**: `lebowski/builder:clang`

**Contents**:
- Clang 17
- libc++
- lld linker

**Use case**: Builds requiring Clang

### 4. Cross-Compilation Toolchains

**Image**: `lebowski/builder:aarch64`

**Contents**:
- aarch64-linux-gnu-gcc
- Cross sysroot

**Use case**: Building for ARM64

## Opinion Examples

### Example 1: Standard Build (No Special Toolchain)

```yaml
# opinions/nginx/vanilla.yaml
version: "1.0"
package: nginx
opinion_name: vanilla
purity_level: pure-compilation

# Uses default container: lebowski/builder:bookworm
# Uses standard GCC

modifications:
  cflags:
    - "-O2"
    - "-pipe"
```

**Result**: Standard nginx with normal glibc

### Example 2: XSC Build (Special Toolchain Required)

```yaml
# opinions/bash/xsc.yaml
extends: ../_base/xsc-baseline.yaml
package: bash
opinion_name: xsc
purity_level: configure-only

# CRITICAL: Must use XSC container!
container_image: "lebowski/builder:xsc"

modifications:
  env:
    CC: gcc  # Host gcc, but with XSC sysroot
    CXX: g++
    LD_LIBRARY_PATH: /toolchain/xsc/lib:/toolchain/xsc/sysroot/lib64

  cflags:
    - "--sysroot=/toolchain/xsc/sysroot"
    - "-O2"

  ldflags:
    - "--sysroot=/toolchain/xsc/sysroot"
    - "-L/toolchain/xsc/lib"
    - "-lxsc-rt"
    - "-Wl,-rpath=/toolchain/xsc/lib"
    - "-Wl,--dynamic-linker=/toolchain/xsc/sysroot/lib64/ld-linux-x86-64.so.2"
```

**Result**: bash with ZERO syscall instructions (uses xsc-glibc)

### Example 3: Parent Opinion for XSC

```yaml
# opinions/_base/xsc-baseline.yaml
version: "1.0"
opinion_name: xsc-baseline
purity_level: configure-only
description: XSC toolchain baseline for zero-syscall builds

# All XSC builds need this container
container_image: "lebowski/builder:xsc"

modifications:
  env:
    CC: gcc
    CXX: g++
    AR: ar
    RANLIB: ranlib
    LD_LIBRARY_PATH: /toolchain/xsc/lib:/toolchain/xsc/sysroot/lib64
    PKG_CONFIG_PATH: /toolchain/xsc/lib/pkgconfig

  cflags:
    - "--sysroot=/toolchain/xsc/sysroot"
    - "-O2"
    - "-fstack-protector-strong"

  ldflags:
    - "--sysroot=/toolchain/xsc/sysroot"
    - "-L/toolchain/xsc/lib"
    - "-lxsc-rt"
    - "-Wl,-rpath=/toolchain/xsc/lib"
    - "-Wl,--dynamic-linker=/toolchain/xsc/sysroot/lib64/ld-linux-x86-64.so.2"
```

**Any opinion that extends this automatically gets XSC toolchain setup!**

## How GCC Knows About XSC

### Standard GCC (NOT XSC-aware)

```bash
$ gcc -o hello hello.c
# Links against /lib/x86_64-linux-gnu/libc.so.6 (standard glibc)
# Binary contains syscall instructions
```

### GCC with XSC Sysroot (XSC-aware via --sysroot)

```bash
$ gcc --sysroot=/toolchain/xsc/sysroot \
      -L/toolchain/xsc/lib -lxsc-rt \
      -o hello hello.c
# Links against /toolchain/xsc/sysroot/lib64/libc.so.6 (xsc-glibc)
# Binary contains ZERO syscall instructions!
```

**Key point**: We use **standard GCC** but point it to **XSC sysroot** via `--sysroot` flag. This tells GCC:
1. Use XSC headers from `/toolchain/xsc/sysroot/usr/include`
2. Link against xsc-glibc at `/toolchain/xsc/sysroot/lib64/libc.so.6`
3. Use XSC dynamic linker

### Alternative: Custom XSC Cross-Compiler

We could also build `x86_64-xsc-linux-gnu-gcc` (Stage 3 compiler from Phase 3 plan), which has XSC paths built-in:

```bash
$ x86_64-xsc-linux-gnu-gcc -o hello hello.c
# Automatically uses XSC sysroot (no --sysroot needed)
```

**But**: This is more complex. Using host GCC with `--sysroot` is simpler.

## Toolchain Detection (Implementation)

Lebowski automatically detects which toolchain to use based on the opinion's `container_image` field:

```python
# In Builder.__init__() - lebowski/builder.py
self.container_image = (
    opinion.metadata.container_image or      # Opinion specifies (e.g., lebowski/builder:xsc)
    default_container_image                   # From config or default
)

# In Builder._ensure_container_image()
def _ensure_container_image(self, runtime: str) -> str:
    """Ensure container image exists, build or pull if necessary"""
    image_name = self.container_image

    # Check if image exists locally
    check_cmd = [runtime, 'images', '-q', image_name]
    # ...

    # Try to pull from registry if not found
    pull_cmd = [runtime, 'pull', image_name]
    # ...

    # Only build default bookworm image locally
    if image_name == "lebowski/builder:bookworm":
        return self._build_default_container_image(runtime, image_name)
    else:
        raise BuildError(f"Container image '{image_name}' not found...")
```

**Key points:**
- No hardcoded XSC logic - toolchain awareness is **data-driven**
- Container image precedence: opinion > config > default
- Registry support for pulling custom toolchain containers
- Clear error messages when custom containers aren't available

## Verification

### After Build: Verify Toolchain Was Used Correctly

**For XSC builds**, verify zero syscalls:

```bash
# Extract .deb
dpkg-deb -x bash_5.1_amd64.deb /tmp/verify

# Find binaries
find /tmp/verify -type f -executable -exec file {} \; | grep ELF

# Verify ZERO syscalls
objdump -d /tmp/verify/bin/bash | grep " syscall$"
# Expected: NO OUTPUT (zero syscalls!)
```

**For standard builds**, syscalls are expected:

```bash
objdump -d /tmp/verify/bin/bash | grep " syscall$"
# Expected: Many syscall instructions (normal!)
```

## Container Image Hierarchy

```
lebowski/builder:base
├── lebowski/builder:bookworm (default)
├── lebowski/builder:xsc (XSC toolchain)
│   └── lebowski/builder:xsc-aggressive (XSC + -O3 -flto)
├── lebowski/builder:clang
└── lebowski/builder:cross
    ├── lebowski/builder:aarch64
    └── lebowski/builder:riscv64
```

## CLI Integration

### Automatic Container Selection

```bash
# Standard build - uses default container
lebowski build nginx --opinion vanilla

# XSC build - opinion specifies container_image: lebowski/builder:xsc
lebowski build bash --opinion xsc
# Automatically uses XSC container!

# Override container
lebowski build bash --opinion xsc --container-image custom/xsc:latest
```

### Container Image in Opinion Metadata

Add to opinion schema:

```yaml
# Opinion metadata
container_image: "lebowski/builder:xsc"  # Optional, defaults to bookworm
```

If specified, this container is used instead of the default.

## Best Practices

### 1. Use Parent Opinions for Toolchain Setup

Create `_base/xsc-baseline.yaml` with all XSC toolchain setup:

```yaml
container_image: "lebowski/builder:xsc"
modifications:
  env:
    CC: gcc
    LD_LIBRARY_PATH: /toolchain/xsc/lib:...
  cflags: ["--sysroot=/toolchain/xsc/sysroot", ...]
  ldflags: ["-L/toolchain/xsc/lib", "-lxsc-rt", ...]
```

Then child opinions just extend it:

```yaml
extends: ../_base/xsc-baseline.yaml
# XSC toolchain setup inherited automatically!
```

### 2. Document Toolchain Requirements

In opinion descriptions:

```yaml
description: |
  XSC-aware bash build with zero syscall instructions.

  REQUIRES: lebowski/builder:xsc container with XSC toolchain
```

### 3. Validate Toolchain in Opinion

Add validation that checks if XSC opinions have XSC container:

```python
if 'xsc' in opinion_name and 'xsc' not in container_image:
    raise OpinionValidationError(
        "XSC opinions must specify container_image: lebowski/builder:xsc"
    )
```

## Future Enhancements

### 1. Toolchain Profiles

```yaml
# In /etc/lebowski.conf
toolchains:
  xsc:
    container: "lebowski/builder:xsc"
    env:
      CC: gcc
      LD_LIBRARY_PATH: /toolchain/xsc/lib
    cflags: ["--sysroot=/toolchain/xsc/sysroot"]
    ldflags: ["-lxsc-rt"]
```

Then opinions just reference:

```yaml
modifications:
  toolchain: xsc
```

### 2. Toolchain Discovery

```bash
lebowski toolchains list
# Available toolchains:
#   standard (default)
#   xsc (zero-syscall)
#   clang (LLVM)

lebowski toolchains info xsc
# XSC Toolchain
#   Container: lebowski/builder:xsc
#   Compiler: gcc with XSC sysroot
#   Features: zero-syscall, ring transitions
```

## Summary

**Key points**:

1. ✅ **Not all GCC is XSC-aware** - Need special XSC toolchain
2. ✅ **Container images** contain toolchains (recommended approach)
3. ✅ **Opinion specifies container** via `container_image` field
4. ✅ **Parent opinions** (like xsc-baseline) set up toolchain
5. ✅ **Verification** confirms correct toolchain was used

**Critical for XSC**:
- Must use `lebowski/builder:xsc` container
- Must set `--sysroot` to XSC sysroot
- Must link against libxsc-rt
- Verify zero syscalls after build

**Example workflow**:

```bash
# Build with XSC toolchain
lebowski build bash --opinion xsc

# Opinion xsc.yaml specifies:
#   container_image: lebowski/builder:xsc
#   (XSC toolchain setup inherited from parent)

# Result: bash with ZERO syscall instructions!
```

---

See also:
- [CONTAINERS.md](./CONTAINERS.md) - Container image design (TODO)
- [XSC-IMPLEMENTATION.md](./XSC-IMPLEMENTATION.md) - XSC technical details
