# Opinion Types and Purity Levels

## The Purity Gradient

Not all opinions are equal in terms of trust and risk. We categorize opinions by their "purity" - how much they modify the original Debian source.

### Level 1: Pure Compilation (Highest Trust)

**What it is**: Debian's exact source code, just built with different compiler flags or defines.

**No code changes. Zero source modifications.**

```yaml
# opinions/nginx/performance.yaml
type: pure-compilation
package: nginx

modifications:
  cflags:
    add: ["-O3", "-march=znver3", "-flto"]
  defines:
    add: ["-DTCP_FASTOPEN=1"]
```

**Why users trust this:**
- Debian's code, bit-for-bit
- No patches that could introduce bugs
- No patches that could introduce backdoors
- Just different compilation settings
- Easy to verify: "same source, different flags"

**Examples:**
- CPU-specific optimizations (`-march=znver3`, `-march=skylake`)
- Optimization levels (`-O3` instead of `-O2`)
- LTO (Link-Time Optimization)
- Size optimization (`-Os`)
- Defines that toggle features (`-DDISABLE_TELEMETRY`)

**User confidence: HIGHEST**

### Level 2: Configure-Only (High Trust)

**What it is**: Debian's source, using different `./configure` flags.

**No source patches, but different build-time decisions.**

```yaml
# opinions/nginx/http3.yaml
type: configure-only
package: nginx

modifications:
  configure_flags:
    add: ["--with-http_v3_module"]
    remove: ["--without-http_v2_module"]
```

**Why users trust this:**
- No code changes
- Just using upstream's built-in options
- Enabling/disabling features the upstream intended
- The code paths exist in Debian's source already

**Examples:**
- Enabling optional modules (`--with-http_v3_module`)
- Disabling unwanted features (`--without-ldap`)
- Different feature combinations

**User confidence: HIGH**

### Level 3: Debian Patches (Medium Trust)

**What it is**: Applying patches from Debian's own patch queue differently.

**Uses Debian's patches, just different selection.**

```yaml
# opinions/nginx/upstream-pure.yaml
type: debian-patches
package: nginx

modifications:
  debian_patches:
    remove:
      - "debian-branding.patch"
      - "debian-specific-defaults.patch"
    # Keep security patches, remove branding
```

**Why users trust this:**
- Patches are from Debian itself
- Just selecting which Debian patches to apply
- Not introducing new code
- Debian already reviewed these patches

**Examples:**
- Removing Debian-specific branding
- Removing Debian-specific defaults
- Keeping only security patches

**User confidence: MEDIUM-HIGH**

### Level 4: Upstream Patches (Medium Trust)

**What it is**: Applying patches from upstream project.

**Modifies source, but using upstream's own patches.**

```yaml
# opinions/nginx/upstream-fixes.yaml
type: upstream-patches
package: nginx

modifications:
  patches:
    - source: upstream
      url: "https://github.com/nginx/nginx/commit/abc123.patch"
      description: "Fix memory leak in HTTP/2"
```

**Why users trust this (somewhat):**
- Patches from official upstream
- Upstream reviewed and merged these
- Backporting fixes to stable Debian

**Why users are cautious:**
- Source is modified
- Could introduce bugs
- Could have unexpected interactions
- Requires reviewing patches

**Examples:**
- Backporting bug fixes
- Cherry-picking performance improvements
- Pulling in new features from upstream

**User confidence: MEDIUM**

### Level 5: Third-Party Patches (Lower Trust)

**What it is**: Applying patches from third parties.

**Modifies source with community or custom patches.**

```yaml
# opinions/nginx/community-features.yaml
type: third-party-patches
package: nginx

modifications:
  patches:
    - source: community
      url: "https://github.com/some-project/nginx-patch/custom.patch"
      description: "Custom feature X"
      author: "community-member"
```

**Why users are cautious:**
- Source is modified
- Not reviewed by Debian or upstream
- Could have security implications
- Requires trust in patch author

**When it's useful:**
- Experimental features
- Niche use cases
- Community-maintained improvements

**User confidence: LOWER**
**Requires: Strong documentation, code review, maintainer reputation**

### Level 6: Custom Scripts (Lowest Trust)

**What it is**: Running arbitrary scripts to modify source.

**Maximum flexibility, minimum guarantees.**

```yaml
# opinions/nginx/custom.yaml
type: custom
package: nginx

modifications:
  scripts:
    pre_build: "scripts/custom-modifications.sh"
```

**Why users are very cautious:**
- Arbitrary code execution
- Could do anything
- Hardest to audit
- Requires complete trust

**When it's acceptable:**
- Advanced users only
- Well-documented scripts
- Trusted maintainers
- Auditable, reviewable scripts

**User confidence: LOWEST**
**Requires: Full code review, established trust**

## Opinion Metadata

Every opinion declares its purity level:

```yaml
# opinions/python3/optimized.yaml
version: "1.0"
package: python3
opinion_name: optimized
purity_level: pure-compilation  # ← Declared purity

description: |
  Python built with PGO and LTO for performance

modifications:
  configure_flags:
    add: ["--enable-optimizations", "--with-lto"]
  cflags:
    add: ["-O3"]
```

## User Interface

When searching/installing, show purity:

```bash
$ lebowski search nginx

nginx opinions:
  ✓ performance        [PURE-COMPILATION]   AMD Zen3 optimized build
  ✓ http3              [CONFIGURE-ONLY]     With HTTP/3 support
  ~ upstream-fixes     [UPSTREAM-PATCHES]   Backported bug fixes
  ⚠ experimental       [THIRD-PARTY]        Community features

Legend:
  ✓ = High trust (no source changes)
  ~ = Medium trust (upstream patches)
  ⚠ = Lower trust (review recommended)
```

## Examples by Purity Level

### Pure Compilation Examples

```yaml
# Python optimized for performance
type: pure-compilation
modifications:
  configure_flags: ["--enable-optimizations", "--with-lto"]
  cflags: ["-O3", "-march=native"]

# GCC optimized for builder's CPU
type: pure-compilation
modifications:
  cflags: ["-march=native", "-mtune=native"]

# nginx with telemetry disabled
type: pure-compilation
modifications:
  defines: ["-UNX_HAVE_TELEMETRY"]
  cflags: ["-O2", "-DNDEBUG"]
```

### Configure-Only Examples

```yaml
# nginx minimal (fewer modules)
type: configure-only
modifications:
  configure_flags:
    remove: ["--with-mail_ssl_module", "--with-stream"]

# ffmpeg with all codecs
type: configure-only
modifications:
  configure_flags:
    add: ["--enable-libx264", "--enable-libx265", "--enable-libvpx"]
```

### Patch Examples

```yaml
# nginx with upstream HTTP/3 patches
type: upstream-patches
modifications:
  patches:
    - url: "https://github.com/nginx/nginx/commit/abc.patch"
      sha256: "..." # Verify integrity
```

## Best Practices

### For Opinion Authors

1. **Prefer higher purity levels**
   - Can you achieve it with just compiler flags? Do that.
   - Can you achieve it with configure flags? Do that before patching.

2. **Be explicit about purity**
   - Always declare `purity_level`
   - Explain why patches are necessary if used

3. **Document risk**
   - If using patches, explain what they do
   - Link to upstream discussions
   - Provide rationale

### For Users

1. **Start with pure-compilation**
   - Safest, easiest to trust
   - No source modifications

2. **Understand what you're installing**
   - Check purity level
   - Read opinion description
   - Review patches if present

3. **Verify before trusting**
   ```bash
   lebowski show nginx:http3
   # Shows: purity level, modifications, patches
   ```

## Implementation

### Validation

The build tool enforces purity declarations:

```python
def validate_opinion(opinion):
    if opinion.purity_level == "pure-compilation":
        # Ensure no patches, no source modifications
        assert not opinion.patches
        assert not opinion.scripts
        # Only allow: cflags, cxxflags, ldflags, defines, configure_flags
```

### Signing and Trust

Different purity levels could have different signing requirements:

- **Pure-compilation**: Community-signed okay
- **Patches**: Require established maintainer
- **Custom scripts**: Require multiple signatures or review

## Why This Matters

### Trust Gradient

Users can choose their comfort level:
- Paranoid? Stick to pure-compilation
- Confident? Use upstream patches
- Expert? Review and use anything

### Transparency

Explicitly declaring purity level means:
- No surprises
- Informed decisions
- Appropriate caution

### Community Quality

Encouraging pure-compilation opinions means:
- More opinions are trustworthy
- Lower barrier to contribution
- Easier to audit

## The Ideal

**Most opinions should be pure-compilation or configure-only.**

This gives users:
- Maximum trust
- Minimum risk
- Easy verification
- Confidence in the system

Patches should be used only when necessary, well-documented, and clearly justified.

## Summary

| Purity Level | Source Changes | User Trust | Use When |
|--------------|----------------|------------|----------|
| Pure Compilation | None | Highest | Different optimization/flags needed |
| Configure-Only | None | High | Different features/modules needed |
| Debian Patches | Selective | Medium-High | Want different Debian patch selection |
| Upstream Patches | Yes | Medium | Need backported fixes/features |
| Third-Party Patches | Yes | Lower | Experimental/community features |
| Custom Scripts | Yes | Lowest | Advanced customization |

**Guideline: Stay as high on the purity ladder as possible.**
