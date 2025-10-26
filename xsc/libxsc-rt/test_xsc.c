/* XSC Test Program
 * 
 * Tests that libxsc-rt works correctly by:
 * 1. Calling xsc_syscall functions
 * 2. Verifying results match expected behavior
 * 3. Checking statistics tracking
 */

#include <stdio.h>
#include <string.h>
#include <assert.h>
#include "xsc_syscall.h"

int main() {
    struct xsc_stats stats;
    char buffer[256];
    int fd;
    ssize_t bytes;
    
    printf("=== XSC Runtime Library Test ===\n\n");
    
    /* Test 1: Reset statistics */
    xsc_reset_stats();
    xsc_get_stats(&stats);
    assert(stats.total_syscalls == 0);
    printf("✓ Test 1: Statistics reset\n");
    
    /* Test 2: Test xsc_write */
    const char *msg = "Hello from XSC!\n";
    bytes = xsc_write(1, msg, strlen(msg));
    assert(bytes == strlen(msg));
    printf("✓ Test 2: xsc_write works\n");
    
    /* Test 3: Check statistics updated */
    xsc_get_stats(&stats);
    assert(stats.total_syscalls > 0);
    printf("✓ Test 3: Statistics tracking works\n");
    printf("  Total syscalls: %lu\n", stats.total_syscalls);
    printf("  Ring transitions: %lu\n", stats.ring_transitions);
    
    /* Test 4: Test xsc_open/close */
    fd = xsc_open("/dev/null", 02, 0);  /* O_RDWR = 02 */
    assert(fd >= 0);
    printf("✓ Test 4: xsc_open works (fd=%d)\n", fd);
    
    int result = xsc_close(fd);
    assert(result == 0);
    printf("✓ Test 5: xsc_close works\n");
    
    /* Test 6: Test xsc_read */
    /* Open /etc/hostname and read it */
    fd = xsc_open("/etc/hostname", 0, 0);  /* O_RDONLY = 0 */
    if (fd >= 0) {
        bytes = xsc_read(fd, buffer, sizeof(buffer) - 1);
        if (bytes > 0) {
            buffer[bytes] = 0;
            printf("✓ Test 6: xsc_read works (read %zd bytes)\n", bytes);
            printf("  Hostname: %s", buffer);
        }
        xsc_close(fd);
    }
    
    /* Final statistics */
    xsc_get_stats(&stats);
    printf("\n=== Final Statistics ===\n");
    printf("Total syscalls: %lu\n", stats.total_syscalls);
    printf("Ring transitions: %lu\n", stats.ring_transitions);
    printf("Failed syscalls: %lu\n", stats.failed_syscalls);
    
    printf("\n✓✓✓ All tests passed! ✓✓✓\n");
    printf("\nNOTE: This is the STUB implementation.\n");
    printf("It still uses syscall instructions internally.\n");
    printf("Once glibc is patched, those will disappear.\n");
    
    return 0;
}
