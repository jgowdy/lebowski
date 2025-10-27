"""
Opinion definition parser and validator.

Opinions are YAML files that describe how to modify Debian source packages.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


# Valid purity levels (in order of trust)
PURITY_LEVELS = [
    "pure-compilation",     # Highest trust: only CFLAGS/defines
    "configure-only",       # High trust: only build flags
    "debian-patches",       # Medium trust: Debian's own patches
    "upstream-patches",     # Medium trust: upstream patches
    "third-party-patches",  # Lower trust: community patches
    "custom",              # Lowest trust: custom scripts
]


@dataclass
class OpinionMetadata:
    """Metadata about an opinion"""
    version: str
    package: str
    opinion_name: str
    purity_level: str
    description: str
    maintainer: Dict[str, str] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    debian_versions: List[str] = field(default_factory=list)
    container_image: Optional[str] = None  # e.g., "lebowski/builder:xsc"


@dataclass
class OpinionModifications:
    """Modifications to apply to the package"""
    configure_flags: Dict[str, List[str]] = field(default_factory=dict)
    cflags: List[str] = field(default_factory=list)
    cxxflags: List[str] = field(default_factory=list)
    ldflags: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    build_deps: Dict[str, List[str]] = field(default_factory=dict)
    patches: List[str] = field(default_factory=list)
    kernel_config: Dict[str, str] = field(default_factory=dict)
    make_vars: Dict[str, str] = field(default_factory=dict)
    debian_rules: Optional[str] = None
    scripts: Dict[str, str] = field(default_factory=dict)


@dataclass
class Opinion:
    """A complete opinion definition"""
    metadata: OpinionMetadata
    modifications: OpinionModifications
    raw: Dict[str, Any]
    _source_file: Optional[str] = None  # Track source file for reproducibility


class OpinionError(Exception):
    """Base class for opinion-related errors"""
    pass


class OpinionValidationError(OpinionError):
    """Opinion failed validation"""
    pass


class OpinionParser:
    """Parse and validate opinion YAML files"""

    @staticmethod
    def load(file_path: Path, is_parent: bool = False) -> Opinion:
        """Load opinion from YAML file

        Args:
            file_path: Path to opinion YAML file
            is_parent: True if loading a parent template (skip validation)
        """
        if not file_path.exists():
            raise OpinionError(f"Opinion file not found: {file_path}")

        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)

        # Handle extends field - load parent opinion first
        parent_opinion = None
        if 'extends' in data:
            parent_path = file_path.parent / data['extends']
            if not parent_path.exists():
                raise OpinionError(f"Parent opinion not found: {parent_path} (from {file_path})")
            parent_opinion = OpinionParser.load(parent_path, is_parent=True)  # Recursive load

        # Parse without validation (will validate final merged opinion)
        opinion = OpinionParser.parse(data, skip_validation=True)
        opinion._source_file = str(file_path)  # Track source for reproducibility

        # Merge with parent if exists
        if parent_opinion:
            opinion = OpinionParser.merge_opinions(parent_opinion, opinion)

        # Validate the final merged opinion (but not parent templates)
        if not is_parent:
            OpinionParser.validate(opinion)

        return opinion

    @staticmethod
    def parse(data: Dict[str, Any], skip_validation: bool = False) -> Opinion:
        """Parse opinion from dictionary

        Args:
            data: Opinion data from YAML
            skip_validation: If True, skip validation (useful for parent templates)
        """
        # Parse metadata
        metadata = OpinionMetadata(
            version=data.get('version', '1.0'),
            package=data.get('package', ''),  # Optional for templates
            opinion_name=data['opinion_name'],
            purity_level=data.get('purity_level', 'configure-only'),
            description=data.get('description', ''),
            maintainer=data.get('maintainer', {}),
            tags=data.get('tags', []),
            debian_versions=data.get('debian_versions', []),
            container_image=data.get('container_image'),  # Optional: specific container for this opinion
        )

        # Parse modifications
        mods_data = data.get('modifications', {})
        modifications = OpinionModifications(
            configure_flags=mods_data.get('configure_flags', {}),
            cflags=mods_data.get('cflags', []),
            cxxflags=mods_data.get('cxxflags', []),
            ldflags=mods_data.get('ldflags', []),
            env=mods_data.get('env', {}),
            build_deps=mods_data.get('build_deps', {}),
            patches=mods_data.get('patches', []),
            kernel_config=mods_data.get('kernel_config', {}),
            make_vars=mods_data.get('make_vars', {}),
            debian_rules=mods_data.get('debian_rules'),
            scripts=mods_data.get('scripts', {}),
        )

        opinion = Opinion(
            metadata=metadata,
            modifications=modifications,
            raw=data,
        )

        # Validate (unless skipped for parent templates)
        if not skip_validation:
            OpinionParser.validate(opinion)

        return opinion

    @staticmethod
    def validate(opinion: Opinion) -> None:
        """Validate opinion definition"""
        # Required fields
        if not opinion.metadata.package:
            raise OpinionValidationError("Missing required field: package")
        if not opinion.metadata.opinion_name:
            raise OpinionValidationError("Missing required field: opinion_name")

        # Validate purity level
        if opinion.metadata.purity_level not in PURITY_LEVELS:
            raise OpinionValidationError(
                f"Invalid purity_level: {opinion.metadata.purity_level}. "
                f"Must be one of: {', '.join(PURITY_LEVELS)}"
            )

        # Validate purity level matches modifications
        OpinionParser.validate_purity(opinion)

    @staticmethod
    def validate_purity(opinion: Opinion) -> None:
        """Validate that modifications match declared purity level"""
        purity = opinion.metadata.purity_level
        mods = opinion.modifications

        if purity == "pure-compilation":
            # Only compilation flags allowed
            forbidden = []
            if mods.configure_flags:
                forbidden.append("configure_flags")
            if mods.patches:
                forbidden.append("patches")
            if mods.scripts:
                forbidden.append("scripts")
            if mods.debian_rules:
                forbidden.append("debian_rules")

            if forbidden:
                raise OpinionValidationError(
                    f"pure-compilation opinion cannot have: {', '.join(forbidden)}. "
                    f"Only cflags, cxxflags, ldflags, env, and make_vars are allowed."
                )

        elif purity == "configure-only":
            # No patches or scripts
            forbidden = []
            if mods.patches:
                forbidden.append("patches")
            if mods.scripts.get('pre_build') or mods.scripts.get('post_build'):
                forbidden.append("scripts")

            if forbidden:
                raise OpinionValidationError(
                    f"configure-only opinion cannot have: {', '.join(forbidden)}. "
                    f"No source modifications allowed."
                )

    @staticmethod
    def merge_opinions(parent: Opinion, child: Opinion) -> Opinion:
        """Merge parent and child opinions

        Merge strategy:
        - Metadata: Use child's metadata (child is the specific opinion being built)
        - Lists (cflags, ldflags, patches, etc.): Normalize and merge - parent then child
        - Dicts (env, make_vars, configure_flags, etc.): Merge - parent then child overrides
        - Single values: Child overrides parent
        - Flags are normalized to remove duplicates and resolve conflicts
        """
        from lebowski.flag_normalizer import FlagNormalizer

        # Start with parent modifications
        parent_mods = parent.modifications
        child_mods = child.modifications

        # Merge configure_flags (dict of lists)
        merged_configure_flags = dict(parent_mods.configure_flags)
        for key, values in child_mods.configure_flags.items():
            if key in merged_configure_flags:
                # Extend existing list
                merged_configure_flags[key] = merged_configure_flags[key] + values
            else:
                merged_configure_flags[key] = values

        # Normalize compiler flags - parent first, then child
        cflags_sources = [
            ("parent", parent_mods.cflags),
            ("child", child_mods.cflags),
        ]
        cflags_result = FlagNormalizer.normalize_cflags(cflags_sources)

        cxxflags_sources = [
            ("parent", parent_mods.cxxflags),
            ("child", child_mods.cxxflags),
        ]
        cxxflags_result = FlagNormalizer.normalize_cflags(cxxflags_sources)

        ldflags_sources = [
            ("parent", parent_mods.ldflags),
            ("child", child_mods.ldflags),
        ]
        ldflags_result = FlagNormalizer.normalize_ldflags(ldflags_sources)

        # Merge patches (no normalization needed)
        merged_patches = parent_mods.patches + child_mods.patches

        # Merge dicts - parent then child overrides
        merged_env = dict(parent_mods.env)
        merged_env.update(child_mods.env)

        merged_build_deps = dict(parent_mods.build_deps)
        for key, values in child_mods.build_deps.items():
            if key in merged_build_deps:
                merged_build_deps[key] = merged_build_deps[key] + values
            else:
                merged_build_deps[key] = values

        merged_kernel_config = dict(parent_mods.kernel_config)
        merged_kernel_config.update(child_mods.kernel_config)

        merged_make_vars = dict(parent_mods.make_vars)
        merged_make_vars.update(child_mods.make_vars)

        merged_scripts = dict(parent_mods.scripts)
        merged_scripts.update(child_mods.scripts)

        # Single values - child overrides
        merged_debian_rules = child_mods.debian_rules if child_mods.debian_rules else parent_mods.debian_rules

        # Create merged modifications with normalized flags
        merged_modifications = OpinionModifications(
            configure_flags=merged_configure_flags,
            cflags=cflags_result.flags,
            cxxflags=cxxflags_result.flags,
            ldflags=ldflags_result.flags,
            env=merged_env,
            build_deps=merged_build_deps,
            patches=merged_patches,
            kernel_config=merged_kernel_config,
            make_vars=merged_make_vars,
            debian_rules=merged_debian_rules,
            scripts=merged_scripts,
        )

        # Merge metadata - child overrides parent, except container_image inherits if not specified
        merged_metadata = OpinionMetadata(
            version=child.metadata.version,
            package=child.metadata.package,
            opinion_name=child.metadata.opinion_name,
            purity_level=child.metadata.purity_level,
            description=child.metadata.description,
            maintainer=child.metadata.maintainer,
            tags=child.metadata.tags,
            debian_versions=child.metadata.debian_versions,
            # Inherit container_image from parent if child doesn't specify it
            container_image=child.metadata.container_image or parent.metadata.container_image,
        )

        # Create merged opinion with merged metadata
        merged_opinion = Opinion(
            metadata=merged_metadata,
            modifications=merged_modifications,
            raw=child.raw,  # Use child's raw data
            _source_file=child._source_file,  # Track child as source
        )

        # Store warnings from opinion inheritance normalization
        merged_opinion._inheritance_warnings = (
            cflags_result.warnings +
            cxxflags_result.warnings +
            ldflags_result.warnings
        )

        return merged_opinion

    @staticmethod
    def get_purity_trust_level(purity: str) -> str:
        """Get human-readable trust level for purity"""
        trust_map = {
            "pure-compilation": "HIGHEST",
            "configure-only": "HIGH",
            "debian-patches": "MEDIUM-HIGH",
            "upstream-patches": "MEDIUM",
            "third-party-patches": "LOWER",
            "custom": "LOWEST",
        }
        return trust_map.get(purity, "UNKNOWN")
