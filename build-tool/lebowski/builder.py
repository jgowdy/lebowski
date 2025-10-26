"""
Core build engine - builds Debian packages with opinions.

This is where reproducibility happens. Every build MUST be bit-for-bit identical.
"""

import subprocess
import hashlib
import shutil
from pathlib import Path
from typing import Dict, Optional, Any
from .opinion import Opinion


class BuildError(Exception):
    """Build failed"""
    pass


class Builder:
    """Builds Debian packages with opinions in reproducible containers"""

    def __init__(
        self,
        opinion: Opinion,
        output_dir: Path,
        use_container: bool = True,
        keep_sources: bool = False,
        verbose: bool = False,
    ):
        self.opinion = opinion
        self.output_dir = Path(output_dir)
        self.use_container = use_container
        self.keep_sources = keep_sources
        self.verbose = verbose

        self.container_image = "lebowski/builder:bookworm"

        # Use /build if available (fast RAID), fallback to /tmp
        if Path("/build").exists() and Path("/build").is_dir():
            self.build_dir = Path("/build/lebowski-build")
        else:
            self.build_dir = Path("/tmp/lebowski-build")

    def build(self) -> Dict[str, Any]:
        """
        Build the package with the opinion.

        Returns dict with:
          - package_path: Path to built .deb
          - sha256: SHA256 hash of package
          - buildinfo_path: Path to .buildinfo file
          - manifest_path: Path to build manifest (reproducibility metadata)
        """
        package = self.opinion.metadata.package
        opinion_name = self.opinion.metadata.opinion_name

        print(f"Building {package} with opinion '{opinion_name}'...")

        # Create build directory
        self.build_dir.mkdir(parents=True, exist_ok=True)

        # Start building manifest for reproducibility
        import time
        import json
        manifest = {
            'lebowski_version': '1.0',
            'build_timestamp': time.time(),
            'build_timestamp_iso': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        }

        try:
            # Step 1: Fetch Debian source package
            print("📥 Fetching Debian source package...")
            source_dir, source_info = self._fetch_source()
            manifest['source'] = source_info

            # Step 2: Apply opinion modifications
            print("🔧 Applying opinion modifications...")
            self._apply_opinion(source_dir)
            manifest['opinion'] = self._get_opinion_metadata()

            # Step 3: Build package
            if self.use_container:
                print("🐳 Building in container (reproducible)...")
                result = self._build_in_container(source_dir, manifest)
            else:
                print("⚠️  Building locally (may not be reproducible)...")
                result = self._build_local(source_dir, manifest)

            # Step 4: Copy to output directory
            self._copy_output(result)

            # Step 5: Save manifest
            manifest_path = self._save_manifest(manifest, result)
            result['manifest_path'] = manifest_path

            # Clean up
            if not self.keep_sources:
                shutil.rmtree(self.build_dir)

            return result

        except Exception as e:
            raise BuildError(f"Build failed: {e}") from e

    def _fetch_source(self) -> tuple[Path, Dict[str, Any]]:
        """Fetch Debian source package using apt-get source

        Returns: (source_dir, source_info dict with provenance)
        """
        package = self.opinion.metadata.package

        # Change to build directory
        import os
        original_dir = os.getcwd()
        os.chdir(self.build_dir)

        try:
            # apt-get source <package>
            cmd = ["apt-get", "source", package]
            if self.verbose:
                print(f"Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=not self.verbose,
                text=True,
                check=True,
            )

            # Find the source directory (created by apt-get source)
            source_dirs = [d for d in self.build_dir.iterdir() if d.is_dir()]
            if not source_dirs:
                raise BuildError("No source directory created")

            source_dir = source_dirs[0]  # Usually package-version/

            # Extract version from directory name
            # Format is usually: package-version/ (e.g., bash-5.1/)
            dir_name = source_dir.name
            version = dir_name.replace(f"{package}-", "", 1) if package in dir_name else "unknown"

            # Find .dsc file for source metadata
            dsc_files = list(self.build_dir.glob("*.dsc"))
            dsc_hash = None
            if dsc_files:
                dsc_hash = self._hash_file(dsc_files[0])

            # Build source provenance info
            source_info = {
                'package': package,
                'version': version,
                'source_dir': str(source_dir),
                'dsc_file': str(dsc_files[0]) if dsc_files else None,
                'dsc_sha256': dsc_hash,
                # Record where the source came from
                'fetch_method': 'apt-get source',
                'fetch_command': ' '.join(cmd),
            }

            print(f"✓ Source fetched: {package} {version}")

            return source_dir, source_info

        finally:
            os.chdir(original_dir)

    def _apply_opinion(self, source_dir: Path) -> None:
        """Apply opinion modifications to source"""
        mods = self.opinion.modifications

        # Handle kernel config modifications
        if mods.kernel_config:
            self._apply_kernel_config(source_dir, mods.kernel_config)

        # Handle configure flags
        if mods.configure_flags:
            self._apply_configure_flags(source_dir, mods.configure_flags)

        # Handle environment variables
        if mods.env:
            # Will be applied during build
            pass

        # Handle CFLAGS/CXXFLAGS/LDFLAGS
        if mods.cflags or mods.cxxflags or mods.ldflags:
            self._apply_compiler_flags(source_dir, mods)

        print("✓ Opinion modifications applied")

    def _apply_kernel_config(self, source_dir: Path, config: Dict[str, str]) -> None:
        """Apply kernel config changes using scripts/config"""
        config_script = source_dir / "scripts" / "config"

        if not config_script.exists():
            raise BuildError("Kernel config script not found (is this a kernel package?)")

        for key, value in config.items():
            if value == "y":
                cmd = [str(config_script), "--enable", key]
            elif value == "n":
                cmd = [str(config_script), "--disable", key]
            else:
                cmd = [str(config_script), "--set-val", key, value]

            if self.verbose:
                print(f"  {' '.join(cmd)}")

            subprocess.run(cmd, cwd=source_dir, check=True)

    def _apply_configure_flags(self, source_dir: Path, flags: Dict[str, list]) -> None:
        """Modify debian/rules to add/remove configure flags"""
        rules_file = source_dir / "debian" / "rules"

        if not rules_file.exists():
            print("  Warning: debian/rules not found, skipping configure flags")
            return

        # This is simplified - real implementation needs to parse debian/rules
        # and modify the appropriate section
        print(f"  Note: Configure flags modification not fully implemented yet")
        print(f"    add: {flags.get('add', [])}")
        print(f"    remove: {flags.get('remove', [])}")

    def _apply_compiler_flags(self, source_dir: Path, mods) -> None:
        """Apply compiler flags by modifying debian/rules or environment"""
        # Simplified - real implementation would modify debian/rules
        # or set DEB_CFLAGS_APPEND, etc.
        if mods.cflags:
            print(f"  CFLAGS: {' '.join(mods.cflags)}")
        if mods.cxxflags:
            print(f"  CXXFLAGS: {' '.join(mods.cxxflags)}")
        if mods.ldflags:
            print(f"  LDFLAGS: {' '.join(mods.ldflags)}")

    def _get_opinion_metadata(self) -> Dict[str, Any]:
        """Get opinion metadata for reproducibility manifest"""
        import yaml

        # If opinion was loaded from file, include file path and hash
        opinion_file = getattr(self.opinion, '_source_file', None)
        opinion_hash = None

        if opinion_file and Path(opinion_file).exists():
            opinion_hash = self._hash_file(Path(opinion_file))

        return {
            'name': self.opinion.metadata.opinion_name,
            'package': self.opinion.metadata.package,
            'purity_level': self.opinion.metadata.purity_level,
            'description': self.opinion.metadata.description,
            'file': str(opinion_file) if opinion_file else None,
            'file_sha256': opinion_hash,
            'modifications': {
                'env': self.opinion.modifications.env,
                'cflags': self.opinion.modifications.cflags,
                'cxxflags': self.opinion.modifications.cxxflags,
                'ldflags': self.opinion.modifications.ldflags,
                'configure_flags': self.opinion.modifications.configure_flags,
                'kernel_config': self.opinion.modifications.kernel_config,
            }
        }

    def _build_in_container(self, source_dir: Path, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Build package in container for reproducibility"""
        import os

        # Check if docker/podman is available
        container_runtime = self._detect_container_runtime()

        if not container_runtime:
            raise BuildError(
                "No container runtime found (docker or podman required for reproducible builds). "
                "Install docker or podman, or use --no-container (not recommended)."
            )

        print(f"  Using {container_runtime} for reproducible build")

        # Build or pull container image
        container_image = self._ensure_container_image(container_runtime)

        # Prepare environment for container
        env_args = []
        for key, value in self.opinion.modifications.env.items():
            env_args.extend(['-e', f'{key}={value}'])

        # Add reproducible build environment
        env_args.extend([
            '-e', 'SOURCE_DATE_EPOCH=1704067200',
            '-e', 'TZ=UTC',
            '-e', 'LANG=C.UTF-8',
            '-e', 'LC_ALL=C.UTF-8',
            '-e', 'DEB_BUILD_OPTIONS=nodoc nocheck',
        ])

        # Add compiler flags
        if self.opinion.modifications.cflags:
            env_args.extend(['-e', f"DEB_CFLAGS_APPEND={' '.join(self.opinion.modifications.cflags)}"])
        if self.opinion.modifications.cxxflags:
            env_args.extend(['-e', f"DEB_CXXFLAGS_APPEND={' '.join(self.opinion.modifications.cxxflags)}"])
        if self.opinion.modifications.ldflags:
            env_args.extend(['-e', f"DEB_LDFLAGS_APPEND={' '.join(self.opinion.modifications.ldflags)}"])

        # Add configure flags
        if self.opinion.modifications.configure_flags:
            add_flags = self.opinion.modifications.configure_flags.get('add', [])
            if add_flags:
                env_args.extend(['-e', f"DEB_CONFIGURE_EXTRA_FLAGS={' '.join(add_flags)}"])

        # Mount source directory and output directory
        build_dir = source_dir.parent

        # Run build in container
        cmd = [
            container_runtime, 'run',
            '--rm',  # Remove container after build
            '-v', f'{build_dir}:/build:rw',  # Mount build directory
            '-w', f'/build/{source_dir.name}',  # Set working directory
        ] + env_args + [
            container_image,
            'dpkg-buildpackage', '-us', '-uc', '-B', '-d'
        ]

        if self.verbose:
            print(f"  Container command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=not self.verbose,
            text=True,
        )

        if result.returncode != 0:
            raise BuildError(f"Container build failed with code {result.returncode}")

        # Find built packages (same as local build)
        parent_dir = source_dir.parent
        deb_files = list(parent_dir.glob("*.deb"))

        if not deb_files:
            raise BuildError("No .deb file produced")

        package_path = deb_files[0]
        sha256 = self._hash_file(package_path)

        buildinfo_files = list(parent_dir.glob("*.buildinfo"))
        buildinfo_path = buildinfo_files[0] if buildinfo_files else None

        # Record build method in manifest
        manifest['build_method'] = 'container'
        manifest['container'] = {
            'runtime': container_runtime,
            'image': container_image,
        }

        manifest['output'] = {
            'package_file': package_path.name,
            'package_sha256': sha256,
            'buildinfo_file': buildinfo_path.name if buildinfo_path else None,
        }

        return {
            'package_path': package_path,
            'sha256': sha256,
            'buildinfo_path': buildinfo_path,
        }

    def _build_local(self, source_dir: Path, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Build package locally using dpkg-buildpackage"""
        # Set reproducible build environment
        import os
        import platform
        env = os.environ.copy()
        env['SOURCE_DATE_EPOCH'] = '1704067200'  # Fixed timestamp
        env['TZ'] = 'UTC'
        env['LANG'] = 'C.UTF-8'
        env['LC_ALL'] = 'C.UTF-8'

        # Apply opinion env vars (CC, LDFLAGS, etc)
        env.update(self.opinion.modifications.env)

        # Apply compiler flags as DEB_* env vars
        if self.opinion.modifications.cflags:
            env['DEB_CFLAGS_APPEND'] = ' '.join(self.opinion.modifications.cflags)
        if self.opinion.modifications.cxxflags:
            env['DEB_CXXFLAGS_APPEND'] = ' '.join(self.opinion.modifications.cxxflags)
        if self.opinion.modifications.ldflags:
            env['DEB_LDFLAGS_APPEND'] = ' '.join(self.opinion.modifications.ldflags)

        # Apply configure flags via DEB_CONFIGURE_EXTRA_FLAGS
        if self.opinion.modifications.configure_flags:
            add_flags = self.opinion.modifications.configure_flags.get('add', [])
            if add_flags:
                env['DEB_CONFIGURE_EXTRA_FLAGS'] = ' '.join(add_flags)
                print(f"  Configure flags: {env['DEB_CONFIGURE_EXTRA_FLAGS']}")

        # Get toolchain information for manifest
        toolchain_info = self._get_toolchain_info(env)
        manifest['toolchain'] = toolchain_info

        # Skip documentation building (avoid texlive dependency)
        env['DEB_BUILD_OPTIONS'] = 'nodoc nocheck'

        # Record build environment (reproducibility critical!)
        manifest['environment'] = {
            'SOURCE_DATE_EPOCH': env.get('SOURCE_DATE_EPOCH'),
            'TZ': env.get('TZ'),
            'LANG': env.get('LANG'),
            'LC_ALL': env.get('LC_ALL'),
            'CC': env.get('CC'),
            'CXX': env.get('CXX'),
            'DEB_CFLAGS_APPEND': env.get('DEB_CFLAGS_APPEND'),
            'DEB_CXXFLAGS_APPEND': env.get('DEB_CXXFLAGS_APPEND'),
            'DEB_LDFLAGS_APPEND': env.get('DEB_LDFLAGS_APPEND'),
            'DEB_CONFIGURE_EXTRA_FLAGS': env.get('DEB_CONFIGURE_EXTRA_FLAGS'),
            'DEB_BUILD_OPTIONS': env.get('DEB_BUILD_OPTIONS'),
            'PATH': env.get('PATH'),  # Critical - toolchain location
        }

        # Record build host info
        manifest['build_host'] = {
            'hostname': platform.node(),
            'system': platform.system(),
            'release': platform.release(),
            'machine': platform.machine(),
        }

        # Skip build-dep installation (assume dependencies are already installed)
        print("  (Skipping build-dep - assuming dependencies installed)")

        # Build package
        print("  Running dpkg-buildpackage...")
        cmd = [
            "dpkg-buildpackage",
            "-us",  # Don't sign source
            "-uc",  # Don't sign changes
            "-B",   # Architecture-specific binary only (skip -doc packages)
            "-d",   # Don't check build dependencies
        ]

        result = subprocess.run(
            cmd,
            cwd=source_dir,
            env=env,
            capture_output=not self.verbose,
            text=True,
        )

        if result.returncode != 0:
            raise BuildError(f"dpkg-buildpackage failed with code {result.returncode}")

        # Find built package
        parent_dir = source_dir.parent
        deb_files = list(parent_dir.glob("*.deb"))

        if not deb_files:
            raise BuildError("No .deb file produced")

        package_path = deb_files[0]

        # Calculate hash
        sha256 = self._hash_file(package_path)

        # Find buildinfo
        buildinfo_files = list(parent_dir.glob("*.buildinfo"))
        buildinfo_path = buildinfo_files[0] if buildinfo_files else None

        # Record output info in manifest
        manifest['output'] = {
            'package_file': package_path.name,
            'package_sha256': sha256,
            'buildinfo_file': buildinfo_path.name if buildinfo_path else None,
        }

        return {
            'package_path': package_path,
            'sha256': sha256,
            'buildinfo_path': buildinfo_path,
        }

    def _copy_output(self, result: Dict[str, Any]) -> None:
        """Copy built packages to output directory"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Copy .deb
        package_path = result['package_path']
        dest = self.output_dir / package_path.name
        shutil.copy2(package_path, dest)
        result['package_path'] = dest

        # Copy .buildinfo
        if result.get('buildinfo_path'):
            buildinfo_path = result['buildinfo_path']
            dest_buildinfo = self.output_dir / buildinfo_path.name
            shutil.copy2(buildinfo_path, dest_buildinfo)
            result['buildinfo_path'] = dest_buildinfo

        print(f"✓ Output copied to: {self.output_dir}")

    def _hash_file(self, path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256 = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _get_toolchain_info(self, env: Dict[str, str]) -> Dict[str, Any]:
        """Get toolchain information for reproducibility"""
        import os

        # Get compiler from environment
        cc = env.get('CC', 'gcc')

        # Try to get compiler path
        compiler_path = shutil.which(cc)

        # Get compiler version
        compiler_version = None
        try:
            result = subprocess.run(
                [cc, '--version'],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                compiler_version = result.stdout.split('\n')[0]
        except:
            pass

        # Get compiler binary hash (if found)
        compiler_hash = None
        if compiler_path and os.path.exists(compiler_path):
            compiler_hash = self._hash_file(Path(compiler_path))

        return {
            'compiler': cc,
            'compiler_path': compiler_path,
            'compiler_version': compiler_version,
            'compiler_sha256': compiler_hash,
        }

    def _save_manifest(self, manifest: Dict[str, Any], result: Dict[str, Any]) -> Path:
        """Save build manifest for reproducibility verification"""
        import json

        # Manifest filename based on output package
        package_name = result['package_path'].stem  # name without .deb
        manifest_filename = f"{package_name}.lebowski-manifest.json"
        manifest_path = self.output_dir / manifest_filename

        # Write manifest with pretty formatting
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2, sort_keys=True)

        print(f"✓ Build manifest saved: {manifest_path}")
        return manifest_path

    def _detect_container_runtime(self) -> Optional[str]:
        """Detect available container runtime (docker or podman)"""
        for runtime in ['docker', 'podman']:
            if shutil.which(runtime):
                return runtime
        return None

    def _ensure_container_image(self, runtime: str) -> str:
        """Ensure container image exists, build if necessary"""
        import os

        image_name = "lebowski/builder:bookworm"

        # Check if image exists
        check_cmd = [runtime, 'images', '-q', image_name]
        result = subprocess.run(check_cmd, capture_output=True, text=True)

        if result.returncode == 0 and result.stdout.strip():
            print(f"  Using existing container image: {image_name}")
            return image_name

        # Image doesn't exist - build it
        print(f"  Building container image: {image_name}")

        # Find Dockerfile
        script_dir = Path(__file__).parent.parent.parent  # lebowski/build-tool/lebowski -> lebowski/
        dockerfile = script_dir / "containers" / "debian-bookworm-builder.Dockerfile"

        if not dockerfile.exists():
            raise BuildError(f"Container Dockerfile not found: {dockerfile}")

        # Build image
        build_cmd = [
            runtime, 'build',
            '-t', image_name,
            '-f', str(dockerfile),
            str(dockerfile.parent)
        ]

        if self.verbose:
            print(f"  Build command: {' '.join(build_cmd)}")

        result = subprocess.run(
            build_cmd,
            capture_output=not self.verbose,
            text=True,
        )

        if result.returncode != 0:
            raise BuildError(f"Failed to build container image: {result.stderr}")

        print(f"  ✓ Container image built: {image_name}")
        return image_name
