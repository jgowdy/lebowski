# Lebowski Build Receipts

A **build receipt** is a compact, cryptographically-signed proof of what was built. You can paste a receipt anywhere (email, chat, website) and anyone can verify it by rebuilding.

## What is a Build Receipt?

Think of it like a blockchain transaction receipt or a git commit. It's a concise statement:

> "I built **bash 5.1-6** using **Lebowski@abc123** with **opinions@def456** and opinion **bash/xsc**, resulting in SHA256 **xyz789**. Signed: Alice"

Anyone can verify this claim by:

```bash
lebowski verify-receipt < receipt.txt
```

## Receipt Format

### Compact Format (Human-Readable)

```
===== LEBOWSKI BUILD RECEIPT =====
Package: bash 5.1-6 amd64
Opinion: bash/xsc (purity: configure-only)
Result: bash_5.1-6_amd64.deb
SHA256: 90d60f9dc7ea25db3bd306e4c32570a3307e3997929015a02e40cc050213ee7c

Reproducibility:
  Lebowski: https://github.com/jgowdy/lebowski @ abc123def456
  Opinions: https://github.com/jgowdy/lebowski-opinions @ 789abc012def
  Container: lebowski/builder:xsc @ sha256:container123...

Built: 2025-10-27T12:34:56Z
Builder: buildserver01 (alice@example.com)

Signature:
-----BEGIN PGP SIGNATURE-----
iQIzBAABCAAdFiEE...
=abc1
-----END PGP SIGNATURE-----
===== END RECEIPT =====
```

### JSON Format (Machine-Readable)

```json
{
  "lebowski_receipt_version": "1.0",
  "package": {
    "name": "bash",
    "version": "5.1-6",
    "architecture": "amd64",
    "source_sha256": "source123..."
  },
  "opinion": {
    "file": "bash/xsc.yaml",
    "sha256": "opinion123...",
    "purity_level": "configure-only"
  },
  "artifacts": [
    {
      "filename": "bash_5.1-6_amd64.deb",
      "sha256": "90d60f9dc7ea25db3bd306e4c32570a3307e3997929015a02e40cc050213ee7c",
      "size": 1445670
    }
  ],
  "reproducibility": {
    "lebowski_repo": "https://github.com/jgowdy/lebowski",
    "lebowski_commit": "abc123def456",
    "opinions_repo": "https://github.com/jgowdy/lebowski-opinions",
    "opinions_commit": "789abc012def",
    "container_image": "lebowski/builder:xsc",
    "container_digest": "sha256:container123..."
  },
  "build": {
    "timestamp": "2025-10-27T12:34:56Z",
    "hostname": "buildserver01",
    "builder_email": "alice@example.com"
  },
  "signature": {
    "pgp": "-----BEGIN PGP SIGNATURE-----\niQIzBAABCAAdFiEE...\n-----END PGP SIGNATURE-----"
  }
}
```

### QR Code Format (For Physical Distribution)

Receipt can be encoded as QR code:

```
lebowski://verify?pkg=bash&ver=5.1-6&sha=90d60f9dc7ea...&sig=...
```

Scan with phone to verify on mobile device.

## Creating a Receipt

### Automatic (After Build)

```bash
# Build package - receipt is automatically generated
lebowski build bash -o xsc --auto-sign

# Receipt saved to:
# output/bash_5.1-6.lebowski-receipt.txt
# output/bash_5.1-6.lebowski-receipt.json
```

### Manual (From Manifest)

```bash
# Generate receipt from existing manifest
lebowski receipt bash_5.1-6.lebowski-manifest.json \
  --output bash_5.1-6.receipt.txt \
  --format text

# Generate QR code
lebowski receipt bash_5.1-6.lebowski-manifest.json \
  --format qr \
  --output bash_5.1-6_qr.png
```

## Verifying a Receipt

### From File

```bash
# Verify from text file
lebowski verify-receipt bash_5.1-6.receipt.txt

# Output:
# Verifying receipt for bash 5.1-6...
# ✓ GPG signature valid (Alice <alice@example.com>)
# ✓ Lebowski repository cloned
# ✓ Opinions repository cloned
# ✓ Building package...
# ✓ SHA256 matches: 90d60f9dc7ea25db...
#
# BUILD VERIFIED! The receipt is valid.
```

### From Stdin (Paste Receipt)

```bash
# Paste receipt from clipboard
lebowski verify-receipt

# Paste receipt here (Ctrl+D when done):
===== LEBOWSKI BUILD RECEIPT =====
Package: bash 5.1-6 amd64
...
===== END RECEIPT =====

# Verification starts automatically
```

### From URL

```bash
# Verify from web URL
lebowski verify-receipt https://builds.bx.ee/receipts/bash-5.1-6-xsc.txt

# Verify from GitHub Gist
lebowski verify-receipt https://gist.githubusercontent.com/alice/12345/receipt.txt
```

### From QR Code

```bash
# Verify from QR code image
lebowski verify-receipt --qr qr_code.png

# Or scan with webcam
lebowski verify-receipt --scan-qr
```

## Example Receipt

```
===== LEBOWSKI BUILD RECEIPT =====
Package: bash 5.1-6 amd64
Opinion: bash/xsc (purity: configure-only)
Result: bash_5.1-6_amd64.deb
SHA256: 90d60f9dc7ea25db3bd306e4c32570a3307e3997929015a02e40cc050213ee7c
Size: 1445670 bytes (1.4 MB)

Description:
  Bash built with XSC toolchain for zero-syscall operation.
  Uses ring-based syscalls instead of traditional syscall instructions.

Reproducibility:
  Lebowski: https://github.com/jgowdy/lebowski
            commit: abc123def456789abcdef0123456789abcdef01

  Opinions: https://github.com/jgowdy/lebowski-opinions
            commit: 789abc012def345678901234567890abcdef12

  Opinion file: bash/xsc.yaml
  Opinion SHA256: xyz789abc...

  Container: lebowski/builder:xsc
  Digest: sha256:container123456789abcdef...

Build Environment:
  Date: 2025-10-27 12:34:56 UTC
  Hostname: buildserver01
  Builder: Alice <alice@example.com>
  CPU: Intel(R) Xeon(R) Gold 6354 (80 cores)
  Toolchain: GCC 12.2.0, glibc 2.36

Verification:
  To reproduce this build and verify the SHA256:

  $ lebowski verify-receipt bash_5.1-6.receipt.txt

  Or manually:

  $ git clone https://github.com/jgowdy/lebowski && cd lebowski
  $ git checkout abc123def456789abcdef0123456789abcdef01
  $ git clone https://github.com/jgowdy/lebowski-opinions
  $ cd lebowski-opinions && git checkout 789abc012def345678901234567890abcdef12 && cd ..
  $ cd build-tool
  $ python3 -m lebowski.cli build bash --opinion-file ../lebowski-opinions/bash/xsc.yaml
  $ sha256sum output/bash_5.1-6_amd64.deb

  Expected: 90d60f9dc7ea25db3bd306e4c32570a3307e3997929015a02e40cc050213ee7c

Signature:
-----BEGIN PGP SIGNATURE-----
iQIzBAABCAAdFiEEABCDEF1234567890ABCDEFGHIJKLFiEEABCDEF12345678
90ABCDEFGHIJKLBQQCgNQAAPoJEABCDEF1234567890ABCDEFGHIJKLdRwP/2x
j5eN8kYqGzWmK7VnD0hZ4rPtYwQ8F3mL+K9xB2aC1dE5fT6gH8iJ7jK0lL1mM
2nN3oO4pP5qQ6rR7sS8tT9uU0vV1wW2xX3yY4zZ5A0aB1bC2cD3dE4eF5fF6g
...
=abc1
-----END PGP SIGNATURE-----
===== END RECEIPT =====
```

## Receipt Components

### Essential Information

1. **Package identity**: name, version, architecture
2. **Opinion used**: file path, SHA256, purity level
3. **Result SHA256**: The binary's hash (proof of output)
4. **Reproducibility info**: git commits, container digest
5. **Signature**: GPG signature of entire receipt

### Optional Information

6. Build timestamp
7. Builder identity
8. Build machine info
9. Description
10. Verification instructions

## Cryptographic Properties

### Receipt Integrity

Receipt is signed with GPG, ensuring:

- **Authenticity**: Came from claimed builder
- **Integrity**: Has not been tampered with
- **Non-repudiation**: Builder can't deny creating it

### Verification Chain

```
Receipt → Verification → Rebuild → SHA256 Match
   ↓                                      ↓
GPG Signature Valid               Proof of Correctness
```

If both verification steps pass:

1. **Signature valid** → Receipt is authentic
2. **SHA256 matches** → Binary is correctly built

## Use Cases

### 1. Quick Verification

```bash
# Someone sends you a receipt
cat bash-receipt.txt | lebowski verify-receipt

# Automatically rebuilds and verifies
```

### 2. Build Attestation

```bash
# Build and generate receipt
lebowski build bash -o xsc --auto-sign

# Publish receipt
cat output/bash_5.1-6.receipt.txt | gh gist create \
  --desc "Bash 5.1-6 XSC build receipt" \
  --public

# Share the gist URL - anyone can verify
```

### 3. Supply Chain Security

```bash
# Company policy: all packages must have valid receipts

# CI/CD generates receipt for every build
lebowski build nginx -o production --auto-sign

# Deployment system verifies receipt before installing
lebowski verify-receipt nginx.receipt.txt && \
  dpkg -i nginx*.deb
```

### 4. Community Trust

```bash
# Multiple people verify and counter-sign
lebowski verify-receipt bash.receipt.txt --counter-sign

# Creates trust network:
# - Alice built it
# - Bob verified it
# - Charlie verified it
# → High confidence it's correct
```

## Receipt Distribution

### GitHub Gists

```bash
# Create public gist with receipt
cat bash_5.1-6.receipt.txt | gh gist create \
  --desc "Bash 5.1-6 XSC build" \
  --filename bash_5.1-6.receipt.txt \
  --public

# Returns URL like:
# https://gist.github.com/alice/abc123...

# Anyone can verify:
lebowski verify-receipt https://gist.githubusercontent.com/alice/abc123.../receipt.txt
```

### Website/Blog

```html
<!-- Embed receipt in webpage -->
<pre class="lebowski-receipt">
===== LEBOWSKI BUILD RECEIPT =====
Package: bash 5.1-6 amd64
...
===== END RECEIPT =====
</pre>

<!-- Add verify button -->
<button onclick="verifyReceipt()">Verify This Build</button>
```

### Social Media

```bash
# Tweet receipt (if short enough)
lebowski receipt bash.manifest.json --format compact | \
  twitter post

# Or link to gist
```

### QR Codes (Physical Distribution)

```bash
# Generate QR code
lebowski receipt bash.manifest.json \
  --format qr \
  --output bash_qr.png

# Print on CD/USB packaging
# Users scan to verify before installing
```

## Implementation

### Receipt Generator Module

```python
# lebowski/receipt.py

import json
import gnupg
from typing import Dict
from datetime import datetime

class ReceiptGenerator:
    """Generate build receipts from manifests"""

    def __init__(self, manifest_path: str):
        self.manifest = self._load_manifest(manifest_path)
        self.gpg = gnupg.GPG()

    def generate_text_receipt(self, sign_key: str = None) -> str:
        """Generate human-readable text receipt"""

        receipt = f"""===== LEBOWSKI BUILD RECEIPT =====
Package: {self.manifest['package']['name']} {self.manifest['package']['version']} {self.manifest['package']['architecture']}
Opinion: {self.manifest['opinion']['name']} (purity: {self.manifest['opinion']['purity_level']})
Result: {self.manifest['artifacts'][0]['filename']}
SHA256: {self.manifest['artifacts'][0]['sha256']}
Size: {self.manifest['artifacts'][0]['size']} bytes

Reproducibility:
  Lebowski: {self.manifest['reproducibility']['lebowski_repo']}
            commit: {self.manifest['reproducibility']['lebowski_commit']}

  Opinions: {self.manifest['reproducibility']['opinions_repo']}
            commit: {self.manifest['reproducibility']['opinions_commit']}

  Container: {self.manifest['container']['image']}
  Digest: {self.manifest['container']['digest']}

Built: {self.manifest['build_timestamp']}
Builder: {self.manifest['build']['builder_email']}

Verification:
  $ lebowski verify-receipt <receipt_file>
"""

        # Sign receipt
        if sign_key:
            signed = self.gpg.sign(receipt, keyid=sign_key, clearsign=True)
            receipt = str(signed)

        receipt += "\n===== END RECEIPT ====="
        return receipt

    def generate_json_receipt(self) -> Dict:
        """Generate machine-readable JSON receipt"""
        return {
            "lebowski_receipt_version": "1.0",
            "package": self.manifest['package'],
            "opinion": self.manifest['opinion'],
            "artifacts": self.manifest['artifacts'],
            "reproducibility": self.manifest['reproducibility'],
            "build": self.manifest['build'],
            "signature": self.manifest.get('signature', {})
        }

    def generate_qr_code(self, output_path: str):
        """Generate QR code with receipt data"""
        import qrcode

        # Create compact URL-encoded receipt
        pkg = self.manifest['package']['name']
        ver = self.manifest['package']['version']
        sha = self.manifest['artifacts'][0]['sha256'][:16]  # First 16 chars

        url = f"lebowski://verify?pkg={pkg}&ver={ver}&sha={sha}"

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        img.save(output_path)
```

### Receipt Verifier Module

```python
# lebowski/receipt_verifier.py

import re
import subprocess
from typing import Tuple, Optional

class ReceiptVerifier:
    """Verify build receipts"""

    def verify_receipt(self, receipt_text: str) -> Tuple[bool, str]:
        """
        Verify a build receipt by rebuilding and comparing SHA256.

        Returns: (success, message)
        """

        # Parse receipt
        receipt = self._parse_receipt(receipt_text)

        # Verify GPG signature
        if not self._verify_signature(receipt_text):
            return (False, "GPG signature verification failed")

        print("✓ GPG signature valid")

        # Clone repositories
        print("Cloning repositories...")
        self._clone_repo(receipt['lebowski_repo'], receipt['lebowski_commit'], '/tmp/lebowski-verify')
        self._clone_repo(receipt['opinions_repo'], receipt['opinions_commit'], '/tmp/opinions-verify')

        # Build package
        print("Building package...")
        result = subprocess.run([
            'python3', '-m', 'lebowski.cli', 'build',
            receipt['package_name'],
            '--opinion-file', f"/tmp/opinions-verify/{receipt['opinion_file']}",
            '--output-dir', '/tmp/receipt-verify-output'
        ], cwd='/tmp/lebowski-verify/build-tool', capture_output=True)

        if result.returncode != 0:
            return (False, f"Build failed: {result.stderr}")

        # Compare SHA256
        import hashlib
        with open(f"/tmp/receipt-verify-output/{receipt['artifact_filename']}", 'rb') as f:
            actual_sha = hashlib.sha256(f.read()).hexdigest()

        if actual_sha == receipt['expected_sha256']:
            return (True, "BUILD VERIFIED! The receipt is valid.")
        else:
            return (False, f"SHA256 mismatch: {actual_sha} != {receipt['expected_sha256']}")

    def _parse_receipt(self, text: str) -> Dict:
        """Parse receipt text"""
        # Extract key information using regex
        package_match = re.search(r'Package: (\S+) (\S+) (\S+)', text)
        sha_match = re.search(r'SHA256: ([0-9a-f]{64})', text)
        lebowski_commit_match = re.search(r'commit: ([0-9a-f]{40})', text)

        return {
            'package_name': package_match.group(1),
            'expected_sha256': sha_match.group(1),
            'lebowski_commit': lebowski_commit_match.group(1),
            # ... extract other fields
        }

    def _verify_signature(self, text: str) -> bool:
        """Verify GPG signature"""
        gpg = gnupg.GPG()
        verified = gpg.verify(text)
        return verified.valid
```

### CLI Integration

```python
# In lebowski/cli.py

@cli.command()
@click.argument('manifest_path')
@click.option('--format', type=click.Choice(['text', 'json', 'qr']), default='text')
@click.option('--output', help='Output file path')
@click.option('--sign-key', help='GPG key ID to sign receipt')
def receipt(manifest_path, format, output, sign_key):
    """Generate build receipt from manifest"""
    from .receipt import ReceiptGenerator

    gen = ReceiptGenerator(manifest_path)

    if format == 'text':
        receipt_text = gen.generate_text_receipt(sign_key)
        if output:
            with open(output, 'w') as f:
                f.write(receipt_text)
        else:
            print(receipt_text)

    elif format == 'json':
        receipt_json = gen.generate_json_receipt()
        if output:
            with open(output, 'w') as f:
                json.dump(receipt_json, f, indent=2)
        else:
            print(json.dumps(receipt_json, indent=2))

    elif format == 'qr':
        if not output:
            output = manifest_path.replace('.json', '_qr.png')
        gen.generate_qr_code(output)
        print(f"QR code saved to {output}")


@cli.command()
@click.argument('receipt_source', required=False)
@click.option('--qr', help='Verify from QR code image')
@click.option('--scan-qr', is_flag=True, help='Scan QR code from webcam')
def verify_receipt(receipt_source, qr, scan_qr):
    """Verify a build receipt"""
    from .receipt_verifier import ReceiptVerifier

    # Get receipt text
    if receipt_source:
        if receipt_source.startswith('http'):
            # Download from URL
            import requests
            receipt_text = requests.get(receipt_source).text
        else:
            # Read from file
            with open(receipt_source) as f:
                receipt_text = f.read()
    else:
        # Read from stdin
        print("Paste receipt (Ctrl+D when done):")
        receipt_text = sys.stdin.read()

    # Verify
    verifier = ReceiptVerifier()
    success, message = verifier.verify_receipt(receipt_text)

    if success:
        print(f"✓ {message}")
        sys.exit(0)
    else:
        print(f"✗ {message}")
        sys.exit(1)
```

## Benefits

1. **Compact**: Can paste in chat/email/social media
2. **Verifiable**: Anyone can verify by rebuilding
3. **Signed**: Cryptographically authenticated
4. **Shareable**: Easy to distribute and verify
5. **Human-Readable**: Not just machine data
6. **Scannable**: QR codes for physical distribution

## Comparison to Other Systems

| System | Receipt Type | Verification |
|--------|--------------|--------------|
| Lebowski | Build receipt | Rebuild + compare |
| Git | Commit hash | Clone + checkout |
| Blockchain | Transaction | Verify signature |
| Package managers | Checksums only | Download + compare (no rebuild) |

Lebowski receipts provide **stronger guarantees** than package managers because you rebuild from source, not just check a hash.

## Next Steps

See also:

- [Publishing Builds](PUBLISHING-BUILDS.md) - Full publication workflow
- [Container Provenance](CONTAINER-PROVENANCE.md) - Container tracking
- [Package Signing](PACKAGE-SIGNING.md) - GPG signing
