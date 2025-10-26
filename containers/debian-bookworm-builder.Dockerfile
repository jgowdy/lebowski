# Lebowski reproducible build container
# Based on Debian Bookworm (stable)

FROM debian:bookworm@sha256:e97ee92bf1e11a2de654e9f3da827d8dce32b54e0490ac83bfc65c8706568116

# Use fixed timestamp for reproducibility
ENV SOURCE_DATE_EPOCH=1704067200
ENV TZ=UTC
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
# Note: Using latest versions from bookworm instead of pinned versions
# TODO: Use snapshot.debian.org with fixed date for true reproducibility
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        devscripts \
        fakeroot \
        debhelper \
        dpkg-dev \
        quilt \
        patch \
        python3 \
        python3-pip \
        python3-yaml \
        ca-certificates \
        libncurses-dev \
        bison \
        autoconf \
        automake \
        autotools-dev \
        libtool \
        pkg-config \
        texinfo \
        && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create build user (non-root for security)
RUN useradd -m -u 1000 -s /bin/bash builder && \
    mkdir -p /build && \
    chown builder:builder /build

USER builder
WORKDIR /build

# Default command
CMD ["/bin/bash"]
