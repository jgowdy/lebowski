# XSC Phase 3: GCC Cross-Compiler Build Plan

**Goal**: Build x86_64-xsc-linux-gnu-gcc that can compile programs linking to libxsc-rt and patched glibc.

**Timeline**: Weeks 3-4 (this phase is complex due to bootstrap requirements)

## Strategy

We need a 3-stage bootstrap because of circular dependencies:

1. **Stage 1**: Build basic x86_64-xsc-linux-gnu-gcc (C only, no libc)
2. **Stage 2**: Build xsc-glibc headers using stage 1 compiler
3. **Stage 3**: Rebuild full GCC (C/C++) with xsc-glibc support

## Current Status

✅ Prerequisites complete:
- libxsc-rt.so built and tested
- glibc 2.36 downloaded and patched
- Implementation guide written

⏩ Starting now:
- GCC 13.2.0 source download
- Cross-compiler build

## Build Steps

### Step 1: Download GCC Source

```bash
cd /build/xsc
wget https://ftp.gnu.org/gnu/gcc/gcc-13.2.0/gcc-13.2.0.tar.xz
tar xf gcc-13.2.0.tar.xz
cd gcc-13.2.0
./contrib/download_prerequisites  # Get GMP, MPFR, MPC, ISL
```

**Expected size**: ~150MB compressed, ~1GB extracted

### Step 2: Configure Stage 1 Compiler

```bash
mkdir -p /build/xsc/gcc-stage1
cd /build/xsc/gcc-stage1

../gcc-13.2.0/configure \
  --prefix=/opt/xsc-toolchain \
  --target=x86_64-xsc-linux-gnu \
  --enable-languages=c \
  --disable-shared \
  --disable-threads \
  --disable-libssp \
  --disable-libgomp \
  --disable-libmudflap \
  --without-headers \
  --with-newlib
```

**Why these flags**:
- `--target=x86_64-xsc-linux-gnu`: Custom target name
- `--enable-languages=c`: Only C for stage 1
- `--without-headers`: No libc headers yet
- `--with-newlib`: Minimal runtime

### Step 3: Build Stage 1

```bash
make -j80 all-gcc
make install-gcc
```

**Expected time**: 10-15 minutes on R820 (80 cores)

**Output**: `/opt/xsc-toolchain/bin/x86_64-xsc-linux-gnu-gcc`

### Step 4: Install libxsc-rt to Toolchain

```bash
cd /build/xsc/src/libxsc-rt
make install PREFIX=/opt/xsc-toolchain
```

**Output**:
- `/opt/xsc-toolchain/lib/libxsc-rt.so`
- `/opt/xsc-toolchain/include/xsc/syscall.h`

### Step 5: Build xsc-glibc Headers

```bash
mkdir -p /opt/xsc-toolchain/sysroot
mkdir -p /build/xsc/glibc-headers
cd /build/xsc/glibc-headers

../glibc-2.36/configure \
  --prefix=/usr \
  --host=x86_64-xsc-linux-gnu \
  --build=x86_64-pc-linux-gnu \
  --with-headers=/opt/xsc-toolchain/sysroot/usr/include \
  --disable-werror

make install-headers install_root=/opt/xsc-toolchain/sysroot
```

**Note**: This will likely fail initially because stage 1 GCC can't compile full glibc. That's expected - we only need headers.

### Step 6: Build Full GCC (Stage 2)

```bash
mkdir -p /build/xsc/gcc-stage2
cd /build/xsc/gcc-stage2

../gcc-13.2.0/configure \
  --prefix=/opt/xsc-toolchain \
  --target=x86_64-xsc-linux-gnu \
  --enable-languages=c,c++ \
  --with-sysroot=/opt/xsc-toolchain/sysroot \
  --disable-multilib

make -j80
make install
```

**Expected time**: 30-40 minutes

**Output**: Full x86_64-xsc-linux-gnu-gcc with C++ support

### Step 7: Build Full xsc-glibc

```bash
mkdir -p /build/xsc/glibc-build
cd /build/xsc/glibc-build

../glibc-2.36/configure \
  --prefix=/usr \
  --host=x86_64-xsc-linux-gnu \
  --build=x86_64-pc-linux-gnu \
  --with-headers=/opt/xsc-toolchain/sysroot/usr/include \
  --disable-werror

make -j80
make install install_root=/opt/xsc-toolchain/sysroot
```

**Expected time**: 15-20 minutes

**Output**: Full xsc-glibc in sysroot

## Expected Challenges

### Challenge 1: Target Triplet

GCC may not recognize `x86_64-xsc-linux-gnu` as a valid target.

**Solution**: Add config files to GCC source:
- `config.sub`: Add xsc to recognized vendors
- `config.guess`: Detect xsc target

**Alternative**: Use `x86_64-unknown-linux-gnu` and rely on sysroot

### Challenge 2: Missing Headers

Stage 1 GCC build may fail looking for system headers.

**Solution**: Use `--without-headers` and `--with-newlib` flags

### Challenge 3: glibc Requires Working Compiler

glibc build needs a compiler that can create executables.

**Solution**: 3-stage bootstrap (stage 1 → headers → stage 2 → full glibc)

### Challenge 4: libxsc-rt Linking

glibc expects to link against libxsc-rt but may not find it.

**Solution**: Install libxsc-rt to `/opt/xsc-toolchain/lib` first

## Verification

After each stage, verify:

### Stage 1 Verification

```bash
/opt/xsc-toolchain/bin/x86_64-xsc-linux-gnu-gcc --version
/opt/xsc-toolchain/bin/x86_64-xsc-linux-gnu-gcc -v
```

### Stage 2 Verification

```bash
# Test compile simple program
cat > test.c << 'EOF'
int main() { return 0; }
EOF

/opt/xsc-toolchain/bin/x86_64-xsc-linux-gnu-gcc \
  --sysroot=/opt/xsc-toolchain/sysroot \
  -o test test.c \
  -lxsc-rt \
  -static

# Verify ZERO syscall instructions
objdump -d test | grep syscall
# Expected: NO OUTPUT
```

### Final Verification

```bash
# Build hello world with XSC
cat > hello-xsc.c << 'EOF'
#include <stdio.h>
int main() {
    printf("Hello from XSC!\n");
    return 0;
}
EOF

/opt/xsc-toolchain/bin/x86_64-xsc-linux-gnu-gcc \
  --sysroot=/opt/xsc-toolchain/sysroot \
  -o hello-xsc hello-xsc.c \
  -lxsc-rt \
  -static

# Verify zero syscalls
objdump -d hello-xsc | grep syscall
# Expected: NO OUTPUT

# Run it
./hello-xsc
# Expected: Hello from XSC!
```

## Timeline

- **Hour 1**: Download GCC, extract, download prerequisites
- **Hour 2**: Configure and build stage 1 GCC
- **Hour 3**: Install libxsc-rt, attempt glibc headers
- **Hour 4**: Debug header installation issues
- **Hour 5**: Configure and build stage 2 GCC
- **Hour 6-7**: Build full xsc-glibc
- **Hour 8**: Testing and verification

**Total estimated time**: 8-10 hours of build time, potentially 1-2 days with debugging

## Success Criteria

Phase 3 is complete when:

1. ✅ x86_64-xsc-linux-gnu-gcc compiles C and C++ programs
2. ✅ Compiled programs link against libxsc-rt
3. ✅ `objdump -d` shows ZERO syscall instructions
4. ✅ hello-xsc runs and produces correct output
5. ✅ Full xsc-glibc installed in sysroot

## Next Phase Preview

**Phase 4-5** (Week 5): Build bash with XSC toolchain

Once toolchain is verified working:
```bash
python3 -m lebowski.cli build bash \
  --opinion-file opinions/bash/xsc.yaml \
  --container-image lebowski/builder:xsc \
  --output-dir /tmp/bash-xsc

# Ultimate verification
objdump -d /tmp/bash-xsc-extract/bin/bash | grep syscall
# Expected: NO OUTPUT

# This proves the entire XSC concept works!
```

## Files to Create

- `/build/xsc/gcc-13.2.0/` - GCC source
- `/build/xsc/gcc-stage1/` - Stage 1 build
- `/build/xsc/gcc-stage2/` - Stage 2 build
- `/build/xsc/glibc-headers/` - Header-only glibc build
- `/build/xsc/glibc-build/` - Full glibc build
- `/opt/xsc-toolchain/` - Final installed toolchain

## Notes

This is the most complex phase because we're building a custom cross-compiler toolchain from scratch. The bootstrap process is intricate and each stage depends on the previous.

**Alternative approach** (if bootstrap fails): Use standard x86_64-linux-gnu target and rely entirely on sysroot + library paths. This would be simpler but less "pure" from XSC perspective.

**Monitoring**: Use `top` or `htop` to verify builds are using all 80 cores effectively.

---

Starting Phase 3 build now...
