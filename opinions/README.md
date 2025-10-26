# Lebowski Opinions Repository

This repository contains opinion definitions for Debian packages.

## Structure

```
opinions/
├── linux/              # Linux kernel opinions
├── nginx/              # nginx opinions
├── python3/            # Python opinions
├── redis/              # Redis opinions
└── ...                 # More packages

patches/                # Patch files (if needed)
scripts/                # Build scripts (if needed)
```

## Creating an Opinion

1. Create YAML file in `opinions/<package>/<opinion-name>.yaml`
2. Follow the schema in `/docs/opinion-format.md`
3. Test with `lebowski build <package> --opinion-file <file>`
4. Submit PR

## Opinion Purity Levels

- **pure-compilation**: Only CFLAGS/defines (highest trust)
- **configure-only**: Only build flags (high trust)
- **patches**: Source modifications (lower trust, needs justification)

Prefer higher purity levels when possible.
