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
@click.option('--container/--no-container', default=True, help='Build in container (reproducible)')
@click.option('--keep-sources', is_flag=True, help='Keep source directory after build')
@click.pass_context
def build(ctx, package, opinion, opinion_file, output_dir, container, keep_sources):
    """
    Build a package with an opinion.

    Examples:
      lebowski build linux --opinion desktop-1000hz
      lebowski build nginx --opinion http3
      lebowski build python3 --opinion optimized
      lebowski build nginx --opinion-file my-opinion.yaml
    """
    verbose = ctx.obj['VERBOSE']

    click.echo(f"🎬 Lebowski: Building {package}")
    click.echo()

    if not container:
        click.echo("⚠️  WARNING: Building without container - build may not be reproducible!")
        click.echo("   Reproducibility is our economic foundation. Use containers.")
        if not click.confirm("   Continue anyway?"):
            sys.exit(1)

    # Load opinion
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
        click.echo("❌ Either --opinion or --opinion-file is required", err=True)
        sys.exit(1)

    try:
        # Parse opinion
        opinion_obj = OpinionParser.load(opinion_path)

        # Show opinion info
        click.echo(f"✓ Opinion loaded: {opinion_obj.metadata.opinion_name}")
        click.echo(f"  Package: {opinion_obj.metadata.package}")
        click.echo(f"  Purity: {opinion_obj.metadata.purity_level} ({OpinionParser.get_purity_trust_level(opinion_obj.metadata.purity_level)} trust)")
        click.echo(f"  Description: {opinion_obj.metadata.description.split(chr(10))[0][:60]}...")
        click.echo()

        # Build
        builder = Builder(
            opinion=opinion_obj,
            output_dir=Path(output_dir),
            use_container=container,
            keep_sources=keep_sources,
            verbose=verbose,
        )

        click.echo("🔨 Starting build...")
        result = builder.build()

        click.echo()
        click.echo("✅ Build successful!")
        click.echo(f"📦 Package: {result['package_path']}")
        click.echo(f"🔐 SHA256: {result['sha256']}")
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
    click.echo("🔍 Searching opinions...")
    click.echo()
    click.echo("(Opinion repository integration coming soon)")
    click.echo()
    click.echo("For now, check the opinions/ directory:")
    click.echo("  opinions/linux/       - Kernel opinions")
    click.echo("  opinions/nginx/       - nginx opinions")
    click.echo("  opinions/python3/     - Python opinions")


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
@click.argument('package_file', type=click.Path(exists=True))
@click.pass_context
def verify(ctx, package_file):
    """
    Verify a package is reproducible (rebuild and compare hash).

    Example:
      lebowski verify nginx-http3_1.24.0-1~opinion1_amd64.deb
    """
    click.echo(f"🔍 Verifying: {package_file}")
    click.echo()
    click.echo("(Verification implementation coming soon)")
    click.echo()
    click.echo("This will:")
    click.echo("  1. Extract opinion from package metadata")
    click.echo("  2. Rebuild in container")
    click.echo("  3. Compare SHA256 hashes")
    click.echo("  4. Report match/mismatch")


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
