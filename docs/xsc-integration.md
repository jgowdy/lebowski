# Lebowski + XSC Integration

## The Mission

**XSC is the point. Lebowski is the delivery vehicle.**

- **XSC**: Ring-based syscalls with hardware CFI enforcement
- **Lebowski**: Build system making XSC deployable
- **Goal**: GoDaddy InfoSec can experiment with XSC security properties

## The Vision

**What users experience:**
```bash
# Download debian-xsc-server.iso (800MB)
# Feels like Debian server install
# Boot, ssh, nginx, databases, python all work
# Don't realize it's XSC with ring-based syscalls
# No traditional syscalls anywhere
```

## Package Strategy: Complete Server

**~400 packages, ~800MB ISO**

### Tier 1: Essential Boot & SSH (~50 packages, ~100MB)

**Kernel & Core:**
- linux-image-xsc (6.1+ with XSC driver)
- linux-firmware (minimal subset for common hardware)
- systemd-sysv or sysvinit
- udev

**Userspace Foundation:**
- glibc (--enable-xsc, x86_64-xsc-linux-gnu)
- libxsc-rt (XSC runtime library)
- bash, dash
- coreutils, util-linux, findutils
- grep, sed, gawk

**Networking & SSH:**
- openssh-server, openssh-client
- iproute2, ifupdown, dhcpcd5
- netbase, iputils-ping
- ca-certificates

**Package Management:**
- apt, dpkg, apt-utils
- gnupg, debian-archive-keyring

**Basic Utilities:**
- sudo, passwd, login
- vim-tiny or nano
- less, more
- tar, gzip, bzip2, xz-utils

### Tier 2: Expected Server Tools (~150 packages total, ~300MB)

**File Transfer & Sync:**
- curl, wget
- rsync, scp
- netcat-openbsd

**Version Control:**
- git

**Text Processing:**
- diffutils, patch
- file, mime-support

**Terminal Tools:**
- tmux or screen
- htop or top
- ncurses-base, ncurses-term

**System Tools:**
- cron, anacron, at
- logrotate
- sysstat (sar, iostat, etc.)
- lsof, strace

**Security:**
- auditd (monitor XSC security events)
- fail2ban
- iptables, nftables

**SSL/Crypto:**
- openssl, libssl3
- certbot (Let's Encrypt)

### Tier 3: Popular Server Services (~300 packages total, ~600MB)

**Web Servers:**
- nginx (most popular on Debian servers)
- apache2-utils (for benchmarking)

**Databases:**
- postgresql-15
- mariadb-server (MySQL-compatible)
- sqlite3

**Caching & Queuing:**
- redis-server
- memcached

**Runtimes & Interpreters:**
- python3 (3.11)
  - python3-pip
  - python3-venv
  - python3-setuptools
- nodejs (LTS)
  - npm
- ruby (for admin scripts)
- perl (ubiquitous in server management)

**Application Servers:**
- uwsgi, uwsgi-plugin-python3
- gunicorn (Python WSGI)

### Tier 4: Developer & Testing Tools (~400 packages total, ~800MB)

**Compilers & Build Tools:**
- gcc, g++ (x86_64-xsc-linux-gnu)
- binutils (XSC-aware)
- make, cmake, autoconf, automake, libtool
- pkg-config
- build-essential

**Debugging & Analysis:**
- gdb (XSC-aware)
- valgrind
- strace, ltrace (verify no syscalls!)
- tcpdump, wireshark-common
- perf (kernel performance analysis)

**Libraries (development):**
- libssl-dev
- zlib1g-dev
- libpq-dev (PostgreSQL)
- python3-dev
- libsqlite3-dev

**Container Tools:**
- docker.io or podman
- containerd

**Monitoring:**
- prometheus-node-exporter
- netdata (optional, adds ~50MB)

**Text Editors (proper ones):**
- vim (full)
- emacs-nox (no X11)

**Additional Utilities:**
- jq (JSON processing)
- unzip, zip
- tree
- bc (calculator)
- dnsutils (dig, nslookup)
- whois
- telnet

## XSC-Specific Modifications

### Every Package Built With:

```bash
# Toolchain
CC=x86_64-xsc-linux-gnu-gcc
CXX=x86_64-xsc-linux-gnu-g++
LD=x86_64-xsc-linux-gnu-ld

# Flags
CFLAGS="-O2 -g"
LDFLAGS="-lxsc-rt"  # Link XSC runtime

# Configure
--host=x86_64-xsc-linux-gnu
--build=x86_64-linux-gnu
```

### Required in Every Binary:

```c
// ELF note for XSC ABI validation
__attribute__((section(".note.XSC_ABI")))
static const struct {
    uint32_t namesz;
    uint32_t descsz;
    uint32_t type;
    char name[4];
    uint32_t abi_version;
} xsc_note = {
    .namesz = 4,
    .descsz = 4,
    .type = 1,
    .name = "XSC",
    .abi_version = 1
};
```

## Lebowski Opinion Structure for XSC

### Base Opinion Template

```yaml
# opinions/<package>/xsc-base.yaml
version: "1.0"
package: <package>
opinion_name: xsc-base
purity_level: configure-only

description: |
  <package> built for XSC architecture (x86_64-xsc-linux-gnu)

  Uses ring-based syscalls instead of traditional syscall instructions.
  Hardware CFI enforcement via Intel CET or ARM PAC.

debian_versions:
  - bookworm

xsc_variant: base  # or cfi-compat

modifications:
  configure_flags:
    add:
      - "--host=x86_64-xsc-linux-gnu"
      - "--build=x86_64-linux-gnu"

  env:
    CC: "x86_64-xsc-linux-gnu-gcc"
    CXX: "x86_64-xsc-linux-gnu-g++"
    LD: "x86_64-xsc-linux-gnu-ld"
    CFLAGS: "-O2 -g"
    LDFLAGS: "-lxsc-rt"

  build_deps:
    add:
      - libxsc-rt-dev

build_notes: |
  Requires XSC toolchain installed:
  - x86_64-xsc-linux-gnu-gcc
  - x86_64-xsc-linux-gnu-binutils
  - libxsc-rt
```

### Key Packages with Opinions

**nginx:**
```yaml
# opinions/nginx/xsc-base.yaml
version: "1.0"
package: nginx
opinion_name: xsc-base
purity_level: configure-only

modifications:
  configure_flags:
    add:
      - "--host=x86_64-xsc-linux-gnu"
      - "--with-cc-opt=-O2 -g"
      - "--with-ld-opt=-lxsc-rt"
```

**Python:**
```yaml
# opinions/python3/xsc-optimized.yaml
version: "1.0"
package: python3-defaults
opinion_name: xsc-optimized
purity_level: configure-only

modifications:
  configure_flags:
    add:
      - "--host=x86_64-xsc-linux-gnu"
      - "--enable-optimizations"
      - "--with-lto"

  env:
    CC: "x86_64-xsc-linux-gnu-gcc"
    LDFLAGS: "-lxsc-rt"
```

**PostgreSQL:**
```yaml
# opinions/postgresql/xsc-base.yaml
version: "1.0"
package: postgresql-15
opinion_name: xsc-base
purity_level: configure-only

modifications:
  configure_flags:
    add:
      - "--host=x86_64-xsc-linux-gnu"
      - "--with-openssl"

  env:
    CC: "x86_64-xsc-linux-gnu-gcc"
```

## Bootstrap Process

### Phase 1: Build XSC Toolchain

```bash
# From existing XSC build system
cd ~/flexsc
./build-xsc-toolchain.sh

# Results in:
# - x86_64-xsc-linux-gnu-gcc
# - x86_64-xsc-linux-gnu-binutils
# - glibc with --enable-xsc
# - libxsc-rt
```

### Phase 2: Build Minimal Packages with Lebowski

```bash
cd ~/lebowski

# Build essential packages for XSC
for pkg in bash coreutils util-linux openssh-server; do
    lebowski build $pkg --opinion xsc-base
done

# Build services
for pkg in nginx postgresql-15 redis python3; do
    lebowski build $pkg --opinion xsc-base
done

# Build dev tools
for pkg in gcc make gdb; do
    lebowski build $pkg --opinion xsc-base
done
```

### Phase 3: Create Debian Repository

```bash
# Collect all built packages
mkdir -p xsc-repo/pool/main

# Copy .deb files
cp *.deb xsc-repo/pool/main/

# Generate Packages file
cd xsc-repo
dpkg-scanpackages pool/main /dev/null | gzip > dists/bookworm/main/binary-amd64/Packages.gz

# Create Release file
apt-ftparchive release dists/bookworm > dists/bookworm/Release

# Sign repository
gpg --detach-sign --armor -o dists/bookworm/Release.gpg dists/bookworm/Release
```

### Phase 4: Bootstrap XSC System

```bash
# Use debootstrap with XSC packages
debootstrap \
    --arch=amd64 \
    --variant=minbase \
    --include="linux-image-xsc,systemd,openssh-server,nginx,postgresql-15,python3" \
    bookworm \
    ./xsc-rootfs \
    http://localhost/xsc-repo

# Install XSC kernel
cp linux-image-xsc*.deb xsc-rootfs/tmp/
chroot xsc-rootfs dpkg -i /tmp/linux-image-xsc*.deb

# Configure for XSC
cat > xsc-rootfs/etc/xsc.conf <<EOF
[rings]
sq_entries=128
cq_entries=256

[security]
strict_abi_check=true
audit_syscall_attempts=true
EOF
```

### Phase 5: Create ISO

```bash
# Install bootloader
grub-install --target=i386-pc --boot-directory=xsc-rootfs/boot /dev/loop0

# Generate initramfs with XSC module
chroot xsc-rootfs update-initramfs -c -k $(uname -r)

# Create ISO
genisoimage \
    -r -J -b isolinux/isolinux.bin \
    -c isolinux/boot.cat \
    -no-emul-boot -boot-load-size 4 \
    -boot-info-table \
    -o debian-xsc-server.iso \
    xsc-rootfs/

# Result: ~800MB ISO
```

## Package List by Category

### Core System (50 packages)
```
linux-image-xsc
linux-firmware
systemd-sysv
udev
glibc
libxsc-rt
bash
coreutils
util-linux
openssh-server
apt
dpkg
sudo
vim-tiny
```

### Networking & Tools (50 packages)
```
nginx
curl
wget
git
rsync
tmux
htop
logrotate
auditd
iptables
openssl
certbot
```

### Databases & Caching (30 packages)
```
postgresql-15
mariadb-server
sqlite3
redis-server
memcached
```

### Runtimes (50 packages)
```
python3
python3-pip
python3-venv
nodejs
npm
ruby
perl
uwsgi
gunicorn
```

### Development (100 packages)
```
gcc
g++
binutils
make
cmake
autoconf
automake
build-essential
gdb
valgrind
strace
tcpdump
```

### Libraries & Dependencies (120 packages)
```
libssl-dev
zlib1g-dev
libpq-dev
python3-dev
libsqlite3-dev
libncurses-dev
...
```

**Total: ~400 packages, ~800MB**

## Integration with Existing XSC Build

### Directory Structure

```
~/lebowski/                    # Lebowski project
~/flexsc/                      # XSC OS project
~/xsc-lebowski-integration/    # Integration point
    ├── package-list.txt       # 400 packages for minimal server
    ├── opinions/              # XSC opinions for each package
    │   ├── nginx/xsc-base.yaml
    │   ├── python3/xsc-optimized.yaml
    │   └── ...
    ├── build-all-xsc.sh       # Build all packages
    ├── create-xsc-repo.sh     # Create Debian repo
    └── bootstrap-xsc-iso.sh   # Create ISO
```

### Build Script Integration

```bash
#!/bin/bash
# build-all-xsc.sh

# Use existing XSC toolchain from ~/flexsc
export PATH="~/flexsc/build/toolchain/bin:$PATH"
export CC="x86_64-xsc-linux-gnu-gcc"

# Use Lebowski to build packages
cd ~/lebowski/build-tool

# Build each package from list
while read package; do
    echo "Building $package for XSC..."
    ./lebowski build "$package" --opinion xsc-base --output-dir ~/xsc-packages/
done < ~/xsc-lebowski-integration/package-list.txt

echo "All XSC packages built to ~/xsc-packages/"
```

## Verification

### After Boot, Verify XSC is Working:

```bash
# Check kernel
uname -a
# Should show XSC kernel

# Check for XSC device
ls -l /dev/xsc

# Verify NO syscall instructions
objdump -d /bin/bash | grep syscall
# Should be empty!

# Check ELF notes
readelf -n /bin/bash | grep XSC_ABI
# Should show XSC_ABI version: 1

# Monitor ring activity
trace-cmd record -e xsc:*

# Test nginx (should use rings)
systemctl start nginx
curl http://localhost
```

## Next Steps

1. Generate complete 400-package list from Debian popcon (server-focused)
2. Create Lebowski opinions for key packages
3. Integrate with existing XSC toolchain build
4. Test bootstrap process
5. Create ISO
6. Verify with GoDaddy InfoSec

**Status: Ready to build package list and opinions.**
