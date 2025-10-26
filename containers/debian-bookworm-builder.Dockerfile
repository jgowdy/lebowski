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
# Pin package versions for reproducibility
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential=12.9 \
        devscripts=2.23.4+deb12u1 \
        fakeroot=1.31-1.2 \
        debhelper=13.11.4 \
        dpkg-dev=1.21.22 \
        quilt=0.67-3 \
        patch=2.7.6-7 \
        python3=3.11.2-1+b1 \
        python3-pip=23.0.1+dfsg-1 \
        python3-yaml=6.0-3+b2 \
        ca-certificates=20230311 \
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
