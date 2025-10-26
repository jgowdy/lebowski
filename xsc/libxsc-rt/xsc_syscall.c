/* XSC Syscall Implementation - STUB VERSION
 *
 * This is a TEMPORARY stub implementation that uses the real syscall
 * instruction internally. This lets us:
 *
 * 1. Build and test the XSC toolchain infrastructure
 * 2. Verify glibc patches work correctly
 * 3. Confirm binaries link against libxsc-rt
 * 4. Test that glibc calls xsc_syscall() instead of syscall instruction
 *
 * TODO: Replace with real ring transition code once kernel support exists.
 */

#define _GNU_SOURCE
#include "xsc_syscall.h"
#include <sys/syscall.h>
#include <sys/mman.h>
#include <fcntl.h>
#include <errno.h>
#include <string.h>

/* Global statistics */
static struct xsc_stats global_stats = {0};

/* Main XSC syscall entry point - STUB VERSION
 *
 * WARNING: This stub uses the syscall instruction internally.
 * When the real implementation is ready, this will be replaced
 * with ring transition code.
 */
long xsc_syscall(long number, long arg1, long arg2, long arg3,
                  long arg4, long arg5, long arg6) {
    long result;
    
    /* Update statistics */
    global_stats.total_syscalls++;
    
    /* TODO: Replace this with ring transition code
     * 
     * Real implementation will:
     * 1. Save current ring 3 state
     * 2. Transition to ring 0
     * 3. Invoke kernel handler
     * 4. Capture result
     * 5. Transition back to ring 3
     * 6. Restore state and return result
     */
    
    /* TEMPORARY: Use real syscall instruction */
    result = syscall(number, arg1, arg2, arg3, arg4, arg5, arg6);
    
    /* Track ring transitions (fake for stub) */
    global_stats.ring_transitions++;
    
    /* Track errors */
    if (result < 0) {
        global_stats.failed_syscalls++;
    }
    
    return result;
}

/* Convenience wrappers */

ssize_t xsc_read(int fd, void *buf, size_t count) {
    return xsc_syscall(SYS_read, fd, (long)buf, count, 0, 0, 0);
}

ssize_t xsc_write(int fd, const void *buf, size_t count) {
    return xsc_syscall(SYS_write, fd, (long)buf, count, 0, 0, 0);
}

int xsc_open(const char *pathname, int flags, mode_t mode) {
    return xsc_syscall(SYS_open, (long)pathname, flags, mode, 0, 0, 0);
}

int xsc_close(int fd) {
    return xsc_syscall(SYS_close, fd, 0, 0, 0, 0, 0);
}

void *xsc_mmap(void *addr, size_t length, int prot, int flags,
               int fd, off_t offset) {
    return (void *)xsc_syscall(SYS_mmap, (long)addr, length, prot, 
                               flags, fd, offset);
}

int xsc_munmap(void *addr, size_t length) {
    return xsc_syscall(SYS_munmap, (long)addr, length, 0, 0, 0, 0);
}

/* Statistics functions */

int xsc_get_stats(struct xsc_stats *stats) {
    if (!stats) {
        errno = EINVAL;
        return -1;
    }
    
    memcpy(stats, &global_stats, sizeof(struct xsc_stats));
    return 0;
}

void xsc_reset_stats(void) {
    memset(&global_stats, 0, sizeof(struct xsc_stats));
}
