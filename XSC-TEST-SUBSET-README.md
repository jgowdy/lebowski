# XSC Test Subset - Proving Integration Works

## Goal

Build **15 critical packages** with Lebowski + XSC toolchain to prove the integration works before scaling to 400 packages.

## Test Package List

**File:** `xsc-test-subset.txt`

### Essential (5):
- bash, coreutils, util-linux, openssh-server, systemd

### Package Management (3):
- apt, dpkg, gnupg

### Key Services (4):
- nginx, postgresql-15, python3, redis-server

### Development Tools (3):
- gcc, gdb, strace

**Total: 15 packages**

## Build Process

### Step 1: Ensure XSC Toolchain is Built

```bash
cd ~/flexsc
./build-xsc-toolchain.sh

# Results in:
# - x86_64-xsc-linux-gnu-gcc
# - glibc with --enable-xsc
# - libxsc-rt
```

### Step 2: Build Test Subset

```bash
cd ~/lebowski
./build-xsc-test-subset.sh

# Builds all 15 packages
# Output: ~/xsc-test-packages/
```

**What it does:**
- Checks XSC toolchain exists
- Adds toolchain to PATH
- Creates XSC opinions from template if missing
- Builds each package with Lebowski
- Categorizes into: essential, services, devtools
- Reports success/failure count

### Step 3: Verify XSC Compliance

```bash
./verify-xsc-packages.sh ~/xsc-test-packages

# Checks each package for:
# ✓ NO syscall instructions (CRITICAL)
# ✓ XSC_ABI ELF note present
# ✓ Links against libxsc-rt
```

**Verification checks:**

For each binary:
1. `objdump -d` → Should show NO syscall/sysenter/int 0x80 instructions
2. `readelf -n` → Should show XSC_ABI note
3. `ldd` → Should show libxsc-rt.so.1

## Success Criteria

### Build Phase
- ✅ All 15 packages build successfully
- ✅ No build errors
- ✅ All .deb files generated

### Verification Phase
- ✅ **ZERO binaries with traditional syscall instructions** (CRITICAL)
- ✅ All binaries have XSC_ABI ELF notes
- ✅ All binaries link against libxsc-rt

### Functional Testing (Next Step)
- ✅ Packages install via dpkg
- ✅ bash works
- ✅ nginx starts and serves pages
- ✅ postgresql accepts connections and runs queries
- ✅ python3 executes scripts
- ✅ strace shows NO syscalls during operation

## If Test Succeeds

**Proceed to full build:**
```bash
# Build all 400 packages
./build-all-xsc-packages.sh  # (to be created)

# Create full Debian repository
./create-xsc-repo.sh

# Bootstrap minimal ISO
./bootstrap-xsc-iso.sh

# Result: debian-xsc-server.iso (~800MB)
```

## If Test Fails

**Common issues and fixes:**

### 1. Syscall instructions found
**Problem:** Binaries contain syscall/sysenter/int 0x80
**Fix:**
- Verify XSC toolchain is in PATH
- Check opinion uses x86_64-xsc-linux-gnu-gcc
- Rebuild XSC toolchain if corrupted

### 2. Missing XSC_ABI notes
**Problem:** No XSC_ABI section in ELF
**Fix:**
- Add XSC_ABI note to linker scripts
- Check glibc built with --enable-xsc
- Verify libxsc-rt provides note injection

### 3. Not linked to libxsc-rt
**Problem:** Binary doesn't link libxsc-rt
**Fix:**
- Add `-lxsc-rt` to LDFLAGS in opinion
- Check libxsc-rt is installed
- Verify ld finds libxsc-rt.so

### 4. Package fails to build
**Problem:** dpkg-buildpackage fails
**Fix:**
- Check build logs for specific errors
- Verify all build dependencies installed
- Check opinion YAML syntax
- Test building Debian package first (without XSC)

## Directory Structure

```
~/lebowski/
├── xsc-test-subset.txt              # 15-package list
├── build-xsc-test-subset.sh         # Build script
├── verify-xsc-packages.sh           # Verification script
├── XSC-TEST-SUBSET-README.md        # This file
└── opinions/
    ├── xsc/TEMPLATE.yaml            # Base template
    ├── nginx/xsc-base.yaml
    ├── python3/xsc-optimized.yaml
    └── postgresql/xsc-base.yaml

~/xsc-test-packages/                 # Build output
├── essential/
│   ├── bash_*.deb
│   ├── coreutils_*.deb
│   ├── apt_*.deb
│   └── ...
├── services/
│   ├── nginx_*.deb
│   ├── postgresql-15_*.deb
│   ├── python3_*.deb
│   └── redis-server_*.deb
└── devtools/
    ├── gcc_*.deb
    ├── gdb_*.deb
    └── strace_*.deb

~/flexsc/                            # XSC OS project
└── build/toolchain/                 # XSC toolchain
    └── bin/
        ├── x86_64-xsc-linux-gnu-gcc
        ├── x86_64-xsc-linux-gnu-ld
        └── ...
```

## Timeline

**Phase 1: Build** (~2-4 hours depending on machine)
- Run build-xsc-test-subset.sh
- Fix any build failures
- Verify all 15 packages built

**Phase 2: Verification** (~10 minutes)
- Run verify-xsc-packages.sh
- Fix any compliance issues
- Ensure zero violations

**Phase 3: Functional Testing** (~1 hour)
- Create minimal test system
- Install packages
- Test basic functionality
- Verify no syscalls during operation

**Phase 4: Scale Up** (if successful)
- Build remaining 385 packages
- Create full ISO
- Comprehensive testing

## Key Files

| File | Purpose | Status |
|------|---------|--------|
| `xsc-test-subset.txt` | 15 critical packages | ✅ Created |
| `build-xsc-test-subset.sh` | Build all 15 packages | ✅ Created |
| `verify-xsc-packages.sh` | Verify XSC compliance | ✅ Created |
| `opinions/xsc/TEMPLATE.yaml` | Base opinion template | ✅ Created |
| `opinions/nginx/xsc-base.yaml` | nginx opinion | ✅ Created |
| `opinions/python3/xsc-optimized.yaml` | Python opinion | ✅ Created |
| `opinions/postgresql/xsc-base.yaml` | PostgreSQL opinion | ✅ Created |

## Next Steps After Success

1. **Document lessons learned** from test subset
2. **Create remaining opinions** for 385 packages
3. **Build all 400 packages** with automation
4. **Create Debian repository** structure
5. **Bootstrap test system** with debootstrap
6. **Create ISO** with genisoimage
7. **Test boot** in VM
8. **Verify XSC operation** (no syscalls, rings working)
9. **Package for GoDaddy InfoSec**

## Reference Commands

```bash
# Check XSC toolchain
which x86_64-xsc-linux-gnu-gcc
x86_64-xsc-linux-gnu-gcc --version

# Build test subset
./build-xsc-test-subset.sh

# Verify packages
./verify-xsc-packages.sh

# Check specific binary
objdump -d ~/xsc-test-packages/essential/bash_*.deb | grep syscall
readelf -n ~/xsc-test-packages/essential/bash_*.deb | grep XSC

# Manual build of single package
cd build-tool
python3 -m lebowski build bash \
    --opinion-file ../opinions/bash/xsc-base.yaml \
    --output-dir ~/xsc-test-packages/test/
```

## Expected Results

**When everything works:**

```
╔════════════════════════════════════════════════════════════╗
║  Build Summary                                             ║
╚════════════════════════════════════════════════════════════╝

✅ Successful: 15
❌ Failed:     0

🎉 All test packages built successfully!

Next steps:
  1. Run verification: ./verify-xsc-packages.sh
  2. Test packages in minimal system
  3. If all pass, scale to full 400-package build
```

```
╔════════════════════════════════════════════════════════════╗
║  Verification Summary                                      ║
╚════════════════════════════════════════════════════════════╝

Packages checked:        15
Binaries checked:        87

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Violations:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Syscall instructions:  0 (PASS)
✅ Missing XSC_ABI notes: 0 (PASS)
✅ Missing libxsc-rt:     0 (PASS)

🎉 ALL PACKAGES ARE XSC COMPLIANT!

Next steps:
  1. Create test repository
  2. Bootstrap minimal test system
  3. Boot and functional test
  4. If all pass -> scale to 400 packages
```

---

**Status: Ready to test. Run `./build-xsc-test-subset.sh` when XSC toolchain is ready.**
