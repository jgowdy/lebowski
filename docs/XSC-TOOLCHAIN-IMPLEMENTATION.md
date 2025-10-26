# XSC Toolchain Implementation Guide

## Executive Summary

**Goal**: Build x86_64-xsc-linux-gnu-gcc toolchain that produces binaries with ZERO `syscall` instructions.

**Key Insight from Research**: GCC doesn't generate `syscall` instructions directly. Instead:
1. GCC calls glibc wrapper functions (read(), write(), open(), etc.)
2. glibc wrappers (in `sysdeps/unix/sysv/linux/x86_64/syscall.S`) emit the `syscall` instruction
3. **To eliminate syscalls**: Modify glibc's syscall wrappers to call `xsc_syscall()` instead

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ User Code: read(fd, buf, count)                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ Standard glibc:      │  XSC glibc:                          │
│   syscall.S          │    xsc_syscall.S                     │
│   mov $0, %rax       │    call xsc_syscall@PLT              │
│   syscall    ◄───────┼─── NO syscall instruction!           │
└──────────────────────┴──────────────────────────────────────┘
                                │
                                ▼
                       ┌─────────────────────┐
                       │ libxsc-rt.so        │
                       │ xsc_syscall()       │
                       │ - Ring transition   │
                       │ - Kernel handler    │
                       │ - Return to ring 3  │
                       └─────────────────────┘
```

## Implementation Strategy

### Option A: Patched glibc (RECOMMENDED)

**Why**: Clean, maintains ABI compatibility, straightforward to verify.

**Steps**:
1. Download glibc 2.36 source
2. Patch `sysdeps/unix/sysv/linux/x86_64/syscall.S` to replace `syscall` with `call xsc_syscall`
3. Build xsc-glibc with x86_64-xsc-linux-gnu target
4. Link all packages against xsc-glibc + libxsc-rt

**Verification**: `objdump -d` of ANY binary should show ZERO `syscall` instructions.

### Option B: Compiler Wrapper (FALLBACK)

**Why**: Simpler but requires intercepting every syscall at link time.

**Steps**:
1. Create x86_64-xsc-linux-gnu-gcc wrapper script
2. Inject `-Wl,--wrap=syscall` for every syscall function
3. Provide libxsc-rt with `__wrap_*` functions
4. Link time rewrites syscall to xsc_syscall

**Problem**: Misses inline syscalls, requires wrapping 300+ functions.

## Phase 1: Build libxsc-rt

**Priority**: Build this FIRST before toolchain, so we can test it.

### libxsc-rt API Design

```c
// xsc/syscall.h
#ifndef _XSC_SYSCALL_H
#define _XSC_SYSCALL_H

#include <sys/types.h>

// Main XSC syscall entry point
long xsc_syscall(long number, long arg1, long arg2, long arg3,
                  long arg4, long arg5, long arg6);

// Convenience wrappers matching Linux syscall API
ssize_t xsc_read(int fd, void *buf, size_t count);
ssize_t xsc_write(int fd, const void *buf, size_t count);
int xsc_open(const char *pathname, int flags, mode_t mode);
int xsc_close(int fd);

// Ring transition statistics
struct xsc_stats {
    unsigned long total_syscalls;
    unsigned long ring_transitions;
    unsigned long cached_transitions;
};

int xsc_get_stats(struct xsc_stats *stats);

#endif /* _XSC_SYSCALL_H */
```

### libxsc-rt Implementation Phases

#### Phase 1.1: Stub Implementation (FOR TESTING)

```c
// xsc/syscall.c (STUB VERSION)
#include "xsc/syscall.h"
#include <unistd.h>
#include <syscall.h>

// TEMPORARY: Use real syscall instruction for testing
// This lets us build the toolchain infrastructure first
long xsc_syscall(long number, long arg1, long arg2, long arg3,
                  long arg4, long arg5, long arg6) {
    // TODO: Replace with ring transition code
    return syscall(number, arg1, arg2, arg3, arg4, arg5, arg6);
}

ssize_t xsc_read(int fd, void *buf, size_t count) {
    return xsc_syscall(__NR_read, fd, (long)buf, count, 0, 0, 0);
}

ssize_t xsc_write(int fd, const void *buf, size_t count) {
    return xsc_syscall(__NR_write, fd, (long)buf, count, 0, 0, 0);
}

// ... (similar wrappers for open, close, etc.)
```

**Purpose**: This stub lets us:
1. Build xsc-glibc that calls `xsc_syscall()`
2. Verify glibc patches work
3. Confirm binaries have zero `syscall` instructions (glibc calls function instead)
4. Replace stub with real ring transitions later

#### Phase 1.2: Ring Transition Implementation (FUTURE)

```c
// xsc/ring_transition.S (x86_64 assembly)
.global xsc_syscall
.type xsc_syscall, @function

xsc_syscall:
    // Save registers
    push %rbx
    push %r12
    push %r13

    // Transition to ring 0
    // TODO: Implement ring transition mechanism
    // This requires kernel support or hypervisor

    // Invoke kernel handler
    // rax = syscall number (already set by caller)
    // rdi, rsi, rdx, r10, r8, r9 = args (already set)

    // Return to ring 3

    // Restore registers
    pop %r13
    pop %r12
    pop %rbx

    ret
```

**Note**: Ring transition requires kernel/hypervisor support. Start with stub.

## Phase 2: Patch glibc for XSC

### 2.1 Download glibc Source

```bash
mkdir -p /build/xsc/glibc-src
cd /build/xsc/glibc-src

wget https://ftp.gnu.org/gnu/glibc/glibc-2.36.tar.xz
tar xf glibc-2.36.tar.xz
cd glibc-2.36
```

### 2.2 Create XSC Patch

**File**: `sysdeps/unix/sysv/linux/x86_64/syscall.S`

**Original**:
```asm
ENTRY (syscall)
        movq %rdi, %rax         /* Syscall number -> rax.  */
        movq %rsi, %rdi         /* shift arg1 - arg5.  */
        movq %rdx, %rsi
        movq %rcx, %rdx
        movq %r8, %r10
        movq %r9, %r8
        movq 8(%rsp),%r9        /* arg6 is on the stack.  */
        syscall                 /* ◄── REMOVE THIS */
        cmpq $-4095, %rax       /* Check %rax for error.  */
        jae SYSCALL_ERROR_LABEL
        ret
```

**XSC Patched Version**:
```asm
ENTRY (syscall)
        movq %rdi, %rax         /* Syscall number -> rax.  */
        movq %rsi, %rdi         /* shift arg1 - arg5.  */
        movq %rdx, %rsi
        movq %rcx, %rdx
        movq %r8, %r10
        movq %r9, %r8
        movq 8(%rsp),%r9        /* arg6 is on the stack.  */

        /* XSC: Call xsc_syscall instead of syscall instruction */
        /* Arguments already in correct registers for xsc_syscall */
        call xsc_syscall@PLT    /* ◄── USE FUNCTION CALL */

        cmpq $-4095, %rax       /* Check %rax for error.  */
        jae SYSCALL_ERROR_LABEL
        ret
```

**Create Patch**:
```bash
cat > /build/xsc/glibc-xsc.patch << 'EOF'
--- a/sysdeps/unix/sysv/linux/x86_64/syscall.S
+++ b/sysdeps/unix/sysv/linux/x86_64/syscall.S
@@ -30,7 +30,9 @@ ENTRY (syscall)
        movq %r8, %r10
        movq %r9, %r8
        movq 8(%rsp),%r9        /* arg6 is on the stack.  */
-       syscall
+       /* XSC: Call xsc_syscall instead of syscall instruction */
+       /* Arguments already in correct registers for xsc_syscall */
+       call xsc_syscall@PLT
        cmpq $-4095, %rax       /* Check %rax for error.  */
        jae SYSCALL_ERROR_LABEL
        ret
EOF
```

### 2.3 Apply Patch

```bash
cd /build/xsc/glibc-src/glibc-2.36
patch -p1 < /build/xsc/glibc-xsc.patch
```

### 2.4 Build xsc-glibc

```bash
mkdir -p /build/xsc/glibc-build
cd /build/xsc/glibc-build

../glibc-src/glibc-2.36/configure \
  --prefix=/opt/xsc-toolchain \
  --host=x86_64-xsc-linux-gnu \
  --build=x86_64-pc-linux-gnu \
  --enable-static-pie \
  --disable-werror

make -j80
make install
```

**Note**: This will fail initially because x86_64-xsc-linux-gnu-gcc doesn't exist yet.

## Phase 3: Build Cross-Compiler

### 3.1 Create Minimal GCC Cross-Compiler

**Purpose**: Build x86_64-xsc-linux-gnu-gcc to compile xsc-glibc.

```bash
mkdir -p /build/xsc/gcc-src
cd /build/xsc/gcc-src

wget https://ftp.gnu.org/gnu/gcc/gcc-13.2.0/gcc-13.2.0.tar.xz
tar xf gcc-13.2.0.tar.xz
cd gcc-13.2.0

# Download prerequisites
./contrib/download_prerequisites

mkdir -p /build/xsc/gcc-build
cd /build/xsc/gcc-build

../gcc-src/gcc-13.2.0/configure \
  --prefix=/opt/xsc-toolchain \
  --target=x86_64-xsc-linux-gnu \
  --enable-languages=c,c++ \
  --disable-multilib \
  --with-sysroot=/opt/xsc-toolchain/sysroot

make -j80
make install
```

### 3.2 Bootstrap Order

**Problem**: Circular dependency:
- xsc-glibc needs x86_64-xsc-linux-gnu-gcc to build
- x86_64-xsc-linux-gnu-gcc needs xsc-glibc headers to build

**Solution**: Three-stage bootstrap:

1. **Stage 1**: Build x86_64-xsc-linux-gnu-gcc (C only, no libc)
2. **Stage 2**: Build xsc-glibc headers + libxsc-rt using stage 1 compiler
3. **Stage 3**: Rebuild full x86_64-xsc-linux-gnu-gcc with xsc-glibc

## Phase 4: Integration Testing

### 4.1 Build Hello World with XSC

```c
// hello-xsc.c
#include <stdio.h>

int main() {
    printf("Hello from XSC!\n");
    return 0;
}
```

**Build**:
```bash
/opt/xsc-toolchain/bin/x86_64-xsc-linux-gnu-gcc \
  -o hello-xsc hello-xsc.c \
  -lxsc-rt \
  -static

# Verify ZERO syscall instructions
objdump -d hello-xsc | grep syscall
# Expected: NO OUTPUT

# Run it
./hello-xsc
# Expected: Hello from XSC!
```

### 4.2 Verification Criteria

**SUCCESS** = All of these are true:

1. ✅ Binary executes correctly
2. ✅ `objdump -d <binary> | grep syscall` returns NO OUTPUT
3. ✅ `ldd <binary>` shows libxsc-rt.so
4. ✅ Binary produces expected output
5. ✅ strace shows syscalls happening (via libxsc-rt)

## Directory Structure

```
/build/xsc/
├── toolchain/              # Final installed toolchain
│   ├── bin/
│   │   ├── x86_64-xsc-linux-gnu-gcc
│   │   ├── x86_64-xsc-linux-gnu-g++
│   │   └── x86_64-xsc-linux-gnu-ar
│   ├── lib/
│   │   ├── libxsc-rt.so
│   │   ├── libxsc-rt.a
│   │   └── gcc/...
│   ├── include/
│   │   └── xsc/
│   │       └── syscall.h
│   └── sysroot/
│       ├── lib/
│       │   ├── libc.so.6      # xsc-glibc
│       │   └── libpthread.so
│       └── usr/
│           └── include/...
│
├── src/
│   ├── libxsc-rt/          # XSC runtime library source
│   │   ├── syscall.c
│   │   ├── ring_transition.S
│   │   ├── xsc/syscall.h
│   │   └── Makefile
│   ├── glibc-2.36/         # Patched glibc source
│   └── gcc-13.2.0/         # GCC source
│
├── build/
│   ├── libxsc-rt/
│   ├── glibc/
│   └── gcc/
│
└── patches/
    ├── glibc-xsc.patch     # Syscall instruction replacement
    └── README.md
```

## Immediate Next Steps

### Week 1: Build libxsc-rt Stub

1. Create `/build/xsc/src/libxsc-rt/` directory structure
2. Write stub xsc_syscall() implementation (uses real syscall for now)
3. Build libxsc-rt.so with standard gcc
4. Write test program that calls xsc_syscall()
5. Verify test program works

**Deliverable**: Working libxsc-rt.so (even though it's still using syscall internally)

### Week 2: Patch and Build glibc

1. Download glibc 2.36 source
2. Create glibc-xsc.patch
3. Apply patch to syscall.S
4. Attempt build (will fail without cross-compiler)
5. Document exact failure points

**Deliverable**: Patched glibc source tree, build failure report

### Week 3: Build Cross-Compiler Stage 1

1. Download GCC 13.2.0 source
2. Configure for x86_64-xsc-linux-gnu target
3. Build C-only cross-compiler
4. Test compiling simple C program
5. Verify x86_64-xsc-linux-gnu-gcc executable works

**Deliverable**: Working x86_64-xsc-linux-gnu-gcc (C only)

### Week 4: Complete Bootstrap

1. Build xsc-glibc using stage 1 compiler
2. Install xsc-glibc to sysroot
3. Rebuild full GCC with C++ support
4. Build hello-xsc test program
5. **VERIFY ZERO SYSCALLS** with objdump

**Deliverable**: Complete XSC toolchain, verified zero-syscall binary

## Success Metrics

### Minimum Viable XSC Toolchain

- [ ] x86_64-xsc-linux-gnu-gcc compiles C programs
- [ ] Compiled binaries execute correctly
- [ ] `objdump -d <binary> | grep syscall` returns ZERO matches
- [ ] libxsc-rt.so is linked
- [ ] Test programs produce expected output

### Production Ready XSC Toolchain

- [ ] C++ support functional
- [ ] xsc-glibc passes glibc test suite
- [ ] Bash builds with XSC opinion
- [ ] All 14 baseline packages build with XSC
- [ ] Performance benchmarks acceptable
- [ ] Documentation complete

## Risk Mitigation

### Risk 1: Ring Transitions Don't Exist

**Mitigation**: Use stub implementation first. Verify glibc patches work BEFORE implementing ring transitions.

### Risk 2: Performance Overhead

**Mitigation**: Benchmark stub version. If acceptable, ring transitions will likely be similar.

### Risk 3: ABI Incompatibility

**Mitigation**: Keep xsc_syscall() signature identical to syscall(). Use PLT for dynamic linking.

### Risk 4: Glibc Dependencies

**Mitigation**: Static link everything initially. Dynamic linking is phase 2.

## Conclusion

**Path Forward**:

1. ✅ **Research Complete**: Understand syscall chain (GCC → glibc → syscall instruction)
2. ⏩ **Next**: Build libxsc-rt stub (Week 1)
3. ⏩ **Then**: Patch glibc (Week 2)
4. ⏩ **Then**: Build cross-compiler (Week 3-4)
5. ⏩ **Finally**: Verify zero syscalls with bash (Week 5)

**This is achievable**. The toolchain is complex but well-defined.

**Timeline**: 4-5 weeks to working XSC toolchain with stub implementation.

**First Milestone**: Hello World binary with ZERO syscall instructions.
