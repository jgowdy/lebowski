# Package Signing in Lebowski

Lebowski supports GPG-based package signing for authentication and trust verification.

## Overview

Package signing provides:
- **Authentication**: Verify packages were built by a trusted source
- **Integrity**: Detect tampering or corruption
- **Traceability**: Track which machine/user built a package
- **Trust Chain**: Build reputation systems for opinion providers

## Signing Modes

### 1. Auto-Sign (Recommended for Getting Started)

Lebowski automatically generates and manages a GPG key per machine:

```bash
# Enable in config
cat >> ~/.config/lebowski/config.yaml <<EOF
signing:
  enabled: true
  auto_sign: true
EOF

# Or use CLI flag
lebowski build bash --opinion-file bash/xsc.yaml --auto-sign
```

**Key Storage**: `~/.config/lebowski/signing-key/`
**Key Name**: `Lebowski Build (hostname)`
**Key Type**: RSA 4096-bit, no expiration

### 2. User-Provided Key

Use your existing GPG key:

```bash
# Find your key ID
gpg --list-keys

# Configure in ~/.config/lebowski/config.yaml
signing:
  enabled: true
  key_id: "ABCD1234EF567890"

# Or use CLI
lebowski build bash --opinion-file bash/xsc.yaml --sign-key ABCD1234
```

### 3. No Signing (Default)

Packages are unsigned by default for faster local builds.

## Configuration

### Config File (`~/.config/lebowski/config.yaml`)

```yaml
signing:
  # Enable package signing
  enabled: true

  # Auto-generate and use Lebowski signing key
  # Creates ~/.config/lebowski/signing-key/ if not exists
  auto_sign: true

  # Or specify your own GPG key ID
  # key_id: "ABCD1234EF567890"

  # Export public key with packages for verification
  export_public_key: true
```

### CLI Flags

```bash
# Auto-sign with Lebowski key
lebowski build <package> --auto-sign

# Sign with specific key
lebowski build <package> --sign-key ABCD1234

# Sign with key from config
lebowski build <package>  # Uses config.signing settings
```

## Signature Files

After a signed build, you'll find:

```
output/
├── bash_5.1-6_amd64.deb
├── bash_5.1-6_amd64.deb.sig           # Detached GPG signature
├── bash_5.1-6_amd64.lebowski-manifest.json
└── lebowski-public-key.asc            # Public key (if export_public_key: true)
```

## Verifying Signatures

### Verify with GPG

```bash
# Verify signature
gpg --verify bash_5.1-6_amd64.deb.sig bash_5.1-6_amd64.deb

# Import public key first if needed
gpg --import lebowski-public-key.asc
gpg --verify bash_5.1-6_amd64.deb.sig bash_5.1-6_amd64.deb
```

### Verify with Lebowski

```bash
lebowski verify bash_5.1-6_amd64.lebowski-manifest.json
```

The manifest includes signature metadata:

```json
{
  "signature": {
    "key_id": "ABCD1234",
    "fingerprint": "1234 5678 9ABC DEF0 ...",
    "signer_name": "Lebowski Build (hostname)",
    "signer_email": "lebowski-build@hostname",
    "key_created": "2025-10-27",
    "signature_file": "bash_5.1-6_amd64.deb.sig"
  }
}
```

## Key Management

### Generate Lebowski Key (Manual)

```bash
# First build with --auto-sign generates key
lebowski build bash --opinion-file bash/xsc.yaml --auto-sign

# Key stored at ~/.config/lebowski/signing-key/
ls -la ~/.config/lebowski/signing-key/
```

### Export Public Key

```bash
# Export from GPG
gpg --armor --export KEYID > my-public-key.asc

# Or Lebowski does this automatically if export_public_key: true
```

### List Keys

```bash
# List all GPG keys
gpg --list-keys

# Show Lebowski key
gpg --list-keys "Lebowski Build"
```

### Revoke/Delete Key

```bash
# Delete Lebowski key
rm -rf ~/.config/lebowski/signing-key/

# Delete from GPG keyring
gpg --delete-key "Lebowski Build (hostname)"
```

## Trust Levels and Purity

Signing is especially important for opinions with lower purity levels:

| Purity Level | Trust | Should Sign? |
|--------------|-------|--------------|
| pure-compilation | HIGHEST | Optional (flags only) |
| configure-only | HIGH | Recommended |
| debian-patches | MEDIUM-HIGH | Recommended |
| upstream-patches | MEDIUM | **Required** |
| third-party-patches | LOWER | **Required** |
| custom | LOWEST | **Required** |

## Opinion-Level Signing Requirements

Opinions can require signing:

```yaml
# In opinion YAML
verification:
  require_signature: true
  min_key_strength: 4096
```

Lebowski will refuse to build unsigned packages if `require_signature: true`.

## Distribution Workflows

### Personal Use

```bash
# Auto-sign for personal tracking
lebowski build bash --auto-sign
# Key unique to your machine
```

### Team/Organization

```bash
# Use shared key for team
signing:
  enabled: true
  key_id: "TEAM-KEY-ID"

# Or per-builder keys in CI
lebowski build bash --sign-key $CI_GPG_KEY_ID
```

### Public Distribution

```bash
# Official Lebowski opinions repository uses:
signing:
  enabled: true
  key_id: "LEBOWSKI-OFFICIAL-KEY"
  export_public_key: true

# Users verify with:
gpg --import lebowski-public-key.asc
gpg --verify package.deb.sig package.deb
```

## Security Considerations

1. **Key Protection**: Auto-generated keys have no passphrase (for automation).
   Use `key_id` with passphrase-protected keys for sensitive builds.

2. **Key Rotation**: Lebowski keys are permanent. Manually rotate if compromised:
   ```bash
   rm -rf ~/.config/lebowski/signing-key/
   lebowski build bash --auto-sign  # Generates new key
   ```

3. **Trust Chain**: Signing doesn't verify opinion content, only builder identity.
   Always review opinions before building.

4. **GPG Best Practices**:
   - Use 4096-bit RSA keys (Lebowski default)
   - Keep private keys secure
   - Regularly backup key material
   - Use hardware tokens for high-value keys

## Examples

### Example 1: Personal Signed Build

```bash
# Enable auto-sign in config
mkdir -p ~/.config/lebowski
cat > ~/.config/lebowski/config.yaml <<EOF
signing:
  enabled: true
  auto_sign: true
EOF

# Build (auto-signed)
lebowski build nginx --opinion-file nginx/xsc-hardened.yaml

# Verify
gpg --verify /tmp/nginx*.deb.sig /tmp/nginx*.deb
```

### Example 2: Team Signing Key

```bash
# Import team key
gpg --import team-lebowski-key.asc

# Configure
cat > ~/.config/lebowski/config.yaml <<EOF
signing:
  enabled: true
  key_id: "TEAM-KEY-ID"
EOF

# Build (signed with team key)
lebowski build bash --opinion-file bash/xsc.yaml
```

### Example 3: CI/CD Pipeline

```yaml
# .github/workflows/build.yml
- name: Import GPG key
  run: echo "$GPG_PRIVATE_KEY" | gpg --import

- name: Build and sign
  run: |
    lebowski build bash \
      --opinion-file bash/xsc-hardened.yaml \
      --sign-key $GPG_KEY_ID \
      --output-dir ./artifacts

- name: Upload artifacts
  uses: actions/upload-artifact@v3
  with:
    name: signed-packages
    path: |
      artifacts/*.deb
      artifacts/*.sig
      artifacts/lebowski-public-key.asc
```

## Troubleshooting

### "Failed to sign package: gpg: signing failed: No secret key"

Key not found. Check:
```bash
gpg --list-secret-keys
```

### "Permission denied: ~/.config/lebowski/signing-key/"

Fix permissions:
```bash
chmod 700 ~/.config/lebowski/signing-key/
```

### "GPG agent failed"

Restart GPG agent:
```bash
gpgconf --kill gpg-agent
gpgconf --launch gpg-agent
```

## Implementation Status

**Implemented** (2025-10-27):
- ✅ Signing module (`lebowski/signing.py`)
- ✅ Config support (`SigningConfig`)
- ✅ Auto-key generation
- ✅ GPG integration
- ✅ Signature metadata in manifest

**TODO**:
- ⏳ CLI flags (--auto-sign, --sign-key)
- ⏳ Builder integration
- ⏳ Signature verification in `lebowski verify`
- ⏳ Opinion-level signing requirements

## References

- [GPG Manual](https://www.gnupg.org/documentation/manuals/gnupg/)
- [Debian Package Signing](https://wiki.debian.org/SecureApt)
- [Reproducible Builds](https://reproducible-builds.org/)
