# Lebowski Build Tool

**Re-empowering common users at the expense of distribution gatekeepers.**

Build Debian packages with custom opinions - reproducibly.

## The Mission

Take power from those who currently control package builds (Debian Developers, maintainers, "experts") and give it to those who actually use the software (common users).

## Installation

```bash
git clone https://github.com/jgowdy/lebowski.git
cd lebowski/build-tool
pip3 install .
```

That's it. The `lebowski` command is now in your PATH.

## Quick Start

```bash
# Build Linux kernel with desktop 1000Hz config (vs Debian's 250Hz)
lebowski build linux --opinion desktop-1000hz

# Build nginx with HTTP/3 support
lebowski build nginx --opinion http3

# Build Python with PGO optimization
lebowski build python3 --opinion optimized

# Validate an opinion file
lebowski validate opinions/linux/desktop-1000hz.yaml

# Show opinion details
lebowski show linux:desktop-1000hz
```

## Core Principle

**Reproducible builds are not optional. They're the economic foundation.**

Without reproducibility, we need expensive centralized infrastructure.
With reproducibility, the community provides infrastructure for free.

Just like package signatures enable distribution mirrors, reproducible builds enable distributed building.

## How It Works

1. **Opinion Definition** - YAML file describing modifications
2. **Fetch Source** - Download Debian source package
3. **Apply Opinion** - Modify according to YAML
4. **Build in Container** - Reproducible environment
5. **Output Package** - Bit-for-bit identical

## Build Receipts (Attestations)

Every build generates a cryptographic receipt - a JSON file containing everything needed to verify and reproduce the build:

- **What was built:** Package name, version, opinion applied
- **When it was built:** Timestamp (ISO 8601 UTC)
- **Input attestation:** SHA256 hashes of all source files and opinion YAML
- **Output attestation:** SHA256 hashes of all generated .deb packages
- **Build environment:** Builder info, Debian version, architecture

Receipts enable:
- **Verification:** Confirm your .deb matches the published build
- **Reproduction:** Rebuild and verify bit-for-bit identical output
- **Trust:** Cryptographic proof of what was built, when, and from what inputs

Receipts are saved as `<package>_<version>_<arch>_receipt.json` in the output directory.

## Opinion Purity Levels

- **pure-compilation** (highest trust) - Only CFLAGS/defines, no source changes
- **configure-only** (high trust) - Only build flags, no patches
- **patches** (lower trust) - Source modifications

## Commands

### build

Build a package with an opinion:

```bash
lebowski build <package> --opinion <name>
lebowski build <package> --opinion-file <file.yaml>
```

Options:
- `--opinion-file` - Use local YAML file
- `--output-dir` - Where to put built packages
- `--no-container` - Build locally (not recommended)
- `--keep-sources` - Don't delete source after build
- `--show-receipt` / `--no-show-receipt` - Display build receipt (default: show)
- `--receipt-format [compact|full|oneline|none]` - Receipt display format (default: compact)
- `--project-name` - Custom project name (appears in package version)

### validate

Validate opinion YAML:

```bash
lebowski validate opinions/nginx/http3.yaml
```

### show

Show opinion details:

```bash
lebowski show nginx:http3
lebowski show linux:desktop-1000hz
```

## Example: Build Custom Kernel

```bash
# The flagship example - kernel customization without pain

# Debian ships 250Hz (server-optimized)
# kernel.org ships 1000Hz (desktop-optimized)
# Users can't easily change this... until now

lebowski build linux --opinion desktop-1000hz

# Wait 1-2 hours for build
# Get: linux-image-*-lebowski-desktop_amd64.deb

sudo dpkg -i linux-image-*-lebowski-desktop*.deb
sudo update-grub
sudo reboot

# Done. Your computer. Your kernel. Your choice.
# No permission needed.
```

## Architecture

```
lebowski/
├── cli.py              # Command-line interface
├── opinion.py          # Opinion parser/validator
├── builder.py          # Build engine
└── __init__.py
```

## Requirements

- Python 3.9+
- Debian-based system
- `apt-get` (for fetching sources)
- `dpkg-buildpackage` (for building)
- Docker or Podman (for reproducible builds)

Install build dependencies:

```bash
sudo apt-get install build-essential devscripts dpkg-dev
```

## Creating Opinions

See `/docs/opinion-format.md` for full specification.

Simple example:

```yaml
version: "1.0"
package: redis
opinion_name: performance
purity_level: pure-compilation

description: |
  Redis with aggressive optimization flags

modifications:
  make_vars:
    OPTIMIZATION: "-O3"
    CFLAGS: "-march=native"
```

## Development

```bash
# Install in dev mode
pip3 install -e .

# Run tests
pytest

# Validate all opinions
find opinions/ -name "*.yaml" -exec lebowski validate {} \;
```

## Philosophy

This tool embodies a simple idea: **users are smart enough to make their own decisions.**

Debian Developers are smart people with valuable expertise. Their opinions should inform choice, not dictate it.

Lebowski provides the tools. Users make the choices. No gatekeepers required.

## Contributing

See `/docs/power-redistribution.md` for the manifesto.

The mission is clear: Transfer power from gatekeepers to users.

Every feature should be evaluated through this lens:
- Does it increase user sovereignty?
- Does it reduce dependence on gatekeepers?
- Does it enable choice without permission?

If yes, build it. If no, reconsider.

## License

MIT

## Resources

- Main docs: `/docs/`
- Opinion repository: `/opinions/`
- Build containers: `/containers/`

---

*"Yeah, well, that's just like, your opinion, man."*

**Exactly. And users deserve the power to hold their own opinions without gatekeepers standing in the way.**
