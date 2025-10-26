# Lebowski Implementation Gaps

**Current Status: ~30% Complete**

Last updated: 2025-10-26

## Critical Gaps (Blocking Core Functionality)

### 1. Container Builds ❌ CRITICAL
**File:** `build-tool/lebowski/builder.py:260-274`

**Current State:**
```python
def _build_in_container(self, source_dir, manifest):
    # TODO: Implement container build
    # For now, fall back to local build
    return self._build_local(source_dir, manifest)
```

**Why Critical:**
- Without containers, reproducibility is NOT guaranteed
- Different systems = different outputs
- Can't verify builds across machines

**What's Needed:**
1. Docker/Podman integration
2. Reproducible build container (Debian bookworm base)
3. Volume mounting for source code
4. Environment isolation
5. Container image pinning (digest-based, not tags)

**Estimated Effort:** 2-3 days

**Acceptance Criteria:**
- [ ] Build in Docker container
- [ ] Same source → same .deb hash on different machines
- [ ] Container image is reproducibly built
- [ ] Works with both Docker and Podman

---

### 2. Configure Flags Modification ❌ CRITICAL
**File:** `build-tool/lebowski/builder.py:164-177`

**Current State:**
```python
def _apply_configure_flags(self, source_dir, flags):
    # This is simplified - real implementation needs to parse debian/rules
    print(f"  Note: Configure flags modification not fully implemented yet")
```

**Why Critical:**
- Many opinions rely on configure flags
- XSC packages REQUIRE --host=x86_64-xsc-linux-gnu
- Can't build cross-compiled packages without this

**What's Needed:**
1. Parse debian/rules (complex - it's a Makefile)
2. Modify configure invocations
3. Handle different build systems (autoconf, cmake, meson)
4. Fallback: Use DEB_CONFIGURE_EXTRA_FLAGS (already partially done)

**Current Workaround:**
- Using DEB_CONFIGURE_EXTRA_FLAGS environment variable
- Works for some packages but not all

**Estimated Effort:** 3-4 days

**Acceptance Criteria:**
- [ ] Can add/remove configure flags
- [ ] Works with autoconf packages
- [ ] Works with cmake packages
- [ ] XSC cross-compilation works

---

### 3. Patch Application System ❌ HIGH
**File:** `build-tool/lebowski/builder.py` (doesn't exist!)

**Current State:**
- Opinion format supports patches
- Builder doesn't apply them
- No _apply_patches() method

**Why High Priority:**
- Some packages NEED patches for XSC compatibility
- Lower purity opinions require patch support
- Limits us to pure-compilation and configure-only

**What's Needed:**
1. Download/fetch patches from URLs or local files
2. Verify patch hashes (security!)
3. Apply patches with `patch` or `quilt`
4. Handle patch failures
5. Record applied patches in manifest

**Estimated Effort:** 2 days

**Acceptance Criteria:**
- [ ] Can apply patches from opinion
- [ ] Verifies patch hashes
- [ ] Handles patch conflicts
- [ ] Records patches in manifest

---

### 4. Build Dependency Installation ❌ MEDIUM
**File:** `build-tool/lebowski/builder.py:333-335`

**Current State:**
```python
# Skip build-dep installation (assume dependencies are already installed)
print("  (Skipping build-dep - assuming dependencies installed)")
```

**Why Medium Priority:**
- Builds fail without dependencies
- Not user-friendly (manual setup required)
- Containers will handle this better

**What's Needed:**
1. Parse Build-Depends from debian/control
2. Install dependencies (apt-get build-dep)
3. Handle missing dependencies gracefully
4. Option to skip (for containers with pre-installed deps)

**Estimated Effort:** 1 day

**Acceptance Criteria:**
- [ ] Automatically install build deps
- [ ] Works without sudo (in containers)
- [ ] Option to skip for pre-configured environments

---

### 5. Verification Command ❌ HIGH
**File:** `build-tool/lebowski/cli.py:239-254`

**Current State:**
```python
def verify(ctx, package_file):
    click.echo("(Verification implementation coming soon)")
```

**Why High Priority:**
- Core concept of Lebowski is verification
- Build Ring depends on this
- Can't prove reproducibility without it

**What's Needed:**
1. Download manifest from URL or local file
2. Rebuild package using manifest's opinion
3. Compare SHA256 hashes
4. Report match/mismatch
5. GPG verification of signatures

**Estimated Effort:** 3-4 days

**Acceptance Criteria:**
- [ ] Can verify packages from manifest URL
- [ ] Rebuilds in container
- [ ] Reports hash match/mismatch
- [ ] Verifies GPG signatures
- [ ] Works with Build Ring concept

---

### 6. GPG Signing ❌ HIGH
**File:** Not implemented anywhere

**Current State:**
- Mentioned in docs
- No implementation

**Why High Priority:**
- Trust model requires cryptographic signatures
- Build Ring needs signatures to verify who built what
- Prevent manifest tampering

**What's Needed:**
1. GPG integration (python-gnupg)
2. Sign manifests with builder's key
3. Sign attestations
4. Verify signatures
5. Web of trust support

**Estimated Effort:** 2-3 days

**Acceptance Criteria:**
- [ ] Can sign manifests with GPG
- [ ] Can verify signatures
- [ ] Integrates with Build Ring
- [ ] Key management documented

---

### 7. Opinion Repository ❌ MEDIUM
**File:** `build-tool/lebowski/cli.py:72-79`

**Current State:**
```python
# TODO: Fetch from opinion repository
click.echo("(Opinion repository integration coming soon)")
```

**Why Medium Priority:**
- Currently requires local files
- Can't easily share opinions
- No centralized discovery

**What's Needed:**
1. Opinion repository design (GitHub-based? HTTP API?)
2. Fetch opinions by package:name
3. Verify opinion signatures
4. Local caching
5. Version pinning

**Estimated Effort:** 4-5 days

**Acceptance Criteria:**
- [ ] Can fetch opinions from central repo
- [ ] Verifies opinion signatures
- [ ] Caches locally
- [ ] Supports version pinning
- [ ] Works offline (cached opinions)

---

## Non-Critical Gaps (Nice to Have)

### 8. Kernel Config Application ⚠️ WORKS (Untested)
**File:** `build-tool/lebowski/builder.py:144-162`

**Current State:**
- Implementation exists
- Uses scripts/config
- Untested with real kernel build

**What's Needed:**
- Test with actual kernel package
- Handle edge cases

**Estimated Effort:** 1 day testing

---

### 9. Better Error Handling ⚠️ PARTIAL
**Current State:**
- Basic exception handling
- No retry logic
- No cleanup on failure

**What's Needed:**
1. Retry failed downloads
2. Clean up on build failure
3. Better error messages
4. Logging system

**Estimated Effort:** 2 days

---

### 10. Attestation Posting Automation ⚠️ MANUAL
**Current State:**
- Generates attestations
- User must manually copy/paste

**What's Needed:**
1. Twitter API integration
2. GitHub API integration
3. Mastodon API integration
4. Slack webhooks
5. Auto-posting option

**Estimated Effort:** 3-4 days

---

## Testing Gaps

### 11. No Successful Builds Yet ❌ CRITICAL
**Current State:**
- bash build in progress (first attempt)
- No verified .deb outputs
- No actual manifests generated
- All examples are theoretical

**What's Needed:**
- Get bash to build successfully
- Generate real manifest.json
- Test attestation with real data
- Verify reproducibility (rebuild → same hash)

**Estimated Effort:** 1-2 days (debugging)

---

### 12. XSC Integration Untested ❌ BLOCKED
**Current State:**
- XSC toolchain exists
- No XSC runtime (libxsc-rt)
- No XSC kernel module
- Can't test XSC packages

**What's Needed:**
1. Build libxsc-rt runtime library
2. Create XSC kernel module
3. Test with hello-world
4. Then test with real packages

**Estimated Effort:** 2-3 weeks (separate project)

---

## Priority Order

### Week 1: Make Lebowski Work
1. ✅ Get bash building (IN PROGRESS)
2. Generate first manifest
3. Test attestation generation
4. Fix immediate bugs

### Week 2: Core Features
1. Container builds (CRITICAL)
2. Configure flags modification
3. Verification command

### Week 3: Security & Trust
1. GPG signing
2. Patch application
3. Opinion repository

### Week 4: XSC Integration
1. Build libxsc-rt
2. Create XSC kernel module
3. Test XSC packages
4. Verify XSC compliance

---

## What Works Right Now

✅ Opinion parsing and validation
✅ Attestation format generation
✅ CLI structure
✅ Source fetching (apt-get source)
✅ Basic local builds (with nodoc flag)
✅ Manifest metadata tracking
✅ SHA256 hashing
✅ Reproducible environment variables

---

## Honest Assessment

**Lebowski is 30% complete:**
- Design: 95% done ✅
- Implementation: 30% done ⚠️
- Testing: 5% done ❌

**To reach MVP (Minimum Viable Product):**
- Need container builds ❌
- Need verification command ❌
- Need 1 successful reproducible build ⚠️ (in progress)

**To reach 1.0:**
- Need all critical gaps filled
- Need XSC integration working
- Need 15+ successful package builds
- Need distributed verification working

---

**Bottom line:** We have a solid foundation. The hard work is ahead.
