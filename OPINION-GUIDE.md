# Lebowski Opinion Authoring Guide

## What Are Opinions?

Opinions are YAML configurations that define **how to build a package differently** from the stock Debian version while maintaining reproducibility.

An opinion specifies:
- Package modifications (compiler flags, configure options, patches)
- Trust level (purity level)
- Target Debian versions
- Build dependencies
- Verification steps

## Why Opinions Matter

Lebowski's core value proposition is **reproducible builds anyone can verify**. Opinions make modifications transparent and auditable:

```
Source + Opinion → Reproducible Build → Verifiable Binary
```

Anyone with the same opinion file can rebuild and verify identical output.

## Purity Levels

Opinions declare trust levels based on modification scope:

| Level | Modifications | Trust | Use Case |
|-------|--------------|-------|----------|
| `pure-compilation` | Compiler flags only (CFLAGS, LDFLAGS) | HIGHEST | Performance optimization |
| `configure-only` | Configure flags + compiler flags | HIGH | Feature toggles, cross-compilation |
| `patch-required` | Source patches | MEDIUM | Bug fixes, backports |
| `custom-code` | Custom code injection | LOW | Research, prototypes |

**Rule of thumb:** Use the highest purity level possible. Lower levels require more scrutiny.

## Basic Structure

Every opinion has this structure:

```yaml
version: "1.0"
package: PACKAGE_NAME
opinion_name: OPINION_NAME
purity_level: PURITY_LEVEL

description: |
  Human-readable description

maintainer:
  name: Your Name
  email: your@email.com

tags:
  - tag1
  - tag2

debian_versions:
  - bookworm
  - bullseye

modifications:
  # Package-specific changes

build_notes: |
  Optional build notes

verification_notes: |
  Optional verification steps
```

## Field Reference

### Required Fields

#### `version`
- Current: `"1.0"`
- Opinion format version
- Quoted string

#### `package`
- Debian source package name (e.g., `bash`, `coreutils`)
- Must match exactly: `apt-cache showsrc PACKAGE`

#### `opinion_name`
- Unique identifier for this opinion
- Naming conventions:
  - `vanilla`: No modifications
  - `optimized`: Performance flags
  - `hardened`: Security flags
  - `xsc-base`: XSC toolchain
  - `test-*`: Testing purposes

#### `purity_level`
- One of: `pure-compilation`, `configure-only`, `patch-required`, `custom-code`

#### `description`
- Multi-line YAML string (`|`)
- Explain what this opinion does and why
- Include expected benefits

#### `maintainer`
- `name`: Maintainer name
- `email`: Contact email

#### `tags`
- YAML list of tags
- Useful for filtering/categorization
- Common tags: `test`, `vanilla`, `xsc`, `optimization`, `hardening`, `performance`

#### `debian_versions`
- YAML list of Debian codenames
- Current: `bookworm` (Debian 12)
- Previous: `bullseye` (Debian 11)

### Optional Fields

#### `xsc_variant`
- XSC-specific: `base` or `cfi-compat`
- Only for XSC builds

#### `build_notes`
- Multi-line notes about build process
- Build time estimates
- Special requirements

#### `verification_notes`
- How to verify the built package
- Commands to run
- Expected output

#### `performance_notes`
- Expected performance improvements
- Benchmarks
- Comparison with stock builds

#### `references`
- YAML list of URLs or file paths
- Related documentation
- Research papers

### Modifications Section

The `modifications` section defines actual changes:

#### `env`
Environment variables:

```yaml
modifications:
  env:
    CFLAGS: "-O3 -march=native"
    LDFLAGS: "-flto"
```

Or empty:
```yaml
modifications:
  env: {}
```

#### `cflags`, `cxxflags`, `ldflags`
Compiler/linker flags (alternative to `env`):

```yaml
modifications:
  cflags:
    - "-O3"
    - "-march=native"
  ldflags:
    - "-flto"
```

Or empty:
```yaml
modifications:
  cflags: []
  cxxflags: []
  ldflags: []
```

#### `configure_flags`
Add or remove configure script flags:

```yaml
modifications:
  configure_flags:
    add:
      - "--enable-optimizations"
      - "--with-lto"
    remove:
      - "--disable-ipv6"
```

#### `build_deps`
Build dependencies:

```yaml
modifications:
  build_deps:
    add:
      - libssl-dev
      - libcurl4-openssl-dev
```

## Examples

### Example 1: Vanilla Build (Simplest)

**Use case:** Test Lebowski infrastructure with no modifications.

```yaml
version: "1.0"
package: bash
opinion_name: test-vanilla
purity_level: pure-compilation

description: |
  Standard bash build with no modifications.
  Used to test Lebowski's core build and attestation functionality.

maintainer:
  name: Lebowski Project
  email: opinions@lebowski.org

tags:
  - test
  - vanilla

debian_versions:
  - bookworm

modifications:
  env: {}
  cflags: []
  cxxflags: []
  ldflags: []
  build_deps:
    add: []

build_notes: |
  This is a vanilla Debian build with no modifications.
  Used to verify Lebowski's reproducible build infrastructure.

verification_notes: |
  Standard Debian package verification:

  dpkg -i bash_*.deb
  bash --version
```

### Example 2: Optimization Flags

**Use case:** Performance-optimized build.

```yaml
version: "1.0"
package: gzip
opinion_name: optimized
purity_level: pure-compilation

description: |
  gzip built with aggressive optimization flags.
  Expected: 10-15% faster compression.

maintainer:
  name: Lebowski Project
  email: opinions@lebowski.org

tags:
  - optimization
  - performance

debian_versions:
  - bookworm

modifications:
  env:
    CFLAGS: "-O3 -march=native -flto"
    LDFLAGS: "-flto"

build_notes: |
  Build time: ~30 seconds
  Binary size: Slightly larger due to inlining

verification_notes: |
  Benchmark compression speed:

  dd if=/dev/zero bs=1M count=100 | gzip > /dev/null

  Compare with stock gzip time.
```

### Example 3: Configure Options

**Use case:** Enable specific features.

```yaml
version: "1.0"
package: python3-defaults
opinion_name: pgo-optimized
purity_level: configure-only

description: |
  Python 3 with Profile-Guided Optimization (PGO).
  10-30% faster execution for most Python workloads.

maintainer:
  name: Lebowski Project
  email: opinions@lebowski.org

tags:
  - python
  - pgo
  - optimization

debian_versions:
  - bookworm

modifications:
  configure_flags:
    add:
      - "--enable-optimizations"
      - "--with-lto"

  env:
    CFLAGS: "-O3"

build_notes: |
  WARNING: Long build time (2-3 hours) due to PGO requiring:
  1. First compilation
  2. Benchmark suite execution
  3. Second compilation with profile data

performance_notes: |
  Expected improvements:
  - CPU-bound workloads: 10-20% faster
  - I/O-bound workloads: 5-10% faster
  - Web frameworks: 15-25% more req/sec

verification_notes: |
  python3 --version

  # Run benchmark
  python3 -m test.pystone
```

### Example 4: Cross-Compilation (XSC)

**Use case:** Build for XSC architecture.

```yaml
version: "1.0"
package: bash
opinion_name: xsc-base
purity_level: configure-only

description: |
  bash built for XSC architecture (x86_64-xsc-linux-gnu).

  Uses ring-based syscalls instead of traditional syscall instructions.
  No CPU traps - all system calls via submission/completion rings.

maintainer:
  name: Lebowski + XSC Project
  email: opinions@lebowski.org

tags:
  - xsc
  - ring-syscalls

debian_versions:
  - bookworm

xsc_variant: base

modifications:
  configure_flags:
    add:
      - "--host=x86_64-xsc-linux-gnu"
      - "--build=x86_64-linux-gnu"

  env:
    CC: "x86_64-xsc-linux-gnu-gcc"
    CXX: "x86_64-xsc-linux-gnu-g++"
    LD: "x86_64-xsc-linux-gnu-ld"
    AR: "x86_64-xsc-linux-gnu-ar"
    RANLIB: "x86_64-xsc-linux-gnu-ranlib"
    CFLAGS: "-O2 -g"
    CXXFLAGS: "-O2 -g"
    LDFLAGS: "-lxsc-rt"

  build_deps:
    add:
      - libxsc-rt-dev
      - x86_64-xsc-linux-gnu-gcc
      - x86_64-xsc-linux-gnu-binutils

build_notes: |
  Requires XSC toolchain installed.
  Build time: Similar to standard Debian build.

verification_notes: |
  # No syscall instructions (critical!)
  objdump -d bash | grep syscall
  # Should be EMPTY

  # XSC_ABI note present
  readelf -n bash | grep XSC_ABI
  # Should show: XSC_ABI   version: 1

  # Links against libxsc-rt
  ldd bash | grep libxsc-rt
  # Should show: libxsc-rt.so.1

references:
  - "https://github.com/jgowdy/xsc-os"
```

## Best Practices

### 1. Start Simple

Begin with `pure-compilation` or vanilla opinion:

```yaml
modifications:
  env: {}
  cflags: []
```

Test the build process before adding complexity.

### 2. Document Everything

Future users (including yourself) need to understand:
- **Why** these modifications?
- **What** is the expected benefit?
- **How** to verify it worked?

### 3. Use Appropriate Purity Levels

| If you need... | Use... |
|----------------|--------|
| Just -O3 | `pure-compilation` |
| --enable-feature | `configure-only` |
| Source patch | `patch-required` |
| Custom code | `custom-code` |

### 4. Test Reproducibility

```bash
# Build twice
python3 -m lebowski.cli build PACKAGE \
    --opinion-file opinions/PACKAGE/OPINION.yaml \
    --output-dir ./build1

python3 -m lebowski.cli build PACKAGE \
    --opinion-file opinions/PACKAGE/OPINION.yaml \
    --output-dir ./build2

# Compare hashes
sha256sum build1/*.deb build2/*.deb
```

Hashes **must** be identical.

### 5. Verify Functionality

Don't just build - test the package works:

```bash
# Install
dpkg -i package_*.deb

# Test basic functionality
package --version
package --help

# Run test suite if available
```

## Testing Your Opinion

### Step 1: Create Opinion File

```bash
mkdir -p opinions/PACKAGE
vi opinions/PACKAGE/my-opinion.yaml
```

### Step 2: Test Build

```bash
cd build-tool

python3 -m lebowski.cli build PACKAGE \
    --opinion-file ../opinions/PACKAGE/my-opinion.yaml \
    --output-dir /tmp/test-output
```

### Step 3: Check Output

```bash
ls -lh /tmp/test-output/
cat /tmp/test-output/*.lebowski-manifest.json
```

### Step 4: Verify Reproducibility

```bash
# Second build
python3 -m lebowski.cli build PACKAGE \
    --opinion-file ../opinions/PACKAGE/my-opinion.yaml \
    --output-dir /tmp/test-output2

# Compare
sha256sum /tmp/test-output/*.deb /tmp/test-output2/*.deb
```

### Step 5: Test Functionality

```bash
# Extract and test
dpkg-deb -x /tmp/test-output/PACKAGE_*.deb /tmp/test-extract
/tmp/test-extract/usr/bin/BINARY --version
```

## Common Issues

### Issue: Build fails immediately

**Cause:** Wrong package name or Debian version mismatch.

**Fix:** Check package exists:
```bash
apt-cache showsrc PACKAGE
```

### Issue: Configure flags ignored

**Cause:** Package doesn't use autoconf/configure.

**Fix:** Use `env` instead to set `DEB_BUILD_OPTIONS` or other variables.

### Issue: Hashes don't match between builds

**Cause:** Non-reproducible modification (timestamps, randomness).

**Fix:**
- Remove `__DATE__`, `__TIME__` macros
- Set `SOURCE_DATE_EPOCH` (Lebowski does this automatically)
- Avoid random seeds

### Issue: Build succeeds but package doesn't work

**Cause:** Incompatible flags or missing dependencies.

**Fix:**
- Test on clean system
- Check `ldd` for missing libraries
- Review build logs for warnings

## Advanced Topics

### Patches (purity_level: patch-required)

```yaml
purity_level: patch-required

modifications:
  patches:
    add:
      - "../../patches/PACKAGE/fix-issue.patch"
```

Patches must be in unified diff format.

### Custom Build Scripts (purity_level: custom-code)

```yaml
purity_level: custom-code

modifications:
  build_script: |
    #!/bin/bash
    # Custom build logic
    ./configure --prefix=/usr
    make -j$(nproc)
```

Use sparingly - reduces trust.

### Conditional Modifications

Use YAML anchors for shared config:

```yaml
xsc_base: &xsc_env
  CC: "x86_64-xsc-linux-gnu-gcc"
  CXX: "x86_64-xsc-linux-gnu-g++"

modifications:
  env:
    <<: *xsc_env
    CFLAGS: "-O2"
```

## Opinion Naming Conventions

| Pattern | Meaning |
|---------|---------|
| `vanilla` | No modifications |
| `test-*` | Testing/development |
| `optimized` | Performance optimizations |
| `hardened` | Security hardening |
| `minimal` | Minimal features |
| `full-featured` | All features enabled |
| `xsc-base` | XSC baseline |
| `xsc-optimized` | XSC + optimizations |

## Verification Checklist

Before publishing an opinion:

- [ ] Builds successfully
- [ ] Reproducible (identical hashes on repeated builds)
- [ ] Package installs without errors
- [ ] Basic functionality works
- [ ] Documentation complete (description, build_notes, verification_notes)
- [ ] Purity level appropriate
- [ ] Tags accurate
- [ ] Maintainer info correct

## Getting Help

- GitHub Issues: https://github.com/jgowdy/lebowski/issues
- Example opinions: `lebowski/opinions/`
- TEMPLATE: `lebowski/opinions/xsc/TEMPLATE.yaml`

## Next Steps

1. Read existing opinions in `opinions/` directory
2. Start with a vanilla opinion for your package
3. Test reproducibility thoroughly
4. Gradually add modifications
5. Document everything
6. Share your opinion with the community

## License

Opinions are typically licensed under the same license as the package they modify, or CC0/Public Domain for configuration files.
