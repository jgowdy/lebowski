# Lebowski Design Document

## Overview

Lebowski enables users to easily install Debian packages built with custom configurations, patches, and features that differ from official Debian packages.

## Core Concepts

### Package Variants

A "variant" is a version of a Debian package built with different:
- **Compilation flags** (e.g., different optimization levels, CPU-specific optimizations)
- **Feature flags** (e.g., enabling/disabling optional features)
- **Patches** (e.g., custom patches, backports, experimental features)
- **Build decisions** (e.g., different dependencies, split packages differently)

### User Opinions

Each variant represents an "opinion" - a set of decisions about how a package should be built. Users can choose the variant that matches their opinion/needs.

## Architecture (To Be Defined)

### Key Components

1. **Build System**
   - Takes Debian source packages
   - Applies custom patches/configurations
   - Builds packages with specified flags
   - Signs packages

2. **Repository System**
   - Hosts built packages
   - Provides APT repository interface
   - Manages multiple variants of same package

3. **Client Tools**
   - Helps users discover available variants
   - Simplifies installation and configuration
   - Manages APT sources

4. **Variant Definitions**
   - Declarative format for defining build variants
   - Version controlled configurations
   - Community contributions

## Technical Approach (To Be Defined)

### Build Infrastructure

Options to consider:
- Local building on user machines
- Centralized build farm
- Distributed/community builds
- Hybrid approach

### Package Distribution

- APT repository hosting
- Variant naming scheme
- Dependency resolution
- Update management

### Security Considerations

- Package signing
- Build reproducibility
- Audit trails
- Trust model

## Open Questions

1. How are variants defined and version controlled?
2. Who can contribute variant definitions?
3. How to ensure security and trust?
4. Local builds vs centralized build farm?
5. How to handle dependency conflicts between variants?
6. Naming convention for variants?
7. How to prevent version conflicts with official packages?

## Next Steps

- [ ] Define variant specification format
- [ ] Design repository structure
- [ ] Prototype build system
- [ ] Design client tool UX
- [ ] Define security/trust model
