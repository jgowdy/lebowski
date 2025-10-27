# apt-Style CLI Design for Lebowski

This document describes the apt/apt-get-inspired command structure for Lebowski, making it feel familiar and enabling aliasing or plugin development.

## Design Goals

1. **Familiar**: Mirror apt/apt-get command patterns
2. **Aliasable**: Allow `alias apt=lebowski` to work naturally
3. **Plugin-ready**: Enable Lebowski to act as apt frontend
4. **Backward-compatible**: Maintain current CLI for scripts

## Command Mapping

### Current vs Proposed

| Current | apt-style | Description |
|---------|-----------|-------------|
| `lebowski build bash --opinion-file ...` | `lebowski build bash` | Build package |
| N/A | `lebowski install bash` | Build and install |
| N/A | `lebowski source bash` | Download source |
| N/A | `lebowski show bash` | Show package opinions |
| N/A | `lebowski search bash` | Search for packages |
| `lebowski verify <manifest>` | `lebowski verify bash` | Verify build |
| N/A | `lebowski update` | Update opinion repositories |

### apt/apt-get Command Reference

For comparison, here are the main apt commands we're mimicking:

```bash
# Package operations
apt install <package>         # Download and install
apt remove <package>          # Remove package
apt purge <package>           # Remove with config
apt upgrade                   # Upgrade all packages
apt full-upgrade             # Upgrade with removals

# Information commands
apt show <package>            # Show package info
apt search <pattern>          # Search packages
apt list                      # List packages

# Source operations
apt-get source <package>      # Download source
apt-get build-dep <package>   # Install build deps
apt-get build <package>       # Build from source

# Repository operations
apt update                    # Update package lists
apt-cache show <package>      # Show package info
apt-cache search <pattern>    # Search cache
```

## Proposed Lebowski Commands

### Build Operations

#### `lebowski build <package> [OPTIONS]`

Build a package from source with an opinion.

**Examples:**

```bash
# Build with default opinion (from config)
lebowski build bash

# Build with specific opinion
lebowski build bash -o xsc
lebowski build bash --opinion xsc

# Build with opinion file path (backward compat)
lebowski build bash --opinion-file opinions/bash/xsc.yaml

# Build with opinion from repository
lebowski build bash -o official:xsc-hardened

# Build to specific output directory
lebowski build bash --output-dir /tmp/bash-xsc

# Build with signing
lebowski build bash --auto-sign
lebowski build bash --sign-key ABCD1234
```

**Options:**

```
-o, --opinion OPINION        Opinion name (e.g., 'xsc', 'official:xsc')
--opinion-file PATH          Opinion file path (backward compat)
--output-dir DIR             Output directory (default: ./output)
--auto-sign                  Auto-sign with Lebowski key
--sign-key KEY_ID            Sign with specific GPG key
-v, --verbose                Verbose output
--keep-sources               Keep build directory
--no-container               Build without container
```

**Opinion Resolution:**

1. If `--opinion-file` provided: use that file
2. If `--opinion` provided: lookup in repositories
3. If config has default opinion for package: use that
4. Otherwise: error (require explicit opinion)

#### `lebowski install <package> [OPTIONS]`

Build and install a package.

**Examples:**

```bash
# Build and install bash with default opinion
lebowski install bash

# Build with specific opinion and install
lebowski install bash -o xsc-hardened

# Install without confirmation
lebowski install -y bash
```

**Options:**

```
-o, --opinion OPINION        Opinion to use
-y, --yes                    Automatic yes to prompts
--output-dir DIR             Save .deb before installing
--auto-sign                  Auto-sign package
```

**Implementation:**

1. Build package (same as `build` command)
2. Run `sudo dpkg -i <package>.deb`
3. Run `sudo apt-get install -f` to fix deps

### Information Commands

#### `lebowski show <package>`

Show available opinions for a package.

**Examples:**

```bash
# Show all opinions for bash
lebowski show bash

# Output:
# Package: bash
# Available opinions:
#   - xsc (official)
#     Purity: configure-only
#     Description: Zero-syscall optimized bash
#
#   - xsc-hardened (official)
#     Purity: configure-only
#     Description: XSC + Intel CET hardening
#
# Default opinion: xsc (from config)
```

#### `lebowski search <pattern>`

Search for packages with opinions.

**Examples:**

```bash
# Search for web servers
lebowski search nginx

# Output:
# nginx - High-performance HTTP server
#   Opinions: high-performance, security-hardened
```

#### `lebowski list [OPTIONS]`

List packages with opinions.

**Examples:**

```bash
# List all packages
lebowski list

# List installed Lebowski-built packages
lebowski list --installed

# List packages with opinion tag
lebowski list --tag xsc
```

### Source Operations

#### `lebowski source <package>`

Download package source code.

**Examples:**

```bash
# Download bash source
lebowski source bash

# Download to specific directory
lebowski source bash --output-dir ~/src/bash

# Download and extract
lebowski source bash --extract
```

### Repository Operations

#### `lebowski update`

Update opinion repositories.

**Examples:**

```bash
# Update all repositories
lebowski update

# Update specific repository
lebowski update official

# Output:
# Updating opinion repository: official
# Fetching https://github.com/jgowdy/lebowski-opinions
# Updated 127 opinions (3 new, 12 modified)
```

### Verification Commands

#### `lebowski verify <package>`

Verify a built package or manifest.

**Examples:**

```bash
# Verify from manifest file (current)
lebowski verify bash_5.1-6.lebowski-manifest.json

# Verify package name (finds latest build)
lebowski verify bash

# Verify and show details
lebowski verify bash --verbose

# Verify with rebuild
lebowski verify bash --rebuild
```

### Configuration Commands

#### `lebowski config [OPTIONS]`

Manage Lebowski configuration.

**Examples:**

```bash
# Show current config
lebowski config show

# Set default opinion for package
lebowski config set-default bash xsc

# Enable signing
lebowski config set signing.enabled true
lebowski config set signing.auto_sign true

# Add opinion repository
lebowski config add-repo custom https://github.com/user/opinions

# Generate example config
lebowski config init
```

## Opinion Resolution

Opinions can be specified in multiple ways:

### 1. Short Name (Default Repository)

```bash
lebowski build bash -o xsc
# Looks in default repository (usually 'official')
# Resolves to: lebowski-opinions/bash/xsc.yaml
```

### 2. Repository:Name

```bash
lebowski build bash -o official:xsc-hardened
# Explicitly specify repository
# Resolves to: official repository -> bash/xsc-hardened.yaml
```

### 3. File Path (Backward Compatibility)

```bash
lebowski build bash --opinion-file ../opinions/bash/custom.yaml
# Direct file path
# No repository lookup
```

### 4. Config Default

```yaml
# ~/.config/lebowski/config.yaml
packages:
  bash: xsc
  nginx: high-performance
```

```bash
lebowski build bash
# Uses 'xsc' opinion from config
```

## Configuration Integration

### Repository Configuration

```yaml
# ~/.config/lebowski/config.yaml
repositories:
  official:
    url: "https://github.com/jgowdy/lebowski-opinions"
    branch: "main"
    cache_ttl: 86400
    enabled: true

  custom:
    url: "https://github.com/myuser/my-opinions"
    branch: "main"
    enabled: true

# Default repository for short names
default_repository: official
```

### Package Defaults

```yaml
# ~/.config/lebowski/config.yaml
packages:
  bash: xsc
  nginx: high-performance
  postgresql: server-hardened
  linux: desktop-1000hz
```

When no opinion is specified, use these defaults.

## apt-get Plugin / Alias Design

### Aliasing apt to lebowski

```bash
# ~/.bashrc or ~/.zshrc
alias apt='lebowski-apt-wrapper'
```

### Wrapper Script

```bash
#!/bin/bash
# lebowski-apt-wrapper

# Check if package has a Lebowski opinion
if lebowski show "$2" &>/dev/null; then
    case "$1" in
        install)
            lebowski install "$2" "${@:3}"
            ;;
        build-dep)
            # Fall back to real apt-get for build deps
            apt-get "$@"
            ;;
        source)
            lebowski source "$2" "${@:3}"
            ;;
        *)
            # Pass through to real apt
            apt "$@"
            ;;
    esac
else
    # Package not in Lebowski, use real apt
    apt "$@"
fi
```

### apt Plugin (dpkg frontend)

Lebowski could register as a dpkg frontend:

```bash
# /usr/share/apt/methods/lebowski
# Makes apt aware of Lebowski-built packages
```

## Implementation Plan

### Phase 1: Core apt-style Commands

1. **Refactor CLI parser** (`lebowski/cli.py`):
   - Support positional package argument
   - Add `-o/--opinion` short flag
   - Maintain backward compatibility with `--opinion-file`

2. **Opinion resolution** (`lebowski/opinion_resolver.py` - NEW):
   - Lookup by name in repositories
   - Support `repo:name` syntax
   - Fall back to config defaults
   - Cache resolved opinions

3. **Repository management** (`lebowski/repo_manager.py` - NEW):
   - Clone/update git repositories
   - Index available opinions
   - Search and list functions

### Phase 2: Additional Commands

4. **Install command** (`lebowski/commands/install.py` - NEW):
   - Build package
   - Run `dpkg -i`
   - Handle dependencies

5. **Show/search commands** (`lebowski/commands/info.py` - NEW):
   - List available opinions
   - Show opinion details
   - Search functionality

6. **Update command** (`lebowski/commands/update.py` - NEW):
   - Update opinion repositories
   - Show what changed

### Phase 3: Integration

7. **apt wrapper script**:
   - Install to `/usr/local/bin/lebowski-apt-wrapper`
   - Provide alias setup instructions

8. **Plugin development**:
   - apt method handler
   - dpkg frontend registration

## Examples: Before and After

### Before (Current)

```bash
# Build bash
python3 -m lebowski.cli build bash \
  --opinion-file ../lebowski-opinions/bash/xsc.yaml \
  --output-dir /tmp/bash-xsc \
  --verbose

# Build and install nginx
python3 -m lebowski.cli build nginx \
  --opinion-file ../lebowski-opinions/nginx/high-performance.yaml \
  --output-dir /tmp/nginx
sudo dpkg -i /tmp/nginx/nginx*.deb
```

### After (apt-style)

```bash
# Build bash
lebowski build bash -o xsc

# Build and install nginx
lebowski install nginx -o high-performance

# Or with aliasing:
alias apt=lebowski
apt install nginx  # Uses Lebowski with configured opinion
```

## Backward Compatibility

All existing commands continue to work:

```bash
# Old style still works
lebowski build bash --opinion-file opinions/bash/xsc.yaml --output-dir /tmp/bash

# New style is shorter
lebowski build bash -o xsc
```

## Command Reference Summary

```bash
# Build operations
lebowski build <package> [-o OPINION]
lebowski install <package> [-o OPINION] [-y]

# Information
lebowski show <package>
lebowski search <pattern>
lebowski list [--installed] [--tag TAG]

# Source operations
lebowski source <package>

# Repository management
lebowski update [REPO]

# Verification
lebowski verify <package|manifest>

# Configuration
lebowski config show
lebowski config set KEY VALUE
lebowski config set-default PACKAGE OPINION
lebowski config add-repo NAME URL

# Legacy (backward compat)
lebowski build <package> --opinion-file PATH
```

## Benefits

1. **Familiar**: Users who know apt will immediately understand Lebowski
2. **Shorter commands**: `lebowski build bash -o xsc` vs long --opinion-file path
3. **Configuration-driven**: Default opinions per package
4. **Repository system**: Centralized opinion distribution
5. **Aliasable**: Can actually replace apt for Lebowski-built packages
6. **Plugin-ready**: Can integrate with apt ecosystem

## Next Steps

1. Implement Phase 1 (core commands and opinion resolution)
2. Update documentation and examples
3. Test backward compatibility
4. Implement Phase 2 (additional commands)
5. Create apt-wrapper script
6. Document plugin development
