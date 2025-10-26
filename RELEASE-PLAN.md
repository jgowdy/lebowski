# Lebowski v1.0 Release Plan

## Current Status: Alpha → v1.0

**Working:**
- ✅ Reproducible builds (bash proven: identical SHA256)
- ✅ Container infrastructure (Docker)
- ✅ Opinion system (YAML configs)
- ✅ Build manifests (JSON with provenance)
- ✅ Parallel builds (unique dirs per package)
- ✅ Parallel compilation (`make -j$(nproc)`)
- ✅ 10+ test opinions (bash, coreutils, grep, sed, tar, gzip, bzip2, xz-utils, findutils, diffutils, patch, make, util-linux)

## v1.0 Requirements (1-2 weeks)

### 1. Core Package Set (20-30 packages)
Build and verify essential utilities:

**Priority 1 (Done):**
- [x] bash
- [x] coreutils
- [x] grep, sed, tar
- [x] gzip, bzip2, xz-utils
- [x] findutils, diffutils, patch, make

**Priority 2 (Next):**
- [ ] gcc (toolchain)
- [ ] binutils
- [ ] glibc
- [ ] python3
- [ ] perl
- [ ] systemd
- [ ] openssh
- [ ] openssl
- [ ] curl, wget
- [ ] git

**Priority 3 (Nice to have):**
- [ ] nginx
- [ ] postgresql
- [ ] redis
- [ ] docker

### 2. Missing Features

**Critical:**
- [x] `verify` command - rebuild and compare hashes
- [ ] Error handling improvements
- [ ] Better progress output
- [ ] Usage examples

**Important:**
- [ ] GPG signing for manifests
- [ ] Opinion validation strictness
- [ ] Container image versioning
- [ ] Build artifact cleanup

**Nice to have:**
- [ ] Web UI for browsing manifests
- [ ] CI integration examples
- [ ] Performance metrics

### 3. Documentation

- [x] README
- [x] INSTALL guide
- [x] Opinion authoring guide
- [ ] Verification guide (covered in INSTALL + OPINION-GUIDE)
- [ ] FAQ
- [ ] Architecture docs
- [ ] API docs (if library use)

### 4. Testing

- [ ] Test on clean system
- [ ] Test with different container runtimes (podman)
- [ ] Test on different architectures (arm64)
- [ ] Reproducibility verification (3+ independent builds)
- [ ] Error case testing

### 5. Release Artifacts

- [ ] GitHub repository
- [ ] GitHub releases (tags)
- [ ] Container images on registry
- [ ] Example opinions repository
- [ ] Announcement blog post

## v2.0: XSC Integration

**After v1.0 stable:**
- [ ] XSC toolchain in container
- [ ] XSC-specific opinions (ring syscalls)
- [ ] libxsc-rt integration
- [ ] XSC kernel module
- [ ] Hardware CFI variants
- [ ] Full XSC distribution

## Timeline

**Week 1:**
- Finish Priority 2 packages (gcc, glibc, systemd, etc)
- Implement `verify` command
- Write INSTALL + opinion authoring guide

**Week 2:**
- Test on clean systems
- Fix bugs
- Write remaining docs
- Create GitHub repo

**Week 3:**
- Release v1.0
- Announce
- Community feedback

**Months 2-3:**
- Stabilize based on feedback
- v2.0: XSC integration

## Success Criteria for v1.0

1. ✅ Reproducible builds proven with 20+ packages
2. ✅ Documentation complete
3. ✅ Clean install works on Ubuntu/Debian
4. ✅ `verify` command works
5. ✅ At least 3 independent verifications

## Notes

- Focus on stability over features
- Reproducibility is THE killer feature
- XSC integration is v2.0, not v1.0
- Community verification is critical
- Don't rush - get it right

## Blockers

**None currently.** Core functionality works. Just need:
- More package testing
- Documentation
- Polish
