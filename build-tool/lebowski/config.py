"""
Configuration system for Lebowski.

Supports system-wide and user-specific configuration files:
- /etc/lebowski.conf (system-wide)
- ~/.config/lebowski/config.yaml (user-specific)

Configuration precedence:
1. CLI flags (highest priority)
2. User config (~/.config/lebowski/config.yaml)
3. System config (/etc/lebowski.conf)
4. Built-in defaults (lowest priority)
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class GlobalDefaults:
    """Global default settings that apply to all builds"""
    optimization_level: Optional[int] = None  # -O2, -O3, etc.
    architecture: Optional[str] = None  # native, x86-64, etc. (for -march)
    lto: Optional[bool] = None  # Link-time optimization
    hardening: bool = True  # Stack protector, FORTIFY_SOURCE
    debug_symbols: bool = False  # Include -g

    # Additional global flags
    cflags: List[str] = field(default_factory=list)
    cxxflags: List[str] = field(default_factory=list)
    ldflags: List[str] = field(default_factory=list)


@dataclass
class RepositoryConfig:
    """Opinion repository configuration"""
    url: str
    branch: str = "main"
    cache_ttl: int = 86400  # 24 hours in seconds
    enabled: bool = True


@dataclass
class SigningConfig:
    """Package signing configuration"""
    enabled: bool = False
    auto_sign: bool = False  # Auto-generate and use Lebowski key
    key_id: Optional[str] = None  # User's GPG key ID
    export_public_key: bool = True  # Export public key with packages


@dataclass
class BuildDefaults:
    """Default build settings"""
    use_container: bool = True
    container_image: str = "lebowski/builder:bookworm"
    parallel_jobs: Optional[int] = None  # None = auto-detect
    keep_sources: bool = False
    work_dir: str = "/build/lebowski"


@dataclass
class LebowskiConfig:
    """Complete Lebowski configuration"""
    version: str = "1.0"

    # Global defaults that apply to all packages
    defaults: GlobalDefaults = field(default_factory=GlobalDefaults)

    # Build configuration
    build: BuildDefaults = field(default_factory=BuildDefaults)

    # Signing configuration
    signing: SigningConfig = field(default_factory=SigningConfig)

    # Opinion repositories
    repositories: Dict[str, RepositoryConfig] = field(default_factory=dict)

    # Package-specific default opinions
    # Format: {package_name: opinion_name}
    package_opinions: Dict[str, str] = field(default_factory=dict)

    # Trust settings
    max_purity_level: str = "custom"  # Most permissive purity level to allow


class ConfigLoader:
    """Load and merge configuration from multiple sources"""

    SYSTEM_CONFIG = Path("/etc/lebowski.conf")
    USER_CONFIG = Path.home() / ".config" / "lebowski" / "config.yaml"

    @staticmethod
    def load() -> LebowskiConfig:
        """Load configuration with proper precedence"""
        # Start with defaults
        config = LebowskiConfig()

        # Load system config
        if ConfigLoader.SYSTEM_CONFIG.exists():
            try:
                system_config = ConfigLoader._load_file(ConfigLoader.SYSTEM_CONFIG)
                config = ConfigLoader._merge_config(config, system_config)
            except Exception as e:
                print(f"Warning: Failed to load system config: {e}")

        # Load user config (overrides system)
        if ConfigLoader.USER_CONFIG.exists():
            try:
                user_config = ConfigLoader._load_file(ConfigLoader.USER_CONFIG)
                config = ConfigLoader._merge_config(config, user_config)
            except Exception as e:
                print(f"Warning: Failed to load user config: {e}")

        return config

    @staticmethod
    def _load_file(path: Path) -> Dict[str, Any]:
        """Load YAML config file"""
        with open(path, 'r') as f:
            data = yaml.safe_load(f)
        return data or {}

    @staticmethod
    def _merge_config(base: LebowskiConfig, override: Dict[str, Any]) -> LebowskiConfig:
        """Merge override config into base config"""
        # Update defaults
        if 'defaults' in override:
            defaults_data = override['defaults']
            if 'optimization_level' in defaults_data:
                base.defaults.optimization_level = defaults_data['optimization_level']
            if 'architecture' in defaults_data:
                base.defaults.architecture = defaults_data['architecture']
            if 'lto' in defaults_data:
                base.defaults.lto = defaults_data['lto']
            if 'hardening' in defaults_data:
                base.defaults.hardening = defaults_data['hardening']
            if 'debug_symbols' in defaults_data:
                base.defaults.debug_symbols = defaults_data['debug_symbols']
            if 'cflags' in defaults_data:
                base.defaults.cflags.extend(defaults_data['cflags'])
            if 'cxxflags' in defaults_data:
                base.defaults.cxxflags.extend(defaults_data['cxxflags'])
            if 'ldflags' in defaults_data:
                base.defaults.ldflags.extend(defaults_data['ldflags'])

        # Update build settings
        if 'build' in override:
            build_data = override['build']
            if 'use_container' in build_data:
                base.build.use_container = build_data['use_container']
            if 'container_image' in build_data:
                base.build.container_image = build_data['container_image']
            if 'parallel_jobs' in build_data:
                base.build.parallel_jobs = build_data['parallel_jobs']
            if 'keep_sources' in build_data:
                base.build.keep_sources = build_data['keep_sources']
            if 'work_dir' in build_data:
                base.build.work_dir = build_data['work_dir']

        # Update signing settings
        if 'signing' in override:
            signing_data = override['signing']
            if 'enabled' in signing_data:
                base.signing.enabled = signing_data['enabled']
            if 'auto_sign' in signing_data:
                base.signing.auto_sign = signing_data['auto_sign']
            if 'key_id' in signing_data:
                base.signing.key_id = signing_data['key_id']
            if 'export_public_key' in signing_data:
                base.signing.export_public_key = signing_data['export_public_key']

        # Update repositories
        if 'repositories' in override:
            for name, repo_data in override['repositories'].items():
                base.repositories[name] = RepositoryConfig(
                    url=repo_data['url'],
                    branch=repo_data.get('branch', 'main'),
                    cache_ttl=repo_data.get('cache_ttl', 86400),
                    enabled=repo_data.get('enabled', True),
                )

        # Update package opinions
        if 'packages' in override:
            base.package_opinions.update(override['packages'])

        # Update trust settings
        if 'max_purity_level' in override:
            base.max_purity_level = override['max_purity_level']

        return base

    @staticmethod
    def apply_defaults_to_opinion(config: LebowskiConfig, opinion: 'Opinion', verbose: bool = False) -> 'Opinion':
        """Apply global defaults to an opinion's modifications

        This adds system-wide compiler flags before opinion-specific flags,
        and normalizes the result to handle conflicts and duplicates.
        """
        from .opinion import OpinionModifications, Opinion
        from .flag_normalizer import FlagNormalizer

        defaults = config.defaults
        mods = opinion.modifications

        # Build default CFLAGS from config
        default_cflags = []

        if defaults.optimization_level is not None:
            default_cflags.append(f"-O{defaults.optimization_level}")

        if defaults.architecture:
            if defaults.architecture == "native":
                default_cflags.append("-march=native")
                default_cflags.append("-mtune=native")
            else:
                default_cflags.append(f"-march={defaults.architecture}")

        if defaults.lto:
            default_cflags.append("-flto")

        if defaults.hardening:
            default_cflags.append("-fstack-protector-strong")
            default_cflags.append("-D_FORTIFY_SOURCE=2")

        if defaults.debug_symbols:
            default_cflags.append("-g")

        # Add user-specified global flags
        default_cflags.extend(defaults.cflags)

        # Build default LDFLAGS
        default_ldflags = list(defaults.ldflags)
        if defaults.lto:
            default_ldflags.insert(0, "-flto")

        # Normalize CFLAGS: config defaults + opinion flags
        cflags_sources = [
            ("config", default_cflags),
            ("opinion", mods.cflags),
        ]
        cflags_result = FlagNormalizer.normalize_cflags(cflags_sources, verbose=verbose)

        # Normalize CXXFLAGS: config defaults + config cxxflags + opinion cxxflags
        cxxflags_sources = [
            ("config", default_cflags + defaults.cxxflags),
            ("opinion", mods.cxxflags),
        ]
        cxxflags_result = FlagNormalizer.normalize_cflags(cxxflags_sources, verbose=verbose)

        # Normalize LDFLAGS: config defaults + opinion ldflags
        ldflags_sources = [
            ("config", default_ldflags),
            ("opinion", mods.ldflags),
        ]
        ldflags_result = FlagNormalizer.normalize_ldflags(ldflags_sources, verbose=verbose)

        # Store normalization results for reporting
        opinion._normalization_warnings = (
            cflags_result.warnings +
            cxxflags_result.warnings +
            ldflags_result.warnings
        )

        # Create new modifications with normalized flags
        merged_mods = OpinionModifications(
            configure_flags=mods.configure_flags,
            cflags=cflags_result.flags,
            cxxflags=cxxflags_result.flags,
            ldflags=ldflags_result.flags,
            env=mods.env,
            build_deps=mods.build_deps,
            patches=mods.patches,
            kernel_config=mods.kernel_config,
            make_vars=mods.make_vars,
            debian_rules=mods.debian_rules,
            scripts=mods.scripts,
        )

        # Create new opinion with merged modifications
        normalized_opinion = Opinion(
            metadata=opinion.metadata,
            modifications=merged_mods,
            raw=opinion.raw,
            _source_file=opinion._source_file,
        )

        # Carry over normalization warnings
        normalized_opinion._normalization_warnings = opinion._normalization_warnings

        return normalized_opinion

    @staticmethod
    def get_default_opinion(config: LebowskiConfig, package: str) -> Optional[str]:
        """Get default opinion for a package from config"""
        return config.package_opinions.get(package)

    @staticmethod
    def create_example_config() -> str:
        """Generate an example configuration file"""
        return """# Lebowski Configuration File
# System: /etc/lebowski.conf
# User: ~/.config/lebowski/config.yaml

version: "1.0"

# Global defaults applied to all builds
defaults:
  # Optimization level (0-3)
  optimization_level: 2

  # CPU architecture optimization
  # Options: native, x86-64, x86-64-v2, x86-64-v3, skylake, zen3, etc.
  architecture: native

  # Link-time optimization
  lto: false

  # Security hardening (stack protector, FORTIFY_SOURCE)
  hardening: true

  # Include debug symbols
  debug_symbols: false

  # Additional global flags (applied to all builds)
  cflags:
    - "-pipe"
  cxxflags: []
  ldflags: []

# Build configuration
build:
  # Always use containers for reproducibility
  use_container: true

  # Default container image
  container_image: "lebowski/builder:bookworm"

  # Parallel build jobs (null = auto-detect)
  parallel_jobs: null

  # Keep source directories after build
  keep_sources: false

  # Working directory for builds
  work_dir: "/build/lebowski"

# Package signing (optional)
signing:
  # Enable package signing
  enabled: false

  # Auto-generate and use Lebowski signing key
  # (Creates ~/.config/lebowski/signing-key/ if not exists)
  auto_sign: false

  # Or specify your own GPG key ID
  # key_id: "ABCD1234EF567890"

  # Export public key with packages for verification
  export_public_key: true

# Opinion repositories
repositories:
  official:
    url: "https://github.com/jgowdy/lebowski-opinions"
    branch: "main"
    cache_ttl: 86400  # 24 hours
    enabled: true

  # Example: Add your own opinion repository
  # custom:
  #   url: "https://github.com/myuser/my-opinions"
  #   branch: "main"
  #   enabled: true

# Package-specific default opinions
# When building without --opinion flag, use these
packages:
  nginx: "optimized"
  postgresql: "server-hardened"
  linux: "desktop-1000hz"
  bash: "minimal"
  python3: "optimized"

# Trust settings
# Maximum purity level to allow (rejects opinions with lower trust)
# Options: pure-compilation, configure-only, debian-patches,
#          upstream-patches, third-party-patches, custom
max_purity_level: "custom"
"""


def get_config() -> LebowskiConfig:
    """Get current Lebowski configuration (cached)"""
    if not hasattr(get_config, '_cached_config'):
        get_config._cached_config = ConfigLoader.load()
    return get_config._cached_config


def reload_config():
    """Force reload configuration from disk"""
    if hasattr(get_config, '_cached_config'):
        delattr(get_config, '_cached_config')
    return get_config()
