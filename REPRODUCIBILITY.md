# Lebowski Reproducibility & Transparency

## The Problem

When building custom Debian packages, you need to **prove** that:
1. The package came from legitimate Debian sources
2. The modifications are exactly what you claim
3. The build environment was controlled and reproducible
4. Anyone can verify the package is legitimate by rebuilding it

This is critical for:
- **Security**: Detect tampering or malicious modifications
- **Trust**: Verify packages before deployment
- **Distributed building**: Community can build and verify packages
- **Compliance**: Prove build provenance for audits

## The Solution: Build Manifests

Every package built with Lebowski produces a **`.lebowski-manifest.json`** file that records:

### 1. Source Provenance
```json
"source": {
  "package": "bash",
  "version": "5.1-6ubuntu1.1",
  "dsc_file": "/tmp/lebowski-build/bash_5.1-6ubuntu1.1.dsc",
  "dsc_sha256": "a1b2c3...",
  "fetch_method": "apt-get source",
  "fetch_command": "apt-get source bash"
}
```
**Proves**: Where the source came from (official Debian repositories)

### 2. Opinion Metadata
```json
"opinion": {
  "name": "xsc-base",
  "package": "bash",
  "purity_level": "configure-only",
  "description": "bash built for XSC architecture",
  "file": "/build/xsc/lebowski/opinions/bash/xsc-base.yaml",
  "file_sha256": "d4e5f6...",
  "modifications": {
    "env": {
      "CC": "x86_64-xsc-linux-gnu-gcc"
    },
    "configure_flags": {
      "add": ["--host=x86_64-xsc-linux-gnu"]
    },
    "ldflags": ["-lxsc-rt"]
  }
}
```
**Proves**: Exact modifications applied (flags, defines, patches)

### 3. Toolchain Information
```json
"toolchain": {
  "compiler": "x86_64-xsc-linux-gnu-gcc",
  "compiler_path": "/storage/icloud-backup/build/xsc-toolchain-x86_64-base/bin/x86_64-xsc-linux-gnu-gcc",
  "compiler_version": "x86_64-xsc-linux-gnu-gcc (GCC) 13.2.0",
  "compiler_sha256": "g7h8i9..."
}
```
**Proves**: Exact toolchain used (version + binary hash)

### 4. Build Environment
```json
"environment": {
  "SOURCE_DATE_EPOCH": "1704067200",
  "TZ": "UTC",
  "LANG": "C.UTF-8",
  "LC_ALL": "C.UTF-8",
  "CC": "x86_64-xsc-linux-gnu-gcc",
  "DEB_CONFIGURE_EXTRA_FLAGS": "--host=x86_64-xsc-linux-gnu --build=x86_64-linux-gnu",
  "DEB_LDFLAGS_APPEND": "-lxsc-rt",
  "PATH": "/storage/icloud-backup/build/xsc-toolchain-x86_64-base/bin:..."
}
```
**Proves**: Exact environment variables (reproducibility critical!)

### 5. Build Host
```json
"build_host": {
  "hostname": "bx",
  "system": "Linux",
  "release": "6.11.0-9-generic",
  "machine": "x86_64"
}
```
**Proves**: Where the package was built

### 6. Output Verification
```json
"output": {
  "package_file": "bash_5.1-6ubuntu1.1_amd64.deb",
  "package_sha256": "j1k2l3...",
  "buildinfo_file": "bash_5.1-6ubuntu1.1_amd64.buildinfo"
}
```
**Proves**: Output package hash for verification

## Verification Workflow

### Build Package
```bash
cd build-tool
python3 -m lebowski.cli build bash \
  --opinion-file ../opinions/bash/xsc-base.yaml \
  --output-dir ~/packages
```

**Outputs:**
- `~/packages/bash_5.1-6ubuntu1.1_amd64.deb` - The package
- `~/packages/bash_5.1-6ubuntu1.1_amd64.buildinfo` - Debian buildinfo
- `~/packages/bash_5.1-6ubuntu1.1_amd64.lebowski-manifest.json` - **Lebowski manifest**

### Verify Package
Anyone can verify the package by:

1. **Check source hash**: Verify .dsc file matches Debian official sources
2. **Check opinion hash**: Verify opinion YAML hasn't been tampered with
3. **Check compiler hash**: Verify compiler binary is legitimate
4. **Rebuild**: Use same environment to reproduce bit-for-bit identical package
5. **Compare hashes**: Rebuilt package should have identical SHA256

```bash
# Verify opinion
sha256sum opinions/bash/xsc-base.yaml
# Should match manifest["opinion"]["file_sha256"]

# Verify compiler
sha256sum /path/to/toolchain/bin/x86_64-xsc-linux-gnu-gcc
# Should match manifest["toolchain"]["compiler_sha256"]

# Rebuild (with same environment)
python3 -m lebowski.cli build bash \
  --opinion-file ../opinions/bash/xsc-base.yaml \
  --output-dir ~/verify

# Compare
sha256sum ~/packages/bash_*.deb ~/verify/bash_*.deb
# Hashes MUST match for reproducibility
```

## Security Properties

### 1. Source Integrity
- `.dsc` hash proves source came from official Debian
- Anyone can fetch the same source and verify hash

### 2. Opinion Transparency
- Opinion YAML hash ensures modifications are documented
- Purity level indicates trust level (configure-only > patches)

### 3. Toolchain Verification
- Compiler binary hash prevents toolchain tampering
- Compiler version ensures consistent compilation

### 4. Reproducible Builds
- Fixed `SOURCE_DATE_EPOCH` = 1704067200 (2024-01-01 00:00:00 UTC)
- Fixed locale (`C.UTF-8`), timezone (`UTC`)
- Documented environment enables bit-for-bit reproduction

### 5. Chain of Custody
Complete audit trail from:
1. Debian source → 2. Opinion modifications → 3. Toolchain → 4. Build → 5. Output package

## Trust Model

### Highest Trust: Pure Compilation
```yaml
purity_level: pure-compilation
modifications:
  cflags: ["-O2", "-march=native"]
```
- Only compiler flags
- No source changes
- Easiest to audit

### High Trust: Configure Only
```yaml
purity_level: configure-only
modifications:
  configure_flags:
    add: ["--enable-xsc"]
  ldflags: ["-lxsc-rt"]
```
- Build flags only
- No source modifications
- Transparent modifications

### Lower Trust: Patches
```yaml
purity_level: custom
modifications:
  patches: ["0001-add-feature.patch"]
  scripts:
    pre_build: "./custom-setup.sh"
```
- Source modifications
- Requires careful review
- Manifest includes patch hashes

## Distributed Verification

### Community Builds
1. Developer publishes:
   - `.deb` package
   - `.lebowski-manifest.json`
   - Opinion YAML

2. Community verifies:
   - Rebuilds package with same opinion + toolchain
   - Compares output hash
   - If hashes match → package is legitimate

### Build Farms
Multiple independent builders can:
- Build same package with same opinion
- All produce identical packages (same SHA256)
- Proves no single builder can inject malware

### Example
```bash
# Builder 1 (bx.ee)
lebowski build bash --opinion xsc-base
# Output: bash_5.1_amd64.deb (sha256: abc123...)

# Builder 2 (community server)
lebowski build bash --opinion xsc-base
# Output: bash_5.1_amd64.deb (sha256: abc123...)

# Builder 3 (CI/CD)
lebowski build bash --opinion xsc-base
# Output: bash_5.1_amd64.deb (sha256: abc123...)

# All three produce IDENTICAL packages → provably legitimate
```

## Implementation Status

### ✅ Implemented
- Source provenance tracking (.dsc hash)
- Opinion metadata and hashing
- Toolchain version and binary hashing
- Reproducible environment variables
- Build host information
- Output package hashing
- JSON manifest generation

### 🚧 TODO
- Container-based builds (ultimate reproducibility)
- Signature verification (GPG)
- Distributed build verification service
- Web UI for manifest inspection
- Automated rebuild verification

## Why This Matters

**Traditional approach:**
- Download .deb from website
- Hope it's legitimate
- No way to verify

**Lebowski approach:**
- Download .deb + manifest
- Rebuild yourself
- Bit-for-bit identical = provably legitimate
- Complete transparency from source → output

**Result:** *"Don't trust, verify."*

---

**Status:** Reproducibility system implemented in `builder.py:40-462`
