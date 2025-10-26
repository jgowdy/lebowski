# libxsc-rt Makefile
# XSC Runtime Library - Zero Syscall Instructions

CC = gcc
AR = ar
CFLAGS = -O2 -Wall -Wextra -fPIC -I.
LDFLAGS = -shared

LIB_NAME = libxsc-rt
MAJOR = 1
MINOR = 0
PATCH = 0

# Shared library versioning
SONAME = $(LIB_NAME).so.$(MAJOR)
SHARED_LIB = $(LIB_NAME).so.$(MAJOR).$(MINOR).$(PATCH)
STATIC_LIB = $(LIB_NAME).a

# Source files
SRCS = xsc_syscall.c
OBJS = $(SRCS:.c=.o)
HEADERS = xsc_syscall.h

# Installation paths
PREFIX ?= /opt/xsc-toolchain
LIBDIR = $(PREFIX)/lib
INCLUDEDIR = $(PREFIX)/include/xsc

.PHONY: all clean install test

all: $(SHARED_LIB) $(STATIC_LIB)

# Build shared library
$(SHARED_LIB): $(OBJS)
	$(CC) $(LDFLAGS) -Wl,-soname,$(SONAME) -o $@ $^
	ln -sf $(SHARED_LIB) $(SONAME)
	ln -sf $(SONAME) $(LIB_NAME).so

# Build static library
$(STATIC_LIB): $(OBJS)
	$(AR) rcs $@ $^

# Compile object files
%.o: %.c $(HEADERS)
	$(CC) $(CFLAGS) -c $< -o $@

# Install library and headers
install: all
	mkdir -p $(LIBDIR) $(INCLUDEDIR)
	install -m 755 $(SHARED_LIB) $(LIBDIR)/
	ln -sf $(SHARED_LIB) $(LIBDIR)/$(SONAME)
	ln -sf $(SONAME) $(LIBDIR)/$(LIB_NAME).so
	install -m 644 $(STATIC_LIB) $(LIBDIR)/
	install -m 644 $(HEADERS) $(INCLUDEDIR)/

# Build test program
test: test_xsc
	@echo "Running XSC test..."
	@./test_xsc
	@echo "Test passed!"

test_xsc: test_xsc.c $(SHARED_LIB)
	$(CC) -o $@ $< -L. -lxsc-rt -Wl,-rpath,$(PWD)

# Clean build artifacts
clean:
	rm -f $(OBJS) $(SHARED_LIB) $(STATIC_LIB) $(SONAME) $(LIB_NAME).so
	rm -f test_xsc

.PHONY: help
help:
	@echo "libxsc-rt Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  all      - Build shared and static libraries (default)"
	@echo "  install  - Install to PREFIX (default: /opt/xsc-toolchain)"
	@echo "  test     - Build and run test program"
	@echo "  clean    - Remove build artifacts"
	@echo "  help     - Show this help message"
	@echo ""
	@echo "Variables:"
	@echo "  PREFIX   - Installation prefix (default: /opt/xsc-toolchain)"
	@echo "  CC       - C compiler (default: gcc)"
	@echo ""
	@echo "Example:"
	@echo "  make"
	@echo "  make test"
	@echo "  make install PREFIX=/usr/local"
