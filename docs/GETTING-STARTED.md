# Getting Started with Lebowski

Lebowski is a data-driven Debian package builder that uses "opinions" (YAML configurations) to customize package builds with specific compiler flags, patches, and optimizations.

## Quick Start

```bash
# Clone the project
git clone https://github.com/jgowdy/lebowski.git
cd lebowski

# Build your first package (bash with XSC optimizations)
cd build-tool
python3 -m lebowski.cli build bash \
  --opinion-file ../lebowski-opinions/bash/xsc.yaml \
  --output-dir /tmp/bash-xsc

# Verify the build
ls -lh /tmp/bash-xsc/
```

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Core Concepts](#core-concepts)
4. [Your First Build](#your-first-build)
5. [Understanding Opinions](#understanding-opinions)
6. [Configuration](#configuration)
7. [Common Workflows](#common-workflows)
8. [Troubleshooting](#troubleshooting)
9. [Next Steps](#next-steps)

## Prerequisites

### System Requirements

- **OS**: Debian Bookworm (12) or Ubuntu 22.04+ (for native builds)
- **Docker**: Required for containerized builds (recommended)
- **Python**: 3.10 or newer
- **Disk Space**: 10GB+ free (for sources and build artifacts)
- **Memory**: 4GB+ RAM (8GB+ for larger packages like Linux kernel)

### Required Tools

```bash
# Debian/Ubuntu
sudo apt-get update
sudo apt-get install -y \
  python3 python3-pip python3-yaml \
  docker.io \
  build-essential dpkg-dev \
  git

# Add your user to docker group (logout/login required)
sudo usermod -aG docker $USER
```

### Optional Tools

```bash
# For package signing
sudo apt-get install -y gnupg debsig-verify

# For verification and analysis
sudo apt-get install -y \
  binutils objdump readelf \
  file diffoscope
```

## Installation

### Option 1: Development Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/jgowdy/lebowski.git
cd lebowski

# Clone the opinions repository
git clone https://github.com/jgowdy/lebowski-opinions.git

# Install Python dependencies
cd build-tool
pip3 install -r requirements.txt

# Run from source
python3 -m lebowski.cli --help
```

### Option 2: System Installation

```bash
# Clone and install
git clone https://github.com/jgowdy/lebowski.git
cd lebowski/build-tool
sudo pip3 install -e .

# Now 'lebowski' command is available system-wide
lebowski --help
```

### Verify Installation

```bash
# Check Docker is working
docker run hello-world

# Check Lebowski CLI
python3 -m lebowski.cli --version

# Check opinions repository
ls ../lebowski-opinions/bash/
```

## Core Concepts

### 1. Opinions

**Opinions** are YAML files that define how to modify a package build:

```yaml
version: "1.0"
package: bash
opinion_name: xsc
purity_level: configure-only

modifications:
  cflags:
    - "-O3"
    - "-march=native"
  configure_args:
    - "--enable-static-link"
```

### 2. Purity Levels

Trust levels indicating how invasive modifications are:

| Level | Description | Trust |
|-------|-------------|-------|
| `pure-compilation` | Only compiler flags | HIGHEST |
| `configure-only` | Configure args + flags | HIGH |
| `debian-patches` | Uses Debian patches | MEDIUM-HIGH |
| `upstream-patches` | Upstream patches | MEDIUM |
| `third-party-patches` | External patches | LOWER |
| `custom` | Custom modifications | LOWEST |

### 3. Build Container

Lebowski uses Docker containers for reproducible builds:

- **Standard**: `lebowski/builder:bookworm` (Debian Bookworm)
- **XSC**: `lebowski/builder:xsc` (with XSC toolchain)

Containers ensure builds are isolated and reproducible.

### 4. Opinion Inheritance

Opinions can extend other opinions:

```yaml
extends: ../_base/xsc.yaml

modifications:
  cflags:
    - "-DEXTRA_FEATURE"  # Added to base opinion flags
```

## Your First Build

### Example 1: Build Bash with XSC Optimization

```bash
cd lebowski/build-tool

# Build bash with zero-syscall optimization
python3 -m lebowski.cli build bash \
  --opinion-file ../lebowski-opinions/bash/xsc.yaml \
  --output-dir /tmp/bash-xsc \
  --verbose

# Check output
ls -lh /tmp/bash-xsc/
# bash_5.1-6_amd64.deb
# bash_5.1-6_amd64.lebowski-manifest.json
```

### Example 2: Build with Native CPU Optimization

```bash
# Build bash optimized for your specific CPU
python3 -m lebowski.cli build bash \
  --opinion-file ../lebowski-opinions/bash/xsc.yaml \
  --output-dir /tmp/bash-native \
  --verbose

# The opinion includes -march=native for CPU-specific optimizations
```

### Example 3: Build with Hardening (Intel CET)

```bash
# Build bash with hardware security features (requires CET-capable CPU)
python3 -m lebowski.cli build bash \
  --opinion-file ../lebowski-opinions/bash/xsc-hardened.yaml \
  --output-dir /tmp/bash-hardened \
  --verbose

# Verify CET is enabled
dpkg-deb -x /tmp/bash-hardened/bash_*.deb /tmp/bash-verify
readelf -n /tmp/bash-verify/bin/bash | grep "x86 feature"
```

### Understanding Build Output

After a successful build, you'll find:

```
/tmp/bash-xsc/
├── bash_5.1-6_amd64.deb              # The built package
├── bash_5.1-6_amd64.lebowski-manifest.json  # Build metadata
├── bash-dbgsym_5.1-6_amd64.deb       # Debug symbols (if built)
└── build.log                          # Detailed build log
```

**Manifest File** contains:
- Opinion used
- Compiler flags applied
- Build timestamp
- Package checksums
- Verification commands

### Installing Your Built Package

```bash
# Install the package
sudo dpkg -i /tmp/bash-xsc/bash_5.1-6_amd64.deb

# Check version
bash --version

# Uninstall if needed
sudo apt-get install --reinstall bash
```

## Understanding Opinions

### Opinion Structure

```yaml
version: "1.0"
package: nginx
opinion_name: high-performance
purity_level: configure-only

description: |
  Nginx built for maximum performance with aggressive optimizations.

maintainer:
  name: Your Name
  email: you@example.com

tags: [nginx, performance, web-server]

modifications:
  # Configure arguments (./configure)
  configure_args:
    - "--with-threads"
    - "--with-http_v2_module"

  # C compiler flags
  cflags:
    - "-O3"
    - "-march=native"
    - "-flto"

  # C++ compiler flags
  cxxflags:
    - "-O3"
    - "-march=native"

  # Linker flags
  ldflags:
    - "-flto"
    - "-Wl,-O2"

  # Environment variables
  env:
    DEB_BUILD_OPTIONS: "parallel=8"

  # Build dependencies (if needed)
  build_deps:
    - libpcre3-dev
    - zlib1g-dev
```

### Available Opinions

Browse the opinions repository:

```bash
cd lebowski-opinions

# List available packages
ls -d */

# List opinions for bash
ls bash/
# xsc.yaml           - Zero-syscall optimization
# xsc-hardened.yaml  - With Intel CET hardening

# List base opinions (reusable)
ls _base/
# xsc.yaml           - Base XSC configuration
# xsc-hardened.yaml  - Base hardened configuration
```

### Creating Your Own Opinion

1. **Copy an existing opinion**:

```bash
cp lebowski-opinions/bash/xsc.yaml lebowski-opinions/bash/my-custom.yaml
```

2. **Edit the opinion**:

```yaml
version: "1.0"
package: bash
opinion_name: my-custom
purity_level: configure-only

description: |
  My custom bash build with specific optimizations.

modifications:
  cflags:
    - "-O3"
    - "-march=skylake"  # Specific CPU architecture
    - "-DMY_CUSTOM_FLAG"

  configure_args:
    - "--enable-static-link"
```

3. **Build with your opinion**:

```bash
python3 -m lebowski.cli build bash \
  --opinion-file ../lebowski-opinions/bash/my-custom.yaml \
  --output-dir /tmp/bash-custom
```

## Configuration

### User Configuration File

Lebowski supports a config file at `~/.config/lebowski/config.yaml`:

```bash
mkdir -p ~/.config/lebowski

cat > ~/.config/lebowski/config.yaml <<EOF
version: "1.0"

# Global defaults applied to all builds
defaults:
  optimization_level: 3
  architecture: native
  lto: true
  hardening: true

# Build configuration
build:
  use_container: true
  container_image: "lebowski/builder:bookworm"
  parallel_jobs: null  # Auto-detect CPU count

# Package signing (optional)
signing:
  enabled: false
  auto_sign: false

# Opinion repositories
repositories:
  official:
    url: "https://github.com/jgowdy/lebowski-opinions"
    branch: "main"
    enabled: true

# Package-specific default opinions
packages:
  bash: "xsc"
  nginx: "high-performance"
EOF
```

### Configuration Precedence

1. **CLI flags** (highest priority)
2. **User config** (`~/.config/lebowski/config.yaml`)
3. **System config** (`/etc/lebowski.conf`)
4. **Built-in defaults** (lowest priority)

### Example: Global Optimization

```yaml
# ~/.config/lebowski/config.yaml
defaults:
  optimization_level: 3       # -O3 for all builds
  architecture: "x86-64-v3"   # Use x86-64-v3 baseline
  lto: true                   # Enable link-time optimization
  hardening: true             # Enable security hardening

  cflags:
    - "-pipe"                 # Use pipes instead of temp files
    - "-fomit-frame-pointer"  # Remove frame pointer
```

Now all builds will use these flags by default.

## Common Workflows

### Workflow 1: Optimize for Your Machine

```bash
# Create config with native optimization
cat > ~/.config/lebowski/config.yaml <<EOF
defaults:
  architecture: native  # Optimize for this CPU
  optimization_level: 3
  lto: true
EOF

# Build any package with native optimizations
python3 -m lebowski.cli build bash \
  --opinion-file ../lebowski-opinions/bash/xsc.yaml
```

### Workflow 2: Signed Package Distribution

```bash
# Enable auto-signing
cat > ~/.config/lebowski/config.yaml <<EOF
signing:
  enabled: true
  auto_sign: true
  export_public_key: true
EOF

# Build and sign
python3 -m lebowski.cli build bash \
  --opinion-file ../lebowski-opinions/bash/xsc.yaml \
  --output-dir /tmp/bash-signed

# Output includes:
# - bash_5.1-6_amd64.deb
# - bash_5.1-6_amd64.deb.sig (signature)
# - lebowski-public-key.asc (public key for verification)
```

### Workflow 3: Build Multiple Packages

```bash
#!/bin/bash
# build-suite.sh

PACKAGES="bash coreutils grep sed gawk"
OPINION_BASE="../lebowski-opinions"
OUTPUT_BASE="/tmp/lebowski-builds"

for pkg in $PACKAGES; do
  echo "Building $pkg..."
  python3 -m lebowski.cli build "$pkg" \
    --opinion-file "$OPINION_BASE/$pkg/xsc.yaml" \
    --output-dir "$OUTPUT_BASE/$pkg" \
    --verbose
done

echo "All builds complete. Output in $OUTPUT_BASE/"
```

### Workflow 4: CI/CD Integration

```yaml
# .github/workflows/build.yml
name: Build Packages

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Docker
        run: docker pull lebowski/builder:bookworm

      - name: Build bash
        run: |
          cd build-tool
          python3 -m lebowski.cli build bash \
            --opinion-file ../lebowski-opinions/bash/xsc.yaml \
            --output-dir ./artifacts

      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: packages
          path: build-tool/artifacts/*.deb
```

## Troubleshooting

### Common Issues

#### 1. "Docker permission denied"

```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

#### 2. "Opinion file not found"

```bash
# Ensure you cloned the opinions repository
git clone https://github.com/jgowdy/lebowski-opinions.git

# Use correct path to opinion file
python3 -m lebowski.cli build bash \
  --opinion-file ../lebowski-opinions/bash/xsc.yaml
```

#### 3. "Failed to download source package"

```bash
# Update apt sources in container
# This is automatic, but you can force rebuild:
docker pull lebowski/builder:bookworm
```

#### 4. "Build failed with compiler error"

```bash
# Check if flags are compatible
# Some aggressive optimizations may cause issues
# Try with less aggressive flags first:
-O2 instead of -O3
Remove -march=native if targeting generic builds
```

#### 5. "XSC toolchain not found"

```bash
# XSC requires special container image
# Make sure opinion specifies:
container_image: "lebowski/builder:xsc"

# Or set in config:
build:
  container_image: "lebowski/builder:xsc"
```

### Getting Help

- **Documentation**: See `docs/` directory
- **GitHub Issues**: https://github.com/jgowdy/lebowski/issues
- **Opinion Examples**: `lebowski-opinions/` repository

### Debug Mode

```bash
# Enable verbose output
python3 -m lebowski.cli build bash \
  --opinion-file ../lebowski-opinions/bash/xsc.yaml \
  --verbose \
  --keep-sources  # Keep build directory for inspection
```

## Next Steps

### Learning More

1. **Read Core Documentation**:
   - [Opinions Format](OPINIONS.md) - Complete opinion reference
   - [Package Signing](PACKAGE-SIGNING.md) - GPG signing setup
   - [XSC Integration](XSC-INTEGRATION.md) - Zero-syscall builds
   - [Data-Driven Toolchains](DATA-DRIVEN-TOOLCHAINS.md) - Custom toolchains

2. **Advanced Topics**:
   - [CPU Baseline Optimization](XSC-CPU-BASELINE.md)
   - [Microarchitecture Levels](XSC-MICROARCH-LEVELS.md)
   - [Aggressive Optimizations](XSC-AGGRESSIVE-OPTS.md)

3. **Reference**:
   - [CLI Reference](CLI-REFERENCE.md) - Complete CLI documentation
   - [Config Reference](CONFIG-REFERENCE.md) - All config options

### Example Projects

1. **Build an optimized system**:
   - Build core packages (bash, coreutils, grep, sed)
   - Create local APT repository
   - Install optimized packages

2. **Create custom opinions**:
   - Fork lebowski-opinions repository
   - Add your own optimization profiles
   - Share with community

3. **Set up CI/CD**:
   - Automate package builds on commits
   - Sign packages with GPG
   - Publish to repository

### Contributing

Lebowski is an open-source project. Contributions welcome:

- Submit opinions to lebowski-opinions repository
- Report bugs and request features
- Improve documentation
- Add new features to the build tool

## Summary

You now know how to:

- ✅ Install Lebowski and its dependencies
- ✅ Build packages with opinions
- ✅ Understand purity levels and trust
- ✅ Create and customize opinions
- ✅ Configure global defaults
- ✅ Troubleshoot common issues

**Quick Reference**:

```bash
# Standard build
python3 -m lebowski.cli build <package> \
  --opinion-file <opinion.yaml> \
  --output-dir <output>

# With signing
python3 -m lebowski.cli build <package> \
  --opinion-file <opinion.yaml> \
  --auto-sign

# Verbose mode
python3 -m lebowski.cli build <package> \
  --opinion-file <opinion.yaml> \
  --verbose
```

Happy building!
