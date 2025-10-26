# Debian, but an Opinion

## The Concept

Debian gives you packages. Lebowski gives you **Debian with your opinion baked in**.

Every Debian package is built with someone's opinions:
- Compiler flags
- Optimization levels
- Security hardening options
- Patch choices
- Feature selections

But those opinions are hidden in build scripts, maintained by packagers, and you have to trust them.

**Lebowski makes opinions explicit, traceable, and reproducible.**

## What's an Opinion?

An opinion is a YAML file that says: "Build this package THIS way."

### Example: Vanilla Opinion

```yaml
version: "1.0"
package: bash
opinion_name: vanilla
purity_level: pure-compilation

description: |
  Standard bash build with Debian defaults.
  No modifications, just reproducible.

maintainer:
  name: Lebowski Project
  email: opinions@lebowski.org

modifications:
  env: {}
  cflags: []
  ldflags: []
```

**Result**: Bash, built exactly like Debian, but reproducibly verified.

### Example: Hardened Opinion

```yaml
version: "1.0"
package: bash
opinion_name: hardened
purity_level: pure-compilation

description: |
  Bash with aggressive security hardening.
  Stack canaries, ASLR, CFI, no-execute stack.

modifications:
  cflags:
    - "-fstack-protector-strong"
    - "-D_FORTIFY_SOURCE=2"
    - "-fPIE"
  ldflags:
    - "-Wl,-z,relro"
    - "-Wl,-z,now"
    - "-pie"
```

**Result**: Bash, hardened against exploits, reproducible and traceable.

### Example: XSC Opinion (Ring-Based Syscalls)

```yaml
version: "1.0"
package: bash
opinion_name: xsc-baseline
purity_level: configure-only

description: |
  Bash built with XSC toolchain.
  Uses ring-based syscalls instead of syscall instructions.
  Verifiable zero-syscall binary.

modifications:
  env:
    CC: x86_64-xsc-linux-gnu-gcc
    CXX: x86_64-xsc-linux-gnu-g++
  ldflags:
    - "-lxsc-rt"
```

**Result**: Bash with NO syscall instructions. Verifiable. Reproducible.

## Why This Matters

### 1. Trust Through Transparency

Traditional Debian:
- "Trust us, we built it securely"
- Build process hidden in maintainer scripts
- Can't verify without rebuilding yourself

Lebowski + Opinions:
- Opinion file shows EXACTLY what was done
- Build manifest provides complete provenance
- Anyone can rebuild and verify SHA256 matches

### 2. Security Through Visibility

You can see:
- Every compiler flag used
- Every patch applied
- Every environment variable set
- Every dependency version

If a package has a backdoor, the opinion file would show suspicious modifications.

### 3. Flexibility Without Fragmentation

One package, multiple opinions:

```
bash/
  vanilla.yaml       → Standard Debian bash
  hardened.yaml      → Security-hardened bash
  xsc.yaml           → Ring-based syscall bash
  size-optimized.yaml → -Os -flto for embedded
  debug.yaml         → -g -O0 for development
```

Same source. Different opinions. All reproducible. All verifiable.

## Use Cases

### XSC Distribution

Build entire Debian distro with x86_64-xsc-linux-gnu toolchain:
- All binaries use ring-based syscalls
- Verifiable zero-syscall instructions
- Reproducible from XSC opinions

### Security-Hardened Distribution

Apply aggressive hardening opinions to all packages:
- Full ASLR, stack canaries, CFI
- Reproducible security baseline
- Independent verification possible

### Embedded/Size-Optimized Distribution

Build minimal distro with -Os -flto opinions:
- Aggressive size optimization
- Reproducible builds for embedded targets

### Audit-Ready Distribution

Build with opinions that prioritize auditability:
- Debug symbols included
- Source maps preserved
- Reproducible audit trail

## The Lebowski Promise

1. **Reproducible**: Same source + same opinion = identical binary (SHA256 match)
2. **Transparent**: Opinion file shows all modifications
3. **Verifiable**: Anyone can rebuild and verify
4. **Traceable**: Build manifest documents complete provenance

## Technical Foundation

Lebowski achieves this through:

- **Container isolation**: Docker with fixed SOURCE_DATE_EPOCH
- **Unique build dirs**: Parallel builds don't collide
- **Opinion framework**: YAML configs applied to build process
- **Build manifests**: JSON with SHA256, timestamps, opinion hash
- **Verification system**: Rebuild from manifest and compare hashes

## Purity Levels

Opinions declare their "purity" - how much they modify:

1. **pure-compilation**: Only compiler flags (HIGHEST trust)
2. **configure-only**: Compiler flags + configure options
3. **patch-required**: Includes source patches
4. **custom-code**: Adds new code to package (LOWEST trust)

The purity level lets you assess trust at a glance.

## Real Example: XSC

### Problem

x86_64 binaries use `syscall` instructions. This is:
- Direct kernel access (hard to secure)
- Not auditable (syscall = kernel blackbox)
- Not portable (kernel ABI changes break things)

### Solution: XSC Opinions

Build all packages with XSC toolchain opinions:
- Compiler: x86_64-xsc-linux-gnu-gcc
- Runtime: libxsc-rt
- Result: Ring-based syscalls, zero `syscall` instructions

### Verification

```bash
# Build bash with XSC opinion
lebowski build bash --opinion-file opinions/bash/xsc.yaml

# Verify zero syscall instructions
objdump -d bash | grep syscall
# (no output = success)
```

### Trust Model

- Opinion file shows: CC=x86_64-xsc-linux-gnu-gcc
- Build manifest shows: opinion SHA256, source SHA256, output SHA256
- Anyone can: Rebuild with same opinion, verify SHA256 matches

## Getting Started

```bash
# Install Lebowski
pip install -r requirements.txt

# Build a package with vanilla opinion
python3 -m lebowski.cli build bash \
  --opinion-file opinions/bash/vanilla.yaml \
  --output-dir /tmp/bash-out

# Verify reproducibility
python3 -m lebowski.cli verify \
  /tmp/bash-out/bash_*.lebowski-manifest.json
```

## Conclusion

**Debian gives you packages.**
**Lebowski gives you Debian with your opinion baked in.**

Explicit. Traceable. Reproducible. Verifiable.

That's the power of opinions.

---

## Learn More

- [Installation Guide](INSTALL.md)
- [Opinion Authoring Guide](OPINION-GUIDE.md)
- [XSC Integration](XSC-BASELINE-COMPLETE.md)
- [Release Plan](RELEASE-PLAN.md)
