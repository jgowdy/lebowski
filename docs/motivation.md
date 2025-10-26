# Why Lebowski?

## The Historical Context

### FreeBSD Ports: Control at a Cost

FreeBSD ports were designed in an era of weak hardware where custom optimization mattered:

```bash
cd /usr/ports/www/nginx
make config      # Select build options via menu
make install     # Build and install with your choices
```

Simple. User-friendly. Powerful. **But slow.**

Compiling everything from source is:
- Time-consuming (hours to build a full system)
- Resource-intensive (high CPU/memory usage)
- Impractical for many users in modern environments

FreeBSD over-optimized for source builds.

### Linux: Speed at the Cost of Control

Linux distributions went the opposite direction - heavily optimized for binary packages:
- Fast installation (seconds instead of hours)
- Low resource usage
- Consistent, tested builds

But this removed user control:
- One-size-fits-all build flags
- Can't easily customize features
- Stuck with maintainer's decisions

Linux over-optimized for binary convenience.

## The Debian Gap

In contrast, Debian makes building from source unnecessarily painful:

1. **Complex Process**
   - `apt-get source package`
   - Edit debian/rules
   - Navigate complex debian/ directory structure
   - Handle build dependencies manually
   - Deal with quilt patches
   - Build with dpkg-buildpackage
   - Install the resulting .deb

2. **Expertise Required**
   - Understanding Debian packaging internals
   - Knowledge of debian/rules syntax
   - Familiarity with dpkg build tools
   - Understanding patch systems (quilt, etc.)

3. **Maintainability Nightmare**
   - Updates require repeating the entire process
   - Your changes might break with new upstream versions
   - No easy way to share your build configuration
   - Security updates become manual work

## The Lebowski Philosophy

**The best of both worlds: Binary speed + User control**

### The Middle Ground

Lebowski provides:
- **Pre-built binary packages** (fast installation, like Linux)
- **Multiple variants** (user choice, like FreeBSD ports)
- **No local compilation required** (practical for modern use)

Instead of choosing between:
- One official binary (fast, no control)
- Building from source (slow, full control)

Lebowski offers:
- Multiple pre-built binaries representing different "opinions"

### User Experience

**Debian's official packages represent Debian's opinion. Users should be able to easily express their own opinions without compiling.**

- **Easy Discovery**: Browse available build variants
- **Simple Installation**: `lebowski install nginx-minimal` or `lebowski install python3-znver3`
- **Fast**: Binary packages install in seconds
- **Declarative**: Variant definitions are version-controlled and shareable
- **Automatic Updates**: Security updates work just like official packages
- **Community Driven**: Anyone can contribute variant definitions
- **Optional Local Builds**: Advanced users can still build locally if desired

## Inspiration

- **FreeBSD Ports**: User-friendly source builds with options
- **Gentoo**: USE flags and customization
- **Arch AUR**: Community-contributed build recipes
- **Nix**: Declarative package definitions

## What Lebowski Is NOT

- Not a replacement for official Debian packages
- Not a fork of Debian
- Not a new package manager
- Not trying to fragment the ecosystem

## What Lebowski IS

- A complement to official Debian
- A way to exercise user choice
- A community of different opinions
- Built on standard Debian tools (APT, .deb format)
- An acknowledgment that one size doesn't fit all

## The Name

> "Yeah, well, that's just like, your opinion, man." - The Dude

The official Debian packages represent the Debian project's well-considered opinions. Lebowski acknowledges that users might have different, equally valid opinions about how their software should be built. Neither opinion is wrong - they're just different.

Just like The Dude.
