# Opinion Definition Format

## Overview

Opinions are defined in YAML files that describe modifications to stock Debian packages.

## Schema

### Basic Structure

```yaml
# opinions/nginx/http3.yaml
version: "1.0"              # Opinion format version
package: nginx              # Debian source package name
opinion_name: http3         # Short identifier for this opinion
description: |              # Human-readable description
  nginx with HTTP/3 (QUIC) support for modern web protocols

maintainer:                 # Opinion maintainer info
  name: John Doe
  email: john@example.com
  github: johndoe

tags:                       # Categorization tags
  - experimental
  - performance
  - http3

modifications:              # The actual changes (see below)
  # ...
```

### Modifications Section

The `modifications` section defines what changes to apply:

#### 1. Build Dependencies

```yaml
modifications:
  build_deps:
    add:                    # Add build dependencies
      - libquiche-dev
      - libnghttp3-dev
    remove:                 # Remove build dependencies (rare)
      - obsolete-lib-dev
```

#### 2. Patches

```yaml
modifications:
  patches:
    - patches/nginx/http3-support.patch
    - patches/nginx/quic-listener.patch
```

Patches stored in `/patches/<package>/` directory.

#### 3. Configure Flags

For autoconf/configure-based packages:

```yaml
modifications:
  configure_flags:
    add:
      - --with-http_v3_module
      - --with-stream_quic_module
    remove:
      - --without-http_v2_module
    replace:
      --with-cc-opt="-O2": --with-cc-opt="-O3 -march=znver3"
```

#### 4. Debian Rules Modifications

For complex changes to `debian/rules`:

```yaml
modifications:
  debian_rules:
    # Append to existing rules
    append: |
      override_dh_auto_configure:
          ./configure --with-custom-flags

    # Or use sed-like replacements
    sed:
      - pattern: 'CFLAGS\s*=.*'
        replacement: 'CFLAGS = -O3 -march=native'
```

#### 5. Compiler Flags

```yaml
modifications:
  cflags:
    add: ["-march=znver3", "-mtune=znver3"]
  cxxflags:
    add: ["-march=znver3", "-mtune=znver3"]
  ldflags:
    add: ["-flto"]

  # Or replace entirely
  cflags:
    set: "-O3 -march=native -flto"
```

#### 6. Environment Variables

```yaml
modifications:
  env:
    DEB_BUILD_OPTIONS: "parallel=4 nocheck"
    DEB_CFLAGS_APPEND: "-march=znver3"
```

#### 7. File Replacements

```yaml
modifications:
  files:
    replace:
      "debian/control": "files/nginx/control.http3"
      "debian/nginx.service": "files/nginx/nginx-http3.service"
```

#### 8. Scripts

For complex modifications:

```yaml
modifications:
  scripts:
    pre_build: scripts/nginx/setup-http3.sh
    post_build: scripts/nginx/verify-modules.sh
```

### Complete Example: nginx-http3

```yaml
version: "1.0"
package: nginx
opinion_name: http3
description: |
  nginx built with HTTP/3 and QUIC support for improved performance
  with modern clients. Requires kernel with UDP GRO support for best
  performance.

maintainer:
  name: Lebowski Project
  email: jay.me
  github: lebowski-project

tags:
  - experimental
  - performance
  - http3
  - quic

upstream_info:
  tested_versions:
    - "1.24.0"
    - "1.25.0"
  upstream_url: "https://nginx.org/en/docs/http/ngx_http_v3_module.html"

modifications:
  build_deps:
    add:
      - libquiche-dev

  configure_flags:
    add:
      - --with-http_v3_module
      - --with-stream_quic_module

  patches:
    - patches/nginx/http3-default-port.patch

notes: |
  After installation, add to nginx.conf:

  server {
      listen 443 quic reuseport;
      listen 443 ssl;
      http3 on;
  }
```

### Complete Example: python3-optimized

```yaml
version: "1.0"
package: python3-defaults
opinion_name: optimized
description: |
  Python 3 built with PGO (Profile-Guided Optimization) and LTO
  for improved performance. Expect 10-30% speedup on CPU-bound workloads.

maintainer:
  name: Lebowski Project
  email: jay.me

tags:
  - performance
  - optimization

modifications:
  configure_flags:
    add:
      - --enable-optimizations
      - --with-lto

  env:
    DEB_CFLAGS_APPEND: "-O3 -flto"
    DEB_BUILD_OPTIONS: "parallel=8"

  scripts:
    post_build: scripts/python3/benchmark.sh

build_time_note: |
  This build takes significantly longer due to PGO (builds Python twice
  and runs benchmark suite). Expect 2-3x normal build time.
```

### Complete Example: gcc-native

```yaml
version: "1.0"
package: gcc-13
opinion_name: native
description: |
  GCC optimized for the build machine's CPU architecture.
  WARNING: Binaries produced will only work on similar CPUs.

maintainer:
  name: Lebowski Project
  email: jay.me

tags:
  - optimization
  - cpu-specific

warnings:
  - "This build is CPU-specific and not portable"
  - "Binaries built with this GCC will only run on similar CPUs"

modifications:
  cflags:
    add:
      - "-march=native"
      - "-mtune=native"

  cxxflags:
    add:
      - "-march=native"
      - "-mtune=native"
```

## Directory Structure

```
lebowski-opinions/          # Git repository
├── README.md
├── opinions/
│   ├── nginx/
│   │   ├── http3.yaml
│   │   ├── minimal.yaml
│   │   └── full.yaml
│   ├── python3/
│   │   ├── optimized.yaml
│   │   └── minimal.yaml
│   └── gcc-13/
│       └── native.yaml
├── patches/
│   ├── nginx/
│   │   └── http3-default-port.patch
│   └── python3/
│       └── custom.patch
├── scripts/
│   ├── nginx/
│   │   └── verify-modules.sh
│   └── python3/
│       └── benchmark.sh
└── files/
    └── nginx/
        └── control.http3
```

## Validation

Opinion files should be validated before acceptance:

```bash
lebowski validate opinions/nginx/http3.yaml
```

Checks:
- YAML syntax valid
- Required fields present
- Patch files exist
- Script files exist and executable
- No dangerous operations

## Best Practices

### 1. Keep It Simple

Prefer simple modifications over complex scripts.

### 2. Document Well

Explain WHY the opinion exists and what benefits it provides.

### 3. Test Across Versions

Test opinion against multiple Debian/package versions.

### 4. Minimal Changes

Make the smallest change necessary to achieve the goal.

### 5. Security Conscious

Don't disable security features for performance.

### 6. Portable When Possible

Unless the opinion is explicitly CPU-specific, keep it portable.

## Future Extensions

Possible additions to the format:

- **Conditional modifications** - based on architecture, Debian version, etc.
- **Opinion inheritance** - base one opinion on another
- **Conflicts** - declare incompatible opinions
- **Dependencies** - opinion requires other opinions
