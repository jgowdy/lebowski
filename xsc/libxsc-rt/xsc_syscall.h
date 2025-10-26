/* XSC Syscall Header
 * Zero-Syscall Runtime Library
 *
 * This header defines the XSC syscall API that replaces direct
 * syscall instructions with ring-based transitions.
 */

#ifndef _XSC_SYSCALL_H
#define _XSC_SYSCALL_H

#include <sys/types.h>
#include <unistd.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Main XSC syscall entry point
 * 
 * Replaces the syscall instruction with a ring transition.
 * Arguments match Linux syscall convention.
 * 
 * Parameters:
 *   number - Linux syscall number (from <asm/unistd_64.h>)
 *   arg1-arg6 - Syscall arguments (usage depends on syscall)
 * 
 * Returns:
 *   Syscall return value, or -errno on error
 */
long xsc_syscall(long number, long arg1, long arg2, long arg3,
                  long arg4, long arg5, long arg6);

/* Convenience wrappers matching standard POSIX API */
ssize_t xsc_read(int fd, void *buf, size_t count);
ssize_t xsc_write(int fd, const void *buf, size_t count);
int xsc_open(const char *pathname, int flags, mode_t mode);
int xsc_close(int fd);
void *xsc_mmap(void *addr, size_t length, int prot, int flags,
               int fd, off_t offset);
int xsc_munmap(void *addr, size_t length);

/* XSC runtime statistics */
struct xsc_stats {
    unsigned long total_syscalls;      /* Total syscalls made */
    unsigned long ring_transitions;    /* Ring 3→0→3 transitions */
    unsigned long cached_transitions;  /* Cached/optimized transitions */
    unsigned long failed_syscalls;     /* Syscalls that returned error */
};

/* Get XSC runtime statistics */
int xsc_get_stats(struct xsc_stats *stats);

/* Reset XSC statistics */
void xsc_reset_stats(void);

#ifdef __cplusplus
}
#endif

#endif /* _XSC_SYSCALL_H */
