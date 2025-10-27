# Lebowski Configuration System

## Overview

Lebowski supports system-wide and user-specific configuration files to set default opinions, compiler flags, and build settings. This allows users to customize their build environment without needing to specify flags every time.

## Configuration Files

### Locations

1. **System-wide**: `/etc/lebowski.conf`
   - Applies to all users on the system
   - Requires root/sudo to create
   - Useful for site-wide policies

2. **User-specific**: `~/.config/lebowski/config.yaml`
   - Applies only to the current user
   - Overrides system settings
   - No special privileges required

### Precedence

Configuration precedence (highest to lowest):

1. **CLI flags** (highest priority)
2. User configuration (`~/.config/lebowski/config.yaml`)
3. System configuration (`/etc/lebowski.conf`)
4. Built-in defaults (lowest priority)

**Example**: If system config sets `-O2` but user config sets `-O3`, the user gets `-O3`.

## Configuration Schema

### Complete Example

```yaml
version: "1.0"

# Global defaults applied to all builds
defaults:
  # Optimization level (0-3)
  optimization_level: 2

  # CPU architecture optimization
  # Options: native, x86-64, x86-64-v2, x86-64-v3, skylake, zen3, etc.
  architecture: native

  # Link-time optimization
  lto: false

  # Security hardening (stack protector, FORTIFY_SOURCE)
  hardening: true

  # Include debug symbols
  debug_symbols: false

  # Additional global flags (applied to all builds)
  cflags:
    - "-pipe"
  cxxflags: []
  ldflags: []

# Build configuration
build:
  # Always use containers for reproducibility
  use_container: true

  # Default container image
  container_image: "lebowski/builder:bookworm"

  # Parallel build jobs (null = auto-detect)
  parallel_jobs: null

  # Keep source directories after build
  keep_sources: false

  # Working directory for builds
  work_dir: "/build/lebowski"

# Opinion repositories
repositories:
  official:
    url: "https://github.com/jgowdy/lebowski-opinions"
    branch: "main"
    cache_ttl: 86400  # 24 hours
    enabled: true

# Package-specific default opinions
# When building without --opinion flag, use these
packages:
  nginx: "optimized"
  postgresql: "server-hardened"
  linux: "desktop-1000hz"
  bash: "minimal"
  python3: "optimized"

# Trust settings
# Maximum purity level to allow (rejects opinions with lower trust)
max_purity_level: "custom"
```

## Configuration Sections

### 1. Global Defaults

Controls compiler flags applied to **all builds** automatically:

```yaml
defaults:
  optimization_level: 3       # Adds -O3
  architecture: native        # Adds -march=native -mtune=native
  lto: true                   # Adds -flto
  hardening: true             # Adds -fstack-protector-strong -D_FORTIFY_SOURCE=2
  debug_symbols: false        # If true, adds -g

  cflags:
    - "-pipe"                 # Custom flags
  cxxflags: []
  ldflags: []
```

**How it works**: Global defaults are **prepended** to opinion flags, so opinions can override them.

**Example**:
- Config: `-O3 -march=native`
- Opinion: `-DXSC_BUILD -O2`
- **Result**: `-O3 -march=native -DXSC_BUILD -O2`
- (GCC uses rightmost `-O` flag, so `-O2` wins)

### 2. Build Settings

Controls how builds are executed:

```yaml
build:
  use_container: true                         # Require container builds (recommended!)
  container_image: "lebowski/builder:bookworm"  # Default container
  parallel_jobs: null                         # Auto-detect CPU cores
  keep_sources: false                         # Clean up after builds
  work_dir: "/build/lebowski"                # Build working directory
```

### 3. Opinion Repositories

Configure where to fetch opinions from:

```yaml
repositories:
  official:
    url: "https://github.com/jgowdy/lebowski-opinions"
    branch: "main"
    cache_ttl: 86400  # 24 hours in seconds
    enabled: true

  custom:
    url: "https://github.com/mycompany/our-opinions"
    branch: "production"
    enabled: true
```

**Note**: Repository integration is coming soon. Currently opinions must be local files.

### 4. Package Default Opinions

Set default opinions for packages:

```yaml
packages:
  nginx: "optimized"          # Use "optimized" opinion by default for nginx
  bash: "minimal"             # Use "minimal" opinion for bash
  postgresql: "server-hardened"
```

**Usage**:
```bash
# Without default: requires --opinion flag
lebowski build nginx --opinion optimized

# With default configured: no --opinion needed!
lebowski build nginx
# Uses "optimized" opinion automatically
```

### 5. Trust Settings

Control which opinion purity levels are allowed:

```yaml
max_purity_level: "debian-patches"  # Only allow high-trust opinions
```

**Purity levels** (highest to lowest trust):
1. `pure-compilation` - Only compiler flags (HIGHEST trust)
2. `configure-only` - Configure flags, no patches (HIGH trust)
3. `debian-patches` - Debian's own patches (MEDIUM-HIGH trust)
4. `upstream-patches` - Upstream patches (MEDIUM trust)
5. `third-party-patches` - Community patches (LOWER trust)
6. `custom` - Custom scripts (LOWEST trust)

**Example**: If `max_purity_level: "configure-only"`, opinions using patches will be rejected.

## CLI Commands

### Generate Example Configuration

```bash
# Show example config on stdout
lebowski config

# Create user configuration
lebowski config --user

# Create system configuration (requires sudo)
sudo lebowski config --system
```

### Using Configuration

Configuration is **automatically loaded** when you run `lebowski build`.

**Example output with config applied**:

```
🎬 Lebowski: Building nginx
📦 Using default opinion for nginx: optimized
✓ Opinion loaded: optimized
  Package: nginx
  Purity: configure-only (HIGH trust)
  Description: Optimized nginx build with performance tuning...

⚙️  Applied config defaults:
  Optimization: -O3
  Architecture: -march=native
  Global CFLAGS: -pipe

🔨 Starting build...
```

## Use Cases

### 1. Personal Workstation (Performance)

`~/.config/lebowski/config.yaml`:
```yaml
defaults:
  optimization_level: 3
  architecture: native
  lto: true

packages:
  "*": "optimized"  # Use optimized opinion for all packages
```

**Result**: All packages built with `-O3 -march=native -flto`

### 2. Production Server (Stability)

`/etc/lebowski.conf`:
```yaml
defaults:
  optimization_level: 2
  architecture: x86-64-v2  # Broad compatibility
  hardening: true

build:
  use_container: true  # Enforce reproducibility

max_purity_level: "configure-only"  # Only high-trust opinions
```

**Result**: Stable, reproducible, secure builds

### 3. Development Workstation (Debug)

`~/.config/lebowski/config.yaml`:
```yaml
defaults:
  optimization_level: 0
  debug_symbols: true

build:
  keep_sources: true  # Keep sources for debugging
```

**Result**: All packages built with `-O0 -g` for debugging

### 4. XSC-Enabled System

`/etc/lebowski.conf`:
```yaml
defaults:
  optimization_level: 2

build:
  container_image: "lebowski/builder:xsc"
  work_dir: "/build/xsc"

packages:
  bash: "xsc"
  coreutils: "xsc"
  nginx: "xsc-optimized"
```

**Result**: All critical packages use XSC toolchain with zero-syscall binaries

## How Configuration Affects Opinions

### Flag Application Order

1. **Config defaults are prepended** to opinion flags
2. **Opinion flags come last** and can override

**Example**:

Config:
```yaml
defaults:
  optimization_level: 3       # Adds -O3 first
  cflags: ["-pipe"]
```

Opinion:
```yaml
modifications:
  cflags:
    - "-DXSC_BUILD"
    - "-O2"                    # Overrides -O3
```

**Final CFLAGS**: `-O3 -pipe -DXSC_BUILD -O2`

### Opinion Inheritance + Config

When using opinion inheritance (`extends`), flags are merged in this order:

1. **Config defaults** (system/user)
2. **Parent opinion** flags
3. **Child opinion** flags

**Example**:

Config:
```yaml
defaults:
  cflags: ["-O3"]
```

Parent opinion (`_base/xsc-baseline.yaml`):
```yaml
modifications:
  cflags: ["--sysroot=/toolchain/xsc/sysroot"]
```

Child opinion (`bash/xsc.yaml`):
```yaml
extends: ../_base/xsc-baseline.yaml
modifications:
  cflags: ["-DXSC_BUILD"]
```

**Final CFLAGS**: `-O3 --sysroot=/toolchain/xsc/sysroot -DXSC_BUILD`

## Best Practices

### 1. Start with User Config

Create `~/.config/lebowski/config.yaml` for personal customizations before modifying system config:

```bash
lebowski config --user
vim ~/.config/lebowski/config.yaml
```

### 2. Use System Config for Policies

Use `/etc/lebowski.conf` for organization-wide policies:
- Security hardening requirements
- Reproducible build enforcement
- Trust level restrictions

### 3. Override with CLI When Needed

Even with config, you can override per-build:

```bash
# Config has optimization_level: 2, but override for this build
lebowski build nginx --opinion custom-O3
```

### 4. Document Your Config

Add comments to your config files explaining **why** you chose specific settings:

```yaml
defaults:
  # Use -O2 instead of -O3 for stability in production
  # Some packages have bugs with aggressive optimization
  optimization_level: 2
```

### 5. Test Config Changes

After modifying config, test with a small package first:

```bash
# Modify config
vim ~/.config/lebowski/config.yaml

# Test with small package
lebowski build sed --opinion test-vanilla

# Verify flags applied correctly
# (Check build output for "Applied config defaults:")
```

## Troubleshooting

### Config Not Being Applied

**Problem**: Your config doesn't seem to be loaded.

**Solutions**:
1. Check file location:
   ```bash
   ls -la ~/.config/lebowski/config.yaml
   ls -la /etc/lebowski.conf
   ```

2. Verify YAML syntax:
   ```bash
   python3 -c "import yaml; yaml.safe_load(open('~/.config/lebowski/config.yaml'))"
   ```

3. Enable verbose output:
   ```bash
   lebowski -v build nginx --opinion test
   ```

### Conflicting Flags

**Problem**: Config and opinion both set `-O2` and `-O3`.

**Solution**: This is expected! The **rightmost** flag wins (GCC behavior):
- Config: `-O3`
- Opinion: `-O2`
- **Result**: `-O2` (opinion wins)

### Permission Denied for System Config

**Problem**: Can't write to `/etc/lebowski.conf`.

**Solution**:
```bash
sudo lebowski config --system
# OR
lebowski config > /tmp/lebowski.conf
sudo mv /tmp/lebowski.conf /etc/lebowski.conf
```

## Future Enhancements

The configuration system will be extended with:

1. **Opinion Repository Integration**
   - Automatic fetching from GitHub
   - Local caching with TTL
   - Multi-repo support

2. **Flag Normalization**
   - Detect conflicting flags
   - Warn about duplicates
   - Optimize flag order

3. **Per-Package Config**
   - Override defaults per package
   ```yaml
   package_overrides:
     nginx:
       optimization_level: 3
       lto: true
   ```

4. **Profile Support**
   - Switch between config profiles
   ```bash
   lebowski --profile production build nginx
   lebowski --profile debug build nginx
   ```

5. **Config Validation**
   ```bash
   lebowski config --validate
   ```

## Summary

The Lebowski configuration system provides:

✅ **System-wide and user-specific** configuration
✅ **Clear precedence** rules (CLI > user > system > defaults)
✅ **Global compiler flags** applied to all builds
✅ **Package default opinions** for convenience
✅ **Repository management** (coming soon)
✅ **Trust level enforcement** for security

**Key Insight**: Configuration makes Lebowski convenient for daily use while maintaining flexibility through CLI overrides.

---

**Next**: See [OPINION-REPOSITORY.md](./OPINION-REPOSITORY.md) for opinion repository design.
