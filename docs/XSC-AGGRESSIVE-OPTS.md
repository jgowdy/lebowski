# XSC Aggressive Optimizations - Beyond -march=ivybridge

**Since we REQUIRE Ivy Bridge, we can be more aggressive.**

## Current Baseline (Conservative)

```bash
-march=ivybridge    # Enables instructions
-mtune=generic      # Schedules for average CPU
-O2                 # Standard optimization
```

This is safe and works well, but leaves performance on the table.

## Aggressive Options (Extract More Performance)

### 1. Auto-Vectorization Improvements

Since we KNOW AVX is available:

```bash
-march=ivybridge
-mtune=ivybridge     # ← Optimize scheduling for IVB specifically, not generic
-O3                  # ← More aggressive inlining, vectorization
-ftree-vectorize     # (already in -O3, but can force with -O2)
-ftree-slp-vectorize # Superword-level parallelism
```

**Tradeoff:**
- `+5-15%` performance on Ivy Bridge
- `-2-5%` performance on Skylake+ (worse scheduling for newer CPUs)
- Larger binaries (more inlining)

### 2. Link-Time Optimization (LTO)

```bash
CFLAGS="-march=ivybridge -O2 -flto"
LDFLAGS="-flto -fuse-linker-plugin"
```

**Benefits:**
- Whole-program optimization
- Better inlining across translation units
- Dead code elimination
- `+5-20%` performance depending on package

**Tradeoff:**
- Longer build times (significantly)
- More memory needed during link
- Can expose bugs in packages

### 3. Profile-Guided Optimization (PGO)

For critical packages (glibc, openssl, nginx):

```bash
# Build 1: Generate profile
CFLAGS="-march=ivybridge -O2 -fprofile-generate"

# Run typical workload to collect profile

# Build 2: Use profile
CFLAGS="-march=ivybridge -O2 -fprofile-use"
```

**Benefits:**
- `+10-30%` performance on hot paths
- Better branch prediction
- Optimal code layout for cache

**Tradeoff:**
- 2x build time (need two builds)
- Need representative workload
- Not reproducible (profile depends on workload)

### 4. Crypto-Specific Optimizations

For packages with cryptography (openssl, gnupg, openssh):

```bash
# OpenSSL configure
./config \
    --prefix=/usr \
    enable-ec_nistp_64_gcc_128 \
    no-ssl3 \
    no-weak-ssl-ciphers \
    -march=ivybridge \
    -maes -mpclmul  # ← Explicitly enable AES-NI, PCLMULQDQ codepaths
```

**Benefits:**
- Ensures crypto libraries use hardware acceleration
- `+5-8x` for AES operations
- `+3-5x` for GCM mode

### 5. Math Optimizations

```bash
-fno-math-errno       # Don't set errno for math functions (faster)
-fno-signed-zeros     # Assume +0 == -0
-fno-trapping-math    # No FP exceptions
```

**Benefits:**
- Better vectorization of math code
- `+5-10%` on numerical workloads

**Tradeoff:**
- Changes IEEE 754 behavior slightly
- Can break code that relies on errno or FP exceptions

### 6. Aggressive Inlining

```bash
-O3                                    # Already aggressive
-finline-functions                     # Force inline even without inline keyword
-funroll-loops                         # Unroll loops for better pipelining
--param inline-unit-growth=50          # Allow 50% code size growth for inlining
--param large-function-growth=200      # Inline larger functions
```

**Benefits:**
- `+10-25%` on tight loops
- Better register allocation
- Eliminates function call overhead

**Tradeoff:**
- Much larger binaries (2-3x code size)
- Worse instruction cache behavior on some workloads
- Longer compile times

## Package-Specific Recommendations

### Tier 1: Critical Performance (Use Aggressive Opts)

**glibc:**
```yaml
cflags:
  - "-march=ivybridge"
  - "-mtune=ivybridge"  # Tune for IVB specifically
  - "-O3"
  - "-flto"
  - "-fno-math-errno"
configure_flags:
  - "--enable-cet"
  - "--enable-kernel=6.1"
```

**openssl:**
```yaml
cflags:
  - "-march=ivybridge"
  - "-maes"
  - "-mpclmul"
  - "-O3"
  - "-flto"
configure_flags:
  - "enable-ec_nistp_64_gcc_128"
  - "no-weak-ssl-ciphers"
```

**nginx:**
```yaml
cflags:
  - "-march=ivybridge"
  - "-O3"
  - "-flto"
configure_flags:
  - "--with-cc-opt=-march=ivybridge -O3 -flto"
  - "--with-ld-opt=-flto"
```

**postgresql:**
```yaml
cflags:
  - "-march=ivybridge"
  - "-O3"
  - "-flto"
  - "-funroll-loops"
configure_flags:
  - "--enable-profiling"  # For PGO later
```

### Tier 2: Standard Performance (Conservative + LTO)

Most packages:
```yaml
cflags:
  - "-march=ivybridge"
  - "-mtune=generic"
  - "-O2"
  - "-flto"  # Add LTO for free 5-10% gain
```

### Tier 3: Safety-Critical (No Aggressive Opts)

Packages where correctness > performance:
```yaml
cflags:
  - "-march=ivybridge"
  - "-mtune=generic"
  - "-O2"
  # No -O3, no LTO, no fast-math
```

Examples: gnupg, openssh, sudo, systemd

## Recommended XSC Strategy

### Base Opinion (Conservative)
`opinions/_base/xsc-ivybridge.yaml` - Keep as-is:
```yaml
cflags:
  - "-march=ivybridge"
  - "-mtune=generic"
  - "-O2"
```

### Aggressive Opinion (Optional)
`opinions/_base/xsc-ivybridge-aggressive.yaml` - NEW:
```yaml
cflags:
  - "-march=ivybridge"
  - "-mtune=ivybridge"  # Tune for IVB, not generic
  - "-O3"
  - "-flto"
  - "-fno-math-errno"
  - "-funroll-loops"
ldflags:
  - "-flto"
  - "-fuse-linker-plugin"
```

Then package opinions can choose:
```yaml
# Conservative (most packages)
inherits: _base/xsc-ivybridge

# Aggressive (performance-critical packages)
inherits: _base/xsc-ivybridge-aggressive
```

## Additional Instruction Set Flags

Force GCC to use specific instruction sets we know exist:

```bash
-mavx         # Force AVX usage
-maes         # Force AES-NI usage
-mpclmul      # Force PCLMULQDQ usage
-mpopcnt      # Force POPCNT usage
-msse4.2      # Force SSE4.2 usage
```

These are redundant with `-march=ivybridge` but can help some packages that do runtime CPU detection and might not enable features.

## Performance Impact Summary

| Optimization | Build Time | Binary Size | Speedup | Risk |
|-------------|------------|-------------|---------|------|
| `-march=ivybridge` | +0% | +5% | +15-30% | None (baseline) |
| `-mtune=ivybridge` | +0% | +0% | +5-10% | Slight (newer CPUs) |
| `-O3` | +10% | +30% | +5-15% | Low |
| `-flto` | +50% | -5% | +5-20% | Medium |
| `-funroll-loops` | +5% | +20% | +5-10% | Low |
| `-ffast-math` | +0% | +0% | +10-20% | **HIGH** (breaks IEEE 754) |
| PGO | +100% | +0% | +10-30% | Medium (reproducibility) |

## What I Recommend

### For XSC Base
Keep conservative baseline:
```bash
-march=ivybridge -mtune=generic -O2
```

### Add Optional Aggressive Base
Create `_base/xsc-ivybridge-aggressive.yaml`:
```bash
-march=ivybridge -mtune=ivybridge -O3 -flto
```

### Package-Specific
- **glibc, openssl:** Aggressive + crypto flags
- **nginx, postgresql, redis:** Aggressive
- **Most packages:** Conservative
- **Security-critical:** Conservative, no LTO

This gives users choice:
- `xsc-ivybridge` - Safe, works great on newer CPUs too
- `xsc-ivybridge-aggressive` - Maximum performance for IVB specifically

Want me to implement the aggressive base opinion?
