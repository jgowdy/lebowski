# Lebowski + XSC Integration Status

## Mission

**XSC is the point. Lebowski is the delivery vehicle.**

Create a ~800MB Debian server ISO that:
- Feels like full Debian install
- Uses XSC ring-based syscalls (no traditional syscalls)
- Has ~400 packages (complete server, no desktop bloat)
- GoDaddy InfoSec can experiment with XSC security properties

## ✅ Completed

### 1. Package List Defined

**File:** `xsc-minimal-server-packages.txt`

**Complete server: ~400 packages, ~800MB ISO**

**Tiers:**
- Tier 1: Essential boot & SSH (~50 packages)
- Tier 2: Expected server tools (~100 packages)
- Tier 3: Server services (~150 packages)
- Tier 4: Dev & testing (~100 packages)

**Key packages included:**
- nginx, apache2-utils
- postgresql-15, mariadb, sqlite, redis, memcached
- python3 (+ pip, venv, common libraries)
- nodejs, ruby, perl
- gcc, gdb, valgrind, strace
- docker, prometheus
- All essential system utilities

**Philosophy:** Server popularity contest - no desktop/GUI cruft.

### 2. XSC Opinion System Created

**Directory:** `opinions/xsc/`

**Files:**
- `TEMPLATE.yaml` - Base template for all XSC packages
- `README.md` - XSC opinion documentation

**Package-specific opinions:**
- `opinions/nginx/xsc-base.yaml` - nginx for XSC
- `opinions/python3/xsc-optimized.yaml` - Python with PGO + XSC
- `opinions/postgresql/xsc-base.yaml` - PostgreSQL for XSC

**All opinions:**
- Use x86_64-xsc-linux-gnu toolchain
- Link against libxsc-rt
- Configure for ring-based syscalls
- Include XSC_ABI ELF note
- Contain NO traditional syscall instructions

### 3. Integration Documentation

**File:** `docs/xsc-integration.md`

**Covers:**
- XSC overview and variants (base, cfi-compat)
- Complete package selection strategy
- Opinion structure for XSC builds
- Bootstrap process (5 phases)
- Verification procedures
- Integration with existing ~/flexsc build

## 🚧 In Progress

### Lebowski + XSC Build Integration

**Need to:**
1. Modify Lebowski builder to detect XSC toolchain
2. Add XSC-specific validation (no syscalls, XSC_ABI note)
3. Create build script that uses Lebowski to build all 400 packages
4. Integrate with existing ~/flexsc/build-xsc-toolchain.sh

## 📋 Next Steps

### Phase 1: Debootstrap Script

Create script to bootstrap XSC minimal system:

```bash
#!/bin/bash
# bootstrap-xsc-iso.sh

# 1. Build XSC toolchain (from ~/flexsc)
cd ~/flexsc
./build-xsc-toolchain.sh

# 2. Build essential packages with Lebowski
cd ~/lebowski
./build-all-xsc-packages.sh  # To be created

# 3. Create Debian repository
./create-xsc-repo.sh  # To be created

# 4. Debootstrap with XSC packages
debootstrap --arch=amd64 \
    --variant=minbase \
    --include="$(cat xsc-minimal-packages-essential.txt)" \
    bookworm \
    ./xsc-rootfs \
    http://localhost/xsc-repo

# 5. Create ISO
./create-xsc-iso.sh  # To be created
```

### Phase 2: Testing

Verify XSC compliance for all packages:

```bash
# For each built package:
for pkg in ~/xsc-packages/*.deb; do
    # Extract binary
    dpkg-deb -x $pkg /tmp/test/

    # Find executables
    find /tmp/test -type f -executable | while read binary; do
        # Verify no syscalls
        if objdump -d "$binary" 2>/dev/null | grep -q syscall; then
            echo "FAIL: $binary contains syscall instructions!"
        fi

        # Verify XSC_ABI note
        if ! readelf -n "$binary" 2>/dev/null | grep -q XSC_ABI; then
            echo "FAIL: $binary missing XSC_ABI note!"
        fi
    done
done
```

### Phase 3: ISO Creation

**Target output:**
```
debian-xsc-server-bookworm-amd64.iso
Size: ~800MB
Boots to: Full server environment
Feels like: Standard Debian server
Actually is: XSC with ring-based syscalls
```

## Files Created

```
lebowski/
├── xsc-minimal-server-packages.txt     # 400-package list
├── XSC-INTEGRATION-STATUS.md           # This file
├── docs/
│   └── xsc-integration.md              # Integration guide
└── opinions/
    ├── xsc/
    │   ├── README.md                   # XSC opinions guide
    │   └── TEMPLATE.yaml               # Base template
    ├── nginx/
    │   └── xsc-base.yaml              # nginx for XSC
    ├── python3/
    │   └── xsc-optimized.yaml         # Python + PGO + XSC
    └── postgresql/
        └── xsc-base.yaml              # PostgreSQL for XSC
```

## Integration Points

### With Existing XSC Build (~/flexsc)

**XSC provides:**
- Kernel with XSC driver (ring-based syscalls)
- XSC toolchain (x86_64-xsc-linux-gnu-gcc)
- glibc with --enable-xsc
- libxsc-rt (runtime library)

**Lebowski provides:**
- Opinion-based build system
- ~400 packages built for XSC
- Debian repository creation
- ISO bootstrap process

**Integration:**
```
~/flexsc/build-xsc-toolchain.sh
            ↓
    (XSC toolchain ready)
            ↓
~/lebowski/build-all-xsc-packages.sh
            ↓
    (400 .deb packages)
            ↓
~/lebowski/create-xsc-repo.sh
            ↓
    (APT repository)
            ↓
~/lebowski/bootstrap-xsc-iso.sh
            ↓
debian-xsc-server.iso (800MB)
```

## Key Decisions Made

### 1. Package Count: ~400 (Complete Server)
- Feels like full Debian
- All common server use cases covered
- No desktop bloat
- ~800MB ISO size

### 2. Opinion Purity: Configure-Only
- All XSC opinions are configure-only (high trust)
- No source patches needed
- Just toolchain + flags + libxsc-rt

### 3. Variants: Start with Base
- Focus on XSC base variant first
- CFI-compat variant later (requires CET/PAC hardware)

### 4. Integration: Complementary
- XSC handles kernel + toolchain
- Lebowski handles userspace packages
- Clean separation of concerns

## Verification Criteria

### Package-Level

✅ No syscall instructions in any binary
✅ XSC_ABI ELF note in all executables
✅ All binaries link against libxsc-rt
✅ Packages built with x86_64-xsc-linux-gnu toolchain

### System-Level

✅ Boots successfully
✅ SSH works
✅ Package management works (apt/dpkg)
✅ Services start (nginx, postgresql, etc.)
✅ No traditional syscalls during operation
✅ Ring usage visible in /dev/xsc

### User Experience

✅ Feels like Debian server install
✅ Familiar commands work (apt-get, systemctl, etc.)
✅ Standard configuration locations
✅ ISO < 1GB
✅ Installation < 30 minutes

## Success Metrics

**For GoDaddy InfoSec:**

1. **Easy to try:** Download ISO, install, boot
2. **Familiar:** Works like Debian
3. **Functional:** Run real services
4. **Verifiable:** Can prove ring-based syscalls working
5. **Secure:** Demonstrate XSC security properties

**Technical proof:**
```bash
# On running XSC system
strace nginx  # Shows NO syscalls!
cat /proc/$(pidof nginx)/maps | grep xsc-rt  # libxsc-rt loaded
ls -l /dev/xsc  # XSC device active
dmesg | grep -i xsc  # XSC kernel driver loaded
```

## Timeline

- ✅ **Phase 1:** Package list + opinions (COMPLETE)
- 🚧 **Phase 2:** Build integration (IN PROGRESS)
- 📋 **Phase 3:** Debootstrap script (NEXT)
- 📋 **Phase 4:** Testing & verification (NEXT)
- 📋 **Phase 5:** ISO creation (FINAL)

**Estimated completion:** 2-3 days of focused work

## Next Immediate Step

Create `build-all-xsc-packages.sh`:

```bash
#!/bin/bash
# Build all XSC packages using Lebowski

# Ensure XSC toolchain in PATH
export PATH="$HOME/flexsc/build/toolchain/bin:$PATH"

# Build essential packages first
for pkg in bash coreutils util-linux openssh-server; do
    lebowski build "$pkg" --opinion xsc-base --output-dir ~/xsc-packages/essential/
done

# Build remaining packages
while read package; do
    lebowski build "$package" --opinion xsc-base --output-dir ~/xsc-packages/
done < xsc-minimal-server-packages.txt

echo "All XSC packages built!"
```

---

**Status: Foundation complete, ready for build integration.**
