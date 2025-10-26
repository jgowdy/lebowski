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
    def load(file_path: Path) -> Opinion:
        """Load opinion from YAML file"""
        if not file_path.exists():
            raise OpinionError(f"Opinion file not found: {file_path}")

        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)

        opinion = OpinionParser.parse(data)
        opinion._source_file = str(file_path)  # Track source for reproducibility
        return opinion

    @staticmethod
    def parse(data: Dict[str, Any]) -> Opinion:
        """Parse opinion from dictionary"""
        # Parse metadata
        metadata = OpinionMetadata(
            version=data.get('version', '1.0'),
            package=data['package'],
            opinion_name=data['opinion_name'],
            purity_level=data.get('purity_level', 'configure-only'),
            description=data.get('description', ''),
            maintainer=data.get('maintainer', {}),
            tags=data.get('tags', []),
            debian_versions=data.get('debian_versions', []),
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

        # Validate
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
