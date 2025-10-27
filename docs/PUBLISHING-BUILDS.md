# Publishing Lebowski Builds

When publishing a build, you need to provide a **complete reproducibility bundle** so anyone can verify your binary by rebuilding from scratch.

## Complete Reproducibility Bundle

A published build includes:

1. **Binary artifacts** (.deb files)
2. **Build manifest** (JSON with all metadata)
3. **Opinion file** (YAML configuration)
4. **Lebowski commit** (git hash of build tool)
5. **Opinions commit** (git hash of opinions repo)
6. **Container information** (Dockerfile + base images)
7. **Signatures** (GPG signatures of artifacts)

## Publication Statement

When you publish, you're making this claim:

> "I certify that **Lebowski commit `abc123`** with **opinions commit `def456`** and **opinion `bash/xsc`** produces **`bash_5.1-6_amd64.deb`** with SHA256 `xyz789`."

Anyone can verify this by:

1. Checking out Lebowski at commit `abc123`
2. Checking out opinions at commit `def456`
3. Building `bash` with opinion `bash/xsc`
4. Comparing SHA256 of result

## Publication Package Structure

```
bash_5.1-6_xsc_amd64.tar.gz              # Publication bundle
├── bash_5.1-6_amd64.deb                  # Binary package
├── bash_5.1-6_amd64.deb.sig              # GPG signature
├── bash_5.1-6.lebowski-manifest.json     # Complete manifest
├── REPRODUCIBILITY.md                    # How to reproduce
├── opinion.yaml                          # Opinion file used
├── Dockerfile                            # Container Dockerfile
├── Dockerfile.base                       # Base image Dockerfile (if needed)
└── verification.sh                       # Automated verification script
```

## Example: Publishing a Bash Build

### 1. Build with Complete Metadata

```bash
# Build bash with metadata collection
lebowski build bash \
  --opinion-file opinions/bash/xsc.yaml \
  --output-dir ./publish \
  --auto-sign \
  --capture-provenance
```

This generates:

```
publish/
├── bash_5.1-6_amd64.deb
├── bash_5.1-6_amd64.deb.sig
└── bash_5.1-6.lebowski-manifest.json
```

### 2. Create Reproducibility Bundle

```bash
# Create publication bundle
lebowski publish bash_5.1-6.lebowski-manifest.json \
  --output publish/bash_5.1-6_xsc_amd64.tar.gz
```

This creates a tarball with everything needed for reproduction.

### 3. Publish to Repository

```bash
# Upload to build repository
aws s3 cp publish/bash_5.1-6_xsc_amd64.tar.gz \
  s3://builds.lebowski.org/bash/5.1-6/xsc/

# Or publish to GitHub Releases
gh release create bash-5.1-6-xsc \
  publish/bash_5.1-6_xsc_amd64.tar.gz \
  --notes "Bash 5.1-6 with XSC optimization"
```

## Manifest with Complete Provenance

```json
{
  "lebowski_version": "0.1.0",
  "build_timestamp": "2025-10-27T12:34:56Z",

  "reproducibility": {
    "lebowski_commit": "abc123def456...",
    "lebowski_repo": "https://github.com/jgowdy/lebowski",
    "opinions_commit": "789abc012def...",
    "opinions_repo": "https://github.com/jgowdy/lebowski-opinions",
    "opinion_file": "bash/xsc.yaml",
    "opinion_sha256": "xyz789..."
  },

  "package": {
    "name": "bash",
    "version": "5.1-6",
    "architecture": "amd64",
    "source_package": "bash_5.1-6.dsc",
    "source_sha256": "abc123..."
  },

  "opinion": {
    "name": "xsc",
    "purity_level": "configure-only",
    "file_path": "bash/xsc.yaml",
    "sha256": "xyz789...",
    "content": "version: \"1.0\"\npackage: bash\n..."
  },

  "container": {
    "image": "lebowski/builder:xsc",
    "image_id": "sha256:abc123...",
    "digest": "sha256:def456...",
    "dockerfile": "FROM debian:bookworm-slim\n...",
    "dockerfile_sha256": "sha256:xyz789...",
    "dockerfile_url": "https://github.com/jgowdy/lebowski/blob/abc123/containers/xsc/Dockerfile",

    "base_images": [
      {
        "image": "debian:bookworm-slim",
        "digest": "sha256:base123...",
        "dockerfile_url": "https://github.com/debuerreotype/docker-debian-artifacts/blob/bookworm-slim/Dockerfile"
      }
    ],

    "installed_packages": [
      {"name": "gcc-12", "version": "12.2.0-14", "architecture": "amd64"},
      {"name": "binutils", "version": "2.40-2", "architecture": "amd64"}
    ],

    "toolchain": {
      "gcc_version": "12.2.0",
      "glibc_version": "2.36",
      "binutils_version": "2.40"
    }
  },

  "build": {
    "hostname": "buildserver01",
    "cpu_model": "Intel(R) Xeon(R) Gold 6354",
    "num_cores": 80,
    "kernel_version": "6.1.0-13-amd64"
  },

  "artifacts": [
    {
      "filename": "bash_5.1-6_amd64.deb",
      "sha256": "90d60f9dc7ea25db3bd306e4c32570a3307e3997929015a02e40cc050213ee7c",
      "size": 1445670,
      "type": "deb"
    }
  ],

  "signature": {
    "key_id": "ABCD1234",
    "fingerprint": "1234 5678 9ABC DEF0 ...",
    "signer_name": "Lebowski Official Builder",
    "signer_email": "builder@lebowski.org",
    "public_key_url": "https://builds.lebowski.org/lebowski-public-key.asc"
  }
}
```

## REPRODUCIBILITY.md

The bundle includes instructions for reproduction:

```markdown
# Reproducing bash_5.1-6_amd64.deb

This package was built with Lebowski and can be reproduced bit-for-bit.

## Quick Reproduction

```bash
# Clone Lebowski at specific commit
git clone https://github.com/jgowdy/lebowski
cd lebowski
git checkout abc123def456

# Clone opinions at specific commit
git clone https://github.com/jgowdy/lebowski-opinions
cd lebowski-opinions
git checkout 789abc012def

# Build the package
cd ../build-tool
python3 -m lebowski.cli build bash \
  --opinion-file ../lebowski-opinions/bash/xsc.yaml \
  --output-dir ./verify

# Compare SHA256
sha256sum ./verify/bash_5.1-6_amd64.deb
# Expected: 90d60f9dc7ea25db3bd306e4c32570a3307e3997929015a02e40cc050213ee7c
```

## Automated Verification

```bash
# Extract bundle
tar xzf bash_5.1-6_xsc_amd64.tar.gz
cd bash_5.1-6_xsc_amd64

# Run verification script
./verification.sh
```

## Container Reproduction

To rebuild the exact container environment:

```bash
# Build base image (Debian Bookworm)
docker pull debian:bookworm-slim@sha256:base123...

# Build Lebowski XSC container from Dockerfile
docker build -f Dockerfile -t lebowski/builder:xsc .

# Build package in container
python3 -m lebowski.cli build bash \
  --opinion-file opinion.yaml \
  --container-image lebowski/builder:xsc
```

## Build Details

- **Lebowski version**: 0.1.0
- **Lebowski commit**: abc123def456
- **Opinions commit**: 789abc012def
- **Opinion**: bash/xsc.yaml
- **Container**: lebowski/builder:xsc
- **Build date**: 2025-10-27T12:34:56Z
- **Builder**: buildserver01

## Verification Status

Anyone who successfully reproduces this build can sign this file:

```
Reproduced by: [Your Name]
Date: [Date]
SHA256: 90d60f9dc7ea25db3bd306e4c32570a3307e3997929015a02e40cc050213ee7c
Signature: [GPG signature]
```
```

## verification.sh

Automated script to verify the build:

```bash
#!/bin/bash
# Automated verification script for bash_5.1-6

set -e

MANIFEST="bash_5.1-6.lebowski-manifest.json"
EXPECTED_SHA256="90d60f9dc7ea25db3bd306e4c32570a3307e3997929015a02e40cc050213ee7c"

# Parse manifest
LEBOWSKI_COMMIT=$(jq -r '.reproducibility.lebowski_commit' $MANIFEST)
OPINIONS_COMMIT=$(jq -r '.reproducibility.opinions_commit' $MANIFEST)
OPINION_FILE=$(jq -r '.reproducibility.opinion_file' $MANIFEST)

echo "=== Lebowski Build Verification ==="
echo "Package: bash_5.1-6"
echo "Opinion: $OPINION_FILE"
echo "Lebowski commit: $LEBOWSKI_COMMIT"
echo "Opinions commit: $OPINIONS_COMMIT"
echo ""

# Clone repositories
echo "Cloning Lebowski..."
git clone https://github.com/jgowdy/lebowski /tmp/lebowski-verify
cd /tmp/lebowski-verify
git checkout $LEBOWSKI_COMMIT

echo "Cloning opinions..."
git clone https://github.com/jgowdy/lebowski-opinions
cd lebowski-opinions
git checkout $OPINIONS_COMMIT
cd ..

# Build package
echo "Building package..."
cd build-tool
python3 -m lebowski.cli build bash \
  --opinion-file ../lebowski-opinions/$OPINION_FILE \
  --output-dir /tmp/bash-verify

# Verify SHA256
ACTUAL_SHA256=$(sha256sum /tmp/bash-verify/bash_*.deb | cut -d' ' -f1)

echo ""
echo "=== Verification Result ==="
echo "Expected SHA256: $EXPECTED_SHA256"
echo "Actual SHA256:   $ACTUAL_SHA256"

if [ "$EXPECTED_SHA256" = "$ACTUAL_SHA256" ]; then
    echo ""
    echo "✓ BUILD REPRODUCED SUCCESSFULLY!"
    echo "The binary is bit-for-bit identical."
    exit 0
else
    echo ""
    echo "✗ BUILD VERIFICATION FAILED!"
    echo "The binary differs from the published version."
    exit 1
fi
```

## Publishing Workflow

### Step-by-Step Publication

#### 1. Prepare Build Environment

```bash
# Ensure git repos are clean with no uncommitted changes
cd /path/to/lebowski
git status  # Should be clean

cd /path/to/lebowski-opinions
git status  # Should be clean

# Note the commit hashes
LEBOWSKI_COMMIT=$(git -C /path/to/lebowski rev-parse HEAD)
OPINIONS_COMMIT=$(git -C /path/to/lebowski-opinions rev-parse HEAD)

echo "Lebowski: $LEBOWSKI_COMMIT"
echo "Opinions: $OPINIONS_COMMIT"
```

#### 2. Build Package with Provenance

```bash
cd /path/to/lebowski/build-tool

# Build with full provenance capture
python3 -m lebowski.cli build bash \
  --opinion-file ../lebowski-opinions/bash/xsc.yaml \
  --output-dir ./publish \
  --auto-sign \
  --capture-provenance \
  --reproducible
```

#### 3. Create Publication Bundle

```bash
# Create bundle directory
mkdir -p bundle/bash_5.1-6_xsc_amd64
cd bundle/bash_5.1-6_xsc_amd64

# Copy artifacts
cp ../../publish/bash_*.deb .
cp ../../publish/bash_*.deb.sig .
cp ../../publish/bash_*.lebowski-manifest.json .

# Copy opinion file
cp ../../../lebowski-opinions/bash/xsc.yaml opinion.yaml

# Export Dockerfile
docker history lebowski/builder:xsc --no-trunc --format "{{.CreatedBy}}" > Dockerfile

# Or copy actual Dockerfile
cp /path/to/lebowski/containers/xsc/Dockerfile .

# Generate REPRODUCIBILITY.md
cat > REPRODUCIBILITY.md <<'EOF'
# Reproducing bash_5.1-6_amd64.deb
...
EOF

# Generate verification script
cat > verification.sh <<'EOF'
#!/bin/bash
...
EOF
chmod +x verification.sh

# Create tarball
cd ..
tar czf bash_5.1-6_xsc_amd64.tar.gz bash_5.1-6_xsc_amd64/

echo "Publication bundle created: bash_5.1-6_xsc_amd64.tar.gz"
```

#### 4. Publish to Repository

```bash
# Option 1: AWS S3
aws s3 cp bash_5.1-6_xsc_amd64.tar.gz \
  s3://builds.lebowski.org/bash/5.1-6/xsc/

# Option 2: GitHub Releases
gh release create bash-5.1-6-xsc \
  bash_5.1-6_xsc_amd64.tar.gz \
  --repo jgowdy/lebowski-builds \
  --title "Bash 5.1-6 (XSC)" \
  --notes "Reproducible build with XSC optimization"

# Option 3: IPFS (for decentralized distribution)
ipfs add bash_5.1-6_xsc_amd64.tar.gz
# Returns: QmXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Option 4: Your own web server
rsync -avz bash_5.1-6_xsc_amd64.tar.gz \
  builds@example.com:/var/www/builds/bash/
```

#### 5. Announce Build

```bash
# Create announcement
cat > announcement.txt <<EOF
New Lebowski Build Available
============================

Package: bash 5.1-6 (XSC optimized)
SHA256: 90d60f9dc7ea25db3bd306e4c32570a3307e3997929015a02e40cc050213ee7c

Reproducibility:
- Lebowski: https://github.com/jgowdy/lebowski/commit/$LEBOWSKI_COMMIT
- Opinions: https://github.com/jgowdy/lebowski-opinions/commit/$OPINIONS_COMMIT
- Opinion: bash/xsc.yaml

Download:
https://builds.lebowski.org/bash/5.1-6/xsc/bash_5.1-6_xsc_amd64.tar.gz

Verify signature:
  gpg --verify bash_5.1-6_amd64.deb.sig bash_5.1-6_amd64.deb

Reproduce build:
  See REPRODUCIBILITY.md in bundle
EOF

# Post announcement
# - GitHub Discussions
# - Mailing list
# - Twitter/social media
```

## lebowski publish Command

To automate this, create a `publish` command:

```bash
# Automatically create publication bundle
lebowski publish bash_5.1-6.lebowski-manifest.json \
  --output bash_5.1-6_xsc_amd64.tar.gz \
  --include-dockerfile \
  --include-verification-script

# Upload to S3
lebowski publish bash_5.1-6.lebowski-manifest.json \
  --upload s3://builds.lebowski.org/bash/5.1-6/xsc/

# Create GitHub release
lebowski publish bash_5.1-6.lebowski-manifest.json \
  --github-release bash-5.1-6-xsc \
  --repo jgowdy/lebowski-builds
```

## Verification by Others

Anyone can verify your published build:

### Option 1: Manual Verification

```bash
# Download bundle
wget https://builds.lebowski.org/bash/5.1-6/xsc/bash_5.1-6_xsc_amd64.tar.gz

# Extract
tar xzf bash_5.1-6_xsc_amd64.tar.gz
cd bash_5.1-6_xsc_amd64

# Run verification script
./verification.sh

# Output:
# ✓ BUILD REPRODUCED SUCCESSFULLY!
# The binary is bit-for-bit identical.
```

### Option 2: Automated Verification with Lebowski

```bash
# Verify from URL
lebowski verify-published \
  https://builds.lebowski.org/bash/5.1-6/xsc/bash_5.1-6_xsc_amd64.tar.gz

# Verify from manifest
lebowski verify bash_5.1-6.lebowski-manifest.json \
  --rebuild
```

## Trust Network

Over time, multiple people verify builds and sign them:

```bash
# After successful reproduction
gpg --sign REPRODUCIBILITY.md

# Publish your verification
git commit -am "Verified bash 5.1-6 XSC build"
git push
```

Build trust through attestations:

```json
{
  "package": "bash_5.1-6_xsc_amd64",
  "sha256": "90d60f9dc7ea25db3bd306e4c32570a3307e3997929015a02e40cc050213ee7c",
  "verifications": [
    {
      "verifier": "Alice <alice@example.com>",
      "gpg_key": "ABCD1234",
      "verified_date": "2025-10-28",
      "signature": "..."
    },
    {
      "verifier": "Bob <bob@example.com>",
      "gpg_key": "EFGH5678",
      "verified_date": "2025-10-29",
      "signature": "..."
    }
  ]
}
```

## Benefits

1. **Complete Transparency**: All build inputs are public
2. **Independent Verification**: Anyone can rebuild and confirm
3. **Long-term Reproducibility**: Builds can be reproduced years later
4. **Supply Chain Security**: Detect compromised builds
5. **Trust Building**: Multiple verifications increase confidence

## Example: Full Publication Workflow

```bash
#!/bin/bash
# publish-bash.sh - Complete publication workflow

set -e

PACKAGE="bash"
OPINION="bash/xsc"
VERSION="5.1-6"

# 1. Ensure clean git state
echo "Checking git status..."
cd /path/to/lebowski
LEBOWSKI_COMMIT=$(git rev-parse HEAD)
cd /path/to/lebowski-opinions
OPINIONS_COMMIT=$(git rev-parse HEAD)

# 2. Build with provenance
echo "Building $PACKAGE..."
cd /path/to/lebowski/build-tool
python3 -m lebowski.cli build $PACKAGE \
  --opinion-file ../lebowski-opinions/$OPINION.yaml \
  --output-dir ./publish \
  --auto-sign \
  --capture-provenance

# 3. Create publication bundle
echo "Creating publication bundle..."
lebowski publish ./publish/${PACKAGE}_${VERSION}.lebowski-manifest.json \
  --output ./publish/${PACKAGE}_${VERSION}_xsc_amd64.tar.gz

# 4. Upload to repository
echo "Uploading to S3..."
aws s3 cp ./publish/${PACKAGE}_${VERSION}_xsc_amd64.tar.gz \
  s3://builds.lebowski.org/$PACKAGE/$VERSION/xsc/

# 5. Create GitHub release
echo "Creating GitHub release..."
gh release create ${PACKAGE}-${VERSION}-xsc \
  ./publish/${PACKAGE}_${VERSION}_xsc_amd64.tar.gz \
  --repo jgowdy/lebowski-builds \
  --title "$PACKAGE $VERSION (XSC)" \
  --notes "Lebowski: $LEBOWSKI_COMMIT\nOpinions: $OPINIONS_COMMIT"

echo "Publication complete!"
echo "SHA256: $(sha256sum ./publish/${PACKAGE}_${VERSION}_amd64.deb | cut -d' ' -f1)"
```

## Next Steps

See also:

- [Container Provenance](CONTAINER-PROVENANCE.md) - Detailed container tracking
- [Package Signing](PACKAGE-SIGNING.md) - GPG signing setup
- [Verification](VERIFICATION.md) - Verifying builds
