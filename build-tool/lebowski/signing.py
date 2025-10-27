"""
Package signing module for Lebowski.

Provides GPG-based package signing with automatic key management.
"""

import subprocess
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class SigningKey:
    """Information about a GPG signing key"""
    key_id: str
    fingerprint: str
    name: str
    email: str
    created: str


class SigningError(Exception):
    """Signing operation failed"""
    pass


class PackageSigner:
    """
    Handles GPG signing of Debian packages.

    Supports:
    - User-provided GPG keys
    - Auto-generated Lebowski signing keys
    - Key management and validation
    """

    # Path to Lebowski's auto-generated key
    LEBOWSKI_KEY_PATH = Path.home() / ".config" / "lebowski" / "signing-key"
    LEBOWSKI_KEY_ID_FILE = LEBOWSKI_KEY_PATH / "key_id.txt"

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def get_or_create_lebowski_key(self) -> SigningKey:
        """
        Get or create Lebowski's auto-generated signing key.

        Returns the key ID to use for signing.
        """
        # Check if we already have a key
        if self.LEBOWSKI_KEY_ID_FILE.exists():
            key_id = self.LEBOWSKI_KEY_ID_FILE.read_text().strip()
            # Verify key still exists
            if self._verify_key_exists(key_id):
                return self._get_key_info(key_id)

        # Generate new key
        return self._generate_lebowski_key()

    def _verify_key_exists(self, key_id: str) -> bool:
        """Check if a GPG key exists"""
        try:
            result = subprocess.run(
                ["gpg", "--list-keys", key_id],
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def _get_key_info(self, key_id: str) -> SigningKey:
        """Get information about a GPG key"""
        try:
            # Get key information using --with-colons format
            result = subprocess.run(
                ["gpg", "--list-keys", "--with-colons", key_id],
                capture_output=True,
                text=True,
                check=True,
            )

            # Parse colon-separated output
            lines = result.stdout.strip().split('\n')

            fingerprint = None
            name = None
            email = None
            created = None

            for line in lines:
                fields = line.split(':')
                if fields[0] == 'fpr':
                    fingerprint = fields[9]
                elif fields[0] == 'uid':
                    # UID format: "Name <email>"
                    uid = fields[9]
                    if '<' in uid and '>' in uid:
                        name = uid.split('<')[0].strip()
                        email = uid.split('<')[1].split('>')[0].strip()
                    else:
                        name = uid
                        email = ""
                elif fields[0] == 'pub':
                    created = fields[5]

            return SigningKey(
                key_id=key_id,
                fingerprint=fingerprint or key_id,
                name=name or "Unknown",
                email=email or "",
                created=created or "unknown",
            )
        except subprocess.CalledProcessError as e:
            raise SigningError(f"Failed to get key info for {key_id}: {e}")

    def _generate_lebowski_key(self) -> SigningKey:
        """Generate a new Lebowski signing key"""
        import socket
        import os

        hostname = socket.gethostname()
        username = os.getenv('USER', 'user')

        # Create config directory
        self.LEBOWSKI_KEY_PATH.mkdir(parents=True, exist_ok=True)

        # Generate key with batch mode
        batch_script = f"""
Key-Type: RSA
Key-Length: 4096
Name-Real: Lebowski Build ({hostname})
Name-Email: lebowski-build@{hostname}
Name-Comment: Auto-generated key for Lebowski package signing
Expire-Date: 0
%no-protection
%commit
"""

        if self.verbose:
            print("Generating new Lebowski signing key...")
            print(f"  Machine: {hostname}")
            print(f"  User: {username}")

        try:
            # Generate key
            result = subprocess.run(
                ["gpg", "--batch", "--generate-key"],
                input=batch_script,
                capture_output=True,
                text=True,
                check=True,
            )

            if self.verbose:
                print(result.stderr)

            # Extract key ID from output
            # Look for line like: "gpg: key ABCD1234 marked as ultimately trusted"
            key_id = None
            for line in result.stderr.split('\n'):
                if 'key' in line and 'marked as ultimately trusted' in line:
                    # Extract key ID
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == 'key' and i + 1 < len(parts):
                            key_id = parts[i + 1]
                            break
                    break

            if not key_id:
                raise SigningError("Failed to extract key ID from gpg output")

            # Save key ID for future use
            self.LEBOWSKI_KEY_ID_FILE.write_text(key_id)

            if self.verbose:
                print(f"✓ Generated key: {key_id}")

            return self._get_key_info(key_id)

        except subprocess.CalledProcessError as e:
            raise SigningError(f"Failed to generate GPG key: {e.stderr}")

    def sign_package(self, deb_path: Path, key_id: str) -> Tuple[Path, str]:
        """
        Sign a Debian package with GPG.

        Args:
            deb_path: Path to .deb file
            key_id: GPG key ID to sign with

        Returns:
            Tuple of (signature_path, signature_content)
        """
        if not deb_path.exists():
            raise SigningError(f"Package not found: {deb_path}")

        # Create detached signature
        sig_path = deb_path.parent / f"{deb_path.name}.sig"

        if self.verbose:
            print(f"Signing {deb_path.name} with key {key_id}...")

        try:
            # Create detached signature
            subprocess.run(
                [
                    "gpg",
                    "--default-key", key_id,
                    "--detach-sign",
                    "--armor",
                    "--output", str(sig_path),
                    str(deb_path)
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            # Read signature
            signature_content = sig_path.read_text()

            if self.verbose:
                print(f"✓ Signature created: {sig_path.name}")

            return sig_path, signature_content

        except subprocess.CalledProcessError as e:
            raise SigningError(f"Failed to sign package: {e.stderr}")

    def verify_signature(self, deb_path: Path, sig_path: Path) -> bool:
        """
        Verify a package signature.

        Returns True if signature is valid, False otherwise.
        """
        try:
            result = subprocess.run(
                ["gpg", "--verify", str(sig_path), str(deb_path)],
                capture_output=True,
                text=True,
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def sign_changes_file(self, changes_path: Path, key_id: str) -> bool:
        """
        Sign a .changes file (used for Debian uploads).

        Args:
            changes_path: Path to .changes file
            key_id: GPG key ID to sign with

        Returns:
            True if signing succeeded
        """
        if not changes_path.exists():
            return False

        try:
            subprocess.run(
                ["debsign", "-k", key_id, str(changes_path)],
                capture_output=True,
                text=True,
                check=True,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    @staticmethod
    def get_signature_metadata(key: SigningKey) -> Dict[str, str]:
        """
        Generate signature metadata for manifest.

        Returns dict suitable for inclusion in build manifest.
        """
        return {
            "key_id": key.key_id,
            "fingerprint": key.fingerprint,
            "signer_name": key.name,
            "signer_email": key.email,
            "key_created": key.created,
        }

    @staticmethod
    def export_public_key(key_id: str, output_path: Path) -> None:
        """Export public key to file for distribution"""
        try:
            result = subprocess.run(
                ["gpg", "--armor", "--export", key_id],
                capture_output=True,
                text=True,
                check=True,
            )
            output_path.write_text(result.stdout)
        except subprocess.CalledProcessError as e:
            raise SigningError(f"Failed to export public key: {e}")
