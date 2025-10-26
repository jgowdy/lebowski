# Lebowski XSC v2.0 Integration Roadmap

## Mission

Build an entire Debian distribution with **zero syscall instructions** using the XSC toolchain and ring-based syscalls.

## Current Status

**v1.0 Baseline: 70% Complete**
- 14 packages building reproducibly
- Container infrastructure proven
- Opinion framework working
- Build manifests tracking provenance
- Verification command tested

**v2.0 XSC Integration: 0% Started**
- XSC toolchain not yet built
- No XSC-enabled container
- No XSC opinions created
- No zero-syscall binaries verified

## XSC Integration Steps

### Phase 1: Build XSC Toolchain

**Goal**: Create x86_64-xsc-linux-gnu-gcc that generates ring-based syscalls instead of `syscall` instructions.

**Requirements**:
1. **GCC source** - Base on GCC 12.x or 13.x
2. **XSC patches** - Modify syscall generation:
   - Replace `syscall` instruction with ring transition
   - Add libxsc-rt linking
   - Generate ring-based call stubs
3. **Build environment** - Bootstrap toolchain
4. **Installation** - Install to `/opt/xsc-toolchain/`

**Steps**:
```bash
# 1. Download GCC source
wget https://ftp.gnu.org/gnu/gcc/gcc-12.3.0/gcc-12.3.0.tar.xz
tar xf gcc-12.3.0.tar.xz
cd gcc-12.3.0

# 2. Apply XSC patches
# TODO: Create patches to replace syscall generation

# 3. Configure for XSC target
./configure \
  --prefix=/opt/xsc-toolchain \
  --target=x86_64-xsc-linux-gnu \
  --enable-languages=c,c++ \
  --disable-multilib

# 4. Build and install
make -j80
make install
```

**Deliverables**:
- [ ] x86_64-xsc-linux-gnu-gcc binary
- [ ] x86_64-xsc-linux-gnu-g++ binary
- [ ] XSC runtime libraries
- [ ] Toolchain installation at /opt/xsc-toolchain/

### Phase 2: Build libxsc-rt

**Goal**: Create the XSC runtime library that handles ring-based syscalls.

**Requirements**:
1. **Ring transition code** - Assembly for ring 0→3 transitions
2. **Syscall table** - Map Linux syscall numbers to ring handlers
3. **Error handling** - Proper errno propagation
4. **Thread safety** - TLS for per-thread state

**Implementation**:
```c
// libxsc-rt/syscall.c
long xsc_syscall(long nr, long arg1, long arg2, ...) {
    // Transition to ring 0
    // Invoke kernel handler
    // Return to ring 3
    // Return result
}
```

**Deliverables**:
- [ ] libxsc-rt.so shared library
- [ ] libxsc-rt.a static library
- [ ] xsc/syscall.h header file
- [ ] Documentation for API

### Phase 3: Create XSC-Enabled Container

**Goal**: Add XSC toolchain to Lebowski container image.

**Dockerfile.xsc**:
```dockerfile
FROM lebowski/builder:bookworm

# Add XSC toolchain
COPY --from=xsc-build /opt/xsc-toolchain /opt/xsc-toolchain

# Add libxsc-rt
COPY --from=xsc-build /opt/xsc-toolchain/lib/libxsc-rt.* /usr/local/lib/

# Update PATH
ENV PATH="/opt/xsc-toolchain/bin:${PATH}"

# Add pkg-config for XSC
COPY xsc.pc /usr/local/lib/pkgconfig/
```

**Build**:
```bash
docker build -f Dockerfile.xsc -t lebowski/builder:xsc .
```

**Deliverables**:
- [ ] lebowski/builder:xsc container image
- [ ] XSC toolchain accessible in container
- [ ] libxsc-rt available for linking

### Phase 4: Create XSC Opinion Template

**Goal**: YAML opinion that builds packages with XSC toolchain.

**opinions/_base/xsc-baseline.yaml**:
```yaml
version: "1.0"
opinion_name: xsc-baseline
purity_level: configure-only

description: |
  Build with XSC toolchain using ring-based syscalls.
  Verifiable zero-syscall binaries.

maintainer:
  name: XSC Project
  email: xsc@lebowski.org

tags: [xsc, security, ring-syscalls]

modifications:
  env:
    CC: x86_64-xsc-linux-gnu-gcc
    CXX: x86_64-xsc-linux-gnu-g++
    AR: x86_64-xsc-linux-gnu-ar
    RANLIB: x86_64-xsc-linux-gnu-ranlib

  ldflags:
    - "-lxsc-rt"

  # Force static linking of XSC runtime
  configure_args:
    - "--enable-static"
    - "--disable-shared"
```

**Per-Package XSC Opinions**:
```
opinions/bash/xsc.yaml    → extends _base/xsc-baseline.yaml
opinions/coreutils/xsc.yaml → extends _base/xsc-baseline.yaml
opinions/gzip/xsc.yaml     → extends _base/xsc-baseline.yaml
```

**Deliverables**:
- [ ] XSC baseline opinion template
- [ ] XSC opinions for 14 baseline packages
- [ ] Opinion inheritance system (extends: _base/xsc-baseline.yaml)

### Phase 5: Build First XSC Package (bash)

**Goal**: Build bash with XSC toolchain and verify zero syscalls.

**Build**:
```bash
python3 -m lebowski.cli build bash \
  --opinion-file opinions/bash/xsc.yaml \
  --output-dir /tmp/bash-xsc \
  --container-image lebowski/builder:xsc
```

**Verification**:
```bash
# Extract bash binary from .deb
dpkg-deb -x /tmp/bash-xsc/bash_*.deb /tmp/bash-xsc-extract

# Verify ZERO syscall instructions
objdump -d /tmp/bash-xsc-extract/bin/bash | grep syscall

# Expected: NO OUTPUT (zero syscall instructions)
# Success: XSC bash uses ring-based syscalls only
```

**Deliverables**:
- [ ] bash .deb built with XSC toolchain
- [ ] Build manifest with XSC opinion hash
- [ ] Verification proof: objdump shows zero syscalls
- [ ] Documentation of verification process

### Phase 6: Expand to Core Packages

**Goal**: Build all 14 baseline packages with XSC toolchain.

**Packages**:
1. bash ✅ (Phase 5 proof of concept)
2. coreutils
3. gzip
4. bzip2
5. xz-utils
6. findutils
7. diffutils
8. patch
9. make
10. sed
11. less
12. screen
13. nano
14. openssl

**Parallel Build**:
```bash
for pkg in coreutils gzip bzip2 xz-utils findutils \
           diffutils patch make sed less screen nano openssl; do
  python3 -m lebowski.cli build $pkg \
    --opinion-file opinions/$pkg/xsc.yaml \
    --output-dir /tmp/$pkg-xsc \
    --container-image lebowski/builder:xsc &
done
```

**Verification**:
```bash
# Verify ALL packages have zero syscalls
for pkg in bash coreutils gzip bzip2 xz-utils findutils \
           diffutils patch make sed less screen nano openssl; do
  echo "=== Checking $pkg ==="
  dpkg-deb -x /tmp/$pkg-xsc/$pkg_*.deb /tmp/$pkg-extract
  objdump -d /tmp/$pkg-extract/bin/* | grep syscall
done

# Expected: NO OUTPUT for all packages
```

**Deliverables**:
- [ ] 14 XSC packages built
- [ ] All packages verified zero syscall
- [ ] Build manifests for all XSC packages
- [ ] Performance comparison: XSC vs baseline

### Phase 7: XSC Distribution Repository

**Goal**: Publish XSC packages as a Debian repository.

**Repository Structure**:
```
/build/xsc/repo/
  dists/
    xsc-bookworm/
      main/
        binary-amd64/
          Packages.gz
          Release
  pool/
    main/
      b/bash/
        bash_5.1-6ubuntu1.1_amd64.deb
        bash_*.lebowski-manifest.json
      c/coreutils/
        coreutils_*.deb
        coreutils_*.lebowski-manifest.json
```

**apt sources.list**:
```
deb https://repo.xsc.lebowski.org/xsc-bookworm main
```

**Deliverables**:
- [ ] XSC Debian repository
- [ ] GPG signing for packages
- [ ] Repository metadata (Packages, Release)
- [ ] Installation instructions

## Success Criteria

**v2.0 Release Requirements**:

1. **XSC Toolchain Built**: x86_64-xsc-linux-gnu-gcc functional
2. **libxsc-rt Working**: Ring-based syscalls operational
3. **Zero Syscalls Verified**: All 14 packages have NO `syscall` instructions
4. **Reproducible**: XSC builds are bit-for-bit reproducible
5. **Documented**: Complete guide for XSC opinion authoring
6. **Repository**: XSC packages available via apt

## Timeline

- **Phase 1-2**: 2-3 weeks (toolchain + libxsc-rt)
- **Phase 3-4**: 1 week (container + opinions)
- **Phase 5**: 2-3 days (bash proof of concept)
- **Phase 6**: 1 week (14 core packages)
- **Phase 7**: 1 week (repository setup)

**Total**: 6-8 weeks for v2.0 XSC integration

## Technical Challenges

### 1. GCC Syscall Generation

**Challenge**: GCC generates `syscall` instructions for Linux syscalls.

**Solution**: Patch GCC to:
- Replace `syscall` instruction generation
- Call xsc_syscall() function instead
- Link libxsc-rt automatically

### 2. Glibc Integration

**Challenge**: Glibc uses `syscall` instructions directly.

**Options**:
- Option A: Patch glibc to use xsc_syscall()
- Option B: Static link everything (avoid glibc syscalls)
- Option C: Build xsc-glibc with modified syscall wrappers

**Recommendation**: Start with Option B (static linking) for simplicity.

### 3. Performance

**Challenge**: Ring transitions may be slower than direct syscalls.

**Mitigation**:
- Syscall batching where possible
- Ring transition caching
- Benchmark and optimize hot paths

### 4. Debugging

**Challenge**: Debugging XSC binaries requires understanding ring transitions.

**Tools**:
- objdump verification scripts
- Ring transition tracing
- Debug XSC opinions with symbols

## Next Steps

**Immediate (Week 1)**:
1. Research GCC syscall generation internals
2. Design libxsc-rt API and implementation
3. Create XSC toolchain build plan
4. Set up /build/xsc/toolchain directory structure

**Short-term (Weeks 2-4)**:
1. Build GCC with XSC modifications
2. Implement libxsc-rt
3. Create XSC container image
4. Build bash with XSC (proof of concept)

**Medium-term (Weeks 5-8)**:
1. Expand to all 14 core packages
2. Set up XSC repository
3. Write XSC integration documentation
4. Independent verification testing

## Conclusion

**v2.0 XSC Integration transforms Lebowski from a reproducible build system into a security-critical distribution platform.**

The XSC toolchain + Lebowski opinions create:
- **Trustworthy binaries**: Reproducible and verifiable
- **Security-hardened**: Zero syscall instructions, ring-based isolation
- **Transparent**: Every modification documented in opinions
- **Auditable**: Complete provenance in build manifests

This is the foundation for the XSC distribution.
