# Reproducible Builds in Lebowski

## Core Principle

**Everything Lebowski does MUST be reproducible.**

Given the same:
- Source package
- Opinion definition
- Build environment

You MUST get the **bit-for-bit identical binary**.

## Why Reproducibility Matters

### 1. Trust Through Verification

Don't ask users to trust pre-built packages. Let them **verify**:

```bash
# Download pre-built package
apt download nginx-http3

# Build it yourself from same opinion
lebowski build nginx --opinion http3 --container

# Compare
sha256sum nginx-http3*.deb
# Should match exactly
```

If hashes match, you know:
- No tampering
- No backdoors
- Build process is honest
- Pre-built binary is trustworthy

### 2. Security Auditing

Anyone can:
- Review the opinion definition
- Rebuild the package
- Verify it matches the published binary
- Catch any malicious modifications

**"Trust, but verify" becomes actually possible.**

### 3. Decentralization

Multiple parties can:
- Build the same package independently
- Verify they all produce identical output
- Host the packages without central authority
- No single point of trust required

### 4. Debugging

Same input = same output means:
- Bugs are reproducible
- Testing is reliable
- Rollbacks work correctly
- No "works on my machine"

## Container-Based Builds

### Why Containers?

**Consistent build environment:**
- Same Debian version
- Same compiler version
- Same dependencies
- Same timestamps
- Same filesystem layout
- Same environment variables

**Anyone can reproduce:**
```bash
# Build environment is defined in container
lebowski build nginx --opinion http3 --container

# Container definition is version-controlled
# Everyone gets the same environment
```

### Container Definition

Every Lebowski build uses a defined container:

```dockerfile
# lebowski-build-base/bookworm.Dockerfile
FROM debian:bookworm@sha256:...  # Pin exact base image

# Install build tools (pinned versions)
RUN apt-get update && \
    apt-get install -y \
        build-essential=12.9 \
        devscripts=2.23.4 \
        dpkg-dev=1.21.22 \
        debhelper=13.11.4

# Set reproducible environment
ENV SOURCE_DATE_EPOCH=0
ENV TZ=UTC
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Reproducible filesystem
RUN echo "force-unsafe-io" > /etc/dpkg/dpkg.cfg.d/02speedup
```

Version controlled, publicly available, pinned to specific versions.

## Achieving Reproducibility

### 1. Fixed Timestamps

Source files have varied timestamps. Fix them:

```bash
# Use SOURCE_DATE_EPOCH
export SOURCE_DATE_EPOCH=$(dpkg-parsechangelog -SDate | date -f - +%s)

# Or use opinion definition timestamp
export SOURCE_DATE_EPOCH=1704067200  # 2024-01-01 00:00:00 UTC
```

### 2. Deterministic Ordering

Ensure consistent ordering:
- File lists sorted
- Tar archives sorted
- Symbol tables sorted

```bash
# In build scripts
find . -type f | sort | ...
```

### 3. Fixed Locale

Locale affects sorting and output:

```bash
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
```

### 4. Fixed Timezone

```bash
export TZ=UTC
```

### 5. Fixed Build Path

Build in same path every time:

```bash
# Always build in
/build/<package>-<version>/
```

### 6. Strip Non-Determinism

Debian provides tools to remove non-deterministic elements from build outputs.

#### strip-nondeterminism

Automatically removes non-deterministic data:
- Timestamps in JAR files
- Timestamps in gzip files
- Timestamps in PNG files
- Randomness in Python `.pyc` files
- Archive member ordering
- File metadata timestamps

```bash
# Install
apt-get install strip-nondeterminism

# Use in build process (usually automatic with debhelper)
strip-nondeterminism path/to/file

# Debhelper integration (automatic in dh)
dh_strip_nondeterminism
```

#### dh_strip_nondeterminism

Debhelper tool that runs `strip-nondeterminism` on all built files:

```bash
# In debian/rules (automatic with dh)
%:
    dh $@

# dh automatically calls dh_strip_nondeterminism
```

#### Common Non-Determinism Sources

**Python bytecode**:
```bash
export PYTHONHASHSEED=0
```

**Rust builds**:
```bash
export RUSTFLAGS="-C link-arg=-Wl,--hash-style=gnu"
```

**Debug symbols** (build paths):
```bash
export DEB_BUILD_OPTIONS="reproducible=-fixfilepath"
# Or
CFLAGS+=" -fdebug-prefix-map=/build/package=."
```

**Jar files**:
```bash
strip-nondeterminism --type jar file.jar
```

**Archive timestamps**:
```bash
# tar
tar --mtime='@1704067200' -czf archive.tar.gz files/

# zip
TZ=UTC zip -X archive.zip files/
```

#### File Metadata

Reset file timestamps and permissions:
```bash
# In container build
find . -newermt "@${SOURCE_DATE_EPOCH}" -print0 | \
    xargs -0r touch --no-dereference --date="@${SOURCE_DATE_EPOCH}"

# Or use find-dbgsym-package
find . -type f -exec touch -d @${SOURCE_DATE_EPOCH} {} +
```

#### Build Path Variations

Different build paths can cause issues:
```bash
# Map build path to fixed location
export DEB_CFLAGS_APPEND="-fdebug-prefix-map=${PWD}=/usr/src/package"
export DEB_CXXFLAGS_APPEND="-fdebug-prefix-map=${PWD}=/usr/src/package"

# Or
dpkg-buildpackage --sanitize-env
```

### 7. Pinned Dependencies

Build dependencies must be exact versions:

```yaml
# In build container spec
build_dependencies:
  - gcc-13=13.2.0-1
  - binutils=2.40-2
  - libc6-dev=2.36-9
```

### 8. Document Build Environment

Every opinion includes build environment spec:

```yaml
# opinions/nginx/http3.yaml
build_environment:
  distribution: debian
  release: bookworm
  container_image: "lebowski/build-base:bookworm-20240101"
  container_digest: "sha256:abc123..."
```

## Lebowski Build Tool Integration

### Container Mode (Default)

```bash
lebowski build nginx --opinion http3

# Internally:
# 1. Pull build container
# 2. Run build inside container
# 3. Extract .deb from container
# 4. Verify reproducibility metadata
```

### Local Mode (Advanced)

```bash
lebowski build nginx --opinion http3 --local

# Warning: May not be reproducible
# Build environment varies by host
# Only for testing/development
```

### Verification Mode

```bash
lebowski verify nginx-http3_1.24.0-1~opinion1_amd64.deb

# 1. Download opinion definition
# 2. Rebuild in container
# 3. Compare hashes
# 4. Report match/mismatch
```

## Build Attestation

Every package includes attestation:

```json
{
  "package": "nginx-http3",
  "version": "1.24.0-1~opinion1",
  "opinion": "http3",
  "opinion_version": "1.0",
  "opinion_git_commit": "abc123...",
  "debian_source": {
    "package": "nginx",
    "version": "1.24.0-1",
    "sha256": "..."
  },
  "build_environment": {
    "container_image": "lebowski/build-base:bookworm-20240101",
    "container_digest": "sha256:...",
    "source_date_epoch": 1704067200
  },
  "built_by": "lebowski-ci",
  "built_at": "2024-01-15T10:30:00Z",
  "sha256": "...",
  "buildinfo_url": "https://buildinfo.bx.ee/..."
}
```

Embedded in .deb metadata, also published separately.

## Buildinfo Files

Debian's `.buildinfo` format documents build:

```
Format: 1.0
Source: nginx
Binary: nginx-http3
Architecture: amd64
Version: 1.24.0-1~opinion1
Build-Path: /build/nginx-1.24.0
Build-Environment:
 SOURCE_DATE_EPOCH=1704067200
 LANG=C.UTF-8
Installed-Build-Depends:
 gcc-13=13.2.0-1
 libc6-dev=2.36-9
 ...
Checksums-Sha256:
 abc123... nginx-http3_1.24.0-1~opinion1_amd64.deb
```

Stored and published for every build.

## Reproducible Builds Database

Public database of all builds:

```
https://builds.bx.ee/nginx/http3/
  ├── 1.24.0-1~opinion1/
  │   ├── nginx-http3_1.24.0-1~opinion1_amd64.deb
  │   ├── nginx-http3_1.24.0-1~opinion1_amd64.buildinfo
  │   ├── attestation.json
  │   └── build.log
```

Anyone can:
- Download buildinfo
- Reproduce the build
- Verify hash matches
- Submit alternative builds for verification

## Community Verification

Multiple builders verify same opinion:

```
Opinion: nginx:http3 1.24.0-1~opinion1
Builder                  SHA256                              Status
lebowski-ci             abc123...                            ✓ Match
@user1 (independent)    abc123...                            ✓ Match
@user2 (independent)    abc123...                            ✓ Match
@user3 (independent)    def456...                            ✗ Mismatch!
```

If multiple independent builders get same hash: **High confidence**
If mismatch: **Investigation required**

## Implementation Plan

### Phase 1: Build Container

1. Create base build containers for each Debian release
2. Pin all dependencies
3. Configure reproducible environment
4. Test reproducibility with sample builds
5. Publish containers to Docker Hub / GitHub Container Registry

### Phase 2: Build Tool Integration

1. Modify `lebowski build` to use containers by default
2. Pass opinion definitions into container
3. Run build inside container
4. Extract .deb and buildinfo
5. Generate attestation

### Phase 3: Verification

1. Implement `lebowski verify` command
2. Download buildinfo from repository
3. Rebuild in container
4. Compare hashes
5. Report results

### Phase 4: Public Build Database

1. Set up builds.bx.ee
2. Store buildinfo, attestations, logs
3. API for querying builds
4. Community submission of verification builds

## Example Workflow

### Opinion Author

```bash
# Create opinion
vim opinions/nginx/http3.yaml

# Test build locally (in container)
lebowski build nginx --opinion http3 --container

# Verify reproducibility
lebowski build nginx --opinion http3 --container
sha256sum nginx-http3*.deb  # Should match previous build

# Submit opinion to repository
git add opinions/nginx/http3.yaml
git commit -m "Add nginx HTTP/3 opinion"
git push
# Open PR
```

### Automatic Build System

```bash
# CI detects new opinion
# Build in container
lebowski build nginx --opinion http3 --container

# Generate attestation
lebowski attest nginx-http3*.deb

# Publish to repository
apt-ftparchive add nginx-http3*.deb

# Publish buildinfo
cp nginx-http3*.buildinfo builds.bx.ee/

# Sign and publish
dpkg-sig --sign builder nginx-http3*.deb
```

### User Verification

```bash
# Download pre-built package
apt download nginx-http3

# Verify
lebowski verify nginx-http3*.deb

# Output:
# ✓ Opinion definition found: nginx:http3 v1.0
# ✓ Buildinfo downloaded
# ⏳ Rebuilding in container...
# ✓ Build successful
# ✓ Hash matches: abc123...
# ✓ Package is reproducible and verified
```

## Technical Considerations

### Docker vs Podman

Support both:

```bash
# Auto-detect
lebowski build nginx --opinion http3

# Explicit
lebowski build nginx --opinion http3 --runtime=docker
lebowski build nginx --opinion http3 --runtime=podman
```

### Build Caching

Container layers cache dependencies:

```dockerfile
# Base layer (rarely changes)
FROM debian:bookworm

# Build tools layer (occasionally changes)
RUN apt-get update && apt-get install -y build-essential

# Package deps layer (per-package, cached)
RUN apt-get build-dep nginx

# Source and build (every time)
COPY source/ /build/
RUN dpkg-buildpackage
```

### Disk Space

Container builds use space:
- Base images: ~100MB each
- Build layers: varies
- Source: varies
- Build artifacts: varies

Typical build: 500MB - 2GB

Cleanup after build:
```bash
lebowski build nginx --opinion http3 --cleanup
```

### Performance

Container overhead is minimal:
- First build: Slower (pull image)
- Subsequent builds: Fast (cached layers)
- Build time: ~same as native
- I/O: Slightly slower on macOS, same on Linux

### Cross-Architecture

Build for different architectures:

```bash
lebowski build nginx --opinion http3 --arch arm64

# Uses qemu-user-static for emulation
# Or native builder on that architecture
```

## Reproducible Build Checklist

For every opinion:

- [ ] Build in defined container
- [ ] Set SOURCE_DATE_EPOCH
- [ ] Set LC_ALL=C.UTF-8
- [ ] Set TZ=UTC
- [ ] Fixed build path
- [ ] Sorted file lists
- [ ] Pinned dependencies
- [ ] Strip build paths
- [ ] Generate buildinfo
- [ ] Test: build twice, compare hashes
- [ ] Document build environment

## Future Enhancements

### 1. Distributed Verification Network

Community members run build verification nodes:
- Automatically rebuild published packages
- Report hash matches/mismatches
- Consensus on package integrity

### 2. Blockchain Attestation

Store package hashes on blockchain for tamper-proof audit trail.

### 3. Build Time Attestation

Secure enclaves attest to build process:
- TPM-backed builds
- SGX enclaves
- Confidential computing

### 4. Reproducible Build Badge

Opinions with verified reproducible builds get badge:

```
nginx:http3  ✓ REPRODUCIBLE (verified by 15 independent builders)
```

## Conclusion

**Reproducibility is not optional in Lebowski. It's fundamental.**

Every package must be:
- Built in a defined container
- Reproducible bit-for-bit
- Verifiable by anyone
- Documented with buildinfo
- Independently verifiable

This creates:
- **Trust** through verification
- **Security** through transparency
- **Decentralization** through reproducibility
- **Freedom** through verifiability

"Don't trust us. Verify yourself."
