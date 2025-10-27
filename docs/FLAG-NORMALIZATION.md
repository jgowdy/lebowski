# Flag Normalization and Conflict Resolution

## Overview

When combining compiler flags from multiple sources (config defaults, parent opinions, child opinions), Lebowski automatically **normalizes** the flags to:

1. **Remove duplicates**
2. **Resolve conflicts** intelligently
3. **Apply proper precedence** (child > parent > config)
4. **Warn about overrides**

This ensures the final build uses clean, conflict-free compiler flags.

## How It Works

### Sources of Flags (in precedence order)

1. **Config defaults** (lowest precedence)
2. **Parent opinion** (from `extends`)
3. **Child opinion** (highest precedence)

**Rule**: Later sources win for conflicting flags.

### Example: Simple Conflict

**Config** (`~/.config/lebowski/config.yaml`):
```yaml
defaults:
  optimization_level: 3  # Adds -O3
```

**Opinion** (`bash/optimized.yaml`):
```yaml
modifications:
  cflags:
    - "-O2"  # Overrides config's -O3
```

**Result**: `-O2` (opinion wins)

**Warning shown**:
```
⚠️  Flag conflicts resolved:
  optimization: -O3 overridden by -O2 (from opinion)
```

## Conflict Categories

The normalizer detects and resolves conflicts in these categories:

### 1. Optimization Level
- **Pattern**: `-O0`, `-O1`, `-O2`, `-O3`, `-Os`, `-Og`, `-Oz`
- **Conflict**: Only one optimization level can be active
- **Resolution**: Later flag wins

**Example**:
```
Config:   -O3
Opinion:  -O2
Result:   -O2  (opinion wins)
```

### 2. Architecture
- **Pattern**: `-march=X`, `-mtune=X`
- **Conflict**: Only one target architecture
- **Resolution**: Later flag wins

**Example**:
```
Config:   -march=native
Opinion:  -march=skylake
Result:   -march=skylake
```

### 3. C++ Standard
- **Pattern**: `-std=c++11`, `-std=c++14`, `-std=c++17`, `-std=c++20`
- **Conflict**: Only one standard version
- **Resolution**: Later flag wins

### 4. LTO (Link-Time Optimization)
- **Pattern**: `-flto`, `-flto=X`
- **Conflict**: Multiple LTO settings
- **Resolution**: Later flag wins

### 5. Stack Protector
- **Pattern**: `-fstack-protector`, `-fstack-protector-strong`, `-fstack-protector-all`
- **Conflict**: Multiple protector levels
- **Resolution**: Later flag wins

### 6. Frame Pointer
- **Pattern**: `-fomit-frame-pointer`, `-fno-omit-frame-pointer`
- **Conflict**: Contradictory settings
- **Resolution**: Later flag wins

### Linker-Specific Conflicts

1. **rpath**: `-Wl,-rpath=X`
2. **Dynamic linker**: `-Wl,--dynamic-linker=X`
3. **Strip**: `-Wl,-s`, `-Wl,--strip-all`

## Duplication Handling

Duplicate flags are automatically removed:

**Example**:
```
Config:   -pipe -fPIC
Parent:   -fPIC -DXSC_BUILD
Child:    -DDEBUG

Before normalization: -pipe -fPIC -fPIC -DXSC_BUILD -DDEBUG
After normalization:  -pipe -fPIC -DXSC_BUILD -DDEBUG
```

## Complete Example: Opinion Inheritance

### Scenario

**Config** (`~/.config/lebowski/config.yaml`):
```yaml
defaults:
  optimization_level: 3
  architecture: native
  cflags: ["-pipe"]
```

**Parent** (`_base/xsc-baseline.yaml`):
```yaml
modifications:
  cflags:
    - "--sysroot=/toolchain/xsc/sysroot"
    - "-O2"
    - "-fstack-protector-strong"
```

**Child** (`bash/xsc-optimized.yaml`):
```yaml
extends: ../_base/xsc-baseline.yaml
modifications:
  cflags:
    - "-DXSC_BUILD"
    - "-march=skylake"  # Override config's march=native
```

### Flag Merge Process

**Step 1**: Combine all sources:
```
Config:  -O3 -march=native -mtune=native -pipe
Parent:  --sysroot=/toolchain/xsc/sysroot -O2 -fstack-protector-strong
Child:   -DXSC_BUILD -march=skylake
```

**Step 2**: Detect conflicts:
```
optimization: -O3 (config) vs -O2 (parent)
march: -march=native (config) vs -march=skylake (child)
```

**Step 3**: Apply precedence (child > parent > config):
```
optimization: -O2 wins (from parent)
march: -march=skylake wins (from child)
```

**Step 4**: Remove duplicates and build final list:
```
Final CFLAGS:
  -O2                                    # parent won over config
  -march=skylake                         # child won over config
  -pipe                                  # from config
  --sysroot=/toolchain/xsc/sysroot      # from parent
  -fstack-protector-strong               # from parent
  -DXSC_BUILD                            # from child
```

**Warnings shown**:
```
⚠️  Flag conflicts resolved:
  optimization: -O3 overridden by -O2 (from parent)
  march: -march=native overridden by -march=skylake (from child)
```

## CLI Output

When building with flag normalization:

```bash
$ lebowski build bash --opinion-file opinions/bash/xsc-optimized.yaml

🎬 Lebowski: Building bash
✓ Opinion loaded: xsc-optimized
  Package: bash
  Purity: configure-only (HIGH trust)

⚙️  Applied config defaults:
  Optimization: -O3
  Architecture: -march=native

⚠️  Flag conflicts resolved:
  optimization: -O3 overridden by -O2 (from parent)
  march: -march=native overridden by -march=skylake (from child)

🔨 Starting build...
```

### Verbose Mode

With `-v` flag, see categorized flags:

```bash
$ lebowski -v build bash --opinion xsc-optimized

📋 Final compiler flags:
  optimization: -O2
  architecture: -march=skylake
  security: -fstack-protector-strong
  defines: -DXSC_BUILD
  linking: --sysroot=/toolchain/xsc/sysroot
  other: -pipe
```

## Flag Validation

The normalizer also validates flag combinations and warns about potentially problematic settings:

### Warning Examples

1. **LTO without optimization**:
```
⚠️  LTO enabled without optimization (-O1/-O2/-O3) - may not be effective
```

2. **Contradictory frame pointer**:
```
⚠️  Both -fomit-frame-pointer and -fno-omit-frame-pointer present
```

3. **PIE and PIC together**:
```
⚠️  Both PIE and PIC flags present - PIE is more restrictive
```

4. **Multiple FORTIFY levels**:
```
⚠️  Multiple FORTIFY_SOURCE levels: ['-D_FORTIFY_SOURCE=2', '-D_FORTIFY_SOURCE=3']
```

## Benefits

### 1. Clarity

Users see exactly what flags are applied and why:

```
⚠️  optimization: -O3 overridden by -O2 (from opinion)
```

This makes it clear that the opinion wanted `-O2` specifically.

### 2. Predictability

No surprising flag order issues. The normalizer ensures conflicts are resolved consistently.

### 3. Efficiency

Duplicate flags are removed, reducing command line length and making builds slightly faster.

### 4. Debugging

With verbose mode, you can see exactly what flags made it to the final build.

## Advanced Examples

### Example 1: Security Hardening Override

**Config** (conservative):
```yaml
defaults:
  hardening: true  # Adds -fstack-protector-strong
```

**Opinion** (aggressive):
```yaml
modifications:
  cflags:
    - "-fstack-protector-all"  # Stronger protection
```

**Result**: `-fstack-protector-all` (opinion wins)

### Example 2: Debug vs Release

**Config** (development):
```yaml
defaults:
  optimization_level: 0
  debug_symbols: true  # Adds -g
```

**Opinion** (release):
```yaml
modifications:
  cflags:
    - "-O3"
    - "-DNDEBUG"
```

**Result**: `-O3 -g -DNDEBUG`
- Optimization: `-O3` (opinion wins)
- Debug symbols: `-g` (not conflicting, both present)
- NDEBUG: Added by opinion

### Example 3: XSC with Custom Optimization

**Config**:
```yaml
defaults:
  optimization_level: 3
  architecture: native
```

**Parent** (xsc-baseline):
```yaml
modifications:
  cflags:
    - "--sysroot=/toolchain/xsc/sysroot"
    - "-O2"
  ldflags:
    - "-L/toolchain/xsc/lib"
    - "-lxsc-rt"
```

**Child** (xsc-aggressive):
```yaml
extends: ../_base/xsc-baseline.yaml
modifications:
  cflags:
    - "-O3"          # Override parent's -O2
    - "-flto"        # Add LTO
```

**Result**:
```
CFLAGS: -O3 -march=native --sysroot=/toolchain/xsc/sysroot -flto
LDFLAGS: -flto -L/toolchain/xsc/lib -lxsc-rt
```

**Conflicts**:
- `optimization: -O3 (config) vs -O2 (parent) -> -O3 (child) wins`
- Config's -O3 initially overridden by parent's -O2
- Then child's -O3 overrides everything

## Implementation Details

### FlagNormalizer Class

Located in `lebowski/flag_normalizer.py`:

```python
class FlagNormalizer:
    @staticmethod
    def normalize_cflags(
        sources: List[Tuple[str, List[str]]],
        verbose: bool = False
    ) -> NormalizationResult:
        """
        Normalize CFLAGS from multiple sources.

        sources: [(name, flags), ...] in precedence order
        Returns: NormalizationResult with final flags + diagnostics
        """
```

### Integration Points

1. **Opinion Inheritance** (`opinion.py:merge_opinions()`):
   - Normalizes when merging parent and child

2. **Config Application** (`config.py:apply_defaults_to_opinion()`):
   - Normalizes when applying config defaults

3. **CLI Display** (`cli.py:build()`):
   - Shows normalization warnings
   - Displays categorized flags in verbose mode

## Best Practices

### 1. Use Opinions for Overrides

Don't fight the config - if you need different flags for a package, use an opinion:

```yaml
# opinions/nginx/debug.yaml
modifications:
  cflags:
    - "-O0"  # Override config optimization for debugging
    - "-g"
```

### 2. Keep Opinions Minimal

Only specify flags that differ from defaults:

```yaml
# Good: Only XSC-specific flags
modifications:
  cflags:
    - "-DXSC_BUILD"
    - "--sysroot=/toolchain/xsc/sysroot"
```

```yaml
# Bad: Redundant with config
modifications:
  cflags:
    - "-O2"  # If config already has this
    - "-march=native"  # If config already has this
    - "-DXSC_BUILD"
```

### 3. Use Parent Opinions for Common Patterns

Create base opinions that others extend:

```yaml
# _base/performance.yaml
modifications:
  cflags:
    - "-O3"
    - "-flto"
    - "-march=native"
```

```yaml
# nginx/perf.yaml
extends: ../_base/performance.yaml
modifications:
  cflags:
    - "-DHTTP2_ENABLED"
```

### 4. Check Verbose Output

When debugging flag issues, use `-v`:

```bash
lebowski -v build nginx --opinion custom
```

This shows the final flags and makes it obvious what won.

## Troubleshooting

### Problem: Unexpected optimization level

**Symptom**: Build uses `-O2` but you expected `-O3`.

**Solution**: Check precedence:
1. Does parent opinion set `-O2`?
2. Check config defaults
3. Use `-v` to see conflicts

### Problem: Missing architecture flags

**Symptom**: Build doesn't use `-march=native`.

**Solution**: Check if opinion overrides it:
```bash
lebowski -v build package --opinion foo
# Look for: march: -march=native overridden by ...
```

### Problem: Duplicate warnings

**Symptom**: Many flags appear twice.

**Solution**: This is expected! Normalizer removes duplicates automatically. The warnings just inform you what was removed.

## Summary

Flag normalization provides:

✅ **Intelligent conflict resolution** (child > parent > config)
✅ **Automatic deduplication** (cleaner build commands)
✅ **Clear warnings** (see what was overridden and why)
✅ **Validation** (detect problematic flag combinations)
✅ **Categorization** (verbose mode shows organized flags)

**Key takeaway**: You don't need to worry about flag conflicts - Lebowski handles them intelligently and tells you what it did.

---

See also:
- [CONFIGURATION.md](./CONFIGURATION.md) - Config system details
- [OPINIONS.md](./OPINIONS.md) - Opinion inheritance
