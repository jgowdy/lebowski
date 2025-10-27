# Lebowski: Reproducible Package Builder

**Build trustworthy software distributions without infrastructure.**

Lebowski enables **cryptographically verifiable** package builds using opinions (YAML configs) and containers. Anyone can rebuild and verify identical binaries.

## Why Lebowski

Building a custom Linux distribution requires:
- ❌ Build farms
- ❌ Package repositories  
- ❌ Trusted infrastructure

Lebowski provides:
- ✅ Bit-for-bit reproducible builds
- ✅ Cryptographic verification (SHA256)
- ✅ Opinion-based modifications
- ✅ Build manifests with full provenance
- ✅ Container isolation
- ✅ Parallel compilation (`make -j$(nproc)`)

**Don't trust, verify.** Anyone can rebuild and confirm identical outputs.

## Quick Start

```bash
# Build bash with vanilla opinion
python3 -m lebowski.cli build bash \
    --opinion-file opinions/bash/test-vanilla.yaml \
    --output-dir ./output

# Check the manifest
cat output/bash-*.lebowski-manifest.json

# Verify by rebuilding
python3 -m lebowski.cli build bash \
    --opinion-file opinions/bash/test-vanilla.yaml \
    --output-dir ./output2

# Compare SHA256
sha256sum output/bash-*.deb output2/bash-*.deb
```

**New to Lebowski?** See **[Getting Started Guide](docs/GETTING-STARTED.md)** for installation, tutorials, and workflows.

## Proven Reproducibility

```
Build 1: 90d60f9dc7ea25db3bd306e4c32570a3307e3997929015a02e40cc050213ee7c
Build 2: 90d60f9dc7ea25db3bd306e4c32570a3307e3997929015a02e40cc050213ee7c
         ^^^ IDENTICAL ^^^
```

## Architecture

```
Source Package → Opinion → Container Build → .deb + Manifest
     (Debian)     (YAML)   (reproducible)    (verifiable)
```

## Opinions

Opinions define build modifications with trust levels:

- **pure-compilation**: Only compiler flags (HIGHEST trust)
- **configure-only**: Configure + compiler flags (HIGH trust)
- **patch-required**: Source patches needed (MEDIUM trust)
- **custom-code**: Custom code injection (LOW trust)

Example opinion:

```yaml
version: "1.0"
package: bash
opinion_name: test-vanilla
purity_level: pure-compilation
debian_versions: [bookworm]
modifications:
  env: {}
  cflags: []
  cxxflags: []
  ldflags: []
```

## Documentation

**Getting Started:**
- **[Getting Started Guide](docs/GETTING-STARTED.md)** - Installation, first build, tutorials
- [CLI Reference](docs/CLI-REFERENCE.md) - Complete command-line documentation
- [Config Reference](docs/CONFIG-REFERENCE.md) - Configuration file options

**Core Features:**
- [Opinions Format](docs/OPINIONS.md) - How to write opinion files
- [Package Signing](docs/PACKAGE-SIGNING.md) - GPG signing and verification
- [Data-Driven Toolchains](docs/DATA-DRIVEN-TOOLCHAINS.md) - Custom compiler toolchains

**XSC Integration:**
- [XSC Overview](docs/XSC-INTEGRATION.md) - Zero-syscall builds
- [CPU Baseline Optimization](docs/XSC-CPU-BASELINE.md) - Microarchitecture tuning
- [Aggressive Optimizations](docs/XSC-AGGRESSIVE-OPTS.md) - Performance tuning

**Additional Documentation:**
- See full list in [docs/](docs/) directory

## Current Status

**Working:**
- ✅ Container-based builds
- ✅ Reproducibility proven (bash, 9+ utilities)
- ✅ Build manifests
- ✅ Parallel compilation
- ✅ Automatic workarounds (bash-doc)
- ✅ Package signing infrastructure
- ✅ Configuration system

**In Progress:**
- ⏳ CLI signing flags (--auto-sign, --sign-key)
- ⏳ Builder signing integration
- ⏳ XSC toolchain builds
- ⏳ More package testing

## Use Cases

1. **XSC Distribution** (primary): Build hardened Linux with ring-based syscalls
2. **Security auditing**: Verify vendor binaries match source
3. **Custom distributions**: Build with specific optimizations
4. **Supply chain security**: Independent verification

## Requirements

- Docker or Podman
- Python 3.8+
- Debian bookworm base (for apt-get source)

## Performance

- Parallel package builds (separate directories)
- Parallel compilation (make -j80 on 80-core systems)
- Fast RAID optimization (`/build` vs `/tmp`)

## License

GPLv3+

## Status

**Alpha** - Core functionality working, active development
