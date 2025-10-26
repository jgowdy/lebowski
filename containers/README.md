# Lebowski Build Containers

These containers provide reproducible build environments.

## Philosophy

**Reproducible builds are not optional. They're the economic foundation.**

Without reproducibility: We need massive infrastructure
With reproducibility: Community provides infrastructure for free

Just like signatures enable distribution mirrors, reproducibility enables distributed building.

## Available Containers

### bookworm-builder.Dockerfile

Base container for building Debian Bookworm packages.

**Features:**
- Debian Bookworm base (pinned digest)
- SOURCE_DATE_EPOCH set
- strip-nondeterminism installed
- Fixed locale (C.UTF-8)
- Fixed timezone (UTC)
- All build tools pinned

**Usage:**
```bash
docker build -t lebowski/builder:bookworm -f bookworm-builder.Dockerfile .
```

## Reproducibility Checklist

Every container MUST:
- [ ] Use pinned base image (with SHA256 digest)
- [ ] Set SOURCE_DATE_EPOCH
- [ ] Set LC_ALL=C.UTF-8
- [ ] Set TZ=UTC
- [ ] Install strip-nondeterminism
- [ ] Pin all installed packages
- [ ] Document exact versions

## Building

```bash
# Build container
cd containers/
docker build -t lebowski/builder:bookworm -f bookworm-builder.Dockerfile .

# Test reproducibility
docker run --rm lebowski/builder:bookworm env | grep -E "(SOURCE_DATE_EPOCH|LC_ALL|TZ)"
```

## Versioning

Containers are versioned and tagged:
- `lebowski/builder:bookworm-1.0`
- `lebowski/builder:bookworm-20240110` (date-based)

Always use specific tags, never `:latest`
