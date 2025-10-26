# Lebowski

> "Yeah, well, that's just like, your opinion, man." - The Dude

**Lebowski re-empowers common users at the expense of distribution gatekeepers.**

## The Problem

The free software movement took power from corporations and gave it to developers. But developers (Debian Developers, kernel maintainers, systemd developers, glibc maintainers) have become a new elite who control what users can do.

**They decide:**
- How packages are built
- What features are enabled
- What optimizations are used
- What's "best for users"

**Users can:**
- Accept it
- Or fork the entire distribution (impossibly expensive)

**This is not freedom. This is gatekeeping.**

The same power structure as before, just different people in charge.

## The Solution

**Lebowski transfers power from gatekeepers back to users.**

Make building custom packages as easy as installing official ones:
- No becoming a Debian Developer
- No convincing gatekeepers
- No forking entire distributions
- No waiting years for approval

Just: `lebowski build nginx --opinion http3`

**Users hold their own opinions. No permission required.**

## Our Power: Reproducibility

**We're creating a new distro. Users have to trust something. Our power comes from making trust unnecessary.**

### Core Principle

**Reproducibility is not a feature. It's the foundation. It's everything.**

Just like package signatures enable distribution mirrors, **reproducible builds enable distributed building:**

- Mirrors solve distribution: Anyone can host packages (verify signature)
- Reproducibility solves building: Anyone can build packages (verify hash)
- **Complete decentralization**: No centralized build infrastructure needed
- **Sustainable economics**: Community contributes resources
- **Mathematical trust**: Verification, not faith

### Core Requirements

1. **Reproducible Builds**: Every package MUST be bit-for-bit reproducible
2. **Container-Based**: All builds happen in defined containers for consistency
3. **Verifiable**: Anyone can rebuild and verify package integrity
4. **Transparent**: All opinion definitions are public and version-controlled
5. **Distributed**: Multiple builders can independently produce identical binaries

## Status

Project in initial design phase. Documentation complete, ready for implementation.

## Quick Start

Phase 1 (MVP) will provide:

```bash
# Build custom kernel (1000Hz desktop instead of Debian's 250Hz server)
lebowski build linux --opinion desktop-1000hz

# Build nginx with HTTP/3 support
lebowski build nginx --opinion http3

# Build Python with PGO optimization
lebowski build python3 --opinion optimized

# Install the resulting packages
sudo dpkg -i *.deb
```

One command. No expertise. No permission needed.

Pre-built packages (Phase 2) coming later.

## Key Concepts

### Opinion Purity Levels

Lebowski differentiates opinions by "purity" - how much they modify Debian's source:

- **Pure Compilation** (Highest Trust): Same source, different compiler flags/defines
  - Example: `python3-optimized` with `-O3 -march=native`
  - **No source code changes**

- **Configure-Only** (High Trust): Same source, different build options
  - Example: `nginx-http3` with `--with-http_v3_module`
  - **No patches, just different ./configure flags**

- **Patches** (Lower Trust): Modified source code
  - Requires more scrutiny
  - Used when necessary

**Most opinions should be pure-compilation or configure-only** for maximum user confidence.

## Documentation

### Essential Reading
- [**Power Redistribution**](docs/power-redistribution.md) - **THE MANIFESTO**: Re-empowering users at the expense of gatekeepers
- [**Kernel Opinions**](docs/kernel-opinions.md) - **THE EXAMPLE**: Making kernel customization trivial (vs deliberately painful)
- [**Trust Model**](docs/trust-model.md) - Why reproducibility is our only power
- [**Comprehensive Design**](docs/comprehensive-design.md) - Full vision: Real freedom, not rhetoric
- [Why Lebowski?](docs/motivation.md) - Philosophy and the middle ground between FreeBSD ports and binary packages

### Technical Design
- [**Reproducible Builds**](docs/reproducible-builds.md) - Container-based, bit-for-bit reproducible builds (THE foundation)
- [Opinion Types & Purity](docs/opinion-types.md) - Understanding opinion trust levels (pure-compilation > configure-only > patches)
- [Opinion Format](docs/opinion-format.md) - YAML format for defining package modifications
- [Build Tool](docs/build-tool.md) - CLI tool design and implementation
- [Architecture](docs/architecture.md) - Technical architecture and components

### Planning & Research
- [Roadmap](docs/roadmap.md) - Phased development plan (Phase 1: opinion definitions, Phase 2: pre-built packages)
- [**Package Research**](docs/package-research.md) - Analysis of popular Debian packages and opinion opportunities
- [Use Cases](docs/use-cases.md) - Example scenarios and user stories
