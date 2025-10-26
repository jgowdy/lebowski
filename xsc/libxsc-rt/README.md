# libxsc-rt - XSC Runtime Library

XSC (eXtended SysCall) Runtime Library providing zero-syscall instruction binaries through ring-based system call transitions.

## Current Status: STUB IMPLEMENTATION

**⚠️ This is a STUB version that still uses syscall instructions internally.**

### What Works

✅ **Library builds successfully**
- libxsc-rt.so.1.0.0 (shared library, 16KB)
- libxsc-rt.a (static library, 3.2KB)
- xsc/syscall.h header file

✅ **API is functional**
- `xsc_syscall()` - main syscall entry point
- `xsc_read()`, `xsc_write()`, `xsc_open()`, `xsc_close()` - convenience wrappers
- `xsc_get_stats()`, `xsc_reset_stats()` - statistics tracking

✅ **Test program passes**
- All 6 tests passing
- Correctly tracks syscall statistics
- Can read/write files
- Hostname test: reads /etc/hostname successfully

✅ **Build system working**
- Makefile with all, install, test, clean targets
- Proper library versioning (SONAME)
- Both shared and static builds

### What Doesnt Work Yet