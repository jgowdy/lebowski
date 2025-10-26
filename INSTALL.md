# Lebowski Installation Guide

## Requirements

- **Docker** or **Podman** (for reproducible builds)
- **Python 3.8+**
- **Debian/Ubuntu base system** (for `apt-get source`)
- 10GB+ free disk space

## Quick Install

```bash
# Clone repository
git clone https://github.com/jgowdy/lebowski.git
cd lebowski

# Install Python dependencies
pip3 install -r build-tool/requirements.txt

# Test installation
python3 -m lebowski.cli --help
```

## Docker Setup

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
# Log out and back in

# Build Lebowski container
cd lebowski/container/lebowski-builder
docker build -t lebowski/builder:bookworm .
```

## Verify Installation

```bash
# Build bash with test opinion
python3 -m lebowski.cli build bash \
    --opinion-file opinions/bash/test-vanilla.yaml \
    --output-dir ./test-output

# Check the output
ls -lh test-output/
cat test-output/bash-*.lebowski-manifest.json
```

## Performance Tuning

### Parallel Compilation
Lebowski auto-detects CPU count and uses `make -j$(nproc)`. No configuration needed.

### Fast Storage
If you have fast storage (SSD/RAID), Lebowski will use `/build` if it exists, otherwise `/tmp`:

```bash
# Create /build directory (requires sudo)
sudo mkdir -p /build
sudo chown $USER:$USER /build
```

### Parallel Package Builds
Build multiple packages simultaneously:

```bash
# Terminal 1
python3 -m lebowski.cli build bash --opinion-file opinions/bash/test-vanilla.yaml --output-dir ./output1 &

# Terminal 2
python3 -m lebowski.cli build coreutils --opinion-file opinions/coreutils/test-vanilla.yaml --output-dir ./output2 &
```

Each build gets a unique directory, so they don't collide.

## Troubleshooting

### "No container runtime found"
Install Docker or Podman:
```bash
# Docker
curl -fsSL https://get.docker.com | sh

# OR Podman
sudo apt install podman
```

### "Container build failed"
Check if container image exists:
```bash
docker images | grep lebowski
```

If missing, build it:
```bash
cd container/lebowski-builder
docker build -t lebowski/builder:bookworm .
```

### "apt-get source failed"
Enable source repositories in `/etc/apt/sources.list`:
```bash
# Add deb-src lines
deb-src http://deb.debian.org/debian bookworm main
deb-src http://security.debian.org/debian-security bookworm-security main
```

Then: `sudo apt-get update`

### Permission Errors
Ensure your user can run Docker:
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

## Advanced: Multi-Architecture

Lebowski supports different architectures through Docker buildx:

```bash
# Setup buildx
docker buildx create --name lebowski-builder --use
docker buildx inspect --bootstrap

# Build for arm64
docker buildx build --platform linux/arm64 \
    -t lebowski/builder:bookworm-arm64 \
    container/lebowski-builder/
```

## Next Steps

- Read [Opinion Authoring Guide](OPINION-GUIDE.md)
- Browse existing opinions in `opinions/`
- Join community discussions
- Verify existing builds: `python3 -m lebowski.cli verify <manifest-url>`
