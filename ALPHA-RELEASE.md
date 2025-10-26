# Lebowski Alpha Release

## Status: Alpha Implementation Complete

**Version:** 0.1.0-alpha
**Date:** 2025-01-25
**Mission:** Re-empower common users at the expense of distribution gatekeepers

## What's Implemented

### ✅ Core Components

1. **Opinion System**
   - YAML-based opinion definitions
   - Purity level validation (pure-compilation > configure-only > patches)
   - Sample opinions for: Linux kernel, nginx, Python, Redis

2. **Build Tool** (`lebowski` CLI)
   - `build` - Build packages with opinions
   - `validate` - Validate opinion YAML files
   - `show` - Display opinion details
   - `search` - Search opinions (stub)
   - `verify` - Verify reproducibility (stub)

3. **Reproducible Build Foundation**
   - Dockerfile for reproducible build environment
   - SOURCE_DATE_EPOCH configuration
   - strip-nondeterminism integration
   - Fixed locale/timezone

4. **Documentation**
   - Complete vision and philosophy (13 docs)
   - Technical specifications
   - Political manifesto
   - Package research (30+ packages)

### 📋 Sample Opinions Created

**Linux Kernel** (THE flagship example):
- `desktop-1000hz` - Kernel.org's default (vs Debian's 250Hz)
- `gaming` - Real-time, low-latency
- `server` - Debian's defaults

**nginx**:
- `http3` - HTTP/3 (QUIC) support
- `performance` - Aggressive optimization

**Python**:
- `optimized` - PGO + LTO for 10-30% speedup

**Redis**:
- `performance` - Optimized builds

## Quick Start

### Installation

```bash
cd /Users/jgowdy/lebowski/build-tool
pip3 install -e .
```

### Build Your First Package

```bash
# The flagship: Custom kernel (1000Hz vs Debian's 250Hz)
lebowski validate ../opinions/linux/desktop-1000hz.yaml
lebowski build linux --opinion-file ../opinions/linux/desktop-1000hz.yaml

# Or nginx with HTTP/3
lebowski validate ../opinions/nginx/http3.yaml
lebowski build nginx --opinion-file ../opinions/nginx/http3.yaml
```

## Current Limitations (Alpha)

### Not Yet Implemented

1. **Full Container Integration**
   - Container builds stub in place
   - Currently falls back to local builds
   - Need to implement Docker/Podman exec

2. **Opinion Repository**
   - Currently uses local files only
   - Need Git integration for fetching opinions
   - Need `lebowski search` implementation

3. **Verification System**
   - `lebowski verify` is a stub
   - Need rebuild-and-compare logic
   - Need buildinfo parsing

4. **Complete Build Modifications**
   - Kernel config: Implemented
   - Configure flags: Partial (debian/rules parsing needed)
   - Compiler flags: Partial (needs DEB_*_APPEND)
   - Patches: Not implemented

5. **Pre-built Packages (Phase 2)**
   - No APT repository yet
   - No automated CI/CD builds
   - No community verification network

### Known Issues

- Local builds may not be fully reproducible yet
- debian/rules modification is simplified
- Some opinion modifications are logged but not applied
- No package signing yet

## What Works Right Now

You can:

✅ Validate opinion YAML files
✅ Parse and display opinions
✅ Fetch Debian source packages
✅ Apply kernel config modifications
✅ Build packages (local, not yet containerized)
✅ Set reproducible environment variables

## Next Steps for Production

### Phase 1 Completion (MVP)

1. **Complete Container Builds**
   - Implement Docker/Podman integration
   - Mount source into container
   - Execute build in container
   - Extract results

2. **Full Opinion Application**
   - debian/rules parsing and modification
   - DEB_CFLAGS_APPEND environment
   - Patch application
   - Build script execution

3. **Opinion Repository**
   - Set up Git repository
   - Implement fetch logic
   - `lebowski search` implementation
   - Opinion versioning

4. **Verification**
   - Implement rebuild-and-compare
   - Buildinfo generation and parsing
   - Hash verification
   - Trust scoring

### Phase 2 (Pre-built Packages)

1. **Build Infrastructure**
   - CI/CD for automated builds
   - Multi-architecture support
   - Package signing

2. **APT Repository**
   - Repository hosting
   - Package publication
   - Automatic updates

3. **Community Verification**
   - Distributed verification network
   - Consensus tracking
   - Trust metrics

## Testing the Alpha

### Test 1: Validate Opinions

```bash
lebowski validate opinions/linux/desktop-1000hz.yaml
lebowski validate opinions/nginx/http3.yaml
lebowski validate opinions/python3/optimized.yaml
```

All should pass validation.

### Test 2: Show Opinion Details

```bash
lebowski show linux:desktop-1000hz
lebowski show nginx:http3
```

Should display full opinion details.

### Test 3: Build (Advanced - requires build deps)

```bash
# Install build tools
sudo apt-get install build-essential devscripts dpkg-dev

# Try building (will take time)
lebowski build nginx --opinion-file opinions/nginx/performance.yaml
```

## Project Structure

```
lebowski/
├── README.md                    # Project overview
├── ALPHA-RELEASE.md            # This file
├── docs/                       # Complete documentation
│   ├── power-redistribution.md # THE MANIFESTO
│   ├── kernel-opinions.md      # Flagship example
│   ├── trust-model.md          # Reproducibility foundation
│   ├── reproducible-builds.md  # Technical implementation
│   ├── opinion-types.md        # Purity levels
│   ├── package-research.md     # 30+ packages analyzed
│   └── ...                     # More docs
├── opinions/                   # Opinion definitions
│   ├── linux/                  # Kernel opinions
│   ├── nginx/                  # nginx opinions
│   ├── python3/                # Python opinions
│   └── redis/                  # Redis opinions
├── build-tool/                 # The lebowski CLI
│   ├── lebowski/
│   │   ├── cli.py             # Command-line interface
│   │   ├── opinion.py         # Opinion parser
│   │   └── builder.py         # Build engine
│   └── setup.py
└── containers/                 # Build containers
    └── bookworm-builder.Dockerfile
```

## The Core Thesis

**The free software movement took power from corporations and gave it to developers.**

**Lebowski takes power from developers and gives it to users.**

**This completes the revolution.**

## Success Metrics

### Technical
- ✅ Opinions can be validated
- ✅ Packages can be built
- ✅ Reproducible environment defined
- ⏳ Container builds work
- ⏳ Builds are bit-for-bit reproducible

### Political
- ✅ Vision documented
- ✅ Manifesto written
- ✅ Flagship example (kernel) defined
- ⏳ Community adoption
- ⏳ Actual users building packages

## How to Contribute

1. **Test the alpha** - Try building packages, report issues
2. **Create opinions** - Write YAML files for your favorite packages
3. **Improve build tool** - Implement TODOs in code
4. **Spread the word** - The mission matters

## Contact

- GitHub: (to be created)
- Email: opinions@lebowski.org (to be set up)
- Docs: `/docs/` directory

## License

GPLv3 or later

## Final Note

This is an alpha. It's incomplete. But the **mission is clear** and the **foundation is solid**.

Reproducibility enables distributed building.
Distributed building eliminates infrastructure costs.
Zero costs enable sustainability.
Sustainability enables success.

**The economics work. The politics matter. The code will follow.**

---

*"Yeah, well, that's just like, your opinion, man."*

**Exactly. And now users can express their opinions without asking permission.**

**Let's build this.**
