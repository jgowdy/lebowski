# XSC Microarchitecture Levels

**Similar to Go's GOAMD64 levels, but for XSC.**

## Overview

Like Go's GOAMD64=v1/v2/v3/v4, XSC defines discrete microarchitecture levels. Each level is a HARD requirement - binaries won't run on older CPUs.

## XSC Levels for x86-64

### XSC-v1: Ivy Bridge (2012) - DEFAULT

**Minimum CPU:**
- Intel: Core i3/i5/i7 3xxx, Xeon E5 v2
- AMD: FX-series (Piledriver), Ryzen (all)

**Required Instructions:**
- AVX (256-bit SIMD)
- AES-NI (hardware AES)
- PCLMULQDQ (carry-less multiply)
- RDRAND (hardware RNG)
- F16C (half-precision floats)
- SSE4.1, SSE4.2, POPCNT

**Compiler Flags:**
```bash
-march=ivybridge -mtune=generic
```

**Benefits over baseline x86-64:**
- 5-8x faster cryptography (AES-NI)
- 2x SIMD width (AVX vs SSE)
- Hardware RNG (RDRAND)

**Who should use:**
- Everyone (this is the XSC default)
- Maximum compatibility while getting modern instruction sets

---

### XSC-v2: Haswell (2013)

**Minimum CPU:**
- Intel: Core i3/i5/i7 4xxx+, Xeon E5 v3+
- AMD: Excavator (2015+), Ryzen (all)

**Additional Instructions beyond v1:**
- AVX2 (256-bit integer SIMD)
- FMA3 (fused multiply-add)
- BMI1, BMI2 (bit manipulation)
- MOVBE (big-endian move)
- LZCNT (leading zero count)

**Compiler Flags:**
```bash
-march=haswell -mtune=generic
```

**Benefits over v1:**
- 2x faster integer vector operations (AVX2)
- Better FP performance (FMA3)
- Faster bit manipulation (BMI1/BMI2)

**Who should use:**
- Performance-critical applications (databases, video encoding)
- Users with 2014+ hardware
- Acceptable to exclude Ivy Bridge (2012-2013)

---

### XSC-v3: Skylake (2015) - OPTIONAL

**Minimum CPU:**
- Intel: Core i3/i5/i7 6xxx+, Xeon Scalable
- AMD: Zen 2+ (Ryzen 3xxx+)

**Additional Instructions beyond v2:**
- AVX-512F, AVX-512DQ, AVX-512CD, AVX-512BW, AVX-512VL (Intel only)
- ADX (multi-precision arithmetic)
- CLFLUSHOPT (cache line flush)

**Compiler Flags:**
```bash
# Intel Skylake-X
-march=skylake-avx512 -mtune=generic

# OR for non-AVX512 (Skylake without AVX-512)
-march=skylake -mtune=generic
```

**Benefits over v2:**
- 2x SIMD width (AVX-512 vs AVX2) on Intel
- Better for HPC, scientific computing, ML inference

**Who should use:**
- Specialized workloads (HPC, ML, video encoding)
- AVX-512 is Intel-only until Zen 5
- Most users should stick with v2

---

### XSC-v4: Zen 3 / Ice Lake (2020) - FUTURE

Reserved for future use. Potential features:
- AVX-512 VNNI (Intel)
- AVX-512 BF16 (Intel)
- Zen 3 optimizations (AMD)

Not currently defined.

---

## XSC Levels for aarch64

### XSC-ARM-v1: ARMv8-A (2013) - DEFAULT

**Minimum CPU:**
- ARM Cortex-A53, A57, A72, A73
- All 64-bit ARM CPUs

**Required Instructions:**
- NEON (SIMD)
- Crypto extensions (AES, SHA1, SHA2)

**Compiler Flags:**
```bash
-march=armv8-a+crypto -mtune=generic
```

---

### XSC-ARM-v2: ARMv8.2-A (2016)

**Additional Instructions:**
- Half-precision FP (FP16)
- Dot product (UDOT, SDOT)

**Compiler Flags:**
```bash
-march=armv8.2-a+crypto+fp16+dotprod -mtune=generic
```

---

## Implementation in Lebowski

### Base Opinions

Create versioned base opinions:

**`opinions/_base/xsc-v1.yaml`** (Ivy Bridge, DEFAULT)
```yaml
version: "1.0"
package: _base
opinion_name: xsc-v1
purity_level: pure-compilation
description: XSC microarchitecture level 1 (Ivy Bridge, 2012+)

modifications:
  cflags:
    - "-march=ivybridge"
    - "-mtune=generic"
    - "-O2"
  cxxflags:
    - "-march=ivybridge"
    - "-mtune=generic"
    - "-O2"
```

**`opinions/_base/xsc-v2.yaml`** (Haswell)
```yaml
version: "1.0"
package: _base
opinion_name: xsc-v2
purity_level: pure-compilation
description: XSC microarchitecture level 2 (Haswell, 2013+)

modifications:
  cflags:
    - "-march=haswell"
    - "-mtune=generic"
    - "-O2"
  cxxflags:
    - "-march=haswell"
    - "-mtune=generic"
    - "-O2"
```

**`opinions/_base/xsc-v3.yaml`** (Skylake)
```yaml
version: "1.0"
package: _base
opinion_name: xsc-v3
purity_level: pure-compilation
description: XSC microarchitecture level 3 (Skylake, 2015+)

modifications:
  cflags:
    - "-march=skylake"
    - "-mtune=generic"
    - "-O2"
  cxxflags:
    - "-march=skylake"
    - "-mtune=generic"
    - "-O2"
```

### Package Opinions Inherit Level

```yaml
# opinions/bash/xsc-base.yaml
inherits: _base/xsc-v1  # ← Explicitly choose level

# opinions/postgresql/xsc-performance.yaml
inherits: _base/xsc-v2  # ← Higher level for performance

# opinions/ffmpeg/xsc-avx512.yaml
inherits: _base/xsc-v3  # ← AVX-512 for video encoding
```

### Environment Variable (Future)

Like Go's GOAMD64:

```bash
export XSC_ARCH_LEVEL=v2
lebowski build postgresql --opinion xsc-performance
# Automatically uses xsc-v2 base
```

### Manifest Records Level

```json
{
  "opinion": {
    "inherits": "_base/xsc-v2",
    "arch_level": "v2",
    "minimum_cpu": "haswell"
  },
  "requirements": {
    "cpu": {
      "arch": "x86_64",
      "level": "xsc-v2",
      "required_flags": [
        "avx", "avx2", "aes", "pclmulqdq", "fma",
        "bmi1", "bmi2", "rdrand", "f16c"
      ]
    }
  }
}
```

## Comparison with Go's GOAMD64

| Go Level | XSC Level | Baseline CPU | Year | Key Instructions |
|----------|-----------|--------------|------|------------------|
| v1 | (none) | x86-64 | 2003 | SSE2 |
| v2 | (none) | Nehalem | 2008 | SSE4.2, POPCNT |
| v3 | **v1** | Ivy Bridge | 2012 | AVX, AES-NI |
| v3 | **v2** | Haswell | 2013 | AVX2, FMA3 |
| v4 | **v3** | Skylake | 2015 | AVX-512 |

**Why XSC starts at Ivy Bridge (Go's v3-ish):**

XSC is about re-empowering users with modern hardware. In 2025, requiring a 2012 CPU is reasonable. We skip the ancient baselines.

## Toolchain Configuration

Update GCC build to support all levels:

```bash
# Stage 5: Full GCC with level support
case "$XSC_LEVEL" in
    v1)
        ARCH_FLAGS="--with-arch=ivybridge --with-tune=generic"
        ;;
    v2)
        ARCH_FLAGS="--with-arch=haswell --with-tune=generic"
        ;;
    v3)
        ARCH_FLAGS="--with-arch=skylake --with-tune=generic"
        ;;
    *)
        # Default to v1
        ARCH_FLAGS="--with-arch=ivybridge --with-tune=generic"
        ;;
esac
```

Or build separate toolchains:
- `/opt/xsc-v1` - Ivy Bridge toolchain
- `/opt/xsc-v2` - Haswell toolchain
- `/opt/xsc-v3` - Skylake toolchain

## CPU Detection Utility Update

```bash
./tools/xsc-cpu-check --level v2

XSC CPU Compatibility Check - Level v2 (Haswell)
===========================

CPU: Intel(R) Xeon(R) CPU E5-4650 v2 @ 2.40GHz

XSC-v1 (Ivy Bridge):
  [✓] AVX, AES-NI, PCLMULQDQ, RDRAND, F16C, SSE4.2, POPCNT
  ✅ COMPATIBLE

XSC-v2 (Haswell):
  [✗] AVX2 - Missing
  [✗] FMA3 - Missing
  [✗] BMI1 - Missing
  [✗] BMI2 - Missing
  ❌ NOT COMPATIBLE

Result: Your CPU supports XSC-v1 but NOT XSC-v2
Use packages built with xsc-v1 opinion.
```

## Recommendations

### Default
Use **XSC-v1** (Ivy Bridge) for all packages unless there's a specific reason:
- Maximum compatibility (2012+ CPUs)
- Gets 90% of performance benefits
- Works on bx.ee server (Ivy Bridge-EP)

### Performance-Critical
Use **XSC-v2** (Haswell) for:
- Databases (PostgreSQL, MySQL)
- Video encoding (ffmpeg)
- Compression (zstd, brotli)
- Numerical computing

Benefits: 2x faster integer vectors (AVX2), better FP (FMA3)
Cost: Excludes 2012-2013 CPUs

### Specialized
Use **XSC-v3** (Skylake) only for:
- HPC workloads
- ML inference (if not using GPU)
- Scientific computing with heavy SIMD

Benefits: AVX-512 (Intel only)
Cost: Excludes pre-2015 CPUs and most AMD

## Migration Path

1. **Now:** Implement xsc-v1, xsc-v2, xsc-v3 base opinions
2. **Short-term:** Build all packages with xsc-v1
3. **Medium-term:** Identify performance-critical packages, offer xsc-v2 variants
4. **Long-term:** Let users choose level with environment variable

## References

- [Go GOAMD64](https://github.com/golang/go/wiki/MinimumRequirements#amd64)
- [x86-64 microarchitecture levels](https://en.wikipedia.org/wiki/X86-64#Microarchitecture_levels)
- [GCC x86 Options](https://gcc.gnu.org/onlinedocs/gcc/x86-Options.html)

---

**Bottom Line:** XSC levels are like Go's GOAMD64. v1 (Ivy Bridge) is the default. v2 (Haswell) for performance. v3 (Skylake) for specialists.
