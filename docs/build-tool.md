# Lebowski Build Tool

## Overview

The `lebowski` CLI tool automates building Debian packages with custom opinions. It handles fetching sources, applying modifications, and building packages - making it as easy as FreeBSD ports.

## Core Workflow

```
1. User runs: lebowski build nginx --opinion http3

2. Tool does:
   ├─ Fetch Debian source package for nginx
   ├─ Download http3.yaml opinion from opinions repo
   ├─ Parse opinion YAML
   ├─ Apply modifications to source
   ├─ Build package
   └─ Output: nginx-http3_VERSION.deb

3. User installs: sudo dpkg -i nginx-http3_VERSION.deb
```

## Commands

### `lebowski build`

Build a package with an opinion.

```bash
lebowski build <package> --opinion <name>
lebowski build <package> -o <name>

# Examples:
lebowski build nginx --opinion http3
lebowski build python3 -o optimized
lebowski build gcc-13 -o native

# Build with local opinion file
lebowski build nginx --opinion-file ./my-opinion.yaml

# Build without opinion (just stock Debian)
lebowski build nginx
```

**Options:**
- `--opinion <name>` - Opinion name from repository
- `--opinion-file <path>` - Local opinion file
- `--output-dir <path>` - Where to put built packages (default: current dir)
- `--keep-sources` - Don't delete source directory after build
- `--debian-version <version>` - Specific Debian version (bookworm, bullseye, etc.)
- `--arch <arch>` - Architecture (default: current system)
- `--jobs <n>` - Parallel jobs for build (default: nproc)

### `lebowski search`

Search for available opinions.

```bash
lebowski search <package>

# Examples:
lebowski search nginx
# Output:
#   nginx:
#     - http3: nginx with HTTP/3 support
#     - minimal: stripped down nginx
#     - full: all modules enabled

lebowski search --all
# List all available opinions for all packages
```

### `lebowski show`

Show details about an opinion.

```bash
lebowski show <package>:<opinion>

# Example:
lebowski show nginx:http3
# Output:
#   Opinion: nginx:http3
#   Description: nginx with HTTP/3 (QUIC) support
#   Maintainer: Lebowski Project
#   Tags: experimental, performance
#   Modifications:
#     - Adds build dependency: libquiche-dev
#     - Adds configure flag: --with-http_v3_module
#     - Applies patches: http3-default-port.patch
```

### `lebowski validate`

Validate an opinion file.

```bash
lebowski validate <opinion-file>

# Example:
lebowski validate opinions/nginx/http3.yaml
# Output:
#   ✓ YAML syntax valid
#   ✓ Required fields present
#   ✓ Patch files exist
#   ✓ No dangerous operations detected
```

### `lebowski init`

Initialize a new opinion.

```bash
lebowski init <package> <opinion-name>

# Example:
lebowski init nginx my-custom
# Creates: opinions/nginx/my-custom.yaml with template
```

### `lebowski list`

List installed Lebowski-built packages.

```bash
lebowski list
# Output:
#   nginx-http3 1.24.0-1~opinion1 (opinion: http3)
#   python3-optimized 3.11.2-1~opinion1 (opinion: optimized)
```

## Internal Implementation

### Step 1: Fetch Debian Source

```bash
# Add deb-src to sources.list if needed
apt-get source <package>

# Or use specific version
apt-get source <package>=<version>
```

Downloads to: `<package>-<version>/`

### Step 2: Parse Opinion

Read and validate YAML opinion file.

### Step 3: Apply Modifications

Based on opinion type:

#### Patches
```bash
cd <package-source>
for patch in opinion.patches:
    patch -p1 < $patch
```

#### Configure Flags
Modify `debian/rules`:
```bash
# Find configure line
# Add/remove/replace flags
```

#### Build Dependencies
Modify `debian/control`:
```bash
# Add to Build-Depends:
```

#### Compiler Flags
Set environment variables or modify debian/rules:
```bash
export DEB_CFLAGS_APPEND="-march=znver3"
```

#### Scripts
Run pre-build scripts:
```bash
bash opinion.scripts.pre_build
```

### Step 4: Build Package

```bash
cd <package-source>

# Install build dependencies
sudo apt-get build-dep .

# Build
dpkg-buildpackage -us -uc -b

# Result: ../*.deb
```

### Step 5: Post-processing

- Run post-build scripts if defined
- Rename package to include opinion name
- Move to output directory
- Clean up sources unless --keep-sources

## Technical Considerations

### Debian Tools Required

The build tool requires:
- `apt-get` - for fetching sources
- `dpkg-buildpackage` - for building packages
- `dpkg-dev` - development tools
- `devscripts` - helper scripts
- `build-essential` - compiler, make, etc.

Install:
```bash
sudo apt-get install build-essential devscripts dpkg-dev
```

### Opinion Repository

Opinions fetched from Git repository:
```bash
# Clone on first use
git clone https://github.com/lebowski-project/opinions.git ~/.lebowski/opinions

# Update before each build
cd ~/.lebowski/opinions
git pull
```

Config:
```yaml
# ~/.lebowski/config.yaml
opinion_repo: https://github.com/lebowski-project/opinions.git
cache_dir: ~/.lebowski/cache
output_dir: ~/lebowski-builds
```

### Package Naming

Built packages renamed to include opinion:

```
Original:  nginx_1.24.0-1_amd64.deb
With opinion: nginx-http3_1.24.0-1~opinion1_amd64.deb
```

Version scheme: `<version>~opinion<N>`
- `~` ensures official packages have priority
- `opinion<N>` identifies this as Lebowski build
- Incrementing N allows multiple opinions of same version

### Caching

Cache downloaded sources:
```
~/.lebowski/cache/
  ├── sources/
  │   └── nginx_1.24.0.orig.tar.gz
  └── built/
      └── nginx-http3_1.24.0-1~opinion1_amd64.deb
```

### Safety

Before applying modifications:
1. Validate opinion file
2. Check for dangerous operations (removing security patches, etc.)
3. Warn user about experimental opinions
4. Show diff of what will be changed

### Reproducible Builds

Optional: Support reproducible builds
- Use fixed timestamps
- Fixed build environment
- Deterministic sorting
- Document build environment

## Implementation Language

Options:

### Python
**Pros:**
- Rich ecosystem
- Easy YAML parsing (PyYAML)
- Good subprocess handling
- Debian-focused libraries available

**Cons:**
- Runtime dependency
- Slower startup

### Go
**Pros:**
- Single binary, no runtime
- Fast
- Good YAML libraries

**Cons:**
- Less Debian ecosystem

### Bash
**Pros:**
- No dependencies
- Native to Debian

**Cons:**
- Complex logic harder
- YAML parsing difficult

**Recommendation: Python**
- Rich Debian ecosystem
- Easy to parse YAML
- Good for MVP
- Can rewrite in Go later if needed

## Example Implementation Structure

```
lebowski/
├── lebowski/
│   ├── __init__.py
│   ├── cli.py              # CLI interface (argparse/click)
│   ├── builder.py          # Core build logic
│   ├── opinion.py          # Opinion parsing/validation
│   ├── source.py           # Debian source fetching
│   ├── modifier.py         # Apply modifications
│   └── config.py           # Configuration
├── tests/
│   ├── test_opinion.py
│   └── test_builder.py
├── setup.py
└── README.md
```

## Development Plan

1. **Core opinion parser** - Read and validate YAML
2. **Source fetcher** - Download Debian sources
3. **Basic modifier** - Apply simple modifications
4. **Builder** - Invoke dpkg-buildpackage
5. **CLI** - User interface
6. **Opinion repository** - Set up Git repo with sample opinions
7. **Testing** - Build real packages with opinions
8. **Documentation** - User guide, opinion author guide
9. **Polish** - Error handling, caching, etc.

## Alpha Release Checklist

- [ ] Parser for opinion YAML format
- [ ] Fetch Debian source packages
- [ ] Apply patches
- [ ] Modify debian/rules for configure flags
- [ ] Modify debian/control for build deps
- [ ] Build package with dpkg-buildpackage
- [ ] Rename output with opinion name
- [ ] CLI with build command
- [ ] At least 3 working example opinions
- [ ] Basic error handling
- [ ] README with installation instructions
