# Container Provenance in Lebowski

When Lebowski uses a container for building, the container's Dockerfile and base images become part of the build recipe. This ensures **complete reproducibility** - anyone can rebuild the exact same environment from scratch.

## Why Container Provenance Matters

A reproducible build requires two things:

1. **Build recipe** (opinion + source package)
2. **Build environment** (container + all dependencies)

Without tracking the container environment, we can't guarantee true reproducibility. The same opinion might produce different binaries if the toolchain version changes.

## What Gets Tracked

### 1. Container Image Information

```json
{
  "container": {
    "image": "lebowski/builder:xsc",
    "image_id": "sha256:abc123...",
    "digest": "sha256:def456...",
    "created": "2025-10-20T15:30:00Z",
    "architecture": "amd64",
    "os": "linux"
  }
}
```

### 2. Dockerfile

The complete Dockerfile used to build the container:

```json
{
  "container": {
    "dockerfile": "FROM debian:bookworm-slim\n\nRUN apt-get update && apt-get install -y \\\n    build-essential \\\n    gcc-12 \\\n    ...",
    "dockerfile_sha256": "abc123..."
  }
}
```

### 3. Base Image Chain

All parent images in the dependency chain:

```json
{
  "container": {
    "base_images": [
      {
        "image": "debian:bookworm-slim",
        "digest": "sha256:xyz789...",
        "created": "2025-10-15T10:00:00Z"
      }
    ]
  }
}
```

### 4. Installed Packages

All packages installed in the container:

```json
{
  "container": {
    "installed_packages": [
      {"name": "gcc-12", "version": "12.2.0-14", "architecture": "amd64"},
      {"name": "binutils", "version": "2.40-2", "architecture": "amd64"},
      ...
    ]
  }
}
```

## Complete Manifest Example

```json
{
  "lebowski_version": "0.1.0",
  "build_timestamp": "2025-10-27T12:34:56Z",
  "package": {
    "name": "bash",
    "version": "5.1-6",
    "architecture": "amd64"
  },
  "opinion": {
    "name": "xsc",
    "sha256": "abc123...",
    "content": "version: 1.0\npackage: bash\n..."
  },
  "container": {
    "image": "lebowski/builder:xsc",
    "image_id": "sha256:abc123...",
    "digest": "sha256:def456...",
    "created": "2025-10-20T15:30:00Z",
    "architecture": "amd64",
    "os": "linux",

    "dockerfile": "FROM debian:bookworm-slim\n...",
    "dockerfile_sha256": "sha256:xyz789...",
    "dockerfile_url": "https://github.com/jgowdy/lebowski/blob/main/containers/xsc/Dockerfile",

    "base_images": [
      {
        "image": "debian:bookworm-slim",
        "digest": "sha256:base123...",
        "created": "2025-10-15T10:00:00Z"
      }
    ],

    "installed_packages": [
      {"name": "gcc-12", "version": "12.2.0-14", "architecture": "amd64"},
      {"name": "binutils", "version": "2.40-2", "architecture": "amd64"},
      {"name": "make", "version": "4.3-4.1", "architecture": "amd64"}
    ],

    "toolchain": {
      "gcc_version": "12.2.0",
      "glibc_version": "2.36",
      "binutils_version": "2.40",
      "make_version": "4.3"
    }
  },
  "build": {
    "machine": "buildserver01",
    "cpu_model": "Intel(R) Xeon(R) Gold 6354",
    "num_cores": 80,
    "total_memory": "512GB"
  },
  "artifacts": [
    {
      "filename": "bash_5.1-6_amd64.deb",
      "sha256": "def456...",
      "size": 1445670
    }
  ],
  "signature": {
    "key_id": "ABCD1234",
    "fingerprint": "1234 5678 9ABC DEF0 ...",
    "signer_name": "Lebowski Build (buildserver01)"
  }
}
```

## Implementation

### 1. Container Inspector Module

```python
# lebowski/container_inspector.py

import docker
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class ContainerInfo:
    """Complete information about a container image"""
    image: str
    image_id: str
    digest: str
    created: str
    architecture: str
    os: str
    dockerfile: Optional[str]
    dockerfile_sha256: Optional[str]
    base_images: List[Dict]
    installed_packages: List[Dict]
    toolchain: Dict

class ContainerInspector:
    """Extract provenance information from Docker containers"""

    def __init__(self):
        self.client = docker.from_env()

    def inspect_image(self, image_name: str) -> ContainerInfo:
        """Get complete information about a container image"""
        image = self.client.images.get(image_name)

        # Get basic image info
        image_info = {
            'image': image_name,
            'image_id': image.id,
            'digest': image.attrs['RepoDigests'][0] if image.attrs.get('RepoDigests') else None,
            'created': image.attrs['Created'],
            'architecture': image.attrs['Architecture'],
            'os': image.attrs['Os']
        }

        # Get Dockerfile if available
        dockerfile = self._get_dockerfile(image)

        # Get base image chain
        base_images = self._get_base_images(image)

        # Get installed packages
        packages = self._get_installed_packages(image_name)

        # Get toolchain versions
        toolchain = self._get_toolchain_info(image_name)

        return ContainerInfo(
            **image_info,
            dockerfile=dockerfile,
            dockerfile_sha256=self._sha256(dockerfile) if dockerfile else None,
            base_images=base_images,
            installed_packages=packages,
            toolchain=toolchain
        )

    def _get_dockerfile(self, image) -> Optional[str]:
        """Extract Dockerfile from image labels or build history"""
        # Check if Dockerfile is in labels
        labels = image.attrs['Config'].get('Labels', {})
        if 'com.lebowski.dockerfile' in labels:
            return labels['com.lebowski.dockerfile']

        # Try to reconstruct from history
        history = image.history()
        dockerfile_lines = []
        for entry in history:
            created_by = entry.get('CreatedBy', '')
            if created_by.startswith('/bin/sh -c'):
                # Extract command
                cmd = created_by.replace('/bin/sh -c #(nop) ', '')
                cmd = cmd.replace('/bin/sh -c ', 'RUN ')
                dockerfile_lines.append(cmd)

        return '\n'.join(dockerfile_lines) if dockerfile_lines else None

    def _get_base_images(self, image) -> List[Dict]:
        """Get chain of base images"""
        base_images = []

        # Parse parent image from Config
        parent = image.attrs.get('Parent')
        if parent:
            try:
                parent_image = self.client.images.get(parent)
                base_images.append({
                    'image_id': parent_image.id,
                    'digest': parent_image.attrs['RepoDigests'][0] if parent_image.attrs.get('RepoDigests') else None,
                    'created': parent_image.attrs['Created']
                })
            except:
                pass

        return base_images

    def _get_installed_packages(self, image_name: str) -> List[Dict]:
        """Get list of installed Debian packages in container"""
        container = None
        try:
            # Run dpkg-query in container
            container = self.client.containers.run(
                image_name,
                'dpkg-query -W -f="${Package}\\t${Version}\\t${Architecture}\\n"',
                remove=False,
                detach=False
            )

            output = container.decode('utf-8')
            packages = []

            for line in output.strip().split('\n'):
                if '\t' in line:
                    name, version, arch = line.split('\t')
                    packages.append({
                        'name': name,
                        'version': version,
                        'architecture': arch
                    })

            return packages
        except Exception as e:
            print(f"Warning: Failed to get package list: {e}")
            return []

    def _get_toolchain_info(self, image_name: str) -> Dict:
        """Get versions of key toolchain components"""
        toolchain = {}

        # Get GCC version
        try:
            output = self.client.containers.run(
                image_name,
                'gcc --version',
                remove=True
            ).decode('utf-8')

            # Parse version from output
            for line in output.split('\n'):
                if 'gcc' in line.lower():
                    version = line.split()[-1]
                    toolchain['gcc_version'] = version
                    break
        except:
            pass

        # Get glibc version
        try:
            output = self.client.containers.run(
                image_name,
                'ldd --version',
                remove=True
            ).decode('utf-8')

            for line in output.split('\n'):
                if 'GLIBC' in line or 'libc' in line:
                    version = line.split()[-1]
                    toolchain['glibc_version'] = version
                    break
        except:
            pass

        # Get binutils version
        try:
            output = self.client.containers.run(
                image_name,
                'ld --version',
                remove=True
            ).decode('utf-8')

            for line in output.split('\n'):
                if 'GNU ld' in line:
                    version = line.split()[-1]
                    toolchain['binutils_version'] = version
                    break
        except:
            pass

        # Get make version
        try:
            output = self.client.containers.run(
                image_name,
                'make --version',
                remove=True
            ).decode('utf-8')

            for line in output.split('\n'):
                if 'GNU Make' in line:
                    version = line.split()[-1]
                    toolchain['make_version'] = version
                    break
        except:
            pass

        return toolchain

    @staticmethod
    def _sha256(content: str) -> str:
        """Calculate SHA256 of string"""
        import hashlib
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
```

### 2. Integration with Builder

```python
# In lebowski/builder.py

from .container_inspector import ContainerInspector

class Builder:
    def build_package(self, ...):
        # ... existing build code ...

        # Inspect container before building
        if use_container:
            inspector = ContainerInspector()
            container_info = inspector.inspect_image(container_image)

            # Add to manifest
            manifest['container'] = {
                'image': container_info.image,
                'image_id': container_info.image_id,
                'digest': container_info.digest,
                'created': container_info.created,
                'architecture': container_info.architecture,
                'os': container_info.os,
                'dockerfile': container_info.dockerfile,
                'dockerfile_sha256': container_info.dockerfile_sha256,
                'base_images': container_info.base_images,
                'installed_packages': container_info.installed_packages,
                'toolchain': container_info.toolchain
            }

        # ... rest of build ...
```

### 3. Dockerfile Labels

To make Dockerfiles easier to track, add labels:

```dockerfile
# containers/xsc/Dockerfile
FROM debian:bookworm-slim

LABEL com.lebowski.version="1.0"
LABEL com.lebowski.toolchain="xsc"
LABEL com.lebowski.base="debian:bookworm-slim"
LABEL com.lebowski.dockerfile.url="https://github.com/jgowdy/lebowski/blob/main/containers/xsc/Dockerfile"

# Store full Dockerfile in label (for provenance)
LABEL com.lebowski.dockerfile="FROM debian:bookworm-slim\n\
RUN apt-get update && apt-get install -y \\\n\
    build-essential \\\n\
    gcc-12 \\\n\
    ..."

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc-12 \
    binutils \
    make \
    ...
```

## Verification with Container Provenance

When verifying a build, Lebowski can:

1. **Rebuild the container** from Dockerfile
2. **Verify container digest** matches manifest
3. **Check package versions** match expected toolchain
4. **Rebuild package** in reconstructed environment

```bash
# Verify with full environment rebuild
lebowski verify bash_5.1-6.lebowski-manifest.json --rebuild-container

# Steps:
# 1. Pull/build base image (debian:bookworm-slim)
# 2. Rebuild lebowski/builder:xsc from Dockerfile
# 3. Verify container digest matches manifest
# 4. Rebuild bash in that container
# 5. Compare outputs
```

## Container Registry Integration

For distributed builds, container images should be:

1. **Published to registry** (Docker Hub, ghcr.io)
2. **Tagged with digest** (immutable reference)
3. **Signed** (Docker Content Trust / Notary)

```yaml
# In opinion file
container:
  image: "ghcr.io/jgowdy/lebowski-builder-xsc:bookworm"
  digest: "sha256:abc123..."  # Immutable reference
  dockerfile_url: "https://github.com/jgowdy/lebowski/blob/main/containers/xsc/Dockerfile"
```

## Benefits

1. **Complete Reproducibility**: Anyone can rebuild from scratch
2. **Security**: Know exactly what's in the build environment
3. **Auditing**: Track toolchain changes over time
4. **Debugging**: Reproduce build failures exactly
5. **Trust**: Verify entire build chain, not just package

## Example: Reproducing a Build 5 Years Later

Given a manifest from 2025, someone in 2030 can:

```bash
# 1. Get manifest
curl https://builds.lebowski.org/bash_5.1-6.manifest.json > manifest.json

# 2. Rebuild base image
docker pull debian:bookworm-slim@sha256:xyz789...

# 3. Rebuild builder container from Dockerfile in manifest
echo "$DOCKERFILE_FROM_MANIFEST" | docker build -t lebowski-builder-xsc:2025 -

# 4. Rebuild package
lebowski verify manifest.json --rebuild-all

# Result: Bit-for-bit identical .deb file
```

This is **true reproducibility** - the ability to recreate the exact build environment years later.

## Storage Considerations

Container provenance adds ~50KB to manifest (Dockerfile + package list). For long-term archival:

- Store Dockerfiles in git (versioned)
- Reference by commit hash
- Archive container images (registry or tar)
- Store base image digests (immutable)

## Future Enhancements

1. **SBOM Generation**: Software Bill of Materials for containers
2. **Vulnerability Scanning**: Track CVEs in build environment
3. **Toolchain Optimization**: Detect unnecessary packages
4. **Container Diffing**: Compare environments between builds
5. **Multi-stage Build Support**: Track intermediate containers

## Implementation Priority

1. ✅ Track container image and digest (basic)
2. ⏳ Extract Dockerfile from labels
3. ⏳ List installed packages
4. ⏳ Get toolchain versions
5. ⏳ Track base image chain
6. ⏳ Container rebuild verification
7. ⏳ Registry integration

## References

- [Reproducible Builds: Container Images](https://reproducible-builds.org/docs/container-images/)
- [Docker Content Trust](https://docs.docker.com/engine/security/trust/)
- [OCI Image Spec](https://github.com/opencontainers/image-spec)
- [SLSA Framework](https://slsa.dev/) - Supply chain security
