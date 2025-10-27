# Data-Driven Toolchain Implementation

## Overview

Lebowski's toolchain awareness (including XSC) is now **completely data-driven** through opinion files and configuration. No hardcoded XSC logic exists in the codebase.

## Implementation

### 1. Opinion Metadata Extension

Added `container_image` field to `OpinionMetadata` (opinion.py:35):

```python
@dataclass
class OpinionMetadata:
    """Metadata about an opinion"""
    version: str
    package: str
    opinion_name: str
    purity_level: str
    description: str
    maintainer: Dict[str, str] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    debian_versions: List[str] = field(default_factory=list)
    container_image: Optional[str] = None  # NEW: e.g., "lebowski/builder:xsc"
```

### 2. Builder Container Image Precedence

Updated `Builder.__init__()` (builder.py:23-56):

```python
def __init__(
    self,
    opinion: Opinion,
    output_dir: Path,
    use_container: bool = True,
    keep_sources: bool = False,
    verbose: bool = False,
    default_container_image: str = "lebowski/builder:bookworm",  # NEW
):
    # Container image precedence:
    # 1. Opinion's container_image (highest - e.g., XSC opinions)
    # 2. Config's default_container_image (from config.build.container_image)
    # 3. Hardcoded default "lebowski/builder:bookworm" (lowest)
    self.container_image = (
        opinion.metadata.container_image or
        default_container_image
    )
```

### 3. Enhanced Container Image Management

Updated `_ensure_container_image()` (builder.py:637-706):

```python
def _ensure_container_image(self, runtime: str) -> str:
    """Ensure container image exists, build or pull if necessary"""
    image_name = self.container_image  # Use opinion's or config's container

    # Check if image exists locally
    if exists_locally(image_name):
        return image_name

    # Try to pull from registry
    if pull_success(image_name):
        return image_name

    # Only build default bookworm image locally
    if image_name == "lebowski/builder:bookworm":
        return self._build_default_container_image(runtime, image_name)
    else:
        raise BuildError(
            f"Container image '{image_name}' not found.\n"
            f"For custom toolchain containers (XSC, etc.), you need to:\n"
            f"  1. Build the container image manually, or\n"
            f"  2. Pull it from a registry"
        )
```

### 4. CLI Integration

Updated CLI to pass config container to Builder (cli.py:154):

```python
builder = Builder(
    opinion=opinion_obj,
    output_dir=Path(output_dir),
    use_container=container,
    keep_sources=keep_sources,
    verbose=verbose,
    default_container_image=config.build.container_image,  # NEW
)
```

Added container image display (cli.py:117-118):

```python
# Show container image if opinion specifies one (e.g., XSC opinions)
if opinion_obj.metadata.container_image:
    click.echo(f"  Container: {opinion_obj.metadata.container_image}")
```

## How It Works

### Standard Build (No Custom Toolchain)

**Opinion file** (opinions/nginx/vanilla.yaml):
```yaml
version: "1.0"
package: nginx
opinion_name: vanilla
purity_level: pure-compilation
# No container_image specified
# Uses default: lebowski/builder:bookworm

modifications:
  cflags:
    - "-O2"
```

**Build flow:**
1. Opinion doesn't specify `container_image`
2. Falls back to config's `build.container_image` (or default)
3. Uses `lebowski/builder:bookworm`
4. Standard Debian toolchain

### XSC Build (Custom Toolchain)

**Parent opinion** (opinions/_base/xsc-baseline.yaml):
```yaml
version: "1.0"
opinion_name: xsc-baseline
purity_level: configure-only
description: XSC toolchain baseline for zero-syscall builds

# Specifies XSC container with toolchain
container_image: "lebowski/builder:xsc"

modifications:
  env:
    CC: gcc
    CXX: g++
    LD_LIBRARY_PATH: /toolchain/xsc/lib:/toolchain/xsc/sysroot/lib64

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

**Child opinion** (opinions/bash/xsc.yaml):
```yaml
extends: ../_base/xsc-baseline.yaml  # Inherits container_image!
package: bash
opinion_name: xsc

modifications:
  cflags:
    - "-DXSC_BUILD"
    - "-DRING_SYSCALLS"
```

**Build flow:**
1. Child extends parent, inherits `container_image: "lebowski/builder:xsc"`
2. Builder sees XSC container specified
3. Tries to pull `lebowski/builder:xsc` from registry
4. If not found, shows error with instructions to build/pull image
5. Uses XSC toolchain from container at `/toolchain/xsc/`

### CLI Output

**Standard build:**
```
✓ Opinion loaded: vanilla
  Package: nginx
  Purity: pure-compilation (HIGHEST trust)
  Description: Standard nginx build...
  # No container line - uses default

🔨 Starting build...
🐳 Building in container (reproducible)...
  Using docker for reproducible build
  Using existing container image: lebowski/builder:bookworm
```

**XSC build:**
```
✓ Opinion loaded: xsc
  Package: bash
  Purity: configure-only (HIGH trust)
  Description: XSC-aware bash build with zero syscall instructions...
  Container: lebowski/builder:xsc  ← Shows custom container

🔨 Starting build...
🐳 Building in container (reproducible)...
  Using docker for reproducible build
  Container image not found locally: lebowski/builder:xsc
  Attempting to pull from registry...
```

## Container Image Precedence

```
1. Opinion's container_image field          (highest)
   └─ e.g., container_image: "lebowski/builder:xsc"

2. Config's build.container_image
   └─ From /etc/lebowski.conf or ~/.config/lebowski/config.yaml

3. Hardcoded default                        (lowest)
   └─ "lebowski/builder:bookworm"
```

## Benefits

✅ **Zero Hardcoded XSC Logic**
- No mention of "xsc" in builder or CLI code
- All XSC awareness comes from opinion files

✅ **Generic Design**
- Works for any custom toolchain (XSC, LLVM, cross-compilation)
- Same mechanism for all special toolchains

✅ **Opinion Inheritance**
- Parent opinions (xsc-baseline.yaml) define toolchain
- Children automatically inherit container image

✅ **Container Registry Support**
- Pulls custom toolchain containers from registries
- Falls back to local build for default image

✅ **Clear Error Messages**
- Tells users exactly how to get custom toolchain containers
- Distinguishes between default and custom images

✅ **Reproducible Builds**
- Container image pinned in opinion file
- Exact toolchain version captured in manifest

## Testing

### Test 1: Standard Build (No Custom Toolchain)

```bash
lebowski build nginx --opinion-file opinions/nginx/vanilla.yaml

# Expected:
# - Uses lebowski/builder:bookworm (default)
# - Standard Debian GCC toolchain
# - Binary has syscall instructions (normal)
```

### Test 2: XSC Build (Custom Toolchain)

```bash
lebowski build bash --opinion-file opinions/bash/xsc.yaml

# Expected:
# - Uses lebowski/builder:xsc (from opinion)
# - XSC toolchain from /toolchain/xsc/
# - Binary has ZERO syscall instructions
```

### Test 3: Missing Custom Container

```bash
# Without lebowski/builder:xsc available
lebowski build bash --opinion-file opinions/bash/xsc.yaml

# Expected error:
# ❌ Build error: Container image 'lebowski/builder:xsc' not found locally
#    and could not be pulled.
#    For custom images like XSC toolchain containers, you need to:
#      1. Build the container image manually, or
#      2. Pull it from a registry
#    Example: docker build -t lebowski/builder:xsc -f /path/to/Dockerfile
```

## Files Modified

1. **lebowski/opinion.py**
   - Added `container_image: Optional[str]` to `OpinionMetadata`
   - Parser reads `container_image` from YAML

2. **lebowski/builder.py**
   - Added `default_container_image` parameter to `__init__()`
   - Implements container image precedence
   - Enhanced `_ensure_container_image()` with registry support
   - Added `_build_default_container_image()` helper

3. **lebowski/cli.py**
   - Passes `config.build.container_image` to Builder
   - Shows container image in CLI output when specified

4. **docs/TOOLCHAINS.md**
   - Updated with implementation details
   - Removed hardcoded detection logic section

## Future Enhancements

### 1. Container Registry Configuration

```yaml
# /etc/lebowski.conf
build:
  container_registry: "registry.example.com"
  container_images:
    xsc: "registry.example.com/lebowski/builder:xsc"
    clang: "registry.example.com/lebowski/builder:clang"
```

### 2. Toolchain Profiles

```yaml
# /etc/lebowski.conf
toolchains:
  xsc:
    container: "lebowski/builder:xsc"
    description: "Zero-syscall XSC toolchain"
    validation:
      verify_zero_syscalls: true

# Opinion uses profile name instead of container image
modifications:
  toolchain: xsc  # References profile above
```

### 3. Automatic Container Building

```python
# If Dockerfile found alongside opinion, offer to build
if not container_exists(opinion.metadata.container_image):
    dockerfile = opinion_dir / "Dockerfile"
    if dockerfile.exists():
        prompt_to_build(dockerfile, opinion.metadata.container_image)
```

## Summary

**Before (hypothetical hardcoded approach):**
```python
# builder.py - BAD: hardcoded XSC logic
if 'xsc' in opinion_name or '--sysroot' in cflags:
    self.container_image = "lebowski/builder:xsc"
    # XSC-specific logic...
```

**After (data-driven approach):**
```python
# builder.py - GOOD: generic, data-driven
self.container_image = (
    opinion.metadata.container_image or  # From opinion YAML
    default_container_image              # From config
)
```

**Key principle:** Toolchain awareness lives in **data files** (opinions), not **code**.
