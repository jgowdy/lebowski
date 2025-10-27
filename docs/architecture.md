# Lebowski Architecture

## Core Vision

Lebowski provides **two paths** to customized Debian packages:

1. **Easy Source Builds** - Make building from source as easy as FreeBSD ports (**Phase 1 - MVP**)
2. **Pre-built Opinions** - Popular variants available as ready-to-install binaries (**Phase 2 - Future**)

## Phase 1 Focus

The MVP focuses on **opinion definitions** - providing the diff/formula/script for opinions, which users apply locally to build packages themselves. Pre-built packages come later.

## The "Opinion" Concept

An "opinion" is a Debian package with a different decision:
- **Compiler flags** - e.g., `-march=znver3` instead of generic x86_64
- **Feature toggles** - e.g., nginx with/without HTTP3
- **Patches** - e.g., cherry-picked fixes or features
- **Build decisions** - e.g., different defaults, different splits
- **Optimizations** - e.g., -O3 instead of -O2, LTO enabled

The base is always the **stock Debian package** - we just tweak it.

## Two-Path Approach

### Path 1: Easy Source Building

Like FreeBSD ports, make it trivial to build from source:

```bash
# Browse available options for a package
lebowski show nginx

# Build with custom options
lebowski build nginx --with-http3 --march=native

# Install your custom build
lebowski install ./nginx*.deb
```

**Benefits:**
- Full control
- Build for your specific hardware
- Custom combinations
- Learning and experimentation

### Path 2: Pre-built Opinions

Popular opinions pre-built and hosted:

```bash
# Browse available pre-built variants
lebowski search nginx
# Results:
#   nginx (official Debian)
#   nginx-minimal (minimal feature set)
#   nginx-full (all features enabled)
#   nginx-http3 (with QUIC/HTTP3)
#   nginx-znver3 (AMD Zen3 optimized)

# Install pre-built variant
lebowski install nginx-http3
```

**Benefits:**
- Fast installation (seconds)
- No compilation needed
- Popular configurations ready to go
- Curated and tested

## Architecture Components

### 1. Opinion Definitions

Declarative files defining how to modify stock Debian packages:

```yaml
# opinions/nginx/http3.yaml
package: nginx
base: debian  # Use Debian source package
opinion_name: http3
description: nginx with HTTP/3 (QUIC) support

modifications:
  configure_flags:
    add:
      - --with-http_v3_module
      - --with-stream_quic_module
  dependencies:
    build_add:
      - libquiche-dev

metadata:
  maintainer: community
  tags: [experimental, performance]
```

### 2. Build System

Takes opinion definitions + Debian source packages:

```
Debian Source Package
         +
Opinion Definition
         ↓
   Build System
         ↓
  Modified .deb
```

**Features:**
- Fetch Debian source automatically
- Apply modifications from opinion file
- Build the package
- Optional: Make reproducible
- Optional: Sign package

### 3. Local Build Tool

User-friendly CLI for building locally:

```bash
lebowski build <package> [--opinion <name>] [--flags ...]
```

Simple as FreeBSD ports, but for Debian.

### 4. Opinion Repository

Central repository of opinion definitions:
- Version controlled (Git)
- Community contributions (PRs)
- Organized by package
- Tagged and searchable

### 5. Binary Package Repository

APT-compatible repository hosting pre-built opinions:
- Built from opinion definitions
- Automated builds (CI/CD)
- Multiple architectures
- Signed packages

### 6. Client Tool

User-facing CLI:

```bash
lebowski search <package>    # Find available opinions
lebowski show <package>      # Show details/options
lebowski build <package>     # Build from source locally
lebowski install <variant>   # Install pre-built opinion
lebowski list                # Show installed opinions
```

## Example Workflows

### Workflow 1: Install Pre-built Opinion

```bash
# User wants nginx with HTTP/3
lebowski search nginx
lebowski install nginx-http3
# Done - installs in seconds
```

### Workflow 2: Build Custom

```bash
# User wants nginx optimized for their CPU
lebowski build nginx --march=native --with-http3
lebowski install ./nginx*.deb
```

### Workflow 3: Create New Opinion

```bash
# Developer creates new opinion
cd opinions/python3/
cp performance.yaml my-custom.yaml
# Edit my-custom.yaml
git commit
git push
# Submit PR to opinion repository
```

## Popular Opinion Categories

### Optimization Opinions
- **Generic** - Stock Debian (baseline)
- **znver3** - AMD Zen 3 optimized
- **znver4** - AMD Zen 4 optimized
- **skylake** - Intel Skylake optimized
- **native** - Optimized for build machine
- **size** - Optimize for size (-Os)
- **speed** - Optimize for speed (-O3, LTO)

### Feature Opinions
- **minimal** - Minimal features, smaller size
- **full** - All optional features enabled
- **no-telemetry** - Telemetry disabled/removed
- **experimental** - Experimental features enabled

### Security Opinions
- **hardened** - Extra hardening flags
- **paranoid** - Maximum hardening

### Patch Opinions
- **upstream-fixes** - Cherry-picked upstream fixes
- **backports** - Features backported from newer versions

## Technical Details

### Naming Convention

```
<package>-<opinion>
```

Examples:
- `nginx-http3`
- `python3-znver3`
- `gcc-13-native`
- `ffmpeg-full`

### Package Versioning

Match Debian version + opinion suffix:

```
nginx: 1.24.0-1 (official Debian)
nginx-http3: 1.24.0-1~opinion1 (Lebowski opinion)
```

The `~opinion` ensures official Debian packages take precedence if both are available.

### APT Repository Structure

```
deb https://repo.bx.ee/debian bookworm main
deb https://repo.bx.ee/opinions bookworm nginx python3 gcc
```

Or integrate into single repo with components.

### Build Automation

GitHub Actions / GitLab CI:
1. Monitor opinion repository for changes
2. On new/updated opinion:
   - Fetch Debian source
   - Apply opinion modifications
   - Build for all architectures
   - Sign packages
   - Publish to repository

## Next Steps

1. Define opinion YAML schema
2. Build prototype build tool
3. Create sample opinions for popular packages
4. Set up CI/CD for automated builds
5. Deploy APT repository
6. Build CLI tool
