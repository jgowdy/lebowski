#!/usr/bin/env python3
"""
Lebowski CLI - Command line interface

Commands:
  build     - Build a package with an opinion
  verify    - Verify a package is reproducible
  search    - Search for available opinions
  show      - Show opinion details
  validate  - Validate an opinion file
"""

import click
import sys
from pathlib import Path
from typing import Optional

from . import __version__
from .opinion import OpinionParser, OpinionError
from .builder import Builder, BuildError
from .attestation import generate_attestation
from .config import get_config, ConfigLoader


@click.group()
@click.version_option(version=__version__)
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def main(ctx, verbose):
    """
    Lebowski - Build Debian packages with custom opinions

    Re-empowering users at the expense of gatekeepers.

    Your computer. Your kernel. Your choice. No permission needed.
    """
    ctx.ensure_object(dict)
    ctx.obj['VERBOSE'] = verbose


@main.command()
@click.argument('package')
@click.option('--opinion', '-o', help='Opinion name from repository')
@click.option('--opinion-file', type=click.Path(exists=True), help='Local opinion YAML file')
@click.option('--output-dir', type=click.Path(), default='.', help='Output directory for built packages')
@click.option('--container/--no-container', default=None, help='Build in container (reproducible)')
@click.option('--keep-sources', is_flag=True, help='Keep source directory after build')
@click.option('--project-name', help='Custom project name for build outputs (overrides opinion)')
@click.option('--show-receipt/--no-show-receipt', default=True, help='Show build attestation (receipt) after build')
@click.option('--receipt-format', type=click.Choice(['compact', 'full', 'oneline', 'none']), default='compact', help='Receipt format to display')
@click.pass_context
def build(ctx, package, opinion, opinion_file, output_dir, container, keep_sources, project_name, show_receipt, receipt_format):
    """
    Build a package with an opinion.

    Examples:
      lebowski build linux --opinion desktop-1000hz
      lebowski build nginx --opinion http3
      lebowski build python3 --opinion optimized
      lebowski build nginx --opinion-file my-opinion.yaml
      lebowski build bash  # Uses default opinion from config
    """
    verbose = ctx.obj['VERBOSE']

    # Load configuration
    config = get_config()

    # Determine container setting (CLI > config)
    use_container = container if container is not None else config.build.use_container

    if not use_container:
        click.echo("⚠️  WARNING: Building without container - build may not be reproducible!")
        click.echo("   Reproducibility is our economic foundation. Use containers.")
        if not click.confirm("   Continue anyway?"):
            sys.exit(1)

    # Resolve opinion
    if opinion_file:
        click.echo(f"📄 Loading opinion from: {opinion_file}")
        opinion_path = Path(opinion_file)
    elif opinion:
        # TODO: Fetch from opinion repository
        click.echo(f"📦 Fetching opinion: {package}:{opinion}")
        opinion_path = Path(f"opinions/{package}/{opinion}.yaml")
        if not opinion_path.exists():
            click.echo(f"❌ Opinion not found: {opinion_path}", err=True)
            click.echo(f"   (Opinion repository integration coming soon)", err=True)
            sys.exit(1)
    else:
        # Try to use default opinion from config
        default_opinion = ConfigLoader.get_default_opinion(config, package)
        if default_opinion:
            click.echo(f"📦 Using default opinion for {package}: {default_opinion}")
            opinion_path = Path(f"opinions/{package}/{default_opinion}.yaml")
            if not opinion_path.exists():
                click.echo(f"❌ Default opinion not found: {opinion_path}", err=True)
                sys.exit(1)
        else:
            click.echo("❌ Either --opinion or --opinion-file is required", err=True)
            click.echo(f"   Or configure a default opinion in /etc/lebowski.conf", err=True)
            sys.exit(1)

    try:
        # Parse opinion
        opinion_obj = OpinionParser.load(opinion_path)

        # Apply configuration defaults to opinion
        opinion_obj = ConfigLoader.apply_defaults_to_opinion(config, opinion_obj, verbose=verbose)

        # Override project_name from CLI if provided
        if project_name:
            opinion_obj.metadata.project_name = project_name

        # Show build header with project name
        display_name = opinion_obj.metadata.project_name or "Unknown project"
        click.echo(f"🎬 {display_name}: Building {package}")
        click.echo()

        # Show opinion info
        click.echo(f"✓ Opinion loaded: {opinion_obj.metadata.opinion_name}")
        click.echo(f"  Package: {opinion_obj.metadata.package}")
        click.echo(f"  Purity: {opinion_obj.metadata.purity_level} ({OpinionParser.get_purity_trust_level(opinion_obj.metadata.purity_level)} trust)")
        click.echo(f"  Description: {opinion_obj.metadata.description.split(chr(10))[0][:60]}...")

        # Show container image if opinion specifies one (e.g., XSC opinions)
        if opinion_obj.metadata.container_image:
            click.echo(f"  Container: {opinion_obj.metadata.container_image}")

        # Show if config defaults are applied
        if config.defaults.optimization_level or config.defaults.architecture or config.defaults.cflags:
            click.echo()
            click.echo("⚙️  Applied config defaults:")
            if config.defaults.optimization_level:
                click.echo(f"  Optimization: -O{config.defaults.optimization_level}")
            if config.defaults.architecture:
                click.echo(f"  Architecture: -march={config.defaults.architecture}")
            if config.defaults.lto:
                click.echo(f"  LTO: enabled")
            if config.defaults.cflags:
                click.echo(f"  Global CFLAGS: {' '.join(config.defaults.cflags)}")

        # Show normalization warnings
        if hasattr(opinion_obj, '_normalization_warnings') and opinion_obj._normalization_warnings:
            click.echo()
            click.echo("⚠️  Flag conflicts resolved:")
            for warning in opinion_obj._normalization_warnings:
                click.echo(f"  {warning}")

        # Show final flags in verbose mode
        if verbose:
            from .flag_normalizer import FlagNormalizer
            click.echo()
            click.echo("📋 Final compiler flags:")
            cflags_categorized = FlagNormalizer.explain_flags(opinion_obj.modifications.cflags)
            for category, flags in cflags_categorized.items():
                click.echo(f"  {category}: {' '.join(flags)}")

        click.echo()

        # Build
        builder = Builder(
            opinion=opinion_obj,
            output_dir=Path(output_dir),
            use_container=container,
            keep_sources=keep_sources,
            verbose=verbose,
            default_container_image=config.build.container_image,
        )

        click.echo("🔨 Starting build...")
        result = builder.build()

        click.echo()
        click.echo("✅ Build successful!")
        click.echo(f"📦 Package: {result['package_path']}")
        click.echo(f"🔐 SHA256: {result['sha256']}")

        # Display attestation (receipt) if requested
        if show_receipt and receipt_format != 'none':
            from .attestation import generate_attestation
            # Derive manifest path from package path
            package_path = Path(result['package_path'])
            package_name = package_path.stem  # name without .deb
            manifest_filename = f"{package_name}.lebowski-manifest.json"
            manifest_path = package_path.parent / manifest_filename

            if manifest_path.exists():
                click.echo()
                click.echo("═" * 70)
                click.echo("📋 BUILD ATTESTATION (RECEIPT)")
                click.echo("═" * 70)
                attestation = generate_attestation(manifest_path, format=receipt_format)
                click.echo(attestation)
                click.echo("═" * 70)
                click.echo(f"📄 Full manifest: {manifest_path}")

        click.echo()
        click.echo("Install with:")
        click.echo(f"  sudo dpkg -i {result['package_path']}")

    except OpinionError as e:
        click.echo(f"❌ Opinion error: {e}", err=True)
        sys.exit(1)
    except BuildError as e:
        click.echo(f"❌ Build error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument('opinion_file', type=click.Path(exists=True))
@click.pass_context
def validate(ctx, opinion_file):
    """
    Validate an opinion YAML file.

    Example:
      lebowski validate opinions/nginx/http3.yaml
    """
    click.echo(f"🔍 Validating: {opinion_file}")
    click.echo()

    try:
        opinion = OpinionParser.load(Path(opinion_file))

        click.echo("✅ Opinion is valid!")
        click.echo()
        click.echo(f"  Package: {opinion.metadata.package}")
        click.echo(f"  Opinion: {opinion.metadata.opinion_name}")
        click.echo(f"  Purity: {opinion.metadata.purity_level} ({OpinionParser.get_purity_trust_level(opinion.metadata.purity_level)} trust)")
        click.echo(f"  Tags: {', '.join(opinion.metadata.tags)}")

    except OpinionError as e:
        click.echo(f"❌ Validation failed: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument('package', required=False)
@click.pass_context
def search(ctx, package):
    """
    Search for available opinions.

    Examples:
      lebowski search nginx
      lebowski search    # List all
    """
    import os
    from pathlib import Path

    opinions_dir = Path("opinions")

    if not opinions_dir.exists():
        click.echo("❌ Opinions directory not found: opinions/", err=True)
        click.echo("   Make sure you're running from the Lebowski repository root", err=True)
        sys.exit(1)

    click.echo("🔍 Searching opinions...")
    click.echo()

    # Find all opinion YAML files
    opinions_found = {}
    for package_dir in sorted(opinions_dir.iterdir()):
        if not package_dir.is_dir() or package_dir.name.startswith('_'):
            continue

        pkg_name = package_dir.name

        # Filter by package if specified
        if package and package not in pkg_name:
            continue

        # Find YAML files in this package directory
        yaml_files = list(package_dir.glob("*.yaml"))
        if yaml_files:
            opinions_found[pkg_name] = []
            for yaml_file in sorted(yaml_files):
                opinion_name = yaml_file.stem
                try:
                    opinion = OpinionParser.load(yaml_file)
                    desc = opinion.metadata.description.split('\n')[0][:50]
                    purity = opinion.metadata.purity_level
                    opinions_found[pkg_name].append({
                        'name': opinion_name,
                        'desc': desc,
                        'purity': purity
                    })
                except Exception:
                    # Skip invalid opinions
                    pass

    if not opinions_found:
        if package:
            click.echo(f"No opinions found for package: {package}")
        else:
            click.echo("No opinions found in opinions/ directory")
        sys.exit(0)

    # Display results
    total_opinions = sum(len(opinions) for opinions in opinions_found.values())
    click.echo(f"Found {total_opinions} opinion(s) in {len(opinions_found)} package(s):")
    click.echo()

    for pkg_name, opinions in opinions_found.items():
        click.echo(f"📦 {pkg_name}")
        for opinion in opinions:
            trust_level = OpinionParser.get_purity_trust_level(opinion['purity'])
            click.echo(f"   • {opinion['name']:<20} [{opinion['purity']:<20}] {trust_level} trust")
            click.echo(f"     {opinion['desc']}")
        click.echo()

    click.echo("Use 'lebowski show <package>:<opinion>' for details")


@main.command()
@click.argument('opinion_ref')
@click.pass_context
def show(ctx, opinion_ref):
    """
    Show details about an opinion.

    Example:
      lebowski show nginx:http3
      lebowski show linux:desktop-1000hz
    """
    if ':' not in opinion_ref:
        click.echo("❌ Opinion reference must be package:opinion (e.g., nginx:http3)", err=True)
        sys.exit(1)

    package, opinion_name = opinion_ref.split(':', 1)
    opinion_file = Path(f"opinions/{package}/{opinion_name}.yaml")

    if not opinion_file.exists():
        click.echo(f"❌ Opinion not found: {opinion_file}", err=True)
        sys.exit(1)

    try:
        opinion = OpinionParser.load(opinion_file)

        click.echo(f"📦 Opinion: {package}:{opinion_name}")
        click.echo()
        click.echo(f"Purity Level: {opinion.metadata.purity_level}")
        click.echo(f"Trust Level: {OpinionParser.get_purity_trust_level(opinion.metadata.purity_level)}")
        click.echo()
        click.echo("Description:")
        click.echo(opinion.metadata.description)
        click.echo()

        if opinion.metadata.tags:
            click.echo(f"Tags: {', '.join(opinion.metadata.tags)}")

        if opinion.metadata.maintainer:
            maint = opinion.metadata.maintainer
            click.echo(f"Maintainer: {maint.get('name', 'Unknown')}")

        click.echo()
        click.echo("Modifications:")

        mods = opinion.modifications
        if mods.configure_flags:
            click.echo(f"  Configure flags: {mods.configure_flags}")
        if mods.cflags:
            click.echo(f"  CFLAGS: {' '.join(mods.cflags)}")
        if mods.kernel_config:
            click.echo(f"  Kernel config changes: {len(mods.kernel_config)} options")

    except OpinionError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument('manifest_url')
@click.option('--output-dir', type=click.Path(), default='/tmp/lebowski-verify', help='Output directory for verification')
@click.pass_context
def verify(ctx, manifest_url, output_dir):
    """
    Verify a package is reproducible (rebuild from manifest and compare hash).

    Examples:
      lebowski verify https://builds.example.com/bash.manifest.json
      lebowski verify /path/to/bash.lebowski-manifest.json
    """
    import json
    import urllib.request

    verbose = ctx.obj['VERBOSE']

    click.echo(f"🔍 Verifying build from manifest")
    click.echo()

    # Download or load manifest
    click.echo(f"📄 Loading manifest: {manifest_url}")
    try:
        if manifest_url.startswith('http://') or manifest_url.startswith('https://'):
            with urllib.request.urlopen(manifest_url) as response:
                manifest = json.loads(response.read())
        else:
            with open(manifest_url, 'r') as f:
                manifest = json.load(f)
    except Exception as e:
        click.echo(f"❌ Failed to load manifest: {e}", err=True)
        sys.exit(1)

    # Display manifest info
    source = manifest.get('source', {})
    opinion = manifest.get('opinion', {})
    expected_output = manifest.get('output', {})

    click.echo(f"  Package: {source.get('package')} {source.get('version')}")
    click.echo(f"  Opinion: {opinion.get('name')}")
    click.echo(f"  Expected hash: {expected_output.get('package_sha256', 'unknown')[:16]}...")
    click.echo()

    # Recreate opinion from manifest
    click.echo("🔧 Recreating opinion from manifest...")
    opinion_data = {
        'version': '1.0',
        'package': source.get('package'),
        'opinion_name': opinion.get('name'),
        'purity_level': opinion.get('purity_level', 'configure-only'),
        'description': opinion.get('description', 'Verification rebuild'),
        'modifications': opinion.get('modifications', {})
    }

    # Save temporary opinion file
    import tempfile
    opinion_file = Path(tempfile.mkdtemp()) / 'verify-opinion.yaml'
    import yaml
    with open(opinion_file, 'w') as f:
        yaml.dump(opinion_data, f)

    # Parse opinion
    try:
        opinion_obj = OpinionParser.load(opinion_file)
    except OpinionError as e:
        click.echo(f"❌ Invalid opinion in manifest: {e}", err=True)
        sys.exit(1)

    # Rebuild package
    click.echo("🔨 Rebuilding package...")
    try:
        builder = Builder(
            opinion=opinion_obj,
            output_dir=Path(output_dir),
            use_container=True,  # Always use container for verification
            keep_sources=False,
            verbose=verbose,
        )

        result = builder.build()

        # Compare hashes
        click.echo()
        click.echo("🔐 Comparing hashes...")
        expected_hash = expected_output.get('package_sha256')
        actual_hash = result['sha256']

        click.echo(f"  Expected: {expected_hash}")
        click.echo(f"  Got:      {actual_hash}")
        click.echo()

        if expected_hash == actual_hash:
            click.echo("✅ VERIFICATION SUCCESSFUL!")
            click.echo("   Hashes match - build is reproducible!")
            sys.exit(0)
        else:
            click.echo("❌ VERIFICATION FAILED!")
            click.echo("   Hashes DO NOT match!")
            click.echo()
            click.echo("⚠️  This could mean:")
            click.echo("   - Build is not reproducible")
            click.echo("   - Toolchain differs")
            click.echo("   - Manifest is incorrect")
            click.echo("   - Package has been tampered with")
            sys.exit(1)

    except BuildError as e:
        click.echo(f"❌ Rebuild failed: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Verification error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.option('--system', is_flag=True, help='Generate system config (/etc/lebowski.conf)')
@click.option('--user', is_flag=True, help='Generate user config (~/.config/lebowski/config.yaml)')
@click.pass_context
def config(ctx, system, user):
    """
    Generate example configuration file.

    Examples:
      lebowski config --user    # Create user config
      lebowski config --system  # Show system config (requires sudo to install)
      lebowski config           # Show config on stdout
    """
    example_config = ConfigLoader.create_example_config()

    if system:
        config_path = ConfigLoader.SYSTEM_CONFIG
        click.echo(f"📝 Generating system configuration: {config_path}")
        click.echo()
        click.echo("⚠️  You will need sudo privileges to write to /etc/")
        if click.confirm("   Continue?"):
            try:
                # Ensure parent directory exists
                config_path.parent.mkdir(parents=True, exist_ok=True)
                with open(config_path, 'w') as f:
                    f.write(example_config)
                click.echo(f"✅ Configuration written to {config_path}")
            except PermissionError:
                click.echo(f"❌ Permission denied. Try: sudo lebowski config --system", err=True)
                sys.exit(1)
    elif user:
        config_path = ConfigLoader.USER_CONFIG
        click.echo(f"📝 Generating user configuration: {config_path}")
        click.echo()
        # Ensure parent directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            f.write(example_config)
        click.echo(f"✅ Configuration written to {config_path}")
        click.echo()
        click.echo("Edit this file to customize your defaults:")
        click.echo(f"  vim {config_path}")
    else:
        # Just print to stdout
        click.echo("# Example Lebowski Configuration")
        click.echo()
        click.echo(example_config)


@main.command()
@click.argument('manifest_file', type=click.Path(exists=True))
@click.option('--format', '-f', type=click.Choice(['compact', 'full', 'oneline', 'json', 'twitter', 'mastodon', 'github', 'slack']),
              default='full', help='Attestation format')
@click.option('--url', help='URL where manifest is hosted')
@click.option('--copy', is_flag=True, help='Copy to clipboard')
@click.pass_context
def attest(ctx, manifest_file, format, url, copy):
    """
    Generate build attestation from manifest.

    Post to social networks, GitHub, Slack, etc. to prove your build is reproducible.

    Examples:
      lebowski attest bash_5.1_amd64.lebowski-manifest.json
      lebowski attest bash.manifest.json --format twitter
      lebowski attest bash.manifest.json --format github --url https://builds.example.com/bash.manifest.json
      lebowski attest bash.manifest.json --format compact --copy
    """
    try:
        attestation = generate_attestation(Path(manifest_file), format=format, manifest_url=url)

        click.echo(attestation)

        if copy:
            try:
                import pyperclip
                pyperclip.copy(attestation)
                click.echo()
                click.echo("✅ Copied to clipboard!")
            except ImportError:
                click.echo()
                click.echo("⚠️  Install pyperclip for clipboard support: pip install pyperclip")

    except FileNotFoundError:
        click.echo(f"❌ Manifest file not found: {manifest_file}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error generating attestation: {e}", err=True)
        if ctx.obj.get('VERBOSE'):
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
