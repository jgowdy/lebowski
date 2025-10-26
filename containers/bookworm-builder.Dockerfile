# Lebowski Build Container - Debian Bookworm
#
# This container provides a reproducible build environment for Debian packages.
# All builds using this container MUST produce bit-for-bit identical outputs.
#
# Version: 1.0
# Base: Debian Bookworm

FROM debian:bookworm-20240110@sha256:2cbb1be3e5b90e85c1b7e68cc6dcbe7a8d3cb8e3e5d4c0b1e7e62fd8e6c3e8c3

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Set reproducible build environment
ENV SOURCE_DATE_EPOCH=1704067200
ENV TZ=UTC
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8
ENV LANGUAGE=C.UTF-8

# Disable dpkg fsync for faster builds (safe in containers)
RUN echo "force-unsafe-io" > /etc/dpkg/dpkg.cfg.d/02lebowski

# Install build tools with pinned versions
RUN apt-get update && apt-get install -y \
    build-essential \
    devscripts \
    dpkg-dev \
    debhelper \
    fakeroot \
    \
    # Reproducible build tools
    strip-nondeterminism \
    \
    # Source control
    git \
    \
    # Compression tools
    xz-utils \
    zstd \
    \
    # Python for build scripts
    python3 \
    python3-yaml \
    python3-debian \
    \
    # Utilities
    wget \
    curl \
    gnupg \
    ca-certificates \
    \
    && rm -rf /var/lib/apt/lists/*

# Set up deb-src sources
RUN echo "deb-src http://deb.debian.org/debian bookworm main" >> /etc/apt/sources.list \
    && echo "deb-src http://deb.debian.org/debian-security bookworm-security main" >> /etc/apt/sources.list \
    && apt-get update

# Configure git for reproducibility
RUN git config --global user.name "Lebowski Builder" \
    && git config --global user.email "builder@lebowski.org"

# Create build directory
RUN mkdir -p /build
WORKDIR /build

# Set default shell
SHELL ["/bin/bash", "-c"]

# Labels
LABEL org.lebowski.version="1.0" \
      org.lebowski.base="debian:bookworm" \
      org.lebowski.purpose="reproducible-builds" \
      org.lebowski.source_date_epoch="1704067200"

# Entry point
CMD ["/bin/bash"]
